"""CLI ورود دستی کدال + اعلام نیازهای اطلاعاتی."""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from arya.providers.codal.manual_store import ManualCodalEvent, ManualCodalStore
from arya.providers.codal.requirements import CODAL_REQUIREMENTS, format_checklist
from arya.providers.market.ticker_map import to_tse_symbol


def register_manual_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "manual",
        help="ورود دستی اطلاعات کدال + چک‌لیست گزارش‌های موردنیاز",
    )
    sp = p.add_subparsers(dest="manual_cmd", required=True)

    need = sp.add_parser("needs", help="لیست اطلاعات/گزارش‌هایی که از کدال لازم است")
    need.add_argument("--ticker", default=None, help="نماد فارسی (اختیاری)")

    add = sp.add_parser("add", help="ثبت یک اطلاعیه استخراج‌شده دستی")
    add.add_argument("--ticker", required=True, help="نماد فارسی")
    add.add_argument(
        "--event",
        required=True,
        choices=["capital", "board", "assembly", "disclosure", "other"],
        help="نوع رویداد",
    )
    add.add_argument("--title", required=True, help="عنوان دقیق اطلاعیه از کدال")
    add.add_argument("--date", default=None, help="تاریخ انتشار YYYY-MM-DD یا شمسی متنی")
    add.add_argument("--notes", default=None, help="یادداشت اختیاری")

    lst = sp.add_parser("list", help="نمایش رویدادهای دستی ثبت‌شده")
    lst.add_argument("--ticker", default=None)

    clr = sp.add_parser("clear", help="حذف رویدادهای دستی یک نماد")
    clr.add_argument("--ticker", required=True)


def run_manual(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    store = ManualCodalStore()

    if args.manual_cmd == "needs":
        ticker = to_tse_symbol(args.ticker) if args.ticker else None
        console.print(format_checklist(ticker))
        table = Table(title="خلاصه اولویت‌ها", show_header=True, header_style="bold")
        table.add_column("اولویت")
        table.add_column("عنوان")
        table.add_column("--event")
        for r in CODAL_REQUIREMENTS:
            table.add_row(r.priority, r.title_fa, r.event_type)
        console.print(table)
        if ticker:
            console.print(
                f"\n[dim]بعد از کپی از کدال:[/dim]\n"
                f'  python -m arya.cli.main manual add --ticker {ticker} '
                f'--event capital --title "..." --date 2025-01-01'
            )
        return 0

    if args.manual_cmd == "add":
        # اگر عنوان بدون کلیدواژه نوع باشد، پیشوند کمکی اضافه کن
        title = args.title.strip()
        prefixes = {
            "capital": "افزایش سرمایه",
            "board": "تغییرات مدیران",
            "assembly": "مجمع",
            "disclosure": "شفاف سازی",
        }
        pref = prefixes.get(args.event)
        if pref and pref not in title:
            title = f"{pref} — {title}"

        ev = store.add(
            ManualCodalEvent(
                ticker=args.ticker,
                title=title,
                event_type=args.event,
                publish_date=args.date,
                notes=args.notes,
            )
        )
        console.print(
            f"[green]ثبت شد[/green]: {ev.ticker} | {ev.event_type} | {ev.title[:70]}"
        )
        console.print(f"[dim]فایل: {store.path}[/dim]")
        console.print(
            f"حالا: python -m arya.cli.main analyze --ticker {ev.ticker}"
        )
        return 0

    if args.manual_cmd == "list":
        events = store.list_events(args.ticker)
        if not events:
            console.print("[yellow]رویداد دستی‌ای ثبت نشده.[/yellow]")
            console.print("ابتدا: python -m arya.cli.main manual needs")
            return 0
        table = Table(show_header=True, header_style="bold")
        table.add_column("نماد")
        table.add_column("نوع")
        table.add_column("تاریخ")
        table.add_column("عنوان")
        for e in events:
            table.add_row(
                e.ticker,
                e.event_type,
                e.publish_date or "—",
                (e.title or "")[:60],
            )
        console.print(table)
        return 0

    if args.manual_cmd == "clear":
        n = store.clear_ticker(args.ticker)
        console.print(f"حذف شد: {n} رکورد برای {to_tse_symbol(args.ticker)}")
        return 0

    return 1
