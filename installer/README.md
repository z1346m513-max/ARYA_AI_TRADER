# بستهٔ اجرایی ARYA Operations

این بسته برای اجرای عملیاتی دو جریان فاز اول آماده شده است:

- همگام‌سازی امن منابع Drive با rclone و ثبت manifest
- health-check اتصال زندهٔ market-watch و تاریخچهٔ TSETMC

## نصب روی Linux

پیش‌نیازها:

- Python 3.10 یا بالاتر
- `rclone`
- remote با نام `drive` در rclone
- دسترسی شبکه به `cdn.tsetmc.com` برای live check

```bash
bash installer/install-linux.sh
source .venv/bin/activate
```

فایل اجرایی اصلی:

```bash
./bin/arya-ops help
```

## فرمان‌ها

### وضعیت لحظه‌ای بازار

```bash
./bin/arya-ops live --ticker فولاد --json
```

### تاریخچهٔ روزانه

```bash
./bin/arya-ops history --ticker فولاد --limit 10 --json
```

### همگام‌سازی آزمایشی

حالت پیش‌فرض dry-run است و هیچ فایل واقعی را کپی نمی‌کند:

```bash
./bin/arya-ops sync \
  --remote drive:arya-phase-one \
  --local-dir data/phase-one
```

پس از بررسی log:

```bash
./bin/arya-ops sync \
  --remote drive:arya-phase-one \
  --local-dir data/phase-one \
  --apply
```

## خروجی و امنیت

- log در `data/logs/drive-sync.log` ذخیره می‌شود.
- manifest در `data/phase-one/manifest.json` ایجاد می‌شود.
- فایل‌های غیرمجاز یا بزرگ‌تر از سقف با وضعیت `rejected` ثبت می‌شوند.
- کلید Service Account و refresh token در این بسته قرار ندارند.
- worker به مسیر سفارش‌گذاری متصل نیست و live check فقط گزارش سلامت feed است.

## اجرای زمان‌بندی‌شده

پس از آزمایش دستی، از systemd timer یا cron استفاده کنید. نمونهٔ cron هر ۱۵ دقیقه:

```cron
*/15 * * * * cd /opt/arya-ai-trader && .venv/bin/python scripts/drive_sync_worker.py --remote drive:arya-phase-one --local-dir data/phase-one --apply >> data/logs/cron.log 2>&1
*/5 * * * * cd /opt/arya-ai-trader && .venv/bin/python scripts/tsetmc_live_check.py --json >> data/logs/tsetmc-health.log 2>&1
```

اجرای live check باید روی محیطی انجام شود که محدودیت شبکهٔ TSETMC را ندارد.
