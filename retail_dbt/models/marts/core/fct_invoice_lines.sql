-- Fact: one row per revenue-bearing invoice line. The lowest-grain fact in the star schema.

select
    invoice_line_id,
    invoice_id,
    customer_id,
    stock_code,
    invoice_date,
    invoice_month,
    quantity,
    unit_price,
    line_revenue,
    is_cancellation,
    is_return,
    is_guest
from {{ ref('int_invoice_lines_cleaned') }}
