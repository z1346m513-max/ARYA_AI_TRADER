# سهامداران عمده و تغییرات مالکیت — TSETMC

## صفحات UI

| URL | نقش |
|-----|-----|
| https://main.tsetmc.com/ShareHolderChanges | UI جدید — تغییرات سهامداران |
| https://old.tsetmc.com/Loader.aspx?ParTree=15131I&t=0 | UI قدیم — فعالیت سهامداران عمده |

## API (cdn.tsetmc.com)

```
GET /api/Shareholder/GetShareHolderChanges/false   # همه تغییرات اخیر
GET /api/Shareholder/GetShareHolderChanges/true    # فقط افزایش
GET /api/Shareholder/GetInstrumentShareHolderLast/{InsCode}
GET /api/Shareholder/GetShareHolderHistory/{InsCode}/{ShareHolderId}/{Days}
GET /api/Instrument/GetInstrumentSearch/{Ticker}   # تبدیل نماد → InsCode
```

صفحه قدیم `ParTree=15131I` HTML است و برای scrape به parser جدا نیاز دارد؛ مسیر اصلی ARYA همان API CDN است.

## CLI

```bash
arya shareholders --changes --limit 30
arya shareholders --changes --only-increase
arya shareholders --ticker فولاد
arya shareholders --ticker FOOLAD --limit 15
```

## کاربرد تحلیلی در ARYA

- افزایش مالکیت حقوقی بزرگ → سیگنال احتمالی smart_money
- خروج سهامدار عمده → هشدار ریسک
- ترکیب با کدال (افزایش سرمایه / مجمع) برای تأیید رویداد

فاز بعد: `ShareholderEventAnalyzer` مشابه `CodalEventAnalyzer` و وزن در `weights.yaml` بخش `smart_money`.
