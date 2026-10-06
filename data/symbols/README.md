# Symbol Master — داده نمادهای بورس ایران

## فایل‌ها

| فایل | توضیح |
|------|--------|
| `equities_flat.json` | لیست سهام با `ticker`, `name`, `industry`, `market` |

## نصب داده

فایل کامل (~۱۰۰۰ نماد، ۲۷ صنعت) را از Artifact پروژه کپی کنید:

```bash
mkdir -p data/symbols
# از بسته arya_symbols_archive یا Release:
cp /path/to/equities_flat.json data/symbols/
```

نمونه رکورد:

```json
{"ticker": "فولاد", "name": "فولاد مبارکه اصفهان", "industry": "فلزات اساسی", "market": "stock"}
```

## CLI

```bash
arya list-industries
arya list-symbols --from-master
arya list-symbols --industry "فلزات اساسی"
arya scan --industry "بانک" --limit 5
```

بدون این فایل، `list-symbols` از Provider (TSETMC/Mock) استفاده می‌کند.
