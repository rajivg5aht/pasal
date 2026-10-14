# Development experiment and verification log

Date: 11 October 2026. All entries are actual executed checks unless explicitly
marked pending. No final test CSV was opened or scored. Historical result files
were retained. Runtime/dependency versions and input hashes are in the audit JSON.

## D01: audit of existing artifacts

Command: `python recommendation-engine/evaluation/audit_existing_artifacts.py
--output docs/audit-2026-10-11.json` using the existing `.venv`.

Verified unique content IDs, row counts, finite/zero-row checks, exact
reconstruction for 32 rows per TF-IDF model, training popularity aggregation,
CF matrix structure, raw metadata dates and train/validation ordering/proportions.
All nine fingerprinted original inputs were rehashed after implementation and
remained unchanged. Structural checks do not establish final recommendation
effectiveness or temporal validity of the old artifacts.

## D02: corrected content representation diagnostic

Command: `python recommendation-engine/evaluation/evaluate_content_comparison.py
--output-dir data/processed/audit-content-comparison-2026-10-11 --max-users 100`.

K=10, seed=42, latest 20 distinct training items by last timestamp, full seen-item
exclusion, deterministic score/item-ID ordering. The same 100 sampled eligible
validation users were evaluated by all three models. All received recommendations.
The union catalogue denominator was 458,477. Existing models/splits were reused.

| Model | Precision@10 | Recall@10 | NDCG@10 | Unique recommended items |
|---|---:|---:|---:|---:|
| Popularity | 0.001000 | 0.0002040816 | 0.0007336392 | 12 |
| Original content | 0.001000 | 0.0050000000 | 0.0018457570 | 827 |
| Property-enhanced content | 0.005000 | 0.0216666667 | 0.0171671839 | 1000 |

These are descriptive development scores only. The sample excludes zero-history
users; metadata eligibility is not time-aware in these legacy models. No
significance, GenAI benefit, H1/H2 support or final model ranking is claimed.
Corrected histories can change eligibility, so this is not a controlled
before/after quality improvement estimate. Later source changes add source hashes
and runtime versions to future comparison manifests; this run predates that
manifest-only addition.

## D03: point-in-time development metadata subset

Command: `python recommendation-engine/preprocessing/build_metadata_snapshot.py
--cutoff-ms 1438968231028 --output-dir
data/processed/metadata-snapshot-development-2026-10-11 --max-items 50 --seed 42`.

- 20,275,902 source property rows processed.
- 10,865,305 selected-property observations before the cutoff processed.
- 411,732 eligible metadata item IDs in the snapshot.
- 50 items selected without interaction/validation relevance information.
- 50 records exported; no schema exclusions or conflicting latest values.
- Post-run database check: zero facts at/after the exclusive cutoff.
- Source hashes and selection rules saved in
  `metadata-snapshot-development-manifest.json`; the SQLite/JSONL artifacts remain
  local under ignored `data/processed/`.

The cutoff derives from the existing legacy training period solely for
development. This is not approval of the final split, not final candidate
availability filtering, and not a representative Nepalese product catalogue.

## D04: GenAI integration dry run and paired fallback export

The 50 exported catalogue records passed `genai/enrichment.py` without `--live`.
No API credentials, external calls or generated outputs were used. A paired
feature export to `data/processed/genai-integration-dry-run-2026-10-11/` reports
zero API records, zero approved generations and 50 fallback items. Byte comparison
confirms the two feature CSVs are identical. This verifies honest fallback
behavior; it provides no evidence about actual GenAI quality or effectiveness.

## D05: regression and environment verification

`python -m unittest discover -s recommendation-engine/tests -v`: **27 tests pass**.
Coverage includes metric arithmetic, recency, full seen filtering, deterministic
ranking, invalid artifact IDs, category popularity, temporal metadata conflicts,
API payload privacy, cache identity, request budget blocking, provider refusals,
reviewed feature inclusion and absent-generation fallback. Provider responses in
tests are mocked fixtures in temporary directories, never research observations.

`python -m compileall -q recommendation-engine`, `python -m pip check` and
`git diff --check` completed successfully (Git reports only a line-ending notice).
Fresh-environment installation, live API access and full application testing are
not yet verified.

