"""
CLI — بورس ایران.

نمونه:
    arya instrument --ticker فولاد
    arya analyze --ticker FOOLAD
    arya codal --symbol فولاد --event capital
    arya client-type --ticker فولاد
    arya shareholders --changes
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console

from arya.app.bootstrap import AryaApp
from arya.dashboard.console_dashboard import render_recommendation
from arya.cli.codal_command import register_codal_parser, run_codal
from arya.cli.shareholder_command import register_shareholder_parser, run_shareholders
from arya.cli.client_type_command import register_client_type_parser, run_client_type
from arya.cli.instrument_command import register_instrument_parser, run_instrument


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arya", description="ARYA AI Trader — بورس ایران"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="تحلیل یک نماد بورسی")
    analyze_p.add_argument("--ticker", required=True)
    analyze_p.add_argument("--market", default="stock", choices=["stock"])
    analyze_p.add_argument("--timeframe", default="1d")
    analyze_p.add_argument("--force-refresh", action="store_true")

    list_p = sub.add_parser("list-symbols", help="لیست نمادها")
    list_p.add_argument("--market", default="stock", choices=["stock"])
    list_p.add_argument("--industry", default=None)
    list_p.add_argument("--from-master", action="store_true")

    sub.add_parser("list-industries", help="لیست صنایع")

    scan_p = sub.add_parser("scan", help="اسکن نمادها")
    scan_p.add_argument("--market", default="stock", choices=["stock"])
    scan_p.add_argument("--timeframe", default="1d")
    scan_p.add_argument("--force-refresh", action="store_true")
    scan_p.add_argument("--industry", default=None)
    scan_p.add_argument("--limit", type=int, default=0)

    sub.add_parser("cache-stats", help="hit-ratio کش")

    register_codal_parser(sub)
    register_shareholder_parser(sub)
    register_client_type_parser(sub)
    register_instrument_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    if args.command == "codal":
        return run_codal(args, console)
    if args.command == "shareholders":
        return run_shareholders(args, console)
    if args.command == "client-type":
        return run_client_type(args, console)
    if args.command == "instrument":
        return run_instrument(args, console)

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
        if args.industry or args.from_master:
            symbols = app.list_symbols_master(industry=args.industry)
        else:
            symbols = app.list_symbols(market=args.market)
        console.print(f"[bold]تعداد: {len(symbols)}[/bold]")
        for s in symbols:
            ind = getattr(s, "industry", None) or "—"
            console.print(f"  {s.ticker:12}  {(s.name or ''):28}  {ind}")

    elif args.command == "list-industries":
        for name, count in app.list_industries():
            console.print(f"  {count:4d}  {name}")

    elif args.command == "scan":
        if args.industry:
            symbols = app.list_symbols_master(industry=args.industry)
        else:
            symbols = app.list_symbols(market=args.market)
        if args.limit and args.limit > 0:
            symbols = symbols[: args.limit]
        for s in symbols:
            try:
                rec = app.analyze_symbol(
                    s.ticker,
                    market=args.market,
                    timeframe=args.timeframe,
                    force_refresh=args.force_refresh,
                )
                render_recommendation(rec, console)
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]{s.ticker}: {exc}[/red]")
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
