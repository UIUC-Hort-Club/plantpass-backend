"""
How long ago a temporary admin password was issued.

"Forgot password" may be asked once a minute. The time is worked out from the
stored expiry, so getting the arithmetic wrong silently changes one minute into
sixteen, or into none.
"""
import importlib
import os
import sys
import time
from decimal import Decimal
from unittest.mock import MagicMock

HANDLER = os.path.join(os.path.dirname(__file__), "../AdminAuthHandler")


def manager_with(item, monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.syspath_prepend(HANDLER)
    sys.modules.pop("temp_password_manager", None)
    manager = importlib.import_module("temp_password_manager")
    table = MagicMock()
    table.get_item.return_value = {"Item": item} if item else {}
    monkeypatch.setattr(manager, "table", table)
    return manager


def issued(seconds_ago):
    # stored as DynamoDB returns it: the expiry, 15 minutes after issue
    return {"id": "temp_password", "expiration": Decimal(int(time.time()) - seconds_ago + 15 * 60)}


def test_no_temporary_password_means_no_wait(monkeypatch):
    assert manager_with(None, monkeypatch).seconds_since_temp_password_issued() is None


def test_the_wait_is_counted_from_when_it_was_issued_not_when_it_expires(monkeypatch):
    assert 58 <= manager_with(issued(59), monkeypatch).seconds_since_temp_password_issued() <= 60
    assert 60 <= manager_with(issued(61), monkeypatch).seconds_since_temp_password_issued() <= 62
