-- Intermediate: roll invoice lines up to order grain (one row per invoice).
-- An "order" is a single invoice; revenue is the net of all its lines.

with lines as (

    select * from {{ ref('int_invoice_lines_cleaned') }}

)

select
    invoice_id,
    any_value(customer_id)                               as customer_id,
    any_value(country)                                   as country,
    min(invoiced_at)                                     as ordered_at,
    cast(min(invoiced_at) as date)                       as order_date,
    cast(date_trunc('month', min(invoiced_at)) as date) as order_month,
    count(*)                                             as n_lines,
    sum(quantity)                                        as total_quantity,
    round(sum(line_revenue), 2)                          as order_revenue,
    bool_or(is_cancellation)                             as is_cancellation,
    bool_and(is_guest)                                   as is_guest
from lines
group by invoice_id
