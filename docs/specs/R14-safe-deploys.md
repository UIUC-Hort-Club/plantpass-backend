# R14 — A test copy of the app, and deploys that are safe while it is in use

Status: approved 2026-11-14
Roadmap item: R14

## Problem and evidence

Decision D9 and question Q7.

- **The club has nowhere to test.** The only running copy is production. With
  D4, production may hold a real event's orders on any day, so "try it on the
  live site, then clear the records" (what the February 2026 test exports
  suggest was done) stops being safe.
- **A merge changes production with no preview.** The backend workflow runs
  `terraform apply -auto-approve` on merge. Nobody, human or agent, sees what
  will be created, changed or destroyed before it happens.
- **Nothing checks the result.** After a deploy the workflow prints three
  values and exits. A broken login would be found by a volunteer.
- **Every deploy touches every Lambda.** The zips are rebuilt each time, so
  Terraform updates all ten functions even when no code changed (the docs-only
  deploy of PR #9 changed ten). One request made seconds after that deploy
  returned 500 and then succeeded on retry. The cause was not confirmed, but a
  deploy during an event should not be able to do that.
- **There is no written way back.** `main` is already guarded by a ruleset in
  both repos ("Guardrail-Master": pull request required, squash only, no force
  push, no deletion), but that ruleset does not require CI to pass, so a red
  pull request can still be merged and deployed.
- In 2026, fixes were merged the day before and the day of the sale.

## What the volunteer sees

Nothing in production. On the test copy, a coloured "TEST — orders here are
not real" bar on every screen, so nobody rings up a real customer there.

## Smallest version

1. **A test copy.** The same Terraform applied a second time with its own
   state and a `-test` suffix on every resource name, served at its own
   address. Production keeps its exact current names: its plan must show no
   changes from this refactor. Idle cost is cents per month (everything is
   pay-per-use).
2. **Merge deploys to the test copy only.** Both repos.
3. **Production is a separate release step:** one workflow, run on a commit
   that is already green on the test copy. An agent may run it under D10; in a
   freeze window only the architect.
4. **Plan before apply.** A pull request that touches `terraform/` shows the
   plan for both copies in the PR. The release step refuses a plan that
   destroys or replaces a table or bucket unless the release was started with
   an explicit override.
5. **Smoke test inside the workflow** after every deploy: site loads, public
   routes answer, a staff route refuses an anonymous caller. On the test copy
   only, also: create an order, pay it, read it back.
6. **Rollback is the same step run on the last good commit.** Written down in
   `ARCHITECTURE.md`. Works because of the standing rule that old orders must
   load in new code and new fields are additive.
7. **A red pull request cannot be merged.** Done 2026-11-14 with the
   architect's go-ahead: "the `test` check must pass" was added to the
   existing "Guardrail-Master" ruleset in both repos. No approvals are
   required, so agent merges under D10 still work.
8. **Pinned build inputs.** The auth layer is built with an unpinned `pip
   install bcrypt PyJWT`, and the Terraform provider versions are not locked.
   Pin both packages, and commit the provider lock file. (Today the unpinned
   layer build has no effect, because layers never redeploy; roadmap R15 fixes
   that and must pin the versions in the same change.)
9. **The frontend deploy refuses a localhost config.** The committed
   `public/config.js` now points at the local dev server, and one workflow
   step overwrites it for production. A guard before the upload
   (`! grep -q localhost dist/config.js`) makes sure a future edit to that
   workflow cannot put the localhost address on every volunteer's phone.

## Left out on purpose

- Gradual rollout (Lambda aliases, canaries) and automatic rollback. One
  maintainer, small traffic: a fast manual rollback is enough until a bad
  release actually hurts an event.
- A separate AWS account for the test copy. Cleaner isolation, more to manage.
- Load tests in CI. The rehearsal (R6) covers this before each sale.
- Copying production data into the test copy. It gets seeded with a sample
  catalog instead.

## Changes

- Data: none. The test copy has its own empty tables.
- API: none.
- Backend files: every `terraform/*.tf` that names a resource (suffix), a
  second backend state key, `variables.tf`; both workflows in
  `.github/workflows/` plus a new release workflow; the email sender is shared.
- Frontend files: `deploy-frontend.yaml` (two targets), a small banner
  component driven by a flag in `config.js`.
- Docs: `ARCHITECTURE.md` (environments, deploy, rollback), the `ship` skill.

## How we know it works

- The refactor's plan against production shows zero changes before anything
  else is merged. This is the one check that must not be skipped.
- A deliberately broken commit is merged to prove the smoke test stops it at
  the test copy.
- A rollback is practised once, on the test copy.
- Cannot be checked before production: the first production release through
  the new workflow. Do it early, in a quiet week, with the architect watching.

## Ship plan

In four small pull requests so each is easy to undo: (1) name suffix with a
no-change production plan, (2) create the test copy, (3) split deploy into
test-on-merge and release-to-production with smoke tests, (4) plan-on-PR and
branch protection. Target: live by mid-December 2026 so the club's testing
window is not squeezed.

## Decided

- A second copy in the same AWS account (D12).
- It starts on the address AWS assigns; the nicer name only if testers want
  it (D13).
- Production release is a deliberate step, not automatic (D14).
- "Tests must pass" is on the `main` ruleset in both repos (D15).
- Assumed, not asked: the test copy has its own admin password and staff
  passphrase; whether the freeze shrinks is decided after the first sale on
  this process.
