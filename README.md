# Pasal — Generative AI-Enhanced Hybrid Recommender System

A thesis project that builds a **hybrid recommendation engine** combining popularity-based, content-based, collaborative filtering, and Generative AI enrichment techniques. Evaluated on the [Retail Rocket](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset) e-commerce dataset.

---

## Project Structure

```
pasal/
├── frontend/               # React / Next.js frontend (coming soon)
├── backend/                 # API server (coming soon)
├── recommendation-engine/   # Core recommendation algorithms
│   ├── models/
│   │   ├── popularity/      # Weighted popularity recommender
│   │   ├── content/         # TF-IDF content-based recommender
│   │   ├── collaborative/   # Collaborative filtering (WIP)
│   │   ├── hybrid/          # Hybrid ensemble (WIP)
│   │   └── switching/       # Switching strategy (WIP)
│   ├── preprocessing/       # Data cleaning and feature engineering
│   ├── evaluation/          # Offline evaluation scripts
│   ├── genai/               # Generative AI enrichment module
│   └── requirements.txt     # Python dependencies
├── data/                    # Dataset directory (NOT committed — see below)
├── docs/                    # Thesis documents and diagrams
├── .gitignore
├── .env.example             # Environment variable template
└── README.md                # ← You are here
```

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** (for the frontend, when ready)
- **Git**

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/rajivg5aht/pasal.git
cd pasal
```

### 2. Set up a Python virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r recommendation-engine/requirements.txt
```

### 4. Obtain the Retail Rocket dataset

Download the dataset from [Kaggle](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset) and place the CSV files in:

```
data/raw/
├── category_tree.csv
├── events.csv
├── item_properties_part1.csv
└── item_properties_part2.csv
```

### 5. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 6. Run preprocessing

```bash
python recommendation-engine/preprocessing/inspect_data.py
python recommendation-engine/preprocessing/preprocess_item_properties.py
python recommendation-engine/preprocessing/preprocess_categories.py
python recommendation-engine/preprocessing/build_item_features.py
python recommendation-engine/preprocessing/create_splits.py
```

### 7. Train models

```bash
# Popularity-based
python recommendation-engine/models/popularity/popularity.py

# Content-based (TF-IDF)
python recommendation-engine/models/content/content_based.py
```

### 8. Evaluate

```bash
python recommendation-engine/evaluation/evaluate_popularity.py
```

## Models

| Model | Status | Description |
|-------|--------|-------------|
| Popularity | ✅ Done | Weighted interaction scoring (view=1, cart=3, buy=5) |
| Content-Based | ✅ Done | TF-IDF on category-tree tokens |
| Collaborative | 🔧 WIP | User-item collaborative filtering |
| Hybrid | 🔧 WIP | Ensemble of all models |
| GenAI Enriched | 🔧 WIP | LLM-enhanced item representations |

## Tech Stack

- **Python** — pandas, scikit-learn, scipy, joblib
- **React / Next.js** — frontend (planned)
- **Node.js** — backend API (planned)

## Dataset

This project uses the **Retail Rocket** e-commerce dataset (~1 GB). The raw data files are **not included** in the repository. See step 4 above for download instructions.

## Author

**Rajiv Ganesh** — Thesis project

## License

This project is part of an academic thesis. All rights reserved.
