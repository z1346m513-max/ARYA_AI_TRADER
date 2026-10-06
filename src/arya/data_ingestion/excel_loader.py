"""
بارگذاری فایل‌های Excel و CSV بازار.

این ماژول فقط مسئول خواندن فایل خام و تبدیل آن به DataFrame است.
هیچ اعتبارسنجی منطقی در اینجا انجام نمی‌شود؛ آن مسئولیت validator است.

پشتیبانی از:
- .xlsx, .xls (نیازمند openpyxl)
- .csv (با جداکننده‌ی خودکار)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


class LoaderError(Exception):
    """خطای بارگذاری فایل."""


def load_market_file(file_path: Path) -> pd.DataFrame:
    """
    فایل Excel یا CSV بازار را می‌خواند و DataFrame برمی‌گرداند.

    Args:
        file_path: مسیر فایل ورودی.

    Returns:
        DataFrame خام با ستون‌های فایل اصلی.

    Raises:
        LoaderError: اگر فرمت پشتیبانی نشود یا فایل خالی باشد.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise LoaderError(
            f"فرمت پشتیبانی نمی‌شود: '{ext}'. "
            f"فرمت‌های مجاز: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if not file_path.exists():
        raise LoaderError(f"فایل پیدا نشد: {file_path}")

    if ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    if df.empty:
        raise LoaderError("فایل خالی است یا هیچ داده‌ای ندارد.")

    return df
