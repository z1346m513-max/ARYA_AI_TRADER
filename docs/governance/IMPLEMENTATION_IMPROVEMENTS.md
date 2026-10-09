# بهبودهای اجرای پروژه — مبنای Milestone بعدی

این سند از بررسی baseline فعلی استخراج شده و بین «واقعیت موجود»، «ریسک» و «پیشنهاد» تفکیک می‌کند.

## 1. Data Provenance و Freshness
واقعیت: TSETMC فعلاً Provider روزانه دارد و در roadmap، freshness و market-hours هنوز کار بعدی هستند.
بهبود لازم: هر داده باید source_id، retrieved_at، source_timestamp، freshness_state، provider_version و validation_status داشته باشد.
معیار پذیرش: داده stale نباید بدون هشدار وارد Recommendation شود.

## 2. Codal
واقعیت: configs/providers.yaml، Codal را mock و disabled تعریف می‌کند.
بهبود لازم: قبل از implementation باید قرارداد منبع، روش دسترسی، rate limit، نوع سند، نسخه/تاریخ و تست fixture تأیید شود. هیچ endpoint حدسی نباید وارد production شود.
معیار پذیرش: adapter فقط پس از evidence ثبت‌شده و contract tests فعال شود.

## 3. Indicator / Strategy Parameters
واقعیت: indicators.yaml پارامتر، وزن و timeframe را قابل تنظیم کرده است.
بهبود لازم: schema validation، versioning تنظیمات، ثبت profile فعال و ذخیره پارامترها در نتایج تحلیل اضافه شود تا نتیجه قابل بازتولید باشد.
معیار پذیرش: هر Recommendation باید config/profile version داشته باشد.

## 4. Multi-timeframe
واقعیت: معماری plugin برای indicator وجود دارد و timeframe در config دیده می‌شود، اما پشتیبانی عملیاتی چندبازه‌ای هنوز کامل نشده است.
بهبود لازم: قرارداد timeframe، alignment، timezone و جلوگیری از look-ahead باید به‌صورت مستقل تست شود.

## 5. Backtest و Optimization
واقعیت: backtest و optimization در roadmap هستند.
بهبود لازم: قبل از هر بهینه‌سازی، split زمانی train/validation/test، هزینه معامله، slippage، کارمزد و جلوگیری از leakage اجباری شود.
معیار پذیرش: هیچ پارامتر بهینه‌شده‌ای بدون گزارش reproducible و out-of-sample وارد production نشود.

## 6. Provider Reliability
بهبود لازم: health state، retry budget، circuit breaker، cache freshness و last-known-good باید در contract Providerها استاندارد شوند.

## 7. AI Decision Engine
واقعیت: موتور فعلی Rule-Based و Explainable است.
بهبود لازم: هر مدل ML/LLM آینده باید evidence bundle، model/version، prompt/config version، input snapshot و confidence/limitations ثبت کند. خروجی AI بدون evidence نباید حقیقت تلقی شود.

## 8. اجرای تیمی
بهبود اعمال‌شده در این PR: AGENTS.md، Constitution، Change Record، Ledger، CODEOWNERS، PR template و Governance CI.
بهبود بعدی: فعال‌سازی واقعی branch protection/ruleset روی main و الزام Governance Gate قبل از merge.

## 9. ترتیب پیشنهادی اجرای فنی
1. Provenance/Freshness contracts
2. Symbol/market master و کیفیت داده
3. Codal با منبع و contract test معتبر
4. multi-timeframe و parameter versioning
5. backtest با leakage controls
6. ML/LLM decision layer
7. GUI و packaging

این ترتیب به معنی رتبه‌بندی تجاری نیست؛ یک ترتیب وابستگی فنی برای کاهش ریسک اجرای پروژه است.