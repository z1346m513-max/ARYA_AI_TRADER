"""ShareChangeAnalyzer — smart_money section from internal model.

Thresholds are provisional. missing data never yields a positive signal.
"""
from __future__ import annotations

from arya.models.analysis_result import SectionScore
from arya.models.shareholders import ShareholderFlowMetrics


class ShareChangeAnalyzer:
    section_name = "smart_money"

    def __init__(
        self,
        count_change_threshold_pct: float = 3.0,
        legal_buy_share_threshold: float = 0.30,
        enabled_signals: tuple[str, ...] = ("concentration", "retail_per_capita", "legal_flow"),
    ):
        self.count_change_threshold_pct = count_change_threshold_pct
        self.legal_buy_share_threshold = legal_buy_share_threshold
        self.enabled_signals = set(enabled_signals)

    def analyze(self, metrics: ShareholderFlowMetrics) -> SectionScore:
        if metrics.data_quality == "missing":
            return SectionScore(
                self.section_name,
                0.0,
                0.0,
                {"reasons": [], "data_quality": "missing", "metrics": metrics.as_dict()},
            )

        signals: list[float] = []
        reasons: list[str] = []

        if "concentration" in self.enabled_signals and metrics.shareholder_count_change_pct is not None:
            ch = metrics.shareholder_count_change_pct
            thr = self.count_change_threshold_pct
            if ch <= -thr:
                signals.append(1.0)
                reasons.append(f"count change {ch:.1f}% (accumulation pattern - model assumption)")
            elif ch >= thr:
                signals.append(-1.0)
                reasons.append(f"count change {ch:.1f}% (distribution pattern - model assumption)")
            else:
                signals.append(0.0)
                reasons.append(f"count change {ch:.1f}% within +/-{thr:.0f}%")

        if "retail_per_capita" in self.enabled_signals:
            buy = metrics.individual_avg_buy_value
            sell = metrics.individual_avg_sell_value
            if buy is not None and sell is not None and sell > 0:
                ratio = buy / sell
                if ratio >= 1.5:
                    signals.append(1.0)
                    reasons.append(f"retail buy/sell per-capita ratio {ratio:.2f}")
                elif ratio <= 0.67:
                    signals.append(-1.0)
                    reasons.append(f"weak retail buy vs sell ({ratio:.2f})")
                else:
                    signals.append(0.0)
                    reasons.append(f"neutral retail ratio ({ratio:.2f})")

        if "legal_flow" in self.enabled_signals:
            share = metrics.legal_buy_share
            net = metrics.legal_net_buy_value
            if share is not None and net is not None:
                if share >= self.legal_buy_share_threshold and net > 0:
                    signals.append(1.0)
                    reasons.append(f"legal buy share {share:.0%} with positive net buy")
                elif net < 0:
                    signals.append(-0.5)
                    reasons.append("negative legal net buy")
                else:
                    signals.append(0.0)
                    reasons.append("no strong legal flow signal")

        if not signals:
            return SectionScore(
                self.section_name,
                0.0,
                0.0,
                {
                    "reasons": reasons,
                    "data_quality": metrics.data_quality,
                    "metrics": metrics.as_dict(),
                    "note": "no active signals",
                },
            )

        score = sum(signals) / len(signals)
        q = 1.0 if metrics.data_quality == "usable" else 0.5
        confidence = min(1.0, (len(signals) / 3.0) * q)
        return SectionScore(
            self.section_name,
            round(score, 4),
            round(confidence, 4),
            {
                "reasons": reasons,
                "data_quality": metrics.data_quality,
                "metrics": metrics.as_dict(),
                "signal_count": len(signals),
            },
        )
