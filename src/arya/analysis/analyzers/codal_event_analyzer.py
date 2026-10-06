"""
تحلیل رویدادمحور اطلاعیه‌های کدال بر اساس عنوان.

بدون پارس صورت مالی؛ فقط سیگنال متنی از نوع رویداد (مجمع، افزایش سرمایه، ...).
امتیاز محافظه‌کارانه است و confidence پایین نگه داشته می‌شود تا تکنیکال را
تحت‌الشعاع قرار ندهد.
"""
from __future__ import annotations

from arya.models.analysis_result import SectionScore
from arya.models.codal import CodalLetter

# (کلمه کلیدی, امتیاز تقریبی [-1,1], برچسب)
_RULES: list[tuple[str, float, str]] = [
    ("افزایش سرمایه", 0.35, "افزایش سرمایه"),
    ("تسعیر", 0.15, "تسعیر ارز"),
    ("سود نقدی", 0.25, "سود نقدی"),
    ("تقسیم سود", 0.25, "تقسیم سود"),
    ("مجمع", 0.1, "مجمع"),
    ("شفاف سازی", 0.0, "شفاف‌سازی"),
    ("شفاف‌سازی", 0.0, "شفاف‌سازی"),
    ("توقف نماد", -0.4, "توقف نماد"),
    ("عدم اظهار نظر", -0.3, "عدم اظهارنظر حسابرس"),
    ("مشروط", -0.2, "گزارش مشروط"),
    ("اصلاحیه", -0.1, "اصلاحیه"),
    ("اعلامیه پذیرفته‌نویسی", 0.2, "پذیرفته‌نویسی"),
]


class CodalEventAnalyzer:
    section_name = "codal"

    def analyze(self, letters: list[CodalLetter], *, max_letters: int = 8) -> SectionScore:
        if not letters:
            return SectionScore(
                self.section_name,
                0.0,
                0.0,
                {"reasons": [], "data_quality": "missing", "count": 0},
            )

        scores: list[float] = []
        reasons: list[str] = []
        seen_tags: set[str] = set()

        for letter in letters[:max_letters]:
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
            if not matched and len(reasons) < 3:
                short = title[:50] + ("…" if len(title) > 50 else "")
                reasons.append(f"کدال: {short}")

        if not scores:
            # اطلاعیه هست ولی قانون خاصی نخورد → خنثی با اطمینان کم
            return SectionScore(
                self.section_name,
                0.0,
                0.15,
                {
                    "reasons": reasons[:5],
                    "data_quality": "titles_only",
                    "count": len(letters),
                },
            )

        avg = sum(scores) / len(scores)
        confidence = min(0.55, 0.15 + 0.08 * len(scores))
        return SectionScore(
            self.section_name,
            round(avg, 4),
            round(confidence, 4),
            {
                "reasons": reasons[:8],
                "data_quality": "event_titles",
                "count": len(letters),
                "matched": len(scores),
            },
        )
