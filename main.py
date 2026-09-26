"""
Banking Customer & Transaction Analytics Dashboard  (single file)

Run:      streamlit run main.py
Install:  pip install -r requirements.txt
Data:     data/bank_transactions.csv   (or upload your own CSV from the sidebar)

How this file is organised
  1. SETTINGS            - page config, data path, currency symbol
  2. DATA & ANALYTICS    - load / filter the data, KPIs and every table behind a chart
  3. DASHBOARD (UI)      - sidebar filters, KPI cards and tabs with Plotly charts
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================================
# 1. SETTINGS
# ============================================================================
st.set_page_config(page_title="Banking Customer & Transaction Analytics", page_icon="🏦", layout="wide")

DATA_PATH = Path(__file__).parent / "data" / "bank_transactions.csv"
CURRENCY = "₹"

# ============================================================================
# 2. DATA & ANALYTICS  (plain pandas - no Streamlit calls in this section)
# ============================================================================
# Business rules
# --------------
# * Volumes, inflow/outflow and balances only count transactions with
#   status == "Success". Failed / Pending rows are still counted in the
#   transaction totals and success rate.
# * Fraud analysis uses the `is_fraud` flag (1 = flagged by the fraud engine).
# * Credit-score bands follow the usual Indian bureau convention:
#   <600 Poor, 600-699 Fair, 700-749 Good, 750+ Excellent.

REQUIRED_COLUMNS = [
    "transaction_id", "transaction_timestamp", "customer_id", "customer_name", "age",
    "gender", "city", "account_type", "customer_segment", "annual_income", "credit_score",
    "has_loan", "transaction_type", "direction", "channel", "merchant_category", "amount",
    "status", "failure_reason", "balance_after", "is_fraud",
]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# --------------------------------------------------------------------------- #
# Loading & filtering
# --------------------------------------------------------------------------- #
def load_data(source) -> pd.DataFrame:
    """Read the transactions CSV (path or file-like) and add derived columns."""
    df = pd.read_csv(source, parse_dates=["transaction_timestamp"])
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    ts = df["transaction_timestamp"]
    df["txn_date"] = ts.dt.normalize()
    df["txn_month"] = ts.dt.to_period("M").dt.to_timestamp()
    df["hour"] = ts.dt.hour
    df["weekday"] = ts.dt.day_name()
    df["is_success"] = df["status"].eq("Success")
    df["signed_amount"] = np.where(
        df["is_success"], np.where(df["direction"].eq("Credit"), df["amount"], -df["amount"]), 0.0
    )
    df["age_group"] = pd.cut(
        df["age"], bins=[0, 29, 39, 49, 59, 200], labels=["<30", "30-39", "40-49", "50-59", "60+"]
    ).astype(str)
    df["credit_band"] = pd.cut(
        df["credit_score"], bins=[0, 599, 699, 749, 900],
        labels=["Poor (<600)", "Fair (600-699)", "Good (700-749)", "Excellent (750+)"],
    ).astype(str)
    df["failure_reason"] = df["failure_reason"].fillna("")
    return df


def apply_filters(
    df: pd.DataFrame,
    start=None,
    end=None,
    account_types=None,
    segments=None,
    cities=None,
    txn_types=None,
    channels=None,
    statuses=None,
) -> pd.DataFrame:
    """Return rows matching every non-empty filter (dates are inclusive)."""
    out = df
    if start is not None:
        out = out[out["txn_date"] >= pd.Timestamp(start)]
    if end is not None:
        out = out[out["txn_date"] <= pd.Timestamp(end)]
    for col, vals in [("account_type", account_types), ("customer_segment", segments), ("city", cities),
                      ("transaction_type", txn_types), ("channel", channels), ("status", statuses)]:
        if vals:
            out = out[out[col].isin(vals)]
    return out


# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
def latest_balance_per_customer(df: pd.DataFrame) -> pd.DataFrame:
    """Balance after each customer's most recent transaction in `df`."""
    return (
        df.sort_values("transaction_timestamp")
        .groupby("customer_id", as_index=False)
        .last()[["customer_id", "customer_name", "account_type", "customer_segment",
                 "credit_score", "balance_after"]]
    )


