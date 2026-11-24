# طراحی CODAL — رابط مخزن با ARYA و پنل مالک

- مأموریت: `PM-CODAL-ALL-001`
- مرحله: Phase 0
- وضعیت: PROPOSED
- تاریخ: 2026-11-24

## 1. معماری مورد نظر مالک

- پایگاه داده فعال روی رایانه/سرور تحت کنترل مالک.
- دسترسی ARYA به مخزن از طریق API یا interface امن و مستند.
- دسترسی مالک هم از پنل ARYA و هم از Google Drive برای فایل‌های خام/نسخه پشتیبان.
- بازار سهام ایران و ماژول CODAL باید از یک مخزن مرجع مشترک استفاده کنند؛ ایجاد دیتابیس موازی و ناسازگار ممنوع.
- در دسترس نبودن CODAL/اینترنت/Drive نباید خواندن داده‌های ذخیره‌شده را متوقف کند.

## 2. بلوک‌های منطقی

1. CODAL ingestion service — دریافت خودکار و دستی.
2. Raw document store — فایل‌های تغییرناپذیر و hash.
3. Active relational repository — داده‌های نرمال‌شده و تاریخچه.
4. Quality/review service — قواعد کیفیت و صف بررسی انسانی.
5. Repository API — خواندن کنترل‌شده و عملیات مجاز.
6. Owner panel — جست‌وجو، مشاهده منبع، نسخه‌ها، خطاها و تأییدهای دستی.
7. Backup worker — انتقال غیرهمزمان نسخه‌های پشتیبان به Drive.

## 3. قرارداد API پیشنهادی (نام‌ها نمونه‌اند)

| عملیات مفهومی | ورودی | خروجی |
|---|---|---|
| جست‌وجوی نماد | ticker, venue, as_of | هویت و وضعیت تاریخی |
| فهرست اطلاعیه | instrument_id, type, date range | نتایج صفحه‌بندی‌شده |
| جزئیات اطلاعیه | disclosure_id, version | metadata و نسخه‌ها |
| دریافت سند | document_id | stream/file با کنترل دسترسی |
| صورت مالی | instrument_id, period, statement_kind | facts و واحدها با provenance |
| فعالیت ماهانه | instrument_id, period range | داده ماهانه و وضعیت کیفیت |
| رویدادها | instrument_id, event_type, date range | رویدادها و زمان اثر |
| کیفیت | entity_ref, status | خطاها و نیازهای بازبینی |
| تاریخچه | entity_ref, as_known_at | نسخه‌ها و رخدادهای قابل ممیزی |

این جدول endpoint واقعی یا OpenAPI specification نیست؛ مسیرها، schemaها و authorization بعداً با تست contract نهایی می‌شوند.

## 4. امنیت و مجوز

- احراز هویت سرویس به سرویس با credential اختصاصی و قابل چرخش.
- حداقل دسترسی لازم؛ تفکیک نقش read-only، ingest، reviewer و owner-admin.
- API ترجیحاً فقط در شبکه محلی/خصوصی در دسترس باشد؛ انتشار عمومی بدون threat model و مجوز مالک ممنوع.
- TLS برای ارتباطات شبکه‌ای؛ secrets خارج از Git و فایل‌های قابل اشتراک.
- audit log برای تغییر دستی، تأیید کیفیت، export و عملیات مدیریتی.
- محدودیت نرخ، pagination، request id و پیام خطای غیرحساس.
- هیچ endpoint نوشتنی برای معاملات یا سفارش در دامنه این مخزن تعریف نمی‌شود.

## 5. رفتار پنل مالک

- جست‌وجو بر اساس نماد، شرکت، نوع اطلاعیه و بازه زمانی.
- نمایش اصل سند، منبع، hash، تاریخ انتشار/دریافت و نسخه.
- مقایسه نسخه‌های اصلاح‌شده.
- نمایش استخراج‌ها، confidence، خطاها و علت رد/ارجاع.
- امکان ثبت اصلاح دستی فقط با دلیل، کاربر، timestamp و حفظ مقدار قبلی.
- امکان export با manifest و منبع.
- گزارش وضعیت ingest و صف retry.
- نشان‌دادن واضح UNVERIFIED/PARTIAL؛ عدم تبدیل آن به داده قطعی.

## 6. سازگاری با ARYA فعلی

کد فعلی شامل provider عمومی بازار و SQLite cache است؛ این‌ها به‌تنهایی معادل مخزن جامع افشاهای مالی نیستند. قبل از اتصال باید:
- interface موجود و وابستگی‌های ماژول سهام ممیزی شود؛
- مرز cache در برابر system of record مشخص شود؛
- قرارداد instrument/symbol و timezone/units هم‌تراز شود؛
- migration و backward compatibility طراحی شود؛
- هیچ مسیر تحلیل، provider یا storage فعلی بدون آزمون و مجوز تغییر نکند.

## 7. تاب‌آوری

- خواندن داده محلی از ingestion و Drive مستقل باشد.
- backup worker صف پایدار، checkpoint و retry داشته باشد.
- در خطای Drive فقط backup در صف می‌ماند؛ DB فعال متوقف نمی‌شود.
- restore drill و checksum verification بخشی از پذیرش است.

## 8. معیار پذیرش

- API contract versioned و مستند.
- آزمون role/authorization و عدم دسترسی غیرمجاز.
- آزمون pagination، idempotency، timeout و retry.
- تست contract بین ARYA و repository.
- پنل برای نسخه‌ها، منبع و وضعیت کیفیت قابل ممیزی باشد.
- restore آزمایشی در محیط جدا موفق باشد.

## 9. موارد باز

انتخاب framework، آدرس‌دهی شبکه، مدل احراز هویت، سطح دسترسی پنل، hosting و تصمیم نهایی DBMS در Phase 0 باید با منابع و محدودیت سخت‌افزار بررسی شود.
