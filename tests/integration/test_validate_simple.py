"""
Tests d'integration pour validate_simple.py, isoles du vrai dossier data/
du projet via des repertoires temporaires (tmp_path) et monkeypatch.
"""
import pandas as pd
import pytest

from scripts import validate_simple
from src.quality.storage import read_latest


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    quarantine_dir = tmp_path / "quarantine"

    monkeypatch.setattr(validate_simple, "RAW_DIR", raw_dir)
    monkeypatch.setattr(validate_simple, "INTERIM_DIR", interim_dir)
    monkeypatch.setattr(validate_simple, "QUARANTINE_DIR", quarantine_dir)

    return raw_dir, interim_dir, quarantine_dir


def test_validate_table_separates_valid_and_invalid_rows(isolated_dirs, write_partition):
    raw_dir, interim_dir, quarantine_dir = isolated_dirs

    customers = pd.DataFrame({
        "customer_id": ["C001", "C002", "C002", None],
        "country": ["France", "Belgique", "Belgique", "Suisse"],
    })
    write_partition(raw_dir, "customers", customers)

    validate_simple.validate_table("customers", "customer_id")

    valid = read_latest(interim_dir, "customers")
    invalid = read_latest(quarantine_dir, "customers")

    assert sorted(valid["customer_id"].tolist()) == ["C001", "C002"]
    assert len(invalid) == 2
    assert set(invalid["rejection_reason"]) == {"duplicate", "customer_id_null"}


def test_validate_table_all_valid_rows_pass(isolated_dirs, write_partition):
    raw_dir, interim_dir, quarantine_dir = isolated_dirs

    products = pd.DataFrame({
        "product_id": ["P001", "P002", "P003"],
        "name": ["Casque", "Enceinte", "Cable"],
    })
    write_partition(raw_dir, "products", products)

    validate_simple.validate_table("products", "product_id")

    valid = read_latest(interim_dir, "products")
    invalid = read_latest(quarantine_dir, "products")

    assert len(valid) == 3
    assert len(invalid) == 0