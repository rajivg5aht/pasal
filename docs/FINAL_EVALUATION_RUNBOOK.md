# Final evaluation implementation and execution protocol

Prepared 14 October 2026. Implementation is fixture-tested; actual holdout results
have not been read. This document is a prospective execution specification, not a
claim that a complete final model or preregistered result already exists.

## Fixed design

Use the approved seven configurations and selected v2 settings. Keep models,
metadata and user histories fixed to the original 70% training partition; do not
refit on validation or append validation interactions. Consequently the test is a
longer-horizon forecast from the same origin than validation. Disclose that choice.
All algorithms receive the same static historical availability and seen-item rules.

Sample uniformly without replacement within the four original-training event-count
cohorts (0, 1–4, 5–19, 20+), at most 500 users per cohort, seed 42. Keep all users
when a cohort is smaller. Sample by user and cohort only, never by model coverage
or target success. Targetless users remain. The primary contrast weights observed
cohorts equally; aggregate sample means are not estimates weighted by population
cohort frequencies. Report both population and sample cohort counts. The sample
cap is a computationally bounded final assessment, not a power guarantee.

Materialize the full event-count 15% only after freeze verification. Preserve the
original test file. The full partition includes 47,040 previously exposed events
and is secondary. The untouched intersection uses timestamps strictly after the
legacy validation endpoint and carries the two primary comparisons. Users may
appear in both populations; these are separate analyses, not independent replications.

At rank 10 report Precision, Recall, NDCG, MAP, HitRate, coverage, targetless and
failed cases, common-property diversity and eligible-target secondary metrics.
Invalid or failed recommendations contribute empty rankings; users are retained.
Report generated-profile exposure, content-route exposure and changed rankings.
This evaluator shares prepared signals; its output deliberately does not claim
independent API latency. Use the separate service diagnostics for that purpose.

## Statistical family

Primary metric: equal-observed-cohort mean NDCG@10 difference on the untouched
intersection. The two prespecified comparisons are:

1. Switching without GenAI minus the tuned fixed hybrid.
2. Switching with GenAI minus switching without GenAI.

Use stratified paired-user bootstrap percentile intervals (2,000 resamples, seed
42). For each contrast, swap paired condition labels within users under the null,
using at most 9,999 permutations and a two-sided statistic. Fixed user weights
retain equal cohort weighting. This assumes label exchangeability under the null;
it is not a randomized deployment causal claim. Apply Holm correction to the two
primary p-values at family alpha .05. Bootstrap intervals are marginal, not jointly
adjusted. Full-partition comparisons are secondary and cannot override a failed
primary comparison. Record ties and signed wins/losses as descriptive quantities.

Method references: [SciPy paired permutation documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html)
and [statsmodels Holm implementation/documentation](https://www.statsmodels.org/stable/_modules/statsmodels/stats/multitest.html).

## Commands after generation and grounding review are complete

Build a new enriched artifact and run the paired validation check first, retaining
all previous versions. Then freeze inputs using the new artifact and completed
sample; the script refuses unfinished attempts, pending reviews and mismatches:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
.venv\Scripts\python.exe recommendation-engine/evaluation/final_holdout.py freeze --enriched data/processed/content-genai-targeted-v1 --sample data/processed/genai-targeted-sample-v1 --reviews data/processed/genai-targeted-sample-v1/reviews.jsonl --output docs/final-evaluation-freeze-v1.json --per-cohort 500
```

Commit that freeze before executing the next command. It records code revision,
all implementation hashes, exact model files, training/raw/split/configuration
hashes, sampling and statistical choices. No actual freeze exists yet while the
generation sample is unfinished. Existing files and result directories cannot be
overwritten; changed inputs fail before holdout outcome fields are read.

```powershell
.venv\Scripts\python.exe recommendation-engine/evaluation/final_holdout.py run --frozen docs/final-evaluation-freeze-v1.json --output data/processed/final-evaluation-v1
```

Retain per-user rankings, failures, diversity coverage, exposure, aggregate results
and hashes. Do not tune after seeing outcomes. A failed interrupted run may leave
partial evidence; preserve it and document any re-execution. Report absent human
ratings as deferred, not as successful independent explanation evaluation.
