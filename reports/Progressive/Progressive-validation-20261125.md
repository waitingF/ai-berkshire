# Progressive 研究验证记录

研究日：2026-11-25（北京时间）。对应[完整报告](Progressive-research-20261125.md)及[精确模型](Progressive-model-20261125.json)。

## 准出结论与边界

报告抽检和定稿后的终值参数 audit 均已准出。抽样固定种子42，98个被工具识别的数据点抽取15个；其中8项为披露事实或事实推导，5项为模型假设/计算，2项为日期及引用年份误识别。15项程序比对均在1%内，但不能宣称15项独立财务双源核验：两项噪声不计金融覆盖，模型项只验证计算。

抽中公司专有CR、分部NPE的第二载体为同一月报PDF，并非独立测量。关键年度收入、普通股净利、现金及短期投资另外与StockAnalysis核对；管理层当前持股、广告单位回报、10月现金单列和商业TNC集中度仍有来源缺口。Macrotrends正文受限，未充当最新完整验证源。

五年表、四季表和经营事实另由负责取数的代理逐项回查，未发现实质数字或币种错误。图表已渲染检查。未提交、推送或发布。

## 抽样记录

```json
[
  {
    "id": 4,
    "label": "车辆险 Agency · 前十月 CR",
    "reported_value": 85.6,
    "unit": "",
    "line_number": 31,
    "raw_text": "| 车辆险 Agency | 29.382 | 25.342 | 35.00% | 85.6 | 90.0 |",
    "fetched_value": 85.6,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm",
    "fetched_value2": 85.6,
    "fetched_source2": "https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43",
    "audit_category": "company_fact",
    "independence_note": "SEC与月报PDF是同一公司披露的两种载体，不是独立原始测量。"
  },
  {
    "id": 5,
    "label": "车辆险 Agency · 10 月 CR",
    "reported_value": 90.0,
    "unit": "",
    "line_number": 31,
    "raw_text": "| 车辆险 Agency | 29.382 | 25.342 | 35.00% | 85.6 | 90.0 |",
    "fetched_value": 90.0,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm",
    "fetched_value2": 90.0,
    "fetched_source2": "https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43",
    "audit_category": "company_fact",
    "independence_note": "SEC与月报PDF是同一公司披露的两种载体，不是独立原始测量。"
  },
  {
    "id": 15,
    "label": "Property · 10 月 CR",
    "reported_value": 60.8,
    "unit": "",
    "line_number": 33,
    "raw_text": "| Property | 3.116 | 2.622 | 3.63% | 74.7 | 60.8 |",
    "fetched_value": 60.8,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm",
    "fetched_value2": 60.8,
    "fetched_source2": "https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43",
    "audit_category": "company_fact",
    "independence_note": "SEC与月报PDF是同一公司披露的两种载体，不是独立原始测量。"
  },
  {
    "id": 14,
    "label": "Property · 前十月 CR",
    "reported_value": 74.7,
    "unit": "",
    "line_number": 33,
    "raw_text": "| Property | 3.116 | 2.622 | 3.63% | 74.7 | 60.8 |",
    "fetched_value": 74.7,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm",
    "fetched_value2": 74.7,
    "fetched_source2": "https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43",
    "audit_category": "company_fact",
    "independence_note": "SEC与月报PDF是同一公司披露的两种载体，不是独立原始测量。"
  },
  {
    "id": 12,
    "label": "Property · 2026 年前十月 NPE（US$bn）",
    "reported_value": 2.622,
    "unit": "",
    "line_number": 33,
    "raw_text": "| Property | 3.116 | 2.622 | 3.63% | 74.7 | 60.8 |",
    "fetched_value": 2.622,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm",
    "fetched_value2": 2.622,
    "fetched_source2": "https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43",
    "audit_category": "company_fact",
    "independence_note": "SEC与月报PDF是同一公司披露的两种载体，不是独立原始测量。"
  },
  {
    "id": 18,
    "label": "Commercial Lines · 前十月 NPW 占比",
    "reported_value": 13.2,
    "unit": "%",
    "line_number": 34,
    "raw_text": "| Commercial Lines | 10.881 | 8.995 | 13.20% | 88.6 | 84.8 |",
    "fetched_value": 13.198736808011013,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm；净签单保费原值计算",
    "fetched_value2": 13.198736808011013,
    "fetched_source2": "https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43",
    "audit_category": "derived_fact",
    "independence_note": "SEC与月报PDF是同一公司披露的两种载体，不是独立原始测量。"
  },
  {
    "id": 29,
    "label": "收盘价 · 含义与限制",
    "reported_value": 11.0,
    "unit": "",
    "line_number": 186,
    "raw_text": "| 收盘价 | US$235.68 | 11 月 24 日；StockAnalysis 与 CompaniesMarketCap 同价 |",
    "fetched_value": 11,
    "fetched_source": "StockAnalysis报价日期2026-11-24；这是月份误识别，非股价",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "extraction_noise",
    "independence_note": ""
  },
  {
    "id": 32,
    "label": "复算普通股市值 · 本报告口径",
    "reported_value": 136.152336,
    "unit": "",
    "line_number": 188,
    "raw_text": "| 复算普通股市值 | US$136.152336bn | 价格×实股；独立站点约 US$136.15bn |",
    "fetched_value": 136.152336,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm；235.68×577.7M",
    "fetched_value2": 136.15,
    "fetched_source2": "https://companiesmarketcap.com/progressive/marketcap/",
    "audit_category": "derived_fact",
    "independence_note": ""
  },
  {
    "id": 36,
    "label": "拼接稀释 EPS / 对应 PE · 本报告口径",
    "reported_value": 19.84,
    "unit": "",
    "line_number": 190,
    "raw_text": "| 拼接稀释 EPS / 对应 PE | 约 US$19.84 / 11.88 倍 | 不同期间平均股本不同，因此是近似值 |",
    "fetched_value": 19.84,
    "fetched_source": "https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm及FY2025月报；不同期平均股数EPS拼接近似",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "derived_fact",
    "independence_note": ""
  },
  {
    "id": 55,
    "label": "基准：回归后温和增长 · 按 10% 折现的今日价值",
    "reported_value": 193.45,
    "unit": "",
    "line_number": 217,
    "raw_text": "| **基准：回归后温和增长** | **+5%** | **16.21** | **14 倍** | **US$226.89** | **−3.73%** | **+2.72%** | **US$193.45** |",
    "fetched_value": 193.4469196093163,
    "fetched_source": "独立Decimal重算：三年EPS14×1.05^t、分配60%、退出PE14、r10%",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "model",
    "independence_note": "模型项核验只证明重算一致，不证明假设真实。"
  },
  {
    "id": 70,
    "label": "基准 · 前十年 EPS 增速",
    "reported_value": 5.0,
    "unit": "%",
    "line_number": 237,
    "raw_text": "| 基准 | +5% | 22.80 / 13.174 | 3% | 7 点 | 11.90 倍 | +1.42% | +5.77% |",
    "fetched_value": 5,
    "fetched_source": "模型基准前十年EPS增速假设；不冒充外部预测",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "model",
    "independence_note": "模型项核验只证明重算一致，不证明假设真实。"
  },
  {
    "id": 76,
    "label": "基准 · 含逐年分配的完整现金 IRR",
    "reported_value": 5.77,
    "unit": "%",
    "line_number": 237,
    "raw_text": "| 基准 | +5% | 22.80 / 13.174 | 3% | 7 点 | 11.90 倍 | +1.42% | +5.77% |",
    "fetched_value": 5.767465226799584,
    "fetched_source": "独立scipy brentq重算逐年现金流IRR，与Decimal二分模型核对",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "model",
    "independence_note": "模型项核验只证明重算一致，不证明假设真实。"
  },
  {
    "id": 82,
    "label": "乐观 · 仅终值工具年化代理",
    "reported_value": 4.24,
    "unit": "%",
    "line_number": 238,
    "raw_text": "| 乐观 | +7% | 27.54 / 15.910 | 4% | 6 点 | 12.96 倍 | +4.24% | +8.50% |",
    "fetched_value": 4.240080075460395,
    "fetched_source": "terminal_value.py irr输出；独立幂运算核对",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "model",
    "independence_note": "模型项核验只证明重算一致，不证明假设真实。"
  },
  {
    "id": 87,
    "label": "11%（补充） · 期望完整现金 IRR",
    "reported_value": 3.47,
    "unit": "%",
    "line_number": 252,
    "raw_text": "| 11%（补充） | −1.07% | 否 | +3.47% | 否 | 合理区间内，三档分母 9 / 8 / 7 点 |",
    "fetched_value": 3.472771106659316,
    "fetched_source": "独立scipy brentq：r11%三情景现金IRR加权",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "model",
    "independence_note": "模型项核验只证明重算一致，不证明假设真实。"
  },
  {
    "id": 95,
    "label": "SEC",
    "reported_value": 2026.0,
    "unit": "",
    "line_number": 313,
    "raw_text": "2. [SEC：2026Q1 10-Q](https://www.sec.gov/Archives/edgar/data/80661/000008066126000177/pgr-20260331.htm)与[Q2 10-Q](https:",
    "fetched_value": 2026,
    "fetched_source": "SEC Q1/Q2文档所属年份；引用年份误识别，非财务数据",
    "fetched_value2": null,
    "fetched_source2": "",
    "audit_category": "extraction_noise",
    "independence_note": ""
  }
]
```

