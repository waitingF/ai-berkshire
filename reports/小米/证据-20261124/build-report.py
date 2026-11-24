"""Render original research chart and insert sourced financial tables."""
from decimal import Decimal as D
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
report = HERE.parent / "小米-research-20261124.md"
text = report.read_text()
history = [
    [2021,"328309.145","19339.321","22039.474","17.75","7.93","9785.288","2615.975","23511.579"],
    [2022,"280044.016","2474.030","8518.007","16.99","1.01","-4389.730","-10189.300","27607.261"],
    [2023,"270970.141","17475.173","19272.754","21.21","7.38","41300.495","35031.595","33631.313"],
    [2024,"365906.350","23658.126","27234.531","20.92","6.70","39295.499","31998.192","33661.442"],
    [2025,"457286.687","41643.389","39166.303","22.26","10.48","34142.377","21373.222","26914.377"],
]
table = "金额为人民币亿元；利润率为百分比。\n\n| 年度 | 收入 | 归母净利 | 调整净利 | 毛利率 | 法定经营利润率 | CFO | 狭义FCF | 现金等价物 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
for row in history:
    cells = [str(row[0])]
    for i, value in enumerate(row[1:], 1):
        cells.append(f"{D(value):.2f}%" if i in (4,5) else f"{D(value)/100:,.2f}")
    table += "| " + " | ".join(cells) + " |\n"
table += "\n狭义FCF=CFO−投资活动列现金购买固定、土地及无形资产，未扣延期无形对价及租赁。法定经营利润包含投资损益，不能视为纯主营利润率。2025收入、归母采用较后发布的年报精确数，与3月业绩公告有微小尾差。\n\n来源：[2025年报五年摘要](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0428/2026042800526.pdf)、[2023年报原件存档](https://cdn.financialreports.eu/financialreports/media/filings/50185/2024/RNS/50185_rns_2024-04-25_5b8517e1-92ca-46a1-9bf9-8bbc0bcd5291.pdf)、[2021年报](https://cdn.cnbj1.fds.api.mi-img.com/company/announcement/en-us/2.%202021%20ANNUAL%20REPORT.pdf)、[StockAnalysis损益表](https://stockanalysis.com/quote/hkg/1810/financials/income-statement/)、[现金流](https://stockanalysis.com/quote/hkg/1810/financials/cash-flow-statement/)。"
text = text.replace("<!-- FINANCIAL_HISTORY -->", table)
quarter = "每格为“收入亿元 / 同比 / 毛利率”，四舍五入至一位小数；分部明细以公司披露为主，最新Q3完整独立分部来源尚缺。\n\n| 业务 | 2025Q4 | 2026Q1 | 2026Q2 | 2026Q3 |\n|---|---:|---:|---:|---:|\n"
rows = [
    ["手机","443.4 / -13.6% / 8.3%","442.7 / -12.5% / 10.1%","421.2 / -7.5% / 8.5%","455.8 / -0.8% / 9.2%"],
    ["IoT与生活消费品","246.0 / -20.3% / 20.1%","246.8 / -23.7% / 25.2%","312.8 / -19.2% / 20.1%","271.5 / -1.4% / 21.7%"],
    ["互联网","98.9 / +5.9% / 76.8%","94.7 / +4.3% / 76.1%","90.4 / -0.6% / 76.8%","94.5 / +0.7% / 73.8%"],
    ["手机×AIoT其他","8.8 / +6.4% / -34.4%","8.5 / +24.5% / -9.6%","15.9 / +16.3% / 0.2%","11.7 / -2.9% / -1.3%"],
    ["汽车/AI等","372.2 / +123.4% / 22.7%","198.6 / +6.9% / 20.1%","249.0 / +17.1% / 19.2%","238.8 / -17.7% / 19.2%"],
    ["集团","1169.2 / +7.3% / 20.8%","991.4 / -10.9% / 22.0%","1089.2 / -6.1% / 19.8%","1072.4 / -5.2% / 20.2%"],
]
for row in rows:
    quarter += "| " + " | ".join(row) + " |\n"
