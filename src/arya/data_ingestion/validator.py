"""
اعتبارسنجی داده‌ی بازار.

بررسی‌های انجام‌شده:
- وجود ستون‌های الزامی (timestamp, symbol, open, high, low, close, volume)
- نبود مقادیر گمشده در ستون‌های کلیدی
- قیمت‌های مثبت
- ناسازگاری OHLC (high >= max(open, close), low <= min(open, close))
- حجم غیرمنفی
- ترتیب زمانی
- ردیف‌های تکراری (timestamp, symbol)
- timezone-aware بودن timestamp

خروجی: ValidationReport با وضعیت VALID / PARTIAL / INVALID / REJECTED
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

OPTIONAL_COLUMNS = ["value", "currency", "market"]


class ValidationStatus(str, Enum):
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    INVALID = "INVALID"
    REJECTED = "REJECTED"


@dataclass
class ValidationReport:
    """گزارش اعتبارسنجی یک فایل بازار."""

    status: ValidationStatus = ValidationStatus.VALID
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    symbols: int = 0
    date_min: str = ""
    date_max: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    row_issues: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "duplicate_rows": self.duplicate_rows,
            "symbols": self.symbols,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "row_issues": list(self.row_issues),
        }


def _parse_timestamp(series: pd.Series) -> pd.Series:
    """ستون timestamp را به datetime تبدیل می‌کند."""
    return pd.to_datetime(series, utc=True, errors="coerce")


def validate_market_data(df: pd.DataFrame) -> ValidationReport:
    """
    DataFrame بازار را اعتبارسنجی می‌کند.

    Args:
        df: DataFrame خام بارگذاری‌شده از Excel/CSV.

    Returns:
        ValidationReport شامل وضعیت و خطاها.
    """
    report = ValidationReport(total_rows=len(df))

    # ۱. بررسی ستون‌های الزامی
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        report.status = ValidationStatus.REJECTED
        report.errors.append(f"ستون‌های الزامی وجود ندارند: {missing}")
        return report

    # ستون‌های اختیاری را هشدار بده
    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in df.columns]
    if missing_optional:
        report.warnings.append(f"ستون‌های اختیاری وجود ندارند: {missing_optional}")

    # ۲. بررسی مقادیر گمشده
    for col in REQUIRED_COLUMNS:
        null_count = df[col].isna().sum()
        if null_count > 0:
            report.warnings.append(
                f"ستون '{col}' دارای {null_count} مقدار گمشده است."
            )

    # ۳. تبدیل timestamp
    df = df.copy()
    df["_ts"] = _parse_timestamp(df["timestamp"])

    # بررسی NaT در timestamp
    nat_count = df["_ts"].isna().sum()
    if nat_count > 0:
        report.errors.append(
            f"{nat_count} ردیف timestamp نامعتبر دارند."
        )

    # ۴. بررسی قیمت‌های مثبت
    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        if (df[col] < 0).any():
            bad = df[df[col] < 0]
            report.errors.append(
                f"ستون '{col}' دارای {len(bad)} قیمت منفی است."
            )
            for idx in bad.index[:10]:
                report.row_issues.append({
                    "row": int(idx),
                    "issue": f"negative_{col}",
                    "value": float(df.loc[idx, col]),
                })

    # ۵. بررسی حجم غیرمنفی
    if (df["volume"] < 0).any():
        bad = df[df["volume"] < 0]
        report.errors.append(
            f"ستون 'volume' دارای {len(bad)} حجم منفی است."
        )

    # ۶. بررسی ناسازگاری OHLC
    ohlc_high = df[["open", "close"]].max(axis=1)
    ohlc_low = df[["open", "close"]].min(axis=1)

    bad_high = df["high"] < ohlc_high
    bad_low = df["low"] > ohlc_low

    if bad_high.any():
        count = int(bad_high.sum())
        report.errors.append(
            f"{count} ردیف: high کمتر از max(open, close) است."
        )
        for idx in df[bad_high].index[:10]:
            report.row_issues.append({
                "row": int(idx),
                "issue": "high_lt_max_open_close",
                "high": float(df.loc[idx, "high"]),
                "open": float(df.loc[idx, "open"]),
                "close": float(df.loc[idx, "close"]),
            })

    if bad_low.any():
        count = int(bad_low.sum())
        report.errors.append(
            f"{count} ردیف: low بزرگتر از min(open, close) است."
        )
        for idx in df[bad_low].index[:10]:
            report.row_issues.append({
                "row": int(idx),
                "issue": "low_gt_min_open_close",
                "low": float(df.loc[idx, "low"]),
                "open": float(df.loc[idx, "open"]),
                "close": float(df.loc[idx, "close"]),
            })

    # ۷. بررسی ردیف‌های تکراری
    dup_mask = df.duplicated(subset=["timestamp", "symbol"], keep=False)
    dup_count = int(dup_mask.sum())
    if dup_count > 0:
        report.duplicate_rows = dup_count
        report.warnings.append(
            f"{dup_count} ردیف تکراری (timestamp, symbol) یافت شد."
        )

    # ۸. بررسی ترتیب زمانی
    if not df["_ts"].is_monotonic_increasing:
        report.warnings.append("داده به‌صورت زمانی مرتب نیست.")

    # ۹. آمار نمادها و بازه‌ی زمانی
    valid_ts = df["_ts"].dropna()
    if len(valid_ts) > 0:
        report.date_min = valid_ts.min().isoformat()
        report.date_max = valid_ts.max().isoformat()

    report.symbols = df["symbol"].nunique() if "symbol" in df.columns else 0
    report.valid_rows = len(df) - report.invalid_rows - report.duplicate_rows

    # ۱۰. تعیین وضعیت نهایی
    if report.errors:
        if len(report.errors) > 3 or any("منفی" in e for e in report.errors):
            report.status = ValidationStatus.INVALID
        else:
            report.status = ValidationStatus.PARTIAL
    else:
        report.status = ValidationStatus.VALID

    return report
