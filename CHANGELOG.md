# Changelog

## [Unreleased] — فاز اول دادهٔ آنلاین بورس ایران
### Changed
- فعال‌شدن `TsetmcMarketProvider` برای بازار `stock` با endpointهای JSON عمومی TSETMC.
- افزودن timeout، retry، backoff و تشخیص پاسخ نامعتبر/مسدودشده برای تاب‌آوری شبکه.
- اصلاح نسخهٔ بسته از `0.1.0-milestone1` به نسخهٔ معتبر PEP 440 (`0.1.0+milestone1`)؛ دلیل: نصب editable قبلاً قبل از اجرای تست‌ها شکست می‌خورد.
- مستندسازی صریح دامنهٔ پروژه: ارز دیجیتال، بورس ایران، فارکس و سهام خارجی؛ مالیات خارج از محدوده است.

### Tests
- تست‌های TSETMC با پاسخ جعلی HTTP اضافه شد تا تست‌ها به شبکه و وضعیت لحظه‌ای بازار وابسته نباشند.
- ۵ تست برای فیلتر بازار، استراتژی روند-مومنتوم و تحلیل نسبت‌های بنیادی اضافه شد.

## [Unreleased] — فیلتر، استراتژی و تحلیل بنیادی
### Added
- فیلتر کمّی بازار بر پایهٔ درصد تغییر، نسبت حجم، ارزش معاملات و قدرت خریدار اختیاری.
- استراتژی قابل‌توضیح EMA سریع/کند + RSI با کنترل حداقل سابقه و جلوگیری از look-ahead.
- مدل و Analyzer نسبت‌های P/E، P/B، بازده سود نقدی، حاشیه سود، بدهی به حقوق صاحبان سهام و نسبت جاری.
- smoke test جدا از CI برای اتصال زنده TSETMC و راهنمای عملیاتی Google Drive/داده زنده.
### Design
- دادهٔ بنیادی ناقص امتیاز مثبت جعلی تولید نمی‌کند و دادهٔ جریان پول بدون provider معتبر وارد سیگنال نمی‌شود.

## [Unreleased] — عملیات همگام‌سازی و feed زنده
### Added
- `drive_sync_worker.py` برای dry-run/apply، allowlist فایل، SHA-256 manifest و پردازش سبک JSON/CSV.
- `tsetmc_live_check.py` برای snapshot market-watch، شمارش quote معتبر و اعلام وضعیت feed.
- API `fetch_market_watch` در provider TSETMC؛ بدون اتصال به مسیر سفارش‌گذاری.
- تست‌های آفلاین worker و market-watch؛ مجموع تست‌های پروژه به ۲۲ رسید.

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
