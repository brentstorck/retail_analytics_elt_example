{{
    config(
        materialized='incremental',
        unique_key='invoice_line_id',
        incremental_strategy='delete+insert'
    )
}}

-- Fact: one row per revenue-bearing invoice line. The lowest-grain fact in the star schema.
--
-- Materialized incrementally to demonstrate the pattern: a normal run only processes lines
-- newer than what is already loaded (a no-op on this static dataset, but exactly how you
-- would handle a continuously growing source in production without rebuilding everything).
-- Use `dbt build --full-refresh` to rebuild from scratch.

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
{% if is_incremental() %}
where invoice_date > (select coalesce(max(invoice_date), date '1900-01-01') from {{ this }})
{% endif %}
