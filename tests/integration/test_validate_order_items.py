"""
Tests d'integration pour validate_order_items.py.
Contrairement a validate_orders.py, il n'y a pas de regle de doublon ici :
seulement presence de la cle, commande connue, quantite et prix.
"""
import pandas as pd
import pytest

from scripts import validate_order_items
from src.quality.storage import read_latest


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    quarantine_dir = tmp_path / "quarantine"

    monkeypatch.setattr(validate_order_items, "RAW_DIR", raw_dir)
    monkeypatch.setattr(validate_order_items, "INTERIM_DIR", interim_dir)
    monkeypatch.setattr(validate_order_items, "QUARANTINE_DIR", quarantine_dir)

    return raw_dir, interim_dir, quarantine_dir


def test_validate_order_items_applies_all_business_rules(isolated_dirs, write_partition):
    raw_dir, interim_dir, quarantine_dir = isolated_dirs

    known_orders = pd.DataFrame({"order_id": ["O001"]})
    write_partition(interim_dir, "orders", known_orders)

    order_items = pd.DataFrame({
        # colonne "case" ajoutee uniquement pour identifier les lignes dans
        # les assertions : order_item_id est None pour l'une d'entre elles,
        # on ne peut donc pas s'en servir comme cle.
        "case": ["valid", "id_null", "order_unknown", "bad_qty", "bad_price"],
        "order_item_id": ["OI001", None, "OI003", "OI004", "OI005"],
        "order_id": ["O001", "O001", "O999", "O001", "O001"],
        "quantity": [2, 1, 1, 0, 1],
        "unit_price": [10.0, 5.0, 5.0, 5.0, -2.0],
    })
    write_partition(raw_dir, "order_items", order_items)

    validate_order_items.main()

    valid = read_latest(interim_dir, "order_items")
    invalid = read_latest(quarantine_dir, "order_items")

    assert valid["case"].tolist() == ["valid"]
    assert len(invalid) == 4

    reasons_by_case = dict(zip(invalid["case"], invalid["rejection_reason"]))
    assert reasons_by_case["id_null"] == "order_item_id_null"
    assert reasons_by_case["order_unknown"] == "order_unknown"
    assert reasons_by_case["bad_qty"] == "invalid_quantity"
    assert reasons_by_case["bad_price"] == "negative_price"