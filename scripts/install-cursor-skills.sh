#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCOPE="${CURSOR_SKILLS_SCOPE:-user}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      SCOPE="project"
      shift
      ;;
    --user)
      SCOPE="user"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./scripts/install-cursor-skills.sh [--user|--project]

Install AI Berkshire Cursor skills generated from skills/*.md.

Options:
  --user      Install to ~/.cursor/skills (default)
  --project   Install to <repo>/.cursor/skills for this repository only

Environment overrides:
  CURSOR_SKILLS_DIR   Destination directory (overrides --user default)
  CURSOR_SKILLS_SCOPE user|project (same as flags above)
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$SCOPE" == "project" ]]; then
  DEST="$ROOT/.cursor/skills"
else
  DEST="${CURSOR_SKILLS_DIR:-$HOME/.cursor/skills}"
fi

python3 "$ROOT/scripts/sync-cursor-skills.py"
mkdir -p "$DEST"

for skill_dir in "$ROOT"/cursor-skills/*; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  rm -rf "$DEST/$name"
  cp -R "$skill_dir" "$DEST/$name"
done

chmod +x "$ROOT"/tools/*.py "$ROOT"/tools/*.sh 2>/dev/null || true

echo "Installed Cursor skills to $DEST"
echo "Do not install into ~/.cursor/skills-cursor; that directory is reserved by Cursor."
if [[ "$SCOPE" == "user" ]]; then
  echo "Skills are available across all projects. Restart Cursor or start a new chat if needed."
else
  echo "Skills are scoped to this repository only."
fi
