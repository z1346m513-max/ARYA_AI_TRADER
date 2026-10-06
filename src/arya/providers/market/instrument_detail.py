"""
جزئیات نماد — معادل صفحه:
  https://old.tsetmc.com/Loader.aspx?ParTree=151311&i={InsCode}
  https://main.tsetmc.com/InstInfo/{InsCode}

API CDN (الگوی 5j9/tsetmc و pytse-client):
  GET /api/Instrument/GetInstrumentSearch/{Query}
  GET /api/Instrument/GetInstrumentInfo/{InsCode}
  GET /api/ClosingPrice/GetClosingPriceInfo/{InsCode}
  GET /api/BestLimits/{InsCode}   (اختیاری — صف)
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class InstrumentDetailError(RuntimeError):
    pass


@dataclass
class InstrumentDetail:
    """اسنپ‌شات قابل‌نمایش صفحه جزئیات نماد."""

    ticker: str
    ins_code: str
    name: str | None = None
    name_en: str | None = None
    isin: str | None = None
    cisin: str | None = None
    market_title: str | None = None  # flowTitle
    board_title: str | None = None  # cgrValCotTitle
    sector: str | None = None
    sector_code: str | None = None
    state: str | None = None  # مجاز / ممنوع / ...
    total_shares: float | None = None  # zTitad
    base_volume: float | None = None
    free_float_pct: float | None = None  # kAjCapValCpsIdx
    eps: float | None = None
    sector_pe: float | None = None
    pe: float | None = None
    psr: float | None = None
    last_price: float | None = None
    close_price: float | None = None
    yesterday_price: float | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    price_change: float | None = None
    volume: float | None = None
    value: float | None = None
    trade_count: float | None = None
    min_week: float | None = None
    max_week: float | None = None
    min_year: float | None = None
    max_year: float | None = None
    threshold_max: float | None = None
    threshold_min: float | None = None
    page_url_old: str | None = None
    page_url_new: str | None = None
    best_limits: list[dict[str, Any]] = field(default_factory=list)
    raw_info: dict[str, Any] | None = None
    raw_price: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw_info", None)
        d.pop("raw_price", None)
        return d


class InstrumentDetailProvider:
    name = "instrument_detail"
    _default_base = "https://cdn.tsetmc.com"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 15.0,
        retries: int = 3,
        backoff_seconds: float = 0.5,
        user_agent: str = "ARYA-AI-Trader/0.2 (+instrument-detail; Iran TSE)",
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
                    raise InstrumentDetailError(f"پاسخ خالی: {url}")
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
        raise InstrumentDetailError(f"جزئیات نماد ناموفق: {url}") from last_error

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
        raise InstrumentDetailError(f"نماد پیدا نشد: {ticker}")

    @staticmethod
    def _num(data: Any, *keys: str) -> float | None:
        if not isinstance(data, dict):
            return None
        for k in keys:
            v = data.get(k)
            if v in (None, ""):
                continue
            try:
                return float(str(v).replace(",", "").strip())
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _str(data: Any, *keys: str) -> str | None:
        if not isinstance(data, dict):
            return None
        for k in keys:
            v = data.get(k)
            if v not in (None, ""):
                return str(v).strip()
        return None

    def fetch(self, ticker: str, *, with_orderbook: bool = True) -> InstrumentDetail:
        """جمع‌آوری اطلاعات صفحه جزئیات نماد."""
        ins = self.resolve_ins_code(ticker)

        info_payload = self._get_json(f"/api/Instrument/GetInstrumentInfo/{ins}")
        info = info_payload.get("instrumentInfo") or {}
        if not isinstance(info, dict):
            info = {}

        price_payload = self._get_json(f"/api/ClosingPrice/GetClosingPriceInfo/{ins}")
        price = price_payload.get("closingPriceInfo") or {}
        if not isinstance(price, dict):
            price = {}

        state_obj = price.get("instrumentState") if isinstance(price.get("instrumentState"), dict) else {}
        eps_obj = info.get("eps") if isinstance(info.get("eps"), dict) else {}
        sector_obj = info.get("sector") if isinstance(info.get("sector"), dict) else {}
        thr_obj = info.get("staticThreshold") if isinstance(info.get("staticThreshold"), dict) else {}

        close = self._num(price, "pClosing", "pc")
        yest = self._num(price, "priceYesterday", "py")
        last = self._num(price, "pDrCotVal", "pl", "last")
        eps_val = self._num(eps_obj, "estimatedEPS", "epsValue", "eps")
        pe = None
        if close and eps_val and eps_val != 0:
            pe = round(close / eps_val, 4)

        free_float = self._num(info, "kAjCapValCpsIdx")

        best_limits: list[dict[str, Any]] = []
        if with_orderbook:
            try:
                bl_payload = self._get_json(f"/api/BestLimits/{ins}")
                rows = bl_payload.get("bestLimits") or []
                if isinstance(rows, list):
                    best_limits = [r for r in rows if isinstance(r, dict)][:10]
            except InstrumentDetailError:
                best_limits = []

        detail = InstrumentDetail(
            ticker=self._str(info, "lVal18AFC", "lVal18") or ticker,
            ins_code=ins,
            name=self._str(info, "lVal30"),
            name_en=self._str(info, "lVal18"),
            isin=self._str(info, "instrumentID", "cIsin"),
            cisin=self._str(info, "cIsin"),
            market_title=self._str(info, "flowTitle"),
            board_title=self._str(info, "cgrValCotTitle"),
            sector=self._str(sector_obj, "lSecVal"),
            sector_code=self._str(sector_obj, "cSecVal"),
            state=self._str(state_obj, "cEtavalTitle", "cEtaval"),
            total_shares=self._num(info, "zTitad"),
            base_volume=self._num(info, "baseVol"),
            free_float_pct=free_float,
            eps=eps_val,
            sector_pe=self._num(eps_obj, "sectorPE"),
            pe=pe,
            psr=self._num(eps_obj, "psr"),
            last_price=last,
            close_price=close,
            yesterday_price=yest,
            open_price=self._num(price, "priceFirst", "pf"),
            high_price=self._num(price, "priceMax"),
            low_price=self._num(price, "priceMin"),
            price_change=self._num(price, "priceChange"),
            volume=self._num(price, "qTotTran5J"),
            value=self._num(price, "qTotCap"),
            trade_count=self._num(price, "zTotTran"),
            min_week=self._num(info, "minWeek"),
            max_week=self._num(info, "maxWeek"),
            min_year=self._num(info, "minYear"),
            max_year=self._num(info, "maxYear"),
            threshold_max=self._num(thr_obj, "psGelStaMax"),
            threshold_min=self._num(thr_obj, "psGelStaMin"),
            page_url_old=f"https://old.tsetmc.com/Loader.aspx?ParTree=151311&i={ins}",
            page_url_new=f"https://main.tsetmc.com/InstInfo/{ins}",
            best_limits=best_limits,
            raw_info=info,
            raw_price=price,
        )
        return detail
