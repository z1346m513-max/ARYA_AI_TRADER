from rich.console import Console

from arya.dashboard.console_dashboard import render_recommendation
from arya.dashboard.i18n import (
    translate_action,
    translate_alert,
    translate_market,
    translate_risk,
    translate_section,
)
from arya.models.analysis_result import (
    Action,
    Recommendation,
    RiskAssessment,
    SectionScore,
)


def _recommendation():
    return Recommendation(
        symbol="فملی@stock",
        overall_score=0.1188,
        confidence=0.3333,
        trend_quality=0.6666,
        liquidity_strength=0.6211,
        action=Action.HOLD,
        reasons=["امتیاز کلی (0.12) در محدوده خنثی قرار دارد."],
        risk=RiskAssessment(
            risk_level="medium",
            risk_score=0.45,
            max_position_size_pct=10.0,
            stop_loss_pct=3.36,
            notes=[],
        ),
        section_scores=[
            SectionScore(
                section="technical",
                score=0.1188,
                confidence=0.3333,
                details={"alerts": ["price_above_sma", "price_above_ema"]},
            )
        ],
    )


def test_persian_translation_map():
    assert translate_action(Action.HOLD) == "نگهداری"
    assert translate_risk("medium") == "متوسط"
    assert translate_section("technical") == "فنی"
    assert translate_market("stock") == "بورس ایران"
    assert translate_alert("price_above_sma") == "قیمت بالاتر از میانگین ساده"


def test_render_recommendation_is_fully_persian_for_known_labels():
    console = Console(record=True, force_terminal=False)
    render_recommendation(_recommendation(), console=console, language="fa")
    output = console.export_text()

    assert "نگهداری" in output
    assert "بورس ایران" in output
    assert "متوسط" in output
    assert "هشدارها:" in output
    assert "قیمت بالاتر از میانگین ساده" in output
    assert "قیمت بالاتر از میانگین نمایی" in output
    assert "technical" not in output
    assert "medium" not in output


def test_internal_model_values_remain_stable():
    rec = _recommendation()
    assert rec.action is Action.HOLD
    assert rec.risk.risk_level == "medium"
    assert rec.section_scores[0].section == "technical"


def test_decision_engine_localizes_section_name():
    from arya.ai.reasoning.decision_engine import RuleBasedDecisionEngine

    decision = RuleBasedDecisionEngine().decide(
        0.1188,
        0.3333,
        [
            SectionScore(
                section="technical",
                score=0.1188,
                confidence=0.3333,
            )
        ],
        language="fa",
    )

    assert "بخش «فنی»" in decision.reasons[0]
    assert "technical" not in decision.reasons[0]
