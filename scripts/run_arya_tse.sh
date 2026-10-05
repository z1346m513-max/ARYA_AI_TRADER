#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
export PYTHONPATH=src
CMD="${1:-list-symbols}"
TICKER="${2:-FOOLAD}"
case "$CMD" in
  analyze) python -m arya.cli.main analyze --ticker "$TICKER" ;;
  list-symbols) python -m arya.cli.main list-symbols ;;
  scan) python -m arya.cli.main scan ;;
  *) echo "Usage: $0 {analyze|list-symbols|scan} [TICKER]"; exit 1 ;;
esac
