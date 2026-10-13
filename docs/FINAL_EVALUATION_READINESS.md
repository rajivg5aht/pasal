# Final evaluation release gates

Status: preparation only; final holdout outcomes have not been opened by this work.
The website and development results do not satisfy these gates by themselves.

1. Complete the frozen 128-item targeted generation attempt set under the original
   prompt/model/output cap. Preserve failures and exact assistant review decisions.
   Do not replace items or quietly change prompts. Keep the uniform 32-item quality
   study separate. Obtain independent ratings under the applicable university
   requirements; if they cannot be obtained, explicitly delimit the quality claims.
2. Build a new versioned enriched matrix only after source-grounding review. Keep
   the property matrix, item ordering, untreated rows and candidate universe intact.
   Report attempted, generated, approved and treated counts separately. Do not
   overwrite the existing 21-item enriched artifact or its development results.
3. Run the existing paired validation diagnostic with the same assessment users,
   seven configurations, selected v2 settings and .25 generated-text block weight.
   Measure actual profile exposure, content-route exposure, generated recommendations
   and ranking changes. A sparse null result cannot support a broad efficacy claim.
4. Freeze a final execution manifest before inspecting holdout outcomes: exact code
   revision, split/model/configuration hashes, fit origins, user selection rule and
   size, seeds, candidate and seen-item rules, cohorts, metrics, paired comparisons,
   uncertainty procedure and compute-failure handling. Any changes after viewing
   holdout results must be reported as exploratory, not a new pristine test.
5. Preserve the legacy test file. Report the proposal-aligned event-count final
   15% with its 47,040 previously exposed validation events disclosed, and the
   untouched legacy-test intersection separately. Never label the full final 15%
   wholly unseen. Partition materialization must preserve stable timestamp/row order.
6. Evaluate all seven configurations on identical cases. Retain targetless cases,
   cold-start users and failed recommendations in headline denominators according
   to the shared evaluator. Report eligible-target metrics separately. Retain every
   per-user outcome needed to audit aggregate comparisons.
7. Apply the prespecified paired user bootstrap (2,000 resamples, seed 42) and
   declared multiplicity treatment; state the exact hypothesis comparisons before
   running them. Report cohort sizes and uncertainty, not only point estimates.
   Existing 200-user validation and density results remain development evidence.
8. Update the dissertation with measured outcomes, retained failures, exposure
   limits, chronological contamination disclosure and distinctions between the
   synthetic shop, operational service diagnostics and offline research results.

Current settings are in `data/processed/validation-tuning-v2/selected_config.json`:
fixed hybrid .50 content/.25 item-CF/.25 popularity; switching thresholds 2/10,
confidence .25 and CF weight .25. Their status remains validation-selected, not
final-test-frozen. No parameter change is justified merely to make switching win.

This checklist records unresolved release conditions; it is not a preregistration
claim or a substitute for a completed, committed execution manifest.
