# طراحی CODAL — فرهنگ داده و شِمای منطقی

- مأموریت: `PM-CODAL-ALL-001`
- مرحله: Phase 0 — طراحی
- وضعیت: PROPOSED؛ schema فیزیکی نهایی نیست
- تاریخ: 2026-11-24

## 1. اصول مدل‌سازی

- شناسه داخلی پایدار برای شرکت، ابزار/نماد، اطلاعیه، سند، نسخه و fact.
- جداسازی شرکت از نماد/ابزار؛ نماد ممکن است تغییر کند یا چند بازار/نوع ابزار داشته باشد.
- جداسازی تاریخ دوره مالی از تاریخ انتشار و زمان دریافت.
- مقدار عددی بدون واحد، مقیاس، دوره و زمینه معنای قابل اتکا ندارد.
- داده خام، داده استخراج‌شده و داده نرمال‌شده لایه‌های جدا دارند.
- تاریخچه append-only است؛ اصلاح با version/supersedes انجام می‌شود.
- حذف فیزیکی داده مرجع بدون مجوز و audit ممنوع است.

## 2. موجودیت‌های پیشنهادی

| موجودیت | کلید و فیلدهای اصلی | توضیح |
|---|---|---|
| companies | company_id, legal_name, national_id? | هویت حقوقی؛ شناسه ملی فقط در صورت منبع معتبر |
| instruments | instrument_id, company_id, ticker, venue, market, status, valid_from/to | نماد و وضعیت تاریخی |
| disclosures | disclosure_id, source_notice_id, instrument_id, title, notice_type, published_at | اطلاعیه و هویت منبع |
| disclosure_versions | version_id, disclosure_id, source_revision, relation, observed_at | نسخه، اصلاحیه، ابطال یا جایگزینی |
| raw_documents | document_id, version_id, media_type, byte_size, sha256, archive_uri | فایل خام immutable |
| financial_statements | statement_id, version_id, period_start/end, fiscal_year, statement_kind, consolidation | زمینه صورت مالی |
| financial_facts | fact_id, statement_id, item_code, label, value_decimal, unit, scale, currency, source_locator | ریز fact مالی |
| monthly_activities | activity_id, version_id, period, product_code, quantity, sales_price, revenue, units | فعالیت ماهانه |
| corporate_events | event_id, version_id, event_type, announced_at, effective_at, status | مجمع، افزایش سرمایه و رویداد |
| provenance | provenance_id, entity_type/id, source_uri, retrieved_at, published_at, extractor_version | ردپای منبع |
| extraction_runs | run_id, started_at, ended_at, extractor_version, status, counters | اجرای استخراج |
| quality_issues | issue_id, entity_ref, rule_id, severity, status, resolution_ref | خطا/ابهام کیفیت |
| manual_reviews | review_id, entity_ref, reviewer, decision, evidence, reviewed_at | ممیزی انسانی |

فیلدهای دارای علامت سؤال یا جزئیات کلید خارجی نیازمند بررسی منبع و قواعد حقوقی/داده‌ای هستند. این جدول DDL یا دستور ایجاد پایگاه داده نیست.

## 3. تعریف داده مالی

هر financial_fact باید حداقل این معناها را حمل کند:
- شرکت و نماد مرتبط در تاریخ اعتبار؛
- اطلاعیه، نسخه و سند مبدأ؛
- نوع صورت، تلفیقی/جداگانه و دوره؛
- کد/عنوان قلم و مقدار دقیق؛
- واحد، مقیاس (ریال/میلیون ریال و غیره) و ارز؛
- محل استخراج در سند؛
- روش و نسخه extractor؛
- وضعیت QC و بازبینی انسانی؛
- زمان انتشار، دریافت و ثبت در مخزن.

مقادیر خام منبع باید قابل بازیابی بمانند. تبدیل واحد باید با مقدار مبدأ، ضریب تبدیل، واحد مقصد و نسخه قاعده ثبت شود.

## 4. زمان و تاریخ اعتبار

- زمان‌های فنی در ذخیره‌سازی با UTC و نمایش با timezone صریح.
- تاریخ شمسی منبع، در صورت وجود، به‌صورت متن/مقدار اصلی نیز حفظ شود.
- `published_at`: زمان اعلام‌شده توسط منبع.
- `retrieved_at`: زمان دریافت توسط سامانه.
- `effective_at`: تاریخ اثرگذاری کسب‌وکاری در صورت وجود.
- `valid_from/to`: بازه اعتبار رابطه نماد/شرکت/بازار.
- هیچ timestamp گمشده‌ای با زمان جاری جایگزین نمی‌شود؛ مقدار نامعلوم باید NULL/UNKNOWN باقی بماند.

## 5. وضعیت‌ها

پیشنهاد وضعیت‌های مستقل:
- ingest: DISCOVERED, DOWNLOADED, FAILED, RETRY_PENDING
- extraction: PENDING, EXTRACTED, PARTIAL, FAILED
- quality: PASS, WARNING, REJECTED, NEEDS_REVIEW
- trust: VERIFIED, PARTIAL, UNVERIFIED, REJECTED
- revision: ORIGINAL, AMENDED, CANCELED, SUPERSEDED

وضعیت‌های فوق باید در طراحی تفصیلی با الگوی نام‌گذاری موجود ARYA هم‌تراز شوند؛ هنوز قرارداد قطعی نیستند.

## 6. پایگاه داده و استقرار

PostgreSQL گزینه پیشنهادی برای پایگاه داده فعال است، نه تصمیم نهایی. انتخاب قطعی منوط به بررسی فضای ذخیره‌سازی، RAM، بازیابی، backup و بار کاری است. SQLite فعلی ARYA که نقش cache دارد نباید بدون بررسی به‌عنوان مخزن جامع و چندکاربره CODAL فرض شود. فایل DB زنده در پوشه همگام‌سازی Drive قرار نمی‌گیرد.

## 7. قیود و شاخص‌های یکپارچگی پیشنهادی

- unique source_notice_id در محدوده‌ای که منبع واقعاً یکتا بودن آن را تضمین کند.
- unique hash برای شناسایی محتوای بایت یکسان؛ نه جایگزین شناسه نسخه.
- foreign key برای روابط سند/نسخه/fact.
- منع fact بدون واحد و دوره معتبر.
- جلوگیری از duplicate بر اساس کلید معنایی و نسخه، نه صرفاً عنوان.
- index بر نماد، نوع اطلاعیه، تاریخ انتشار، دوره مالی و وضعیت کیفیت.
- تغییرات انسانی و سیستمی audit trail داشته باشند.

## 8. معیار پذیرش

- فرهنگ داده برای تمام اطلاعیه‌های داخل دامنه تکمیل شود.
- نگاشت حداقل نمونه‌های واقعی به entityها بدون ابهام باشد.
- اصلاحیه، نماد تغییرکرده، تلفیقی/جداگانه و واحدهای متفاوت مدل‌پذیر باشند.
- هیچ fact بدون سند، locator، دوره و واحد پذیرفته نشود.
- طرح migration، backup/restore و نگهداری نسخه‌ها پیش از انتخاب DB ارائه شود.

## 9. تصمیم‌های باز

انتخاب DBMS، نوع شناسه رسمی شرکت/نماد، taxonomy اطلاعیه‌ها، retention، سیاست حذف، و دامنه تاریخچه به تأیید مالک و شواهد فنی وابسته‌اند.
