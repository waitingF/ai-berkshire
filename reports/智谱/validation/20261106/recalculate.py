"""Reproduce this report's assumptions with financial_rigor Decimal inputs."""
import json
import sys
from decimal import getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from financial_rigor import exact as D

getcontext().prec = 40
inputs = json.loads((HERE / "model-inputs.json").read_text())
shares = D(inputs["shares"])
fx = D(inputs["cny_hkd"])
price = D(inputs["price_hkd"])
cash = D(inputs["net_cash_cny_100m_assumption"])
dilution = D(inputs["annual_dilution_assumption"])
roic = D(inputs["roic_assumption"])
shares_100m = shares / D(100000000)
mcap = price * shares_100m / fx
snapshot = {
    "mcap_hkd_100m": price * shares_100m,
    "mcap_cny_100m": mcap,
    "FY2025_PS": mcap / D("7.24334"),
    "TTM_revenue_cny_100m": D("7.24334") - D("1.90877") + D("9.53892"),
    "H1_annualized_revenue_cny_100m": D("9.53892") * 2,
    "net_cash_june_cny_100m": (D(3993722)+D(506139)-D(2224789)-D(379410))/D(100000),
    "unrestricted_net_cash_june_cny_100m": (D(3887727)+D(506139)-D(2224789)-D(379410))/D(100000),
    "FCF_H1_cny_100m": (-D(3374057)-D(586417))/D(100000),
    "H1_RD_gross_profit_ratio": D(2131171)/D(251611),
    "H1_gross_margin_pct": D(251611)/D(953892)*100,
    "H1_API_share_pct": D(825176)/D(953892)*100,
    "H1_API_gross_margin_pct": D(202871)/D(825176)*100,
    "FY2025_API_gross_margin_pct": D(36000)/D(190379)*100,
    "H2_2025_API_gross_margin_pct": D(36116)/(D(190379)-D(29100))*100,
    "H1_local_revenue_change_pct": (D(128716)/(D(190877)-D(29100))-1)*100,
    "H1_vs_FY2025_annualized_CFO_ratio": D(3374057)*2/D(2246123),
    "july_net_proceeds_hkd_100m": D("31374.95")/100,
    "september_net_equity_hkd_100m": D("15664.13")/100,
    "july_deployed_by_august_hkd_100m": D("10954.80")/100,
    "july_deployed_by_august_cny_100m_at_model_fx": D("10954.80")/100/fx,
    "cash_bridge_before_post_june_spending_cny_100m": ((D(3887727)+D(506139)-D(2224789)-D(379410))/D(100000) + (D("31374.95")+D("15664.13")+D("23610.24"))/100/fx - D("201.4")),
    "CB_full_conversion_shares": shares+D(26365026),
    "total_H_shares_pct": D(263059605)/shares*100,
    "price714_change_pct": (price/D(714)-1)*100,
    "price892_5_change_pct": (price/D("892.5")-1)*100,
    "intraday_snapshot_hkd": "432.4 at 2026-11-06 10:14:46; Tencent delayed snapshot",
    "intraday_mcap_hkd_100m": D("432.4")*shares_100m
}
snapshot["TTM_PS"] = mcap / snapshot["TTM_revenue_cny_100m"]
snapshot["H1_annualized_PS"] = mcap / snapshot["H1_annualized_revenue_cny_100m"]
for arr in ("1.6", "1.8", "3"):
    revenue = D(arr)*10*D(inputs["usd_cny_for_arr"])
    snapshot[f"ARR_{arr}_billion_usd_cny_100m"] = revenue
    snapshot[f"P_ARR_{arr}_billion_usd"] = mcap/revenue
snapshot["EV_ARR_1_8_basecash"]=(mcap-cash)/snapshot["ARR_1.8_billion_usd_cny_100m"]
snapshot["annualized_H1_operating_expenses_cny_100m"]=(D(2131171)+D(177666)+D(103346))*2/D(100000)
snapshot["static_breakeven_annual_revenue_cny_100m"]=snapshot["annualized_H1_operating_expenses_cny_100m"]/(D(251611)/D(953892))
snapshot["Tang_direct_pct_assuming_unchanged"]=D(26835330)/shares*100
snapshot["concert_group_pct_assuming_unchanged"]=D(133044230)/shares*100

def calculate_case(case, r, cash_amount):
    fcf = list(map(D,case["fcf_cny_100m"]))
    g = D(case["g"])
    # Standard terminal value: cash flow in year 11 / (r-g).
    # terminal_value.py's earnings multiple applies to year-11 earnings;
    # grow year-10 earnings by (1+g) explicitly to align timing.
    multiple = (1-g/roic)/(r-g)
    profit11 = D(case["terminal_operating_profit_cny_100m"])*(1+g)
    terminal_ev = profit11*multiple
    q=(1+r)*(1+dilution)
    pv_fcf=sum((v/q**(i+1) for i,v in enumerate(fcf)),D(0))
    pv_terminal=terminal_ev/q**10
    equity=cash_amount+pv_fcf+pv_terminal
    price_now=max(D(0),equity/shares_100m*fx)
    cash2029=cash_amount+sum(fcf[:3],D(0))
    future2029=sum((v/((1+r)**(i+1-3)*(1+dilution)**(i+1)) for i,v in enumerate(fcf) if i>=3),D(0))
    # Express all future per-share claims in original-share units.
    terminal2029=terminal_ev/((1+r)**7*(1+dilution)**10)
    price2029=max(D(0),(cash2029/(1+dilution)**3+future2029+terminal2029)/shares_100m*fx)
    required_profit10=(mcap-cash_amount-pv_fcf)*q**10/(multiple*(1+g))
    return {
        "terminal_multiple_on_year11_profit":multiple,
        "r_minus_g":r-g,
        "PV_FCF_cny_100m":pv_fcf,
        "PV_terminal_cny_100m":pv_terminal,
        "equity_value_cny_100m":equity,
        "price_now_hkd":price_now,
        "price2029_hkd":price2029,
        "price2029_change_pct":(price2029/price-1)*100,
        "required_2036_operating_profit_at_current_price_cny_100m":required_profit10,
        "required_revenue_at_15pct_margin_cny_100m":required_profit10/D("0.15"),
        "PV_cash_hkd_per_share":cash_amount/shares_100m*fx,
        "terminal_value_fraction_of_operating_value":pv_terminal/(pv_fcf+pv_terminal) if pv_fcf+pv_terminal else None
    }

valuation={}
for name,case in inputs["scenarios"].items():
    valuation[name]={str(r):calculate_case(case,D(r),cash) for r in inputs["discount_rates"]}
valuation["base_net_cash_sensitivity"]={str(c):calculate_case(inputs["scenarios"]["base"],D("0.08"),D(c))["price_now_hkd"] for c in (100,200,300)}
valuation["base_no_dilution_price_hkd"] = None
previous=dilution
dilution=D(0)
valuation["base_no_dilution_price_hkd"]=calculate_case(inputs["scenarios"]["base"],D("0.08"),cash)["price_now_hkd"]
dilution=previous
valuation["base_margin_of_safety_25pct_price_hkd"]=valuation["base"]["0.09"]["price_now_hkd"]*D("0.75")

def encode(x):
    if isinstance(x,dict): return {k:encode(v) for k,v in x.items()}
    if isinstance(x,list): return [encode(v) for v in x]
    return str(x) if hasattr(x,"as_tuple") else x

out=encode({"snapshot":snapshot,"valuation":valuation,"assumptions":inputs})
(HERE/"calculations.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(encode({"snapshot":snapshot,"valuation":valuation}),ensure_ascii=False,indent=2))
