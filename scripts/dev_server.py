#!/usr/bin/env python3
"""
Local stand-in for the PlantPass API: the real Lambda handlers, a fake AWS.

    make dev                       # http://localhost:8787, seeded with sample data
    python scripts/dev_server.py --port 9000

Requests are routed with the route keys in terraform/apigateway.tf and handed
to the same lambda_handler functions production runs. DynamoDB and S3 are
moto's in-memory fakes, so nothing is saved between runs and nothing can reach
a real AWS account. Staff passphrase: "dev". Admin login needs no password.

Development and tests only. Nothing here is deployed: the deploy workflow zips
lambda/<Handler>/*.py and nothing else.

Not covered: the WebSocket API and email sending (both are skipped), the admin
password flows (no password is stored, so turning on "password protect admin"
locks you out until a restart), API Gateway's own behaviour (throttling,
payload limits), and IAM.
"""
import argparse
import importlib
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parent.parent
LAMBDA = ROOT / "lambda"

# Fake credentials first, before boto3 is imported anywhere, so that even a
# call moto does not intercept cannot touch a real account.
for name in ("AWS_PROFILE", "AWS_SESSION_TOKEN", "EMAIL_LAMBDA_ARN", "WEBSOCKET_ENDPOINT"):
    os.environ.pop(name, None)
os.environ.update(
    AWS_ACCESS_KEY_ID="local-fake",
    AWS_SECRET_ACCESS_KEY="local-fake",
    AWS_DEFAULT_REGION="us-east-1",
    AWS_REGION="us-east-1",  # some handlers pick their region from this one
    AWS_IGNORE_CONFIGURED_ENDPOINT_URLS="true",  # e.g. a LocalStack AWS_ENDPOINT_URL in the shell
    AWS_EC2_METADATA_DISABLED="true",
    JWT_SECRET="local-dev-server-secret-not-used-anywhere-real",
    PASSWORD_BUCKET="local-admin-password",
    PASSWORD_KEY="admin-password",
)

# First path segment -> handler folder. apigateway.tf says which routes exist;
# this says who serves them.
HANDLERS = {
    "transactions": "TransactionHandler",
    "products": "ProductsHandler",
    "discounts": "DiscountsHandler",
    "payment-methods": "PaymentMethodsHandler",
    "lock": "LockHandler",
    "feature-toggles": "FeatureTogglesHandler",
    "plantpass-access": "PlantPassAccessHandler",
    "admin": "AdminAuthHandler",
}

# Table name -> (hash key, [(index name, hash key, range key or None)]).
# The server refuses to start if these names differ from terraform/dynamodb*.tf.
TABLES = {
    "transactions": (
        "purchase_id",
        [
            ("timestamp-index", "timestamp", None),
            ("payment-status-timestamp-index", "payment_status", "timestamp"),
        ],
    ),
    "products": ("SKU", []),
    "discounts": ("name", []),
    "payment_methods": ("name", []),
    "PlantPass-FeatureToggles": ("config_id", []),
    "PlantPass-Locks": ("resource_type", []),
    "PlantPass-Access": ("config_id", []),
    "temp_passwords": ("id", []),
    "websocket_connections": ("connectionId", []),
}
NUMBER_KEYS = {"timestamp"}

SAMPLE_PRODUCTS = [
    {"SKU": "4INRND", "item": "4-inch Round", "price_ea": 5.0, "sort_order": 1},
    {"SKU": "3PACK", "item": "3-Pack", "price_ea": 6.0, "sort_order": 2},
    {"SKU": "SMORCH", "item": "Small Orchid", "price_ea": 20.0, "sort_order": 3},
    {"SKU": "BEAKER", "item": "250 mL Beaker", "price_ea": 4.5, "sort_order": 4},
]
SAMPLE_DISCOUNTS = [{"name": "Member 10%", "type": "percent", "value": 10, "sort_order": 1}]
SAMPLE_PAYMENT_METHODS = [
    {"name": "Cash", "sort_order": 1},
    {"name": "Zelle", "sort_order": 2},
    {"name": "Check", "sort_order": 3},
]


def read_routes():
    """[(method, [segments]), ...] from the route_key lines in apigateway.tf."""
    text = (ROOT / "terraform" / "apigateway.tf").read_text()
    found = re.findall(r'route_key\s*=\s*"([A-Z]+) (/[^"]*)"', text)
    return [(method, path.strip("/").split("/")) for method, path in found]


def match_route(routes, method, path):
    """Return (route key, path parameters) or None. Literal segments win over {params}."""
    parts = path.strip("/").split("/")
    best = None
    for route_method, template in routes:
        if route_method != method or len(template) != len(parts):
            continue
        params, literals = {}, 0
        for want, got in zip(template, parts):
            if want.startswith("{"):
                params[want[1:-1]] = got
            elif want == got:
                literals += 1
            else:
                break
        else:
            if best is None or literals > best[0]:
                best = (literals, f"{route_method} /{'/'.join(template)}", params)
    return best and best[1:]


def check_tables_match_terraform():
    declared = set()
    for tf in (ROOT / "terraform").glob("dynamodb*.tf"):
        declared |= set(re.findall(r'(?m)^  name\s*=\s*"([^"]+)"', tf.read_text()))
    if declared != set(TABLES):
        sys.exit(
            "dev server: TABLES in scripts/dev_server.py and terraform/dynamodb*.tf "
            f"disagree about {sorted(declared ^ set(TABLES))}"
        )


