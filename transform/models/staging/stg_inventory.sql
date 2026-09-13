select
    inventory_key,
    inventory_id,
    product_key,
    warehouse_key,
    date_key,
    stock_quantity
from {{ source('dwh', 'fact_inventory') }}