## Pending research runs

Common seven-configuration cohort/density evaluation; validation tuning and
sensitivity; genuine GenAI grounding/quality/cost assessment; equivalent
switching ablation; uncertainty and statistical comparisons; service load/latency;
privacy/fairness audit; final frozen-test evaluation after supervisor decisions.

## D06 — common evaluator development diagnostic (12 October 2026)

Command: `.venv/Scripts/python.exe recommendation-engine/evaluation/run_popularity_diagnostic.py --output data/processed/common-popularity-2026-10-12`.
Seed 42; 1,000 users selected independently of model coverage. Cohorts:
926 zero-history, 57 with 1-4 events, 14 with 5-19, 3 with 20+.
All served; zero failures; 9 users have no novel-item targets and remain in the
headline denominator. Popularity Precision@10 0.0003, Recall@10 0.00183333,
NDCG@10 0.00132908, MAP@10 0.00109583, HitRate@10 0.003.
These are legacy-split smoke results, not final H1/H2 evidence. Training-observed
candidates only; no metadata availability filter. In-process scorer latency
excludes candidate preparation and is NOT API/system latency. Outputs and hashes
are local in the named directory; final test data was not opened.
Verification: 37 unittest checks passed, including five new common-evaluator
checks and five free-provider/explanation checks. All generation calls in those
tests are mocked; no actual GenAI output exists yet.

## D07 — versioned event-count development split

`build_event_count_development.py --output data/splits/event-count-v1` completed.
Actual counts: training 1,929,270; validation 413,415; planned test 413,416.
No boundary ties changed event proportions. Training and validation are sorted.
The 47,040 previously exposed test events are recorded. Test outcomes were not
materialized or evaluated. Original split hashes match the earlier audit.
A tracked copy of the provenance is `docs/event-count-development-manifest.json`.

## Implementation verification checkpoint

44 unit tests pass after adding temporal content training and switching policy
checks. Switching thresholds in fixtures are examples, not tuned parameters.
Dissertation methods drafting is underway. Local scoring diagnostics do not
measure server load or end-to-end API latency. No paid usage or live generation.

## D08 — full historical metadata and content rebuild

`build_metadata_snapshot.py --cutoff-ms 1438558255147 --output-dir data/processed/metadata-event-count-v1`
completed over 20,275,902 source rows: 411,732 exported items, zero latest-value
conflicts and zero schema exclusions. SQL verification found zero facts at/after
the cutoff. The maximum stored timestamp was 1438484400000.
`models/content/train_snapshot.py --catalogue data/processed/metadata-event-count-v1/catalogue.jsonl --output data/processed/content-event-count-v1 --cutoff-ms 1438558255147`
completed: 411,732 rows, 100,000 features, 4,903,232 nonzeros, 24 empty rows.
Availability: 58,189 available, 351,820 unavailable, 1,723 unknown.
Availability must be applied consistently to ALL algorithms at evaluation time;
empty vectors must be retained in coverage/fallback reporting. These are ordinary
property features, not GenAI. Tracked manifests hold exact hashes.

## D09 — genuine generation pilot attempt, no successful generation

A one-item pilot was selected by reservoir sampling (Python Random seed 42) from
all snapshot items before examining outcomes: item 460256. The sample is for
integration only, not a representative effectiveness experiment. The user
configured a Groq Free account locally. The first attempt failed with a network
ConnectionError, produced no text, and is retained in the cache/quota ledger.
Automatic approval review rejected an escalated external metadata transfer;
explicit approval was requested. No bypass or successful generation occurred.
The pilot item is marked unavailable, which does not prevent a catalogue-only
integration test but excludes it from available-item recommendations.

## D10 — corrected temporal baseline diagnostic

