"""Research calculations only. Money: CNY bn unless a key says otherwise."""
from decimal import Decimal as D, getcontext
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

getcontext().prec = 40
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("financial_rigor", ROOT / "tools/financial_rigor.py")
rigor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rigor)
E = rigor.exact

price, shares, fx = E("26.50"), E("25.740747757"), E("0.8501")
mcap_hkd, mcap = price * shares, price * shares * fx
adjusted = E("39.166303") - E("32.817233") + E("17.175059")
sbc = E("5.365075") - E("3.935320") + E("3.239158")
economic = adjusted - sbc
eps_cny, eps_hkd = E(20) / shares, E(20) / shares / fx
attributable_ttm = E("41.643389") - E("35.099600") + E("18.061106")
revenue_ttm = E("457.286687") - E("340.370162") + E("315.302752")
borrowing = E("27.906615") + E("17.547096")
narrow_cash = E("38.442969") + E("56.537448") + E("12.321762") + E("2.247158")

result = {
    "price_hkd": price, "shares_bn": shares, "cny_per_hkd": fx,
    "mcap_hkd_bn": mcap_hkd, "mcap_cny_bn": mcap,
    "ttm_adjusted_bn": adjusted, "ttm_sbc_bn": sbc, "ttm_adjusted_less_sbc_bn": economic,
    "normalized_economic_bn_assumption": E(20),
    "normalization_uplift_pct": (E(20) / economic - 1) * 100,
    "eps_cny_model": eps_cny, "eps_hkd_model": eps_hkd,
    "ttm_attributable_bn": attributable_ttm, "ttm_revenue_bn": revenue_ttm,
    "pe_ttm_attributable": mcap / attributable_ttm,
    "pe_ttm_adjusted": mcap / adjusted, "pe_ttm_less_sbc": mcap / economic,
    "pe_model": mcap / 20, "ps": mcap / revenue_ttm,
    "borrowing_bn": borrowing, "narrow_cash_bn": narrow_cash,
    "narrow_net_cash_bn": narrow_cash - borrowing,
    "broad_cash_bn_rounded": E("196.9"),
    "broad_net_cash_bn_rounded": E("196.9") - borrowing,
    "ev_sales_narrow": (mcap - narrow_cash + borrowing) / revenue_ttm,
    "ev_sales_broad": (mcap - E("196.9") + borrowing) / revenue_ttm,
    "q3_cfo_less_management_capex_bn_proxy": E("-23.0344") - E("3.5807"),
    "inventory_change_from_dec_pct": (E("108.304061") / E("80.989452") - 1) * 100,
    "q3_cfo_profit_pct": E("-23.0344") / E("3.876256") * 100,
    "cash_decline_since_june_bn": E("219.3") - E("196.9"),
    "q3_core_operating_bn": E("21.614507") - E("9.242571") - E("8.582310") - E("1.653276"),
    "buyback_average_hkd": E("13.106128202") / E("0.43154"),
    "lei_economic_pct": (E("3.979972128") + E("2.076807510")) / shares * 100,
    "lei_voting_pct": (E("3.979972128") * 10 + E("2.076807510")) / (E("4.419197866") * 10 + E("21.321549891")) * 100,
    "fy2025_cash_purchase_fcfe_proxy_bn": E("34.142377") - E("12.769155"),
    "fy2025_after_deferred_and_lease_bn": E("34.142377") - E("12.769155") - E("2.499913") - E("2.902504"),
    "fy2025_after_deferred_and_lease_yield_pct": (E("34.142377") - E("12.769155") - E("2.499913") - E("2.902504")) / mcap * 100,
    "ttm_cfo_bn": E("34.142377") - E("33.528360") - E("20.984274"),
    "three_year": [], "ten_year": [], "full_cash_sensitivity": [],
}

for name, growth, pe, probability in [
    ("bear", E("-0.05"), E(14), E("0.30")),
    ("base", E("0.15"), E(22), E("0.50")),
    ("bull", E("0.30"), E(30), E("0.20")),
]:
    future_eps = eps_hkd * (1 + growth) ** 3
    target = future_eps * pe
    result["three_year"].append({
        "name": name, "growth": growth, "pe": pe, "probability": probability,
        "profit_bn": E(20) * (1 + growth) ** 3,
        "eps_hkd": future_eps, "target_hkd": target,
        "pv_hkd_at_8pct_cny_basis": target / E("1.08") ** 3,
        "annual_price_return_pct": ((target / price) ** (E(1) / 3) - 1) * 100,
    })
