#!/bin/bash
# 提交前本地预检：先本地验证触发监控数据与扫描 OK（不发任何通知），再决定提交推送。
# 用法：bash scripts/prepush-check.sh
# 通过后：git add ... && git commit && git pull --rebase origin main && git push origin main

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "═══ 步骤 1/3：数据完整性校验（--check，纯本地，无网络无通知）═══"
python3 tools/trigger_scanner.py --check

echo
echo "═══ 步骤 2/3：全量扫描（默认模式，只写日报，零通知）═══"
python3 tools/trigger_scanner.py 2>&1 | tail -8

echo
echo "═══ 步骤 3/3：JSON 输出校验 + 复核视图（供 GitHub Actions 消费）═══"
python3 tools/trigger_scanner.py --json 2>/dev/null > /tmp/scan-preview.json
python3 - <<'EOF'
import json
d = json.load(open("/tmp/scan-preview.json"))
print(f"  扫描标的：{d['scanned_targets']} | 触发：{d['triggered']} | 接近：{d['near']} | 事件提醒：{d['events_total']}")
print(f"  报告：{d['report']}")

def fmt_num(v):
    return f"{v:g}" if v is not None else "-"

rows = d.get("review_items", [])
rows.sort(key=lambda r: ({"TRIGGERED":0,"NEAR":1,"FAR":2,"NO_DATA":3}.get(r["status"],9), r["name"], r["zone"]))
print("\n  ┌─ 复核视图：每个标的/区间，现价落在哪里、建议动作是什么 ─┐")
print("  | 标的 | 市场 | 区间 | 现价 | 状态 | 触发带 | 距触发 | 建议动作 | 备注")
print("  |" + "-" * 100 + "|")
for r in rows:
    low, high, pr, st = r["low"], r["high"], r["price"], r["status"]
    if r["dir"] == "below":
        band = f"≤{fmt_num(high)}"
    elif r["dir"] == "above":
        band = f"≥{fmt_num(low)}"
    else:
        band = f"{fmt_num(low)}~{fmt_num(high)}"
    gap = ""
    if st in ("TRIGGERED", "NO_DATA"):
        gap = {"TRIGGERED": "已触发", "NO_DATA": "无行情"}[st]
    elif r["dir"] == "below":
        gap = f"{(pr/high - 1)*100:+.1f}%" if pr and high else "-"
    elif r["dir"] == "above":
        gap = f"{(pr/low - 1)*100:+.1f}%" if pr and low else "-"
    else:
        if pr is not None and low is not None and high is not None:
            if pr < low:
                gap = f"下方{(low/pr - 1)*100:.1f}%"
            else:
                gap = f"上方{(pr/high - 1)*100:.1f}%"
    flag = {"TRIGGERED":"🔴","NEAR":"🟡","FAR":"  ","NO_DATA":"⚪"}[st]
    print(f"  | {r['name']} | {r['market']} | {r['zone']} | {fmt_num(pr)} | {flag}{st:<9} | {band:<12} | {gap:<8} | {r['action']} | {r['note'][:20]}")

print("\n  ▲ 状态：已触发🔴 / 接近🟡(3%内) / 未触发 / 无行情⚪；距触发：负=已在带内下方，正=还差百分之几")
EOF

echo
echo "✅ 本地预检通过（本次未发送任何通知：微信推送需 GitHub Secret，仅在 Actions 中发送）"
echo "   确认数据 OK 后，再执行提交与推送。"
