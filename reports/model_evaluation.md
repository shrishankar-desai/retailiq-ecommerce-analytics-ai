# Model Evaluation — RetailIQ Studio

Evaluation generated from all uploaded raw event records; UTC timestamps. The training pipeline is fully reproducible with `python scripts/build.py --input-dir input_data`.

| Parameter | Observed |
|---|---|
| Training cutoff | 2015-08-18 04:23:31.966 UTC |
| Validation cutoff | 2015-09-02 17:49:11.563 UTC |
| Training events | 2,204,881 |
| Validation events | 275,610 |
| Test events | 275,610 |
| Model candidate catalog | 8,000 products |
| Eligible warm validation users | 12,766 |
| Eligible warm test users | 10,536 |

## Results

| Split | Model | Precision@5 | Recall@5 | Hit Rate@5 | Coverage* |
|---|---|---:|---:|---:|---:|
| Validation | Popularity | 0.0345% | 0.1442% | 0.1723% | 0.0750% |
| Validation | Item similarity | 0.1441% | 0.4175% | 0.6972% | 73.7375% |
| Validation | Category blend | 0.1833% | 0.5374% | 0.8852% | 53.8875% |
| Test | Popularity | 0.0513% | 0.2209% | 0.2563% | 0.0750% |
| Test | Item similarity | 0.1291% | 0.4207% | 0.6264% | 71.3375% |
| Test | Category blend | 0.1481% | 0.4736% | 0.7118% | 50.8375% |

*Coverage is the share of the **8,000-item training catalog** appearing across evaluated top-five lists, not the share of all 235,061 products in the source dataset.*

### Formal definitions

For an eligible visitor *u*, let R(u) be the five unseen items the system recommends and T(u) be the **distinct future items not already in that visitor's training history**.

- Precision@5 = mean over users of `|R(u) ∩ T(u)| / 5`.
- Recall@5 = mean over users of `|R(u) ∩ T(u)| / |T(u)|`.
- Hit Rate@5 = share of eligible users with `|R(u) ∩ T(u)| > 0`.
- Catalog coverage = unique recommended products / 8,000 training candidates.

**Eligibility:** Users must appear in the training history and have at least one not-previously-seen item in the relevant later split. The initial counts before excluding exact repeats were 15,239 validation and 11,587 test visitors. Precision, recall, and hit rate do not mix cold-start users into the denominator. Interactions are implicit feedback and include views, carts, and purchases, **not only verified positive purchases**.

### Cautions

1. The 2015 traffic is sparse: most visitors have only one event; future sessions may have no overlapping recommended products.
2. Item-to-item collaborative filtering favors supported products; only 8,000 candidate items are used to keep the model compact.
3. Categories are anonymized and, for modeling, available as of the training cutoff; category data is incomplete.
4. Model weights and ranking formulas are an explainable baseline, not exhaustively tuned. No online randomized experiment or causal sales-lift estimation was performed.
5. Test-set results reflect a selected warm-user cohort. In production, cold-start visitors use a popularity fallback.

**Interpretation:** The category-aware blend has about 2.8× the hit rate of popularity on the held-out test period, but the absolute hit rate remains below 1%. This is a technical proof-of-concept, **not a commercial performance promise**.
