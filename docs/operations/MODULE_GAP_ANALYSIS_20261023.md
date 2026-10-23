# وضعیت ماژول‌ها و کمبودهای مخزن — 2026-10-23

## شاخه‌های Git

| Branch | محتوا |
|--------|--------|
| `main` | هسته Milestone 1 |
| `feat/portfolio-monitoring-stage-zero` | نگاشت market-watch + docs جزئی |
| `feat/daily-ingest-and-stage-zero-docs` | اسکلت ingest روزانه + اسناد مرحله صفر |

## لایه‌های نسبتاً کامل

- `providers/market/tsetmc_provider.py`, `mock_provider.py`
- `analysis/analyzers/technical_analyzer.py`, `fundamental_analyzer.py`
- `analysis/scoring/scoring_engine.py`, `recommendation/recommendation_engine.py`
- `ai/reasoning/decision_engine.py`
- `app/bootstrap.py`, `cli/main.py`, `config/settings.py`
- `dashboard/console_dashboard.py`
- `models/market_data.py`, `fundamentals.py`, `analysis_result.py`

## ماژول‌های placeholder (عمدتاً فقط `__init__.py` خالی)

| مسیر | نقش | اولویت |
|------|------|--------|
| `providers/codal/` | داده کدال | بالا |
| `providers/news/` | اخبار | متوسط |
| `providers/sentiment/`, `macro/` | احساسات / کلان | پایین |
| `providers/crypto/`, `forex/` | بازارهای دیگر | متوسط |
| `codal/` | دامنه کدال | بالا |
| `portfolio/` | پرتفوی / رصد نهاد | بالا |
| `scheduler/` | زمان‌بندی داخلی | متوسط |
| `storage/` | SQLite / ماندگاری | بالا |
| `backtest/`, `alerts/` | بک‌تست / هشدار | متوسط |
| `api/` | HTTP API | پایین |
| `optimization/` | بهینه‌سازی | پایین |
| `ai/explainability`, `prediction`, `prompt`, `models` | AI پیشرفته | بعد از داده پایدار |
| `analysis/ranking`, `report` | رتبه‌بندی / گزارش | متوسط |

## کمبود اطلاعات

1. ماتریس کامل کدال / CFI / سهامداران (جز TSETMC قیمت)
2. قرارداد پارامتری ShareChange / ClientType (CR-20261024-001 فاز ۰)
3. تعریف محصول: پرتفوی صندوق vs سبدگردان vs مشتری
4. اسکیما Storage رسمی
5. سیاست Scoring برای missing section vs missing data
6. محیط اجرا با IP ایران

## وزن‌های بدون Analyzer

`smart_money`, `news`, `codal`, `liquidity`, `risk` در weights.yaml رزرو شده‌اند؛ مسیر واقعی عمدتاً `technical` (+ fundamental با کیفیت داده) است.
