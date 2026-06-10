"""Local self-serve dashboard over the dbt marts (a Hex stand-in you can run today).

    streamlit run dashboard/app.py

Reads the same marts Hex would read, straight from the DuckDB warehouse, and renders the
core views: headline KPIs, revenue trend, cohort retention, RFM segments, and geography.
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = os.environ.get("DUCKDB_PATH", str(REPO_ROOT / "warehouse" / "retail.duckdb"))

st.set_page_config(page_title="Retail Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def q(sql: str) -> pd.DataFrame:
    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


st.title("Retail Analytics: Revenue & Retention")
st.caption(f"Reading marts from `{DUCKDB_PATH}`")

if not Path(DUCKDB_PATH).exists():
    st.error(
        "Warehouse not found. Build it first:\n\n"
        "```\npython -m pipeline.run\n```"
    )
    st.stop()

# --- Headline KPIs -------------------------------------------------------------
kpi = q(
    """
    select
        round(sum(revenue)) as revenue,
        sum(n_orders) as orders,
        sum(n_new_customers) as new_customers,
        round(sum(revenue) / nullif(sum(n_orders), 0), 2) as aov
    from marts.mart_revenue_daily
    """
).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Net revenue", f"£{kpi.revenue:,.0f}")
c2.metric("Orders", f"{int(kpi.orders):,}")
c3.metric("New customers", f"{int(kpi.new_customers):,}")
c4.metric("Avg order value", f"£{kpi.aov:,.2f}")

st.divider()

# --- Revenue trend -------------------------------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("Monthly revenue")
    monthly = q("select month, revenue, revenue_mom_pct from marts.mart_revenue_monthly order by month")
    fig = px.bar(monthly, x="month", y="revenue")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("New vs returning customers")
    mix = q(
        """
        select month, n_new_customers as "New", n_returning_customers as "Returning"
        from marts.mart_revenue_monthly order by month
        """
    )
    mix_long = mix.melt(id_vars="month", var_name="type", value_name="customers")
    fig = px.bar(mix_long, x="month", y="customers", color="type", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Cohort retention heatmap --------------------------------------------------
st.subheader("Cohort retention")
cohorts = q(
    """
    select cohort_month, months_since_cohort, retention_rate
    from marts.mart_customer_cohorts
    where months_since_cohort between 0 and 12
    """
)
if not cohorts.empty:
    pivot = cohorts.pivot(index="cohort_month", columns="months_since_cohort", values="retention_rate")
    fig = px.imshow(
        pivot,
        labels=dict(x="Months since first order", y="Cohort", color="Retention"),
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=".0%",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Segments + geography ------------------------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("Customers by RFM segment")
    seg = q(
        """
        select rfm_segment, count(*) as customers, round(sum(monetary)) as revenue
        from marts.mart_rfm_segments group by rfm_segment order by revenue desc
        """
    )
    fig = px.bar(seg, x="customers", y="rfm_segment", orientation="h")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue by region")
    geo = q(
        """
        select region, round(sum(revenue)) as revenue
        from marts.mart_country_performance group by region order by revenue desc
        """
    )
    fig = px.bar(geo, x="region", y="revenue")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Top products")
st.dataframe(
    q(
        """
        select revenue_rank, stock_code, description, units_sold, total_revenue, return_rate
        from marts.mart_product_performance order by revenue_rank limit 25
        """
    ),
    use_container_width=True,
    hide_index=True,
)

# --- Data quality footer -------------------------------------------------------
with st.expander("Pipeline health (mart_data_quality)"):
    st.dataframe(q("select * from marts.mart_data_quality"), use_container_width=True, hide_index=True)
