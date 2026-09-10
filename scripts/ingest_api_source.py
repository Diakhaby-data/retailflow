"""
Ingestion de la Source B (API produits/categories).
Meme logique que les autres sources, mais on interroge une API HTTP
au lieu de lire un fichier ou une base de donnees.
"""
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path("data/raw")
API_URL = "http://localhost:8000"
ENDPOINTS = {
    "products": "/products",
    "categories": "/categories",
}


def main():
    ingestion_date = date.today().isoformat()

    for table, endpoint in ENDPOINTS.items():
        response = requests.get(f"{API_URL}{endpoint}")
        response.raise_for_status()  # leve une erreur si l'API a repondu un code d'echec
        df = pd.DataFrame(response.json())

        output_dir = RAW_DIR / table / f"ingestion_date={ingestion_date}"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{table}.parquet"
        df.to_parquet(output_path, index=False)

        print(f"{table:12s} -> {len(df):>6,} lignes -> {output_path}")


if __name__ == "__main__":
    main()