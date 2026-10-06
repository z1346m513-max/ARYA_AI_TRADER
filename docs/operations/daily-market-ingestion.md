# دریافت و پردازش داده‌ی روزانه‌ی بازار

## مختصر

این سند مسیر استاندارد دریافت، اعتبارسنجی و نرمال‌سازی فایل‌های دستی بازار
(Excel/CSV) را توضیح می‌دهد. هدف این است که داده‌ی روزانه‌ی بازار به‌صورت
کنترل‌شده، قابل‌بازتولید و قابل‌ردیابی وارد سیستم شود.

## مسیر پردازش

```
Excel/CSV دستی
    ↓
Inbox (data/inbox/market/)
    ↓
Loader (excel_loader.py)
    ↓
Validator (validator.py) ──→ Quality Report
    ↓
Normalizer (normalizer.py) ──→ Normalized CSV/JSONL
    ↓
Archive (data/archive/market/)
    ↓
Manifest (data/manifests/)
    ↓
Agentهای تحلیل (آینده)
```

هیچ Agent یا تحلیلی نباید مستقیماً فایل خام را بخواند؛ تمام تحلیل‌ها باید از
داده‌ی normalized و manifest-دار استفاده کنند.

## ساختار پوشه‌ها

```
data/
  inbox/market/       فایل‌های جدید ورودی
  processing/         فایل‌های در حال پردازش
  archive/market/     فایل‌های پردازش‌شده و معتبر
  rejected/           فایل‌های رد‌شده
  normalized/         داده‌ی نرمال‌شده
  manifests/          manifest‌ها (SHA-256 + metadata)
  agent_outputs/      خروجی Agentهای تحلیل (آینده)
  reports/daily/      گزارش‌های کیفیت و روزانه
```

## فرمت فایل ورودی

### ستون‌های الزامی

| ستون | نوع | توضیح |
|---|---|---|
| `timestamp` | datetime | زمان کندل (ISO 8601، ترجیحاً timezone-aware) |
| `symbol` | string | نماد معاملاتی |
| `open` | float | قیمت باز شدن |
| `high` | float | بالاترین قیمت (>= max(open, close)) |
| `low` | float | پایین‌ترین قیمت (<= min(open, close)) |
| `close` | float | قیمت بسته شدن |
| `volume` | float | حجم معاملات (>= 0) |

### ستون‌های اختیاری

| ستون | پیش‌فرض | توضیح |
|---|---|---|
| `value` | 0.0 | ارزش معاملات |
| `currency` | IRR | واحد پول |
| `market` | stock | نوع بازار |

### نام‌گذاری پیشنهادی

```
market_YYYY-MM-DD_provider.xlsx
```

مثال: `market_2026-10-06_tsetmc.xlsx`

## اجرا

### پردازش یک فایل

```bash
python scripts/process_market_file.py \
  --input data/inbox/market/market_2026-10-06.xlsx \
  --format csv
```

### پردازش تمام فایل‌های inbox

```bash
python scripts/process_market_file.py --inbox
```

### خروجی JSON کامل

```bash
python scripts/process_market_file.py \
  --input data/inbox/market/market_2026-10-06.xlsx \
  --json
```

## خروجی

برای هر فایل پردازش‌شده:

1. **فایل نرمال‌شده:** `data/normalized/market_2026-10-06_normalized.csv`
2. **Manifest:** `data/manifests/market_2026-10-06.xlsx.manifest.json`
3. **گزارش کیفیت (Markdown):** `data/reports/daily/market_2026-10-06_quality.md`
4. **گزارش کیفیت (JSON):** `data/reports/daily/market_2026-10-06_quality.json`
5. **فایل اصلی در Archive:** `data/archive/market/market_2026-10-06.xlsx`

## اعتبارسنجی‌ها

| بررسی | شدت | توضیح |
|---|---|---|
| ستون‌های الزامی | REJECT | تمام ستون‌های الزامی باید وجود داشته باشند |
| قیمت مثبت | ERROR | open, high, low, close باید مثبت باشند |
| حجم غیرمنفی | ERROR | volume نمی‌تواند منفی باشد |
| سازگاری OHLC | ERROR | high >= max(open, close) و low <= min(open, close) |
| ردیف تکراری | WARNING | (timestamp, symbol) نباید تکراری باشد |
| ترتیب زمانی | WARNING | داده باید به ترتیب زمانی مرتب باشد |
| timezone-aware | WARNING | timestamp باید timezone-aware باشد |

## Idempotency

اگر فایلی قبلاً پردازش شده باشد (بر اساس SHA-256)، پردازش مجدد انجام نمی‌شود
و manifest قبلی برمی‌گردد. این کار از پردازش تکراری و مخلوط شدن داده جلوگیری
می‌کند.

## محدودیت‌ها

- این لایه صرفاً خواندنی است: به صرافی، API یا broker وصل نمی‌شود.
- هیچ سفارش یا معامله‌ای ثبت نمی‌کند.
- نتایج صرفاً برای تحقیق هستند.
- اتصال به Google Drive و زمان‌بندی خودکار در فاز بعدی اضافه می‌شود.

## وابستگی‌ها

- `openpyxl` برای خواندن فایل‌های Excel (.xlsx, .xls)
- `pandas` برای پردازش داده
- `pydantic` (در صورت نیاز در آینده)
