"""
Tests d'integration pour validate_payments.py.

Point d'attention : quand order_id est inconnu, order_total vaut NaN
(le .map() ne trouve pas de correspondance). Toute comparaison avec NaN
renvoie False en pandas, donc rule_amount_reasonable est aussi False
dans ce cas : une commande inconnue declenche DEUX raisons de rejet
("order_unknown" et "amount_exceeds_order"), meme si le montant est
parfaitement normal.
"""
import pandas as pd
import pytest

from scripts import validate_payments
from src.quality.storage import read_latest


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    quarantine_dir = tmp_path / "quarantine"

    monkeypatch.setattr(validate_payments, "RAW_DIR", raw_dir)
    monkeypatch.setattr(validate_payments, "INTERIM_DIR", interim_dir)
    monkeypatch.setattr(validate_payments, "QUARANTINE_DIR", quarantine_dir)

    return raw_dir, interim_dir, quarantine_dir


def test_validate_payments_applies_all_business_rules(isolated_dirs, write_partition):
    raw_dir, interim_dir, quarantine_dir = isolated_dirs

    known_orders = pd.DataFrame({
        "order_id": ["O001", "O002"],
        "total_amount": [100.0, 50.0],
    })
    write_partition(interim_dir, "orders", known_orders)

    payments = pd.DataFrame({
        "case": ["valid", "id_null", "order_unknown", "amount_too_high"],
        "payment_id": ["P001", None, "P003", "P004"],
        "order_id": ["O001", "O001", "O999", "O002"],
        "amount": [100.0, 50.0, 10.0, 999.0],
    })
    write_partition(raw_dir, "payments", payments)

    validate_payments.main()

    valid = read_latest(interim_dir, "payments")
    invalid = read_latest(quarantine_dir, "payments")

    assert valid["case"].tolist() == ["valid"]
    assert len(invalid) == 3

    reasons_by_case = dict(zip(invalid["case"], invalid["rejection_reason"]))
    assert reasons_by_case["id_null"] == "payment_id_null"
    assert reasons_by_case["order_unknown"] == "order_unknown,amount_exceeds_order"
    assert reasons_by_case["amount_too_high"] == "amount_exceeds_order"