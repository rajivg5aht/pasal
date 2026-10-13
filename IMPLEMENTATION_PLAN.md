# Pasal: accelerated four-week execution plan

## Execution policy — latest user instruction

Work continuously in dependency order. Week/date allocations below are historical
capacity estimates, not start gates or waiting periods. Start the next ready task
immediately after verification; complete the project as quickly as practical.
The user has superseded deadline-driven scheduling. Preserve the required scope
and research checks. Use short, meaningful commits and frequent small pushes
(approximately every 4-5 minutes when a verified chunk is ready). Aim for at least
60 substantive commits across the project; never pad history or split changes
into broken intermediate states to satisfy a counter. Do not publish credentials,
raw datasets, generated model binaries or unreviewed private files.

Updated 12 October 2026. **Final submission: 8 November 2026 (confirmed).**
Completion target: **5-6 November**; **7 November** is reserved for final
verification, corrections and submission packaging. November 4 is superseded.

## Dependency checkpoint - 13 October 2026

Temporal artifacts, six-model tuning, genuine Free API generation, reviewed
seventh-model integration and the connected website are implemented. All 65 Python
regression tests pass. Density v1 completed; v2 is rerunning after correcting the
fixed-hybrid objective to include zero-history users. Preserve both versions.
The next ready work is to finish that evidence package, expand justified GenAI
exposure, complete independent quality review and controlled end-to-end tests,
then freeze final experiments. Continue dissertation writing alongside each result.
Free API access is configured; the remaining constraint is coverage and quality,
not account setup. The original calendar below is planning history, not a gate.

## Remaining calendar and capacity

The original four-week sequence below is retained. Its original 224-hour budget
included 11 October; from 12 October through 7 November there are **216 hours**
at 8 hours/day. These are available student hours, not elapsed agent work or
guaranteed compute capacity. Use the following remaining allocations:

| Dates | Hours | Required outcome |
|---|---:|---|
| Oct 12-17 | 48 | Document protocol decisions; temporal rebuild; common evaluator; verified baselines; free GenAI integration/pilot; methods draft |
| Oct 18-24 | 56 | Tune fixed hybrid/switching on validation; reviewed GenAI ablation; FastAPI/Express/MongoDB; implementation chapter |
| Oct 25-31 | 56 | Integrated responsive website, privacy controls; seven-configuration/density rehearsal; quality/load tests; results draft |
| Nov 1-4 | 32 | Freeze configurations; final experiments and paired analysis; complete dissertation with actual results |
| Nov 5-6 | 16 | Reproduction, dissertation/reference checks, demonstration and release; resolve defects |
| Nov 7 | 8 | Final verification, corrections, backups and submission preparation |
| Nov 8 | — | Confirmed submission deadline; do not plan development here |

Within each development day, reserve at least one hour for dissertation and
evidence recording. If a milestone slips, reduce cosmetic scope and the declared
representative GenAI subset before cutting required comparisons or validation.
Do not postpone writing until experiments finish. API spend is strictly **$0**.
Free account setup is the only live-generation dependency; unrelated work proceeds.
Research ambiguities are resolved under delegated authority in
`docs/RESEARCH_DECISIONS.md`, which supersedes pending-approval wording below.

## Original allocation retained for planning history

Capacity confirmed by the user: 8 hours/day, 56
hours/week, approximately 224 hours over 28 days. Planning horizon: 11 October
through 7 November; approximate submission date 8 November 2026, to be confirmed
against the university's exact deadline. Aim for a submission-ready release by
day 26, preserving days 27-28 as contingency. This is a capacity plan, not a
guarantee that unresolved research decisions or external access will arrive.

The original approved 12-week schedule remains part of the proposal: approval
week 2, frozen data/baselines week 6, integrated switching/GenAI week 9, final
evaluation/dissertation week 12. The schedule below accelerates execution without
claiming these original milestones were completed.

## Week 1: reliable data, evaluation and first genuine GenAI pilot (56 hours)

| Work | Hours | Completion evidence |
|---|---:|---|
| Audit, agreed protocol and supervisor clarification package | 8 | Findings, requirement mapping, preserved artifacts, explicit holdout options |
| Timestamp-preserving metadata and versioned data preparation | 12 | No-future-data fixtures; source/cutoff hashes; preserved original test |
| Common cohort/candidate evaluator and ranking tests | 12 | All four cohorts retained; empty results counted; per-user outputs and manifests |
| Global/category popularity and reproducible content/CF training | 10 | Matched user/candidate rules, ID alignment and baseline smoke checks |
| Real GenAI adapter, cache, grounding checks and small authorized pilot | 8 | Actual provider responses distinguished from test fixtures; quality/cost logs |
| Dissertation methods and daily evidence log | 6 | Data/architecture/methods draft with limitations |

