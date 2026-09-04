# 每日监控

**数据截止日**：2026-09-04（Asia/Shanghai）
**运行状态**：DEGRADED
**摘要**：P0 2 · P1 16 · 新增价格 1 · 新增披露 17 · 异常 1
**数据源状态**：quotes=OK、cninfo=OK、hkex=OK、sec=FAILED（SEC ticker 未映射到 CIK: SE）

> 价格条件、正式披露与其他研究缺口在同一份报告中展示；优先级表示研究处理顺序，不代表交易信号。

## 一、价格监控

> 价格优先级：P0=到达建仓或研究复核条件；P1=距对应边界≤5%；P2 与已越警戒线事项不展示。优先级只表示复核紧迫度，不代表交易信号。

| 优先级 | 标的 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |
|---|---|---|---|---:|---:|---:|---|
| P0 | [AppLovin](../AppLovin/AppLovin-earnings-2026Q2.md) | US | 分批复核带 | [300.00, 330.00] | 313.58 | 区间内 | TRIGGERED |
| P0 | [Reddit](../Reddit/Reddit-earnings-2026Q2.md) | US | 小仓跟踪带 | [145.00, 165.00] | 155.99 | 区间内 | TRIGGERED |
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | H | H股原分批研究带（暂停执行） | [20.00, 28.00] | 25.72 | 区间内 | TRIGGERED |
| P0 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-research-20260803.md) | US | 研究性分批带 | [12.00, 16.00] | 15.50 | 区间内 | TRIGGERED |
| P0 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | H | 评估带 | [35.00, 40.00] | 33.66 | 低于下界 3.8% | TRIGGERED |
| P0 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | US | 分批评估区 | [6.00, 8.50] | 8.20 | 区间内 | TRIGGERED |
| P0 | [赣锋锂业](../%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A/%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A-earnings-2026H1.md) | H | H股小仓带 | [34.60, 43.80] | 36.62 | 区间内 | TRIGGERED |
| P1 | [Novo Nordisk](../Novo%20Nordisk/Novo%20Nordisk-earnings-2026Q2.md) | US | 观察仓带 | [44.00, 46.00] | 47.51 | 3.3% | NEAR |
| P1 | [华虹半导体](../%E5%8D%8E%E8%99%B9%E5%AE%8F%E5%8A%9B/%E5%8D%8E%E8%99%B9%E5%8D%8A%E5%AF%BC%E4%BD%93-earnings-2026H1.md) | H | H股小仓复核带 | [80.00, 105.00] | 109.70 | 4.5% | NEAR |
| P1 | [腾讯控股](../%E8%85%BE%E8%AE%AF/%E8%85%BE%E8%AE%AF-thesis.md) | H | 加仓带 | [400.00, 430.00] | 442.80 | 3.0% | NEAR |

## 二、财报与正式披露监控

