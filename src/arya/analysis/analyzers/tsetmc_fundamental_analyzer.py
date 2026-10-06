"""بنیادی سبک از صفحه جزئیات TSETMC (EPS / P/E) — بدون صورت مالی کدال."""
from __future__ import annotations

from arya.models.analysis_result import SectionScore
from arya.providers.market.instrument_detail import InstrumentDetail


class TsetmcFundamentalAnalyzer:
    section_name = "fundamental"

    def analyze(self, detail: InstrumentDetail) -> SectionScore:
        reasons: list[str] = []
        score = 0.0
        confidence = 0.2

        pe = detail.pe
        sector_pe = detail.sector_pe
        eps = detail.eps

        if eps is not None:
            reasons.append(f"EPS تقریبی: {eps:,.0f}")
        if pe is not None and pe > 0:
            reasons.append(f"P/E: {pe:.2f}")
            if sector_pe is not None and sector_pe > 0:
                reasons.append(f"P/E گروه: {sector_pe:.2f}")
                # ارزان‌تر از گروه → مثبت ملایم
                rel = (sector_pe - pe) / sector_pe
                score = round(max(-0.5, min(0.5, rel * 0.8)), 4)
                confidence = 0.45
                if pe < sector_pe * 0.7:
                    reasons.append("P/E به‌طور محسوس زیر گروه")
                elif pe > sector_pe * 1.3:
                    reasons.append("P/E بالاتر از گروه")
            else:
                # بدون گروه: P/E خیلی بالا محتاطانه منفی
                if pe > 25:
                    score = -0.15
                    reasons.append("P/E نسبتاً بالا")
                elif pe < 8:
                    score = 0.2
                    reasons.append("P/E پایین")
                confidence = 0.35

        if detail.free_float_pct is not None:
            reasons.append(f"شناوری: {detail.free_float_pct:.0f}%")

        if not reasons:
            return SectionScore(
                self.section_name,
                0.0,
                0.0,
                {"reasons": [], "data_quality": "missing"},
            )

        return SectionScore(
            self.section_name,
            score,
            confidence,
            {"reasons": reasons[:6], "data_quality": "tsetmc_info"},
        )
