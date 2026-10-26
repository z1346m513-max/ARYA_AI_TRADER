"""Offline parser tests for ClientTypeAll."""
from arya.providers.shareholders.client_type_all_provider import ClientTypeAllProvider

SAMPLE = (
    "46348559193224090,100,10,1000000,500000,80,20,400000,600000;"
    "123,1,1,10,10,1,1,10,10;"
)


def test_parse_client_type_all_basic():
    rows = ClientTypeAllProvider.parse_client_type_all(SAMPLE)
    assert "46348559193224090" in rows
    r = rows["46348559193224090"]
    assert r["n_buy_count"] == 100
    assert r["l_buy_volume"] == 500000
    assert r["n_sell_volume"] == 400000


def test_parse_empty():
    assert ClientTypeAllProvider.parse_client_type_all("") == {}
    assert ClientTypeAllProvider.parse_client_type_all(";;;") == {}
