# ممیزی مخازن متن‌باز برای ارتقای ARYA AI Trader

**تاریخ بررسی:** 2026-10-28
**دامنه:** پلتفرم تحلیل بورس ایران؛ سهام، صندوق‌ها و سبدگردان‌ها در چارچوب تحلیل بازار ایران.
**هدف:** یافتن اجزای نرم‌افزاری و الگوهای مجاز برای ارتقای کیفیت داده، تحلیل، مدیریت ریسک، explainability و workflow. این گزارش توصیهٔ خرید/فروش یا تأیید دادهٔ بازار نیست.

## خلاصهٔ اجرایی

ده مخزن در پنج حوزه بررسی شدند. هیچ‌کدام در شواهد بررسی‌شده منبع زندهٔ TSETMC، فهرست کامل و تأییدشدهٔ ابزارهای ایران، یا پلتفرم آمادهٔ تحلیل و توصیهٔ معاملاتی ایران ارائه نمی‌کند. بعضی مخازن از نظر معماری مفیدند، اما افزودن چارچوب‌های بزرگ (Qlib، Dagster، GX، QuantStats، SHAP) بدون نیاز اثبات‌شده هزینه و وابستگی ایجاد می‌کند. تصمیم این تغییر: پیاده‌سازی بومیِ کنترل ساختاری OHLCV و ثبت ردپای داده در SQLite، بدون کپی کد یا افزودن dependency خارجی. الگوهای بررسی‌شده الهام طراحی‌اند و منبع متناظر/نسبت مالکیت برای پیاده‌سازی تازه ادعا نمی‌شود.

## فهرست بررسی‌ها

