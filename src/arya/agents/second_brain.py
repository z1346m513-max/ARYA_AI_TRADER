"""
مغز دوم (Second Brain):
- نگهداری اطلاعات ایجنت‌ها
- دسته‌بندی بر اساس kind/tags/ticker
- پایداری روی دیسک در data/second_brain/
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from arya.agents.base import AgentMessage, utc_now

logger = logging.getLogger(__name__)


class SecondBrain:
    def __init__(self, root: str | Path = "data/second_brain") -> None:
        self.root = Path(root)
        self.working_dir = self.root / "working"
        self.episodic_dir = self.root / "episodic"
        self.knowledge_dir = self.root / "knowledge"
        self.index_path = self.root / "index.json"
        for d in (
            self.working_dir,
            self.episodic_dir,
            self.knowledge_dir / "symbols",
            self.knowledge_dir / "strategies",
            self.knowledge_dir / "research",
            self.knowledge_dir / "peers",
        ):
            d.mkdir(parents=True, exist_ok=True)

        self._working: list[dict[str, Any]] = []
        self._index: dict[str, Any] = self._load_index()

    def _load_index(self) -> dict[str, Any]:
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {"entries": []}
        return {"entries": []}

    def _save_index(self) -> None:
        self.index_path.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def remember(self, msg: AgentMessage, *, persist: bool = True) -> str:
        """ثبت در حافظه کاری و در صورت نیاز روی دیسک."""
        entry_id = str(uuid4())
        record = {
            "id": entry_id,
            "agent": msg.agent,
            "kind": msg.kind,
            "ticker": msg.ticker,
            "tags": msg.tags,
            "ts": msg.ts,
            "ttl_hours": msg.ttl_hours,
            "source": msg.source,
            "payload": msg.payload,
        }
        self._working.append(record)

        # ایندکس سبک
        self._index.setdefault("entries", []).append(
            {
                "id": entry_id,
                "agent": msg.agent,
                "kind": msg.kind,
                "ticker": msg.ticker,
                "tags": msg.tags,
                "ts": msg.ts,
            }
        )
        # نگهداشت ایندکس در حد معقول
        if len(self._index["entries"]) > 5000:
            self._index["entries"] = self._index["entries"][-4000:]

        if persist:
            self._persist(record)
            self._save_index()

        logger.debug("brain.remember %s %s %s", msg.agent, msg.kind, msg.ticker)
        return entry_id

    def _persist(self, record: dict[str, Any]) -> None:
        day = (record.get("ts") or utc_now())[:10]
        epi = self.episodic_dir / day
        epi.mkdir(parents=True, exist_ok=True)
        path = epi / f"{record['id']}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        kind = record.get("kind") or "misc"
        ticker = record.get("ticker")
        if ticker and kind in {"instrument_detail", "client_type", "recommendation", "codal_event"}:
            sym_dir = self.knowledge_dir / "symbols"
            sym_path = sym_dir / f"{ticker}.json"
            bucket: dict[str, Any] = {}
            if sym_path.exists():
                try:
                    bucket = json.loads(sym_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    bucket = {}
            bucket.setdefault("ticker", ticker)
            bucket.setdefault("history", [])
            bucket["history"].append({"id": record["id"], "kind": kind, "ts": record["ts"]})
            bucket["history"] = bucket["history"][-50:]
            bucket["last"] = record
            bucket["updated_at"] = utc_now()
            sym_path.write_text(json.dumps(bucket, ensure_ascii=False, indent=2), encoding="utf-8")

        if kind in {"research_note", "peer_pattern"}:
            sub = "peers" if kind == "peer_pattern" else "research"
            rpath = self.knowledge_dir / sub / f"{record['id']}.json"
            rpath.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        if kind == "strategy_scan":
            sp = self.knowledge_dir / "strategies" / f"{record['id']}.json"
            sp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        # آخرین working snapshot
        snap = self.working_dir / "last_session.json"
        snap.write_text(
            json.dumps(self._working[-100:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def recall(
        self,
        *,
        ticker: str | None = None,
        kind: str | None = None,
        tag: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """بازیابی از حافظه کاری + ایندکس."""
        hits: list[dict[str, Any]] = []
        for rec in reversed(self._working):
            if ticker and rec.get("ticker") != ticker:
                continue
            if kind and rec.get("kind") != kind:
                continue
            if tag and tag not in (rec.get("tags") or []):
                continue
            hits.append(rec)
            if len(hits) >= limit:
                return hits

        # تکمیل از دانش نماد روی دیسک
        if ticker and len(hits) < limit:
            sym_path = self.knowledge_dir / "symbols" / f"{ticker}.json"
            if sym_path.exists():
                try:
                    bucket = json.loads(sym_path.read_text(encoding="utf-8"))
                    last = bucket.get("last")
                    if last and last not in hits:
                        hits.append(last)
                except (OSError, json.JSONDecodeError):
                    pass
        return hits[:limit]

    def categorize_summary(self, ticker: str | None = None) -> dict[str, Any]:
        """خلاصه دسته‌بندی‌شده برای Analyst."""
        items = self.recall(ticker=ticker, limit=50)
        by_kind: dict[str, list] = defaultdict(list)
        for it in items:
            by_kind[str(it.get("kind"))].append(it)
        return {
            "ticker": ticker,
            "counts": {k: len(v) for k, v in by_kind.items()},
            "kinds": dict(by_kind),
            "generated_at": utc_now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "root": str(self.root.resolve()),
            "working_items": len(self._working),
            "index_entries": len(self._index.get("entries") or []),
            "disk_exists": self.root.exists(),
        }
