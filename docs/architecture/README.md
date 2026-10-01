# معماری ARYA AI Trader

## ۱. جریان داده (Pipeline)

```
┌───────────┐   ┌─────────┐   ┌──────────────────┐   ┌────────────────┐
│ Providers │──▶│ Storage │──▶│ Indicator Engine  │──▶│ Analysis Engine │
└───────────┘   └─────────┘   └──────────────────┘   └────────────────┘
                                                              │
                                                              ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Dashboard    │◀──│ Recommendation │◀──│ Risk Manager  │◀──│ Scoring/AI    │
│                │   │    Engine      │   │               │   │ Decision Engine│
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
```

هر جعبه یک ماژول مستقل با یک قرارداد ورودی/خروجی ثابت است؛ ماژول‌های بعدی به
جزئیات پیاده‌سازی ماژول‌های قبلی وابسته نیستند، فقط به مدل داده‌ی خروجی آن‌ها
(`arya/models/*`) وابسته‌اند. این یعنی هر لایه را می‌توان جدا از بقیه توسعه،
تست یا جایگزین کرد.

## ۲. مسئولیت هر لایه

### Providers (`src/arya/providers/`)
دریافت داده‌ی خام OHLCV یا اخبار/بنیادی از منابع خارجی. هر Provider کلاس
`MarketDataProvider` (`providers/base.py`) را پیاده‌سازی و با
`@ProviderRegistry.register("driver_name")` خودش را معرفی می‌کند.
درایور فعال هر بازار در `configs/providers.yaml` تعیین می‌شود.
`MockMarketProvider` برای تست آفلاین باقی مانده و `TsetmcMarketProvider` برای
دادهٔ روزانهٔ بورس ایران در فاز اول فعال است. اتصال‌های واقعی بعدی (Binance،
Codal و خبرگزاری‌ها) باید همین قرارداد را رعایت کنند و بدون تغییر لایه‌های
بالادست اضافه شوند. Provider TSETMC دارای timeout/retry، User-Agent و تشخیص
پاسخ نامعتبر است؛ دادهٔ دریافت‌شده باید در لایهٔ Storage ثبت شود.

### Storage (`src/arya/storage/`)
کش کردن داده‌ی دریافتی (فعلاً SQLite سبک) تا فراخوانی مکرر Provider لازم نباشد.
`OHLCVStore.save()` / `.load()`.

### Indicator Engine (`src/arya/technical/`)
اجرای تمام اندیکاتورهای فعال (طبق `configs/indicators.yaml`) روی دیتافریم OHLCV.
هر اندیکاتور کلاس `Indicator` (`indicators/base.py`) را پیاده‌سازی و با
`@IndicatorRegistry.register("name")` ثبت می‌شود. **این معماری Plugin است** —
افزودن اندیکاتور جدید فقط یک فایل جدید + یک خط کانفیگ نیاز دارد، بدون تغییر
در `IndicatorEngine`.

خروجی هر اندیکاتور یک `IndicatorResult` با:
- `value`: مقادیر خام (مثلا rsi=65.2)
- `score`: امتیاز نرمال‌شده در بازه `[-1, 1]`
- `triggered_alerts`: لیست هشدارهای فعال‌شده

### Analysis Engine (`src/arya/analysis/analyzers/`)
ترکیب `IndicatorResult`ها در یک بخش (مثلا «تکنیکال») به یک `SectionScore`.
هر بخش تحلیلی (تکنیکال، بنیادی، اخبار، کدال، اسمارت‌مانی، جریان نقدینگی، ریسک)
یک Analyzer مجزا خواهد داشت که همگی خروجی یکسان (`SectionScore`) تولید می‌کنند.
در Milestone 1 فقط `TechnicalAnalyzer` پیاده‌سازی شده است.

### Scoring Engine (`src/arya/analysis/scoring/`)
ترکیب تمام `SectionScore`ها بر اساس وزن‌های `configs/weights.yaml` (یا پروفایل
فعال: کم‌ریسک/متعادل/پرریسک) به یک امتیاز کلی و سطح اطمینان کلی.
بخش‌های هنوز پیاده‌سازی‌نشده به‌طور خودکار از محاسبه کنار گذاشته می‌شوند
(بدون خراب‌کردن نرمال‌سازی وزن‌ها).

### AI Decision Engine (`src/arya/ai/reasoning/`)
نسخه‌ی فعلی Rule-Based و کاملاً قابل توضیح (Explainable) است: بر اساس آستانه‌ها
و هم‌جهتی بخش‌ها تصمیم می‌گیرد و دلایل فارسی تولید می‌کند. طراحی به‌گونه‌ای است
که در Milestone 3 می‌توان یک مدل یادگیری ماشین/LLM (`ai/models`, `ai/prediction`)
را جایگزین یا به‌عنوان لایه‌ی دوم ترکیب کرد، بدون تغییر قرارداد
`DecisionEngine.decide(overall_score, overall_confidence, section_scores) -> Decision`.

### Risk Manager (`src/arya/risk/`)
بر اساس نوسان اخیر قیمت و کیفیت روند، سطح ریسک، حداکثر اندازه‌ی پوزیشن پیشنهادی
و درصد حد ضرر را محاسبه می‌کند.

### Recommendation Engine (`src/arya/analysis/recommendation/`)
مونتاژ نهایی: امتیاز کلی + اطمینان + کیفیت روند + قدرت نقدشوندگی + پیشنهاد
خرید/نگهداری/فروش + دلایل + ریسک، در قالب مدل `Recommendation`.

### Dashboard (`src/arya/dashboard/`, `src/arya/ui/` در آینده)
مصرف‌کننده‌ی نهایی مدل `Recommendation`. نسخه‌ی فعلی خروجی Console (با `rich`) است.
داشبورد گرافیکی PySide6 دقیقاً از همین مدل تغذیه خواهد شد.

## ۳. تنظیمات (`src/arya/config/settings.py`)

کلاس `Settings` تمام فایل‌های YAML را یک‌بار در ابتدای اجرا بارگذاری می‌کند و
متدهای کمکی (`enabled_indicators()`, `active_weight_profile()`, `provider_for()`)
را در اختیار بقیه‌ی سیستم قرار می‌دهد. **هیچ ماژولی مستقیماً فایل YAML باز نمی‌کند.**

## ۴. چرا این معماری؟

- **جداپذیری (Decoupling):** هر لایه فقط به مدل داده‌ی لایه‌ی قبل وابسته است، نه
  به پیاده‌سازی داخلی آن. تعویض Provider یا اضافه‌کردن اندیکاتور تأثیری روی
  Scoring Engine ندارد.
- **توسعه‌پذیری از طریق کانفیگ:** فعال/غیرفعال‌کردن اندیکاتور، تغییر وزن، تغییر
  پروفایل ریسک، همگی بدون تغییر کد و فقط با ویرایش YAML انجام می‌شود.
- **معماری Plugin:** اندیکاتورها و (در آینده) استراتژی‌ها و Providerها با یک
  دکوریتور ثبت می‌شوند؛ هسته (`IndicatorEngine`, `ProviderRegistry`) هیچ‌وقت
  نیازی به تغییر برای افزودن مورد جدید ندارد.
- **قابلیت توضیح (Explainability):** AI Decision Engine از ابتدا دلیل تولید
  می‌کند، نه فقط یک عدد؛ این هم برای اعتماد کاربر و هم برای ادغام آینده با
  LLM (فایل `ai/explainability`) حیاتی است.
