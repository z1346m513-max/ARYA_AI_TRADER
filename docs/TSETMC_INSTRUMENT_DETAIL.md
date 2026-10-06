# صفحه جزئیات نماد (ParTree=151311)

## UI

```
https://old.tsetmc.com/Loader.aspx?ParTree=151311&i={InsCode}
https://main.tsetmc.com/InstInfo/{InsCode}
```

مثال:
```
https://old.tsetmc.com/Loader.aspx?ParTree=151311&i=60369091709615715
```

## API CDN

| داده | Endpoint |
|------|----------|
| جست‌وجو | `/api/Instrument/GetInstrumentSearch/{Query}` |
| اطلاعات نماد | `/api/Instrument/GetInstrumentInfo/{InsCode}` |
| قیمت امروز | `/api/ClosingPrice/GetClosingPriceInfo/{InsCode}` |
| صف | `/api/BestLimits/{InsCode}` |

## CLI

```bash
arya instrument --ticker فولاد
arya instrument --ticker FOOLAD --no-orderbook
```

خروجی: وضعیت، بازار/تابلو، صنعت، قیمت، EPS/PE، شناوری، حجم مبنا، آستانه‌ها، صف، لینک صفحه.
