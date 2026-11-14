# PlantPass — how it is built

A map, not a manual. It tells you where to look and what will bite you. When
this file and the code disagree, the code is right; fix this file.

## The two repos

Check them out side by side under one folder and start agents from that folder.

```
plantpass/                     workspace folder (not a repo)
├── plantpass-backend/         Python Lambdas + all Terraform + the agent kit
│   ├── lambda/<Name>Handler/  one folder per Lambda
│   ├── lambda/layers/python/shared_utils/   shared layer (validation lives here)
│   ├── lambda/tests/          pytest
│   ├── terraform/             every AWS resource, including the frontend's bucket and CDN
│   ├── docs/                  product brief, roadmap, decisions, specs
│   └── .agents/skills/        skills for both repos
└── plantpass-frontend/        React 19 + TypeScript + Vite + MUI
    ├── src/components/core/   OrderEntry, OrderLookup: the sale-day screens
    ├── src/components/AdminConsole/
    ├── src/api/               one small file per API call, through apiClient.ts (three older files call fetch directly)
    ├── src/types/index.ts     API shapes, mirrored by hand from the backend
    └── tests/                 vitest + Testing Library
```

## Request path

Browser → CloudFront (`hortclubplantpass.org`) → S3 static site. The site reads
`/config.js` at load for the API and WebSocket URLs. API calls go to API
Gateway (HTTP API) → one Lambda per resource → DynamoDB. A WebSocket API pushes
"transaction changed" events to open screens.

## API routes

`terraform/apigateway.tf` is the source of truth. The READMEs' route lists are
out of date.

| Route | Lambda | Who may call |
|---|---|---|
| `POST /transactions` | TransactionHandler | staff or admin token |
| `GET /transactions/{purchase_id}` | TransactionHandler | **public** (customer receipt lookup) |
| `PUT /transactions/{purchase_id}` | TransactionHandler | staff or admin token |
| `DELETE /transactions/{purchase_id}` | TransactionHandler | staff or admin token |
| `GET /transactions/recent-unpaid` | TransactionHandler | staff or admin token |
| `GET /transactions/sales-analytics` | TransactionHandler | staff or admin token |
| `GET /transactions/export-data` | TransactionHandler | admin |
| `DELETE /transactions/clear-all` | TransactionHandler | admin. **Deletes every order.** |
| `GET /products`, `/discounts`, `/payment-methods`, `/feature-toggles` | one handler each | **public** |
| `PUT` on those four | same | admin |
| `GET/PUT /lock/{resourceType}` | LockHandler | admin |
| `GET/PUT /plantpass-access` | PlantPassAccessHandler | admin |
| `POST /plantpass-access/verify` | PlantPassAccessHandler | **public**; returns a 24h staff token |
| `POST /admin/login`, `/admin/forgot-password` | AdminAuthHandler | **public**; login returns a 24h admin token |
| `POST /admin/change-password`, `/admin/reset-password` | AdminAuthHandler | see handler |
| none | EmailHandler | no API route, on purpose: it does no authentication. TransactionHandler and AdminAuthHandler invoke it directly. |
| `POST /products`, `PUT`/`DELETE /products/{SKU}`, and the same three for `/discounts` | ProductsHandler, DiscountsHandler | routed in Terraform but not implemented: the handlers answer 404. The frontend saves whole lists with `PUT`. |

Which routes are public is decided by `is_public_endpoint()` in
`auth_middleware.py`. Tokens are HS256 JWTs carrying `role: staff | admin`.

## The order record

Table `transactions`, key `purchase_id` (`ABC-DEF`, six random letters). Built
in `lambda/TransactionHandler/transaction.py`.

```
purchase_id      "ABC-DEF"
timestamp        epoch seconds, set when the order is CREATED (there is no paid-at time)
items            [{SKU, item, quantity, price_ea}]   price is copied in at creation
discounts        [{name, type: "percent"|"dollar", value, amount_off}]
club_voucher     number
customer_email   string, may be ""
payment          {method: "", paid: false}
payment_status   "unpaid" | "paid"    duplicate of payment.paid, exists for the index
receipt          {subtotal, discount, total}   total = max(subtotal - discount, 0)
```

Things to know:

- The create request uses `voucher` and `email`; the stored record uses
  `club_voucher` and `customer_email`.
- Updating an order keeps each item's original name and price. A price change
  in the admin console does not reprice existing unpaid orders.
