# PlantPass — agent guide

PlantPass is a lightweight checkout app for the UIUC Horticulture Club: at the
plant sale and other club events, volunteers ring up sales on their own phones. This repo
is the backend (Python Lambdas, all Terraform) and the home of the agent kit
for both repos. The frontend is `../plantpass-frontend`.

## How we work here

1. **The architect decides.** Joseph Ku decides what gets built, the data
   model, and when anything ships. You bring evidence and a recommendation,
   then stop and ask. Say once if you disagree, then follow the decision.
2. **Small on purpose.** Every feature goes through the filter in
   `docs/PRODUCT.md` before a line is written. "Do not build" is a good
   outcome. Never add scope the spec does not contain.
3. **Simplest thing that works.** The `ponytail` skill is the house style for
   all code. Use level `ultra` while planning, `full` while building.
4. **Say what you did not check.** There is no staging environment. Be exact
   about what ran and what did not.

## The path a change takes

| Step | Skill | Ends with |
|---|---|---|
| Should it exist? What is the smallest version? | `/plan-feature` | a one-page spec in `docs/specs/`, waiting for approval |
| Build it | `/build-feature` | commits on `feat/...` branches in one or both repos |
| Prove it | `/check` | an honest pass/fail report |
| Review it | `/ponytail-review` | findings to fix |
| Release it | `/ship` | PRs, an independent review, then merge and deploy when the merge gate is met |

Whole-repo health: `/ponytail-audit`. Deferred shortcuts: `/ponytail-debt`.

## Read before you change anything

- `docs/PRODUCT.md`: who uses this, the principles, the filter.
- `docs/ARCHITECTURE.md`: the map, the order record, deploy, and the traps.
- `docs/ROADMAP.md`: what is planned, and what was declined and why.
- `docs/DECISIONS.md`: what the architect has decided. Do not reopen without
  new evidence.

Each repo has its own code graph in `graphify-out/` (not committed). Query it
before grepping, and name the graph when you are not inside that repo:
`graphify explain "Transaction" --graph plantpass-backend/graphify-out/graph.json`
(or `plantpass-frontend/...`). Refresh both with `make -C plantpass-backend
graph`. The graph shows committed structure; read the real file before editing.

## Commands

```bash
make check                 # pytest + terraform fmt + terraform validate (creates .venv on first run)
make test                  # pytest only
cd lambda && ../.venv/bin/python -m pytest tests/test_transaction_math.py -q   # one file
```

Frontend: `npm --prefix ../plantpass-frontend run check`.

## Hard rules

- **Production is the only environment.** Never send a non-GET request to the
  production API. Never run the frontend dev server and submit a form: it is
  wired to production.
- **Never run `terraform apply`, `destroy`, `import`, or `state` commands, or
  any AWS CLI write.** Deploys happen only through GitHub Actions on merge to
  `main`.
- **A merge to `main` is a production deploy.** Only `/ship` merges, and only
  through its merge gate: an independent review that says approve, and a
  written case that `main` is better for it (decision D10). Inside a freeze
  window, or when data-holding infrastructure would be replaced, the architect
  merges.
- **Never clear, delete, or bulk-edit orders.** That data is the club's sale
  record.
- **No secrets in the repo.** Both repos are public.
- Branch from `origin/main` as `feat/<ID>-<slug>` or `fix/<slug>`. Do not push
  to `main`. Do not force-push.

## Backend conventions

- One folder per Lambda under `lambda/`, entry point
  `lambda_handler.lambda_handler`, routed on `event["routeKey"]`.
- Runtime is Python 3.11. No new runtime dependencies without the architect;
  the only packaged ones are `bcrypt` and `PyJWT` (auth layer).
- `auth_middleware.py` and `decimal_utils.py` are copied into each handler.
  Edit every copy identically; `tests/test_shared_copies.py` enforces it.
- Order money and state rules live in `lambda/TransactionHandler/transaction.py`
  and are pinned by `tests/test_transaction_math.py`. Change a rule and its
  test together.
- Records written before your change must still load. Give new fields a
  default in `Transaction._initialize_from_db`.
- A new Lambda, zip, or route needs Terraform **and** workflow changes; follow
  "Adding things" in `docs/ARCHITECTURE.md`.
- A deliberate shortcut gets a comment: `# shortcut: <the limit>, <when to
  upgrade>`.
