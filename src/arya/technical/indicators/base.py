"""
قرارداد پایه‌ی اندیکاتورها + رجیستری Plugin.
هر اندیکاتور جدید فقط باید این کلاس را Extend کند و با دکوریتور @IndicatorRegistry.register
خودش را معرفی کند؛ به این ترتیب می‌توان اندیکاتور/استراتژی اضافه کرد بدون تغییر هسته
(دقیقاً همان نیازمندی "سیستم پلاگین" که در نقشه راه خواسته شده).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from arya.models.analysis_result import IndicatorResult


class Indicator(ABC):
    """کلاس پایه‌ی هر اندیکاتور تکنیکال."""

    name: str = "base"
    group: str = "unknown"

    def __init__(self, params: dict[str, Any] | None = None, weight: float = 1.0):
        self.params = params or {}
        self.weight = weight

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> IndicatorResult:
        """
        df: دیتافریم OHLCV با ایندکس timestamp و ستون‌های open/high/low/close/volume
        خروجی: IndicatorResult شامل مقدار خام، امتیاز نرمال‌شده [-1,1] و هشدارهای فعال‌شده
        """
        raise NotImplementedError

    @staticmethod
    def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, value))


class IndicatorRegistry:
    """رجیستری Plugin برای اندیکاتورها."""

    _registry: dict[str, type[Indicator]] = {}

    @classmethod
    def register(cls, indicator_name: str):
        def _wrap(indicator_cls: type[Indicator]):
            cls._registry[indicator_name] = indicator_cls
            return indicator_cls

        return _wrap

    @classmethod
    def create(cls, indicator_name: str, **kwargs) -> Indicator:
        if indicator_name not in cls._registry:
            raise ValueError(
                f"اندیکاتور ناشناخته: '{indicator_name}'. "
                f"اندیکاتورهای ثبت‌شده: {list(cls._registry)}"
            )
        return cls._registry[indicator_name](**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._registry)
