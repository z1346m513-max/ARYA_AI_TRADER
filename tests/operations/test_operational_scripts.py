import json
import sys
from pathlib import Path

from arya.providers.market.tsetmc_provider import TsetmcMarketProvider

sys.path.insert(0, str(Path(__file__).parents[2]))
from scripts.drive_sync_worker import process_downloads


def test_drive_worker_processes_json_and_rejects_disallowed_files(tmp_path: Path):
    local = tmp_path / "phase-one"
    local.mkdir()
    (local / "report.json").write_text('{"ticker": "فولاد", "eps": 600}', encoding="utf-8")
    (local / "secret.key").write_text("must not enter knowledge base", encoding="utf-8")
    manifest = local / "manifest.json"

    first = process_downloads(local, manifest, 1024 * 1024)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert first["processed"] == 1
    assert first["rejected"] == 1
    assert payload["files"]["report.json"]["content"]["records"] == 1
    assert payload["files"]["secret.key"]["status"] == "rejected"

    second = process_downloads(local, manifest, 1024 * 1024)
    assert second["skipped"] >= 1


def test_market_watch_maps_quote_fields(monkeypatch):
    provider = TsetmcMarketProvider(base_url="https://example.test", retries=1)
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda path: {
            "marketwatch": [
                {
                    "lVal18AFC": "فولاد",
                    "lVal30": "فولاد مبارکه",
                    "pDrCotVal": 120,
                    "pClosing": 118,
                    "priceYesterday": 110,
                    "qTotTran5J": 5000,
                    "qTotCap": 600000,
                }
            ]
        },
    )
    quotes = provider.fetch_market_watch("فولاد")
    assert quotes[0]["ticker"] == "فولاد"
    assert quotes[0]["last"] == 120
    assert quotes[0]["volume"] == 5000
