-- Dimension: a daily date spine spanning the dataset, built with dbt_utils.date_spine.
-- Bounds are the known extent of Online Retail II (2009-12-01 .. 2011-12-31).

with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2009-12-01' as date)",
        end_date="cast('2012-01-01' as date)"
    ) }}

)

select
    cast(date_day as date)                                  as date_key,
    extract(year   from date_day)                          as year,
    extract(quarter from date_day)                         as quarter,
    extract(month  from date_day)                          as month,
    extract(day    from date_day)                          as day_of_month,
    cast(date_trunc('month', date_day) as date)            as month_start,
    strftime(date_day, '%Y-%m')                            as year_month,
    extract(dow from date_day)                             as day_of_week,
    (extract(dow from date_day) in (0, 6))                 as is_weekend
from spine
