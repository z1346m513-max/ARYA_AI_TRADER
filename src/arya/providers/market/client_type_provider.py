"""
حقیقی / حقوقی (ClientType) — الگوی مشترک pytse-client و 5j9/tsetmc.

API CDN:
  GET /api/ClientType/GetClientType/{InsCode}/1/0     # آخرین
  GET /api/ClientType/GetClientTypeHistory/{InsCode}  # تاریخچه
  GET /api/Instrument/GetInstrumentSearch/{Ticker}
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ClientTypeProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClientTypeSnapshot:
    """خلاصه خرید/فروش حقیقی و حقوقی یک نماد."""

    ticker: str
    ins_code: str
    buy_individual_volume: float | None = None
    buy_individual_count: float | None = None
    buy_institutional_volume: float | None = None
    buy_institutional_count: float | None = None
    sell_individual_volume: float | None = None
    sell_individual_count: float | None = None
    sell_institutional_volume: float | None = None
    sell_institutional_count: float | None = None

    @property
    def net_institutional_volume(self) -> float | None:
        b = self.buy_institutional_volume
        s = self.sell_institutional_volume
        if b is None or s is None:
            return None
        return b - s

    @property
    def net_individual_volume(self) -> float | None:
        b = self.buy_individual_volume
        s = self.sell_individual_volume
        if b is None or s is None:
            return None
        return b - s

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["net_institutional_volume"] = self.net_institutional_volume
        d["net_individual_volume"] = self.net_individual_volume
        return d


class ClientTypeProvider:
    name = "client_type"
    _default_base = "https://cdn.tsetmc.com"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 15.0,
        retries: int = 3,
        backoff_seconds: float = 0.5,
        user_agent: str = "ARYA-AI-Trader/0.2 (+client-type; Iran TSE)",
    ) -> None:
        self.base_url = (base_url or self._default_base).rstrip("/")
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.user_agent = user_agent

    def _get_json(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                req = Request(
                    url,
                    headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                )
                with urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                if not raw:
                    raise ClientTypeProviderError(f"پاسخ خالی: {url}")
                return json.loads(raw.decode("utf-8-sig"))
            except HTTPError as exc:
                last_error = exc
                if exc.code in {429, 500, 502, 503, 504} and attempt < self.retries - 1:
                    time.sleep(self.backoff_seconds * (2**attempt))
                    continue
                break
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(self.backoff_seconds * (2**attempt))
                    continue
                break
        raise ClientTypeProviderError(f"ClientType ناموفق: {url}") from last_error

    def resolve_ins_code(self, ticker: str) -> str:
        payload = self._get_json(f"/api/Instrument/GetInstrumentSearch/{quote(ticker)}")
        rows = payload.get("instrumentSearch") or []
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            sym = str(row.get("lVal18AFC") or row.get("lVal18") or "").strip()
            if sym == ticker and row.get("insCode"):
                return str(row["insCode"])
        if rows and isinstance(rows[0], dict) and rows[0].get("insCode"):
            return str(rows[0]["insCode"])
        raise ClientTypeProviderError(f"نماد پیدا نشد: {ticker}")

    @staticmethod
    def _num(row: dict, *keys: str) -> float | None:
        for k in keys:
            v = row.get(k)
            if v in (None, ""):
                continue
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
        return None

    def fetch_latest(self, ticker: str) -> ClientTypeSnapshot:
        ins = self.resolve_ins_code(ticker)
        # قرارداد رایج CDN: GetClientType/{insCode}/{toDateOrFlag}/{fromFlag}
        payload = self._get_json(f"/api/ClientType/GetClientType/{ins}/1/0")
        row = payload.get("clientType") or payload
        if isinstance(row, list) and row:
            row = row[0]
        if not isinstance(row, dict):
            row = {}

        return ClientTypeSnapshot(
            ticker=ticker,
            ins_code=ins,
            buy_individual_volume=self._num(row, "buy_I_Volume", "buyIVolume"),
            buy_individual_count=self._num(row, "buy_CountI", "buyCountI"),
            buy_institutional_volume=self._num(row, "buy_N_Volume", "buyNVolume"),
            buy_institutional_count=self._num(row, "buy_CountN", "buyCountN"),
            sell_individual_volume=self._num(row, "sell_I_Volume", "sellIVolume"),
            sell_individual_count=self._num(row, "sell_CountI", "sellCountI"),
            sell_institutional_volume=self._num(row, "sell_N_Volume", "sellNVolume"),
            sell_institutional_count=self._num(row, "sell_CountN", "sellCountN"),
        )
