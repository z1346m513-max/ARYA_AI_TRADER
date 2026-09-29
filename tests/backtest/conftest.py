"""Fixtureهای مشترک برای تست‌های بک‌تست."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def trending_up_df() -> pd.DataFrame:
    """دیتافریم با روند نزولی اولیه سپس صعودی برای تست کراس صعودی."""
    n = 120
    rng = np.random.default_rng(42)
    # ابتدا نزولی، سپس صعودی تا کراس SMA رخ دهد
    close = np.zeros(n)
    close[:40] = 150 - np.cumsum(np.linspace(0.5, 0.5, 40))  # نزولی
    close[40:] = 130 + np.cumsum(np.linspace(0.8, 0.8, 80))  # صعودی قوی‌تر
    close += rng.normal(0, 1, n)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    return pd.DataFrame({
        "open": close + rng.normal(0, 0.2, n),
        "high": close + abs(rng.normal(0, 0.5, n)),
        "low": close - abs(rng.normal(0, 0.5, n)),
        "close": close,
        "volume": rng.integers(1000, 5000, n).astype(float),
    }, index=dates)


@pytest.fixture
def flat_df() -> pd.DataFrame:
    """دیتافریم با قیمت ثابت - نباید سیگنال تولید کند."""
    n = 100
    close = np.full(n, 100.0)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    return pd.DataFrame({
        "open": close,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "volume": np.full(n, 1000.0),
    }, index=dates)


@pytest.fixture
def volatile_df() -> pd.DataFrame:
    """دیتافریم با نوسان بالا برای تست رفتار ریسک."""
    rng = np.random.default_rng(99)
    n = 150
    close = 100 + np.cumsum(rng.normal(0, 3, n))
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    return pd.DataFrame({
        "open": close + rng.normal(0, 0.2, n),
        "high": close + abs(rng.normal(0, 1, n)),
        "low": close - abs(rng.normal(0, 1, n)),
        "close": close,
        "volume": rng.integers(1000, 5000, n).astype(float),
    }, index=dates)
