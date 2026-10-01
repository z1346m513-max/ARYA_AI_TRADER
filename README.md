# ARYA AI Trader

پلتفرم تحلیل چندبازاره (بورس ایران، ارز دیجیتال، فارکس) با معماری Enterprise،
موتور امتیازدهی وزن‌دار، موتور تصمیم‌گیری هوش مصنوعی و مدیریت ریسک.

> **وضعیت فعلی: Milestone 1 — Core Pipeline + TSETMC foundation**
> پایپ‌لاین اصلی با داده‌ی Mock قابل تست است و provider قابل‌تنظیم TSETMC برای
> دادهٔ روزانهٔ بورس ایران اضافه شده است. GUI، بک‌تست و نصب‌کنندهٔ ویندوز هنوز
> در نقشه راه (`docs/roadmap`) هستند.

## محدوده پروژه

این پروژه فقط برای **ارز دیجیتال، بورس ایران، فارکس و سهام خارجی** است.
قابلیت‌ها و مستندات مالیاتی عمداً خارج از محدوده‌اند. اولویت فاز اول، ساخت
پلتفرم واقعی با دادهٔ آنلاین بورس ایران و کنترل صریح تازگی/خطای منبع داده است.

## معماری کلی

```
Providers → Storage → Indicator Engine → Analysis Engine →
Scoring Engine → AI Decision Engine → Risk Manager →
Recommendation Engine → Dashboard
```

جزئیات کامل هر لایه، قراردادها (Contracts) و نحوه‌ی افزودن Provider/اندیکاتور/
Analyzer جدید در [`docs/architecture/README.md`](docs/architecture/README.md) آمده است.

## نصب

```bash
python -m venv .venv
source .venv/bin/activate        # ویندوز: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## اجرای سریع (CLI)

```bash
# تحلیل یک نماد
arya analyze --ticker FOOLAD --market stock

# لیست نمادهای موجود در یک بازار (Mock)
arya list-symbols --market crypto

# تحلیل تمام نمادهای یک بازار
arya scan --market crypto
```

یا بدون نصب پکیج:

```bash
PYTHONPATH=src python -m arya.cli.main analyze --ticker BTCUSDT --market crypto
```

## اجرای تست‌ها

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## تنظیمات

همه‌ی رفتار سیستم از طریق فایل‌های YAML در `configs/` کنترل می‌شود، بدون نیاز
به تغییر کد:

| فایل | مسئولیت |
|---|---|
| `app.yaml` | تنظیمات کلی برنامه، لاگ، مسیرهای ذخیره‌سازی |
| `indicators.yaml` | فعال/غیرفعال، پارامتر، وزن، رنگ، تایم‌فریم و هشدار هر اندیکاتور |
| `weights.yaml` | وزن هر بخش تحلیلی (تکنیکال/بنیادی/اخبار/...) + پروفایل‌های ریسک |
| `providers.yaml` | انتخاب درایور هر منبع داده (TSETMC برای stock و Mock برای تست) |
| `scheduler.yaml` | زمان‌بندی به‌روزرسانی خودکار به تفکیک بازار |
| `ui.yaml` | تم، زبان، ابعاد پنجره‌ها (برای GUI آینده) |

## نقشه راه

به [`docs/roadmap/README.md`](docs/roadmap/README.md) مراجعه کنید.

## دادهٔ آنلاین بورس ایران

درایور پیش‌فرض بازار `stock`، `tsetmc` است و از endpointهای JSON عمومی
TSETMC استفاده می‌کند. timeout، retry و `base_url` در `configs/providers.yaml`
قابل تنظیم‌اند. برای اجرای تست‌ها یا توسعهٔ بدون شبکه، درایور بازار را به
`mock` تغییر دهید. این اتصال فعلاً تاریخچهٔ روزانه (timeframe=`1d`) را پوشش
می‌دهد و قبل از استفادهٔ عملی باید محدودیت شبکه، نرخ درخواست و کیفیت دادهٔ
روز جاری در محیط استقرار بررسی شود.

## لایسنس

به فایل [`LICENSE`](LICENSE) مراجعه کنید (قابل تغییر بر اساس نیاز کسب‌وکار).
