# اتصال اختیاری TradingAgents به ARYA

**وضعیت:** PARTIALLY_IMPLEMENTED — کد و آزمون‌های واحد آفلاین افزوده شده‌اند؛ تأیید CI، اجرای محلی و پذیرش مالک هنوز لازم است.  
**نسخه upstream:** v0.7.1  
**تاریخ بررسی منبع:** 2026-11-13

## هدف و مرز معماری

TradingAgents به‌عنوان یک موتور پژوهش چندایجنتی جداگانه به ARYA متصل شده است. تحلیلگرهای بنیادی، تکنیکال/بازار، اخبار و احساسات آن می‌توانند گزارش تولید کنند؛ گروه پژوهشگر صعودی/نزولی و مدیران ریسک/پرتفوی در همان چارچوب upstream کار می‌کنند.

این اتصال عمداً جایگزین هسته ARYA نیست:
- خروجی TradingAgents فقط یک rating دسته‌ای پنج‌سطحی (Buy، Overweight، Hold، Underweight، Sell) یا REVIEW است.
- این rating به امتیاز عددی ARYA، Decision، RiskAssessment یا Recommendation تبدیل نمی‌شود.
- مدیر ریسک فعلی ARYA مستقل باقی می‌ماند و TradingAgents مجوز سفارش یا معامله ایجاد نمی‌کند.
- اجرای پیش‌فرض ARYA، Provider بورس ایران/TSETMC و سایر مسیرهای موجود بدون نصب این افزونه تغییر نمی‌کنند.
- گزارش، کش و حافظه TradingAgents خارج از مخزن و به‌طور پیش‌فرض زیر ~/.arya/tradingagents/ ذخیره می‌شوند.

## بازارهای قابل استفاده

این bridge فعلاً فقط دو مقدار asset class را قبول می‌کند:

| مقدار | upstream asset type | محدوده |
|---|---|---|
| international_stock | stock | نماد سهام پشتیبانی‌شده توسط زنجیره داده TradingAgents/Yahoo Finance؛ مانند AAPL یا 7203.T |
| crypto | crypto | جفت‌های رمزارزی پشتیبانی‌شده؛ مانند BTC-USD |

**بورس ایران/TSETMC و فارکس از این bridge پشتیبانی نمی‌شوند.** مقدار stock در خود ARYA به بازار ایران اشاره دارد؛ برای جلوگیری از اشتباه، این adapter مقدار international_stock را مطالبه می‌کند. برای بازار ایران باید مسیر رسمی داده و تحلیل ARYA حفظ شود تا زمانی که یک adapter اختصاصی با قرارداد داده و شواهد معتبر توسعه یابد.

TradingAgents از Providerهای خودش استفاده می‌کند؛ در حال حاضر این اجرا داده OHLCV یا بنیادی ARYA را به آن تزریق نمی‌کند. بنابراین خروجی آن نظر پژوهشی دوم است، نه تحلیل هم‌داده یا تأیید مستقل داده‌های ARYA. کیفیت و مجوز استفاده از داده‌های هر Provider باید جداگانه بررسی شود.

## نصب افزونه

این افزونه به Python 3.11 یا بالاتر نیاز دارد. بسته upstream به‌صورت dependency پیش‌فرض ARYA نصب نمی‌شود. از آن‌جا که نسخه upstream به pandas 3 نیاز دارد و ARYA نسخه‌های قدیمی‌تر را نیز می‌پذیرد، برای جلوگیری از ارتقای ناخواسته dependencyهای محیط اصلی ARYA، نصب را در virtualenv جدا انجام دهید.

در PowerShell و از ریشه پروژه:

~~~powershell
py -3.11 -m venv .venv-ta
.\.venv-ta\Scripts\python.exe -m pip install --upgrade pip
.\.venv-ta\Scripts\python.exe -m pip install -e .
.\.venv-ta\Scripts\python.exe -m pip install -r requirements-tradingagents.txt
~~~

فایل requirements، wheel انتشار رسمی TauricResearch/TradingAgents v0.7.1 را pin می‌کند. اطلاعات انتشار رسمی، مجوز Apache-2.0 و digest ثبت‌شده برای wheel:

- مخزن: https://github.com/TauricResearch/TradingAgents
- انتشار: https://github.com/TauricResearch/TradingAgents/releases/tag/v0.7.1
- wheel SHA-256: db5cc7459c44acce3549ba1cc9e4d8c6a32253bb42e17222eeb13042daa4a382
- وابستگی اختیاری: requirements-tradingagents.txt

هیچ کد upstream در ARYA کپی نشده است؛ adapter فقط از API عمومی Python همان نسخه استفاده می‌کند.

## کلید مدل زبانی

