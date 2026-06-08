-- Staging: 1:1 with the raw source. Rename to snake_case, cast types, trim strings, and
-- derive row-level business flags. No filtering or aggregation happens here — that keeps
-- staging an honest, debuggable mirror of the source. A surrogate key is added so every
-- downstream line item has a stable, testable primary key.

with source as (

    select * from {{ source('raw', 'online_retail') }}

),

cleaned as (

    select
        -- identifiers
        trim(invoice)                                        as invoice_id,
        upper(trim(stock_code))                              as stock_code,
        nullif(trim(description), '')                        as description,
        customer_id,
        nullif(trim(country), '')                            as country,

        -- measures
        cast(quantity as integer)                            as quantity,
        cast(price as double)                                as unit_price,
        round(cast(quantity as integer) * cast(price as double), 2) as line_revenue,

        -- time
        cast(invoice_date as timestamp)                      as invoiced_at,
        cast(invoice_date as date)                           as invoice_date,

        -- row-level flags (meaning assigned here, filtering deferred to intermediate)
        (trim(invoice) like 'C%')                            as is_cancellation,
        (cast(quantity as integer) < 0)                      as is_return,
        (customer_id is null)                                as is_guest,
        (cast(price as double) <= 0)                         as is_non_revenue,

        -- lineage
        _source_sheet,
        _loaded_at

    from source
    where invoice is not null
      and stock_code is not null

)

select
    {{ dbt_utils.generate_surrogate_key([
        'invoice_id', 'stock_code', 'invoiced_at', 'quantity', 'unit_price', 'customer_id'
    ]) }}                                                    as invoice_line_id,
    *
from cleaned
