# شواهد فاز ۰ — ۱۴۰۵/۰۸/۰۱ (2026-10-24)

> این پوشه بخشی از گیت شواهد «CR-20261024-001 / CR-20261024-002» است.
> قاعدهٔ ثبت: هر فایل یا «دادهٔ واقعی خام» است یا «ثبت شکست واقعی». هیچ پاسخی شبیه‌سازی نشده است.
> مالک این پوشه (طبق جدول مالکیت فایل): **Z.ai** — برای استناد همکاران آزاد است.

## روش واکشی

- **دسترسی مستقیم** از محیط ساخت به همهٔ هاست‌های TSETMC (`cdn.`, `old.`, `service.`, `api.tsetmc.com`) مسدود است — همهٔ پروب‌های مستقیم timeout شدند (فایل‌های `0*`).
- واکشی موفق فقط از طریق **پروکسی WebFetch** ممکن شد. پسوند `PROXY_` در نام فایل یعنی «از مسیر پروکسی، بدون تغییر دستی».

## فهرست شواهد

| فایل | منبع | نتیجه | توضیح |
|---|---|---|---|
| `01..09_*.meta.json` / `*.raw.*` | دسترسی مستقیم (urllib) | FAILED | ۹ پروب مستقیم: timeout. سندِ محدودیت شبکهٔ محیط ساخت. |
| `10_PROXY_cdn_GetClosingPriceDailyList_foolad.raw.json` | `cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/46348559193224090/5` | **VERIFIED** | پاسخ کامل واقعی. ۵ روز معاملهٔ اخیر فولاد؛ آخرین `dEven=20261021` (کلوز ۴۲۲۰، حجم ۴٫۸۶ میلیارد سهم). |
| `11_PROXY_cdn_GetInstrumentSearch_foolad.raw.json` | `cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/فولاد` | **VERIFIED** | پاسخ کامل واقعی. `insCode` فولاد = `46348559193224090`؛ فیلدهای `insCode2/3/4`، `flow`، `cgrValCot` و ... زنده تأیید شد. |
| `12_PROXY_old_ClientTypeAll_sample.raw.txt` | `old.tsetmc.com/tsev2/data/ClientTypeAll.aspx?t=46348559193224090` | **VERIFIED (reachable) + UNVERIFIED (معناشناسی فیلدها)** | snapshot کل بازار حقیقی/حقوقی؛ ~۱۰۵ هزار کاراکتر؛ ردیف‌ها با insCode قدیمی کلید خورده‌اند. ردیف فولاد (`53809308236531169 = insCode3 فولاد`) در خروجی کامل حاضر بود و در نمونه ثبت شده است. **دو خط جدید (break line) در فایل نمونه فقط برای خوانایی افزوده شده و جزء payload اصلی نیستند — دادهٔ اصلی یک خط با جداکنندهٔ `;` است.** |
| `13_PROXY_old_ClientTypeAll_oldcode_rows.raw.txt` + `.meta.json` | `old.tsetmc.com/tsev2/data/ClientTypeAll.aspx?t=53809308236531169` (کد قدیمی) | **VERIFIED** | پاسخ دقیقاً هم‌اندازهٔ واکشی قبلی (۱۰۵٬۲۲۴ کاراکتر) ⇒ پارامتر `t` نادیده گرفته می‌شود؛ endpoint = snapshot بازارکامل آخرین روز. **تأیید ساختاری قالب ۹ فیلدی:** `insCode, iBuyCount, lBuyCount, iBuyVol, lBuyVol, iSellCount, lSellCount, iSellVol, lSellVol` — در همهٔ ردیف‌ها مجموع خرید = مجموع فروش. تاریخ snapshot در پاسخ نیست و با ۵ روز بستهٔ فولاد تطبیق ندارد ⇒ انتساب تاریخ UNVERIFIED. |
| `14_PROXY_old_ClientType_single.meta.json` | `old.tsetmc.com/tsev2/data/ClientType.aspx?t=53809308236531169` | FAILED | endpoint تک‌نمادی از پروکسی خوانده نشد (بدنهٔ خالی/خطای تبدیل). مسیر عملیاتی M2: ClientTypeAll بازارکامل + فیلتر insCode قدیمی. |
| `15_PROXY_cdn_GetClientType_oldcode.meta.json` | `cdn.tsetmc.com/api/ClientType/GetClientType/53809308236531169/20261021` (کد قدیمی + تاریخ واقعی) | FAILED | تلاش دوم طبق پیشنهاد بند ۲ همین سند: پروکسی پاسخ را تبدیل نکرد (Html Convert Error). با دو شکست واقعی، این endpoint از مسیر پروکسی قابل احراز نیست؛ مسیر M2: ClientTypeAll. |
| `16_PROXY_service_WSDL_retry.meta.json` | `service.tsetmc.com/webservice/TsePublicV2.asmx?WSDL` و `?singleWsdl` و `?op=ShareChange` / `?op=ClientType` | FAILED (schema) / VERIFIED (فهرست ۴۶ عملیات، بار سوم) | هر دو صفت WSDL فقط صفحهٔ HTML فهرست عملیات را می‌دهند؛ صفحات ?op= هم قالب SOAP template را نشان نمی‌دهند (ShareChange = شناسهٔ 39). WSDL کامل همچنان UNVERIFIED — نیازمند egress مستقیم یا My Browser. |
| `17_PROXY_api_tsetmc_docs_verified.meta.json` | `api.tsetmc.com/docs` | **VERIFIED (reachable)** + UNVERIFIED (مسیرهای دقیق) | ارتقای فایل 02 (پروب مستقیمش FAILED بود): مستندات REST رسمی خوانده شد — دستهٔ «نوع خریداران» (id 37) موجود؛ **نیاز صریح به نام کاربری/رمز از شرکت مدیریت فناوری بورس تهران** تأیید شد؛ همهٔ خروجی‌ها JSON. تا زمان credential رسمی، مسیر بدون-auth کاربردی همان ClientTypeAll است. |

