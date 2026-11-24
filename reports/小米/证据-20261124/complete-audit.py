"""Fill the fixed sample from independently read sources and model traces.

Single-source facts and researcher assumptions are explicitly distinguished;
an arithmetic PASS is never represented as a second external source.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
report = HERE.parent / "小米-research-20261124.md"
raw = (HERE / "audit-extract.log").read_text()
sample = json.loads(raw[raw.index("\n[\n") + 1:])
(HERE / "audit-original.json").write_text(json.dumps(sample,ensure_ascii=False,indent=2)+"\n")
q3 = "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1124/2026112400538.pdf"
h1 = "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0818/2026081801014.pdf"
q4 = "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0324/2026032400608.pdf"
sa = "https://stockanalysis.com/quote/hkg/1810/financials/"
star = "https://hk.stockstar.com/IG2026112400029708.shtml"
it = "https://www.ithome.com/1/031/709.htm"
ms = "https://www.marketscreener.com/news/xiaomi-corporation-reports-earnings-results-for-the-third-quarter-and-nine-months-ended-september-30-ce7851dbd980f523"
model = json.loads((HERE / "model-output.json").read_text())
records = {
    152: (6821.298155605, "HKEX股本+双行情价复算；market-governance.md",6815.5,"StockAnalysis统计展示市值（舍入股本）", "derived_fact"),
    1: (1072.39525,q3,1072.3953,ms,"fact_two_sources"),
    7: (38.75581,q3,38.7558,ms,"fact_two_sources"),
    15: (-230.344,q3,-230.34,it,"fact_two_sources"),
    19: (1969,q3,1969,star,"fact_two_sources"),
    20: (455.786,q3,455.79,star,"fact_two_sources"),
    36: (245.966,q4,246,"https://www.capitalfutures.com.tw/zh-tw/financial/breakingnewsarticle?contentid=c26032400832","fact_two_sources"),
    37: (246.812,h1,None,"未取得独立分部复核；不得填造", "fact_single_source"),
    42: (90.437,h1,None,"未取得独立分部复核；不得填造", "fact_single_source"),
    45: (8.544,h1,None,"未取得独立分部复核；不得填造", "fact_single_source"),
    64: (11,q4,None,"公司非IFRS分部管理口径，独立复核缺口", "fact_single_source"),
    65: (-31,h1,None,"公司非IFRS分部管理口径，独立复核缺口", "fact_single_source"),
    66: (-26,h1,None,"公司非IFRS分部管理口径，独立复核缺口", "fact_single_source"),
    91: (22,"model.py:three_year基准PE输入；研究假设",None,"不适用：假设不冒充外部事实", "model_assumption"),
    113: (float(model["ten_year"][0]["complete_cash_irr_pct"]),"model-output.json:ten_year[0]；Decimal逐年FCFE及NPV根",None,"数学复算，不是第二外部来源", "model_derived"),
    109: (7.5,"(0.08-0.005)*100；固定模型输入",None,"数学恒等式", "model_derived"),
    120: (float(model["ten_year"][1]["complete_cash_irr_pct"]),"model-output.json:ten_year[1]；Decimal逐年FCFE及NPV根",None,"数学复算，不是第二外部来源", "model_derived"),
    116: (6.5,"(0.08-0.015)*100；固定模型输入",None,"数学恒等式", "model_derived"),
    126: (float(model["ten_year"][2]["terminal_only_irr_at_8pct"]),"model-output.json:ten_year[2]；完整精度输入",9.56,"terminal_value.py irr原输出；仅独立数学勾稽", "model_derived"),
    147: (230.344,q3,230.34,it,"fact_two_sources"),
}
false_ids = {12:"把Q2中的2误抓成财务值",75:"把截至9月中的9误抓成财务值",143:"把H1中的1误抓成财务值"}
results=[]
for point in sample:
    if point["id"] in false_ids:
        continue
    value,source,value2,source2,kind = records[point["id"]]
    point.update(fetched_value=value,fetched_source=source,fetched_value2=value2,fetched_source2=source2,verification_kind=kind)
    results.append(point)

def add(label,reported,value,source,value2=None,source2="",kind="fact_two_sources",note=""):
    results.append({"id":200+len(results),"label":label,"reported_value":reported,"unit":"见主报告",
        "fetched_value":value,"fetched_source":source,"fetched_value2":value2,"fetched_source2":source2,
        "verification_kind":kind,"note":note})

# Replace the three semantic extraction errors with the actual financial facts
# in the affected row / supporting the affected recommendation.
add("纠正误抓Q2标签：手机2026Q3毛利率",9.2,9.2,q3,9.2,star,note="对应原ID12，直接核正确财务字段")
add("纠正误抓月份：滚动营业收入亿元",4322.19,float(model["ttm_revenue_bn"])*10,"官方年报与Q3桥接；model-output.json",4322.19,sa,note="对应原ID75")
add("持仓复核事实：汽车/AI Q3经营亏损亿元",34,34,q3,None,"未取得独立同口径分部利润，保留单源限制",kind="fact_single_source",note="替代原ID143中的H1标签；来源不是虚构的财务值1")

# Supplement table shapes omitted by extractor (year-only labels and multiple
# values in one cell), rather than pretending the random sample covered them.
annual="https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0428/2026042800526.pdf"
add("补充2022收入亿元",2800.44,2800.44016,annual,2800.44,sa)
add("补充2025归母净利亿元",416.43,416.43389,annual,416.43,sa)
add("补充2025狭义FCF亿元",213.73,213.73222,"公司现金流CFO减现金购置；financial-sources.md",213.73,"https://stockanalysis.com/quote/hkg/1810/financials/cash-flow-statement/")
add("补充TTM调整减税前SBC亿元",188.55,188.55216,"公司三期调整桥；financial-sources.md",None,"SBC三期完整独立来源未得",kind="fact_single_source")
add("补充每股正常化经济盈利港元",.9140,float(model["eps_hkd_model"]),"model.py:200亿元假设/股本/汇率",None,"研究假设的算术，不是已报告每股盈利",kind="model_derived")

for item in results:
    rv,fv=item['reported_value'],item['fetched_value']
    assert abs(rv-fv)/abs(rv) <= .01, item
    if item.get('fetched_value2') is not None:
        assert abs(rv-item['fetched_value2'])/abs(rv) <= .01, item
(HERE / "audit-results.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
summary={"seed":20261124,"extracted_points":153,"random_sample":23,"semantic_false_positives":false_ids,
    "valid_random_points":20,"corrected_replacements":3,"additional_checks":5,"verdict_rows":len(results),
    "single_source_rows":[x["label"] for x in results if x["verification_kind"]=="fact_single_source"],
    "scope":"PASS verifies fetched values and model arithmetic only. Single-source facts are not independent dual-source clearance."}
(HERE / "audit-coverage.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
proc=subprocess.run([sys.executable,"tools/report_audit.py","verdict","--results",json.dumps(results,ensure_ascii=False),"--report",str(report)],cwd=ROOT,text=True,capture_output=True)
(HERE / "audit-verdict.log").write_text(re.sub(r"\x1b\[[0-9;]*m","",proc.stdout+proc.stderr))
print(proc.stdout)
raise SystemExit(proc.returncode)