Run: `run_popularity_diagnostic.py --train data/splits/event-count-v1/train.csv --validation data/splits/event-count-v1/validation.csv --content-dir data/processed/content-event-count-v1 --output data/processed/temporal-baselines-2026-10-12 --max-users 1000`.
All three models share 1,000 users (917/63/17/3 in the four cohorts), candidate availability and seen exclusions. Twelve targetless users retained; zero model failures.
- category_popularity: served 1000; Precision@10=0.00090000; Recall@10=0.00733333; NDCG@10=0.00508460.
- global_popularity: served 1000; Precision@10=0.00050000; Recall@10=0.00450000; NDCG@10=0.00299127.
- tfidf: served 76; Precision@10=0.00080000; Recall@10=0.00269048; NDCG@10=0.00127745.

This is development-only, with very small warm cohorts; not hypothesis testing. Unknown availability is admitted, explicit unavailable items excluded. TF-IDF has no zero-history fallback by design; switching will provide the appropriate route. Final test untouched. All 45 tests pass.

## D11 — approved genuine Groq Free pilot succeeds

After explicit user authorization of the external catalogue-only transfer, the
failed sandbox attempt was archived and one request succeeded. Model:
`openai/gpt-oss-20b`; 553 input / 454 output tokens, including 349 reported
reasoning tokens. Observed client latency: 1,168.122 ms. Provider headers report
1,000 requests/day and 8,000 tokens/minute limits. No paid tier or fallback used.

The description preserves category 1244 and available=0 and states semantic
product details are unavailable. The assistant performed a source comparison;
this is NOT independent human rating or evidence of the proposal's quality targets.
One review tied to the exact output hash was recorded locally. The paired feature
export reports one genuine approved item, zero fallback items. The sample item
is unavailable and is not served as an available recommendation. No ranking
benefit is asserted. Evidence summary: `docs/genai-pilot-evidence.json`.

The original network failure remains archived. The successful API response,
review and paired features remain under ignored local data paths. No credentials,
raw catalogue payload or generated full response were committed to GitHub.

## D12 — full collaborative model and development tuning

The temporal CF model uses all 978,921 training users, 1,496,559 unique user-item
pairs and 200,975 items. Binary distinct-user cosine, top 50 neighbours, excludes
the diagonal and resolves ties by item ID. The retained graph has 2,589,203 edges;
72,423 items have no neighbours. See cf-event-count-manifest.json for provenance.

Validation sampling uses seed 42 and 100 users per history cohort. Half of each
cohort is assigned to tuning and half to disjoint assessment (200 each). Fixed
hybrid searches a 0.25-step simplex; switching searches prespecified history,
confidence and CF-blend grids. Objective: equal mean NDCG@10 across nonzero-history
tuning cohorts. Selection and summary are tracked in validation-tuning-*.json.
Selected fixed weights: content .75, CF .25, popularity 0. Switching thresholds:
2/10 events, confidence .25 and CF blend .25. These are not a final test freeze.

Assessment NDCG@10: category popularity .0169822; fixed hybrid .0150444;
switching .0138460; TF-IDF .0126633; global popularity .0081102; CF .0045403.
The category baseline exceeds switching. Equal stratification is not population
weighting; this diagnostic cannot establish hypothesis support. GenAI was not
included. The final test remains unopened for evaluation.

## D13 — connected application and MongoDB verification

On October 12 the existing local MongoDB was reused because it already owned
port 27017. Import completed for 411,732 historical catalogue records. FastAPI,
Express and React were run together. Browser checks retrieved item 16 (category
333), verified details and guest basket-to-login transition, and inspected desktop
and 390x844 mobile layouts; mobile DOM width did not exceed viewport width.
Screenshot: screenshots/storefront-desktop.jpg.

Four backend tests passed, including 20 concurrent consented event updates,
opt-out rejecting further updates and clearing history, and preserving a wishlist
through reset. The integration test used its own UUID-named database and removed
only that database. Three frontend tests passed and TypeScript/production build
passed. These are engineering checks, not a complete usability, accessibility,
security or performance study. Browser authentication was not exercised with an
account; authentication was verified through backend HTTP tests.

## D14 — local service load diagnostic and scoring optimization

