# راهنمای کامل استفاده از ARYA AI Trader

نسخه: ۰.۲ (فقط بورس ایران + TSETMC + کدال)  
Branch پیشنهادی: `feat/continue-tse-codal-2026-10-06`

---

## ۱. پیش‌نیازها

| مورد | توضیح |
|------|--------|
| سیستم‌عامل | Windows 10/11 (PowerShell) |
| پایتون | ۳.۱۰ تا ۳.۱۵ (پیشنهاد پایدار: ۳.۱۲) |
| اینترنت | برای TSETMC و کدال؛ ترجیحاً **بدون VPN خارجی** |
| Git | برای دریافت آخرین کد |

---

## ۲. نصب از صفر

### ۲.۱ کلون / ورود به پروژه

```powershell
cd C:\Users\ziya
git clone https://github.com/ziya1346/ARYA_AI_TRADER.git
cd C:\Users\ziya\ARYA_AI_TRADER
git checkout feat/continue-tse-codal-2026-10-06
```

اگر از قبل پروژه را دارید:

```powershell
cd C:\Users\ziya\ARYA_AI_TRADER
git fetch origin
git checkout feat/continue-tse-codal-2026-10-06
git pull origin feat/continue-tse-codal-2026-10-06
```

### ۲.۲ ساخت محیط مجازی

```powershell
cd C:\Users\ziya\ARYA_AI_TRADER
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

اگر Activation مسدود شد:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

باید ابتدای خط `(.venv)` دیده شود.

### ۲.۳ نصب بسته

```powershell
python -m pip install -U pip setuptools wheel
python -m pip install -e .
```

اگر `pip install -e .` خطا داد، موقت:

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

### ۲.۴ تأیید نصب

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main --help
```

باید لیست دستورات را ببینید: `analyze`, `instrument`, `codal`, `client-type`, …

**نکته:** اگر `arya.exe` خطای Fatal launcher داد، همیشه از فرم زیر استفاده کنید:

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main <دستور>
```

---

## ۳. نقشه منابع داده

| منبع | چه می‌دهد | دستور ARYA |
|------|-----------|------------|
| **TSETMC** | قیمت، صف، جزئیات نماد، حقیقی/حقوقی، سهامداران | `instrument`, `client-type`, `shareholders`, `analyze` |
| **کدال** | اطلاعیه، افزایش سرمایه، مدیران، افشا | `codal`, بخش رویداد در `analyze` |
| **Symbol Master** (اختیاری) | لیست نماد + صنعت از فایل محلی | `list-industries`, `list-symbols --from-master` |

---

## ۴. دستورات روزمره (کپی/پیست)

همه دستورات را از پوشه پروژه و با venv اجرا کنید.

### ۴.۱ صفحه جزئیات نماد (معادل ParTree=151311)

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main instrument --ticker فولاد
.\.venv\Scripts\python.exe -m arya.cli.main instrument --ticker FOOLAD
.\.venv\Scripts\python.exe -m arya.cli.main instrument --ticker فملی --no-orderbook
```

خروجی: وضعیت، بازار/تابلو، صنعت، قیمت، EPS، P/E، شناوری، صف، لینک صفحه.

### ۴.۲ حقیقی و حقوقی

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main client-type --ticker فولاد
```

### ۴.۳ سهامداران عمده / تغییرات

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main shareholders --ticker فولاد
.\.venv\Scripts\python.exe -m arya.cli.main shareholders --changes --limit 30
.\.venv\Scripts\python.exe -m arya.cli.main shareholders --changes --only-increase
```

### ۴.۴ کدال

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main codal --symbol فولاد --event all
.\.venv\Scripts\python.exe -m arya.cli.main codal --symbol فولاد --event capital
.\.venv\Scripts\python.exe -m arya.cli.main codal --symbol فولاد --event board --pages 2
```

| `--event` | معنی |
|-----------|------|
| `all` | همه اطلاعیه‌های اخیر |
| `capital` | افزایش سرمایه / حق تقدم / پذیره‌نویسی |
| `board` | تغییرات مدیران / هیئت‌مدیره |

اگر خطا گرفتید: VPN خارجی را خاموش کنید و https://search.codal.ir را در مرورگر تست کنید.

### ۴.۵ تحلیل ترکیبی یک نماد

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main analyze --ticker FOOLAD
.\.venv\Scripts\python.exe -m arya.cli.main analyze --ticker FOOLAD --force-refresh
```

