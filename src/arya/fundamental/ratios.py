"""
محاسبه‌ی نسبت‌های مالی.

این ماژول ۱۸ نسبت کلیدی مالی را پیاده‌سازی می‌کند که در پوشه‌ی Google Drive
کاربر موجود هستند. هر نسبت یک RatioResult برمی‌گرداند که شامل مقدار، فرمول،
وضعیت و هشدارهاست.

دسته‌بندی نسبت‌ها:
- ارزش بازار: P/E، P/BV، P/S، P/CF، PEG
- سودآوری: حاشیه سود ناخالص، حاشیه سود خالص، ROE، ROA
- نقدینگی: نسبت جاری، نسبت آنی، نسبت نقد
- اهرمی: بدهی به حقوق صاحبان سهام، بدهی به دارایی، پوشش هزینه بهره
- کارایی: گردش موجودی، گردش دارایی ثابت، دوره وصول مطالبات
- تقسیم سود: نسبت پرداخت سود سهام

قواعد:
- تقسیم بر صفر یا داده ناقص: value=None، status=UNAVAILABLE
- P/E با EPS منفی: NOT_MEANINGFUL
- PEG با رشد صفر یا منفی: NOT_MEANINGFUL
- پوشش هزینه بهره با بهره صفر: NOT_MEANINGFUL
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from arya.fundamental.models import FinancialData

RatioStatus = Literal["OK", "UNAVAILABLE", "NOT_MEANINGFUL"]


@dataclass(frozen=True)
class RatioResult:
    """نتیجه‌ی محاسبه‌ی یک نسبت مالی."""

    key: str
    name: str
    category: str
    value: float | None
    formula: str
    status: RatioStatus
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "category": self.category,
            "value": self.value,
            "formula": self.formula,
            "status": self.status,
            "warnings": list(self.warnings),
        }


def _safe_div(
    numerator: float | None,
    denominator: float | None,
) -> tuple[float | None, bool]:
    """
    تقسیم امن. برمی‌گرداند: (نتیجه یا None, آیا مخرج صفر بود).

    اگر numerator یا denominator برابر None باشد: (None, False)
    اگر denominator برابر صفر باشد: (None, True)
    """
    if numerator is None or denominator is None:
        return None, False
    if denominator == 0:
        return None, True
    return numerator / denominator, False


# ═══════════════════════════════════════════════════════════════
#  نسبت‌های ارزش بازار
# ═══════════════════════════════════════════════════════════════

def price_to_earnings(data: FinancialData) -> RatioResult:
    """P/E = قیمت بازار هر سهم / سود هر سهم"""
    if data.eps is not None and data.eps <= 0:
        return RatioResult(
            key="pe",
            name="نسبت قیمت به درآمد (P/E)",
            category="market_value",
            value=None,
            formula="قیمت بازار / EPS",
            status="NOT_MEANINGFUL",
            warnings=["EPS صفر یا منفی است؛ P/E معنا ندارد."],
        )
    value, zero_div = _safe_div(data.market_price, data.eps)
    if value is None and zero_div:
        return RatioResult(
            key="pe", name="نسبت قیمت به درآمد (P/E)", category="market_value",
            value=None, formula="قیمت بازار / EPS", status="NOT_MEANINGFUL",
            warnings=["EPS صفر است."],
        )
    if value is None:
        return RatioResult(
            key="pe", name="نسبت قیمت به درآمد (P/E)", category="market_value",
            value=None, formula="قیمت بازار / EPS", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="pe", name="نسبت قیمت به درآمد (P/E)", category="market_value",
        value=value, formula="قیمت بازار / EPS", status="OK",
    )


def price_to_book(data: FinancialData) -> RatioResult:
    """P/BV = قیمت بازار / ارزش دفتری هر سهم"""
    warnings: list[str] = []
    # مسیر per-share
    if data.market_price is not None and data.book_value_per_share is not None:
        if data.book_value_per_share <= 0:
            return RatioResult(
                key="pb", name="نسبت ارزش دفتری (P/BV)", category="market_value",
                value=None, formula="قیمت بازار / ارزش دفتری هر سهم",
                status="NOT_MEANINGFUL",
                warnings=["ارزش دفتری هر سهم صفر یا منفی است."],
            )
        value = data.market_price / data.book_value_per_share
        return RatioResult(
            key="pb", name="نسبت ارزش دفتری (P/BV)", category="market_value",
            value=value, formula="قیمت بازار / ارزش دفتری هر سهم", status="OK",
        )
    # مسیر market-cap
    mc = data.market_cap_value
    if mc is not None and data.equity is not None and data.equity > 0:
        value = mc / data.equity
        return RatioResult(
            key="pb", name="نسبت ارزش دفتری (P/BV)", category="market_value",
            value=value, formula="ارزش بازار / حقوق صاحبان سهام", status="OK",
            warnings=["از مسیر market_cap / equity محاسبه شد."],
        )
    return RatioResult(
        key="pb", name="نسبت ارزش دفتری (P/BV)", category="market_value",
        value=None, formula="قیمت بازار / ارزش دفتری هر سهم", status="UNAVAILABLE",
        warnings=["داده‌ی کافی موجود نیست."],
    )


def price_to_sales(data: FinancialData) -> RatioResult:
    """P/S = قیمت بازار هر سهم / فروش هر سهم"""
    warnings: list[str] = []
    # مسیر per-share: قیمت / (فروش / تعداد سهم)
    if data.market_price is not None and data.revenue is not None and data.shares_outstanding is not None:
        if data.shares_outstanding > 0:
            sales_per_share = data.revenue / data.shares_outstanding
            value = data.market_price / sales_per_share
            return RatioResult(
                key="ps", name="نسبت قیمت به فروش (P/S)", category="market_value",
                value=value, formula="قیمت بازار / فروش هر سهم", status="OK",
            )
    # مسیر market-cap
    mc = data.market_cap_value
    if mc is not None and data.revenue is not None and data.revenue > 0:
        value = mc / data.revenue
        return RatioResult(
            key="ps", name="نسبت قیمت به فروش (P/S)", category="market_value",
            value=value, formula="ارزش بازار / کل فروش", status="OK",
            warnings=["از مسیر market_cap / revenue محاسبه شد."],
        )
    return RatioResult(
        key="ps", name="نسبت قیمت به فروش (P/S)", category="market_value",
        value=None, formula="قیمت بازار / فروش هر سهم", status="UNAVAILABLE",
        warnings=["داده‌ی کافی موجود نیست."],
    )


def price_to_cash_flow(data: FinancialData) -> RatioResult:
    """P/CF = قیمت بازار / جریان نقدی هر سهم"""
    # مسیر per-share
    if data.market_price is not None and data.cash_flow_per_share is not None:
        if data.cash_flow_per_share <= 0:
            return RatioResult(
                key="pcf", name="قیمت به جریان نقدینگی (P/CF)", category="market_value",
                value=None, formula="قیمت بازار / جریان نقدی هر سهم",
                status="NOT_MEANINGFUL",
                warnings=["جریان نقدی هر سهم صفر یا منفی است."],
            )
        value = data.market_price / data.cash_flow_per_share
        return RatioResult(
            key="pcf", name="قیمت به جریان نقدینگی (P/CF)", category="market_value",
            value=value, formula="قیمت بازار / جریان نقدی هر سهم", status="OK",
        )
    # مسیر market-cap
    mc = data.market_cap_value
    if mc is not None and data.operating_cash_flow is not None and data.operating_cash_flow > 0:
        value = mc / data.operating_cash_flow
        return RatioResult(
            key="pcf", name="قیمت به جریان نقدینگی (P/CF)", category="market_value",
            value=value, formula="ارزش بازار / جریان نقدی عملیاتی", status="OK",
            warnings=["از مسیر market_cap / operating_cash_flow محاسبه شد."],
        )
    return RatioResult(
        key="pcf", name="قیمت به جریان نقدینگی (P/CF)", category="market_value",
        value=None, formula="قیمت بازار / جریان نقدی هر سهم", status="UNAVAILABLE",
        warnings=["داده‌ی کافی موجود نیست."],
    )


def peg_ratio(data: FinancialData) -> RatioResult:
    """PEG = P/E / نرخ رشد سالانه سود (به درصد)"""
    pe_result = price_to_earnings(data)
    if pe_result.status != "OK" or pe_result.value is None:
        return RatioResult(
            key="peg", name="نسبت PEG", category="market_value",
            value=None, formula="P/E / نرخ رشد سالانه سود",
            status=pe_result.status,
            warnings=["P/E قابل محاسبه نیست."],
        )
    if data.earnings_growth_rate_percent is None:
        return RatioResult(
            key="peg", name="نسبت PEG", category="market_value",
            value=None, formula="P/E / نرخ رشد سالانه سود", status="UNAVAILABLE",
            warnings=["نرخ رشد سود موجود نیست."],
        )
    if data.earnings_growth_rate_percent <= 0:
        return RatioResult(
            key="peg", name="نسبت PEG", category="market_value",
            value=None, formula="P/E / نرخ رشد سالانه سود",
            status="NOT_MEANINGFUL",
            warnings=["نرخ رشد سود صفر یا منفی است؛ PEG معنا ندارد."],
        )
    value = pe_result.value / data.earnings_growth_rate_percent
    return RatioResult(
        key="peg", name="نسبت PEG", category="market_value",
        value=value, formula="P/E / نرخ رشد سالانه سود", status="OK",
    )


# ═══════════════════════════════════════════════════════════════
#  نسبت‌های سودآوری
# ═══════════════════════════════════════════════════════════════

def gross_profit_margin(data: FinancialData) -> RatioResult:
    """حاشیه سود ناخالص = (فروش - بهای تمام‌شده) / فروش"""
    gp = data.gross_profit_value
    value, zero_div = _safe_div(gp, data.revenue)
    if value is None and zero_div:
        return RatioResult(
            key="gross_margin", name="حاشیه سود ناخالص", category="profitability",
            value=None, formula="(فروش - COGS) / فروش", status="NOT_MEANINGFUL",
            warnings=["فروش صفر است."],
        )
    if value is None:
        return RatioResult(
            key="gross_margin", name="حاشیه سود ناخالص", category="profitability",
            value=None, formula="(فروش - COGS) / فروش", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="gross_margin", name="حاشیه سود ناخالص", category="profitability",
        value=value, formula="(فروش - COGS) / فروش", status="OK",
    )


def net_profit_margin(data: FinancialData) -> RatioResult:
    """حاشیه سود خالص = سود خالص / فروش"""
    value, zero_div = _safe_div(data.net_income, data.revenue)
    if value is None and zero_div:
        return RatioResult(
            key="net_margin", name="حاشیه سود خالص", category="profitability",
            value=None, formula="سود خالص / فروش", status="NOT_MEANINGFUL",
            warnings=["فروش صفر است."],
        )
    if value is None:
        return RatioResult(
            key="net_margin", name="حاشیه سود خالص", category="profitability",
            value=None, formula="سود خالص / فروش", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="net_margin", name="حاشیه سود خالص", category="profitability",
        value=value, formula="سود خالص / فروش", status="OK",
    )


def return_on_equity(data: FinancialData) -> RatioResult:
    """ROE = سود خالص / حقوق صاحبان سهام"""
    equity = data.avg_equity or data.equity
    warnings: list[str] = []
    if data.avg_equity is None and data.equity is not None:
        warnings.append("از مقدار پایان دوره استفاده شد؛ میانگین موجود نیست.")
    value, zero_div = _safe_div(data.net_income, equity)
    if value is None and zero_div:
        return RatioResult(
            key="roe", name="بازده حقوق صاحبان سهام (ROE)", category="profitability",
            value=None, formula="سود خالص / حقوق صاحبان سهام", status="NOT_MEANINGFUL",
            warnings=["حقوق صاحبان سهام صفر است."],
        )
    if value is None:
        return RatioResult(
            key="roe", name="بازده حقوق صاحبان سهام (ROE)", category="profitability",
            value=None, formula="سود خالص / حقوق صاحبان سهام", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="roe", name="بازده حقوق صاحبان سهام (ROE)", category="profitability",
        value=value, formula="سود خالص / حقوق صاحبان سهام", status="OK",
        warnings=warnings,
    )


def return_on_assets(data: FinancialData) -> RatioResult:
    """ROA = سود خالص / کل دارایی‌ها"""
    assets = data.avg_total_assets or data.total_assets
    warnings: list[str] = []
    if data.avg_total_assets is None and data.total_assets is not None:
        warnings.append("از مقدار پایان دوره استفاده شد؛ میانگین موجود نیست.")
    value, zero_div = _safe_div(data.net_income, assets)
    if value is None and zero_div:
        return RatioResult(
            key="roa", name="بازده دارایی‌ها (ROA)", category="profitability",
            value=None, formula="سود خالص / کل دارایی‌ها", status="NOT_MEANINGFUL",
            warnings=["کل دارایی‌ها صفر است."],
        )
    if value is None:
        return RatioResult(
            key="roa", name="بازده دارایی‌ها (ROA)", category="profitability",
            value=None, formula="سود خالص / کل دارایی‌ها", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="roa", name="بازده دارایی‌ها (ROA)", category="profitability",
        value=value, formula="سود خالص / کل دارایی‌ها", status="OK",
        warnings=warnings,
    )


# ═══════════════════════════════════════════════════════════════
#  نسبت‌های نقدینگی
# ═══════════════════════════════════════════════════════════════

def current_ratio(data: FinancialData) -> RatioResult:
    """نسبت جاری = دارایی جاری / بدهی جاری"""
    value, zero_div = _safe_div(data.current_assets, data.current_liabilities)
    if value is None and zero_div:
        return RatioResult(
            key="current_ratio", name="نسبت جاری", category="liquidity",
            value=None, formula="دارایی جاری / بدهی جاری", status="NOT_MEANINGFUL",
            warnings=["بدهی جاری صفر است."],
        )
    if value is None:
        return RatioResult(
            key="current_ratio", name="نسبت جاری", category="liquidity",
            value=None, formula="دارایی جاری / بدهی جاری", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="current_ratio", name="نسبت جاری", category="liquidity",
        value=value, formula="دارایی جاری / بدهی جاری", status="OK",
    )


def quick_ratio(data: FinancialData) -> RatioResult:
    """نسبت آنی = (دارایی جاری - موجودی) / بدهی جاری"""
    if data.current_assets is None or data.current_liabilities is None:
        return RatioResult(
            key="quick_ratio", name="نسبت آنی", category="liquidity",
            value=None, formula="(دارایی جاری - موجودی) / بدهی جاری",
            status="UNAVAILABLE", warnings=["داده‌ی کافی موجود نیست."],
        )
    inv = data.inventory or 0.0
    numerator = data.current_assets - inv
    if data.current_liabilities == 0:
        return RatioResult(
            key="quick_ratio", name="نسبت آنی", category="liquidity",
            value=None, formula="(دارایی جاری - موجودی) / بدهی جاری",
            status="NOT_MEANINGFUL", warnings=["بدهی جاری صفر است."],
        )
    value = numerator / data.current_liabilities
    return RatioResult(
        key="quick_ratio", name="نسبت آنی", category="liquidity",
        value=value, formula="(دارایی جاری - موجودی) / بدهی جاری", status="OK",
    )


def cash_ratio(data: FinancialData) -> RatioResult:
    """نسبت نقد = نقد / بدهی جاری"""
    value, zero_div = _safe_div(data.cash, data.current_liabilities)
    if value is None and zero_div:
        return RatioResult(
            key="cash_ratio", name="نسبت نقد", category="liquidity",
            value=None, formula="نقد / بدهی جاری", status="NOT_MEANINGFUL",
            warnings=["بدهی جاری صفر است."],
        )
    if value is None:
        return RatioResult(
            key="cash_ratio", name="نسبت نقد", category="liquidity",
            value=None, formula="نقد / بدهی جاری", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="cash_ratio", name="نسبت نقد", category="liquidity",
        value=value, formula="نقد / بدهی جاری", status="OK",
    )


# ═══════════════════════════════════════════════════════════════
#  نسبت‌های اهرمی
# ═══════════════════════════════════════════════════════════════

def debt_to_equity(data: FinancialData) -> RatioResult:
    """بدهی به حقوق صاحبان سهام = کل بدهی / حقوق صاحبان سهام"""
    value, zero_div = _safe_div(data.debt, data.equity)
    if value is None and zero_div:
        return RatioResult(
            key="debt_to_equity", name="بدهی به حقوق صاحبان سهام",
            category="leverage", value=None,
            formula="کل بدهی / حقوق صاحبان سهام", status="NOT_MEANINGFUL",
            warnings=["حقوق صاحبان سهام صفر است."],
        )
    if value is None:
        # مسیر جایگزین: total_liabilities / equity
        value2, zd2 = _safe_div(data.total_liabilities, data.equity)
        if value2 is not None:
            return RatioResult(
                key="debt_to_equity", name="بدهی به حقوق صاحبان سهام",
                category="leverage", value=value2,
                formula="کل بدهی / حقوق صاحبان سهام", status="OK",
                warnings=["از total_liabilities به جای debt استفاده شد."],
            )
        return RatioResult(
            key="debt_to_equity", name="بدهی به حقوق صاحبان سهام",
            category="leverage", value=None,
            formula="کل بدهی / حقوق صاحبان سهام", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="debt_to_equity", name="بدهی به حقوق صاحبان سهام",
        category="leverage", value=value,
        formula="کل بدهی / حقوق صاحبان سهام", status="OK",
    )


def debt_to_asset(data: FinancialData) -> RatioResult:
    """بدهی به دارایی = کل بدهی / کل دارایی‌ها"""
    debt = data.debt or data.total_liabilities
    value, zero_div = _safe_div(debt, data.total_assets)
    if value is None and zero_div:
        return RatioResult(
            key="debt_to_asset", name="بدهی به دارایی", category="leverage",
            value=None, formula="کل بدهی / کل دارایی‌ها", status="NOT_MEANINGFUL",
            warnings=["کل دارایی‌ها صفر است."],
        )
    if value is None:
        return RatioResult(
            key="debt_to_asset", name="بدهی به دارایی", category="leverage",
            value=None, formula="کل بدهی / کل دارایی‌ها", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="debt_to_asset", name="بدهی به دارایی", category="leverage",
        value=value, formula="کل بدهی / کل دارایی‌ها", status="OK",
    )


def interest_coverage(data: FinancialData) -> RatioResult:
    """پوشش هزینه بهره = سود عملیاتی / هزینه بهره"""
    if data.interest_expense is not None and data.interest_expense == 0:
        return RatioResult(
            key="interest_coverage", name="پوشش هزینه بهره", category="leverage",
            value=None, formula="سود عملیاتی / هزینه بهره",
            status="NOT_MEANINGFUL",
            warnings=["هزینه بهره صفر است؛ نسبت معنا ندارد."],
        )
    value, zero_div = _safe_div(data.operating_income, data.interest_expense)
    if value is None and zero_div:
        return RatioResult(
            key="interest_coverage", name="پوشش هزینه بهره", category="leverage",
            value=None, formula="سود عملیاتی / هزینه بهره",
            status="NOT_MEANINGFUL",
            warnings=["هزینه بهره صفر است."],
        )
    if value is None:
        return RatioResult(
            key="interest_coverage", name="پوشش هزینه بهره", category="leverage",
            value=None, formula="سود عملیاتی / هزینه بهره",
            status="UNAVAILABLE", warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="interest_coverage", name="پوشش هزینه بهره", category="leverage",
        value=value, formula="سود عملیاتی / هزینه بهره", status="OK",
    )


# ═══════════════════════════════════════════════════════════════
#  نسبت‌های کارایی
# ═══════════════════════════════════════════════════════════════

def inventory_turnover(data: FinancialData) -> RatioResult:
    """گردش موجودی = بهای تمام‌شده / میانگین موجودی"""
    inv = data.avg_inventory or data.inventory
    warnings: list[str] = []
    if data.avg_inventory is None and data.inventory is not None:
        warnings.append("از مقدار پایان دوره استفاده شد؛ میانگین موجود نیست.")
    value, zero_div = _safe_div(data.cost_of_goods_sold, inv)
    if value is None and zero_div:
        return RatioResult(
            key="inventory_turnover", name="گردش موجودی", category="efficiency",
            value=None, formula="COGS / میانگین موجودی", status="NOT_MEANINGFUL",
            warnings=["موجودی صفر است."],
        )
    if value is None:
        return RatioResult(
            key="inventory_turnover", name="گردش موجودی", category="efficiency",
            value=None, formula="COGS / میانگین موجودی", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="inventory_turnover", name="گردش موجودی", category="efficiency",
        value=value, formula="COGS / میانگین موجودی", status="OK",
        warnings=warnings,
    )


def fixed_asset_turnover(data: FinancialData) -> RatioResult:
    """گردش دارایی ثابت = فروش / میانگین دارایی ثابت"""
    fa = data.avg_fixed_assets or data.fixed_assets
    warnings: list[str] = []
    if data.avg_fixed_assets is None and data.fixed_assets is not None:
        warnings.append("از مقدار پایان دوره استفاده شد؛ میانگین موجود نیست.")
    value, zero_div = _safe_div(data.revenue, fa)
    if value is None and zero_div:
        return RatioResult(
            key="fixed_asset_turnover", name="گردش دارایی ثابت",
            category="efficiency", value=None,
            formula="فروش / میانگین دارایی ثابت", status="NOT_MEANINGFUL",
            warnings=["دارایی ثابت صفر است."],
        )
    if value is None:
        return RatioResult(
            key="fixed_asset_turnover", name="گردش دارایی ثابت",
            category="efficiency", value=None,
            formula="فروش / میانگین دارایی ثابت", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="fixed_asset_turnover", name="گردش دارایی ثابت",
        category="efficiency", value=value,
        formula="فروش / میانگین دارایی ثابت", status="OK",
        warnings=warnings,
    )


def receivables_collection_period(data: FinancialData) -> RatioResult:
    """دوره وصول مطالبات = (میانگین مطالبات / فروش) × ۳۶۵"""
    rec = data.avg_receivables or data.receivables
    warnings: list[str] = []
    if data.avg_receivables is None and data.receivables is not None:
        warnings.append("از مقدار پایان دوره استفاده شد؛ میانگین موجود نیست.")
    value, zero_div = _safe_div(rec, data.revenue)
    if value is None and zero_div:
        return RatioResult(
            key="receivables_period", name="دوره وصول مطالبات",
            category="efficiency", value=None,
            formula="(مطالبات / فروش) × ۳۶۵", status="NOT_MEANINGFUL",
            warnings=["فروش صفر است."],
        )
    if value is None:
        return RatioResult(
            key="receivables_period", name="دوره وصول مطالبات",
            category="efficiency", value=None,
            formula="(مطالبات / فروش) × ۳۶۵", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    days = value * 365
    return RatioResult(
        key="receivables_period", name="دوره وصول مطالبات",
        category="efficiency", value=days,
        formula="(مطالبات / فروش) × ۳۶۵", status="OK",
        warnings=warnings,
    )


# ═══════════════════════════════════════════════════════════════
#  نسبت‌های تقسیم سود
# ═══════════════════════════════════════════════════════════════

def dividend_payout_ratio(data: FinancialData) -> RatioResult:
    """نسبت پرداخت سود = سود تقسیمی هر سهم / سود هر سهم"""
    if data.eps is not None and data.eps <= 0:
        return RatioResult(
            key="payout_ratio", name="نسبت پرداخت سود", category="dividend",
            value=None, formula="DPS / EPS", status="NOT_MEANINGFUL",
            warnings=["EPS صفر یا منفی است."],
        )
    value, zero_div = _safe_div(data.dividend_per_share, data.eps)
    if value is None and zero_div:
        return RatioResult(
            key="payout_ratio", name="نسبت پرداخت سود", category="dividend",
            value=None, formula="DPS / EPS", status="NOT_MEANINGFUL",
            warnings=["EPS صفر است."],
        )
    if value is None:
        return RatioResult(
            key="payout_ratio", name="نسبت پرداخت سود", category="dividend",
            value=None, formula="DPS / EPS", status="UNAVAILABLE",
            warnings=["داده‌ی کافی موجود نیست."],
        )
    return RatioResult(
        key="payout_ratio", name="نسبت پرداخت سود", category="dividend",
        value=value, formula="DPS / EPS", status="OK",
    )


# ═══════════════════════════════════════════════════════════════
#  تابع تجمیعی
# ═══════════════════════════════════════════════════════════════

_ALL_RATIO_FUNCS = [
    price_to_earnings,
    price_to_book,
    price_to_sales,
    price_to_cash_flow,
    peg_ratio,
    gross_profit_margin,
    net_profit_margin,
    return_on_equity,
    return_on_assets,
    current_ratio,
    quick_ratio,
    cash_ratio,
    debt_to_equity,
    debt_to_asset,
    interest_coverage,
    inventory_turnover,
    fixed_asset_turnover,
    receivables_collection_period,
    dividend_payout_ratio,
]


def calculate_all_ratios(data: FinancialData) -> dict[str, RatioResult]:
    """
    تمام ۱۸ نسبت مالی را محاسبه می‌کند.

    Args:
        data: داده‌ی بنیادی شرکت.

    Returns:
        دیکشنری از key به RatioResult.
    """
    results: dict[str, RatioResult] = {}
    for func in _ALL_RATIO_FUNCS:
        result = func(data)
        results[result.key] = result
    return results
