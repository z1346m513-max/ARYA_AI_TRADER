"""
ماژول تحلیل بنیادی: محاسبه‌ی نسبت‌های مالی.

این ماژول ۱۸ نسبت کلیدی مالی را پیاده‌سازی می‌کند:
- ارزش بازار: P/E، P/BV، P/S، P/CF، PEG
- سودآوری: حاشیه سود ناخالص، حاشیه سود خالص، ROE، ROA
- نقدینگی: نسبت جاری، نسبت آنی، نسبت نقد
- اهرمی: بدهی به حقوق صاحبان سهام، بدهی به دارایی، پوشش هزینه بهره
- کارایی: گردش موجودی، گردش دارایی ثابت، دوره وصول مطالبات
- تقسیم سود: نسبت پرداخت سود سهام

منابع: فایل‌های Google Drive کاربر شامل فرمول‌های نسبت‌های مالی و سند اهمیت
نسبت‌های ارزش بازار برای سرمایه‌گذاری.
"""
from __future__ import annotations

from arya.fundamental.models import FinancialData
from arya.fundamental.ratios import (
    RatioResult,
    calculate_all_ratios,
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
)

__all__ = [
    "FinancialData",
    "RatioResult",
    "calculate_all_ratios",
    "price_to_earnings",
    "price_to_book",
    "price_to_sales",
    "price_to_cash_flow",
    "peg_ratio",
    "gross_profit_margin",
    "net_profit_margin",
    "return_on_equity",
    "return_on_assets",
    "current_ratio",
    "quick_ratio",
    "cash_ratio",
    "debt_to_equity",
    "debt_to_asset",
    "interest_coverage",
    "inventory_turnover",
    "fixed_asset_turnover",
    "receivables_collection_period",
    "dividend_payout_ratio",
]
