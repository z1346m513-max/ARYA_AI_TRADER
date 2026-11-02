"""Offline parser and exact instrument-resolution tests."""
import json

import pytest

from arya.providers.shareholders.client_type_all_provider import (
    ClientTypeAllProvider,
    ClientTypeAllProviderError,
)

SAMPLE = (
    "46348559193224090,100,10,1000000,500000,80,20,400000,600000;"
    "123,1,1,10,10,1,1,10,10;"
)


def test_parse_client_type_all_basic():
    rows = ClientTypeAllProvider.parse_client_type_all(SAMPLE)
    assert "46348559193224090" in rows
    row = rows["46348559193224090"]
    assert row["n_buy_count"] == 100
    assert row["l_buy_volume"] == 500000
    assert row["n_sell_volume"] == 400000


def test_parse_empty():
    assert ClientTypeAllProvider.parse_client_type_all("") == {}
    assert ClientTypeAllProvider.parse_client_type_all(";;;") == {}


def test_parser_rejects_missing_numeric_fields_and_negative_or_nonfinite_values():
    payload = (
        "1,1,,2,3,4,5,6,7;"
        "2,1,1,-2,3,4,5,6,7;"
        "3,1,1,nan,3,4,5,6,7;"
        "4,1,1,2,3,4,5,6,7;"
    )
    rows = ClientTypeAllProvider.parse_client_type_all(payload)
    assert list(rows) == ["4"]


def test_parser_rejects_duplicate_instrument_codes():
    rows = ClientTypeAllProvider.parse_client_type_all("1,1,1,1,1,1,1,1,1;1,2,2,2,2,2,2,2,2;")
    assert rows["1"]["n_buy_count"] == 1


def test_resolve_ins_code_requires_exact_match(monkeypatch):
    provider = ClientTypeAllProvider()
    payload = {"instrumentSearch": [
        {"lVal18AFC": "OTHER", "insCode": "10"},
        {"lVal18AFC": "TARGET", "insCode": "20"},
    ]}
    monkeypatch.setattr(provider, "_fetch_bytes", lambda _url: json.dumps(payload).encode())
    assert provider._resolve_ins_code("TARGET") == "20"


def test_resolve_ins_code_rejects_no_exact_match(monkeypatch):
    provider = ClientTypeAllProvider()
    payload = {"instrumentSearch": [{"lVal18AFC": "OTHER", "insCode": "10"}]}
    monkeypatch.setattr(provider, "_fetch_bytes", lambda _url: json.dumps(payload).encode())
    with pytest.raises(ClientTypeAllProviderError, match="exact ticker match not found"):
        provider._resolve_ins_code("TARGET")


def test_resolve_ins_code_rejects_ambiguous_exact_matches(monkeypatch):
    provider = ClientTypeAllProvider()
    payload = {"instrumentSearch": {"items": [
        {"lVal18AFC": "TARGET", "insCode": "10"},
        {"lVal18": "TARGET", "insCode": "20"},
    ]}}
    monkeypatch.setattr(provider, "_fetch_bytes", lambda _url: json.dumps(payload).encode())
    with pytest.raises(ClientTypeAllProviderError, match="ambiguous exact ticker match"):
        provider._resolve_ins_code("TARGET")
