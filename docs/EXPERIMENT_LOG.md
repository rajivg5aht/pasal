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
