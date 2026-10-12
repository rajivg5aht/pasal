# Pasal backend

`npm ci`, then `npm start` from this directory. Requires MongoDB and the local
FastAPI service. Run `docker compose up -d mongo` from the root when Docker is
available, then `node src/import-catalogue.js` here to import the historical
catalogue. Import is repeatable and does not delete user records.

Root ignored `.env` requires `SESSION_SECRET` and `RECOMMENDATION_SERVICE_TOKEN`
(each random, at least 32 characters). Optional: `MONGODB_URI`, `BACKEND_PORT`,
`RECOMMENDATION_SERVICE_URL`, `APP_ORIGIN`. Production cookies require HTTPS.
The development server binds only to localhost. No default passwords or tokens.

Session IDs use HTTP-only same-site cookies with a MongoDB session store.
Passwords use salted scrypt. Mutations require a trusted Origin; authentication
attempts and general requests have separate rate limits. Request errors suppress
private details. Recommendation requests use authenticated server-side profiles,
not a browser-supplied identity. Opt-out atomically clears recommendation history
and category preferences; operational cart/wishlist records remain separate.

Profile writes are single-document atomic MongoDB updates conditional on consent.
Event count counts consented view/cart actions; only the last 20 distinct items
and a full seen set are retained, not raw browsing event logs. This minimizes
stored data but is a documented limitation for detailed event-audit research.
History is capped at 100,000 unique items and lists at 100 items.

The HTTP suite (`npm test`) uses an explicit in-memory test repository and session
store. Production startup always uses MongoDB. Passing HTTP tests alone does not
confirm database integration, which must be tested against a running MongoDB.

Research recommendation eligibility admits unknown historical availability;
the browsing/import layer is stricter and displays only available=1. The API
filters missing/unavailable catalogue cards and may return fewer than ten. Do not
use this UI-filtered list for offline benchmark scores or claim current inventory.
