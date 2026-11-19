## RetailIQ Commerce Studio — E-commerce Analytics & Recommendations

## Live Demo

[Explore the RetailIQ Dashboard](https://retailiq-ecommerce-analytics-ai.onrender.com/)

Free-hosted demo: The first load may take around 30–60 seconds while the server wakes up.

The default app reads the historical research artifacts in `data/processed/`. A separate synthetic-data generator is included for independent experiments. The interface displays the source recorded in the active summary file.

## Commerce Studio interface

[Open the live Commerce Studio dashboard](https://retailiq-ecommerce-analytics-ai.onrender.com/)

The plum, coral and lavender workspace includes product investigation, shopper analysis, side-by-side recommendations, offline model evaluation and CSV reporting. All displayed values come from the active data artifacts.

An interactive e-commerce analytics and product recommendation platform built using Python, FastAPI, machine learning, and modern web technologies.

### Features
- Commerce Studio interface in plum, coral and lavender, with responsive layouts
- Overview product investigation and actual offline method comparison
- Side-by-side visitor recommendations versus a popularity baseline
- Downloadable commerce report with source and metric definitions
- Customer behavior analytics
- Product performance insights
- Interactive visualizations
- Personalized product recommendations
- Machine learning performance evaluation
- Data processing and automated testing

**Live Demo:** https://retailiq-ecommerce-analytics-ai.onrender.com/

**Technology:** Python, FastAPI, Docker, Machine Learning, HTML/CSS/JavaScript

**Demo data:** The default packaged results describe historical Retailrocket shopping interactions. This is a portfolio research demonstration, not a client engagement or live store integration.

## Run on Windows

Open PowerShell inside this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. You do not need any original Retailrocket files. The app includes processed historical aggregates and a fitted recommendation model.

On macOS/Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

## Regenerate all synthetic data and model results

```bash
python scripts/generate_synthetic.py --output-dir synthetic_demo/input_data
python scripts/build.py --input-dir synthetic_demo/input_data --root synthetic_demo --max-items 240
```

The training pipeline converts event rows and historical item properties to aggregates; resolves category history at event time; trains implicit item-to-item recommendations; and applies a chronological 80/10/10 evaluation split. By default, the hosted app reads its packaged `data/processed/` files; to use freshly retrained synthetic outputs, copy the regenerated files from `synthetic_demo/data/processed/` to `data/processed/` or set `RETAILIQ_DATA_DIR` to that directory.

## Model evaluation for the default packaged data

| Model | Precision@5 | Recall@5 | Hit Rate@5 |
| --- | ---: | ---: | ---: |
| Popular items baseline | 0.0513% | 0.2209% | 0.2563% |
| Item-to-item similarity | 0.1291% | 0.4207% | 0.6264% |
| Category-aware blend | 0.1481% | 0.4736% | 0.7118% |

Results are on **10,536 eligible warm users** in the packaged historical test split. They indicate the ranking methods can be compared and evaluated, **not that these performance numbers will generalize to real e-commerce sites**. See [model evaluation](reports/model_evaluation.md) for definitions.

## Architecture

```text
Event/property CSVs (historical research data or separately generated synthetic data) → scripts/build.py
  ├── src/analytics.py (data preparation, aggregates, quality checks)
  ├── src/recommender.py (implicit feedback, similarity ranking, fallback)
  └── data/processed/ (precomputed tables, model, evaluation)
          ↓
      FastAPI app.py (JSON endpoints)
          ↓
      Static dashboard (HTML / CSS / JavaScript + Plotly)
```

Tech: **Python, pandas, SciPy/scikit-learn, FastAPI, Plotly, pytest, Docker**. Source files and model outputs are in this repository for easy reproducibility. Run automated tests with:

```bash
python -m pytest -q
```

## Run as a hosted web service

This is a FastAPI app, **not a Streamlit app**. For an ASGI hosting service, use:

```bash
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
```

A `Dockerfile` is included. Set any platform's exposed public port appropriately. Hosting may have a fee. Local testing is not a public deployment.

## Case study and limitations

See [client case study](reports/client_case_study.md). This project models event counts, not monetary revenue or causal conversion uplift. Product identifiers are anonymized; no product names or prices are available. The category blend results are improvements over a simple popularity baseline **within the packaged historical evaluation only**. A real customer deployment requires the customer's own event definitions, data permissions, privacy requirements, purchase-quality labels, model retraining, and monitoring.

## Data provenance and license

The default `data/processed/summary.json` identifies historical Retailrocket events as its source. The corresponding packaged evaluation uses 10,536 eligible test visitors. The separate `synthetic_demo/` workflow is an alternative dataset and must not be confused with the default deployment. `RETAILIQ_DATA_DIR` selects the active artifacts.

Research data attribution: [Retailrocket dataset and CC BY-NC-SA 4.0 source](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset). Code is supplied under the MIT license in `LICENSE`; that code license does not change the research dataset's permissions. Client deployments need appropriately permitted data and retraining.

**Portfolio scope:** A working e-commerce analytics application and offline top-five recommendation engine, with reproducible evaluation and API tests. Demo metrics are not client outcomes.
