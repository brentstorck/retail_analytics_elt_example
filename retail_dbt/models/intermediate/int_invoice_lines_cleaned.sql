-- Intermediate: the set of invoice lines that count as revenue activity.
-- Business rule applied here (and documented): drop non-revenue lines (price <= 0, e.g.
-- manual adjustments, samples, bad-debt write-offs) and any line missing a quantity.
-- Cancellations and returns are KEPT with their negative revenue so net metrics are correct.

with lines as (

    select * from {{ ref('stg_online_retail') }}

)

select
    invoice_line_id,
    invoice_id,
    stock_code,
    description,
    customer_id,
    country,
    quantity,
    unit_price,
    line_revenue,
    invoiced_at,
    invoice_date,
    cast(date_trunc('month', invoice_date) as date) as invoice_month,
    is_cancellation,
    is_return,
    is_guest
from lines
where not is_non_revenue
  and quantity is not null
