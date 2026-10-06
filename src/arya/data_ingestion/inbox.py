"""
Pipeline دریافت و پردازش داده‌ی بازار.

این ماژول کل فرآیند Inbox → Validation → Normalization → Archive را
هماهنگ می‌کند و manifest و گزارش کیفیت تولید می‌کند.

ساختار پوشه‌ها:
    data/inbox/market/       فایل‌های جدید ورودی
    data/processing/         فایل‌های در حال پردازش
    data/archive/market/     فایل‌های پردازش‌شده و معتبر
    data/rejected/           فایل‌های رد‌شده
    data/normalized/         داده‌ی نرمال‌شده
    data/manifests/          manifest‌ها
    data/agent_outputs/     خروجی Agentهای تحلیل
    data/reports/daily/      گزارش‌های روزانه
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from arya.data_ingestion.excel_loader import LoaderError, load_market_file
from arya.data_ingestion.manifest import FileManifest
from arya.data_ingestion.normalizer import (
    NormalizedMarketData,
    normalize_market_data,
    save_normalized,
)
from arya.data_ingestion.validator import ValidationReport, ValidationStatus, validate_market_data

# مسیرهای پیش‌فرض (نسبت به ریشه‌ی پروژه)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INBOX = PROJECT_ROOT / "data" / "inbox" / "market"
DEFAULT_PROCESSING = PROJECT_ROOT / "data" / "processing"
DEFAULT_ARCHIVE = PROJECT_ROOT / "data" / "archive" / "market"
DEFAULT_REJECTED = PROJECT_ROOT / "data" / "rejected"
DEFAULT_NORMALIZED = PROJECT_ROOT / "data" / "normalized"
DEFAULT_MANIFESTS = PROJECT_ROOT / "data" / "manifests"
DEFAULT_REPORTS = PROJECT_ROOT / "data" / "reports" / "daily"


@dataclass
class IngestionResult:
    """نتیجه‌ی پردازش یک فایل ورودی."""

    manifest: FileManifest | None = None
    validation: ValidationReport | None = None
    normalized: NormalizedMarketData | None = None
    success: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "error": self.error,
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "normalized": self.normalized.to_dict() if self.normalized else None,
        }


class IngestionPipeline:
    """
    Pipeline هماهنگ‌کننده‌ی دریافت، اعتبارسنجی و نرمال‌سازی.

    پیکربندی مسیرها قابل تنظیم است؛ پیش‌فرض‌ها از ساختار استاندارد
    پروژه استفاده می‌کنند.
    """

    def __init__(
        self,
        inbox_dir: Path = DEFAULT_INBOX,
        processing_dir: Path = DEFAULT_PROCESSING,
        archive_dir: Path = DEFAULT_ARCHIVE,
        rejected_dir: Path = DEFAULT_REJECTED,
        normalized_dir: Path = DEFAULT_NORMALIZED,
        manifests_dir: Path = DEFAULT_MANIFESTS,
        reports_dir: Path = DEFAULT_REPORTS,
    ):
        self.inbox_dir = Path(inbox_dir)
        self.processing_dir = Path(processing_dir)
        self.archive_dir = Path(archive_dir)
        self.rejected_dir = Path(rejected_dir)
        self.normalized_dir = Path(normalized_dir)
        self.manifests_dir = Path(manifests_dir)
        self.reports_dir = Path(reports_dir)

    def process_file(
        self,
        file_path: Path,
        source: str = "manual_upload",
        output_format: str = "csv",
        archive_original: bool = True,
    ) -> IngestionResult:
        """
        یک فایل ورودی را پردازش می‌کند.

        مراحل:
        ۱. ساخت manifest اولیه با SHA-256
        ۲. بارگذاری فایل
        ۳. اعتبارسنجی
        ۴. نرمال‌سازی (اگر معتبر باشد)
        ۵. ذخیره‌ی داده‌ی نرمال‌شده
        ۶. ذخیره‌ی manifest و گزارش
        ۷. انتقال فایل اصلی به archive یا rejected

        Args:
            file_path: مسیر فایل ورودی.
            source: منبع فایل (manual_upload, api, drive_sync).
            output_format: فرمت خروجی نرمال‌شده (csv یا jsonl).
            archive_original: اگر True، فایل اصلی به archive منتقل شود.

        Returns:
            IngestionResult شامل manifest، validation و normalized.
        """
        result = IngestionResult()
        file_path = Path(file_path)

        try:
            # ۱. manifest اولیه
            manifest = FileManifest.create(file_path, source=source)

            # بررسی idempotency: آیا قبلاً پردازش شده؟
            manifest_path = self.manifests_dir / f"{file_path.name}.manifest.json"
            if manifest_path.exists():
                with open(manifest_path, encoding="utf-8") as f:
                    existing = json.load(f)
                if existing.get("sha256") == manifest.sha256:
                    result.manifest = FileManifest(
                        file_name=existing["file_name"],
                        file_path=existing["file_path"],
                        sha256=existing["sha256"],
                        source=existing.get("source", source),
                        schema_version=existing.get("schema_version", "market-v1"),
                        received_at=existing.get("received_at", ""),
                        processed_at=existing.get("processed_at", ""),
                        rows=existing.get("rows", 0),
                        symbols=existing.get("symbols", 0),
                        date_min=existing.get("date_min", ""),
                        date_max=existing.get("date_max", ""),
                        validation_status=existing.get("validation_status", "PENDING"),
                        analysis_status=existing.get("analysis_status", "PENDING"),
                        normalized_path=existing.get("normalized_path"),
                        errors=existing.get("errors", []),
                        warnings=existing.get("warnings", []),
                        extra=existing.get("extra", {}),
                    )
                    result.success = True
                    result.error = "فایل قبلاً پردازش شده (idempotency)."
                    return result

            # ۲. بارگذاری
            df = load_market_file(file_path)

            # ۳. اعتبارسنجی
            report = validate_market_data(df)
            result.validation = report

            # ۴ و ۵. نرمال‌سازی و ذخیره
            if report.status != ValidationStatus.REJECTED:
                normalized = normalize_market_data(df, report)
                if normalized:
                    norm_path = save_normalized(
                        normalized,
                        self.normalized_dir,
                        file_path.name,
                        fmt=output_format,
                    )
                    result.normalized = normalized
                    manifest = manifest.with_validation(
                        status=report.status.value,
                        rows=report.total_rows,
                        symbols=report.symbols,
                        date_min=report.date_min,
                        date_max=report.date_max,
                        errors=report.errors,
                        warnings=report.warnings,
                        normalized_path=str(norm_path),
                    )
                else:
                    manifest = manifest.with_validation(
                        status="INVALID",
                        rows=report.total_rows,
                        symbols=report.symbols,
                        date_min=report.date_min,
                        date_max=report.date_max,
                        errors=["نرمال‌سازی انجام نشد."],
                        warnings=report.warnings,
                    )
            else:
                manifest = manifest.with_validation(
                    status=report.status.value,
                    rows=report.total_rows,
                    symbols=report.symbols,
                    date_min=report.date_min,
                    date_max=report.date_max,
                    errors=report.errors,
                    warnings=report.warnings,
                )

            # ۶. ذخیره‌ی manifest
            manifest.save(self.manifests_dir)

            # ۷. گزارش کیفیت
            self._save_quality_report(file_path.name, manifest, report)

            # ۸. انتقال فایل اصلی
            if archive_original:
                dest = self.archive_dir if report.status != ValidationStatus.REJECTED else self.rejected_dir
                dest.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(file_path, dest / file_path.name)

            result.manifest = manifest
            result.success = report.status != ValidationStatus.REJECTED

        except LoaderError as e:
            result.error = str(e)
            result.success = False
        except Exception as e:
            result.error = f"خطای غیرمنتظره: {e}"
            result.success = False

        return result

    def _save_quality_report(
        self,
        filename: str,
        manifest: FileManifest,
        report: ValidationReport,
    ) -> Path:
        """گزارش کیفیت داده را به‌صورت Markdown و JSON ذخیره می‌کند."""
        import json as json_mod

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        base = Path(filename).stem

        # JSON report
        json_path = self.reports_dir / f"{base}_quality.json"
        quality_data = {
            "file": filename,
            "sha256": manifest.sha256,
            "validation": report.to_dict(),
            "generated_at": manifest.processed_at,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json_mod.dump(quality_data, f, ensure_ascii=False, indent=2)

        # Markdown report
        md_path = self.reports_dir / f"{base}_quality.md"
        lines = [
            f"# گزارش کیفیت داده: {filename}",
            "",
            f"- **SHA-256:** `{manifest.sha256}`",
            f"- **وضعیت اعتبارسنجی:** {manifest.validation_status}",
            f"- **زمان پردازش:** {manifest.processed_at}",
            f"- **تعداد ردیف:** {report.total_rows}",
            f"- **نمادها:** {report.symbols}",
            f"- **بازه‌ی زمانی:** {report.date_min} تا {report.date_max}",
            "",
        ]

        if report.errors:
            lines.append("## خطاها")
            for err in report.errors:
                lines.append(f"- {err}")
            lines.append("")

        if report.warnings:
            lines.append("## هشدارها")
            for w in report.warnings:
                lines.append(f"- {w}")
            lines.append("")

        if report.duplicate_rows > 0:
            lines.append(f"## ردیف‌های تکراری: {report.duplicate_rows}")
            lines.append("")

        if manifest.normalized_path:
            lines.append(f"## فایل نرمال‌شده: `{manifest.normalized_path}`")
            lines.append("")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return md_path

    def process_inbox(self, source: str = "manual_upload") -> list[IngestionResult]:
        """
        تمام فایل‌های موجود در inbox را پردازش می‌کند.

        Args:
            source: منبع فایل‌ها.

        Returns:
            لیست نتایج پردازش.
        """
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for ext in ["*.xlsx", "*.xls", "*.csv"]:
            for f in sorted(self.inbox_dir.glob(ext)):
                results.append(self.process_file(f, source=source))
        return results
