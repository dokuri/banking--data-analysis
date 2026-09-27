# 🏦 Banking Customer & Transaction Analytics Dashboard

A **Streamlit + Plotly** dashboard for analyzing banking customer behavior, transactions, cash flow, channel usage, and fraud risk.

This project **does not contain or generate synthetic banking data**. The dashboard requires the user to upload a banking transaction CSV through the Streamlit interface.

---

## 📌 Project Overview

The dashboard analyzes banking transaction data using:

* Python
* Pandas
* NumPy
* Plotly
* Streamlit

The application provides interactive analytics for:

* Customer behavior
* Transaction patterns
* Cash inflow and outflow
* Customer segmentation
* Credit scores
* Banking channels
* Transaction failures
* Fraud flags
* Rule-based transaction risk scoring

### Data Flow

```text
User Banking CSV
       ↓
Streamlit File Upload
       ↓
Data Validation
       ↓
Data Cleaning & Transformation
       ↓
Pandas Analytics
       ↓
Plotly Visualizations
       ↓
Interactive Streamlit Dashboard
```

---

# 📁 Project Structure

```text
02_banking_dashboard/
│
├── main.py
├── requirements.txt
└── README.md
```

There is **no bundled `data/` folder** and no sample/synthetic transaction dataset.

---

# 🛠️ Technology Stack

| Technology | Purpose                    |
| ---------- | -------------------------- |
| Python     | Application development    |
| Pandas     | Data cleaning and analysis |
| NumPy      | Numerical calculations     |
| Plotly     | Interactive charts         |
| Streamlit  | Dashboard development      |
| CSV        | Input data format          |

---

# ⚙️ Requirements

## Python

Python **3.9 or newer** is recommended.

## Python Libraries

Install the required libraries:

```bash
pip install -r requirements.txt
```

Or install them manually:

```bash
pip install streamlit pandas numpy plotly
```

---

# ▶️ Running the Dashboard

Open the project directory:

```bash
cd 02_banking_dashboard
```

Run:

```bash
streamlit run main.py
```

The dashboard will normally open at:

```text
http://localhost:8501
```

If port `8501` is already being used:

```bash
streamlit run main.py --server.port 8502
```

---

# 📂 Uploading Banking Data

After starting the application:

1. Open the Streamlit dashboard.
2. Go to the sidebar.
3. Click **Upload Banking CSV**.
4. Select your CSV file.
5. The application validates the required columns.
6. The dashboard processes the uploaded data.
7. Interactive charts and KPIs are displayed.

The application does **not** create or insert sample transactions if a file is not uploaded.

---

# 📋 Required CSV Columns

Your banking dataset should contain the following columns:

```text
transaction_id
transaction_timestamp
customer_id
customer_name
age
gender
city
account_type
customer_segment
annual_income
credit_score
has_loan
transaction_type
direction
channel
merchant_category
amount
status
failure_reason
balance_after
is_fraud
```

Extra columns are allowed.

---

# 📖 Data Dictionary

| Column                  | Description                                                |
| ----------------------- | ---------------------------------------------------------- |
| `transaction_id`        | Unique transaction identifier                              |
| `transaction_timestamp` | Date and time of the transaction                           |
| `customer_id`           | Unique customer identifier                                 |
| `customer_name`         | Customer name                                              |
| `age`                   | Customer age                                               |
| `gender`                | Customer gender                                            |
| `city`                  | Customer city                                              |
| `account_type`          | Type of bank account                                       |
| `customer_segment`      | Customer classification such as Mass, Affluent, or Premium |
| `annual_income`         | Customer annual income                                     |
| `credit_score`          | Customer credit score                                      |
| `has_loan`              | Indicates whether the customer has a loan                  |
| `transaction_type`      | Type of transaction                                        |
| `direction`             | Credit or Debit                                            |
| `channel`               | Channel used for the transaction                           |
| `merchant_category`     | Category of merchant                                       |
| `amount`                | Transaction amount                                         |
| `status`                | Transaction status such as Success, Failed, or Pending     |
| `failure_reason`        | Reason for a failed or pending transaction                 |
| `balance_after`         | Account balance after the transaction                      |
| `is_fraud`              | Fraud indicator: `1` for flagged, `0` otherwise            |

---

# 📊 Dashboard Sections

The dashboard contains five main sections.

## 1. 📊 Overview

Provides overall transaction and cash-flow analysis.

Includes:

* Total transactions
* Number of customers
* Successful transaction volume
* Success rate
* Total credits
* Total debits
* Net cash flow
* Monthly credits vs. debits
* Transaction volume by transaction type
* Channel usage

---

# 2. 👥 Customers

Provides customer-level analytics.

Includes:

* Average balance by customer segment
* Transaction volume by age group
* Credit-score distribution
* Credit-score bands
* Top customers by transaction volume
* Customer segmentation analysis

### Credit Score Bands

```text
Poor       < 600
Fair       600–699
Good       700–749
Excellent  750+
```

---

# 3. 💳 Transactions

Provides detailed transaction analysis.

Includes:

* Transactions by weekday
* Transactions by hour
* Weekday/hour heatmap
* Merchant-category spending
* Top cities
* Transaction failures
* Failure reasons
* Transaction-type analysis

---

# 4. 🚨 Fraud & Risk

Provides fraud and transaction-risk analysis.

Includes:

* Fraud flag count
* Fraud rate
* Fraud transaction value
* Fraud by hour
* Fraud by channel
* Fraud by transaction type
* Flagged transaction table
* Rule-based risk score comparison

