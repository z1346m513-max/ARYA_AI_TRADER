"""
Provider سهامداران عمده و تغییرات مالکیت — TSETMC.

منابع:
  UI جدید: https://main.tsetmc.com/ShareHolderChanges
  UI قدیم: https://old.tsetmc.com/Loader.aspx?ParTree=15131I&t=0
  API CDN:
    GET /Shareholder/GetShareHolderChanges/{onlyIncrease}
    GET /Shareholder/GetInstrumentShareHolderLast/{InsCode}
    GET /Shareholder/GetShareHolderHistory/{InsCode}/{ShareHolderId}/{Days}

onlyIncrease:
  false = همه تغییرات (افزایش و کاهش)
  true  = فقط افزایش مالکیت
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class ShareholderProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ShareHolderChange:
    """یک رکورد تغییر مالکیت سهامدار عمده."""

    symbol: str | None
    company_name: str | None
    holder_name: str | None
    ins_code: str | None
    share_holder_id: str | None
    shares_before: float | None
    shares_after: float | None
    shares_change: float | None
    percent_before: float | None
    percent_after: float | None
    percent_change: float | None
    date: str | None  # معمولاً YYYYMMDD یا ISO
    raw: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw", None)
        return d


@dataclass(frozen=True)
class ShareHolder:
    name: str
    shares: float | None
    percent: float | None
    change: float | None
    share_holder_id: str | None
    raw: dict[str, Any] | None = None


class ShareholderProvider:
    """کلاینت CDN برای سهامداران TSETMC."""

    name = "shareholder"
    _default_base = "https://cdn.tsetmc.com"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 20.0,
        retries: int = 3,
        backoff_seconds: float = 0.5,
        user_agent: str = "ARYA-AI-Trader/0.2 (+shareholder; Iran TSE)",
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
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "application/json",
                    },
                )
                with urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                if not raw:
                    raise ShareholderProviderError(f"پاسخ خالی: {url}")
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
        raise ShareholderProviderError(f"دریافت سهامداران ناموفق: {url}") from last_error

    @staticmethod
    def _num(row: dict, *keys: str) -> float | None:
        for k in keys:
            v = row.get(k)
            if v in (None, ""):
                continue
            try:
                return float(str(v).replace(",", ""))
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _str(row: dict, *keys: str) -> str | None:
        for k in keys:
            v = row.get(k)
            if v not in (None, ""):
                return str(v).strip()
        return None

    def fetch_changes(self, *, only_increase: bool = False) -> list[ShareHolderChange]:
        """
        فهرست تغییرات سهامداران عمده (کل بازار / اخیر).

        معادل صفحه: main.tsetmc.com/ShareHolderChanges
        API: /Shareholder/GetShareHolderChanges/false|true
        """
        flag = "true" if only_increase else "false"
        payload = self._get_json(f"/api/Shareholder/GetShareHolderChanges/{flag}")
        rows = payload.get("shareHoldersChanges") or payload.get("shareHolderChanges") or []
        if isinstance(payload, list):
            rows = payload
        if not isinstance(rows, list):
            rows = []

        out: list[ShareHolderChange] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            before = self._num(row, "numberOfSharesBefore", "sharesBefore", "c1")
            after = self._num(row, "numberOfSharesAfter", "sharesAfter", "c2")
            change = self._num(row, "numberOfSharesChange", "sharesChange", "change")
            if change is None and before is not None and after is not None:
                change = after - before
            out.append(
                ShareHolderChange(
                    symbol=self._str(row, "lVal18AFC", "symbol", "lVal18"),
                    company_name=self._str(row, "lVal30", "companyName"),
                    holder_name=self._str(row, "shareHolderName", "holderName", "name"),
                    ins_code=self._str(row, "insCode", "instrumentInsCode"),
                    share_holder_id=self._str(row, "shareHolderId", "shareHolderShareID", "id"),
                    shares_before=before,
                    shares_after=after,
                    shares_change=change,
                    percent_before=self._num(row, "percentBefore", "perBefore"),
                    percent_after=self._num(row, "percentAfter", "perAfter"),
                    percent_change=self._num(row, "percentChange", "perChange"),
                    date=self._str(row, "dEven", "date", "changeDate"),
                    raw=row,
                )
            )
        return out

    def resolve_ins_code(self, ticker: str) -> str:
        path = f"/api/Instrument/GetInstrumentSearch/{quote(ticker)}"
        payload = self._get_json(path)
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
        raise ShareholderProviderError(f"نماد پیدا نشد: {ticker}")

    def fetch_holders(self, ticker: str) -> list[ShareHolder]:
        """آخرین سهامداران عمده یک نماد."""
        ins = self.resolve_ins_code(ticker)
        payload = self._get_json(f"/api/Shareholder/GetInstrumentShareHolderLast/{ins}")
        rows = payload.get("shareHolder") or []
        if not isinstance(rows, list):
            rows = []
        out: list[ShareHolder] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            out.append(
                ShareHolder(
                    name=self._str(row, "shareHolderName", "name") or "",
                    shares=self._num(row, "numberOfShares", "shares", "c1"),
                    percent=self._num(row, "perOfShares", "percent", "per"),
                    change=self._num(row, "change", "shareChange"),
                    share_holder_id=self._str(row, "shareHolderId", "shareHolderShareID", "id"),
                    raw=row,
                )
            )
        return out

    def fetch_holder_history(
        self, ticker: str, share_holder_id: str, days: int = 90
    ) -> list[dict[str, Any]]:
        ins = self.resolve_ins_code(ticker)
        payload = self._get_json(
            f"/api/Shareholder/GetShareHolderHistory/{ins}/{share_holder_id}/{days}"
        )
        rows = payload.get("shareHolder") or []
        return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []
