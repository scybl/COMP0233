#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

if ! python -c "import numpy, requests" >/dev/null 2>&1; then
  echo "Missing Python dependencies. Run: bash scripts/setup_env.sh"
  exit 1
fi

python -B -m tube_planning.showcase
