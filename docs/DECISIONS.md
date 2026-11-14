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

## Open questions

Waiting on the architect. Each has an agent recommendation, not a decision.

**Q7 — Where does the club test?** D6 gives developers and agents a local
server, but club members cannot use something that runs on a laptop, and with
D4 production may be holding a real event's orders at any time. Recommendation:
a hosted test copy of the whole app at its own address, which is also the first
half of safe deploys (D9). Spec: `specs/R14-safe-deploys.md`.

**Q8 — How should events and catalogs work?** Several choices that are the
architect's: whether past events stay in the app or are exported and closed,
how big a non-plant catalog gets, and whether two events can run at once.
Spec: `specs/R13-events-and-catalogs.md`.

**Q9 — When does the club want to start testing, and is there a smaller event
before April that could be the trial run?** Sets the dates in the roadmap.
