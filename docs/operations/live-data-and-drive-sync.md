# عملیات داده زنده و همگام‌سازی منابع

## ۱) فراهم‌کردن دسترسی Google Drive

دو روش پیشنهادی وجود دارد:

### روش تعاملی برای همین نشست

1. مرورگر Manus را روی یکی از لینک‌های Drive باز کنید.
2. با حسابی که دسترسی Viewer یا Editor به پوشه دارد وارد شوید.
3. پس از ورود، فایل‌ها و پوشه‌ها قابل بررسی و خلاصه‌سازی هستند.
4. این روش برای بررسی دستی مناسب است و **همگام‌سازی unattended** ایجاد نمی‌کند.

### روش عملیاتی برای همگام‌سازی فاز اول

برای همگام‌سازی خودکار، بهترین روش یک حساب سرویس یا OAuth محدودشده است:

1. در Google Cloud یک پروژهٔ جدا برای ARYA ایجاد کنید و Google Drive API را فقط
   برای همان پروژه فعال کنید.
2. یک Service Account بسازید و فقط ایمیل همان حساب را روی دو پوشهٔ Drive با
   سطح `Viewer` share کنید؛ سطح Editor لازم نیست.
3. کلید JSON را هرگز داخل Git، فایل `.env` commit‌شده یا پیام گفتگو قرار ندهید.
   آن را در Secret Manager/secret محیط عملیاتی بگذارید.
4. sync worker فقط metadata، hash فایل، زمان تغییر و نسخهٔ فایل را ثبت کند؛
   فایل اصلی را بدون نیاز کپی نکند و برای فایل‌های خارج از حوزه ردپا ثبت کند.
5. قبل از واردکردن سند به knowledge base، allowlist پسوند، اندازه، MIME type و
   پوشهٔ مجاز اعمال شود. لینک‌ها و منابع مالیاتی از دامنهٔ پروژه حذف شوند.
6. برای هر اجرای sync، manifest با `file_id`, `modified_time`, `sha256`, `status`
   ذخیره شود تا تکرارپذیری و rollback ممکن باشد.

برای حساب شخصی، OAuth کاربرمحور با refresh token محدود به Drive read-only از
Service Account مناسب‌تر است. توکن و client secret باید فقط در secret store
محیط عملیاتی نگه‌داری شوند.

### Worker پایتونی

برای اجرای قابل‌ردیابی sync و پردازش فایل‌ها از `scripts/drive_sync_worker.py`
استفاده کنید. حالت پیش‌فرض dry-run است:

```bash
PYTHONPATH=src python scripts/drive_sync_worker.py \
  --remote drive:arya-phase-one \
  --local-dir data/phase-one
```

پس از بررسی log، اجرای واقعی را با `--apply` انجام دهید:

```bash
PYTHONPATH=src python scripts/drive_sync_worker.py \
  --remote drive:arya-phase-one \
  --local-dir data/phase-one \
  --apply
```

Worker فایل‌های مجاز را با SHA-256 در `manifest.json` ثبت می‌کند، JSON/CSV را
به‌صورت سبک بررسی می‌کند و PDF/XLSX را برای استخراج امن بعدی در صف metadata
قرار می‌دهد. فایل‌های خارج از allowlist یا بزرگ‌تر از سقف، rejected می‌شوند.

## ۲) تست‌های اتصال زنده به بورس ایران

تست‌های واحد پروژه عمداً Mock هستند و نباید به بازار زنده وابسته شوند. تست زنده
باید به‌صورت **smoke test جداگانه** در محیط عملیاتی اجرا شود:

```bash
PYTHONPATH=src python scripts/live_tsetmc_smoke.py \
  --ticker فولاد --limit 10 --json
```

برای بررسی مستقیم snapshot لحظه‌ای market-watch نیز اجرا کنید:

```bash
PYTHONPATH=src python scripts/tsetmc_live_check.py \
  --ticker فولاد --json
```

