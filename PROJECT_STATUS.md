# Pasal status and continuation handover

## Current checkpoint — 13 October 2026

Continue in dependency order without calendar waiting. Preserve the approved
seven configurations and existing verified artifacts. Push substantive verified
chunks; do not manufacture commits to reach the project's 60-commit target.

### Completed and verified

- Temporal train/validation and historical metadata rebuild; final holdout deferred.
- Full training-data item-CF and property TF-IDF; six-condition validation tuning.
- Genuine 32-item Groq Free sample complete: 24 schema-valid, eight failed attempts;
  assistant grounding review approved 21 and rejected three. No replacements,
  retries or paid fallback. Independent human quality ratings remain outstanding.
- Seventh configuration trained from actual reviewed generated descriptions.
  All 411,732 rows retained; only 21 enriched. All seven configurations assessed
  on the same 200 validation users. One profile was exposed; no rankings changed.
  This is insufficient exposure for a conclusive GenAI hypothesis assessment.
- React, Express, MongoDB and FastAPI connected; accounts, consent, history reset,
  wishlist and research basket implemented. Historical catalogue imported.
- Recommendations refresh after consented activity is stored. Generated summaries
  have distinct labels and exact review provenance; baseline serving is still the
  default, with explicit optional enriched-artifact configuration.
- Lazy online scoring preserves route rankings. Development single-request P95
  fell from 354 to 187 ms; capacity rejections remain at concurrency four. These
  are local service diagnostics, not final end-to-end performance evidence.
- All 65 Python regression tests pass, including density, diversity and corrected
  tuning fixtures. Four backend tests (including isolated real MongoDB), four
  frontend tests and the production build pass. Requirements encoding repaired;
  all 122 pins match installed versions and pip check passes.
- Dissertation methodology, implementation and measured preliminary findings
  updated. GenAI protocol/runbook and versioned evidence are in docs/.

### In progress

The v1 four-density suite completed. Corrected tuning includes cold users in the
fixed-hybrid objective: weights are .50 content, .25 CF, .25 popularity. Switching
settings are unchanged. The comparison is being rerun in density-evaluation-v2,
reusing verified CF fits and preserving v1. Densities: 10%, 25%, 50%, 100%. Samples are
nested, histories and cohorts recomputed, original cohorts also reported, and
users/candidate universe/settings held fixed. Outputs are versioned under
versioned directories. Do not restart or overwrite a running suite.

### Running locally

Existing Windows MongoDB on 27017 is reused. Recommender: 127.0.0.1:8000;
backend: 127.0.0.1:3000; storefront: http://127.0.0.1:5173. Services were restored
after the interrupted session. Credentials remain only in ignored .env.

### Remaining research and delivery work

1. Expand scientifically justified GenAI coverage within Free limits; improve
   generation reliability in a separately versioned study, retaining failures.
   Anonymous property codes cannot justify invented semantic product facts.
2. Finish density reporting, sensitivity/diversity/statistical analyses, then
   freeze the final protocol before opening holdout outcomes. Disclose the known
   historical validation exposure and report the untouched intersection separately.
3. Independent explanation-quality review/ethics, usability/accessibility testing,
   controlled end-to-end load tests and production deployment verification.
4. Verify literature/citations, finish dissertation results/discussion/limitations,
   and prepare reproducible final artifacts. The thesis is not complete.

## Historical checkpoint retained for audit (11 October)


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
