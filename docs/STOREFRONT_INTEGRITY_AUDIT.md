# Storefront integrity audit and implementation checklist

All six supplied screenshots reviewed. Existing visual identity is retained.
Screenshot 1: wishlist contains only anonymous names. Screenshot 2: basket correctly
disclaims payment but lacks useful product information. Screenshot 3: numeric
category selection and placeholder cards cannot support ordinary shopping.
Screenshot 4: consent/reset works but native multi-select is cumbersome and a stale
notice is shown. Screenshots 5/6: text search for clothing cannot match item IDs.

The research catalogue contains historical Retailrocket IDs, encoded property
values and category/parent IDs, not verified product titles, brands, photos or
prices. Category hierarchy does not decode category meanings. MongoDB's imported
titles are explicitly generic. No administrator role or demo product collection
exists. Research recommendations use numeric IDs and hydrate those exact records;
they must never hydrate unrelated synthetic products. Existing auth uses scrypt,
persistent sessions, origin checks, rate limits and server-side consent handling.

## Essential implementation (dependency order)

| Work | Files/components | Verification | Effort estimate |
|---|---|---|---|
| Preserve research files | hash inventory of 83 raw/split/model/evaluation files | compare hashes after changes | <1 hour |
| Separate synthetic catalogue and profiles | backend demo models/router, seed script | cross-source rejection, isolated Mongo tests | 3-5 hours |
| Customer shop | new demo React component, existing styles | browse/search/filter/sort/detail/lists/consent tests | 4-6 hours |
| Focused admin | server roles, local role provisioning, protected product CRUD/dashboard | anonymous/customer denied; input validation; actual aggregates | 3-5 hours |
| Research Lab integration | keep existing App and numeric APIs; explicit navigation and strategy trace | original tests and service checks | 1-2 hours |
| Document validity boundary | status, dissertation and operator guide | no synthetic-to-Retailrocket mapping; unchanged hashes | 1-2 hours |

Estimates are effort ranges, not waiting periods. Work proceeds continuously.
Optional simulated checkout, real payments, order logistics and advanced inventory
are deferred. Demo prices/stock/attributes and original vector illustrations are
explicitly synthetic. No external images, brand identities or product claims are
invented for Retailrocket. Administrators can edit only demo records and select
safe bundled illustrations; uploads are deferred to avoid unnecessary attack surface.

The demo shop uses clearly labelled editorial browsing and same-category links,
not an additional research algorithm. The Research Lab continues to run the approved
switching controller on Retailrocket IDs. Separate profile/list collections and
namespaced string demo IDs prevent contamination. There is no public default admin
password; an existing registered account must be promoted by a local operator.
Final research evaluation remains outstanding; this UI work cannot establish H1/H2.

## Verification outcome — 13 October 2026

Implementation above is complete for the bounded prototype. Eight frontend tests,
all five backend tests (including isolated MongoDB integration) and the production
build pass. All 83 protected research hashes match. See PASAL_OPERATOR_GUIDE.md for
operator role provisioning, exact verification scope and remaining limitations.
