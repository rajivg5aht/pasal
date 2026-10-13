# Reproducing the GenAI development comparison

Run from the repository root in PowerShell using the existing virtual environment.
Install its UTF-8 pinned requirements when preparing a new environment. The full
historical catalogue, property matrix, CF matrix and validation tuning outputs
must already exist; these large artifacts remain local and are not GitHub files.
Never substitute the legacy all-time matrices or final test data in these commands.

## Generate and review

The frozen sample is `data/processed/genai-quality-sample-v1`. Its declaration is
tracked in `docs/genai-quality-sample-manifest.json`. Do not redraw it after seeing
failures. Resume only unsent records, keeping the existing cache and quota ledger:

```powershell
.venv\Scripts\python.exe recommendation-engine/genai/run_free_batch.py --sample data/processed/genai-quality-sample-v1 --cache data/enriched/groq-free-v1 --max-new-requests 32 --live --skip-recorded-failures
```

The batch loads only GROQ_API_KEY and GROQ_ACCOUNT_TIER from ignored `.env`.
It requires the user-verified Free account. Never delete failed cache entries to
force retries or change the sample membership. Compare each successful description
with its exact source before recording a review; see GENAI_QUALITY_PROTOCOL.md.
Reviews remain local at `data/processed/genai-quality-sample-v1/reviews.jsonl`.

## Train and evaluate

Use new output version directories when repeating a run; commands deliberately
refuse to overwrite prior evidence. The example paths below identify the first
run and should be reused for inspection once they exist, not overwritten.

```powershell
.venv\Scripts\python.exe recommendation-engine/genai/quality_report.py --sample data/processed/genai-quality-sample-v1 --cache data/enriched/groq-free-v1 --reviews data/processed/genai-quality-sample-v1/reviews.jsonl --output data/processed/genai-quality-sample-v1/quality-report.json
.venv\Scripts\python.exe recommendation-engine/models/content/train_enriched.py --catalogue data/processed/metadata-event-count-v1/catalogue.jsonl --base-dir data/processed/content-event-count-v1 --sample-dir data/processed/genai-quality-sample-v1 --cache-dir data/enriched/groq-free-v1 --reviews-path data/processed/genai-quality-sample-v1/reviews.jsonl --output data/processed/content-genai-quality-v1
.venv\Scripts\python.exe recommendation-engine/evaluation/paired_genai.py --train data/splits/event-count-v1/train.csv --validation data/splits/event-count-v1/validation.csv --content-dir data/processed/content-event-count-v1 --enriched-dir data/processed/content-genai-quality-v1 --cf-dir data/processed/cf-event-count-v1 --tuning-dir data/processed/validation-tuning-v1 --output data/processed/paired-genai-quality-v1
```

The comparison reuses the selected development settings and disjoint assessment
users. It reports all seven configurations, paired bootstrap uncertainty and
actual enrichment exposure. A zero difference from a tiny partial treatment is
not a final negative H2 result. No final holdout is opened by these scripts.

## Optional serving

The default website serves the established property-only switching model.
After verifying the enriched artifacts, set PASAL_ENRICHED_ARTIFACT_DIR locally
to their absolute directory and restart the recommender to inspect that condition.
This explicit setting does not silently replace the baseline. Serving verifies
artifact hashes and displays only reviewed descriptions, separately labelled from
the local ranking reason. It makes no live GenAI calls during browsing.
