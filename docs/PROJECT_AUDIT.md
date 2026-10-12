# Pasal: project audit and improvement record

Date: 11 October 2026. Baseline commit: `dacd4d3`, branch `main`.

## Assessment

Pasal has a reusable recommendation research foundation, but is not yet a
validated thesis system or an integrated application. Existing work should be
retained. The immediate critical path is research validity, not storefront polish.

The audit read all 19 existing Python source files, the requirements, README,
configuration template, Git status/history, the three supplied handovers, and the
26-page approved proposal. Proposal pages were rendered for visual inspection;
Figures 2, 4, 5, 8 and 11 were inspected at higher resolution. All existing model
matrices were inspected, with sampled content reconstruction, training-score
verification and a new validation diagnostic. The final test CSV was not opened,
scored, modified or used for model selection. Raw-event timestamp counts and raw
metadata timestamps were inspected for structural validity only.

Attachments are context, not fresh instructions: their contradictory requests to
start from scratch, their old implementation status, and their six-model summary
do not override the user's current request or the approved seven-setting text.
The revised title and Pasal name come from the handovers; the approved concept,
research questions and hypotheses are retained.

## Work acknowledged and verified

| Existing work | Evidence and qualification |
|---|---|
| Python environment | Existing Python 3.12 environment works; `pip check` passes. It was reused. |
| Repository | Initially clean; three reachable commits; no tracked dataset or virtual environment. Local `main` and cached `origin/main` both point to `dacd4d3`. Live remote state was not checked. |
| Data preparation | Raw data and existing processed features/splits exist. 2,756,101 raw event timestamps counted. Preparation has validity issues below. |
| Popularity | 205,106 ranked items; all saved weighted scores exactly match aggregation of current training events. Weights are view=1/cart=3/transaction=5, not validation-selected. |
| Original TF-IDF | 417,053 rows, 1,546 features, 881,250 nonzeros; float32; unique IDs, finite values, no empty rows. |
| Property-enhanced TF-IDF | 417,053 rows, 100,000 features, 6,595,215 nonzeros; float32; unique IDs, finite values, no empty rows. This is deterministic feature engineering, not GenAI. |
| Content alignment | 32 evenly spaced rows per model reconstructed exactly using the existing vectorizer and matching feature text. This supports sampled alignment, not proof of temporal validity. |
| Item-based CF | 48,023 x 48,023 sparse matrix; unique IDs, finite nonnegative similarities, zero diagonal, at most 50 neighbors. It covers 23.41% of training item IDs and remains a 20,000-user sampled prototype. |
| Fixed hybrid | Working one-user demonstration source and saved output; normalized popularity/content/CF components. Weights are manually fixed, with no shared-cohort evaluation. |
| Preliminary evaluation | Existing outputs retained; different populations mean the separate scores are not a fair model league table. |

Machine-readable evidence: `docs/audit-2026-10-11.json`. The audit records hashes
for existing training/validation files, TF-IDF artifacts and popularity ranking.

## Findings at the start of this pass, in priority order

### A01: split proportions differ from the approved event split (high, unresolved)

`preprocessing/create_splits.py` takes 70% and 85% of elapsed calendar duration,
not event count. Actual training is 2,024,042 events (73.4386%); validation is
365,683 (13.2681%). The remainder inferred from raw total is 13.2933%; the test
file itself was not read. Training ends strictly before validation begins, so
this is not evidence of behavioral leakage between those two partitions.

Replacing splits silently would create a second problem: sorting raw timestamps
and taking event-count boundaries yields 1438558255147 ms and 1440541861629 ms.
47,040 events in the existing validation file fall in the proposed new test
period. That data has already supported development. A renamed split cannot be
claimed to erase this exposure. Preserve the existing test and obtain a
documented supervisor decision; see `PROPOSAL_CLARIFICATIONS.md`.

### A02: time-varying metadata loses provenance (high, unresolved)

`preprocess_item_properties.py` drops `timestamp`, then deduplicates all observed
item/property/value combinations. Category building combines different category
versions, and enhanced features combine property values across dates, including
availability. The inputs contain 4,284,148 property rows at or after the start of
validation. 5,320 indexed content items were first observed in the source
metadata only at or after that cutoff. Existing recommendation code makes every
indexed item eligible irrespective of its first-observed time or availability.

