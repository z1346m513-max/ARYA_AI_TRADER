"""CLI کدال: general | افزایش سرمایه | تغییرات مدیران"""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from arya.providers.codal import CodalProvider, CodalProviderError
from arya.providers.codal.events import (
    filter_board_changes,
    filter_capital_increase,
)
from arya.providers.codal.symbol_map import to_codal_symbol


def register_codal_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("codal", help="اطلاعیه‌های کدال (افزایش سرمایه / مدیران)")
    p.add_argument("--symbol", required=True, help="نماد (فارسی یا لاتین)")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--page", type=int, default=1)
    p.add_argument(
        "--event",
        choices=["all", "capital", "board"],
        default="all",
        help="all | capital=افزایش سرمایه | board=تغییرات مدیران",
    )
    p.add_argument(
        "--pages",
        type=int,
        default=1,
        help="تعداد صفحات جست‌وجو قبل از فیلتر (حداکثر ۳)",
    )


def run_codal(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    provider = CodalProvider()
    symbol = to_codal_symbol(args.symbol)

    try:
        collected = []
        total = 0
        pages = max(1, min(args.pages, 3))
        for page in range(1, pages + 1):
            letters, total = provider.search_letters(symbol, page=page, length=50)
            collected.extend(letters)
            if page * 50 >= total:
                break
    except CodalProviderError as exc:
        console.print(f"[red]خطای کدال:[/red] {exc}")
        console.print(
            "[yellow]نکته:[/yellow] کدال معمولاً فقط از داخل ایران در دسترس است."
        )
        return 1

    if args.event == "capital":
        letters = filter_capital_increase(collected)
        label = "افزایش سرمایه / حق تقدم"
    elif args.event == "board":
        letters = filter_board_changes(collected)
        label = "تغییرات مدیران / هیئت مدیره"
    else:
        letters = collected
        label = "همه اطلاعیه‌ها"

    letters = letters[: max(1, args.limit)]
    console.print(
        f"[bold]کدال — {symbol}[/bold]  [{label}]  "
        f"(کل منبع≈{total} | فیلتر شده: {len(letters)})"
    )
    table = Table(show_header=True, header_style="bold")
    table.add_column("TracingNo", style="cyan")
    table.add_column("تاریخ")
    table.add_column("عنوان")
    for letter in letters:
        table.add_row(
            letter.tracing_no,
            (letter.publish_datetime or letter.sent_datetime or "—")[:16],
            (letter.title or "")[:90],
        )
    console.print(table)
    return 0
