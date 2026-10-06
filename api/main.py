"""
API FastAPI RetailFlow : expose en lecture seule les KPI calcules par dbt
(customer_mart, sales_mart, inventory_mart). Aucune ecriture, aucun modele
ML : contrairement a ShowroomPrive, RetailFlow n'a pas de prediction a servir.
"""
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.warehouse.loading import get_engine

app = FastAPI(
    title="RetailFlow API",
    description="API de consultation des KPI e-commerce : clients, ventes, stock.",
    version="1.0.0",
)

# Instrumente l'app : ajoute un middleware qui mesure chaque requete (methode,
# route, code de statut, duree), et expose ces mesures sur GET /metrics au
# format texte attendu par Prometheus. Rien a faire cote Postgres ou dbt :
# ces metriques concernent uniquement le trafic HTTP de l'API elle-meme.
Instrumentator().instrument(app).expose(app)

_engine: Optional[Engine] = None


def get_db() -> Engine:
    # Cree le moteur une seule fois (premier appel), le reutilise ensuite.
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


class CustomerKPI(BaseModel):
    customer_id: str
    orders_count: int
    total_revenue: float
    average_order_value: float
    last_order_date: Optional[date] = None
    customer_segment: str


class SaleKPI(BaseModel):
    date: date
    country: str
    category: str
    revenue: float
    orders: int
    units_sold: int
    average_order_value: float


class InventoryKPI(BaseModel):
    product_id: str
    current_stock: int
    average_daily_sales: float
    days_of_stock: Optional[float] = None
    stock_status: str


class TopCategory(BaseModel):
    category: str
    revenue: float


class TopCustomer(BaseModel):
    customer_id: str
    total_revenue: float


class DashboardSummary(BaseModel):
    total_revenue: float
    total_orders: int
    top_categories: list[TopCategory]
    low_stock_count: int
    out_of_stock_count: int
    top_customers: list[TopCustomer]


@app.get("/customers", response_model=list[CustomerKPI], tags=["customers"])
def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    engine: Engine = Depends(get_db),
):
    query = text(
        "SELECT * FROM marts.customer_mart ORDER BY customer_id OFFSET :skip LIMIT :limit"
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"skip": skip, "limit": limit}).mappings().all()
    return rows


@app.get("/customers/{customer_id}", response_model=CustomerKPI, tags=["customers"])
def get_customer(customer_id: str, engine: Engine = Depends(get_db)):
    query = text("SELECT * FROM marts.customer_mart WHERE customer_id = :customer_id")
    with engine.connect() as conn:
        row = conn.execute(query, {"customer_id": customer_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Client {customer_id} introuvable")
    return row


@app.get("/customers/segment/{segment}", response_model=list[CustomerKPI], tags=["customers"])
def get_customers_by_segment(segment: str, engine: Engine = Depends(get_db)):
    query = text("SELECT * FROM marts.customer_mart WHERE customer_segment = :segment")
    with engine.connect() as conn:
        rows = conn.execute(query, {"segment": segment}).mappings().all()
    return rows


@app.get("/sales", response_model=list[SaleKPI], tags=["sales"])
def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    engine: Engine = Depends(get_db),
):
    query = text("SELECT * FROM marts.sales_mart ORDER BY date OFFSET :skip LIMIT :limit")
    with engine.connect() as conn:
        rows = conn.execute(query, {"skip": skip, "limit": limit}).mappings().all()
    return rows


@app.get("/sales/pays/{country}", response_model=list[SaleKPI], tags=["sales"])
def get_sales_by_country(country: str, engine: Engine = Depends(get_db)):
    query = text("SELECT * FROM marts.sales_mart WHERE country = :country ORDER BY date")
    with engine.connect() as conn:
        rows = conn.execute(query, {"country": country}).mappings().all()
    return rows


@app.get("/sales/categorie/{category}", response_model=list[SaleKPI], tags=["sales"])
def get_sales_by_category(category: str, engine: Engine = Depends(get_db)):
    query = text("SELECT * FROM marts.sales_mart WHERE category = :category ORDER BY date")
    with engine.connect() as conn:
        rows = conn.execute(query, {"category": category}).mappings().all()
    return rows


@app.get("/inventory", response_model=list[InventoryKPI], tags=["inventory"])
def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    engine: Engine = Depends(get_db),
):
    query = text(
        "SELECT * FROM marts.inventory_mart ORDER BY product_id OFFSET :skip LIMIT :limit"
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"skip": skip, "limit": limit}).mappings().all()
    return rows


@app.get("/inventory/{product_id}", response_model=InventoryKPI, tags=["inventory"])
def get_inventory_item(product_id: str, engine: Engine = Depends(get_db)):
    query = text("SELECT * FROM marts.inventory_mart WHERE product_id = :product_id")
    with engine.connect() as conn:
        row = conn.execute(query, {"product_id": product_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Produit {product_id} introuvable")
    return row


@app.get("/inventory/statut/{stock_status}", response_model=list[InventoryKPI], tags=["inventory"])
def get_inventory_by_status(stock_status: str, engine: Engine = Depends(get_db)):
    query = text("SELECT * FROM marts.inventory_mart WHERE stock_status = :stock_status")
    with engine.connect() as conn:
        rows = conn.execute(query, {"stock_status": stock_status}).mappings().all()
    return rows


@app.get("/dashboard", response_model=DashboardSummary, tags=["dashboard"])
def get_dashboard(engine: Engine = Depends(get_db)):
    with engine.connect() as conn:
        totals = conn.execute(
            text(
                "SELECT COALESCE(SUM(revenue), 0) AS total_revenue, "
                "COALESCE(SUM(orders), 0) AS total_orders FROM marts.sales_mart"
            )
        ).mappings().first()

        top_categories = conn.execute(
            text(
                "SELECT category, SUM(revenue) AS revenue FROM marts.sales_mart "
                "GROUP BY category ORDER BY revenue DESC LIMIT 5"
            )
        ).mappings().all()

        stock_counts = conn.execute(
            text(
                "SELECT stock_status, COUNT(*) AS n FROM marts.inventory_mart "
                "WHERE stock_status IN ('low_stock', 'out_of_stock') GROUP BY stock_status"
            )
        ).mappings().all()

        top_customers = conn.execute(
            text(
                "SELECT customer_id, total_revenue FROM marts.customer_mart "
                "ORDER BY total_revenue DESC LIMIT 5"
            )
        ).mappings().all()

    stock_map = {row["stock_status"]: row["n"] for row in stock_counts}

    return {
        "total_revenue": totals["total_revenue"],
        "total_orders": totals["total_orders"],
        "top_categories": list(top_categories),
        "low_stock_count": stock_map.get("low_stock", 0),
        "out_of_stock_count": stock_map.get("out_of_stock", 0),
        "top_customers": list(top_customers),
    }