"""Presentation translations for ARYA console output.

Internal enums/keys remain stable English identifiers; only the UI labels are
localized here. The default language is Persian (fa).
"""

from __future__ import annotations

from arya.models.analysis_result import Action

ACTION_FA = {
    Action.BUY: "خرید",
    Action.HOLD: "نگهداری",
    Action.SELL: "فروش",
}

RISK_FA = {
    "low": "کم",
    "medium": "متوسط",
    "high": "زیاد",
}

SECTION_FA = {
    "technical": "فنی",
    "fundamental": "بنیادی",
    "news": "اخبار",
    "codal": "کدال",
    "smart_money": "پول هوشمند",
    "liquidity_flow": "جریان نقدینگی",
    "risk": "ریسک",
}

MARKET_FA = {
    "stock": "بورس ایران",
    "crypto": "ارز دیجیتال",
    "forex": "فارکس",
}

ALERT_FA = {
    "price_above_sma": "قیمت بالاتر از میانگین ساده",
    "price_above_ema": "قیمت بالاتر از میانگین نمایی",
    "rsi_overbought": "شاخص RSI در محدوده اشباع خرید",
    "rsi_oversold": "شاخص RSI در محدوده اشباع فروش",
}


def translate_action(action: Action, language: str = "fa") -> str:
    if language == "en":
        return action.name.title()
    return ACTION_FA.get(action, action.value)


def translate_risk(level: str, language: str = "fa") -> str:
    if language == "en":
        return level
    return RISK_FA.get(level, level)


def translate_section(section: str, language: str = "fa") -> str:
    if language == "en":
        return section
    return SECTION_FA.get(section, section)


def translate_market(market: str, language: str = "fa") -> str:
    if language == "en":
        return market
    return MARKET_FA.get(market, market)


def translate_alert(alert: str, language: str = "fa") -> str:
    if language == "en":
        return alert
    return ALERT_FA.get(alert, alert)