این فرمان تعداد quoteهای دریافتی، quote معتبر، قیمت آخر، قیمت پایانی، حجم و
زمان بررسی را گزارش می‌کند. خروجی فقط health-check است و به هیچ مسیر سفارش‌گذاری
متصل نیست.

این تست موارد زیر را کنترل می‌کند:

- resolve شدن نماد در TSETMC
- دریافت حداقل تعداد کندل
- مثبت و معتبر بودن قیمت‌ها
- مرتب‌بودن timestampها
- ثبت زمان اجرای تست و آخرین timestamp داده

### سیاست اجرا

- smoke test در CI عمومی اجرا نشود؛ به شبکه و گاهی IP مناسب ایران نیاز دارد.
- در محیط عملیاتی با cron، scheduler یا health-check هر ۵ تا ۱۵ دقیقه اجرا شود؛
  در ساعات بسته‌بودن بازار، نتیجه با وضعیت `market_closed` تفسیر شود نه شکست داده.
- retry و timeout محدود باشد و بین درخواست‌ها backoff اعمال شود؛ از حلقهٔ بی‌نهایت
  و موازی‌سازی تهاجمی روی endpointهای TSETMC خودداری شود.
- شکست تست باید alert بدهد، اما نباید به‌تنهایی سفارش یا معامله ایجاد کند.
- دادهٔ آخرین موفق و زمان تازگی در storage نگه‌داری شود تا dashboard بتواند
  `stale_data` را از دادهٔ تازه جدا کند.
- مرحلهٔ بعدی باید market-watch و client-type را هم با contract test و fixture
  مصنوعی پوشش دهد.

## ۳) منابعی که به قابلیت تبدیل شدند

- منابع فیلتر TSETMC: حجم، ارزش معاملات، درصد تغییر، صف و قدرت خریدار →
  `arya.scanner.filters`
- بورس‌تریدر و نقشه بازار: پایش لحظه‌ای، جریان پول، watchlist و alert → درایور
  و scheduler فاز بعد
- CodalChart: رویداد افزایش سرمایه و اطلاعیه‌های بنیادی → adapter Codal فاز بعد
- Rahavard365 و ابزارهای نموداری: فیلتر، چندبازه‌ای و مقایسهٔ بازدهی → استراتژی
  روند-مومنتوم و برنامهٔ backtest
- منابع کریپتو و DEX: تحلیل wallet و نقدشوندگی → خارج از فاز اول بورس، ولی در
  قرارداد provider چندبازاره باقی می‌ماند.

منابع تبلیغاتی، حساب‌های کاربری و لینک‌های مالیاتی بوکمارک وارد منطق پروژه
نشده‌اند.

## ۴) کنترل کیفیت و ردپای دادهٔ تحلیل

پیش از تحلیل نماد، فیلتر بازار یا اجرای استراتژی، `AryaApp` سری OHLCV را از
`arya.data_quality.validate_ohlcv_series` عبور می‌دهد. سری خالی، قیمت غیرمتناهی
یا غیرمثبت، حجم منفی، OHLC ناسازگار، timestamp تکراری/نامرتب یا timestampهای
دارای timezone ناسازگار رد می‌شوند. رکورد اعتبارسنجی پیش از تصمیم‌گیری در جدول
SQLite با نام `data_quality_runs` ذخیره می‌شود؛ شامل provider، نماد/بازار،
timeframe، زمان دریافت برنامه به UTC، تعداد ردیف، بازهٔ timestamp داده، هش
SHA-256 snapshot نرمال‌شده و issueها. فیلد `data_quality_run_id` در Recommendation
به همان رکورد اشاره می‌کند. دادهٔ ردشده به analyzer نمی‌رسد و CLI با کد خروج ۲
متوقف می‌شود.

