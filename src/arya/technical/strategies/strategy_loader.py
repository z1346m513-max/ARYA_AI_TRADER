"""بارگذاری پروفایل‌های استراتژی از configs/strategies.yaml"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_strategies(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else Path("configs/strategies.yaml")
    if not p.exists():
        # مسیر جایگزین نسبت به ریشه بسته
        alt = Path(__file__).resolve().parents[3] / "configs" / "strategies.yaml"
        p = alt if alt.exists() else p
    if not p.exists():
        return {"default_profile": "trend_rsi_balanced", "profiles": {}}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {"default_profile": "trend_rsi_balanced", "profiles": {}}
    data.setdefault("profiles", {})
    return data


def get_profile(name: str | None = None, path: str | Path | None = None) -> tuple[str, dict[str, Any]]:
    cfg = load_strategies(path)
    profiles: dict = cfg.get("profiles") or {}
    key = name or cfg.get("default_profile") or next(iter(profiles), "")
    if key not in profiles:
        raise KeyError(f"پروفایل استراتژی یافت نشد: {key!r}. موجود: {list(profiles)}")
    return key, profiles[key]


def list_profiles(path: str | Path | None = None) -> list[tuple[str, str]]:
    cfg = load_strategies(path)
    out = []
    for name, prof in (cfg.get("profiles") or {}).items():
        if isinstance(prof, dict):
            out.append((name, str(prof.get("description") or "")))
    return out
