# R14 — A test copy of the app, and deploys that are safe while it is in use

Status: draft
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
- **There is no written way back,** and `main` can be pushed to directly.
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
7. **`main` is protected:** changes arrive by pull request with CI passing.

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

## Questions for the architect

1. **A second copy in the same AWS account, a few cents a month idle. OK?**
   Recommendation: yes.
2. **What address, and who controls DNS?** Recommendation:
   `test.hortclubplantpass.org`. The Terraform mentions certificate validation
   in Cloudflare; if DNS lives there, the architect adds two records by hand.
3. **Should production release be automatic once the test copy passes, or a
   deliberate step?** Recommendation: deliberate. It keeps D10's review gate
   meaningful and lets the club test a version before it goes live.
4. **May the agent turn on branch protection for `main` in both club repos**
   (pull request and passing CI required)? It is a setting on the club's
   GitHub organisation, so it needs an explicit yes.
5. **After this ships, does the 14-day freeze shrink** (for example to the
   event days plus two)? Recommendation: decide after the first sale run on
   the new process.
6. **Do club testers need their own admin password on the test copy?**
   Recommendation: yes, a separate one, shared freely with testers.
