"""
قرارداد (Contract) پایه برای تمام Providerهای داده.
هر Provider جدید (TSETMC، Binance، Codal، ...) باید این کلاس را پیاده‌سازی کند
تا بدون تغییر در بقیه‌ی پایپ‌لاین، به سیستم اضافه شود (معماری Plugin-friendly).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from arya.models.market_data import OHLCVSeries, Symbol


class MarketDataProvider(ABC):
    """Provider پایه برای داده‌های OHLCV بازار."""

    name: str = "base"

    @abstractmethod
    def fetch_ohlcv(self, symbol: Symbol, timeframe: str, limit: int = 200) -> OHLCVSeries:
        """آخرین `limit` کندل را برای نماد و تایم‌فریم مشخص برمی‌گرداند."""
        raise NotImplementedError

    @abstractmethod
    def list_symbols(self) -> list[Symbol]:
        """لیست نمادهای پشتیبانی‌شده توسط این Provider."""
        raise NotImplementedError


class ProviderRegistry:
    """رجیستری ساده برای انتخاب Provider بر اساس درایور تنظیم‌شده در providers.yaml."""

    _registry: dict[str, type[MarketDataProvider]] = {}

    @classmethod
    def register(cls, driver_name: str):
        def _wrap(provider_cls: type[MarketDataProvider]):
            cls._registry[driver_name] = provider_cls
            return provider_cls

        return _wrap

    @classmethod
    def create(cls, driver_name: str, **kwargs) -> MarketDataProvider:
        if driver_name not in cls._registry:
            raise ValueError(
                f"درایور Provider ناشناخته: '{driver_name}'. "
                f"درایورهای موجود: {list(cls._registry)}"
            )
        return cls._registry[driver_name](**kwargs)
