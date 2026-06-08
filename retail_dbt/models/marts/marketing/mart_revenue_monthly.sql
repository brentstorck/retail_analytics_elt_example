-- Metric mart: monthly revenue with month-over-month growth and customer mix.

with orders as (

    select
        o.invoice_id,
        o.customer_id,
        o.order_month,
        o.order_date,
        o.order_revenue,
        c.first_order_date
    from {{ ref('fct_orders') }} o
    left join {{ ref('dim_customers') }} c using (customer_id)
    where not o.is_cancellation

),

monthly as (

    select
        order_month                                                              as month,
        count(distinct invoice_id)                                              as n_orders,
        count(distinct customer_id)                                             as n_active_customers,
        count(distinct case when order_date = first_order_date then customer_id end) as n_new_customers,
        round(sum(order_revenue), 2)                                            as revenue
    from orders
    group by order_month

)

select
    month,
    n_orders,
    n_active_customers,
    n_new_customers,
    n_active_customers - n_new_customers                                        as n_returning_customers,
    revenue,
    round(revenue / nullif(n_orders, 0), 2)                                     as avg_order_value,
    round(revenue - lag(revenue) over (order by month), 2)                      as revenue_mom_change,
    round(
        (revenue - lag(revenue) over (order by month))
        / nullif(lag(revenue) over (order by month), 0) * 100
    , 1)                                                                        as revenue_mom_pct
from monthly
order by month
