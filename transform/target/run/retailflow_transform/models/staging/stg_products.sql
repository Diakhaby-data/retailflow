
  create view "retailflow"."staging"."stg_products__dbt_tmp"
    
    
  as (
    select
    product_key,
    product_id,
    product_name,
    category_id,
    category_name,
    brand,
    unit_cost,
    unit_price,
    stock_threshold
from "retailflow"."dwh"."dim_product"
  );