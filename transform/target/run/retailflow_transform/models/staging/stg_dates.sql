
  create view "retailflow"."staging"."stg_dates__dbt_tmp"
    
    
  as (
    select
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    day,
    day_of_week,
    day_name,
    is_weekend
from "retailflow"."dwh"."dim_date"
  );