quarter += "\n| 集团指标（亿元） | 2025Q4 | 2026Q1 | 2026Q2 | 2026Q3 |\n|---|---:|---:|---:|---:|\n| 调整净利 | 63.49 | 60.72 | 62.19 | 48.84 |\n| CFO | 6.14 | -17.92 | 38.42 | -230.34 |\n| 汽车/AI分部经营结果 | +11 | -31 | -26 | -34 |\n\n来源：[2025Q4公告](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0324/2026032400608.pdf)、[2026H1公告](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0818/2026081801014.pdf)、[2026Q3公告](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1124/2026112400538.pdf)；计算和单源限制见[财务底稿](证据-20261124/financial-sources.md)。"
text = text.replace("<!-- QUARTER_HISTORY -->", quarter)
peers = "| 比较对象 | 数据商TTM PE / PS | 为什么不能套倍数 |\n|---|---|---|\n| 小米（11/24收盘） | 约24.61倍 / 1.35倍 | 数据商摊薄口径；本文实际股数PE为23.57倍 |\n| 苹果（11/23完整收盘） | 38.87倍 / 10.59倍 | 品牌定价、服务毛利及资本回报结构不同，不能直接给予小米苹果倍数 |\n| 比亚迪（11/24收盘） | 14.86倍 / PS不作精确锚 | AAStocks同日PE15.13倍；EPS口径存在差别，多股类PS未完成归集核对 |\n\n上述仅为数据商报告利润倍数观察，不与小米扣SBC经济利润PE直接相减；苹果11/24交易日尚未结束，未混入盘中值。[苹果统计](https://stockanalysis.com/stocks/aapl/statistics/)、[苹果FY2026财表](https://www.apple.com/newsroom/pdfs/fy2026q4/FY26_Q4_Consolidated_Financial_Statements.pdf)、[比亚迪统计](https://stockanalysis.com/quote/hkg/1211/statistics/)、[比亚迪Q3财报](https://www.hkexnews.hk/listedco/listconews/sehk/2026/1029/2026102900816.pdf)、[口径差异底稿](证据-20261124/market-governance.md)。"
text = text.replace("<!-- PEER_VALUATION -->", peers)
report.write_text(text)

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
fig, axes = plt.subplots(1,3,figsize=(15,4.6),layout="constrained")
fig.patch.set_facecolor("#faf9f6")
for ax in axes:
    ax.set_facecolor("#faf9f6")
years = [str(x[0]) for x in history]
axes[0].barh(["Phone","IoT / lifestyle","Internet","Other","Auto / AI"],[186.440,123.200,37.440,4.137,106.070],color=["#435e80","#638b94","#c58a43","#b0ada7","#8d6c8f"])
axes[0].invert_yaxis()
axes[0].set_title("FY2025 revenue mix",loc="left",weight="bold")
axes[0].set_xlabel("CNY bn")
axes[1].bar(years,[float(D(x[1])/1000) for x in history],color="#435e80",alpha=.85)
axes[1].set_title("Revenue and adjusted profit",loc="left",weight="bold")
axes[1].set_ylabel("Revenue, CNY bn")
twin=axes[1].twinx()
twin.plot(years,[float(D(x[3])/1000) for x in history],color="#be703a",marker="o",linewidth=2)
twin.set_ylabel("Adjusted profit, CNY bn",color="#a95b26")
twin.spines["top"].set_visible(False)
axes[2].plot(years,[float(D(x[4])) for x in history],marker="o",label="Gross margin",color="#435e80")
axes[2].plot(years,[float(D(x[5])) for x in history],marker="o",label="Statutory operating margin",color="#be703a")
axes[2].set_ylim(0,26)
axes[2].set_title("Margins: investment gains affect EBIT",loc="left",weight="bold")
axes[2].set_ylabel("%")
axes[2].legend(frameon=False,loc="lower left",fontsize=8)
fig.suptitle("XIAOMI  |  Operating map  |  Data cutoff 24 Nov 2026",x=.015,ha="left",fontsize=14,weight="bold")
fig.savefig(HERE / "financial-map.png",dpi=160,facecolor=fig.get_facecolor())
print("Inserted financial and peer tables; wrote financial-map.png")
