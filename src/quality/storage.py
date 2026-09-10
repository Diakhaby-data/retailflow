"""
Fonctions communes de lecture/ecriture du data lake.
Partagees par tous les scripts de validation Data Quality.
"""
from datetime import date
from pathlib import Path

import pandas as pd


def latest_partition(base_dir: Path, table: str) -> Path:
    partitions = sorted((base_dir / table).glob("ingestion_date=*"))
    return partitions[-1]


def read_latest(base_dir: Path, table: str) -> pd.DataFrame:
    partition = latest_partition(base_dir, table)
    return pd.read_parquet(partition / f"{table}.parquet")


def write_valid_invalid(
    valid_df: pd.DataFrame,
    invalid_df: pd.DataFrame,
    table: str,
    interim_dir: Path,
    quarantine_dir: Path,
) -> None:
    ingestion_date = date.today().isoformat()

    interim_partition = interim_dir / table / f"ingestion_date={ingestion_date}"
    interim_partition.mkdir(parents=True, exist_ok=True)
    valid_df.to_parquet(interim_partition / f"{table}.parquet", index=False)

    quarantine_partition = quarantine_dir / table / f"ingestion_date={ingestion_date}"
    quarantine_partition.mkdir(parents=True, exist_ok=True)
    invalid_df.to_parquet(quarantine_partition / f"{table}.parquet", index=False)