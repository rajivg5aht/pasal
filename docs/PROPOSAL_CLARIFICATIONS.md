# Supervisor clarification note

**Superseded on 12 October 2026:** implementation decisions are now delegated by
the supervisor through the user. See `RESEARCH_DECISIONS.md` for the selected
interpretations. The options below are retained as historical documentation.

Prepared 11 October 2026. Page references are printed pages (PDF page = +1).
The user confirmed the seven configurations on 11 October. Figure 11's extra
user-user CF/BERT4Rec references will not expand the approved methodology.

## 1. Preserve holdout integrity while addressing the split mismatch

The approved p. 11 split allocates 70/15/15 of chronological events. Existing code
uses elapsed-time percentages, producing about 73.44/13.27/13.29 of events.
Training and validation date ranges are separate, but rows inside them are not
sorted. The row-order bug is now corrected in content history construction.

Recreating a straightforward event-count split would place **47,040 events
already used as validation into the new test period**. Existing validation
exposure cannot be undone by changing filenames. The original test CSV has not
been opened, evaluated or modified in this audit.

Please choose between these approaches, or specify another defensible protocol:

1. Preserve the untouched original test boundary and approve/document the
   deviation from exact event proportions; repair development processing inside
   the remaining data. This protects the historical final holdout.
2. Create a new version with the approved event-count split, disclose prior
   validation exposure explicitly, and agree how independent final evidence will
   be established. Do not call its entire test partition previously unseen.

No existing split has been regenerated. The user requested both options for
supervisor review, not an automatic selection.

## 2. Figure 5's hybrid components (p. 14)

The middle-history branch says "Fixed weighted hybrid (CB + Popularity)" but its
legend defines CB as collaborative filtering. The low-confidence fallback says
"Combine collaborative (CB) and popularity signals". Existing prototype code
uses popularity, content and CF together. Please confirm the intended components
for the fixed baseline, middle-history branch and low-confidence fallback.

The readable branch order is n=0 -> onboarding/global route; 0<n<T1 -> content;
T1<=n<T2 -> fixed hybrid; n>=T2 -> confident CF or hybrid fallback. Thresholds
must be validation-selected; cohort boundaries must not be treated as thresholds.
The no-history "Global category popularity" label and unspecified new-item
exposure cap also need an explicit interpretation before final policy tuning.

## 3. Final evaluation operational definitions

Figure 11 (p. 19) mentions leave-one-out and multiple splits, while p. 11 fixes a
chronological holdout. Treat these as unresolved evaluation notes, not permission
to alter the main protocol. Confirm their intended role if required.

Clarify Figure 11's >=15% ranking improvement and <=15% degradation targets
relative to H1/H2's wording; define disproportionate latency/cost and whether
the example <800 ms P95 target is binding. Predeclare paired statistical testing,
confidence intervals, repeated-seed treatment and switching-accuracy definition.
Targets are not guaranteed results; negative findings must be reported honestly.

## 4. GenAI grounding and assessment

Retailrocket category/property IDs are anonymized. Generated claims about brand,
material, function, price or Nepal-specific products are not supported by those
IDs. The pipeline must preserve source evidence, distinguish genuine provider
outputs from property processing, validate generated statements and report weak
semantic information as a limitation. A representative enrichment subset is
permitted by p. 18; it must use reproducible selection and matching ablations.

External GenAI receives catalogue metadata only (p. 20); histories and identity
remain local. A human explanation-quality study needs the applicable ethical
approval and consent. Confirm the assessment approach early enough for week 3.
