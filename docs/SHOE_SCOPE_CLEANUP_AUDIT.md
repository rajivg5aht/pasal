# Shoe storefront and cleanup audit

16 October 2026. User requested a shoe-focused Kathmandu Valley store with real
product records. Approval of the changed thesis title/research scope and a usable
catalogue/image source are awaiting clarification. The existing approved research
design remains unchanged meanwhile.

## Cleanup performed

- Inspected 220 tracked files. No exact duplicate application files found.
- Two verification reports are byte-identical, but both are retained as research
  evidence: `demo-recommender-consent-verification.json` and
  `demo-recommender-live-verification.json`.
- Removed 12 `__pycache__` directories under the recommendation engine after
  verifying absolute paths and that their contents were only regenerable `.pyc`
  files. Git checkpoint before work: `c167bf76af7b876665290a7705cbb6ce10f4837d`.
- Retained the local test database, database-copy evidence, dependencies, virtual
  environment, all original datasets, models, reviews and experiment outputs.
  These are not unnecessary merely because they are ignored by Git.
- No unused dependency or source module has yet been proven safe to remove.

## Defect fixed

Storefront product cards and detail controls previously allowed adding zero-stock
products. They now disable additions when stock is exhausted or the cart already
contains the displayed stock quantity. Quantity input respects the stock bound;
the action also checks it. Removal remains possible. Atomic checkout continues
to validate actual stock on the server because displayed stock can become stale.
Verification: 14 frontend tests passed, including a zero-stock interaction test;
TypeScript and production build passed.

## Shoe catalogue requirements still outstanding

The current schema supports synthetic illustration keys, not verified product
photographs or source provenance. Existing products must not be renamed into
unrelated shoes: their orders and interaction records refer to those identities.
Use new IDs for new shoe records and preserve historical order snapshots.

Before import, retain source URLs and observation dates for product names,
specifications and prices; establish image permissions and exact model/colour
matches. Generic shoe photographs cannot serve as photographs of named models.
Do not claim stock, sale availability or supplier affiliation from a public
listing. Checkout remains an explicitly simulated order flow.

The separate storefront recommender must operate on these new catalogue IDs and
their actual attributes/consented activity. Retailrocket identifiers and frozen
research results must remain separate; no shoe-specific efficacy claim follows
from the anonymous Retailrocket experiment.

The existing final-experiment and dissertation gates remain open. This audit is
not a claim of submission readiness or completion of the shoe catalogue.