---

# 5. 🗂️ Data

Displays the filtered uploaded dataset.

Users can:

* View transactions
* Apply filters
* Inspect columns
* Download the filtered dataset as CSV

---

# 🔎 Dashboard Filters

The sidebar provides interactive filters for:

* City
* Account Type
* Customer Segment
* Transaction Type
* Channel
* Transaction Status
* Fraud Status

The charts and KPI values update according to the selected filters.

---

# 💰 Business Metrics

## Successful Transaction Volume

Only successful transactions are included:

```text
status = Success
```

---

## Credit / Inflow

Successful transactions where:

```text
direction = Credit
```

---

## Debit / Outflow

Successful transactions where:

```text
direction = Debit
```

---

## Net Cash Flow

```text
Net Cash Flow = Total Credits - Total Debits
```

Only successful transactions are considered.

---

## Success Rate

```text
Success Rate =
Successful Transactions / Total Transactions × 100
```

---

## Fraud Rate

```text
Fraud Rate =
Fraud Flagged Transactions / Total Transactions × 100
```

---

## Fraud Value

```text
Fraud Value =
Sum of Amount for Fraud-Flagged Transactions
```

---

# 🚨 Rule-Based Risk Score

The dashboard includes a transparent rule-based risk score.

The score increases according to the following rules:

| Condition                                              | Score |
| ------------------------------------------------------ | ----: |
| Transaction between 00:00–04:59                        |   +40 |
| Amount greater than 3× customer's median transaction   |   +30 |
| Remote channel such as UPI / Net Banking / Online Card |   +20 |
| Transaction amount greater than ₹50,000                |   +10 |

The maximum possible score is:

```text
100
```

This is a **rule-based analytical indicator**, not a machine-learning fraud prediction model.

---

# 🧹 Data Processing

When a CSV is uploaded, the application performs several processing steps.

### Timestamp conversion

```python
pd.to_datetime()
```

### Numeric conversion

Numeric fields such as:

```text
age
annual_income
credit_score
amount
balance_after
is_fraud
```

are converted into numeric data types.

### Additional analytical columns

The application creates:

```text
txn_month
hour
weekday
age_group
credit_band
is_success
signed_amount
risk_score
```

These columns are generated during processing and do not have to be present in the original CSV.

---

# 📈 Visualization

The project uses **Plotly** for interactive visualizations.

Charts include:

* Bar charts
* Pie charts
* Histograms
* Heatmaps
* KPI metrics
* Interactive tables

Users can interact with the charts directly inside the Streamlit dashboard.

---

# 📥 Download Filtered Data

After applying filters, the dashboard provides:

```text
Download Filtered CSV
```

The downloaded file contains only the currently filtered records.

---

# 🔐 Data Privacy

This project does not include a pre-generated banking dataset.

Users should only upload banking data that they are authorized to process.

For portfolio demonstrations, use:

* Publicly available datasets
* Properly anonymized datasets
* Organization-approved datasets

Do not upload confidential customer information without appropriate authorization.

---

# ⚠️ Data Validation

The application checks whether the uploaded CSV contains the required columns.

If required columns are missing, the application displays an error instead of attempting to process incomplete data.

The following fields should follow these formats:

### Timestamp

```text
YYYY-MM-DD HH:MM:SS
```

Example:

```text
2026-08-15 14:35:20
```

### Direction

Expected values:

```text
Credit
Debit
```

### Status

Typical values:

```text
Success
Failed
Pending
```

### Fraud

Expected values:

```text
0
1
```

---

# 🧪 Example Workflow

```text
1. Prepare banking CSV
        ↓
2. Start Streamlit
        ↓
3. Upload CSV
        ↓
4. Validate columns
        ↓
5. Clean data
        ↓
6. Apply dashboard filters
        ↓
7. Calculate KPIs
        ↓
8. Analyze customers
        ↓
9. Analyze transactions
        ↓
10. Analyze fraud and risk
        ↓
11. Download filtered results
```

---

# 💼 Skills Demonstrated

This project demonstrates practical skills in:

* Python
* Pandas
* NumPy
* Data Cleaning
* Exploratory Data Analysis
* Data Transformation
* Statistical Analysis
* Financial Data Analysis
* Customer Segmentation
* Fraud Risk Analysis
* Data Visualization
* Plotly
* Streamlit
* Interactive Dashboard Development
* CSV Data Processing

---

# 🎯 Project Objective

The objective of this project is to build an interactive banking analytics solution that transforms transaction-level data into meaningful business insights.

The dashboard helps analyze:

```text
Customer Behaviour
        +
Transaction Patterns
        +
Cash Flow
        +
Banking Channels
        +
Credit Profiles
        +
Fraud Indicators
        ↓
Interactive Business Dashboard
```

---

# 👨‍💻 Project Type

**Domain:** Banking / Finance Analytics

**Project Category:** Data Analytics & Business Intelligence

**Application:** Interactive Banking Dashboard

**Data Source:** User-provided CSV

**Synthetic Data:** Not included

**Machine Learning:** Not used for fraud prediction

**Dashboard Framework:** Streamlit

**Visualization:** Plotly

---

# 📌 Important Note

This project is designed as an **analytics dashboard**, not as a production banking or fraud-detection system.

The rule-based risk score is intended for analytical demonstration and should not be treated as a financial, compliance, or fraud-investigation decision system.

---

## 👤 Author

**Dokuri Shilish Reddy**

Data Analyst | Python | SQL | Power BI | Data Analytics
