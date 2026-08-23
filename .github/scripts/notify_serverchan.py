#!/usr/bin/env python3
"""读取 trigger_scanner.py --json 的输出，通过 Server酱（sctapi.ftqq.com）推送微信通知。

推送内容用 Markdown 表格（Server酱 Turbo 渲染表格，微信里显示为表格）。

用法：
    python3 tools/trigger_scanner.py --json > scan.json
    python3 .github/scripts/notify_serverchan.py scan.json          # 发送
    python3 .github/scripts/notify_serverchan.py scan.json --preview  # 只预览不发送（无需 key）
    python3 .github/scripts/notify_serverchan.py scan.json --force   # 无触发也发摘要

需要环境变量 SERVERCHAN_SENDKEY（Server酱 Turbo 的 SendKey，存为 GitHub Secret）。
默认"有触发或事件提醒才推送"。
"""

import argparse
import json
import os
import subprocess
import sys

_TIMEOUT = 30


def _post(url, data):
    """用 curl --noproxy 直连（与仓库其他工具一致，绕过系统代理）。"""
    result = subprocess.run(
        ["/usr/bin/curl", "-s", "--noproxy", "*",
         "-X", "POST", "--data-urlencode", f"title={data['title']}",
         "--data-urlencode", f"desp={data['desp']}", url],
        capture_output=True, timeout=_TIMEOUT,
    )
    if result.returncode != 0:
        raise ConnectionError(f"curl 请求失败: {result.stderr.decode(errors='replace')[:200]}")
    return result.stdout.decode("utf-8", errors="replace")


def build_desp(scan, include_warn=False):
    """构建 Markdown 表格形式的推送正文。返回 (title, desp)。
    include_warn=False：警戒触发（涨过警戒线/不追高）不放进推送，避免干扰。"""
    triggered = scan.get("triggered_items", [])
    warned = scan.get("warned_items", [])
    events = scan.get("events", [])
    near_items = scan.get("near_items", [])

    lines = [f"**扫描标的**：{scan.get('scanned_targets')} 个\n"]

    # 已触发价位 —— 表格（仅价格在买入范围内）
    if triggered:
        lines.append(f"## 🔴 已触发价位（{len(triggered)}）\n")
        lines.append("| 标的 | 市场 | 触发区间 | 现价 | 建议动作 | 判定 |")
        lines.append("|---|---|---|---|---|---|")
        for it in triggered:
            price = f"{it['price']:g}" if it.get("price") is not None else "-"
            msg = it.get("msg", "").replace("现价 ", "").replace("（触发线）", "")
            lines.append(f"| {it['name']} | {it['market']} | {it['zone']} | {price} "
                         f"| {it.get('action') or '-'} | {msg} |")
        lines.append("")

    # 警戒触发 —— 单独一组，默认不含（include_warn=True 才放）
    if include_warn and warned:
        lines.append(f"## ⚠️ 警戒（涨过警戒线/不追高，{len(warned)}）\n")
        lines.append("| 标的 | 市场 | 警戒区间 | 现价 | 建议动作 |")
        lines.append("|---|---|---|---|---|")
        for it in warned:
            price = f"{it['price']:g}" if it.get("price") is not None else "-"
            lines.append(f"| {it['name']} | {it['market']} | {it['zone']} | {price} "
                         f"| {it.get('action') or '-'} |")
        lines.append("")

    # 事件提醒 —— 表格（含动作列）
    if events:
        overdue = [e for e in events if e["status"] == "OVERDUE"]
        today = [e for e in events if e["status"] == "TODAY"]
        soon = [e for e in events if e["status"] == "SOON"]
        if overdue:
            lines.append(f"## 🔴 事件已到期（{len(overdue)}）\n")
            lines.append("| 标的 | 事件 | 动作 |")
            lines.append("|---|---|---|")
            for e in overdue:
                lines.append(f"| {e['name']} | {e['label']} | {e.get('action') or '-'} |")
            lines.append("")
        if today:
            lines.append(f"## 🟠 今天到期（{len(today)}）\n")
            lines.append("| 标的 | 事件 | 动作 |")
            lines.append("|---|---|---|")
            for e in today:
                lines.append(f"| {e['name']} | {e['label']} | {e.get('action') or '-'} |")
            lines.append("")
        if soon:
            lines.append(f"## 🟡 7 天内到期（{len(soon)}）\n")
            lines.append("| 标的 | 事件 | 动作 | 距到期 |")
            lines.append("|---|---|---|---|")
            for e in soon:
                lines.append(f"| {e['name']} | {e['label']} | {e.get('action') or '-'} | {e['msg']} |")
            lines.append("")

    if near_items:
        lines.append(f"## 🟡 接近触发（距边界 3% 内，{len(near_items)}）\n")
        lines.append("| 标的 | 市场 | 区间 | 现价 | 建议动作 | 判定 |")
        lines.append("|---|---|---|---|---|---|")
        for it in near_items:
            price = f"{it['price']:g}" if it.get("price") is not None else "-"
            msg = it.get("msg", "").replace("现价 ", "")
            lines.append(f"| {it['name']} | {it['market']} | {it['zone']} | {price} "
                         f"| {it.get('action') or '-'} | {msg} |")
        lines.append("")

    desp = "\n".join(lines)
    title = f"标的触发监控 {scan.get('date', '')}"
    return title[:32], desp


def main():
    ap = argparse.ArgumentParser(description="Server酱微信推送（表格模式）")
    ap.add_argument("scan_json", help="trigger_scanner.py --json 的输出文件")
    ap.add_argument("--force", action="store_true", help="无触发也推送（发摘要）")
    ap.add_argument("--preview", action="store_true", help="只打印推送正文预览，不发送（无需 key）")
    ap.add_argument("--warn", action="store_true",
                    help="同时推送警戒触发（涨过警戒线/不追高）；默认不推，避免干扰")
    args = ap.parse_args()

    with open(args.scan_json, encoding="utf-8") as f:
        scan = json.load(f)

    triggered = scan.get("triggered_items", [])
    events = scan.get("events", [])

    if not (triggered or events) and not args.force:
        print("无触发、无事件提醒，跳过推送")
        return

    title, desp = build_desp(scan, include_warn=args.warn)

    if args.preview:
        print(f"标题：{title}\n")
        print(desp)
        return

    sendkey = os.environ.get("SERVERCHAN_SENDKEY", "").strip()
    if not sendkey:
        print("❌ 未设置 SERVERCHAN_SENDKEY 环境变量（或加 --preview 只看预览）", file=sys.stderr)
        sys.exit(1)

    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    try:
        resp = _post(url, {"title": title, "desp": desp})
    except Exception as e:
        print(f"❌ 推送失败: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        body = json.loads(resp)
    except ValueError:
        body = {"raw": resp[:200]}
    if body.get("code") == 0:
        print("✅ Server酱推送成功")
    else:
        print(f"⚠️ Server酱返回异常: {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
