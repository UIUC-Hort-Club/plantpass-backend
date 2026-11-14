---
name: plan-feature
description: >
  Decide with the architect whether a PlantPass feature should exist, and if
  so write its one-page spec. Use before any feature work, and for "should we
  build X", "plan X", "what's next on the roadmap", "is this worth it",
  "spec this", a roadmap ID such as R1, or /plan-feature. Produces a verdict
  and a spec file. Writes no code.
argument-hint: "[idea or roadmap ID]"
---

# Plan a feature

Your job is to protect a small app from growing. The architect decides; you
bring the evidence and a recommendation. Most ideas should come out of this
smaller than they went in, and some should not come out at all.

Work in ponytail `ultra` mode for this skill: question the request itself.

## 1. Load the ground rules

Read, in the backend repo: `docs/PRODUCT.md`, `docs/ROADMAP.md`,
`docs/DECISIONS.md`. If the idea is already decided, declined, or specced, say
so and stop. Do not reopen a decision without new evidence.

No argument given: list the `proposed` and `approved` roadmap items in order,
recommend the next one with a one-line reason, and ask which to plan.

## 2. Find the evidence

Look for the cost in `docs/reports/`. If it is not there, ask the architect
for the specific sale-day moment. Then read the code the idea touches (query
the graphify graph first if `graphify-out/graph.json` exists) and check what
already exists. Several things the 2026 report asked for were already built.

## 3. Run the filter

Apply the five questions in `PRODUCT.md` in order and stop at the first "no".
Then give exactly one verdict:

- **Build**: passes as asked.
- **Build smaller**: the need is real; a tenth-size version meets it. Say what
  is cut.
- **Not now**: plausible, no evidence yet. Say what would count as evidence.
- **Do not build**: fails the filter. Say which question and why, and name
  what a person, paper, or a spreadsheet does instead.

For anything but Build or Build smaller: propose the one-line entry for the
roadmap's "Not building" or "Ideas" table and stop here.

## 4. Trace the reach

List every place the change must touch in both repos. Use the "Adding things"
checklists in `docs/ARCHITECTURE.md` and check each trap listed there. Always
answer:

- What does an order written before this change look like when read after it?
- Does the frontend that is live today still work against the new backend?
- Does anything change on the checker or cashier screen? Count the additions.

## 5. Write the spec

Copy `docs/specs/TEMPLATE.md` to `docs/specs/<ID>-<slug>.md` and fill it in.
One page. Status `draft`. Put every choice that belongs to the architect (data
model, new state, new dependency, new infrastructure, anything a volunteer
sees) under "Questions for the architect" with your recommendation.

## 6. Hand over and stop

Reply with: the verdict in one line, the smallest version in two or three
sentences, what was left out, and the numbered questions. Then stop. Do not
start building.

When the architect approves: set the spec's status to `approved <date>`, set
the roadmap item to `specced`, and add a `DECISIONS.md` entry for each
architectural answer they gave, in their words. Then tell them `/build-feature
<ID>` is next.
