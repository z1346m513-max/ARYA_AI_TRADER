# نقشه راه ARYA AI Trader

## ✅ Milestone 1 — Core Pipeline + TSETMC foundation (فعلی)
- ساختار کامل پروژه طبق معماری تأییدشده
- `Settings` مرکزی + ۶ فایل YAML کاملاً کاربردی
- `MockMarketProvider` (داده‌ی مصنوعی Deterministic برای توسعه/تست آفلاین)
- `OHLCVStore` (کش SQLite)
- Indicator Engine با معماری Plugin + ۵ اندیکاتور واقعی: SMA, EMA, RSI, MACD, Bollinger, OBV
- `TechnicalAnalyzer` → `ScoringEngine` (وزن‌دهی + پروفایل‌های کم‌ریسک/متعادل/پرریسک)
- `RuleBasedDecisionEngine` (قابل توضیح، آماده جایگزینی/ترکیب با ML)
- `RiskManager` (سطح ریسک، حد ضرر، حداکثر پوزیشن)
- `RecommendationEngine` + Dashboard متنی (rich)
- CLI کامل (`arya analyze / list-symbols / scan`)
- تست‌های واحد برای Provider، اندیکاتورها و کل پایپ‌لاین
- Provider قابل‌تنظیم TSETMC برای جست‌وجوی نماد و تاریخچهٔ روزانهٔ بورس ایران
- timeout/retry و تست آفلاین Provider برای جلوگیری از وابستگی تست‌ها به شبکه

## 🔜 Milestone 2 — پلتفرم عملیاتی داده و تحلیل
- تکمیل جریان آنلاین بورس ایران: market watch، تازگی داده، rate limit، پایش و fallback
- اتصال Binance (کریپتو) و providerهای فارکس/سهام خارجی
- Analyzer برای بنیادی، اخبار، کدال، اسمارت‌مانی، جریان نقدینگی
- الگوهای قیمتی (`technical/patterns`) و استراتژی‌های ترکیبی (`technical/strategies`)
- Watchlist، Alerts چندکاناله (درون‌برنامه/ایمیل)
- Scheduler واقعی مطابق `configs/scheduler.yaml` (Background jobs)

## 🔜 Milestone 3 — هوش مصنوعی و بک‌تست
- مدل‌های یادگیری ماشین/LLM در `ai/models`, `ai/prediction`
- لایه‌ی Explainability پیشرفته (تولید گزارش تحلیلی به زبان طبیعی)
- موتور بک‌تست کامل روی داده‌ی تاریخی
- بهینه‌سازی پارامتر اندیکاتورها/استراتژی (`optimization/`)

## 🔜 Milestone 4 — رابط کاربری گرافیکی (PySide6)
- داشبورد، نمودار (candlestick + اندیکاتورها)، واچ‌لیست، پرتفوی، تنظیمات
- تم روشن/تیره طبق `configs/ui.yaml`
- گزارش‌های قابل چاپ/خروجی PDF و Excel

## 🔜 Milestone 5 — نسخه‌ی نصبی ویندوز
- بسته‌بندی با PyInstaller/Nuitka
- Setup.exe با Inno Setup (آیکون اختصاصی، میانبر دسکتاپ)
- مکانیزم به‌روزرسانی خودکار نسخه

## 🔜 Milestone 6 — قابلیت‌های تکمیلی
- سیستم پروفایل ریسک کاربر + Import/Export تنظیمات
- مقایسه هم‌زمان چند نماد
- مدیریت چند کاربره (در صورت نیاز)

> مالیات و قابلیت‌های مالیاتی در محدودهٔ این پروژه نیستند.
