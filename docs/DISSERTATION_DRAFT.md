# Pasal dissertation working draft

Author: Rajiv Ganeju. Status: evidence-based working text, not a submission-ready
dissertation. The approved proposal controls scope. Final results and independently
verified literature citations are still required. Do not copy pending claims into
the abstract as findings.

## Methodology: research design

Pasal investigates whether history-dependent switching among conventional
recommendation strategies improves recommendation quality for users with limited
interaction histories. A separate ablation examines the effect of genuinely
generated catalogue descriptions on the content representation. Generation is a
supporting component: it does not replace the ranking algorithms or determine
personal preferences. The seven experimental configurations are global
popularity, category popularity, TF-IDF content similarity, item-based
collaborative filtering, a tuned fixed hybrid, switching without generated
metadata, and switching with generated metadata.

The research uses Retailrocket events and anonymized item properties. The
application's Nepal-oriented presentation does not establish that the research
dataset represents Nepalese shoppers or products. Encoded property identifiers
provide limited semantic evidence. Generated descriptions must preserve this
limitation instead of inventing recognizable product categories, brands or
materials.

## Temporal design and threats to validity

An audit found that the prototype's original split used fractions of elapsed
time rather than fractions of event count. The repaired protocol sorts events
chronologically and allocates 70%, 15% and 15% to training, validation and test,
subject to integer rounding and a declared policy that keeps simultaneous
boundary events together. For 2,756,101 events, the resulting nominal counts are
1,929,270, 413,415 and 413,416. No boundary tie changes these counts in this run.

Repartitioning does not erase earlier experimental exposure. Of the planned test
events, 47,040 were previously in validation. Consequently, the complete 15% test
must be described as historically exposed. A separate confirmatory analysis is
planned on the intersection with the untouched original test period, strictly
after timestamp 1440756695565. Neither new test analysis is used for tuning.
This dual reporting preserves visibility of the proposal's split while avoiding
a false claim that all test outcomes were previously unseen.

Metadata is reconstructed from timestamped property observations strictly before
the prediction origin. For each item and property, the latest eligible fact is
retained; conflicting values at the same latest timestamp are marked ambiguous.
Models trained from the old all-time property tables cannot serve as final
leakage-controlled evidence. Input fingerprints and cutoffs are recorded with
each new artifact so that temporal provenance can be checked independently.

## Recommendation history and evaluation population

Profiles use the most recent distinct interacted items ordered by their last
event timestamp. A separate complete seen-item set prevents older interactions
from reappearing merely because the profile window was shortened. User cohorts
are determined by the number of historical events, including repeats: zero,
1-4, 5-19 and at least 20. These reporting groups are distinct from the switching
thresholds, which must be selected on validation data.

The common evaluator selects users independently of individual model coverage.
Every algorithm receives the same history, candidate eligibility and targets.
Empty results and invalid recommendations contribute zero rather than causing
the user to be dropped. Novel-item discovery excludes already-seen items from
targets; users left without novel targets remain in the headline population and
are separately counted. Relevant items unavailable at the prediction origin
remain in the headline recall denominator. Eligible-target metrics are secondary
and must be labeled explicitly. This prevents apparently stronger results from
being produced by silently changing the evaluation population.

Precision, recall, normalized discounted cumulative gain, average precision and
hit rate are computed at rank ten. Missing recommendation slots count as misses.
Aggregate results will be accompanied by cohort sizes, coverage, failure rates
and paired uncertainty estimates. Latency measured inside a Python ranking
function is not a substitute for end-to-end API latency under load.

## Generative metadata and explanations

The implemented integration targets Groq-hosted GPT-OSS 20B on a Free account.
Only allowlisted catalogue properties leave the machine. User identifiers,
interaction histories and preference profiles remain local. Responses are
cached by input provenance, model, token allowance and prompt/schema versions.
The adapter rejects incomplete responses and invalid citations, but schema
validity alone is not evidence of factual accuracy. Only outputs with explicit
review tied to the exact output hash may enter the enriched feature table.

The paired feature export uses identical items and base features for both
conditions. Missing or rejected generations use the unchanged base features.
Explanations combine a locally recorded strategy reason with an optional reviewed
generated catalogue description. This distinction prevents generated language
from being presented as evidence of a personalized causal explanation.

A single genuine Groq Free generation has now completed. The request consumed
553 input tokens and 454 output tokens, with 1,168 ms client-observed latency.
An assistant compared the description against the source and recorded a grounded
review tied to its output hash. This is not an independent human quality rating.
The paired feature export contains one generated description. Because this was
an integration pilot and the sampled item was unavailable, it establishes neither
recommendation benefit nor representative generation quality. The larger
prespecified sample, quality assessment and paired ranking experiment remain
pending. Zero API spend follows the user-confirmed Free tier; no independent
billing statement has yet been collected.

