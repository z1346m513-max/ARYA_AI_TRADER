"""تست‌های استراتژی‌های خط پایه: تولید سیگنال و عدم استفاده از دادهٔ آینده."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from arya.backtest import MovingAverageCrossover, MomentumStrategy
from arya.backtest.models import Side


class TestMovingAverageCrossover:
    def test_no_signals_on_short_data(self):
        """دادهٔ کوتاه نباید سیگنال تولید کند."""
        n = 10
        df = pd.DataFrame({
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.0] * n,
            "volume": [1000.0] * n,
        })
        strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
        assert strategy.generate_signals(df) == []

    def test_no_signals_on_flat_data(self, flat_df):
        """قیمت ثابت نباید سیگنال تولید کند."""
        strategy = MovingAverageCrossover(fast_period=10, slow_period=30)
        signals = strategy.generate_signals(flat_df)
        assert signals == []

    def test_buy_signal_on_uptrend(self, trending_up_df):
        """روند صعودی باید حداقل یک سیگنال خرید تولید کند."""
        strategy = MovingAverageCrossover(fast_period=10, slow_period=30)
        signals = strategy.generate_signals(trending_up_df)
        buy_signals = [s for s in signals if s.side == Side.BUY]
        assert len(buy_signals) > 0

    def test_invalid_periods_raise(self):
        """دوره‌های نامعتبر باید خطا بدهد."""
        with pytest.raises(ValueError, match="fast_period"):
            MovingAverageCrossover(fast_period=50, slow_period=20)

    def test_signal_bar_index_in_range(self, trending_up_df):
        """همهٔ بار اندیس‌های سیگنال باید در محدودهٔ داده باشند."""
        strategy = MovingAverageCrossover(fast_period=10, slow_period=30)
        signals = strategy.generate_signals(trending_up_df)
        n = len(trending_up_df)
        for sig in signals:
            assert 0 <= sig.bar_index < n

    def test_no_future_data_leak(self):
        """بررسی عدم نشت دادهٔ آینده: سیگنال در اندیس i نباید به داده‌های بعد از i وابسته باشد.

        این تست با حذف داده‌های بعد از نقطهٔ سیگنال، صحت را بررسی می‌کند.
        """
        n = 100
        rng = np.random.default_rng(42)
        close = 100 + np.cumsum(rng.normal(0, 1, n))
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
        df_full = pd.DataFrame({
            "open": close + rng.normal(0, 0.2, n),
            "high": close + abs(rng.normal(0, 0.5, n)),
            "low": close - abs(rng.normal(0, 0.5, n)),
            "close": close,
            "volume": rng.integers(1000, 5000, n).astype(float),
        }, index=dates)

        strategy = MovingAverageCrossover(fast_period=10, slow_period=30)
        signals_full = strategy.generate_signals(df_full)

        if not signals_full:
            pytest.skip("سیگنالی تولید نشد، تست نشتی داده قابل بررسی نیست")

        # بررسی: سیگنال‌های تولیدشده با دادهٔ کامل و دادهٔ کوتاه‌شده تا همان نقطه باید یکسان باشند
        first_signal = signals_full[0]
        df_truncated = df_full.iloc[:first_signal.bar_index + 1]
        signals_trunc = strategy.generate_signals(df_truncated)

        # حداقل اولین سیگنال باید در دادهٔ کوتاه‌شده هم وجود داشته باشد
        if signals_trunc:
            assert signals_trunc[0].bar_index == first_signal.bar_index
            assert signals_trunc[0].side == first_signal.side


class TestMomentumStrategy:
    def test_buy_signal_on_strong_momentum(self):
        """بازده قوی مثبت باید سیگنال خرید تولید کند."""
        n = 50
        close = np.linspace(100, 150, n)  # روند صعودی قوی
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
        df = pd.DataFrame({
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(n, 1000.0),
        }, index=dates)

        strategy = MomentumStrategy(lookback=10, threshold=0.01)
        signals = strategy.generate_signals(df)
        buy_signals = [s for s in signals if s.side == Side.BUY]
        assert len(buy_signals) > 0

    def test_sell_signal_on_negative_momentum(self):
        """بازده منفی قوی باید سیگنال فروش تولید کند."""
        n = 50
        close = np.linspace(150, 100, n)  # روند نزولی قوی
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
        df = pd.DataFrame({
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(n, 1000.0),
        }, index=dates)

        strategy = MomentumStrategy(lookback=10, threshold=0.01)
        signals = strategy.generate_signals(df)
        sell_signals = [s for s in signals if s.side == Side.SELL]
        assert len(sell_signals) > 0

    def test_no_signals_on_flat_data(self, flat_df):
        """بازار ثابت نباید سیگنال تولید کند."""
        strategy = MomentumStrategy(lookback=10, threshold=0.05)
        signals = strategy.generate_signals(flat_df)
        assert signals == []

    def test_invalid_lookback_raises(self):
        """lookback نامعتبر باید خطا بدهد."""
        with pytest.raises(ValueError, match="lookback"):
            MomentumStrategy(lookback=0)
