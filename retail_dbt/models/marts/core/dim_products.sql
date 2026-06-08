-- Dimension: one row per product (stock code). Description is the most recent seen.

-- Sources descriptive attributes from the intermediate line model (the fact table is kept
-- lean: keys + measures only, no descriptive text).
with lines as (

    select * from {{ ref('int_invoice_lines_cleaned') }}

)

select
    stock_code,
    arg_max(description, invoice_date)                                       as description,
    count(distinct invoice_id)                                              as n_orders,
    sum(case when quantity > 0 then quantity else 0 end)                    as units_sold,
    sum(case when quantity < 0 then -quantity else 0 end)                   as units_returned,
    round(sum(line_revenue), 2)                                             as total_revenue,
    round(
        sum(case when quantity < 0 then -quantity else 0 end)
        / nullif(sum(case when quantity > 0 then quantity else 0 end), 0)
    , 4)                                                                    as return_rate
from lines
group by stock_code