`--force-refresh` کش قیمت را نادیده می‌گیرد.

### ۴.۶ لیست نماد و صنعت (Symbol Master)

فایل اختیاری: `data/symbols/equities_flat.json`

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main list-industries
.\.venv\Scripts\python.exe -m arya.cli.main list-symbols --from-master
.\.venv\Scripts\python.exe -m arya.cli.main list-symbols --industry "فلزات اساسی"
```

### ۴.۷ اسکن و آمار کش

```powershell
.\.venv\Scripts\python.exe -m arya.cli.main scan --limit 5
.\.venv\Scripts\python.exe -m arya.cli.main scan --industry "بانک" --limit 5
.\.venv\Scripts\python.exe -m arya.cli.main cache-stats
```

---

## ۵. نگاشت نماد لاتین → فارسی

تستمک و کدال عمدتاً **نماد فارسی** می‌خواهند. ARYA چند نماد پرکاربرد را نگاشت می‌کند:

| لاتین | فارسی |
|-------|--------|
| FOOLAD | فولاد |
| FMLI | فملی |
| KHODRO | خودرو |
| SHASTA | شستا |
| BMLT | وبملت |
| … | `src/arya/providers/market/ticker_map.py` |

برای نمادهای دیگر همان نام فارسی تابلو را بزنید.

نماد فارسی در PowerShell:

```powershell
chcp 65001
.\.venv\Scripts\python.exe -m arya.cli.main instrument --ticker فولاد
```

---

## ۶. تنظیمات مهم

| فایل | نقش |
|------|-----|
| `configs/app.yaml` | کش، مسیر دیتابیس، محدوده بازار |
| `configs/providers.yaml` | driver تستمک/mock، فعال‌بودن کدال |
| `data/database/arya.db` | کش OHLCV |
| `data/symbols/equities_flat.json` | آرشیو نماد+صنعت |

نمونه فعال‌سازی کدال در `providers.yaml`:

```yaml
codal:
  enabled: true
  timeout_seconds: 25
  retries: 3
  min_interval_seconds: 1.0
```

---

## ۷. عیب‌یابی سریع

| علامت | کار |
|--------|-----|
| `Fatal error in launcher` / Python313 | از `python -m arya.cli.main` استفاده کنید؛ venv را از نو بسازید |
| `نماد پیدا نشد: FOOLAD` | `git pull` برای نگاشت، یا نماد فارسی |
| `pip` و خطای TOML در pyproject | `git pull` آخرین Branch |
| کدال timeout | VPN خاموش، مرورگر search.codal.ir، اینترنت موبایل |
| `deactivate` پیدا نشد | venv از قبل فعال نیست؛ مستقیم `Activate.ps1` |
| پروژه در مسیر خانه نیست | `cd` به پوشه‌ای که `src\arya` دارد |

تست شبکه کدال:

```powershell
nslookup search.codal.ir
```

---

## ۸. جریان کار پیشنهادی یک تریدر

1. جزئیات و تابلو: `instrument --ticker ...`  
2. پول هوشمند روز: `client-type --ticker ...`  
3. رویداد سرمایه/مدیران: `codal --event capital|board`  
4. جمع‌بندی: `analyze --ticker ...`  
5. در صورت نیاز: `shareholders --changes`

---

## ۹. آنچه هنوز فاز بعد است

- پارس کامل اعداد صورت مالی Excel از کدال  
- اتصال رسمی ClientType به وزن `smart_money` در Scoring  
- صف زنده مداوم / هشدار تلگرام  
- Merge نهایی به `main` پس از تست کامل Branch

---

## ۱۰. یک‌خط‌های خلاصه

```powershell
cd C:\Users\ziya\ARYA_AI_TRADER
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m arya.cli.main --help
.\.venv\Scripts\python.exe -m arya.cli.main instrument --ticker فولاد
.\.venv\Scripts\python.exe -m arya.cli.main client-type --ticker فولاد
.\.venv\Scripts\python.exe -m arya.cli.main codal --symbol فولاد --event capital
.\.venv\Scripts\python.exe -m arya.cli.main analyze --ticker FOOLAD
```
