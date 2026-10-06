"""
هماهنگ‌کننده ایجنت‌ها + مغز دوم.
فعلاً چرخه ساده: Research → (داده موجود Market/Flow از قبل) → خلاصه حافظه.
"""
from __future__ import annotations

import logging
from typing import Any

from arya.agents.research_agent import ResearchAgent
from arya.agents.second_brain import SecondBrain
from arya.agents.base import AgentMessage

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, brain: SecondBrain | None = None) -> None:
        self.brain = brain or SecondBrain()
        self.research = ResearchAgent(self.brain)

    def run_research_cycle(self, query: str = "بورس ایران TSETMC کدال", online: bool = False) -> dict[str, Any]:
        msgs = self.research.run(query=query, online=online)
        return {
            "stored": len(msgs),
            "brain": self.brain.status(),
            "sample": [m.kind for m in msgs],
        }

    def recall_ticker(self, ticker: str) -> dict[str, Any]:
        return self.brain.categorize_summary(ticker=ticker)

    def ingest(self, msg: AgentMessage) -> str:
        return self.brain.remember(msg, persist=True)
