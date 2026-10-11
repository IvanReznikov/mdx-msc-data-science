# MDX-Bazario — the course business

The course is a story: **you have just joined MDX-Bazario as a data scientist.** MDX-Bazario is a fictional Dubai-based e-commerce company (web + app marketplace). Every lecture, one department brings you a question; every tool in the syllabus answers one of those questions. The warehouse is `data/business/data/`, built by the **instructor-only generator** (`private/generators/generate_business_data.py`, gitignored): every table MERGES 2–3 REAL datasets from `data/datasets/` (telco churn labels, StudentsPerformance scores, london_merged daily counts/weather, AAPL volume, real SMS text, NER POS transitions) and then injects 16 real-world artifacts (MCAR/MAR nulls, case-mixed and typo'd categories, duplicate rows, impossible and heavy-tail outliers, unit drift, numbers-as-text, mixed date formats, whitespace, unicode junk, future dates, ID collisions, a junk column). Clean pre-artifact truth (holdout targets, hidden intent, the 90-day forecast continuation) goes to `private/homework_keys/` only. MDX-Bazario is the **class** story: in-class tasks, HW05 (which needs intent ground truth real data can't provide) and debriefs. **Homeworks run on real datasets** — see `private/homework/README.md`.

The domain was chosen deliberately: **retail/e-commerce is the most common first DS job** — churn and customer value (CRM), demand and pricing (category management), marketing-mix modelling (growth), ticket triage (support ops), clickstream intent (product analytics), last-mile routing (operations). Students walk out recognising the tables *and* the questions.

## Tables

| Table | Rows (seed 42) | Department & question | Embedded patterns (instructor knows; students discover) |
|---|---|---|---|
| `customers.csv` | 5,920 (6,000 generated − 100 holdout + dupes) | CRM: *"Who will churn, and what is a customer worth?"* | churn 26.4 % (VIP 2.7 % vs standard 42.4 % — hypothesis test); early-tenure spike; promo-hunters (`discount_share`) churn; satisfaction effect real but *linear correlation* weak — binary-target lesson; `days_since_last_order` **defines** churn → deliberate leakage trap; `total_spend_aed` right-skewed (median ≈ 11 k / mean ≈ 18 k AED) → log-transform lesson |
| `products.csv` | 300 | Category mgmt: *"What drives demand? What's a bestseller?"* | price elasticity per category (electronics −1.6 … grocery −0.5); rating & review-count multipliers; `is_bestseller` = top quintile (20 %) |
| `marketing_daily.csv` | 655 (+15 dirty rows) | Growth: *"Does spend pay off, per channel?"* | real london_merged daily pattern — note the **weekend sessions drop (~−18 %)**: commuter-driven real data contradicting the memo's 'weekends sell themselves' assumption (a deliberate teaching twist); AAPL-volume revenue lumps; hidden 90-day forecast continuation in the keys |
| `support_tickets.csv` | 900 | Support ops: *"Route tickets automatically"* | 5 categories expressed in keyworded templated text → naive Bayes; imbalanced (praise rarest) |
| `web_sessions.csv` | 1,487 events / 420 sessions | Product: *"What is the visitor's intent right now?"* | 4 hidden intent states (browsing/comparing/buying/leaving) with Markov transitions emitting click events — recovering intent from events alone is the HMM/RNN task; truth is instructor-only |
| `delivery_points.csv` | 15 | Operations: *"Route the last-mile van"* | Dubai-zone coordinates for the GA/TSP exercise |

Real datasets stay only where realism is the point: vision (`mini_mnist`, `5_class_images`) and the big-data demo (`OnlineRetail`). Everything else runs on MDX-Bazario.

## Lecture mapping (canonical IDs — see `private/docs/LECTURE_INVENTORY.md`)

| Lecture | Table(s) | The business question |
|---|---|---|
| L00 Python | all small tables | first tour of the warehouse: load, slice, clean |
| L01 Intro ML | `customers`, `products` | features vs label: who churns; what makes a bestseller |
| L02 Statistics | `customers`, `marketing_daily` | distributions of tenure/spend/sessions; means vs medians |
| L03 Probability & testing | `customers`, `marketing_daily` | is the VIP-vs-standard churn gap real? Ramadan/weekend lift vs noise |
| L04 Algorithms & DS | `web_sessions`, `support_tickets` | scanning event logs efficiently; complexity on 1,600-row streams |
| L05 Linear algebra | `customers`, `products` | feature vectors, distances between customers/products |
| L06 Dim. reduction | `customers`, `products` | standardise then PCA; interpret PC1 ("engagement") |
| L07–L08 Regression | `marketing_daily` → sessions/revenue; `products` → units; `customers` → spend | marketing response; demand curves; log-target regression; regularization; CV |
| L10 Metrics | `customers` churn | confusion matrix, precision/recall on a 24 % positive class — why accuracy lies |
| L11 kNN | `customers`, `products` | similar customers (segments); distances need scaling |
| L13 Trees & forests | `customers`, `products` | interpretable churn rules and demand drivers |
| L14 Boosting | `products`, `customers` | from the slide toy stumps to a real ensemble |
| L15 Naive Bayes | `support_tickets` | classify refund / shipping_delay / damaged / account / praise |
| L16 Clustering | `customers` | RFM-style segments for CRM |
| L17–L18 Neural nets | `customers`, `products` | same churn/demand tasks, learned representations |
| L20 CNN | *(real images — MNIST / 5-class)* | product-photo tagging is the framing only |
| L22 RNN | `web_sessions` (and `marketing_daily` as a sequence) | next-event prediction; sequence modelling |
| L23 HMM | `web_sessions` | **recover the hidden purchase-intent states** (instructor holds the truth) |
| L24 SVM | `customers`, `products` | margins and kernels on the real tables |
| L25 RL & GA | `delivery_points` | last-mile route optimisation (TSP), GA tuning |
| L26 Deployment | any trained model | ship the churn/CLV model behind an app (`../deployment/`) |

## Operating rules

- **One seed = one cohort.** `python private/generators/generate_business_data.py --seed 2026` regenerates every table and every private key; last year's answers and Kaggle submissions quietly stop matching. **The generator is never published** (it lives in gitignored `private/generators/`) — students cannot decode a process they cannot read; the debrief reveals it in class.
- **The generator is the documentation.** Column semantics and effect sizes live in `private/generators/generate_business_data.py` (+ `generate_orders.py`); this README stays a map, not a spec.
- The generator is instructor-only; the debrief **walks through it in class** after each deadline — seeing the truth-generating process is the best debrief there is.
- The slide decks keep their own toy examples (football players etc.) for the hand-worked math; MDX-Bazario is where every technique lands on "production" data. Add tables by adding a `make_*` function + a mapping row; never mutate shipped CSVs by hand.
