# TSETMC Market Provider

## وضعیت

ARYA AI Trader اکنون یک Provider واقعی برای بورس ایران دارد:

- Driver: `tsetmc`
- Backend: `pytse-client==0.19.1`
- منبع: TSETMC
- قرارداد داخلی: `MarketDataProvider`
- خروجی: `OHLCVSeries`
- تایم‌فریم فعلی: روزانه (`1d`)

## جریان داده

```
AryaApp
   |
   v
Settings.provider_for("stock")
   |
   v
ProviderRegistry.create("tsetmc", market="stock")
   |
   v
TsetmcMarketProvider
   |
   v
pytse_client.Ticker(symbol)
   |
   v
TSETMC
   |
   v
Ticker.history
   |
   v
OHLCVSeries
   |
   +--> SQLite cache
   +--> Indicator Engine
   +--> Analysis / Risk / Recommendation
```

## نکات طراحی

Provider عمداً به `AryaApp` یا Indicator Engine وابسته نیست. بنابراین:

1. Mock برای تست‌های آفلاین باقی می‌ماند.
2. TSETMC فقط با تغییر `configs/providers.yaml` فعال می‌شود.
3. لایه‌های تحلیل به pytse-client وابسته نیستند.
4. در آینده می‌توان Binance/Codal/Providerهای دیگر را بدون تغییر قرارداد اضافه کرد.

## محدودیت فعلی

`pytse-client.Ticker.history` در این Provider به‌صورت مشخص برای داده روزانه استفاده می‌شود. داده intraday/tick باید در Provider جداگانه پیاده‌سازی شود و نباید با قرارداد روزانه مخلوط شود.

## تست اتصال واقعی

پس از نصب dependency:

```powershell
python -c "from pytse_client import Ticker; t=Ticker('فملی'); print(t.title); print(t.last_price); print(t.volume); print(t.last_date)"
```

برای اجرای تست‌های پروژه:

```powershell
pytest tests/providers/test_tsetmc_provider.py -v
pytest tests/ -v
```
