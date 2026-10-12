# Pasal

**Generative Artificial Intelligence-Enhanced Hybrid Recommender System for Cold-Start Mitigation in Online Retail**

Undergraduate thesis research prototype by **Rajiv Ganeju**. Pasal studies validation-tuned switching among traditional recommenders, with Generative AI limited to grounded catalogue enrichment and explanations. Retailrocket is the research dataset; Kathmandu is the intended demonstration context.

## Current state

Existing work includes preprocessing, global popularity, original and property-enhanced TF-IDF models, sampled item-CF, an untuned fixed-hybrid demonstration and preliminary evaluations. **Property-enhanced features are not GenAI.** The current pass adds an artifact audit, correctness repairs, regression tests, timestamp-preserving metadata preparation and a real API-backed GenAI integration with reviewed feature export. Live GenAI runs await API access.

The switching policy and shared cohort evaluator are implemented and tested; model integration/tuning, final experiments and the integrated website are not complete. Existing split/metadata issues prevent treating preliminary scores as final thesis evidence.

- [Project status and handover](PROJECT_STATUS.md)
- [Detailed audit](docs/PROJECT_AUDIT.md)
- [Approved-requirement traceability](REQUIREMENTS_TRACEABILITY.md)
- [Continuous execution backlog and original capacity plan](IMPLEMENTATION_PLAN.md)
- [Resolved research decisions](docs/RESEARCH_DECISIONS.md)
- [GenAI integration and safeguards](recommendation-engine/genai/README.md)

## Existing environment and checks

Reuse the existing Python 3.12 virtual environment. From the project root:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s recommendation-engine/tests -v
.\.venv\Scripts\python.exe -m compileall -q recommendation-engine
```

The dependency pins describe the existing development environment. A fresh installation has not yet been verified. The standard-library tests are also compatible with Pytest discovery when that planned test tool is installed.

## Safe diagnostic commands

Choose new output paths; historical outputs are preserved:

```powershell
.\.venv\Scripts\python.exe recommendation-engine/evaluation/audit_existing_artifacts.py --output docs/audit-next.json
.\.venv\Scripts\python.exe recommendation-engine/evaluation/evaluate_content_comparison.py --output-dir data/processed/content-check-next --max-users 100
```

The content comparison uses one shared validation sample and saves aggregate/per-user metrics, recommendations and a manifest. It excludes zero-history users and uses legacy artifacts. It is a representation diagnostic, **not** the final cold-start or seven-configuration experiment. Neither command reads the final test CSV.

Avoid rerunning legacy preprocessing/training over existing files: split and metadata repairs require a versioned protocol. Other legacy smoke/evaluation scripts still overwrite their default CSV output paths.

## Data and approved architecture

The existing raw data, processed artifacts and splits are stored under `data/` and ignored by Git. Dataset source: [Retailrocket on Kaggle](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset). No redownload is needed on the current machine.

The approved stack is React/TypeScript/Vite/Tailwind, Node/Express, Python/FastAPI and MongoDB. Frontend/backend directories remain placeholders. `.env.example` reserves settings; the GenAI CLI reads its key from the local process environment, not automatically from `.env`.

Seven intended configurations: global popularity, category popularity, TF-IDF, item-CF, tuned fixed hybrid, switching without GenAI, switching with GenAI. Use validation for tuning and freeze decisions before final testing. The versioned event-count protocol explicitly marks historical test exposure and reserves the untouched subset for separate confirmatory reporting; see the research decision record.

Keep credentials, raw datasets, large generated artifacts and environments outside tracked source. Report measured, implemented and planned work separately. This is an academic research prototype, not a production retail system.

All rights reserved.
