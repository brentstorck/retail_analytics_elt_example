-- Dimension: one row per known customer. Lifetime aggregates plus the RFM inputs
-- (recency/frequency/monetary). Recency is measured against the latest activity in the
-- dataset (a fixed historical corpus), not wall-clock time, so metrics are reproducible.
-- Guest (null customer_id) and cancelled orders are excluded from the customer dimension.

with orders as (

    select *
    from {{ ref('int_orders') }}
    where customer_id is not null
      and not is_cancellation

),

anchor as (

    select max(order_date) as as_of_date from orders

),

agg as (

    select
        customer_id,
        arg_max(country, ordered_at)                 as country,
        min(order_date)                              as first_order_date,
        max(order_date)                              as last_order_date,
        cast(date_trunc('month', min(order_date)) as date) as cohort_month,
        count(distinct invoice_id)                   as lifetime_orders,
        sum(total_quantity)                          as lifetime_units,
        round(sum(order_revenue), 2)                 as lifetime_revenue
    from orders
    group by customer_id

)

select
    a.customer_id,
    a.country,
    a.first_order_date,
    a.last_order_date,
    a.cohort_month,
    a.lifetime_orders,
    a.lifetime_units,
    a.lifetime_revenue,
    round(a.lifetime_revenue / nullif(a.lifetime_orders, 0), 2) as avg_order_value,
    date_diff('day', a.last_order_date, anchor.as_of_date)      as recency_days,
    date_diff('day', a.first_order_date, a.last_order_date)     as tenure_days
from agg a
cross join anchor
