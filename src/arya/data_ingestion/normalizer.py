"""
نرمال‌سازی داده‌ی بازار.

داده‌ی خام اعتبارسنجی‌شده را به یک فرمت استاندارد و تغییرناپذیر تبدیل می‌کند:
- timestamp به UTC timezone-aware
- مرتب‌سازی بر اساس (symbol, timestamp)
- حذف ردیف‌های تکراری (timestamp, symbol)
- اضافه کردن ستون‌های اختیاری اگر وجود ندارند
- ذخیره به‌صورت CSV یا JSONL

خروجی: NormalizedMarketData شامل DataFrame و آمار
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from arya.data_ingestion.validator import ValidationReport, ValidationStatus

NORMALIZED_COLUMNS = [
    "timestamp",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "value",
    "currency",
    "market",
]


@dataclass
class NormalizedMarketData:
    """داده‌ی نرمال‌شده‌ی بازار."""

    df: pd.DataFrame
    rows: int = 0
    symbols: int = 0
    date_min: str = ""
    date_max: str = ""
    output_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "symbols": self.symbols,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "output_path": self.output_path,
            "metadata": dict(self.metadata),
        }


def normalize_market_data(
    df: pd.DataFrame,
    report: ValidationReport,
) -> NormalizedMarketData | None:
    """
    DataFrame خام را نرمال می‌کند.

    اگر وضعیت اعتبارسنجی REJECTED باشد، نرمال‌سازی انجام نمی‌شود.

    Args:
        df: DataFrame خام.
        report: گزارش اعتبارسنجی.

    Returns:
        NormalizedMarketData یا None اگر داده رد شده باشد.
    """
    if report.status == ValidationStatus.REJECTED:
        return None

    df = df.copy()

    # اضافه کردن ستون‌های اختیاری اگر وجود ندارند
    for col in ["value", "currency", "market"]:
        if col not in df.columns:
            if col == "value":
                df[col] = 0.0
            elif col == "currency":
                df[col] = "IRR"
            elif col == "market":
                df[col] = "stock"

    # تبدیل timestamp به UTC
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

    # حذف ردیف‌های با timestamp نامعتبر
    df = df.dropna(subset=["timestamp"])

    # حذف ردیف‌های تکراری (timestamp, symbol)
    df = df.drop_duplicates(subset=["timestamp", "symbol"], keep="first")

    # مرتب‌سازی
    df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

    # انتخاب فقط ستون‌های استاندارد
    available = [c for c in NORMALIZED_COLUMNS if c in df.columns]
    df = df[available]

    normalized = NormalizedMarketData(
        df=df,
        rows=len(df),
        symbols=df["symbol"].nunique() if "symbol" in df.columns else 0,
        date_min=df["timestamp"].min().isoformat() if len(df) > 0 else "",
        date_max=df["timestamp"].max().isoformat() if len(df) > 0 else "",
        metadata={
            "validation_status": report.status.value,
            "duplicate_rows_removed": report.duplicate_rows,
        },
    )

    return normalized


def save_normalized(
    data: NormalizedMarketData,
    output_dir: Path,
    source_filename: str,
    fmt: str = "csv",
) -> Path:
    """
    داده‌ی نرمال‌شده را در مسیر مشخص‌شده ذخیره می‌کند.

    Args:
        data: داده‌ی نرمال‌شده.
        output_dir: پوشه‌ی خروجی.
        source_filename: نام فایل اصلی (برای نام‌گذاری).
        fmt: فرمت خروجی (csv یا jsonl).

    Returns:
        مسیر فایل ذخیره‌شده.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    base = Path(source_filename).stem
    ext = ".csv" if fmt == "csv" else ".jsonl"
    output_path = output_dir / f"{base}_normalized{ext}"

    if fmt == "csv":
        data.df.to_csv(output_path, index=False)
    else:
        data.df.to_json(output_path, orient="records", lines=True, date_format="iso")

    data.output_path = str(output_path)
    return output_path
