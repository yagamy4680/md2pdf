#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "md2pdf: uv is required: https://docs.astral.sh/uv/" >&2
  exit 127
fi

exec uv run --project "$ROOT" python "$ROOT/md2pdf.py" "$@"
