# Shoe storefront implementation

The approved cold-start thesis title and seven Retailrocket configurations remain
unchanged. Kathmandu Valley and shoes define the customer-facing context, as
clarified by the author on 16 October 2026.

1. Source identifiable shoe photographs with documented reuse permission.
2. Add a shared image registry, source credit and honest simulated-offer labels.
3. Insert new shoe IDs without relabelling or deleting existing products/orders.
4. Expand catalogue coverage, implement shoe-specific variants and verify the
   complete shopping journey before retiring legacy synthetic products.
5. Review a defined shoe-metadata GenAI payload and obtain authorization for that
   new external transfer. Existing approval covers only the Retailrocket sample.
6. Finish independent research evaluation and dissertation deliverables.

## First implemented slice

Two source-identified shoe records: black Derby (brand/model unknown) and Adidas
Predator Absolado TRX TF (historical 2007 photograph). Source links, credits,
licences and verification dates are in `catalogue/shoe-images.json`. Image URLs
are allowlisted; arbitrary remote URLs remain unsupported. A photograph cannot
be assigned a different product title through the admin API. Failed image loads
show an explicit unavailable message instead of an unrelated illustration.

The shoe seed script is additive and idempotent: existing records, stock, profiles,
orders and research data are not rewritten. NPR amounts and stock are explicitly
simulated, not scraped or claimed as current Kathmandu offers. These starter
records are not a complete 15–25 product catalogue. Photos are hosted remotely;
offline image availability is not guaranteed. No new external GenAI calls for
shoe data have been made.

The existing recommender consumes these records through the same separate demo
catalogue. No Retailrocket-to-shoe mapping is introduced. Ranking usefulness and
cold-start behaviour for the expanded shoe catalogue require further verification.

Verification: 14 frontend tests and production build passed; all eight backend
tests passed after restarting the preserved local and isolated test MongoDB
instances. Both new shoe records were inserted successfully. The initial attempts
failed because those database processes were stopped; no data reset was used.
No fresh browser walkthrough or remote-photo availability guarantee is claimed.
