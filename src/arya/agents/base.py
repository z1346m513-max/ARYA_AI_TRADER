"""قرارداد مشترک ایجنت‌های ARYA."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class AgentMessage:
    """واحد اطلاعاتی که به مغز دوم نوشته می‌شود."""

    agent: str
    kind: str
    payload: dict[str, Any]
    ticker: str | None = None
    tags: list[str] = field(default_factory=list)
    ts: str = field(default_factory=utc_now)
    ttl_hours: int | None = 48
    source: str | None = None


class Agent(ABC):
    name: str = "agent"

    @abstractmethod
    def run(self, **kwargs: Any) -> list[AgentMessage]:
        """اجرای یک چرخه و برگرداندن پیام‌ها برای حافظه."""
