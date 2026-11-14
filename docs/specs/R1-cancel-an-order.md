# R1 — Cancel an order instead of faking a payment

Status: draft
Roadmap item: R1

## Problem and evidence

2026 sale report, "Discrepancies" 1 and 2. Orders sat unpaid after the customer
had left. Volunteers cleared the backlog by marking them "Cash". Every order in
the export says paid, so real sales and cleared-out orders cannot be told
apart: an estimated 20–30 false orders and 3–6% of revenue.

The cashier screen has a "Delete Order" button. It was not what volunteers
reached for under pressure, and a deleted order leaves no trace, so the club
cannot count cancellations either. Decision D7: a cancelled order becomes
`void`; it is not deleted.

## What the volunteer sees

Cashier screen (Order Lookup), with an unpaid order loaded: the red "Delete
Order" button becomes "Cancel Order", in the same place, with the same
confirmation dialog. No new field, no new button, no new decision.

A cancelled order leaves the "recent unpaid" list at once. Looked up again by
its ID it shows "Cancelled" and is view-only, like a completed order.

Checker screen: no change. Customer receipt lookup: shows "Cancelled".

## Smallest version

1. A third order state, `void`, next to `unpaid` and `paid`.
2. `PUT /transactions/{id}` accepts `{"void": true}` for an unpaid order. A
   paid order cannot be voided. No new route, so no Terraform change.
3. Voided orders are left out of the recent-unpaid list (already true: the
   list asks the index for `unpaid`) and out of every total in analytics
   (already true: totals count paid orders only).
4. The export's `transactions.csv` gains a `status` column: `paid`, `unpaid`
   or `void`. The existing `paid` column stays, so old spreadsheets still work.
5. The analytics order table shows the status.

## Left out on purpose

- A reason for the cancellation, and who cancelled. Nothing in the report
  needed them, and both add typing to the busiest screen.
- Voiding a paid order (a refund). The club handles refunds in person; add it
  if a sale shows refunds being recorded wrongly.
- A screen listing cancelled orders. The export has them.
- Hard delete from the staff screens; see question 1.

## Changes

- Data: `payment_status` gains the value `void`. Today that field is
  recomputed from `payment.paid` every time an order is loaded, so a stored
  `void` would be lost on the next update; the load must keep it. Orders
  written before this change are unaffected.
- API: `void` in the `PUT` body; `payment_status: "void"` in responses. The
  live frontend keeps working: it never sends `void` and treats anything not
  paid as unpaid.
- Backend files: `TransactionHandler/transaction.py` (state, load),
  `database_interface.py` (apply `void`, refuse on a paid order),
  `lambda_handler.py` (pass it through), `csv_export.py` (`status` column),
  `sales_analytics.py` (status in the order table). Nothing in the layer
  (trap 9).
- Frontend files: `core/OrderLookup.tsx` (button, cancelled view),
  `core/SubComponents/Receipt.tsx` and `CustomerOrderLookup` (show
  "Cancelled"), `AdminConsole/SalesAnalytics.tsx` (status in the table, export
  help text), `api/transaction_interface/` (one call), `types/index.ts`.
- Docs: `USAGE.md` ("Order Lookup": cancel instead of delete),
  `ARCHITECTURE.md` (order states).

## How we know it works

- Tests: a voided order stays void after a load and a later update; voiding a
  paid order is refused; a voided order is absent from recent-unpaid and from
  analytics totals; the export row says `void`. Order rules go in
  `test_transaction_math.py`, the flow in `test_dev_server.py`.
- Without a live event: on the local copy, enter two orders, cancel one, pay
  the other, check the unpaid list, analytics and the export.
- Cannot be checked before production: nothing specific to this change.

## Ship plan

Backend first; it is additive and the live frontend ignores it. Then the
frontend. Undo by reverting; an order voided in between would read as unpaid
again to the old code, which is safe.

## Questions for the architect

1. **Does "Cancel Order" replace "Delete Order" on the cashier screen, or sit
   beside it?** Recommendation: replace. Two red buttons that both make an
   order disappear is a choice volunteers should not have to make, and delete
   is the one that loses data. Deleting stays possible for an organizer
   through the admin console.
2. **Can a cancelled order be restored?** Recommendation: yes, with one
   "Restore order" button on the cancelled order's view, which makes it
   unpaid again. Without it, a mis-tap means re-entering the order, which is
   the cost D7 was meant to avoid.
3. **May an order be cancelled only while unpaid?** Recommendation: yes.
4. **Should the customer's receipt page say "Cancelled"**, or simply "not
   found"? Recommendation: "Cancelled", so a customer holding a slip gets an
   answer.
