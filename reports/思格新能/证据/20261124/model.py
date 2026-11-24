"""Selected public facts and reproducible arithmetic; no downloaded source text."""
from contextlib import redirect_stdout
from decimal import Decimal as D, getcontext
from pathlib import Path
import json
import subprocess
import sys

getcontext().prec = 40
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from tools import financial_rigor as f
from tools import terminal_value as t

sources = {
    "prospectus": "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0408/2026040800018_c.pdf",
    "interim": "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0911/2026091101520_c.pdf",
    "etnet_final": "https://www.etnet.com.hk/www/eng/stocks/realtime/quote_ci_pl.php?code=6656&quarter=final",
    "etnet_interim": "https://www.etnet.com.hk/www/eng/stocks/realtime/quote_ci_pl.php?code=6656&quarter=interim",
    "etnet_bs": "https://www.etnet.com.hk/www/eng/stocks/realtime/quote_ci_bs.php?code=6656&quarter=interim",
    "etnet_cf": "https://www.etnet.com.hk/www/eng/stocks/realtime/quote_ci_cashflow.php?code=6656&quarter=final",
    "etnet_business": "https://www.etnet.com.hk/www/tc/stocks/realtime/quote_ci_detail.php?code=6656&eyear=0&pyear=0",
    "stockanalysis_cf": "https://stockanalysis.com/quote/hkg/6656/financials/cash-flow-statement/",
    "weidn": "https://market.weidn.com/cn/company/hk/06656/",
    "capitalization": "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1117/2026111701457.pdf",
    "buyback": "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1124/2026112400965.pdf",
    "quote": "https://qt.gtimg.cn/q=hk06656",
    "yahoo": "https://query1.finance.yahoo.com/v8/finance/chart/6656.HK?range=5d&interval=1d",
    "fx": "https://query1.finance.yahoo.com/v8/finance/chart/HKDCNY=X?range=5d&interval=1d",
    "xe": "https://www.xe.com/zh-cn/currencyconverter/convert/?Amount=1&From=HKD&To=CNY",
}
# CNY million unless explicitly specified. No five-year history is available.
facts = {
    "2023": dict(revenue="58.302", gross="18.249", profit="-373.452", cfo="-369.714", equipment="92.157", intangible="0.759", land="0", cash="233.306", rd="193.005", pbt="-373.286", finance="4.755"),
    "2024": dict(revenue="1329.838", gross="623.630", profit="83.845", cfo="-95.805", equipment="42.865", intangible="0.674", land="0", cash="424.294", rd="280.253", pbt="55.647", finance="10.820"),
    "2025": dict(revenue="9000.512", gross="4504.853", profit="2918.832", cfo="-199.990", equipment="352.711", intangible="0.396", land="18.266", cash="1109.293", rd="494.028", pbt="3296.226", finance="23.775"),
    "2025H1": dict(revenue="2733.786", gross="1419.377", profit="806.605", cfo="450.762", equipment="74.167", intangible="0.396", land="18.267", rd="228.024", pbt="870.907", finance="7.349"),
    "2026H1": dict(revenue="9873.625", gross="3998.996", profit="2427.716", cfo="1974.001", equipment="257.557", intangible="5.790", land="61.103", cash="8236.289", bank_cash="8247.419", debt="3119.835", lease="35.777", equity="9936.487", rd="371.339", pbt="3034.359", finance="30.375"),
}
price, shares, fx = D("72.25"), D("746498790"), D("0.8496")
out = {"cutoff": "2026-11-24", "price_hkd": price, "shares_conservative_including_treasury": shares, "cny_per_hkd": fx, "facts": facts}
for row in facts.values():
    row.update({k: str(v) for k, v in {"capex": sum(D(row[x]) for x in ("equipment", "intangible", "land")), "gross_margin": D(row["gross"])/D(row["revenue"])*100, "operating_proxy_margin": (D(row["pbt"])+D(row["finance"]))/D(row["revenue"])*100}.items()})
    row["fcf"] = str(D(row["cfo"])-D(row["capex"]))
