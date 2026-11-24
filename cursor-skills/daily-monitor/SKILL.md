---
name: daily-monitor
description: Use when the user asks to refresh, validate, interpret, troubleshoot, or configure the repository's daily price monitoring workflow.
---

## Cursor adapter note

This skill is generated from `skills/daily-monitor.md` so Claude Code, Codex, and Cursor users share one canonical workflow.

- Treat `$ARGUMENTS` as the user's request in the current Cursor thread.
- When the source mentions Claude-only surfaces such as Task, Agent, WebSearch, Bash, Read, or Write, use the closest Cursor capability available in this session: Task/subagent tools for parallel research, WebSearch or browser MCP for live data, Shell for local commands, and Read/Write for workspace files.
- Use shared project tools from `tools/` in this repository. Prefer running commands from the repository root with paths like `python3 tools/financial_rigor.py ...`; if the current thread starts outside the repo, locate the actual checkout path first instead of assuming a fixed home-directory path.
- Before starting research, run the `date` command to confirm today's date; treat it as the baseline for "latest" data and state the data cutoff date in the report header. Never assume the current date from training data.
- Preserve the research quality rules from `AGENTS.md`: cross-check financial data, use exact arithmetic tools for valuation/math, and clearly label uncertainty and source gaps.

# 每日监控：价格监控

对 `$ARGUMENTS` 执行价格监控。输入为 `data/triggers.json` 中的价格区间和腾讯行情快照；结果用于研究复核，不构成买卖或仓位结论。

## 执行契约

1. 先运行 `date`，以 Asia/Shanghai 当日为数据截止日。
2. 先只读校验：`python3 tools/daily_monitor.py --check`。
3. 主动刷新：`python3 tools/daily_monitor.py`；该命令直接更新日期报告、latest Markdown/JSON 和价格机器状态，无需 AI 或公告源凭证。
4. 读取 `reports/daily-monitor/daily-monitor-latest.md` 与同名 JSON；页面展示所有已登记标的的 `价格监控`，包含价格区间、现价、距边界、状态和已登记本地研究链接。同一标的多个价格区间分别展示；未登记有效价格区间的标的展示行情、标注未评级。
5. 解释 P0/P1/P2 和行情源健康度。达到区间只触发研究复核，不能自动改变 thesis、人工登记或组合。

## 范围与状态

- 正常输出仅写 `reports/daily-monitor/` 与 `data/monitoring-state.json`；人工配置 `data/triggers.json` 保持不变。
- 当前流程已移除 CNINFO/HKEX/SEC 公告采集、正文抽取、DeepSeek 判断、研报完整性检查和事件监控；暂不建立独立公告页面。
- 保留已有公告游标、待处理文档、事件及研究缺口状态；本流程仅更新 `price_states`、行情源健康度与运行日期。
- 行情源失败时仍生成 `DEGRADED` 报告；只对价格状态变化及行情首次故障、恢复产生通知事项，持续状态不重复通知。
- Python 刷新命令本身不提交、不推送、不发送通知。GitHub Actions 与 `scripts/run-daily-monitor-local.sh` 使用现有发布流程提交机器产物后，由 Pages 展示 latest。
- 自动运行时间以 `.github/workflows/daily-monitor.yml` 和本机 launchd 配置为准。
- `reports/trigger-scan/` 为历史归档；过去的合并日报保留，Pages 活动入口仍钉 `reports/daily-monitor/daily-monitor-latest.md`。

## 指定标的与离线验证

定点扫描使用独立状态和输出目录，避免覆盖全量价格页：

```bash
runtime_dir=$(mktemp -d)
python3 tools/daily_monitor.py --watch 标的名 \
  --state-file "$runtime_dir/state.json" \
  --report-dir "$runtime_dir/reports"
```

离线验证只读取合成行情夹具，不联网：

```bash
runtime_dir=$(mktemp -d)
python3 tools/daily_monitor.py \
  --offline-fixtures tests/fixtures/daily-monitor \
  --state-file "$runtime_dir/state.json" \
  --report-dir "$runtime_dir/reports" \
  --json
```

## 展示与排序

- P0 表示达到已登记研究复核条件；P1 表示距边界不超过 5% 或行情待核验；P2 表示尚未接近或此前条件已解除。三档全部展示；未登记价格区间的标的用 `-` 表示未评级，排在末尾。上涨警戒线不参与价格监控。
- 先按 P0 → P1 → P2 → 未评级排序，同级内按距边界百分比从大到小排列；缺失距离排同级末尾，距离相同再按名称、事项标题和唯一标识稳定排序。
- 距离统一为 `abs(现价 - 触发边界) / 触发边界`；`below` 取上限，区间取上界，仅有下限时取下限。P0 也显示百分比；排序使用未四舍五入的数值。

## 提交前自动刷新

每个新 clone 执行一次 `bash scripts/install-git-hooks.sh`，启用版本化 `.githooks/pre-commit`。此后本地每次正常 `git commit` 都先联网刷新腾讯行情，并将 latest Markdown/JSON 和当日 Markdown 三个文件暂存进本次提交；推送到 main 后由现有 Pages workflow 发布。

提交前刷新使用正式状态的临时副本，不改正式 `data/monitoring-state.json`，不发送通知，以保留定时监控的通知基线。行情缺失时允许提交标注 `DEGRADED` 的报告；程序执行或暂存失败时阻止提交。监控配置和代码有未暂存改动时，先完整暂存相关文件再提交。该刷新只暂存本次生成的三个日报文件。

监控结果用于学习和研究，不构成投资建议。
