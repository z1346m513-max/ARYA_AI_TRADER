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

from arya.models.analysis_result import Action, Recommendation

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
