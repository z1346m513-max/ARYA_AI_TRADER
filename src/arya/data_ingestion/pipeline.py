"""Versioned manual-file contract and local, atomic research report pipeline."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from arya.data_quality import validate_ohlcv_series
from arya.models.market_data import Candle, OHLCVSeries, Symbol

SCHEMA_VERSION = "manual-ohlcv-v1"
PIPELINE_VERSION = "1"
MARKETS = ("iran_equity", "crypto", "forex")
REQUIRED = ("timestamp", "symbol", "open", "high", "low", "close", "volume")
OPTIONAL = ("market", "timeframe", "currency", "venue", "volume_unit")
MAX_BYTES = 20 * 1024 * 1024
MAX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 32


class IngestionError(ValueError):
    """Rejected data, configuration or incomplete concurrent processing."""


@dataclass(frozen=True)
class IngestionContext:
    market: str
    source: str
    venue: str
    currency: str
    volume_unit: str
    timeframe: str = "1d"
    max_age_hours: float | None = None

    def __post_init__(self) -> None:
        if self.market not in MARKETS:
            raise IngestionError(f"market must be one of {MARKETS}")
        for key in ("source", "venue", "currency", "timeframe"):
            value = getattr(self, key)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise IngestionError(f"{key} must be explicit and non-empty")
        allowed_units = {
            "iran_equity": {"shares"},
            "crypto": {"base_asset"},
            "forex": {"base_asset", "ticks"},
        }
        if self.volume_unit not in allowed_units[self.market]:
            raise IngestionError(f"invalid volume_unit for {self.market}")
        if self.market == "iran_equity" and self.currency not in {"IRR", "IRT"}:
            raise IngestionError("Iran equity currency must explicitly be IRR or IRT; no conversion is performed")
        if self.max_age_hours is not None and (
            not math.isfinite(self.max_age_hours) or self.max_age_hours <= 0
        ):
            raise IngestionError("max_age_hours must be finite and positive")


def _table(blob: bytes, suffix: str) -> list[dict[str, Any]]:
    """Load literal cells only. Formulas are rejected, never evaluated/cached."""
    workbook = None
    try:
        if suffix == ".csv":
            rows = csv.reader(io.StringIO(blob.decode("utf-8-sig"), newline=""), strict=True)
        else:
            try:
                import defusedxml  # noqa: F401 -- required for untrusted XML
                import openpyxl
            except ImportError as exc:
                raise IngestionError("XLSX requires: pip install -e '.[excel]'") from exc
            with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                if sum(item.file_size for item in archive.infolist()) > MAX_EXPANDED_BYTES:
                    raise IngestionError("XLSX expanded size exceeds limit")
            workbook = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=False, keep_links=False)
            if "ohlcv" not in workbook.sheetnames:
                raise IngestionError("XLSX must contain sheet 'ohlcv'")
            sheet = workbook["ohlcv"]
            # Ignore potentially forged worksheet dimensions; bound iteration ourselves.
            sheet.reset_dimensions()
            rows = sheet.iter_rows(values_only=True)
        headers = next(rows, None)
        if headers is None:
            raise IngestionError("empty file")
        headers = list(headers)
        if len(headers) > MAX_COLUMNS:
            raise IngestionError("too many columns")
        if any(not isinstance(h, str) or h != h.strip() for h in headers):
            raise IngestionError("headers must be literal, unpadded strings")
        if len(set(headers)) != len(headers):
            raise IngestionError("duplicate headers")
        missing = set(REQUIRED) - set(headers)
        unknown = set(headers) - set(REQUIRED + OPTIONAL)
        if missing or unknown:
            raise IngestionError(f"invalid headers; missing={sorted(missing)}, unknown={sorted(unknown)}")
        result = []
        for row_index, values in enumerate(rows, start=2):
            if row_index > MAX_ROWS + 1:
                raise IngestionError("row limit exceeded")
            values = list(values)
            if not values or all(v in (None, "") for v in values):
                continue
            if len(values) != len(headers):
                raise IngestionError(f"row {row_index}: inconsistent column count")
            if any(isinstance(v, str) and v.lstrip().startswith("=") for v in values):
                raise IngestionError(f"row {row_index}: formulas are forbidden")
            result.append(dict(zip(headers, values)))
        if not result:
            raise IngestionError("no observations")
        return result
    except IngestionError:
        raise
    except Exception as exc:
        # Untrusted ZIP/XML/CSV failures are data rejection, not partial success.
        raise IngestionError(f"cannot parse {suffix} file ({type(exc).__name__})") from exc
    finally:
        if workbook is not None:
            workbook.close()


def _normalize(rows: list[dict], context: IngestionContext) -> tuple[list[dict], list[dict]]:
    normalized: list[dict] = []
    groups: dict[str, list[Candle]] = {}
    for index, row in enumerate(rows, start=2):
        for key in OPTIONAL:
            if key in row and row[key] != getattr(context, key):
                raise IngestionError(f"row {index}: {key} conflicts with ingestion context")
        symbol = row["symbol"]
        if not isinstance(symbol, str) or not symbol.strip() or symbol != symbol.strip():
            raise IngestionError(f"row {index}: symbol must be a non-empty string")
        raw_time = row["timestamp"]
        try:
            if not isinstance(raw_time, str):
                raise ValueError("timestamp must be ISO 8601 text with offset")
            timestamp = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("timezone offset is required")
            timestamp = timestamp.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError) as exc:
            raise IngestionError(f"row {index}: invalid timestamp; use ISO 8601 text with timezone") from exc
        numbers = {}
        for key in REQUIRED[2:]:
            value = row[key]
            try:
                if value in (None, "") or isinstance(value, bool):
                    raise ValueError("missing/bool")
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError("non-finite")
            except (TypeError, ValueError, OverflowError) as exc:
                raise IngestionError(f"row {index}: invalid {key}") from exc
            numbers[key] = number
        candle = Candle(timestamp=timestamp, **numbers)
        groups.setdefault(symbol, []).append(candle)
        normalized.append({
            "timestamp": timestamp.isoformat(), "symbol": symbol,
            **asdict(context), **numbers,
        })
    quality = []
    for symbol, candles in groups.items():
        series = OHLCVSeries(
            symbol=Symbol(symbol, "stock" if context.market == "iran_equity" else context.market, currency=context.currency),
            timeframe=context.timeframe, candles=candles,
        )
        report = validate_ohlcv_series(series)
        if not report.is_valid:
            raise IngestionError(f"{symbol}: " + "; ".join(issue.code for issue in report.issues))
        quality.append({"symbol": symbol, **asdict(report)})
    return normalized, quality


def _freshness(rows: list[dict], now: datetime, threshold: float | None) -> list[dict]:
    times: dict[str, list[datetime]] = {}
    for row in rows:
        times.setdefault(row["symbol"], []).append(datetime.fromisoformat(row["timestamp"]))
    result = []
    for symbol, stamps in times.items():
        age = (now - max(stamps)).total_seconds() / 3600
        status = "FUTURE" if age < 0 else (
            "UNKNOWN" if threshold is None else ("STALE" if age > threshold else "WITHIN_AGE_LIMIT")
        )
        # No exchange calendar or source authority is inferred from an age limit.
        result.append({"symbol": symbol, "status": status, "age_hours": round(age, 6)})
    return result


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def ingest_file(
    file_path: Path | str, root: Path | str, context: IngestionContext,
    *, now: datetime | None = None,
) -> dict:
    """Publish one complete content-addressed run; never modify the input file.

    All consumers must read completed runs only. A lock serializes cooperating
    writers; staging and final directories share a filesystem for atomic rename.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise IngestionError("evaluation time must be timezone-aware")
    now = now.astimezone(timezone.utc)
    file_path, root = Path(file_path), Path(root)
    if file_path.is_symlink() or not file_path.is_file():
        raise IngestionError("input must be a regular, non-symlink file")
    suffix = file_path.suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise IngestionError("only .csv and .xlsx are supported")
    with file_path.open("rb") as handle:
        blob = handle.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES:
        raise IngestionError("input exceeds 20 MiB")
    digest = hashlib.sha256(blob).hexdigest()
    identity = {
        "sha256": digest, "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION, "format": suffix, **asdict(context),
    }
    run_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    market_root = root / context.market
    completed = market_root / "runs" / run_id
    rejected = market_root / "rejected" / run_id
    market_root.mkdir(parents=True, exist_ok=True)
    lock = market_root / ".ingest.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise IngestionError(f"ingestion locked: {lock}; verify no worker is active before removing stale lock") from exc
    staging = None
    try:
        if completed.exists():
            try:
                manifest = json.loads((completed / "manifest.json").read_text(encoding="utf-8"))
                normalized_blob = (completed / "normalized.json").read_bytes()
                if hashlib.sha256(normalized_blob).hexdigest() != manifest["normalized_sha256"]:
                    raise IngestionError("completed normalized artifact failed integrity check")
                if not (completed / "report.json").is_file():
                    raise IngestionError("completed report is missing; restore the run before retrying")
                rows = json.loads(normalized_blob)
            except (OSError, KeyError, json.JSONDecodeError) as exc:
                raise IngestionError("completed run is damaged; restore artifacts before retrying") from exc
            freshness = _freshness(rows, now, context.max_age_hours)
            # Duplicate calls must not claim that yesterday's age assessment is current.
            return {
                "status": "DUPLICATE", "run_id": run_id, "run_path": str(completed),
                "manifest": manifest, "evaluated_at_utc": now.isoformat(),
                "freshness": freshness,
                "risk_gate": "BLOCK" if any(x["status"] in {"STALE", "FUTURE"} for x in freshness) else "UNASSESSED",
            }
        market_runs = market_root / "runs"
        market_runs.mkdir(exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".pending-", dir=market_runs))
        manifest = {
            **identity, "run_id": run_id, "file_name": file_path.name,
            "received_at_utc": now.isoformat(), "bytes": len(blob),
            "source_trust": "UNVERIFIED", "validation_status": "PENDING",
        }
        (staging / ("input" + suffix)).write_bytes(blob)
        try:
            normalized, quality = _normalize(_table(blob, suffix), context)
        except IngestionError as exc:
            manifest.update(validation_status="REJECTED", error=str(exc))
            _write_json(staging / "manifest.json", manifest)
            rejected.parent.mkdir(exist_ok=True)
            if not rejected.exists():
                staging.rename(rejected)
                staging = None
            raise
        freshness = _freshness(normalized, now, context.max_age_hours)
        blocked = any(item["status"] in {"STALE", "FUTURE"} for item in freshness)
        summary = []
        grouped: dict[str, list[dict]] = {}
        for row in normalized:
            grouped.setdefault(row["symbol"], []).append(row)
        for symbol, observations in sorted(grouped.items()):
            summary.append({
                "symbol": symbol, "rows": len(observations),
                "as_of": observations[-1]["timestamp"], "last_close": observations[-1]["close"],
                "min_low": min(row["low"] for row in observations),
                "max_high": max(row["high"] for row in observations),
            })
        manifest.update(
            validation_status="VALID", rows=len(normalized), symbols=len(summary),
            timestamp_min=min(row["timestamp"] for row in normalized),
            timestamp_max=max(row["timestamp"] for row in normalized),
        )
        report = {
            "run_id": run_id, "market": context.market, "context": asdict(context),
            "generated_at_utc": now.isoformat(), "data_status": "STRUCTURALLY_VALID",
            "source_trust": "UNVERIFIED", "freshness": freshness,
            "risk_gate": "BLOCK" if blocked else "UNASSESSED",
            "analysis_status": "RESEARCH_ONLY", "summary": summary,
            "recommendations": [],
            "limitations": [
                "Manual source authenticity, exchange calendars, adjustment and completeness are unverified.",
                "Descriptive statistics only; no autonomous AI, trading signal, risk approval or order execution.",
                "Fundamental and flow inputs are not supplied by this schema.",
            ],
        }
        _write_json(staging / "normalized.json", normalized)
        manifest["normalized_sha256"] = hashlib.sha256((staging / "normalized.json").read_bytes()).hexdigest()
        _write_json(staging / "manifest.json", manifest)
        _write_json(staging / "report.json", report)
        outputs = staging / "agent_outputs"
        outputs.mkdir()
        _write_json(outputs / "data_quality.json", {"run_id": run_id, "quality": quality, "freshness": freshness})
        _write_json(outputs / "technical.json", {"run_id": run_id, "status": "DESCRIPTIVE_ONLY", "summary": summary})
        for stage in ("fundamental", "market_flow"):
            _write_json(outputs / f"{stage}.json", {"run_id": run_id, "status": "NOT_AVAILABLE", "reason": "Required inputs not supplied"})
        _write_json(outputs / "risk.json", {"run_id": run_id, "gate": report["risk_gate"], "trading_enabled": False})
        _write_json(outputs / "synthesis.json", report)
        # JSON carries user-controlled text. Keep Markdown free of injected HTML/links.
        (staging / "report.md").write_text(
            "# ARYA manual market data report\n\n"
            f"Market: {context.market}. Run: `{run_id}`.\n\n"
            f"Rows: {len(normalized)}. Instruments: {len(summary)}. "
            f"Risk gate: {report['risk_gate']}. Source trust: UNVERIFIED.\n\n"
            "This is a structural-quality and descriptive research report, not investment advice. "
            "See report.json for observations, freshness and limitations.\n",
            encoding="utf-8",
        )
        staging.rename(completed)
        staging = None
        return {"status": "PROCESSED", "run_id": run_id, "run_path": str(completed), "manifest": manifest}
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        lock.rmdir()
