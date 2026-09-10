"""
Mock API REST simulant le catalogue produits de l'application e-commerce
(Source B du cahier des charges). Sert /products et /categories a partir
des donnees generees dans data/external/products.csv.

Objectif : que le futur script d'ingestion fasse un vrai appel HTTP
(requests.get), pas juste un pandas.read_csv(), pour se rapprocher
d'une vraie source API externe.
"""
from pathlib import Path

import pandas as pd
from fastapi import FastAPI

app = FastAPI(title="RetailFlow Mock Products API")

PRODUCTS_PATH = Path("data/external/products.csv")
_products_df = pd.read_csv(PRODUCTS_PATH)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def get_products():
    return _products_df.to_dict(orient="records")


@app.get("/categories")
def get_categories():
    categories = (
        _products_df[["category_id", "category_name"]]
        .drop_duplicates()
        .to_dict(orient="records")
    )
    return categories
