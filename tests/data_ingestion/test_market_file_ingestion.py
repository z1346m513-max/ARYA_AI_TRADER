import csv
import hashlib
import io
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from arya.data_ingestion import pipeline
from arya.data_ingestion.cli import main
from arya.data_ingestion.pipeline import IngestionContext, IngestionError, ingest_file

NOW = datetime(2026, 11, 8, 12, tzinfo=timezone.utc)
HEADERS = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
ROWS = [
    ["2026-11-07T09:00:00+03:30", "فولاد", 100, 110, 90, 105, 1000],
    ["2026-11-08T09:00:00+03:30", "فولاد", 105, 115, 100, 110, 1200],
]


@pytest.fixture
def context():
    return IngestionContext("iran_equity", "manual-export", "TSE", "IRR", "shares", max_age_hours=48)


def csv_file(tmp_path, rows=None, headers=None, name="market.csv"):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(HEADERS if headers is None else headers)
    writer.writerows(ROWS if rows is None else rows)
    path = tmp_path / name
    path.write_text(stream.getvalue(), encoding="utf-8-sig")
    return path


def read_result(result, name):
    return json.loads((Path(result["run_path"]) / name).read_text(encoding="utf-8"))


def test_csv_complete_auditable_run_keeps_input(tmp_path, context):
    path = csv_file(tmp_path)
    original = path.read_bytes()
    result = ingest_file(path, tmp_path / "output", context, now=NOW)
    assert result["status"] == "PROCESSED"
    assert path.read_bytes() == original
    manifest = read_result(result, "manifest.json")
    assert manifest["sha256"] == hashlib.sha256(original).hexdigest()
    assert manifest["rows"] == 2
    assert manifest["source_trust"] == "UNVERIFIED"
    assert manifest["received_at_utc"] == NOW.isoformat()
    assert (Path(result["run_path"]) / "input.csv").read_bytes() == original
    normalized = read_result(result, "normalized.json")
    assert normalized[0]["timestamp"] == "2026-11-07T05:30:00+00:00"
    assert normalized[0]["currency"] == "IRR"
    report = read_result(result, "report.json")
    assert report["risk_gate"] == "UNASSESSED"
    assert report["recommendations"] == []
    assert report["freshness"][0]["status"] == "WITHIN_AGE_LIMIT"
    assert read_result(result, "agent_outputs/fundamental.json")["status"] == "NOT_AVAILABLE"
    assert read_result(result, "agent_outputs/technical.json")["status"] == "DESCRIPTIVE_ONLY"
    assert not list((tmp_path / "output").rglob(".pending-*"))
    assert not list((tmp_path / "output").rglob(".ingest.lock"))


@pytest.mark.parametrize("market,currency,unit", [
    ("iran_equity", "IRT", "shares"), ("crypto", "USDT", "base_asset"), ("forex", "USD", "ticks"),
])
def test_market_separation_and_no_implicit_currency_conversion(tmp_path, market, currency, unit):
    path = csv_file(tmp_path)
    result = ingest_file(
        path, tmp_path / "output",
        IngestionContext(market, "manual", "test-venue", currency, unit), now=NOW,
    )
    assert Path(result["run_path"]).parent.parent.name == market
    normalized = read_result(result, "normalized.json")
    assert normalized[0]["close"] == 105
    assert normalized[0]["currency"] == currency
    assert read_result(result, "report.json")["freshness"][0]["status"] == "UNKNOWN"


def test_duplicate_recomputes_age_without_republishing(tmp_path, context):
    path = csv_file(tmp_path)
    root = tmp_path / "output"
    first = ingest_file(path, root, context, now=NOW)
    before = (Path(first["run_path"]) / "report.json").read_bytes()
    second = ingest_file(path, root, context, now=NOW + timedelta(days=10))
    assert second["status"] == "DUPLICATE"
    assert first["run_id"] == second["run_id"]
    assert second["freshness"][0]["status"] == "STALE"
    assert second["risk_gate"] == "BLOCK"
    assert (Path(first["run_path"]) / "report.json").read_bytes() == before
    assert len(list((root / "iran_equity" / "runs").iterdir())) == 1


def test_changed_context_has_new_identity(tmp_path, context):
    path = csv_file(tmp_path)
    first = ingest_file(path, tmp_path / "output", context, now=NOW)
    second = ingest_file(path, tmp_path / "output", replace(context, currency="IRT"), now=NOW)
    assert first["run_id"] != second["run_id"]


def test_tampered_normalized_artifact_is_not_reused(tmp_path, context):
    path = csv_file(tmp_path)
    first = ingest_file(path, tmp_path / "output", context, now=NOW)
    (Path(first["run_path"]) / "normalized.json").write_text("[]", encoding="utf-8")
    with pytest.raises(IngestionError, match="integrity"):
        ingest_file(path, tmp_path / "output", context, now=NOW)


def test_incomplete_published_run_is_not_reused(tmp_path, context):
    path = csv_file(tmp_path)
    first = ingest_file(path, tmp_path / "output", context, now=NOW)
    (Path(first["run_path"]) / "report.json").unlink()
    with pytest.raises(IngestionError, match="report is missing"):
        ingest_file(path, tmp_path / "output", context, now=NOW)


