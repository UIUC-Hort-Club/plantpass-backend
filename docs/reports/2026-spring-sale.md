# 2026 spring sale — what the report tells us

Digest of the post-sale business report for the April 11, 2026 sale, kept to
the facts that should shape the software. The full report (charts, per-product
tables, vendor payback) is `2026_PlantPass_Business_Report.html`, generated
April 12, 2026 from export `plantpass_data_export_20260412_160444`. The
architect has both.

## The day

- Saturday, 9:00am–5:00pm Central. 700 orders, 3,551 items, 24 products.
- $23,366 net, $24,176 before discounts. Average order $33.38, median $26.00.
- Busiest 15 minutes: 10:00–10:15am, 46 orders. First three hours: 490 orders
  (70%) and 77% of revenue. Last two hours: 75 orders.
- Payment: cash 436 (62%), Zelle 237 (34%), check 27 (4%).
- Vouchers: 50 orders, $815 total, 14 orders fully covered ($0 total). Largest
  single voucher $150.
- Mid-sale changes made by hand in the admin console: four prices cut around
  3:38–4:03pm; bonsai added at 10:10am, terrariums at 2:40pm.

## What went wrong, in order of cost

1. **Unpaid orders piled up and were force-completed as "Cash".** Orders sat
   in the backlog after the customer had paid or walked away. Volunteers
   cleared them by marking them Cash. Some were really cancelled orders. Every
   order in the export says `paid: True`, so real sales and cleared-out junk
   cannot be told apart. Estimated effect: 20–30 false orders, revenue
   overstated by roughly $650–$1,300 (3–6%), cash share overstated.
2. **No way to say "this order was cancelled".** Same root cause as 1. The
   report says cancelled orders "could not be deleted"; the code does have a
   Delete Order button on the cashier screen, so why it was not used on the day
   is an open question (hard to find? failed? not known to volunteers?).
3. **A voucher larger than the order.** One order had a $26 subtotal and a $28
   voucher. Total correctly showed $0, but the export records $28 of discount
   on a $26 order.
4. **A trailing space in a product name.** "4-inch Round " (SKU 4INRND) in
   every row. Breaks exact-match grouping in a spreadsheet.
5. **No starting stock counts.** Sales volume cannot be turned into
   sell-through, so the club cannot tell what sold out from what was
   over-ordered.
6. **Timestamps are raw UTC epoch seconds** (`1775940282.0`). Whoever analyses
   the export has to convert by hand.
7. **Vendor payback was computed by hand** for bonsai ($655) and terrariums
   ($175) by filtering SKUs.

Also seen in the code history, not in the report: the sales analytics endpoint
timed out on sale day and was patched live (backend commits of April 11, 2026).

## What the report asked for

The report's "Developer Notes" list about twenty features. They are triaged,
with reasons, in `../ROADMAP.md`. Do not treat the report's list as a backlog:
it was written from the analyst's chair, and several items would make the
volunteer's screen worse to make the spreadsheet better.
