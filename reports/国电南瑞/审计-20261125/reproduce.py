"""Reproduce the 2026-11-25 research calculations. No network or state writes."""
import ast
import contextlib
import io
import json
import subprocess
import sys
from decimal import Decimal as D, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import financial_rigor as rigor
import terminal_value as terminal

getcontext().prec = 40
logs = []
calcs = {}


def calc(name, expression):
    """Use the shared calculator and retain a Decimal check of its float path."""
    def evaluate(node):
        if isinstance(node, ast.Constant):
            return D(ast.get_source_segment(expression, node))
        if isinstance(node, ast.UnaryOp):
            return -evaluate(node.operand) if isinstance(node.op, ast.USub) else evaluate(node.operand)
        a, b = evaluate(node.left), evaluate(node.right)
        return {ast.Add: lambda: a+b, ast.Sub: lambda: a-b,
                ast.Mult: lambda: a*b, ast.Div: lambda: a/b,
                ast.Pow: lambda: a**b}[type(node.op)]()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        shared = rigor.exact_calc(expression)
    result = evaluate(ast.parse(expression, mode="eval").body)
    assert shared is not None and abs(D(str(shared))-result) <= max(D("1e-10"), abs(result)*D("1e-12"))
    logs.append(name + "\n" + buf.getvalue() + "Decimal复核: " + str(result))
    calcs[name] = {"expression": expression, "value": str(result)}
    return result


def run(tool, *args):
    p = subprocess.run([sys.executable, str(ROOT / "tools" / tool), *map(str, args)],
                       capture_output=True, text=True, check=True)
    logs.append(p.stdout)
    return p.stdout


shares = D("8031756156")
price = D("24.60")
profit = D("8335343392.88")
eps = calc("eps_ttm", f"{profit}/{shares}")
mcap = calc("mcap", f"{price}*{shares}")
netcash = calc("net_cash_conservative", "6932263372.88+6013927424.63-352207283.33-7000000-71136126.99-57434388.23")
run("financial_rigor.py", "verify-market-cap", "--price", price, "--shares", shares,
    "--reported", "197581000000", "--currency", "CNY")
for field, first, second, unit in [
    ("2025营业收入", "66228963223.21", "66228963223.21", "CNY"),
    ("2025归母净利润", "8278971723.32", "8278971723.32", "CNY"),
    ("2026Q3货币资金", "6932263372.88", "6932263372.88", "CNY"),
    ("2026Q3交易性金融资产", "6013927424.63", "6013927424.63", "CNY"),
    ("2026Q3股本", str(shares), str(shares), "股"),
    ("2026Q3累计经营现金流", "-2919538534.11", "-2919538534.11", "CNY"),
    ("2026Q3保守净现金", str(netcash), str(netcash), "CNY"),
]:
    run("financial_rigor.py", "cross-validate", "--field", field, "--values",
        json.dumps({"巨潮原始报告": float(first), "东方财富结构化分发": float(second)}, ensure_ascii=False), "--unit", unit)

series = [
    (2021,"42411007392.46","5642448311.81","31011682368.56","6843422141.78","4670773603.37","2016394641.36","12508960927.62"),
    (2022,"46828962926.94","6446181151.11","34164697635.46","7851765879.63","8759962599.71","3415193158.37","14743557762.16"),
    (2023,"51655248318.66","7175185980.94","37813103058.37","8544114750.84","11278310677.65","1952239391.71","16750152852"),
    (2024,"57829172321.78","7610235695.07","42459770307.62","9118972452.31","11086788479.77","1850169755.99","9033417046.54"),
    (2025,"66228963223.21","8278971723.32","49117323852.59","9809281552.09","12768702125.04","2110354922.10","7323259338.52"),
]
annual=[]
for year, rev, ni, cost, op, cfo, capex, cash in series:
    row = dict(year=year, revenue=rev, profit=ni, cost=cost, operating_profit=op, cfo=cfo, capex=capex, cash=cash)
    for key, expression in {"gross_margin":f"(1-{cost}/{rev})*100", "operating_margin":f"{op}/{rev}*100",
                            "fcf":f"{cfo}-{capex}", "net_margin":f"{ni}/{rev}*100"}.items():
        row[key]=str(calc(f"{year}_{key}", expression))
    annual.append(row)

