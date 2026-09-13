
  create view "retailflow"."staging"."stg_customers__dbt_tmp"
    
    
  as (
    select
    customer_key,
    customer_id,
    first_name,
    last_name,
    email,
    country,
    city,
    signup_date,
    customer_segment
from "retailflow"."dwh"."dim_customer"
  );