"""
ایجنت پژوهش: جمع‌آوری نکات مفید از منابع از پیش‌تعریف‌شده
و ارسال به مغز دوم (بدون وابستگی اجباری به اینترنت در حالت آفلاین).

در حالت آنلاین می‌تواند URLهای ثابت مستند را بخواند؛
یافته‌ها با kind=research_note در Second Brain ذخیره می‌شوند.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from arya.agents.base import Agent, AgentMessage
from arya.agents.second_brain import SecondBrain

logger = logging.getLogger(__name__)

# منابع مجاز و مرتبط با بورس ایران / زیرساخت داده
CURATED_SOURCES: list[dict[str, str]] = [
    {
        "id": "tsetmc_cdn",
        "title": "TSETMC CDN API",
        "url": "https://cdn.tsetmc.com",
        "tags": "tsetmc,api,market",
        "note": "منبع قیمت، ClientType، سهامدار، جزئیات نماد",
    },
    {
        "id": "codal_search",
        "title": "کدال جست‌وجو",
        "url": "https://search.codal.ir",
        "tags": "codal,disclosure",
        "note": "افشا، افزایش سرمایه، مدیران؛ در صورت قطع از manual استفاده شود",
    },
    {
        "id": "peer_tsetmc",
        "title": "پروژه مشابه 5j9/tsetmc",
        "url": "https://github.com/5j9/tsetmc",
        "tags": "peer,github,tsetmc",
        "note": "الگوی async و endpointهای Instrument/ClosingPrice",
    },
    {
        "id": "peer_pytse",
        "title": "پروژه مشابه pytse-client",
        "url": "https://github.com/TheRook/pytse-client",
        "tags": "peer,github,clienttype",
        "note": "الگوی ClientType و سهامداران",
    },
]


class ResearchAgent(Agent):
    name = "research"

    def __init__(self, brain: SecondBrain | None = None) -> None:
        self.brain = brain or SecondBrain()

    def run(self, **kwargs: Any) -> list[AgentMessage]:
        query = str(kwargs.get("query") or "بورس ایران")
        online = bool(kwargs.get("online", False))
        messages: list[AgentMessage] = []

        for src in CURATED_SOURCES:
            reachable = None
            if online:
                reachable = self._ping(src["url"])
            payload = {
                "query": query,
                "source_id": src["id"],
                "title": src["title"],
                "url": src["url"],
                "note": src["note"],
                "reachable": reachable,
                "summary": f"{src['title']}: {src['note']} (مرتبط با: {query})",
                "relevance": 0.8 if query else 0.5,
            }
            kind = "peer_pattern" if "peer" in src["tags"] else "research_note"
            msg = AgentMessage(
                agent=self.name,
                kind=kind,
                payload=payload,
                tags=[t.strip() for t in src["tags"].split(",") if t.strip()],
                source=src["url"],
                ttl_hours=168,
            )
            self.brain.remember(msg, persist=True)
            messages.append(msg)

        return messages

    @staticmethod
    def _ping(url: str, timeout: float = 8.0) -> bool:
        try:
            req = Request(url, method="HEAD", headers={"User-Agent": "ARYA-ResearchAgent/0.1"})
            with urlopen(req, timeout=timeout) as resp:
                return 200 <= getattr(resp, "status", 200) < 500
        except Exception:  # noqa: BLE001
            try:
                req = Request(url, headers={"User-Agent": "ARYA-ResearchAgent/0.1"})
                with urlopen(req, timeout=timeout) as resp:
                    return True
            except (URLError, TimeoutError, OSError):
                return False
