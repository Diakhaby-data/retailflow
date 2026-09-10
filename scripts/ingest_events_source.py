"""
Ingestion de la Source D (evenements JSON Lines).
"""
from datetime import date
from pathlib import Path

import pandas as pd

SOURCE_PATH = Path("data/external/events.jsonl")
RAW_DIR = Path("data/raw")


def main():
    df = pd.read_json(SOURCE_PATH, lines=True)  # lines=True = comprend le format JSONL

    ingestion_date = date.today().isoformat()
    output_dir = RAW_DIR / "events" / f"ingestion_date={ingestion_date}"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "events.parquet"
    df.to_parquet(output_path, index=False)

    print(f"events        -> {len(df):>6,} lignes -> {output_path}")


if __name__ == "__main__":
    main()