#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

if [[ -n "${CONDA_PREFIX:-}" || -n "${VIRTUAL_ENV:-}" ]]; then
  PYTHON_BIN="${PYTHON_BIN:-python}"
else
  PYTHON_BOOTSTRAP="${PYTHON_BOOTSTRAP:-python3}"
  if [[ ! -d .venv ]]; then
    "$PYTHON_BOOTSTRAP" -m venv .venv
  fi

  source .venv/bin/activate
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")
PY

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt
"$PYTHON_BIN" -m pip install -e ".[dev]"

echo "Environment ready. Run: bash scripts/run_demo.sh"
