---
name: build-feature
description: >
  Implement an approved PlantPass spec across the backend and frontend repos,
  with tests, on feature branches. Use for "build R1", "implement the spec",
  "start on <feature>", /build-feature. Requires a spec in docs/specs/ with
  status approved; without one, run plan-feature first.
argument-hint: "<spec ID>"
---

# Build a feature

Build exactly what the approved spec says, in the smallest change that fully
does it. Follow the `ponytail` skill (level `full`) for every line.

## Before writing code

1. Open `docs/specs/<ID>-*.md` in the backend repo. If its status is not
   `approved`, stop and say so. Small fixes with no behaviour change (typo,
   dead code, a failing test) do not need a spec; anything a volunteer or the
   export would notice does.
2. Read `docs/ARCHITECTURE.md`, especially "Traps", and the `AGENTS.md` of
   each repo you will touch.
3. Read the code the spec names, and every caller of anything you will change.
4. In each repo you will touch: `git fetch origin`, confirm the tree is clean,
   then `git switch -c feat/<ID>-<slug> origin/main`. Use the same branch name
   in both repos. If the tree is not clean, stop and ask.

## Build order

1. **Backend first.** Change the handler and its tests together. New logic
   with a branch, money, auth, or a data write gets one test that fails
   without it. Money and order-state changes go in
   `lambda/tests/test_transaction_math.py`.
2. **Keep the live frontend working.** New response fields are fine. Do not
   rename or remove a field, and do not make a new request field required, in
   the same release that introduces it.
3. **Old orders must still load.** Any new field on the order needs a default
   in `Transaction._initialize_from_db`, and a test that reads a record
   without it.
4. **Then the frontend.** Update `src/types/index.ts` and
   `tests/types/contract-validation.test.ts` to match the backend, then the API
   file, then the component. Reuse what `src/components/common/` and MUI
   already give you.
5. **Docs that people read.** If a volunteer or organizer does anything
   differently, update `plantpass-frontend/USAGE.md` in the same change. If
   you changed a route, table, or trap, update `docs/ARCHITECTURE.md`.

## Rules that are easy to break here

- Editing `auth_middleware.py` or `decimal_utils.py`: change every copy
  identically. `tests/test_shared_copies.py` will tell you if you missed one.
- A new Lambda or zip needs lines in `deploy-backend.yaml`. A new environment
  variable needs `terraform/lambda.tf`.
- Never run the frontend dev server and submit a form; it writes to
  production. Never call a non-GET production endpoint.
- Never run `terraform apply`, `plan` with real state, or any AWS write.
- Do not add a dependency for something a few lines or MUI already do. If you
  think one is needed, that is a question for the architect.
- Stay inside the spec. Something else looks broken: note it for the roadmap,
  do not fix it here.

## Finish

1. Run the `check` skill. Fix what it finds; do not weaken a test or a
   threshold to get green.
2. Run `ponytail-review` on the diff in each repo and fix every "Must fix".
3. Commit on the feature branch in small, plainly worded commits. Do not push.
4. Report: what was built, the files touched in each repo, test results as
   run, anything in the spec you could not do, what was not verified (there is
   no end-to-end environment unless roadmap R5 has shipped), and that `/ship
   <ID>` is next.
