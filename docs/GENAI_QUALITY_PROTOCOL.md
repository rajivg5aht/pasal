# Generated catalogue quality protocol

## Prespecified first sample

The 32-item uniform reservoir (seed 42) was frozen in commit 97aef4e before
generation. Its population is the historical catalogue with available != 0,
including unknown availability: 59,912 items. The sample contains 29 explicitly
available and three unknown-availability items across 23 category values. No
training interactions, validation relevance or test outcomes selected these items.
Failed or rejected items are not replaced. This is a feasibility/quality sample;
it is too small to guarantee category-level precision or sufficient ranking exposure.

The request keeps the existing prompt version, temperature 0, GPT-OSS 20B and
800 maximum completion tokens. Catalogue property codes alone leave the machine.
Published Groq Free limits were rechecked on October 12, 2026 at
https://console.groq.com/docs/rate-limits. Local reservations are more conservative.
No paid fallback, tier change or automatic retry is permitted. HTTP 400
json_validate_failed is a failed generation outcome, not a reason to replace an
item. The first two failed requests lack detailed error codes because the adapter
originally retained exception class only; this missingness must remain disclosed.

## Grounding review

For every successful schema-valid response, compare every assertion against the
exact historical source. Record an explicit decision and rationale tied to the
output hash. Approve only descriptions whose category/status/code claims match
the source without inventing product meaning or current retail facts. Reject
claims such as current purchase availability, inferred material, brand, price,
location or product type. Do not edit generated prose to hide a failure.

Assistant review is an engineering grounding screen. It is not independent human
rating or a substitute for approved human-subject evaluation. A description that
only lists correct anonymous identifiers may be grounded but have little practical
relevance. Grounding approval must not be reported as semantic usefulness.

The later human rubric should separately assess factual consistency (supported
assertions / assessable assertions), unsupported claims with severity, clarity,
and relevance to understanding an item. Record unassessable anonymous semantics
explicitly. Reviewers must see the source facts and historical-data limitation;
raters, consent/ethics arrangements, sampling and disagreements must be documented
before claiming independent ratings. No such ratings have been collected here.

## Accounting and analysis

Report all 32 selected items, attempted and unattempted counts, provider/schema
failures, pending reviews, approved and rejected outputs. Wilson intervals around
schema success describe API reliability only. Report missing token usage on failed
responses; observed token totals are lower bounds. Free-account attestation is
not an independently obtained billing statement. Record observed median/P95 API
latency with sample size; these are not end-to-end website load-test results.

For the development ranking ablation, preserve the original property matrix and
append a separate generated-text TF-IDF block at fixed weight .25. Normalize only
treated rows; retain every catalogue item and unchanged eligibility. Keep all
failed, rejected and unreviewed items on exactly the original property vectors.
The weight is a declared development choice, not a test-tuned optimum.

Use the existing disjoint validation assessment users and settings for seven
configurations. Report generated catalogue coverage, profile exposure, generated
items actually recommended and changed rankings. No exposure or an unchanged
ranking is not evidence that useful full-coverage GenAI has been disproved. This
small partial-treatment experiment cannot establish the proposal's final H2.
Final test evaluation still requires a frozen, fully documented protocol.
