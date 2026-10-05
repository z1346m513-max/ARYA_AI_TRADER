# چک‌لیست حذف کریپتو، فارکس و سهام خارجی

پس از Merge این Branch، موارد زیر را در کل پروژه جستجو و حذف/اصلاح کنید.

## جستجوهای پیشنهادی

```text
crypto
forex
BTC
ETH
USDT
Binance
Oanda
EURUSD
GBPUSD
BTCUSDT
choices=["stock", "crypto", "forex"]
```

## فایل‌های اصلاح‌شده در این Branch

- README.md
- configs/app.yaml
- configs/providers.yaml
- configs/scheduler.yaml
- src/arya/cli/main.py
- src/arya/providers/market/mock_provider.py

## قرارداد جدید

- market فقط `stock`
- currency پیش‌فرض `IRR`
- بدون Provider برای Binance/Oanda
