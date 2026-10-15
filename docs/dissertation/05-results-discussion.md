# 5 Development results and discussion

## 5.1 Status of the evidence

This chapter reports development evidence only. The final frozen holdout has not
been evaluated. Consequently these findings cannot be substituted for final H1
or H2 conclusions. In particular, the development aggregate includes cohorts
outside the precise primary hypothesis populations and reuses validation data.

## 5.2 Corrected density comparison

All seven configurations completed at retained training-event densities of 10%,
25%, 50% and 100%. Nested samples and the same 200 assessment users were used.
Interaction-dependent models and histories were rebuilt, while the candidate
universe contained 100,599 items. History cohorts and novel targets can change
with density, so the trend does not isolate model robustness alone.

| Retained events | Fixed hybrid | Category popularity | Switching | Switching with partial GenAI |
|---|---:|---:|---:|---:|
| 10% | .018273 | .017818 | .008631 | .008631 |
| 25% | .018603 | .015377 | .006533 | .006533 |
| 50% | .026408 | .017159 | .015434 | .015434 |
| 100% | .021008 | .016982 | .013846 | .013846 |

Table 1. Development mean NDCG@10, not final hypothesis estimates.

The fixed hybrid achieved the highest observed aggregate mean among the seven
configurations at every density. At full density the descriptive switching-minus-
fixed-hybrid difference was −.007162, with a post-hoc percentile interval of
[−.015259, −.001021]. This interval is unadjusted for multiple comparisons and
does not establish the approved H1 conclusion. The small tuning sample weakly
identified thresholds: 54 of 72 grid settings tied for the maximum objective.
The prespecified first-maximum rule was retained rather than selecting a setting
after examining final outcomes.

## 5.3 Genuine generation and treatment exposure

The uniform 32-item generation sample produced 24 schema-valid outputs and eight
failed requests. Schema success was 75%, with a Wilson 95% interval of 57.9–86.7%.
Assistant grounding screening approved 21 outputs and rejected three descriptions
that overstated historical availability. This is evidence about operational
generation and source consistency, not independent human usefulness or relevance.
Reported usage was 11,099 input and 11,785 output tokens; usage for eight failures
was unavailable, making these lower bounds.

The paired enriched artifact preserved all 411,732 rows and ordinary features.
Only one assessed full-density profile contained an enriched item, and it did
not take the content route. No switching rankings changed at any density. The
zero difference therefore reflects inadequate observed treatment exposure; it
does not demonstrate equivalence or a general absence of GenAI benefit.

A training-only selection analysis estimated that a targeted 128-item set could
expose 20,290 content-route users, or 2.91%, compared with 293 for a uniform set
of the same size. These counts assume every selected output is approved and
measure in-sample potential, not future exposure or effect size. The targeted
sample is still being generated under conservative Free-tier quotas. Its final
failure, approval, usage and ranking outcomes will be reported after completion.

At the eighth operational checkpoint, 98 of 128 declared items had been attempted:
69 outputs passed schema validation and 29 attempts failed or were rejected during
generation. Assistant grounding screening approved 41 outputs and rejected 28;
none of the 69 schema-valid outputs remained unreviewed. Thirty items were still
unattempted when the conservative rolling daily quota stopped generation. These
are incomplete-sample counts, not final quality estimates. Recorded usage totalled
35,641 input and 34,329 output tokens, excluding unavailable usage for 29 failures.
The evidence is recorded in `docs/genai-targeted-batch-8-results.json`.

Rejected outputs included unsupported present-day availability claims, category
codes presented as item identities, and omitted source-property citations for
asserted facts. Accepted outputs often only restated anonymous property names or
explicit historical availability flags. Acceptance therefore indicates source
consistency under assistant screening, not meaningful semantic enrichment or
independent human judgement. No targeted-treatment ranking benefit is asserted.

## 5.4 Interpretation and threats to validity

The development findings challenge the assumption that switching necessarily
outperforms a fixed combination. Sparse behavioural evidence, weak threshold
identification and the selected content representation offer plausible explanations,
but this study has not isolated their causal contributions. The defensible response
is to retain the comparison and disclose negative or inconclusive evidence.

Anonymous properties sharply constrain what a language model can add. Grounded
outputs often restate property codes. A source-faithful description can still be
uninformative to a shopper, and an attractive description can invent unsupported
semantics. Independent human ratings would address aspects that schema checks
and assistant screening cannot establish; they remain deferred.

Historical exposure in part of the repaired test split, a bounded stratified
sample, static training-origin histories, targeted generation and modest local
load measurements limit generalisation. The synthetic storefront is an engineering
demonstration, not a second validated experimental population. Neither user
satisfaction in Kathmandu nor commercial performance can be inferred from these
offline measurements.

## 5.5 Final results still required

The submission version must replace this status paragraph with the frozen
untouched-intersection results, secondary exposed-partition results, exact cohort
counts, paired uncertainty, multiplicity-adjusted comparisons and treatment
exposure. Density and efficiency evidence must be discussed separately from
ranking significance. A final abstract and conclusion must state the observed
outcome even if neither hypothesis is supported. No such outcome is asserted here.
