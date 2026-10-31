from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "docs/governance/PLATFORM_CONSTITUTION.md",
    "docs/governance/STARTUP_CHECKLIST.md",
    "docs/governance/CHANGE_LEDGER.md",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    "skills/arya-platform-governance/SKILL.md",
]
CR_RE = re.compile(r"CR-\d{8}-\d{3}")
CR_FILENAME_RE = re.compile(r"CR-\d{8}-\d{3}\.md")

def invalid_change_record_filenames(changes_dir: Path) -> list[str]:
    """Return Change Record filenames that do not follow the canonical ID format."""
    return sorted(
        path.name
        for path in changes_dir.glob("CR-*.md")
        if not CR_FILENAME_RE.fullmatch(path.name)
    )

def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing:
        print("Missing mandatory governance files:")
        for item in missing:
            print(item)
        return 1

    change_files = sorted((ROOT / "docs/changes").glob("CR-*.md"))
    bad_names = [p.name for p in change_files if not re.fullmatch(r"CR-\d{8}-\d{3}\.md", p.name)]
    if bad_names:
        print("Invalid Change Record filenames:", ", ".join(bad_names))
        return 1

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and event_path:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        body = event.get("pull_request", {}).get("body") or ""
        ids = sorted(set(CR_RE.findall(body)))
        if not ids:
            print("PR governance failure: no Change Record ID in PR body")
            return 1
        ledger = (ROOT / "docs/governance/CHANGE_LEDGER.md").read_text(encoding="utf-8")
        for cr_id in ids:
            path = ROOT / "docs/changes" / f"{cr_id}.md"
            if not path.is_file():
                print(f"PR references missing Change Record: {cr_id}")
                return 1
            if cr_id not in ledger:
                print(f"Change Record missing from ledger: {cr_id}")
                return 1

    print("Governance checks passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())