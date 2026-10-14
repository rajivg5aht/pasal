# Demonstration ordering deployment

The order API requires MongoDB transactions. The current application database at
localhost:27017 is standalone. Checkout fails closed with a clear 503 response;
it never falls back to non-atomic writes. The isolated integration-test replica
set at port 27118 is not the application database and must not be used as one.

## Implemented contract

- Signed-in customers POST `/api/demo/orders` with a UUID key, exact cart lines,
  reviewed total, fictional delivery details and explicit simulation acceptance.
- The server verifies the current cart, derives prices from stored demo products,
  checks active stock and commits order, stock deductions and cart clearing in one
  transaction. Price, stock or cart changes roll back every write.
- Replaying the same customer/key/payload returns the original order. Reusing a key
  with different details returns conflict. Orders snapshot product names/prices.
- Customer history is ownership-filtered. Only a placed order can be cancelled by
  its customer. Administrator transitions are placed → confirmed → dispatched →
  delivered; placed or confirmed may instead become cancelled. Cancellation
  restores stock exactly once in the same transaction. All are simulated states.
- Stock edits require the expected previous stock, and create an audit record.
  Newly created products start at zero stock; administrators explicitly assign
  synthetic quantities. Product edits never overwrite stock.
- Only fictional recipient/area/note are requested, not payment or street-address
  details. No payment is collected, no delivery occurs and no order trains research
  models. Status histories omit internal actor IDs in API responses.

## Proposed local deployment change — requires user approval

Preserve the existing database at port 27017. Create a new single-node replica set
named `pasalLocal` on loopback port 27018 with a persistent local data directory.
Stop the backend briefly so the source application records remain stable. Run
`backend/scripts/copy-local-database.js --confirm-stopped-backend` from `backend`.
The script refuses a nonempty target, copies records and indexes, verifies sorted
BSON fingerprints and counts before/after copying, and records local evidence.
It deliberately excludes sessions, requiring a fresh sign-in. It never drops or
updates the source database and never overwrites an existing target.

After evidence passes, change the local MONGODB_URI to
`mongodb://127.0.0.1:27018/pasal?replicaSet=pasalLocal`, restart the backend and verify
login, research hydration, checkout and administrator status updates. The original
database remains a rollback source. Do not silently switch back after new orders
are created: reconcile new writes first. No raw files, model artifacts or frozen
evaluation files are part of this database operation.

This is a development single-node deployment, not fault-tolerant production
infrastructure. The existing compose file remains unchanged until an approved
deployment path is selected. Docker startup was unavailable in this session;
isolated transaction tests used the installed MongoDB binary instead.