## 抽检工具原始输出

```text
======================================================================
报告数据抽检 — 准出/打回判决
报告：Progressive-research-20261125.md
======================================================================

  ✅ 通过 [ 4] 车辆险 Agency · 前十月 CR                  报告:        85.60 
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm: 85.60 (偏差 0.00%)  |  https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43: 85.60 (偏差 0.00%)
  ✅ 通过 [ 5] 车辆险 Agency · 10 月 CR                 报告:        90.00 
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm: 90.00 (偏差 0.00%)  |  https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43: 90.00 (偏差 0.00%)
  ✅ 通过 [15] Property · 10 月 CR                   报告:        60.80 
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm: 60.80 (偏差 0.00%)  |  https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43: 60.80 (偏差 0.00%)
  ✅ 通过 [14] Property · 前十月 CR                    报告:        74.70 
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm: 74.70 (偏差 0.00%)  |  https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43: 74.70 (偏差 0.00%)
  ✅ 通过 [12] Property · 2026 年前十月 NPE（US$bn）      报告:         2.62 
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm: 2.62 (偏差 0.00%)  |  https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43: 2.62 (偏差 0.00%)
  ✅ 通过 [18] Commercial Lines · 前十月 NPW 占比        报告:        13.20 %
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm；净签单保费原值计算: 13.20 (偏差 0.01%)  |  https://ml.globenewswire.com/Resource/Download/2fe3e4d9-789e-472c-ad1e-7da4d29d4f43: 13.20 (偏差 0.01%)
  ✅ 通过 [29] 收盘价 · 含义与限制                          报告:        11.00 
                                                    StockAnalysis报价日期2026-11-24；这是月份误识别，非股价: 11.00 (偏差 0.00%)
  ✅ 通过 [32] 复算普通股市值 · 本报告口径                      报告:       136.15 
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm；235.68×577.7M: 136.15 (偏差 0.00%)  |  https://companiesmarketcap.com/progressive/marketcap/: 136.15 (偏差 0.00%)
  ✅ 通过 [36] 拼接稀释 EPS / 对应 PE · 本报告口径             报告:        19.84 
                                                    https://www.sec.gov/Archives/edgar/data/80661/000008066126000384/pgr202610ex99earningsrelea.htm及FY2025月报；不同期平均股数EPS拼接近似: 19.84 (偏差 0.00%)
  ✅ 通过 [55] 基准：回归后温和增长 · 按 10% 折现的今日价值           报告:       193.45 
                                                    独立Decimal重算：三年EPS14×1.05^t、分配60%、退出PE14、r10%: 193.45 (偏差 0.00%)
  ✅ 通过 [70] 基准 · 前十年 EPS 增速                      报告:         5.00 %
                                                    模型基准前十年EPS增速假设；不冒充外部预测: 5.00 (偏差 0.00%)
  ✅ 通过 [76] 基准 · 含逐年分配的完整现金 IRR                  报告:         5.77 %
                                                    独立scipy brentq重算逐年现金流IRR，与Decimal二分模型核对: 5.77 (偏差 0.04%)
  ✅ 通过 [82] 乐观 · 仅终值工具年化代理                       报告:         4.24 %
                                                    terminal_value.py irr输出；独立幂运算核对: 4.24 (偏差 0.00%)
  ✅ 通过 [87] 11%（补充） · 期望完整现金 IRR                 报告:         3.47 %
                                                    独立scipy brentq：r11%三情景现金IRR加权: 3.47 (偏差 0.08%)
  ✅ 通过 [95] SEC                                  报告:      2026.00 
                                                    SEC Q1/Q2文档所属年份；引用年份误识别，非财务数据: 2026.00 (偏差 0.00%)

----------------------------------------------------------------------
  抽检总数: 15  |  通过: 15  |  警告: 0  |  不通过: 0

【准出】所有抽检数据通过，报告可发布。
======================================================================
{
  "verdict": "PASS",
  "pass_count": 15,
  "warn_count": 0,
  "fail_count": 0,
  "total": 15,
  "fail_items": [],
  "warn_items": []
}

```

