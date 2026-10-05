"""
CLI نسخه فقط بورس ایران.

نمونه:
    arya analyze --ticker FOOLAD
    arya list-symbols
    arya scan
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console

from arya.app.bootstrap import AryaApp
from arya.dashboard.console_dashboard import render_recommendation

DEFAULT_MARKET = "stock"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arya",
        description="ARYA AI Trader — تحلیل بورس ایران",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="تحلیل یک نماد بورسی")
    analyze_p.add_argument("--ticker", required=True, help="نماد، مثلا FOOLAD")
    analyze_p.add_argument("--timeframe", default="1d", help="تایم‌فریم (پیش‌فرض 1d)")
    analyze_p.add_argument(
        "--force-refresh",
        action="store_true",
        help="نادیده گرفتن کش و دریافت مجدد",
    )

    sub.add_parser("list-symbols", help="لیست نمادهای در دسترس (Mock یا Provider فعال)")

    scan_p = sub.add_parser("scan", help="تحلیل تمام نمادهای لیست Provider")
    scan_p.add_argument("--timeframe", default="1d")
    scan_p.add_argument("--force-refresh", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()
    app = AryaApp()

    if args.command == "analyze":
        kwargs = dict(
            ticker=args.ticker,
            market=DEFAULT_MARKET,
            timeframe=args.timeframe,
        )
        try:
            rec = app.analyze_symbol(**kwargs, force_refresh=args.force_refresh)
        except TypeError:
            rec = app.analyze_symbol(**kwargs)
        render_recommendation(rec, console)

    elif args.command == "list-symbols":
        symbols = app.list_symbols(market=DEFAULT_MARKET)
        console.print("[bold]نمادهای بورس ایران (Provider فعال)[/bold]")
        for s in symbols:
            industry = getattr(s, "industry", None) or "—"
            name = s.name or ""
            console.print(f"  {s.ticker:12}  {name:30}  {industry}")

    elif args.command == "scan":
        symbols = app.list_symbols(market=DEFAULT_MARKET)
        for s in symbols:
            try:
                rec = app.analyze_symbol(
                    s.ticker,
                    market=DEFAULT_MARKET,
                    timeframe=args.timeframe,
                    force_refresh=args.force_refresh,
                )
            except TypeError:
                rec = app.analyze_symbol(
                    s.ticker, market=DEFAULT_MARKET, timeframe=args.timeframe
                )
            render_recommendation(rec, console)

    return 0


if __name__ == "__main__":
    sys.exit(main())
