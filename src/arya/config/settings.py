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
    "analysis": "analysis.yaml",
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
    analysis: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_dir: str | Path | None = None) -> "Settings":
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

    def analysis_profile(self, profile_name: str | None = None) -> dict[str, Any]:
        """Return a deep copy of the selected analysis profile."""
        name = profile_name or self.analysis.get("active_profile", "balanced")
        profiles = self.analysis.get("profiles", {})
        profile = profiles.get(name)
        if profile is None:
            raise ConfigError(f"پروفایل تحلیل پیدا نشد: {name}")
        return copy.deepcopy(profile)

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = Settings._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    @staticmethod
    def _validate_analysis_values(
        indicators: dict[str, Any],
        decision: dict[str, Any],
        risk: dict[str, Any],
        history_limit: int,
    ) -> None:
        if history_limit < 5:
            raise ConfigError("history_limit باید حداقل 5 باشد.")

        required_rows = 5
        enabled_count = 0
        for group, values in indicators.items():
            for name, cfg in (values or {}).items():
                if not isinstance(cfg, dict) or not cfg.get("enabled"):
                    continue
                enabled_count += 1
                params = cfg.get("params", {})
                weight = float(cfg.get("weight", 1.0))
                if weight < 0:
                    raise ConfigError(f"وزن اندیکاتور {name} نمی‌تواند منفی باشد.")

                if name in {"sma", "ema", "bollinger"}:
                    period = int(params.get("period", 20))
                    if period < 2:
                        raise ConfigError(f"دوره {name} باید حداقل 2 باشد.")
                    required_rows = max(required_rows, period)
                elif name == "rsi":
                    period = int(params.get("period", 14))
                    overbought = float(params.get("overbought", 70))
                    oversold = float(params.get("oversold", 30))
                    if period < 2 or not 0 <= oversold < overbought <= 100:
                        raise ConfigError("پارامترهای RSI نامعتبر هستند.")
                    required_rows = max(required_rows, period + 1)
                elif name == "macd":
                    fast = int(params.get("fast", 12))
                    slow = int(params.get("slow", 26))
                    signal = int(params.get("signal", 9))
                    if not (2 <= fast < slow) or signal < 2:
                        raise ConfigError("پارامترهای MACD نامعتبر هستند.")
                    required_rows = max(required_rows, slow + signal)
                elif name == "obv":
                    required_rows = max(required_rows, 2)

        if enabled_count == 0:
            raise ConfigError("حداقل یک اندیکاتور باید فعال باشد.")
        if history_limit < required_rows:
            raise ConfigError(
                f"history_limit={history_limit} برای اندیکاتورهای انتخاب‌شده کافی نیست؛ "
                f"حداقل {required_rows} کندل لازم است."
            )

        buy_threshold = float(decision.get("buy_threshold", 0.25))
        sell_threshold = float(decision.get("sell_threshold", -0.25))
        if not -1.0 <= sell_threshold < buy_threshold <= 1.0:
            raise ConfigError("آستانه‌های خرید/فروش نامعتبر هستند.")

        volatility_window = int(risk.get("volatility_window", 14))
        if volatility_window < 2:
            raise ConfigError("پنجره نوسان ریسک باید حداقل 2 باشد.")

    def for_analysis(
        self,
        *,
        profile_name: str | None = None,
        indicator_overrides: dict[str, Any] | None = None,
        decision_overrides: dict[str, Any] | None = None,
        risk_overrides: dict[str, Any] | None = None,
        history_limit: int | None = None,
    ) -> "Settings":
        """Create an isolated Settings copy for a single analysis run."""
        cloned = copy.deepcopy(self)
        profile = cloned.analysis_profile(profile_name)

        if profile.get("indicators"):
            cloned.indicators = self._deep_merge(cloned.indicators, profile["indicators"])

        runtime_indicators = indicator_overrides or {}
        if runtime_indicators:
            cloned.indicators = self._deep_merge(cloned.indicators, runtime_indicators)

        runtime = cloned.analysis.setdefault("runtime", {})
        runtime["profile"] = profile_name or cloned.analysis.get("active_profile", "balanced")
        runtime["decision"] = self._deep_merge(
            profile.get("decision", {}),
            decision_overrides or {},
        )
        runtime["risk"] = self._deep_merge(
            profile.get("risk", {}),
            risk_overrides or {},
        )
        runtime["history_limit"] = int(
            history_limit
            if history_limit is not None
            else profile.get("history_limit", 200)
        )
        self._validate_analysis_values(
            cloned.indicators,
            runtime["decision"],
            runtime["risk"],
            runtime["history_limit"],
        )
        return cloned

