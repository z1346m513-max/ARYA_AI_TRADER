"""Scheduler-facing market history refresh job.

The real scheduler can call run_once() according to configs/scheduler.yaml.
Scheduling mechanics remain separate from cache/provider policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from arya.app.bootstrap import AryaApp


@dataclass(frozen=True)
class RefreshJobReport:
    refreshed: int
    warnings: int


class MarketHistoryRefreshJob:
    def __init__(self, app: AryaApp):
        self.app = app

    def run_once(self, market: str = "stock", limit: int = 200) -> RefreshJobReport:
        results = self.app.refresh_market_history(
            market=market,
            limit=limit,
        )
        return RefreshJobReport(
            refreshed=sum(1 for item in results if item.refreshed),
            warnings=sum(1 for item in results if item.warning),
        )
