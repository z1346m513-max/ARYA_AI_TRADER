"""Provider دادهٔ بورس ایران بر پایهٔ endpointهای عمومی TSETMC.

این Provider بدون API key کار می‌کند، اما برای پایداری، timeout، retry و تشخیص
پاسخ‌های مسدودشده را اعمال می‌کند. نمادهای TSETMC با ``insCode`` شناسایی می‌شوند
و از طریق جست‌وجوی نماد به تاریخچهٔ روزانه نگاشت می‌شوند.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.providers.base import MarketDataProvider, ProviderRegistry


class TsetmcProviderError(RuntimeError):
    """خطای قابل‌گزارش هنگام دریافت داده از TSETMC."""


@ProviderRegistry.register("tsetmc")
class TsetmcMarketProvider(MarketDataProvider):
    """دریافت دادهٔ روزانهٔ نمادهای بورس و فرابورس ایران از TSETMC."""

    name = "tsetmc"
    _default_base_url = "https://cdn.tsetmc.com"
    _market_watch_path = (
        "/api/ClosingPrice/GetMarketWatch?market=0&paperTypes[0]=1&paperTypes[1]=2"
        "&paperTypes[2]=3&paperTypes[3]=4&paperTypes[4]=5&paperTypes[5]=6"
        "&paperTypes[6]=7&paperTypes[7]=8&paperTypes[8]=9"
        "&withBestLimits=false&hEven=0&RefID=0"
    )

    def __init__(
        self,
        market: str = "stock",
        base_url: str | None = None,
        timeout: float = 15.0,
        retries: int = 3,
        backoff_seconds: float = 0.5,
        user_agent: str = "ARYA-AI-Trader/0.1 (+https://github.com/ziya1346/ARYA_AI_TRADER)",
    ):
        if market != "stock":
            raise ValueError("TSETMC provider فقط برای market='stock' پشتیبانی می‌شود")
        self.market = market
        self.base_url = (base_url or self._default_base_url).rstrip("/")
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.user_agent = user_agent

    def _get_json(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                if not raw:
                    raise TsetmcProviderError(f"پاسخ خالی از TSETMC: {url}")
                try:
                    payload = json.loads(raw.decode("utf-8-sig"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise TsetmcProviderError("پاسخ TSETMC JSON معتبر نیست یا دسترسی مسدود شده است") from exc
                if not isinstance(payload, dict):
                    raise TsetmcProviderError("ساختار پاسخ TSETMC نامعتبر است")
                return payload
            except HTTPError as exc:
                last_error = exc
                retryable = exc.code in {429, 500, 502, 503, 504}
                if not retryable:
                    break
            except (URLError, TimeoutError, TsetmcProviderError) as exc:
                last_error = exc
            if attempt < self.retries - 1:
                time.sleep(self.backoff_seconds * (2**attempt))
        raise TsetmcProviderError(f"دریافت داده از TSETMC ناموفق بود: {url}") from last_error

    @staticmethod
    def _unwrap(payload: dict, key: str) -> list[dict]:
        value = payload.get(key, [])
        if isinstance(value, dict):
            value = value.get("items", value.get("data", []))
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def list_symbols(self) -> list[Symbol]:
        rows = self._unwrap(self._get_json(self._market_watch_path), "marketwatch")
        result: list[Symbol] = []
        seen: set[str] = set()
        for row in rows:
            ticker = str(row.get("lVal18AFC") or row.get("lVal18") or "").strip()
            if ticker and ticker not in seen:
                seen.add(ticker)
                result.append(Symbol(ticker=ticker, market="stock", name=row.get("lVal30")))
        return result

    def _resolve_instrument(self, ticker: str) -> tuple[str, str | None]:
        rows = self._unwrap(self._get_json(f"/api/Instrument/GetInstrumentSearch/{quote(ticker)}"), "instrumentSearch")
        for row in rows:
            symbol = str(row.get("lVal18AFC") or row.get("lVal18") or "").strip()
            if symbol == ticker:
                return str(row["insCode"]), row.get("lVal30")
        if rows and rows[0].get("insCode"):
            return str(rows[0]["insCode"]), rows[0].get("lVal30")
        raise TsetmcProviderError(f"نماد در TSETMC پیدا نشد: {ticker}")

    @staticmethod
    def _number(row: dict, *keys: str, default: float = 0.0) -> float:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return default

    @staticmethod
    def _timestamp(row: dict) -> datetime:
        raw = str(row.get("dEven") or row.get("date") or "")
        if len(raw) == 8 and raw.isdigit():
            return datetime.strptime(raw, "%Y%m%d").replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc)

    def fetch_ohlcv(self, symbol: Symbol, timeframe: str, limit: int = 200) -> OHLCVSeries:
        if timeframe not in {"1d", "1D", "daily"}:
            raise ValueError("TSETMC provider فعلاً فقط timeframe روزانه را پشتیبانی می‌کند")
        if limit <= 0:
            raise ValueError("limit باید بزرگ‌تر از صفر باشد")
        ins_code, resolved_name = self._resolve_instrument(symbol.ticker)
        rows = self._unwrap(
            self._get_json(f"/api/ClosingPrice/GetClosingPriceDailyList/{ins_code}/{limit}"),
            "closingPriceDaily",
        )
        candles: list[Candle] = []
        for row in rows[-limit:]:
            close = self._number(row, "pClosing", "pc", "pDrCotVal")
            previous = self._number(row, "priceYesterday", "py", default=close)
            open_ = self._number(row, "priceFirst", "pf", default=previous)
            high = self._number(row, "priceMax", "pmax", default=max(open_, close))
            low = self._number(row, "priceMin", "pmin", default=min(open_, close))
            if close <= 0 or low < 0 or high < low:
                continue
            candles.append(Candle(self._timestamp(row), open_, high, low, close, self._number(row, "qTotTran5J", "zTotTran")))
        if not candles:
            raise TsetmcProviderError(f"برای نماد {symbol.ticker} دادهٔ روزانه‌ای دریافت نشد")
        candles.sort(key=lambda candle: candle.timestamp)
        return OHLCVSeries(
            symbol=Symbol(ticker=symbol.ticker, market="stock", name=symbol.name or resolved_name),
            timeframe="1d",
            candles=candles,
        )
