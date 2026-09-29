"""
بک‌تست تکرارپذیر با گیت ریسک و جریان معاملاتی شبیه‌سازی‌شده.

استفادهٔ سریع:

```python
from arya.backtest import BacktestEngine, BacktestConfig, MovingAverageCrossover

engine = BacktestEngine(config=BacktestConfig())
result = engine.run(df, strategy=MovingAverageCrossover(), symbol="FOOLAD")
print(result.metrics.total_return_pct)
```

هشدار: عملکرد گذشته در بک‌تست، تضمین‌کنندهٔ عملکرد آینده نیست.
"""
from arya.backtest.engine import BacktestConfig, BacktestEngine
from arya.backtest.models import (
    BacktestResult,
    EquityPoint,
    Fill,
    Order,
    OrderStatus,
    PerformanceMetrics,
    Position,
    Side,
    Signal,
    Trade,
)
from arya.backtest.strategies import MovingAverageCrossover, MomentumStrategy, Strategy

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestResult",
    "EquityPoint",
    "Fill",
    "Order",
    "OrderStatus",
    "PerformanceMetrics",
    "Position",
    "Side",
    "Signal",
    "Trade",
    "MovingAverageCrossover",
    "MomentumStrategy",
    "Strategy",
]
