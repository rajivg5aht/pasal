# GenAI exposure and feasibility plan

Recorded 13 October 2026, before implementing the analysis or selecting a new
generation batch. Preserve the seven approved configurations and existing runs.

1. Read only the original training events, historical catalogue, selected policy
   and prior aggregate API evidence. Verify training and catalogue fingerprints
   against their existing manifests; reject events at or after the cutoff.
2. Measure content-route training users and their recent unique profile items.
   Zero-history users cannot obtain a content profile. Historical unavailable
   items remain in histories but are excluded from this candidate-enrichment pool.
3. Compare nested uniform eligible-catalogue samples with deterministic samples
   ordered by distinct content-route training users per item, ties by item ID.
   Sizes are 32, 128, 256 and 512; seed 42. No validation/test outcomes or
   assessment user identities enter selection. Targeted coverage is in-sample
   engineering feasibility, not a generalization estimate or representative survey.
4. Report raw training-profile exposure, category breadth, estimated workload
   and source fingerprints. Exposure is an upper bound on successful reviewed
   enrichment; generation failures and rejection can reduce it. Profile exposure
   alone does not establish ranking changes or benefit.
5. Check Groq's published Free limits and retain conservative local guards.
   Keep estimated successful-output usage separate from unknown failure usage.
   No paid fallback, remote calls or credentials are needed for this analysis.
6. Test selection determinism, raw-event routing, future-event rejection and
   duplicate/cutoff checks; run on actual training data. Record results before
   choosing the next sample. Freeze any chosen sample before generation.

Deliverables: reproducible analysis command, regression fixtures, versioned local
sample IDs, tracked aggregate feasibility report, and an evidence-based next
experiment decision. Independent quality ratings and the final holdout remain
separate outstanding requirements.

## Decision after measured feasibility

The completed training-only analysis found 697,327 content-route users, of whom
192,010 have an eligible historical profile item. At 128 items, uniform sampling
touches 293 users (0.042%); selection by distinct low-history user support touches
20,290 (2.91%), across 73 known categories. Even this higher figure remains small
and assumes every selected generation is approved. It is not future-user coverage.

Choose the 128-item training-support sample as a bounded development intervention,
preserving the separate 32-item uniform quality study. The 256/512 alternatives
have diminishing coverage gains and at least six/eleven fresh local quota windows.
The chosen sample reserves 464,751 tokens under the existing conservative guard,
so needs at least three fresh daily windows; packing and shared usage can add time.
Observed pilot usage averaged 953.5 tokens for the 24 usage-known attempts;
eight failures have unknown usage. Do not replace reservations with that average.

Groq's Free limits for GPT-OSS 20B were checked on 13 October 2026: 30 requests/min,
1,000/day, 8,000 tokens/min and 200,000/day. Keep local guards at 20, 900, 7,000 and
180,000 respectively. Source: https://console.groq.com/docs/rate-limits.

Freeze exact catalogue records and source hashes before API calls. Keep the same
model, prompt, output cap and source-only payload. Start with at most eight new
requests; stop on authentication, transport or quota failure, preserve cached
outcomes, and never automatically retry failed items or switch to paid usage.
Review generated outputs before fitting a new enriched artifact. The selected
items are a targeted intervention: do not pool its quality estimate with the
uniform study or present its conditional exposure as population effectiveness.
Retain the existing unconditional assessment and report actual route/profile
exposure when the new artifact is ready; do not change thresholds to force benefit.