کلید API یا اطلاعات ورود را در Git، فایل نمونه، issue یا گفتگو قرار ندهید. کلید provider انتخابی باید فقط در محیط اجرای محلی تنظیم شود. برای نمونه، با OpenAI در PowerShell:

~~~powershell
$env:OPENAI_API_KEY = "YOUR_API_KEY"
$env:TRADINGAGENTS_LLM_PROVIDER = "openai"
~~~

مقدار API key را در مخزن ذخیره نکنید. providerهای دیگر و local endpointها طبق راهنمای رسمی upstream قابل تنظیم هستند. هزینه و محدودیت API متناسب با provider و عمق مناظره اعمال می‌شود.

## اجرا

نمونه سهام خارجی:

~~~powershell
.\.venv-ta\Scripts\python.exe scripts\run_tradingagents_research.py --ticker AAPL --date 2026-11-13 --asset-class international_stock --provider openai --language Persian
~~~

نمونه رمزارز:

~~~powershell
.\.venv-ta\Scripts\python.exe scripts\run_tradingagents_research.py --ticker BTC-USD --date 2026-11-13 --asset-class crypto --provider openai
~~~

برای اجرای --help، نصب بسته upstream الزامی نیست؛ اما اجرای واقعی به نصب افزونه و تنظیم یک provider معتبر نیاز دارد.

خروجی JSON شامل rating، نسخه upstream، وضعیت نیاز به بازبینی و مسیر گزارش است. REVIEW نباید به HOLD تبدیل شود و نیازمند بازبینی انسانی یا اجرای دوباره است.

## پرتفوی

در API پایتون می‌توان یک mapping پرتفوی را به adapter داد. دو حالت زیر معنای متفاوت دارند:
- portfolio=None: اطلاعات پرتفوی در دسترس نیست.
- portfolio={"positions": []}: پرتفوی مشخصاً خالی است.

بدون اطلاعات معتبر پرتفوی، مقدار خالی را به‌جای نامعلوم ارسال نکنید. در runner فعلی، پرتفوی به‌صورت پیش‌فرض ارسال نمی‌شود.

## محدودیت‌ها و ریسک‌ها

1. این اتصال، داده خام ARYA را به TradingAgents تزریق نمی‌کند و کیفیت منبع upstream را تأیید نمی‌کند.
2. rating یک خروجی زبانی/دسته‌ای است، نه احتمال موفقیت، بازده پیش‌بینی‌شده یا اندازه موقعیت کالیبره‌شده.
3. نتایج LLM ممکن است با provider، مدل، داده و زمان اجرا تغییر کنند؛ بک‌تست یا گزارش یک اجرا دلیل سودآوری نیست.
4. اجرای واقعی TradingAgents می‌تواند درخواست داده و LLM ایجاد کند و هزینه/محدودیت provider داشته باشد.
5. حافظه و گزارش‌های upstream در مسیر جداگانه نگهداری می‌شوند؛ این حافظه هنوز با دفتر شواهد یا حافظه تصمیم ARYA ادغام نشده است.
6. forex، بورس ایران/TSETMC، دارایی‌های غیربورسی صندوق‌ها و داده‌های داخلی CODAL در این مرحله پوشش ندارند.
7. هیچ اتصال broker، paper execution یا live order در این bridge اضافه نشده است.

## آزمون

آزمون‌های tests/ai/test_tradingagents_adapter.py با stubهای محلی اجرا می‌شوند و به API، حساب LLM یا اینترنت نیاز ندارند. آن‌ها مسیر نصب‌نبودن dependency، رد کردن بازار نامعتبر، ساخت config ایزوله، rating REVIEW، انتقال پرتفوی و اعتبارسنجی تاریخ را بررسی می‌کنند.

پس از checkout شاخه، از ریشه پروژه و در همان virtualenv جدا اجرا کنید:

~~~powershell
.\.venv-ta\Scripts\python.exe -m pytest tests\ai\test_tradingagents_adapter.py -q
.\.venv-ta\Scripts\python.exe scripts\verify_governance.py
.\.venv-ta\Scripts\python.exe -m compileall -q src tests scripts
.\.venv-ta\Scripts\python.exe -m pytest -q
~~~

آزمون واقعی متصل به provider عمداً در CI/آزمون واحد اجرا نمی‌شود؛ اجرای live فقط با تصمیم و کلیدهای محلی کاربر انجام شود.

## منابع رسمی

- TradingAgents repository and README: https://github.com/TauricResearch/TradingAgents
- Python API entrypoint and propagate() return contract: https://github.com/TauricResearch/TradingAgents/blob/v0.7.1/tradingagents/graph/trading_graph.py
- PortfolioContext: https://github.com/TauricResearch/TradingAgents/blob/v0.7.1/tradingagents/portfolio.py
- Release v0.7.1 (published 2026-10-27): https://github.com/TauricResearch/TradingAgents/releases/tag/v0.7.1