result["three_year_weighted_pv_hkd"] = sum(x["pv_hkd_at_8pct_cny_basis"] * x["probability"] for x in result["three_year"])
result["reverse_3y_growth_at_pe22"] = ((price * E("1.08") ** 3 / (eps_hkd * 22)) ** (E(1) / 3) - 1) * 100
result["base_pv_margin_at_18_pct"] = (1 - 18 / result["three_year"][1]["pv_hkd_at_8pct_cny_basis"]) * 100
result["base_pv_margin_at_20_pct"] = (1 - 20 / result["three_year"][1]["pv_hkd_at_8pct_cny_basis"]) * 100

terminal_roic, interim_roic = E("0.15"), E("0.20")
scenario_inputs = [("bear", E(20), E("0.005"), E("0.30")),
                   ("base", E(50), E("0.015"), E("0.50")),
                   ("bull", E(100), E("0.02"), E("0.20"))]

def cash_irr(cashflows):
    lo, hi = E("-0.90"), E("1.00")
    for _ in range(180):
        mid = (lo + hi) / 2
        npv = -mcap + sum(cf / (1 + mid) ** t for t, cf in enumerate(cashflows, 1))
        if npv > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2 * 100

anchors = []
for name, terminal_profit, g, probability in scenario_inputs:
    growth = (terminal_profit / 20) ** (E(1) / 10) - 1
    # Growth requires investment. FCFE = earnings - incremental earnings / ROIC.
    earnings = [E(20) * (1 + growth) ** t for t in range(11)]
    cashflows = [earnings[t] - (earnings[t] - earnings[t-1]) / interim_roic for t in range(1, 11)]
    pe8 = (1 - g / terminal_roic) / (E("0.08") - g)
    pe10 = (1 - g / terminal_roic) / (E("0.10") - g)
    anchor = ((terminal_profit * pe10 / mcap) ** (E(1) / 10) - 1) * 100
    anchors.append(anchor)
    terminal_only = ((terminal_profit * pe8 / mcap) ** (E(1) / 10) - 1) * 100
    complete = cashflows.copy()
    complete[-1] += terminal_profit * pe8
    result["ten_year"].append({
        "name": name, "probability": probability, "profit_bn": terminal_profit,
        "growth_10y": growth, "g": g, "roic_terminal": terminal_roic,
        "roic_interim": interim_roic, "terminal_pe_at_8pct": pe8,
        "terminal_only_irr_at_8pct": terminal_only,
        "irr10_anchor": anchor, "annual_fcfe_bn": cashflows,
        "complete_cash_irr_pct": cash_irr(complete),
        "complete_cash_pv_bn": sum(cf / E("1.08") ** t for t, cf in enumerate(complete, 1)),
    })
result["terminal_only_weighted_irr_pct"] = sum(x["terminal_only_irr_at_8pct"] * x["probability"] for x in result["ten_year"])
result["complete_cash_weighted_irr_pct"] = sum(x["complete_cash_irr_pct"] * x["probability"] for x in result["ten_year"])
result["complete_cash_weighted_pv_hkd"] = sum(x["complete_cash_pv_bn"] * x["probability"] for x in result["ten_year"]) / shares / fx
for rate in map(E, ["0.06", "0.07", "0.08", "0.09", "0.10"]):
    irrs, pvs = [], []
    for x in result["ten_year"]:
        pe = (1 - x["g"] / terminal_roic) / (rate - x["g"])
        cfs = x["annual_fcfe_bn"].copy()
        cfs[-1] += x["profit_bn"] * pe
        irrs.append(cash_irr(cfs))
        pvs.append(sum(cf / (1 + rate) ** t for t, cf in enumerate(cfs, 1)))
    result["full_cash_sensitivity"].append({
        "r": rate, "weighted_irr_pct": sum(v * x["probability"] for v, x in zip(irrs, result["ten_year"])),
        "weighted_pv_hkd": sum(v * x["probability"] for v, x in zip(pvs, result["ten_year"])) / shares / fx,
        "passes": sum(v * x["probability"] for v, x in zip(irrs, result["ten_year"])) >= rate * 100,
        "c2_valid_all_scenarios": all(rate - x["g"] >= E("0.05") for x in result["ten_year"]),
    })
