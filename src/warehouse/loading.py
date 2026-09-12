"""
Fonctions communes de connexion et de chargement du Data Warehouse.
Insertion idempotente basee sur la cle naturelle de chaque table.
"""
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


def get_engine():
    load_dotenv()
    db_url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(db_url)


def insert_new_rows(engine, df: pd.DataFrame, table: str, natural_key: str) -> int:
    existing = pd.read_sql(f"SELECT {natural_key} FROM dwh.{table}", engine)[natural_key]
    new_rows = df[~df[natural_key].isin(existing)]

    if not new_rows.empty:
        new_rows.to_sql(table, engine, schema="dwh", if_exists="append", index=False)

    return len(new_rows)


def get_key_map(engine, table: str, natural_key: str, surrogate_key: str) -> pd.Series:
    df = pd.read_sql(f"SELECT {natural_key}, {surrogate_key} FROM dwh.{table}", engine)
    return df.set_index(natural_key)[surrogate_key]


def to_date_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y%m%d").astype("Int64")