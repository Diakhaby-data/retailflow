"""
Ingestion de la Source A (PostgreSQL : orders, order_items, payments).
Meme logique que la Source C, mais on lit une base de donnees au lieu
d'un fichier CSV.
"""
import os
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

RAW_DIR = Path("data/raw")
TABLES = ["orders", "order_items", "payments"]


def main():
    load_dotenv()  # lit .env et rend ses variables accessibles via os.getenv

    # chaine de connexion : le format standard attendu par SQLAlchemy pour
    # savoir QUI se connecte, AVEC QUEL mot de passe, A QUELLE adresse,
    # QUEL port, et QUELLE base.
    db_url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    engine = create_engine(db_url)  # cree un "connecteur" reutilisable

    ingestion_date = date.today().isoformat()

    for table in TABLES:
        df = pd.read_sql(f"SELECT * FROM {table}", engine)

        output_dir = RAW_DIR / table / f"ingestion_date={ingestion_date}"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{table}.parquet"
        df.to_parquet(output_path, index=False)

        print(f"{table:12s} -> {len(df):>6,} lignes -> {output_path}")


if __name__ == "__main__":
    main()