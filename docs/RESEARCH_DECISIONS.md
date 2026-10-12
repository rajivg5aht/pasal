# Research implementation decisions — 12 October 2026

Authority: the user reports supervisor delegation to choose and justify sound
implementation details. The approved proposal remains authoritative. This record
supersedes requests for supervisor selection in PROPOSAL_CLARIFICATIONS.md; that
note remains an audit trail, not a current blocker.

## Seven configurations and Figure 5

Retain global popularity, category popularity, TF-IDF, item-CF, tuned fixed hybrid,
switching without GenAI, switching with GenAI. Do not add BERT4Rec/user-user CF.
Interpret the ambiguous CB in the middle/fallback branch as **collaborative**,
following the figure's explicit legend and fallback description. Thus those
branches use validation-tuned item-CF + popularity. Low-history uses content;
high-history uses CF when its evidence confidence meets a validation-tuned
threshold. The standalone fixed-hybrid baseline retains the existing three
components (content, item-CF, popularity), with validation tuning replacing manual
weights. Record this distinction in every configuration manifest.

Zero-history routing uses explicit onboarding categories when available and
global popularity otherwise. Offline missing preferences remain missing; never
infer them from validation/test outcomes. New-item exposure is disabled in the
primary comparison (cap zero) because the proposal does not specify allocation;
nonzero caps may be validation sensitivity analyses declared before test.
Event-count cohorts are reporting groups, not automatically switching thresholds.

## Chronological split and exposure

Create a separate, versioned 70/15/15 split by event count, stable ordering by
timestamp then source row. Never overwrite legacy files. Metadata is strictly
earlier than each prediction origin; training ends before validation begins.
If a boundary cuts equal timestamps, quarantine boundary-time training facts
from fitting and report the tiny effective-count deviation rather than pretending
simultaneous events are historical evidence.

The new final 15% contains 47,040 events previously used for validation. Mark
that segment **previously exposed**, and do not tune on it again. Report full
15% results as the proposal-aligned but historically exposed analysis; use the
untouched legacy-test intersection as an independent confirmatory analysis.
Require conclusions to distinguish the two; the full test cannot become pristine
through repartitioning. No new test results may guide parameters or model choice.
Preserve the original test file and defer reading outcomes until configuration
freeze. This is a disclosed limitation, not a claim that leakage was erased.

## Evaluation definitions

Use one chronological protocol rather than inconsistent leave-one-out notes.
All algorithms share users, candidate availability, targets and seen filtering.
Count repeated historical events for cohorts; retain zero-history users, failed
recommendations and relevant but unavailable items in headline denominators.
Also report eligible-target metrics explicitly, never substitute them silently.
Tune exclusively on validation; freeze seeds, configurations and input hashes.
Use paired user bootstrap 95% intervals (2,000 resamples, seed 42) for primary
NDCG@10 differences, with Holm correction for the declared primary comparisons.
Report Precision/Recall/MAP/HitRate@10, coverage, diversity and cohort sample sizes.
Density experiments use seeded training-event subsampling, recomputing histories
and cohorts; retain a second original-cohort view to expose cohort migration.
Switching win rate compares paired per-user NDCG with the fixed baseline; avoid
calling it classifier accuracy when no ground-truth optimal strategy exists.
Improvement/degradation and P95 targets are assessment targets, not promised results.

## Genuine GenAI and grounded explanations

Choose Groq-hosted openai/gpt-oss-20b on a Free organization, not the paid OpenAI
API. Use cached catalogue-only generation, strict schemas and grounded review.
Descriptions remain honest about anonymous identifiers. An explanation combines
a reviewed generated catalogue description with the actual local strategy reason;
the model never invents why a user was selected and receives no user history.
No payment method, upgrade, paid fallback or automatic retry. API cost is zero
only for a verified Free organization; record tokens, latency and failures as well.
Representativeness and subset size must be declared before inspecting outcomes.
No simulated output counts as GenAI evidence. Quality ratings by the researcher
are not represented as an independent human-subject study.
