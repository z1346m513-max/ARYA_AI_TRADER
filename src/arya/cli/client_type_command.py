"""CLI: arya client-type --ticker فولاد"""
from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

from arya.providers.market.client_type_provider import (
    ClientTypeProvider,
    ClientTypeProviderError,
)


def register_client_type_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("client-type", help="حقیقی/حقوقی یک نماد (TSETMC ClientType)")
    p.add_argument("--ticker", required=True)


def run_client_type(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    try:
        snap = ClientTypeProvider().fetch_latest(args.ticker)
    except ClientTypeProviderError as exc:
        console.print(f"[red]خطا:[/red] {exc}")
        return 1

    table = Table(title=f"حقیقی/حقوقی — {snap.ticker}", show_header=True)
    table.add_column("")
    table.add_column("حقیقی", justify="right")
    table.add_column("حقوقی", justify="right")
    table.add_row(
        "خرید (حجم)",
        f"{snap.buy_individual_volume:,.0f}" if snap.buy_individual_volume else "—",
        f"{snap.buy_institutional_volume:,.0f}" if snap.buy_institutional_volume else "—",
    )
    table.add_row(
        "فروش (حجم)",
        f"{snap.sell_individual_volume:,.0f}" if snap.sell_individual_volume else "—",
        f"{snap.sell_institutional_volume:,.0f}" if snap.sell_institutional_volume else "—",
    )
    table.add_row(
        "خالص",
        f"{snap.net_individual_volume:+,.0f}" if snap.net_individual_volume is not None else "—",
        f"{snap.net_institutional_volume:+,.0f}"
        if snap.net_institutional_volume is not None
        else "—",
    )
    console.print(table)
    console.print(f"[dim]insCode={snap.ins_code}[/dim]")
    return 0
