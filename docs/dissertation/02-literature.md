# 2 Related work and design rationale

## 2.1 Conventional components and hybridisation

Sarwar et al. (2001) investigate item-based collaborative recommendation as an
alternative to user-neighbourhood methods, with attention to recommendation quality
and scalability. This provides a basis for including item-CF in Pasal. The paper's
results do not establish how Pasal's weighted implicit events, sparse profiles or
historical candidate constraints will behave; those require local evaluation.
An item-CF component is therefore a baseline and an available switching branch,
not an assumed solution to every cold-start case.

TF-IDF provides a transparent content baseline: term weights reflect within-document
frequency and inverse collection frequency, while cosine similarity compares
normalised vectors (Manning, Raghavan and Schütze, 2008). In Pasal the tokens encode
properties rather than readable retail descriptions. Similarity in this space
means shared encoded evidence, not necessarily similarity that a customer would
recognise. This distinction also limits the interpretation of diversity measured
using the same property vectors.

Burke (2002) surveys hybrid recommendation and demonstrates that combining
recommendation evidence can improve a system in a particular setting. It motivates
comparison between combinations, rather than a universal claim that hybrids win.
Pasal operationalises the distinction between a fixed weighted combination and a
history-dependent selection rule. Its thresholds and weights are chosen using
validation evidence. The fixed hybrid remains a serious comparator: a more complex
controller is not preferred merely because it is adaptive in design.

## 2.2 Temporal validity and dataset semantics

Ji et al. (2023) show that recommendation evaluation can leak future information
when the global interaction timeline is not respected, and that leaked information
can affect comparisons between models. The relevance to Pasal is methodological:
both model fitting and metadata must precede the prediction origin. A chronological
event split alone is insufficient if item properties are reconstructed from later
observations. This study consequently records cutoffs and hashes for both events
and metadata. Earlier validation exposure is disclosed rather than erased by
renaming a partition.

The Retailrocket publisher describes time-dependent item properties and anonymised
values, with explicit category identifiers and availability flags. The dataset has
2,756,101 interactions and includes views, cart additions and transactions
(Retailrocket, n.d.). This supports implicit-feedback experimentation, but it does
not provide a trustworthy mapping from anonymous item IDs to contemporary product
names, brands or images. Pasal's synthetic shop is separate for this reason. The
published schema also explains why a historical availability flag must not be
presented as current purchasability.

## 2.3 Generative models within recommendation pipelines

Lin et al. (2024) organise language-model integration across recommendation stages,
including feature engineering, representation, ranking, interaction and control.
Their taxonomy helps specify Pasal's narrower intervention: the language model
contributes reviewed catalogue text while conventional components retain ranking
control. The survey identifies effectiveness, efficiency and ethical challenges;
it does not justify assuming that anonymous numeric metadata contains recoverable
retail semantics.

Pasal's design therefore tests a limited question: does source-grounded generated
text add useful signal to the existing property representation under the available
metadata and budget? Generation that merely repeats codes may pass grounding review
yet add little information. Generic repeated prose may also increase similarity
between otherwise unrelated items. These are plausible mechanisms to investigate,
not observed causal explanations until supported by measured exposure and rankings.
The ablation keeps the ordinary feature block and uses the same items and candidates
so that changed treatment coverage cannot silently redefine the task.

## 2.4 Synthesis and study boundaries

The literature motivates complementary recommendation evidence, explicit temporal
control and careful specification of where generation enters a system. Pasal brings
these requirements together in a reproducible, resource-constrained prototype.
The defensible research question is comparative effectiveness under this dataset
and protocol. It is not whether language models can reconstruct hidden identities,
whether switching always outperforms a fixed hybrid, or whether a Kathmandu-themed
interface establishes local-market generalisability.

This chapter is a focused verified foundation. The final literature chapter should
also integrate the approved proposal's existing cited studies after checking each
source and its relevance; no unverified proposal citation is treated as confirmed
merely because it was previously included.
