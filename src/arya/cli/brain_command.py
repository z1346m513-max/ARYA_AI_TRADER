"""CLI مغز دوم و پژوهش."""
from __future__ import annotations

import argparse
import json

from rich.console import Console
from rich.table import Table

from arya.agents.orchestrator import Orchestrator
from arya.agents.second_brain import SecondBrain
from arya.providers.market.ticker_map import to_tse_symbol


def register_brain_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("brain", help="مغز دوم — حافظه مرکزی ایجنت‌ها")
    sp = p.add_subparsers(dest="brain_cmd", required=True)

    sp.add_parser("status", help="وضعیت حافظه و مسیر دیسک")

    rec = sp.add_parser("recall", help="بازیابی حافظه برای یک نماد یا کلی")
    rec.add_argument("--ticker", default=None)
    rec.add_argument("--kind", default=None)
    rec.add_argument("--limit", type=int, default=15)

    sp.add_parser("diagram", help="چاپ مسیر مستند دیاگرام معماری")


def register_research_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("research", help="ایجنت جست‌وجو → مغز دوم")
    p.add_argument("--query", default="بورس ایران TSETMC کدال")
    p.add_argument("--online", action="store_true", help="پینگ منابع")


def run_brain(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    brain = SecondBrain()

    if args.brain_cmd == "status":
        st = brain.status()
        console.print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.brain_cmd == "diagram":
        console.print("مستند دیاگرام: docs/ARCHITECTURE_AGENTS.md")
        console.print("مخزن فیزیکی: data/second_brain/")
        return 0

    if args.brain_cmd == "recall":
        ticker = to_tse_symbol(args.ticker) if args.ticker else None
        if ticker and not args.kind:
            summary = brain.categorize_summary(ticker=ticker)
            console.print(json.dumps({"counts": summary["counts"], "generated_at": summary["generated_at"]}, ensure_ascii=False, indent=2))
            return 0
        hits = brain.recall(ticker=ticker, kind=args.kind, limit=args.limit)
        table = Table(show_header=True, header_style="bold")
        table.add_column("زمان")
        table.add_column("ایجنت")
        table.add_column("kind")
        table.add_column("نماد")
        table.add_column("tags")
        for h in hits:
            table.add_row(
                str(h.get("ts", ""))[:19],
                str(h.get("agent")),
                str(h.get("kind")),
                str(h.get("ticker") or "—"),
                ",".join(h.get("tags") or [])[:30],
            )
        console.print(table)
        return 0

    return 1


def run_research(args: argparse.Namespace, console: Console | None = None) -> int:
    console = console or Console()
    orch = Orchestrator()
    result = orch.run_research_cycle(query=args.query, online=args.online)
    console.print("[green]ایجنت پژوهش اجرا شد → مغز دوم[/green]")
    console.print(json.dumps(result, ensure_ascii=False, indent=2))
    console.print("بازیابی: python -m arya.cli.main brain status")
    return 0
