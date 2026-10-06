"""
Fixtures partagees par les tests d'integration des scripts de qualite.
Evite de dupliquer la creation de partitions RAW/INTERIM/QUARANTINE
dans chaque fichier de test.
"""
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def write_partition():
    def _write(base_dir: Path, table: str, df: pd.DataFrame, ingestion_date: str = "2026-01-01") -> None:
        partition = base_dir / table / f"ingestion_date={ingestion_date}"
        partition.mkdir(parents=True, exist_ok=True)
        df.to_parquet(partition / f"{table}.parquet", index=False)
    return _write