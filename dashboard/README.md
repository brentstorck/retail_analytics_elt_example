# Local dashboard (Streamlit)

A runnable preview of the marts so the project is demonstrable end-to-end without a cloud
BI account. **Hex is the intended production BI tool** (see `../hex/`); this Streamlit app
reads the exact same dbt marts from DuckDB and renders the same views.

```bash
# after the warehouse is built (python -m pipeline.run)
streamlit run dashboard/app.py
```

It reads `DUCKDB_PATH` (defaults to `../warehouse/retail.duckdb`) and renders headline
KPIs, monthly revenue, the cohort-retention heatmap, RFM segments, revenue by region, and
the data-quality snapshot.
