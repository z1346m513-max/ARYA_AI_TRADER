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
