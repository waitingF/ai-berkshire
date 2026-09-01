# 每日监控

**数据截止日**：2026-09-01（Asia/Shanghai）
**运行状态**：DEGRADED
**摘要**：P0 0 · P1 6 · 新增价格 1 · 新增披露 5 · 异常 0
**数据源状态**：quotes=OK、cninfo=OK、hkex=OK、sec=OK

> 价格条件、正式披露与其他研究缺口在同一份报告中展示；优先级表示研究处理顺序，不代表交易信号。

## 一、价格监控

> 价格优先级：P0=到达建仓或研究复核条件；P1=距对应边界≤5%；P2 与已越警戒线事项不展示。优先级只表示复核紧迫度，不代表交易信号。

| 优先级 | 标的 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |
|---|---|---|---|---:|---:|---:|---|
| P0 | [AppLovin](../AppLovin/AppLovin-earnings-2026Q2.md) | US | 分批复核带 | [300.00, 330.00] | 311.54 | 区间内 | TRIGGERED |
| P0 | [Novo Nordisk](../Novo%20Nordisk/Novo%20Nordisk-earnings-2026Q2.md) | US | 观察仓带 | [44.00, 46.00] | 45.75 | 区间内 | TRIGGERED |
| P0 | [Reddit](../Reddit/Reddit-earnings-2026Q2.md) | US | 小仓跟踪带 | [145.00, 165.00] | 146.22 | 区间内 | TRIGGERED |
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | H | H股原分批研究带（暂停执行） | [20.00, 28.00] | 27.04 | 区间内 | TRIGGERED |
| P0 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | H | 评估带 | [35.00, 40.00] | 34.64 | 低于下界 1.0% | TRIGGERED |
| P0 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | US | 分批评估区 | [6.00, 8.50] | 8.23 | 区间内 | TRIGGERED |
| P0 | [赣锋锂业](../%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A/%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A-earnings-2026H1.md) | H | H股小仓带 | [34.60, 43.80] | 40.48 | 区间内 | TRIGGERED |
| P1 | [lululemon](../lululemon/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | US | 观察仓带 | ≤ 119.00 | 120.82 | 1.5% | NEAR |
| P1 | [Qualcomm](../Qualcomm/Qualcomm-earnings-FY2026Q3.md) | US | 理想买入带 | ≤ 160.00 | 162.48 | 1.5% | NEAR |
| P1 | [中国平安](../%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89/%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89-thesis.md) | A | A股持有/分批复核带 | [48.00, 55.00] | 57.23 | 4.1% | NEAR |
| P1 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-research-20260803.md) | US | 研究性分批带 | [12.00, 16.00] | 16.08 | 0.5% | NEAR |
| P1 | [腾讯控股](../%E8%85%BE%E8%AE%AF/%E8%85%BE%E8%AE%AF-thesis.md) | H | 加仓带 | [400.00, 430.00] | 441.40 | 2.7% | NEAR |
| P1 | [贵州茅台](../%E8%8C%85%E5%8F%B0/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | 建仓参考带 | [1100.00, 1250.00] | 1299.56 | 4.0% | NEAR |

## 二、财报与正式披露监控

| 优先级 | 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |
|---|---|---|---|---:|---|---|
| P1 | [三环集团](../%E4%B8%89%E7%8E%AF%E9%9B%86%E5%9B%A2/%E4%B8%89%E7%8E%AF%E9%9B%86%E5%9B%A2-research-20260803.md) | H | [新增公告，内容待确认](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103364.htm) | 1 | 19:30 | REVIEW |
| P1 | [云迹科技](../%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80/%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80-earnings-2026H1.md) | H | [ANNOUNCEMENT UPDATE ON THE EXPECTED TIMETABLE REGARDING THE …](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103473.pdf) | 1 | 20:07 | REVIEW |
| P1 | [北京君正](../%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3/%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3-research-20260817.md) | H | [Letter and Reply Form to Registered Shareholders - Arrangeme…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103605.pdf)<br>[Letter and Reply Form to Non-registered Shareholders - Arran…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103607.pdf)<br>[(1) COMPLETION OF CERTAIN INVESTMENT PROJECT FUNDED BY PROCE…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103611.pdf)<br>[FORM OF PROXY FOR THE FIRST EXTRAORDINARY GENERAL MEETING OF…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103619.pdf)<br>[NOTICE OF THE FIRST EXTRAORDINARY GENERAL MEETING OF 2026](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103615.pdf) | 5 | 21:14 | REVIEW |
| P1 | [华虹宏力](../%E5%8D%8E%E8%99%B9%E5%AE%8F%E5%8A%9B/%E5%8D%8E%E8%99%B9%E5%8D%8A%E5%AF%BC%E4%BD%93-earnings-2026H1.md) | H | [DISCLOSEABLE TRANSACTION IN RELATION TO THE JV INVESTMENT AG…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103625.pdf) | 1 | 21:15 | REVIEW |
| P1 | [立讯精密](../%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86/%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86-research-20260803.md) | H | [新增公告，内容待确认](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0901/2026090103600.htm) | 1 | 21:03 | REVIEW |

| 优先级 | 标的 | 披露/事项 | 日期 | 状态 | 为什么现在 | 核验事实/正式来源 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|---|
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | 2026H1业绩：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报；事件保持开放。披露后核扣除约4.7亿公允价值收益后的经营利润、库存减值、管理层资本配置；当前暂停新建仓。 |
| P0 | [兆易创新](../%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0/%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0-earnings-2026H1.md) | 2026H1正式中报：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报，事件保持开放；披露后核扣非、经营现金流、库存、关联交易。 |
| P0 | [多氟多](../%E5%A4%9A%E6%B0%9F%E5%A4%9A/%E5%A4%9A%E6%B0%9F%E5%A4%9A-earnings-2026H1.md) | 2026H1正式报告：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报，事件保持开放；披露后核锂盐毛利、OCF、净债务。 |
| P2 | [Adobe](../Adobe/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | FY2026Q3财报（公司IR已确认）：9 天后到期 | 2026-09-10 | UPCOMING_14D | 登记事件状态为9 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | Adobe IR 列示 2026-09-10 14:00 PT Q3 FY2026 earnings call；核FY2026 Q3业绩、CEO交接与AI产品商业化；SEC正式披露将由每日扫描捕获 |
| P2 | [lululemon](../lululemon/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | 下季报后复检：9 天后到期 | 2026-09-10 | UPCOMING_14D | 登记事件状态为9 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 核北美同店与库存 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入250-265m指引、GAAP毛利率29%-31%、Adjusted EBITDA亏损、backlog转化、现金消耗及稀释股数<br>待人工确认 |
| P2 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核广告/电商是否重回双位数、毛利率能否恢复至至少53%、自由现金流、可灵收入/亏损与增资交割。<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核剔除喜马拉雅后的原有业务增长、会员收入、毛利率、广告承压和Non-IFRS利润<br>待人工确认 |

## 三、其他监控

| 优先级 | 标的/数据源 | 事项 | 日期 | 状态 | 为什么现在 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|
| P2 | [Progressive](../Progressive/Progressive-earnings-2026Q2.md) | 2026年8月月度结果复核窗口：14 天后到期 | 2026-09-15 | UPCOMING_14D | 登记事件状态为14 天后到期，需按备注核验；监控本身不作投资决定。 | - | 日期为研究复核窗口，待公司IR确认具体发布时间；核NPW、CR、广告费用与事故年损失率。 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | Iridium交易审批与融资条款：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 跟踪Iridium股东和监管审批、3.6bn美元桥贷置换成本、最终交换比例与并表时间<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 喜马拉雅整合与商誉复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 核独立收入、盈利/FCF、后台整合成本、无形资产摊销及92.36亿元新增商誉<br>待人工确认 |

---

价格达到条件只触发研究复核；正式披露的模型判断也只用于研究分流。
本报告用于学习和研究，不构成投资建议，也不会自动作出买卖或仓位结论。
