"""
Validation de la table payments (Data Quality).
"""
from pathlib import Path

import pandas as pd

from src.quality.storage import read_latest, write_valid_invalid
from src.quality.report import print_quality_report

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
QUARANTINE_DIR = Path("data/quarantine")


def main():
    payments = read_latest(RAW_DIR, "payments")
    orders = read_latest(INTERIM_DIR, "orders")

    order_totals = orders.set_index("order_id")["total_amount"]
    payments["order_total"] = payments["order_id"].map(order_totals)

    rule_payment_id_present = payments["payment_id"].notna()
    rule_order_exists = payments["order_id"].isin(orders["order_id"])
    rule_amount_reasonable = payments["amount"] <= payments["order_total"] + 0.01

    is_valid = rule_payment_id_present & rule_order_exists & rule_amount_reasonable

    valid_payments = payments[is_valid].drop(columns="order_total").copy()
    invalid_payments = payments[~is_valid].copy()

    def reasons(i):
        r = []
        if not rule_payment_id_present[i]: r.append("payment_id_null")
        if not rule_order_exists[i]: r.append("order_unknown")
        if not rule_amount_reasonable[i]: r.append("amount_exceeds_order")
        return ",".join(r)

    invalid_payments["rejection_reason"] = [reasons(i) for i in invalid_payments.index]

    write_valid_invalid(valid_payments, invalid_payments, "payments", INTERIM_DIR, QUARANTINE_DIR)

    total, valid_count, rejected_count = len(payments), len(valid_payments), len(invalid_payments)
    print_quality_report("payments", total, valid_count, rejected_count, {
        "Unknown order_id": (~rule_order_exists).sum(),
        "Amount exceeds order": (~rule_amount_reasonable).sum(),
    })


if __name__ == "__main__":
    main()