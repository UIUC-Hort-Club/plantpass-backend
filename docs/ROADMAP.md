# Roadmap

What is worth building, what is not, and why. Every item here has been put
through the filter in `PRODUCT.md`.

**Status of this file:** first triaged by an agent on 2026-11-14 from the 2026
sale report and a read of the code, then updated the same day with the
architect's decisions D4–D10. Statuses: `proposed` → `approved` → `specced`
(has a file in `specs/`) → `building` → `shipped`, or `declined`. Only the
architect moves an item to `approved`.

## Dates

| When | What |
|---|---|
| **April 9–11, 2027** | Spring plant sale (D5) |
| March 26, 2027 | Freeze starts: nothing merges without the architect (D9) |
| March 12–25 | Full rehearsal at last year's volume (R6); fixes only |
| February 15 – March 12 | Club tests on the hosted test copy, ideally at a small real event (needs R14, Q9) |
| February 12 | Everything below marked for 2027 is live on the test copy |
| January | Events and catalogs (R13), order states (R1), export and data fixes |
| November – December 2026 | Foundations: security (S1), local test server (R5), test copy and safe deploys (R14), shared-code cleanup (R12) |

The dates before the freeze are an agent's proposal and move with Q9.

## Before the April 2027 sale

These each fix something that cost the club real accuracy or risk in 2026.

| ID | What | Evidence | Smallest version | Status |
|---|---|---|---|---|
| S1 | Security hardening, two items | Found reading the code, 2026-11-14 | Details are with the architect, not in this file. Both are small Terraform changes. Do these first. | building |
| R1 | Cancel an order instead of faking a payment | Report §1–2: 20–30 unpaid orders were marked "Cash" to clear the backlog; revenue is uncertain by 3–6% | A "Cancel order" action on the cashier screen that sets a third state, `void`. Voided orders leave the unpaid list and are excluded from analytics; the export gets a `status` column. No reasons, no approvals, no undo screen. Decided: D7. | approved |
| R2 | Voucher cannot exceed the order | Report §3: $28 voucher on a $26 order | Backend clamps the applied voucher to the subtotal after other discounts. One line plus a test. | proposed |
| R3 | Trim names on save | Report §4: "4-inch Round " in every row | Backend strips whitespace from product, discount and payment-method names when the list is saved. One-time fix of the stored row happens by re-saving the list. | proposed |
| R4 | Record when an order was paid | Report "created vs. completed": all time charts use creation time; backlog delay cannot be measured | Add `paid_at` when payment is marked paid; add the column to the export. No UI. | proposed |
| R5 | A safe place to try changes | Local dev writes to production; an analytics timeout was found and patched on sale day | A small local server that runs the handlers against a fake DynamoDB, and a dev config that points the frontend at it instead of production. Decided: D6. | approved |
| R6 | Rehearse the sale | Same sale-day timeout; nothing today exercises 700 orders | Script that replays last year's export through whatever R5 provides, then loads analytics and export. Run it before every sale. Depends on R5. | proposed |
| R7 | Confirm staff access works with the passphrase off | `ARCHITECTURE.md` trap 6 | Reproduce in R5's environment. Either fix it or remove the toggle. | proposed |

## Since the 2026-11-14 decisions

These come from the architect's direction rather than from the sale report.

| ID | What | Why | Smallest version | Status |
|---|---|---|---|---|
| R13 | Run any event, with its own products | D4: the club will use this beyond the plant sale, with other catalogs such as lab supplies | Each order is stamped with the current event; analytics and export are per event; an organizer starts a new event without deleting the last one, and loads a product list from a spreadsheet. Plant-sale wording leaves the UI. Draft: `specs/R13-events-and-catalogs.md`. | specced (draft, has questions) |
| R14 | A test copy of the app, and deploys that are safe while it is in use | D9, Q7: the club must test before April; with D4 production can be live any day, and today a merge applies straight to it with no preview | A second copy of the stack at its own address that every merge deploys to first; production is released from a version already proven there, with an automatic smoke test and a one-step rollback. Draft: `specs/R14-safe-deploys.md`. | specced (draft, has questions) |

## Worth doing if cheap

| ID | What | Evidence | Smallest version | Status |
|---|---|---|---|---|
| R8 | Show how long an unpaid order has been waiting | Report: backlog built up unnoticed | Age ("12 min") on each row of the recent-unpaid list, highlighted past 10 minutes. No alerts, no sounds, no timers. | proposed |
| R9 | Readable export | Report §"Timezone": timestamps are `1775940282.0`, quantities are `1.0` | Add a local-time column (America/Chicago, ISO format); write whole numbers as whole numbers. Keep the existing columns so old spreadsheets still work. | proposed |
| R10 | Starting stock per product | Report §5, called the biggest gap for planning | One optional number per product in the admin console, entered before the sale. Export shows starting, sold, remaining. **No** live decrement on the checkout screens and no alerts. | proposed |
| R11 | Vendor tag on a product | Report: bonsai and terrarium payback ($830) was worked out by hand | One optional free-text `vendor` on a product; it appears as a column in the items export. No settlement report; a pivot table does that. | proposed |
| R12 | One copy of the shared backend helpers | `ARCHITECTURE.md` traps 1–3 | Handlers import from the `shared_utils` layer; delete the per-handler copies and `lambda/shared/`; re-enable the skipped transaction handler test. Behaviour must not change. Do it right after R5 so it can be tested. | proposed |

## Not building

Recorded so they are not re-argued each year. Reopen one only with new
evidence from a sale.

| What the report asked for | Why not |
|---|---|
| Timed price schedule (automatic markdown at 3:30pm) | Happened once, for four products, and the admin console already does it in under a minute. The hard part was deciding under pressure, and software does not fix that: decide the markdown the week before and write it on the run sheet. A scheduler is clock logic that can only be tested on the day. |
| Volunteer or operator ID on each order | Means a login or a name prompt on every device, against principle 1. The club has no use for per-volunteer productivity numbers. |
| Customer ID or loyalty | No use case. Email is already optional. |
| Payment verification flag | Exists only to detect force-completed orders. R1 removes the reason anyone would force-complete. |
| Item categories | 24 products. Grouping takes a minute in a spreadsheet; R11 covers the one grouping that mattered. Revisit only if R13 shows a real catalog too long to scan. |
| Notes field on orders | A free-text box on the busiest screen. Nothing in the report needed one once R1 exists. |
| Live inventory with auto-decrement and low-stock alerts | Counts drift the moment a plant is dropped, miscounted, or given away, and then the screen is lying to the checker. R10 gives the planning number without the false precision. |
| Real-time dashboard | Already exists: Sales Analytics refreshes over the WebSocket. |
| Receipt by QR code or text | Already exists in two forms: `/orders?id=ABC-DEF` and the optional email receipt. |
| Per-discount detail in the export | Already exists. `transaction_discounts.csv` was empty in 2026 because no discounts were configured; vouchers are in `transactions.csv`. |
| Pending-order timeout notifications | R8 shows the age where the cashier is already looking. Notifications on volunteers' personal phones are a permissions and noise problem. |

## Ideas with no evidence yet

Nothing here is planned. Add an idea with the date and who raised it; it moves
up only when a sale shows it was needed.

- Pre-sale readiness checklist as a skill (certificate, email sender, admin
  login, clear test data, export works). Raised by the agent, 2026-11-14.