Thus the artifacts do not establish what was knowable at recommendation time.
The audit has not quantified how much this affected ranking scores. Rebuild
versioned point-in-time metadata from the existing raw files, preserving
timestamp and source provenance. Fit content vocabulary/IDF on the documented
eligible catalogue, and permit metadata-only cold-start items when their metadata
was already available. Enrichment before split materialization does not justify
using future item attributes or behavioral information.

### A03: recent histories were taken from unsorted file order (high, fixed in source)

Training contains 1,012,222 adjacent timestamp reversals; validation contains
182,307. A chronologically separated partition need not have sorted rows.
`dict.fromkeys(items)[-20:]` also retains first occurrences, not the most recent
interaction with each item. Both content recommendation scripts and both content
evaluation scripts now use stable timestamp sorting, last-occurrence
deduplication, then truncation. Full seen-item sets remain separate.

### A04: fixed hybrid could recommend older seen items (high, fixed in source)

The hybrid built its exclusion set after truncating history to 20 items. It now
keeps all seen items while using only recent profile evidence. A 22-item fixture
verifies that older items remain excluded. The hybrid still has no verified
zero-history fallback or final evaluation; this repair does not complete it.

### A05: current user selection does not evaluate cold-start (high, unresolved)

The shared content comparison requires usable history in BOTH content models,
excluding zero-history users. CF selects a different model-covered population.
Popularity's standalone evaluation uses many more users. A valid common
evaluation must define the population independently of each model, include all
four event-count cohorts, and retain empty/short rankings as failures of service
coverage rather than silently dropping users. Profile truncation and unique-item
counts must not redefine historical interaction cohorts.

The revised content comparison deliberately remains a representation diagnostic;
its manifest explicitly labels this restriction. It is not the final common
seven-configuration evaluator.

### A06: catalogue denominator is explicable but not time-aware (high, partly resolved)

Both content ID sets are identical. Their 417,053 items plus 41,424 popularity
items without content total exactly 458,477. This is a legitimate union, not a
duplicate-ID bug. It is not proof that all those items were available at the
evaluation cutoff. The existing hybrid only ranks content IDs and consequently
cannot use popularity/CF-only candidates.

The prior 672-item finding is not a reason to delete candidates. Its handover
diagnostic was acknowledged rather than repeated. Absence from observed
interactions does not prove irrelevance; logged-data evaluation cannot establish
the relevance of unobserved exposure. Temporal availability must be established
separately for every candidate.

### A07: deterministic ranking and failure reporting needed improvement (medium, fixed in part)

Category-only features produce large score ties. `argpartition`/reverse `argsort`
did not define a scientific tie-breaking policy. Content ranking and hybrid
ranking now use score descending then item ID ascending, reject non-finite and
non-positive candidates, and handle empty candidates. Shared comparison loading
checks duplicate IDs and finite nonnegative matrix entries. Metrics reject
duplicate recommendations, respect K, and count missing slots as zero.

The shared comparison now saves per-user metrics (including empty outputs),
sample IDs, relevant-item counts, coverage, input hashes and explicit limitations
in a new output directory. Existing result files are never overwritten by it.
Other standalone legacy scripts still write their historic default filenames;
use the documented comparison command for new diagnostic work.

### A08: core approved contributions were missing at audit baseline (high)

At the audit baseline there was no category-popularity implementation, validated fixed-hybrid training
and tuning, switching controller, GenAI enrichment/explanation implementation,
cohort/density experiments, threshold sensitivity analysis, ablation runner,
confidence intervals or hypothesis tests. `genai`, `experiments`, `switching`,
`frontend`, and `backend` had no source implementations at audit time. No FastAPI
service, Express application, MongoDB integration, React UI, consent/reset/opt-out
flow, authentication, availability filter, latency/cost telemetry or deployment
configuration exists in the reviewed workspace.

These are missing work, not failures of the existing feature-engineering effort.

### A09: reproducibility and efficiency limitations (medium, outstanding)

- The content builder had been changed to enhanced-only training; rebuilding the
  original model is not exposed by the current trainer. Its earlier source exists
  in Git history and can be recovered into a versioned configurable trainer.
- String `dtype="float32"` was changed to `np.float32`. Both existing matrices
  already store float32, so a dtype warning alone is not a reason to retrain.
- CF aggregates event weights but builds a binary matrix using ones. This is a
  valid binary co-occurrence choice if explicitly described; it is not weighted
  cosine CF simply because weights are calculated earlier in the file.
- CF training filters users to at least three unique items and samples 20,000;
  the sampling restriction and limited item coverage must be reported and
  replaced or justified before final baseline comparison.
