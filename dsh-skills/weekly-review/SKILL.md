---
name: weekly-review
description: "周检：重点优先的研究待办分诊"
---

## DeepSeek Harness adapter note

This skill is generated from `skills/weekly-review.md` so Claude Code, Codex, Cursor, and DeepSeek Harness users share one canonical workflow.

- Treat `$ARGUMENTS` as the user's request in the current DeepSeek Harness session.
- When the source mentions Claude-only surfaces such as Task, Agent, WebSearch, Bash, Read, or Write, use the closest DeepSeek Harness capability available in this session: `subagent` for parallel research, `web_search` for web queries, `bash` for local commands, and the read/write/edit/grep/glob tools for files.
- Use shared project tools from `tools/` in this repository. Prefer running commands from the repository root with paths like
`python3 tools/financial_rigor.py ...`; if the current session starts outside the repo, locate the actual checkout path first instead of assuming a fixed home-directory path.
- Before starting research, run the `date` command to confirm today's date; treat it as the baseline for "latest" data and state the data cutoff date in the report header. Never assume the current date from training data.
- Preserve the research quality rules from `AGENTS.md`: cross-check financial data, use exact arithmetic tools for valuation/math, and clearly label uncertainty and source gaps.

# 周检：重点优先的研究待办分诊

对 `$ARGUMENTS` 执行投资研究周检。

**v1 调用方式：** `/weekly-review`

本版本只支持默认周检，不支持参数模式；如果用户提供参数，简要说明本版本将忽略参数并按默认范围执行。

> 目标不是每周重做投研，而是找出本周真正需要决策、核验或深读的事项。

## 定位与边界

本 Skill 是**联网、重点优先的分诊台**：输出按优先级排序的待办清单，并仅写入周检归档。除
`reports/weekly-check/weekly-check-{YYYYMMDD}.md` 与
`reports/weekly-check/weekly-check-latest.md` 外，不修改任何看板、台账、thesis 或组合文件。

它不替代：

- `/earnings-review` 的财报深读；
- `/news-pulse` 的异动归因；
- `/thesis-tracker` 的假设、红线和估值复核；
- `/thesis-drift` 的新旧论文证据对比；
- `/portfolio-review` 的真实仓位和机会成本决策。

严禁自动给出买入、卖出、加仓、减仓或仓位结论。周检只说明“下一步该做什么、为什么现在做”。

## 第一步：确认时间与读取本地基线

1. 先运行 `date`，将结果作为本次联网数据截止日，并在输出开头写明。
2. 读取：
   - `reports/重点标的看板.md`；
   - `reports/标的跟踪表.md`；
   - `reports/weekly-check/weekly-check-latest.md` 和最近一份历史周检（若存在）；
   - `reports/**/*-thesis*.md`；
   - 入选公司目录下最新的研究、财报和新闻报告。
3. 从重点标的看板提取：公司名/代码、健康度、假设摘要、本周关注、下次动作和链接。
4. 从标的跟踪表提取：标的、代码、动作、锚定价、触发条件、复检日、状态、升级字段和来源报告。
5. 为每个入选标的确定一个用于周检就地跳转的主报告：
   - 重点标的优先链接 thesis；没有 thesis 时，链接与本次触发最相关的最新财报、新闻或研究报告；
   - 非重点台账条目链接台账中的来源报告；
   - 完整性缺口链接触发该缺口的具体报告。

如果某个链接失效、代码不唯一或公司名称无法映射到行情/披露主体，标为「待人工确认」，不要猜测替代标的。

## 第二步：确定本轮联网范围

### 重点标的：全量检查

对重点标的看板中的**每一家公司**检查自上次本地更新以来的：

1. 最新股价与估值快照；
2. 公司 IR、交易所、SEC、港交所等正式财报、业绩预告、公告和投资者活动；
3. 可能涉及管理层、监管、竞争格局或 thesis 红线的重大事件；
4. 看板的下次财报、Investor Day 或其他明确节点是否已到期或将在未来 14 天发生。

### 非重点标的：选择性检查

不要每周完整查询台账全部条目。仅纳入满足任一条件的开放条目：

1. 复检日已到，或未来 14 天到期；
2. 状态为「已触发待决策」或「已过期」；
3. 有明确数值价格区间/阈值，且当前价格已进入或接近该条件；
4. 满足既有 thesis 升级门：实际买入或准备纳入核心观察池、同一标的累计至少两条未关闭建议、或已触发待决策且准备认真决策。

若价格条件只有“便宜时”“明显回调”等不可量化措辞，只能列为待人工确认，不能宣称接近触发。

## 第三步：证据规则

1. 公司 IR、监管文件、交易所披露、年报/季报和正式业绩材料优先于媒体、博客和社交内容。
2. 对价格、估值和会影响行动优先级的关键数值，在可行时用两个独立来源交叉验证；口径不一致时说明差异，不取平均数掩盖问题。
3. 新闻是线索，不是 thesis 改变的充分证据；只有可验证的一手披露或可靠事实才能支持“假设可能变化”的待办。
4. 价格变化不能单独改变论文健康度。价格只影响价格条件是否触发以及估值复核优先级；除非同时出现可验证经营证据，不得把它表述为基本面变化。
5. 没有可靠新增事实时写「无新增事实」；来源不足、披露相互冲突或无法核验时写「待人工确认」。不要为了填表制造结论。

