# Client Case Study: E-commerce Analytics + Item Discovery

## 1. The business challenge

An e-commerce organization captures millions of events, but raw logs do not directly answer: Which products get attention? How many people engage with carts or purchase events? What categories account for product interest? Which products could an anonymous visitor explore next?

## 2. The solution

**RetailIQ Studio** combines an interactive dashboard with an offline product recommendation proof-of-concept. A scripted pipeline transforms more than 2.75 million events and two files of time-varying product properties into reusable aggregates and a trained recommendation index. The dashboard offers customer segments, product/category analysis, and top-five suggestions for sampled anonymous visitor histories.

## 3. Verified historical facts

- Shopping activity: **2,756,101** events from **1,407,580** unique visitors.
- Engagement: **2,664,312** views, **69,332** cart additions, **22,457** item-level transaction events.
- Purchase records contain **17,672** distinct transaction IDs.
- All original activity spans **May 3 to September 18, 2015**.
- A strict event-time category lookup linked **76.16%** of events to prior category snapshots.

## 4. Technical implementation

**Analytics** — Event quality checks, UTC normalization, deduplicated visitor reach, purchase item counts, distinct order IDs, category tree rollups, and exportable product leaderboards.

**Machine learning** — Implicit-feedback item similarity using sparse matrices and visitor co-interactions; popularity-based cold start; category-aware ranking; global chronological train/validation/test split.

**Delivery** — Responsive web interface with FastAPI-backed JSON API, shipped local Plotly visualizations, model and metric files, automated tests, GitHub Actions workflow, and deployment-ready Dockerfile.

## 5. Measured model results

The category-aware recommender reached a **0.7118%** top-five hit rate over **10,536** eligible warm users in the held-out test period, compared with **0.2563%** for the popularity baseline. This is an approximately **2.8× relative improvement** in an offline ranking metric, although performance remains low in absolute terms. This is **not evidence** of commercial sales improvement. Full reproducible metrics are in `model_evaluation.md`.

## 6. Business interpretation and next steps

A prospective client could use this approach to prioritize product-page investigations and measure browsing and cart activity from their own storefront event data. Personalized recommendations should first be evaluated for data coverage and product relevance, then tested online through a properly designed A/B test before making any uplift claims.

## 7. Scope and integrity statement

This is a **self-directed demonstration project**, not a commissioned engagement or real-time production integration. Product names, sales prices, revenue, and monetary outcomes are not in the data. Data were originally published for research and are **CC BY-NC-SA 4.0**; commercial deployments must use licensed data or new client-provided data and a retrained model.
