"""Standalone CLI for the optional TradingAgents research bridge."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from arya.ai.agents import (
    TradingAgentsAdapter,
    TradingAgentsIntegrationError,
    TradingAgentsOptions,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an isolated TradingAgents research pass (no ARYA orders)."
    )
    parser.add_argument("--ticker", required=True, help="Yahoo-supported symbol, e.g. AAPL or BTC-USD")
    parser.add_argument("--date", required=True, help="Analysis date in YYYY-MM-DD format")
    parser.add_argument(
        "--asset-class",
        required=True,
        choices=("international_stock", "crypto"),
        help="Use international_stock for Yahoo-listed stocks; crypto for Yahoo crypto pairs.",
    )
    parser.add_argument("--provider", default=None, help="Optional TradingAgents LLM provider")
    parser.add_argument("--language", default="Persian", help="Analyst/report output language")
    parser.add_argument(
        "--analysts",
        default="market,news,fundamentals,social",
        help="Comma-separated analysts: market,news,fundamentals,social",
    )
    parser.add_argument("--data-dir", type=Path, default=None, help="Optional separate data root")
    parser.add_argument("--no-report", action="store_true", help="Do not persist the report tree")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        options = TradingAgentsOptions(
            selected_analysts=tuple(
                item.strip() for item in args.analysts.split(",") if item.strip()
            ),
            output_language=args.language,
            llm_provider=args.provider,
            data_dir=args.data_dir,
            save_report=not args.no_report,
        )
        result = TradingAgentsAdapter(options).analyze(
            args.ticker,
            args.date,
            asset_class=args.asset_class,
        )
    except (TradingAgentsIntegrationError, TypeError, ValueError) as exc:
        print(f"TradingAgents research failed: {exc}", file=sys.stderr)
        return 2

    payload = {
        "ticker": result.ticker,
        "trade_date": result.trade_date,
        "asset_class": result.asset_class,
        "rating": result.rating,
        "requires_review": result.requires_review,
        "framework_version": result.framework_version,
        "report_path": str(result.report_path) if result.report_path else None,
        "note": "Research output only; not an ARYA recommendation or order authorization.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