## 第四步：排定待办优先级

| 级别 | 触发条件 | 周检动作 |
|---|---|---|
| **P0：立即处理** | 正式披露显示潜在红线事件；新财报/年报已发布；台账已触发待决策；当前价格已进入明确买卖带 | 写明可验证证据与触发条件，指定下一项 workflow |
| **P1：本周处理** | 未来 14 天有业绩/关键事件；复检日已到；thesis 健康度 ≤6；关键假设将在近期披露中验证 | 列入本周待办，写明截止日和唯一关键问题 |
| **P2：保持观察** | 无新一手事实，或价格/事件条件仍未达到 | 简要写明等待的事件或价格条件，不展开研究 |

红线、正式财报和已触发待决策优先于普通价格波动。若同一事项满足多级条件，取最高优先级。

## 第五步：完整性检查

在输出中单列以下只读检查结果：

1. 存在 `*-thesis*.md`、却未出现在重点标的看板主表的公司；
2. 有明确买入、分批、观望或回避建议、却未被重点看板或标的跟踪表覆盖的报告；
3. thesis 缺少明确下次检查时间或关键关注项；
4. 台账复检日已过、但状态仍未关闭的条目；
5. 满足 thesis 升级门、却尚未建立 thesis 的台账条目。

只报告缺口，不自动补录、不修改状态、不创建 thesis。

## 第六步：建议分流

对每个 P0/P1 待办只推荐一个首选 workflow；确有必要时才附一个后续动作：

| 情况 | 首选下一步 |
|---|---|
| 新财报、年报、业绩预告或电话会材料 | `/earnings-review 公司名` |
| 股价异动或新闻因果不明 | `/news-pulse 公司名` |
| 核心假设、红线或估值锚点需要重新判断 | `/thesis-tracker 公司名` |
| 新旧报告的判断疑似矛盾 | `/thesis-drift 公司名 旧报告路径 新报告路径` |
| 需要决定真实仓位、换仓或组合风险 | `/portfolio-review` |

若标的没有结构化 thesis，先建议建立 thesis，不要直接声称论文已经破裂。

## 第七步：输出与归档

### 本地报告链接规则

周检中的标的名称必须写成指向主报告的 Markdown 链接，方便在 Pages 中从待办直接回源：

1. “本周待办队列”“重点标的状态”“非重点台账触发项”三个表格，以及“本周不处理项”中的每个标的名称都使用本地报告链接；不要只在文末集中列出来源。
2. 链接使用从 `reports/weekly-check/` 出发的相对路径，例如 `[腾讯（0700.HK）](../腾讯/腾讯-thesis.md)`。
3. 同一标的在同一份周检中保持主报告链接一致；外部披露或行情链接继续放在“已验证事实”等证据位置，不能替代本地报告入口。
4. 写入前验证每个本地链接目标存在。无法确定或目标不存在时，保留纯文本标的并紧随 `（报告链接待人工确认）`，不要猜测路径或生成死链。

输出并保存一份 Markdown 周检报告，固定使用以下结构：

```markdown
# 周检待办清单

**数据截止日：** YYYY-MM-DD 时区
**检查范围：** 重点标的 N 家；非重点台账入选 M 条；完整性扫描全部 thesis/台账

## 一、本周待办队列

| 优先级 | 标的（链接主报告） | 触发原因 | 已验证事实 | 建议下一步 |
|---|---|---|---|---|

## 二、重点标的状态

| 标的（链接主报告） | 状态 | 新增事实或数据缺口 | 下一个节点 |
|---|---|---|---|

## 三、非重点台账触发项

| 标的（链接主报告） | 台账状态 | 条件/复检进展 | 建议下一步 |
|---|---|---|---|

## 四、完整性检查

- 看板覆盖缺口：
- 台账覆盖缺口：
- thesis 复检缺口：
- 升级候选：

## 五、本周不处理项

仅列出 P2 标的及其等待条件，标的名称同样链接主报告。
```

每个 P0/P1 条目必须含可追溯的披露、行情或本地报告证据。P2 和“无新增事实”条目保持一行，不重复公司长逻辑。

归档规则：

1. 按数据截止日写入 `reports/weekly-check/weekly-check-{YYYYMMDD}.md`；同日重复运行更新同一份快照，不创建 `-v2`。
2. 历史日期文件只读保留，不覆盖、不删除。
3. 更新 `reports/weekly-check/weekly-check-latest.md`，链接当前快照，并以日期倒序维护历史周检列表。
4. 当前对话返回本次快照和 latest 页的可点击路径。

## 关键原则

- **先排序，再深读**：周检的价值是减少注意力分散，不是扩大阅读量。
- **事实优先于价格**：价格触发复核，不自动改变商业判断。
- **重点全查，台账筛查**：深度覆盖与广度覆盖不能用同一频率。
- **归档但不改状态**：周检只写自己的快照与 latest 索引，不替用户修改看板、台账、thesis、组合或投资动作。