| مخزن | مجوز مشاهده‌شده | تناسب با ARYA | تصمیم استفاده |
|---|---|---|---|
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | تعارض مهم: مجوز ریشه AGPL-3.0 است، ولی README/بخش platform به Apache-2.0 اشاره می‌کنند؛ metadata نیز NOASSERTION گزارش شده است. | الگوی provider/plugin و clientها مفید؛ هیچ اتصال TSETMC تأیید نشد. | از کد/وابستگی استفاده نشود تا تعارض مجوز برای فایل/نسخهٔ دقیق کتبی روشن شود؛ فقط ایدهٔ عمومی adapter. |
| [FinanceDataReader](https://github.com/FinanceData/FinanceDataReader) | MIT؛ برای کپی باید copyright و permission notice حفظ شود. | reader چندمنبعی و نماد منبع‌دار؛ پوشش معرفی‌شده ایران/TSETMC را اثبات نمی‌کند. | فقط الگوی مرزبندی؛ TSETMC و کد محلی خود ARYA باقی بماند. |
| [Microsoft Qlib](https://github.com/microsoft/qlib) | MIT؛ notice حفظ شود؛ contribution به upstream ممکن است مشمول Microsoft CLA باشد. | طراحی research pipeline، دادهٔ point-in-time، portfolio state و backtest. | برای این تغییر وابستگی اضافه نشد؛ چارچوب بزرگ و تکرار storage/workflow موجود است. |
| [backtesting.py](https://github.com/kernc/backtesting.py) | AGPL-3.0. | حلقهٔ زمانی و متریک‌های معامله نمونهٔ فنی؛ عمدتاً backtest تک‌دارایی و بدون بازار ایران. | کپی یا dependency انجام نشد؛ فقط مفاهیم عمومی، به دلیل copyleft و نیاز به منطق اختصاصی ایران. |
| [QuantStats](https://github.com/ranaroussi/quantstats) | Apache-2.0؛ حفظ license/notice و اعلام تغییرات لازم. | متریک‌های سری بازده، drawdown و مقایسه با benchmark. | در این تغییر dependency نشد؛ ارزیابی جداگانه پس از تعریف قرارداد بازده و تقویم معاملاتی. |
| [vectorbt](https://github.com/polakowo/vectorbt) | Apache-2.0 به‌همراه Commons Clause؛ محدودیت مهم در عرضهٔ تجاری محصول/خدمت مبتنی بر آن. | پژوهش برداری/سیگنال و پرتفوی؛ دادهٔ ایران را ثابت نمی‌کند. | کپی یا dependency انجام نشد؛ Commons Clause با استفادهٔ محصولی نیازمند بررسی حقوقی است. |
| [Dagster](https://github.com/dagster-io/dagster) | Apache-2.0؛ حفظ notice/license و NOTICE در صورت کاربرد. | asset graph، resource، آزمون و scheduling/lineage. | dependency اضافه نشد؛ برای نیازهای فعلی، ثبت محلی SQLite کم‌هزینه‌تر است. |
| [SHAP](https://github.com/shap/shap) | MIT؛ notice حفظ شود. | توضیح attribution برای مدل‌های یادگرفته‌شده؛ جایگزین توضیح امتیاز قاعده‌محور نیست. | فعلاً dependency نشد؛ ابتدا سهم هر جزء امتیاز ARYA را به‌صورت قطعی نمایش می‌دهیم. |
| [Great Expectations](https://github.com/fivetran/great_expectations) | Apache-2.0؛ فایل‌های تغییرکرده و NOTICE/attribution را رعایت کنید. | قراردادهای assertion و validation batch. | به‌جای چارچوب کامل، checks محدود و بومی برای OHLCV پیاده شد. |
| [OpenLineage](https://github.com/OpenLineage/OpenLineage) | Apache-2.0؛ DCO به معنی واگذاری کامل copyright نیست. | شناسهٔ run/job/dataset، schema version و facets برای lineage. | الگوی ثبت رویداد در جدول بومی SQLite استفاده شد؛ client/collector اضافه نشد. |

اطلاعات stars و فعالیت مخازن نوسانی‌اند و برای تصمیم معماری به‌تنهایی معیار نیستند؛ شواهد snapshot، شاخه/commit و license مستقیم در لینک‌های مخزن/فایل مرجع بالا قابل بازبینی است. ارزیابی به معنی ممیزی حقوقی کامل، ممیزی امنیتی، ضمانت نگهداری آتی یا تأیید صحت مالی کتابخانه‌ها نیست.

## تصمیم لایسنس و مالکیت

1. هیچ منبع خارجی در این تغییر کپی، vendored، نصب یا به‌عنوان dependency اضافه نشده است؛ فایل‌های پیاده‌شده در ARYA کد تازه و متناسب با قراردادهای موجود پروژه هستند.
2. MIT و Apache-2.0 مجوزهای permissive هستند، اما اجازهٔ استفاده به معنی انتقال copyright upstream به ARYA نیست. هر کپی آینده باید license، copyright/NOTICE و الزامات تغییر فایل را رعایت کند و در third-party notices ثبت شود.
3. AGPL-3.0، Commons Clause و license نامعلوم/متناقض برای dependency یا کپی نیازمند مجوز مستقل و بازبینی حقوقی/مالک است؛ صرف ارزش فنی مجوز را رفع نمی‌کند.
4. سیاست مالکیت فکری داخلی ARYA و حقوقی که مجوزهای شخص ثالث اعطا می‌کنند دو موضوع جدا هستند. این تغییر هیچ‌یک را بازتعریف نمی‌کند و قانون اساسی/سیاست مالکیت مخزن را تغییر نمی‌دهد.
5. قبل از پذیرش/ارسال کد اختصاصی ARYA به مخازن دیگر، CLA/DCO و حق grant را بررسی کنید؛ مشارکت upstream ممکن است با سیاست حفظ حقوق مالک پروژه ناسازگار باشد.

## تغییر بومی انجام‌شده در این PR

- اعتبارسنجی ساختاری OHLCV پیش از analyzers، filter و strategy: سری خالی، timestamp نامعتبر/تکراری/نامرتب یا ناسازگار از نظر timezone، قیمت غیرمتناهی/غیرمثبت، حجم منفی، و OHLC نامنطبق رد می‌شوند.
- هر batch اعتبارسنجی‌شده یا مردودشده در SQLite به‌صورت `data_quality_runs` ثبت می‌شود: run ID، نماد/بازار/timeframe، نام provider، زمان دریافت محلی UTC، تعداد ردیف‌ها، اولین/آخرین زمان داده، SHA-256 محتوای نرمال‌شده، نتیجه و فهرست issueها.
- توصیهٔ نهایی `data_quality_run_id` دارد تا بتوان آن را به ورودی اعتبارسنجی‌شده پیوند داد.
- هیچ دادهٔ خام TSETMC، زمان اصلی quote، تقویم تعطیلات، کامل‌بودن کندل‌ها یا تازگی معاملاتی در این تغییر تصدیق نمی‌شود. `retrieved_at_utc` زمان دریافت برنامه است، نه timestamp ارائه‌دهنده. تقویم ایران و سیاست stale-data باید در تغییر مستقلی با منبع/قرارداد قابل‌اثبات تکمیل شود.
- در خطای ساختاری، نتیجهٔ اعتبارسنجی ثبت می‌شود و داده به تحلیل نمی‌رسد. آزمون‌ها آفلاین/قطعی‌اند و به شبکه وابسته نیستند.

## دامنهٔ باقی‌مانده / موارد نیازمند تصمیم

- freshness بر اساس session calendar تهران، توقف نماد، تعطیلات و timestamp رسمی منبع نیازمند قرارداد معتبر و تصمیم مالک است؛ timestamp آخرین کندل به‌تنهایی برای تعیین stale کافی نیست.
- point-in-time fundamentals، survivorship-bias guard، corporate actions، fees/slippage و مدل backtest هنوز به این PR اضافه نشده‌اند.
- سرویس واقعی داده و حق استفاده/بازنشر آن جداگانه نیاز به اثبات دارد؛ این ممیزی GitHub آن را حل نمی‌کند.
- افزودن dependency یا برداشتن کد خارجی در PRهای بعدی باید انتخاب مشخص، نسخه/commit، license دقیق هر فایل/وابستگی، آزمایش هم‌ارزی و تأیید governance داشته باشد.

## منابع اصلی

- OpenBB: [LICENSE](https://github.com/OpenBB-finance/OpenBB/blob/develop/LICENSE)، [project](https://github.com/OpenBB-finance/OpenBB).
- FinanceDataReader: [MIT LICENSE](https://github.com/FinanceData/FinanceDataReader/blob/master/LICENSE.txt), [README](https://github.com/FinanceData/FinanceDataReader/blob/master/README.md).
- Qlib: [MIT LICENSE](https://raw.githubusercontent.com/microsoft/qlib/main/LICENSE), [releases](https://github.com/microsoft/qlib/releases).
- backtesting.py: [GitHub API license metadata](https://api.github.com/repos/kernc/backtesting.py), [package metadata](https://raw.githubusercontent.com/kernc/backtesting.py/master/setup.py).
- QuantStats: [Apache-2.0 LICENSE](https://github.com/ranaroussi/quantstats/blob/main/LICENSE.txt), [README](https://github.com/ranaroussi/quantstats).
- vectorbt: [LICENSE including Commons Clause](https://github.com/polakowo/vectorbt/blob/master/LICENSE.md).
- Dagster: [LICENSE](https://github.com/dagster-io/dagster/blob/master/LICENSE).
- SHAP: [MIT LICENSE](https://raw.githubusercontent.com/shap/shap/main/LICENSE).
- Great Expectations: [LICENSE](https://github.com/fivetran/great_expectations/blob/develop/LICENSE), [contribution terms](https://github.com/fivetran/great_expectations/blob/develop/CLA.md).
- OpenLineage: [LICENSE](https://raw.githubusercontent.com/OpenLineage/OpenLineage/main/LICENSE), [contribution/DCO guide](https://raw.githubusercontent.com/OpenLineage/OpenLineage/main/CONTRIBUTING.md).
