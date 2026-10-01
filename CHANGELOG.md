# Changelog

## [Unreleased] — فاز اول دادهٔ آنلاین بورس ایران
### Changed
- فعال‌شدن `TsetmcMarketProvider` برای بازار `stock` با endpointهای JSON عمومی TSETMC.
- افزودن timeout، retry، backoff و تشخیص پاسخ نامعتبر/مسدودشده برای تاب‌آوری شبکه.
- اصلاح نسخهٔ بسته از `0.1.0-milestone1` به نسخهٔ معتبر PEP 440 (`0.1.0+milestone1`)؛ دلیل: نصب editable قبلاً قبل از اجرای تست‌ها شکست می‌خورد.
- مستندسازی صریح دامنهٔ پروژه: ارز دیجیتال، بورس ایران، فارکس و سهام خارجی؛ مالیات خارج از محدوده است.

### Tests
- تست‌های TSETMC با پاسخ جعلی HTTP اضافه شد تا تست‌ها به شبکه و وضعیت لحظه‌ای بازار وابسته نباشند.

## [0.1.0-milestone1] - 2026-07-17
### Added
- ساختار کامل پروژه طبق معماری تأییدشده (docs, configs, src/arya/*, tests, installer)
- لایه‌ی تنظیمات مرکزی (`Settings`) با ۶ فایل YAML
- `MockMarketProvider` برای توسعه و تست آفلاین
- کش SQLite (`OHLCVStore`)
- Indicator Engine با معماری Plugin و اندیکاتورهای SMA, EMA, RSI, MACD, Bollinger Bands, OBV
- `TechnicalAnalyzer`, `ScoringEngine`, `RuleBasedDecisionEngine`, `RiskManager`, `RecommendationEngine`
- Dashboard متنی (rich) و CLI (`arya analyze|list-symbols|scan`)
- تست‌های واحد پایه
