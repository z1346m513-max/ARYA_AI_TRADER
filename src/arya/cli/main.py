"""
CLI ورودی برنامه.

نمونه استفاده:
    arya analyze --ticker FOOLAD --market stock
    arya list-symbols --market crypto
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console

from arya.app.bootstrap import AryaApp
from arya.dashboard.console_dashboard import render_recommendation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arya", description="ARYA AI Trader CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="تحلیل یک نماد و نمایش پیشنهاد")
    analyze_p.add_argument("--ticker", required=True, help="نماد، مثلا FOOLAD یا BTCUSDT")
    analyze_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])
    analyze_p.add_argument("--timeframe", default="1d")
    analyze_p.add_argument(
        "--profile",
        default=None,
        choices=["balanced", "conservative", "momentum", "trend_following"],
        help="پروفایل پارامترهای تحلیل",
    )

    list_p = sub.add_parser("list-symbols", help="لیست نمادهای موجود در یک بازار")
    list_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])

    scan_p = sub.add_parser("scan", help="تحلیل تمام نمادهای یک بازار")
    scan_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])

    sub.add_parser("gui", help="اجرای رابط گرافیکی فارسی ARYA")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    if args.command == "gui":
        try:
            from arya.ui.app import main as gui_main
        except ImportError as exc:
            console.print(
                '[bold red]رابط گرافیکی نصب نیست.[/bold red] '
                '[bold]وابستگی GUI را با uv pip install --python .venv\\Scripts\\python.exe -e ".[gui]" نصب کنید.[/bold]'
            )
            console.print(f"جزئیات: {exc}")
            return 2
        return gui_main()

    app = AryaApp()
    language = app.settings.app.get("app", {}).get("language", "fa")

    if args.command == "analyze":
        analysis_settings = app.settings.for_analysis(profile_name=args.profile)
        rec = app.analyze_symbol(
            args.ticker,
            market=args.market,
            timeframe=args.timeframe,
            analysis_settings=analysis_settings,
        )
        render_recommendation(rec, console, language=language)

    elif args.command == "list-symbols":
        symbols = app.list_symbols(market=args.market)
        for s in symbols:
            console.print(f"  {s.ticker}  ({s.name})")

    elif args.command == "scan":
        symbols = app.list_symbols(market=args.market)
        for s in symbols:
            rec = app.analyze_symbol(s.ticker, market=args.market)
            render_recommendation(rec, console, language=language)

    return 0


if __name__ == "__main__":
    sys.exit(main())