@pytest.mark.parametrize("updates", [
    {"market": "stock"}, {"source": ""}, {"venue": " "}, {"currency": "USD"},
    {"volume_unit": "ticks"}, {"max_age_hours": 0}, {"max_age_hours": -1},
    {"max_age_hours": float("nan")}, {"max_age_hours": float("inf")},
])
def test_invalid_context(context, updates):
    with pytest.raises(IngestionError):
        replace(context, **updates)


@pytest.mark.parametrize("field,value", [
    ("timestamp", "2026-11-08"), ("timestamp", "2026-02-30T00:00:00Z"),
    ("timestamp", ""), ("symbol", ""), ("open", ""), ("open", 0),
    ("high", 90), ("low", 120), ("volume", -1), ("close", "nan"),
    ("volume", "inf"), ("open", "=1+1"),
])
def test_bad_row_is_quarantined_without_partial_output(tmp_path, context, field, value):
    rows = [list(ROWS[0])]
    rows[0][HEADERS.index(field)] = value
    path = csv_file(tmp_path, rows)
    root = tmp_path / "output"
    with pytest.raises(IngestionError):
        ingest_file(path, root, context, now=NOW)
    rejected = list((root / "iran_equity" / "rejected").glob("*/manifest.json"))
    assert len(rejected) == 1
    assert json.loads(rejected[0].read_text())["validation_status"] == "REJECTED"
    assert not list((root / "iran_equity" / "runs").iterdir())
    assert path.exists()
    assert not (root / "iran_equity" / ".ingest.lock").exists()


@pytest.mark.parametrize("rows", [[ROWS[0], ROWS[0]], list(reversed(ROWS))])
def test_duplicates_and_unordered_observations_are_not_silently_fixed(tmp_path, context, rows):
    with pytest.raises(IngestionError):
        ingest_file(csv_file(tmp_path, rows), tmp_path / "output", context, now=NOW)


@pytest.mark.parametrize("headers", [
    HEADERS[:-1], HEADERS + ["volume"], HEADERS + ["secret_extra"],
])
def test_headers_rejected(tmp_path, context, headers):
    with pytest.raises(IngestionError):
        ingest_file(csv_file(tmp_path, headers=headers), tmp_path / "output", context, now=NOW)


@pytest.mark.parametrize("extra,value", [("market", "crypto"), ("currency", "IRT"), ("venue", "OTHER")])
def test_mixed_context_rejected(tmp_path, context, extra, value):
    path = csv_file(tmp_path, [ROWS[0] + [value]], HEADERS + [extra])
    with pytest.raises(IngestionError, match="conflicts"):
        ingest_file(path, tmp_path / "output", context, now=NOW)


@pytest.mark.parametrize("now,status", [
    (NOW + timedelta(days=10), "STALE"),
    (NOW - timedelta(days=3), "FUTURE"),
])
def test_age_gate_blocks_stale_and_future(tmp_path, context, now, status):
    result = ingest_file(csv_file(tmp_path), tmp_path / "output", context, now=now)
    report = read_result(result, "report.json")
    assert report["risk_gate"] == "BLOCK"
    assert report["freshness"][0]["status"] == status


def test_each_symbol_is_assessed_for_age(tmp_path, context):
    rows = [list(ROWS[0]), list(ROWS[1])]
    rows[0][0] = "2026-01-01T00:00:00Z"
    rows[0][1] = "قدیمی"
    result = ingest_file(csv_file(tmp_path, rows), tmp_path / "output", context, now=NOW)
    report = read_result(result, "report.json")
    assert report["risk_gate"] == "BLOCK"
    assert {x["status"] for x in report["freshness"]} == {"STALE", "WITHIN_AGE_LIMIT"}


def xlsx_file(tmp_path, rows=None, sheet="ohlcv"):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    workbook.active.title = sheet
    workbook.active.append(HEADERS)
    for row in ROWS if rows is None else rows:
        workbook.active.append(row)
    path = tmp_path / "market.xlsx"
    workbook.save(path)
    workbook.close()
    return path


def test_xlsx_actual_read_only_loader(tmp_path, context):
    result = ingest_file(xlsx_file(tmp_path), tmp_path / "output", context, now=NOW)
    assert result["manifest"]["rows"] == 2
    assert read_result(result, "normalized.json")[0]["symbol"] == "فولاد"


def test_xlsx_formula_is_rejected_not_cached(tmp_path, context):
    row = list(ROWS[0])
    row[2] = "=100"
    with pytest.raises(IngestionError, match="formulas"):
        ingest_file(xlsx_file(tmp_path, [row]), tmp_path / "output", context, now=NOW)


def test_xlsx_naive_native_datetime_requires_explicit_offset(tmp_path, context):
    row = list(ROWS[0])
    row[0] = NOW.replace(tzinfo=None)
    with pytest.raises(IngestionError, match="timestamp"):
        ingest_file(xlsx_file(tmp_path, [row]), tmp_path / "output", context, now=NOW)


