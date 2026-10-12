# Internal recommendation service

Run from the repository root with `.venv/Scripts/python.exe recommendation-engine/service/run.py`.
The launcher reads only `RECOMMENDATION_SERVICE_TOKEN` from ignored `.env`.
Use a random token of at least 32 characters shared only with the Express server.
Never expose it in frontend configuration. The server binds to `127.0.0.1:8000`.

The current service requires the versioned content/CF artifacts and
`data/processed/validation-tuning-v1/selected_config.json`. Startup verifies model
hashes, training identity and cutoffs. Missing artifacts fail startup. This is a
validation-selected research model, not a final frozen thesis result.

- `GET /health`: readiness.
- `POST /recommendations`, authenticated with `X-Service-Token`: validated profile
  with `personalization`, raw `event_count`, at most 20 `recent_items` in last-event
  order, full `seen_items`, explicit `selected_categories`, and `k` (1-50).
- Response includes item IDs, strategy reasons, model cutoff, configuration
  status and local scoring latency. It honestly reports `genai_used=false` until
  an enriched model and reviewed explanation store are connected.

Express must construct profiles from authenticated, consent-controlled database
records. This internal service does not replace user authentication or consent
persistence. Opt-out discards both history and preferences. Profiles are not
stored or sent to GenAI. Two scoring calls may run concurrently; excess receives
503. Ingress body-size/rate limits belong at Express as well.

The historical Retailrocket model has no present-day inventory knowledge.
Availability is a historical research constraint, not live commercial stock.
The website must keep demo product claims separate from anonymous research IDs.

Tests use [FastAPI's in-process test client](https://fastapi.tiangolo.com/tutorial/testing/).
On this Windows host, asyncio requires loopback access even for in-process tests;
a restricted sandbox may block its socketpair before requests run.
