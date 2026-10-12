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

## D12 � full collaborative model and development tuning

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

## D13 � connected application and MongoDB verification

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
