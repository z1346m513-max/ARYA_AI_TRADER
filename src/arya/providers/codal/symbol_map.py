"""نگاشت نماد لاتین TSETMC به نماد فارسی رایج در کدال."""
from __future__ import annotations

# نگاشت دستی نمادهای پرکاربرد؛ در صورت نبود، خود ticker برگردانده می‌شود.
LATIN_TO_CODAL: dict[str, str] = {
    "FOOLAD": "فولاد",
    "FMLI": "فملی",
    "FARS": "فارس",
    "SHASTA": "شستا",
    "KHODRO": "خودرو",
    "WEB": "ونوین",
    "SHIRAZ": "شسپا",
    "SEPAH": "وسپه",
    "KARGAR": "سکارون",
    "DAPCO": "ددانا",
    "SHPN": "شپنا",
    "TAPICO": "تاپیکو",
    "KHSAPA": "خساپا",
    "BTEJARAT": "وتجارت",
    "BMLT": "وبملت",
}


def to_codal_symbol(ticker: str) -> str:
    """تبدیل ticker لاتین به نماد کدال در صورت امکان."""
    t = (ticker or "").strip()
    if not t:
        return t
    upper = t.upper()
    if upper in LATIN_TO_CODAL:
        return LATIN_TO_CODAL[upper]
    # اگر از قبل فارسی است، همان را برگردان
    return t
