"""
Symbol Master سبک — بایگانی نمادهای بورسی با صنعت.

منبع پیش‌فرض: data/symbols/equities_flat.json
در صورت نبود فایل، لیست خالی و fallback به Provider.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from arya.models.market_data import Symbol

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path("data/symbols/equities_flat.json")


class SymbolMaster:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self._by_ticker: dict[str, Symbol] = {}
        self._by_industry: dict[str, list[Symbol]] = {}
        self._loaded = False

    def load(self) -> int:
        if not self.path.exists():
            logger.warning("Symbol Master: فایل یافت نشد: %s", self.path)
            self._loaded = True
            return 0

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("equities_flat.json باید لیست باشد")

        by_ticker: dict[str, Symbol] = {}
        by_industry: dict[str, list[Symbol]] = {}

        for row in raw:
            if not isinstance(row, dict):
                continue
            ticker = str(row.get("ticker") or "").strip()
            if not ticker:
                continue
            industry = str(row.get("industry") or "سایر").strip() or "سایر"
            sym = Symbol(
                ticker=ticker,
                market=str(row.get("market") or "stock"),
                name=row.get("name"),
                currency="IRR",
                industry=industry,
            )
            by_ticker[ticker] = sym
            by_industry.setdefault(industry, []).append(sym)

        self._by_ticker = by_ticker
        self._by_industry = by_industry
        self._loaded = True
        logger.info("Symbol Master: %d نماد در %d صنعت", len(by_ticker), len(by_industry))
        return len(by_ticker)

    def _ensure(self) -> None:
        if not self._loaded:
            self.load()

    def get(self, ticker: str) -> Symbol | None:
        self._ensure()
        return self._by_ticker.get(ticker) or self._by_ticker.get(ticker.strip())

    def list_all(self) -> list[Symbol]:
        self._ensure()
        return list(self._by_ticker.values())

    def list_industries(self) -> list[str]:
        self._ensure()
        return sorted(self._by_industry.keys())

    def list_by_industry(self, industry: str) -> list[Symbol]:
        self._ensure()
        if industry in self._by_industry:
            return list(self._by_industry[industry])
        # match partial
        industry_l = industry.strip()
        for key, symbols in self._by_industry.items():
            if industry_l in key or key in industry_l:
                return list(symbols)
        return []

    def count(self) -> int:
        self._ensure()
        return len(self._by_ticker)
