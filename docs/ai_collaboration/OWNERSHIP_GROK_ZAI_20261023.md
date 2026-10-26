# جدول مالکیت نهایی — Grok / Z.ai

**تاریخ نهایی‌سازی (Grok):** 2026-10-23 
**مرجع پیام Z.ai:** branch `feat/m2-phase0-real-data` + شواهد `docs/sources/evidence/`

## مالکیت فایل / مسیر

| مسیر | مالک | وضعیت | یادداشت |
|------|------|--------|----------|
| `docs/changes/CR-20261024-001.md` | Z.ai | Z.ai | ADR/CR ShareChange |
| `docs/sources/connector-and-repo-evaluation-2026-10-24.md` | Z.ai | Z.ai | |
| `docs/sources/evidence/**` | Z.ai | Z.ai | شواهد خام فاز ۰ |
| `scripts/phase0_evidence.py` | Z.ai | Z.ai | |
| `docs/changes/CR-20261024-002.md` + utilization map | Z.ai | بعدی | |
| `src/arya/providers/shareholders/**` **درایورهای واقعی** (غیر mock) | Z.ai | بعدی | |
| `tests/providers/test_shareholders_*.py` | Z.ai | بعدی | |
| بخش `shareholders:` در `configs/providers.yaml` (driver واقعی) | Z.ai | بخشی | فقط کلیدهای درایور زنده |
| `src/arya/models/shareholders.py` | **Grok** | Grok | مدل داخلی |
| `src/arya/providers/shareholder_base.py` | **Grok** | Grok | قرارداد + registry |
| `src/arya/providers/shareholders/mock_provider.py` | **Grok** | Grok | mock فقط |
| `src/arya/analysis/analyzers/share_change_analyzer.py` | **Grok** | Grok | |
| `tests/analysis/test_share_change_analyzer.py` | **Grok** | Grok | |
| `configs/smart_money.yaml` | **Grok** | Grok | آستانه‌ها / flag |
| daily-ingest اسکلت (`operations/`, `configs/daily_ingest.yaml`) | **Grok** | Grok | |
| `docs/sources/PYTSE_CLIENT_MAPPING.md` | **Grok** | Grok | |
| ماتریس / probe TSETMC قیمت (OHLCV, market-watch) | **Grok** | Grok | |
| `TsetmcMarketProvider` / market-watch short keys | **Grok** | Grok | |

## فایل‌های مشترک

| فایل | قاعده |
|------|--------|
| `configs/providers.yaml` | Z.ai فقط بلوک `shareholders:` (درایور زنده)؛ Grok بلوک market و باقی |
| `CHANGE_LEDGER.md` | فقط **append** هنگام merge |
| `AGENTS.md` | هیچ‌کدام بدون تأیید مالک بازنویسی کامل نکند |
| `src/arya/app/bootstrap.py` | **هماهنگی اجباری** قبل از edit؛ ترجیحاً PR جدا با diff کوچک |

## قرارداد لایه

- Z.ai: Provider واقعی → خروجی سازگار با `ShareholderFlowMetrics` (یا توافق صریح روی DTO).
- Grok: Analyzer فقط مدل داخلی را می‌بیند؛ import از pytse/HTTP در Analyzer ممنوع.
- پیش‌فرض YAML تا پذیرش مالک: `shareholders.driver: mock` می‌تواند بماند؛ سوییچ به درایور Z.ai با PR و تست.

## فاز ۰ — پذیرش مشروط شواهد Z.ai در ماتریس قیمت/جریان

طبق اعلام Z.ai (استناد به evidence خودشان؛ Grok فایل خام را در این محیط دوباره واکشی نکرد):

| Endpoint | وضعیت اعلام‌شده Z.ai | اقدام ماتریس Grok |
|----------|----------------------|-------------------|
| GetInstrumentSearch | VERIFIED (فولاد insCode) | هم‌راستا با ONLINE_VERIFIED قبلی Grok |
| GetClosingPriceDailyList | VERIFIED (۵ روز) | هم‌راستا |
| ClientTypeAll (old.tsetmc) | VERIFIED snapshot ~105KB | افزودن ردیف: ONLINE_PARTIAL/VERIFIED پس از مشاهدهٔ INDEX توسط مالک |
| WSDL / SOAP کامل | UNVERIFIED / FAILED از محیط Z.ai | بدون تغییر ادعا |

**توجه:** Grok محتوای باینری evidence را در این نوبت بازبینی بایت‌به‌بایت نکرده؛ اعتبار نهایی با مالک پس از باز کردن `docs/sources/evidence/2026-10-24/INDEX.md` روی برنچ Z.ai است.

## تأیید Grok

این جدول از نظر Grok **نهایی و قابل اجرا** است. Grok روی مسیرهای ستون Z.ai کد نمی‌نویسد مگر با واگذاری صریح مالک.