| 优先级 | 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |
|---|---|---|---|---:|---|---|
| P0 | [lululemon](../lululemon/lululemon-research-20260904.md) | US | [8-K](https://www.sec.gov/Archives/edgar/data/1397187/000139718726000126/lulu-20260903.htm)<br>[10-Q](https://www.sec.gov/Archives/edgar/data/1397187/000139718726000127/lulu-20260802.htm) | 2 | 04:10 | REVIEW |
| P0 | [圣邦股份](../%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD/%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD-research-20260803.md) | H | [Letter to Registered Shareholders - Arrangements on Dissemin…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401362.pdf)<br>[Letter to Non-Registered Shareholders - Arrangement on Disse…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401415.pdf)<br>[2026 Interim Report](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401485.pdf)<br>[Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401543.pdf) | 4 | 18:00 | REVIEW |
| P1 | [ALB](../Albemarle/Albemarle-research-20260901.md) | US | [8-K](https://www.sec.gov/Archives/edgar/data/915913/000114036126035623/ef20081522_8k.htm) | 1 | 05:00 | REVIEW |
| P1 | [中国广核](../%E4%B8%AD%E5%9B%BD%E5%B9%BF%E6%A0%B8/%E4%B8%AD%E5%9B%BD%E5%B9%BF%E6%A0%B8-earnings-2026H1.md) | H | [IMMEDIATE COMMENCEMENT OF FULL CONSTRUCTION OF ZHAOYUAN UNIT…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401404.pdf) | 1 | 17:45 | REVIEW |
| P1 | [中芯国际](../%E4%B8%AD%E8%8A%AF%E5%9B%BD%E9%99%85/%E4%B8%AD%E8%8A%AF%E5%9B%BD%E9%99%85-earnings-2026Q2.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401087.pdf) | 1 | 17:03 | REVIEW |
| P1 | [云迹科技](../%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80/%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80-earnings-2026H1.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090400880.pdf) | 1 | 16:45 | DONE |
| P1 | [兆易创新](../%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0/%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0-earnings-2026H1.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090400564.pdf)<br>[翌日披露报表](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401455.pdf) | 2 | 17:49 | REVIEW |
| P1 | [华虹宏力](../%E5%8D%8E%E8%99%B9%E5%AE%8F%E5%8A%9B/%E5%8D%8E%E8%99%B9%E5%8D%8A%E5%AF%BC%E4%BD%93-earnings-2026H1.md) | H | [MONTHLY RETURN OF EQUITY ISSUER ON MOVEMENTS IN SECURITIES F…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090400313.pdf)<br>[(1) PROPOSED CHANGE IN USE OF PROCEEDS FROM THE RMB SHARE IS…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401194.pdf)<br>[NOTICE OF EXTRAORDINARY GENERAL MEETING](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401243.pdf)<br>[PROXY FORM Extraordinary General Meeting to be held on 23 Se…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401298.pdf) | 4 | 17:31 | REVIEW |
| P1 | [圣邦股份](../%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD/%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD-research-20260803.md) | A | [关于部分股票期权注销完成的公告](https://static.cninfo.com.cn/finalpage/2026-09-04/1225548318.PDF)<br>[H股公告-致非登记股东之函件-以电子方式发布公司通讯之安排](https://static.cninfo.com.cn/finalpage/2026-09-04/1225549657.PDF)<br>[H股公告-致登记股东之函件-发布公司通讯之安排](https://static.cninfo.com.cn/finalpage/2026-09-04/1225549658.PDF)<br>[H股公告-截至2026年8月31日止股份发行人的证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-09-04/1225549656.PDF)<br>[H股公告-2026年中期报告](https://static.cninfo.com.cn/finalpage/2026-09-04/1225549655.PDF) | 5 | 19:08 | REVIEW |
| P1 | [安克创新](../%E5%AE%89%E5%85%8B%E5%88%9B%E6%96%B0/%E5%AE%89%E5%85%8B%E5%88%9B%E6%96%B0-earnings-2026H1.md) | A | [中国国际金融股份有限公司关于安克创新科技股份有限公司2026年半年度跟踪报告](https://static.cninfo.com.cn/finalpage/2026-09-04/1225548906.PDF)<br>[H股公告-截至2026年8月31日止之股份发行人的证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-09-04/1225548905.PDF) | 2 | 19:00 | REVIEW |
| P1 | [晶合集成](../%E6%99%B6%E5%90%88%E9%9B%86%E6%88%90/%E6%99%B6%E5%90%88%E9%9B%86%E6%88%90-research-20260821.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090400970.pdf) | 1 | 16:52 | DONE |
| P1 | [极视角](../%E6%9E%81%E8%A7%86%E8%A7%92/%E6%9E%81%E8%A7%86%E8%A7%92-earnings-2026H1.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090402007.pdf)<br>[VOLUNTARY ANNOUNCEMENT STRATEGIC COOPERATION AGREEMENTS](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090402131.pdf) | 2 | 19:56 | REVIEW |
| P1 | [海尔智家](../%E6%B5%B7%E5%B0%94%E6%99%BA%E5%AE%B6-deepseek%E5%88%86%E6%9E%90/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | H | [翌日披露报表](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090400996.pdf) | 1 | 16:54 | DONE |
| P1 | [深演智能](../%E6%B7%B1%E6%BC%94%E6%99%BA%E8%83%BD/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401296.pdf) | 1 | 17:30 | DONE |
| P1 | [澜起科技](../%E6%BE%9C%E8%B5%B7%E7%A7%91%E6%8A%80/%E6%BE%9C%E8%B5%B7%E7%A7%91%E6%8A%80-earnings-2026H1.md) | H | [翌日披露报表](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090401727.pdf) | 1 | 18:28 | DONE |
| P1 | [立讯精密](../%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86/%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86-research-20260803.md) | H | [(Revised) Monthly Return of Equity Issuers on Movements in S…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090400532.pdf)<br>[Monthly Return of Equity Issuers on Movements in Securities …](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0904/2026090400632.pdf) | 2 | 16:33 | REVIEW |
| P1 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | US | [FORM 6-K](https://www.sec.gov/Archives/edgar/data/1744676/000119312526381951/d124958d6k.htm)<br>[FORM 6-K](https://www.sec.gov/Archives/edgar/data/1744676/000119312526382837/d103245d6k.htm) | 2 | 16:29 | REVIEW |

| 优先级 | 标的 | 披露/事项 | 日期 | 状态 | 为什么现在 | 核验事实/正式来源 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|---|
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | 2026H1业绩：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报；事件保持开放。披露后核扣除约4.7亿公允价值收益后的经营利润、库存减值、管理层资本配置；当前暂停新建仓。 |
| P0 | [兆易创新](../%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0/%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0-earnings-2026H1.md) | 2026H1正式中报：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报，事件保持开放；披露后核扣非、经营现金流、库存、关联交易。 |
| P0 | [多氟多](../%E5%A4%9A%E6%B0%9F%E5%A4%9A/%E5%A4%9A%E6%B0%9F%E5%A4%9A-earnings-2026H1.md) | 2026H1正式报告：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报，事件保持开放；披露后核锂盐毛利、OCF、净债务。 |
| P2 | [Adobe](../Adobe/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | FY2026Q3财报（公司IR已确认）：6 天后到期 | 2026-09-10 | UPCOMING_7D | 登记事件状态为6 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | Adobe IR 列示 2026-09-10 14:00 PT Q3 FY2026 earnings call；核FY2026 Q3业绩、CEO交接与AI产品商业化；SEC正式披露将由每日扫描捕获 |
| P2 | [Albemarle](../Albemarle/Albemarle-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Energy Storage实现价与销量、Specialties利润、TTM FCF、资本开支、净债务、CGP3恢复及CEO继任<br>待人工确认 |
| P2 | [AZZ Inc.](../AZZ/AZZ-research-20260901.md) | FY2027 Q2财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Metal/Precoat量价与EBITDA率、Washington新线、Seattle整合、债务削减及FY2027指引<br>待人工确认 |
| P2 | [Credo Technology](../Credo/Credo-research-20260903.md) | FY2027 Q2财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入US$525–535m指引兑现、GAAP毛利率62.9%–64.9%、AEC驱动是否分散、库存/应收/经营现金流、SBC与DustPhotonics光学协同<br>待人工确认 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入250-265m指引、GAAP毛利率29%-31%、Adjusted EBITDA亏损、backlog转化、现金消耗及稀释股数<br>待人工确认 |
| P2 | [Sea Limited](../SE/SE-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Shopee EBITDA/GMV、GMV增速、物流成本、Monee拨备/贷款、90+ NPL、Garena bookings及Q3调整后EBITDA新口径<br>待人工确认 |
| P2 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核广告/电商是否重回双位数、毛利率能否恢复至至少53%、自由现金流、可灵收入/亏损与增资交割。<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核剔除喜马拉雅后的原有业务增长、会员收入、毛利率、广告承压和Non-IFRS利润<br>待人工确认 |

## 三、其他监控

| 优先级 | 标的/数据源 | 事项 | 日期 | 状态 | 为什么现在 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|
| P1 | SEC | 数据源异常 | - | FAILED | SEC ticker 未映射到 CIK: SE | - | 待人工确认 |
| P2 | [Credo Technology](../Credo/Credo-research-20260903.md) | FY2027 Q2财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 复核客户集中度、AEC与光学产品发展、毛利率、FCF转化、收购整合与稀释是否改变US$120–140研究带<br>待人工确认 |
| P2 | [Progressive](../Progressive/Progressive-earnings-2026Q2.md) | 2026年8月月度结果复核窗口：11 天后到期 | 2026-09-15 | UPCOMING_14D | 登记事件状态为11 天后到期，需按备注核验；监控本身不作投资决定。 | - | 日期为研究复核窗口，待公司IR确认具体发布时间；核NPW、CR、广告费用与事故年损失率。 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | Iridium交易审批与融资条款：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 跟踪Iridium股东和监管审批、3.6bn美元桥贷置换成本、最终交换比例与并表时间<br>待人工确认 |
| P2 | [Sea Limited](../SE/SE-research-20260901.md) | Sea 2026Q3财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 复核竞争税、Shopee盈利质量、Monee信用周期、Garena现金流及当前估值是否提供安全边际<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 喜马拉雅整合与商誉复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 核独立收入、盈利/FCF、后台整合成本、无形资产摊销及92.36亿元新增商誉<br>待人工确认 |

---

价格达到条件只触发研究复核；正式披露的模型判断也只用于研究分流。
本报告用于学习和研究，不构成投资建议，也不会自动作出买卖或仓位结论。
