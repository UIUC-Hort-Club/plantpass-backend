# <ID> — <name>

Status: draft | approved YYYY-MM-DD | shipped YYYY-MM-DD | declined YYYY-MM-DD
Roadmap item: <ID or "new">

One page. If it does not fit, the feature is too big; cut it.

## Problem and evidence

What went wrong, for whom, and where that is recorded (report section, sale-day
moment, code reference). No evidence, no spec.

## What the volunteer sees

Which screen changes and how. Count the added fields, buttons and decisions on
the checker and cashier screens. "Nothing" is the best answer.

## Smallest version

What gets built. Plain sentences.

## Left out on purpose

What a fuller version would have, and what would have to happen at a sale for
it to be worth adding.

## Changes

- Data: new or changed fields, and what an order written before this change
  looks like when read after it.
- API: routes and request or response shapes that change. Say whether the old
  frontend keeps working against the new backend.
- Backend files:
- Frontend files:
- Docs: `USAGE.md` if a volunteer or organizer does anything differently.

## How we know it works

- Tests to add (one per risky branch, not coverage).
- How to see it working without a live sale.
- What cannot be checked before production, and who checks it after deploy.

## Ship plan

Order (backend first when both change), what to watch after deploy, and how to
undo it.

## Questions for the architect

Each with a recommendation.
