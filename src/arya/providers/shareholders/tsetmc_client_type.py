"""درایور واقعی TSETMC برای دادهٔ حقیقی/حقوقی — یکپارچه با قرارداد فعلی مخزن.

یکپارچه‌سازی (CR-20261029-001 به دستور مالک، پس از بازبینی چهار-ایتمی پیش از ادغام):
- قرارداد: ``arya.providers.shareholder_base.ShareholderDataProvider`` (همان رجیستری مشترک
  با درایورهای ``mock`` و ``client_type_all``؛ مسیر قرارداد تکراری حذف شد)
- خروجی ``fetch_shareholder_flow``: مدل فعلی ``ShareholderFlowMetrics`` (نه dict)؛
  ``shareholder_count_series`` همیشه tuple و در نبود تاریخچهٔ تاریخ‌دار **صریحاً خالی** ``()`` است.
- متریک‌های پولی (ریال) فقط با VWAP واقعی روزِ منتسب ساخته می‌شوند؛ درایور ``client_type_all``
  مقادیر حجمی می‌دهد — تفاوت معناشناسی در notes هر خروجی ثبت می‌شود.

سه‌لایهٔ گیت انتساب تاریخ snapshot (پاسخ به ایراد مالک: «شباهت حجم، اثبات تاریخ نیست»):
  لایهٔ ۱ — یکتایی تطبیق: اگر بیش از یک روز بستهٔ واقعی در تلورانس حجم باشند ⇒ «مبهم» ⇒ عدم انتساب.
  لایهٔ ۲ — باند VWAP: VWAP روزِ نامزد باید در ``[priceMin, priceMax]`` همان روز بیفتد
            (برای هر روز معاملاتی واقعی به‌طور ریاضی برقرار است؛ نقض آن یعنی ردیف بسته خراب است).
  لایهٔ ۳ — تأیید مستقل چند-نمادی: ``confirm_snapshot_date`` چند نماد را مستقلاً انتساب می‌دهد و
            فقط با توافق کافی تاریخ را تأیید می‌کند؛ ``fetch_shareholder_flow(confirmed_date=...)``
            هر خروجیِ ناسازگار با تاریخِ تأییدشده را به partial تنزل می‌دهد.

منابع (همه VERIFIED با شواهد خام فاز ۰ — CR-20261024-002 روی برنچ مستندات):
- شناسهٔ نماد: ``cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/{ticker}``
  (insCode جدید + insCode3 قدیمی؛ ردیف‌های snapshot با کد قدیمی کلید خورده‌اند — فایل شواهد 13)
- snapshot بازارکامل آخرین روز معاملاتی: ``old.tsetmc.com/tsev2/data/ClientTypeAll.aspx``
  (پارامتر t نادیده گرفته می‌شود؛ snapshot کل بازار است — فایل‌های شواهد 12/13)
- تاریخچهٔ بستهٔ روزانه: ``cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{insCode}/{limit}``
  (فیلدهای واقعی: dEven, priceMin, priceMax, qTotTran5J, qTotCap, ... — فایل شواهد 10)

سیاست «فقط دادهٔ واقعی»: هیچ عدد ساختگی، تاریخ حدسی یا سری ساختگی تولید نمی‌شود؛
خطای شبکه/پارس به data_quality="missing" با note صریح تبدیل می‌شود (هم‌الگوی درایور client_type_all)،
و «مشاهدهٔ واقعیِ نبود نماد» نیز missing است — اما با note متمایز.
"""
from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from arya.models.shareholders import ShareholderFlowMetrics
from arya.providers.shareholder_base import ShareholderDataProvider, ShareholderProviderRegistry


class TsetmcClientTypeError(RuntimeError):
    """خطای لایهٔ دادهٔ درایور واقعی (شبکه، پاسخ نامعتبر، نقض گیت ساختاری)."""


@dataclass(frozen=True)
class InstrumentIdentity:
    """هویت واقعی نماد از جست‌وجوی رسمی cdn (شواهد فاز ۰: فایل 11)."""

    ticker: str
    name: str | None
    ins_code: str             # کد جدید — کلید سرویس‌های cdn
    old_ins_code: str | None  # insCode3 — کلید ردیف‌های snapshot (شواهد: فایل 13)


