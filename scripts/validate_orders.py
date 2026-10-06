"""
Validation de la table orders (Data Quality).
Separe les lignes valides des invalides, ecrit les deux quelque part,
et affiche un rapport chiffre.
"""
from pathlib import Path

import pandas as pd

from src.quality.storage import read_latest, write_valid_invalid
from src.quality.report import print_quality_report

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
QUARANTINE_DIR = Path("data/quarantine")

ALLOWED_STATUSES = {"pending", "paid", "shipped", "delivered", "cancelled"}


def main():
    orders = read_latest(RAW_DIR, "orders")
    customers = read_latest(INTERIM_DIR, "customers")
    known_customer_ids = set(customers["customer_id"])

    rule_id_present = orders["order_id"].notna()
    rule_not_duplicate = ~orders.duplicated(subset="order_id", keep="first")
    rule_customer_not_null = orders["customer_id"].notna()
    rule_customer_known = orders["customer_id"].isna() | orders["customer_id"].isin(known_customer_ids)
    rule_amount_positive = orders["total_amount"] >= 0
    rule_status_valid = orders["order_status"].isin(ALLOWED_STATUSES)
    rule_date_valid = pd.to_datetime(orders["order_date"], errors="coerce").notna()

    is_valid = (
        rule_id_present
        & rule_not_duplicate
        & rule_customer_not_null
        & rule_customer_known
        & rule_amount_positive
        & rule_status_valid
        & rule_date_valid
    )

    valid_orders = orders[is_valid].copy()
    invalid_orders = orders[~is_valid].copy()

    def reasons(i):
        r = []
        if not rule_id_present[i]: r.append("order_id_null")
        if not rule_not_duplicate[i]: r.append("duplicate")
        if not rule_customer_not_null[i]: r.append("customer_id_null")
        if not rule_customer_known[i]: r.append("customer_unknown")
        if not rule_amount_positive[i]: r.append("negative_amount")
        if not rule_status_valid[i]: r.append("invalid_status")
        if not rule_date_valid[i]: r.append("invalid_date")
        return ",".join(r)

    invalid_orders["rejection_reason"] = [reasons(i) for i in invalid_orders.index]

    write_valid_invalid(valid_orders, invalid_orders, "orders", INTERIM_DIR, QUARANTINE_DIR)

    total, valid_count, rejected_count = len(orders), len(valid_orders), len(invalid_orders)

    print_quality_report("orders", total, valid_count, rejected_count, {
        "Duplicates": (~rule_not_duplicate).sum(),
        "Null values (customer_id)": (~rule_customer_not_null).sum(),
        "Referential errors": (~rule_customer_known).sum(),
        "Invalid status": (~rule_status_valid).sum(),
        "Invalid dates": (~rule_date_valid).sum(),
        "Negative amounts": (~rule_amount_positive).sum(),
    })


if __name__ == "__main__":
    main()