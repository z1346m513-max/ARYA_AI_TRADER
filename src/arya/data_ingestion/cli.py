"""One-shot CLI for manual files or an already-synchronized local inbox."""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

from arya.data_ingestion.pipeline import MARKETS, IngestionContext, IngestionError, ingest_file


def add_arguments(parser: argparse.ArgumentParser) -> None:
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--file", type=Path, help="CSV or XLSX with ohlcv sheet")
    inputs.add_argument("--inbox", type=Path, help="Scan local folder once; no cloud access")
    parser.add_argument("--market", choices=MARKETS, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--venue", required=True)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--volume-unit", choices=["shares", "base_asset", "ticks"], required=True)
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--max-age-hours", type=float, default=None)
    parser.add_argument("--root", type=Path, default=Path("data/market_pipeline"))
    parser.add_argument("--settle-seconds", type=float, default=30, help="Minimum file age for inbox scan")


def run(args: argparse.Namespace) -> int:
    results, failed = [], False
    try:
        context = IngestionContext(
            args.market, args.source, args.venue, args.currency,
            args.volume_unit, args.timeframe, args.max_age_hours,
        )
        if not math.isfinite(args.settle_seconds) or args.settle_seconds < 0:
            raise IngestionError("settle-seconds must be finite and non-negative")
        if args.inbox is not None and not args.inbox.is_dir():
            raise IngestionError("inbox directory does not exist")
        files = [args.file] if args.file is not None else sorted(
            p for p in args.inbox.iterdir()
            if p.is_file() and not p.is_symlink() and p.suffix.lower() in {".csv", ".xlsx"}
            and not p.name.startswith(("~$", "."))
            and time.time() - p.stat().st_mtime >= args.settle_seconds
        )
        for path in files:
            try:
                results.append(ingest_file(path, args.root, context))
            except (IngestionError, OSError, ValueError) as exc:
                failed = True
                results.append({"file_name": path.name, "status": "ERROR", "error": str(exc)})
    except (IngestionError, OSError) as exc:
        failed = True
        results.append({"status": "ERROR", "error": str(exc)})
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2, allow_nan=False))
    return 2 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    return run(parser.parse_args(argv))
