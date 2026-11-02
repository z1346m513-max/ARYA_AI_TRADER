"""Internal shareholder-flow evidence contract.

ClientTypeAll supplies share volumes and participant counts, not Rial values.
Missing values remain None; units are explicit in field names.
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
    # Share volume per individual buyer/seller (shares per participant).
    individual_avg_buy_volume: float | None = None
    individual_avg_sell_volume: float | None = None
    # Share volumes, not monetary values.
    legal_buy_volume: float | None = None
    legal_sell_volume: float | None = None
    legal_net_buy_volume: float | None = None
    # Fraction of total buy-side share volume, in [0, 1].
    legal_buy_volume_share: float | None = None
    # Reserved for sources that explicitly provide Rial-denominated values.
    individual_avg_buy_value_rial: float | None = None
    individual_avg_sell_value_rial: float | None = None
    legal_net_buy_value_rial: float | None = None
    data_quality: str = "missing"
    source: str = "unknown"
    source_timestamp_utc: str | None = None
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "shareholder_count_change_pct": self.shareholder_count_change_pct,
            "individual_avg_buy_volume": self.individual_avg_buy_volume,
            "individual_avg_sell_volume": self.individual_avg_sell_volume,
            "legal_buy_volume": self.legal_buy_volume,
            "legal_sell_volume": self.legal_sell_volume,
            "legal_net_buy_volume": self.legal_net_buy_volume,
            "legal_buy_volume_share": self.legal_buy_volume_share,
            "individual_avg_buy_value_rial": self.individual_avg_buy_value_rial,
            "individual_avg_sell_value_rial": self.individual_avg_sell_value_rial,
            "legal_net_buy_value_rial": self.legal_net_buy_value_rial,
            "data_quality": self.data_quality,
            "source": self.source,
            "source_timestamp_utc": self.source_timestamp_utc,
            "series_len": len(self.shareholder_count_series),
            "notes": list(self.notes),
        }
