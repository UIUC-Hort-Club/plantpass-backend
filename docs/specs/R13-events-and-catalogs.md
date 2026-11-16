# R13 — Run any event, with its own products

Status: approved 2026-11-14
Roadmap item: R13

## Problem and evidence

Decision D4: the club will use PlantPass at events other than the plant sale,
selling other things (lab supplies, for example).

Today the app assumes one sale:

- There is one pile of orders. To start a second event the organizer must
  export, then press "Clear Records", which deletes everything and cannot be
  undone. Skip the export and the last event is lost; skip the clear and two
  events' sales are added together in analytics and the export.
- There is one product list, edited one row at a time. Loading fifty lab
  supplies means typing fifty rows, and doing so destroys the plant list.
- The home screen and passphrase prompt say "Spring Plant Fair Staff".

## What the volunteer sees

Checker and cashier: the event's name where it now says "Spring Plant Fair",
and nothing else. No new field, button or decision.

Organizer (admin console): the current event's name at the top; a "Start new
event" action; "Import" and "Download" buttons on the product list; an event
picker on the export.

## Smallest version

1. **One current event.** A name (for example "Spring Plant Sale 2027") stored
   in the existing settings table. "Start new event" asks for a name and makes
   it current. Nothing is deleted.
2. **Orders remember their event.** Each new order is stamped with the current
   event. Orders from before this change count as "2026 Spring Plant Sale".
3. **Everything defaults to the current event.** Recent-unpaid, analytics and
   the export show the current event. The export can also be run for a past
   event.
4. **Products load from a spreadsheet.** "Download" gives the current list as
   a CSV (name, SKU, price). "Import" replaces the list from a CSV, after
   showing a preview and any rows it would reject. The saved CSV is the club's
   copy of a catalog; switching back to plants is importing last year's file.
   Orders already copy each item's name and price, so past orders never depend
   on the live list.
5. **Neutral wording.** "Staff" and the event name replace the plant-fair text.

## Left out on purpose

- **Two events at once.** Needs per-event products, passphrases and device
  assignment. Worth it only if the club actually double-books.
- **Catalogs stored per event inside the app.** The CSV does this with no new
  screens. Revisit if organizers lose the files.
- **Per-event discounts and payment methods.** They stay as global lists the
  organizer edits before an event, as now.
- **Browsing a past event's orders in the app.** The export covers it.
- **Search or categories on the checker's screen.** Only needed if a real
  catalog is too long to scan (D18).

## Changes

- Data: `event` (string) on the order, with an index on it; a `current_event`
  row in the settings table. Reading an order without `event` yields the 2026
  sale. The settings table also keeps one read-only copy of the product list
  with each finished event, saved when the next event starts and used only
  to put `products.csv` in that event's export. It is not a catalog the
  organizer can switch to (D20). No new table.
- API: `GET/PUT` for the current event; `event` query parameter on export and
  analytics; `event` in order responses. The live frontend keeps working: all
  additions.
- Backend files: `TransactionHandler/transaction.py`, `database_interface.py`,
  `sales_analytics.py` (and the clear-all route and function removed: D19),
  `csv_export.py`, `lambda_handler.py`;
  `FeatureTogglesHandler` (or a small sibling route) for the setting;
  `terraform/apigateway.tf` for new routes and `terraform/dynamodb.tf` for the
  index.
- Frontend files: `AdminConsole/` (event header, start-event dialog, product
  import/download, export picker, and "Clear Records" removed: D19), `Home/HomeScreen.tsx`,
  `Home/PlantPassAccessModal.tsx`, `types/index.ts`.
- Docs: `USAGE.md` gains "Running an event" (before, during, after).

## How we know it works

- Tests: an order with no `event` reads as the 2026 sale; analytics and export
  for event A exclude event B's orders; CSV import rejects a duplicate SKU, a
  missing price and a negative price, and trims names (this is also R3).
- Without a live event: on the local server (R5), create two events with
  different product lists and orders in each; check each export.
- Cannot be checked before production: nothing, if R5 and R14 are in place.

## Ship plan

Backend first (additive), then frontend. Depends on R5 for testing. Undo by
reverting; orders keep an `event` field the old code ignores.

Orders are indexed by event (one new index on the orders table), so the
recent-unpaid list, analytics and export for an event read only that event's
orders and stay fast as past events accumulate (D11).

## Decided

- One current event at a time (D17).
- Assume about forty products or fewer; no search on the checker's screen
  (D18).
- Past events' orders are kept and exportable; "Clear Records" is removed from
  the admin console (D19).
- Product lists are CSV files in and out, and each event's export carries its
  product list (D20). So the export gains a `products.csv`, written from a
  copy of the list saved when the next event starts.
- Assumed, not asked: the clear-all API route is removed along with the
  console button, since a destructive route with no screen is only a risk;
  discounts and payment methods are not per event; the
  app keeps its name with the event name under it; orders are indexed by event
  from the start rather than filtered after a full read.
