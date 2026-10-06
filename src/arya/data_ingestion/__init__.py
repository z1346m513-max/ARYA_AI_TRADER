"""
لایه‌ی دریافت و کنترل داده‌ی بازار (Data Ingestion).

این ماژول مسیر استاندارد پردازش فایل‌های دستی (Excel/CSV) بازار را فراهم می‌کند:

    Inbox → Validation → Normalization → Agents → Reports

هیچ Agent یا تحلیلی نباید مستقیماً فایل خام را بخواند؛ تمام تحلیل‌ها باید
از داده‌ی normalized و manifest-دار استفاده کنند تا بازتولید‌پذیری حفظ شود.

این لایه صرفاً خواندنی است: هیچ اتصال صرافی، ثبت سفارش یا credential
معاملاتی ندارد.
"""
from __future__ import annotations

from arya.data_ingestion.inbox import IngestionPipeline, IngestionResult
from arya.data_ingestion.manifest import FileManifest
from arya.data_ingestion.validator import ValidationReport, ValidationStatus
from arya.data_ingestion.normalizer import NormalizedMarketData

__all__ = [
    "IngestionPipeline",
    "IngestionResult",
    "FileManifest",
    "ValidationReport",
    "ValidationStatus",
    "NormalizedMarketData",
]
