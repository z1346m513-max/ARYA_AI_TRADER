# ادامه پروژه — TSE + کدال (2026-10-06)

## انجام‌شده در این Branch

1. Provider واقعی کدال (از Branch قبلی) نگه داشته شد
2. `CodalEventAnalyzer` — امتیاز رویداد از عنوان اطلاعیه
3. اتصال به `AryaApp.analyze_symbol` — بخش `codal` وارد Scoring می‌شود
4. نگاشت `FOOLAD → فولاد` و چند نماد رایج
5. قفل بازار فقط `stock`
6. خطاهای کدال پایپ‌لاین تکنیکال را متوقف نمی‌کنند

## اجرا

```bash
# از داخل ایران برای داده زنده کدال
arya analyze --ticker FOOLAD --market stock
arya codal --symbol فولاد --limit 5
```

## فاز بعد

- Symbol Master + صنعت
- Cache-First OHLCV
- پارس Excel/HTML صورت‌های مالی کدال → FundamentalMetrics
- اسکن بر اساس صنعت
