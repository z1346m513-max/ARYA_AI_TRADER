from arya.ui.rtl import normalize_persian_text, normalize_ticker, to_ascii_digits


def test_normalize_persian_arabic_keyboard_variants():
    assert normalize_persian_text("  فملی  ") == "فملی"
    assert normalize_persian_text("فملي") == "فملی"
    assert normalize_persian_text("كی") == "کی"


def test_normalize_ticker_removes_zero_width_characters():
    assert normalize_ticker("فم\u200bلی") == "فملی"


def test_to_ascii_digits():
    assert to_ascii_digits("۱۲۳۴۵ ٠١٢") == "12345 012"
