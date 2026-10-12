# Approved-requirement traceability

Updated 12 October 2026. Printed proposal pages below; PDF page is +1.
The user's current instruction confirms the seven methodology configurations.

| Requirement | Proposal source | Implementation / verification | Audit status |
|---|---|---|---|
| New-user cold start; secondary new-item cold start | pp. 5-9 | Evidence-aware switching, cohort results | Baseline foundation only |
| Literature and research gap | pp. 8, 12-13 | Dissertation/reference audit | Proposal present; Zhao 2024 and Zhang 2025 entries missing |
| DSRM, CRISP-DM, Agile | p. 10 | Requirement-driven build/test/evidence cycles | Retained in plan |
| Retailrocket interactions/properties/categories | p. 11, Fig. 4 | Raw files, preprocessing, provenance | Present; audited; temporal repair required |
| 70/15/15 chronological event split | p. 11 | Split manifest, disjointness/time checks | Versioned event-count development split built; historical exposure documented; final test deferred |
| GenAI metadata before splitting; cached/versioned; no future behavior | p. 11, Fig. 4 | Catalogue-only generation, point-in-time features, cache | Free Groq adapter/cache/reviewed export tested; One genuine Free API pilot completed with assistant grounding review; representative evaluation pending |
| Cohorts 0 / 1-4 / 5-19 / 20+ | p. 11 | Raw event-count cohorts independent of model coverage | Common evaluator implemented; 1,000-user development diagnostic covers all cohorts |
| Densities 10 / 25 / 50 / 100 percent | p. 11 | Reproducible train-only samples and manifests | Not implemented |
| Global popularity | p. 15 | Exact training-score reconstruction | Implemented; current scores verified |
| Category popularity | p. 15 | Category rankings and fallback/eligibility tests | Implemented in this pass; fixture-tested; full evaluation pending |
| TF-IDF content | p. 15 | Models, unique IDs, sampled vector reconstruction | Corrected-cutoff snapshot and TF-IDF trained; 24 empty rows documented; ranking evaluation pending |
| Item-CF | p. 15 | Similarities, common-cohort results | Sample prototype only |
| Tuned fixed hybrid | p. 15 | Normalization, candidate alignment, validation tuning | One-user untuned prototype; seen filtering repaired |
| Switching without GenAI | pp. 14-15, Fig. 5 | Branch tests, validation thresholds, coverage/confidence | Policy and branch tests implemented; decisions recorded; validation tuning pending |
| Switching with genuine GenAI | p. 15 | Matching no-GenAI/GenAI ablation | Missing at audit baseline; integration work follows |
| Sensitivity and frozen thresholds before testing | pp. 14-15 | Tuning manifest and locked configuration | Missing |
| Explanations and transparent decision factors | pp. 14, 17, 20 | Local rationale and grounded AI-assisted explanation | Local explanation composition implemented; live reviewed descriptions and UI integration pending |
| React/TypeScript/Vite/Tailwind | p. 16 | Responsive storefront and Vitest/RTL checks | Frontend directory empty at audit baseline |
| Node/Express, Python/FastAPI, MongoDB | pp. 16-17 | Real services, schemas, API/database integration tests | Not implemented at audit baseline |
| Consent, provenance, preference reset, opt-out | pp. 8, 17, 20 | Backend-enforced consent/event/reset tests | Missing |
| Availability and eligibility constraints | Fig. 8, p. 17 | Temporal candidate filters; live inventory rules | Missing |
| Dataset/model/prompt/decision/latency logs | p. 17 | Versioned manifests and privacy-aware telemetry | Diagnostic manifests added; service logging missing |
| Precision/Recall/NDCG/MAP/Hit Rate | Fig. 11, p. 19 | Hand-calculated metrics, per-user results | All five implemented with hand-calculated fixtures; final comparisons pending |
| Catalogue coverage, diversity, robustness | pp. 8, 15, Fig. 11 | Defined candidate denominator and density/missing-metadata tests | Preliminary union coverage only |
| Switching accuracy, gain, win rate | Fig. 11 | Predeclared definitions and paired results | Missing |
| GenAI relevance/consistency/hallucination/alignment | Fig. 11 | Source-grounding validation and approved rating rubric | Missing; not inferable from API schema compliance |
| Response time, throughput, P95, top-K generation | Fig. 11 | Measured load/burst/concurrency tests | Missing |
| Cost, tokens, CPU, memory | Fig. 11 | Real usage and amortized offline/request costs | Missing |
| Significance, confidence intervals, reproducibility | Fig. 11 | Paired analysis, seeds and replay | Diagnostic evidence added; final analysis missing |
| Privacy/fairness/transparency/user-control audit | RQ2 p. 9, p. 20 | Cohort/coverage/popularity bias and safeguard checks | Missing |
| Catalogue-only external GenAI; no sensitive profiling | p. 20 | Payload allowlist, privacy-negative tests | Required integration constraint |
| Pytest/Vitest/RTL/Git/Docker | p. 16, Fig. 8 | Automated tests and reproducible setup | Git pushes + 45 unittest checks (pytest-compatible); service/UI/Docker checks pending |
| Honest research-prototype claims | pp. 20-21 | Separate implemented/measured/planned statements | Audit/status records; final dissertation pending |

Figure 11 targets to retain and evaluate, not claim achieved: >=15% NDCG/Recall
gain over best baseline; better cold-start precision/coverage and switching gain;
explanation relevance >=4/5, consistency >=90%, hallucinations <=5%; acceptable
P95 (example <800 ms); <=15% high-sparsity performance drop; lower API/token cost;
reproducible, statistically evaluated findings. Operational ambiguities are in
`docs/RESEARCH_DECISIONS.md`. Never manipulate experiments to meet targets.
