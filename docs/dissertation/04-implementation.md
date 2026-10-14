# 4 System implementation

## 4.1 Architecture and data boundaries

Pasal comprises a React/Vite client, an Express application API, MongoDB storage
and a local FastAPI recommendation service. The browser uses the application API
for accounts, preferences, catalogue operations and recommendations. The backend
obtains research rankings from the recommendation service and hydrates identifiers
against the corresponding catalogue. Offline data preparation and evaluation are
separate processes with explicit artifact manifests.

The customer shop contains 16 explicitly synthetic demonstration products with
understandable categories, illustrative artwork and demonstration prices. Its
identifiers and interaction records are separate from Retailrocket. The Research
Lab retains anonymous numeric identifiers and historical properties. There is no
arbitrary mapping from a synthetic product to a research item and no claim that
Retailrocket evaluation validates rankings for unrelated demonstration products.

This boundary resolves a practical presentation problem without inventing facts.
Customers can explore a coherent Kathmandu-oriented shopping prototype while an
examiner can inspect the actual research model and its route explanation. The
synthetic shop does not establish real stock, supplier relationships or fulfilment.

## 4.2 Customer and administrator workflows

The shop supports meaningful text search, category filtering, sorting, product
details, wishlist, cart and preference controls. Stored interactions use the
appropriate catalogue identifiers. Account persistence is exercised through
logout and login checks. Cross-account isolation and history clearing are tested.
Cart updates report their saved state even when optional personalisation activity
recording fails, avoiding an apparent failed save after a successful database write.

Administration is restricted by stored account roles checked on each request.
There is no published default administrator password. An operator promotes an
existing registered account using the documented local command. Revoking that
role removes access without relying on a stale client-side menu state. The
dashboard manages demonstration products and their active status, uses a bounded
set of illustrations, and reports actual stored statistics.

The application is a research prototype. It does not process real payments or
place fulfilment orders. Administrative functions do not edit frozen research
artifacts or relabel anonymous items as known products. These scope decisions
prioritise correctness and demonstrability over unrelated commerce features.

## 4.3 Recommendation serving and resilience

The Research Lab exposes the selected strategy and the evidence used by the
switching controller. Ordinary property matching, collaborative evidence and
popularity remain the approved ranking components. Optional generated text is
identified separately from the locally recorded routing reason. A fluent catalogue
description is not presented as proof of a personalised causal explanation.

Service work is bounded to two active requests and two waiting requests with a
500 ms wait limit. Requests beyond capacity receive a controlled 503 response
with Retry-After rather than consuming unbounded resources. Queue wait is included
in observed latency. Release occurs on both success and failure. Single-threaded
BLAS settings reduce resource contention in this local experimental environment.

## 4.4 Verification and limitations

The recorded October 14 verification includes nine frontend tests, five backend
tests including real MongoDB integration, and a successful production frontend
build. Backend checks cover persistence, isolation, consent reset and live role
revocation. Research code has a separate Python test suite covering temporal
features, history rules, metrics, generation provenance and final evaluation.
Its current exact count belongs in the submission evidence manifest, rather than
being treated as a permanent property of the system.

A research-preservation checkpoint matched hashes for 83 protected raw, split,
model and evaluation files before and after storefront work. This verifies that
specific checkpoint, not every possible future change. A final preservation check
is still required when packaging the submission.

The bounded-capacity public-API diagnostic completed all 72 measured requests.
Recommendation P95 at concurrency four was 127.1 ms. This small local development
workload includes the API path but is not a production load guarantee or evidence
of ranking quality. Its earlier failing run remains recorded, so the improvement
is auditable rather than inferred from only successful runs.
