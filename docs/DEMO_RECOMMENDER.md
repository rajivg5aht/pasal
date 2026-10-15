# Separate storefront switching recommender

Implemented 15 October 2026. Express sends only demo catalogue fields and anonymous
consented item profiles to authenticated local FastAPI. No demo input goes to Groq,
and no demo ID maps to a Retailrocket item. Research artifacts remain separate.

The adapter fits TF-IDF on synthetic titles, descriptions, categories and attributes.
Popularity is distinct-item support in consented profiles; item-CF uses cosine-
normalised co-occurrence. It reuses `switching.policy.recommend` with the serving
2/10 history thresholds, .25 confidence threshold and .25 CF weight. These settings
were selected on research validation data; transfer does not validate demo quality.

Zero-history users receive category/global popularity as evidence permits. One
event selects content; 2–9 select CF/popularity; at least ten with sufficient CF
confidence selects item-CF, otherwise the hybrid fallback. When no scored candidates
exist, an explicitly labelled deterministic catalogue fallback is returned. It is
not presented as a learned recommendation. No demo generation is claimed:
`genai_used` is false. The Research Lab retains the genuine GenAI experiment.

Only active, positive-stock products are eligible; full retained seen items are
excluded and Express rechecks live eligibility on hydration. Internal integer
positions are transient indexes into this demo catalogue, never research IDs.
Limits are 100 products, 5,000 latest updated consenting profiles, 20 recent distinct
items per profile and 1,000 seen items. The model is fitted per request from this
bounded snapshot; it is not a production incremental or population-wide model.

Version-1 consent explicitly permits personalisation and contribution to other
demo shoppers' co-viewing/popularity signals. Legacy category-only consent is
excluded. Reconfirming starts fresh history; withdrawal removes future contribution
and clears history/preferences while retaining operational cart, wishlist and orders.
Account IDs, emails and delivery details never enter the local recommendation payload.

Six Python fixtures cover content, CF, preferences, consent, eligibility, seen-item
filtering, honest fallback and invalid history/IDs. Backend integration checks
cover payload separation, legacy consent and fresh-history renewal. The live
diagnostic `backend/scripts/verify-demo-recommender.js` uses two labelled synthetic
accounts to verify actual content/hybrid/CF transitions, then clears their activity.
Its recorded results are engineering evidence, not research efficacy or a browser
walkthrough. Smaller catalogue, recent-profile sampling and transferred thresholds
must remain explicit limitations.
