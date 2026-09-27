# Smart TSETMC History Cache

## هدف

ARYA نباید برای هر تحلیل، تاریخچه ۲۰۰ کندلی را دوباره از TSETMC بگیرد.
Cache-aside و refresh policy جدید بین Provider و Pipeline قرار می‌گیرد.

## Cache key

فرمت canonical:

    ohlcv:{market}:{ticker}:{timeframe}:adjust={0|1}

نمونه:

    ohlcv:stock:فملی:1d:adjust=0

limit عمداً در key نیست. یک cache entry می‌تواند داده بیشتری از درخواست فعلی داشته باشد و در درخواست‌های کوچک‌تر trim شود.

## TTL policy

برای daily stock history:

| وضعیت بازار | Fresh TTL | Stale grace |
|---|---:|---:|
| داخل session | 60 ثانیه | 15 دقیقه |
| خارج session | 6 ساعت | 48 ساعت |

Session از configs/scheduler.yaml و timezone پروژه خوانده می‌شود. تعطیلات رسمی هنوز calendar جداگانه ندارند؛ بنابراین scheduler فقط پنجره زمانی پیکربندی‌شده را می‌شناسد.

## Request flow

    Analyze(symbol)
       |
       v
    History cache lookup
       |
       +-- MISS --------------------+
       |                            |
       +-- FRESH --> serve cached   |
       |                            |
       +-- STALE -------------------+--> refresh provider
       |                              |       |
       |                              |       +-- success -> save + serve fresh
       |                              |
       |                              +-- failure -> serve stale + warning
       |
       +-- EXPIRED -----------------> refresh provider
                                      |
                                      +-- success -> save + serve fresh
                                      |
                                      +-- failure -> fail closed

برای stale data، پاسخ با هشدار همراه است تا داده قدیمی به‌صورت silent مصرف نشود.

## Automatic refresh flow

MarketHistoryRefreshJob.run_once() نقطه ورود Scheduler است.

Scheduler طبق configs/scheduler.yaml برای stock هر 1 دقیقه در session اجرا می‌شود و فقط cache entryهای due را refresh می‌کند. این job فقط entryهای موجود در cache را لمس می‌کند؛ بنابراین watchlist/cache باید تعیین کند چه نمادهایی تحت refresh خودکار باشند.

ترتیب پیشنهادی در نسخه بعد:

1. watchlist symbols در cache ثبت شوند.
2. Scheduler هر 1 دقیقه job را اجرا کند.
3. entryهای fresh بدون network call رد شوند.
4. stale/expired entryها refresh شوند.
5. خطای provider، entry قبلی را برای مدت stale grace حفظ کند.
6. پس از عبور از stale grace، داده قدیمی دیگر برای تحلیل مصرف نشود.

## Failure semantics

- Cache miss + provider failure: MarketDataUnavailable
- Fresh cache + provider failure: provider اصلاً فراخوانی نمی‌شود.
- Stale cache + refresh failure: stale data با warning برگردانده می‌شود.
- Expired cache + refresh failure: درخواست fail می‌شود.
- Successful refresh: last_error پاک می‌شود.

## Tests

tests/storage/test_history_cache.py این موارد را پوشش می‌دهد:

- canonical key و حذف limit از key
- cache hit و جلوگیری از call اضافی به Provider
- TTL طولانی‌تر خارج session
- stale fallback هنگام timeout
- fail-closed برای expired cache
- refresh موفق stale entry
- استفاده مجدد از cache بزرگ‌تر برای limit کوچک‌تر

## پیاده‌سازی

- src/arya/storage/history_cache.py
- src/arya/storage/history_service.py
- src/arya/scheduler/market_refresh.py
- configs/scheduler.yaml

Pipeline اصلی AryaApp.analyze_symbol() اکنون از MarketHistoryService استفاده می‌کند.
