#!/usr/bin/env python3
"""Worker امن همگام‌سازی منابع Drive برای فاز اول.

ویژگی‌ها:
- اجرای rclone copy به‌صورت idempotent و بدون حذف فایل‌های مقصد
- dry-run پیش‌فرض برای جلوگیری از کپی ناخواسته
- allowlist پسوندها و حجم فایل
- ثبت sha256، اندازه، زمان تغییر و وضعیت پردازش در manifest
- پردازش سبک JSON/CSV و ثبت صف بررسی برای PDF/XLSX

نمونه:
  PYTHONPATH=src python scripts/drive_sync_worker.py \
    --remote drive:arya-phase-one --local-dir data/phase-one --apply
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_EXTENSIONS = {".json", ".csv", ".xlsx", ".xls", ".pdf", ".txt", ".md"}
TEXT_EXTENSIONS = {".json", ".csv", ".txt", ".md"}
DEFAULT_MAX_BYTES = 50 * 1024 * 1024


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "files": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("files"), dict):
            return payload
    except (OSError, json.JSONDecodeError):
        pass
    raise RuntimeError(f"manifest معتبر نیست یا قابل خواندن نیست: {path}")


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def run_rclone(remote: str, local_dir: Path, log_file: Path, apply: bool, max_bytes: int) -> int:
    local_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "rclone", "copy", remote, str(local_dir),
        "--drive-shared-with-me", "--checksum", "--fast-list",
        "--max-size", f"{max_bytes}b", "--log-file", str(log_file), "--log-level", "INFO",
    ]
    if not apply:
        command.append("--dry-run")
    print("$", " ".join(command))
    try:
        result = subprocess.run(command, check=False, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("rclone نصب نیست یا در PATH قرار ندارد") from exc
    return result.returncode


def parse_text_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    result: dict[str, Any] = {"parser": "metadata-only"}
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            result["parser"] = "json"
            result["records"] = len(payload) if isinstance(payload, list) else 1
            result["top_level"] = list(payload)[:20] if isinstance(payload, dict) else None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            result["error"] = f"json_parse_error: {exc}"
    elif suffix == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                headers = next(reader, [])
                result["parser"] = "csv"
                result["headers"] = headers[:30]
                result["records"] = sum(1 for _ in reader)
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            result["error"] = f"csv_parse_error: {exc}"
    else:
        result["parser"] = "text-metadata-only"
    return result


def process_downloads(local_dir: Path, manifest_path: Path, max_bytes: int) -> dict[str, int]:
    manifest = load_manifest(manifest_path)
    files = manifest.setdefault("files", {})
    counts = {"seen": 0, "processed": 0, "skipped": 0, "rejected": 0, "errors": 0}
    now = datetime.now(timezone.utc).isoformat()

    manifest_resolved = manifest_path.resolve()
    for path in sorted(p for p in local_dir.rglob("*") if p.is_file()):
        if path.resolve() == manifest_resolved:
            continue
        counts["seen"] += 1
        relative = path.relative_to(local_dir).as_posix()
        suffix = path.suffix.lower()
        size = path.stat().st_size
        if suffix not in ALLOWED_EXTENSIONS or size > max_bytes:
            files[relative] = {"status": "rejected", "reason": "extension_or_size", "size": size, "updated_at": now}
            counts["rejected"] += 1
            continue
        digest = sha256_file(path)
        previous = files.get(relative, {})
        if previous.get("sha256") == digest and previous.get("status") == "processed":
            counts["skipped"] += 1
            continue
        item: dict[str, Any] = {
            "status": "processed",
            "sha256": digest,
            "size": size,
            "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "modified_time": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            "processed_at": now,
        }
        if suffix in TEXT_EXTENSIONS:
            item["content"] = parse_text_file(path)
        else:
            item["content"] = {"parser": "queued_for_secure_document_extraction"}
        files[relative] = item
        counts["processed"] += 1

    manifest["updated_at"] = now
    write_manifest(manifest_path, manifest)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Secure rclone sync and resource processing worker")
    parser.add_argument("--remote", default="drive:arya-phase-one")
    parser.add_argument("--local-dir", type=Path, default=Path("data/phase-one"))
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--log-file", type=Path, default=Path("data/logs/drive-sync.log"))
    parser.add_argument("--max-size-mb", type=int, default=50)
    parser.add_argument("--apply", action="store_true", help="اجرای copy واقعی؛ در حالت پیش‌فرض dry-run است")
    args = parser.parse_args()
    manifest = args.manifest or args.local_dir / "manifest.json"
    max_bytes = args.max_size_mb * 1024 * 1024

    try:
        code = run_rclone(args.remote, args.local_dir, args.log_file, args.apply, max_bytes)
        if code != 0:
            print(json.dumps({"ok": False, "stage": "rclone", "exit_code": code}, ensure_ascii=False))
            return code
        counts = process_downloads(args.local_dir, manifest, max_bytes)
        print(json.dumps({"ok": True, "mode": "apply" if args.apply else "dry-run", "manifest": str(manifest), "counts": counts}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
