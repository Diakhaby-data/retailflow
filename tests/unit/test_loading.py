"""
Tests unitaires pour les fonctions pures de src/warehouse/loading.py.
to_date_key est une simple transformation de dates, testable sans I/O.
"""
import pandas as pd

from src.warehouse.loading import to_date_key


def test_to_date_key_converts_valid_dates():
    dates = pd.Series(["2026-01-15", "2026-12-31"])
    result = to_date_key(dates)
    assert result.tolist() == [20260115, 20261231]


def test_to_date_key_handles_invalid_date_as_na():
    dates = pd.Series(["2026-01-15", "pas une date"])
    result = to_date_key(dates)
    assert result.iloc[0] == 20260115
    assert pd.isna(result.iloc[1])


def test_to_date_key_returns_nullable_integer_dtype():
    dates = pd.Series(["2026-01-15", None])
    result = to_date_key(dates)
    assert str(result.dtype) == "Int64"