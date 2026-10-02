from datetime import datetime, timezone, timedelta

from arya.models.data_quality import DataCoverage, DataProvenance, DataQuality, DataStatus


def test_provenance_age_is_non_negative():
    provenance = DataProvenance(
        source="mock",
        status=DataStatus.SYNTHETIC,
        quality=DataQuality.LOW,
        fetched_at=datetime.now(timezone.utc) - timedelta(seconds=5),
    )
    assert provenance.age_seconds is not None
    assert provenance.age_seconds >= 5


def test_coverage_ratio():
    coverage = DataCoverage(available=("technical", "risk"), unavailable=("fundamental", "news"))
    assert coverage.ratio == 0.5
