# ARYA AI Trader — فقط بورس ایران (TSE)

پلتفرم تحلیل **بازار سرمایه ایران** (بورس و فرابورس) با معماری لایه‌ای،
موتور امتیازدهی وزن‌دار، تصمیم‌گیری قابل توضیح و مدیریت ریسک.

> **محدوده محصول:** فقط سهام و ابزارهای بازار ایران.  
> ارز دیجیتال، فارکس و سهام خارجی از دامنه محصول حذف شده‌اند.

> **وضعیت:** Milestone 1 — Core Pipeline + پایه TSETMC  
> پایپ‌لاین با Mock قابل تست است؛ درایور `tsetmc` برای داده روزانه بورس در دسترس است.

## معماری

```
Providers (TSETMC/Mock) → Storage → Indicator Engine → Analysis →
Scoring → AI Decision → Risk Manager → Recommendation → Dashboard/CLI
```

## نصب

```bash
python -m venv .venv
# ویندوز: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## اجرای سریع (CLI)

```bash
# تحلیل یک نماد بورسی
arya analyze --ticker FOOLAD

# لیست نمادها
arya list-symbols

# اسکن
arya scan
```

بازار همیشه `stock` است؛ سوییچ crypto/forex وجود ندارد.

بدون نصب پکیج:

```bash
PYTHONPATH=src python -m arya.cli.main analyze --ticker FOOLAD
```

## تنظیمات

| فایل | مسئولیت |
|------|---------|
| `configs/app.yaml` | تنظیمات کلی، فقط بازار stock |
| `configs/indicators.yaml` | اندیکاتورها |
| `configs/weights.yaml` | وزن و پروفایل ریسک |
| `configs/providers.yaml` | mock یا tsetmc برای بورس ایران |
| `configs/scheduler.yaml` | جلسه معاملاتی تهران |
| `configs/ui.yaml` | تم و زبان |

برای تست آفلاین در `providers.yaml` مقدار `driver` را روی `mock` بگذارید.

## مستندات تمرکز TSE

- [`docs/TSE_TRADER_RECOMMENDATIONS.md`](docs/TSE_TRADER_RECOMMENDATIONS.md)
- [`docs/REMOVAL_CHECKLIST.md`](docs/REMOVAL_CHECKLIST.md)
- [`docs/ROADMAP_TSE.md`](docs/ROADMAP_TSE.md)

## لایسنس

مطابق [`LICENSE`](LICENSE).
