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
