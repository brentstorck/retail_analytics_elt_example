# CLAUDE.md

Guidance for Claude Code (and any engineer) working in this repository.

## What this project is

An end-to-end **analytics engineering** project built on a real, public e-commerce
dataset. It ingests raw transaction logs, transforms them into canonical, tested data
models with **dbt**, orchestrates the whole run with **Airflow**, and serves the results
as self-serve dashboards in **Hex** (with a local Streamlit preview of the same models).

It was deliberately scoped to mirror the **Anthropic Analytics Data Engineer** role:
raw logs → canonical datasets → trusted company metrics → self-serve dashboards, with
data-integrity tests and freshness SLAs throughout. The point is not the dataset; it is
to demonstrate the *exact* toolchain and patterns that role uses, working together.

> Honesty note for anyone extending this: this is a personal portfolio project on a
> public dataset (UCI Online Retail II). It is not production infrastructure for a real
> company. Keep claims about it accurate: "built to demonstrate X," not "ran X in
> production." The engineering is real; the business is illustrative.

## The stack and why each piece is here

| Layer            | Tool                  | Maps to JD requirement                                  |
|------------------|-----------------------|---------------------------------------------------------|
| Ingestion (E/L)  | Python (`pipeline/`)  | "multi-step ETL jobs," "SQL and Python"                 |
| Warehouse        | DuckDB                | local stand-in for Snowflake/BigQuery; zero-setup       |
| Transformation   | dbt (`retail_dbt/`)   | "build and manage key data pipelines in dbt"            |
| Orchestration    | Airflow (`airflow/`)  | "workflow management platforms like Airflow"            |
| Version control  | git / GitHub          | "version control management tools through GitHub"       |
| BI / self-serve  | Hex (`hex/`)          | "dashboarding in visualization tools like Hex"          |
| Local BI preview | Streamlit (`dashboard/`) | runnable proof of the marts before Hex is connected  |

DuckDB is used as the warehouse so the project runs on any laptop with no cloud account.
Everything dbt does here (sources, staging → marts, tests, docs, freshness) is identical
against Snowflake/BigQuery; only the `profiles.yml` adapter changes. Spark is intentionally
**not** used: at this data scale it would be cargo-culting, and the JD does not ask for it.

## Architecture (data flow)

```
UCI Online Retail II (.xlsx, two sheets)
        │  pipeline/extract.py   (download + cache, idempotent)
        ▼
   data/online_retail_II.xlsx
        │  pipeline/load.py      (normalize cols, add _loaded_at, dedupe exact dups)
        ▼
   DuckDB: raw.online_retail                      ← dbt SOURCE (with freshness SLA)
        │  dbt: models/staging                    ← clean, type, flag cancellations/returns
        ▼
   staging.stg_online_retail
        │  dbt: models/intermediate               ← business logic, line + order grain
        ▼
   intermediate.int_invoice_lines_cleaned, int_orders
        │  dbt: models/marts/core                 ← dimensional model (star schema)
        ▼
   dim_customers, dim_products, dim_dates, fct_invoice_lines, fct_orders
        │  dbt: models/marts/marketing + ops      ← GTM/Product metrics + data-quality
        ▼
   mart_revenue_daily/monthly, mart_customer_cohorts, mart_rfm_segments,
   mart_country_performance, mart_product_performance, mart_data_quality
        │  Hex / Streamlit
        ▼
   self-serve dashboards (revenue, retention, segments, geo, product, pipeline health)
```

## dbt conventions used here (follow these when adding models)

- **Layering:** `staging/` (views, 1:1 with sources, only renaming/typing/light flags) →
  `intermediate/` (views, business logic, joins) → `marts/` (tables, what BI reads).
- **Naming:** `stg_`, `int_`, `dim_`, `fct_`, `mart_`. Surrogate keys via
  `dbt_utils.generate_surrogate_key`. Primary keys are the first column and are tested
  `unique` + `not_null`.
- **Schemas:** custom schemas land verbatim (`staging`, `intermediate`, `marts`) via the
  `generate_schema_name` macro override in `macros/`.
- **Sources:** declared in `models/staging/_staging__sources.yml` with `loaded_at_field`
  and `freshness` (warn 36h / error 7d), the data SLA.
- **Tests = data integrity:** generic tests (`unique`, `not_null`, `relationships`,
  `accepted_values`, `dbt_utils.accepted_range`) live next to models in `_*.yml`.
  Cross-model invariants live as singular tests in `tests/` (e.g. order revenue must
  reconcile to the sum of its line items; no future invoice dates; retention ≤ 100%).
- **Docs:** every model and key column has a `description`. `dbt docs generate` builds the
  lineage graph and catalog.
- **Exposures:** `models/marts/_exposures.yml` registers the Hex dashboard as a downstream
  consumer so lineage runs source → mart → dashboard.
- **Seeds:** `seeds/country_region.csv` enriches country → region for GTM rollups.

## How to run

See `README.md` for the full walkthrough. The short version:

```bash
# 1. install
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. set the warehouse path (loader + dbt must agree)
$env:DUCKDB_PATH = "$PWD\warehouse\retail.duckdb"   # PowerShell

# 3. run the whole pipeline without Airflow
python -m pipeline.run            # extract -> load -> dbt build -> export marts

# or step by step
python -m pipeline.extract
python -m pipeline.load
cd retail_dbt && dbt deps && dbt seed && dbt build && dbt docs generate

# 4. preview the marts locally
streamlit run dashboard/app.py
```

Airflow is the *orchestrated* version of the same steps (`airflow/dags/retail_analytics_dag.py`);
run it via the provided `docker-compose.yaml`. The plain-Python `pipeline.run` exists so the
project is verifiable on Windows without Docker/WSL.

## Map to the job description (for the resume)

Every bolded JD phrase below is demonstrated somewhere concrete in this repo:

- **"build and manage key data pipelines in dbt that transform raw logs into canonical
  datasets"** → `retail_dbt/models/` (staging → intermediate → marts star schema).
- **"multi-step ETL jobs ... workflow management platforms like Airflow"** →
  `pipeline/` + `airflow/dags/retail_analytics_dag.py`.
- **"high data integrity standards and SLAs"** → dbt tests (generic + singular) and
  source freshness; `mart_data_quality` surfaces pipeline health as a dashboard.
- **"insightful and reliable dashboards to track ... core metrics"** → `hex/` queries +
  `dashboard/` Streamlit app over the marts.
- **"self-serve analytics to scale across the company"** → pre-aggregated marts designed
  so a non-engineer can build a chart with one `select * from mart_...`.
- **"partnering with GTM and Product leads"** → the marts are deliberately the metrics
  those teams own: revenue/AOV/geo (GTM), cohort retention + RFM segments (Product/CRM).
- **"SQL and Python," "version control through GitHub"** → throughout; this repo.

## When extending this repo

- Add new metrics as marts, not as one-off queries. If two dashboards need it, it's a mart.
- Every new model gets a `description` and at least a `not_null`/`unique` test on its key.
- Run `dbt build` (not just `run`) so tests execute with the models.
- Keep `pipeline/` importable with no Airflow dependency; the DAG only orchestrates it.
- Don't break the source → mart → exposure lineage; it's part of the story.