@dataclass(frozen=True)
class ShareholderSnapshotRow:
    """یک ردیف واقعی snapshot حقیقی/حقوقی (قالب ۹ فیلدی تأییدشده در شواهد فاز ۰)."""

    ins_code: str
    individual_buy_count: int
    legal_buy_count: int
    individual_buy_volume: int
    legal_buy_volume: int
    individual_sell_count: int
    legal_sell_count: int
    individual_sell_volume: int
    legal_sell_volume: int

    @property
    def total_buy_volume(self) -> int:
        return self.individual_buy_volume + self.legal_buy_volume

    @property
    def total_sell_volume(self) -> int:
        return self.individual_sell_volume + self.legal_sell_volume


@dataclass(frozen=True)
class _Attribution:
    """نتیجهٔ تلاش برای انتساب تاریخ snapshot به یک روز بستهٔ واقعی."""

    date: int | None
    vwap: float | None
    relative_diff: float | None
    second_best_diff: float | None
    days_checked: int
    rejected_reason: str | None


@ShareholderProviderRegistry.register("tsetmc_client_type")
class TsetmcClientTypeProvider(ShareholderDataProvider):
    """دریافت دادهٔ واقعی حقیقی/حقوقی از snapshot بازارکامل TSETMC + گیت سه‌لایهٔ انتساب تاریخ."""

    name = "tsetmc_client_type"
    _default_cdn = "https://cdn.tsetmc.com"
    _default_old = "https://old.tsetmc.com"
    _snapshot_path = "/tsev2/data/ClientTypeAll.aspx"

    def __init__(
        self,
        base_url_cdn: str | None = None,
        base_url_old: str | None = None,
        timeout: float = 20.0,
        retries: int = 3,
        backoff_seconds: float = 0.5,
        snapshot_volume_tolerance: float = 0.05,
        user_agent: str = "ARYA-AI-Trader/0.1 (+https://github.com/z1346m513-max/ARYA_AI_TRADER)",
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
                    raise TsetmcClientTypeError(f"پاسخ خالی از TSETMC: {url}")
                text = raw.decode("utf-8-sig", errors="replace")
                if expect == "json" and not text.lstrip().startswith("{"):
                    raise TsetmcClientTypeError("پاسخ TSETMC JSON معتبر نیست یا دسترسی مسدود شده است")
                return text
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (URLError, TimeoutError, TsetmcClientTypeError) as exc:
                last_error = exc
            if attempt < self.retries - 1:
                time.sleep(self.backoff_seconds * (2**attempt))
        raise TsetmcClientTypeError(f"دریافت داده از TSETMC ناموفق بود: {url}") from last_error

    def _get_json(self, url: str) -> dict:
        try:
            payload = json.loads(self._fetch(url, expect="json"))
        except json.JSONDecodeError as exc:
            raise TsetmcClientTypeError(f"پارس JSON ناموفق بود: {url}") from exc
        if not isinstance(payload, dict):
            raise TsetmcClientTypeError(f"ساختار پاسخ نامعتبر است: {url}")
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
            if str(row.get("lVal18AFC") or row.get("lVal18") or "").strip() == ticker:
                exact = row
                break
        if exact is None and rows:
            exact = rows[0]
        if exact is None or not exact.get("insCode"):
            raise TsetmcClientTypeError(f"نماد در TSETMC پیدا نشد: {ticker}")
        return InstrumentIdentity(
            ticker=ticker,
            name=exact.get("lVal30"),
            ins_code=str(exact["insCode"]),
            old_ins_code=str(exact["insCode3"]) if exact.get("insCode3") else None,
        )

    # ──────────────── snapshot بازارکامل (old.tsetmc — VERIFIED) ────────────────

    def fetch_market_snapshot(self) -> tuple[dict[str, ShareholderSnapshotRow], int]:
        """پارس snapshot واقعی؛ خروجی: {insCode قدیمی: ردیف} + تعداد ردیف‌های ردشده.

        گیت ساختاری (تأییدشده در شواهد فاز ۰): مجموع خرید باید برابر مجموع فروش باشد.
        """
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
            if row.total_buy_volume != row.total_sell_volume:
                rejected += 1
                continue
            rows[row.ins_code] = row
        if not rows:
            raise TsetmcClientTypeError("snapshot حقیقی/حقوقی خالی یا نامعتبر بود")
        return rows, rejected

    # ──────────────── تاریخچهٔ بستهٔ واقعی (cdn — VERIFIED) ────────────────

    def fetch_closing_history(self, ins_code: str, days: int) -> list[dict]:
        if days <= 0:
            raise ValueError("days باید بزرگ‌تر از صفر باشد")
        url = f"{self.base_url_cdn}/api/ClosingPrice/GetClosingPriceDailyList/{ins_code}/{int(days)}"
        return self._unwrap(self._get_json(url), "closingPriceDaily")

    def _attribute_snapshot_date(
        self, snapshot_total_volume: int, closing_rows: list[dict]
    ) -> _Attribution:
        """انتساب تاریخ با گیت سه‌لایه؛ هر شکست دلیل صریح دارد و هیچ‌گاه حدس نمی‌زند.

        لایهٔ ۱: بهترین تطبیق باید در تلورانس باشد «و» یکتا باشد (دومین تطبیق خارج از تلورانس).
        لایهٔ ۲: VWAP روزِ نامزد باید در باند قیمتی همان روز باشد.
        """
        scored: list[tuple[float, dict]] = []
        for row in closing_rows:
            volume = float(row.get("qTotTran5J") or 0)
            if volume <= 0:
                continue
            diff = abs(snapshot_total_volume - volume) / volume
            scored.append((diff, row))
        if not scored:
            return _Attribution(None, None, None, None, 0, "no_closing_rows_with_volume")
        scored.sort(key=lambda pair: pair[0])
        best_diff, best_row = scored[0]
        second_diff = scored[1][0] if len(scored) > 1 else None
        checked = len(scored)
        if best_diff > self.snapshot_volume_tolerance:
            return _Attribution(None, None, best_diff, second_diff, checked, "no_volume_match_within_tolerance")
        if second_diff is not None and second_diff <= self.snapshot_volume_tolerance:
            # لایهٔ ۱ — شباهت حجم به یک روزِ دیگر هم می‌خورد؛ انتخاب «نزدیک‌ترین» حدس است، نه احراز
            return _Attribution(None, None, best_diff, second_diff, checked, "ambiguous_volume_match")
        volume = float(best_row["qTotTran5J"])
        cap = float(best_row.get("qTotCap") or 0)
        vwap = (cap / volume) if volume > 0 else None
        if not vwap or cap <= 0:
            return _Attribution(None, None, best_diff, second_diff, checked, "invalid_vwap_data")
        pmin = float(best_row.get("priceMin") or 0)
        pmax = float(best_row.get("priceMax") or 0)
        if pmin > 0 and pmax > 0 and not (pmin - 1e-9 <= vwap <= pmax + 1e-9):
            # لایهٔ ۲ — VWAP واقعی هیچ روزی نمی‌تواند خارج از باند قیمتی همان روز باشد
            return _Attribution(None, None, best_diff, second_diff, checked, "vwap_outside_day_price_band")
        return _Attribution(int(best_row["dEven"]), vwap, best_diff, second_diff, checked, None)

    # ──────────── تأیید مستقل چند-نمادی (لایهٔ ۳ — همه endpointها VERIFIED) ────────────

    def confirm_snapshot_date(self, tickers: tuple[str, ...] | list[str], days: int = 30, min_agreement: float = 0.6) -> dict:
        """اعتبارسنجی مستقل تاریخ snapshot با توافق چند نماد مستقل.

        snapshot کل بازار است؛ پس همهٔ ردیف‌ها به «یک» روز تعلق دارند. اگر انتساب‌های مستقلِ
        چند نماد روی یک تاریخ توافق نکنند، تاریخ قابل احراز نیست (ریشهٔ احتمالی: تطبیق اشتباه حجم).
        خروجی شامل per_ticker (تاریخ/دلیل هر نماد)، agreed_date و agreement_ratio است؛
        هیچ متریک قیمتی/امتیازی اینجا ساخته نمی‌شود — فقط احراز تاریخ با دادهٔ واقعی.
        """
        per_ticker: dict[str, dict] = {}
        dates: list[int] = []
        for ticker in tickers:
            try:
                identity = self.resolve_ticker(ticker)
                snapshot, _rejected = self.fetch_market_snapshot()
                row, matched_by = self._locate_row(identity, snapshot)
                if row is None:
                    per_ticker[ticker] = {"date": None, "verdict": "missing", "matched_by": None}
                    continue
                closing_rows = self.fetch_closing_history(identity.ins_code, days)
                att = self._attribute_snapshot_date(row.total_buy_volume, closing_rows)
                if att.date is not None:
                    dates.append(att.date)
                    per_ticker[ticker] = {
                        "date": att.date,
                        "verdict": "attributed",
                        "matched_by": matched_by,
                        "relative_diff": att.relative_diff,
                    }
                else:
                    per_ticker[ticker] = {"date": None, "verdict": att.rejected_reason or "unattributable"}
            except TsetmcClientTypeError as exc:
                per_ticker[ticker] = {"date": None, "verdict": f"error: {exc}"}
        attributed_count = len(dates)
        agreed_date: int | None = None
        agreement_ratio = 0.0
        if dates and tickers:
            top_date, top_count = Counter(dates).most_common(1)[0]
            agreement_ratio = top_count / len(tickers)
            if agreement_ratio >= min_agreement:
                agreed_date = top_date
        return {
            "per_ticker": per_ticker,
            "agreed_date": agreed_date,
            "agreement_ratio": round(agreement_ratio, 4),
            "attributed_count": attributed_count,
            "sample_size": len(tickers),
            "min_agreement": min_agreement,
        }

    # ─────────────────────────── API کانونی ───────────────────────────

    def _locate_row(self, identity: InstrumentIdentity, snapshot: dict[str, ShareholderSnapshotRow]):
        """کلید ردیف‌ها = کد قدیمی (شواهد فاز ۰)؛ کد جدید فقط به‌عنوان fallback."""
        if identity.old_ins_code and identity.old_ins_code in snapshot:
            return snapshot[identity.old_ins_code], "old_ins_code"
        if identity.ins_code in snapshot:
            return snapshot[identity.ins_code], "ins_code"
        return None, None

    def fetch_shareholder_flow(
        self, ticker: str, days: int = 5, confirmed_date: int | None = None
    ) -> ShareholderFlowMetrics:
        """خروجی: مدل فعلی ShareholderFlowMetrics (سازگار کامل با ShareChangeAnalyzer).

        - data_quality="usable": snapshot واقعی + انتساب یکتای تاریخ + باند VWAP
          (+ سازگاری با confirmed_date در صورت ارائه) ⇒ متریک‌های ریالی با VWAP واقعی روز
        - data_quality="partial": دادهٔ واقعی هست ولی تاریخ قابل احراز نیست ⇒ همهٔ متریک‌ها None، سری ()
        - data_quality="missing": نماد یافت نشد / در snapshot نیست / شبکه یا پاسخ نامعتبر ⇒ note صریح
        """
        ticker = (ticker or "").strip()
        if not ticker:
            return ShareholderFlowMetrics(
                ticker="", data_quality="missing", source=self.name, notes=("empty ticker",)
            )
        try:
            identity = self.resolve_ticker(ticker)
            snapshot, rejected = self.fetch_market_snapshot()
        except TsetmcClientTypeError as exc:
            return ShareholderFlowMetrics(
                ticker=ticker, data_quality="missing", source=self.name, notes=(str(exc),)
            )
        row, matched_by = self._locate_row(identity, snapshot)
        if row is None:
            return ShareholderFlowMetrics(
                ticker=ticker,
                data_quality="missing",
                source=self.name,
                notes=(
                    f"insCode={identity.ins_code} (old={identity.old_ins_code}) در snapshot کل بازار نیست",
                    f"snapshot_rows={len(snapshot)} rejected_rows={rejected}",
                ),
            )
        try:
            closing_rows = self.fetch_closing_history(identity.ins_code, days)
        except TsetmcClientTypeError as exc:
            return ShareholderFlowMetrics(
                ticker=ticker,
                data_quality="partial",
                source=self.name,
                notes=(
                    f"تاریخچهٔ بسته در دسترس نیست: {exc}",
                    f"insCode={identity.ins_code}",
                ),
            )
        att = self._attribute_snapshot_date(row.total_buy_volume, closing_rows)
        if att.date is None or att.vwap is None:
            return ShareholderFlowMetrics(
                ticker=ticker,
                data_quality="partial",
                source=self.name,
                notes=(
                    f"انتساب تاریخ رد شد: {att.rejected_reason}",
                    f"relative_diff={att.relative_diff} second_best_diff={att.second_best_diff} tolerance={self.snapshot_volume_tolerance}",
                    f"insCode={identity.ins_code} matched_by={matched_by}",
                ),
            )
        if confirmed_date is not None and att.date != int(confirmed_date):
            # لایهٔ ۳ — تاریخِ منتسب با تأیید مستقل چند-نمادی نمی‌خواند ⇒ partial
            return ShareholderFlowMetrics(
                ticker=ticker,
                data_quality="partial",
                source=self.name,
                notes=(
                    f"تاریخ منتسب snapshot ({att.date}) با تاریخ تأییدشدهٔ مستقل ({confirmed_date}) نمی‌خواند",
                    f"insCode={identity.ins_code}",
                ),
            )
        total_buy = float(row.total_buy_volume)
        legal_buy_share = round(row.legal_buy_volume / total_buy, 6) if total_buy > 0 else None
        individual_avg_buy_value = (
            round(row.individual_buy_volume * att.vwap / row.individual_buy_count, 2)
            if row.individual_buy_count > 0
            else None
        )
        individual_avg_sell_value = (
            round(row.individual_sell_volume * att.vwap / row.individual_sell_count, 2)
            if row.individual_sell_count > 0
            else None
        )
        legal_net_buy_value = round((row.legal_buy_volume - row.legal_sell_volume) * att.vwap, 2)
        return ShareholderFlowMetrics(
            ticker=ticker,
            shareholder_count_series=(),  # صریح: تاریخچهٔ تعداد سهامداران هنوز تجمیع نشده (مسئولیت daily-ingest)
            shareholder_count_change_pct=None,
            individual_avg_buy_value=individual_avg_buy_value,
            individual_avg_sell_value=individual_avg_sell_value,
            legal_buy_share=legal_buy_share,
            legal_net_buy_value=legal_net_buy_value,
            data_quality="usable",
            source=f"tsetmc_client_type:{self.base_url_old}{self._snapshot_path}",
            notes=(
                f"snapshot_date={att.date}",
                f"vwap_rial={round(att.vwap, 4)}",
                f"relative_diff={round(att.relative_diff, 6) if att.relative_diff is not None else None}",
                f"matched_by={matched_by}",
                "مقادیر سرانه ریالی هستند (حجم × VWAP واقعی روز ÷ تعداد معاملات)",
                "shareholder_count_series عمداً خالی است — نیازمند تجمیع روزانه در daily-ingest",
            ),
        )

    def inspect_snapshot(self, ticker: str, days: int = 5) -> dict:
        """دادهٔ خام واقعی + تشخیص انتساب؛ هیچ متریک مشتق‌شده‌ای برنمی‌گرداند (برای دیباگ/ops)."""
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
            att = self._attribute_snapshot_date(row.total_buy_volume, closing_rows)
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
                "date": att.date,
                "relative_diff": att.relative_diff,
                "second_best_diff": att.second_best_diff,
                "tolerance": self.snapshot_volume_tolerance,
                "days_checked": att.days_checked,
                "vwap": att.vwap,
                "verdict": "attributed" if att.date is not None else (att.rejected_reason or "unattributable"),
            }
        return result
