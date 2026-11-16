"""
The live-update channel must never carry an order.

The dashboard only needs to know that something changed; it then fetches the
data through the API with its token.
"""
import importlib
import json
import os
import sys
from unittest.mock import MagicMock

HANDLER = os.path.join(os.path.dirname(__file__), "../TransactionHandler")


def test_a_broadcast_says_only_that_orders_changed(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("CONNECTIONS_TABLE", "websocket_connections")
    monkeypatch.syspath_prepend(HANDLER)
    sys.modules.pop("websocket_notifier", None)
    notifier = importlib.import_module("websocket_notifier")

    connections = MagicMock()
    connections.scan.return_value = {"Items": [{"connectionId": "abc"}]}
    monkeypatch.setattr(notifier, "dynamodb", MagicMock(Table=lambda name: connections))
    client = MagicMock()
    monkeypatch.setattr(notifier, "get_api_gateway_client", lambda: client)

    notifier.notify_transaction_update("created")

    (call,) = client.post_to_connection.call_args_list
    assert call.kwargs["ConnectionId"] == "abc"
    assert json.loads(call.kwargs["Data"]) == {"type": "transaction_update", "event": "created"}
