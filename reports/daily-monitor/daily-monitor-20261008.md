# 每日监控

**数据截止日**：2026-10-08（Asia/Shanghai）
**运行状态**：DEGRADED
**摘要**：P0 7 · P1 30 · 新增价格 11 · 新增披露 22 · 异常 0
**数据源状态**：quotes=OK、cninfo=OK、hkex=OK、sec=OK

> 价格条件、正式披露与其他研究缺口在同一份报告中展示；优先级表示研究处理顺序，不代表交易信号。

## 一、价格监控

> 价格优先级：P0=到达建仓或研究复核条件；P1=距对应边界≤5%；P2 与上涨警戒线事项不展示。优先级只表示复核紧迫度，不代表交易信号。
> 最新研究报告日期仅比较标的已登记的本地报告；优先取报告中的日期标注，其次取文件名，无法判定显示 -。

| 优先级 | 标的 | 最新研究报告日期 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |
|---|---|---|---|---|---:|---:|---:|---|
| P0 | [Adobe](../Adobe/Adobe-earnings-2026Q3.md) | 2026-09-12 | US | Q3后研究性分批上限 | ≤ 247.00 | 232.77 | 区间内 | TRIGGERED |
| P0 | [Albemarle](../Albemarle/Albemarle-research-20260901.md) | 2026-09-01 | US | 研究性分批评估带 | [90.00, 110.00] | 102.75 | 区间内 | TRIGGERED |
| P0 | [AppLovin](../AppLovin/AppLovin-news-20261007.md) | 2026-10-07 | US | 分批复核带 | [300.00, 330.00] | 281.29 | 低于下界 6.2% | TRIGGERED |
| P0 | [Reddit](../Reddit/Reddit-earnings-2026Q2.md) | 2026-08-31 | US | 小仓跟踪带 | [145.00, 165.00] | 152.71 | 区间内 | TRIGGERED |
| P0 | [Sea Limited](../SE/SE-research-20260901.md) | 2026-09-01 | US | 分层研究性评估区间 | [75.00, 105.00] | 94.66 | 区间内 | TRIGGERED |
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | 2026-09-12 | H | H股原分批研究带（暂停执行） | [20.00, 28.00] | 24.22 | 区间内 | TRIGGERED |
| P0 | [中国平安](../%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89/%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89-earnings-2026H1.md) | 2026-09-12 | A | A股持有/分批复核带 | [48.00, 55.00] | 52.67 | 区间内 | TRIGGERED |
| P0 | [中芯国际](../%E4%B8%AD%E8%8A%AF%E5%9B%BD%E9%99%85/%E4%B8%AD%E8%8A%AF%E5%9B%BD%E9%99%85-earnings-2026Q2.md) | 2026-08-23 | H | H股研究建仓带 | ≤ 58.00 | 56.95 | 区间内 | TRIGGERED |
| P0 | [云迹科技](../%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80/%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80-earnings-2026H1.md) | 2026-08-31 | H | 研究性小仓评估带 | [20.00, 35.00] | 5.82 | 低于下界 70.9% | TRIGGERED |
| P0 | [亨通光电](../%E4%BA%A8%E9%80%9A%E5%85%89%E7%94%B5/%E4%BA%A8%E9%80%9A%E5%85%89%E7%94%B5-research-20260826.md) | 2026-08-26 | A | 研究性分批评估带 | [45.00, 55.00] | 52.70 | 区间内 | TRIGGERED |
| P0 | [华虹半导体](../%E5%8D%8E%E8%99%B9%E5%AE%8F%E5%8A%9B/%E5%8D%8E%E8%99%B9%E5%8D%8A%E5%AF%BC%E4%BD%93-earnings-2026H1.md) | 2026-08-31 | H | H股小仓复核带 | [80.00, 105.00] | 95.25 | 区间内 | TRIGGERED |
| P0 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-earnings-2026Q2.md) | 2026-09-12 | US | Q2后研究性分批带 | [12.00, 16.00] | 14.92 | 区间内 | TRIGGERED |
| P0 | [思格新能](../%E6%80%9D%E6%A0%BC%E6%96%B0%E8%83%BD/%E6%80%9D%E6%A0%BC%E6%96%B0%E8%83%BD-earnings-2026H1.md) | 2026-08-31 | H | 稳健型研究性评估带 | [250.00, 280.00] | 226.60 | 低于下界 9.4% | TRIGGERED |
| P0 | [晶合集成](../%E6%99%B6%E5%90%88%E9%9B%86%E6%88%90/%E6%99%B6%E5%90%88%E9%9B%86%E6%88%90-research-20260821.md) | 2026-08-21 | H | 观察带 | [14.00, 23.00] | 22.08 | 区间内 | TRIGGERED |
| P0 | [美团-W](../%E7%BE%8E%E5%9B%A2/%E7%BE%8E%E5%9B%A2-earnings-2026H1.md) | 2026-08-31 | H | 舒适加仓带 | ≤ 70.00 | 69.25 | 区间内 | TRIGGERED |
| P0 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 2026-08-31 | US | 分批评估区 | [6.00, 8.50] | 7.99 | 区间内 | TRIGGERED |
| P0 | [赣锋锂业](../%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A/%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A-earnings-2026H1.md) | 2026-08-31 | H | H股小仓带 | [34.60, 43.80] | 29.28 | 低于下界 15.4% | TRIGGERED |
| P0 | [迅策科技](../%E8%BF%85%E7%AD%96/%E8%BF%85%E7%AD%96%E7%A7%91%E6%8A%80-earnings-2026H1.md) | 2026-08-31 | H | 评估带 | [60.00, 85.00] | 84.50 | 区间内 | TRIGGERED |
| P1 | Northrop Grumman | - | US | 研究性评估带 | [430.00, 470.00] | 473.46 | 0.7% | NEAR |
| P1 | [PDD Holdings](../%E6%8B%BC%E5%A4%9A%E5%A4%9A/%E6%8B%BC%E5%A4%9A%E5%A4%9A-thesis.md) | 2026-08-31 | US | 首次建仓评估线 | ≤ 75.00 | 78.50 | 4.7% | NEAR |
| P1 | [中兴通讯](../%E4%B8%AD%E5%85%B4%E9%80%9A%E8%AE%AF/%E4%B8%AD%E5%85%B4%E9%80%9A%E8%AE%AF-research-20260803.md) | 2026-08-03 | A | 评估带 | [22.00, 28.00] | 29.32 | 4.7% | NEAR |
| P1 | [北京君正](../%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3/%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3-research-20260817.md) | 2026-08-17 | A | A股复核带 | [90.00, 115.00] | 119.74 | 4.1% | NEAR |
| P1 | [多氟多](../%E5%A4%9A%E6%B0%9F%E5%A4%9A/%E5%A4%9A%E6%B0%9F%E5%A4%9A-earnings-2026H1.md) | 2026-09-12 | A | 评估带 | [26.00, 30.00] | 30.05 | 0.2% | NEAR |
| P1 | [杭叉集团](../%E6%9D%AD%E5%8F%89%E9%9B%86%E5%9B%A2/%E6%9D%AD%E5%8F%89%E9%9B%86%E5%9B%A2-research-20260926.md) | 2026-09-26 | A | 研究性分批评估带 | [20.00, 21.50] | 21.73 | 1.1% | NEAR |
| P1 | [雅克科技](../%E9%9B%85%E5%85%8B%E7%A7%91%E6%8A%80/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | 2026-07-20 | A | 卫星仓带 | [90.00, 110.00] | 115.39 | 4.9% | NEAR |

## 二、财报与正式披露监控

| 优先级 | 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |
|---|---|---|---|---:|---|---|
| P1 | [lululemon](../lululemon/lululemon-news-20261007.md) | US | [8-K](https://www.sec.gov/Archives/edgar/data/1397187/000139718726000131/lulu-20260930.htm) | 1 | 08:15 | REVIEW |
| P1 | [中兴通讯](../%E4%B8%AD%E5%85%B4%E9%80%9A%E8%AE%AF/%E4%B8%AD%E5%85%B4%E9%80%9A%E8%AE%AF-research-20260803.md) | A | [关于按照《香港上市规则》公布2026年9月份证券变动月报表的公告](https://static.cninfo.com.cn/finalpage/2026-10-08/1225591340.PDF) | 1 | 00:00 | REVIEW |
| P1 | [中芯国际](../%E4%B8%AD%E8%8A%AF%E5%9B%BD%E9%99%85/%E4%B8%AD%E8%8A%AF%E5%9B%BD%E9%99%85-earnings-2026Q2.md) | A | [港股公告：证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-10-08/1225595451.PDF) | 1 | 00:00 | DONE |
| P1 | [剑桥科技](../%E5%89%91%E6%A1%A5%E7%A7%91%E6%8A%80/%E5%89%91%E6%A1%A5%E7%A7%91%E6%8A%80-research-20260817.md) | H | [1. PLACING OF NEW H SHARES UNDER GENERAL MANDATE&#x3b; AND 2…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1008/2026100800139.pdf) | 1 | 08:25 | REVIEW |
| P1 | [剑桥科技](../%E5%89%91%E6%A1%A5%E7%A7%91%E6%8A%80/%E5%89%91%E6%A1%A5%E7%A7%91%E6%8A%80-research-20260817.md) | A | [关于根据一般性授权配售新H股及发行可转换债券的公告](https://static.cninfo.com.cn/finalpage/2026-10-08/1225596020.PDF)<br>[H股公告-月报表](https://static.cninfo.com.cn/finalpage/2026-10-08/1225595320.PDF)<br>[第五届董事会第三十六次会议决议公告](https://static.cninfo.com.cn/finalpage/2026-10-08/1225596019.PDF) | 3 | 00:00 | REVIEW |
| P1 | [北京君正](../%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3/%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3-research-20260817.md) | A | [H股公告-截至2026年9月30日止股份发行人的证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-10-08/1225596034.PDF) | 1 | 11:46 | REVIEW |
| P1 | [北京君正](../%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3/%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3-research-20260817.md) | H | [MONTHLY RETURN OF EQUITY ISSUER ON MOVEMENTS IN SECURITIES F…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1008/2026100800111.pdf) | 1 | 08:01 | DONE |
| P1 | [华虹宏力](../%E5%8D%8E%E8%99%B9%E5%AE%8F%E5%8A%9B/%E5%8D%8E%E8%99%B9%E5%8D%8A%E5%AF%BC%E4%BD%93-earnings-2026H1.md) | H | [(REVISED) MONTHLY RETURN OF EQUITY ISSUER ON MOVEMENTS IN SE…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1008/2026100800287.pdf) | 1 | 15:02 | REVIEW |
| P1 | [圣邦股份](../%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD/%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD-research-20260803.md) | A | [H股公告-截至2026年9月30日止股份发行人的证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-10-08/1225595387.PDF) | 1 | 00:00 | DONE |
| P1 | [天齐锂业](../%E5%A4%A9%E9%BD%90%E9%94%82%E4%B8%9A/%E5%A4%A9%E9%BD%90%E9%94%82%E4%B8%9A-research-20260803.md) | A | [H股公告：证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-10-08/1225589957.PDF) | 1 | 00:00 | DONE |
| P1 | [安克创新](../%E5%AE%89%E5%85%8B%E5%88%9B%E6%96%B0/%E5%AE%89%E5%85%8B%E5%88%9B%E6%96%B0-earnings-2026H1.md) | A | [H股公告-截至2026年9月30日止之股份发行人的证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-10-08/1225596002.PDF) | 1 | 07:52 | REVIEW |
| P1 | [立讯精密](../%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86/%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86-research-20260803.md) | A | [H股公告-截至2026年9月30日止月份之股份发行人的证券变动月报表](https://static.cninfo.com.cn/finalpage/2026-10-08/1225595408.PDF) | 1 | 00:00 | DONE |
| P1 | [群核科技](../%E7%BE%A4%E6%A0%B8%E7%A7%91%E6%8A%80/%E7%BE%A4%E6%A0%B8%E7%A7%91%E6%8A%80-earnings-2026H1.md) | H | [PROPOSED CHANGE OF COMPANY NAME&#x3b; PROPOSED AMENDMENTS TO…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1008/2026100800235.pdf) | 1 | 12:00 | DONE |
| P1 | [蓝思科技](../%E8%93%9D%E6%80%9D%E7%A7%91%E6%8A%80/%E8%93%9D%E6%80%9D%E7%A7%91%E6%8A%80-research-20260803.md) | A | [H股公告：联合公告每月更新资料内容有关中信里昂证券有限公司代表蓝思科技股份有限公司就收购巨腾国际控股有限公司全部已发行股…](https://static.cninfo.com.cn/finalpage/2026-10-08/1225595388.PDF) | 1 | 00:00 | REVIEW |
| P1 | [赣锋锂业](../%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A/%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A-earnings-2026H1.md) | A | [H股公告](https://static.cninfo.com.cn/finalpage/2026-10-08/1225590578.PDF) | 1 | 00:00 | DONE |
| P1 | [长光辰芯](../%E9%95%BF%E5%85%89%E8%BE%B0%E8%8A%AF/%E9%95%BF%E5%85%89%E8%BE%B0%E8%8A%AF-team-20260409/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1008/2026100800001.pdf) | 1 | 06:02 | DONE |

| 优先级 | 标的 | 披露/事项 | 日期 | 状态 | 为什么现在 | 核验事实/正式来源 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|---|
| P0 | [Accenture](../Accenture/Accenture-thesis.md) | FY26 Q4/全年财报（约9月）：已逾期 | 2026-09-30 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 核全年本币增速、利润率、AI可审计指标 |
| P1 | [Alphabet/Google](../Google/Google-earnings-2026Q2.md) | 2026Q3/10-Q后复检：12 天后到期 | 2026-10-20 | UPCOMING_14D | 登记事件状态为12 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 核CapEx、FCF、云增速 |
| P1 | [AZZ Inc.](../AZZ/AZZ-research-20260901.md) | FY2027 Q2财报（公司IR已确认）：5 天后到期 | 2026-10-13 | UPCOMING_7D | 登记事件状态为5 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 公司IR于2026-09-23公告：10月13日美股收盘后发布财报，10月14日11:00 ET举行电话会。核Metal/Precoat量价与EBITDA率、Washington新线、Seattle整合、债务削减及FY2027指引。[公司公告](https://investor.azz.com/2026-09-23-AZZ-Inc-to-Review-Second-Quarter-Fiscal-Year-2027-Financial-Results-on-Wednesday,-October-14,-2026) |
| P1 | [Microsoft](../%E5%BE%AE%E8%BD%AF/%E5%BE%AE%E8%BD%AF-thesis.md) | FY2027Q1财报：12 天后到期 | 2026-10-20 | UPCOMING_14D | 登记事件状态为12 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 核Azure增速、云毛利、>$50B CapEx后的FCF |
| P1 | [SK hynix](../SK%E6%B5%B7%E5%8A%9B%E5%A3%AB/SK%E6%B5%B7%E5%8A%9B%E5%A3%AB-thesis-20260713.md) | 3Q26财报：12 天后到期 | 2026-10-20 | UPCOMING_14D | 登记事件状态为12 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 核HBM4/HBM4E认证与份额、DRAM/NAND价格、扩产现金回报 |
| P1 | [英特尔](../Intel/Intel-research-20260826.md) | 2026Q3财报（日期待公司IR确认）：14 天后到期 | 2026-10-22 | UPCOMING_14D | 登记事件状态为14 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 核DCAI单位/ASP、产品FCF、Foundry外部收入和亏损率、18A/14A客户及总股本/债务变化 |
| P2 | [Albemarle](../Albemarle/Albemarle-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Energy Storage实现价与销量、Specialties利润、TTM FCF、资本开支、净债务、CGP3恢复及CEO继任<br>待人工确认 |
| P2 | [Credo Technology](../Credo/Credo-research-20260903.md) | FY2027 Q2财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入US$525–535m指引兑现、GAAP毛利率62.9%–64.9%、AEC驱动是否分散、库存/应收/经营现金流、SBC与DustPhotonics光学协同<br>待人工确认 |
| P2 | [Planet Labs PBC](../Planet%20Labs/Planet%20Labs-research-20260908.md) | FY2027 Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核D&I/商业收入、点时确认收入、RPO/Backlog、GAAP营业亏损、Capex、ATM与完全稀释股数<br>待人工确认 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入250-265m指引、GAAP毛利率29%-31%、Adjusted EBITDA亏损、backlog转化、现金消耗及稀释股数<br>待人工确认 |
| P2 | [Sea Limited](../SE/SE-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Shopee EBITDA/GMV、GMV增速、物流成本、Monee拨备/贷款、90+ NPL、Garena bookings及Q3调整后EBITDA新口径<br>待人工确认 |
| P2 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-earnings-2026Q2.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核广告同比是否仍>15%、游戏是否止跌、毛利率是否≥36%、应收账款与经营现金流；Q4财报再验游戏同比转正承诺。<br>待人工确认 |
| P2 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B-research-20260927.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核广告和电商止跌、毛利率能否恢复至至少53%、CFO扣资本购买与租赁、可灵亏损与融资稀释；若仅一季改善，后续一期再验证。<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核剔除喜马拉雅后的原有业务增长、会员收入、毛利率、广告承压和Non-IFRS利润<br>待人工确认 |

## 三、其他监控

| 优先级 | 标的/数据源 | 事项 | 日期 | 状态 | 为什么现在 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|
| P0 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-earnings-2026Q2.md) | 《Lumi Master》全球上线：已逾期 | 2026-09-17 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | 核初期留存、付费与投放纪律；不以下载量/榜单替代游戏收入和ROI，也不构成自动交易信号。 |
| P1 | [Accenture](../Accenture/Accenture-thesis.md) | Investor Day：6 天后到期 | 2026-10-14 | UPCOMING_7D | 登记事件状态为6 天后到期，需按备注核验；监控本身不作投资决定。 | - | 核增长战略、并购整合、AI承诺 |
| P1 | [AppLovin](../AppLovin/AppLovin-news-20261007.md) | 新闻脉搏：增长与合规风险复检：13 天后到期 | 2026-10-21 | UPCOMING_14D | 登记事件状态为13 天后到期，需按备注核验；监控本身不作投资决定。 | - | 核电商真实流量/付费客户与收入、游戏广告份额/价差、Unity数据争议与圣迭戈县儿童广告及隐私诉讼；核公司回应/临时救济/平台整改，不把指控当裁决或跌价当买入信号 |
| P1 | [lululemon](../lululemon/lululemon-news-20261007.md) | 新闻与新CEO执行复检：13 天后到期 | 2026-10-21 | UPCOMING_14D | 登记事件状态为13 天后到期，需按备注核验；监控本身不作投资决定。 | - | 核新CEO战略/量化产品销售、财务指引与Q3正式披露日期；跟踪退税消费者诉讼/PFAS正式进展。美洲可比销售、流量/转化、折扣、库存及剔除退税的正常毛利为核心；中国区分报表和固定汇率口径。新品/开店/名人交易不等于经营修复。 |
| P1 | [Progressive](../Progressive/Progressive-research-20260927.md) | 2026年9月月度结果：6 天后到期 | 2026-10-14 | UPCOMING_7D | 登记事件状态为6 天后到期，需按备注核验；监控本身不作投资决定。 | - | 公司8月月报宣布该日开盘前披露；核NPW、CR、事故年率、准备金发展与在保保单；广告费待Q3 10-Q。 |
| P2 | [Credo Technology](../Credo/Credo-research-20260903.md) | FY2027 Q2财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 复核客户集中度、AEC与光学产品发展、毛利率、FCF转化、收购整合与稀释是否改变US$120–140研究带<br>待人工确认 |
| P2 | [Planet Labs PBC](../Planet%20Labs/Planet%20Labs-research-20260908.md) | FY2027 Q3财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 判断国防项目能否转为可重复高毛利服务，并重估稀释、净现金和估值<br>待人工确认 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | Iridium交易审批与融资条款：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 跟踪Iridium股东和监管审批、3.6bn美元桥贷置换成本、最终交换比例与并表时间<br>待人工确认 |
| P2 | [Sea Limited](../SE/SE-research-20260901.md) | Sea 2026Q3财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 复核竞争税、Shopee盈利质量、Monee信用周期、Garena现金流及当前估值是否提供安全边际<br>待人工确认 |
| P2 | [杭叉集团](../%E6%9D%AD%E5%8F%89%E9%9B%86%E5%9B%A2/%E6%9D%AD%E5%8F%89%E9%9B%86%E5%9B%A2-research-20260926.md) | 可转债最终条款及审核进展：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 预案尚未发行；核发行规模、转股价、票息、项目审批、潜在稀释和每股资本回报<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 喜马拉雅整合与商誉复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 核独立收入、盈利/FCF、后台整合成本、无形资产摊销及92.36亿元新增商誉<br>待人工确认 |

---

价格达到条件只触发研究复核；正式披露的模型判断也只用于研究分流。
本报告用于学习和研究，不构成投资建议，也不会自动作出买卖或仓位结论。