## 关键数据和估值工具原始输出

工具中的通用ROE和IRR标签须按主报告解释：EPS/BVPS不等于会计ROE；irr/flip的k=0输出为仅终值年化代理，完整现金IRR另以逐年现金流计算。

```text
============================================================
市值验算 (Market Cap Verification)
============================================================
  股价 (Price):       235.68 USD
  总股本 (Shares):    577.70M
  计算市值:           136.15B USD
  报告市值:           136.15B USD
  偏差:               0.00%

  ✅ 验证通过, 偏差仅 0.00%
============================================================
交叉验证: FY2025 GAAP收入 (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 87,671.00 USD million

  ✅ SEC                 : 87,671.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis总收入(加回投资费用34): 87,671.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 87,671.00 USD million
============================================================
交叉验证: FY2025普通股归属净利润 (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 11,308.00 USD million

  ✅ SEC                 : 11,308.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis       : 11,308.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 11,308.00 USD million
============================================================
交叉验证: FY2025现金(排受限) (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 125.00 USD million

  ✅ SEC                 : 125.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis       : 125.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 125.00 USD million
============================================================
交叉验证: FY2025现金+短期投资 (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 10,130.00 USD million

  ✅ SEC                 : 10,130.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis现金125+Other Investments内短投10005: 10,130.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 10,130.00 USD million
============================================================
交叉验证: 2026Q3现金+短期投资 (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 2,266.00 USD million

  ✅ SEC                 : 2,266.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis现金141+Other Investments内短投2125: 2,266.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 2,266.00 USD million
============================================================
交叉验证: 最新实股与季度股数时点差 (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 578.53 million shares

  ✅ 20261031_SEC        : 577.70 million shares  (偏差 0.14%)
  ✅ 20261001_SEC及StockAnalysis: 579.36 million shares  (偏差 0.14%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 578.53 million shares
============================================================
估值指标验算 (Valuation Verification)
============================================================
  当前股价: 235.68

  PE (TTM):  235.68 / 19.84 = 11.88x
  盈利收益率: 8.42%
  PB:        235.68 / 61.90 = 3.81x
  ROE:       19.84 / 61.90 = 32.05%
  股息率:    0.40 / 235.68 = 0.17%

  ✅ 以上指标均使用精确十进制计算, 无浮点误差
注：工具EPS/BVPS=32.05%只是期末净资产比，非会计ROE；官方最新TTM ROE=34.4%。
============================================================
三情景估值模型 (Three-Scenario Valuation)
============================================================
  当前股价: 235.68 USD
  当前EPS:  14
  预测期:   3年

  情景                年增速     目标PE      目标EPS       目标股价      涨跌幅
  ------------ -------- -------- ---------- ---------- --------
  乐观 (Bull)         12%      16x      19.67     314.7   +33.5%
  中性 (Base)          5%      14x      16.21     226.9    -3.7%
  悲观 (Bear)         -3%      10x      12.78     127.8   -45.8%

  ✅ 所有计算使用精确十进制, 结果可审计复现

========================================================================
估值口径准出检查   币种=USD   r=10.00%   ROIC=18%   g=2.0%/3.0%/4.0%
========================================================================

【C1】币种一致性 — r 与 g 必须用同一个币种
     USD 口径基准：美国10年期国债 4.70% + 中国总ERP 5.18%（含1.01%国别溢价）
     r 合理区间 [9.0%, 11.5%]   g 上限 4.0%   Rf 4.70%
     → ✓ 通过

【C2】分母宽度 — r-g 至少 5 个百分点
     悲观  g= 2.0%  r-g= 8.0pct  PE=     11.1x  g+0.5pct → 11.5x (+3%)  
     基准  g= 3.0%  r-g= 7.0pct  PE=     11.9x  g+0.5pct → 12.4x (+4%)  
     乐观  g= 4.0%  r-g= 6.0pct  PE=     13.0x  g+0.5pct → 13.6x (+5%)  
     → ✓ 通过

【C3】离散风险归属 — 退市/VIE/地缘/监管必须归情景，不得进 r 或 β
     ✓ 赔付与价格竞争 → 情景
     ✓ 常规巨灾 → 情景
     ⚠ 灾难性巨灾及准备金崩塌 → 未建模
     ⚠ 自动驾驶责任重构 → 未建模
     ⚠ 数据隐私诉讼 → 未建模
     β = 1.0（默认值，无需理由）
     → ✓ 通过

========================================================================
⚠ C3: 「灾难性巨灾及准备金崩塌」未建模，必须写进报告的「限制」章节
⚠ C3: 「自动驾驶责任重构」未建模，必须写进报告的「限制」章节
⚠ C3: 「数据隐私诉讼」未建模，必须写进报告的「限制」章节

【准出】三条硬约束全部通过，可以把估值写进报告。
       但上述 3 条警告必须在报告里显式写出。


PE(终值) = (1 - g/ROIC) / (r - g)

  ROIC = 18.0%   g = 2.00%   r = 10.00%

  留存率 g/ROIC   = 0.0200 / 0.18 = 0.1111  (11.1%)
  分子 1 - 留存率 = 0.8889                    （即派息率 88.9%）
  分母 r - g      = 0.1000 - 0.0200 = 0.0800  (8.0pct)

  退出 PE = 0.8889 / 0.0800 = 11.1x


IRR = (2036市值 / 今日市值)^(1/10) - 1 + 股息率 - 稀释率

  2036 市值 = 6,608 x 11.1x = 73,426
  今日市值 = 136,152
  总倍数   = 0.5393
  几何年化 = -5.99%
  股息-稀释 = +0.00%

  IRR = -5.99%


PE(终值) = (1 - g/ROIC) / (r - g)

  ROIC = 18.0%   g = 3.00%   r = 10.00%

  留存率 g/ROIC   = 0.0300 / 0.18 = 0.1667  (16.7%)
  分子 1 - 留存率 = 0.8333                    （即派息率 83.3%）
  分母 r - g      = 0.1000 - 0.0300 = 0.0700  (7.0pct)

  退出 PE = 0.8333 / 0.0700 = 11.9x


IRR = (2036市值 / 今日市值)^(1/10) - 1 + 股息率 - 稀释率

  2036 市值 = 13,174 x 11.9x = 156,835
  今日市值 = 136,152
  总倍数   = 1.1519
  几何年化 = +1.42%
  股息-稀释 = +0.00%

  IRR = +1.42%


PE(终值) = (1 - g/ROIC) / (r - g)

  ROIC = 18.0%   g = 4.00%   r = 10.00%

  留存率 g/ROIC   = 0.0400 / 0.18 = 0.2222  (22.2%)
  分子 1 - 留存率 = 0.7778                    （即派息率 77.8%）
  分母 r - g      = 0.1000 - 0.0400 = 0.0600  (6.0pct)

  退出 PE = 0.7778 / 0.0600 = 13.0x


IRR = (2036市值 / 今日市值)^(1/10) - 1 + 股息率 - 稀释率

  2036 市值 = 15,910 x 13.0x = 206,240
  今日市值 = 136,152
  总倍数   = 1.5148
  几何年化 = +4.24%
  股息-稀释 = +0.00%

  IRR = +4.24%


Progressive  |  基准 r = 10.00%   Δr = ±2pp   币种 USD   g平移 +0.0%   Rf = 4.92%   持有期 10 年
币种合理区间：r ∈ [9.0%, 11.5%]（同 audit C1）；区间外档位仅供参考，不参与翻转判定。
判定规则：期望 IRR ≥ r → 通过仓位压力测试；否则未通过。
角色：十年模型 = 仓位压力测试，不是买入/持有/回避的唯一否决票。

档位               r       期望IRR        相对 r      压力测试
------------------------------------------------------
r−2pp        8.00%      +3.77%     -4.23pp  未通过（区间外，仅供参考）
基准 r        10.00%      +0.28%     -9.72pp  未通过
r+2pp       12.00%      -2.24%    -14.24pp  未通过（区间外，仅供参考）
------------------------------------------------------

【稳定】Δr±2pp 区间内压力测试始终未通过——相对折现率扰动更稳健。
        注意：两侧档位都在区间外，区间内只有基准一档参与判定；可用更小的 --delta 在区间内复核。
        未通过仍只约束仓位，不自动等于回避；须与其他五个维度并列决策。

提醒：禁止为迎合买入结论而把 r 调出币种合理区间；敏感性是为了一致性审计，不是为了「调低 r 去买」。


Progressive  |  基准 r = 10.00%   Δr = ±1pp   币种 USD   g平移 +0.0%   Rf = 4.92%   持有期 10 年
币种合理区间：r ∈ [9.0%, 11.5%]（同 audit C1）；区间外档位仅供参考，不参与翻转判定。
判定规则：期望 IRR ≥ r → 通过仓位压力测试；否则未通过。
角色：十年模型 = 仓位压力测试，不是买入/持有/回避的唯一否决票。

档位               r       期望IRR        相对 r      压力测试
------------------------------------------------------
r−1pp        9.00%      +1.86%     -7.14pp  未通过
基准 r        10.00%      +0.28%     -9.72pp  未通过
r+1pp       11.00%      -1.07%    -12.07pp  未通过
------------------------------------------------------

【稳定】Δr±1pp 区间内压力测试始终未通过——相对折现率扰动更稳健。
        未通过仍只约束仓位，不自动等于回避；须与其他五个维度并列决策。

提醒：禁止为迎合买入结论而把 r 调出币种合理区间；敏感性是为了一致性审计，不是为了「调低 r 去买」。


```

