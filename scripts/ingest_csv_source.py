"""
Ingestion de la Source C (CSV plats : customers, returns, inventory).
Lit les fichiers dans data/external/, les ecrit en Parquet dans data/raw/,
partitionnes par date d'ingestion (pas par date metier).
"""
from datetime import date
from pathlib import Path

import pandas as pd

from src.monitoring.metrics import push_ingestion_metric

SOURCE_DIR = Path("data/external")
RAW_DIR = Path("data/raw")
TABLES = ["customers", "returns", "inventory"]


def main():
    ingestion_date = date.today().isoformat()  # ex: "2026-09-10"

    for table in TABLES:
        df = pd.read_csv(SOURCE_DIR / f"{table}.csv")

        output_dir = RAW_DIR / table / f"ingestion_date={ingestion_date}"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{table}.parquet"
        df.to_parquet(output_path, index=False)  # ecriture au format colonnes

        print(f"{table:12s} -> {len(df):>6,} lignes -> {output_path}")
        push_ingestion_metric(table, len(df))


if __name__ == "__main__":
    main()