for name, expression in {
    "ttm_revenue":"66228963223.21+43879577511.61-38576507202.81",
    "ttm_cfo":"12768702125.04-2919538534.11-4714110770.90",
    "ttm_capex":"2110354922.10+1178331939.15-1237649038.30",
    "ttm_fcf":"12768702125.04-2110354922.10-2919538534.11-1178331939.15-4714110770.90+1237649038.30",
    "ttm_pe":f"{mcap}/{profit}",
    "pb":f"{mcap}/52572913859.30",
    "ps":f"{mcap}/71532033532.01",
    "fcf_yield":f"3084014997.08/{mcap}*100",
    "fcf_conversion":"3084014997.08/8335343392.88*100",
    "ev_sales":f"({mcap}+3766038700.54-{netcash})/71532033532.01",
    "dividend_yield":"0.628/24.60*100",
    "peg_8pct":f"{mcap}/{profit}/8",
    "2026_9m_gross_margin":"(1-32713639974.08/43879577511.61)*100",
    "2026_h1_gross_margin":"(1-20731180000.21/27767190529.75)*100",
    "2026_9m_net_margin":"4911652568.60/43879577511.61*100",
    "2025_9m_net_margin":"4855280899.04/38576507202.81*100",
    "2026_9m_fcf":"-2919538534.11-1178331939.15",
    "2026_q3_cfo":"-2919538534.11-591109591.80",
    "2026_q3_fcf":"-2919538534.11-591109591.80-1178331939.15+754329578.19",
    "2026_q2_revenue":"27767190529.75-9564242921.53",
    "2026_q2_profit":"3072688826.28-721291973.43",
    "2025_q4_revenue":"66228963223.21-38576507202.81",
    "2025_q4_profit":"8278971723.32-4855280899.04",
    "2025_q4_cfo":"12768702125.04-4714110770.90",
    "2026_supplier_payment_increase":"41795983055.81-32468813767.36",
    "2026_payables_decline":"22475311026.78-27828765884.55",
    "2026_receipts_growth":"(46787758173.36/44973628424.82-1)*100",
    "h1_related_sales_pct":"40.59+0.93+0.55",
    "xj_h1_margin":"(1-5226962810.61/6525206200.08)*100",
    "sf_h1_margin":"(1-3043022187.32/4482004433.21)*100",
    "retention_implied_return":"0.06/(1-0.60)*100",
    "chair_hold_pct_2025":"20736/8031756156*100",
    "2025_roic_upper_proxy":"9809281552.09*(1-0.13)/(56459444556.90+587370367.85-24493631524.25)*100",
}.items():
    calc(name, expression)
run("financial_rigor.py", "cross-validate", "--field", "董事长2025披露持股占年末注册股本",
    "--values", json.dumps({"选举公告持股和年末股本": float(calcs['chair_hold_pct_2025']['value']),
                            "年报持股表和东方财富股本": float(calcs['chair_hold_pct_2025']['value'])}, ensure_ascii=False), "--unit", "%")
run("financial_rigor.py", "verify-valuation", "--price", price, "--eps", eps,
    "--bvps", calc("bvps",f"52572913859.30/{shares}"),
    "--fcf-per-share",calc("fcf_per_share",f"3084014997.08/{shares}"), "--dividend", "0.628")
run("financial_rigor.py", "three-scenario", "--price", price, "--eps", eps, "--shares", "80.31756156",
    "--growth", ".12", ".08", "0", "--pe", "24", "22", "16", "--years", "3", "--currency", "CNY")

three=[]
for label, growth, pe, prob in [("悲观","0","16","0.3"),("基准","0.08","22","0.5"),("乐观","0.12","24","0.2")]:
    future=calc(label+"_3y_price",f"{eps}*(1+{growth})**3*{pe}")
    div=calc(label+"_3y_dividends", "+".join(f"{eps}*(1+{growth})**{t}*0.60" for t in range(1,4)))
    pv=calc(label+"_3y_pv", "+".join(f"{eps}*(1+{growth})**{t}*0.60/(1.08)**{t}" for t in range(1,4))+f"+{future}/1.08**3")
    total=calc(label+"_3y_total_return",f"(({future}+{div})/24.60-1)*100")
    ann=calc(label+"_3y_annual_return",f"((({future}+{div})/24.60)**(1/3)-1)*100")
    three.append(dict(label=label,growth=growth,pe=pe,p=prob,future=str(future),div=str(div),pv=str(pv),total_return=str(total),annual_return=str(ann)))
calc("weighted_3y_pv","+".join(f"{s['p']}*{s['pv']}" for s in three))
calc("reverse_3y_growth_22pe_8pct",f"((24.60*1.08**3/({eps}*22))**(1/3)-1)*100")
lo,hi=D("-0.2"),D("0.5")
for _ in range(160):
    growth=(lo+hi)/2
    value=sum(eps*(1+growth)**t*D(".6")/D("1.08")**t for t in range(1,4))+eps*(1+growth)**3*22/D("1.08")**3
    if value < price: lo=growth
    else: hi=growth
calcs["reverse_3y_growth_including_dividends"]={"value":str((lo+hi)/2*100),"method":"Decimal二分：三年60%派息+末期22PE，8%折现，匹配24.60"}

