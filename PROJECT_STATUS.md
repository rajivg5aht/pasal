# Pasal status and continuation handover

## Current checkpoint — 12 October 2026

Execute continuously in dependency order, without waiting for calendar weeks.
Preserve the approved seven configurations. Push small verified commits; the
60-commit goal must reflect substantive work, not artificial splitting.

### Verified work

- Approved-methodology ambiguities and holdout exposure decisions documented.
- Event-count train/validation split rebuilt; final test remains deferred.
- Historical metadata: 411,732 items, zero future facts; TF-IDF trained on this
  snapshot with 100,000 features. Original artifacts preserved.
- Full item-CF: 978,921 training users, 200,975 items and 2,589,203 retained
  neighbours. Training hash/cutoff checks protect artifact loading.
- Shared engine serves six non-GenAI configurations with common eligibility,
  complete seen-item exclusion and explicit switching reasons.
- Validation tuning completed on 200 users, assessed on 200 disjoint users,
  stratified equally by history cohort. This is a development diagnostic.
  Category popularity outperformed switching on assessment NDCG@10; no
  superiority claim is justified. See the experiment log and tuning evidence.
- Genuine Groq Free one-item pilot succeeded (553 input / 454 output tokens).
  It is integration evidence, not independent quality or ranking evidence.
- FastAPI, Express sessions, MongoDB catalogue and React storefront connected.
  Imported 411,732 historical catalogue records; browsing shows available items.
  Accounts, optional personalization, history reset, wishlist and research basket
  implemented. No payments, actual orders or current stock claims.
- Tests: 54 Python tests (previous checkpoint), four backend tests including real
  MongoDB concurrent updates/opt-out, three frontend tests; frontend production
  build passed. Browser verified real search, details, guest sign-in transition
  and responsive desktop/mobile layout. See frontend/README.md.

### Running locally

The existing Windows MongoDB service owns port 27017 and is reused. Docker is
running, but a second MongoDB container cannot bind that occupied port; do not
stop the existing database. Recommender: 127.0.0.1:8000; backend: 127.0.0.1:3000;
storefront: http://127.0.0.1:5173. See component READMEs for restart instructions.
Secrets remain in ignored .env. Catalogue-only transfer to Groq Free is approved.

### Next priorities and remaining work

1. Prespecify a representative eligible GenAI enrichment sample, generate within
   Free limits, document grounding review and uncertainty, and train the paired
   seventh condition. Current online reasons are local templates, not GenAI text.
2. Complete cohort/density/sensitivity experiments and paired confidence intervals;
   freeze configuration before final testing, disclose prior validation exposure
   and report the independent untouched intersection separately.
3. Extend end-to-end authentication/privacy, accessibility, usability and system
   performance checks. Production deployment configuration is not yet verified.
4. Continue dissertation implementation/results sections from measured evidence;
   verify literature, independent quality ratings and final limitations.

The project and dissertation are not complete. No final-test effectiveness result
or representative GenAI improvement has been established.

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
