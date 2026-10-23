"""درایور واقعی TSETMC برای دادهٔ حقیقی/حقوقی (اسمارت‌مانی) — بدون هیچ دادهٔ ساختگی.

منبع‌ها (همه با شواهد خام در docs/sources/evidence/2026-10-24/):
- شناسهٔ نماد: ``cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/{ticker}`` (VERIFIED — فایل 11)
- snapshot بازارکامل حقیقی/حقوقی آخرین روز معاملاتی:
  ``old.tsetmc.com/tsev2/data/ClientTypeAll.aspx`` (VERIFIED — فایل‌های 12 و 13؛ پارامتر t نادیده گرفته می‌شود)
- تاریخچهٔ بستهٔ روزانه برای انتساب تاریخ snapshot و محاسبهٔ VWAP واقعی:
  ``cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{insCode}/{limit}`` (VERIFIED — فایل 10)

گیت راستی‌آزمایی (سیاست «فقط دادهٔ واقعی» — CR-20261024-002):
- ساختار ردیف: ``insCode, iBuyCount, lBuyCount, iBuyVol, lBuyVol, iSellCount, lSellCount, iSellVol, lSellVol``
- هر ردیف باید اتحاد «مجموع خرید = مجموع فروش» را پاس کند ( invariant تأییدشده در شواهد)؛ وگرنه رد و شمرده می‌شود.
- متریک‌های مشتق‌شده (سرانه‌ها، سهم حقوقی، خرید خالص حقوقی) فقط زمانی محاسبه می‌شوند که حجم snapshot
  با حجم یکی از روزهای بستهٔ واقعی (qTotTran5J) در حد tolerant تطبیق کند و تاریخ روز مشخص شود؛
  در غیر این صورت data_quality="partial" و هیچ عددی حدس زده نمی‌شود.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from arya.providers.shareholders.base import (
    FLOW_KEYS,
    InstrumentIdentity,
    ShareholderDataProvider,
    ShareholderDataProviderError,
    ShareholderProviderRegistry,
    ShareholderSnapshotRow,
    empty_flow,
)


@dataclass
class _Attribution:
    date: int | None
    vwap: float | None
    relative_diff: float | None
    days_checked: int


@ShareholderProviderRegistry.register("tsetmc_client_type")
class TsetmcClientTypeProvider(ShareholderDataProvider):
    """دریافت دادهٔ واقعی حقیقی/حقوقی از snapshot بازارکامل TSETMC + گیت انتساب تاریخ."""

    name = "tsetmc_client_type"
    _default_cdn = "https://cdn.tsetmc.com"
    _default_old = "https://old.tsetmc.com"
    _snapshot_path = "/tsev2/data/ClientTypeAll.aspx"

    def __init__(
        self,
        base_url_cdn: str | None = None,
        base_url_old: str | None = None,
        timeout: float = 15.0,
        retries: int = 3,
        backoff_seconds: float = 0.5,
        snapshot_volume_tolerance: float = 0.05,
        user_agent: str = "ARYA-AI-Trader/0.1 (+https://github.com/ziya1346/ARYA_AI_TRADER)",
    ):
        self.base_url_cdn = (base_url_cdn or self._default_cdn).rstrip("/")
        self.base_url_old = (base_url_old or self._default_old).rstrip("/")
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.snapshot_volume_tolerance = max(0.0, snapshot_volume_tolerance)
        self.user_agent = user_agent

    # ─────────────────────────── لایهٔ HTTP ───────────────────────────

    def _fetch(self, url: str, expect: str) -> str:
        """درخواست واقعی با timeout/retry؛ خروجی فقط متن واقعی سرور."""
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "*/*"})
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                if not raw:
                    raise ShareholderDataProviderError(f"پاسخ خالی از TSETMC: {url}")
                text = raw.decode("utf-8-sig", errors="replace")
                if expect == "json" and not text.lstrip().startswith("{"):
                    raise ShareholderDataProviderError("پاسخ TSETMC JSON معتبر نیست یا دسترسی مسدود شده است")
                return text
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (URLError, TimeoutError, ShareholderDataProviderError) as exc:
                last_error = exc
            if attempt < self.retries - 1:
                time.sleep(self.backoff_seconds * (2**attempt))
        raise ShareholderDataProviderError(f"دریافت داده از TSETMC ناموفق بود: {url}") from last_error

    def _get_json(self, url: str) -> dict:
        try:
            payload = json.loads(self._fetch(url, expect="json"))
        except json.JSONDecodeError as exc:
            raise ShareholderDataProviderError(f"پارس JSON ناموفق بود: {url}") from exc
        if not isinstance(payload, dict):
            raise ShareholderDataProviderError(f"ساختار پاسخ نامعتبر است: {url}")
        return payload

    @staticmethod
    def _unwrap(payload: dict, key: str) -> list[dict]:
        value = payload.get(key, [])
        if isinstance(value, dict):
            value = value.get("items", value.get("data", []))
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    # ─────────────────────── شناسهٔ نماد (cdn — VERIFIED) ───────────────────────

    def resolve_ticker(self, ticker: str) -> InstrumentIdentity:
        url = f"{self.base_url_cdn}/api/Instrument/GetInstrumentSearch/{quote(ticker)}"
        rows = self._unwrap(self._get_json(url), "instrumentSearch")
        exact: dict | None = None
        for row in rows:
            if str(row.get("lVal18AFC") or "").strip() == ticker:
                exact = row
                break
        if exact is None and rows:
            exact = rows[0]
        if exact is None or not exact.get("insCode"):
            raise ShareholderDataProviderError(f"نماد در TSETMC پیدا نشد: {ticker}")
        return InstrumentIdentity(
            ticker=ticker,
            name=exact.get("lVal30"),
            ins_code=str(exact["insCode"]),
            old_ins_code=str(exact["insCode3"]) if exact.get("insCode3") else None,
        )

    # ──────────────── snapshot بازارکامل (old.tsetmc — VERIFIED) ────────────────

    def fetch_market_snapshot(self) -> tuple[dict[str, ShareholderSnapshotRow], int]:
        """پارس snapshot واقعی؛ خروجی: {insCode: ردیف} + تعداد ردیف‌های ردشده."""
        url = f"{self.base_url_old}{self._snapshot_path}"
        text = self._fetch(url, expect="text")
        rows: dict[str, ShareholderSnapshotRow] = {}
        rejected = 0
        for chunk in text.split(";"):
            chunk = chunk.strip().strip("\r\n")
            if not chunk:
                continue
            fields = chunk.split(",")
            if len(fields) != 9:
                rejected += 1
                continue
            try:
                values = [int(float(v)) for v in fields[1:]]
                row = ShareholderSnapshotRow(fields[0].strip(), *values)
            except (TypeError, ValueError):
                rejected += 1
                continue
            # گیت ساختاری تأییدشده در شواهد: مجموع خرید باید برابر مجموع فروش باشد
            if row.total_buy_volume != row.total_sell_volume:
                rejected += 1
                continue
            rows[row.ins_code] = row
        if not rows:
            raise ShareholderDataProviderError("snapshot حقیقی/حقوقی خالی یا نامعتبر بود")
        return rows, rejected

    # ──────────────── تاریخچهٔ بستهٔ واقعی (cdn — VERIFIED) ────────────────

    def fetch_closing_history(self, ins_code: str, days: int) -> list[dict]:
        if days <= 0:
            raise ValueError("days باید بزرگ‌تر از صفر باشد")
        url = f"{self.base_url_cdn}/api/ClosingPrice/GetClosingPriceDailyList/{ins_code}/{int(days)}"
        return self._unwrap(self._get_json(url), "closingPriceDaily")

    def _attribute_snapshot_date(self, snapshot_total_volume: int, closing_rows: list[dict]) -> _Attribution:
        """انتساب تاریخ snapshot با تطبیق حجم با روزهای بستهٔ واقعی؛ بدون تطبیق = None."""
        best: tuple[float, dict] | None = None
        checked = 0
        for row in closing_rows:
            volume = float(row.get("qTotTran5J") or 0)
            if volume <= 0:
                continue
            checked += 1
            diff = abs(snapshot_total_volume - volume) / volume
            if best is None or diff < best[0]:
                best = (diff, row)
        if best is not None and best[0] <= self.snapshot_volume_tolerance:
            row = best[1]
            volume = float(row["qTotTran5J"])
            vwap = float(row.get("qTotCap") or 0) / volume if volume > 0 else None
            return _Attribution(date=int(row["dEven"]), vwap=vwap, relative_diff=best[0], days_checked=checked)
        return _Attribution(
            date=None,
            vwap=None,
            relative_diff=best[0] if best is not None else None,
            days_checked=checked,
        )

    # ─────────────────────────── API کانونی ───────────────────────────

    def _locate_row(self, identity: InstrumentIdentity, snapshot: dict[str, ShareholderSnapshotRow]):
        if identity.old_ins_code and identity.old_ins_code in snapshot:
            return snapshot[identity.old_ins_code], "old_ins_code"
        if identity.ins_code in snapshot:
            return snapshot[identity.ins_code], "ins_code"
        return None, None

    def fetch_shareholder_flow(self, ticker: str, days: int = 30) -> dict:
        """خروجی dict با دقیقاً کلیدهای FLOW_KEYS — سازگار با ShareholderFlowMetrics(**flow).

        - data_quality="usable": snapshot واقعی + انتساب موفق تاریخ به یک روز بستهٔ واقعی
        - data_quality="partial": دادهٔ واقعی هست ولی تاریخ snapshot قابل انتساب نیست → هیچ عدد مشتق‌شده‌ای تولید نمی‌شود
        - data_quality="missing": نماد در snapshot امروز نیست (مشاهدهٔ واقعیِ نبود داده)
        """
        identity = self.resolve_ticker(ticker)
        snapshot, _rejected = self.fetch_market_snapshot()
        row, matched_by = self._locate_row(identity, snapshot)
        if row is None:
            return empty_flow("missing")
        closing_rows = self.fetch_closing_history(identity.ins_code, days)
        attribution = self._attribute_snapshot_date(row.total_buy_volume, closing_rows)
        if attribution.date is None or not attribution.vwap:
            # سیاست «فقط دادهٔ واقعی»: بدون انتساب تاریخ، هیچ متریک مشتق‌شده‌ای حدس زده نمی‌شود
            return empty_flow("partial")
        flow = empty_flow("usable")
        total_buy = float(row.total_buy_volume)
        if total_buy > 0:
            flow["legal_buy_share"] = round(row.legal_buy_volume / total_buy, 6)
        if row.individual_buy_count > 0:
            flow["individual_avg_buy_value"] = round(row.individual_buy_volume * attribution.vwap / row.individual_buy_count, 2)
        if row.individual_sell_count > 0:
            flow["individual_avg_sell_value"] = round(
                row.individual_sell_volume * attribution.vwap / row.individual_sell_count, 2
            )
        flow["legal_net_buy_value"] = round(
            (row.legal_buy_volume - row.legal_sell_volume) * attribution.vwap, 2
        )
        # shareholder_count_series نیازمند تاریخچهٔ تاریخ‌دار است؛ تجمیع آن مسئولیت daily-ingest است
        # (بدون تاریخ‌گذاری واقعی، سری ساختگی محسوب می‌شود و تولیدش ممنوع است)
        flow["shareholder_count_series"] = None
        assert set(flow) == set(FLOW_KEYS)
        return flow

    def inspect_snapshot(self, ticker: str, days: int = 30) -> dict:
        """دادهٔ خام واقعی + تشخیص انتساب؛ هیچ متریک مشتق‌شده‌ای برنمی‌گرداند."""
        identity = self.resolve_ticker(ticker)
        snapshot, rejected = self.fetch_market_snapshot()
        row, matched_by = self._locate_row(identity, snapshot)
        result: dict = {
            "ticker": ticker,
            "name": identity.name,
            "ins_code": identity.ins_code,
            "old_ins_code": identity.old_ins_code,
            "matched_by": matched_by,
            "snapshot_rows_total": len(snapshot),
            "snapshot_rows_rejected": rejected,
            "row": None,
            "attribution": None,
        }
        if row is not None:
            closing_rows = self.fetch_closing_history(identity.ins_code, days)
            attribution = self._attribute_snapshot_date(row.total_buy_volume, closing_rows)
            result["row"] = {
                "ins_code": row.ins_code,
                "individual_buy_count": row.individual_buy_count,
                "legal_buy_count": row.legal_buy_count,
                "individual_buy_volume": row.individual_buy_volume,
                "legal_buy_volume": row.legal_buy_volume,
                "individual_sell_count": row.individual_sell_count,
                "legal_sell_count": row.legal_sell_count,
                "individual_sell_volume": row.individual_sell_volume,
                "legal_sell_volume": row.legal_sell_volume,
                "total_buy_volume": row.total_buy_volume,
            }
            result["attribution"] = {
                "date": attribution.date,
                "relative_diff": attribution.relative_diff,
                "tolerance": self.snapshot_volume_tolerance,
                "days_checked": attribution.days_checked,
                "vwap": attribution.vwap,
                "verdict": "attributed" if attribution.date is not None else "unattributable",
            }
        return result
