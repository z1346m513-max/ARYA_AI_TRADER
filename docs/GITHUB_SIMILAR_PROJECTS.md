# پروژه‌های مشابه GitHub — الگوبرداری برای ARYA

بررسی کتابخانه‌های عمومی بورس ایران (بدون کپی کد GPL؛ فقط الگو و endpoint).

## پروژه‌های مرجع

| پروژه | Stars | الگوی مفید برای ARYA |
|--------|------:|----------------------|
| [Glyphack/pytse-client](https://github.com/Glyphack/pytse-client) | ~316 | `Ticker` facade، سهامداران، حقیقی/حقوقی، شناوری، EPS/PE، صفحه `ParTree=151311` |
| [mahs4d/tsetmc-api](https://github.com/mahs4d/tsetmc-api) | ~65 | تفکیک ماژول: Symbol / MarketWatch / DayDetails / Group |
| [5j9/tsetmc](https://github.com/5j9/tsetmc) | ~35 | async CDN، `major_holders_activity` از `ParTree=15131I`، ClientType |
| [yghaderi/oxtapus](https://github.com/yghaderi/oxtapus) | ~28 | قرارداد Provider تایپ‌شده، HTTP مقاوم، Polars |
| [mohsenebrahimyir/codal-tsetmc](https://github.com/mohsenebrahimyir/codal-tsetmc) | ~15 | جست‌وجوی کدال + ذخیره برای بنیادی |
| [amirziveh/codal-skill](https://github.com/amirziveh/codal-skill) | — | مرجع API `search.codal.ir` (Accept JSON، rate-limit) |
| [solitraderbusiness/tsetmc-mcp](https://github.com/solitraderbusiness/tsetmc-mcp) | — | ابزارهای صف، money-flow، فیلتر زبان طبیعی؛ **اجبار IP ایران** |

## الگوهایی که ARYA باید حفظ کند

1. **InsCode محور** — همه endpointهای CDN با `InsCode`؛ جست‌وجوی نماد جداست.
2. **صفحه نماد** — `old.tsetmc.com/Loader.aspx?ParTree=151311&i={InsCode}` منبع UI جزئیات (EPS، گروه، وضعیت).
3. **سهامداران** — `ShareHolderChanges` + `GetInstrumentShareHolderLast` (پیاده‌شده).
4. **حقیقی/حقوقی** — `ClientType` برای smart_money (در این Commit اضافه می‌شود).
5. **کدال رویدادمحور** — افزایش سرمایه / تغییرات مدیران قبل از پارس Excel.
6. **Cache-First + rate-limit** — همه peerها روی محدودیت CDN/کدال تأکید دارند.
7. **جداسازی Provider از Analyzer** — مثل oxtapus/tsetmc-api؛ ARYA همین را دارد.

## چیزهایی که عمداً کپی نمی‌کنیم

- وابستگی سنگین به Selenium برای کل بازار
- دانلود «all symbols history» بدون کنترل حجم
- ادغام فارکس/کریپتو (دامنه ARYA فقط TSE + کدال)

## نقشه اعمال در ARYA

| الگو | وضعیت |
|------|--------|
| TSETMC OHLCV | ✅ tsetmc_provider |
| Codal search | ✅ codal_provider |
| ShareHolderChanges | ✅ shareholder_provider |
| ClientType حقیقی/حقوقی | ✅ این Commit |
| رویداد افزایش سرمایه / مدیران | ✅ این Commit |
| صف ۵ سطحی BestLimits | ⏳ فاز بعد |
| تعدیل قیمت/افزایش تعداد سهام | ⏳ فاز بعد |
