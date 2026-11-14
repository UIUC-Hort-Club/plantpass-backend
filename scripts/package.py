#!/usr/bin/env python3
"""
Build the Lambda zips, byte-for-byte reproducibly.

    python scripts/package.py            # writes into terraform/
    python scripts/package.py <folder>   # writes somewhere else (tests)

The same code always produces the same zip, so Terraform's source_code_hash
changes only for a function whose code changed. That is what lets a pull
request's plan say "No changes" and lets a deploy leave untouched functions
alone. No compression, fixed timestamps and sorted names, because all three
vary between machines.

Each zip holds the handler folder's *.py files, as the deploy always has.
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Handler folder -> zip name. The names are the ones in terraform/terraform.tfvars.
# tests/test_package.py fails if a handler folder is missing here.
ZIPS = {
    "TransactionHandler": "transactions_handler_lambda_package.zip",
    "AdminAuthHandler": "admin_password_lambda_package.zip",
    "ProductsHandler": "products_handler_lambda_package.zip",
    "DiscountsHandler": "discounts_handler_lambda_package.zip",
    "PaymentMethodsHandler": "payment_methods_handler_lambda_package.zip",
    "WebSocketHandler": "websocket_handler_lambda_package.zip",
    "EmailHandler": "emailhandler_lambda_package.zip",
    "LockHandler": "lockhandler_lambda_package.zip",
    "FeatureTogglesHandler": "featuretoggleshandler_lambda_package.zip",
    "PlantPassAccessHandler": "plantpassaccess_lambda_package.zip",
}


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for folder, name in ZIPS.items():
        with zipfile.ZipFile(out / name, "w", zipfile.ZIP_STORED) as archive:
            for source in sorted((ROOT / "lambda" / folder).glob("*.py")):
                info = zipfile.ZipInfo(source.name, date_time=(1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o644 << 16
                archive.writestr(info, source.read_bytes())


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ROOT / "terraform")
