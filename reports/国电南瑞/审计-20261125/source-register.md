# 国电南瑞研究信源记录

核验日：2026-11-25；北京时间。金额原始单位为人民币元，报告展示为亿元。仅保存抽取事实、定位和计算输入；不保存完整公告、下载PDF或模型提示词。

## 报表渠道

| 资料 | 原始来源与定位 | 第二分发渠道 |
|---|---|---|
| 2021—2022七项年度原值 | [2022年报公司公告全文](https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=9137289)，主要会计数据、合并利润表、合并现金流量表、合并资产负债表 | 东方财富RPT_DMSK_FN三表；逐格核对21项中的14项一致 |
| 2023七项原值 | [2024年报公司公告全文](https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=11033834)，2023追溯比较列及上述四表 | 东方财富年度行，7项一致 |
| 2024—2025年度原值 | [2025年报](https://static.cninfo.com.cn/finalpage/2026-04-30/1225257886.PDF)，主要会计数据、合并三表、主营业务表；[公司公告全文](https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12278691)可检索元数 | 东方财富年度三表，2024为2025年报追溯值；[东方财富分发原PDF](https://pdf.dfcfw.com/pdf/H2_AN202604291821752997_1.pdf) |
| 2026H1 | [中报](https://static.cninfo.com.cn/finalpage/2026-08-27/1225508099.PDF)，第9页财务、第23—24页分部、第40—41页关联销售、第192／196页继保持股 | 东方财富三表及[中报PDF](https://pdf.dfcfw.com/pdf/H2_AN202608261828473521_1.pdf) |
| 2026Q3 | [三季报](https://static.cninfo.com.cn/finalpage/2026-10-29/1225635689.PDF)，第1—3页摘要与现金解释、第6—9页资产负债、第10—12页利润、第13—14页现金 | 东方财富DMSK/F10三表及[三季报PDF](https://pdf.dfcfw.com/pdf/H2_AN202610281831118643_1.pdf) |
| 许继2026H1 | [巨潮原件](https://static.cninfo.com.cn/finalpage/2026-08-20/1225483623.PDF)，主要会计数据、成本、控制关系 | [东方财富原PDF](https://pdf.dfcfw.com/pdf/H2_AN202608191828163577_1.pdf) |
| 四方2026H1 | [巨潮原件](https://static.cninfo.com.cn/finalpage/2026-08-27/1225508922.PDF)，主要财务指标、成本与分部表，印刷页与PDF索引有差异 | [东方财富原PDF](https://pdf.dfcfw.com/pdf/H2_AN202608261828476393_1.pdf)，收入、归母、成本及二次／储能毛利逐项核对 |

东方财富API复取模板：[合并资产负债表](https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_F10_FINANCE_GBALANCE&columns=ALL&filter=%28SECUCODE%3D%22600406.SH%22%29&sortColumns=REPORT_DATE&sortTypes=-1&pageSize=50&pageNumber=1)。reportName可替换为RPT_DMSK_FN_INCOME、RPT_DMSK_FN_CASHFLOW、RPT_DMSK_FN_BALANCE；完整三表还包括RPT_F10_FINANCE_GINCOME、RPT_F10_FINANCE_GCASHFLOW。该渠道核验转录和分类，不构成第二次独立审计。

历史表原始输入保存在calculations.json的annual数组，含收入、归母、成本、营业利润、CFO、现金购建长期资产及货币资金；2021/22来源为2022年报，2023为2024年报追溯口径，2024/25为2025年报追溯口径。不得宣称严格同口径五年有机增长。

## 最新关键输入

| 字段 | 2026Q3期末／累计，人民币元 |
|---|---:|
| 注册股本，股 | 8031756156 |
| 营业收入 | 43879577511.61 |
| 归母净利润 | 4911652568.60 |
| CFO | -2919538534.11 |
| 现金购建长期资产 | 1178331939.15 |
| 货币资金 | 6932263372.88 |
| 交易性金融资产 | 6013927424.63 |
| 短借／长借 | 352207283.33／7000000 |
| 一年内非流动负债／租赁 | 71136126.99／57434388.23 |
| 归母权益／少数权益 | 52572913859.30／3766038700.54 |

以上关键字段已核对官方表及东方财富F10全量表。现金代理不含其他科目的定存、大额存单，亦未逐项剔受限货币，不能冒充完整可分配净现金。EV仅作示意。

## 其他可复核出处

- [新浪收盘行情](https://stocks.sina.cn/sh/?code=sh600406&page_type=simple&vt=1)：2026-11-25 15:34:59，24.60元，市值1975.81亿元；腾讯快照20261125161456同价、股本8031756156。
- [2026H1实施分红](https://static.cninfo.com.cn/finalpage/2026-09-22/1225575117.PDF)：0.153元／股，9月29日支付；[中证报分发全文](https://epaper.cs.com.cn/zgzqb/html/2026-09/22/nw.D110000zgzqb_20260922_5-B020.htm)。实际金额1221357557.35元，非预案1221949631.85元。
- [11月3日回购进展](https://epaper.cs.com.cn/zgzqb/html/2026-11/03/nw.D110000zgzqb_20261103_1-B013.htm)：截至10/31，8778052股、201156664.80元，激励用途。
- [11月3日说明会原件](https://sns.sseinfo.com/resources/images/upload/202611/202611041001053718450310.pdf)：管理层解释业务结构、汇率、退税、海外回款；无精确季度分部利润。
- [中债／财政部曲线](https://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo?locale=cn_ZH&nameType=1)：11/25十年国债约1.59%。模型ERP6.41%、β1.0为研究设定。
- 2025国网销售额3668786.26万元、占55.40%，前五客户4435084.78万元、占66.96%；合同金额不可代替收入。
- 2025分部毛利率与2026H1分部为直接披露；若与分部收入／成本重新相除的微小尾数不同，展示以公司两位小数披露为准。

## 模型与核验边界

三年PE、增长和情景概率是研究假设；十年g、ROIC、净派息率和增量再投资回报也是假设。被抽到时核验其与计算参数一致、工具输出和独立Decimal重算一致，不填写成“外部权威预测”。工具内calc含浮点求值，复现脚本同时以Decimal重算并校验一致性；终值工具本身含浮点，保留其原输出，不虚称全部金融工具内部均为十进制。

完整经济现金IRR由逐年现金和终值二分求根，与工具“终值几何回报＋固定派息率”分开。期望情景IRR为情景IRR概率加权，不是期望现金路径的IRR，也不是证券可兑现收益承诺。

大师引文使用巴菲特2008信、芒格2014独立回顾、段永平2011-10-07雪球原帖仓库归档及李录2026-10-05哥大官方实录；均非对本公司直接评价。原文链接和定位列于正文，未编造买卖立场。
