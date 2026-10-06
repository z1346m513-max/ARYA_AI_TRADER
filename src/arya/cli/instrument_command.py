"""CLI: arya instrument --ticker فولاد"""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from arya.providers.market.instrument_detail import (
    InstrumentDetailError,
    InstrumentDetailProvider,
)
from arya.providers.market.ticker_map import to_tse_symbol


def register_instrument_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "instrument",
        help="صفحه جزئیات نماد (ParTree=151311)",
    )
    p.add_argument(
        "--ticker",
        required=True,
        help="نماد فارسی تابلو، مثلاً فولاد یا فملی",
    )
    p.add_argument(
        "--no-orderbook",
        action="store_true",
        help="بدون صف خرید/فروش",
    )


def _fmt(v: float | None, *, signed: bool = False) -> str:
    if v is None:
        return "—"
    if signed:
        return f"{v:+,.0f}"
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:,.2f}"


def run_instrument(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    ticker = to_tse_symbol(args.ticker)
    try:
        d = InstrumentDetailProvider().fetch(
            ticker, with_orderbook=not args.no_orderbook
        )
    except InstrumentDetailError as exc:
        console.print(f"[red]خطا:[/red] {exc}")
        console.print(
            "[yellow]نکته:[/yellow] نماد را فارسی وارد کنید (فولاد، فملی، شپنا، …)."
        )
        return 1

    header = (
        f"[bold]{d.ticker}[/bold] — {d.name or ''}\n"
        f"بازار: {d.market_title or '—'} | تابلو: {d.board_title or '—'}\n"
        f"صنعت: {d.sector or '—'} | وضعیت: {d.state or '—'}\n"
        f"ISIN: {d.isin or '—'} | InsCode: {d.ins_code}"
    )
    console.print(Panel(header, title="جزئیات نماد (TSETMC)", expand=False))

    price = Table(title="قیمت و معاملات", show_header=True, header_style="bold")
    price.add_column("فیلد")
    price.add_column("مقدار", justify="right")
    for k, v in [
        ("آخرین", _fmt(d.last_price)),
        ("پایانی", _fmt(d.close_price)),
        ("دیروز", _fmt(d.yesterday_price)),
        ("باز", _fmt(d.open_price)),
        ("بیشینه", _fmt(d.high_price)),
        ("کمینه", _fmt(d.low_price)),
        ("تغییر", _fmt(d.price_change, signed=True)),
        ("حجم", _fmt(d.volume)),
        ("ارزش", _fmt(d.value)),
        ("تعداد معاملات", _fmt(d.trade_count)),
        ("حجم مبنا", _fmt(d.base_volume)),
        ("آستانه بالا", _fmt(d.threshold_max)),
        ("آستانه پایین", _fmt(d.threshold_min)),
    ]:
        price.add_row(k, v)
    console.print(price)

    fund = Table(title="بنیادی / ساختار", show_header=True, header_style="bold")
    fund.add_column("فیلد")
    fund.add_column("مقدار", justify="right")
    for k, v in [
        ("تعداد سهام", _fmt(d.total_shares)),
        ("شناوری %", _fmt(d.free_float_pct)),
        ("EPS", _fmt(d.eps)),
        ("P/E", _fmt(d.pe)),
        ("P/E گروه", _fmt(d.sector_pe)),
        ("PSR", _fmt(d.psr)),
        ("کمینه هفته", _fmt(d.min_week)),
        ("بیشینه هفته", _fmt(d.max_week)),
        ("کمینه سال", _fmt(d.min_year)),
        ("بیشینه سال", _fmt(d.max_year)),
    ]:
        fund.add_row(k, v)
    console.print(fund)

    if d.best_limits:
        ob = Table(title="صف (BestLimits)", show_header=True, header_style="bold")
        ob.add_column("#")
        for col in ("تقاضا تعداد", "تقاضا حجم", "تقاضا قیمت", "عرضه قیمت", "عرضه حجم", "عرضه تعداد"):
            ob.add_column(col, justify="right")
        for i, row in enumerate(d.best_limits[:5], 1):
            ob.add_row(
                str(i),
                str(row.get("zOrdMeDem") or "—"),
                str(row.get("qTitMeDem") or "—"),
                str(row.get("pMeDem") or "—"),
                str(row.get("pMeOf") or "—"),
                str(row.get("qTitMeOf") or "—"),
                str(row.get("zOrdMeOf") or "—"),
            )
        console.print(ob)

    if d.page_url_old:
        console.print(f"[dim]صفحه قدیم: {d.page_url_old}[/dim]")
    if d.page_url_new:
        console.print(f"[dim]صفحه جدید: {d.page_url_new}[/dim]")
    return 0
