#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

command -v "${PYTHON_BIN}" >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v rclone >/dev/null || { echo "rclone is required; install/configure it before sync" >&2; exit 1; }

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/pip" install -e "${ROOT_DIR}[dev]"
chmod +x "${ROOT_DIR}/bin/arya-ops" "${ROOT_DIR}/scripts/"*.py

mkdir -p "${ROOT_DIR}/data/phase-one" "${ROOT_DIR}/data/logs"
cat <<EOF
ARYA operations installed.

Executable:
  ${ROOT_DIR}/bin/arya-ops

Use the project virtualenv:
  source ${VENV_DIR}/bin/activate

Verify:
  ${ROOT_DIR}/bin/arya-ops version
  ${ROOT_DIR}/bin/arya-ops live --json
  ${ROOT_DIR}/bin/arya-ops sync --remote drive:arya-phase-one --local-dir data/phase-one
EOF