Days 1-2: audit and protocol; days 3-4: temporal data and evaluator; days 5-6:
baselines and GenAI pilot; day 7: reproduce checks and review milestone. API
access and the holdout decision are needed early; do not postpone these until
the experiment week. Do not run paid generation without an authorized budget.

## Week 2: research contribution and service foundation (56 hours)

| Work | Hours | Completion evidence |
|---|---:|---|
| Fixed-hybrid score/candidate alignment and validation tuning | 10 | Tuned weights, fallback/seen-item tests, paired baseline comparison |
| Switching implementation, threshold tuning and sensitivity | 12 | Supervisor-confirmed Figure 5 components; decision traces and branch tests |
| Grounded GenAI enrichment and explanations; representative subset if needed | 10 | Versioned real outputs, review results, non-GenAI comparison and failure fallback |
| FastAPI + Express + MongoDB contracts and integration | 14 | Authentication/events/products/recommendation endpoints; integration tests |
| Dissertation implementation and experimental protocol | 6 | Claims mapped to code and planned measurements |
| Regression / reproduction checkpoint | 4 | Rebuild and replay small validation experiment |

## Week 3: professional working prototype and experiment rehearsal (56 hours)

| Work | Hours | Completion evidence |
|---|---:|---|
| React/TypeScript/Vite/Tailwind storefront and real API integration | 20 | Responsive browse/search/detail/cart/wishlist/preferences/recommendations |
| Consent, opt-out/reset, authentication and error-path verification | 8 | Backend-enforced safeguards and user-visible controls |
| Seven configurations, cohort/density ablations and robustness rehearsal | 12 | 0/1-4/5-19/20+; 10/25/50/100%; validation-only tuning |
| Load, latency, resource, cost and generation-quality measurements | 8 | Hardware/configuration record, real usage, quality rubric |
| Dissertation results structure and limitations | 4 | Tables/figures generated from actual outputs |
| End-to-end regression checkpoint | 4 | Functional demonstration and recoverable release candidate |

## Week 4: freeze, final evidence, dissertation and delivery (56 hours)

| Work | Hours | Completion evidence |
|---|---:|---|
| Freeze protocol/configurations and run approved final evaluation | 10 | Final holdout policy approved; no test-driven tuning |
| Statistical analysis, ablations, fairness and interpretation | 8 | Paired differences, confidence intervals/tests, negative findings reported |
| Complete and cross-check dissertation and references | 16 | Accurate methods/results/discussion; all claims and citations checked |
| Presentation, viva preparation and recorded/live demonstration | 4 | Rehearsed explanation of contribution and limitations |
| Fresh setup, final regression, accessibility and packaging | 2 | Reproduction smoke check and delivery instructions |
| Contingency (days 27-28) | 16 | Resolve failures without dropping research integrity requirements |

Total: **224 hours**. These allocations include user review/writing effort; they
are not assertions that every experiment fits a fixed compute duration.

## Scope and dependency rules

Follow the seven configurations explicitly confirmed by the user: global
popularity, category popularity, TF-IDF, item-CF, tuned fixed hybrid, switching
without GenAI, switching with GenAI. Do not add user-user CF/BERT4Rec from the
inconsistent figure. Figure 5's hybrid components remain unresolved.

Preserve existing work. The audited history/ranking utilities, data downloads,
working environment and structurally checked artifacts are reusable. Metadata
snapshots and affected models must be rebuilt only under a documented version;
old outputs remain development evidence.

The critical path is protocol/holdout -> temporal data -> shared evaluator ->
verified baselines -> tuned switching/real GenAI ablation -> configuration freeze
-> final experiments -> defensible reporting. Service contracts, UI work,
privacy tests and dissertation drafting can proceed alongside research without
depending on Figure 5's labels. This is scheduling concurrency, not permission
to spawn extra agents.

If time becomes constrained, use the proposal's representative GenAI subset,
limit nonessential polish and deploy locally for a credible demonstration.
Do not remove required comparisons, invent results, call property tokens GenAI,
use an exposed holdout as pristine, or add payment/marketplace/logistics scope.

## Immediate next tasks

1. Send the prepared split/holdout and Figure 5 clarification note to the
   supervisor (the user sends it; no automatic external messaging).
2. Complete timestamp-preserving metadata preparation and the common evaluator.
3. Run the genuine GenAI pilot once provider/model/budget are specified, then
   validate grounding before incorporating generated text into TF-IDF.
