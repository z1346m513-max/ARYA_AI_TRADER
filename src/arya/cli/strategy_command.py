"""
CLI استراتژی قابل‌تنظیم و اسکن بازار.

arya strategy list
arya strategy show --profile momentum_volume
arya strategy scan --profile trend_rsi_balanced --limit 30
arya strategy test --ticker فولاد --profile rsi_oversold_bounce
"""
from __future__ import annotations

import argparse
import logging

from rich.console import Console
from rich.table import Table

from arya.app.bootstrap import AryaApp
from arya.models.market_data import Symbol
from arya.providers.market.ticker_map import SAMPLE_PERSIAN_TICKERS, to_tse_symbol
from arya.technical.strategies.rule_engine import evaluate_profile
from arya.technical.strategies.strategy_loader import get_profile, list_profiles, load_strategies

logger = logging.getLogger(__name__)


def register_strategy_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("strategy", help="استراتژی اندیکاتوری قابل‌تنظیم + اسکن")
    sp = p.add_subparsers(dest="strategy_cmd", required=True)

    sp.add_parser("list", help="لیست پروفایل‌های configs/strategies.yaml")

    show = sp.add_parser("show", help="نمایش قوانین و اعداد یک پروفایل")
    show.add_argument("--profile", default=None)

    test = sp.add_parser("test", help="تست استراتژی روی یک نماد")
    test.add_argument("--ticker", required=True)
    test.add_argument("--profile", default=None)
    test.add_argument("--force-refresh", action="store_true")

    scan = sp.add_parser("scan", help="اسکن نمادها و استخراج مطابق استراتژی")
    scan.add_argument("--profile", default=None)
    scan.add_argument("--limit", type=int, default=40, help="حداکثر نماد برای بررسی")
    scan.add_argument("--only-pass", action="store_true", default=True)
    scan.add_argument("--all", dest="only_pass", action="store_false")
    scan.add_argument("--from-master", action="store_true")
    scan.add_argument("--industry", default=None)
    scan.add_argument("--force-refresh", action="store_true")


def _universe(app: AryaApp, args: argparse.Namespace) -> list[str]:
    tickers: list[str] = []
    if args.from_master or args.industry:
        symbols = app.list_symbols_master(industry=args.industry)
        tickers = [s.ticker for s in symbols]
    else:
        try:
            symbols = app.list_symbols(market="stock")
            tickers = [s.ticker for s in symbols]
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_symbols ناموفق: %s — از نمونه فارسی استفاده می‌شود", exc)
            tickers = []
    if not tickers:
        tickers = list(SAMPLE_PERSIAN_TICKERS)
    # یکتا + نرمال فارسی
    seen: set[str] = set()
    out: list[str] = []
    for t in tickers:
        p = to_tse_symbol(t)
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    limit = getattr(args, "limit", 0) or 0
    if limit > 0:
        out = out[:limit]
    return out


def run_strategy(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()

    if args.strategy_cmd == "list":
        rows = list_profiles()
        if not rows:
            console.print("[red]هیچ پروفایلی در configs/strategies.yaml نیست[/red]")
            return 1
        table = Table(title="پروفایل‌های استراتژی", show_header=True, header_style="bold")
        table.add_column("نام")
        table.add_column("توضیح")
        default = load_strategies().get("default_profile")
        for name, desc in rows:
            mark = " *" if name == default else ""
            table.add_row(name + mark, desc)
        console.print(table)
        console.print("[dim]* = default_profile — اعداد را در configs/strategies.yaml ویرایش کنید[/dim]")
        return 0

    if args.strategy_cmd == "show":
        name, prof = get_profile(args.profile)
        console.print(f"[bold]{name}[/bold] — {prof.get('description', '')}")
        console.print(f"حداقل کندل: {prof.get('min_candles')} | عمل در صورت عبور: {prof.get('action_when_pass')}")
        table = Table(show_header=True, header_style="bold")
        table.add_column("id")
        table.add_column("type")
        table.add_column("پارامترها")
        for rule in prof.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            params = {k: v for k, v in rule.items() if k not in {"id", "type"}}
            table.add_row(str(rule.get("id")), str(rule.get("type")), str(params))
        console.print(table)
        return 0

    app = AryaApp()
    name, prof = get_profile(args.profile)

    if args.strategy_cmd == "test":
        ticker = to_tse_symbol(args.ticker)
        series, _ = app._fetch_series(
            Symbol(ticker=ticker, market="stock"),
            "1d",
            force_refresh=args.force_refresh,
        )
        match = evaluate_profile(series.to_dataframe(), name, prof)
        status = "[green]PASS[/green]" if match.passed else "[yellow]FAIL[/yellow]"
        console.print(f"{ticker} | پروفایل={name} | {status} | action={match.action} | score={match.score}")
        for r in match.reasons:
            console.print(f"  • {r}")
        return 0

    if args.strategy_cmd == "scan":
        universe = _universe(app, args)
        console.print(
            f"اسکن [bold]{name}[/bold] روی {len(universe)} نماد — فقط PASS={args.only_pass}"
        )
        table = Table(show_header=True, header_style="bold")
        table.add_column("نماد")
        table.add_column("نتیجه")
        table.add_column("عمل")
        table.add_column("امتیاز", justify="right")
        table.add_column("جزئیات")

        passed_n = 0
        for ticker in universe:
            try:
                series, _ = app._fetch_series(
                    Symbol(ticker=ticker, market="stock"),
                    "1d",
                    force_refresh=args.force_refresh,
                    limit=120,
                )
                match = evaluate_profile(series.to_dataframe(), name, prof)
            except Exception as exc:  # noqa: BLE001
                if not args.only_pass:
                    table.add_row(ticker, "ERROR", "—", "—", str(exc)[:40])
                continue
            if args.only_pass and not match.passed:
                continue
            if match.passed:
                passed_n += 1
            table.add_row(
                ticker,
                "PASS" if match.passed else "fail",
                match.action,
                f"{match.score:.2f}",
                " | ".join(match.reasons)[:80],
            )

        console.print(table)
        console.print(f"[bold]تعداد مطابق استراتژی: {passed_n}[/bold]")
        console.print(
            "[dim]تنظیم اعداد: فایل configs/strategies.yaml را ویرایش کنید[/dim]"
        )
        return 0

    return 1