## Preliminary engineering evidence — not hypothesis results

A 1,000-user legacy-split popularity diagnostic retained 926 zero-history users,
57 users with 1-4 events, 14 with 5-19 and three with at least 20. All received
recommendations, and nine users had no novel targets. This run verifies that the
new evaluator retains cold-start users; it does not establish superiority of
switching or generated metadata. The small nonzero-history cohorts also motivate
reporting full-population or prespecified stratified evaluation rather than
overinterpreting this smoke sample.

## Completion checklist

- Verify the literature and bibliography against original sources; resolve
  missing proposal references without inventing citations.
- Finish leakage-controlled model training, validation tuning and all seven
  configurations; freeze the reproducibility manifest before test evaluation.
- Run genuine generation and document sample selection, review rubric, token
  usage, failures, latency and actual Free-account cost evidence.
- Complete cohort/density/sensitivity comparisons, paired uncertainty analysis,
  diversity/coverage and system performance measurements.
- Complete the application, privacy controls, integration tests and architecture
  figures; describe only implemented behavior.
- Write results, discussion, limitations, conclusions and abstract from measured
  evidence, including negative or inconclusive outcomes.

## Implemented prototype and development assessment

The prototype now connects a React/Vite interface to an Express API with MongoDB
sessions and a local FastAPI recommendation service. Personalization is opt-in;
turning it off atomically clears recommendation history and preferred categories.
Operational wishlist and basket data remain separate. User identity and history
are not sent to the generative provider. The interface describes anonymized items
and historical availability without inventing product names, prices or orders.
Displayed strategy explanations currently use local templates; genuine generated
explanation integration remains to be completed.

The full training-data item collaborative model contains 200,975 items and
2,589,203 retained neighbour links. Development tuning used 200 validation users
and disjoint assessment used 200 more, with equal history-cohort allocation.
Category popularity achieved assessment NDCG@10 of 0.0169822, compared with
0.0138460 for the selected switching model. This preliminary outcome does not
support superiority of switching. It is neither a population-weighted estimate
nor final hypothesis evidence. The GenAI condition and final holdout experiments
are still pending, and these limitations must remain explicit in the final thesis.

## Genuine generation feasibility and partial-treatment results

A prespecified uniform sample of 32 eligible historical items produced 24
schema-valid Groq Free outputs and eight failed/rejected requests. The schema
success proportion was 75% (Wilson 95% interval 57.9–86.7%). This measures API
reliability, not factual consistency or relevance. Assistant source comparison
approved 21 outputs and rejected three descriptions that overstated historical
availability as purchase availability. These reviews are not independent human
ratings. Token reporting was unavailable for all eight failed requests; the
observed 11,099 input and 11,785 output tokens are therefore lower bounds.

A paired feature model retained all 411,732 catalogue rows and unchanged ordinary
property features, adding a separate generated-text block for the 21 approved
items. In the seven-condition development assessment of 200 users, only one
profile contained an enriched item, no enriched items were recommended, and no
switching recommendation lists changed. The resulting zero paired NDCG difference
must be interpreted as inadequate exposure in a small partial-treatment diagnostic,
not as a conclusive test of the GenAI hypothesis. Larger, justified treatment
coverage and final frozen cohort/density experiments remain necessary.

Local engineering load checks also motivated lazy component scoring. In small
synthetic single-request diagnostics, successful-request P95 fell from 353.6 to
187.3 ms while ranking-equivalence fixtures passed. Capacity rejections still
occurred with four simultaneous requests. These measurements exclude the browser,
Express and MongoDB path and do not establish final system performance targets.


## Density experiment and correction to development tuning

The four-density development experiment retains 10%, 25%, 50% and 100% of training
events using nested samples. It fixes 200 assessment users and a 100,599-item
candidate universe while rebuilding interaction-dependent CF and histories.
History cohorts can change with density. Novel targets also change when previously
seen interactions are removed, so density trends cannot be attributed solely to
model robustness. An explicitly post-hoc analysis holds novelty targets fixed
and measures list diversity in the original property TF-IDF representation.
Anonymous-code distance is not human semantic diversity.

A correctness review found that the initial tuning objective omitted zero-history
users even when choosing fixed-hybrid weights. Including all four cohorts equally
changed the chosen content/CF/popularity weights from .75/.25/0 to .50/.25/.25.
Switching thresholds were unchanged. Earlier results remain versioned development
evidence, and the density comparison has been repeated with corrected weights.
Neither reuse of validation data nor zero GenAI differences under sparse treatment
exposure establish final hypothesis results. The final holdout protocol must be
frozen before final testing.

### Corrected development density results

All seven approved configurations completed at all four densities. The table
shows mean primary NDCG@10 on the same 200 original-stratified assessment users.
Novel targets are recomputed from each retained history; the samples are not
population-weighted and are not final test observations.

