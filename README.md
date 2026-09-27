# ARYA AI Trader

پلتفرم تحلیل چندبازاره (بورس ایران، ارز دیجیتال، فارکس) با معماری Enterprise،
موتور امتیازدهی وزن‌دار، موتور تصمیم‌گیری هوش مصنوعی و مدیریت ریسک.

> **وضعیت فعلی: Milestone 2 — TSETMC Provider (گام نخست)**
> پایپ‌لاین اصلی کامل و اجراشدنی است؛ داده‌ی Mock برای تست آفلاین حفظ شده و
> Provider واقعی TSETMC برای بورس ایران اضافه شده است. GUI با PySide6، Binance،
> Codal، بک‌تست و نصب‌کننده‌ی ویندوز همچنان در نقشه راه (`docs/roadmap`) هستند.

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
| `providers.yaml` | انتخاب درایور هر منبع داده (mock / tsetmc / binance / ...) |
| `scheduler.yaml` | زمان‌بندی به‌روزرسانی خودکار به تفکیک بازار |
| `ui.yaml` | تم، زبان، ابعاد پنجره‌ها (برای GUI آینده) |

## نقشه راه

به [`docs/roadmap/README.md`](docs/roadmap/README.md) مراجعه کنید.

## لایسنس

به فایل [`LICENSE`](LICENSE) مراجعه کنید (قابل تغییر بر اساس نیاز کسب‌وکار).