- There are only two states. "Cancelled" does not exist; a cancelled order is
  either deleted (gone) or left unpaid.
- `receipt.discount` is not capped at the subtotal, only `receipt.total` is.
- Index `payment-status-timestamp-index` serves the cashier's recent-unpaid
  list. Analytics, export and clear-all scan the whole table; fine at 700 rows.

Other tables: `products` (key `SKU`), `discounts` (key `name`),
`payment_methods` (key `name`), `PlantPass-FeatureToggles`, `PlantPass-Locks`,
`PlantPass-Access`, `temp_passwords` (TTL), `websocket_connections` (TTL).
Products, discounts and payment methods are saved by replacing the whole list.

Feature toggles (`FeatureTogglesHandler`): `collectEmailAddresses`,
`passwordProtectAdmin`, `protectPlantPassAccess`.

## Environments

There is one: production. No staging, no local backend.

- `plantpass-frontend/public/config.js` points the local dev server at the
  **production API**. `npm run dev` plus "Enter Order" writes a real order into
  the real sale data.
- Unit tests in both repos mock the network and the database. Nothing local
  exercises a Lambda against DynamoDB or the UI against a real API.

## Deploy

Merging to `main` deploys. There is no other step and no approval gate in CI.

- **Backend** (`.github/workflows/deploy-backend.yaml`): pytest → build the two
  layers and zip each handler's `*.py` → `terraform apply -auto-approve`. State
  is in S3. Never run `terraform apply` from a laptop.
- **Frontend** (`.github/workflows/deploy-frontend.yaml`): lint + vitest →
  `npm run build` → write `dist/config.js` from repo secrets → `aws s3 sync
  --delete` → CloudFront invalidation.
- When a change spans both, ship the backend first and keep it compatible with
  the frontend that is already live.

## Adding things

**A route on an existing Lambda:** route in `terraform/apigateway.tf`; branch
in that handler's `lambda_handler.py`; if public, add it to
`is_public_endpoint()` in every copy of `auth_middleware.py` (see below); a
file in `plantpass-frontend/src/api/`; the type in `src/types/index.ts`.

**A new Lambda** also needs: function, log group and permission in
`terraform/lambda.tf`; a zip-path variable in `terraform/variables.tf`; a zip
line **and** a `-var` line in `deploy-backend.yaml`. Miss the workflow lines
and the deploy fails after merge.

**A field on the order:** `transaction.py` (`_initialize_from_json`,
`_initialize_from_db` with a default for old records, `to_dict`); validation in
`layers/python/shared_utils/validation.py`; `csv_export.py` if it belongs in
the export; `src/types/index.ts`; `tests/types/contract-validation.test.ts`.

## Traps

1. **Shared helpers are copied, not imported.** `auth_middleware.py` exists in
   nine places (seven of the ten handlers, `lambda/shared/`, the layer) and
   `decimal_utils.py` in six (four handlers, `lambda/shared/`, the layer). Handlers import their local copy. A fix made in
   one copy silently does nothing in the others. `tests/test_shared_copies.py`
   fails if the copies drift. `response_utils.py` and `dynamodb_client.py` have
   real per-handler differences; read before you "fix" them.
2. **`lambda/shared/` is only used by the tests.** Nothing deployed reads it.
3. **Every handler's entry file is called `lambda_handler.py`** and uses flat
   imports. Tests juggle `sys.path` and `sys.modules` to load one at a time;
   copy the pattern in `tests/test_products_handler.py`. This is why
   `tests/test_transaction_handler.py.skip` is switched off.
4. **Money is computed in floats** in `transaction.py` and converted to
   Decimal on the way into DynamoDB. Percent discounts can produce long
   fractions; round deliberately when you touch this.
5. **Lambdas run Python 3.11.** Local virtualenvs may be newer. Do not use
   syntax or stdlib newer than 3.11.
6. **Staff access with the passphrase turned off.** With
   `protectPlantPassAccess` off the frontend skips the passphrase prompt, so
   the device never receives a staff token, yet every staff route requires one.
   Read from the code and one unauthenticated request; not yet reproduced in
   the UI. Treat "passphrase off" as untested.
7. **`DELETE /transactions/clear-all` and the admin console's "Clear Records"
   wipe the sale.** Point-in-time recovery is on for the table, but nobody has
   practised a restore.
8. **Product and discount names are identifiers.** Orders match discounts by
   name and items by SKU. Renaming mid-sale orphans the old name on unpaid
   orders.
