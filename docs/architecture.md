# Architecture & metric dictionary

## Design principles

- **ELT, not ETL.** Land raw data first (`raw.online_retail`), then transform in the
  warehouse with dbt. Raw stays an immutable mirror of the source so any transformation
  can be re-derived and debugged.
- **Layered models.** `staging` (rename/type/flag, 1:1 with source) → `intermediate`
  (business rules, grain changes) → `marts` (dimensional core + metric marts). Each layer
  has one job; nothing reaches across layers.
- **Marts are the contract.** BI tools read only marts. Marts are tables (fast), tested,
  and documented; the joins and edge cases are solved once, upstream.
- **Tests are part of the pipeline.** `dbt build` runs models and tests together; a failed
  test fails the run, so bad data never reaches a dashboard.

## Layer reference

| Model                          | Layer        | Grain                         |
|--------------------------------|--------------|-------------------------------|
| `stg_online_retail`            | staging      | invoice line                  |
| `int_invoice_lines_cleaned`    | intermediate | revenue-bearing invoice line  |
| `int_orders`                   | intermediate | order (invoice)               |
| `fct_invoice_lines`            | marts/core   | invoice line                  |
| `fct_orders`                   | marts/core   | order                         |
| `dim_customers`                | marts/core   | customer                      |
| `dim_products`                 | marts/core   | product (stock code)          |
| `dim_dates`                    | marts/core   | day                           |
| `mart_revenue_daily`           | marts/mkt    | day                           |
| `mart_revenue_monthly`         | marts/mkt    | month                         |
| `mart_customer_cohorts`        | marts/mkt    | cohort month × age            |
| `mart_rfm_segments`            | marts/mkt    | customer                      |
| `mart_country_performance`     | marts/mkt    | country                       |
| `mart_product_performance`     | marts/mkt    | product                       |
| `mart_data_quality`            | marts/ops    | pipeline (1 row)              |

## Key business rules

- **Cancellation:** invoice number begins with `C`. Kept (with negative revenue) so net
  metrics are correct; excluded from the customer dimension and most marts via
  `not is_cancellation`.
- **Return:** negative quantity. Drives `return_rate` in `dim_products`.
- **Non-revenue line:** `unit_price <= 0` (manual adjustments, samples, bad debt). Dropped
  from revenue analytics in `int_invoice_lines_cleaned`; counted in `mart_data_quality`.
- **Guest:** null `customer_id` (~20% of lines). Counted in revenue/orders but excluded
  from customer-level marts (cohorts, RFM) since they can't be tracked over time.
- **Dedup:** exact-duplicate raw rows are removed in the loader before modeling.

## Metric definitions

- **Net revenue** = Σ(quantity × unit_price) over revenue-bearing lines (returns subtract).
- **AOV** = net revenue ÷ orders.
- **New customer (in period)** = order date equals the customer's first order date.
- **Retention rate (cohort, month m)** = distinct customers from the cohort who ordered in
  month *m* ÷ cohort size. Month 0 is 100% by construction.
- **RFM scores** = quintiles (1–5) of recency (inverted), frequency, monetary across all
  known customers; combined into named segments for lifecycle targeting.
- **Recency** = days from a customer's last order to the latest order in the dataset
  (the corpus is historical, so "today" is anchored to the data, not wall-clock time).

## Mapping to the warehouse

DuckDB file at `DUCKDB_PATH`, catalog `retail`, schemas: `raw`, `staging`, `intermediate`,
`marts`, `seeds`. Swapping to Snowflake/BigQuery is a `profiles.yml` change only.
