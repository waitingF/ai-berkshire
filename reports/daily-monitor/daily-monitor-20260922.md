# 每日监控

**数据截止日**：2026-09-22（Asia/Shanghai）
**运行状态**：DEGRADED
**摘要**：P0 1 · P1 11 · 新增价格 2 · 新增披露 9 · 异常 1
**数据源状态**：quotes=OK、cninfo=OK、hkex=OK、sec=FAILED（SEC ticker 未映射到 CIK: UFO）

> 价格条件、正式披露与其他研究缺口在同一份报告中展示；优先级表示研究处理顺序，不代表交易信号。

## 一、价格监控

> 价格优先级：P0=到达建仓或研究复核条件；P1=距对应边界≤5%；P2 与已越警戒线事项不展示。优先级只表示复核紧迫度，不代表交易信号。

| 优先级 | 标的 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |
|---|---|---|---|---:|---:|---:|---|
| P0 | [Novo Nordisk](../Novo%20Nordisk/Novo%20Nordisk-earnings-2026Q2.md) | US | 观察仓带 | [44.00, 46.00] | 39.80 | 低于下界 9.5% | TRIGGERED |
| P0 | [Reddit](../Reddit/Reddit-earnings-2026Q2.md) | US | 小仓跟踪带 | [145.00, 165.00] | 158.73 | 区间内 | TRIGGERED |
| P0 | [Sea Limited](../SE/SE-research-20260901.md) | US | 分层研究性评估区间 | [75.00, 105.00] | 102.65 | 区间内 | TRIGGERED |
| P0 | [上海复旦](../%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6/%E4%B8%8A%E6%B5%B7%E5%A4%8D%E6%97%A6-earnings-2026H1.md) | H | H股原分批研究带（暂停执行） | [20.00, 28.00] | 27.10 | 区间内 | TRIGGERED |
| P0 | [中国平安](../%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89/%E4%B8%AD%E5%9B%BD%E5%B9%B3%E5%AE%89-earnings-2026H1.md) | A | A股持有/分批复核带 | [48.00, 55.00] | 54.46 | 区间内 | TRIGGERED |
| P0 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-earnings-2026Q2.md) | US | Q2后研究性分批带 | [12.00, 16.00] | 15.18 | 区间内 | TRIGGERED |
| P0 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | H | 评估带 | [35.00, 40.00] | 31.22 | 低于下界 10.8% | TRIGGERED |
| P0 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | US | 分批评估区 | [6.00, 8.50] | 8.17 | 区间内 | TRIGGERED |
| P0 | [赣锋锂业](../%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A/%E8%B5%A3%E9%94%8B%E9%94%82%E4%B8%9A-earnings-2026H1.md) | H | H股小仓带 | [34.60, 43.80] | 33.34 | 低于下界 3.6% | TRIGGERED |
| P1 | [Adobe](../Adobe/Adobe-earnings-2026Q3.md) | US | Q3后研究性分批上限 | ≤ 247.00 | 249.52 | 1.0% | NEAR |
| P1 | [Albemarle](../Albemarle/Albemarle-research-20260901.md) | US | 研究性分批评估带 | [90.00, 110.00] | 112.92 | 2.7% | NEAR |
| P1 | [AppLovin](../AppLovin/AppLovin-earnings-2026Q2.md) | US | 分批复核带 | [300.00, 330.00] | 330.17 | 0.1% | NEAR |
| P1 | [杭叉集团](../%E6%9D%AD%E5%8F%89%E9%9B%86%E5%9B%A2-deepseek%E5%88%86%E6%9E%90/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | 等待带 | [20.00, 23.00] | 23.45 | 2.0% | NEAR |
| P1 | [汇川技术](../%E6%B1%87%E5%B7%9D%E6%8A%80%E6%9C%AF/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | 理想买点带 | [45.00, 52.00] | 54.05 | 3.9% | NEAR |
| P1 | [美团-W](../%E7%BE%8E%E5%9B%A2/%E7%BE%8E%E5%9B%A2-earnings-2026H1.md) | H | 舒适加仓带 | ≤ 70.00 | 73.20 | 4.6% | NEAR |
| P1 | [贵州茅台](../%E8%8C%85%E5%8F%B0/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | 建仓参考带 | [1100.00, 1250.00] | 1253.80 | 0.3% | NEAR |

## 二、财报与正式披露监控

| 优先级 | 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |
|---|---|---|---|---:|---|---|
| P1 | [北京君正](../%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3/%E5%8C%97%E4%BA%AC%E5%90%9B%E6%AD%A3-research-20260817.md) | A | [关于首次回购公司股份暨回购股份方案实施进展的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575136.PDF) | 1 | 00:00 | REVIEW |
| P1 | [厦门钨业](../%E5%8E%A6%E9%97%A8%E9%92%A8%E4%B8%9A/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | [厦门钨业关于2026年度第一期科技创新债券发行结果的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225573804.PDF)<br>[厦门钨业关于公司提起仲裁的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225573806.PDF) | 2 | 00:00 | REVIEW |
| P1 | [国电南瑞](../%E5%9B%BD%E7%94%B5%E5%8D%97%E7%91%9E/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | [国电南瑞关于2026年半年度权益分派实施后调整回购价格上限的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575120.PDF)<br>[国电南瑞2026年半年度权益分派实施公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575117.PDF)<br>[上海东方华银律师事务所关于国电南瑞科技股份有限公司差异化分红之法律意见书](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575102.PDF) | 3 | 00:00 | REVIEW |
| P1 | [圣邦股份](../%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD/%E5%9C%A3%E9%82%A6%E8%82%A1%E4%BB%BD-research-20260803.md) | A | [关于部分股票期权注销完成的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225576260.PDF) | 1 | 16:26 | DONE |
| P1 | [多氟多](../%E5%A4%9A%E6%B0%9F%E5%A4%9A/%E5%A4%9A%E6%B0%9F%E5%A4%9A-earnings-2026H1.md) | A | [关于控股股东及其一致行动人部分股份解质押的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225573782.PDF) | 1 | 00:00 | REVIEW |
| P1 | [德明利](../%E5%BE%B7%E6%98%8E%E5%88%A9/%E5%BE%B7%E6%98%8E%E5%88%A9-research-20260826.md) | A | [关于2025年股票期权激励计划预留部分授予登记完成的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225574554.PDF) | 1 | 00:00 | REVIEW |
| P1 | [拓荆科技](../%E6%8B%93%E8%8D%86%E7%A7%91%E6%8A%80/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | [关于召开2026年半年度业绩暨现金分红说明会的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225573948.PDF) | 1 | 00:00 | REVIEW |
| P1 | [汇川技术](../%E6%B1%87%E5%B7%9D%E6%8A%80%E6%9C%AF/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.md) | A | [上海市锦天城律师事务所关于深圳市汇川技术股份有限公司第八期股权激励计划（草案）的法律意见书](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575746.PDF)<br>[关于变更部分回购股份用途并注销暨减少公司注册资本及修订《公司章程》的公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575738.PDF)<br>[第六届董事会薪酬与考核委员会关于第八期股权激励计划相关事项的核查意见](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575743.PDF)<br>[关于召开2026年第二次临时股东会的通知](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575745.PDF)<br>[第八期股权激励计划（草案）](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575740.PDF)<br>[第六届董事会第十七次会议决议公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575744.PDF)<br>[创业板上市公司股权激励自查表](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575742.PDF)<br>[汇川技术第八期股权激励计划实施考核管理办法](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575741.PDF)<br>[第八期股权激励计划（草案）摘要](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575739.PDF) | 9 | 00:00 | REVIEW |
| P1 | [立讯精密](../%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86/%E7%AB%8B%E8%AE%AF%E7%B2%BE%E5%AF%86-research-20260803.md) | A | [关于“立讯转债”即将到期及停止交易的第二次提示性公告](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575502.PDF) | 1 | 00:00 | REVIEW |

| 优先级 | 标的 | 披露/事项 | 日期 | 状态 | 为什么现在 | 核验事实/正式来源 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|---|
| P2 | [Accenture](../Accenture/Accenture-thesis.md) | FY26 Q4/全年财报（约9月）：8 天后到期 | 2026-09-30 | UPCOMING_14D | 登记事件状态为8 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 核全年本币增速、利润率、AI可审计指标 |
| P2 | [Albemarle](../Albemarle/Albemarle-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Energy Storage实现价与销量、Specialties利润、TTM FCF、资本开支、净债务、CGP3恢复及CEO继任<br>待人工确认 |
| P2 | [AZZ Inc.](../AZZ/AZZ-research-20260901.md) | FY2027 Q2财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Metal/Precoat量价与EBITDA率、Washington新线、Seattle整合、债务削减及FY2027指引<br>待人工确认 |
| P2 | [Credo Technology](../Credo/Credo-research-20260903.md) | FY2027 Q2财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入US$525–535m指引兑现、GAAP毛利率62.9%–64.9%、AEC驱动是否分散、库存/应收/经营现金流、SBC与DustPhotonics光学协同<br>待人工确认 |
| P2 | [Planet Labs PBC](../Planet%20Labs/Planet%20Labs-research-20260908.md) | FY2027 Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核D&I/商业收入、点时确认收入、RPO/Backlog、GAAP营业亏损、Capex、ATM与完全稀释股数<br>待人工确认 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核收入250-265m指引、GAAP毛利率29%-31%、Adjusted EBITDA亏损、backlog转化、现金消耗及稀释股数<br>待人工确认 |
| P2 | [Sea Limited](../SE/SE-research-20260901.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核Shopee EBITDA/GMV、GMV增速、物流成本、Monee拨备/贷款、90+ NPL、Garena bookings及Q3调整后EBITDA新口径<br>待人工确认 |
| P2 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-earnings-2026Q2.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核广告同比是否仍>15%、游戏是否止跌、毛利率是否≥36%、应收账款与经营现金流；Q4财报再验游戏同比转正承诺。<br>待人工确认 |
| P2 | [快手](../%E5%BF%AB%E6%89%8B/%E5%BF%AB%E6%89%8B2026Q2%E8%B4%A2%E6%8A%A5%E6%B7%B1%E5%BA%A6%E8%A7%A3%E8%AF%BB-20260820.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核广告/电商是否重回双位数、毛利率能否恢复至至少53%、自由现金流、可灵收入/亏损与增资交割。<br>待人工确认 |
| P2 | [腾讯控股](../%E8%85%BE%E8%AE%AF/%E8%85%BE%E8%AE%AF-thesis.md) | 2026Q3财报：8 天后到期 | 2026-09-30 | UPCOMING_14D | 登记事件状态为8 天后到期，需按备注核验；监控本身不作投资决定。 | - | - | 盯Q3 FCF转正、AI预付款回收、国际游戏、回购 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 2026Q3财报（日期待公司IR确认）：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | - | 核剔除喜马拉雅后的原有业务增长、会员收入、毛利率、广告承压和Non-IFRS利润<br>待人工确认 |

## 三、其他监控

| 优先级 | 标的/数据源 | 事项 | 日期 | 状态 | 为什么现在 | 下一流程 | 备注 |
|---|---|---|---|---|---|---|---|
| P0 | [Novo Nordisk](../Novo%20Nordisk/Novo%20Nordisk-earnings-2026Q2.md) | Capital Markets Day：已逾期 | 2026-09-21 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | 核美国市场修复、口服Wegovy/下一代管线与2027增长框架 |
| P0 | [Progressive](../Progressive/Progressive-earnings-2026Q2.md) | 2026年8月月度结果复核窗口：已逾期 | 2026-09-18 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | 公司IR月度结果日历确认2026-09-18发布8月结果；届时核NPW、CR、广告费用与事故年损失率。 |
| P0 | [哔哩哔哩](../%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9-earnings-2026Q2.md) | 《Lumi Master》全球上线：已逾期 | 2026-09-17 | OVERDUE | 登记事件状态为已逾期，需按备注核验；监控本身不作投资决定。 | - | 核初期留存、付费与投放纪律；不以下载量/榜单替代游戏收入和ROI，也不构成自动交易信号。 |
| P1 | SEC | 数据源异常 | - | FAILED | SEC ticker 未映射到 CIK: UFO | - | 待人工确认 |
| P2 | [Credo Technology](../Credo/Credo-research-20260903.md) | FY2027 Q2财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 复核客户集中度、AEC与光学产品发展、毛利率、FCF转化、收购整合与稀释是否改变US$120–140研究带<br>待人工确认 |
| P2 | [Planet Labs PBC](../Planet%20Labs/Planet%20Labs-research-20260908.md) | FY2027 Q3财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 判断国防项目能否转为可重复高毛利服务，并重估稀释、净现金和估值<br>待人工确认 |
| P2 | [Rocket Lab](../RKLB/RKLB-research-20260831.md) | Iridium交易审批与融资条款：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 跟踪Iridium股东和监管审批、3.6bn美元桥贷置换成本、最终交换比例与并表时间<br>待人工确认 |
| P2 | [Sea Limited](../SE/SE-research-20260901.md) | Sea 2026Q3财报后论文复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 复核竞争税、Shopee盈利质量、Monee信用周期、Garena现金流及当前估值是否提供安全边际<br>待人工确认 |
| P2 | [腾讯音乐](../%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90/%E8%85%BE%E8%AE%AF%E9%9F%B3%E4%B9%90-research-20260831.md) | 喜马拉雅整合与商誉复检：日期缺失或格式异常 | - | OPEN | 登记事件状态为日期缺失或格式异常，需按备注核验；监控本身不作投资决定。 | - | 核独立收入、盈利/FCF、后台整合成本、无形资产摊销及92.36亿元新增商誉<br>待人工确认 |

---

价格达到条件只触发研究复核；正式披露的模型判断也只用于研究分流。
本报告用于学习和研究，不构成投资建议，也不会自动作出买卖或仓位结论。
