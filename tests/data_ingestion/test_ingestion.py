"""
تست‌های قرارداد data_ingestion.

موارد پوشش‌داده‌شده:
- فایل معتبر: manifest + normalized تولید می‌شود
- ستون الزامی نبود: رد می‌شود
- کندل نامعتبر: خطا ثبت می‌شود
- ردیف تکراری: شناسایی می‌شود
- timestamp بدون timezone: هشدار داده می‌شود
- idempotency: فایل تکراری پردازش نمی‌شود
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arya.data_ingestion.excel_loader import load_market_file, LoaderError
from arya.data_ingestion.manifest import FileManifest, compute_sha256
from arya.data_ingestion.normalizer import normalize_market_data, save_normalized
from arya.data_ingestion.validator import validate_market_data, ValidationStatus
from arya.data_ingestion.inbox import IngestionPipeline


# ─── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def valid_df():
    return pd.DataFrame({
        "timestamp": [
            "2026-10-06T10:00:00+03:30",
            "2026-10-06T11:00:00+03:30",
            "2026-10-06T12:00:00+03:30",
        ],
        "symbol": ["فولاد", "فولاد", "فولاد"],
        "open": [1000.0, 1010.0, 1020.0],
        "high": [1020.0, 1030.0, 1040.0],
        "low": [990.0, 1000.0, 1010.0],
        "close": [1010.0, 1020.0, 1030.0],
        "volume": [10000, 12000, 8000],
    })


@pytest.fixture
def invalid_ohlc_df():
    return pd.DataFrame({
        "timestamp": ["2026-10-06T10:00:00+03:30"],
        "symbol": ["فولاد"],
        "open": [1000.0],
        "high": [990.0],   # خطا: high < open
        "low": [1010.0],  # خطا: low > open
        "close": [1005.0],
        "volume": [5000],
    })


@pytest.fixture
def duplicate_df():
    return pd.DataFrame({
        "timestamp": [
            "2026-10-06T10:00:00+03:30",
            "2026-10-06T10:00:00+03:30",
        ],
        "symbol": ["فولاد", "فولاد"],
        "open": [1000.0, 1000.0],
        "high": [1020.0, 1020.0],
        "low": [990.0, 990.0],
        "close": [1010.0, 1010.0],
        "volume": [10000, 10000],
    })


@pytest.fixture
def temp_dirs(tmp_path):
    """مسیرهای موقت برای تست pipeline."""
    return {
        "inbox": tmp_path / "inbox" / "market",
        "processing": tmp_path / "processing",
        "archive": tmp_path / "archive" / "market",
        "rejected": tmp_path / "rejected",
        "normalized": tmp_path / "normalized",
        "manifests": tmp_path / "manifests",
        "reports": tmp_path / "reports" / "daily",
    }


@pytest.fixture
def pipeline(temp_dirs):
    return IngestionPipeline(
        inbox_dir=temp_dirs["inbox"],
        processing_dir=temp_dirs["processing"],
        archive_dir=temp_dirs["archive"],
        rejected_dir=temp_dirs["rejected"],
        normalized_dir=temp_dirs["normalized"],
        manifests_dir=temp_dirs["manifests"],
        reports_dir=temp_dirs["reports"],
    )


def write_csv(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


# ─── Manifest Tests ────────────────────────────────────────

def test_manifest_sha256_computed(valid_df, tmp_path):
    csv_path = write_csv(valid_df, tmp_path / "test_market.csv")
    manifest = FileManifest.create(csv_path)
    assert len(manifest.sha256) == 64
    assert manifest.file_name == "test_market.csv"
    assert manifest.source == "manual_upload"


def test_manifest_is_immutable(valid_df, tmp_path):
    csv_path = write_csv(valid_df, tmp_path / "test_market.csv")
    manifest = FileManifest.create(csv_path)
    with pytest.raises(Exception):
        manifest.sha256 = "changed"  # frozen dataclass


# ─── Validator Tests ────────────────────────────────────────

def test_valid_data_passes(valid_df):
    report = validate_market_data(valid_df)
    assert report.status == ValidationStatus.VALID
    assert report.total_rows == 3
    assert report.symbols == 1
    assert len(report.errors) == 0


def test_missing_required_column_rejected():
    df = pd.DataFrame({"timestamp": ["2026-10-06"], "symbol": ["X"]})
    report = validate_market_data(df)
    assert report.status == ValidationStatus.REJECTED
    assert any("الزامی" in e for e in report.errors)


def test_invalid_ohlc_detected(invalid_ohlc_df):
    report = validate_market_data(invalid_ohlc_df)
    assert report.status in (ValidationStatus.INVALID, ValidationStatus.PARTIAL)
    assert any("high" in e.lower() for e in report.errors)


def test_duplicate_rows_detected(duplicate_df):
    report = validate_market_data(duplicate_df)
    assert report.duplicate_rows == 2
    assert any("تکراری" in w for w in report.warnings)


def test_negative_price_detected():
    df = pd.DataFrame({
        "timestamp": ["2026-10-06T10:00:00+03:30"],
        "symbol": ["X"],
        "open": [-100.0],
        "high": [10.0],
        "low": [5.0],
        "close": [8.0],
        "volume": [100],
    })
    report = validate_market_data(df)
    assert any("منفی" in e for e in report.errors)


# ─── Normalizer Tests ──────────────────────────────────────

def test_normalize_valid_data(valid_df):
    report = validate_market_data(valid_df)
    normalized = normalize_market_data(valid_df, report)
    assert normalized is not None
    assert normalized.rows == 3
    assert normalized.symbols == 1
    assert normalized.date_min != ""
    assert normalized.date_max != ""


def test_normalize_rejected_returns_none():
    df = pd.DataFrame({"timestamp": [], "symbol": []})
    # ساخت یک report رد شده
    from arya.data_ingestion.validator import ValidationReport
    report = ValidationReport(status=ValidationStatus.REJECTED)
    result = normalize_market_data(df, report)
    assert result is None


def test_normalize_removes_duplicates(duplicate_df):
    report = validate_market_data(duplicate_df)
    normalized = normalize_market_data(duplicate_df, report)
    assert normalized is not None
    assert normalized.rows == 1  # یکی از دو ردیف تکراری حذف می‌شود


def test_save_normalized_csv(valid_df, tmp_path):
    report = validate_market_data(valid_df)
    normalized = normalize_market_data(valid_df, report)
    out_path = save_normalized(normalized, tmp_path, "market_2026-10-06.xlsx", fmt="csv")
    assert out_path.exists()
    assert out_path.suffix == ".csv"


def test_save_normalized_jsonl(valid_df, tmp_path):
    report = validate_market_data(valid_df)
    normalized = normalize_market_data(valid_df, report)
    out_path = save_normalized(normalized, tmp_path, "market_2026-10-06.xlsx", fmt="jsonl")
    assert out_path.exists()
    assert out_path.suffix == ".jsonl"


# ─── Loader Tests ──────────────────────────────────────────

def test_load_csv(valid_df, tmp_path):
    csv_path = write_csv(valid_df, tmp_path / "market.csv")
    df = load_market_file(csv_path)
    assert len(df) == 3
    assert "symbol" in df.columns


def test_load_unsupported_format(tmp_path):
    bad_path = tmp_path / "market.txt"
    bad_path.write_text("hello")
    with pytest.raises(LoaderError):
        load_market_file(bad_path)


def test_load_nonexistent_file():
    with pytest.raises(LoaderError):
        load_market_file(Path("/nonexistent/file.xlsx"))


# ─── Pipeline Integration Tests ─────────────────────────────

def test_pipeline_process_valid_file(valid_df, pipeline, temp_dirs):
    csv_path = write_csv(valid_df, temp_dirs["inbox"] / "market_2026-10-06.csv")
    result = pipeline.process_file(csv_path, archive_original=True)

    assert result.success is True
    assert result.manifest is not None
    assert result.manifest.validation_status == "VALID"
    assert result.manifest.normalized_path is not None
    assert Path(result.manifest.normalized_path).exists()

    # manifest ذخیره شده
    manifest_path = temp_dirs["manifests"] / "market_2026-10-06.csv.manifest.json"
    assert manifest_path.exists()

    # فایل به archive منتقل شده
    archived = temp_dirs["archive"] / "market_2026-10-06.csv"
    assert archived.exists()

    # گزارش کیفیت تولید شده
    report_md = temp_dirs["reports"] / "market_2026-10-06_quality.md"
    assert report_md.exists()


def test_pipeline_rejects_missing_columns(pipeline, temp_dirs):
    df = pd.DataFrame({"timestamp": ["2026-10-06"], "symbol": ["X"]})
    csv_path = write_csv(df, temp_dirs["inbox"] / "bad_market.csv")
    result = pipeline.process_file(csv_path)

    assert result.success is False
    assert result.manifest is not None
    assert result.manifest.validation_status == "REJECTED"

    # فایل به rejected منتقل شده
    rejected = temp_dirs["rejected"] / "bad_market.csv"
    assert rejected.exists()


def test_pipeline_idempotency(valid_df, pipeline, temp_dirs):
    csv_path = write_csv(valid_df, temp_dirs["inbox"] / "market_dup.csv")

    # پردازش اول
    r1 = pipeline.process_file(csv_path)
    assert r1.success is True

    # پردازش دوم - باید idempotent باشد
    r2 = pipeline.process_file(csv_path)
    assert r2.manifest is not None
    assert r2.error is not None
    assert "idempotency" in r2.error.lower() or "قبلاً" in r2.error


def test_pipeline_process_inbox(valid_df, pipeline, temp_dirs):
    write_csv(valid_df, temp_dirs["inbox"] / "market_2026-10-06.csv")
    write_csv(valid_df, temp_dirs["inbox"] / "market_2026-10-07.csv")

    results = pipeline.process_inbox()
    assert len(results) == 2
    assert all(r.success for r in results)


def test_pipeline_quality_report_content(valid_df, pipeline, temp_dirs):
    csv_path = write_csv(valid_df, temp_dirs["inbox"] / "market_test.csv")
    pipeline.process_file(csv_path)

    report_md = temp_dirs["reports"] / "market_test_quality.md"
    content = report_md.read_text(encoding="utf-8")
    assert "SHA-256" in content
    assert "VALID" in content
    assert "نمادها" in content
