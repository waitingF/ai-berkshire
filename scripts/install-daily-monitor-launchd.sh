#!/usr/bin/env bash

set -euo pipefail

label="com.ai-berkshire.daily-monitor"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
default_repo="$(cd "$script_dir/.." && pwd -P)"
repo_path="${1:-$default_repo}"
runner_path="$repo_path/scripts/run-daily-monitor-local.sh"
launch_agents_path="$HOME/Library/LaunchAgents"
logs_path="$HOME/Library/Logs/ai-berkshire"
plist_path="$launch_agents_path/$label.plist"
user_domain="gui/$(id -u)"

xml_escape() {
  printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/"/\&quot;/g' -e "s/'/\&apos;/g"
}

git -C "$repo_path" rev-parse --git-dir >/dev/null
[[ -x "$runner_path" ]] || {
  echo "错误：运行器不可执行：$runner_path" >&2
  exit 1
}

mkdir -p "$launch_agents_path" "$logs_path"

escaped_runner_path="$(xml_escape "$runner_path")"
escaped_repo_path="$(xml_escape "$repo_path")"
escaped_stdout_path="$(xml_escape "$logs_path/daily-monitor.out.log")"
escaped_stderr_path="$(xml_escape "$logs_path/daily-monitor.err.log")"

cat > "$plist_path" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$escaped_runner_path</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$escaped_repo_path</string>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>16</integer><key>Minute</key><integer>10</integer></dict>
    <dict><key>Weekday</key><integer>2</integer><key>Hour</key><integer>16</integer><key>Minute</key><integer>10</integer></dict>
    <dict><key>Weekday</key><integer>3</integer><key>Hour</key><integer>16</integer><key>Minute</key><integer>10</integer></dict>
    <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>16</integer><key>Minute</key><integer>10</integer></dict>
    <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>16</integer><key>Minute</key><integer>10</integer></dict>
  </array>
  <key>ProcessType</key>
  <string>Background</string>
  <key>StandardOutPath</key>
  <string>$escaped_stdout_path</string>
  <key>StandardErrorPath</key>
  <string>$escaped_stderr_path</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>TZ</key>
    <string>Asia/Shanghai</string>
  </dict>
</dict>
</plist>
EOF

plutil -lint "$plist_path"
launchctl bootout "$user_domain/$label" >/dev/null 2>&1 || true
launchctl bootstrap "$user_domain" "$plist_path"
launchctl enable "$user_domain/$label"

echo "✅ 已安装本机每日监控任务：$label"
echo "   时间：每周一至周五 16:10（本机时区）"
echo "   任务文件：$plist_path"
echo "   日志：$logs_path/daily-monitor.out.log"
echo "   环境变量优先读取：$HOME/.config/ai-berkshire/daily-monitor.env"
echo "   若该文件不存在，运行器会回退读取：$repo_path/.env"
