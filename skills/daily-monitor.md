---
name: daily-monitor
description: Use when the user asks to run, validate, interpret, troubleshoot, or configure the repository's daily price, official-disclosure, event, or research-gap monitoring workflow.
---

# 每日监控：价格、正式披露与研究缺口

对 `$ARGUMENTS` 执行统一每日监控。它是增量研究入口，不是缩短版投研，也不构成买卖或仓位结论。

## 执行契约

1. 先运行 `date`，以 Asia/Shanghai 当日为数据截止日。
2. 先只读校验：`python3 tools/daily_monitor.py --check`。
3. 默认执行：`python3 tools/daily_monitor.py`；指定标的使用 `--watch 标的名`。
4. 读取生成的 `reports/daily-monitor/daily-monitor-latest.md` 与同名 JSON，报告只能有三个业务部分：
   - `价格监控`
   - `财报与正式披露监控`
   - `其他监控`
5. 解释 P0/P1/P2、待人工确认、已解除与数据源健康度；对每个标的只保留一个影响最高的下一研究流程。

## 数据和证据边界

| 层 | 允许来源与用途 |
|---|---|
| 价格 | 腾讯行情快照，只判断已登记 zone 的状态变化 |
| A 股披露 | 巨潮资讯 CNINFO 正式公告 |
| 港股披露 | HKEXnews 正式公告 |
| 美股披露 | SEC EDGAR submissions 与 Archives |
| 备用 | AKShare 只作线索；没有正式链接不得标为已验证事实 |
| AI | DeepSeek 只处理新增事实、优先级、thesis/台账缺口和下一研究流程 |

不得用一般网络搜索替代一期正式披露源。正式事实必须保留官方 HTTPS 链接；PDF/HTML 只在临时目录下载和抽取有限片段，不把 PDF、完整正文或完整提示词写入仓库。扫描件标记 `OCR_REQUIRED / 待人工确认`，一期不做 OCR。

价格达到区间只表示需要研究复核，不能自动改变 thesis 健康度。DeepSeek 可以提高程序优先级，不能降低；不得输出或执行买入、卖出、加减仓或仓位比例，不得自动修改 thesis、看板、台账、事件、`data/triggers.json` 或组合文件。

## 状态与失败处理

- `data/triggers.json` 是人工维护配置；`data/monitoring-state.json` 是机器状态，不合并。
- 正常输出仅写 `reports/daily-monitor/` 与机器状态。
- 单一数据源、正文抽取或 DeepSeek 失败时仍保留确定性价格/事件结果，生成 `DEGRADED` 报告；失败源不推进游标，AI 失败的文档保持待重试。
- 只通知新 P0/P1、状态变化、首次故障、恢复和已解除；持续状态不重复通知。
- `reports/weekly-check/` 与 `reports/trigger-scan/` 是历史归档，不再更新、合并或作为 Pages 活动入口。

## 安全本地验证

离线端到端测试，不联网也不修改仓库状态：

```bash
runtime_dir=$(mktemp -d)
python3 tools/daily_monitor.py \
  --offline-fixtures tests/fixtures/daily-monitor \
  --state-file "$runtime_dir/state.json" \
  --report-dir "$runtime_dir/reports" \
  --json
```

仅验证用户在本地环境中提供的 DeepSeek Key；使用合成数据，不扫描标的、不写报告或状态：

```bash
export DEEPSEEK_API_KEY='由用户在本地设置，禁止写入文件或日志'
export DEEPSEEK_MODEL='deepseek-v4-flash'  # 可选
python3 tools/daily_monitor.py --check-ai
```

SEC 不需要 API Key；配置免费的 `EDGAR_IDENTITY` 为真实可联系的 User-Agent，例如 `姓名 email@example.com`。不要打印任何 Secret。

## 输出解读

- P0：立即安排研究复核；P1：近期处理；P2：持续状态或低优先级观察。
- 新财报优先 `/earnings-review`；异动归因用 `/news-pulse`；论文复核用 `/thesis-tracker` 或 `/thesis-drift`；真实组合决策才使用 `/portfolio-review`。
- 监控结果用于学习和研究，不构成投资建议。
