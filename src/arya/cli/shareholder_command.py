"""CLI: arya shareholders --changes | arya shareholders --ticker فولاد"""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from arya.providers.market.shareholder_provider import (
    ShareholderProvider,
    ShareholderProviderError,
)


def register_shareholder_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "shareholders",
        help="تغییرات سهامداران عمده (TSETMC ShareHolderChanges)",
    )
    p.add_argument(
        "--changes",
        action="store_true",
        help="لیست تغییرات اخیر کل بازار (معادل ShareHolderChanges)",
    )
    p.add_argument(
        "--only-increase",
        action="store_true",
        help="فقط افزایش مالکیت",
    )
    p.add_argument("--ticker", default=None, help="آخرین سهامداران یک نماد")
    p.add_argument("--limit", type=int, default=20)


def run_shareholders(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    provider = ShareholderProvider()

    try:
        if args.ticker:
            holders = provider.fetch_holders(args.ticker)
            console.print(f"[bold]سهامداران عمده — {args.ticker}[/bold]  ({len(holders)})")
            table = Table(show_header=True, header_style="bold")
            table.add_column("نام")
            table.add_column("تعداد سهام", justify="right")
            table.add_column("درصد", justify="right")
            table.add_column("تغییر", justify="right")
            for h in holders[: max(1, args.limit)]:
                table.add_row(
                    (h.name or "—")[:40],
                    f"{h.shares:,.0f}" if h.shares is not None else "—",
                    f"{h.percent:.2f}" if h.percent is not None else "—",
                    f"{h.change:,.0f}" if h.change is not None else "—",
                )
            console.print(table)
            return 0

        # پیش‌فرض: تغییرات بازار
        changes = provider.fetch_changes(only_increase=args.only_increase)
        console.print(
            f"[bold]تغییرات سهامداران عمده[/bold]  "
            f"(منبع: ShareHolderChanges | تعداد: {len(changes)})"
        )
        table = Table(show_header=True, header_style="bold")
        table.add_column("نماد")
        table.add_column("سهامدار")
        table.add_column("تغییر سهام", justify="right")
        table.add_column("تاریخ")
        for c in changes[: max(1, args.limit)]:
            ch = c.shares_change
            ch_s = f"{ch:+,.0f}" if ch is not None else "—"
            table.add_row(
                c.symbol or "—",
                (c.holder_name or "—")[:32],
                ch_s,
                c.date or "—",
            )
        console.print(table)
        console.print(
            "[dim]صفحات مرجع: main.tsetmc.com/ShareHolderChanges  |  "
            "old.tsetmc.com ParTree=15131I[/dim]"
        )
        return 0

    except ShareholderProviderError as exc:
        console.print(f"[red]خطای سهامداران:[/red] {exc}")
        console.print(
            "[yellow]نکته:[/yellow] CDN تستمک ممکن است از خارج ایران یا بدون IP ایران محدود باشد."
        )
        return 1
