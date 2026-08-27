#!/usr/bin/env bash
# 为当前 clone 启用仓库内版本化 Git hooks。

set -euo pipefail
default_repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
repo_path="${1:-$default_repo}"

git -C "$repo_path" rev-parse --git-dir >/dev/null
git -C "$repo_path" config --local core.hooksPath .githooks

echo "✅ 已启用 Git hooks：core.hooksPath=.githooks"
echo "   pre-commit：相关监控文件快速校验"
echo "   pre-push：完整离线校验"
