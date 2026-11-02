"""Deterministic offline shareholder fixtures."""
from __future__ import annotations

from arya.models.shareholders import ShareholderCountPoint, ShareholderFlowMetrics
from arya.providers.shareholder_base import ShareholderDataProvider, ShareholderProviderRegistry


@ShareholderProviderRegistry.register("mock")
class MockShareholderProvider(ShareholderDataProvider):
    name = "mock"

    def fetch_shareholder_flow(self, ticker: str, days: int = 5) -> ShareholderFlowMetrics:
        key = (ticker or "").strip()
        if key.upper() in {"ACCUM", "FOOLAD", "فولاد"} or key.endswith("_ACC"):
            series = tuple(ShareholderCountPoint(f"2026-10-{17 + i:02d}", 120_000 - i * 800) for i in range(min(days, 5)))
            return ShareholderFlowMetrics(
                ticker=key, shareholder_count_series=series, shareholder_count_change_pct=-4.2,
                individual_avg_buy_volume=2.1e5, individual_avg_sell_volume=1.0e5,
                legal_buy_volume=5.0e6, legal_sell_volume=1.0e6, legal_net_buy_volume=4.0e6,
                legal_buy_volume_share=0.38, data_quality="usable", source="mock:accumulation",
                notes=("fixture share volumes; no Rial values",),
            )
        if key.upper() in {"DIST", "DISTRIB"} or key.endswith("_DIST"):
            series = tuple(ShareholderCountPoint(f"2026-10-{17 + i:02d}", 100_000 + i * 900) for i in range(min(days, 5)))
            return ShareholderFlowMetrics(
                ticker=key, shareholder_count_series=series, shareholder_count_change_pct=5.1,
                individual_avg_buy_volume=0.8e5, individual_avg_sell_volume=1.9e5,
                legal_buy_volume=1.0e6, legal_sell_volume=3.0e6, legal_net_buy_volume=-2.0e6,
                legal_buy_volume_share=0.12, data_quality="usable", source="mock:distribution",
                notes=("fixture share volumes; no Rial values",),
            )
        return ShareholderFlowMetrics(ticker=key or "UNKNOWN", data_quality="missing", source="mock:empty", notes=("no shareholder data in mock",))
