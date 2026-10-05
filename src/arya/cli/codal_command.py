"""دستور CLI: arya codal --symbol فولاد"""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from arya.providers.codal import CodalProvider, CodalProviderError


def register_codal_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("codal", help="جست‌وجوی اطلاعیه‌های کدال برای یک نماد")
    p.add_argument("--symbol", required=True, help="نماد کدال (ترجیحاً فارسی، مثلاً فولاد)")
    p.add_argument("--limit", type=int, default=10, help="تعداد نمایش")
    p.add_argument("--page", type=int, default=1)


def run_codal(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    provider = CodalProvider()
    try:
        letters, total = provider.search_letters(args.symbol, page=args.page)
    except CodalProviderError as exc:
        console.print(f"[red]خطای کدال:[/red] {exc}")
        console.print(
            "[yellow]نکته:[/yellow] کدال معمولاً فقط از داخل ایران در دسترس است و rate-limit دارد."
        )
        return 1

    letters = letters[: max(1, args.limit)]
    console.print(f"[bold]کدال — {args.symbol}[/bold]  (کل: {total} | نمایش: {len(letters)})")
    table = Table(show_header=True, header_style="bold")
    table.add_column("TracingNo", style="cyan")
    table.add_column("تاریخ انتشار")
    table.add_column("عنوان")
    for letter in letters:
        table.add_row(
            letter.tracing_no,
            (letter.publish_datetime or letter.sent_datetime or "—")[:16],
            (letter.title or "")[:80],
        )
    console.print(table)
    return 0
