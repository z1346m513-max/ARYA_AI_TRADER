# ثبت منابع Google Drive

## وضعیت فعلی
دو پوشهٔ زیر به‌عنوان مخازن مرجع پروژه تعیین شده‌اند:

| ID | URL | Current access | Trust state |
|---|---|---|---|
| Drive-1 | https://drive.google.com/drive/folders/1QS-0UJX2Hqwv_gEa0XTSuVJVu9pVouaW | در محیط فعلی غیرقابل دسترسی | UNVERIFIED |
| Drive-2 | https://drive.google.com/drive/folders/1p-mjgJI1IdPRf-j3olrvL8c--1-7XvlL | در محیط فعلی غیرقابل دسترسی | UNVERIFIED |

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
