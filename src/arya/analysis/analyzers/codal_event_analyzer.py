"""
تحلیل رویدادمحور کدال — تمرکز روی افزایش سرمایه و تغییرات مدیران.
"""
from __future__ import annotations

from arya.models.analysis_result import SectionScore
from arya.models.codal import CodalLetter
from arya.providers.codal.events import classify_event

# (کلمه کلیدی, امتیاز [-1,1], برچسب) — خاص‌ترها اول
_RULES: list[tuple[str, float, str]] = [
    ("افزایش سرمایه از محل سود", 0.4, "افزایش سرمایه/سود انباشته"),
    ("افزایش سرمایه از محل تجدید ارزیابی", 0.25, "افزایش سرمایه/تجدید ارزیابی"),
    ("افزایش سرمایه از محل مطالبات", 0.3, "افزایش سرمایه/مطالبات"),
    ("افزایش سرمایه از محل آورده", 0.35, "افزایش سرمایه/آورده نقدی"),
    ("افزایش سرمایه", 0.35, "افزایش سرمایه"),
    ("حق تقدم", 0.2, "حق تقدم"),
    ("سلب حق تقدم", 0.15, "سلب حق تقدم"),
    ("پذیره نویسی", 0.2, "پذیره‌نویسی"),
    ("پذیرفته‌نویسی", 0.2, "پذیره‌نویسی"),
    ("تغییرات مدیران", 0.05, "تغییرات مدیران"),
    ("تغییر مدیران", 0.05, "تغییرات مدیران"),
    ("استعفای مدیرعامل", -0.15, "استعفای مدیرعامل"),
    ("استعفا مدیرعامل", -0.15, "استعفای مدیرعامل"),
    ("عزل مدیرعامل", -0.2, "عزل مدیرعامل"),
    ("انتصاب مدیرعامل", 0.1, "انتصاب مدیرعامل"),
    ("هیئت مدیره", 0.05, "هیئت مدیره"),
    ("هیات مدیره", 0.05, "هیئت مدیره"),
    ("استعفا", -0.1, "استعفا"),
    ("انتصاب", 0.05, "انتصاب"),
    ("تسعیر", 0.15, "تسعیر ارز"),
    ("سود نقدی", 0.25, "سود نقدی"),
    ("تقسیم سود", 0.25, "تقسیم سود"),
    ("مجمع", 0.1, "مجمع"),
    ("توقف نماد", -0.4, "توقف نماد"),
    ("عدم اظهار نظر", -0.3, "عدم اظهارنظر حسابرس"),
    ("مشروط", -0.2, "گزارش مشروط"),
]


class CodalEventAnalyzer:
    section_name = "codal"

    def analyze(self, letters: list[CodalLetter], *, max_letters: int = 12) -> SectionScore:
        if not letters:
            return SectionScore(
                self.section_name,
                0.0,
                0.0,
                {
                    "reasons": [],
                    "data_quality": "missing",
                    "count": 0,
                    "capital_increase": 0,
                    "board_change": 0,
                },
            )

        scores: list[float] = []
        reasons: list[str] = []
        seen_tags: set[str] = set()
        n_capital = 0
        n_board = 0

        for letter in letters[:max_letters]:
            event = classify_event(letter)
            if event == "capital_increase":
                n_capital += 1
            elif event == "board_change":
                n_board += 1

            title = letter.title or ""
            matched = False
            for keyword, score, tag in _RULES:
                if keyword in title:
                    matched = True
                    scores.append(score)
                    if tag not in seen_tags:
                        seen_tags.add(tag)
                        short = title[:60] + ("…" if len(title) > 60 else "")
                        reasons.append(f"کدال/{tag}: {short}")
                    break
            if not matched and event and len(reasons) < 5:
                short = title[:50] + ("…" if len(title) > 50 else "")
                reasons.append(f"کدال/{event}: {short}")

        details = {
            "reasons": reasons[:10],
            "count": len(letters),
            "capital_increase": n_capital,
            "board_change": n_board,
            "matched": len(scores),
        }

        if not scores:
            details["data_quality"] = "titles_only"
            return SectionScore(self.section_name, 0.0, 0.15 if letters else 0.0, details)

        avg = sum(scores) / len(scores)
        confidence = min(0.6, 0.18 + 0.07 * len(scores))
        # رویداد سرمایه/مدیران confidence را کمی بالا می‌برد
        if n_capital or n_board:
            confidence = min(0.7, confidence + 0.08)
        details["data_quality"] = "event_titles"
        return SectionScore(
            self.section_name,
            round(avg, 4),
            round(confidence, 4),
            details,
        )
