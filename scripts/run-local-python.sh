#!/usr/bin/env bash
# Run repository Python commands with the project virtual environment when present.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_root="${AI_BERKSHIRE_VENV:-$repo_root/.venv}"

if [[ -n "${AI_BERKSHIRE_PYTHON:-}" ]]; then
  exec "$AI_BERKSHIRE_PYTHON" "$@"
fi

if [[ -x "$venv_root/bin/python" ]]; then
  exec "$venv_root/bin/python" "$@"
fi

exec python3 "$@"
