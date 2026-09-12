"""
Charge les dimensions (hors dim_date) dans le Data Warehouse.
"""
from pathlib import Path

import pandas as pd

from src.quality.storage import read_latest
from src.warehouse.loading import get_engine, insert_new_rows

INTERIM_DIR = Path("data/interim")


def main():
    engine = get_engine()

    customers = read_latest(INTERIM_DIR, "customers")
    n = insert_new_rows(engine, customers, "dim_customer", "customer_id")
    print(f"dim_customer   : {n} nouvelles lignes")

    products = read_latest(INTERIM_DIR, "products")
    n = insert_new_rows(engine, products, "dim_product", "product_id")
    print(f"dim_product    : {n} nouvelles lignes")

    orders = read_latest(INTERIM_DIR, "orders")
    countries = pd.concat([customers["country"], orders["shipping_country"]]).dropna().unique()
    dim_location = pd.DataFrame({"country": countries})
    n = insert_new_rows(engine, dim_location, "dim_location", "country")
    print(f"dim_location   : {n} nouvelles lignes")

    inventory = read_latest(INTERIM_DIR, "inventory")
    warehouse_ids = inventory["warehouse_id"].dropna().unique()
    dim_warehouse = pd.DataFrame({"warehouse_id": warehouse_ids})
    n = insert_new_rows(engine, dim_warehouse, "dim_warehouse", "warehouse_id")
    print(f"dim_warehouse  : {n} nouvelles lignes")


if __name__ == "__main__":
    main()