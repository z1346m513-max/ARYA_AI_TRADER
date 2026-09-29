# Backtest runner

`scripts/run_backtest.py` is a local, read-only backtest runner. It does not connect to exchanges, brokers, or provider APIs, and it cannot send orders.

## Input

Provide chronological OHLCV CSV data. The runner requires these columns:

```csv
timestamp,open,high,low,close,volume
2025-01-01T00:00:00Z,100,102,99,101,1200
```

Only `timestamp`, `open`, and `close` are used by the initial strategy. Do not use future-corrected or otherwise leaky data.

## Run

```bash
python scripts/run_backtest.py \
  --input data/your-symbol-1h.csv \
  --output data/reports/my-backtest.json \
  --initial-cash 100000 \
  --fast 20 --slow 50 \
  --fee-bps 10 --slippage-bps 5
```

The included strategy is long-only SMA crossover. A signal is calculated after a candle closes and executed at the *next* candle's open; this avoids same-bar look-ahead. Fees and slippage are included on each fill.

## Report

The JSON output contains parameters, final equity, net return, maximum drawdown, return volatility, and every simulated fill. Treat results as a research artifact, not a trading recommendation. Validate timestamp ordering, corporate actions, liquidity, spreads, data quality, and out-of-sample performance before relying on results.
