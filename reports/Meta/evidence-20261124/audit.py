"""Audit the dated report against read source snapshots and independent formulas.

External values are explicit observed snapshots, not copies of reported_value.
Forecasts and editorial thresholds are checked only for internal consistency.
"""
from decimal import Decimal as D, getcontext
from pathlib import Path
from collections import Counter
import json
import math
import subprocess
import sys

getcontext().prec = 38
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT = HERE.parent / 'Meta-research-20261124.md'
run = subprocess.run([sys.executable, str(ROOT/'tools/report_audit.py'), 'extract',
                      '--report', str(REPORT), '--seed', '20261124'],
                     text=True, capture_output=True, check=True)
(HERE/'audit-extract.txt').write_text(run.stdout)
items = json.loads(run.stdout[run.stdout.index('[\n  {'):])
annual = 'https://stockanalysis.com/stocks/meta/financials/'
bs = 'https://stockanalysis.com/stocks/meta/financials/balance-sheet/'
cf = 'https://stockanalysis.com/stocks/meta/financials/cash-flow-statement/'
k2022 = 'https://investor.atmeta.com/investor-news/press-release-details/2023/Meta-Reports-Fourth-Quarter-and-Full-Year-2022-Results/default.aspx'
k2025 = 'https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm'
q1 = 'https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-First-Quarter-2026-Results/default.aspx'
q2 = 'https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Second-Quarter-2026-Results/default.aspx'
q3 = 'https://www.sec.gov/Archives/edgar/data/1326801/000162828026066773/meta-20260930.htm'
q4 = 'https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Fourth-Quarter-and-Full-Year-2025-Results/default.aspx'
ap2 = 'https://apnews.com/article/bcbc62dde6d2cac724e3b3385fcabeab'
macro_oi = 'https://www.macrotrends.net/stocks/charts/META/meta-platforms/operating-income'
shares = D(2214472367) + D(341768886)
future = shares + D(46000000) + D(20000000)
mcap = D('597.60') * shares / D(1000000)
normalized_profit = (D(79380)+D(9890)+D(2400)+D(1180)+D(609)-D(1126))*D('.83')
model_eps = normalized_profit*D(1000000)/future
source_calc = 'Independent Decimal formula in evidence-20261124/audit.py; observed SEC/IR inputs and declared assumptions'