def compute_kpis(df: pd.DataFrame) -> dict:
    ok = df[df["is_success"]]
    n = len(df)
    cust = latest_balance_per_customer(df) if n else pd.DataFrame()
    inflow = float(ok.loc[ok["direction"] == "Credit", "amount"].sum())
    outflow = float(ok.loc[ok["direction"] == "Debit", "amount"].sum())
    return {
        "transactions": n,
        "customers": int(df["customer_id"].nunique()),
        "success_rate": float(df["is_success"].mean()) if n else 0.0,
        "total_volume": float(ok["amount"].sum()),
        "avg_txn_value": float(ok["amount"].mean()) if len(ok) else 0.0,
        "inflow": inflow,
        "outflow": outflow,
        "net_flow": inflow - outflow,
        "avg_balance": float(cust["balance_after"].mean()) if n else 0.0,
        "avg_credit_score": float(cust["credit_score"].mean()) if n else 0.0,
        "fraud_flagged": int(df["is_fraud"].sum()),
        "fraud_rate": float(df["is_fraud"].mean()) if n else 0.0,
        "fraud_amount": float(df.loc[df["is_fraud"] == 1, "amount"].sum()),
    }


# --------------------------------------------------------------------------- #
# Aggregations used by charts
# --------------------------------------------------------------------------- #
def monthly_flow(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly credits, debits and net flow (successful transactions only)."""
    ok = df[df["is_success"]]
    g = ok.pivot_table(index="txn_month", columns="direction", values="amount", aggfunc="sum", fill_value=0.0)
    for col in ("Credit", "Debit"):
        if col not in g:
            g[col] = 0.0
    g = g.reset_index().rename(columns={"Credit": "credits", "Debit": "debits"})
    g["net_flow"] = g["credits"] - g["debits"]
    return g[["txn_month", "credits", "debits", "net_flow"]].sort_values("txn_month")


def monthly_txn_count(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("txn_month", as_index=False).agg(transactions=("transaction_id", "count"))


def type_summary(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[df["is_success"]]
    return (
        ok.groupby("transaction_type")
        .agg(transactions=("transaction_id", "count"), volume=("amount", "sum"), avg_amount=("amount", "mean"))
        .reset_index()
        .sort_values("volume", ascending=False)
    )


def channel_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("channel")
        .agg(transactions=("transaction_id", "count"), volume=("amount", "sum"),
             success_rate=("is_success", "mean"), fraud_flags=("is_fraud", "sum"))
        .reset_index()
        .sort_values("transactions", ascending=False)
    )


def weekday_hour_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Transactions per weekday (rows) x hour of day (columns), zero-filled."""
    m = df.pivot_table(index="weekday", columns="hour", values="transaction_id", aggfunc="count", fill_value=0)
    return m.reindex(index=WEEKDAYS, columns=range(24), fill_value=0)


def hourly_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("hour").agg(transactions=("transaction_id", "count"), fraud_flags=("is_fraud", "sum"))
    return g.reindex(range(24), fill_value=0).rename_axis("hour").reset_index()


def merchant_summary(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[df["is_success"] & df["merchant_category"].ne("Not Applicable") & df["merchant_category"].ne("Utilities")]
    return (
        ok.groupby("merchant_category", as_index=False)
        .agg(spend=("amount", "sum"), transactions=("transaction_id", "count"))
        .sort_values("spend", ascending=False)
    )


def failure_reasons(df: pd.DataFrame) -> pd.DataFrame:
    bad = df[df["status"].ne("Success")]
    bad = bad.assign(failure_reason=bad["failure_reason"].replace("", "Unspecified"))
    return (
        bad.groupby(["status", "failure_reason"], as_index=False).size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )


def city_summary(df: pd.DataFrame) -> pd.DataFrame:
    base = df.groupby("city").agg(customers=("customer_id", "nunique"), transactions=("transaction_id", "count"))
    vol = df[df["is_success"]].groupby("city").agg(volume=("amount", "sum"))
    return base.join(vol, how="left").fillna(0).reset_index().sort_values("volume", ascending=False)


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[df["is_success"]]
    seg = ok.groupby("customer_segment").agg(volume=("amount", "sum"), avg_txn=("amount", "mean"))
    cust = latest_balance_per_customer(df).groupby("customer_segment").agg(
        customers=("customer_id", "count"), avg_balance=("balance_after", "mean"))
    return cust.join(seg, how="left").fillna(0).reset_index()


def account_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    cust = latest_balance_per_customer(df).groupby("account_type").agg(
        customers=("customer_id", "count"), avg_balance=("balance_after", "mean"))
    vol = df[df["is_success"]].groupby("account_type").agg(volume=("amount", "sum"))
    return cust.join(vol, how="left").fillna(0).reset_index()


def age_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    order = ["<30", "30-39", "40-49", "50-59", "60+"]
    g = df[df["is_success"]].groupby("age_group").agg(volume=("amount", "sum"), transactions=("transaction_id", "count"))
    return g.reindex(order, fill_value=0).rename_axis("age_group").reset_index()


def credit_band_summary(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Poor (<600)", "Fair (600-699)", "Good (700-749)", "Excellent (750+)"]
    cust = latest_balance_per_customer(df).assign(
        credit_band=lambda d: pd.cut(d["credit_score"], [0, 599, 699, 749, 900], labels=order).astype(str))
    g = cust.groupby("credit_band").agg(customers=("customer_id", "count"), avg_balance=("balance_after", "mean"))
    return g.reindex(order, fill_value=0).rename_axis("credit_band").reset_index()


def customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    """One row per customer: activity, volume, latest balance and risk counts."""
    ok = df[df["is_success"]]
    act = df.groupby(["customer_id", "customer_name"]).agg(
        transactions=("transaction_id", "count"),
        failed=("status", lambda s: int((s == "Failed").sum())),
        fraud_flags=("is_fraud", "sum"),
    ).reset_index()
    vol = ok.groupby("customer_id").agg(total_volume=("amount", "sum")).reset_index()
    bal = latest_balance_per_customer(df)[["customer_id", "account_type", "customer_segment",
                                           "credit_score", "balance_after"]]
    out = act.merge(vol, on="customer_id", how="left").merge(bal, on="customer_id", how="left")
    out["total_volume"] = out["total_volume"].fillna(0.0)
    return out.sort_values("total_volume", ascending=False)


def fraud_by(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Fraud flags per value of `column` (e.g. channel, transaction_type)."""
    return (
        df.groupby(column)
        .agg(transactions=("transaction_id", "count"), fraud_flags=("is_fraud", "sum"))
        .assign(fraud_rate_pct=lambda d: d["fraud_flags"] / d["transactions"] * 100)
        .reset_index()
        .sort_values("fraud_flags", ascending=False)
    )


def fraud_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["transaction_id", "transaction_timestamp", "customer_name", "transaction_type", "channel",
            "amount", "status", "failure_reason"]
    return df[df["is_fraud"] == 1][cols].sort_values("amount", ascending=False)


def add_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transparent rule-based risk score (0-100) to compare against the fraud flag.

    +40 night-time (00:00-04:59)  +30 amount > 3x the customer's median
    +20 remote channel (Net Banking / Online Card / UPI)  +10 amount > 50,000
    """
    d = df.copy()
    med = d.groupby("customer_id")["amount"].transform("median")
    d["risk_score"] = (
        40 * d["hour"].between(0, 4).astype(int)
        + 30 * (d["amount"] > 3 * med).astype(int)
        + 20 * d["channel"].isin(["Net Banking", "Online Card", "UPI"]).astype(int)
        + 10 * (d["amount"] > 50_000).astype(int)
    )
    return d


# ============================================================================
# 3. DASHBOARD (UI)
# ============================================================================
@st.cache_data(show_spinner=False)
def load_default(path: str):
    return load_data(path)


def show(fig, height: int = 380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    st.plotly_chart(fig)


def money(x: float) -> str:
    """Compact Indian-style formatting: ₹1.25 Cr / ₹4.5 L / ₹12,300."""
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e7:
        return f"{sign}{CURRENCY}{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"{sign}{CURRENCY}{x / 1e5:.2f} L"
    return f"{sign}{CURRENCY}{x:,.0f}"


# --------------------------------------------------------------------------- #
# Data source
# --------------------------------------------------------------------------- #
st.title("🏦 Banking Customer & Transaction Analytics")
st.caption("Synthetic data for demonstration - filter in the sidebar or upload your own transactions CSV.")

uploaded = st.sidebar.file_uploader("Upload your own transactions CSV (optional)", type="csv")
try:
    df = load_data(uploaded) if uploaded is not None else load_default(str(DATA_PATH))
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load data: {exc}")
    st.stop()

# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #
st.sidebar.header("Filters")
d_min, d_max = df["txn_date"].min().date(), df["txn_date"].max().date()
date_range = st.sidebar.date_input("Transaction date", value=(d_min, d_max), min_value=d_min, max_value=d_max)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = date_range
else:
    start, end = d_min, d_max

account_types = st.sidebar.multiselect("Account type", sorted(df["account_type"].unique()))
segments = st.sidebar.multiselect("Customer segment", sorted(df["customer_segment"].unique()))
cities = st.sidebar.multiselect("City", sorted(df["city"].unique()))
txn_types = st.sidebar.multiselect("Transaction type", sorted(df["transaction_type"].unique()))
channels = st.sidebar.multiselect("Channel", sorted(df["channel"].unique()))
statuses = st.sidebar.multiselect("Status", sorted(df["status"].unique()))
st.sidebar.caption("Leave a filter empty to include everything.")

fdf = apply_filters(df, start, end, account_types, segments, cities, txn_types, channels, statuses)
if fdf.empty:
    st.warning("No transactions match the selected filters.")
    st.stop()

# --------------------------------------------------------------------------- #
# KPI cards
# --------------------------------------------------------------------------- #
k = compute_kpis(fdf)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{k['transactions']:,}")
c2.metric("Active customers", f"{k['customers']:,}")
c3.metric("Successful volume", money(k["total_volume"]))
c4.metric("Success rate", f"{k['success_rate']:.1%}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Net cash flow", money(k["net_flow"]), help="Credits minus debits (successful transactions)")
c6.metric("Avg balance / customer", money(k["avg_balance"]))
c7.metric("Avg credit score", f"{k['avg_credit_score']:.0f}")
c8.metric("Fraud-flagged", f"{k['fraud_flagged']} ({k['fraud_rate']:.1%})")

tab_over, tab_cust, tab_txn, tab_fraud, tab_data = st.tabs(
    ["📊 Overview", "👥 Customers", "💳 Transactions", "🚨 Fraud & risk", "🗂️ Data"]
)

# --------------------------------------------------------------------------- #
# Tab 1 - Overview
# --------------------------------------------------------------------------- #
with tab_over:
    flow = monthly_flow(fdf)
    left, right = st.columns(2)
    with left:
        long = flow.melt(id_vars="txn_month", value_vars=["credits", "debits"], var_name="type", value_name="amount")
        show(px.bar(long, x="txn_month", y="amount", color="type", barmode="group",
                    title="Monthly credits vs. debits",
                    labels={"txn_month": "Month", "amount": f"Amount ({CURRENCY})"}))
    with right:
        show(px.line(flow, x="txn_month", y="net_flow", markers=True, title="Monthly net cash flow",
                     labels={"txn_month": "Month", "net_flow": f"Net flow ({CURRENCY})"}))

    left, right = st.columns(2)
    with left:
        show(px.pie(type_summary(fdf), names="transaction_type", values="volume", hole=0.45,
                    title="Volume by transaction type"))
    with right:
        show(px.bar(channel_summary(fdf), x="channel", y="transactions", title="Transactions by channel",
                    labels={"channel": "", "transactions": "Transactions"}))

    show(px.bar(monthly_txn_count(fdf), x="txn_month", y="transactions", title="Transaction count per month",
                labels={"txn_month": "Month", "transactions": "Transactions"}))

# --------------------------------------------------------------------------- #
# Tab 2 - Customers
# --------------------------------------------------------------------------- #
with tab_cust:
    left, right = st.columns(2)
    with left:
        show(px.bar(segment_summary(fdf), x="customer_segment", y="avg_balance",
                    title="Average balance by customer segment",
                    labels={"customer_segment": "", "avg_balance": f"Avg balance ({CURRENCY})"}))
    with right:
        show(px.bar(account_type_summary(fdf), x="account_type", y="avg_balance",
                    title="Average balance by account type",
                    labels={"account_type": "", "avg_balance": f"Avg balance ({CURRENCY})"}))

    left, right = st.columns(2)
    with left:
        show(px.bar(age_group_summary(fdf), x="age_group", y="volume", title="Transaction volume by age group",
                    labels={"age_group": "Age group", "volume": f"Volume ({CURRENCY})"}))
    with right:
        show(px.bar(credit_band_summary(fdf), x="credit_band", y="avg_balance",
                    title="Average balance by credit-score band",
                    labels={"credit_band": "", "avg_balance": f"Avg balance ({CURRENCY})"}))

    cust = customer_summary(fdf)
    show(px.scatter(cust, x="credit_score", y="balance_after", size="transactions", color="customer_segment",
                    hover_data=["customer_name"], title="Credit score vs. latest balance (bubble = # transactions)",
                    labels={"credit_score": "Credit score", "balance_after": f"Latest balance ({CURRENCY})"}),
         height=430)
    st.subheader("Top 10 customers by transaction volume")
    st.dataframe(cust.head(10), hide_index=True)

# --------------------------------------------------------------------------- #
# Tab 3 - Transactions
# --------------------------------------------------------------------------- #
with tab_txn:
    show(px.imshow(weekday_hour_matrix(fdf), aspect="auto", color_continuous_scale="Blues",
                   labels=dict(x="Hour of day", y="", color="Txns"), title="When do customers transact? (weekday x hour)"),
         height=380)

    left, right = st.columns(2)
    with left:
        show(px.bar(merchant_summary(fdf), x="merchant_category", y="spend",
                    title="Card & UPI spend by merchant category",
                    labels={"merchant_category": "", "spend": f"Spend ({CURRENCY})"}))
    with right:
        show(px.bar(city_summary(fdf).head(10), x="city", y="volume", title="Top cities by volume",
                    labels={"city": "", "volume": f"Volume ({CURRENCY})"}))

    fr = failure_reasons(fdf)
    if fr.empty:
        st.info("No failed or pending transactions in the current selection.")
    else:
        show(px.bar(fr, x="failure_reason", y="count", color="status", title="Failed / pending transactions by reason",
                    labels={"failure_reason": "", "count": "Count"}))

# --------------------------------------------------------------------------- #
# Tab 4 - Fraud & risk
# --------------------------------------------------------------------------- #
with tab_fraud:
    f1, f2, f3 = st.columns(3)
    f1.metric("Flagged transactions", f"{k['fraud_flagged']}")
    f2.metric("Fraud rate", f"{k['fraud_rate']:.2%}")
    f3.metric("Value at risk", money(k["fraud_amount"]))

    left, right = st.columns(2)
    with left:
        show(px.bar(hourly_summary(fdf), x="hour", y="fraud_flags", title="Fraud flags by hour of day",
                    labels={"hour": "Hour (0-23)", "fraud_flags": "Flagged"}))
    with right:
        show(px.bar(fraud_by(fdf, "channel"), x="channel", y="fraud_flags", title="Fraud flags by channel",
                    labels={"channel": "", "fraud_flags": "Flagged"}))

    show(px.bar(fraud_by(fdf, "transaction_type"), x="transaction_type", y="fraud_rate_pct",
                title="Fraud rate by transaction type (%)",
                labels={"transaction_type": "", "fraud_rate_pct": "Fraud rate %"}))

    st.subheader("Flagged transactions")
    ft = fraud_table(fdf)
    if ft.empty:
        st.info("No fraud-flagged transactions in the current selection.")
    else:
        st.dataframe(ft, hide_index=True)

    with st.expander("Rule-based risk score vs. the fraud flag"):
        scored = add_risk_score(fdf)
        st.write("A simple, explainable score: +40 night-time, +30 amount > 3x the customer's median, "
                 "+20 remote channel, +10 amount > 50,000. Compare average score of flagged vs. normal transactions:")
        cmp_df = scored.groupby("is_fraud", as_index=False)["risk_score"].mean()
        cmp_df["is_fraud"] = cmp_df["is_fraud"].map({0: "Normal", 1: "Flagged"})
        show(px.bar(cmp_df, x="is_fraud", y="risk_score", title="Average rule-based risk score",
                    labels={"is_fraud": "", "risk_score": "Avg risk score"}), height=320)

# --------------------------------------------------------------------------- #
# Tab 5 - Data
# --------------------------------------------------------------------------- #
with tab_data:
    st.write(f"{len(fdf):,} transactions after filters")
    cols = [c for c in REQUIRED_COLUMNS if c in fdf.columns]
    st.dataframe(fdf[cols], hide_index=True)
    st.download_button("Download filtered data (CSV)", fdf[cols].to_csv(index=False).encode("utf-8"),
                       file_name="filtered_transactions.csv", mime="text/csv")
