# Decisions

Append-only log of what the architect has decided. Newest at the bottom. If a
decision is reversed, add a new entry that says so; do not edit the old one.

Agents: read this before proposing anything. Do not reopen a decision without
new evidence. Do not add an entry the architect has not actually made; put
proposals under "Open questions" instead.

Format: `D<n> — YYYY-MM-DD — decision`, then why, in a sentence or two.

## Decided

**D1 — 2026-11-14 — PlantPass is a lightweight checkout app for the
Horticulture Club's plant sale, and being easy for volunteers comes first.**
Stated by the architect when setting up agent-driven development. Expanded into
`PRODUCT.md`.

**D2 — 2026-11-14 — Joseph Ku is the architect. Agents plan, build, test and
deploy; the architect decides what is needed and what is not.** Agents bring a
recommendation and the evidence; they do not start building on their own
judgement of scope.

**D3 — 2026-11-14 — Agent skills live in the repositories, not in a
per-machine plugin.** The ponytail skills are vendored under `.agents/skills/`
so they are versioned with the code and travel with a clone.

**D4 — 2026-11-14 — PlantPass is for any club event, not only the spring
plant sale.** The club should be able to run it at other events and load in a
different set of products, lab supplies for example. This widens D1: still
lightweight, still volunteer-first, but nothing may assume one event a year or
that everything sold is a plant. `PRODUCT.md` was rewritten to match.

**D5 — 2026-11-14 — Next plant sale: April 9–11, 2027.** Development starts
now so the club can test well before it.

**D6 — 2026-11-14 — Testing without production: a small local server that runs
the Lambda handlers against a fake DynamoDB.** (Was Q2, option a.) Roadmap R5.

**D7 — 2026-11-14 — A cancelled order becomes `void`; it is not deleted.**
(Was Q3.) Roadmap R1.

**D8 — 2026-11-14 — The agent kit and product docs stay in
`plantpass-backend`.** (Was Q1.) Two repos, no merge into one.

**D9 — 2026-11-14 — Nothing merges in the 14 days before a sale, and the
deploy process should become safe enough to release while the app is serving
traffic.** (Was Q4.) The freeze is the rule today; making it unnecessary is
roadmap R14. For the 2027 sale the freeze starts March 26, 2027.

**D10 — 2026-11-14 — An agent may merge to `main` without asking when all
three hold: a review has been performed, its verdict is approve, and the net
effect against `main` is better.** (Was Q6.) How `/ship` applies this is
written in that skill; the architect's words are the rule, the skill is the
agent's reading of them.

**D11 — 2026-11-14 — "Make sure this app is secure, easy to use, lightweight
and fast, and optimized for AI driven development."** The architect's standing
brief, in their words. Written into `PRODUCT.md` as "Always true, never
traded"; use it to break ties in any recommendation.

Decisions D12 to D25 were settled on 2026-11-14 in a one-question-at-a-time
interview; each was the architect accepting the agent's recommendation.

**D12 — 2026-11-14 — A hosted test copy of the whole app, in the same AWS
account,** with its own empty database, for the club to test on and for every
change to be proven on before production. (Was Q7.)

**D13 — 2026-11-14 — The test copy starts on the address AWS assigns
(`…cloudfront.net`).** `test.hortclubplantpass.org` is added only if testers
find the link awkward. DNS is at Cloudflare and its records are added by hand.

**D14 — 2026-11-14 — Production is a separate, deliberate release step.** A
merge deploys to the test copy only and smoke-tests it; production is released
from a version that passed there. An agent may run the release under D10;
inside a freeze window only the architect.

**D15 — 2026-11-14 — A pull request cannot merge unless the `test` check
passes.** Added the same day to the existing "Guardrail-Master" ruleset in both
repos. No approvals are required, so D10 still works.

**D16 — 2026-11-14 — The schedule stands:** test copy ready by February 12,
2027; club testing from February 15; rehearsal March 12–25; freeze from March
26; no real event before the April sale. (Was Q9.)

**D17 — 2026-11-14 — One current event at a time.** No overlapping events.

**D18 — 2026-11-14 — Assume product lists of about forty items or fewer.** The
checker's screen stays as it is; add search only if a real event's list turns
out longer.

**D19 — 2026-11-14 — Past events' orders are kept and exportable, and "Clear
Records" is removed from the admin console.**

**D20 — 2026-11-14 — Product lists are loaded and saved as spreadsheet (CSV)
files,** and each event's export carries the product list that event used.
Catalogs are not stored per event inside the app.

**D21 — 2026-11-14 — "Cancel Order" replaces "Delete Order" on the cashier's
screen.** Volunteers can no longer permanently delete an order.

**D22 — 2026-11-14 — A cancelled order has a single "Restore order" button**
that puts it back in the unpaid list.

**D23 — 2026-11-14 — Approved before the April sale:** R15 (layer changes
deploy), R2 (voucher cap), R3 (trim names), R4 (paid-at time), R6 (rehearsal),
R7 (the passphrase-off toggle).

**D24 — 2026-11-14 — Approved if time allows, cut-off February 12, 2027:** R8
(unpaid age), R9 (readable export), R10 (starting stock), R11 (vendor tag), R12
(one copy of shared code). Anything not on the test copy by the cut-off waits
until after the sale.

**D25 — 2026-11-14 — Build order:** (1) test copy and safe deploys, starting
with a Terraform plan on every pull request; (2) layer changes deploy, then one
copy of the shared code; (3) cancel an order, then voucher cap, name trimming,
paid-at; (4) events and product import; (5) the passphrase toggle, unpaid age,
readable export, starting stock, vendor tag; (6) rehearsal in March.

## Assumed, not asked

Small choices the agent made under D11 rather than put to the architect. They
are not decisions; strike or change any of them.

- The test copy has its own admin password and staff passphrase, separate from
  production, and shows a "TEST" bar on every screen.
- Whether the 14-day freeze shrinks is decided after the first sale run on the
  new deploy process.
- Discounts and payment methods stay as single lists the organizer edits
  before each event; they are not per event.
- The app keeps its name and logo for every event, with the event's name
  shown under it.
- An order can be cancelled only while unpaid.
- The customer's receipt page says "Cancelled" for a cancelled order.
- Orders get a database index on their event from the start, so one event's
  screens never read another event's orders.

## Open questions

None.
