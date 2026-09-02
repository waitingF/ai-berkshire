# 每日监控

**数据截止日**：2026-09-02（Asia/Shanghai）
**运行状态**：DEGRADED
**摘要**：P0 4 · P1 21 · 新增价格 2 · 新增披露 22 · 异常 0
**数据源状态**：quotes=OK、cninfo=OK、hkex=OK、sec=OK

> 价格条件、正式披露与其他研究缺口在同一份报告中展示；优先级表示研究处理顺序，不代表交易信号。

## 一、价格监控

> 价格优先级：P0=到达建仓或研究复核条件；P1=距对应边界≤5%；P2 与已越警戒线事项不展示。优先级只表示复核紧迫度，不代表交易信号。

| 优先级 | 标的 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |
|---|---|---|---|---:|---:|---:|---|
| P0 | [AppLovin](../AppLovin/AppLovin-earnings-2026Q2.md) | US | 分批复核带 | [300.00, 330.00] | 311.74 | 区间内 | TRIGGERED |
| P0 | [lululemon](../lululemon/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | US | 观察仓带 | ≤ 119.00 | 118.00 | 区间内 | TRIGGERED |
| P0 | [Novo Nordisk](../Novo%20Nordisk/Novo%20Nordisk-earnings-2026Q2.md) | US | 观察仓带 | [44.00, 46.00] | 45.12 | 区间内 | TRIGGERED |
| P0 | [Reddit](../Reddit/Reddit-earnings-2026Q2.md) | US | 小仓跟踪带 | [145.00, 165.00] | 144.64 | 低于下界 0.2% | TRIGGERED |
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | H | H股原分批研究带（暂停执行） | [20.00, 28.00] | 26.52 | 区间内 | TRIGGERED |
| P0 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-research-20260803.md) | US | 研究性分批带 | [12.00, 16.00] | 15.79 | 区间内 | TRIGGERED |
| P0 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | H | 评估带 | [35.00, 40.00] | 33.64 | 低于下界 3.9% | TRIGGERED |
| P0 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | US | 分批评估区 | [6.00, 8.50] | 8.29 | 区间内 | TRIGGERED |
| P0 | [赣锋锂业](../%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A/%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A-earnings-2026H1.md) | H | H股小仓带 | [34.60, 43.80] | 38.22 | 区间内 | TRIGGERED |
| P1 | [Qualcomm](../Qualcomm/Qualcomm-earnings-FY2026Q3.md) | US | 理想买入带 | ≤ 160.00 | 166.61 | 4.1% | NEAR |
| P1 | [中国平安](../%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89/%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89-thesis.md) | A | A股持有/分批复核带 | [48.00, 55.00] | 56.63 | 3.0% | NEAR |
| P1 | [腾讯控股](../%E8%85%BE%E8%AE%AF/%E8%85%BE%E8%AE%AF-thesis.md) | H | 加仓带 | [400.00, 430.00] | 438.20 | 1.9% | NEAR |
| P1 | [贵州茅台](../%E8%8C%85%E5%8F%B0/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | 建仓参考带 | [1100.00, 1250.00] | 1297.50 | 3.8% | NEAR |

## 二、财报与正式披露监控

| 优先级 | 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |
|---|---|---|---|---:|---|---|
| P0 | [云迹科技](../%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80/%E4%BA%91%E8%BF%B9%E7%A7%91%E6%8A%80-earnings-2026H1.md) | H | [POLL RESULTS OF THE EXTRAORDINARY GENERAL MEETING HELD ON WE…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0902/2026090202091.pdf) | 1 | 19:01 | REVIEW |
| P0 | [华虹宏力](../%E5%8D%8E%E8%99%B9%E5%AE%8F%E5%8A%9B/%E5%8D%8E%E8%99%B9%E5%8D%8A%E5%AF%BC%E4%BD%93-earnings-2026H1.md) | H | [Interim Report 2026](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0902/2026090200736.pdf) | 1 | 16:30 | REVIEW |
| P1 | [三环集团](../%E4%B8%89%E7%8E%AF%E9%9B%86%E5%9B%A2/%E4%B8%89%E7%8E%AF%E9%9B%86%E5%9B%A2-research-20260803.md) | A | [H股公告-翌日披露报表](https://static.cninfo.com.cn/finalpage/2026-09-02/1225541874.PDF)<br>[关于召开2026年第二次临时股东会的通知](https://static.cninfo.com.cn/finalpage/2026-09-02/1225541872.PDF)<br>[关于回购股份比例达到1%暨回购进展的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225541873.PDF) | 3 | 00:00 | REVIEW |
| P1 | [东方电气](../%E4%B8%9C%E6%96%B9%E7%94%B5%E6%B0%94/%E4%B8%9C%E6%96%B9%E7%94%B5%E6%B0%94-research-20260803.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0902/2026090201733.pdf) | 1 | 17:50 | REVIEW |
| P1 | [中兴通讯](../%E4%B8%AD%E5%85%B4%E9%80%9A%E8%AE%AF/%E4%B8%AD%E5%85%B4%E9%80%9A%E8%AE%AF-research-20260803.md) | A | [关于按照《香港上市规则》公布2026年8月份证券变动月报表的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225540530.PDF) | 1 | 00:00 | DONE |
| P1 | [中国平安](../%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89/%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89-thesis.md) | A | [中国平安H股公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225541592.PDF) | 1 | 00:00 | DONE |
| P1 | [中国广核](../%E4%B8%AD%E5%9B%BD%E5%B9%BF%E6%A0%B8/%E4%B8%AD%E5%9B%BD%E5%B9%BF%E6%A0%B8-earnings-2026H1.md) | H | [Monthly Return of Equity Issuer on Movements in Securities f…](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0902/2026090200661.pdf) | 1 | 16:01 | REVIEW |
| P1 | [兆易创新](../%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0/%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0-earnings-2026H1.md) | A | [兆易创新关于以集中竞价交易方式回购A股股份的进展公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225540932.PDF) | 1 | 00:00 | REVIEW |
| P1 | [剑桥科技](../%E5%89%91%E6%A1%A5%E7%A7%91%E6%8A%80/%E5%89%91%E6%A1%A5%E7%A7%91%E6%8A%80-research-20260803.md) | A | [H股公告-月報表](https://static.cninfo.com.cn/finalpage/2026-09-02/1225543947.PDF)<br>[H股公告-派发中期股息](https://static.cninfo.com.cn/finalpage/2026-09-02/1225543948.PDF)<br>[H股公告-派发截至2026年6月30日止六个月的中期股息（更新）](https://static.cninfo.com.cn/finalpage/2026-09-02/1225543951.PDF)<br>[2026年半年度A股权益分派实施公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225541696.PDF) | 4 | 00:00 | DONE |
| P1 | [北京君正](../%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3/%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3-research-20260817.md) | A | [关于召开2026年第一次临时股东会的通知](https://static.cninfo.com.cn/finalpage/2026-09-02/1225541638.PDF) | 1 | 00:00 | DONE |
| P1 | [华虹宏力](../%E5%8D%8E%E8%99%B9%E5%AE%8F%E5%8A%9B/%E5%8D%8E%E8%99%B9%E5%8D%8A%E5%AF%BC%E4%BD%93-earnings-2026H1.md) | A | [关于对外投资的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225542065.PDF) | 1 | 00:00 | REVIEW |
| P1 | [晶合集成](../%E6%99%B6%E5%90%88%E9%9B%86%E6%88%90/%E6%99%B6%E5%90%88%E9%9B%86%E6%88%90-research-20260821.md) | H | [新增公告，内容待确认](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0902/2026090202024.htm) | 1 | 18:50 | REVIEW |
| P1 | [汇川技术](../%E6%B1%87%E5%B7%9D%E6%8A%80%E6%9C%AF/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | [关于第七期股权激励计划预留授予部分股票期权注销完成的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225543110.PDF)<br>[关于第六期股权激励计划首次授予部分股票期权注销完成的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225543111.PDF)<br>[关于第六期股权激励计划预留授予部分股票期权注销完成的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225543109.PDF)<br>[关于第六期股权激励计划第二类限制性股票归属结果暨股份上市的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225543471.PDF) | 4 | 16:56 | DONE |
| P1 | [海尔智家](../%E6%B5%B7%E5%B0%94%E6%99%BA%E5%AE%B6-deepseek%E5%88%86%E6%9E%90/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | H | [翌日披露报表](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0902/2026090201771.pdf) | 1 | 17:57 | REVIEW |
| P1 | [澜起科技](../%E6%BE%9C%E8%B5%B7%E7%A7%91%E6%8A%80/%E6%BE%9C%E8%B5%B7%E7%A7%91%E6%8A%80-earnings-2026H1.md) | H | [翌日披露报表](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0902/2026090201943.pdf) | 1 | 18:22 | REVIEW |
| P1 | [澜起科技](../%E6%BE%9C%E8%B5%B7%E7%A7%91%E6%8A%80/%E6%BE%9C%E8%B5%B7%E7%A7%91%E6%8A%80-earnings-2026H1.md) | A | [H股公告-翌日披露报表](https://static.cninfo.com.cn/finalpage/2026-09-02/1225541970.PDF)<br>[澜起科技关于以集中竞价交易方式回购A股股份的进展公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225540833.PDF) | 2 | 00:00 | REVIEW |
| P1 | [立讯精密](../%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86/%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86-research-20260803.md) | A | [关于股份回购进展情况的公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225540885.PDF) | 1 | 00:00 | DONE |
| P1 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | US | [FORM 6-K](https://www.sec.gov/Archives/edgar/data/1744676/000119312526378527/d894888d6k.htm) | 1 | 04:46 | REVIEW |
| P1 | [赣锋锂业](../%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A/%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A-earnings-2026H1.md) | A | [H股公告](https://static.cninfo.com.cn/finalpage/2026-09-02/1225542579.PDF) | 1 | 00:00 | DONE |

| 优先级 | 标的 | 披露/事项 | 日期 | 状态 | 为什么现在 | 核验事实/正式来源 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|---|
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | 2026H1业绩：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报；事件保持开放。披露后核扣除约4.7亿公允价值收益后的经营利润、库存减值、管理层资本配置；当前暂停新建仓。 |
| P0 | [兆易创新](../%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0/%E5%85%86%E6%98%93%E5%88%9B%E6%96%B0-earnings-2026H1.md) | 2026H1正式中报：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报，事件保持开放；披露后核扣非、经营现金流、库存、关联交易。 |
| P0 | [多氟多](../%E5%A4%9A%E6%B0%9F%E5%A4%9A/%E5%A4%9A%E6%B0%9F%E5%A4%9A-earnings-2026H1.md) | 2026H1正式报告：已逾期 | 2026-08-31 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | - | 截至2026-08-31 21:30未取得正式中报，事件保持开放；披露后核锂盐毛利、OCF、净债务。 |
| P1 | [Albemarle](../Albemarle/Albemarle-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Energy Storage实现价与销量、Specialties利润、TTM FCF、资本开支、净债务、CGP3恢复及CEO继任<br>待人工确认 |
| P1 | [AZZ Inc.](../AZZ/AZZ-research-20260901.md) | FY2027 Q2财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Metal/Precoat量价与EBITDA率、Washington新线、Seattle整合、债务削减及FY2027指引<br>待人工确认 |
| P1 | [Sea Limited](../SE/SE-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Shopee EBITDA/GMV、GMV增速、物流成本、Monee拨备/贷款、90+ NPL、Garena bookings及Q3调整后EBITDA新口径<br>待人工确认 |
| P2 | [Adobe](../Adobe/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | FY2026Q3财报（公司IR已确认）：8 天后到期 | 2026-09-10 | UPCOMING_14D | 登记事件状态为8 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | Adobe IR 列示 2026-09-10 14:00 PT Q3 FY2026 earnings call；核FY2026 Q3业绩、CEO交接与AI产品商业化；SEC正式披露将由每日扫描捕获 |
| P2 | [lululemon](../lululemon/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | 下季报后复检：8 天后到期 | 2026-09-10 | UPCOMING_14D | 登记事件状态为8 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 核北美同店与库存 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入250-265m指引、GAAP毛利率29%-31%、Adjusted EBITDA亏损、backlog转化、现金消耗及稀释股数<br>待人工确认 |
| P2 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核广告/电商是否重回双位数、毛利率能否恢复至至少53%、自由现金流、可灵收入/亏损与增资交割。<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核剔除喜马拉雅后的原有业务增长、会员收入、毛利率、广告承压和Non-IFRS利润<br>待人工确认 |

## 三、其他监控

| 优先级 | 标的/数据源 | 事项 | 日期 | 状态 | 为什么现在 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|
| P1 | [Sea Limited](../SE/SE-research-20260901.md) | Sea 2026Q3财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 复核竞争税、Shopee盈利质量、Monee信用周期、Garena现金流及当前估值是否提供安全边际<br>待人工确认 |
| P2 | [Progressive](../Progressive/Progressive-earnings-2026Q2.md) | 2026年8月月度结果复核窗口：13 天后到期 | 2026-09-15 | UPCOMING_14D | 登记事件状态为13 天后到期，需按备注核验；监控本身不作投资决定。 | - | 日期为研究复核窗口，待公司IR确认具体发布时间；核NPW、CR、广告费用与事故年损失率。 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | Iridium交易审批与融资条款：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 跟踪Iridium股东和监管审批、3.6bn美元桥贷置换成本、最终交换比例与并表时间<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 喜马拉雅整合与商誉复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 核独立收入、盈利/FCF、后台整合成本、无形资产摊销及92.36亿元新增商誉<br>待人工确认 |

---

价格达到条件只触发研究复核；正式披露的模型判断也只用于研究分流。
本报告用于学习和研究，不构成投资建议，也不会自动作出买卖或仓位结论。
