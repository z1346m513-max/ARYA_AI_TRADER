import numpy as np
import pandas as pd
import pytest

import arya.technical.indicators.trend.moving_average  # noqa: F401
import arya.technical.indicators.momentum.rsi  # noqa: F401
import arya.technical.indicators.momentum.macd  # noqa: F401
import arya.technical.indicators.volatility.bollinger  # noqa: F401
import arya.technical.indicators.volume.obv  # noqa: F401
from arya.technical.indicators.base import IndicatorRegistry


@pytest.fixture
def sample_df():
    rng = np.random.default_rng(1)
    n = 100
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    df = pd.DataFrame(
        {
            "open": close + rng.normal(0, 0.2, n),
            "high": close + abs(rng.normal(0, 0.5, n)),
            "low": close - abs(rng.normal(0, 0.5, n)),
            "close": close,
            "volume": rng.integers(1000, 5000, n).astype(float),
        }
    )
    return df


@pytest.mark.parametrize("name", ["sma", "ema", "rsi", "macd", "bollinger", "obv"])
def test_indicator_computes_and_score_in_range(sample_df, name):
    indicator = IndicatorRegistry.create(name, params={}, weight=1.0)
    result = indicator.compute(sample_df)
    assert -1.0 <= result.score <= 1.0
    assert result.name == name
    assert isinstance(result.value, dict)


def test_rsi_overbought_alert():
    # قیمت به‌طور مصنوعی به‌شدت صعودی -> RSI باید overbought بدهد
    close = np.linspace(100, 200, 40)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(40, 1000.0),
        }
    )
    indicator = IndicatorRegistry.create("rsi", params={"period": 14, "overbought": 70, "oversold": 30})
    result = indicator.compute(df)
    assert "overbought" in result.triggered_alerts