- Property preprocessing reads chunks but retains them all in lists before
  concatenation. CF forms co-occurrence before pruning. Both can have high peak
  memory. Use measured, bounded processing for the final pipeline.
- Enhanced feature values are tokenized/truncated to 80 characters; collisions,
  discarded tokens and property selection need documented feature ablations.
- Dependency pins work locally (`pip check` passes), but include the whole
  notebook environment. A fresh installation and runtime/dev dependency split
  remain unverified. Proposed web-stack dependencies are not installed by this
  requirements file.

### A10: proposal and documentation consistency (medium, partly corrected)

The supplied handover omits category popularity from one six-model list. The
proposal's methodology explicitly lists seven. Figures 5 and 11 have additional
ambiguities described in `PROPOSAL_CLARIFICATIONS.md`; none were silently resolved.
Figure 11 includes MAP, hit rate, uncertainty, load/resource and GenAI quality
measures beyond the three metrics in the existing scripts.

The README previously claimed completed models and named Next.js; the approved
frontend is React/TypeScript/Vite/Tailwind. The template suggested PostgreSQL;
the approved database is MongoDB. These descriptions are corrected. The author
name now matches the proposal cover: Rajiv Ganeju.

The literature review cites Zhao et al. (2024) and Zhang et al. (2025), but neither
has a corresponding entry in the supplied reference list. Resolve citations
before dissertation submission. Individual paper claims and every DOI have not
been externally verified by this repository audit. Figures contain terminology
and copyediting issues; preserve the approved research meaning while clarifying
them with the supervisor. No final dissertation beyond the proposal was present.

## Verification and results of the initial repair pass

- Ten regression tests pass, covering timestamp recency, repeated items,
  independent user histories, older seen-item exclusion, ties, invalid scores,
  metric arithmetic, short/empty rankings, duplicates, ID mapping and valid
  metadata-only candidates.
- Every Python source compiles; dependency consistency check passes.
- Read-only artifact audit completed; hashes and structural measurements saved.
- Corrected 100-user comparison ran successfully on existing validation data;
  all three models returned recommendations for all selected users.
- The new comparison writes to
  `data/processed/audit-content-comparison-2026-10-11/`. Its scores are diagnostic
  only, not evidence that H1 or H2 is satisfied. User eligibility can change with
  corrected histories, so this is not a controlled before/after quality study.
- No model retraining, split regeneration, external API call, public deployment,
  or participant data collection occurred. The assistant did not run a Git
  commit/push; commit `4d58fb6` appeared during the session and was preserved.

## Subsequent unblocked implementation in this session

The user confirmed the seven configurations, requested both holdout options for
supervisor review, provided 224 hours over four weeks, and confirmed no API access
yet. The four-week plan includes 16 hours of contingency.

Added a category-conditioned popularity baseline with deterministic ties,
eligibility/seen filtering and an explicit configurable global fallback. Added a
SQLite-backed metadata snapshot builder that keeps timestamps, excludes future
facts and flags conflicting latest values. It processed all 20,275,902 raw
property rows and exported a reproducible 50-item development subset. The
snapshot retained facts strictly before 1438968231028 ms, the legacy training
cutoff plus one millisecond. This does not select a final split protocol.

Added an actual OpenAI Responses API adapter, strict catalogue-only payloads,
versioned caches, usage/latency records, conservative budget reservations and
output-grounding checks. A separate exact-output review is required before
generated descriptions enter matched with/without-GenAI feature tables. API
contract tests use mocked responses, not research generations. No live model
call, actual GenAI-quality result or H2 evaluation is claimed.

The expanded suite passes **27 tests**, including temporal snapshots, category
popularity, privacy payload rejection, cache reuse, refusal handling, budget
blocking, reviewed feature export and unchanged fallback features. Original
audited inputs were rehashed: all nine remain byte-for-byte unchanged.

## Order of improvement

1. Resolve the split/holdout and proposal ambiguities; version the agreed protocol.
2. Repair metadata provenance and create a shared cohort/candidate evaluator.
3. Verify/rebuild the affected baselines; implement category popularity and tune
   the fixed hybrid on validation only.
4. Implement and validate the switching policy and grounded GenAI ablation.
5. Integrate the required services and consented demonstration, with system tests.
6. Freeze configurations, conduct approved final experiments, and report actual
   findings, uncertainty, limitations and negative results in the dissertation.
