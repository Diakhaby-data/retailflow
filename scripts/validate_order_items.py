"""
Validation de la table order_items (Data Quality).
Meme principe que validate_orders.py.
"""
from datetime import date
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
QUARANTINE_DIR = Path("data/quarantine")


def latest_partition(table: str) -> Path:
    partitions = sorted((RAW_DIR / table).glob("ingestion_date=*"))
    return partitions[-1]


def main():
    items = pd.read_parquet(latest_partition("order_items") / "order_items.parquet")
    orders = pd.read_parquet(latest_partition("orders") / "orders.parquet")
    known_order_ids = set(orders["order_id"])

    rule_item_id_present = items["order_item_id"].notna()
    rule_order_exists = items["order_id"].isin(known_order_ids)
    rule_quantity_positive = items["quantity"] > 0
    rule_price_non_negative = items["unit_price"] >= 0

    is_valid = (
        rule_item_id_present
        & rule_order_exists
        & rule_quantity_positive
        & rule_price_non_negative
    )

    valid_items = items[is_valid].copy()
    invalid_items = items[~is_valid].copy()

    def reasons(i):
        r = []
        if not rule_item_id_present[i]: r.append("order_item_id_null")
        if not rule_order_exists[i]: r.append("order_unknown")
        if not rule_quantity_positive[i]: r.append("invalid_quantity")
        if not rule_price_non_negative[i]: r.append("negative_price")
        return ",".join(r)

    invalid_items["rejection_reason"] = [reasons(i) for i in invalid_items.index]

    ingestion_date = date.today().isoformat()

    interim_dir = INTERIM_DIR / "order_items" / f"ingestion_date={ingestion_date}"
    interim_dir.mkdir(parents=True, exist_ok=True)
    valid_items.to_parquet(interim_dir / "order_items.parquet", index=False)

    quarantine_dir = QUARANTINE_DIR / "order_items" / f"ingestion_date={ingestion_date}"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    invalid_items.to_parquet(quarantine_dir / "order_items.parquet", index=False)

    total, valid_count, rejected_count = len(items), len(valid_items), len(invalid_items)

    print("DATA QUALITY REPORT - order_items")
    print("-" * 40)
    print(f"Rows processed  : {total:,}")
    print(f"Valid rows      : {valid_count:,}")
    print(f"Rejected rows   : {rejected_count:,}")
    print(f"Quality score   : {100 * valid_count / total:.2f}%")
    print()
    print(f"Unknown order_id   : {(~rule_order_exists).sum():,}")
    print(f"Invalid quantity   : {(~rule_quantity_positive).sum():,}")
    print(f"Negative price     : {(~rule_price_non_negative).sum():,}")


if __name__ == "__main__":
    main()