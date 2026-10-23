"""مدل داخلی جریان سهامداران / حقیقی-حقوقی — مستقل از منبع شبکه.

منبع واقعی (SOAP/REST/cdn) فقط از طریق Provider تزریق می‌شود.
تا فاز ۰ شواهد، داده‌ها از mock/fixture می‌آیند.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShareholderCountPoint:
    trade_date: str
    count: float


@dataclass(frozen=True)
class ShareholderFlowMetrics:
    ticker: str
    shareholder_count_series: tuple[ShareholderCountPoint, ...] = ()
    shareholder_count_change_pct: float | None = None
    individual_avg_buy_value: float | None = None
    individual_avg_sell_value: float | None = None
    legal_buy_share: float | None = None
    legal_net_buy_value: float | None = None
    data_quality: str = "missing"
    source: str = "unknown"
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "shareholder_count_change_pct": self.shareholder_count_change_pct,
            "individual_avg_buy_value": self.individual_avg_buy_value,
            "individual_avg_sell_value": self.individual_avg_sell_value,
            "legal_buy_share": self.legal_buy_share,
            "legal_net_buy_value": self.legal_net_buy_value,
            "data_quality": self.data_quality,
            "source": self.source,
            "series_len": len(self.shareholder_count_series),
            "notes": list(self.notes),
        }
