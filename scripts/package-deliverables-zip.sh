#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deliverables/relay-command-desk-source.zip"

cd "$ROOT"

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git archive --format=zip --output="$OUT" HEAD
  echo "Wrote $OUT via git archive"
  exit 0
fi

rm -f "$OUT"
zip -r "$OUT" . \
  -x "./.git/*" \
  -x "./.venv/*" \
  -x "./apps/api/.venv/*" \
  -x "./**/node_modules/*" \
  -x "./apps/web/dist/*" \
  -x "./.env" \
  -x "./**/__pycache__/*" \
  -x "./**/.pytest_cache/*" \
  -x "./**/.ruff_cache/*" \
  -x "./**/htmlcov/*" \
  -x "./.coverage" \
  -x "./**/.coverage" \
  -x "./**/*.tsbuildinfo" \
  -x "./deliverables/relay-command-desk-source.zip"
echo "Wrote $OUT via zip"
