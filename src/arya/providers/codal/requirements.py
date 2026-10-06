"""
چک‌لیست اطلاعاتی که ARYA از کدال نیاز دارد — برای استخراج دستی.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CodalRequirement:
    code: str
    title_fa: str
    why: str
    where_on_codal: str
    priority: str  # high | medium | low
    event_type: str  # برای ورود دستی


# فهرست ثابت — نرم‌افزار همین را اعلام می‌کند
CODAL_REQUIREMENTS: tuple[CodalRequirement, ...] = (
    CodalRequirement(
        code="CAPITAL_INCREASE",
        title_fa="افزایش سرمایه / حق تقدم / پذیره‌نویسی",
        why="امتیاز رویداد سرمایه و تشخیص نوع (آورده، سود انباشته، تجدید ارزیابی)",
        where_on_codal="جست‌وجوی نماد → فیلتر عنوان «افزایش سرمایه» یا «حق تقدم»",
        priority="high",
        event_type="capital",
    ),
    CodalRequirement(
        code="BOARD_CHANGE",
        title_fa="تغییرات مدیران / هیئت مدیره / مدیرعامل",
        why="ریسک حاکمیتی و امتیاز بخش رویداد مدیران",
        where_on_codal="عنوان‌های «تغییرات مدیران»، «استعفا»، «انتصاب»",
        priority="high",
        event_type="board",
    ),
    CodalRequirement(
        code="ASSEMBLY",
        title_fa="دعوت به مجمع / تصمیمات مجمع",
        why="سود نقدی، تقسیم سود، زمان‌بندی توقف نماد",
        where_on_codal="«مجمع عمومی»، «تصمیمات مجمع»",
        priority="medium",
        event_type="assembly",
    ),
    CodalRequirement(
        code="DISCLOSURE",
        title_fa="شفاف‌سازی / اطلاعات بااهمیت",
        why="هشدار ریسک و اخبار غیرمترقبه",
        where_on_codal="«شفاف سازی»، «اطلاعات با اهمیت»",
        priority="medium",
        event_type="disclosure",
    ),
    CodalRequirement(
        code="AUDIT_OPINION",
        title_fa="نظر حسابرس (مقبول / مشروط / عدم اظهار)",
        why="امتیاز منفی برای گزارش مشروط یا عدم اظهارنظر",
        where_on_codal="صورت‌های مالی حسابرسی‌شده — بند اظهارنظر",
        priority="medium",
        event_type="other",
    ),
    CodalRequirement(
        code="INTERIM_FS",
        title_fa="صورت مالی میان‌دوره‌ای / سالانه (خلاصه)",
        why="فاز بعد: EPS واقعی، حاشیه سود، رشد درآمد (فعلاً اختیاری دستی)",
        where_on_codal="صورت‌های مالی → پیوست Excel/PDF",
        priority="low",
        event_type="other",
    ),
    CodalRequirement(
        code="MONTHLY_ACTIVITY",
        title_fa="گزارش فعالیت ماهانه",
        why="فاز بعد: روند تولید/فروش ماهانه",
        where_on_codal="گزارش فعالیت ماهانه هیئت مدیره",
        priority="low",
        event_type="other",
    ),
)


def requirements_for_analyze() -> list[CodalRequirement]:
    """مواردی که برای غنی‌شدن analyze اولویت دارند."""
    return [r for r in CODAL_REQUIREMENTS if r.priority in {"high", "medium"}]


def format_checklist(ticker: str | None = None) -> str:
    lines = [
        "══════════════════════════════════════════════",
        "  چک‌لیست استخراج دستی از کدال (codal.ir)",
        "══════════════════════════════════════════════",
    ]
    if ticker:
        lines.append(f"  نماد هدف: {ticker}")
        lines.append(f"  جست‌وجو در کدال با همین نماد فارسی")
    lines.append("")
    for i, r in enumerate(CODAL_REQUIREMENTS, 1):
        lines.append(f"{i}. [{r.priority.upper()}] {r.title_fa}")
        lines.append(f"   کد: {r.code} | نوع ورود دستی: --event {r.event_type}")
        lines.append(f"   چرا لازم است: {r.why}")
        lines.append(f"   کجا در کدال: {r.where_on_codal}")
        lines.append("")
    lines.append("پس از استخراج، با دستور زیر وارد سیستم کنید:")
    lines.append(
        '  arya manual add --ticker نماد --event capital|board|assembly|disclosure|other '
        '--title "عنوان دقیق اطلاعیه" --date 1403-01-15'
    )
    lines.append("")
    lines.append("فایل ذخیره: data/manual/codal_events.json")
    return "\n".join(lines)
