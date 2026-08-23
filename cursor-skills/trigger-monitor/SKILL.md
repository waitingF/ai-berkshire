---
name: trigger-monitor
description: 标的触发监控：研究报告产出的买卖价位带/复检节点需登记到 data/triggers.json，每日扫描比对价位是否触发、事件是否到期。本 Skill 定义何时登记、如何登记、如何本地预检，适用于全部研究产出流程（investment-research / investment-team / earnings-review / thesis-tracker / weekly-review 等）。
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
| 周检对账 | 跑 `--json` 与看板/台账交叉核对，补漏登记 |
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

- `dir`：`below`（价格 ≤ high 触发）/ `above`（价格 ≥ low 触发）/ `range`（low ≤ 价格 ≤ high 触发）
- `market`：必须对应 `codes` 里的键（A/H/US/KR/JP），否则 `--check` 报错
- `action`：报告稳健结论（买入/分批/观望/回避）；`note`：触发附加条件（红线、前提）

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
2. `python3 tools/trigger_scanner.py --check` 确认数据结构合法
3. `python3 tools/trigger_scanner.py --watch 标的名` 定点扫一遍验证

## 每日扫描与提醒

- **扫描**：`python3 tools/trigger_scanner.py`（腾讯行情 API，零依赖，写日报到 `reports/trigger-scan/`；默认不发任何通知）
- **GitHub Actions**：`.github/workflows/trigger-scan.yml` 工作日 18:00 自动扫描 + Server酱微信推送（Secret：`SERVERCHAN_SENDKEY`）；未配置 Secret 则不推送

## 提交前本地预检

任何涉及 `data/triggers.json` 或扫描器的改动，push 前必须：

```bash
bash scripts/prepush-check.sh
```

流程：`--check` 数据校验 → 全量扫描（写日报，零通知）→ `--json` 输出校验（列出触发/接近明细与建议动作）。任一步失败即终止。**预检通过 ≠ 已提交**，需用户确认后再 commit + push（先 `git pull --rebase origin main`）。

## 边界

- 触发只表示价位到达，**不代表买入信号**：是否建仓以对应 thesis/研究报告的红线与条件为准（`note` 字段带出）。
- 行情为腾讯 API 快照，A股/港股当日最新，美股/韩股/日股为最近收盘。

*本监控用于学习研究跟踪，不构成投资建议。*
