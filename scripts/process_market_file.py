#!/usr/bin/env python3
"""
اسکریپت CLI پردازش فایل بازار.

اجرا:
    python scripts/process_market_file.py --input data/inbox/market/market_2026-10-06.xlsx
    python scripts/process_market_file.py --input data/inbox/market/market_2026-10-06.xlsx --format jsonl
    python scripts/process_market_file.py --inbox   # پردازش تمام فایل‌های inbox

این اسکریپت صرفاً تحقیقاتی و read-only است:
به صرافی یا API وصل نمی‌شود و سفارش ثبت نمی‌کند.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# اضافه کردن src به مسیر
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arya.data_ingestion import IngestionPipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="پردازش فایل Excel/CSV بازار - اعتبارسنجی و نرمال‌سازی"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input",
        type=str,
        help="مسیر فایل Excel/CSV بازار",
    )
    group.add_argument(
        "--inbox",
        action="store_true",
        help="پردازش تمام فایل‌های موجود در data/inbox/market/",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "jsonl"],
        default="csv",
        help="فرمت خروجی نرمال‌شده (پیش‌فرض: csv)",
    )
    parser.add_argument(
        "--source",
        default="manual_upload",
        help="منبع فایل (manual_upload, api, drive_sync)",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="فایل اصلی را به archive منتقل نکن",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="خروجی به‌صورت JSON کامل",
    )

    args = parser.parse_args()

    pipeline = IngestionPipeline()

    if args.inbox:
        print("پردازش تمام فایل‌های inbox...")
        results = pipeline.process_inbox(source=args.source)
        if not results:
            print("هیچ فایلی در inbox پیدا نشد.")
            return 0

        if args.json:
            output = [r.to_dict() for r in results]
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            for r in results:
                _print_result(r)
        return 0 if all(r.success for r in results) else 1

    file_path = Path(args.input)
    result = pipeline.process_file(
        file_path,
        source=args.source,
        output_format=args.format,
        archive_original=not args.no_archive,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_result(result)

    return 0 if result.success else 1


def _print_result(result) -> None:
    """نتیجه‌ی پردازش را در ترمینال نمایش می‌دهد."""
    if result.error and not result.manifest:
        print(f"خطا: {result.error}")
        return

    m = result.manifest
    v = result.validation

    print(f"\n{'=' * 60}")
    print(f"فایل: {m.file_name}")
    print(f"SHA-256: {m.sha256[:16]}...")
    print(f"وضعیت: {m.validation_status}")
    print(f"ردیف‌ها: {v.total_rows if v else 0}")
    print(f"نمادها: {v.symbols if v else 0}")
    if v and v.date_min:
        print(f"بازه‌ی زمانی: {v.date_min} تا {v.date_max}")
    if v and v.errors:
        print(f"\nخطاها ({len(v.errors)}):")
        for e in v.errors:
            print(f"  - {e}")
    if v and v.warnings:
        print(f"\nهشدارها ({len(v.warnings)}):")
        for w in v.warnings:
            print(f"  - {w}")
    if m.normalized_path:
        print(f"\nفایل نرمال‌شده: {m.normalized_path}")
    print(f"manifest ذخیره شد.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    sys.exit(main())
