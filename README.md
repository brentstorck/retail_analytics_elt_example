# Retail Analytics Platform

End-to-end **analytics engineering** project: raw e-commerce transaction logs → canonical,
tested data models → company metrics → self-serve dashboards.

**Stack:** Python (ETL) · DuckDB (warehouse) · **dbt** (transformation + tests + docs) ·
**Airflow** (orchestration) · **Hex** (BI / self-serve) · git/GitHub.
**Data:** [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) —
~1M real UK online-retail transactions, 2009–2011 (public, no login required).

This project transforms raw invoice logs into a star-schema warehouse and a set of marts
that answer the questions a **GTM/Product** analytics team actually asks: *How is revenue
trending? Are we retaining the customers we acquire? Which segments and countries drive
growth? Which products and pipelines are healthy?* Data-integrity tests and freshness SLAs
run on every build.

```
raw logs ──▶ staging ──▶ intermediate ──▶ dim/fct (star schema) ──▶ metric marts ──▶ Hex / Streamlit
            (dbt views)   (dbt views)        (dbt tables)            (dbt tables)
            └──────────────── tested + documented + freshness-checked ───────────────┘
                              orchestrated end-to-end by Airflow
```

## What's in here

| Path                          | What it is                                                        |
|-------------------------------|------------------------------------------------------------------|
| `pipeline/`                   | Python extract + load + export (the "EL" of ELT), no Airflow dep  |
| `retail_dbt/`                 | dbt project: sources, staging → marts, tests, seeds, docs, exposures |
| `airflow/`                    | Airflow DAG + Docker setup that orchestrates the same pipeline    |
| `hex/`                        | Hex dashboard spec + the exact SQL for each chart                 |
| `dashboard/`                  | Streamlit app — local preview of the marts (runnable today)       |
| `docs/architecture.md`        | deeper design notes and the metric dictionary                     |
| `CLAUDE.md`                   | engineering guide + job-description mapping                        |

## Quickstart (Windows / PowerShell)

```powershell
# 1) environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2) point the loader and dbt at the same warehouse file
$env:DUCKDB_PATH = "$PWD\warehouse\retail.duckdb"

# 3) run the whole pipeline (extract -> load -> dbt build -> export marts)
python -m pipeline.run

# 4) explore
cd retail_dbt
dbt docs generate; dbt docs serve      # lineage graph + data catalog at localhost:8080
cd ..
streamlit run dashboard/app.py          # self-serve dashboards over the marts
```

macOS/Linux: replace the activate line with `. .venv/bin/activate` and set
`export DUCKDB_PATH="$PWD/warehouse/retail.duckdb"`.

## Run it step by step

```bash
python -m pipeline.extract     # download + cache the dataset (idempotent)
python -m pipeline.load        # load raw .xlsx -> DuckDB raw.online_retail

cd retail_dbt
dbt deps                       # install dbt_utils
dbt seed                       # load country -> region mapping
dbt build                      # run models AND tests together
dbt source freshness           # check the data SLA
dbt docs generate              # build lineage + catalog
cd ..

python -m pipeline.export      # write marts to data/exports/*.csv for Hex upload
```

## Orchestrated run (Airflow)

The DAG `airflow/dags/retail_analytics_dag.py` runs the same steps on a daily schedule with
retries, task SLAs, and a freshness check. Airflow does not run natively on Windows, so use
the provided Docker setup (or WSL):

```bash
cd airflow
docker compose up -d           # Airflow UI at http://localhost:8080  (admin/admin)
# trigger the "retail_analytics" DAG from the UI
```

See `airflow/README` notes in `docker-compose.yaml` for details.

## The marts (what BI reads)

| Mart                         | Grain                         | Used for                                  |
|------------------------------|-------------------------------|-------------------------------------------|
| `mart_revenue_daily`         | day                           | revenue, orders, AOV, new vs returning    |
| `mart_revenue_monthly`       | month                         | MoM growth, active/new customers          |
| `mart_customer_cohorts`      | acquisition month × age       | retention curves / cohort heatmap         |
| `mart_rfm_segments`          | customer                      | RFM segmentation (Champions … Lost)       |
| `mart_country_performance`   | country (+ region)            | geo revenue, AOV, share                   |
| `mart_product_performance`   | product                       | top products, revenue, return rate        |
| `mart_data_quality`          | pipeline                      | row counts, null %, cancel/return rates   |

Full column-level definitions are in the dbt docs (`dbt docs serve`) and `docs/architecture.md`.

## Data integrity (the SLA story)

- **Source freshness** on `raw.online_retail._loaded_at` (warn 36h / error 7d).
- **Generic tests** — `unique`, `not_null`, `relationships`, `accepted_values`,
  `dbt_utils.accepted_range` — on keys, foreign keys, and value ranges.
- **Singular tests** in `retail_dbt/tests/` enforce cross-model invariants:
  - order revenue reconciles to the sum of its line items,
  - no invoice dates in the future,
  - cohort retention never exceeds 100%.
- `dbt build` fails the pipeline if any test fails, so bad data never reaches a dashboard.

## License / data attribution

Code: MIT (see `LICENSE`). Data: UCI Machine Learning Repository, *Online Retail II*
(Chen, 2019), used for educational/portfolio purposes.
