# 1 Introduction

## 1.1 Research problem

Pasal examines recommendation under limited behavioural evidence. A new visitor
has no interaction history from which to estimate individual interests. A visitor
with a few interactions offers some evidence, but that evidence may be insufficient
for reliable collaborative neighbourhoods. A fixed combination of recommendation
components applies the same weighting rule across these situations. This project
investigates whether an explicit, validation-tuned switching rule can allocate
different components according to the evidence available for each user.

The project also examines a constrained role for Generative AI. Generated catalogue
descriptions can change the content representation, but they cannot legitimately
recover product identities from anonymous codes without supporting evidence. The
study therefore distinguishes generation from factual recovery. It evaluates a
reviewed generated-text extension to the ordinary property representation rather
than assuming that fluent text improves ranking.

Pasal combines an offline Retailrocket experiment with an interactive e-commerce
research prototype. The customer demonstration is oriented towards Kathmandu,
while the research dataset is historical and does not establish a Nepalese user
population. Separate synthetic demonstration products make the shopping interface
understandable without pretending that an anonymous research item is a known brand
or product. This separation is part of the research validity boundary.

## 1.2 Aim and research questions

The aim is to implement and evaluate an explainable switching hybrid recommender
with genuinely generated metadata while preserving temporal validity, user control
and transparent provenance. The approved proposal asks how validation-tuned
switching compares with conventional and fixed-hybrid baselines across user-history
cohorts and reduced interaction density. Its ethical question concerns safeguards
for proportionate use of behavioural evidence and generated content.

H1 concerns users with 1–19 historical interactions: switching should improve mean
NDCG@10 over the strongest non-switching baseline, remain robust when training
interaction density decreases, and avoid disproportionate API latency increases.
H2 concerns users with 0–19 historical interactions: generated metadata should
improve NDCG@10 over the equivalent non-generative switching configuration without
disproportionate end-to-end latency or per-request cost. These are empirical claims
to assess, not implementation acceptance criteria that must be made true.

The ranking components are global popularity, category popularity, TF-IDF content
similarity and item-based collaborative filtering. The comparisons add a tuned
fixed hybrid and switching with and without generated metadata, giving seven
configurations. The study does not introduce extra algorithms to replace those
specified in the approved methodology.

## 1.3 Scope and contribution

The technical contribution is an auditable integration of chronological data
preparation, historical metadata, reproducible recommenders, a transparent switching
policy, constrained generation, and an interactive consent-controlled application.
The experimental contribution depends on the final measured comparisons. Novelty
is not claimed merely because the application combines familiar algorithms or
uses a language model.

Evaluation includes relevance at rank ten, catalogue coverage, common-feature-space
diversity, interaction-density sensitivity, generation failures and usage, and
service latency. Offline ranking and operational website measurements answer
different questions and are reported separately. The generation study separates
schema reliability, assistant grounding screening and independent human quality
ratings; the last of these remains deferred and must not be implied by the others.

The prototype supports accounts, explicit consent, preference and history reset,
wishlist, cart and restricted administration. Synthetic prices and illustrations
serve a demonstration purpose. Real payments, fulfilment and verified live inventory
are outside scope. No demonstration interaction is appended to the frozen research
experiments.

## 1.4 Dissertation status and structure

This chapter is part of the evidence-based draft. Final ranking results and the
completed generation sample are still required before a submission abstract and
final hypothesis conclusions can be written. The intended structure proceeds from
related work to methodology, implementation, results, discussion and conclusion.
Historical development results remain identified as such even after final results
become available. The repository retains the original proposal and versioned
evidence so that changes in implementation can be distinguished from changes in
the approved research approach.