cfg = {"小米": {"roic": .15, "g": [.005, .015, .02], "p": [.30, .50, .20],
                 "irr10": [float(x) for x in anchors], "k": 0}}

def serial(obj):
    if isinstance(obj, D):
        return str(obj)
    raise TypeError(type(obj))

(OUT / "model-output.json").write_text(json.dumps(result, default=serial, ensure_ascii=False, indent=2) + "\n")
(OUT / "terminal-config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")

audit = ["tools/terminal_value.py", "audit", "--currency", "CNY", "--r", "0.08", "--roic", ".15", "--g", ".005,.015,.02", "--rf", ".02", "--beta", "1.0", "--discrete-risks", "库存减值:情景,汽车及AI亏损:情景,严重召回:未建模,印度追缴:未建模,VIE失效:未建模,地缘断供:未建模"]
commands = [
    audit,
    ["tools/financial_rigor.py", "verify-market-cap", "--price", str(price), "--shares", str(shares * 10**9), "--reported", "682127000000", "--currency", "HKD"],
    ["tools/financial_rigor.py", "cross-validate", "--field", "FY2025收入", "--values", '{"公司":457286.687,"StockAnalysis":457287}', "--unit", "百万元"],
    ["tools/financial_rigor.py", "cross-validate", "--field", "FY2025归母利润", "--values", '{"公司":41643.389,"StockAnalysis":41643}', "--unit", "百万元"],
    ["tools/financial_rigor.py", "cross-validate", "--field", "Q3现金等价物", "--values", '{"公司":38442.969,"StockAnalysis":38443}', "--unit", "百万元"],
    ["tools/financial_rigor.py", "cross-validate", "--field", "Q3狭义现金及短投定存", "--values", json.dumps({"公司分项重建": float(narrow_cash * 1000), "StockAnalysis":109549}), "--unit", "百万元"],
    ["tools/financial_rigor.py", "verify-valuation", "--price", str(price), "--eps", str(attributable_ttm / shares / fx), "--dividend", "0", "--revenue-per-share", str(revenue_ttm / shares / fx)],
    ["tools/financial_rigor.py", "three-scenario", "--price", str(price*fx), "--eps", str(eps_cny), "--shares", str(shares * 10), "--growth", ".30", ".15", "-.05", "--pe", "30", "22", "14", "--years", "3", "--currency", "CNY"],
]
for x in result["ten_year"]:
    commands += [
        ["tools/terminal_value.py", "pe", "--roic", ".15", "--g", str(x["g"]), "--r", ".08"],
        ["tools/terminal_value.py", "irr", "--profit", str(x["profit_bn"]), "--mcap", str(mcap), "--pe", str(x["terminal_pe_at_8pct"]), "--years", "10", "--payout", "0"],
        ["tools/terminal_value.py", "pe", "--roic", ".15", "--g", str(x["g"]), "--r", ".10"],
        ["tools/terminal_value.py", "irr", "--profit", str(x["profit_bn"]), "--mcap", str(mcap), "--pe", str((1-x["g"] / terminal_roic) / (E(".10")-x["g"])), "--years", "10", "--payout", "0"],
    ]
for delta in [".02", ".01"]:
    commands.append(["tools/terminal_value.py", "flip", "--config", str(OUT / "terminal-config.json"), "--name", "小米", "--r", ".08", "--delta", delta, "--currency", "CNY", "--g-shift", "0", "--rf", ".02"])
with (OUT / "tool-validation.log").open("w") as log:
    for command in commands:
        if len(command) > 1 and command[1] == "cross-validate":
            command += ["--tolerance", "1.0"]
        proc = subprocess.run([sys.executable, *command], cwd=ROOT, text=True, capture_output=True)
        log.write("$ python3 " + " ".join(command) + "\n" + proc.stdout + proc.stderr + "\n")
        if proc.returncode:
            raise SystemExit(f"Failed: {command}: {proc.stderr}")
print(json.dumps(result, default=serial, ensure_ascii=False, indent=2))