ttm = {k: D(facts["2025"][k])-D(facts["2025H1"][k])+D(facts["2026H1"][k]) for k in ("revenue", "profit", "cfo", "capex", "fcf")}
mcap_hkd = price*shares/D(1000000)
mcap_cny = mcap_hkd*fx
net_cash = D("8236.289")-D("3119.835")-D("35.777")
eps = ttm["profit"]*D(1000000)/shares/fx
out.update(ttm=ttm, mcap_hkd_m=mcap_hkd, mcap_cny_m=mcap_cny, net_cash_cny_m=net_cash, eps_ttm_hkd=eps,
    pe=mcap_cny/ttm["profit"], ps=mcap_cny/ttm["revenue"], pb=mcap_cny/D("9936.487"),
    ev_revenue=(mcap_cny-net_cash)/ttm["revenue"], p_fcf=mcap_cny/ttm["fcf"], fcf_yield=ttm["fcf"]/mcap_cny*100,
    cfo_profit=ttm["cfo"]/ttm["profit"]*100, fcf_profit=ttm["fcf"]/ttm["profit"]*100,
    old225_adjusted=D(225)/3, old250_adjusted=D(250)/3, price_change_from_old=(price/(D(225)/3)-1)*100,
    h1_cfo_profit=D("1974.001")/D("2427.716")*100,
    h1_fcf_profit=D("1649.551")/D("2427.716")*100)
out["ancillary"] = dict(
    xu_direct_pct=(D("16916480")+D("6829380"))/D("248832930")*100,
    xu_deemed_pct=(D("16916480")+D("6829380")+D("55520950")+D("35679480"))/D("248832930")*100,
    ten_pct_new_shares_per_share_loss_pct=(1-1/D("1.1"))*100,
    bands_base_value_discount_pct=[(1-p/D("81.29825902257138888201314384057877133989"))*100 for p in map(D,["60","65"])],
)
out["three_year"] = []
for name, growth, pe in [("bear", "-0.15", "8"), ("base", "0.08", "12"), ("bull", "0.20", "16")]:
    terminal = eps*(1+D(growth))**3*D(pe)
    out["three_year"].append(dict(name=name, growth=growth, pe=pe, terminal_price=terminal, present_price=terminal/D("1.1")**3, annual_return=(terminal/price)**(D(1)/3)-1))
out["three_year_weighted_present"] = sum(x["present_price"]*w for x,w in zip(out["three_year"],map(D,["0.3","0.5","0.2"])))
# Ten-year terminal-only pressure test: no dividends and no net cash added twice.
profits = [D(2000), D(10000), D(22000)]
irrs = []
out["ten_year"] = []
for profit,g in zip(profits,map(D,["0.01","0.02","0.03"])):
    pe = (1-g/D("0.15"))/(D("0.10")-g)
    irr = t.irr_from_terminal(float(profit/fx),float(mcap_hkd),float(pe),10,0)
    irrs.append(irr*100)
    out["ten_year"].append(dict(profit_cny_m=profit,g=g,pe=pe,irr_pct=irr*100, profit_cagr_pct=((profit/ttm["profit"])**(D(1)/10)-1)*100))
config = {"思格新能": dict(roic=0.15,g=[0.01,0.02,0.03],p=[0.30,0.50,0.20],irr10=irrs,k=0)}
# Reverse equity DCF, CNY profits converted to HKD at constant FX.
# Transitional distributable cash = net profit * q; terminal PE is Gordon derived.
# No current net cash is added: all cash is conservatively reserved for operations.
def reverse_growth(q):
    def value(h):
        return sum(ttm["profit"]*(1+h)**y*q/D("1.1")**y for y in range(1,11)) + ttm["profit"]*(1+h)**10*(1-D("0.02")/D("0.15"))/(D("0.10")-D("0.02"))/D("1.1")**10
    lo,hi=D("-0.5"),D("1")
    for _ in range(160):
        mid=(lo+hi)/2
        if value(mid)>mcap_cny: hi=mid
        else: lo=mid
    return (lo+hi)/2*100
