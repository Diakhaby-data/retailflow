
  create view "retailflow"."staging"."stg_locations__dbt_tmp"
    
    
  as (
    select
    location_key,
    country
from "retailflow"."dwh"."dim_location"
  );