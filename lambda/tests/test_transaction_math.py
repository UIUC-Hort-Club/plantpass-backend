"""
Order money and state rules in TransactionHandler/transaction.py.

These pin down what the code does today, so a change to discounts, vouchers or
order state fails here first. When a rule is changed on purpose, change its
test in the same commit.
"""
import os
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../TransactionHandler"))

from transaction import Transaction  # noqa: E402


def order(items=None, discounts=None, voucher=0):
    return Transaction.from_json(
        {
            "items": items
            if items is not None
            else [
                {"SKU": "4INRND", "item": "4-inch Round", "quantity": 4, "price_ea": 5.0},
                {"SKU": "3PACK", "item": "3-Pack", "quantity": 1, "price_ea": 6.0},
            ],
            "discounts": discounts or [],
            "voucher": voucher,
        }
    )


TEN_PERCENT = {"name": "10% Off", "type": "percent", "value": 10}
FIVE_DOLLARS = {"name": "$5 Off", "type": "dollar", "value": 5}


def test_new_order_totals_and_starts_unpaid():
    t = order()
    assert t.receipt == {"subtotal": 26.0, "discount": 0, "total": 26.0}
    assert t.payment == {"method": "", "paid": False}
    assert t.payment_status == "unpaid"


def test_order_id_is_three_letters_dash_three_letters():
    pid = order().purchase_id
    assert len(pid) == 7 and pid[3] == "-"
    assert (pid[:3] + pid[4:]).isalpha() and pid.isupper()


def test_percent_discount_is_taken_from_subtotal():
    t = order(discounts=[{**TEN_PERCENT, "selected": True}])
    assert t.receipt["discount"] == pytest.approx(2.6)
    assert t.receipt["total"] == pytest.approx(23.4)


def test_dollar_discount_is_a_flat_amount():
    t = order(discounts=[{**FIVE_DOLLARS, "selected": True}])
    assert t.receipt["total"] == pytest.approx(21.0)


def test_unselected_discount_is_recorded_but_takes_nothing_off():
    t = order(discounts=[{**TEN_PERCENT, "selected": False}])
    assert t.discounts == [{**TEN_PERCENT, "amount_off": 0}]
    assert t.receipt["total"] == pytest.approx(26.0)


def test_discounts_and_voucher_stack():
    t = order(
        discounts=[{**TEN_PERCENT, "selected": True}, {**FIVE_DOLLARS, "selected": True}],
        voucher=10,
    )
    # 26.00 - 2.60 - 5.00 - 10.00
    assert t.receipt["total"] == pytest.approx(8.4)


def test_total_never_goes_below_zero():
    assert order(voucher=28).receipt["total"] == 0


def test_voucher_larger_than_order_is_recorded_in_full():
    # Today's behaviour, seen once at the 2026 sale. Roadmap R2
    # changes it to cap the voucher at the subtotal; update this test then.
    t = order(voucher=28)
    assert t.club_voucher == 28
    assert t.receipt["discount"] == 28
    assert t.receipt["subtotal"] == 26.0


def test_marking_paid_sets_both_payment_fields():
    t = order()
    t.update_payment({"method": "Cash", "paid": True})
    assert t.payment == {"method": "Cash", "paid": True}
    assert t.payment_status == "paid"


def test_changing_quantity_keeps_the_price_the_order_was_created_with():
    t = order(discounts=[{**TEN_PERCENT, "selected": True}])
    t.update_items(
        [{"SKU": "4INRND", "item": "renamed", "quantity": 10, "price_ea": 3.0}]
    )
    assert t.items == [
        {"SKU": "4INRND", "item": "4-inch Round", "quantity": 10, "price_ea": 5.0}
    ]
    # the percent discount follows the new subtotal
    assert t.receipt["subtotal"] == 50.0
    assert t.receipt["discount"] == pytest.approx(5.0)


def test_deselecting_a_discount_on_update_removes_it_from_the_total():
    t = order(discounts=[{**TEN_PERCENT, "selected": True}])
    t.update_discounts([{"name": "10% Off", "selected": False}])
    assert t.receipt["total"] == pytest.approx(26.0)


def test_changing_the_voucher_recalculates_the_total():
    t = order()
    t.update_voucher(6)
    assert t.club_voucher == 6
    assert t.receipt["total"] == pytest.approx(20.0)


def test_the_stored_record_has_exactly_these_fields():
    t = Transaction.from_json(
        {
            "items": [{"SKU": "3PACK", "item": "3-Pack", "quantity": 1, "price_ea": 6.0}],
            "voucher": 1,
            "email": "customer@example.com",
        }
    )
    stored = t.to_dict()
    assert set(stored) == {
        "purchase_id",
        "timestamp",
        "items",
        "discounts",
        "club_voucher",
        "customer_email",
        "payment",
        "payment_status",
        "receipt",
    }
    # the request says "email" and "voucher"; the record says otherwise
    assert stored["customer_email"] == "customer@example.com"
    assert stored["club_voucher"] == 1


def test_a_paid_order_is_still_paid_after_loading_from_the_database():
    t = order()
    t.update_payment({"method": "Zelle", "paid": True})
    stored = t.to_dict()
    del stored["payment_status"]  # rebuilt from payment.paid on load

    loaded = Transaction.from_db_record(stored)
    assert loaded.payment_status == "paid"
    assert loaded.payment == {"method": "Zelle", "paid": True}
    assert loaded.to_dict() == t.to_dict()


def test_round_trip_through_the_database_shape():
    t = order(discounts=[{**TEN_PERCENT, "selected": True}], voucher=1.5)
    record = t.to_db_record()
    assert record["receipt"]["subtotal"] == Decimal("26.0")
    assert isinstance(record["club_voucher"], Decimal)

    loaded = Transaction.from_db_record(t.to_dict())
    assert loaded.to_dict() == t.to_dict()


def test_old_or_damaged_records_still_load():
    t = Transaction.from_db_record({"purchase_id": "ABC-DEF", "items": None})
    assert t.items == [] and t.discounts == [] and t.receipt == {}
    assert t.payment == {"method": "", "paid": False}
    assert t.payment_status == "unpaid"
    assert t.get_summary() == {
        "purchase_id": "ABC-DEF",
        "timestamp": None,
        "total_quantity": 0,
        "grand_total": 0,
        "paid": False,
    }
