-- Ops mart: a single-row pipeline-health snapshot, surfaced as a dashboard so data
-- integrity is monitored, not assumed. Pairs with dbt tests + source freshness.

with staged as (

    select * from {{ ref('stg_online_retail') }}

)

select
    count(*)                                                            as n_rows,
    count(distinct invoice_id)                                          as n_invoices,
    count(distinct customer_id)                                         as n_customers,
    count(distinct stock_code)                                          as n_products,
    round(100.0 * sum(case when is_guest         then 1 else 0 end) / count(*), 2) as pct_guest_lines,
    round(100.0 * sum(case when is_cancellation  then 1 else 0 end) / count(*), 2) as pct_cancellation_lines,
    round(100.0 * sum(case when is_return        then 1 else 0 end) / count(*), 2) as pct_return_lines,
    sum(case when is_non_revenue then 1 else 0 end)                     as n_non_revenue_lines,
    min(invoice_date)                                                   as min_invoice_date,
    max(invoice_date)                                                   as max_invoice_date,
    max(_loaded_at)                                                     as last_loaded_at,
    date_diff('day', max(invoice_date), cast(max(_loaded_at) as date))  as source_lag_days
from staged
