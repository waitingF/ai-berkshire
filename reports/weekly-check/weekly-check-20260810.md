# 周检待办清单

**数据截止日：** 2026-08-10 15:00 Asia/Shanghai  
**检查范围：** 重点标的 13 家；非重点台账入选 4 条；完整性扫描全部 8 份 thesis、55 条台账及 2026-07-31 后新增研究报告。  
**补检说明：** 上周漏做的周检现按默认范围补做；价格快照截至 8 月 10 日亚洲交易时段（美股为 8 月 7 日收盘），不将价格变化表述为基本面变化。

## 一、本周待办队列

| 优先级 | 标的（链接主报告） | 触发原因 | 已验证事实 | 建议下一步 |
|---|---|---|---|---|
| **P0** | [AppLovin（APP）](../AppLovin/AppLovin-checklist-20260807.md) | 新财报已发布，且价格仍在既定 $300–350 复核带。 | [2026Q2 10-Q](https://www.sec.gov/Archives/edgar/data/1751008/000175100826000059/app-20260630.htm) 于 8/5 披露；本地研究核对 Q2 收入 $1.924B、CFO $0.869B 与 Q3 指引。8/7 收盘 $346.80（Nasdaq 与腾讯美股行情同值；同一时点聚合行情，不视为独立双源）。 | `/earnings-review AppLovin`：只核 Q2 增长、现金转化、ROAS/客户留存可验证性及 Q3 指引。 |
| **P0** | [中国平安（601318.SH / 2318.HK）](../中国平安/中国平安-thesis.md) | 当前价格进入 thesis 明确的 **48–55 元**复核带。 | 8/10 A 股行情为 53.35 元（[腾讯](https://qt.gtimg.cn/q=sh601318)）及 53.32 元（[新浪](https://hq.sinajs.cn/list=sh601318)）；两源差 0.06%，位于既定带内。尚无中报新事实。 | `/thesis-tracker 中国平安`：先按利差损监测表核对净投资收益率、NBV、偿付能力和中报前风险，不推导交易动作。 |
| **P0** | [Archrock（AROC）](../Archrock/Archrock-research-20260805.md) | 新的 Q2 官方业绩已发布，而台账仍处“待触发”。 | 公司 8/4 [Q2 官方业绩公告](https://www.globenewswire.com/news-release/2026/08/04/3338849/0/en/archrock-reports-second-quarter-2026-results.html)披露收入 $371.238m、CFO $160.782m；本地报告同时指出截至 8/5 尚未见对应 10-Q。 | `/earnings-review Archrock`：补核 10-Q 的现金、净债务、CapEx、利用率与继任披露。 |
| **P1** | [腾讯（00700.HK）](../腾讯/腾讯-thesis.md) | Q2 节点在未来 2 天。 | 看板及公司 IR 资料列明 8/12 发布 Q2。8/10 行情约 HK$478.4–479.6（[腾讯](https://qt.gtimg.cn/q=hk00700) / [新浪](https://hq.sinajs.cn/list=rt_hk00700)），仍高于约 HK$400 复核线。 | `/earnings-review 腾讯`：聚焦 AI 投入回报、回购、广告/游戏和监管事项。 |
| **P1** | [拼多多（PDD）](../拼多多/拼多多-thesis.md) | 健康度仅 5/10；Q2 预计约 8/24，正好进入 14 天窗口。 | 8/7 美股收盘 $91.76（[Nasdaq](https://api.nasdaq.com/api/quote/PDD/info?assetclass=stocks)）；距 <$75 价格复核线约 18.27%，未触发。关键仍是 Q2 Non-GAAP 净利率是否连续低于 15%。 | `/thesis-tracker 拼多多`：为 Q2 预设利润率、主站增速、资本回报三项判据。 |
| **P1** | [美团（3690.HK）](../美团/美团-thesis.md) | 健康度 6/10，全年利润恢复假设已受损。 | 8/10 行情 HK$93.35（[腾讯](https://qt.gtimg.cn/q=hk03690) / [新浪](https://hq.sinajs.cn/list=rt_hk03690)）; 距 <HK$70 复核线约 25.01%，无价格触发。中报前暂无新的经营一手事实。 | `/thesis-tracker 美团`：明确中报对补贴、UE、份额与销售费用率的判据。 |
| **P1** | [泡泡玛特（9992.HK）](../泡泡玛特/泡泡玛特-thesis.md) | 健康度 6/10；中报预计 8/19，进入 14 天窗口。 | 8/10 行情 HK$154.10–154.20（[腾讯](https://qt.gtimg.cn/q=hk09992) / [新浪](https://hq.sinajs.cn/list=rt_hk09992)），较 HK$140 上沿高约 9.18%，未触发价格带。 | `/earnings-review 泡泡玛特`：分 IP/地区、库存周转与海外增速是唯一核心问题。 |
| **P1** | [Accenture（ACN）](../Accenture/Accenture-thesis.md) | 健康度 6/10，且价格数据存在需先排除的口径冲突。 | 看板 8/9 写约 $145；8/7 [Nasdaq](https://api.nasdaq.com/api/quote/ACN/info?assetclass=stocks) 为 $175.72。后者已高于 thesis 的 $145–165 决策带，不能取平均数或据旧价宣称触发。 | `/thesis-tracker Accenture`：先人工确认复权、时点及代码口径，再检查 FY26 全年增长/利润率证据。 |
| **P1** | [中芯国际（688981.SH / 00981.HK）](../中芯国际/中芯国际-research-20260731.md) | 2026Q2 业绩会计划 8/14，进入未来 14 天。 | 本地研究所引公司 Q1 材料给出 Q2 收入环比 +14%–16%、毛利率 20%–22%指引，均非已实现结果。8/10 A/H 行情分别约 126.25 元 / 66.05 港元（[腾讯](https://qt.gtimg.cn/q=sh688981,hk00981) / [新浪](https://hq.sinajs.cn/list=sh688981,rt_hk00981)）。 | `/earnings-review 中芯国际`：核验利用率、毛利率、CapEx/FCF 与 A/H 估值差。 |
| **P1** | [Progressive（PGR）](../Progressive/Progressive-earnings-2026Q2.md) | 台账的 8/3 10-Q、8/4 电话会复检窗口已到，但状态仍为“待触发”。 | 本地 Q2 精读仅覆盖 7/15 月度/季度运营快报，并明确要求补 10-Q 与电话会；当前没有将后续材料错误当成已核验事实。 | `/earnings-review Progressive`：补读 10-Q/电话会，重点为 Property 一次性因素、费率竞争、现金流和交班。 |
| **P1** | [Palantir（PLTR）](../Palantir/Palantir-research-20260801.md) | 台账明确的 8/3 Q2 复检日已过。 | 本地报告截止 8/1，写明当时最新仅为 Q1、Q2 定于 8/3 盘后；8/7 收盘 $172.01（[Nasdaq](https://api.nasdaq.com/api/quote/PLTR/info?assetclass=stocks)），远高于 $70–85 复核带。尚未抓取到可归档的 Q2 一手材料，标待人工确认。 | `/earnings-review Palantir`：先取得正式 Q2 业绩，再核 US 商业 TCV/客户、SBC 和指引。 |
| **P1** | [AMD（AMD）](../AMD/AMD-research-20260804.md) | 台账要求在 Q2 业绩与 10-Q 后复检。 | 8/7 收盘 $483.36（[Nasdaq](https://api.nasdaq.com/api/quote/AMD/info?assetclass=stocks)），未进入 $220–300 带；本轮未能取得可归档的 Q2 一手文件，不能把市场行情当作业绩已核验。 | `/earnings-review AMD`：核对 AI GPU 增长、毛利、FCF、稀释后 EPS 与权证稀释。 |
| **P1** | [小米（1810.HK）](../小米/小米-news-20260729.md) | 台账复检日为 8/18 中期业绩后，进入未来 14 天。 | 8/10 行情约 HK$27.50–27.52（[腾讯](https://qt.gtimg.cn/q=hk01810) / [新浪](https://hq.sinajs.cn/list=rt_hk01810)）；公司先前公告的中期业绩节点为 8/18。 | `/earnings-review 小米`：只核手机/IoT、汽车亏损与现金流兑现。 |
| **P1** | [蓝思科技（300433.SZ / 6613.HK）](../蓝思科技/蓝思科技-research-20260803.md) | 台账复检日为 8/22 半年报后，进入未来 14 天。 | 本地研究记录预约披露日 8/22；8/10 A 股 34.90 元（[腾讯](https://qt.gtimg.cn/q=sz300433) / [新浪](https://hq.sinajs.cn/list=sz300433)），未进入 18–24 元带。 | `/earnings-review 蓝思科技`：核主业恢复、FCF、客户集中度及新业务利润披露。 |

## 二、重点标的状态

| 标的（链接主报告） | 状态 | 新增事实或数据缺口 | 下一个节点 |
|---|---|---|---|
| [腾讯（00700.HK）](../腾讯/腾讯-thesis.md) | P1 | 价格双源一致；未见 Q2 前足以改变 thesis 的新一手经营事实。 | 8/12 Q2 |
| [拼多多（PDD）](../拼多多/拼多多-thesis.md) | P1 | 健康度 5/10；美股价格仅获得单一可用聚合快照，Q2 日期仍为预期值。 | 约 8/24 Q2 |
| [美团（3690.HK）](../美团/美团-thesis.md) | P1 | 健康度 6/10；价格未触发，等待中报验证利润恢复路径。 | 约 8/27 中报 |
| [泡泡玛特（9992.HK）](../泡泡玛特/泡泡玛特-thesis.md) | P1 | 健康度 6/10；价格未触发，分 IP/地区和库存数据待中报。 | 约 8/19 中报 |
| [微软（MSFT）](../微软/微软-thesis.md) | P2 | 8/7 收盘 $499.99（[Nasdaq](https://api.nasdaq.com/api/quote/MSFT/info?assetclass=stocks)）；本轮无新增一手经营事实，价格本身不改变健康度。 | FY2027 Q1 |
| [SK 海力士（000660.KS）](../SK海力士/SK海力士-thesis-20260713.md) | P2 | Naver 8/10 收盘约 ₩1,420,000（[行情](https://fchart.stock.naver.com/sise.nhn?symbol=000660&timeframe=day&count=3&requestType=0)），单源，待人工复核；没有新的正式经营披露。 | 2026Q3 |
| [Accenture（ACN）](../Accenture/Accenture-thesis.md) | P1 | 健康度 6/10；看板与外部价格快照冲突，必须先校正数据口径。 | FY2026 Q4/全年，约 9 月 |
| [中国平安（601318.SH / 2318.HK）](../中国平安/中国平安-thesis.md) | P0 | A 股落入 48–55 元复核带；无中报新事实。 | 约 8/21 中报 |
| [上海复旦（688385.SH / 01385.HK）](../上海复旦/上海复旦-research-20260802.md) | P2 | 无结构化 thesis；8/10 A/H 行情约 55.17 元 / 27.16 港元（单一行情源），未取得正式 H1 时间表。 | 待正式 H1 披露/建立 thesis |
| [中芯国际（688981.SH / 00981.HK）](../中芯国际/中芯国际-research-20260731.md) | P1 | Q2 指引尚待兑现；A/H 价格已更新，但不能替代业绩验证。 | 8/14 Q2 业绩会 |
| [AppLovin（APP）](../AppLovin/AppLovin-checklist-20260807.md) | P0 | Q2 10-Q 已披露；价格处既定复核带，Q3 指引需要逐项审读。 | Q3 业绩/独立 ROAS 证据 |
| [标普 500 指数（S&P 500）](../标普纳指定投-checklist-20260809.md) | P2 | 8/7 SPY $773.26 为单一行情快照；本轮无新的结构性事实。 | 半年比例检查、年度再平衡 |
| [纳斯达克 100 指数（NASDAQ-100）](../标普纳指定投-checklist-20260809.md) | P2 | 8/7 QQQ $723.03 为单一行情快照；等待持仓比例与风险承受度复核。 | 半年比例检查、年度再平衡 |

## 三、非重点台账触发项

| 标的（链接主报告） | 台账状态 | 条件/复检进展 | 建议下一步 |
|---|---|---|---|
| [Archrock（AROC）](../Archrock/Archrock-research-20260805.md) | 待触发；P0 | Q2 官方业绩已出；10-Q 在本地报告截止时仍未取得，价格也未进入 $22.20–25.90 带。 | `/earnings-review Archrock` |
| [Progressive（PGR）](../Progressive/Progressive-earnings-2026Q2.md) | 待触发；P1 | 8/3–8/4 的明确复检窗口已过；未更新状态，后续一手材料待核。 | `/earnings-review Progressive` |
| [Palantir（PLTR）](../Palantir/Palantir-research-20260801.md) | 待触发；P1 | 8/3 Q2 复检日已过；当前价远未触及量化价格带；正式 Q2 文件待人工确认。 | `/earnings-review Palantir` |
| [AMD（AMD）](../AMD/AMD-research-20260804.md) | 待触发；P1 | 台账约定的 Q2/10-Q 后复检尚未在本地闭环；当前价远未触及 $220–300 带。 | `/earnings-review AMD` |

## 四、完整性检查

- **看板覆盖缺口：** 无。全部 8 份 `*-thesis*.md` 已纳入重点标的主表。
- **台账覆盖缺口：** 仍有含明确观察/回避或价格条件、但未被重点看板或台账覆盖的报告，包括 [Reddit](../Reddit/Reddit-research-20260731.md)、[IBKR](../IBKR/IBKR-research-20260729.md)、[ServiceNow](../ServiceNow/ServiceNow-research-20260729.md)、[Tesla Q2](../Tesla/Tesla-earnings-2026Q2.md)，以及存储专题中的 [美光](../存储/美光科技-投资研究报告-20260730.md)、[三星电子](../存储/三星电子-投资研究报告-20260730.md)、[兆易创新](../存储/兆易创新-投资研究报告-20260730.md)。仅报告缺口，不判断其建议仍有效。
- **thesis 复检缺口：** 现有 8 份 thesis 均有下次检查时间或关键关注项；没有“缺少检查项”的 thesis。台账中 [Progressive](../Progressive/Progressive-earnings-2026Q2.md)、[Palantir](../Palantir/Palantir-research-20260801.md) 的明确复检日已过但状态未关闭，已列入 P1。
- **升级候选：** [蚂蚁数科](../蚂蚁数科/蚂蚁数科-team-20260508/最终报告.md)仍有 3 条未关闭建议而无结构化 thesis；[AppLovin](../AppLovin/AppLovin-checklist-20260807.md)已进入重点看板且有部分仓位背景但无 thesis，应在 P0 财报核验后再决定是否建立。

## 五、本周不处理项

- [微软（MSFT）](../微软/微软-thesis.md)：等待 FY2027 Q1 对 Azure、云毛利、CapEx 与 FCF 的联合验证。
- [SK 海力士（000660.KS）](../SK海力士/SK海力士-thesis-20260713.md)：等待 3Q 对 HBM4/HBM4E 认证、DRAM/NAND 价格、bit 出货和扩产现金回报的验证。
- [上海复旦（688385.SH / 01385.HK）](../上海复旦/上海复旦-research-20260802.md)：等待正式 H1 披露；没有 thesis 前不把行情波动升级为论文结论。
- [标普 500 指数（S&P 500）](../标普纳指定投-checklist-20260809.md)：等待半年比例检查及账户/税务结构核验。
- [纳斯达克 100 指数（NASDAQ-100）](../标普纳指定投-checklist-20260809.md)：等待半年比例检查，关注与标普的重叠和集中度。

## 主要证据与限制

- [重点标的看板](../重点标的看板.md)、[标的跟踪表](../标的跟踪表.md)、上次 [2026-07-31 周检](weekly-check-20260731.md)。
- 正式披露优先：AppLovin 10-Q、Archrock 官方业绩、各本地报告中已链接的公司 IR/交易所/SEC 材料。
- 港/A 股报价使用腾讯与新浪交叉；美国报价的可用来源在本次会话中仅能稳定取得 Nasdaq 快照，腾讯美股接口与其同时间同值，不能冒充独立双源。Yahoo Finance 图表接口受限流，SEC/IR 个别页面受反爬限制；这些项目均标为“待人工确认”，不以单源价格或新闻改变 thesis。

*本报告用于学习和研究分诊，不构成投资建议；未提出买入、卖出、加仓、减仓或仓位结论。*