Two bounded runs used identical synthetic anonymous/one-event/25-event profiles,
three warm-ups and 30 requests at each concurrency (1, 2, 4). The endpoint is
localhost FastAPI only; no accounts or database writes. Baseline successful P95
was 353.6/670.6/660.2 ms. Scoring was changed to calculate only components needed
by the chosen switching route; fixtures verify identical ranks across all routes
and fallback cases. The repeat measured 187.3/313.7/413.1 ms successful P95.
At concurrency 1, successful throughput rose from 4.06 to 10.63 requests/second.

Both runs served 30/30 at concurrency 1 and 2. At concurrency 4, capacity admission
returned HTTP 503 for 19/30 before and 12/30 after. These are reported failures,
not hidden from denominators or counted as successful throughput. Sampled service
RSS peaked around 417 MB before and 411 MB after (decimal units). Full phase data
are in service-load-diagnostic-v1.json and v2.json.

These small sequential development measurements ran alongside background work;
they are not controlled final performance evidence or proof of the proposal's
latency target under load. Browser, Express and database latency are excluded.
The interrupted prior service processes were restarted; the existing MongoDB and
its catalogue were preserved. Requirements encoding was also repaired: 122 pins
now use UTF-8, parse correctly, match installed packages and pass pip check.

## D15 — complete 32-item genuine generation sample

All 32 prespecified items were attempted on Groq Free without retries or
replacements: 24 schema-valid outputs, eight failed/rejected requests. Schema
success was 75%, Wilson 95% interval 57.9–86.7%; this is API reliability, not
factual consistency. Seven failures have HTTP 400 recorded; six additionally
identify json_validate_failed. The earliest failure retained exception class only.
Reported usage totals 11,099 input and 11,785 output tokens; all eight failures
lack usage, so these totals are lower bounds. Observed attempt median latency
was 1,675.8 ms and P95 2,274.2 ms. No paid fallback or tier change was used.

The assistant compared all 24 successful outputs against their exact sources:
21 approved, three rejected for unsupported purchasing implications. These are
engineering grounding reviews, not independent human quality ratings. Descriptions
mostly restate anonymous identifiers, and groundedness does not establish usefulness.
See genai-quality-sample-results.json and GENAI_QUALITY_PROTOCOL.md.

## D16 — partial-coverage seventh configuration

The versioned enriched model preserves 411,732 original item rows and 100,000
property columns, appending 145 generated-text columns with fixed .25 weight.
Only 21 rows are enriched (0.0051% of the complete historical catalogue); all
other vectors remain unchanged. Source hashes and exact output-linked reviews
are checked before use. The actual artifact passed four in-process API requests
(anonymous and three synthetic one-event profiles), and reviewed-description
provenance was checked. Those four requests recommended no generated-description
items, which remains explicit in enriched-service-smoke.json.

All seven configurations were evaluated on the same 200 existing validation
assessment users with the previously selected settings. Only one user had a
sample-enriched item in their profile; none received an enriched item and no
switching rankings changed. The paired NDCG difference and bootstrap interval
were zero. This is inadequate treatment exposure, not evidence that full-coverage
GenAI is ineffective or that H2 has been tested conclusively. The final holdout
remains untouched. See paired-genai-quality-results.json and GENAI_RUNBOOK.md.


## D17 - density diagnostic and tuning correction (13 October 2026)

The v1 seven-condition suite completed at 10%, 25%, 50% and 100% training-event
density with 200 fixed assessment users and 100,599 fixed candidate items. All
original artifacts remain. The v1 aggregates and figure are historical development
evidence; they use the earlier fixed-hybrid weights.

The initial tuning objective excluded zero-history users even for fixed-hybrid
weight selection. Because zero popularity weight can leave these users unserved,
this exclusion is inappropriate. The objective now gives equal weight to all
four approved cohorts. A regression fixture demonstrates that cold users can
change selection. The complete Python suite passed all 65 tests.

The same disjoint tuning/assessment partition was rerun in validation-tuning-v2.
Fixed weights changed from (.75 content, .25 CF, 0 popularity) to
(.50 content, .25 CF, .25 popularity). Switching settings remained (low 2, high
10, confidence .25, CF weight .25). No holdout outcomes were opened. Reusing the
assessment sample after a correctness repair is development evidence, not a
newly independent confirmatory experiment.

