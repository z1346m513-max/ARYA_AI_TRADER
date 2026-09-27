# Persian RTL Desktop GUI

## هدف

رابط گرافیکی ARYA از ابتدا با پشتیبانی فارسی و راست‌به‌چپ طراحی شده است. هسته تحلیل، Providerها، cache و مدل‌های داخلی مستقل از زبان رابط باقی می‌مانند.

## اجرا

پس از نصب وابستگی GUI:

    uv pip install --python .venv\Scripts\python.exe -e ".[gui]"

اجرای GUI:

    python -m arya.ui

یا:

    arya gui

ورودی مستقیم script مستقل:

    arya-gui

## رفتار زبان

زبان از configs/app.yaml خوانده می‌شود:

    app:
      language: "fa"

برای فارسی:

- QApplication در حالت Right-to-Left قرار می‌گیرد.
- QLocale روی فارسی ایران تنظیم می‌شود.
- QLineEdit ورودی نماد RTL و راست‌چین دارد.
- حروف رایج صفحه‌کلید عربی به فارسی نرمال می‌شوند.
- فاصله‌های اضافی و Zero Width characters در ticker پاک می‌شوند.
- مقادیر داخلی مثل buy/hold/sell و technical به‌صورت presentation-level ترجمه می‌شوند.

## جریان تحلیل

    GUI input
       |
       v
    normalize_ticker()
       |
       v
    AnalysisWorker
       |
       v
    AryaApp
       |
       v
    Smart History Cache
       |
       +--> TSETMC refresh when due
       |
       v
    Indicators / Analysis / Risk / Recommendation
       |
       v
    Persian GUI

تحلیل در QThread اجرا می‌شود تا دریافت داده از TSETMC رابط کاربری را متوقف نکند. اتصال‌های SQLite نیز در همان worker thread ساخته و بسته می‌شوند.

## تست

تست‌های GUI بدون dependency اجباری به PySide6، بخش normalization را اجرا می‌کنند. تست smoke رابط، در صورت نصب نبودن PySide6، skip می‌شود.

    python -m pytest tests/ui/ -v

برای کل پروژه:

    python -m pytest -v

## تنظیمات پیشرفته تحلیل

تنظیمات تحلیل بخشی از هسته ARYA هستند و فقط مخصوص GUI نیستند.

پروفایل‌های آماده در configs/analysis.yaml:
- balanced
- conservative
- momentum
- trend_following

هر تحلیل می‌تواند profile مخصوص خود را بگیرد و سپس overrideهای لحظه‌ای روی آن اعمال کند.

موارد قابل تنظیم:
- فعال/غیرفعال کردن SMA، EMA، RSI، MACD، Bollinger و OBV
- دوره SMA و EMA
- دوره و حدود RSI
- Fast/Slow/Signal در MACD
- دوره و انحراف معیار Bollinger
- وزن هر اندیکاتور
- تعداد کندل تاریخچه
- آستانه خرید و فروش
- پنجره محاسبه نوسان ریسک و آستانه‌های نوسان

تنظیمات لحظه‌ای به صورت copy از Settings اعمال می‌شوند و فایل‌های پایه را تغییر نمی‌دهند.

مثال CLI:

    arya analyze --ticker "فملی" --market stock --timeframe 1d --profile momentum

پروفایل برای تحلیل قابل تعویض است و از همان TSETMC/Cache/Indicator/Decision/Risk pipeline استفاده می‌کند.
