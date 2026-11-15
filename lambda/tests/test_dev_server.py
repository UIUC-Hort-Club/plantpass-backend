"""
One order through the real handlers, end to end, on the local dev server.

This is the only test that runs the Lambdas against a database (moto's fake
DynamoDB) instead of mocks. The server runs in its own process because the
other test files replace boto3 with a mock for the whole pytest process.
"""
import json
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parents[2] / "scripts" / "dev_server.py"


@pytest.fixture(scope="module")
def api():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    # Output is inherited, so pytest shows the server's log (and any handler
    # traceback) with a failing test. Never a PIPE: nobody would read it, and
    # the server blocks once it has logged 64 KB into one.
    server = subprocess.Popen([sys.executable, str(SERVER), "--port", str(port)])

    def request(method, path, body=None, token=None):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Bearer {token}"} if token else {},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                status, text = response.status, response.read().decode()
        except urllib.error.HTTPError as error:
            status, text = error.code, error.read().decode()
        return status, json.loads(text) if text else None

    try:
        for _ in range(100):
            if server.poll() is not None:
                pytest.fail("dev server exited at startup; see its captured output")
            try:
                request("GET", "/feature-toggles")
                break
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.1)
        else:
            pytest.fail("dev server did not start within 10 seconds")
        yield request
    finally:
        server.terminate()
        server.wait(timeout=10)


@pytest.fixture(scope="module")
def staff(api):
    status, body = api("POST", "/plantpass-access/verify", {"passphrase": "dev"})
    assert status == 200
    return body["token"]


@pytest.fixture(scope="module")
def admin(api):
    status, body = api("POST", "/admin/login", {})
    assert status == 200
    return body["token"]


def new_order(api, staff, **overrides):
    order = {
        "items": [{"SKU": "4INRND", "item": "4-inch Round", "quantity": 4, "price_ea": 5.0}],
        "discounts": [{"name": "Member 10%", "type": "percent", "value": 10, "selected": True}],
        "voucher": 1,
        "email": "customer@example.com",
        **overrides,
    }
    status, body = api("POST", "/transactions", order, staff)
    assert status == 201, body
    return body["transaction"]


def unpaid_ids(api, staff):
    status, body = api("GET", "/transactions/recent-unpaid?limit=20", token=staff)
    assert status == 200
    return [t["purchase_id"] for t in body["transactions"]]


def test_public_routes_need_no_token_and_staff_routes_do(api):
    assert api("GET", "/products")[0] == 200
    assert api("GET", "/feature-toggles")[0] == 200
    assert api("GET", "/transactions/recent-unpaid")[0] == 401
    assert api("POST", "/transactions", {"items": []})[0] == 401
    assert api("GET", "/no-such-route")[0] == 404


def test_wrong_passphrase_gets_no_token(api):
    status, body = api("POST", "/plantpass-access/verify", {"passphrase": "nope"})
    assert status == 401 and "token" not in body


def test_an_order_from_entry_to_paid(api, staff):
    order = new_order(api, staff)
    order_id = order["purchase_id"]
    assert re.fullmatch(r"[A-Z]{3}-[A-Z]{3}", order_id)
    # 4 x $5.00, less 10% ($2.00), less a $1 voucher
    assert order["receipt"] == {"subtotal": 20.0, "discount": 3.0, "total": 17.0}
    assert order["payment_status"] == "unpaid"

    # the cashier's backlog, served by the payment-status index
    assert order_id in unpaid_ids(api, staff)

    # the customer's receipt lookup needs no login
    status, receipt = api("GET", f"/transactions/{order_id}")
    assert status == 200 and receipt["receipt"]["total"] == 17.0

    # the cashier corrects the quantity; the percent discount follows, and the
    # price stays what it was when the order was entered, whatever is sent
    changed = [{"SKU": "4INRND", "item": "4-inch Round", "quantity": 2, "price_ea": 3.0}]
    status, body = api("PUT", f"/transactions/{order_id}", {"items": changed}, staff)
    assert status == 200, body
    assert body["transaction"]["receipt"] == {"subtotal": 10.0, "discount": 2.0, "total": 8.0}

    # an update must carry whole items: a bare SKU and quantity is rejected
    status, _ = api(
        "PUT", f"/transactions/{order_id}", {"items": [{"SKU": "4INRND", "quantity": 1}]}, staff
    )
    assert status == 400

    status, body = api(
        "PUT", f"/transactions/{order_id}", {"payment": {"method": "Cash", "paid": True}}, staff
    )
    assert status == 200
    paid = body["transaction"]
    assert paid["payment"] == {"method": "Cash", "paid": True}
    assert paid["payment_status"] == "paid"
    assert paid["customer_email"] == "customer@example.com"

    assert order_id not in unpaid_ids(api, staff)


def test_analytics_count_only_paid_orders(api, staff):
    before = api("GET", "/transactions/sales-analytics", token=staff)[1]

    unpaid = new_order(api, staff)
    paid = new_order(api, staff)
    api("PUT", f"/transactions/{paid['purchase_id']}", {"payment": {"method": "Zelle", "paid": True}}, staff)

    after = api("GET", "/transactions/sales-analytics", token=staff)[1]
    assert after["total_orders"] == before["total_orders"] + 1
    assert after["total_sales"] == pytest.approx(before["total_sales"] + 17.0)
    # the table under the totals lists every order, each flagged paid or not
    listed = {t["purchase_id"]: t["paid"] for t in after["transactions"]}
    assert listed[paid["purchase_id"]] is True
    assert listed[unpaid["purchase_id"]] is False


def test_export_is_admin_only(api, staff, admin):
    assert api("GET", "/transactions/export-data", token=staff)[0] == 403
    status, body = api("GET", "/transactions/export-data", token=admin)
    assert status == 200
    assert body["filename"].startswith("plantpass_data_export_") and body["content"]


def test_only_an_admin_can_change_the_product_list(api, staff, admin):
    products = api("GET", "/products")[1]
    assert api("PUT", "/products", products, staff)[0] == 403
    assert api("PUT", "/products", products, admin)[0] == 200
    assert api("GET", "/products")[1] == products


def test_a_deleted_order_is_gone(api, staff):
    order_id = new_order(api, staff)["purchase_id"]
    assert api("DELETE", f"/transactions/{order_id}", token=staff)[0] == 204
    assert api("GET", f"/transactions/{order_id}")[0] == 404
    assert order_id not in unpaid_ids(api, staff)
