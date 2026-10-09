# ARYA AI Trader

پلتفرم تحلیل چندبازاره (بورس ایران، ارز دیجیتال، فارکس) با معماری Enterprise،
موتور امتیازدهی وزن‌دار، موتور تصمیم‌گیری هوش مصنوعی و مدیریت ریسک.

> وضعیت فعلی: Milestone 1 — Core Pipeline + TSETMC foundation

## حاکمیت اجباری پروژه

قبل از هر کار، همه اعضای تیم و ایجنت‌ها باید AGENTS.md و قانون اساسی پلتفرم را بخوانند.
توسعه بر مبنای اطلاعات غیرمعتبر ممنوع است و هر تغییر باید Change Record، دلیل، شواهد و نتیجه اعتبارسنجی داشته باشد.

- AGENTS.md
- docs/governance/PLATFORM_CONSTITUTION.md
- docs/governance/STARTUP_CHECKLIST.md
- docs/governance/CHANGE_LEDGER.md
- docs/governance/OWNER_AND_IP_POLICY.md
- skills/arya-platform-governance/SKILL.md
- docs/sources/DRIVE_SOURCE_REGISTRY.md

اصل مهم: اگر شواهد کافی وجود ندارد، ایجنت باید STOP کند و از حدس‌زدن خودداری کند.

## محدوده پروژه

این پروژه فقط برای ارز دیجیتال، بورس ایران، فارکس و سهام خارجی است. قابلیت‌ها و مستندات مالیاتی عمداً خارج از محدوده‌اند.

## معماری کلی

Providers → Storage → Indicator Engine → Analysis Engine → Scoring Engine → AI Decision Engine → Risk Manager → Recommendation Engine → Dashboard

جزئیات قراردادها در docs/architecture/README.md آمده است.

## نصب

python -m venv .venv
pip install -r requirements.txt
pip install -e .

## اجرای تست‌ها

pip install -e ".[dev]"
pytest tests/ -v

## تنظیمات

رفتار سیستم از طریق فایل‌های YAML در configs/ کنترل می‌شود؛ از جمله indicators.yaml، providers.yaml، weights.yaml و filters.yaml.

## نقشه راه

به docs/roadmap/README.md مراجعه کنید.

## داده آنلاین بورس ایران

درایور پیش‌فرض بازار stock، tsetmc است و برای تست آفلاین mock استفاده می‌شود. راهنمای عملیات داده زنده و Drive در docs/operations/live-data-and-drive-sync.md قرار دارد.

## لایسنس و مالکیت

به LICENSE و docs/governance/OWNER_AND_IP_POLICY.md مراجعه کنید. سیاست پروژه، حفظ حقوق و اختیار پروژه برای مالک مخزن ziya1346 است؛ واگذاری حقوق مشارکت‌کنندگان باید در قرارداد کتبی مناسب تثبیت شود.