A new density-evaluation-v2 run uses corrected settings, preserving v1. CF fits
are reused only after matching training fingerprints. Secondary descriptive
analysis holds novelty targets to the original full-history seen set and measures
diversity in unchanged property TF-IDF space; it is explicitly post-hoc and does
not replace the declared primary metrics. Document encoding was normalized to
UTF-8 after finding legacy Windows dash bytes mixed into UTF-8 text.


### D17 completion

The corrected v2 suite completed all four densities and seven conditions (5,600
model/user observations). Fixed-hybrid mean NDCG@10 was .018273, .018603, .026408,
and .021008 at 10%, 25%, 50%, and 100%, respectively. It had the highest observed
mean among the seven conditions at each density. These are development results.
No GenAI ranking changes occurred, and no user combined generated profile content
with the content route. This is inadequate treatment exposure, not GenAI equivalence.

Secondary stable-target, common-space diversity and descriptive paired bootstrap
analyses completed. At full density switching minus fixed hybrid is -.007162
with an unadjusted percentile interval [-.015259, -.001021]. The comparison is
post-hoc, not confirmatory. 54 of 72 switching settings tied for the tuning maximum.
The PNG/PDF figure was visually inspected: labels and legends are readable without
clipping. Aggregate JSON/CSV, figures and sensitivity evidence are versioned in docs.

An independent review packet was prepared with all 24 successful generations,
including the three assistant-rejected outputs. Verified 24 unique anonymous case
labels, blank ratings and absence of approval decisions. Eight generation failures
remain accounted for separately. No human ratings or consent claims were invented.
All three local services returned HTTP 200 on their health/root checks.


## D18 - training-only GenAI exposure and frozen expansion

GENAI_EXPOSURE_PLAN.md was recorded before implementation. The analysis read only
training events, historical catalogue, tuning provenance and existing pilot usage;
validation/test outcomes were not opened. At the chosen policy threshold, 697,327
training users have a content route; 192,010 have an eligible profile item.

| Items | Uniform exposed users | Targeted exposed users | Targeted share | Minimum fresh daily windows |
|---|---:|---:|---:|---:|
| 32 | 33 | 9,105 | 1.306% | 1 |
| 128 | 293 | 20,290 | 2.910% | 3 |
| 256 | 704 | 29,907 | 4.289% | 6 |
| 512 | 1,418 | 43,555 | 6.246% | 11 |

Targeting uses distinct low-history training-user support with item-ID ties.
Uniform selection is a nested seeded permutation, separate from the original
reservoir quality pilot. The chosen 128-item targeted development sample covers
73 known categories, with 464,751 conservatively reserved tokens. It is not a
representative quality study or a prediction of future-user exposure. Generation
failures and rejected outputs will reduce the achievable treatment coverage.

Commit 3f9a3d5 froze the sample before any new requests. Automatic approval review
initially required separate consent for this expanded sample; the user then
explicitly approved the full 128-item catalogue-only transfer. A capped eight-new-
request batch started using existing quota guards, no retries and no paid fallback.
The first full regression run encountered OpenBLAS memory allocation failure;
limiting BLAS threads to one allowed all 69 tests to pass. No model settings changed.

## D19 - anonymous public-API development diagnostic

A bounded read-only diagnostic exercised products, categories and recommendations
through Express, MongoDB and FastAPI. Three warm-ups and 72 measured requests
completed successfully, at concurrency 1, 2 and 4. Each phase contained eight
requests per route. Every recommendation response contained ten unique items
with matching available catalogue records and the anonymous global-popularity
strategy. The additional response-validation regression fixture passed.

Recommendation P95 was 63.6, 54.4 and 84.0 ms; category-list P95 was 197.3 ms at
concurrency one and 234.2 ms at four. The report retains all attempts and returned
counts. This small mixed-route diagnostic excludes browser rendering, authenticated
flows and controlled isolation from background generation. It does not establish
final system targets. See public-api-load-diagnostic-v1.json.


### Follow-up: first targeted batch and category index verification

