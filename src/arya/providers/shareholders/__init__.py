"""لایهٔ Provider دادهٔ سهامداران/حقیقی-حقوقی (اسمارت‌مانی) — فقط دادهٔ واقعی.

مالکیت فایل (جدول تأییدشدهٔ مالک): Z.ai — برنچ feat/m2-phase0-real-data
مدل ShareholderFlowMetrics و Analyzer: مالکیت Grok (feat/m2-smart-money-offline).
"""
from arya.providers.shareholders.base import (
    FLOW_KEYS,
    InstrumentIdentity,
    ShareholderDataProvider,
    ShareholderDataProviderError,
    ShareholderProviderRegistry,
    ShareholderSnapshotRow,
    empty_flow,
)
from arya.providers.shareholders.tsetmc_client_type import TsetmcClientTypeProvider

__all__ = [
    "FLOW_KEYS",
    "InstrumentIdentity",
    "ShareholderDataProvider",
    "ShareholderDataProviderError",
    "ShareholderProviderRegistry",
    "ShareholderSnapshotRow",
    "TsetmcClientTypeProvider",
    "empty_flow",
]
