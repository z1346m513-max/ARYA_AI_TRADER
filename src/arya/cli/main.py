"""
CLI ورودی برنامه.

نمونه استفاده:
    arya analyze --ticker FOOLAD --market stock
    arya list-symbols --market crypto
    arya fundamental --ticker FOOLAD --json data/financials/foolad.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console

from arya.app.bootstrap import AryaApp
from arya.dashboard.console_dashboard import (
    render_recommendation,
    render_fundamental_analysis,
    render_full_analysis,
)
from arya.fundamental.models import FinancialData


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arya", description="ARYA AI Trader CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_p = sub.add_parser("analyze", help="تحلیل یک نماد و نمایش پیشنهاد")
    analyze_p.add_argument("--ticker", required=True, help="نماد، مثلا FOOLAD یا BTCUSDT")
    analyze_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])
    analyze_p.add_argument("--timeframe", default="1d")
    analyze_p.add_argument(
        "--financial-data",
        type=str,
        default=None,
        help="مسیر فایل JSON داده‌ی بنیادی (اختیاری)",
    )

    list_p = sub.add_parser("list-symbols", help="لیست نمادهای موجود در یک بازار")
    list_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])

    scan_p = sub.add_parser("scan", help="تحلیل تمام نمادهای یک بازار")
    scan_p.add_argument("--market", default="stock", choices=["stock", "crypto", "forex"])

    fund_p = sub.add_parser("fundamental", help="تحلیل بنیادی ۱۹ نسبت مالی")
    fund_p.add_argument("--ticker", default="", help="نماد (برای عنوان)")
    fund_p.add_argument(
        "--json",
        type=str,
        default=None,
        help="مسیر فایل JSON داده‌ی بنیادی",
    )
    fund_p.add_argument(
        "--market-price",
        type=float,
        default=None,
        help="قیمت بازار هر سهم",
    )
    fund_p.add_argument(
        "--eps",
        type=float,
        default=None,
        help="سود هر سهم",
    )
    fund_p.add_argument(
        "--revenue",
        type=float,
        default=None,
        help="کل فروش",
    )
    fund_p.add_argument(
        "--net-income",
        type=float,
        default=None,
        help="سود خالص",
    )
    fund_p.add_argument(
        "--equity",
        type=float,
        default=None,
        help="حقوق صاحبان سهام",
    )
    fund_p.add_argument(
        "--total-assets",
        type=float,
        default=None,
        help="کل دارایی‌ها",
    )
    fund_p.add_argument(
        "--debt",
        type=float,
        default=None,
        help="کل بدهی",
    )
    fund_p.add_argument(
        "--current-assets",
        type=float,
        default=None,
        help="دارایی جاری",
    )
    fund_p.add_argument(
        "--current-liabilities",
        type=float,
        default=None,
        help="بدهی جاری",
    )
    fund_p.add_argument(
        "--inventory",
        type=float,
        default=None,
        help="موجودی",
    )

    return parser


def _load_financial_data(args: argparse.Namespace) -> FinancialData | None:
    """داده‌ی بنیادی را از JSON یا پارامترهای CLI می‌سازد."""
    if args.json:
        json_path = Path(args.json)
        if not json_path.exists():
            print(f"خطا: فایل پیدا نشد: {json_path}")
            return None
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        return FinancialData(**data)

    # ساخت از پارامترهای خط فرمان
    fields = {}
    for key in [
        "market_price", "eps", "revenue", "net_income",
        "equity", "total_assets", "debt",
        "current_assets", "current_liabilities", "inventory",
    ]:
        val = getattr(args, key, None)
        if val is not None:
            fields[key] = val

    if not fields:
        return None
    return FinancialData(**fields)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console()

    app = AryaApp()

    if args.command == "analyze":
        financial_data = None
        if args.financial_data:
            json_path = Path(args.financial_data)
            if json_path.exists():
                with open(json_path, encoding="utf-8") as f:
                    financial_data = FinancialData(**json.load(f))

        rec = app.analyze_symbol(
            args.ticker,
            market=args.market,
            timeframe=args.timeframe,
            financial_data=financial_data,
        )

        if financial_data is not None:
            fundamental_section = app.analyze_financial_data(financial_data)
            render_full_analysis(rec, fundamental_section, console)
        else:
            render_recommendation(rec, console)

    elif args.command == "list-symbols":
        symbols = app.list_symbols(market=args.market)
        for s in symbols:
            console.print(f"  {s.ticker}  ({s.name})")

    elif args.command == "scan":
        symbols = app.list_symbols(market=args.market)
        for s in symbols:
            rec = app.analyze_symbol(s.ticker, market=args.market)
            render_recommendation(rec, console)

    elif args.command == "fundamental":
        data = _load_financial_data(args)
        if data is None:
            console.print("[bold red]خطا: داده‌ی بنیادی ارائه نشده.[/bold red]")
            console.print(
                "از --json <file> یا پارامترهای --market-price, --eps, ... استفاده کنید."
            )
            return 1

        section = app.analyze_financial_data(data)
        render_fundamental_analysis(section, symbol=args.ticker, console=console)

    return 0


if __name__ == "__main__":
    sys.exit(main())
