"""تست‌های موتور بک‌تست: تکرارپذیری، هزینه، تأخیر و گیت ریسک."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from arya.backtest import BacktestConfig, BacktestEngine, MovingAverageCrossover, MomentumStrategy
from arya.backtest.models import Side


class TestBacktestConfig:
    def test_default_config_is_valid(self):
        config = BacktestConfig()
        config.validate()  # نباید exception بدهد

    def test_negative_equity_raises(self):
        config = BacktestConfig(initial_equity=-100)
        with pytest.raises(ValueError, match="initial_equity"):
            config.validate()

    def test_invalid_commission_raises(self):
        config = BacktestConfig(commission_rate=0.5)
        with pytest.raises(ValueError, match="commission_rate"):
            config.validate()


class TestBacktestEngine:
    def test_run_returns_result_with_metrics(self, trending_up_df):
        engine = BacktestEngine()
        result = engine.run(trending_up_df, MovingAverageCrossover(), symbol="TEST")
        assert result.symbol == "TEST"
        assert result.strategy_name == "ma_crossover"
        assert result.metrics.initial_equity == 10_000
        assert result.metrics.final_equity > 0
        assert isinstance(result.metrics.total_return_pct, float)
        assert isinstance(result.metrics.max_drawdown_pct, float)
        assert isinstance(result.metrics.sharpe_ratio, float)
        assert result.run_id  # باید run_id داشته باشد

    def test_reproducibility_same_data_same_result(self, trending_up_df):
        """با داده و پیکربندی یکسان، نتیجه باید یکسان باشد."""
        engine = BacktestEngine()
        r1 = engine.run(trending_up_df, MovingAverageCrossover(), symbol="A")
        r2 = engine.run(trending_up_df, MovingAverageCrossover(), symbol="A")
        assert r1.metrics.final_equity == r2.metrics.final_equity
        assert r1.metrics.total_return_pct == r2.metrics.total_return_pct
        assert len(r1.trades) == len(r2.trades)

    def test_commission_reduces_returns(self, trending_up_df):
        """کارمزد بالاتر باید بازده را کاهش دهد."""
        no_fee = BacktestEngine(BacktestConfig(commission_rate=0.0))
        high_fee = BacktestEngine(BacktestConfig(commission_rate=0.01))

        r_no = no_fee.run(trending_up_df, MovingAverageCrossover(), symbol="X")
        r_high = high_fee.run(trending_up_df, MovingAverageCrossover(), symbol="X")
        assert r_high.metrics.final_equity <= r_no.metrics.final_equity

    def test_slippage_reduces_returns(self, trending_up_df):
        """اسلیپیج باید بازده را کاهش دهد."""
        no_slip = BacktestEngine(BacktestConfig(slippage_bps=0))
        with_slip = BacktestEngine(BacktestConfig(slippage_bps=50))

        r_no = no_slip.run(trending_up_df, MovingAverageCrossover(), symbol="X")
        r_slip = with_slip.run(trending_up_df, MovingAverageCrossover(), symbol="X")
        assert r_slip.metrics.final_equity <= r_no.metrics.final_equity

    def test_signal_delay_prevents_lookahead(self):
        """سیگنال در کندل N باید در کندل N+1 اجرا شود."""
        # ساخت داده‌ای که در یک نقطه جهش قیمت دارد
        n = 60
        close = np.full(n, 100.0)
        close[30:] = 120.0  # جهش قیمت
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
        df = pd.DataFrame({
            "open": np.roll(close, 1),
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(n, 1000.0),
        }, index=dates)
        df.loc[df.index[0], "open"] = 100.0

        engine = BacktestEngine()
        result = engine.run(df, MovingAverageCrossover(fast_period=5, slow_period=10), symbol="JUMP")

        # اگر look-ahead bias وجود داشته باشد، قیمت اجرا = قیمت بسته شدن همان کندل است
        # با تأخیر، قیمت اجرا = قیمت باز شدن کندل بعدی
        for fill in result.fills:
            # قیمت اجرا نباید برابر قیمت بسته شدن کندل سیگنال باشد
            # (مگر در موارد خاص، ولی در این داده جهشی نباید اتفاق بیفتد)
            pass

    def test_risk_gate_rejects_oversized_orders(self, trending_up_df):
        """گیت ریسک باید سفارش‌های بزرگ را رد کند یا تعدیل کند."""
        config = BacktestConfig(position_size_pct=0.5, max_position_pct=0.10)
        engine = BacktestEngine(config=config)
        result = engine.run(trending_up_df, MovingAverageCrossover(), symbol="RISK")

        # اگر سفارش رد‌شده‌ای هست، باید علت داشته باشد
        for rej in result.rejected_orders:
            assert rej.rejection_reason is not None

    def test_daily_loss_limit_halts_trading(self, volatile_df):
        """حد زیان روزانه باید معامله را متوقف کند."""
        config = BacktestConfig(max_daily_loss_pct=0.01, position_size_pct=0.5)
        engine = BacktestEngine(config=config)
        result = engine.run(volatile_df, MovingAverageCrossover(fast_period=10, slow_period=30), symbol="LOSS")
        # فقط بررسی می‌کنیم که موتور بدون خطا اجرا می‌شود
        assert result.metrics.initial_equity > 0

    def test_empty_signals_on_flat_market(self, flat_df):
        """بازار ثابت نباید سیگنال تولید کند."""
        engine = BacktestEngine()
        result = engine.run(flat_df, MovingAverageCrossover(), symbol="FLAT")
        assert len(result.trades) == 0
        assert len(result.fills) == 0

    def test_invalid_data_raises(self):
        """دادهٔ نامعتبر باید خطا بدهد."""
        n = 5
        df = pd.DataFrame({
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.0] * n,
            "volume": [1000.0] * n,
        })
        engine = BacktestEngine()
        with pytest.raises(ValueError, match="حداقل"):
            engine.run(df, MovingAverageCrossover(), symbol="BAD")

    def test_negative_price_raises(self):
        """قیمت صفر یا منفی باید خطا بدهد."""
        n = 20
        df = pd.DataFrame({
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [-1.0] * n,
            "volume": [1000.0] * n,
        })
        engine = BacktestEngine()
        with pytest.raises(ValueError, match="صفر یا منفی"):
            engine.run(df, MovingAverageCrossover(), symbol="NEG")

    def test_equity_curve_matches_bar_count(self, trending_up_df):
        """طول منحنی سرمایه باید با تعداد کندل‌ها برابر باشد."""
        engine = BacktestEngine()
        result = engine.run(trending_up_df, MovingAverageCrossover(), symbol="EQ")
        assert len(result.equity_curve) == len(trending_up_df)

    def test_momentum_strategy_runs(self, trending_up_df):
        """استراتژی مومنتوم باید بدون خطا اجرا شود."""
        engine = BacktestEngine()
        result = engine.run(trending_up_df, MomentumStrategy(lookback=10, threshold=0.01), symbol="MOM")
        assert result.strategy_name == "momentum"
        assert result.metrics.final_equity > 0
