from datetime import datetime, timezone
from math import nan

import pytest

from arya.app.bootstrap import AryaApp
from arya.data_quality import OHLCVQualityError, snapshot_sha256, validate_ohlcv_series
from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.storage.cache import OHLCVStore


def make_series(candles=None):
    candles = candles if candles is not None else [
        Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 12, 9, 11, 100),
        Candle(datetime(2026, 1, 3, tzinfo=timezone.utc), 11, 13, 10, 12, 120),
    ]
    return OHLCVSeries(Symbol("TEST", "stock"), "1d", candles)


def test_valid_series_passes_structural_checks():
    report = validate_ohlcv_series(make_series())
    assert report.is_valid
    assert report.row_count == 2
    assert report.issues == ()
    assert report.first_timestamp.startswith("2026-01-02")


def test_empty_series_is_rejected():
    report = validate_ohlcv_series(make_series([]))
    assert not report.is_valid
    assert report.issues[0].code == "empty_series"


@pytest.mark.parametrize(
    ("candles", "expected_code"),
    [
        ([Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 9, 8, 11, 1)], "high_below_ohlc"),
        ([Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10, -1)], "negative_volume"),
        ([
            Candle(datetime(2026, 1, 3, tzinfo=timezone.utc), 10, 11, 9, 10, 1),
            Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10, 1),
        ], "unordered_timestamp"),
        ([
            Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10, 1),
            Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 11, 9, 10, 1),
        ], "duplicate_timestamp"),
    ],
)
def test_invalid_series_reports_specific_issue(candles, expected_code):
    report = validate_ohlcv_series(make_series(candles))
    assert not report.is_valid
    assert expected_code in {issue.code for issue in report.issues}


def test_snapshot_hash_is_stable_and_changes_with_data():
    first = make_series()
    same = make_series()
    changed = make_series([
        Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 12, 9, 11, 100),
        Candle(datetime(2026, 1, 3, tzinfo=timezone.utc), 11, 13, 10, 12, 121),
    ])
    assert snapshot_sha256(first) == snapshot_sha256(same)
    assert snapshot_sha256(first) != snapshot_sha256(changed)


def test_non_finite_values_and_mixed_timezone_timestamps_are_rejected():
    series = make_series([
        Candle(datetime(2026, 1, 2), 10, 12, 9, 11, 100),
        Candle(datetime(2026, 1, 3, tzinfo=timezone.utc), 11, 13, 10, nan, 120),
    ])
    report = validate_ohlcv_series(series)
    codes = {issue.code for issue in report.issues}
    assert not report.is_valid
    assert "incomparable_timestamp" in codes
    assert "non_finite_close" in codes


def test_store_persists_validation_event(tmp_path):
    store = OHLCVStore(tmp_path / "quality.db")
    series = make_series()
    report = validate_ohlcv_series(series)
    store.record_data_quality("run-1", series, "fixture", "2026-01-03T00:00:00+00:00", report, snapshot_sha256(series))
    loaded = store.load_data_quality_run("run-1")
    assert loaded["ticker"] == "TEST"
    assert loaded["provider"] == "fixture"
    assert loaded["is_valid"] is True
    assert loaded["row_count"] == 2
    assert loaded["issues"] == []
    store.close()


def test_recommendation_references_quality_run_and_bad_data_is_not_analyzed(tmp_path, monkeypatch):
    from arya.config.settings import Settings

    settings = Settings.load()
    settings.providers["market"]["stock"]["driver"] = "mock"
    settings.app["storage"]["path"] = str(tmp_path / "app.db")
    app = AryaApp(settings)
    recommendation = app.analyze_symbol("FOOLAD")
    assert recommendation.data_quality_run_id
    event = app.store.load_data_quality_run(recommendation.data_quality_run_id)
    assert event["is_valid"] is True
    assert event["provider"] == "mock"

    class InvalidProvider:
        name = "invalid-test-provider"

        def fetch_ohlcv(self, symbol, timeframe, limit=200):
            return make_series([
                Candle(datetime(2026, 1, 2, tzinfo=timezone.utc), 10, 9, 8, 11, 1)
            ])

    monkeypatch.setattr(app, "_provider_for_market", lambda market: InvalidProvider())
    with pytest.raises(OHLCVQualityError):
        app.analyze_symbol("BROKEN")
    rows = app.store._conn.execute(
        "SELECT run_id, is_valid, issues_json FROM data_quality_runs WHERE ticker='TEST'"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][1] == 0
    assert "high_below_ohlc" in rows[0][2]
    app.store.close()
