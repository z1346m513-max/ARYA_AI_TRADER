# Runbook: جمع‌آوری روزانه منابع رصد

**وضعیت:** اسکلت (Stage A) — منابع هنوز `NOT_TESTED`

## دستور CLI

```bash
arya ingest-daily --list
arya ingest-daily --dry-run
arya ingest-daily
arya ingest-daily --sources shareholder_changes,sectors_summary
```

## cron پیشنهادی (سرور ایران)

```cron
30 16 * * 0-4  cd /opt/ARYA_AI_TRADER && .venv/bin/arya ingest-daily >> data/logs/ingest-daily.log 2>&1
```

## اصل‌ها
- داده خام در Git commit نمی‌شود
- تا ONLINE_VERIFIED/آزمون IP ایران، enabled=false
- ترجیح JSON پایدار بر HTML

جزئیات: `configs/daily_ingest.yaml`
