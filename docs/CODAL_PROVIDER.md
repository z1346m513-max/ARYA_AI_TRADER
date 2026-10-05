# Provider واقعی کدال

## منبع

- Base: `https://search.codal.ir/api/search`
- جست‌وجو: `GET /v2/q?Symbol=...&PageNumber=1`
- Header الزامی: `Accept: application/json`

## محدودیت‌ها

1. **Geo-restriction:** معمولاً فقط از داخل ایران در دسترس است.
2. **Rate limit:** پس از تعداد محدود درخواست، HTTP 429 ممکن است ساعت‌ها طول بکشد.
3. **نماد:** کدال اغلب با نماد فارسی کار می‌کند (مثلاً `فولاد` نه `FOOLAD`).
4. این فاز فقط **فهرست اطلاعیه‌ها** است؛ استخراج اعداد صورت‌های مالی از Excel/HTML فاز بعد است.

## کانفیگ

`configs/providers.yaml` → `codal.enabled: true`

## CLI

```bash
arya codal --symbol فولاد --limit 5
```
