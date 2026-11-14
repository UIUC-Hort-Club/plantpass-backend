---
name: check
description: >
  Run every local verification for PlantPass in both repos and report honestly
  what passed, what failed, and what was not checked. Use for "run the tests",
  "is it green", "check everything", "verify", before any commit or ship, and
  as /check. Changes no code.
argument-hint: "[backend|frontend]"
---

# Check

Run the checks, read the output, report what happened. Never summarise a run
you did not make, and never call something verified that these checks do not
cover.

Paths are relative to the workspace folder that holds both repos.

## Backend

```bash
make -C plantpass-backend check
```

This creates `.venv` on first run, then runs:

| Step | Proves |
|---|---|
| `pytest` in `lambda/` | handler routing, auth middleware, validation, order money math, and that the copied shared helpers are identical |
| `terraform fmt -check` | formatting, which CI would not catch |
| `terraform validate` | the Terraform parses and references resolve. It does **not** show what an apply would change. |

## Frontend

```bash
npm --prefix plantpass-frontend run check
```

Runs `npm test` (ESLint, then vitest with coverage thresholds) and `npm run
build` (TypeScript, then the Vite production build). If `node_modules` is
missing, run `npm --prefix plantpass-frontend ci` first.

## When both repos changed

Compare the order shape by hand: `Transaction.to_dict()` in
`plantpass-backend/lambda/TransactionHandler/transaction.py` against
`Transaction` and `TransactionResponse` in
`plantpass-frontend/src/types/index.ts`. Nothing automated checks that the two
repos agree.

## Report

One line per step with the real counts (for example "pytest: 83 passed"), then:

- **Failed:** the failing test or error, quoted, with file and line.
- **Not checked:** always list these, because no automated check covers them:
  the UI in a browser, Lambdas against real DynamoDB and API Gateway, the
  WebSocket, email sending, and the deploy itself. Add anything you skipped
  and why.

## Seeing a change in the app

The checks above do not open the app. For anything a volunteer or organizer
would see, also run it: `make -C plantpass-backend dev` in one terminal and
`npm --prefix plantpass-frontend run dev` in another, then use the screen you
changed (staff passphrase `dev`; admin login needs no password). Fake data,
nothing saved, production untouched. Say in the report whether you did this.

A failure that was already failing on `origin/main` is still a failure. Say it
was pre-existing and show how you know.
