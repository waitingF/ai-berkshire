#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCOPE="${DSH_SKILLS_SCOPE:-project}"

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
Usage: ./scripts/install-dsh-skills.sh [--project|--user]

Install AI Berkshire DeepSeek Harness skills generated from skills/*.md.

The default project scope installs to <repo>/.dsh/skills, the project-dsh
skill root (highest rank in DSH discovery) for sessions rooted in this
repository. Use --user to install to $DSH_HOME/skills (default ~/.dsh/skills)
so the skills are available across all projects.

Options:
  --project   Install to <repo>/.dsh/skills for this repository only (default)
  --user      Install to ~/.dsh/skills

Environment overrides:
  DSH_SKILLS_DIR   Destination directory (overrides --user default)
  DSH_SKILLS_SCOPE project|user (same as flags above)
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
  DEST="$ROOT/.dsh/skills"
else
  DEST="${DSH_SKILLS_DIR:-${DSH_HOME:-$HOME/.dsh}/skills}"
fi

python3 "$ROOT/scripts/generate-dsh-skills.py"
mkdir -p "$DEST"

for skill_dir in "$ROOT"/dsh-skills/*; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  rm -rf "$DEST/$name"
  cp -R "$skill_dir" "$DEST/$name"
done

chmod +x "$ROOT"/tools/*.py "$ROOT"/tools/*.sh 2>/dev/null || true

echo "Installed DeepSeek Harness skills to $DEST"
if [[ "$SCOPE" == "user" ]]; then
  echo "Skills are available across all projects. DSH watches this root; new sessions pick them up automatically."
else
  echo "Skills are scoped to this repository only (DSH project-dsh root, rank 100)."
fi
