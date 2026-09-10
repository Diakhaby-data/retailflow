"""
Validation de la table orders (Data Quality).
Separe les lignes valides des invalides, ecrit les deux quelque part,
et affiche un rapport chiffre.
"""
from datetime import date
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
QUARANTINE_DIR = Path("data/quarantine")

ALLOWED_STATUSES = {"pending", "paid", "shipped", "delivered", "cancelled"}


def latest_partition(table: str) -> Path:
    partitions = sorted((RAW_DIR / table).glob("ingestion_date=*"))
    return partitions[-1]  # le plus recent, grace au format AAAA-MM-JJ trie alphabetiquement


def main():
    orders = pd.read_parquet(latest_partition("orders") / "orders.parquet")
    customers = pd.read_parquet(latest_partition("customers") / "customers.parquet")
    known_customer_ids = set(customers["customer_id"])

    # chaque regle = un masque booleen (Vrai/Faux par ligne)
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

    ingestion_date = date.today().isoformat()

    interim_dir = INTERIM_DIR / "orders" / f"ingestion_date={ingestion_date}"
    interim_dir.mkdir(parents=True, exist_ok=True)
    valid_orders.to_parquet(interim_dir / "orders.parquet", index=False)

    quarantine_dir = QUARANTINE_DIR / "orders" / f"ingestion_date={ingestion_date}"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    invalid_orders.to_parquet(quarantine_dir / "orders.parquet", index=False)

    total, valid_count, rejected_count = len(orders), len(valid_orders), len(invalid_orders)

    print("DATA QUALITY REPORT - orders")
    print("-" * 40)
    print(f"Rows processed  : {total:,}")
    print(f"Valid rows      : {valid_count:,}")
    print(f"Rejected rows   : {rejected_count:,}")
    print(f"Quality score   : {100 * valid_count / total:.2f}%")
    print()
    print(f"Duplicates                 : {(~rule_not_duplicate).sum():,}")
    print(f"Null values (customer_id)  : {(~rule_customer_not_null).sum():,}")
    print(f"Referential errors         : {(~rule_customer_known).sum():,}")
    print(f"Invalid status             : {(~rule_status_valid).sum():,}")
    print(f"Invalid dates              : {(~rule_date_valid).sum():,}")
    print(f"Negative amounts           : {(~rule_amount_positive).sum():,}")


if __name__ == "__main__":
    main()