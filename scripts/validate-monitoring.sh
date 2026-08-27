#!/usr/bin/env bash
# 监控规则统一只读校验入口：本地 hooks 与 GitHub Actions 共用。

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

mode="${1:---full}"
if [[ "$mode" != "--fast" && "$mode" != "--full" ]]; then
  echo "用法：bash scripts/validate-monitoring.sh [--fast|--full]" >&2
  exit 2
fi

echo "═══ 监控配置校验 ═══"
python3 tools/trigger_scanner.py --check
python3 tools/daily_monitor.py --check

echo
echo "═══ 生成技能一致性校验 ═══"
python3 scripts/sync-codex-skills.py --check
python3 scripts/sync-cursor-skills.py --check
python3 scripts/generate-dsh-skills.py --check

if [[ "$mode" == "--fast" ]]; then
  echo
  echo "✅ 监控规则快速校验通过。"
  exit 0
fi

echo
echo "═══ 全量单元测试 ═══"
python3 -m unittest discover -s tests -p 'test_*.py' -v

echo
echo "═══ Python 语法校验（只读）═══"
python3 - <<'PY'
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
