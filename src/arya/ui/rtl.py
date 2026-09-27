"""Persian/RTL helpers shared by the GUI presentation layer."""

from __future__ import annotations

import re

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_ARABIC_TO_PERSIAN = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک"})

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def normalize_persian_text(value: str) -> str:
    """Normalize common Arabic/Persian keyboard variants without changing meaning."""
    text = value.translate(_ARABIC_TO_PERSIAN)
    text = _ZERO_WIDTH_RE.sub("", text)
    return " ".join(text.strip().split())


def normalize_ticker(value: str) -> str:
    """Normalize a ticker typed with Persian/Arabic keyboard variants."""
    return normalize_persian_text(value)


def to_ascii_digits(value: str) -> str:
    """Convert Persian/Arabic numerals to ASCII numerals for parsing."""
    return value.translate(_PERSIAN_DIGITS).translate(_ARABIC_DIGITS)