The first eight targeted generation attempts completed with six schema-valid
outputs and two HTTP 400 failures. All six outputs passed assistant comparison
against their exact historical sources; these are not independent human ratings.
The 128-item sample remains incomplete, with 120 items unattempted. Reported usage
is 3,175 input and 2,865 output tokens; both failures lack usage, so totals are
lower bounds. No failures were retried or replaced. The outputs largely restate
anonymous property identifiers; grounding does not establish practical usefulness.

Query-plan inspection found that category discovery fetched 58,189 product
documents. An additive (available, category) index changed this to 809 index keys
and zero document fetches. The exact category-set hash was unchanged. MongoDB's
809 distinct values include the missing category; the public API continues to
filter that value and return 808 category codes.

In the repeated small public-API diagnostic, category P95 at concurrency one
fell from 197.3 to 5.5 ms. All requests at concurrency one and two succeeded.
At concurrency four, three of eight recommendation requests returned 503 as the
faster mixed workload reached the existing two-request service capacity limit.
The failures remain in public-api-load-diagnostic-v2.json; the index improvement
must not be described as resolving recommendation concurrency. All four backend
tests, including the isolated real MongoDB test, passed after the index addition.

## 13 October: storefront verification and targeted batch 2

- Eight frontend tests pass serially; five backend tests pass with MongoDB tests
  enabled, none skipped. Production build passes. One parallel frontend run ran
  out of memory; serial rerun passed, so retain resource-aware execution.
- All 83 protected research files match the pre-change SHA256 inventory; see
  storefront-research-preservation-after.json.
- Browser verified synthetic mug search/details and same-category links, admin
  login boundary, and actual Research Lab zero-history routing.
- Targeted GenAI sample: two new requests, one valid grounded output and one
  json_validate_failed response. No retries. Cumulative 10 attempted, seven
  assistant-approved, three failed, 118 unattempted. See
  genai-targeted-batch-2-results.json. Human quality ratings are still outstanding.

## 13 October: targeted batch 3 and independent review analysis

- Eight new calls under the approved 128-item sample, existing free quotas and
  original prompt/model: five schema passes, three recorded JSON failures.
- Cumulative: 18 attempted, 110 unattempted, 12 valid, six provider/schema failures,
  nine assistant-approved and three assistant-rejected. No retries or paid fallback.
- Evidence: genai-targeted-batch-3-results.json. Source comparison reasons are in
  ignored local sample reviews.jsonl, tied to exact cached output hashes.
- Implemented immutable-packet validation and per-reviewer descriptive analysis;
  no human ratings entered. Three focused tests and all 73 Python tests pass.
- Full sandbox suite stalled at service tests and was stopped. The permitted local
  service-access rerun passed all 73. No test results are inferred from the stall.
- FINAL_EVALUATION_READINESS.md records unresolved release gates, not a final freeze.

## 13 October: bounded admission and quota pause

- GenAI continuation invoked with a four-request cap; daily reservation guard
  stopped before any new call. Counts remain 18 attempts. No quota bypass.
- Human review deferred by user; confirmed requirements do not constitute ratings.
- Service now permits two active plus two waiting requests, maximum wait 500 ms.
  Overflow/timeout remains 503; successful latency includes queue time.
- All 76 Python tests passed with local service access. Recommender restarted.
- public-api-load-diagnostic-v3.json: 72/72 measured requests valid, including all
  eight recommendation requests at concurrency four; recommendation P95 127.1 ms.
  v2's three concurrency-four 503s remain preserved. Development comparison only.

## 14 October: authenticated shopping checks and targeted batch 4

- Fixed successful-cart-save visibility when subsequent optional activity fails;
  quantity decreases no longer produce add-to-cart events.
- Verified re-login persistence, cross-account isolation, preserved shopping lists
  on history reset and live-session admin role revocation in isolated MongoDB.
- Nine frontend tests, all five backend tests and production build pass.
- Two new requests: 68000 and 69533, both schema-valid and assistant-approved.
  Cumulative 20 attempted, 14 generated, six provider failures, 11 approvals,
  three grounding rejections, 108 unattempted. No retries or paid fallback.
- Evidence: genai-targeted-batch-4-results.json. Human review remains deferred.