def start_fake_aws():
    check_tables_match_terraform()
    from moto import mock_dynamodb, mock_s3

    mock_dynamodb().start()
    mock_s3().start()

    import boto3

    dynamodb = boto3.client("dynamodb")
    for table, (hash_key, indexes) in TABLES.items():
        attributes = {hash_key}
        for _, index_hash, index_range in indexes:
            attributes |= {index_hash} | ({index_range} if index_range else set())
        spec = dict(
            TableName=table,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": hash_key, "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": a, "AttributeType": "N" if a in NUMBER_KEYS else "S"}
                for a in sorted(attributes)
            ],
        )
        if indexes:
            spec["GlobalSecondaryIndexes"] = [
                {
                    "IndexName": name,
                    "KeySchema": [{"AttributeName": index_hash, "KeyType": "HASH"}]
                    + ([{"AttributeName": index_range, "KeyType": "RANGE"}] if index_range else []),
                    "Projection": {"ProjectionType": "ALL"},
                }
                for name, index_hash, index_range in indexes
            ]
        dynamodb.create_table(**spec)

    boto3.client("s3").create_bucket(Bucket=os.environ["PASSWORD_BUCKET"])

    # Settings the handlers read as plain rows. Admin password protection is
    # off so the admin console opens without a password locally; the staff
    # passphrase is on because that is how a device gets its staff token.
    resource = boto3.resource("dynamodb")
    resource.Table("PlantPass-FeatureToggles").put_item(
        Item={
            "config_id": "feature_toggles",
            "collectEmailAddresses": True,
            "passwordProtectAdmin": False,
            "protectPlantPassAccess": True,
        }
    )
    resource.Table("PlantPass-Access").put_item(
        Item={"config_id": "plantpass_access", "passphrase": "dev"}
    )


# Every handler folder has a lambda_handler.py and flat imports of same-named
# helper files, so only one handler's modules can be importable at a time.
LOCAL_MODULES = {p.stem for d in HANDLERS.values() for p in (LAMBDA / d).glob("*.py")}
_loaded = {}
sys.path.insert(0, str(LAMBDA / "layers" / "python"))  # shared_utils, as the layer provides it
sys.path.insert(0, "")  # slot 0 is swapped to the active handler's folder


def handler_for(folder):
    for name in LOCAL_MODULES:
        sys.modules.pop(name, None)
    sys.path[0] = str(LAMBDA / folder)
    if folder in _loaded:
        sys.modules.update(_loaded[folder])
    else:
        importlib.import_module("lambda_handler")
        _loaded[folder] = {n: sys.modules[n] for n in LOCAL_MODULES if n in sys.modules}
    return _loaded[folder]["lambda_handler"].lambda_handler


ROUTES = read_routes()


def call(method, path, body=None, headers=None, query=None):
    """Run one request through the matching Lambda. Returns (status, headers, body text)."""
    matched = match_route(ROUTES, method, path)
    folder = HANDLERS.get(path.strip("/").split("/")[0])
    if not matched or not folder:
        return 404, {}, json.dumps({"message": "Not Found"})
    route_key, params = matched
    event = {
        "routeKey": route_key,
        "headers": {k.lower(): v for k, v in (headers or {}).items()},
    }
    if params:
        event["pathParameters"] = params
    if query:
        event["queryStringParameters"] = query
    if body:
        event["body"] = body
    response = handler_for(folder)(event, None)
    return response["statusCode"], response.get("headers") or {}, response.get("body") or ""


def seed():
    _, _, body = call("POST", "/admin/login", "{}")
    auth = {"Authorization": f"Bearer {json.loads(body)['token']}"}
    for path, rows in (
        ("/products", SAMPLE_PRODUCTS),
        ("/discounts", SAMPLE_DISCOUNTS),
        ("/payment-methods", SAMPLE_PAYMENT_METHODS),
    ):
        status, _, text = call("PUT", path, json.dumps(rows), auth)
        assert status == 200, f"seeding {path} failed: {status} {text}"


CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,PUT,POST,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
}


class Handler(BaseHTTPRequestHandler):
    timeout = 5  # one request at a time, so a silent connection must not block the rest

    def _respond(self, status, headers, text):
        payload = text.encode()
        self.send_response(status)
        for key, value in {"Content-Type": "application/json", **CORS, **headers}.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if status != 204:
            self.wfile.write(payload)

    def _handle(self):
        if self.command == "OPTIONS":
            return self._respond(204, {}, "")
        url = urlsplit(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode() if length else None
        try:
            status, headers, text = call(
                self.command, url.path, body, dict(self.headers), dict(parse_qsl(url.query))
            )
        except Exception as error:  # a handler crashed at import or outside its own try
            status, headers, text = 500, {}, json.dumps({"message": f"dev server: {error!r}"})
        self._respond(status, headers, text)

    do_GET = do_POST = do_PUT = do_DELETE = do_OPTIONS = _handle


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    unserved = {parts[0] for _, parts in ROUTES} - set(HANDLERS)
    if unserved:
        sys.exit(f"dev server: apigateway.tf has routes under {sorted(unserved)} but HANDLERS has no folder for them")
    start_fake_aws()
    seed()
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"PlantPass dev API on http://localhost:{args.port}  (staff passphrase: dev)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
