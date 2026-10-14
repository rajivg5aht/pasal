# 3 Methodology

## 3.1 Experimental design

The controlled comparison uses the seven configurations in the approved proposal:
global popularity, category popularity, TF-IDF content similarity, item-based
collaborative filtering, a fixed hybrid, switching without generated metadata and
switching with generated metadata. The ambiguous diagram labels do not introduce
user-user filtering or BERT4Rec. The enumerated methodology determines the
implementation. The generation ablation changes the content representation while
holding the switching policy, item universe and ordinary features constant.

Retailrocket supplies 2,756,101 timestamped events and anonymous item properties.
The corrected split sorts events chronologically, retaining source order for ties,
and allocates 1,929,270 events to training, 413,415 to validation and 413,416 to
planned testing. The boundary rule keeps simultaneous events together; there are
no count changes due to boundary ties in this dataset. The original time-duration
split remains preserved as historical evidence.

Repartitioning moved 47,040 previously used validation events into the planned
test partition. These events cannot become unseen merely by renaming the split.
Accordingly, the primary final population is the intersection with the untouched
original test period, after timestamp 1440756695565. The full event-count test
partition is a secondary, historically exposed analysis. Both are disclosed and
neither is used to retune the selected models. This follows the temporal-validity
concern described by Ji et al. (2023).

## 3.2 Historical features and recommendation histories

Item properties are reconstructed before the prediction origin. The latest
eligible observation for each item-property pair is retained; conflicting values
at the same latest timestamp are marked ambiguous. Availability is a historical
flag, not a guarantee that a product can currently be purchased. The feature
manifest records its cutoff and input fingerprints.

User profiles contain recent distinct items ordered by their last interaction.
A separate complete seen-item set excludes older interactions from recommendations
even when they fall outside the profile window. Reporting cohorts count events,
including repeated interactions: 0, 1–4, 5–19 and 20+. They are not interchangeable
with the independently tuned switching thresholds.

For final testing, models and histories remain fixed to the original training
partition. Validation interactions are not appended and models are not refitted
on validation. Test predictions therefore assess a longer forecast horizon from
the same origin. This choice avoids silently changing a tuned system but limits
claims about continuously updating production recommenders.

## 3.3 Tuning and generation intervention

The selected fixed-hybrid weights are .50 content, .25 collaborative filtering
and .25 popularity. The selected switching settings use history thresholds 2 and
10, confidence threshold .25 and collaborative weight .25. Selection occurred on
validation data. Tuning and development assessment use separate 200-user samples;
these small samples limit the precision of parameter selection.

Genuine generation uses Groq Free with GPT-OSS 20B. Only allowlisted anonymous
catalogue properties enter the provider prompt. User identities, histories and
preferences remain local. Responses are cached with input provenance, model,
prompt/schema versions and token allowance. Schema validation checks structure
and citations; subsequent assistant grounding screening compares each response
with its exact historical source. Approval is bound to the output hash. This
screening is not an independent human quality rating.

The uniform 32-item study assesses operational feasibility. A distinct frozen
128-item intervention selects items using training-only support among users
eligible for the content route, to increase potential feature exposure. No final
test outcomes inform selection. This targeted set is not representative of the
catalogue and cannot estimate catalogue-wide generation quality. Failed requests
are retained rather than replaced with favourable responses.

Approved generated text forms an additional content-feature block. Every item
retains its ordinary features; missing or rejected generations retain the base
representation. Generated descriptions do not create product identities. Local
strategy reasons explain the selected route, while optional reviewed text
describes catalogue evidence. These two explanation sources remain distinguishable.

## 3.4 Outcomes and statistical analysis

At rank ten the evaluator reports precision, recall, NDCG, average precision and
hit rate. Precision uses ten recommendation slots, including missing slots as
misses. Recall divides retrieved relevant items by the novel target count. NDCG
discounts a relevant result by log base two of rank plus one and normalises by
the ideal ordering. Average precision averages precision at relevant ranks with
the declared rank-ten denominator. The implementation and fixtures define edge
cases; users without novel targets receive zero and remain in headline results.

Every configuration receives the same population, candidate rules and histories.
Invalid or failed outputs become empty rankings rather than excluded users.
Relevant unavailable targets remain in headline denominators; eligible-target
metrics are secondary. Coverage and diversity use a common candidate universe
and ordinary-property space. Anonymous-code diversity is not human semantic
diversity. Generation exposure and changed rankings are reported alongside scores.

The final protocol samples at most 500 users per original-history cohort,
uniformly without replacement with seed 42, keeping all users in smaller cohorts.
It records population and sampled counts. H1 compares switching without GenAI
with the validation-best non-switching baseline, the fixed hybrid, among users
with 1–19 events. H2 compares switching with and without GenAI among users with
0–19 events. The 20+ cohort is descriptive. Each contrast weights its observed
eligible cohorts equally, rather than estimating the population-frequency mean.

Paired, within-cohort user bootstrap resampling supplies 95% percentile intervals
from 2,000 resamples. Within-user label exchange supplies two-sided permutation
p-values using at most 9,999 permutations. Holm adjustment controls the two
primary comparisons at family alpha .05. Bootstrap intervals are marginal, not
simultaneous. Label exchangeability is an assumption; these offline comparisons
do not establish a causal deployment effect. Density and end-to-end efficiency
remain separate parts of the compound hypotheses.

Before any final outcomes are read, the freeze records code, model, source,
configuration, review and split hashes. Execution refuses changed inputs or an
unfinished generation sample. Existing result directories cannot be overwritten.
This is a prospective execution control, not a claim of external preregistration.

## 3.5 Ethics and reproducibility boundaries

The application makes personalisation optional and separates operational cart and
wishlist records from recommendation history. Revoking consent clears history
and category preferences. Research identifiers are not linked to synthetic shop
products. The user confirmed applicable human-review requirements, but independent
reviewers are unavailable and that assessment is deferred. No assistant ratings
are substituted for human participants.

The repository retains versioned code, manifests, experimental summaries and
execution instructions. Large local datasets and model binaries are excluded
from Git. Reproduction therefore requires obtaining the original dataset and
following the documented build sequence; a source checkout alone is insufficient.
