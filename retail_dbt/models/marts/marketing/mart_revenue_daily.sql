-- Metric mart: daily revenue and customer activity on a COMPLETE calendar.
-- Aggregates non-cancelled orders, then joins onto dim_dates so days with zero sales still
-- show up as a 0 row instead of silently disappearing (which would distort any trend or
-- moving-average chart). New vs returning is decided by whether the order falls on the
-- customer's first order date.

with orders as (

    select
        o.invoice_id,
        o.customer_id,
        o.order_date,
        o.total_quantity,
        o.order_revenue,
        c.first_order_date
    from {{ ref('fct_orders') }} o
    left join {{ ref('dim_customers') }} c using (customer_id)
    where not o.is_cancellation

),

daily as (

    select
        order_date,
        count(distinct invoice_id)                                                as n_orders,
        count(distinct customer_id)                                               as n_active_customers,
        count(distinct case when order_date = first_order_date then customer_id end) as n_new_customers,
        sum(total_quantity)                                                       as n_units,
        round(sum(order_revenue), 2)                                             as revenue
    from orders
    group by order_date

),

date_range as (

    select min(order_date) as start_date, max(order_date) as end_date from daily

),

calendar as (

    select d.date_key
    from {{ ref('dim_dates') }} d
    cross join date_range r
    where d.date_key between r.start_date and r.end_date

)

select
    cal.date_key                                                            as order_date,
    coalesce(dy.n_orders, 0)                                                as n_orders,
    coalesce(dy.n_active_customers, 0)                                      as n_active_customers,
    coalesce(dy.n_new_customers, 0)                                         as n_new_customers,
    coalesce(dy.n_active_customers, 0) - coalesce(dy.n_new_customers, 0)    as n_returning_customers,
    coalesce(dy.n_units, 0)                                                 as n_units,
    coalesce(dy.revenue, 0)                                                 as revenue,
    round(dy.revenue / nullif(dy.n_orders, 0), 2)                          as avg_order_value
from calendar cal
left join daily dy on cal.date_key = dy.order_date
order by cal.date_key