def test_xlsx_missing_sheet(tmp_path, context):
    with pytest.raises(IngestionError, match="sheet"):
        ingest_file(xlsx_file(tmp_path, sheet="other"), tmp_path / "output", context, now=NOW)


def test_xlsx_zip_expansion_limit(tmp_path, context, monkeypatch):
    path = xlsx_file(tmp_path)
    monkeypatch.setattr(pipeline, "MAX_EXPANDED_BYTES", 1)
    with pytest.raises(IngestionError, match="expanded"):
        ingest_file(path, tmp_path / "output", context, now=NOW)


def test_input_size_limit(tmp_path, context, monkeypatch):
    path = csv_file(tmp_path)
    monkeypatch.setattr(pipeline, "MAX_BYTES", 1)
    with pytest.raises(IngestionError, match="20 MiB"):
        ingest_file(path, tmp_path / "output", context, now=NOW)


@pytest.mark.parametrize("suffix", [".xls", ".xlsm", ".txt"])
def test_unsupported_input_formats(tmp_path, context, suffix):
    path = tmp_path / ("market" + suffix)
    path.write_bytes(b"not a supported format")
    with pytest.raises(IngestionError, match="only"):
        ingest_file(path, tmp_path / "output", context, now=NOW)


def test_input_symlink_is_rejected(tmp_path, context):
    path = csv_file(tmp_path)
    link = tmp_path / "link.csv"
    link.symlink_to(path)
    with pytest.raises(IngestionError, match="non-symlink"):
        ingest_file(link, tmp_path / "output", context, now=NOW)


def test_corrupt_xlsx_is_quarantined(tmp_path, context):
    path = tmp_path / "corrupt.xlsx"
    path.write_bytes(b"not a zip archive")
    with pytest.raises(IngestionError, match="cannot parse"):
        ingest_file(path, tmp_path / "output", context, now=NOW)
    assert list((tmp_path / "output").rglob("rejected/*/manifest.json"))


def test_row_limit(tmp_path, context, monkeypatch):
    path = csv_file(tmp_path)
    monkeypatch.setattr(pipeline, "MAX_ROWS", 1)
    with pytest.raises(IngestionError, match="row limit"):
        ingest_file(path, tmp_path / "output", context, now=NOW)


def test_locked_worker_does_not_remove_other_workers_lock(tmp_path, context):
    path = csv_file(tmp_path)
    lock = tmp_path / "output" / "iran_equity" / ".ingest.lock"
    lock.mkdir(parents=True)
    with pytest.raises(IngestionError, match="locked"):
        ingest_file(path, tmp_path / "output", context, now=NOW)
    assert lock.exists()


def test_failed_publish_is_never_visible_and_can_retry(tmp_path, context, monkeypatch):
    path = csv_file(tmp_path)
    original = pipeline._write_json

    def failure(target, payload):
        if target.name == "report.json":
            raise OSError("simulated storage failure")
        original(target, payload)

    with monkeypatch.context() as scoped:
        scoped.setattr(pipeline, "_write_json", failure)
        with pytest.raises(OSError):
            ingest_file(path, tmp_path / "output", context, now=NOW)
    assert not list((tmp_path / "output").rglob("report.json"))
    assert not list((tmp_path / "output").rglob(".pending-*"))
    assert ingest_file(path, tmp_path / "output", context, now=NOW)["status"] == "PROCESSED"


def cli_args(tmp_path):
    return [
        "--market", "iran_equity", "--source", "manual", "--venue", "TSE",
        "--currency", "IRR", "--volume-unit", "shares", "--root", str(tmp_path / "output"),
    ]


def test_cli_runs_without_bootstrapping_live_app(tmp_path, monkeypatch, capsys):
    from arya.cli.main import main as arya_main

    def forbidden():
        raise AssertionError("must not initialize application, provider or SQLite")

    monkeypatch.setattr("arya.cli.main.AryaApp", forbidden)
    path = csv_file(tmp_path)
    assert arya_main(["ingest-market-file", "--file", str(path), *cli_args(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["results"][0]["status"] == "PROCESSED"


def test_inbox_continues_after_bad_file_and_ignores_temp_and_unsettled(tmp_path, capsys):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    csv_file(inbox, name="good.csv")
    csv_file(inbox, rows=[["bad"]], name="bad.csv")
    csv_file(inbox, name="~$temporary.xlsx")
    assert main(["--inbox", str(inbox), "--settle-seconds", "3600", *cli_args(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["results"] == []
    assert main(["--inbox", str(inbox), "--settle-seconds", "0", *cli_args(tmp_path)]) == 2
    results = json.loads(capsys.readouterr().out)["results"]
    assert [row["status"] for row in results] == ["ERROR", "PROCESSED"]


def test_inbox_missing_is_error_not_empty_success(tmp_path, capsys):
    assert main(["--inbox", str(tmp_path / "missing"), *cli_args(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out)["results"][0]["status"] == "ERROR"