out["reverse_dcf_growth_pct"] = {str(q): reverse_growth(q) for q in [D("0.20"),D("0.60"),D("0.80")]}
with (HERE/"financial-rigor.log").open("w") as log, redirect_stdout(log):
    f.verify_market_cap(float(price),float(shares),53929680000,"HKD")
    for field,values,unit in [
        ("2025收入",{"招股书":9000.512,"ETNet":9000.512},"CNY million"),
        ("2025归母",{"招股书":2918.832,"ETNet":2918.832},"CNY million"),
        ("2026H1收入",{"中报":9873.625,"ETNet":9873.625},"CNY million"),
        ("2026H1归母",{"中报":2427.716,"ETNet":2427.716},"CNY million"),
        ("2026H1银行现金",{"中报":8247.419,"ETNet":8247.419},"CNY million"),
        ("2025CFO",{"招股书":-199.990,"ETNet":-199.990},"CNY million"),
        ("H1CFO",{"中报":1974.001,"Weidn":1974.0},"CNY million"),
        ("HKDCNY现货异步快照",{"Yahoo":0.8496,"XE":0.84979547},"CNY/HKD"),
    ]: f.cross_validate(field,values,unit,1)
    f.verify_valuation(float(price),float(eps),float(D("9936.487")*1000000/shares/fx),float(ttm["fcf"]*1000000/shares/fx),float(D("2.698")/3),float(ttm["revenue"]*1000000/shares/fx))
    f.three_scenario_valuation(float(price),float(eps),float(shares/100000000),0.20,0.08,-0.15,16,12,8,3,"HKD")
    for expr in ["9000512-2733786+9873625","2918832-806605+2427716","-199990-450762+1974001","352711+396+18266-74167-396-18267+257557+5790+61103","1323249-602993","8236289-3119835-35777","(16916480+6829380)/248832930*100","(16916480+6829380+55520950+35679480)/248832930*100","(1-1/1.1)*100"]: f.exact_calc(expr)
    print("\nDecimal calculations (40 digits), inputs and results:")
    print(json.dumps(out,ensure_ascii=False,default=str,indent=2))
(HERE/"计算结果.json").write_text(json.dumps(out,ensure_ascii=False,default=str,indent=2)+"\n")
(HERE/"来源索引.json").write_text(json.dumps(sources,ensure_ascii=False,indent=2)+"\n")
(HERE/"terminal-config.json").write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n")
audit = ["audit","--currency","HKD","--r","0.10","--roic","0.15","--g","0.01,0.02,0.03","--rf","0.047","--beta","1","--discrete-risks","渠道去库:情景,价格竞争:情景,补贴回撤:情景,产品全面禁售:未建模,地缘断供:未建模"]
commands = [audit]
for profit,g in zip(profits,["0.01","0.02","0.03"]):
    pe = (1-D(g)/D("0.15"))/(D("0.10")-D(g))
    commands += [["pe","--roic","0.15","--g",g,"--r","0.10"],["irr","--profit",str(profit/fx),"--mcap",str(mcap_hkd),"--pe",str(pe),"--years","10","--payout","0"]]
for delta in ["0.02","0.01"]:
    commands.append(["flip","--config",str(HERE/"terminal-config.json"),"--name","思格新能","--r","0.10","--delta",delta,"--currency","HKD","--g-shift","0","--rf","0.047"])
commands.append(audit)
with (HERE/"terminal.log").open("w") as log:
    for args in commands:
        result = subprocess.run([sys.executable,str(ROOT/"tools/terminal_value.py"),*args],capture_output=True,text=True)
        log.write(result.stdout+result.stderr)
        if result.returncode: raise RuntimeError(result.stdout)
print(json.dumps({k:v for k,v in out.items() if k!="facts"},ensure_ascii=False,default=str,indent=2))
