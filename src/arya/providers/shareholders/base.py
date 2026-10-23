"""قرارداد (Contract) لایهٔ Provider برای دادهٔ سهامداران/حقیقی-حقوقی.

طبق CR-20261024-001 (تصمیم D1): منطق تحلیل هرگز HTTP/SOAP نمی‌بیند؛ Analysis فقط
مدل دادهٔ خروجی Providers را مصرف می‌کند.

قرارداد سازگاری با مدل همکار (مهم — مالکیت فایل):
- مالک مدل `ShareholderFlowMetrics`: ایجنت Grok (برنچ feat/m2-smart-money-offline، مسیر arya/models/shareholders.py)
- خروجی `fetch_shareholder_flow` یک dict است که «دقیقاً» با همین کلیدها ساخته می‌شود:
  shareholder_count_series, individual_avg_buy_value, individual_avg_sell_value,
  legal_buy_share, legal_net_buy_value, data_quality
  تا در برنچ Grok به‌صورت `ShareholderFlowMetrics(**flow)` مصرف شود.
- افزودن/تغییر کلید بدون هماهنگی با مالک مدل ممنوع است (CR-20261024-002).

سیاست دادهٔ واقعی (دستور مالک): این لایه هیچ دادهٔ ساختگی/mock تولید نمی‌کند؛
اگر واقعیت شبکه قابل احراز نباشد، خطا یا data_quality محافظه‌کارانه برمی‌گردد.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

# کلیدهای مجاز خروجی flow — هم‌تراز با فیلدهای ShareholderFlowMetrics در CR-20261024-001
FLOW_KEYS: tuple[str, ...] = (
    "shareholder_count_series",
    "individual_avg_buy_value",
    "individual_avg_sell_value",
    "legal_buy_share",
    "legal_net_buy_value",
    "data_quality",
)


class ShareholderDataProviderError(RuntimeError):
    """خطای قابل‌گزارش لایهٔ دادهٔ سهامداران (شبکه، پاسخ نامعتبر، نقض گیت راستی‌آزمایی)."""


@dataclass
class ShareholderSnapshotRow:
    """یک ردیف واقعی snapshot حقیقی/حقوقی (قالب ۹ فیلدی تأییدشده در evidence/2026-10-24 فایل 13)."""

    ins_code: str
    individual_buy_count: int
    legal_buy_count: int
    individual_buy_volume: int
    legal_buy_volume: int
    individual_sell_count: int
    legal_sell_count: int
    individual_sell_volume: int
    legal_sell_volume: int

    @property
    def total_buy_volume(self) -> int:
        return self.individual_buy_volume + self.legal_buy_volume

    @property
    def total_sell_volume(self) -> int:
        return self.individual_sell_volume + self.legal_sell_volume


@dataclass
class InstrumentIdentity:
    """هویت واقعی نماد از جست‌وجوی رسمی cdn.tsetmc.com (شواهد: فایل 11)."""

    ticker: str
    name: str | None
    ins_code: str             # کد جدید (مثلاً فولاد: 46348559193224090)
    old_ins_code: str | None  # insCode3 — کلید ردیف‌ها در snapshot قدیمی (فایل 13)


def empty_flow(data_quality: str) -> dict:
    """قالب استاندارد flow؛ فقط کلیدهای مجاز FLOW_KEYS."""
    return {
        "shareholder_count_series": None,
        "individual_avg_buy_value": None,
        "individual_avg_sell_value": None,
        "legal_buy_share": None,
        "legal_net_buy_value": None,
        "data_quality": data_quality,
    }


class ShareholderDataProvider(ABC):
    """Provider پایهٔ دادهٔ سهامداران — متد کانونی مطابق CR-20261024-001."""

    name: str = "base"

    @abstractmethod
    def fetch_shareholder_flow(self, ticker: str, days: int = 30) -> dict:
        """خروجی: dict با کلیدهای FLOW_KEYS (سازگار با ShareholderFlowMetrics(**flow))."""
        raise NotImplementedError

    @abstractmethod
    def inspect_snapshot(self, ticker: str, days: int = 30) -> dict:
        """دادهٔ خام واقعی + تشخیص‌ها (بدون هیچ متریک مشتق‌شده) — برای شفافیت و دیباگ."""
        raise NotImplementedError


class ShareholderProviderRegistry:
    """رجیستری درایورهای سهامداران — هم‌الگوی ProviderRegistry لایهٔ market."""

    _registry: dict[str, type[ShareholderDataProvider]] = {}

    @classmethod
    def register(cls, driver_name: str):
        def _wrap(provider_cls: type[ShareholderDataProvider]):
            cls._registry[driver_name] = provider_cls
            return provider_cls

        return _wrap

    @classmethod
    def create(cls, driver_name: str, **kwargs) -> ShareholderDataProvider:
        if driver_name not in cls._registry:
            raise ShareholderDataProviderError(
                f"درایور سهامداران ناشناخته: '{driver_name}'. درایورهای ثبت‌شده: {list(cls._registry)}"
            )
        return cls._registry[driver_name](**kwargs)
