#!/usr/bin/env bash
# 监控规则统一只读校验入口：本地 hooks 与 GitHub Actions 共用。

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

run_python() {
  bash scripts/run-local-python.sh "$@"
}

mode="${1:---full}"
if [[ "$mode" != "--fast" && "$mode" != "--full" ]]; then
  echo "用法：bash scripts/validate-monitoring.sh [--fast|--full]" >&2
  exit 2
fi

echo "═══ 监控配置校验 ═══"
run_python tools/trigger_scanner.py --check
run_python tools/daily_monitor.py --check

echo
echo "═══ 生成技能一致性校验 ═══"
run_python scripts/sync-codex-skills.py --check
run_python scripts/sync-cursor-skills.py --check
run_python scripts/generate-dsh-skills.py --check

if [[ "$mode" == "--fast" ]]; then
  echo
  echo "✅ 监控规则快速校验通过。"
  exit 0
fi

echo
echo "═══ 全量单元测试 ═══"
run_python -m unittest discover -s tests -p 'test_*.py' -v

echo
echo "═══ Python 语法校验（只读）═══"
run_python - <<'PY'
import ast
import subprocess
from pathlib import Path

paths = subprocess.run(
    ["git", "ls-files", "*.py"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
for raw_path in paths:
    path = Path(raw_path)
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print(f"Checked {len(paths)} tracked Python files")
PY

echo
echo "✅ 监控规则完整校验通过。"
