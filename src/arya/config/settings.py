"""
مدیریت متمرکز تنظیمات پروژه.
تمام فایل‌های YAML موجود در configs/ در این‌جا بارگذاری و به‌صورت dict/dataclass
در اختیار بقیه‌ی ماژول‌ها قرار می‌گیرند. هر ماژول باید از این کلاس تنظیمات خودش
را بخواند؛ هیچ ماژولی مستقیماً فایل YAML باز نمی‌کند.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs"

_CONFIG_FILES = {
    "app": "app.yaml",
    "indicators": "indicators.yaml",
    "weights": "weights.yaml",
    "providers": "providers.yaml",
    "scheduler": "scheduler.yaml",
    "ui": "ui.yaml",
}


class ConfigError(Exception):
    """خطای مربوط به بارگذاری یا اعتبارسنجی تنظیمات."""


@dataclass
class Settings:
    """کانتینر تمام تنظیمات بارگذاری‌شده."""

    config_dir: Path
    app: dict[str, Any] = field(default_factory=dict)
    indicators: dict[str, Any] = field(default_factory=dict)
    weights: dict[str, Any] = field(default_factory=dict)
    providers: dict[str, Any] = field(default_factory=dict)
    scheduler: dict[str, Any] = field(default_factory=dict)
    ui: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_dir: str | Path | None = None) -> Settings:
        base = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
        if not base.exists():
            raise ConfigError(f"مسیر تنظیمات پیدا نشد: {base}")

        data: dict[str, Any] = {}
        for key, filename in _CONFIG_FILES.items():
            file_path = base / filename
            if not file_path.exists():
                raise ConfigError(f"فایل تنظیمات یافت نشد: {file_path}")
            with open(file_path, encoding="utf-8") as f:
                data[key] = yaml.safe_load(f) or {}

        return cls(config_dir=base, **data)

    def active_weight_profile(self) -> dict[str, float]:
        """وزن‌های فعال (پروفایل انتخاب‌شده) را برمی‌گرداند."""
        profile_name = self.weights.get("active_profile", "balanced")
        profiles = self.weights.get("profiles", {})
        weights = profiles.get(profile_name) or self.weights.get("sections", {})
        total = sum(weights.values()) or 1.0
        # نرمال‌سازی تا مجموع دقیقا ۱ شود
        return {k: v / total for k, v in weights.items()}

    def enabled_indicators(self) -> dict[str, dict[str, Any]]:
        """دیکشنری تخت (flat) از تمام اندیکاتورهای فعال به همراه گروهشان."""
        flat: dict[str, dict[str, Any]] = {}
        for group, indicators in self.indicators.items():
            for name, cfg in (indicators or {}).items():
                if cfg.get("enabled"):
                    entry = copy.deepcopy(cfg)
                    entry["group"] = group
                    entry["name"] = name
                    flat[name] = entry
        return flat

    def provider_for(self, market: str) -> dict[str, Any]:
        return self.providers.get("market", {}).get(market, {})