risk="增长稀释:情景,付款账期重置:情景,海外坏账:情景,极端电网事故:未建模,关联治理突变:未建模"
audit_args=["audit","--currency","CNY","--r",".08","--roic",".15","--g","0,.015,.02","--rf",".0159","--beta","1","--discrete-risks",risk]
run("terminal_value.py",*audit_args)
spec={"roic":.15,"g":[0,.015,.02],"p":[.3,.5,.2],"irr10":[],"k":.025}
ten=[]
cash_stress={str(r):[] for r in [D('.06'),D('.07'),D('.08'),D('.09'),D('.10')]}
for label,growth,g,p in [("悲观","0.02","0","0.3"),("基准","0.06","0.015","0.5"),("乐观","0.10","0.02","0.2")]:
    final=calc(label+"_10y_profit",f"{profit}/1e8*(1+{growth})**10")
    exitpe=calc(label+"_10y_pe",f"(1-{g}/0.15)/(0.08-{g})")
    run("terminal_value.py","pe","--roic",".15","--g",g,"--r",".08")
    run("terminal_value.py","irr","--profit",final,"--mcap",mcap/D("1e8"),"--pe",exitpe,"--years",10,"--payout",".025")
    pe10=calc(label+"_anchor_pe10",f"(1-{g}/0.15)/(0.10-{g})")
    run("terminal_value.py","irr","--profit",final,"--mcap",mcap/D("1e8"),"--pe",pe10,"--years",10,"--payout",".025")
    anchor=terminal.irr_from_terminal(float(final),float(mcap/D("1e8")),float(pe10),10,.025)*100
    spec["irr10"].append(anchor)
    approx=terminal.irr_from_terminal(float(final),float(mcap/D("1e8")),float(exitpe),10,.025)*100
    # Economic distributions: growth consumes incremental equity capital at 20%.
    payout=calc(label+"_10y_cash_payout",f"1-{growth}/0.20")
    dividends=[profit*(1+D(growth))**t*payout for t in range(1,11)]
    terminal_value=final*D("1e8")*exitpe
    pv=calc(label+"_cash_dcf_equity_value", "+".join(f"{v}/1.08**{t}" for t,v in enumerate(dividends,1))+f"+{terminal_value}/1.08**10")/shares
    def npv(rate):
        return sum(v/(1+rate)**t for t,v in enumerate(dividends,1))+terminal_value/(1+rate)**10-mcap
    low,high=D("-0.5"),D("1")
    for _ in range(180):
        mid=(low+high)/2
        if npv(mid)>0: low=mid
        else: high=mid
    actual=(low+high)/2*100
    calc(label+"_cash_irr_npv_per_share", "("+"+".join(f"{v}/(1+{actual}/100)**{t}" for t,v in enumerate(dividends,1))+f"+{terminal_value}/(1+{actual}/100)**10)/{shares}")
    ten.append(dict(label=label,growth=growth,g=g,p=p,profit=str(final),pe=str(exitpe),approx_irr=approx,payout=str(payout),cash_dcf=str(pv),cash_irr=str(actual)))
    for rate, bucket in cash_stress.items():
        term_pe=(1-D(g)/D('.15'))/(D(rate)-D(g))
        lo,hi=D('-.5'),D('1')
        for _ in range(180):
            mid=(lo+hi)/2
            value=sum(v/(1+mid)**t for t,v in enumerate(dividends,1))+final*D('1e8')*term_pe/(1+mid)**10-mcap
            if value>0: lo=mid
            else: hi=mid
        bucket.append(dict(p=p,irr=str((lo+hi)/2*100),spread=str(D(rate)-D(g))))
(OUT/"terminal-config.json").write_text(json.dumps({"国电南瑞":spec},ensure_ascii=False,indent=2)+"\n")
run("terminal_value.py","flip","--config",OUT/"terminal-config.json","--name","国电南瑞","--r",".08","--delta",".02","--currency","CNY","--g-shift","0","--rf",".0159")
run("terminal_value.py","flip","--config",OUT/"terminal-config.json","--name","国电南瑞","--r",".08","--delta",".01","--currency","CNY","--g-shift","0","--rf",".0159")
calc("weighted_cash_dcf","+".join(f"{s['p']}*{s['cash_dcf']}" for s in ten))
calc("weighted_cash_irr","+".join(f"{s['p']}*{s['cash_irr']}" for s in ten))
for rate,bucket in cash_stress.items():
    calc("cash_stress_"+rate,"+".join(f"{s['p']}*{s['irr']}" for s in bucket))
for ret in ['0.15','0.25']:
    growth=D('.06'); payout=1-growth/D(ret)
    terminal_value=D(ten[1]['profit'])*D('1e8')*D(ten[1]['pe'])
    dividends=[profit*(1+growth)**t*payout for t in range(1,11)]
    calc("base_cash_dcf_reinvestment_return_"+ret, "("+"+".join(f"{v}/1.08**{t}" for t,v in enumerate(dividends,1))+f"+{terminal_value}/1.08**10)/{shares}")
calc("19_vs_base_3y_pv",f"(1-19/{three[1]['pv']})*100")
calc("17_vs_base_3y_pv",f"(1-17/{three[1]['pv']})*100")
run("terminal_value.py",*audit_args)
(OUT/"calculations.json").write_text(json.dumps(dict(calculations=calcs,annual=annual,three_year=three,ten_year=ten,cash_stress=cash_stress),ensure_ascii=False,indent=2)+"\n")
(OUT/"tool-output.txt").write_text("\n\n".join(logs)+"\n")
print(json.dumps(dict(three_year=three,ten_year=ten,summary={k:v for k,v in calcs.items() if k in ['weighted_3y_pv','weighted_cash_dcf','weighted_cash_irr','reverse_3y_growth_22pe_8pct']}),ensure_ascii=False,indent=2))
