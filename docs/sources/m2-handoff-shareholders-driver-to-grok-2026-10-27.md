# یادداشت تحویل M2 — درایور واقعی سهامداران آمادهٔ ادغام (از Z.ai به Grok)

**Date:** 2026-10-27 (۱۴۰۵/۰۸/۰۵)
**از:** ایجنت Z.ai (برنچ `feat/m2-phase0-real-data` — ۵ کامیت محلی، push نیازمند credential مالک)
**به:** ایجنت Grok (برنچ `feat/m2-smart-money-offline` — مالک ShareholderFlowMetrics، mock driver، ShareChangeAnalyzer، daily-ingest)
**موضوع:** نقطهٔ اتصال دو برنچ: خروجی درایور واقعی ← مصرف در مدل و Analyzer

---

## ۱. خلاصهٔ یک‌پاراگرافی

درایور واقعی حقیقی/حقوقی TSETMC (تصمیم تأییدشدهٔ مالک در CR-20261024-002) پیاده‌سازی و روی ۹ تست آفلاین با فیکسچر واقعی پایدار شد؛ کل مخزن ۳۱ پاس. خروجی `fetch_shareholder_flow` یک dict است که «دقیقاً» با کلیدهای `FLOW_KEYS` ساخته می‌شود تا در مدل شما به‌صورت `ShareholderFlowMetrics(**flow)` مصرف شود. هیچ تغییری در مدل، mock driver یا ShareChangeAnalyzer داده نشده است. این سند قرارداد دقیق اتصال و کارهای سمت شما (daily-ingest) را مشخص می‌کند.

## ۲. چه چیزهایی آماده است (کدام فایل‌ها، کدام کامیت‌ها)

| فایل | نقش | کامیت |
|---|---|---|
| `src/arya/providers/shareholders/base.py` | قرارداد `ShareholderDataProvider`، `FLOW_KEYS`، `ShareholderSnapshotRow`، `InstrumentIdentity`، رجیستری | `458c667` |
| `src/arya/providers/shareholders/tsetmc_client_type.py` | درایور واقعی: resolve نماد (cdn VERIFIED)، snapshot بازارکامل (old VERIFIED)، گیت ساختاری، گیت انتساب تاریخ با روزهای بستهٔ واقعی | `458c667` |
| `tests/providers/test_tsetmc_client_type.py` | ۹ تست آفلاین روی فیکسچر واقعی `12_PROXY_old_ClientTypeAll_sample.raw.txt` | `458c667` |
| `configs/providers.yaml` بخش `shareholders:` | پیکربندی (فقط این بخش — مالکیت بخش: Z.ai) | `458c667` |
| `docs/sources/evidence/2026-10-24/` (۱۷ فایل + INDEX.md) | شواهد خام واقعی + ثبت شکست‌ها | `46bea07`, `4ee3e63`, `d64132b` |
| `docs/sources/project-utilization-map-2026-10-24.md` | نقشهٔ بهره‌برداری پروژه‌ها (مستقیم/شبیه‌سازی/ردشده با دلیل) | `d64132b` |

## ۳. قرارداد اتصال (دقیق — همین را مصرف کنید)

```python
from arya.providers.shareholders import (
    ShareholderProviderRegistry,
    TsetmcClientTypeProvider,
)

# ساخت از رجیستری (هم‌الگوی لایهٔ market):
provider = ShareholderProviderRegistry.create("tsetmc_client_type")

# یا با پیکربندی providers.yaml (بخش shareholders):
provider = TsetmcClientTypeProvider(
    base_url_cdn="https://cdn.tsetmc.com",
    base_url_old="https://old.tsetmc.com",
    timeout=15.0, retries=3,
    snapshot_volume_tolerance=0.05,
)

flow = provider.fetch_shareholder_flow("فولاد", days=30)
# flow دقیقاً این کلیدها را دارد (ترتیب کلیدها بی‌اهمیت):
# {
#   "shareholder_count_series":   None (فعلاً همیشه — بند ۵),
#   "individual_avg_buy_value":   float یا None,
#   "individual_avg_sell_value":  float یا None,
#   "legal_buy_share":            float یا None,
#   "legal_net_buy_value":        float یا None,
#   "data_quality":               "usable" | "partial" | "missing",
# }
metrics = ShareholderFlowMetrics(**flow)   # نقطهٔ اتصال با مدل شما
```

**الزام مدل شما:** `ShareholderFlowMetrics` باید این ۶ فیلد را با همین نام‌ها بپذیرد. اگر نام فیلدی در مدل شما فرق دارد، «تغییر FLOW_KEYS بدون هماهنگی ممنوع است» (CR-20261024-002) — لطفاً نام پیشنهادی را در پاسخ هماهنگی بنویسید تا یکی از دو طرف با یک تغییر کوچک هم‌تراز شود. ترجیح: اگر مدل شما فیلد کمتری دارد، نگاشت در مرز (adapter نازک در سمت شما) انجام شود، نه تغییر قرارداد.

## ۴. معناشناسی data_quality (قرارداد مصرف در Analyzer)

| مقدار | یعنی چه | رفتار مورد انتظار Analyzer |
|---|---|---|
| `usable` | snapshot واقعی + انتساب موفق تاریخ به یک روز بستهٔ واقعی (تطبیق حجم در تلورانس ۵٪) + VWAP واقعی همان روز | متریک‌ها معتبرند؛ مصرف عادی |
| `partial` | دادهٔ واقعی دیده شد ولی تاریخ snapshot قابل انتساب نیست ⇒ همهٔ متریک‌ها None هستند | **نباید** به‌عنوان امتیاز/سیگنال مصرف شود؛ فقط «مشاهدهٔ ناقص واقعی» ثبت شود |
| `missing` | نماد امروز در snapshot کل بازار نیست (مشاهدهٔ واقعیِ نبود) | مثل partial؛ شاید نماد متوقف/بدون معامله بوده باشد |

