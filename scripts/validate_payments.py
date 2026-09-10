"""
Validation de la table payments (Data Quality).
"""
from datetime import date
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
QUARANTINE_DIR = Path("data/quarantine")


def latest_partition(base_dir: Path, table: str) -> Path:
    partitions = sorted((base_dir / table).glob("ingestion_date=*"))
    return partitions[-1]


def main():
    payments = pd.read_parquet(latest_partition(RAW_DIR, "payments") / "payments.parquet")
    orders = pd.read_parquet(latest_partition(INTERIM_DIR, "orders") / "orders.parquet")

    # table de correspondance order_id -> total_amount, pour "chercher" le
    # montant de la commande associee a chaque paiement. On part des
    # commandes deja validees (INTERIM), pas des brutes, car order_id doit
    # y etre unique pour que .map() fonctionne.
    order_totals = orders.set_index("order_id")["total_amount"]
    payments["order_total"] = payments["order_id"].map(order_totals)

    rule_payment_id_present = payments["payment_id"].notna()
    rule_order_exists = payments["order_id"].isin(orders["order_id"])
    rule_amount_reasonable = payments["amount"] <= payments["order_total"] + 0.01

    is_valid = rule_payment_id_present & rule_order_exists & rule_amount_reasonable

    valid_payments = payments[is_valid].copy()
    invalid_payments = payments[~is_valid].copy()

    def reasons(i):
        r = []
        if not rule_payment_id_present[i]: r.append("payment_id_null")
        if not rule_order_exists[i]: r.append("order_unknown")
        if not rule_amount_reasonable[i]: r.append("amount_exceeds_order")
        return ",".join(r)

    invalid_payments["rejection_reason"] = [reasons(i) for i in invalid_payments.index]

    ingestion_date = date.today().isoformat()

    interim_dir = INTERIM_DIR / "payments" / f"ingestion_date={ingestion_date}"
    interim_dir.mkdir(parents=True, exist_ok=True)
    valid_payments.drop(columns="order_total").to_parquet(interim_dir / "payments.parquet", index=False)

    quarantine_dir = QUARANTINE_DIR / "payments" / f"ingestion_date={ingestion_date}"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    invalid_payments.to_parquet(quarantine_dir / "payments.parquet", index=False)

    total, valid_count, rejected_count = len(payments), len(valid_payments), len(invalid_payments)

    print("DATA QUALITY REPORT - payments")
    print("-" * 40)
    print(f"Rows processed  : {total:,}")
    print(f"Valid rows      : {valid_count:,}")
    print(f"Rejected rows   : {rejected_count:,}")
    print(f"Quality score   : {100 * valid_count / total:.2f}%")
    print()
    print(f"Unknown order_id       : {(~rule_order_exists).sum():,}")
    print(f"Amount exceeds order   : {(~rule_amount_reasonable).sum():,}")


if __name__ == "__main__":
    main()