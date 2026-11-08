# دفتر ثبت تغییرات و شواهد

این فایل شاخص رسمی Change Recordهاست. هر تغییر معنادار باید یک رکورد مستقل در docs/changes/ داشته باشد.

## قالب وضعیت
- **IMPLEMENTED:** پیاده‌سازی شده و شواهد/اعتبارسنجی متناسب با دامنه ثبت شده است.
- **PARTIALLY_IMPLEMENTED:** بخشی از دامنه اجرا شده و بخش‌های باقی‌مانده صریحاً مشخص شده‌اند.
- **PROPOSED:** پیشنهاد یا طراحی ثبت شده ولی هنوز پیاده‌سازی نشده است.
- **BLOCKED:** کار به‌دلیل مانع مستند فنی، دسترسی، شواهد یا حقوقی متوقف است.

**قید شواهد:** `UNVERIFIED` وضعیت پیاده‌سازی نیست؛ فقط برای مشخص‌کردن ادعا، منبع، اتصال یا رفتاری به‌کار می‌رود که هنوز مستقلاً راستی‌آزمایی نشده است.

## رکوردها

| ID | Date | Change | Status | Evidence | Validation | Owner Decision |
|---|---|---|---|---|---|---|
| CR-20261108-001 | 2026-11-08 | ورودی آفلاین Excel/CSV با جداسازی سه بازار و رفع تطبیق مبهم/تاریخ ساختگی TSETMC | PARTIALLY_IMPLEMENTED | درخواست مالک؛ baseline 7695aca؛ قرارداد فایل داخلی؛ مستندات Python/openpyxl و تست‌های آفلاین | 120 تست کامل و 74 هدفمند موفق؛ پوشش ورودی 96٪؛ governance، compile و diff-check موفق؛ CI در انتظار PR | مأموریت PM-DATA-PERPLEXITY-01؛ آماده بازبینی؛ ادغام و استقرار مجاز نیست |
| CR-20261002-001 | 2026-10-02 | ایجاد قانون اساسی، Startup Gate، سیاست شواهد و فرآیند چندایجنتی | IMPLEMENTED | وضعیت واقعی مخزن، مستندات معماری، سیاست‌های رسمی GitHub برای PR/protection | مستندات و ساختار فایل‌ها بررسی شد؛ CI ایجاد شد | مالک پروژه تأییدکننده نهایی |
| CR-20261002-002 | 2026-10-02 | ثبت محدودیت دسترسی به دو پوشه Google Drive و جلوگیری از ادعای خواندن/نوشتن بدون اتصال | BLOCKED | اتصال Google Drive در محیط فعلی DISABLED_BY_ADMIN؛ لینک‌ها قابل خواندن نبودند | هیچ محتوای Drive ادعا یا وارد کد نشده است | نیازمند فراهم‌شدن اتصال Drive |
| CR-20261002-003 | 2026-10-02 | بهبود اجرای چندایجنتی، ثبت بهبودهای فنی و Governance Gate قابل اجرا | IMPLEMENTED | بررسی baseline مخزن، architecture، roadmap، provider config و مستندات رسمی GitHub | script و workflow اضافه شد؛ اجرای واقعی CI پس از PR قابل ثبت است | مالک پروژه تأییدکننده نهایی |
| CR-20261028-001 | 2026-10-28 | ممیزی ۱۰ مخزن GitHub و افزودن OHLCV quality gate و SQLite provenance | PROPOSED | `docs/research/OSS_REUSE_REVIEW_20261028.md`; license files/metadata مخازن upstream؛ کد/provider/tests فعلی ARYA | 33 pytest، governance، compileall و diff-check موفق؛ بدون کپی کد یا dependency؛ آزمون live اجرا نشد | بازبینی/پذیرش با مالک پروژه در PR |
| CR-20261031-002 | 2026-10-31 | تعریف وضعیت‌های پیاده‌سازی و توسعه قالب Change Record | IMPLEMENTED | `docs/architecture/AGENT_COLLABORATION_AND_EXECUTION.md`; `docs/changes/CR-20261031-002.md` | بازبینی مستندات؛ آزمون خودکار مستندات NOT RUN | PM-002 تأیید شد؛ PR #55 با تأیید جداگانه مالک در main ادغام شد |
| CR-20261031-003 | 2026-10-31 | اصلاح نام‌گذاری Change Record و افزودن تست رگرسیون Governance Gate | IMPLEMENTED | `scripts/verify_governance.py`; `tests/test_verify_governance.py`; `docs/changes/CR-20261031-003.md` | Governance verifier، install، compileall و pytest موفق؛ 35 تست در 0.70s (Actions run #19) | اصلاح در شاخه مستقل؛ ادغام نیازمند تأیید جداگانه مالک |

## قانون
هیچ تغییر کدی نباید بدون ID این دفتر وارد PR شود.

| CR-20261102-001 | 2026-11-02 | افزودن کد مأموریت اجباری برای همکاران انسانی و AI، الزام مطالعه قانون اساسی و ثبت گزارش؛ افزودن پروتکل انتصاب | PROPOSED | دستور مالک؛ baseline قانون اساسی، AGENTS.md، STARTUP_CHECKLIST.md و CHANGE_LEDGER.md | بازبینی محتوایی انجام شد؛ CI و تست خودکار هنوز اجرا نشده؛ PR نیازمند review مالک | در انتظار تأیید نهایی مالک |

## ثبت تکمیلی تغییر M2

| ID | Date | Change | Status | Evidence | Validation | Owner Decision |
|---|---|---|---|---|---|---|
| CR-20261102-002 | 2026-11-02 | اصلاح معنای واحدها، تطبیق دقیق نماد و کیفیت شواهد سهامداران برای Smart Money | IMPLEMENTED | `docs/changes/CR-20261102-002.md`; PR #60 محدودشده بر پایه main | مالک پروژه: Python 3.11.15؛ 14 تست هدفمند و 49 تست کامل روی شاخه‌ی مستقل موفق؛ Governance CI پس از اصلاح نام‌گذاری نیازمند اجرای مجدد است | ادغام فقط پس از بازبینی مستقل، CI سبز و تأیید صریح مالک |


| CR-20261103-001 | 2026-11-03 | پیشنهاد منشور حاکمیت دو گروه بازار داخلی و خارجی و الزام مطالعه آن در AGENTS.md | PROPOSED | `docs/governance/DUAL_TEAM_GOVERNANCE.md`; `docs/changes/CR-20261103-001.md`; درخواست مالک | بازبینی محتوایی انجام شد؛ تست خودکار/CI در انتظار PR؛ هیچ کد اجرایی تغییر نکرده است | در انتظار review و تأیید صریح مالک؛ تا آن زمان منشور لازم‌الاجرا نیست |