| Retained events | Fixed hybrid | Category popularity | Switching | Switching + partial GenAI |
|---|---:|---:|---:|---:|
| 10% | .018273 | .017818 | .008631 | .008631 |
| 25% | .018603 | .015377 | .006533 | .006533 |
| 50% | .026408 | .017159 | .015434 | .015434 |
| 100% | .021008 | .016982 | .013846 | .013846 |

The fixed hybrid has the highest observed mean among all seven configurations
at each density. At full density the descriptive switching-minus-fixed-hybrid
paired difference is -.007162, with a 2,000-resample percentile interval
[-.015259, -.001021]. This post-hoc interval is unadjusted for multiplicity and
does not constitute a confirmatory test of the approved hypothesis. Corresponding
intervals against category and global popularity include zero. The small tuning
sample also weakly identifies switching thresholds: 54 of 72 grid configurations
tie for the maximum objective, and the prespecified first-maximum rule was retained.

No switching rankings changed with GenAI at any density. Although one full-density
profile contains an enriched item, it does not take the content route; no assessed
user has both a generated profile item and a content route at any density. This
explains why these comparisons provide inadequate evidence about the ranking
effect of enriched content. Reporting unchanged rankings as proof of no GenAI
benefit would overstate the experiment. All aggregate metrics and exposure counts
are retained in density-development-v2-results.json, with the secondary analyses
reported separately. The final holdout remains unopened for evaluation.


### Feasibility of increasing generated-feature exposure

A training-only design comparison evaluated nested uniform catalogue selection
and selection ranked by distinct low-history user support. At the selected policy,
697,327 training users take the content route; 192,010 have eligible profile items.
A uniform 128-item sample exposes 293 users, compared with 20,290 (2.91%) for the
support-based sample. The latter covers 73 known categories. This is in-sample
potential exposure, assuming generation and approval of every selected item. It
is not a power calculation, future coverage estimate or ranking-effect measure.

A 128-item targeted development intervention was frozen separately from the
uniform quality study. Larger 256/512-item alternatives expose 4.29%/6.25% of
content-route training users but require at least six/eleven fresh daily windows
under local quota guards. The chosen set reserves 464,751 tokens, requiring at
least three fresh daily windows; packing, other usage and provider constraints
can extend this. Support-based selection favors frequent profile items and cannot
support representative catalogue-quality claims. The user explicitly authorized
its catalogue-only transfer; generation is in progress, not yet a completed result.

An anonymous public-API engineering diagnostic also completed 72 measured requests
across three concurrency levels, plus three warm-ups. Recommendation responses
included ten unique, correctly hydrated available catalogue items. Successful
recommendation P95 ranged from 54.4 to 84.0 ms across these small mixed-route phases.
The measurements include Express, FastAPI and MongoDB hydration but exclude browser
rendering, authenticated histories and controlled workload isolation. They are
preliminary integration evidence rather than final performance findings.


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

## Website integrity and research boundary — 13 October 2026

The product audit found no verified human-readable Retailrocket identities, brands,
prices or photographs. Pasal therefore implements two experiences: a separate
16-record synthetic Kathmandu-oriented shop and the original numeric-ID Research
Lab. Demo records use namespaced string IDs, separate collections and explicit
synthetic labels. Search, categories, cart quantities, wishlist and consent apply
to the appropriate catalogue. Same-category demo suggestions are not presented as
outputs of the evaluated switching model. No cross-catalogue mapping is invented.

The administrator interface manages only demo products and displays actual service
observations. Authorization checks stored roles server-side; public registration
cannot assign an administrator role. Product deactivation preserves saved references.
Only bundled illustrations can be selected. Live request counts and latency are
operational observations, not substitutes for experimental measurements.

Verification passed eight frontend tests, five backend tests including real MongoDB
isolation tests, and a production build. All 83 inventoried raw/split/model/evaluation
artifacts retained their SHA256 hashes. Browser inspection confirmed the research
controller reported global_popularity for a zero-history profile, thresholds 2/10,
CF confidence 0.000 against a 0.25 cutoff, and the historical training cutoff.
These observations demonstrate integration, not superiority or hypothesis support.

A further bounded Groq Free batch attempted two previously unattempted items. Item
23762 returned a schema-valid description that accurately enumerates source keys
without semantic product inference; assistant grounding review approved this exact
output. Item 29196 failed provider JSON validation and was not retried. Cumulative
progress is 10/128 attempted, seven generated and assistant-approved, three failed,
118 unattempted. Reported usage is 3,607 input and 3,470 output tokens, excluding
unavailable failure usage. Independent human quality ratings remain outstanding.
The incomplete sample and descriptions that restate anonymous identifiers cannot
establish useful semantic enrichment or recommendation gains.
