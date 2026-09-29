"""
Indicator Engine: لایه‌ی دوم پایپ‌لاین (Storage -> Indicator Engine -> Analysis Engine).

مسئولیت: خواندن لیست اندیکاتورهای فعال از configs/indicators.yaml، اجرای هرکدام
روی دیتافریم OHLCV، و برگرداندن لیستی از IndicatorResult. اضافه کردن اندیکاتور
جدید فقط نیاز به یک فایل جدید در technical/indicators/<group>/ و ثبت آن با
@IndicatorRegistry.register دارد - هسته این فایل تغییر نمی‌کند.
"""
from __future__ import annotations

import logging

import pandas as pd

import arya.technical.indicators.momentum.macd  # noqa: F401
import arya.technical.indicators.momentum.rsi  # noqa: F401

# Import کردن ماژول‌های اندیکاتور تا دکوریتورهای @register اجرا و در رجیستری ثبت شوند.
import arya.technical.indicators.trend.moving_average  # noqa: F401
import arya.technical.indicators.volatility.bollinger  # noqa: F401
import arya.technical.indicators.volume.obv  # noqa: F401
from arya.config.settings import Settings
from arya.models.analysis_result import IndicatorResult
from arya.technical.indicators.base import IndicatorRegistry

logger = logging.getLogger(__name__)


class IndicatorEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self, df: pd.DataFrame) -> list[IndicatorResult]:
        """تمام اندیکاتورهای فعال را روی df اجرا می‌کند و نتایج را برمی‌گرداند."""
        results: list[IndicatorResult] = []
        enabled = self.settings.enabled_indicators()

        min_rows_required = 5
        if len(df) < min_rows_required:
            logger.warning("داده کافی برای محاسبه اندیکاتورها وجود ندارد (rows=%d)", len(df))
            return results

        for indicator_name, cfg in enabled.items():
            if indicator_name not in IndicatorRegistry.available():
                logger.warning("اندیکاتور '%s' در کانفیگ فعال است اما پیاده‌سازی ندارد", indicator_name)
                continue
            try:
                indicator = IndicatorRegistry.create(
                    indicator_name,
                    params=cfg.get("params", {}),
                    weight=float(cfg.get("weight", 1.0)),
                )
                result = indicator.compute(df)
                results.append(result)
            except Exception:
                logger.exception("خطا در محاسبه اندیکاتور '%s'", indicator_name)

        return results