دلیل این محافظه‌کاری: تاریخ snapshot در پاسخ سرور نیست و در شواهد فاز ۰ حجم فولاد با هیچ‌یک از ۵ روز پایانی تطبیق نکرد (فایل 13). سیاست «فقط دادهٔ واقعی» مالک اجازهٔ حدس تاریخ را نمی‌دهد. اگر بعد از ادغام در ساعات درست اجرا شود، انتساب خودکار برقرار می‌شود و بدون تغییر کد `usable` می‌گیرید — بند ۵.

## ۵. کارهای سمت شما (daily-ingest — مالکیت Grok)

1. **زمان اجرا:** snapshot را «یک‌بار در روز، بلافاصله پس از بسته‌شدن بازار» بگیرید (پیشنهاد: ~۱۳:۱۵ تهران). سرور همیشه آخرین روز معاملاتی را می‌دهد و پارامتر `t` نادیده گرفته می‌شود (فایل 13)؛ یعنی دیروز با امروز بازنویسی می‌شود ⇒ **نگه‌داشت روزانه تنها راه ساخت تاریخچه است.**
2. **ذخیرهٔ خام اول، مشتق بعد:** ردیف‌های خام snapshot را با کلید `(old_ins_code, attribution_date)` ذخیره کنید؛ attribution را از `inspect_snapshot(ticker)` بگیرید (شامل `attribution.verdict` و `relative_diff` برای دیباگ). اگر `verdict == "unattributable"` بود، ردیف را با `date=NULL` و دادهٔ خام کامل ذخیره کنید — فردا با شواهد بیشتر قابل رفع است.
3. **سری `shareholder_count_series`:** درایور فعلاً همیشه None برمی‌گرداند (سری بدون تاریخ = دادهٔ ساختگی ممنوع). همین که daily-ingest شما چند روز ذخیرهٔ تاریخ‌دار ساخت، این سری از روی ذخیرهٔ شما قابل محاسبه است؛ اگر می‌خواهید درایور خودش سری بدهد، قرارداد جدید (مثلاً پارامتر `history_source`) باید با توافق دو طرف به CR بعدی برود.
4. **نبود credential: همین مسیر کافی است.** REST رسمی (`api.tsetmc.com`) نیاز به نام کاربری/رمز از شرکت مدیریت فناوری بورس دارد (شواهد فایل 17)؛ تا زمانی که مالک credential نگیرد، ClientTypeAll بدون-auth مسیر عملیاتی است.

## ۶. تست و راستی‌آزمایی قبل از ادغام

```bash
python -m pytest -q          # کل مخزن: ۳۱ passed
python -m pytest tests/providers/test_tsetmc_client_type.py -v
```

فیکسچرها واقعی‌اند (snapshot خام ۱۰۵KB ضبط‌شده). دو ردیف closing داخل تست‌ها سنتتیک‌اند و با برچسب صریح «فقط برای ریاضی انتساب» — این دو در مسیر اجرای production نیستند و نقض سیاست فقط-داده-واقعی محسوب نمی‌شوند (توضیح کامل در docstring همان تست‌ها).

## ۷. مرز مالکیت (تأییدشدهٔ مالک — یادآوری)

- Z.ai دست نمی‌زند به: مدل `ShareholderFlowMetrics`، mock driver، `ShareChangeAnalyzer`، daily-ingest skeleton، اسناد pytse/ماتریس، و کل برنچ `feat/m2-smart-money-offline`.
- Grok دست نمی‌زند به: `src/arya/providers/shareholders/**`، `tests/providers/test_shareholders_*.py` / `test_tsetmc_client_type.py`، بخش `shareholders:` در `configs/providers.yaml`، پوشهٔ شواهد، CR-001/CR-002 و اسناد sources من.
- فایل‌های مشترک: `configs/providers.yaml` (بخشی) و `CHANGE_LEDGER.md` (فقط append در زمان merge توسط مالک).

## ۸. وضعیت برنچ و ترتیب پیشنهادی merge

برنچ `feat/m2-phase0-real-data` (۵ کامیت: `d5533de`، `46bea07`، `4ee3e63`، `458c667`، `d64132b`) فعلاً در محیط ساخت است؛ push به‌دلیل نبود credential ناموفق بود (2026-10-27 دوباره آزموده شد). ترتیب پیشنهادی به مالک: (۱) push هر دو برنچ، (۲) merge `feat/m2-phase0-real-data` به `feat/m2-smart-money-offline` یا مستقیم به main — تداخل فایلی نداریم چون محدوده‌ها تفکیک‌اند؛ تنها نقطهٔ مشترک بالقوه `configs/providers.yaml` است که فقط بخش `shareholders:` را اضافه کرده‌ایم. بعد از merge، سطرهای Ledger مربوط به CR-001/CR-002 را طبق پیوست الف همان اسناد append کنید.

## ۹. موارد باز که بر ادغام اثر ندارد ولی برای اطلاع است

WSDL کامل TsePublicV2 و GetClientType تک‌نمادی از محیط ما احراز نشدند (فایل‌های 15/16 — دو شکست واقعی هرکدام)؛ REST رسمی credential می‌خواهد (فایل 17). هیچ‌کدام مسیر ClientTypeAll را مسدود نمی‌کنند. جزئیات: `docs/sources/evidence/2026-10-24/INDEX.md` بند «هنوز UNVERIFIED».
