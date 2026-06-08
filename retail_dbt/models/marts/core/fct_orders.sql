-- Fact: one row per order (invoice). Net order revenue and order-level flags.

select
    invoice_id,
    customer_id,
    country,
    ordered_at,
    order_date,
    order_month,
    n_lines,
    total_quantity,
    order_revenue,
    is_cancellation,
    is_guest
from {{ ref('int_orders') }}
