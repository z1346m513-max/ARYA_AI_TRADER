# ثبت منابع Google Drive

## وضعیت فعلی
دو پوشهٔ زیر به‌عنوان مخازن مرجع پروژه تعیین شده‌اند:

| ID | URL | Current access | Trust state |
|---|---|---|---|
| Drive-1 | https://drive.google.com/drive/folders/1QS-0UJX2Hqwv_gEa0XTSuVJVu9pVouaW | در محیط فعلی غیرقابل دسترسی | UNVERIFIED |
| Drive-2 | https://drive.google.com/drive/folders/1p-mjgJI1IdPRf-j3olrvL8c--1-7XvlL | در محیط فعلی غیرقابل دسترسی | UNVERIFIED |
| Drive-User-Provided | https://drive.google.com/drive/folders/1VV4bepF0i33q-4pco15BvMSCmeDBEh4h | در نشست 2026-10-10 با Drive API خوانده شد؛ این پوشه با Drive-1/2 بالا متفاوت است | فایل `سبد گردانان بورس.xlsx` به تصریح کاربر اشتباهی بارگذاری شده و برای هدف پروژه `REJECTED / OUT OF SCOPE`; hash فقط جهت audit trail |

### بررسی 2026-10-10 — Drive-User-Provided

- پوشه با نام «بورس ایران» قابل دسترسی بود و زیرپوشه `Support sites` فایل `سبد گردانان بورس.xlsx` را داشت. کاربر در 2026-10-10 تصریح کرد این فایل اشتباهی بارگذاری شده و منظور پروژه نیست؛ بنابراین به‌عنوان داده یا منبع هدف **کنار گذاشته شده است**.
- فایل با ID `1LkXtSGYLlxvLY3lewnAX9MNhKJQraeFj`، MIME نوع XLSX، اندازه 57,393 بایت و modified time برابر `2026-10-10T12:28:15.196Z` از Drive API دریافت شد.
- Drive API مقدار MD5 `6c88034436a0e04d517e879f04ee957c` و نسخهٔ محلی مقدار SHA-256 `e930e9cf8cb684619cba84a35a52b929534a1a1411867d9562b39b87b7d4cf1e` را گزارش/محاسبه کرد.
- شمارش فنی فایل اشتباه 130 ردیف و 130 پیوند CFI را نشان داده است؛ این توصیف صرفاً audit trail فایل مردود است و نباید برای فهرست‌سازی، نگاشت نهاد یا تحلیل استفاده شود.
- دسترسی‌پذیری و hash فقط دریافت همان فایل را اثبات می‌کنند، نه صحت، جامعیت یا مجوز. وضعیت فایل برای هدف این پروژه `REJECTED / OUT OF SCOPE` است.
- ارزیابی و شکاف‌ها در `docs/discovery/FUND_HOLDINGS_DISCOVERY_IR.md` و `CR-20261010-001` ثبت شده است.

## Manifest موردنیاز پس از فعال‌شدن دسترسی
برای هر فایل:
- Drive file ID
- path/name
- MIME type
- modified time
- SHA-256
- source folder
- access date
- document version
- evidence claims
- trust state: VERIFIED / PARTIAL / UNVERIFIED / REJECTED
- related Change Record / ADR

## قانون ingest
هیچ سند UNVERIFIED نباید مبنای تولید کد یا تصمیم معماری قطعی قرار گیرد.

## همگام‌سازی
فایل‌های تولیدشدهٔ پروژه که باید در Drive نگه‌داری شوند باید با manifest ثبت شوند. اگر اتصال write در دسترس نیست، فقط وضعیت BLOCKED ثبت می‌شود؛ هرگز موفقیت ساختگی گزارش نمی‌شود.
