
  
    

  create  table "retailflow"."marts"."sales_mart__dbt_tmp"
  
  
    as
  
  (
    with base as (
    select
        oi.order_id,
        oi.quantity,
        oi.unit_price,
        oi.date_key,
        p.category_name,
        o.location_key
    from "retailflow"."staging"."stg_order_items" oi
    left join "retailflow"."staging"."stg_products" p on oi.product_key = p.product_key
    left join "retailflow"."staging"."stg_orders" o on oi.order_id = o.order_id
),

enriched as (
    select
        d.full_date as date,
        l.country,
        b.category_name as category,
        b.order_id,
        b.quantity,
        b.unit_price
    from base b
    left join "retailflow"."staging"."stg_dates" d on b.date_key = d.date_key
    left join "retailflow"."staging"."stg_locations" l on b.location_key = l.location_key
)

select
    date,
    country,
    category,
    sum(quantity * unit_price) as revenue,
    count(distinct order_id) as orders,
    sum(quantity) as units_sold,
    round(sum(quantity * unit_price) / nullif(count(distinct order_id), 0), 2) as average_order_value
from enriched
group by date, country, category
order by date, country, category
  );
  