#!/usr/bin/env python3
"""标的触发监控 — 每日扫描脚本。

读取 data/triggers.json（结构化触发点 + 事件），用腾讯行情 API 拉取最新价，
比对"关键价位区间"是否触发，检查事件（财报日/复检日）是否到期/临近，
输出每日报告 reports/trigger-scan/trigger-scan-{YYYYMMDD}.md。

数据源：腾讯行情 API（qt.gtimg.cn，零依赖、无需鉴权、支持 A股/港股/美股/韩股/日股/ETF 批量）。
设计见 docs/2026-08-21-标的触发监控-design.md。

用法：
    python3 tools/trigger_scanner.py                 # 默认：扫描 + 输出报告
    python3 tools/trigger_scanner.py --json    # 输出 JSON 摘要（供 GitHub Actions / 本地验证消费）
    python3 tools/trigger_scanner.py --no-report     # 只打印终端摘要，不写报告文件
    python3 tools/trigger_scanner.py --watch 1       # 只扫描 watch 名单（id 或名称子串）
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIGGERS_FILE = os.path.join(ROOT, "data", "triggers.json")
REPORT_DIR = os.path.join(ROOT, "reports", "trigger-scan")
_TIMEOUT = 20
_BATCH = 30  # 腾讯行情一次查询上限（实测 30 个安全）


# ---------------------------------------------------------------------------
# 行情获取（腾讯 API，复用 ashare_data.py 的 curl --noproxy 直连方式）
# ---------------------------------------------------------------------------

def _curl_qq(codes):
    """批量查询腾讯行情，返回 {腾讯代码: 解析后的 dict}。"""
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    try:
        result = subprocess.run(
            ["/usr/bin/curl", "-s", "--noproxy", "*",
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
             url],
            capture_output=True, timeout=_TIMEOUT,
        )
        raw = result.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️ 行情请求失败: {e}", file=sys.stderr)
        return {}
    out = {}
    # 响应形如：v_sh600519="1~贵州茅台~600519~...";v_hk00700="...";
    for m in re.finditer(r'v_([^=]+)="([^"]*)"', raw):
        code, payload = m.group(1), m.group(2)
        fields = payload.split("~")
        if len(fields) < 35:
            continue
        out[code] = {
            "name": fields[1],
            "price": _to_float(fields[3]),
            "prev_close": _to_float(fields[4]),
            "change_pct": _to_float(fields[32]),
            "high": _to_float(fields[33]) if len(fields) > 33 else None,
            "low": _to_float(fields[34]) if len(fields) > 34 else None,
            "time": fields[30] if len(fields) > 30 else "",
        }
    return out


def _to_float(v):
    try:
        f = float(v)
        return f if f == f else None  # NaN → None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# 触发判定
# ---------------------------------------------------------------------------

def judge_zone(price, zone):
    """判断价格相对触发区间状态。返回 (状态, 说明)。
    状态: 'TRIGGERED' 已触发 / 'NEAR' 接近（距边界≤3%）/ 'FAR' 未触发。"""
    if price is None or price <= 0:
        return "NO_DATA", "无行情"
    low = zone.get("low")
    high = zone.get("high")
    d = zone.get("dir", "range")
    if d == "below":          # 价格 ≤ high 触发
        if price <= high:
            return "TRIGGERED", f"现价 {price:.2f} ≤ {high:.2f}（触发线）"
        if price <= high * 1.03:
            return "NEAR", f"现价 {price:.2f}，距触发线 {high:.2f} 3% 内"
        return "FAR", f"现价 {price:.2f}，触发线 {high:.2f}"
    if d == "above":          # 价格 ≥ low 触发 → 警戒（涨过警戒线/不追高），非买入触发
        if price >= low:
            return "WARN", f"现价 {price:.2f} ≥ {low:.2f}（警戒线）"
        if price >= low * 0.97:
            return "NEAR", f"现价 {price:.2f}，距警戒线 {low:.2f} 3% 内"
        return "FAR", f"现价 {price:.2f}，警戒线 {low:.2f}"
    # range：low ≤ price ≤ high 触发；区间外按距最近边界的比例判定接近
    if low is None and high is None:
        return "FAR", "无价格区间"
    if low is not None and high is not None:
        if low <= price <= high:
            return "TRIGGERED", f"现价 {price:.2f} ∈ [{low:.2f}, {high:.2f}]"
        if price < low:
            gap = (low - price) / low
            if gap <= 0.03:
                return "NEAR", f"现价 {price:.2f}，距下沿 {low:.2f} 3% 内"
            return "FAR", f"现价 {price:.2f}，区间 [{low:.2f}, {high:.2f}]"
        gap = (price - high) / high
        if gap <= 0.03:
            return "NEAR", f"现价 {price:.2f}，距上沿 {high:.2f} 3% 内"
        return "FAR", f"现价 {price:.2f}，区间 [{low:.2f}, {high:.2f}]"
    if low is not None:       # price ≥ low 触发
        if price >= low:
            return "TRIGGERED", f"现价 {price:.2f} ≥ {low:.2f}"
        if price >= low * 0.97:
            return "NEAR", f"现价 {price:.2f}，距 {low:.2f} 3% 内"
        return "FAR", f"现价 {price:.2f}，触发线 {low:.2f}"
    if price <= high:         # price ≤ high 触发
        return "TRIGGERED", f"现价 {price:.2f} ≤ {high:.2f}"
    if price <= high * 1.03:
        return "NEAR", f"现价 {price:.2f}，距 {high:.2f} 3% 内"
    return "FAR", f"现价 {price:.2f}，触发线 {high:.2f}"


def judge_event(ev, today):
    """事件到期判定。返回 (状态, 天数说明)。"""
    d = ev.get("date") or ""
    if not d:
        return "OPEN", "待定"
    try:
        ev_date = datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        return "OPEN", f"日期格式异常({d})"
    delta = (ev_date - today).days
    if delta < 0:
        return "OVERDUE", f"已到期 {-delta} 天"
    if delta == 0:
        return "TODAY", "今天到期"
    if delta <= 7:
        return "SOON", f"{delta} 天后"
    return "FUTURE", f"{delta} 天后"


_DEFAULT_EVENT_ACTIONS = {
    "财报": "财报精读",
    "公告": "核公告",
    "复检": "复检 thesis",
    "投资者日": "跟踪投资者日",
}


def event_action(ev):
    """事件到期后的动作：优先事件登记的 action，缺省按 type 映射。"""
    a = (ev.get("action") or "").strip()
    if a:
        return a
    return _DEFAULT_EVENT_ACTIONS.get(ev.get("type", ""), "复核")


# ---------------------------------------------------------------------------
# 数据校验（--check）：防止维护 triggers.json 时漂移/出错
# ---------------------------------------------------------------------------

def cmd_check():
    """校验 data/triggers.json 结构完整性。有错误返回非零退出码。"""
    with open(TRIGGERS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    errors, warns = [], []
    targets = data.get("targets", [])
    seen_ids, seen_codes = set(), set()
    valid_dir = {"below", "above", "range"}
    valid_group = {"重点", "台账"}

    for t in targets:
        tid = t.get("id", "")
        if not tid:
            errors.append("存在缺少 id 的标的")
        elif tid in seen_ids:
            errors.append(f"重复标 id：{tid}")
        seen_ids.add(tid)

        if t.get("group") not in valid_group:
            warns.append(f"{tid}：group 非法（{t.get('group')}），应为 重点/台账")

        codes = t.get("codes", {})
        if not codes:
            errors.append(f"{tid}：缺少 codes（无法拉行情）")
        for mkt, code in codes.items():
            if code in seen_codes:
                errors.append(f"{tid}：代码重复 {code}（{mkt}）")
            seen_codes.add(code)
            if not (code.startswith(("sh", "sz", "bj", "hk", "us", "kr", "jp"))):
                warns.append(f"{tid}：代码前缀异常 {code}（应 sh/sz/bj/hk/us/kr/jp）")

        for z in t.get("zones", []):
            if z.get("market") not in codes:
                errors.append(f"{tid}：zone「{z.get('label')}」引用市场 {z.get('market')} 不存在于 codes")
            if z.get("dir", "range") not in valid_dir:
                errors.append(f"{tid}：zone「{z.get('label')}」dir 非法（{z.get('dir')}）")
            low, high = z.get("low"), z.get("high")
            if low is not None and high is not None and low > high:
                errors.append(f"{tid}：zone「{z.get('label')}」low({low}) > high({high})")
            if z.get("dir") == "below" and high is None:
                errors.append(f"{tid}：zone「{z.get('label')}」dir=below 但无 high")
            if z.get("dir") == "above" and low is None:
                errors.append(f"{tid}：zone「{z.get('label')}」dir=above 但无 low")

        for ev in t.get("events", []):
            d = ev.get("date", "")
            if d:
                try:
                    datetime.strptime(d, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"{tid}：事件「{ev.get('label')}」日期格式非法（{d}），应为 YYYY-MM-DD")
            if ev.get("market") and ev.get("market") not in codes:
                warns.append(f"{tid}：事件「{ev.get('label')}」市场 {ev.get('market')} 不存在于 codes")

    n_zones = sum(len(t.get("zones", [])) for t in targets)
    n_events = sum(len(t.get("events", [])) for t in targets)
    print(f"标的数：{len(targets)}；触发区间：{n_zones}；事件：{n_events}；唯一代码：{len(seen_codes)}")
    if warns:
        print(f"\n⚠️ 警告（{len(warns)}）：")
        for w in warns:
            print(f"  - {w}")
    if errors:
        print(f"\n❌ 错误（{len(errors)}）：")
        for e in errors:
            print(f"  - {e}")
        print("\n校验未通过。")
        return 1
    print("\n✅ 校验通过。")
    return 0


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------

def write_report(targets, rows, event_rows, triggered, warned, near, today):
    """写日报：日期版 + latest 稳定入口（内容相同）。返回 (日期路径, latest 路径)。"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    dated = os.path.join(REPORT_DIR, f"trigger-scan-{today:%Y%m%d}.md")
    latest = os.path.join(REPORT_DIR, "trigger-scan-latest.md")
    lines = [
        "# 标的触发监控日报",
        "",
        f"**扫描日期**：{today}",
        f"**数据源**：[`data/triggers.json`](../../data/triggers.json)（{len(targets)} 标的 / {len(rows)} 区间 / {len(event_rows)} 到期事件）",
        f"**行情源**：腾讯行情 API（qt.gtimg.cn）",
        "",
        f"> 本页为最新日报（`trigger-scan-latest.md`）；历史日报见同目录 [`trigger-scan/`](.) 下的 `trigger-scan-YYYYMMDD.md`。",
        "",
        "---",
        "",
        "## 一、已触发价位区间",
        "",
    ]
    if triggered:
        lines.append("| 标的 | 市场 | 触发区间 | 现价 | 判定 | 动作 | 备注 |")
        lines.append("|------|------|----------|------|------|------|------|")
        for r in triggered:
            lines.append(f"| {r['name']} | {r['market']} | {r['zone_label']} | "
                         f"{r['price'] if r['price'] is not None else '-'} | {r['msg']} | "
                         f"{r['action']} | {r['note']} |")
    else:
        lines.append("无。")
    lines += ["", "## 二、警戒（涨过警戒线 / 不追高，非买入触发）", ""]
    if warned:
        lines.append("| 标的 | 市场 | 警戒区间 | 现价 | 判定 | 动作 |")
        lines.append("|------|------|----------|------|------|------|")
        for r in warned:
            lines.append(f"| {r['name']} | {r['market']} | {r['zone_label']} | "
                         f"{r['price'] if r['price'] is not None else '-'} | {r['msg']} | "
                         f"{r['action']} |")
    else:
        lines.append("无。")
    lines += ["", "## 三、接近触发（距边界 3% 内）", ""]
    if near:
        lines.append("| 标的 | 市场 | 区间 | 现价 | 判定 | 动作 | 备注 |")
        lines.append("|------|------|------|------|------|------|------|")
        for r in near:
            lines.append(f"| {r['name']} | {r['market']} | {r['zone_label']} | "
                         f"{r['price'] if r['price'] is not None else '-'} | {r['msg']} | "
                         f"{r['action']} | {r['note']} |")
    else:
        lines.append("无。")
    lines += ["", "## 四、事件提醒（到期 / 今天 / 7 天内）", ""]
    if event_rows:
        lines.append("| 标的 | 事件 | 类型 | 日期 | 状态 | 要核验的内容 |")
        lines.append("|------|------|------|------|------|--------------|")
        for r in event_rows:
            lines.append(f"| {r['name']} | {r['label']} | {r['type']} | {r['date']} | "
                         f"{r['msg']} | {r['note']} |")
    else:
        lines.append("无。")
    lines += [
        "",
        "---",
        "",
        "## 维护说明",
        "",
        "- 价位/事件来自 [`data/triggers.json`](../../data/triggers.json)，由研究结论登记，不由本脚本猜测。",
        "- 触发只表示价位到达，**不代表买入信号**：是否建仓以对应 thesis / 研究报告的红线与条件为准。",
        "- 行情为腾讯 API 快照，A股/港股为当日最新，美股/韩股/日股为最近收盘。",
        "",
        "*本扫描用于学习研究跟踪，不构成投资建议。*",
    ]
    content = "\n".join(lines) + "\n"
    with open(dated, "w", encoding="utf-8") as f:
        f.write(content)
    with open(latest, "w", encoding="utf-8") as f:
        f.write(content)
    return dated, latest


