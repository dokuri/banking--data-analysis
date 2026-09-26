# 🏦 Banking Customer & Transaction Analytics Dashboard

A single-file **Streamlit + Plotly** dashboard for exploring customer behaviour, cash flow, channel usage and
fraud risk in a bank's transaction data.

The bundled dataset is **300 synthetic transactions** from 83 customers across 11 Indian cities
(1 Oct 2025 – 20 Sep 2026, amounts in ₹). No real customers or accounts are represented.

## 1. Files

```
02_banking_dashboard/
├── main.py                       # the whole app: data + analytics + dashboard
├── requirements.txt              # Python libraries to install
├── data/bank_transactions.csv    # 300 transactions × 21 columns
└── README.md
```

## 2. Requirements

* Python 3.9 or newer
* Libraries: `streamlit`, `pandas`, `numpy`, `plotly`

```bash
pip install -r requirements.txt
```

(Equivalent to `pip install streamlit pandas numpy plotly`.)

## 3. Run

```bash
streamlit run main.py
```

Streamlit opens the dashboard at <http://localhost:8501>. (If the port is busy: `streamlit run main.py --server.port 8502`.)

## 4. How it works

`main.py` is organised in three sections, top to bottom:

1. **Settings** – page configuration, path to the CSV, currency symbol.
2. **Data & analytics** – plain pandas functions, no Streamlit calls:
   * `load_data()` reads the CSV, checks required columns, and adds helper columns
     (`txn_month`, `hour`, `weekday`, `age_group`, `credit_band`, `is_success`, `signed_amount`).
   * `apply_filters()` narrows the transactions using the sidebar choices.
   * `compute_kpis()` and the `*_summary()` / `fraud_*()` functions produce every number and table behind a chart.
3. **Dashboard (UI)** – sidebar filters → KPI cards → five tabs of Plotly charts. The default CSV is cached with
   `st.cache_data`; you can also upload your own CSV from the sidebar.

```
data/bank_transactions.csv → load_data() → apply_filters(sidebar) → KPIs + summaries → Plotly charts
```

**One row = one transaction**, with the customer's attributes repeated on every row (a flat layout that is easy to
filter). Balances were simulated in time order per customer, so `balance_after` is consistent: a debit larger than the
available balance fails with *Insufficient Funds*.

### Business rules
| Metric | Definition |
|---|---|
| **Successful volume / inflow / outflow** | Only `status == "Success"` transactions move money. Failed and Pending rows are ignored. |
| **Net cash flow** | Credits − debits (successful only). |
| **Success rate** | Successful ÷ all transactions. |
| **Avg balance per customer** | Mean of each customer's *latest* `balance_after` inside the selected filters. |
| **Fraud rate** | Rows with `is_fraud = 1` ÷ all transactions. Value at risk = their total amount. |
| **Credit bands** | Poor < 600 · Fair 600–699 · Good 700–749 · Excellent 750+ |
| **Rule-based risk score** | +40 night-time (00:00–04:59), +30 amount > 3× the customer's median, +20 remote channel (Net Banking / Online Card / UPI), +10 amount > ₹50,000. A transparent baseline to compare with the fraud flag. |

### Dashboard tabs
| Tab | What you see |
|---|---|
| 📊 Overview | Monthly credits vs. debits, net cash flow, volume by transaction type, channel usage, monthly counts |
| 👥 Customers | Balance by segment / account type / credit band, volume by age group, credit-score scatter, top-10 customers |
| 💳 Transactions | Weekday × hour heat-map, merchant-category spend, top cities, failure reasons |
| 🚨 Fraud & risk | Flagged count / rate / value, fraud by hour, channel and type, flagged-transaction table, risk-score comparison |
| 🗂️ Data | Filtered table + CSV download |

## 5. Data dictionary (`data/bank_transactions.csv`)

| Column | Description |
|---|---|
| `transaction_id` | Unique id (TXN10000001…) |
| `transaction_timestamp` | Date & time of the transaction |
| `customer_id`, `customer_name` | Customer identifiers (synthetic) |
| `age`, `gender`, `city` | Customer demographics |
| `account_type` | Savings, Salary, Current, Premium Savings |
| `customer_segment` | Mass / Affluent / Premium, derived from `annual_income` |
| `annual_income` | Declared yearly income (₹) |
| `credit_score` | 300–900 scale (565–859 in this sample) |
| `has_loan` | Yes / No (customers with a loan pay monthly `Loan EMI`s) |
| `transaction_type` | UPI Payment, Card Purchase, Fund Transfer, Cash Withdrawal, Bill Payment, Salary Credit, Deposit, Loan EMI |
| `direction` | Credit (money in) or Debit (money out) |
| `channel` | UPI, Mobile Banking, Net Banking, ATM, POS Terminal, Online Card, Branch, Direct Credit, Auto Debit |
| `merchant_category` | Groceries, Dining, … for UPI/card spend; `Utilities` for bills; `Not Applicable` otherwise |
| `amount` | Transaction amount (₹) |
| `status` | Success, Failed, Pending |
| `failure_reason` | Insufficient Funds, Technical Error, Blocked by Fraud Engine, Awaiting Settlement (blank if successful) |
| `balance_after` | Customer's balance after this transaction |
| `is_fraud` | 1 = flagged as fraudulent, else 0 (12 of 300 rows) |

### Sanity check
With no filters you should see: **300 transactions · 83 customers · ₹30.21 L successful volume · 94.0 % success rate ·
net flow ₹6.59 L · avg balance ₹2.16 L · avg credit score 702 · 12 fraud flags (4.0 %)**.

## 6. Using your own data
Provide a CSV with the same 21 column names (extra columns are fine; missing ones show a clear error) and upload it
from the sidebar, or replace `data/bank_transactions.csv`. `transaction_timestamp` must be parseable
(`YYYY-MM-DD HH:MM:SS`), `direction` must be `Credit`/`Debit`, and `status` should include `Success`.

## 7. Troubleshooting
* `ModuleNotFoundError` → run the `pip install` line in section 2 (inside your virtual environment, if you use one).
* "No transactions match the selected filters" → clear one or more sidebar filters.

