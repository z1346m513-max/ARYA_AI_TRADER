"""درایور mock سهامداران — fixture دترمینیستیک برای تست آفلاین."""
from __future__ import annotations

from arya.models.shareholders import ShareholderCountPoint, ShareholderFlowMetrics
from arya.providers.shareholder_base import ShareholderDataProvider, ShareholderProviderRegistry


@ShareholderProviderRegistry.register("mock")
class MockShareholderProvider(ShareholderDataProvider):
    name = "mock"

    def fetch_shareholder_flow(self, ticker: str, days: int = 5) -> ShareholderFlowMetrics:
        key = (ticker or "").strip()
        if key.upper() in {"ACCUM", "FOOLAD", "فولاد"} or key.endswith("_ACC"):
            series = tuple(
                ShareholderCountPoint(f"2026-10-{17 + i:02d}", 120_000 - i * 800)
                for i in range(min(days, 5))
            )
            return ShareholderFlowMetrics(
                ticker=key,
                shareholder_count_series=series,
                shareholder_count_change_pct=-4.2,
                individual_avg_buy_value=2.1e8,
                individual_avg_sell_value=1.0e8,
                legal_buy_share=0.38,
                legal_net_buy_value=5.0e9,
                data_quality="usable",
                source="mock:accumulation",
                notes=("fixture accumulation",),
            )
        if key.upper() in {"DIST", "DISTRIB"} or key.endswith("_DIST"):
            series = tuple(
                ShareholderCountPoint(f"2026-10-{17 + i:02d}", 100_000 + i * 900)
                for i in range(min(days, 5))
            )
            return ShareholderFlowMetrics(
                ticker=key,
                shareholder_count_series=series,
                shareholder_count_change_pct=5.1,
                individual_avg_buy_value=0.8e8,
                individual_avg_sell_value=1.9e8,
                legal_buy_share=0.12,
                legal_net_buy_value=-2.0e9,
                data_quality="usable",
                source="mock:distribution",
                notes=("fixture distribution",),
            )
        return ShareholderFlowMetrics(
            ticker=key or "UNKNOWN",
            data_quality="missing",
            source="mock:empty",
            notes=("no shareholder data in mock",),
        )