def main():
    ap = argparse.ArgumentParser(description="标的触发监控 — 每日扫描")
    ap.add_argument("--no-report", action="store_true", help="不写报告文件")
    ap.add_argument("--watch", nargs="*", default=None,
                    help="只扫描指定标的（id 或名称子串），默认全部")
    ap.add_argument("--json", action="store_true", help="终端只输出 JSON 摘要（供脚本消费）")
    ap.add_argument("--check", action="store_true", help="只校验数据文件完整性，不扫描")
    args = ap.parse_args()

    if args.check:
        sys.exit(cmd_check())

    today = date.today()
    if not os.path.exists(TRIGGERS_FILE):
        print(f"❌ 找不到 {TRIGGERS_FILE}")
        sys.exit(1)
    with open(TRIGGERS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    targets = data["targets"]
    if args.watch:
        wl = [w.lower() for w in args.watch]
        targets = [t for t in targets
                   if any(w in t["id"].lower() or w in t["name"].lower() for w in wl)]
        if not targets:
            print(f"⚠️ watch 名单无匹配：{args.watch}")
            sys.exit(0)

    # 收集去重代码并批量拉行情
    all_codes = []
    for t in targets:
        for c in t.get("codes", {}).values():
            if c not in all_codes:
                all_codes.append(c)
    quotes = {}
    for i in range(0, len(all_codes), _BATCH):
        batch = all_codes[i:i + _BATCH]
        quotes.update(_curl_qq(batch))

    # 逐标的判定
    rows = []          # 触发/接近明细
    event_rows = []    # 事件明细
    for t in targets:
        name = t["name"]
        for mkt, code in t.get("codes", {}).items():
            q = quotes.get(code, {})
            price = q.get("price")
            for z in t.get("zones", []):
                if z.get("market") != mkt:
                    continue
                st, msg = judge_zone(price, z)
                rows.append({
                    "name": name, "market": mkt, "code": code,
                    "price": price, "zone_label": z.get("label", ""),
                    "low": z.get("low"), "high": z.get("high"),
                    "dir": z.get("dir", "range"),
                    "action": z.get("action", ""), "note": z.get("note", ""),
                    "status": st, "msg": msg,
                    "change_pct": q.get("change_pct"), "qtime": q.get("time"),
                })
        for ev in t.get("events", []):
            if ev.get("done"):
                continue  # 已处理（复检完成/事件落地）的事件不再提醒
            st, msg = judge_event(ev, today)
            if st in ("OVERDUE", "TODAY", "SOON"):
                event_rows.append({
                    "name": name, "label": ev.get("label", ""),
                    "type": ev.get("type", ""), "date": ev.get("date", ""),
                    "note": ev.get("note", ""), "status": st, "msg": msg,
                    "action": event_action(ev),
                })

    # 排序：触发 > 警戒 > 接近 > 事件
    order = {"TRIGGERED": 0, "WARN": 1, "NEAR": 2, "FAR": 3, "NO_DATA": 4}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["name"]))
    ev_order = {"OVERDUE": 0, "TODAY": 1, "SOON": 2}
    event_rows.sort(key=lambda r: (ev_order.get(r["status"], 9), r.get("date", "")))

    triggered = [r for r in rows if r["status"] == "TRIGGERED"]
    warned = [r for r in rows if r["status"] == "WARN"]
    near = [r for r in rows if r["status"] == "NEAR"]
    overdue_ev = [r for r in event_rows if r["status"] == "OVERDUE"]

    # ---- 报告文件（两种模式都写，除非 --no-report）----
    report_path = None
    if not args.no_report:
        dated_path, latest_path = write_report(targets, rows, event_rows, triggered, warned, near, today)
        report_path = dated_path

    # ---- 终端输出 ----
    if args.json:
        # review_items：全部区间行（含未触发），供 prepush-check.sh 复核
        review_items = [{
            "name": r["name"], "market": r["market"],
            "zone": r["zone_label"], "dir": r["dir"],
            "low": r["low"], "high": r["high"],
            "price": r["price"], "status": r["status"], "msg": r["msg"],
            "action": r["action"], "note": r["note"],
        } for r in rows]
        summary = {
            "date": today.isoformat(),
            "scanned_targets": len(targets),
            "triggered": len(triggered), "warned": len(warned), "near": len(near),
            "events_overdue": len(overdue_ev), "events_total": len(event_rows),
            "report": report_path,
            "triggered_items": [{"name": r["name"], "market": r["market"],
                                 "zone": r["zone_label"], "price": r["price"],
                                 "action": r["action"], "msg": r["msg"]} for r in triggered],
            "warned_items": [{"name": r["name"], "market": r["market"],
                              "zone": r["zone_label"], "price": r["price"],
                              "action": r["action"], "msg": r["msg"]} for r in warned],
            "near_items": [{"name": r["name"], "market": r["market"],
                            "zone": r["zone_label"], "price": r["price"],
                            "action": r["action"], "msg": r["msg"]} for r in near],
            "events": [{"name": r["name"], "label": r["label"],
                        "status": r["status"], "msg": r["msg"],
                        "action": r["action"]} for r in event_rows],
            "review_items": review_items,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        sys.exit(0)

    print("=" * 72)
    print(f"标的触发监控 | {today}（数据源 data/triggers.json，共 {len(targets)} 标的）")
    print("=" * 72)

    print("\n🔴 已触发价位区间（价格在买入范围内）：")
    if triggered:
        for r in triggered:
            print(f"  [{r['name']}·{r['market']}] {r['zone_label']} → {r['msg']}"
                  f"（动作：{r['action']}）")
            if r["note"]:
                print(f"      注：{r['note']}")
    else:
        print("  无")

    print("\n⚠️ 警戒（涨过警戒线 / 不追高，非买入触发）：")
    if warned:
        for r in warned:
            print(f"  [{r['name']}·{r['market']}] {r['zone_label']} → {r['msg']}"
                  f"（动作：{r['action']}）")
    else:
        print("  无")

    print("\n🟡 接近触发（3% 内）：")
    if near:
        for r in near:
            print(f"  [{r['name']}·{r['market']}] {r['zone_label']} → {r['msg']}")
    else:
        print("  无")

    print("\n📅 事件提醒（到期/今天/7天内）：")
    if event_rows:
        for r in event_rows:
            flag = {"OVERDUE": "🔴", "TODAY": "🟠", "SOON": "🟡"}[r["status"]]
            print(f"  {flag} [{r['name']}] {r['label']}（{r['date'] or '待定'}，{r['msg']}）")
            if r["note"]:
                print(f"      核：{r['note']}")
    else:
        print("  无")

    if report_path:
        print(f"\n📄 报告已写入 {report_path}")


if __name__ == "__main__":
    main()
