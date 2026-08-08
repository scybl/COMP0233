#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${PYTHON_BIN:-}" && -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

PYTHON_BIN="${PYTHON_BIN:-python}"

if ! "$PYTHON_BIN" -c "import numpy, requests" >/dev/null 2>&1; then
  echo "Missing Python dependencies. Run: bash scripts/setup_env.sh"
  exit 1
fi

"$PYTHON_BIN" -B -m tube_planning.evaluation \
  --network-file data/tfl_snapshot/baseline_network.csv \
  --format csv \
  data/tfl_snapshot/costs/2026-07-01.fixed-cost \
  data/tfl_snapshot/demo_criteria.cfile \
  "data/tfl_snapshot/proposals/*.csv"