# Tuple: value1, source1, value2, source2, verification type.
checks = {
 '收入 · 2021': (117929,k2022,117929,annual,'external_fact'),
 'GAAP净利润 · 2022': (23200,k2022,23200,annual,'external_fact'),
 'GAAP营业利润 · 2022': (28944,k2022,28944,macro_oi+' (search-index snapshot; direct page blocked)','external_fact'),
 'GAAP营业利润 · 2025': (83276,k2025,83276,annual,'external_fact'),
 '毛利率 · 2025': ((1-D(36175)/D(200966))*100,k2025+'; recomputed from revenue/COGS',82.00,annual,'derived_from_external_facts'),
 '毛利率 · 2024': ((1-D(30161)/D(164501))*100,k2025+'; recomputed from revenue/COGS',81.66,annual,'derived_from_external_facts'),
 '现金及可交易证券 · 2021': (47998,k2022,47998,bs,'external_fact'),
 '现金及可交易证券 · 2022': (40738,k2022,40738,bs,'external_fact'),
 '收入 · 2026Q1': (56311,q1,56311,annual+'?p=quarterly','external_fact'),
 '广告收入 · 2025Q4': (58137,q4,58137,annual+'?p=quarterly','external_fact'),
 'FoA营业利润 · 2026Q3': (17117,q3,17120,'https://stockanalysis.com/stocks/meta/financials/metrics/?p=quarterly (17.12B displayed precision)','external_fact'),
 'RL营业亏损 · 2025Q4': (-6021,q4,-6020,'https://www.proactiveinvestors.com/companies/news/1086427/meta-beats-q4-revenue-and-eps-estimates-raises-2026-capex-guidance-1086427.html (search snapshot: loss 6.02B)','external_fact'),
 'GAAP净利润 · 2026Q2': (15848,q2,15850,ap2+' (15.85B displayed precision)','external_fact'),
 '公司定义FCF · 2026Q2': (784,q2,784,ap2,'external_fact'),
 '11月4日远期超额配售行使 · 已核事实': (40,'https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Announces-Pricing-of-Offering-of-Depositary-Shares-Representing-Series-A-Mandatory-Convertible-Preferred-Stock-and-Offering-of-Class-A-Common-Stock-in-Connection-with-Forward-Sale-Agreements/default.aspx (original 40m, not updated total 46m)',None,'','external_fact_primary_only'),
 '11月23日C股诉讼披露 · 对股东的意义': (D(60000000000)/D(100000000),'https://www.sec.gov/Archives/edgar/data/1326801/000119312526431036/d116268dfwp.htm',600,'https://www.investing.com/news/stock-market-news/meta-pauses-class-c-share-issuance-amid-shareholder-lawsuit-5046609','external_fact'),
 '平滑盈利PE · 验算值': (mcap/normalized_profit,source_calc,None,'','model_recalculation'),
 '公司口径FCF收益率 · 验算值': (D(25126)/mcap*100,source_calc,None,'','model_recalculation'),
 '基准 · 第三年EPS': (model_eps*D('1.12')**3,source_calc,None,'','model_recalculation'),
 '乐观 · 第三年股价': (model_eps*D('1.20')**3*26,source_calc,None,'','model_recalculation'),
 '乐观 · 三年PE': (26,'model.py: author-declared 3-year bull PE assumption, not externally verifiable',None,'','author_assumption'),
 'Alphabet · 第三方远期PE': (20.20,'https://stockanalysis.com/stocks/googl/statistics/ (2026-11-24 observed snapshot)',None,'','third_party_estimate_single_source'),
 'Pinterest · 第三方远期PE': (8.86,'https://stockanalysis.com/stocks/pins/statistics/ (2026-11-24 observed snapshot)',None,'','third_party_estimate_single_source'),
 '悲观 · r-g': ((D('.10')-D('.01'))*100,source_calc,None,'','model_recalculation'),
 '基准 · 留存率g／ROIC': (D('.03')/D('.18')*100,source_calc,None,'','model_recalculation'),
 '乐观 · 终值代理年化': ((math.pow(float(D(300000)*shares/future*((1-D('.04')/D('.18'))/(D('.10')-D('.04')))/mcap),0.1)-1+2.1/597.6)*100,source_calc+'; independent float-root calculation',None,'','model_recalculation'),
 '价格上行复核 · 建议': (750,'Declared editorial risk-review threshold in dated report; no claim of external validation',None,'','author_assumption'),
 'TTM FCF · 处理结果': (D(754)+D(2769),q4+' and '+q3+'; finance principal roll-forward',D(28649)-D(25126),cf+'; company-FCF bridge','derived_from_external_facts'),
 'TTM FCF · 独立来源': (D(133087)-D(104438),q4+' and '+q3+'; CFO minus cash PPE',28649,cf,'derived_from_external_facts'),
}
for item in items:
    label = item['label']
    if label == 'RL长期投资 · 可观察结果':
        item['verification_type'] = 'parser_artifact_excluded'
        item['verification_note'] = '2027 is a calendar year inside prose, not a financial amount; excluded, not claimed as passed.'
        continue
    if label not in checks:
        raise ValueError('Unmapped sample: '+label)
    v1,s1,v2,s2,kind = checks[label]
    item.update(fetched_value=float(v1), fetched_source=s1,
                fetched_value2=None if v2 is None else float(v2), fetched_source2=s2,
                verification_type=kind)
    if kind == 'external_fact_primary_only':
        item['verification_note'] = 'Only original 40m extracted by parser. Latest 46m was separately confirmed in 2026-11-05 SEC 8-K; independent verification of transaction share counts remains a source gap.'
(HERE/'audit-results.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
cmd = [sys.executable,str(ROOT/'tools/report_audit.py'),'verdict','--results',json.dumps(items,ensure_ascii=False),'--report',REPORT.name,'--output-json']
verdict = subprocess.run(cmd,text=True,capture_output=True,check=True)
(HERE/'audit-verdict.txt').write_text(verdict.stdout)
summary = {'sample_seed':20261124,'sampled':len(items),'types':dict(Counter(x['verification_type'] for x in items)),
           'note':'Numeric verdict does not upgrade author assumptions, single-source estimates, or same-issuer transaction facts to independent source verification.'}
(HERE/'audit-coverage.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(verdict.stdout)
print(json.dumps(summary,ensure_ascii=False))
