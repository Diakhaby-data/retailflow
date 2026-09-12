"""
Construit et charge la dimension dim_date.
Couvre toutes les dates rencontrees dans les tables validees.
"""
from pathlib import Path

import pandas as pd

from src.quality.storage import read_latest
from src.warehouse.loading import get_engine, insert_new_rows

INTERIM_DIR = Path("data/interim")

DATE_SOURCES = [
    ("orders", "order_date"),
    ("payments", "payment_date"),
    ("returns", "return_date"),
    ("inventory", "snapshot_date"),
    ("customers", "signup_date"),
]


def get_date_range() -> tuple:
    all_dates = []
    for table, column in DATE_SOURCES:
        df = read_latest(INTERIM_DIR, table)
        all_dates.append(pd.to_datetime(df[column], errors="coerce"))
    combined = pd.concat(all_dates).dropna()
    return combined.min(), combined.max()


def build_dim_date(start, end) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="D")
    return pd.DataFrame({
        "date_key": dates.strftime("%Y%m%d").astype(int),
        "full_date": dates.date,
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": dates.strftime("%B"),
        "day": dates.day,
        "day_of_week": dates.dayofweek,
        "day_name": dates.strftime("%A"),
        "is_weekend": dates.dayofweek >= 5,
    })


def main():
    engine = get_engine()

    start, end = get_date_range()
    dim_date = build_dim_date(start, end)
    n = insert_new_rows(engine, dim_date, "dim_date", "date_key")

    print(f"Plage couverte : {start.date()} -> {end.date()}")
    print(f"Nouvelles lignes inserees : {n}")
    print(f"Deja presentes (ignorees) : {len(dim_date) - n}")


if __name__ == "__main__":
    main()