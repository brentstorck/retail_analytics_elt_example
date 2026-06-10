"""Render key marts to static PNGs for the README.

    python scripts/export_charts.py

These are the same views the Streamlit/Hex dashboards show, exported as images so the repo
is visually complete without a running BI tool. Requires the warehouse to be built and
`kaleido` installed (pip install -r requirements-dev.txt).
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb
import plotly.express as px

ROOT = Path(__file__).resolve().parents[1]
DB = os.environ.get("DUCKDB_PATH", str(ROOT / "warehouse" / "retail.duckdb"))
OUT = ROOT / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)

TEMPLATE = "plotly_white"


def main() -> None:
    con = duckdb.connect(DB, read_only=True)
    try:
        # 1) Monthly net revenue
        m = con.execute(
            "select month, revenue from marts.mart_revenue_monthly order by month"
        ).fetchdf()
        fig = px.bar(m, x="month", y="revenue", title="Monthly net revenue (GBP)", template=TEMPLATE)
        fig.write_image(OUT / "revenue_monthly.png", width=1000, height=430, scale=2)

        # 2) Cohort retention heatmap
        c = con.execute(
            "select cohort_month, months_since_cohort, retention_rate "
            "from marts.mart_customer_cohorts where months_since_cohort <= 12"
        ).fetchdf()
        piv = c.pivot(index="cohort_month", columns="months_since_cohort", values="retention_rate")
        fig = px.imshow(
            piv,
            color_continuous_scale="Blues",
            aspect="auto",
            title="Monthly acquisition-cohort retention",
            labels=dict(x="Months since first order", y="Cohort", color="Retention"),
            template=TEMPLATE,
        )
        fig.write_image(OUT / "cohort_retention.png", width=1000, height=480, scale=2)

        # 3) Revenue by region
        r = con.execute(
            "select region, sum(revenue) as revenue from marts.mart_country_performance "
            "group by region order by revenue desc"
        ).fetchdf()
        fig = px.bar(
            r, x="revenue", y="region", orientation="h",
            title="Revenue by region", template=TEMPLATE,
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        fig.write_image(OUT / "revenue_by_region.png", width=1000, height=430, scale=2)
    finally:
        con.close()

    print(f"wrote charts to {OUT}")


if __name__ == "__main__":
    main()
