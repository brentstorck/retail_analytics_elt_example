-- Metric mart: daily revenue and customer activity. Non-cancelled orders only.
-- New vs returning is decided by whether the order falls on the customer's first order date.

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

)

select
    order_date,
    n_orders,
    n_active_customers,
    n_new_customers,
    n_active_customers - n_new_customers          as n_returning_customers,
    n_units,
    revenue,
    round(revenue / nullif(n_orders, 0), 2)       as avg_order_value
from daily
order by order_date
