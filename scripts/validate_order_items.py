"""
Validation de la table order_items (Data Quality).
Meme principe que validate_orders.py.
"""
from pathlib import Path

from src.quality.storage import read_latest, write_valid_invalid
from src.quality.report import print_quality_report

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
QUARANTINE_DIR = Path("data/quarantine")


def main():
    items = read_latest(RAW_DIR, "order_items")
    orders = read_latest(INTERIM_DIR, "orders")
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

    write_valid_invalid(valid_items, invalid_items, "order_items", INTERIM_DIR, QUARANTINE_DIR)

    total, valid_count, rejected_count = len(items), len(valid_items), len(invalid_items)

    print_quality_report("order_items", total, valid_count, rejected_count, {
        "Unknown order_id": (~rule_order_exists).sum(),
        "Invalid quantity": (~rule_quantity_positive).sum(),
        "Negative price": (~rule_price_non_negative).sum(),
    })


if __name__ == "__main__":
    main()