## معناشناسی فیلدهای ClientTypeAll (ساختاری تأیید شد — به‌روزرسانی فایل 13)

الگوی هر ردیف: `insCode, iBuyCount, lBuyCount, iBuyVol, lBuyVol, iSellCount, lSellCount, iSellVol, lSellVol`

- نمونهٔ کنترل ۱ (سهم خرد، تطابق کامل خرید/فروش): `971068957336171` → خرید ۱۰۰+۴۴٬۴۵۶ = فروش ۴۴٬۴۵۶+۱۰۰ = ۴۴٬۵۵۶
- نمونهٔ کنترل ۲ (فولاد): `53809308236531169` → خرید ۲٬۵۱۱٬۶۴۰+۱٬۱۹۸٬۳۸۰ = فروش ۳٬۱۱۰٬۰۲۰+۶۰۰٬۰۰۰ = ۳٬۷۱۰٬۰۲۰
- ✅ ساختار ۹ فیلدی و اتحاد مجموع خرید = مجموع فروش در همهٔ ردیف‌های مشاهده‌شده برقرار است.
- ⚠️ دو مورد همچنان UNVERIFIED است: (۱) تاریخ دقیق snapshot (با هیچ‌کدام از ۵ روز بستهٔ واقعی فولاد تطبیق ندارد) و (۲) تطبیق مقادیر با صفحهٔ حقیقی/حقوقی سایت برای یک روز مشخص. درایور (CR-20261024-002) مشتق‌سازی را فقط پس از تطبیق حجم snapshot با یکی از روزهای بستهٔ واقعی مجاز می‌داند؛ در غیر این صورت رد صریح می‌کند.

## هنوز UNVERIFIED (به‌روزرسانی پس از پروب‌های فایل‌های 15–17)

1. WSDL کامل `TsePublicV2.asmx` — سه تلاش پروکسی (`?WSDL`، `?singleWsdl`، `?op=`) همه فقط فهرست ۴۶ عملیات می‌دهند (فایل 16). نیازمند egress مستقیم یا My Browser.
2. امضای `GetClientType/{insCode}/{date}` روی cdn — **دو شکست واقعی** ثبت شد: insCode جدید (20261021/22) و کد قدیمی + تاریخ معتبر 20261021 (فایل 15). از مسیر پروکسی بسته است؛ مسیر عملیاتی M2: ClientTypeAll.
3. مسیرهای دقیق REST رسمی — صفحهٔ `api.tsetmc.com/docs` خوانده شد (فایل 17) و نیاز به credential رسمی از شرکت مدیریت فناوری بورس تأیید شد؛ ولی مسیرهای دقیق endpointها از پروکسی استخراج نمی‌شود (فقط TOC).
4. معناشناسی دقیق فیلدهای ClientTypeAll (بند بالا).
5. نرخ محدودسازی (rate limit) — با هیچ پروبی احراز نشده؛ درایور خودش retry/timeout دارد و رفتار محتاطانه نگه داشته شده است.

## پیام به همکاران (ماتریس pytse / daily-ingest)

- سه endpoint تأییدشدهٔ بالا را می‌توانید بدون واکشی مجدد در ماتریس استفاده کنید؛ استناد: همین پوشه + تاریخ.
- مسیر دادهٔ واقعیِ سهامدارانِ کم‌ریسک برای M2: `old.tsetmc.com/tsev2/data/ClientTypeAll.aspx` (snapshot روز) → تجمیع روزانه در storage؛ مسیر cdn برای تاریخچهٔ تک‌نمادی پس از رفع UNVERIFIED بند ۲.
