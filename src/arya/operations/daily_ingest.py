"""Daily ingest skeleton for TSETMC/Codal watch sources (Stage A, no live fetch by default)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml


@dataclass
class SourceSpec:
    id: str
    label: str
    page_url: str
    preferred_api: str | None = None
    status: str = "NOT_TESTED"
    enabled: bool = False
    notes: str | None = None


@dataclass
class IngestConfig:
    enabled: bool
    timezone: str
    output_root: Path
    user_agent: str
    timeout_seconds: float
    retries: int
    backoff_seconds: float
    sources: list[SourceSpec] = field(default_factory=list)
    save_raw: bool = True
    save_manifest: bool = True
    commit_to_git: bool = False


@dataclass
class SourceRunResult:
    source_id: str
    ok: bool
    message: str
    output_dir: Path | None = None
    bytes_written: int = 0


def load_ingest_config(path: Path | str) -> IngestConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    storage = raw.get("storage") or {}
    sources: list[SourceSpec] = []
    for key, item in (raw.get("sources") or {}).items():
        if not isinstance(item, dict):
            continue
        sources.append(
            SourceSpec(
                id=str(item.get("id") or key),
                label=str(item.get("label") or key),
                page_url=str(item.get("page_url") or ""),
                preferred_api=item.get("preferred_api"),
                status=str(item.get("status") or "NOT_TESTED"),
                enabled=bool(item.get("enabled", False)),
                notes=item.get("notes"),
            )
        )
    return IngestConfig(
        enabled=bool(raw.get("enabled", False)),
        timezone=str(raw.get("timezone") or "Asia/Tehran"),
        output_root=Path(str(raw.get("output_root") or "data/snapshots")),
        user_agent=str(raw.get("user_agent") or "ARYA-AI-Trader/0.1"),
        timeout_seconds=float(raw.get("timeout_seconds") or 30),
        retries=int(raw.get("retries") or 2),
        backoff_seconds=float(raw.get("backoff_seconds") or 1.0),
        sources=sources,
        save_raw=bool(storage.get("save_raw", True)),
        save_manifest=bool(storage.get("save_manifest", True)),
        commit_to_git=bool(storage.get("commit_to_git", False)),
    )


def list_sources(cfg: IngestConfig) -> list[SourceSpec]:
    return list(cfg.sources)


def run_daily_ingest(
    cfg: IngestConfig,
    *,
    source_ids: list[str] | None = None,
    dry_run: bool = False,
    now: datetime | None = None,
) -> list[SourceRunResult]:
    if cfg.commit_to_git:
        raise ValueError("commit_to_git is not supported and must stay false")
    day = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    selected = cfg.sources
    if source_ids:
        wanted = set(source_ids)
        selected = [s for s in cfg.sources if s.id in wanted]
    results: list[SourceRunResult] = []
    for src in selected:
        out_dir = cfg.output_root / day / src.id
        if dry_run or not cfg.enabled or not src.enabled:
            reason = []
            if dry_run:
                reason.append("dry-run")
            if not cfg.enabled:
                reason.append("global disabled")
            if not src.enabled:
                reason.append(f"source disabled ({src.status})")
            results.append(
                SourceRunResult(
                    source_id=src.id,
                    ok=True,
                    message="skipped: " + ", ".join(reason) + f" -> {out_dir}",
                    output_dir=out_dir,
                )
            )
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        stub = {
            "source_id": src.id,
            "label": src.label,
            "page_url": src.page_url,
            "status": src.status,
            "fetched_at": (now or datetime.now(timezone.utc)).isoformat(),
            "note": "Stage A stub — no network fetch yet",
        }
        payload = json.dumps(stub, ensure_ascii=False, indent=2).encode("utf-8")
        if cfg.save_raw:
            (out_dir / "stub.json").write_bytes(payload)
        if cfg.save_manifest:
            manifest = {
                "source_id": src.id,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "page_url": src.page_url,
                "status": src.status,
            }
            (out_dir / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        results.append(
            SourceRunResult(
                source_id=src.id,
                ok=True,
                message="stub written",
                output_dir=out_dir,
                bytes_written=len(payload),
            )
        )
    return results