## 年度现金及股数双源补充原始输出

```text
COMMAND: python3 tools/financial_rigor.py cross-validate --field FY2025 Revenue as reported --values {"SEC":87671,"StockAnalysis as reported":87671,"Macrotrends":87671} --unit USD million
============================================================
交叉验证: FY2025 Revenue as reported (Cross-Validation)
============================================================
  数据来源数: 3
  参考中位数: 87,671.00 USD million

  ✅ SEC                 : 87,671.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis as reported: 87,671.00 USD million  (偏差 0.00%)
  ✅ Macrotrends         : 87,671.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 87,671.00 USD million

COMMAND: python3 tools/financial_rigor.py cross-validate --field FY2025 consolidated NI --values {"SEC":11308,"StockAnalysis consolidated":11308,"Macrotrends common":11308} --unit USD million
============================================================
交叉验证: FY2025 consolidated NI (Cross-Validation)
============================================================
  数据来源数: 3
  参考中位数: 11,308.00 USD million

  ✅ SEC                 : 11,308.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis consolidated: 11,308.00 USD million  (偏差 0.00%)
  ✅ Macrotrends common  : 11,308.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 11,308.00 USD million

COMMAND: python3 tools/financial_rigor.py cross-validate --field FY2025 cash excluding restricted --values {"SEC":125,"StockAnalysis":125} --unit USD million
============================================================
交叉验证: FY2025 cash excluding restricted (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 125.00 USD million

  ✅ SEC                 : 125.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis       : 125.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 125.00 USD million

COMMAND: python3 tools/financial_rigor.py cross-validate --field FY2025 short term investments --values {"SEC":10005,"StockAnalysis Other Investments":10005} --unit USD million
============================================================
交叉验证: FY2025 short term investments (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 10,005.00 USD million

  ✅ SEC                 : 10,005.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis Other Investments: 10,005.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 10,005.00 USD million

COMMAND: python3 tools/financial_rigor.py cross-validate --field Q32026 cash excluding restricted --values {"SEC":141,"StockAnalysis":141} --unit USD million
============================================================
交叉验证: Q32026 cash excluding restricted (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 141.00 USD million

  ✅ SEC                 : 141.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis       : 141.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 141.00 USD million

COMMAND: python3 tools/financial_rigor.py cross-validate --field Q32026 short term investments --values {"SEC":2125,"StockAnalysis Other Investments":2125} --unit USD million
============================================================
交叉验证: Q32026 short term investments (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 2,125.00 USD million

  ✅ SEC                 : 2,125.00 USD million  (偏差 0.00%)
  ✅ StockAnalysis Other Investments: 2,125.00 USD million  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 2,125.00 USD million

COMMAND: python3 tools/financial_rigor.py cross-validate --field Shares outstanding October 1 2026 --values {"SEC":579.362175,"StockAnalysis filing date":579.36} --unit million shares
============================================================
交叉验证: Shares outstanding October 1 2026 (Cross-Validation)
============================================================
  数据来源数: 2
  参考中位数: 579.36 million shares

  ✅ SEC                 : 579.36 million shares  (偏差 0.00%)
  ✅ StockAnalysis filing date: 579.36 million shares  (偏差 0.00%)

  ✅ 所有来源偏差 ≤ 2.0%, 数据一致

  共识值 (加权中位数): 579.36 million shares

COMMAND: python3 tools/financial_rigor.py calc --expr 70778-52343
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 70778-52343
  结果:   18,435.00
  精确值: 18435

COMMAND: python3 tools/financial_rigor.py calc --expr 10881-8224
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 10881-8224
  结果:   2,657.00
  精确值: 2657

COMMAND: python3 tools/financial_rigor.py calc --expr 100-(8854-6729)/(70778-52343)*100
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 100-(8854-6729)/(70778-52343)*100
  结果:   88.47
  精确值: 88.47301328993763

COMMAND: python3 tools/financial_rigor.py calc --expr 100-(1416-1000)/(10881-8224)*100
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 100-(1416-1000)/(10881-8224)*100
  结果:   84.34
  精确值: 84.34324426044411

COMMAND: python3 tools/financial_rigor.py calc --expr 19.23+16.26-15.65
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 19.23+16.26-15.65
  结果:   19.84
  精确值: 19.840000000000003

COMMAND: python3 tools/financial_rigor.py calc --expr 11308+9499-9203
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 11308+9499-9203
  结果:   11,604.00
  精确值: 11604

COMMAND: python3 tools/financial_rigor.py calc --expr 81661+71576-67646
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 81661+71576-67646
  结果:   85,591.00
  精确值: 85591

COMMAND: python3 tools/financial_rigor.py calc --expr 125+10005
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 125+10005
  结果:   10,130.00
  精确值: 10130

COMMAND: python3 tools/financial_rigor.py calc --expr 141+2125
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 141+2125
  结果:   2,266.00
  精确值: 2266

COMMAND: python3 tools/financial_rigor.py calc --expr 125+10005-6897
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 125+10005-6897
  结果:   3,233.00
  精确值: 3233

COMMAND: python3 tools/financial_rigor.py calc --expr 141+2125-8389
============================================================
精确计算 (Exact Calculator)
============================================================
  表达式: 141+2125-8389
  结果:   -6,123.00
  精确值: -6123


```

