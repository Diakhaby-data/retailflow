"""
Validation "simple" des tables sans defauts injectes.
Verifie juste que la cle primaire est presente et unique.
"""
from pathlib import Path

from src.quality.storage import read_latest, write_valid_invalid
from src.quality.report import print_quality_report

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
QUARANTINE_DIR = Path("data/quarantine")

TABLES = {
    "customers": "customer_id",
    "products": "product_id",
    "categories": "category_id",
    "returns": "return_id",
    "inventory": "inventory_id",
}


def validate_table(table: str, pk_column: str) -> None:
    df = read_latest(RAW_DIR, table)

    rule_pk_present = df[pk_column].notna()
    rule_pk_unique = ~df.duplicated(subset=pk_column, keep="first")

    is_valid = rule_pk_present & rule_pk_unique

    valid_df = df[is_valid].copy()
    invalid_df = df[~is_valid].copy()

    def reasons(i):
        r = []
        if not rule_pk_present[i]: r.append(f"{pk_column}_null")
        if not rule_pk_unique[i]: r.append("duplicate")
        return ",".join(r)

    invalid_df["rejection_reason"] = [reasons(i) for i in invalid_df.index]

    write_valid_invalid(valid_df, invalid_df, table, INTERIM_DIR, QUARANTINE_DIR)

    total, valid_count, rejected_count = len(df), len(valid_df), len(invalid_df)
    print_quality_report(table, total, valid_count, rejected_count, {
        "Null PK": (~rule_pk_present).sum(),
        "Duplicate PK": (~rule_pk_unique).sum(),
    })
    print()


def main():
    for table, pk_column in TABLES.items():
        validate_table(table, pk_column)


if __name__ == "__main__":
    main()