---
name: ship
description: >
  Take a built PlantPass change to production: push the branches, open pull
  requests, wait for CI, get an independent review, merge when the merge gate
  is met (which deploys), watch the deploy, and smoke-test. Use for "ship it",
  "deploy", "open the PR", "release R1", /ship. Merging to main deploys to the
  live system; the gate in this skill decides whether an agent may merge or
  must ask the architect.
argument-hint: "<spec ID or branch>"
---

# Ship

In both repos, a merge to `main` is a production deploy. There is no staging
yet (roadmap R14). The backend deploy runs `terraform apply -auto-approve`.
The merge is the irreversible step.

Repos: `UIUC-Hort-Club/plantpass-backend`, `UIUC-Hort-Club/plantpass-frontend`.

## 1. Preconditions

Stop if any is false, and say which.

- A feature has a spec with status `approved`, and what was built matches it.
  Fixes with no behaviour change, docs and tooling need no spec.
- The `check` skill was run on the current commits and is green.
- Work is committed on its branch; the tree is clean.

## 2. Open the pull requests

For each repo that changed, backend first:

```bash
git push -u origin <branch>
gh pr create --base main --title "<plain title>" --body "<body>"
```

The body says: what changes for volunteers (or "nothing"), what changes in the
data or API, how it was tested, what could not be tested, and how to undo it.
Link the spec. For a backend PR that touches `terraform/`, list every resource
you expect the apply to create, change, or destroy; if you expect any destroy
or replacement, put that in the first line.

Then wait for CI: `gh pr checks <number> --watch`. Red CI: fix it on the
branch. Never merge red, and never re-run until it passes without knowing why
it failed.

## 3. The merge gate (decision D10)

The architect's rule: an agent may merge when **a review has been performed,
its verdict is approve, and the net effect against `main` is better.** This is
how to meet each part. If you cannot meet one, ask the architect.

1. **A review has been performed.** Run `ponytail-review` on the pull
   request's whole diff in a fresh agent that did not write the change. Give
   it the diff and the spec, not your opinion of them.
2. **Its verdict is approve.** The review ends `Verdict: Ship.` with no "Must
   fix" open. "Fix 1 and 3 first" is not approve: fix, push, review again.
3. **The net effect against `main` is better.** All of these, stated in
   writing:
   - CI is green on the PR's head commit, and `check` is green locally on the
     same commit.
   - No test was deleted, skipped or loosened and no threshold lowered, unless
     the spec says so.
   - The change does what its spec or description says and nothing else.
   - The pull request's `plan` job matches what you expect: open its summary
     (`gh run view <run-id>` on the "Run Tests" run) and compare it line by
     line with the list in the PR body. A change that should not touch
     infrastructure must plan as "No changes". Anything in the plan you did
     not expect is a stop, not a detail.

Post the review's verdict and the net-effect statement as a comment on the PR
before merging, so the architect can audit every agent merge afterwards.

**Always ask the architect, whatever the review says, when:**

- the date is inside a freeze window (14 days before an event through its last
  day; for the 2027 sale, March 26 – April 11, 2027);
- Terraform would destroy or replace anything that holds data (a DynamoDB
  table, an S3 bucket) or anything customers reach (the API, the CDN, DNS,
  certificates);
- the change alters what a volunteer sees and that is not in an approved spec;
- the reviewer and the author disagree about a finding;
- you cannot say plainly why `main` is better with this change than without.

These five are the agent's reading of "net effect is better", not the
architect's words. The architect can loosen or tighten them in `DECISIONS.md`.

## 4. Merge and watch, one repo at a time

Backend first whenever both changed. Do not start the frontend until the
backend is deployed and smoke-tested.

```bash
gh pr merge <number> --squash --delete-branch      # never --admin
gh run list --workflow "Deploy Backend" --limit 1   # or "Deploy Frontend"
gh run watch <run-id> --exit-status
```

If the deploy run fails, stop. Read the log (`gh run view <run-id>
--log-failed`), report it, and do not merge anything else. A failed Terraform
apply may have partly applied; say so.

## 5. Smoke test

Read-only requests only. The production API URL is in the live site's config,
not in the repo (the committed `config.js` points at the local dev server).
Wait about ten seconds after a backend deploy before the first request: every
deploy updates every Lambda, and a request that lands mid-update can fail once.

```bash
API=$(curl -s https://hortclubplantpass.org/config.js | grep -o "https://[a-z0-9]*\.execute-api[^'/]*")
curl -s -o /dev/null -w "%{http_code}\n" "$API/feature-toggles"        # 200
curl -s "$API/products" | head -c 300                                  # JSON list
curl -s -o /dev/null -w "%{http_code}\n" "$API/transactions/recent-unpaid"   # 401: auth still enforced
curl -s -o /dev/null -w "%{http_code}\n" https://hortclubplantpass.org/      # 200
curl -s https://hortclubplantpass.org/config.js | grep -c execute-api         # 1: the live site still points at production, not localhost
```

Then give the architect the short list of things only a person can check in
the browser for this change (for example: log in, enter one order, cancel it).
Creating or changing orders in production is the architect's call, never
yours.

## 6. If it is wrong

Undo by reverting: `git revert` the merge commit on a new branch, open a PR,
and ship that through the same steps. A revert of a broken release meets the
gate's "net effect" by definition, but still gets a review. Reverting code
does not undo data already written in a new shape; say what was written. Do
not delete data, edit DynamoDB, or run Terraform by hand.

## 7. Close out

Set the spec to `shipped <date>` and the roadmap item to `shipped`. Add a line
to `DECISIONS.md` only if the architect decided something new along the way.
Report what is live, the PR and run links, whether you merged under the gate or
the architect did, the smoke-test results as observed, and what remains
unverified.
