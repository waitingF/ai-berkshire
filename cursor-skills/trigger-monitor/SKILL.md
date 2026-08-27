---
name: trigger-monitor
description: Use when a research report contains an explicit price band, review date, earnings checkpoint, or other trigger that must be registered and validated for daily monitoring.
---

## Cursor adapter note

This skill is generated from `skills/trigger-monitor.md` so Claude Code, Codex, and Cursor users share one canonical workflow.

- Treat `$ARGUMENTS` as the user's request in the current Cursor thread.
- When the source mentions Claude-only surfaces such as Task, Agent, WebSearch, Bash, Read, or Write, use the closest Cursor capability available in this session: Task/subagent tools for parallel research, WebSearch or browser MCP for live data, Shell for local commands, and Read/Write for workspace files.
- Use shared project tools from `tools/` in this repository. Prefer running commands from the repository root with paths like `python3 tools/financial_rigor.py ...`; if the current thread starts outside the repo, locate the actual checkout path first instead of assuming a fixed home-directory path.
- Before starting research, run the `date` command to confirm today's date; treat it as the baseline for "latest" data and state the data cutoff date in the report header. Never assume the current date from training data.
- Preserve the research quality rules from `AGENTS.md`: cross-check financial data, use exact arithmetic tools for valuation/math, and clearly label uncertainty and source gaps.

# 标的触发监控：价位登记 + 事件跟踪

对所有研究流程的产出执行**触发点登记**：凡报告含明确买卖/观望建议价位带、或复检/财报节点，必须登记到 `data/triggers.json`，并说明每日扫描与本地预检方式。

**核心原则：没有登记 = 该触发点不在监控内。**

## 何时登记（强制时机）

| 时机 | 动作 |
|------|------|
| 研究报告产出时 | 含**明确买卖/观望价位带**或**复检节点** → 立即登记 |
| 复检/财报完成后 | 对应事件加 `"done": true`（保留留档，不再提醒） |
| 每日完整性检查 | 查看每日监控“其他监控”的覆盖缺口，人工核验后补漏登记 |
| 价位带修正 | 直接改 JSON 后跑 `--check` |

**不登记的场景**：只有分析、无明确价位/节点建议的报告；估值类触发（PE/PS 线依赖财务数据，仅在 note 注明，不设 zone）。

## 如何登记（改 data/triggers.json）

### ① 给已有标的加价位带（zones）

```json
"zones": [
  {"label": "加仓带", "dir": "range", "low": 400, "high": 430,
   "market": "H", "action": "评估加仓",
   "note": "仅当红线未触或Q3证实FCF转正+AI回收"}
]
```

- `dir`：`below`（价格 ≤ high 触发）/ `range`（价格进入区间或低于 low，统一在价格 ≤ high 时触发）/ `above`（价格 ≥ low 触发 `WARN`）
- `market`：必须对应 `codes` 里的键（A/H/US/KR/JP），否则 `--check` 报错
- `action`：报告稳健结论（买入/分批/观望/回避）；`note`：触发附加条件（红线、前提）

同一标的、同一市场的组合约束：

- 下行评估条件只能有一个：`below` 或 `range` 二选一；`range` 必须同时提供 `low/high`。
- 可以额外登记一个 `above` 估值警戒线，用于“不追高/复核仓位”，触发状态为 `WARN`，不代表卖出。
- 同时存在下行评估条件和 `above` 时，必须满足 `above.low > 下行条件.high`，避免同一价格同时触发相反含义。
- 允许：`below`、`range`、`above`、`below + above`、`range + above`。
- 禁止：`below + range`、多个 `above`、`below + range + above`、上下条件重叠。

```json
"zones": [
  {"label": "研究性分批评估带", "dir": "range", "low": 80, "high": 90,
   "market": "US", "action": "分批评估", "note": "仍须核验经营条件"},
  {"label": "估值警戒线", "dir": "above", "low": 120,
   "market": "US", "action": "不追高，复核仓位", "note": "仅为研究警戒"}
]
```

### ② 加/改事件（events）

```json
"events": [
  {"date": "2026-09-30", "type": "财报", "label": "2026Q3财报",
   "note": "盯Q3 FCF转正、AI预付款回收", "market": "H"}
]
```

- 处理完 → 加 `"done": true`；演变成新周期事件 → 另加新事件

### ③ 新标的全新建 target

```json
{"id": "新标的", "name": "xx", "group": "重点",
 "codes": {"H": "hk0xxxx"}, "source": "来源",
 "links": [...], "zones": [...], "events": [...]}
```

### 改完必做

1. 更新文件顶部 `"updated": "YYYY-MM-DD"`
2. `python3 tools/daily_monitor.py --check` 确认配置与机器状态合法
3. 用临时状态与报告目录定点验证，避免污染正式运行状态：

```bash
runtime_dir=$(mktemp -d)
python3 tools/daily_monitor.py --no-ai --watch 标的名 \
  --state-file "$runtime_dir/state.json" \
  --report-dir "$runtime_dir/reports"
```

## 每日扫描与提醒

- **扫描**：`python3 tools/daily_monitor.py`（写入统一 `reports/daily-monitor/` 报告；价格只是三个业务部分之一）
- **GitHub Actions**：`.github/workflows/daily-monitor.yml` 工作日 17:30（Asia/Shanghai）运行；只通知状态变化，未配置 `SERVERCHAN_SENDKEY` 则跳过通知

## 提交前本地预检

任何涉及 `data/triggers.json` 或扫描器的改动，push 前必须：

```bash
bash scripts/prepush-check.sh
```

流程保留旧扫描器结构校验，并验证统一每日监控的价格状态兼容性。任一步失败即终止。**预检通过 ≠ 已提交**，需用户确认后再 commit + push（先 `git pull --rebase origin main`）。

## 边界

- 触发只表示价位到达，**不代表买入信号**：是否建仓以对应 thesis/研究报告的红线与条件为准（`note` 字段带出）。
- 行情为腾讯 API 快照，A股/港股当日最新，美股/韩股/日股为最近收盘。

*本监控用于学习研究跟踪，不构成投资建议。*
