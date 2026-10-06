"""
نمادهای بورس ایران — پیش‌فرض فارسی.

ورودی لاتین (مثل FOOLAD) فقط برای سازگاری به فارسی نگاشت می‌شود.
در CLI و مستندات همیشه نماد فارسی توصیه می‌شود.
"""
from __future__ import annotations

# لاتین → فارسی (اختیاری؛ ترجیح با نماد فارسی تابلو است)
LATIN_TO_PERSIAN: dict[str, str] = {
    "FOOLAD": "فولاد",
    "FMLI": "فملی",
    "MSMI": "فملی",
    "FARS": "فارس",
    "SHASTA": "شستا",
    "KHODRO": "خودرو",
    "IKCO": "خودرو",
    "WEB": "ونوین",
    "SHPN": "شپنا",
    "TAPICO": "تاپیکو",
    "KHSAPA": "خساپا",
    "BTEJARAT": "وتجارت",
    "BMLT": "وبملت",
    "BMI": "وبملت",
    "KAHROBA": "بکهنوج",
    "KGOL": "کگل",
    "CHAD": "کچاد",
    "SHEPNA": "شپنا",
    "SHABAN": "شبان",
    "RENA": "خریخت",
}

# نمونه نمادهای فارسی پرکاربرد (برای مستند و mock)
SAMPLE_PERSIAN_TICKERS: tuple[str, ...] = (
    "فولاد",
    "فملی",
    "شپنا",
    "خودرو",
    "خساپا",
    "شستا",
    "وبملت",
    "وتجارت",
    "کگل",
    "کچاد",
    "فارس",
    "تاپیکو",
)


def to_tse_symbol(ticker: str) -> str:
    """خروجی همیشه ترجیحاً نماد فارسی تابلو."""
    t = (ticker or "").strip()
    if not t:
        return t
    return LATIN_TO_PERSIAN.get(t.upper(), t)


def search_candidates(ticker: str) -> list[str]:
    """ترتیب جست‌وجو: فارسی نگاشت‌شده، ورودی خام."""
    t = (ticker or "").strip()
    if not t:
        return []
    out: list[str] = []
    mapped = to_tse_symbol(t)
    for c in (mapped, t):
        if c and c not in out:
            out.append(c)
    # اگر ورودی لاتین بود upper را هم امتحان نکن — تستمک فارسی می‌خواهد
    return out
