# Hex dashboard

The serving layer. Hex reads the dbt **marts** (never raw tables) and presents them as a
single self-serve app. Because the marts are already aggregated and tested, each chart is
one short `SELECT`. That is the whole point of the marts layer: a non-engineer can build
or tweak a chart without touching SQL joins or worrying about correctness.

## Dashboard layout

A single Hex app, "Executive Revenue & Retention," with five sections:

1. **Headline KPIs** (tiles): total net revenue, orders, customers, AOV, return rate.
   Cell: `queries/01_kpi_headline.sql`
2. **Revenue trend** (line + bar combo): monthly revenue with MoM % and new vs returning
   customers. Cell: `queries/02_revenue_trend.sql`
3. **Cohort retention** (heatmap / pivot): acquisition month by months-since, colored by
   retention rate. Cell: `queries/03_cohort_retention.sql`
4. **Customer segments** (bar): customer count and revenue by RFM segment, with a segment
   filter that cross-filters the page. Cell: `queries/04_rfm_segments.sql`
5. **Geography & products**: revenue by region/country (map or bar) and a top-products
   table. Cells: `queries/05_country_performance.sql`, `queries/06_top_products.sql`

Add an input parameter (e.g. a date range or country dropdown) and wire it into the cells
to demonstrate Hex's parameterized, interactive apps.

## Connecting Hex to the data (pick one)

**A. MotherDuck (recommended, keeps it a true warehouse connection).**
MotherDuck is hosted DuckDB and Hex has a native connector. Push the local warehouse up,
then point Hex at it:

```sql
-- in the DuckDB CLI, after building the project locally
ATTACH 'md:';                              -- connect to MotherDuck (after `SET motherduck_token`)
CREATE DATABASE retail FROM 'warehouse/retail.duckdb';
```

Then in Hex, add a MotherDuck data connection and query `retail.marts.mart_*`.

**B. CSV upload (works on Hex's free tier, no warehouse).**
Run `python -m pipeline.export` to write `data/exports/*.csv`, then upload those files as
Hex data sources. Each mart becomes a table you can query or chart directly.

**C. Native warehouse (production shape).**
If the dbt project is pointed at Snowflake/BigQuery instead of DuckDB (a `profiles.yml`
change only), connect Hex straight to that warehouse and query the `marts` schema.

## Note

The `.sql` files here are written against the DuckDB/MotherDuck schema names
(`marts.mart_*`). If you load the marts via CSV upload, replace `marts.mart_x` with the
uploaded table name Hex assigns.
