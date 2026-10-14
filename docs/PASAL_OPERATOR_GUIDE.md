# Pasal local operator guide

## Open the running prototype

- Shop: http://127.0.0.1:5173/
- Retailrocket Research Lab: http://127.0.0.1:5173/#research
- Administrator: http://127.0.0.1:5173/#admin

The shop contains 16 explicitly synthetic products, readable categories, original
vector illustrations and illustrative NPR prices. Search, category filtering,
sorting, product details, wishlist, quantity cart and optional category preferences
operate on these records. Signed-in customers can review checkout, place explicitly
simulated orders, view history and cancel a placed order. No payment is collected
and no real delivery takes place. Use fictional delivery details only.

## Start the current local deployment

The application uses the approved, verified `pasalLocal` replica set at
localhost:27018. The original localhost:27017 database is preserved. Do not run
the application against the old copy after creating new records in the new one.
The ignored root `.env` selects the new URI. To restart locally:

1. Run `backend/scripts/start-local-mongo.ps1` from PowerShell and wait for MongoDB
   to become primary. It opens no visible helper window.
2. From the root, set `OPENBLAS_NUM_THREADS=1`, then run
   `.venv/Scripts/python.exe recommendation-engine/service/run.py`.
3. In `backend`, run `npm start`.
4. In `frontend`, run `npm run dev`.

Copied sessions were deliberately omitted; sign in again with your existing
account. The current compose file is the older standalone configuration,
not the active transaction-ready deployment. See `COMMERCE_DEPLOYMENT.md`.

## Administrator access

Register your own account through the shop. From the backend directory, the local
operator can assign the role to that existing account:

```powershell
node scripts/set-admin.js "YOUR_REGISTERED_EMAIL"
```

Sign in at the administrator URL using that account's existing password. There is
no default administrator password, public role assignment or privileged signup.
The account must be deliberately selected by the operator; none was selected on
the user's behalf. Backend authorization checks the stored role on each request.

Administrators can create and edit synthetic products, set category/subcategory,
select a bundled illustration, and deactivate products. Deactivation preserves
saved references. Inventory controls use expected-stock checks and an audit log.
Order management supports simulated status changes and cancellation with atomic
stock restoration. Remote image uploads, real orders and research artifact editing
are outside this dashboard's scope. Catalogue lists currently return at most 100
products per query; pagination is needed before scaling beyond this small prototype.

The dashboard reports actual demo counts, consented activity and research service
health. Research request metrics are recent observations, capped to the latest
1,000 retained requests with seven-day expiry, not experimental results. No
observations means unknown rather than zero latency or proven reliability.

## How recommendations remain scientifically valid

Demo IDs start with `demo-`. Demo products/profiles/cart/wishlist live in separate
MongoDB collections. The shop's curated/category browsing is explicitly labelled;
it does not call the Retailrocket ranker or claim experimental recommendation quality.

The Research Lab retains numeric Retailrocket IDs and its existing consented
profile API. Express passes that profile to FastAPI's approved switching controller,
which returns research item IDs. Those IDs hydrate only research catalogue records.
The UI exposes the reported strategy, configuration, historical cutoff and routing
information. Anonymous codes are not decoded into invented product identities.

Groq enrichment is an offline, allowlisted, reviewed research pipeline. It does not
send customer profiles to a model and does not create shop product identities.
Live demonstration activity is excluded from frozen experiment files.

## Verification checkpoint: 13 October 2026

- Frontend: eight tests passed with `npm test -- --maxWorkers=1`.
- Backend: five tests passed, none skipped, with `RUN_MONGO_TESTS=1` and
  `node --test --test-concurrency=1`; disposable isolated databases were used.
- Production frontend build passed.
- All 83 protected research artifact hashes matched the before inventory.
- Browser verified readable catalogue, mug search/detail, correct same-category
  links, administrator sign-in boundary and Research Lab navigation. Responsive
  DOM check at width 390 returned a two-column grid without horizontal overflow.
- Authenticated admin creation was tested through the UI component with fixtures
  and through real isolated MongoDB API tests; no live administrator account was
  provisioned or claimed as manually browser-tested.

One concurrent test run exhausted memory; the serial rerun passed. Use serial
tests and `OPENBLAS_NUM_THREADS=1` for Python work on this machine. Final held-out
research evaluation, independent human GenAI review and dissertation completion
remain outstanding; a working shop is not evidence that either hypothesis holds.
