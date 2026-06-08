-- Customer segments: count, revenue, and average value by RFM segment.
-- Chart: bar of n_customers (or total_monetary) by rfm_segment.
select
    rfm_segment,
    count(*)                              as n_customers,
    round(sum(monetary))                  as total_monetary,
    round(avg(monetary), 2)              as avg_monetary,
    round(avg(frequency), 2)             as avg_frequency,
    round(avg(recency_days), 1)          as avg_recency_days
from marts.mart_rfm_segments
group by rfm_segment
order by total_monetary desc;
