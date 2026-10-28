# Common Denominator — Real-Time Fraud Detection That Explains Itself

A live dashboard that watches a stream of UPI-style transactions, scores each one for fraud risk, and tells you **in plain English why**.

> All data in this project is synthetic and generated for demonstration.

## The problem

Digital payment fraud hits ordinary people hardest: someone's account suddenly sends a large amount to a stranger at 3 AM from another city. Most fraud tools output a bare score ("risk: 0.93") that analysts and customers can't act on or trust. We wanted detection that is fast **and** explainable.

## Our approach: hybrid scoring

| Layer | What it does | Why |
|---|---|---|
| **Rule engine** (`rules.py`) | Adds points and a human-readable reason for each red flag: amount far above the user's norm, odd hour, first-time payee, unusual city, rapid repeated transfers | Transparent and auditable; every score comes with reasons |
| **ML model** (`ml.py`) | Gradient Boosting classifier estimating fraud probability from the same signals | Learns how the signals combine, catching patterns a single rule misses |
| **Blend** | `final = 0.6 × rules + 0.4 × ML` | Explainability from rules, pattern-learning from ML |

Risk levels: **Low** (< 40), **Medium** (40–69), **High** (70+).

## Features

- **Live monitor**: transactions stream in via Server-Sent Events, with counters, a risk-score line chart and a Low/Medium/High donut.
- **Explainable scores**: click any row to see the rule score, ML score and every reason.
- **Check a transaction**: enter your own user, amount, hour, location and payee type and get an instant score.
- **Analyst actions**: for Medium/High rows, click *Alert customer*, *Block* or *Mark safe* (quick *Block* and *Alert* buttons sit in the table; all three are in the expanded row). Actions are recorded server-side (`GET /actions`).
- **Money counters**: *Amount flagged* (total value of High-risk transactions) and *Money protected* (total value of transactions the analyst blocked).
- **Family alerts (simulated)**: every High-risk transaction produces a mock SMS to the account holder's family with a YES / NO reply prompt.
- **Multilingual dashboard**: switch between English, हिन्दी and ಕನ್ನಡ. Labels, risk levels, every explanation and the SMS text are translated, including rows already on screen.
- **Demo scenarios**: one-click "fraud scenario" (3 AM ₹24,000 transfer from Delhi) and "rapid-transfer burst" (4 quick transfers to new payees).

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 (use a single browser tab for the live demo).

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Dashboard |
| `/stream` | GET | Live scored transactions (SSE) |
| `/check` | POST | Score a manual transaction (`user`, `amount`, `hour`, `location`, `new_payee`) |
| `/action` | POST | Record `alert` / `block` / `safe` for a transaction `id` |
| `/actions` | GET | All recorded actions |
| `/users` | GET | Demo user profiles and locations |
| `/trigger/fraud`, `/trigger/burst` | POST | Queue scripted demo scenarios |

## Project structure

```
app.py          Flask server and API routes
rules.py        Rule engine + hybrid score blending (also emits structured reason codes for translation)
ml.py           Gradient Boosting model (trained at startup)
simulator.py    Synthetic transaction generator and demo scenarios
static/index.html   Dashboard UI (Chart.js, English/Hindi/Kannada)
```

## Limitations and honest notes

- The ML model is trained on **synthetic** data, so it demonstrates the architecture, not real-world accuracy. With real labelled transactions it would be retrained.
- Actions (alert/block/safe) are logged in memory; a real system would call a bank or payment API and persist to a database. The family SMS is simulated on screen; nothing is actually sent.
- Hindi and Kannada translations should be reviewed by a native speaker before any real-world use.
- State is shared across browser tabs, so use one tab when demoing.

## Roadmap

- Train on a real public dataset and report precision/recall
- Per-transaction feature explanations (e.g. SHAP)
- Real SMS / app notification to the customer or family member on *Alert*
- Persistent storage and analyst audit trail

## Team

Add your team name and members here.
