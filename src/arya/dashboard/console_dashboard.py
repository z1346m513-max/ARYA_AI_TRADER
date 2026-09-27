"""
Dashboard (نسخه‌ی Console): آخرین حلقه‌ی پایپ‌لاین.

نمایش از تنظیمات زبان پروژه پیروی می‌کند و مقادیر داخلی انگلیسی را فقط در
لایه presentation ترجمه می‌کند؛ مدل‌های داخلی API همچنان stable باقی می‌مانند.
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from arya.dashboard.i18n import (
    translate_action,
    translate_alert,
    translate_market,
    translate_risk,
    translate_section,
)
from arya.models.analysis_result import Recommendation


def render_recommendation(
    rec: Recommendation,
    console: Console | None = None,
    language: str = "fa",
) -> None:
    console = console or Console()

    action_label = translate_action(rec.action, language)
    symbol_label, separator, market_code = rec.symbol.partition("@")
    market_label = ""
    if separator:
        market_label = (
            f" | بازار: {translate_market(market_code, language)}"
            if language != "en"
            else f" | market: {translate_market(market_code, language)}"
        )

    header = (
        f"{action_label}  —  امتیاز کلی: {float(rec.overall_score):+.2f}  "
        f"| اطمینان: {rec.confidence:.0%}  | کیفیت روند: {rec.trend_quality:.0%}  "
        f"| نقدشوندگی: {float(rec.liquidity_strength):.0%}"
    )
    console.print(
        Panel(
            header,
            title=f"{symbol_label}{market_label}",
            expand=False,
        )
    )

    if rec.risk:
        risk_table = Table(
            title="ارزیابی ریسک" if language != "en" else "Risk assessment",
            show_header=True,
            header_style="bold cyan",
        )
        risk_table.add_column("سطح ریسک" if language != "en" else "Risk level")
        risk_table.add_column("امتیاز ریسک" if language != "en" else "Risk score")
        risk_table.add_column(
            "حداکثر پوزیشن" if language != "en" else "Max position"
        )
        risk_table.add_column(
            "حد ضرر پیشنهادی" if language != "en" else "Suggested stop loss"
        )
        risk_table.add_row(
            translate_risk(rec.risk.risk_level, language),
            f"{float(rec.risk.risk_score):.2f}",
            f"{rec.risk.max_position_size_pct:.1f}%",
            f"{rec.risk.stop_loss_pct:.1f}%"
            if rec.risk.stop_loss_pct
            else "-",
        )
        console.print(risk_table)

    if rec.reasons:
        console.print("دلایل:" if language != "en" else "Reasons:")
        for reason in rec.reasons:
            console.print(f"  • {reason}")

    # Expose translated indicator section/alerts without changing core models.
    for section in rec.section_scores:
        details = section.details or {}
        alerts = details.get("alerts") or []
        if alerts and language != "en":
            console.print("هشدارها:")
            for alert in alerts:
                console.print(f"  • {translate_alert(alert, language)}")
        if language == "en":
            console.print(
                f"Section: {translate_section(section.section, language)}"
                f" | score: {float(section.score):+.2f}"
                f" | confidence: {section.confidence:.0%}"
            )

    console.print()
