"""
Provider واقعی کدال (search.codal.ir).

- بدون API key
- نیاز به دسترسی شبکه از داخل ایران (geo-restriction)
- Accept: application/json الزامی است
- rate-limit سخت؛ backoff نمایی روی 429

محدوده: جست‌وجوی اطلاعیه‌ها بر اساس نماد؛ پارس صورت‌های مالی Excel فاز بعد.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from arya.models.codal import CodalLetter

logger = logging.getLogger(__name__)


class CodalProviderError(RuntimeError):
    """خطای قابل‌گزارش هنگام دریافت داده از کدال."""


class CodalProvider:
    """کلاینت جست‌وجوی افشا در کدال."""

    name = "codal"
    _default_base = "https://search.codal.ir/api/search"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 20.0,
        retries: int = 3,
        backoff_seconds: float = 1.0,
        min_interval_seconds: float = 1.0,
        user_agent: str = "ARYA-AI-Trader/0.2 (+codal; Iran TSE only)",
    ) -> None:
        self.base_url = (base_url or self._default_base).rstrip("/")
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self.user_agent = user_agent
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        last_error: Exception | None = None

        for attempt in range(self.retries):
            self._throttle()
            try:
                req = Request(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "application/json",
                        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
                    },
                )
                with urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                self._last_request_at = time.monotonic()
                if not raw:
                    raise CodalProviderError(f"پاسخ خالی از کدال: {url}")
                text = raw.decode("utf-8-sig")
                try:
                    return json.loads(text)
                except json.JSONDecodeError as exc:
                    raise CodalProviderError(
                        "پاسخ کدال JSON نیست؛ احتمالاً مسدود یا Accept نامعتبر"
                    ) from exc
            except HTTPError as exc:
                last_error = exc
                self._last_request_at = time.monotonic()
                if exc.code == 429:
                    wait = self.backoff_seconds * (2 ** attempt) * 5
                    logger.warning("کدال 429 — انتظار %.1fs", wait)
                    time.sleep(wait)
                    continue
                if exc.code in {500, 502, 503, 504} and attempt < self.retries - 1:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
                    continue
                break
            except (URLError, TimeoutError, CodalProviderError, json.JSONDecodeError) as exc:
                last_error = exc
                self._last_request_at = time.monotonic()
                if attempt < self.retries - 1:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
                    continue
                break

        raise CodalProviderError(f"دریافت از کدال ناموفق: {url}") from last_error

    @staticmethod
    def _map_letter(row: dict[str, Any]) -> CodalLetter:
        url = row.get("Url") or row.get("url")
        pdf = row.get("PdfUrl") or row.get("pdfUrl")
        return CodalLetter(
            tracing_no=str(row.get("TracingNo") or row.get("tracingNo") or ""),
            symbol=str(row.get("Symbol") or row.get("symbol") or "").strip(),
            company_name=str(row.get("CompanyName") or row.get("companyName") or "").strip(),
            title=str(row.get("Title") or row.get("title") or "").strip(),
            sent_datetime=row.get("SentDateTime") or row.get("sentDateTime"),
            publish_datetime=row.get("PublishDateTime") or row.get("publishDateTime"),
            letter_code=row.get("LetterCode") or row.get("letterCode"),
            letter_type=str(row.get("LetterType") or row.get("letterType") or "") or None,
            url=url,
            pdf_url=pdf,
            has_html=bool(row.get("HasHtml") or row.get("hasHtml")),
            has_attachment=bool(row.get("HasAttachment") or row.get("hasAttachment")),
            letter_serial=row.get("LetterSerial") or row.get("letterSerial"),
        )

    def search_letters(
        self,
        symbol: str,
        *,
        page: int = 1,
        length: int = 20,
        letter_type: int | None = None,
        category: int | None = None,
    ) -> tuple[list[CodalLetter], int]:
        """جست‌وجوی اطلاعیه‌های یک نماد. Returns: (letters, total_count)"""
        symbol = symbol.strip()
        if not symbol:
            raise ValueError("نماد خالی است")

        params: dict[str, Any] = {
            "Symbol": symbol,
            "PageNumber": str(page),
            "Audited": "true",
            "NotAudited": "true",
            "AuditorRef": "-1",
            "Category": str(category if category is not None else -1),
            "Childs": "true",
            "CompanyState": "-1",
            "CompanyType": "-1",
            "Consolidatable": "true",
            "IsNotAudited": "false",
            "LetterType": str(letter_type if letter_type is not None else -1),
            "Mains": "true",
            "NotConsolidatable": "true",
            "Publisher": "false",
            "TracingNo": "-1",
            "search": "true",
        }
        if length and length > 0:
            params["Length"] = str(min(length, 50))

        payload = self._get_json("/v2/q", params)
        if not isinstance(payload, dict):
            raise CodalProviderError("ساختار پاسخ جست‌وجوی کدال نامعتبر است")

        total = int(payload.get("Total") or payload.get("total") or 0)
        raw_letters = payload.get("Letters") or payload.get("letters") or []
        if not isinstance(raw_letters, list):
            raw_letters = []

        letters = [self._map_letter(r) for r in raw_letters if isinstance(r, dict)]
        return letters, total

    def fetch_recent(self, symbol: str, limit: int = 10) -> list[CodalLetter]:
        """آخرین اطلاعیه‌های نماد (صفحه ۱)."""
        letters, _ = self.search_letters(symbol, page=1, length=max(limit, 10))
        return letters[:limit]

    def health_check(self) -> bool:
        """بررسی دسترسی (ممکن است از خارج ایران شکست بخورد)."""
        try:
            self.search_letters("فولاد", page=1, length=1)
            return True
        except CodalProviderError:
            return False
