from arya.models.analysis_result import Action, IndicatorResult, Recommendation, SectionScore
from arya.models.data_quality import DataCoverage, DataQuality, DataProvenance, DataStatus


def test_recommendation_preserves_legacy_defaults():
    result = Recommendation(
        symbol="TEST",
        overall_score=0.4,
        confidence=0.7,
        trend_quality=0.8,
        liquidity_strength=0.6,
        action=Action.BUY,
    )
    assert result.coverage.ratio == 0.0
    assert result.confidence_is_data_limited is True


def test_indicator_can_carry_provenance_and_confidence():
    result = IndicatorResult(
        name="RSI",
        group="momentum",
        value={"rsi": 65.0},
        score=0.3,
        weight=1.0,
        confidence=0.9,
        provenance=DataProvenance(
            source="mock",
            status=DataStatus.SYNTHETIC,
            quality=DataQuality.LOW,
        ),
    )
    assert result.confidence == 0.9
    assert result.provenance.source == "mock"


def test_section_score_accepts_provenance():
    score = SectionScore(
        section="technical",
        score=0.5,
        confidence=0.8,
        provenance=DataProvenance(source="tsetmc", status=DataStatus.FRESH),
    )
    assert score.provenance.status is DataStatus.FRESH
