# راهنمای بک‌تست

## مقدمه

موتور بک‌تست ARYA یک ابزار تکرارپذیر برای ارزیابی استراتژی‌های معاملاتی است. این
موتور با اعمال کارمزد، اسلیپیج، تأخیر اجرا و گیت ریسک، عملکرد استراتژی را در شرایطی
نزدیک به واقعیت شبیه‌سازی می‌کند.

> **هشدار مهم:** عملکرد گذشته در بک‌تست، تضمین‌کنندهٔ عملکرد آینده نیست. بک‌تست تنها
> ابزاری برای ارزیابی منطق استراتژی است و تصمیم نهایی معامله باید با قضاوت انسانی
> انجام شود.

## شروع سریع

```python
import pandas as pd
from arya.backtest import BacktestEngine, BacktestConfig, MovingAverageCrossover

# داده‌های OHLCV را در دیتافریم با ستون‌های open, high, low, close, volume آماده کنید
df = pd.read_csv("data.csv", parse_dates=["date"], index_col="date")

# پیکربندی بک‌تست
config = BacktestConfig(
    initial_equity=10_000,
    commission_rate=0.001,      # 0.1% کارمزد
    slippage_bps=5,             # 5 basis points اسلیپیج
    position_size_pct=0.10,     # 10% سرمایه برای هر پوزیشن
    max_position_pct=0.25,     # حداکثر 25% تمرکز
    max_daily_loss_pct=0.05,    # توقف پس از 5% زیان روزانه
)

# اجرای بک‌تست
engine = BacktestEngine(config=config)
result = engine.run(df, strategy=MovingAverageCrossover(fast_period=20, slow_period=50), symbol="FOOLAD")

# مشاهدهٔ معیارها
print(f"بازده کل: {result.metrics.total_return_pct:.2f}%")
print(f"حداکثر افت سرمایه: {result.metrics.max_drawdown_pct:.2f}%")
print(f"نسبت شارپ: {result.metrics.sharpe_ratio:.2f}")
print(f"نرخ برد: {result.metrics.win_rate*100:.1f}%")
print(f"تعداد معاملات: {result.metrics.total_trades}")
```

## مفروضات و محدودیت‌ها

### تأخیر یک کندلی (Look-ahead Bias Prevention)

سیگنال تولیدشده در کندل N در کندل N+1 با قیمت باز شدن اجرا می‌شود. این تأخیر
از استفادهٔ ناخواسته از داده‌های آینده جلوگیری می‌کند.

### مدل هزینه‌ها

- **کارمزد**: درصدی از ارزش نامی سفارش (`commission_rate`)
- **اسلیپیج**: به‌صورت basis points، خرید گران‌تر و فروش ارزان‌تر از قیمت مبنا
- **هزینهٔ کل**: کارمزد + هزینهٔ اسلیپیج

### گیت ریسک

هر سفارش قبل از اجرا از گیت ریسک عبور می‌کند:

| محدودیت | توضیح |
|---|---|
| حداکثر اندازهٔ سفارش | درصدی از کل سرمایه |
| حداکثر تمرکز پوزیشن | ارزش کل پوزیشن نباید از درصد مشخصی بیشتر شود |
| حد زیان روزانه | توقف خودکار معامله پس از رسیدن به آستانه |

سفارش‌های رد‌شده با علت در `result.rejected_orders` ثبت می‌شوند.

### معیارهای عملکرد

| معیار | توضیح |
|---|---|
| `total_return_pct` | بازده کل در دورهٔ بک‌تست |
| `annualized_return_pct` | بازده سالانه‌شده |
| `volatility_pct` | نوسان سالانه‌شده |
| `max_drawdown_pct` | حداکثر افت سرمایه |
| `sharpe_ratio` | نسبت شارپ (با نرخ بدون ریسک) |
| `sortino_ratio` | نسبت سورتینو (بازده منفی فقط) |
| `win_rate` | نرخ معاملات سودده |
| `profit_factor` | نسبت سود ناخالص به زیان ناخالص |
| `turnover` | نسبت ارزش معاملات به سرمایهٔ میانگین |

## استراتژی‌های موجود

### 1. Moving Average Crossover (خط پایه)

تقاطع میانگین متحرک ساده (SMA). سیگنال خرید در کراس صعودی و فروش در کراس نزولی.

```python
from arya.backtest import MovingAverageCrossover

strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
```

### 2. Momentum Strategy

سیگنال خرید/فروش بر اساس بازده اخیر قیمت.

```python
from arya.backtest import MomentumStrategy

strategy = MomentumStrategy(lookback=20, threshold=0.02)
```

## افزودن استراتژی جدید

برای افزودن استراتژی جدید، کلاسی بسازید که قرارداد `Strategy` را پیاده کند:

```python
from arya.backtest.models import Signal, Side
from arya.backtest.strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    name = "my_strategy"

    def generate_signals(self, df):
        # منطق استراتژی شما اینجا
        # فقط از داده‌های تا لحظهٔ فعلی استفاده کنید
        signals = []
        # ...
        return signals
```

## محدودیت‌ها

- این موتور فقط بک‌تست و paper trading است و هیچ اتصال کارگزاری ندارد.
- مدل اجرای ساده است: سفارش market با اسلیپیج ثابت.
- پورتفوی تک‌نمادی است؛ مدیریت چندنمادی در فاز بعدی اضافه می‌شود.
- تقسیم سود و تغییرات سرمایه مدل نمی‌شوند.
