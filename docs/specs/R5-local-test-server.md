# R5 — A safe place to try changes

Status: approved 2026-11-14 (approach decided in D6)
Roadmap item: R5

## Problem and evidence

There was one environment, production. `npm run dev` in the frontend was wired
to the production API, so trying a change meant writing real orders into the
club's data. Every backend test mocked the database, so no test ran a Lambda
against one. An analytics timeout was found and patched on sale day in 2026.

## What the volunteer sees

Nothing. Developer tooling only.

## Smallest version

1. `make dev` in the backend starts one small server on `localhost:8787`. It
   reads the route list from `terraform/apigateway.tf` and hands each request
   to the same `lambda_handler` production runs. DynamoDB and S3 are in-memory
   fakes. Sample products are loaded; nothing is saved between runs.
2. The frontend's committed `public/config.js` points at that server instead of
   production. The deploy workflow already overwrites the file for production.
3. One end-to-end test file takes an order from entry to paid through the real
   handlers, in CI.

## Left out on purpose

- The WebSocket API (live dashboard updates) and email sending. Both are
  skipped locally; add them when a feature needs them.
- Keeping data between runs. A fresh start is the point.
- A hosted copy the club can use. That is R14.

## Changes

- Data, API: none. No deployed code changes.
- Backend files: `scripts/dev_server.py`, `lambda/tests/test_dev_server.py`,
  `Makefile` (`make dev`), `lambda/requirements-test.txt` (bcrypt, which the
  admin handler imports).
- Frontend files: `public/config.js`.
- Docs: `ARCHITECTURE.md` environments, both `AGENTS.md`, the `ship` skill's
  smoke test (it read the production URL from the file that now says
  localhost).

## How we know it works

- The end-to-end tests pass locally and in CI.
- The real UI, driven in a headless browser against the local server, enters
  and pays an order.
- Cannot be checked locally: anything API Gateway, IAM or real DynamoDB does
  differently from the fakes. R14's test copy covers that.

## Ship plan

Frontend first, then backend. The frontend change is safe alone (its dev
config points at a port where nothing listens yet). The backend change is not:
its docs say local development is safe, which is only true once the frontend
no longer points at production. The frontend deploy must still serve the
production URLs afterwards: check the live `config.js` after it deploys. Undo
by reverting either PR; nothing deployed reads the new files.

## Questions for the architect

None. Local staff passphrase is `dev`; local admin login needs no password.