## 定稿后估值口径复检

```text

========================================================================
估值口径准出检查   币种=USD   r=10.00%   ROIC=18%   g=2.0%/3.0%/4.0%
========================================================================

【C1】币种一致性 — r 与 g 必须用同一个币种
     USD 口径基准：美国10年期国债 4.70% + 中国总ERP 5.18%（含1.01%国别溢价）
     r 合理区间 [9.0%, 11.5%]   g 上限 4.0%   Rf 4.70%
     → ✓ 通过

【C2】分母宽度 — r-g 至少 5 个百分点
     悲观  g= 2.0%  r-g= 8.0pct  PE=     11.1x  g+0.5pct → 11.5x (+3%)  
     基准  g= 3.0%  r-g= 7.0pct  PE=     11.9x  g+0.5pct → 12.4x (+4%)  
     乐观  g= 4.0%  r-g= 6.0pct  PE=     13.0x  g+0.5pct → 13.6x (+5%)  
     → ✓ 通过

【C3】离散风险归属 — 退市/VIE/地缘/监管必须归情景，不得进 r 或 β
     ✓ 赔付与价格竞争 → 情景
     ✓ 常规巨灾 → 情景
     ⚠ 灾难性巨灾及准备金崩塌 → 未建模
     ⚠ 自动驾驶责任重构 → 未建模
     ⚠ 数据隐私诉讼 → 未建模
     β = 1.0（默认值，无需理由）
     → ✓ 通过

========================================================================
⚠ C3: 「灾难性巨灾及准备金崩塌」未建模，必须写进报告的「限制」章节
⚠ C3: 「自动驾驶责任重构」未建模，必须写进报告的「限制」章节
⚠ C3: 「数据隐私诉讼」未建模，必须写进报告的「限制」章节

【准出】三条硬约束全部通过，可以把估值写进报告。
       但上述 3 条警告必须在报告里显式写出。


```

## 触发与台账收尾

- 沿用 target ID `Progressive`，保留历史报告和已完成事件，新研究为首个链接；研究带150—170美元、警戒220美元，与正文一致。
- 旧10月14日和11月3日复检窗口已完成；12月16日为官方盘前月报日，12月31日及次年3月31日明确为人工研究检查/兜底，非确认预约财报日。
- Progressive只在重点看板待办汇总，不在重点主表，因此在非重点台账新增 `20261125-PGR`，旧9月事件接续关闭、结果无法判定，未将触价当投资命中；全部计数从当时主表重算。
- `trigger_scanner.py --check` 和 `daily_monitor.py --check` 均通过。
- 临时状态与临时报告目录的单标的在线日监控返回OK、items=1、notifications=0；正式monitoring-state和每日报告未由本任务写入。
