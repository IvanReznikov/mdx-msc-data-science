# MDX-Bazario business challenges — pick your fight

Ten challenges posed by the departments of the fictional company whose data lives in
`data/business/`. Four are what a department realistically asks; three are **tricky**
(the trap is conceptual — the numbers look great and the answer is wrong); three are
**hard** (technically demanding end-to-end). Difficulty maps to lectures: the tools
listed are where you learn them.

Solutions and ground truth stay in `private/` — these briefs are the public facing side.

---

## Business challenges — what a department actually asks

### 1. Churn triage — CRM
> *"Who is about to leave, and what do we do about it?"*
- **Data:** `customers.csv` · **Tools:** L02, L09, L10
- **Deliverable:** ranked risk list (top 100) + the three strongest churn drivers, in business words.

### 2. The Ramadan stock plan — Planning & Buying
> *"How much stock for the March campaign? Guessing cost us last year."*
- **Data:** `marketing_daily.csv`, `orders.csv` · **Tools:** L07, L08, L22
- **Deliverable:** weekly demand forecast for the campaign window + the cost of being wrong in each direction.

### 3. Ticket triage — Support
> *"900 tickets a month reach the wrong queue first. Fix the routing."*
- **Data:** `support_tickets.csv` · **Tools:** L15, L17
- **Deliverable:** a classifier that routes by issue type, with per-class recall the support lead can read.

### 4. The last-mile loop — Operations
> *"Tomorrow's 15 deliveries — what order do we drive them in?"*
- **Data:** `delivery_points.csv` · **Tools:** L25 (genetic algorithms)
- **Deliverable:** the route, the distance saved vs. naive order, and the runtime budget.

---

## Tricky challenges — the numbers look great, the answer is wrong

### 5. The bestsellers paradox — Commercial
> *"Product A beats B in every single category, yet B outsells it overall. Find the lie."*
- **Data:** `products.csv`, `order_items.csv` · **Tools:** L03, L16
- **The trap:** Simpson's paradox — segment mix, not product quality, drives the aggregate.

### 6. The self-fulfilling churn model — CRM (again)
> *"Your model is 94% accurate. It is also useless. Explain."*
- **Data:** `customers.csv` · **Tools:** L09, L10
- **The trap:** target leakage — the strongest feature encodes the future ("0 orders in the final month"). Cross-validation cannot save you from leaking time.

### 7. The AOV mirage — Finance
> *"Average order value jumped 20% — marketing wants credit. Revenue is flat. Reconcile."*
- **Data:** `orders.csv` · **Tools:** L02, L03
- **The trap:** survivorship + mix shift — small baskets churned away, so the average rose while the total didn't.

---

## Hard challenges — technically demanding, end-to-end

### 8. Next-basket prediction — Commercial & Data Science
> *"Predict each customer's next purchase category before they open the app."*
- **Data:** `order_items.csv` · **Tools:** L17, L22
- **Why hard:** sequence modelling, honest temporal splits, and an evaluation the business understands.

### 9. Reading the customer's mind — Growth
> *"Our clickstream has hidden states — browsing, comparing, checkout-bound. Recover them."*
- **Data:** `web_sessions.csv` · **Tools:** L23 (HMMs)
- **Why hard:** unsupervised structure recovery on sequences; validating that the states MEAN something.

### 10. Price it right — Commercial & Finance
> *"For each category: what happens to revenue if we move price ±5%? Give the CFO confidence bounds."*
- **Data:** `products.csv`, `orders.csv` · **Tools:** L07, L08, L25 (GA hyperparameter search)
- **Why hard:** elasticity from observational data, uncertainty quantification, and a recommendation that survives the CFO's questions.

---

## Ground rules

- Every challenge: start from the memo line, not the dataset — real work starts blurry.
- AI tools allowed for all of them ("AI writes, you verify") — the verification IS the deliverable.
- Pick **one business + one tricky** for the portfolio; the hard tier feeds the hackathon.
