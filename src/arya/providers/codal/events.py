"""
فیلتر رویدادهای مهم کدال: افزایش سرمایه و تغییرات مدیران.

الگو: جست‌وجوی عنوان (پایدارتر از LetterType شناور بین انواع ناشر).
"""
from __future__ import annotations

from arya.models.codal import CodalLetter

# کلیدواژه‌های افزایش سرمایه (اولویت از خاص به عام)
CAPITAL_INCREASE_KEYWORDS: tuple[str, ...] = (
    "افزایش سرمایه",
    "اعلامیه پذیره نویسی",
    "اعلامیه پذیرفته‌نویسی",
    "پذیره نویسی",
    "پذیرفته‌نویسی",
    "حق تقدم",
    "سلب حق تقدم",
    "تسعیر",
)

# کلیدواژه‌های تغییرات مدیران / هیئت مدیره
BOARD_CHANGE_KEYWORDS: tuple[str, ...] = (
    "تغییرات مدیران",
    "تغییر مدیران",
    "هیئت مدیره",
    "هیات مدیره",
    "استعفای",
    "استعفا",
    "انتصاب",
    "عزل",
    "عضو هیئت مدیره",
    "عضو هیات مدیره",
    "مدیرعامل",
    "مدیران اجرایی",
    "ترکیب اعضای",
)


def _title_matches(title: str, keywords: tuple[str, ...]) -> bool:
    t = title or ""
    return any(k in t for k in keywords)


def is_capital_increase(letter: CodalLetter) -> bool:
    return _title_matches(letter.title, CAPITAL_INCREASE_KEYWORDS)


def is_board_change(letter: CodalLetter) -> bool:
    return _title_matches(letter.title, BOARD_CHANGE_KEYWORDS)


def filter_capital_increase(letters: list[CodalLetter]) -> list[CodalLetter]:
    return [x for x in letters if is_capital_increase(x)]


def filter_board_changes(letters: list[CodalLetter]) -> list[CodalLetter]:
    return [x for x in letters if is_board_change(x)]


def classify_event(letter: CodalLetter) -> str | None:
    if is_capital_increase(letter):
        return "capital_increase"
    if is_board_change(letter):
        return "board_change"
    return None
