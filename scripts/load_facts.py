"""
Charge les tables de faits dans le Data Warehouse.
Reconstruit les cles etrangeres (customer_key, product_key, date_key...)
a partir des cles naturelles, via les dimensions deja chargees.
"""
from pathlib import Path

import pandas as pd

from src.quality.storage import read_latest
from src.warehouse.loading import get_engine, insert_new_rows, get_key_map, to_date_key

INTERIM_DIR = Path("data/interim")


def main():
    engine = get_engine()

    customer_key_map = get_key_map(engine, "dim_customer", "customer_id", "customer_key")
    product_key_map = get_key_map(engine, "dim_product", "product_id", "product_key")
    location_key_map = get_key_map(engine, "dim_location", "country", "location_key")
    warehouse_key_map = get_key_map(engine, "dim_warehouse", "warehouse_id", "warehouse_key")

    orders = read_latest(INTERIM_DIR, "orders")

    fact_orders = pd.DataFrame({
        "order_id": orders["order_id"],
        "customer_key": orders["customer_id"].map(customer_key_map),
        "date_key": to_date_key(orders["order_date"]),
        "location_key": orders["shipping_country"].map(location_key_map),
        "order_status": orders["order_status"],
        "payment_method": orders["payment_method"],
        "total_amount": orders["total_amount"],
    })
    n = insert_new_rows(engine, fact_orders, "fact_orders", "order_id")
    print(f"fact_orders      : {n} nouvelles lignes")

    order_customer_map = orders.set_index("order_id")["customer_id"]
    order_date_map = orders.set_index("order_id")["order_date"]

    items = read_latest(INTERIM_DIR, "order_items")
    fact_order_items = pd.DataFrame({
        "order_item_id": items["order_item_id"],
        "order_id": items["order_id"],
        "product_key": items["product_id"].map(product_key_map),
        "customer_key": items["order_id"].map(order_customer_map).map(customer_key_map),
        "date_key": to_date_key(items["order_id"].map(order_date_map)),
        "quantity": items["quantity"],
        "unit_price": items["unit_price"],
        "discount": items["discount"],
    })
    n = insert_new_rows(engine, fact_order_items, "fact_order_items", "order_item_id")
    print(f"fact_order_items : {n} nouvelles lignes")

    payments = read_latest(INTERIM_DIR, "payments")
    fact_payments = pd.DataFrame({
        "payment_id": payments["payment_id"],
        "order_id": payments["order_id"],
        "date_key": to_date_key(payments["payment_date"]),
        "amount": payments["amount"],
        "payment_method": payments["payment_method"],
        "payment_status": payments["payment_status"],
        "transaction_id": payments["transaction_id"],
    })
    n = insert_new_rows(engine, fact_payments, "fact_payments", "payment_id")
    print(f"fact_payments    : {n} nouvelles lignes")

    returns = read_latest(INTERIM_DIR, "returns")
    fact_returns = pd.DataFrame({
        "return_id": returns["return_id"],
        "order_id": returns["order_id"],
        "product_key": returns["product_id"].map(product_key_map),
        "date_key": to_date_key(returns["return_date"]),
        "quantity": returns["quantity"],
        "reason": returns["reason"],
    })
    n = insert_new_rows(engine, fact_returns, "fact_returns", "return_id")
    print(f"fact_returns     : {n} nouvelles lignes")

    inventory = read_latest(INTERIM_DIR, "inventory")
    fact_inventory = pd.DataFrame({
        "inventory_id": inventory["inventory_id"],
        "product_key": inventory["product_id"].map(product_key_map),
        "warehouse_key": inventory["warehouse_id"].map(warehouse_key_map),
        "date_key": to_date_key(inventory["snapshot_date"]),
        "stock_quantity": inventory["stock_quantity"],
    })
    n = insert_new_rows(engine, fact_inventory, "fact_inventory", "inventory_id")
    print(f"fact_inventory   : {n} nouvelles lignes")


if __name__ == "__main__":
    main()