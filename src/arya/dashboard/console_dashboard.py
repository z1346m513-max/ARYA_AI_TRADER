"""
Dashboard (نسخه‌ی Console): آخرین حلقه‌ی پایپ‌لاین.
در Milestone 1 خروجی به‌صورت جدول متنی رنگی (rich) نمایش داده می‌شود.
داشبورد گرافیکی PySide6 (src/arya/ui/windows) دقیقاً از همین مدل Recommendation
تغذیه خواهد کرد - هیچ تغییری در لایه‌های بالادست لازم نیست.
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from arya.models.analysis_result import Action, Recommendation, SectionScore

_ACTION_STYLE = {
    Action.BUY: "bold green",
    Action.HOLD: "bold yellow",
    Action.SELL: "bold red",
}

_ACTION_FA = {
    Action.BUY: "خرید",
    Action.HOLD: "نگهداری",
    Action.SELL: "فروش",
}

_CATEGORY_STYLE = {
    "market_value": "bold cyan",
    "profitability": "bold green",
    "liquidity": "bold blue",
    "leverage": "bold red",
    "efficiency": "bold magenta",
    "dividend": "bold yellow",
}

_CATEGORY_FA = {
    "market_value": "ارزش بازار",
    "profitability": "سودآوری",
    "liquidity": "نقدینگی",
    "leverage": "اهرم",
    "efficiency": "کارایی",
    "dividend": "تقسیم سود",
}

_STATUS_STYLE = {
    "OK": "green",
    "UNAVAILABLE": "dim",
    "NOT_MEANINGFUL": "bold red",
}

_STATUS_FA = {
    "OK": "✓",
    "UNAVAILABLE": "—",
    "NOT_MEANINGFUL": "✗",
}

_CATEGORY_ORDER = [
    "market_value",
    "profitability",
    "liquidity",
    "leverage",
    "efficiency",
    "dividend",
]

_PERCENT_KEYS = {"gross_margin", "net_margin", "roe", "roa", "debt_to_asset"}


def render_recommendation(rec: Recommendation, console: Console | None = None) -> None:
    console = console or Console()

    style = _ACTION_STYLE[rec.action]
    action_fa = _ACTION_FA[rec.action]

    header = (
        f"[{style}]{action_fa}[/{style}]  —  امتیاز کلی: {rec.overall_score:+.2f}  "
        f"| اطمینان: {rec.confidence:.0%}  | کیفیت روند: {rec.trend_quality:.0%}  "
        f"| نقدشوندگی: {rec.liquidity_strength:.0%}"
    )
    console.print(Panel(header, title=f"[bold]{rec.symbol}[/bold]", expand=False))

    if rec.risk:
        risk_table = Table(title="ارزیابی ریسک", show_header=True, header_style="bold cyan")
        risk_table.add_column("سطح ریسک")
        risk_table.add_column("امتیاز ریسک")
        risk_table.add_column("حداکثر پوزیشن")
        risk_table.add_column("حد ضرر پیشنهادی")
        risk_table.add_row(
            rec.risk.risk_level,
            f"{rec.risk.risk_score:.2f}",
            f"{rec.risk.max_position_size_pct:.1f}%",
            f"{rec.risk.stop_loss_pct:.1f}%" if rec.risk.stop_loss_pct else "-",
        )
        console.print(risk_table)

    if rec.reasons:
        console.print("[bold]دلایل:[/bold]")
        for r in rec.reasons:
            console.print(f"  • {r}")

    console.print()


def _format_ratio_value(key: str, value: float | None) -> str:
    """مقدار نسبت را برای نمایش قالب‌بندی می‌کند."""
    if value is None:
        return "—"
    if key in _PERCENT_KEYS:
        return f"{value:.2%}"
    if key == "receivables_period":
        return f"{value:.1f} روز"
    return f"{value:.2f}"


def render_fundamental_analysis(
    section_score: SectionScore,
    symbol: str = "",
    console: Console | None = None,
) -> None:
    """
    نتیجه‌ی تحلیل بنیادی (۱۹ نسبت مالی) را در داشبورد کنسول نمایش می‌دهد.

    شامل:
    - پنل خلاصه: امتیاز، اطمینان، کیفیت داده
    - جدول تمام ۱۹ نسبت با دسته، مقدار، وضعیت و فرمول
    - لیست دلایل (نسبت‌های امتیازدهی‌شده با آستانه)
    - آمار نسبت‌های امتیازدهی‌شده، ناموجود و بدون معنا

    Args:
        section_score: خروجی analyze_financial_data یا analyze(metrics).
        symbol: نماد (اختیاری، برای عنوان پنل).
        console: کنسول rich (اختیاری).
    """
    console = console or Console()
    details = section_score.details
    ratios_dict: dict = details.get("ratios", {})

    title = f"تحلیل بنیادی: {symbol}" if symbol else "تحلیل بنیادی"

    # ─── پنل خلاصه ───
    score = section_score.score
    confidence = section_score.confidence
    data_quality = details.get("data_quality", "missing")
    dq_fa = {
        "usable": "قابل استفاده",
        "partial": "ناقص",
        "sparse": "کم",
        "missing": "ناچیز",
    }.get(data_quality, data_quality)

    score_color = "green" if score > 0 else ("red" if score < 0 else "yellow")
    summary = (
        f"امتیاز: [{score_color}]{score:+.4f}[/{score_color}]  |  "
        f"اطمینان: {confidence:.0%}  |  "
        f"کیفیت داده: {dq_fa}"
    )
    console.print(Panel(summary, title=f"[bold]{title}[/bold]", expand=False))

    # ─── جدول تمام ۱۹ نسبت ───
    ratio_table = Table(
        title="نسبت‌های مالی (۱۹ مورد)",
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    ratio_table.add_column("دسته", style="dim", width=12)
    ratio_table.add_column("نام نسبت", width=28)
    ratio_table.add_column("مقدار", justify="right", width=12)
    ratio_table.add_column("وضعیت", justify="center", width=8)
    ratio_table.add_column("فرمول", style="dim")

    scored_keys = set(details.get("scored_ratio_keys", []))

    def _sort_key(item):
        key, ratio_data = item
        cat = ratio_data.get("category", "")
        if cat in _CATEGORY_ORDER:
            return (_CATEGORY_ORDER.index(cat), key)
        return (99, key)

    sorted_ratios = sorted(ratios_dict.items(), key=_sort_key)

    for key, ratio_data in sorted_ratios:
        category = ratio_data.get("category", "")
        name = ratio_data.get("name", key)
        value = ratio_data.get("value")
        status = ratio_data.get("status", "UNAVAILABLE")
        formula = ratio_data.get("formula", "")

        cat_fa = _CATEGORY_FA.get(category, category)
        cat_style = _CATEGORY_STYLE.get(category, "")

        value_str = _format_ratio_value(key, value)
        status_icon = _STATUS_FA.get(status, "?")
        status_style = _STATUS_STYLE.get(status, "")
        scored_marker = " ★" if key in scored_keys else ""

        ratio_table.add_row(
            f"[{cat_style}]{cat_fa}[/{cat_style}]",
            f"{name}{scored_marker}",
            value_str,
            f"[{status_style}]{status_icon}[/{status_style}]",
            formula,
        )

    console.print(ratio_table)

    # ─── دلایل (امتیازدهی‌شده) ───
    reasons = details.get("reasons", [])
    if reasons:
        console.print("\n[bold]دلایل امتیازدهی:[/bold]")
        for r in reasons:
            console.print(f"  • {r}")

    # ─── آمار ───
    scored_count = len(details.get("scored_ratio_keys", []))
    unavailable_count = len(details.get("unavailable_ratio_keys", []))
    not_meaningful_count = len(details.get("not_meaningful_ratio_keys", []))

    console.print(
        f"\n[dim]نسبت‌های امتیازدهی‌شده: {scored_count}/۱۹  |  "
        f"ناموجود: {unavailable_count}  |  "
        f"بدون معنا: {not_meaningful_count}  |  "
        f"اطلاعاتی: {19 - scored_count}/۱۹"
        f"[/dim]"
    )
    console.print()


def render_full_analysis(
    rec: Recommendation,
    fundamental_section: SectionScore | None = None,
    console: Console | None = None,
) -> None:
    """
    تحلیل کامل نماد را نمایش می‌دهد: پیشنهاد معاملاتی + تحلیل بنیادی.

    Args:
        rec: پیشنهاد نهایی از پایپ‌لاین.
        fundamental_section: خروجی تحلیل بنیادی (اختیاری).
        console: کنسول rich (اختیاری).
    """
    console = console or Console()

    render_recommendation(rec, console)

    if fundamental_section is not None:
        render_fundamental_analysis(
            fundamental_section, symbol=rec.symbol, console=console
        )
