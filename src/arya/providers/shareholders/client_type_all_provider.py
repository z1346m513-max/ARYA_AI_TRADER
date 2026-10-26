"""Real ClientTypeAll driver — natural/legal flow from old.tsetmc.com.

Format reference (secondary): 5j9/tsetmc market_watch.client_type_all
Columns: ins_code, n_buy_count, l_buy_count, n_buy_volume, l_buy_volume,
         n_sell_count, l_sell_count, n_sell_volume, l_sell_volume
Row separator: ;

Limits: volume/count only (no Rial value); no shareholder count; may timeout outside Iran.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from arya.models.shareholders import ShareholderFlowMetrics
from arya.providers.shareholder_base import ShareholderDataProvider, ShareholderProviderRegistry


class ClientTypeAllProviderError(RuntimeError):
    pass


@ShareholderProviderRegistry.register("client_type_all")
class ClientTypeAllProvider(ShareholderDataProvider):
    name = "client_type_all"
    _default_data_url = "https://old.tsetmc.com/tsev2/data/ClientTypeAll.aspx"
    _default_cdn_base = "https://cdn.tsetmc.com"
    _search_path = "/api/Instrument/GetInstrumentSearch/{query}"

    def __init__(
        self,
        data_url: str | None = None,
        cdn_base: str | None = None,
        timeout: float = 20.0,
        retries: int = 3,
        backoff_seconds: float = 0.5,
        user_agent: str = "ARYA-AI-Trader/0.1 (+client-type-all)",
    ):
        self.data_url = data_url or self._default_data_url
        self.cdn_base = (cdn_base or self._default_cdn_base).rstrip("/")
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.user_agent = user_agent
        self._cache_rows: dict[str, dict[str, float]] | None = None
        self._cache_at: float | None = None
        self._cache_ttl = 60.0

    def _fetch_bytes(self, url: str) -> bytes:
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                req = Request(url, headers={"User-Agent": self.user_agent, "Accept": "*/*"})
                with urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                if not raw:
                    raise ClientTypeAllProviderError(f"empty response: {url}")
                return raw
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (URLError, TimeoutError, ClientTypeAllProviderError) as exc:
                last_error = exc
            if attempt < self.retries - 1:
                time.sleep(self.backoff_seconds * (2**attempt))
        raise ClientTypeAllProviderError(f"fetch failed: {url}") from last_error

    def _resolve_ins_code(self, ticker: str) -> str:
        path = self._search_path.format(query=quote(ticker))
        url = f"{self.cdn_base}{path}"
        raw = self._fetch_bytes(url)
        try:
            payload = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ClientTypeAllProviderError("instrument search JSON invalid") from exc
        rows = payload.get("instrumentSearch") or []
        if isinstance(rows, dict):
            rows = rows.get("items") or rows.get("data") or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            sym = str(row.get("lVal18AFC") or row.get("lVal18") or "").strip()
            if sym == ticker and row.get("insCode"):
                return str(row["insCode"])
        if rows and isinstance(rows[0], dict) and rows[0].get("insCode"):
            return str(rows[0]["insCode"])
        raise ClientTypeAllProviderError(f"ticker not found: {ticker}")

    @staticmethod
    def parse_client_type_all(text: str) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        chunks = text.replace("\r", "").replace("\n", "").split(";")
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = chunk.split(",")
            if len(parts) < 9:
                continue
            ins = parts[0].strip()
            if not ins or not ins.isdigit():
                continue
            try:
                nums = [float(x) if x not in ("", None) else 0.0 for x in parts[1:9]]
            except ValueError:
                continue
            result[ins] = {
                "n_buy_count": nums[0],
                "l_buy_count": nums[1],
                "n_buy_volume": nums[2],
                "l_buy_volume": nums[3],
                "n_sell_count": nums[4],
                "l_sell_count": nums[5],
                "n_sell_volume": nums[6],
                "l_sell_volume": nums[7],
            }
        return result

    def _load_all_rows(self) -> dict[str, dict[str, float]]:
        now = time.time()
        if (
            self._cache_rows is not None
            and self._cache_at is not None
            and (now - self._cache_at) < self._cache_ttl
        ):
            return self._cache_rows
        raw = self._fetch_bytes(self.data_url)
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="ignore")
        rows = self.parse_client_type_all(text)
        if not rows:
            raise ClientTypeAllProviderError("no rows parsed from ClientTypeAll")
        self._cache_rows = rows
        self._cache_at = now
        return rows

    def fetch_shareholder_flow(self, ticker: str, days: int = 5) -> ShareholderFlowMetrics:
        del days
        ticker = (ticker or "").strip()
        if not ticker:
            return ShareholderFlowMetrics(ticker="", data_quality="missing", source=self.name)
        try:
            ins_code = self._resolve_ins_code(ticker)
            rows = self._load_all_rows()
        except ClientTypeAllProviderError as exc:
            return ShareholderFlowMetrics(
                ticker=ticker,
                data_quality="missing",
                source=self.name,
                notes=(str(exc),),
            )
        row = rows.get(ins_code)
        if not row:
            return ShareholderFlowMetrics(
                ticker=ticker,
                data_quality="missing",
                source=self.name,
                notes=(f"insCode={ins_code} not in ClientTypeAll",),
            )
        n_buy_vol = row["n_buy_volume"]
        l_buy_vol = row["l_buy_volume"]
        n_sell_vol = row["n_sell_volume"]
        l_sell_vol = row["l_sell_volume"]
        n_buy_cnt = row["n_buy_count"]
        n_sell_cnt = row["n_sell_count"]
        total_buy = n_buy_vol + l_buy_vol
        legal_buy_share = (l_buy_vol / total_buy) if total_buy > 0 else None
        legal_net_volume = l_buy_vol - l_sell_vol
        ind_avg_buy = (n_buy_vol / n_buy_cnt) if n_buy_cnt > 0 else None
        ind_avg_sell = (n_sell_vol / n_sell_cnt) if n_sell_cnt > 0 else None
        return ShareholderFlowMetrics(
            ticker=ticker,
            individual_avg_buy_value=ind_avg_buy,
            individual_avg_sell_value=ind_avg_sell,
            legal_buy_share=legal_buy_share,
            legal_net_buy_value=legal_net_volume,
            data_quality="partial",
            source=f"{self.name}:{self.data_url}",
            notes=(
                f"insCode={ins_code}",
                "volume-based not Rial; no shareholder count in ClientTypeAll",
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
