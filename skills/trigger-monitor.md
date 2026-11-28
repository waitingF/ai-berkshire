---
name: trigger-monitor
description: Use when a research report contains an explicit price band, review date, earnings checkpoint, or other trigger that must be registered and validated for daily monitoring.
---

# 标的触发监控：价位登记 + 事件跟踪

对所有研究流程的产出执行**触发点登记**：凡报告含明确买卖/观望建议价位带、或复检/财报节点，必须登记到 `data/triggers.json`，并说明每日扫描与本地预检方式。

**核心原则：未登记价格不在监控内；事件登记仅供人工复核，当前每日监控不自动扫描或提醒事件。**

## 价带与监控主索引同源

- 切换监控主报告时，同时核对并更新该标的的 `zones`、`action`、`note` 和上行警戒线，使日报链接与实际监控条件一致。`source` 写明价格依据报告、日期及替代关系。
- 主索引采用最新包含明确价带的公司研究或财报精读。无交易价带的访谈、Checklist、单独压力情景作为辅助材料，在 `source` 注明路径，不以较新日期覆盖价格依据报告。
- 最新财报若明确延续原方案或要求进入其引用的原研究带，可以继承该区间；`links` 保留被引用报告，`source` 和 `note` 交代数值出处及最新经营前提。
- 最新有效判断没有明确价格区间且未继承旧价带时，保留报告和人工复核记录，令 `zones` 为空。PE/PS 条件只记入说明，不猜测静态价格。
- 上行警戒采用报告明确给出的价格复核阈值；旧线没有新报告依据时停用，不能把模型乐观目标价临时改成卖出线。

## 何时登记（强制时机）

| 时机 | 动作 |
|------|------|
| 研究报告产出时 | 含**明确买卖/观望价位带**或**复检节点** → 立即登记 |
| 复检/财报完成后 | 对应事件加 `"done": true`（保留留档，不再提醒） |
| 人工复核 | 根据研究报告与台账补漏登记；当前每日监控不执行研报完整性检查 |
| 价位带修正 | 直接改 JSON 后跑 `--check` |

**不登记的场景**：只有分析、无明确价位/节点建议的报告；估值类触发（PE/PS 线依赖财务数据，仅在 note 注明，不设 zone）。

## 如何登记（改 data/triggers.json）

**先查重，再修改**：按交易所及股票代码查找 `targets`，再用公司中文/英文全称、`source` 和 `links` 中的既有报告核对同一公司；ADR 与本地上市证券也要核实归属。若已有同标的 target，沿用其 `id` 和 `name`，在该条内维护代码、去重后的报告链接、价位带和事件，保留仍有效的历史记录及已完成事件。若因中英文命名已有重复 target，合并到同一条，修复引用后删除重复项；遵守下方同市场价位带约束。只有确认没有现有 target 时才新建，不能仅因报告目录或输入语言不同就建第二条。报告链接应指向复用后的同标的目录，并确认文件存在。

### ① 给已有标的加价位带（zones）

```json
"zones": [
  {"label": "加仓带", "dir": "range", "low": 400, "high": 430,
   "market": "H", "action": "评估加仓",
   "note": "仅当红线未触或Q3证实FCF转正+AI回收"}
]
```

- `dir`：`below`（价格 ≤ high 触发）/ `range`（价格进入区间或低于 low，统一在价格 ≤ high 时触发）/ `above`（价格 ≥ low 触发 `WARN`）
- `market`：必须对应 `codes` 里的键（A/H/US/KR/JP/FR/UK/SE/NL/DE/AU/TW），否则 `--check` 报错。海外本地行情使用 `yahoo:` 代码，例如 `"UK": "yahoo:CHG.L"`；币种和后缀约束见 [每日监控](daily-monitor.md) 的“行情市场与计价”。
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
python3 tools/daily_monitor.py --watch 标的名 \
  --state-file "$runtime_dir/state.json" \
  --report-dir "$runtime_dir/reports"
```

## 每日扫描与提醒

- **扫描**：`python3 tools/daily_monitor.py`（主动刷新 `reports/daily-monitor/` 中的日期报告与 latest Markdown/JSON，只运行价格监控）
- **GitHub Actions**：`.github/workflows/daily-monitor.yml` 按 workflow 中的工作日配置运行；只通知价格状态与行情源健康度变化，未配置 `SERVERCHAN_SENDKEY` 则跳过通知

## 提交前本地预检

任何涉及 `data/triggers.json` 或扫描器的改动，push 前必须：

```bash
bash scripts/prepush-check.sh
```

流程保留旧扫描器结构校验，并验证统一每日监控的价格状态兼容性。任一步失败即终止。**预检通过 ≠ 已提交**，需用户确认后再 commit + push（先 `git pull --rebase origin main`）。

## 边界

- 触发只表示价位到达，**不代表买入信号**：是否建仓以对应 thesis/研究报告的红线与条件为准（`note` 字段带出）。
- 当前每日监控使用腾讯与 Yahoo Finance 本地市场行情快照，休市时展示最近交易时点；Yahoo 行情可能延迟。价格保留当地币种（GBp 为便士），不自动换汇或替换为 ADR。旧 `trigger_scanner.py` 扫描仅用于兼容预检，活动行情入口为 `daily_monitor.py`。

*本监控用于学习研究跟踪，不构成投资建议。*
