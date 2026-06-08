-- Singular test: each order's revenue must equal the sum of its line revenues.
-- Catches grain/aggregation bugs between fct_invoice_lines and fct_orders. Allows a
-- 1-penny tolerance for floating-point rounding.

with line_totals as (

    select invoice_id, round(sum(line_revenue), 2) as lines_revenue
    from {{ ref('fct_invoice_lines') }}
    group by invoice_id

),

orders as (

    select invoice_id, order_revenue
    from {{ ref('fct_orders') }}

)

select
    o.invoice_id,
    o.order_revenue,
    l.lines_revenue
from orders o
join line_totals l using (invoice_id)
where abs(o.order_revenue - l.lines_revenue) > 0.01
