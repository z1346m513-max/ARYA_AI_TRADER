"""نگاشت نماد لاتین → فارسی برای جست‌وجوی TSETMC / کدال."""
from __future__ import annotations

LATIN_TO_PERSIAN: dict[str, str] = {
    "FOOLAD": "فولاد",
    "FMLI": "فملی",
    "FARS": "فارس",
    "SHASTA": "شستا",
    "KHODRO": "خودرو",
    "WEB": "ونوین",
    "SHPN": "شپنا",
    "TAPICO": "تاپیکو",
    "KHSAPA": "خساپا",
    "BTEJARAT": "وتجارت",
    "BMLT": "وبملت",
    "KAHROBA": "بکهنوج",
}


def to_tse_symbol(ticker: str) -> str:
    """برای API تستمک نماد فارسی برمی‌گرداند در صورت وجود نگاشت."""
    t = (ticker or "").strip()
    if not t:
        return t
    return LATIN_TO_PERSIAN.get(t.upper(), t)


def search_candidates(ticker: str) -> list[str]:
    """ترتیب تلاش برای جست‌وجو: فارسی نگاشت‌شده، اصل، upper."""
    t = (ticker or "").strip()
    if not t:
        return []
    out: list[str] = []
    mapped = to_tse_symbol(t)
    for c in (mapped, t, t.upper()):
        if c and c not in out:
            out.append(c)
    return out
