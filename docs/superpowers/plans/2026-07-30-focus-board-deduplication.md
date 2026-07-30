# 重点标的与建议台账去重 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将重点标的从买卖建议跟踪表移除，改由重点标的看板独立维护。

**Architecture:** 修改两份活文档的主表、汇总和交叉说明；同时更新两个既有设计文档，将「重点看板优先」固化为维护规则。全部内容是 Markdown，无运行时依赖。

**Tech Stack:** Markdown、`rg`、`git diff --check`。

## Global Constraints

- 重点标的看板中出现的标的不进入买卖建议跟踪表。
- 仅移除腾讯、拼多多、美团、微软、Accenture、中国平安的 8 条既有建议事件。
- 台账汇总必须为 40 条、待触发 38、已关闭 2、近季命中率 1/1。
- 不改动其他研究报告或用户已有未跟踪文件。

---

### Task 1: 去除重复事件并更新台账边界

**Files:**
- Modify: `reports/买卖建议跟踪表.md`

- [x] 删除腾讯、拼多多（两条）、美团、微软、Accenture（两条）、中国平安的 8 个主表行。
- [x] 更新页眉收录规则、台账统计、未收录说明及维护提示，明确重点看板标的不再入账。
- [x] 用精确 ID 检索确认没有上述重点标的的主表条目残留。

### Task 2: 明确看板与台账分工

**Files:**
- Modify: `reports/重点标的看板.md`

- [x] 把交叉说明和摘要改为「非重点标的」范围，并说明重点标的在看板内独立跟踪。
- [x] 将摘要数值改为台账的更新后数值。
- [x] 保留主表中的所有重点标的行与其动作说明。

### Task 3: 固化维护规则并验证

**Files:**
- Modify: `docs/2026-07-20-建议跟踪台账-design.md`
- Modify: `docs/2026-07-16-重点标的看板-design.md`

- [x] 将台账收录范围改为排除重点标的看板内标的，并将看板定义为重点标的的动作跟踪入口。
- [x] 运行 `git diff --check`；使用表格分隔行计数和状态/结果搜索复核 40 行及汇总。
