"""
Tests d'integration pour l'API RetailFlow (api/main.py).

Ces tests tournent contre la vraie base Postgres de dev (schema marts,
deja peuple par le pipeline Airflow/dbt), pas contre une base isolee.
Consequence assumee : impossible de figer des valeurs metier precises
dans les assertions (les donnees peuvent changer si le pipeline est
rejoue). On verifie donc la structure des reponses, et on decouvre les
valeurs a tester (un customer_id existant, un segment existant, etc.)
via l'API elle-meme plutot que de les ecrire en dur.

Prerequis pour lancer ces tests : le conteneur retailflow-postgres doit
tourner et les marts dbt doivent etre a jour (dbt run).
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------- /customers ----------

def test_get_customers_returns_a_list_of_valid_shape(client):
    response = client.get("/customers", params={"limit": 5})
    assert response.status_code == 200

    customers = response.json()
    assert isinstance(customers, list)
    assert len(customers) <= 5

    if customers:
        first = customers[0]
        expected_fields = {"customer_id", "orders_count", "total_revenue",
                            "average_order_value", "customer_segment"}
        assert expected_fields.issubset(first.keys())


def test_get_customer_by_id_then_404_for_unknown_id(client):
    existing = client.get("/customers", params={"limit": 1}).json()
    assert existing, "aucun client en base : impossible de tester /customers/{id}"
    customer_id = existing[0]["customer_id"]

    response = client.get(f"/customers/{customer_id}")
    assert response.status_code == 200
    assert response.json()["customer_id"] == customer_id

    response_404 = client.get("/customers/ID_QUI_NE_PEUT_PAS_EXISTER")
    assert response_404.status_code == 404


def test_get_customers_by_segment_returns_only_that_segment(client):
    sample = client.get("/customers", params={"limit": 50}).json()
    assert sample, "aucun client en base : impossible de tester le filtre par segment"
    segment = sample[0]["customer_segment"]

    response = client.get(f"/customers/segment/{segment}")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(c["customer_segment"] == segment for c in results)


# ---------- /sales ----------

def test_get_sales_returns_a_list_of_valid_shape(client):
    response = client.get("/sales", params={"limit": 5})
    assert response.status_code == 200

    sales = response.json()
    assert isinstance(sales, list)
    assert len(sales) <= 5

    if sales:
        first = sales[0]
        expected_fields = {"date", "country", "category", "revenue",
                            "orders", "units_sold", "average_order_value"}
        assert expected_fields.issubset(first.keys())


def test_get_sales_by_country_returns_only_that_country(client):
    sample = client.get("/sales", params={"limit": 50}).json()
    assert sample, "aucune vente en base : impossible de tester le filtre par pays"
    country = sample[0]["country"]

    response = client.get(f"/sales/pays/{country}")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(s["country"] == country for s in results)


def test_get_sales_by_category_returns_only_that_category(client):
    sample = client.get("/sales", params={"limit": 50}).json()
    assert sample, "aucune vente en base : impossible de tester le filtre par categorie"
    category = sample[0]["category"]

    response = client.get(f"/sales/categorie/{category}")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(s["category"] == category for s in results)


# ---------- /inventory ----------

def test_get_inventory_returns_a_list_of_valid_shape(client):
    response = client.get("/inventory", params={"limit": 5})
    assert response.status_code == 200

    inventory = response.json()
    assert isinstance(inventory, list)
    assert len(inventory) <= 5

    if inventory:
        first = inventory[0]
        expected_fields = {"product_id", "current_stock",
                            "average_daily_sales", "stock_status"}
        assert expected_fields.issubset(first.keys())


def test_get_inventory_item_then_404_for_unknown_id(client):
    existing = client.get("/inventory", params={"limit": 1}).json()
    assert existing, "aucun produit en base : impossible de tester /inventory/{id}"
    product_id = existing[0]["product_id"]

    response = client.get(f"/inventory/{product_id}")
    assert response.status_code == 200
    assert response.json()["product_id"] == product_id

    response_404 = client.get("/inventory/PRODUIT_QUI_NE_PEUT_PAS_EXISTER")
    assert response_404.status_code == 404


def test_get_inventory_by_status_uses_known_enum_values(client):
    for status in ("low_stock", "out_of_stock"):
        response = client.get(f"/inventory/statut/{status}")
        assert response.status_code == 200
        results = response.json()
        assert all(item["stock_status"] == status for item in results)


# ---------- /dashboard ----------

def test_get_dashboard_returns_consistent_summary(client):
    response = client.get("/dashboard")
    assert response.status_code == 200

    summary = response.json()
    assert summary["total_revenue"] >= 0
    assert summary["total_orders"] >= 0
    assert len(summary["top_categories"]) <= 5
    assert len(summary["top_customers"]) <= 5
    assert summary["low_stock_count"] >= 0
    assert summary["out_of_stock_count"] >= 0