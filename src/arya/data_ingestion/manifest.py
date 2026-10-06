"""
مدل Manifest فایل ورودی.

هر فایل ورودی پس از پردازش یک manifest دریافت می‌کند که شامل:
- هش SHA-256 فایل (برای idempotency و جلوگیری از پردازش تکراری)
- زمان دریافت و پردازش (UTC، timezone-aware)
- وضعیت اعتبارسنجی
- آمار داده (تعداد ردیف، نمادها، بازه‌ی زمانی)
- مسیر فایل normalized خروجی

Manifestها در data/manifests/ ذخیره می‌شوند تا ردیابی کامل باشد.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "market-v1"


def compute_sha256(file_path: Path) -> str:
    """SHA-256 هش فایل را محاسبه می‌کند."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> datetime:
    """زمان فعلی UTC با timezone-aware را برمی‌گرداند."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class FileManifest:
    """manifest تغییرناپذیر برای یک فایل ورودی پردازش‌شده."""

    file_name: str
    file_path: str
    sha256: str
    source: str                          # manual_upload | api | drive_sync
    schema_version: str = SCHEMA_VERSION
    received_at: str = ""                # ISO 8601 UTC
    processed_at: str = ""
    rows: int = 0
    symbols: int = 0
    date_min: str = ""
    date_max: str = ""
    validation_status: str = "PENDING"   # VALID | PARTIAL | INVALID | REJECTED
    analysis_status: str = "PENDING"     # PENDING | RUNNING | DONE | FAILED
    normalized_path: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "file_path": self.file_path,
            "sha256": self.sha256,
            "source": self.source,
            "schema_version": self.schema_version,
            "received_at": self.received_at,
            "processed_at": self.processed_at,
            "rows": self.rows,
            "symbols": self.symbols,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "validation_status": self.validation_status,
            "analysis_status": self.analysis_status,
            "normalized_path": self.normalized_path,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "extra": dict(self.extra),
        }

    @classmethod
    def create(
        cls,
        file_path: Path,
        source: str = "manual_upload",
    ) -> "FileManifest":
        """یک manifest اولیه قبل از اعتبارسنجی می‌سازد."""
        now = utc_now().isoformat()
        sha = compute_sha256(file_path)
        return cls(
            file_name=file_path.name,
            file_path=str(file_path),
            sha256=sha,
            source=source,
            received_at=now,
            processed_at=now,
        )

    def with_validation(
        self,
        *,
        status: str,
        rows: int,
        symbols: int,
        date_min: str,
        date_max: str,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        normalized_path: str | None = None,
    ) -> "FileManifest":
        """نسخه‌ی جدید manifest با نتایج اعتبارسنجی برمی‌گرداند (immutable)."""
        return FileManifest(
            file_name=self.file_name,
            file_path=self.file_path,
            sha256=self.sha256,
            source=self.source,
            schema_version=self.schema_version,
            received_at=self.received_at,
            processed_at=utc_now().isoformat(),
            rows=rows,
            symbols=symbols,
            date_min=date_min,
            date_max=date_max,
            validation_status=status,
            analysis_status=self.analysis_status,
            normalized_path=normalized_path,
            errors=errors or [],
            warnings=warnings or [],
            extra=dict(self.extra),
        )

    def save(self, manifests_dir: Path) -> Path:
        """manifest را به‌صورت JSON در مسیر مشخص‌شده ذخیره می‌کند."""
        import json

        manifests_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = manifests_dir / f"{self.file_name}.manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return manifest_file
