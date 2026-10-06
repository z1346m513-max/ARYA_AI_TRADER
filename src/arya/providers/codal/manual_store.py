"""
ذخیره دستی اطلاعیه‌ها وقتی search.codal.ir در دسترس نیست.

مسیر پیش‌فرض: data/manual/codal_events.json
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from arya.models.codal import CodalLetter
from arya.providers.market.ticker_map import to_tse_symbol

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path("data/manual/codal_events.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ManualCodalEvent:
    ticker: str
    title: str
    event_type: str  # capital | board | assembly | disclosure | other
    publish_date: str | None = None  # YYYY-MM-DD
    notes: str | None = None
    source: str = "manual"
    entered_at: str = field(default_factory=_utc_now)
    tracing_no: str | None = None

    def to_letter(self) -> CodalLetter:
        return CodalLetter(
            tracing_no=self.tracing_no or f"MANUAL-{self.ticker}-{self.entered_at}",
            symbol=self.ticker,
            company_name=None,
            title=self.title,
            sent_datetime=self.publish_date,
            publish_datetime=self.publish_date,
            letter_code=None,
            letter_type=self.event_type,
            url=None,
            pdf_url=None,
            has_html=False,
            has_attachment=False,
            letter_serial=None,
        )


class ManualCodalStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_PATH

    def _load_raw(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("خواندن فایل دستی کدال ناموفق: %s", exp if False else exc)
            return []
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def _save_raw(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_events(self, ticker: str | None = None) -> list[ManualCodalEvent]:
        want = to_tse_symbol(ticker) if ticker else None
        out: list[ManualCodalEvent] = []
        for row in self._load_raw():
            t = str(row.get("ticker") or "")
            if want and to_tse_symbol(t) != want:
                continue
            out.append(
                ManualCodalEvent(
                    ticker=t,
                    title=str(row.get("title") or ""),
                    event_type=str(row.get("event_type") or "other"),
                    publish_date=row.get("publish_date"),
                    notes=row.get("notes"),
                    source=str(row.get("source") or "manual"),
                    entered_at=str(row.get("entered_at") or _utc_now()),
                    tracing_no=row.get("tracing_no"),
                )
            )
        return out

    def add(self, event: ManualCodalEvent) -> ManualCodalEvent:
        event.ticker = to_tse_symbol(event.ticker)
        rows = self._load_raw()
        rows.append(asdict(event))
        self._save_raw(rows)
        logger.info("رویداد دستی کدال ثبت شد: %s | %s", event.ticker, event.title[:40])
        return event

    def letters_for(self, ticker: str) -> list[CodalLetter]:
        return [e.to_letter() for e in self.list_events(ticker)]

    def clear_ticker(self, ticker: str) -> int:
        t = to_tse_symbol(ticker)
        rows = self._load_raw()
        kept = [r for r in rows if to_tse_symbol(str(r.get("ticker") or "")) != t]
        removed = len(rows) - len(kept)
        self._save_raw(kept)
        return removed
