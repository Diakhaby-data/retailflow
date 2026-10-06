"""
Tests d'integration pour validate_orders.py : couvre les 7 regles metier
(cle, doublon, client connu, montant positif, statut valide, date valide).
"""
import pandas as pd
import pytest

from scripts import validate_orders
from src.quality.storage import read_latest


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    quarantine_dir = tmp_path / "quarantine"

    monkeypatch.setattr(validate_orders, "RAW_DIR", raw_dir)
    monkeypatch.setattr(validate_orders, "INTERIM_DIR", interim_dir)
    monkeypatch.setattr(validate_orders, "QUARANTINE_DIR", quarantine_dir)

    return raw_dir, interim_dir, quarantine_dir


def test_validate_orders_applies_all_business_rules(isolated_dirs, write_partition):
    raw_dir, interim_dir, quarantine_dir = isolated_dirs

    known_customers = pd.DataFrame({"customer_id": ["C001", "C002"]})
    write_partition(interim_dir, "customers", known_customers)

    orders = pd.DataFrame({
        "order_id": ["O001", "O002", "O002", "O003", "O004", "O005", "O006"],
        "customer_id": ["C001", "C002", "C002", "C999", "C001", "C001", "C001"],
        "total_amount": [100.0, 50.0, 50.0, 20.0, -10.0, 30.0, 40.0],
        "order_status": ["paid", "shipped", "shipped", "paid", "paid", "n_importe_quoi", "paid"],
        "order_date": [
            "2026-01-05", "2026-01-06", "2026-01-06", "2026-01-07",
            "2026-01-08", "2026-01-09", "pas une date",
        ],
    })
    write_partition(raw_dir, "orders", orders)

    validate_orders.main()

    valid = read_latest(interim_dir, "orders")
    invalid = read_latest(quarantine_dir, "orders")

    assert sorted(valid["order_id"].tolist()) == ["O001", "O002"]
    assert len(invalid) == 5

    reasons_by_order = dict(zip(invalid["order_id"], invalid["rejection_reason"]))
    assert reasons_by_order["O002"] == "duplicate"
    assert reasons_by_order["O003"] == "customer_unknown"
    assert reasons_by_order["O004"] == "negative_amount"
    assert reasons_by_order["O005"] == "invalid_status"
    assert reasons_by_order["O006"] == "invalid_date"