"""
CLI — بورس ایران + کدال + Cache-First.

نمونه:
    arya analyze --ticker FOOLAD
    arya analyze --ticker FOOLAD --force-refresh
    arya list-symbols
    arya scan
    arya codal --symbol فولاد --limit 5
    arya cache-stats
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console

from arya.app.bootstrap import AryaApp
from arya.dashboard.console_dashboard import render_recommendation
from arya.cli.codal_command import register_codal_parser, run_codal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arya", description="ARYA AI Trader — بورس ایران و کدال"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="تحلیل یک نماد بورسی")
    analyze_p.add_argument("--ticker", required=True, help="نماد، مثلا FOOLAD")
    analyze_p.add_argument("--market", default="stock", choices=["stock"])
    analyze_p.add_argument("--timeframe", default="1d")
    analyze_p.add_argument(
        "--force-refresh", action="store_true", help="نادیده گرفتن کش"
    )

    list_p = sub.add_parser("list-symbols", help="لیست نمادها")
    list_p.add_argument("--market", default="stock", choices=["stock"])

    scan_p = sub.add_parser("scan", help="اسکن نمادهای Provider")
    scan_p.add_argument("--market", default="stock", choices=["stock"])
    scan_p.add_argument("--timeframe", default="1d")
    scan_p.add_argument("--force-refresh", action="store_true")

    sub.add_parser("cache-stats", help="نمایش hit-ratio کش")

    register_codal_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    if args.command == "codal":
        return run_codal(args, console)

    app = AryaApp()

    if args.command == "analyze":
        rec = app.analyze_symbol(
            args.ticker,
            market=args.market,
            timeframe=args.timeframe,
            force_refresh=args.force_refresh,
        )
        render_recommendation(rec, console)

    elif args.command == "list-symbols":
        for s in app.list_symbols(market=args.market):
            console.print(f"  {s.ticker}  ({s.name})")

    elif args.command == "scan":
        for s in app.list_symbols(market=args.market):
            rec = app.analyze_symbol(
                s.ticker,
                market=args.market,
                timeframe=args.timeframe,
                force_refresh=args.force_refresh,
            )
            render_recommendation(rec, console)
        snap = app.cache_stats()
        console.print(
            f"[dim]cache hit_ratio={snap.hit_ratio:.1%} hits={snap.hits} "
            f"misses={snap.misses} stale={snap.stale}[/dim]"
        )

    elif args.command == "cache-stats":
        snap = app.cache_stats()
        console.print(
            f"hit_ratio={snap.hit_ratio:.1%}  hits={snap.hits}  "
            f"misses={snap.misses}  stale={snap.stale}  saves={snap.saves}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
