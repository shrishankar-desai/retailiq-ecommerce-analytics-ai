## RetailIQ — E-commerce Analytics & AI Recommendation System

**[View Live Interactive Dashboard](https://retailiq-ecommerce-analytics-ai.onrender.com/)**

An interactive e-commerce analytics and product recommendation platform built using Python, FastAPI, machine learning, and modern web technologies.

### Features
- Customer behavior analytics
- Product performance insights
- Interactive visualizations
- Personalized product recommendations
- Machine learning performance evaluation
- Data processing and automated testing

**Live Demo:** https://retailiq-ecommerce-analytics-ai.onrender.com/

**Technology:** Python, FastAPI, Docker, Machine Learning, HTML/CSS/JavaScript

**Demo Data:** The publicly hosted demonstration uses synthetic data. Results are illustrative and do not represent actual client business performance.

## Run on Windows

Open PowerShell inside this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. You do not need any original Retailrocket files. The app includes synthetic processed data and a separately fitted synthetic-data model.

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

## Model evaluation on fictional data

| Model | Precision@5 | Recall@5 | Hit Rate@5 |
| --- | ---: | ---: | ---: |
| Popular items baseline | 2.468% | 3.716% | 11.915% |
| Item-to-item similarity | 7.128% | 10.826% | 31.170% |
| Category-aware blend | 7.149% | 10.853% | 31.277% |

Results are on **940 eligible warm users** in the synthetic test split. They indicate the ranking methods can be compared and evaluated, **not that these performance numbers will generalize to real e-commerce sites**. See [model evaluation](reports/model_evaluation.md) for definitions.

## Architecture

```text
Synthetic event/property CSVs (generated) → scripts/build.py
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

See [client case study](reports/client_case_study.md). This project models event counts, not monetary revenue or causal conversion uplift. Product identifiers are fictional; no product names or prices are available. The category blend results are improvements over a simple popularity baseline **within the generated dataset only**. A real customer deployment requires the customer's own event definitions, data permissions, privacy requirements, purchase-quality labels, model retraining, and monitoring.

## Data provenance and license

This GitHub-ready portfolio demo was built by retraining on **independently generated synthetic data**. It contains **no original Retailrocket records or Retailrocket-derived aggregates or fitted model**. The broader original project was inspired by the Retailrocket public e-commerce research dataset: [source and CC BY-NC-SA 4.0 attribution](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset). That research dataset is not included here and is not permission for a commercial deployment.

Code is supplied under the MIT license in `LICENSE`. Data in the public demo is fictional and independently generated for this sample application.

**Suggested portfolio claim:** "Built a working e-commerce analytics dashboard and offline top-five recommendation engine, with reproducible synthetic-data evaluation and API tests." Do not describe demo metrics as client outcomes.
