# PlantPass — product brief

Read this before proposing, planning, or building anything. It is the yardstick
every feature is measured against.

## What it is

A lightweight checkout app for the UIUC Horticulture Club. Volunteers use it on
their own phones and laptops to ring up what the club sells at an event. It has
to be obvious to someone who has never seen it before and has a line of
customers in front of them.

The spring plant sale is the biggest event and sets the load, but it is not the
only one. The club should be able to run PlantPass at any event, load in
whatever that event sells (plants, lab supplies, anything with a name and a
price), and come back to it months later without a developer (decision D4).

It is **not** a general point-of-sale system, an inventory system, or a
payments processor. Money changes hands outside the app (cash, Zelle, check);
PlantPass only records what was sold and how it was paid.

## How an event runs

| Station | Who | Screen | What they do |
|---|---|---|---|
| Checker | volunteer | `/plantpass` → Order Entry | Counts the customer's items, enters quantities, voucher and discounts. Gets an Order ID (`ABC-DEF`) and writes it on a paper slip. |
| Cashier | volunteer | `/plantpass` → Order Lookup | Looks up the Order ID (or taps it in "recent unpaid"), takes payment, picks the payment method, completes the order. |
| Customer | anyone | `/orders` | Optional: looks up their own receipt by Order ID. |
| Organizer | club officer | `/admin-console` | Sets up products, discounts, payment methods before the event; watches sales; exports data afterwards. |

A small event may have one person doing both stations. An order that has been
entered but not yet paid is **unpaid** and sits in the cashier's backlog until
someone completes or cancels it.

## The load it must carry

The 2026 plant sale (Saturday April 11, 9am–5pm) is the high-water mark:

- 700 orders, 3,551 items, 24 products, $23.4k revenue.
- Peak: 46 orders in 15 minutes (about 3 per minute) at 10:00am. 70% of all
  orders happen before noon.
- Payment mix: 62% cash, 34% Zelle, 4% check. 7% of orders used a club voucher.
- Prices were changed by hand once, mid-afternoon, to clear stock.
- Products were added mid-sale (bonsai at 10:10, terrariums at 2:40).

Source: `docs/reports/2026-spring-sale.md`. The 2027 sale is April 9–11, three
days instead of one. Other events are smaller in volume but may have a longer
product list; nobody has measured one yet.

## Principles, in priority order

1. **A volunteer can use it with zero training.** If a screen needs
   explaining, it is wrong. Fewer fields, fewer taps, fewer choices.
2. **It does not fail during an event.** Each event happens once. Boring and
   proven beats clever.
3. **The numbers afterwards are true.** The club uses the export to settle
   with vendors and plan the next event. Wrong data is worse than missing
   data, and one event's numbers must never leak into another's.
4. **An organizer can set up an event alone.** Loading products, starting
   clean, and getting the data out afterwards must not need a developer or a
   deploy.
5. **It stays small.** One maintainer. Every feature is a thing that can break
   mid-event and must be re-understood months later.

When these pull against each other, the lower number wins.

## Always true, never traded

The architect's standing brief (decision D11): the app is **secure, easy to
use, lightweight and fast, and optimized for AI-driven development**. Easy and
lightweight are principles 1 and 5 above. The other three are not ranked,
because nothing above is allowed to cost them:

- **Secure.** The repos are public and the app holds customer emails and the
  club's sales record. Every route that changes or reveals data checks who is
  asking; no secret lives in source; a login cannot be guessed at without
  limit. A feature that needs a security shortcut is not ready.
- **Fast.** A volunteer on a phone, on crowded event Wi-Fi, should never wait
  on the app. A screen that gets slower as the day's orders pile up is a bug.
  Measure before and after anything that touches the order screens or reads
  the whole order table.
- **Built for agents to change safely.** Any change can be made, checked and
  run locally by an agent without touching production; the rules a change must
  respect are written down and tested, not remembered; a deploy can be
  previewed and undone. When a change is hard for an agent to verify, fix
  that before building the next feature.

## The filter: does this need to exist?

Ask these in order. Stop at the first "no".

1. **Did it cost us something real at a real event, or does the architect's
   stated direction require it?** Point to the line in a sale report, a
   specific moment at an event, or the entry in `DECISIONS.md`. "It would be
   nice" and "other POS systems have it" are not evidence.
2. **Can a person, a piece of paper, or a spreadsheet after the event do it
   instead?** If the export plus ten minutes in a spreadsheet answers the
   question, the app does not need the feature.
3. **Does it add nothing to the checker's or cashier's screen?** A new field,
   button, or decision during the rush needs much stronger evidence than a
   change in the admin console or the export.
4. **Is there a version that is a tenth of the size?** Build that one. Record
   what was left out.
5. **Can it be tested without a live event?** If the first real test is 10am
   on sale day, it is not ready.

Two more questions since D4. They do not block a feature; they shape it.

- **Does it assume plants, or one event a year?** Wording, product fields and
  data lifecycle must work for a lab-supply sale in October as well as the
  plant sale in April.
- **Does it still work when production is in use?** There may be a live event
  on any given day. A change that needs an empty database or a quiet week is
  not finished.

A "no" is a useful result. Record it in `docs/ROADMAP.md` under "Not building"
with the reason, so it is not re-argued every year.

## Who decides

Joseph Ku is the architect. Agents propose, with evidence and a recommendation;
the architect decides what gets built, what the data model is, and when
anything ships. Decisions are recorded in `docs/DECISIONS.md`. An agent that
disagrees says so once, clearly, then follows the decision.

## Not this app's job

Inventory management with live stock counts, customer accounts or loyalty,
card processing, per-volunteer logins, use by other clubs, offline mode. Each
of these has been considered; see `docs/ROADMAP.md` for why.
