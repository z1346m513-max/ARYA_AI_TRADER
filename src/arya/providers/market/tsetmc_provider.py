"""Provider واقعی بورس ایران با pytse-client / TSETMC.

این Provider فقط قرارداد MarketDataProvider را پیاده‌سازی می‌کند تا
لایه‌های بالادست به pytse-client وابسته نباشند.
نسخه هدف pytse-client: 0.19.1
"""

from __future__ import annotations

import logging

import pandas as pd
from pytse_client import Ticker

from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.providers.base import MarketDataProvider, ProviderRegistry

logger = logging.getLogger(__name__)


@ProviderRegistry.register("tsetmc")
class TsetmcMarketProvider(MarketDataProvider):
    """دریافت OHLCV روزانه از TSETMC از طریق pytse-client."""

    name = "tsetmc"

    def __init__(self, market: str = "stock", adjust: bool = False):
        if market != "stock":
            raise ValueError("TsetmcMarketProvider فقط برای market='stock' است.")
        self.market = market
        self.adjust = adjust

    def list_symbols(self) -> list[Symbol]:
        """نمادهای موجود در دیتای محلی pytse-client را برمی‌گرداند."""
        from pytse_client.symbols_data import all_symbols

        return [
            Symbol(ticker=ticker, market="stock", name=ticker, currency="IRR")
            for ticker in sorted(all_symbols())
        ]

    def fetch_ohlcv(
        self, symbol: Symbol, timeframe: str, limit: int = 200
    ) -> OHLCVSeries:
        if symbol.market != "stock":
            raise ValueError("TSETMC فقط نمادهای market='stock' را می‌پذیرد.")
        if timeframe not in {"1d", "1D", "daily"}:
            raise ValueError(
                "pytse-client Ticker.history در این Provider فقط timeframe روزانه "
                "را پشتیبانی می‌کند؛ از '1d' استفاده کنید."
            )
        if limit <= 0:
            raise ValueError("limit باید بزرگ‌تر از صفر باشد.")

        logger.info("Fetching TSETMC history for %s (limit=%s)", symbol.ticker, limit)
        ticker = Ticker(symbol=symbol.ticker, adjust=self.adjust)
        history = ticker.history

        if history is None or history.empty:
            raise ValueError(f"برای نماد '{symbol.ticker}' داده تاریخی دریافت نشد.")

        frame = self._normalize_history(history).tail(limit)
        if frame.empty:
            raise ValueError(f"داده OHLCV معتبر برای '{symbol.ticker}' وجود ندارد.")

        resolved_symbol = Symbol(
            ticker=symbol.ticker,
            market="stock",
            name=ticker.title or symbol.name or symbol.ticker,
            currency="IRR",
        )
        candles = [
            Candle(
                timestamp=row["timestamp"].to_pydatetime()
                if hasattr(row["timestamp"], "to_pydatetime")
                else row["timestamp"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for _, row in frame.iterrows()
        ]
        return OHLCVSeries(
            symbol=resolved_symbol,
            timeframe="1d",
            candles=candles,
        )

    @staticmethod
    def _normalize_history(history: pd.DataFrame) -> pd.DataFrame:
        """ستون‌های history را به قرارداد داخلی ARYA نگاشت می‌کند."""
        frame = history.copy()
        frame.columns = [str(column).strip().lower() for column in frame.columns]

        aliases = {
            "timestamp": ("date", "datetime", "timestamp", "time"),
            "open": ("open", "open_price"),
            "high": ("high", "high_price"),
            "low": ("low", "low_price"),
            "close": ("close", "adj_close", "adj close", "final"),
            "volume": ("volume", "vol", "trade_volume"),
        }

        selected: dict[str, str] = {}
        for target, candidates in aliases.items():
            for candidate in candidates:
                if candidate in frame.columns:
                    selected[target] = candidate
                    break
            if target not in selected:
                raise ValueError(
                    f"ستون لازم '{target}' در TSETMC history پیدا نشد. "
                    f"ستون‌های دریافتی: {list(frame.columns)}"
                )

        normalized = frame[[selected[key] for key in aliases]].rename(
            columns={selected[key]: key for key in aliases}
        )
        normalized["timestamp"] = pd.to_datetime(
            normalized["timestamp"], errors="coerce"
        )
        for column in ("open", "high", "low", "close", "volume"):
            normalized[column] = pd.to_numeric(
                normalized[column], errors="coerce"
            )

        normalized = normalized.dropna(
            subset=["timestamp", "open", "high", "low", "close", "volume"]
        )
        normalized = normalized.sort_values("timestamp").reset_index(drop=True)
        return normalized
