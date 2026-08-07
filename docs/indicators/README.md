# راهنمای اندیکاتورها

فهرست کامل اندیکاتورهای پیاده‌سازی‌شده، فرمول محاسبه و نحوه‌ی نرمال‌سازی امتیاز.
منبع حقیقت (source of truth) برای رفتار هر اندیکاتور کد آن در
`src/arya/technical/indicators/<group>/` است؛ این فایل فقط توضیح انسانی‌خوان می‌دهد.

| اندیکاتور | گروه | پارامترها | خروجی |
|---|---|---|---|
| SMA | trend | period | میانگین متحرک ساده |
| EMA | trend | period | میانگین متحرک نمایی |
| RSI | momentum | period, overbought, oversold | شاخص قدرت نسبی |
| MACD | momentum | fast, slow, signal | همگرایی/واگرایی میانگین متحرک |
| Bollinger Bands | volatility | period, std_dev | باندهای نوسان |
| OBV | volume | - | حجم تعادلی |

اندیکاتورهای بیشتر (market_structure, smart_money, statistics) در Milestone 2 اضافه می‌شوند.
