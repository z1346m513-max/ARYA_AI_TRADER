# Changelog

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
