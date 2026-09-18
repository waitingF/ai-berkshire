#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "$script_dir/.." && pwd -P)"
environment_file="${DAILY_MONITOR_ENV_FILE:-$HOME/.config/ai-berkshire/daily-monitor.env}"

fail() {
  echo "错误：$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
用法：scripts/run-daily-monitor-local.sh [--check]

默认执行每日监控，并在报告成功生成后提交和推送机器生成的日报文件。
--check 只同步专用 worktree 并校验监控配置，不运行监控或提交。
EOF
}

load_environment() {
  local fallback_environment_file="$repo_root/.env"

  if [[ -f "$environment_file" ]]; then
    load_environment_file "$environment_file"
    echo "已加载监控环境变量：$environment_file"
  elif [[ -f "$fallback_environment_file" ]]; then
    load_environment_file "$fallback_environment_file"
    echo "已加载监控环境变量：$fallback_environment_file"
  else
    echo "未找到监控环境变量文件；将按可用数据源执行。" >&2
  fi
}

load_environment_file() {
  local file_path="$1"
  local line
  local line_number=0
  local key
  local value

  while IFS= read -r line || [[ -n "$line" ]]; do
    line_number=$((line_number + 1))
    if [[ "$line" =~ ^[[:space:]]*$ || "$line" =~ ^[[:space:]]*# ]]; then
      continue
    fi
    if [[ ! "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]]; then
      fail "环境变量文件格式错误：${file_path}:${line_number}。请使用 KEY=VALUE 格式。"
    fi

    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    if [[ "$value" =~ ^\"(.*)\"$ || "$value" =~ ^\'(.*)\'$ ]]; then
      value="${BASH_REMATCH[1]}"
    elif [[ "$value" == \"* || "$value" == *\" || "$value" == \'* || "$value" == *\' ]]; then
      fail "环境变量文件引号不匹配：${file_path}:${line_number}。"
    fi

    export "$key=$value"
  done < "$file_path"
}

resolve_python() {
  if [[ -n "${AI_BERKSHIRE_PYTHON:-}" ]]; then
    python_bin="$AI_BERKSHIRE_PYTHON"
  elif [[ -x "$repo_root/.venv/bin/python" ]]; then
    python_bin="$repo_root/.venv/bin/python"
  else
    fail "未找到 Python。请设置 AI_BERKSHIRE_PYTHON 或创建 $repo_root/.venv。"
  fi

  [[ -x "$python_bin" ]] || fail "Python 不可执行：$python_bin"
}

resolve_branch() {
  local remote_head

  remote_head="$(git -C "$repo_root" symbolic-ref --quiet --short refs/remotes/origin/HEAD || true)"
  if [[ -n "${DAILY_MONITOR_BRANCH:-}" ]]; then
    branch="$DAILY_MONITOR_BRANCH"
  elif [[ "$remote_head" == origin/* ]]; then
    branch="${remote_head#origin/}"
  else
    branch="main"
  fi
}

acquire_lock() {
  if mkdir "$lock_directory" 2>/dev/null; then
    printf '%s\n' "$$" > "$lock_directory/pid"
    return
  fi

  local existing_pid=""
  if [[ -f "$lock_directory/pid" ]]; then
    existing_pid="$(cat "$lock_directory/pid")"
  fi

  if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
    echo "每日监控已在运行（PID $existing_pid），本次跳过。"
    exit 0
  fi

  rm -f "$lock_directory/pid"
  rmdir "$lock_directory" 2>/dev/null || fail "无法清理过期锁：$lock_directory"
  mkdir "$lock_directory"
  printf '%s\n' "$$" > "$lock_directory/pid"
}

release_lock() {
  rm -f "$lock_directory/pid"
  rmdir "$lock_directory" 2>/dev/null || true
}

prepare_worktree() {
  mkdir -p "$state_directory"
  acquire_lock
  trap release_lock EXIT

  git -C "$repo_root" rev-parse --git-dir >/dev/null
  git -C "$repo_root" fetch --prune origin "$branch"

  if [[ -e "$worktree_directory/.git" ]]; then
    git -C "$worktree_directory" rev-parse --is-inside-work-tree >/dev/null
  else
    if [[ -e "$worktree_directory" ]]; then
      [[ -d "$worktree_directory" ]] || fail "worktree 路径不是目录：$worktree_directory"
      [[ -z "$(find "$worktree_directory" -mindepth 1 -maxdepth 1 -print -quit)" ]] \
        || fail "worktree 路径非空：$worktree_directory"
      rmdir "$worktree_directory"
    fi
    git -C "$repo_root" worktree add --detach "$worktree_directory" "origin/$branch"
  fi

  git -C "$worktree_directory" fetch --prune origin "$branch"
  git -C "$worktree_directory" checkout --detach --force "origin/$branch"
  git -C "$worktree_directory" reset --hard "origin/$branch"
  git -C "$worktree_directory" clean -ffdx
  echo "已同步专用 worktree 到 origin/${branch}。"
}

resolve_generated_conflicts() {
  local conflicted_files
  local conflict_path
  local has_unexpected_conflict=false

  conflicted_files="$(git -C "$worktree_directory" diff --name-only --diff-filter=U)"
  [[ -n "$conflicted_files" ]] || return 1

  while IFS= read -r conflict_path; do
    case "$conflict_path" in
      reports/daily-monitor/* | data/monitoring-state.json) ;;
      *) has_unexpected_conflict=true ;;
    esac
  done <<< "$conflicted_files"

  if [[ "$has_unexpected_conflict" == true ]]; then
    git -C "$worktree_directory" rebase --abort || true
    fail "重放日报提交时遇到非监控产物冲突，已中止以保护远端改动。"
  fi

  while IFS= read -r conflict_path; do
    git -C "$worktree_directory" checkout --theirs -- "$conflict_path"
    git -C "$worktree_directory" add -- "$conflict_path"
  done <<< "$conflicted_files"

  GIT_EDITOR=true git -C "$worktree_directory" rebase --continue || {
    git -C "$worktree_directory" rebase --abort || true
    fail "无法继续重放日报提交。"
  }
}

push_monitor_commit() {
  local attempt

  for attempt in 1 2 3; do
    if git -C "$worktree_directory" push origin "HEAD:refs/heads/$branch"; then
      echo "日报提交已推送到 origin/${branch}。"
      return
    fi

    echo "远端已有新提交，重放日报提交（第 $attempt 次）。"
    git -C "$worktree_directory" fetch --prune origin "$branch"
    if git -C "$worktree_directory" rebase "origin/$branch"; then
      continue
    fi
    resolve_generated_conflicts || {
      git -C "$worktree_directory" rebase --abort || true
      fail "无法识别重放冲突。"
    }
  done

  fail "三次尝试后仍无法推送日报。"
}

run_monitor() {
  local monitor_exit
  local monitor_date
  local monitor_output="$worktree_directory/daily-monitor-run.json"
  local notification_output

  "$python_bin" "$worktree_directory/tools/daily_monitor.py" --check

  set +e
  "$python_bin" "$worktree_directory/tools/daily_monitor.py" --json > "$monitor_output"
  monitor_exit=$?
  set -e
  cat "$monitor_output"

  if [[ "$monitor_exit" -ne 0 && "$monitor_exit" -ne 2 ]]; then
    fail "每日监控未能生成报告，退出码 $monitor_exit。"
  fi
  if [[ "$monitor_exit" -eq 2 ]]; then
    echo "每日监控以降级状态生成报告，将照常提交机器产物。"
  fi

  notification_output="$(
    "$python_bin" "$worktree_directory/.github/scripts/notify_daily_monitor.py" \
      "$worktree_directory/reports/daily-monitor/daily-monitor-latest.json" 2>&1
  )"
  printf '%s\n' "$notification_output"
  case "$notification_output" in
    *"每日监控通知：SENT"* | *"每日监控通知：SKIPPED"*) ;;
    *) fail "每日监控通知未完成；日报未提交。" ;;
  esac

  git -C "$worktree_directory" config user.name "daily-monitor-local"
  git -C "$worktree_directory" config user.email "daily-monitor-local@localhost"
  git -C "$worktree_directory" add reports/daily-monitor/ data/monitoring-state.json
  if git -C "$worktree_directory" diff --cached --quiet; then
    echo "日报与机器状态没有变化，无需提交。"
    return
  fi

  monitor_date="$(TZ=Asia/Shanghai date '+%F')"
  git -C "$worktree_directory" commit -m "每日监控 $monitor_date"
  push_monitor_commit
}

check_only=false
if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi
case "${1:-}" in
  "") ;;
  --check) check_only=true ;;
  --help | -h)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

load_environment
resolve_python
resolve_branch
state_directory="${DAILY_MONITOR_STATE_DIR:-$HOME/Library/Application Support/ai-berkshire}"
worktree_directory="${DAILY_MONITOR_WORKTREE_DIR:-$state_directory/daily-monitor-worktree}"
lock_directory="$state_directory/daily-monitor.lock"
prepare_worktree

if [[ "$check_only" == true ]]; then
  "$python_bin" "$worktree_directory/tools/daily_monitor.py" --check
  echo "本机每日监控已就绪：worktree=${worktree_directory}，branch=${branch}"
  exit 0
fi

run_monitor
