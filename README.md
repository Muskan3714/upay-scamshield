# upay ScamShield: AI early warning for scam transfers

**AI DEV FEST 2026 AI Hackathon (DIU CPC x upay), Track 01: Trust and Risk Intelligence**

**Live demo:** https://upay-scamshield.streamlit.app
**Team:** M4LW4R3HYDR4S: Shobnom Sultana Muskan, Parvez Hossen Badal, Hakeemul Adnan Rafee
**University:** University of Information Technology and Sciences (UITS)

---

## 1. Project overview

**Problem.** Mobile wallet users in Bangladesh lose money to "send money" scams: fake prize calls, "I sent money to your number by mistake, please return it", and account takeovers after a PIN or OTP is stolen. The victim usually approves the transfer themselves, so the PIN does not protect them, and once money reaches a mule wallet it is cashed out quickly.

**Background.** The scam patterns in our synthetic data are based on public reports. Bangladesh Bank data reported by the Daily Observer puts payment-ecosystem fraud losses at about Tk 92.60 crore in 2025 ([source](https://observerbd.com/news/590829)). Reported methods include social engineering calls asking for the OTP ([source](https://observerbd.com/news/590830)), fake prize and lottery messages ([example case](https://en.prothomalo.com/bangladesh/Brahmanbaria-tea-seller-loses-Tk-65-000-in-Bkash)), and "money sent to you by mistake" calls, which bKash warns about on its fraud awareness page ([source](https://www.bkash.com/en/help/avoid-fraud)).

**Problem statement.** For first-time and less digitally confident upay users, phone-coached scam transfers cause direct money loss and reduce trust in the wallet. We built ScamShield, which uses each customer's own transaction history, the receiving wallet and the transfer network to warn or pause a risky transfer before the money leaves, and to find the mule wallets that collect the money. Success is measured by scam money protected, false alarms on genuine transfers, and mule rings discovered.

**Two datasets, one system.**

| Dataset | What it is | Models |
|---|---|---|
| **A · Demo** | Our synthetic data: the main raw transaction log plus our earlier synthetic set (kept for comparison) | Trained on days 30 to 72, tested on the future days 72 to 90 |
| **B · Your data** | Anyone's own transaction log, loaded in the app or from the command line | ScamShield builds new models from it: a new anomaly model always, and a new classifier when the log has fraud labels |

Switch the active dataset in the sidebar; every page and the API then run on that dataset. Dataset A is the demo; Dataset B is how ScamShield runs as a real model on real data.

**Solution.** ScamShield works directly on a raw transaction log, the kind of data upay already stores:

| Level | What it does |
|---|---|
| Each transfer | Four independent AI engines check it in real time against the customer's own history; the result is ALLOW, WARN (Bangla reasons, user decides) or HOLD (re-verify and analyst review) |
| The network | Finds mule wallets that receive high-risk money from many victims and groups them into rings by their shared collector wallet |
| The fraud team | Every alert and ring comes with an evidence-based case summary; analysts manage cases with status, notes, an audit trail and a PDF case report |
| upay's systems | A real-time scoring API (`api.py`) that the Send Money flow can call before a transfer is confirmed |

The system never blocks money permanently on its own. High-impact cases go to a human.

## 2. Features

- **Works on raw transaction logs.** Input is just `timestamp, sender, receiver, amount, device, district`. Every signal is computed from history by `pipeline.py`, point-in-time (only data from before each transfer), exactly as a live system would.
- **Per-customer behaviour.** Each customer's usual amount, usual hours, known devices, usual districts and contacts are learned from their own past transfers.
- **Four AI engines with an agreement panel:** a scam classifier (XGBoost), a behaviour anomaly model (Isolation Forest, no labels needed), a takeover check against the customer's own habits, and a network check of the receiving wallet. The app shows how many engines agree ("3 of 4 engines flag this").
- **Money-mule network discovery:** graph analysis (NetworkX) finds wallets receiving high-risk money from many unrelated senders and groups them into rings by their shared collector.
- **Explainable warnings:** SHAP values (XGBoost `pred_contribs`) turned into plain-language reasons in Bangla and English.
- **Business rules kept separate from ML** (`risk_engine.py`).
- **Dataset B · your data:** load any CSV in the format below (in the app, or `python workspace.py your_log.csv`). ScamShield checks the data, learns every customer's habits, fits a new anomaly model on it and, if it has fraud labels, trains a new classifier on the earlier 70% and tests it on the later 30%, comparing it with the demo model and a simple rule. In the app, each browser session gets its own private Dataset B (`workspaces/B_<session>/`); from the command line it is saved in `workspaces/B/`. The whole app and the API can then run on it. IDs are kept as text, so phone-style wallet numbers like 01712345678 keep their leading zero.
- **Live customer mode:** pick a real customer from the log and try a new transfer; it is scored live from their real history using the same code as the API.
- **Real-time scoring API:** `POST /score` returns the decision, scores, engine results and Bangla/English reasons.
- **Case management:** escalate alerts or rings (no duplicates), status, analyst, notes, timestamped audit trail, PDF case report, CSV export.
- **Model and impact dashboard:** evaluation on future data, rule baseline, unseen-scam test, detection by scam type, fairness check.
- **Security-operations console UI:** sidebar navigation, live system status, a live threat feed, a Command Center overview and a phone-style customer view.
- **Datasets page:** Dataset A's two synthetic sets (the main raw log and our earlier customer-profile set, both kept, with downloads), the status of Dataset B, and a cross-dataset test of the demo models on the earlier synthetic set.

## 3. Technology stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Data pipeline | pandas, NumPy (`pipeline.py`, point-in-time features) |
| Classifier | XGBoost |
| Anomaly detection | scikit-learn Isolation Forest |
| Network analysis | NetworkX, Graphviz (built into Streamlit) |
| Explainability | SHAP values via XGBoost `pred_contribs` |
| App / UI | Streamlit, custom CSS in upay colours, inline SVG line icons (`icons.py`) and Material Symbols; no emoji |
| API | FastAPI + Uvicorn |
| Case reports | ReportLab (PDF) |
| Testing | pytest |
| Hosting | Streamlit Community Cloud |

No external AI API or paid service is used.

## 4. Requirements

- Python 3.10 or newer, `pip`, `git`
- About 1 GB free disk space and 2 GB RAM; any laptop (no GPU needed)
- Python packages listed in `requirements.txt`

## 5. Installation and setup

```bash
git clone https://github.com/YodirHydra/upay-scamshield
cd upay-scamshield
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 6. Environment variables

None are required. Optional:
- `SCAMSHIELD_WORKSPACE` chooses the dataset the API runs on: `A` (demo, default) or `B` (your data, after `python workspace.py your_log.csv`).
- `SCAMSHIELD_SHARED_B=1` makes the app use that same shared Dataset B. By default, on a public server, every browser session gets its **own private Dataset B**, so one visitor's upload is never visible to another; old session uploads are deleted automatically after 12 hours.

## 7. Run and build commands

```bash
python generate_data.py           # Dataset A: the main synthetic raw log in data/ (optional, already included)
python generate_data_profiles.py  # Dataset A: the earlier synthetic set in data/previous/ (optional, already included)
python train.py             # 2. build features, train both models, run the network analysis (optional, already included)
streamlit run app.py        # 3. the app: open http://localhost:8501
uvicorn api:app --port 8000 # 4. the real-time API on Dataset A: open http://localhost:8000/docs

# Run ScamShield as a real model on your own data (Dataset B):
python workspace.py your_log.csv            # builds Dataset B in workspaces/B/
set SCAMSHIELD_WORKSPACE=B                   # Windows (macOS/Linux: export SCAMSHIELD_WORKSPACE=B)
uvicorn api:app --port 8000                  # the API now scores against your data
```

The trained models and data are committed, so `streamlit run app.py` works straight after install (the first load takes about 30 seconds while it learns every customer's history). There is no separate build step.

**Deploy (Streamlit Community Cloud):** push to a public GitHub repo, go to share.streamlit.io, choose *New app*, select the repo, branch `main`, main file `app.py`, then *Deploy*. Make sure the `.streamlit` folder is pushed too.

## 8. Live deployment URL

https://upay-scamshield.streamlit.app

## 9. Testing instructions

```bash
pytest -q
```

The 20 tests check, among other things: the business impact estimate; building Dataset B from an unlabelled log with phone-style IDs and day-first dates; training a new model when labels exist; that no future data leaks into features; that the API's live scoring gives exactly the same features as training; day-first date parsing and data-quality warnings; that the model beats the rule baseline on future data; the anomaly model on an unseen scam type; mule rings without flagging shops; the profile comparison; engine agreement; the case workflow and PDF; and the API's decisions for a normal transfer and a takeover.

**Pages (sidebar):** Command Center, Send Money, Analyst Queue, Mule Network, Dataset B · Your Data, Datasets, Cases, Model & Impact. The dataset switcher (A or B) is at the top of the sidebar.

**Manual check in the app:**
1. *Send Money*, real-customer mode: pick a customer, keep their usual contact, phone and district: ALLOW. Change "Send to" to a wallet in the mule network: WARN from the network engine. Pick a new phone, another district, 03:00 and a large amount: HOLD.
2. *Analyst queue*: open a transaction, see the engines and the comparison with the customer's own history, then *Escalate to case*.
3. *Dataset B · Your Data*: upload a CSV (or use the practice sample), read the data-quality notes, press *Build Dataset B*, then see the new model compared with the demo model and a simple rule. Switch to Dataset B in the sidebar and every page runs on it.
4. *Cases*: change status, add a note, download the PDF.
5. API: run `uvicorn api:app`, open `/docs`, try `POST /score`.

## 10. Data format and other configuration

| Column | Need | Meaning |
|---|---|---|
| txn_id | required | Unique transfer ID |
| timestamp | required | `2026-07-01 14:30:00` or `01/07/2026 14:30` |
| sender_id, receiver_id | required | Wallet IDs |
| amount | required | BDT |
| device_id, district | required | Device used and where |
| on_active_call | optional | 1 if the customer was on a phone call |
| sender_created_at, receiver_created_at | optional | Wallet opening dates (strongly recommended) |
| is_fraud | optional | Confirmed fraud labels (enables accuracy check and retraining) |

Thresholds are in `risk_engine.py` and `mule_network.py`; they are business-policy settings. `data/ground_truth.csv` and `data/wallet_roles_ground_truth.csv` hold the synthetic labels and are used only for evaluation, never by the models at scoring time.

---

## Results

**Evaluated like a live system:** trained on days 30 to 72, tested on the *future*, days 72 to 90 (17,038 transfers, 325 scams).

| Metric | ScamShield | Simple rule* |
|---|---|---|
| Scams caught | **86%** | 43% |
| Precision (alerts that are real scams) | **76%** | 41% |
| Genuine transfers warned | **0.5%** | 1.2% |
| Scam money protected | **93%** | 68% |
| ROC-AUC | 0.997 | N/A |

\*Rule: new recipient AND amount of at least BDT 5,000.

**By scam type:** social engineering 96%, account takeover 96%, low-signal scams (normal-looking transfers to older "rented" mule accounts) 63%.

**Unseen scam type test.** Both models were trained with no account-takeover examples. The classifier alone caught 41% of takeovers; with the anomaly model, 99%.

**Network.** 54 wallets flagged as mules, all real mules (100% precision), covering 70% of mule wallets that received money; all 12 rings found; 0 shops wrongly flagged.

**Fairness (tenure).** New customers (<180 days) had a 0.95% false alarm rate vs 0.53% for established customers. New users are a small group in the test set (only 2 scams), so this comparison is uncertain; it should be re-checked on real data, and thresholds could be set per customer group.

**Cross-dataset test (earlier synthetic set).** Scoring our earlier, independently generated set with models trained only on the main log still catches 89% of scams (vs 49% for the simple rule), but false alarms rise to 7.4% because the data looks different. Retraining on that set itself (earlier 70%, tested on the later 30%) brings false alarms down to 3.3% with 91% of scams caught. This is the same thing we expect with real upay data, which is why retraining in shadow mode is the first real-world step.

**Business impact (estimate, per 100,000 send money transfers).** Our test data has far more scams than real life, so we apply the rates measured on future transfers to a realistic number of scams, from the Tk 92.60 crore yearly loss figure and Bangladesh Bank's 134.26 million send money transfers a month ([source](https://thefinancialexpress.com.bd/home/mfs-transactions-maintain-rising-trend-in-oct-25)). Assumptions: all reported losses are send money scams (base) or half of them (cautious); average scam Tk 7,114; a false WARN costs Tk 2; a HOLD costs Tk 20 for the customer plus 10 analyst minutes at Tk 300/hour.

| Per 100,000 transfers | Base | Cautious | Simple rule (base) |
|---|---|---|---|
| Alerts | 545 (408 WARN, 138 HOLD) | 542 | 1,176 (all reviewed) |
| Analyst hours | 23 | 22 | 196 |
| Money protected | Tk 53,161 | Tk 26,581 | Tk 39,172 |
| Friction cost | Tk 10,457 | Tk 10,243 | Tk 82,325 |
| Protected per Tk 1 of friction | 5.1 | 2.6 | 0.5 |

In a stress test (half the losses, half the detection, twice the false alarms) friction would exceed savings, which is why the HOLD threshold is tuned on real data first. The app's Model & Impact page has this calculator with every assumption adjustable (`business.py`).

**Data quality matters.** On a short 15-day log with no wallet opening dates, false alarms rose to about 7%, because with little history many genuine transfers look "new". The app now warns about this automatically.

## Synthetic data assumptions

All data is generated by `generate_data.py`; no real customer data or PII is used. The raw log contains no labels; labels are kept in a separate file, like a fraud team's confirmed cases.
- 3,000 customers over 90 days (the first 30 days only build history), each with a usual amount (median about BDT 1,100), usual active hours, one or two phones, a home district and 3 to 13 contacts; 92% of genuine transfers are inside usual hours; 10% go to someone new (including friends who just joined upay); 3% are large payments; 1% use a new phone; 3% are from another district.
- 12,000 people wallets (12% opened during the period), 300 shops, 60 popular wallets (e.g. landlords, family collectors) that receive from many customers.
- 80 mule wallets in 12 rings: 60% freshly opened, 40% older "rented" accounts; each mule is used for a few days, unevenly (a few busy mules, many rarely used); mules forward money to their ring's collector. Shops pay suppliers, so forwarding money is not suspicious by itself.
- Social engineering (1,000): during normal hours from the customer's own phone, 1.5 to 8 times the usual amount, on a call 70% of the time. Account takeover (220 events, 522 transfers): new phone 85%, other district 70%, night 60%, 1 to 4 quick drains of 3 to 15 times the usual amount. Low-signal (270): normal-looking amounts to older mule accounts.

## Responsible AI

- **Privacy:** synthetic data only; the pipeline needs no names, phone numbers or NID.
- **Explainability:** every warning and every ring shows its reasons.
- **Human oversight:** HOLD and ring cases go to an analyst; the user can still confirm a WARN.
- **Fairness:** measured across new and established customers and reported openly.
- **Transparency:** the UI and API return the classifier score, anomaly score, rules, engine results and features separately.
- **Security:** no secrets in the repo; no free-form LLM makes the decision; inputs are validated; every value that comes from uploaded data or typed notes is HTML-escaped before display and in PDF reports (no injected markup); Dataset B is private per session; uploaded data is never committed (`workspaces/` is git-ignored).

## Path to production

1. Point `pipeline.py` at a governed, anonymised export of upay transfers (same columns) and retrain both models.
2. Tune thresholds with upay's fraud team in shadow mode (score silently, compare with confirmed fraud).
3. Call `POST /score` from the Send Money flow; run the network job daily.
4. Run an A/B pilot measuring scam loss per 10,000 transfers and the cancellation rate after warnings.
5. Feed analyst case decisions back as new training labels.
