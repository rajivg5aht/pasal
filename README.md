# Pasal

**Generative Artificial Intelligence-Enhanced Hybrid Recommender System for Cold-Start Mitigation in Online Retail**

Undergraduate thesis research prototype by **Rajiv Ganeju**. Pasal studies validation-tuned switching among traditional recommenders, with Generative AI limited to grounded catalogue enrichment and explanations. Retailrocket is the research dataset; Kathmandu is the intended demonstration context.

## Current state

The React storefront, Express commerce API and FastAPI recommendation service are implemented. The separate synthetic Kathmandu catalogue supports customer accounts, persistent wishlist/cart, demonstration checkout, order history and protected administrator operations. Demo recommendations use consented demo evidence; Retailrocket research IDs and experiments remain separate.

All seven research configurations and validation tuning are implemented. Genuine Groq Free catalogue generation is in progress: at the latest reviewed checkpoint, 98/128 targeted items were attempted, 41 outputs approved, 28 grounding-rejected and 29 generation failures retained. **Property processing alone is not GenAI; assistant grounding screening is not independent human review.** Final holdout evaluation and dissertation completion remain outstanding. Development scores are not final hypothesis evidence.

- [Local startup, customer/admin use and limitations](docs/PASAL_OPERATOR_GUIDE.md)
- [Latest verified progress](docs/STATUS_2026_10_15.md)
- [Final evaluation protocol](docs/FINAL_EVALUATION_RUNBOOK.md)
- [Separate demo recommender](docs/DEMO_RECOMMENDER.md)
- [Commerce deployment and preserved database](docs/COMMERCE_DEPLOYMENT.md)

The active checkout database is the approved local replica set on port 27018.
`compose.yaml` starts only the original standalone MongoDB on port 27017; it is
not the current checkout deployment or a complete application launcher. Follow
the operator guide. Do not replace the existing database or rerun migration.

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
$env:OPENBLAS_NUM_THREADS='1'
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

The approved stack is React/TypeScript/Vite/Tailwind, Node/Express, Python/FastAPI and MongoDB. Frontend and backend contain the working application. Use `.env.example` for configuration names; never commit credentials. The approved batch runner loads only `GROQ_API_KEY` and `GROQ_ACCOUNT_TIER` from the local root `.env`, without printing them. Quota exhaustion stops generation; cached failures are preserved.

Seven intended configurations: global popularity, category popularity, TF-IDF, item-CF, tuned fixed hybrid, switching without GenAI, switching with GenAI. Use validation for tuning and freeze decisions before final testing. The versioned event-count protocol explicitly marks historical test exposure and reserves the untouched subset for separate confirmatory reporting; see the research decision record.

Keep credentials, raw datasets, large generated artifacts and environments outside tracked source. Report measured, implemented and planned work separately. This is an academic research prototype, not a production retail system.

All rights reserved.
