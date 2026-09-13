with latest_snapshot as (
    select
        product_key,
        max(date_key) as latest_date_key
    from {{ ref('stg_inventory') }}
    group by product_key
),

current_stock as (
    select
        i.product_key,
        sum(i.stock_quantity) as current_stock
    from {{ ref('stg_inventory') }} i
    inner join latest_snapshot ls
        on i.product_key = ls.product_key
        and i.date_key = ls.latest_date_key
    group by i.product_key
),

sales_period as (
    select count(distinct date_key) as total_days
    from {{ ref('stg_order_items') }}
),

sales_by_product as (
    select
        product_key,
        sum(quantity) as total_quantity_sold
    from {{ ref('stg_order_items') }}
    group by product_key
)

select
    p.product_id,
    coalesce(cs.current_stock, 0) as current_stock,
    round(coalesce(s.total_quantity_sold, 0)::numeric / sp.total_days, 2) as average_daily_sales,
    case
        when coalesce(s.total_quantity_sold, 0) > 0
            then round(coalesce(cs.current_stock, 0) / (s.total_quantity_sold::numeric / sp.total_days), 1)
        else null
    end as days_of_stock,
    case
        when coalesce(cs.current_stock, 0) <= 0 then 'out_of_stock'
        when cs.current_stock <= p.stock_threshold then 'low_stock'
        else 'ok'
    end as stock_status
from {{ ref('stg_products') }} p
cross join sales_period sp
left join current_stock cs on p.product_key = cs.product_key
left join sales_by_product s on p.product_key = s.product_key