این checks فقط سلامت ساختاری را بررسی می‌کنند. زمان دریافت محلی، timestamp منبع
نیست؛ آزمون حاضر freshness بر مبنای تقویم بورس ایران، تعطیلات، توقف نماد، کامل‌بودن
کندل‌ها یا معتبر بودن اقتصادی قیمت را اثبات نمی‌کند. تا زمان تعریف تقویم و قرارداد
دادهٔ معتبر، آن‌ها نباید از این نتیجه‌ها «دادهٔ تازه/رسمی» استنتاج کنند. جزئیات
ممیزی کتابخانه‌های متن‌باز و تصمیم‌های مجوز در
`docs/research/OSS_REUSE_REVIEW_20261028.md` ثبت شده است.

## ۵) اتصال مستقیم TSETMC و محدودیت‌های فعلی

در `configs/providers.yaml` درایور سهام همین حالا `tsetmc`، فعال، با
`https://cdn.tsetmc.com`، timeout و retry محدود پیکربندی شده است. پیاده‌سازی
`src/arya/providers/market/tsetmc_provider.py` از `urllib` استاندارد پایتون
استفاده می‌کند و به SDK یا کد اتصال شخص ثالث نیاز ندارد. کد فعلی درخواست GET
برای جست‌وجوی نماد در `/api/Instrument/GetInstrumentSearch/{ticker}`، تاریخچهٔ
روزانه در `/api/ClosingPrice/GetClosingPriceDailyList/{insCode}/{limit}` و
market-watch در `/api/ClosingPrice/GetMarketWatch?...` می‌فرستد. این‌ها رفتار
مشاهده‌شدهٔ کد فعلی‌اند؛ در این مخزن specification رسمی/تضمین پایداری API ثبت
نشده است.

برای آزمون خواندنی از محیط اجرا:

```bash
PYTHONPATH=src python3 scripts/live_tsetmc_smoke.py \
  --ticker فولاد --limit 10 --timeout 15 --json
PYTHONPATH=src python3 -m arya.cli.main analyze --ticker فولاد --market stock
```

در 2026-10-28، sandbox نام دامنه را resolve کرد ولی اتصال HTTPS timeout شد؛ در
نتیجه هیچ قیمت زنده دریافت یا تأیید نشد. آزمون را از میزبان مجازِ اجرای واقعی با
خروجی شبکهٔ مجاز به `cdn.tsetmc.com:443` تکرار کنید؛ timeout یک sandbox اثبات
خرابی TSETMC نیست.

### موانع لازم‌الحل پیش از ادعای دادهٔ معتبر

- `_resolve_instrument` ابتدا تطبیق دقیق می‌کند، اما اگر exact ticker پیدا نشود
  به اولین نتیجهٔ جست‌وجو fallback می‌کند. این رفتار می‌تواند شناسهٔ ابزار دیگری
  را برگرداند؛ پیش از مصرف عملیاتی، exact match را اجباری و نتیجهٔ مبهم را رد کنید.
- `_timestamp` در نبود `dEven`/`date` از `datetime.now(UTC)` استفاده می‌کند.
  این زمان ساختگی برای مشاهدهٔ بازار است؛ در قرارداد «بدون دادهٔ مصنوعی»، نبود
  تاریخ منبع باید خطای داده باشد و سری باید رد شود.
- `fetch_market_watch` فیلد `timestamp` را با زمان اجرای محلی برنامه پر می‌کند؛
  این retrieval time است، نه زمان quote از TSETMC. آن را با نام جداگانه ذخیره
  کنید و فقط در صورت وجود/تأیید، timestamp واقعی منبع را ثبت کنید.
- آزمون‌های pytest برای Provider از پاسخ fixture استفاده می‌کنند. تا smoke زنده
  از شبکهٔ مجاز، تطبیق مستقل نماد/قیمت/زمان و مستندشدن semantics فیلدها موفق
  نشده‌اند، این Provider را «از نظر دسترسی/تازگی تأییدشده» معرفی نکنید.
