"""مدل‌های افشای کدال — مستقل از Provider."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CodalLetter:
    """یک اطلاعیه/نامه منتشرشده در کدال."""

    tracing_no: str
    symbol: str
    company_name: str
    title: str
    sent_datetime: str | None = None
    publish_datetime: str | None = None
    letter_code: str | None = None
    letter_type: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    has_html: bool = False
    has_attachment: bool = False
    letter_serial: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def report_url(self) -> str | None:
        if self.url:
            if self.url.startswith("http"):
                return self.url
            return f"https://www.codal.ir{self.url}"
        return None
