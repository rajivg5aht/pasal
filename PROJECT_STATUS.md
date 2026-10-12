# Pasal status and continuation handover

Updated 11 October 2026. Baseline commit `dacd4d3`, branch `main`. Commit `4d58fb6`
appeared during this session containing earlier changes; the assistant did not
create it. Subsequent additions remain in the working tree. Reuse the existing
workspace, data and `.venv`.

## Current milestone

Existing baseline implementation audited; initial correctness repairs verified;
GenAI integration and temporal metadata preparation added. **The complete thesis
prototype and final experiments are not finished.**

| Area | Status | Evidence / remaining work |
|---|---|---|
| Proposal/source/artifact review | Completed within documented scope | `docs/PROJECT_AUDIT.md` and audit JSON |
| History, full seen filtering, deterministic ranking | Verified by regression fixtures | Revised content comparison executed for 100 users |
| Existing popularity/content artifacts | Structurally checked; not final research-valid | Exact training popularity; 32 reconstructed vectors/model; temporal limitations |
| Item-CF / fixed hybrid | Partial prototypes | Sampled CF; manually weighted one-user hybrid |
| Snapshot builder | Implemented; fixtures and real-data run pass | 20,275,902 raw rows processed; 50-item development export; final cutoff depends on holdout decision |
| Genuine GenAI adapter/cache/feature export | Implemented; offline contract tests pass | No API access; no actual generated research results yet |
| Category popularity | Implemented; four fixture tests pass | Common final evaluation outstanding |
| Common final evaluator | Not started | Current diagnostic excludes zero-history users |
| Switching / final GenAI ablation | Not started | Figure 5 components pending; live GenAI access needed |
| Frontend / Express / FastAPI / MongoDB | Not started | No application source at audit baseline |
| Cohort/density/sensitivity/final test / dissertation | Outstanding | Follow the frozen approved protocol and four-week plan |

## User decisions received

- Follow the **seven** configurations in the approved methodology; do not add
  user-user CF/BERT4Rec from Figure 11.
- Record Figure 5's ambiguity for supervisor clarification; continue unaffected
  development. Do not change the approved research approach.
- Prepare **both** split/holdout options for supervisor review; do not select one
  or regenerate current splits silently.
- Approximately four weeks remaining, 8 hours/day, 224 total hours. See the
  detailed four-week plan and contingency allocation.
- No API access yet: build and test the integration first. No live API generation
  is authorized/configured in this pass. Actual GenAI enrichment/evaluation
  remains required and cannot be replaced by property processing.

## Changes and evidence

Read all original Python source and the approved proposal before editing source.
Corrected timestamp recency in content scripts, retained full hybrid seen sets,
added deterministic score ties, matrix/ID checks and tested ranking metrics.
The new shared diagnostic refuses to overwrite prior outputs and records
per-user metrics, sample IDs and input hashes.

Added `evaluation/audit_existing_artifacts.py`, `research_utils.py`,
`preprocessing/build_metadata_snapshot.py`, `genai/enrichment.py`,
`genai/build_enriched_features.py`, `models/popularity/category_popularity.py`,
test modules and research documentation. The expanded suite has 27 passing tests.
The GenAI feature export requires reviews keyed to the exact output hash and
preserves identical item populations/base features for paired comparisons.

Existing raw files, splits, matrices, rankings and result CSVs were preserved.
The final test CSV was not read or evaluated. Raw event timestamps were used only
for structural counts/boundaries and the holdout-overlap diagnosis.

Verification commands already run from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s recommendation-engine/tests -v
.\.venv\Scripts\python.exe -m compileall -q recommendation-engine
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe recommendation-engine/evaluation/audit_existing_artifacts.py --output docs/audit-2026-10-11.json
.\.venv\Scripts\python.exe recommendation-engine/evaluation/evaluate_content_comparison.py --output-dir data/processed/audit-content-comparison-2026-10-11 --max-users 100
```

The revised 100-user scores are development diagnostics, not H1/H2 findings.
No new quality claim is justified by changes in sample eligibility or tie rules.
The real-data snapshot and 50-record GenAI dry run completed. Post-run SQL checks
found zero future facts, and paired feature exports were byte-identical with
zero generated descriptions. See `docs/EXPERIMENT_LOG.md` for actual commands,
measurements and limitations.

During development, a NumPy JSON-serialization issue in the audit and SQLite
connection cleanup issue in a Windows fixture were found and repaired. The
audit was rerun successfully; neither failure modified original research inputs.

## Next three priorities

1. User sends `docs/PROPOSAL_CLARIFICATIONS.md` to the supervisor and records the
   holdout and hybrid-branch decisions. No external message has been sent here.
2. Complete shared cohort/candidate evaluation and baseline training on the
   agreed temporal protocol; retain failures and zero-history users.
3. Obtain GenAI provider/model/budget, run a small genuine enrichment pilot,
   review grounding and prepare the matching no-GenAI/GenAI experiment.

Read the audit, traceability and plan before continuing. Do not restart the
project, redownload data, delete metadata-only items for lacking interactions,
claim the proposal's targets are achieved, or label fixture output as research
evidence. Website integration and dissertation drafting can proceed alongside
research once their corresponding milestones are reached.
