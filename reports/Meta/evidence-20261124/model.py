"""Reproduce Meta's 2026-11-24 research snapshot; no network or shared-state writes.

Amounts: USD millions, except actual shares and per-share values.
Forecasts are research assumptions. Tool logs preserve known source conflicts.
"""
from decimal import Decimal as D, getcontext
from pathlib import Path
import json
import subprocess
import sys

getcontext().prec = 38
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
price = D('597.60')
shares = D(2214472367 + 341768886)
future_shares = shares + D(66000000)  # 46m forward incl. exercised option + 20m preferred max.
dilution_factor = shares / future_shares
mcap = price * shares / D(1000000)
eps_core = D('29.33') - D('3.13') + D('3.57')
# Build a consistent profit anchor from GAAP operating profit, documented one-offs,
# actual net interest/other income, and an assumed normalized 17% tax rate.
# Retain all SBC. Do not make undisclosed New Mexico provision adjustments.
normalized_oi = D(79380) + D(9890) + D(2400) + D(1180)
normalized_pretax = normalized_oi + D(609) - D(1126)
initial_profit = normalized_pretax * (1 - D('.17'))
eps_model = initial_profit * D(1000000) / future_shares
r, roic, rf = D('.10'), D('.18'), D('.0492')
gs = [D('.01'), D('.03'), D('.04')]
probabilities = [D('.30'), D('.50'), D('.20')]
profits10 = [D(90000), D(180000), D(300000)]
k = D('2.10') / price



def jsonable(x):
    if isinstance(x, D):
        return str(x)
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [jsonable(v) for v in x]
    return x


def exit_pe(g, rate=r):
    return (1 - g / roic) / (rate - g)


def solve_irr(cashflows):
    def npv(rate):
        return sum(v / (1 + rate) ** t for t, v in enumerate(cashflows))
    lo, hi = D('-.90'), D('2')
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


out = {
    'price': price, 'shares': shares, 'future_shares_assumption': future_shares,
    'one_off_dilution_pct': (future_shares / shares - 1) * 100,
    'mcap_m': mcap, 'partial_adjusted_eps_approx': eps_core,
    'normalized_oi_m': normalized_oi, 'normalized_pretax_m': normalized_pretax,
    'normalized_eps_at_current_shares': initial_profit*D(1000000)/shares,
    'model_eps_after_one_off_dilution': eps_model,
    'core_profit_proxy_m': initial_profit,
    'ttm': {'revenue': 241605, 'oi_gaap': 79380, 'ni_gaap': 75249, 'cfo': 133087,
            'cash_ppe': 104438, 'finance_lease_principal': 3523, 'fcf_company': 25126, 'sbc': 26943},
    'ratios': {
        'pe_eps': price / D('29.33'), 'pe_current_shares_profit': mcap / D(75249),
        'pe_normalized': mcap / initial_profit, 'ps': mcap / D(241605),
        'pb': mcap / D(272386), 'p_fcf_company': mcap / D(25126),
        'fcf_yield_pct': D(25126) / mcap * 100,
        'ev_sales_borrowings': (mcap + D(83669) - D(82449)) / D(241605),
        'dividend_yield_pct': k * 100,
        'fcf_minus_sbc': D(25126) - D(26943),
        'q3_ad_share_pct': D(63061) / D(64601) * 100,
        'q3_gross_margin_pct': (1 - D(13369) / D(64601)) * 100,
        'q3_oi_margin_pct': D(12988) / D(64601) * 100,
        'q3_oi_without_state_charge_pct': D(22878) / D(64601) * 100,
        'q3_foa_margin_pct': D(17117) / D(64158) * 100,
        'q3_ad_growth_from_drivers_pct': (D('1.10') * D('1.14') - 1) * 100,
    },
    'annual': [], 'three_year': [], 'ten_year': [],
}
revenues = [117929, 116609, 134902, 164501, 200966]
costs = [22649, 25249, 25959, 30161, 36175]
ois = [46753, 28944, 46751, 69380, 83276]
for year, rev, cost, oi in zip(range(2021, 2026), revenues, costs, ois):
    out['annual'].append({'year': year, 'gross_margin': (1 - D(cost) / D(rev)) * 100,
                          'oi_margin': D(oi) / D(rev) * 100})

for label, growth, pe in zip(['bear', 'base', 'bull'], [D('-.05'), D('.12'), D('.20')], [D(16), D(22), D(26)]):
    eps3 = eps_model * (1 + growth) ** 3
    target = eps3 * pe
    dividend = D('2.10')
    pv = sum(dividend / (1+r) ** t for t in range(1, 4)) + target / (1+r) ** 3
    irr = solve_irr([-price, dividend, dividend, dividend + target])
    out['three_year'].append({'case': label, 'growth': growth, 'pe': pe, 'eps3': eps3,
                              'target3': target, 'pv_today_with_dividend': pv, 'cash_irr_pct': irr*100})
out['three_year_weighted_pv'] = sum(p * x['pv_today_with_dividend'] for p, x in zip(probabilities, out['three_year']))

for label, profit10, g in zip(['bear', 'base', 'bull'], profits10, gs):
    pe = exit_pe(g)
    growth = (profit10 / initial_profit) ** (D(1)/10) - 1
    # New equity proceeds fund the forecast capital program; no additional cash windfall.
    profit_attributable_current = profit10 * dilution_factor
    proxy_irr = (profit_attributable_current * pe / mcap) ** (D(1)/10) - 1 + k
    out['ten_year'].append({'case': label, 'profit10_m': profit10,
                            'profit10_current_shareholders_m': profit_attributable_current,
                            'growth_from_core_proxy': growth, 'g': g, 'spread': r-g,
                            'retention': g/roic, 'pe': pe, 'proxy_irr_pct': proxy_irr*100})
out['proxy_expected_irr_pct'] = sum(p * x['proxy_irr_pct'] for p, x in zip(probabilities, out['ten_year']))
out['preferred_option_dilution_discount_pct'] = (1 - future_shares / (future_shares + D(3000000))) * 100
out['atm_60b_illustrative_new_shares_at_anchor'] = D(60000000000) / price

out['entry_discount_to_weighted_pv_pct'] = [(1 - x / out['three_year_weighted_pv']) * 100 for x in [D(450), D(480)]]
out['book_roic_proxy_fy2025_pct'] = D(83276) * D('.83') / (D(217243)+D(58744)-D(81592)) * 100

# Reverse cash DCF: constant growth of actual company FCF, before SBC substitute.
# This is a generous cash proxy; it excludes additional legal and financing deductions.
def reverse_value(growth):
    fcf = D(25126)
    return sum(fcf*(1+growth)**t/(1+r)**t for t in range(1,11)) + fcf*(1+growth)**10*D('1.03')/(r-D('.03'))/(1+r)**10
lo, hi = D('-.2'), D('.6')
for _ in range(200):
    mid = (lo + hi) / 2
    if reverse_value(mid) > mcap:
        hi = mid
    else:
        lo = mid
out['reverse_fcf_growth_pct'] = (lo+hi)/2*100

config = {'Meta': {'roic': float(roic), 'g': [float(x) for x in gs],
                   'p': [float(x) for x in probabilities],
                   'irr10': [float(x['proxy_irr_pct']) for x in out['ten_year']], 'k': float(k)}}
(HERE/'terminal-config.json').write_text(json.dumps(config, indent=2)+'\n')
(HERE/'model-output.json').write_text(json.dumps(jsonable(out), ensure_ascii=False, indent=2)+'\n')
logs = []


def run(tool, arguments):
    cmd = [sys.executable, str(ROOT/'tools'/tool), *[str(x) for x in arguments]]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    logs.append('$ '+' '.join(cmd)+'\n'+result.stdout+result.stderr)


run('financial_rigor.py', ['verify-market-cap', '--price', price, '--shares', shares,
                           '--reported', 1528000000000, '--currency', 'USD'])
for field, values in [
    ('FY2025_revenue', {'Meta_10K': 200966, 'StockAnalysis': 200966, 'Macrotrends_search_snapshot': 200966}),
    ('FY2025_NI', {'Meta_10K': 60458, 'StockAnalysis': 60458, 'Macrotrends_search_snapshot': 60458}),
    ('Q3_cash_securities', {'Meta_10Q': 82449, 'StockAnalysis': 82449}),
    ('Actual_shares', {'SEC_Oct16': int(shares), 'StockAnalysis_rounded': 2560000000}),
    ('TTM_revenue', {'Meta_annual_plus_YTD': 241605, 'StockAnalysis': 241605}),
    ('TTM_NI', {'Meta_annual_plus_YTD': 75249, 'StockAnalysis': 75249}),
    ('TTM_CFO', {'Meta_annual_plus_YTD': 133087, 'StockAnalysis': 133087}),
    ('TTM_FCF_reconciled', {'Meta_company_FCF': 25126, 'SA_28649_less_finance_principal_3523': 25126}),
]:
    run('financial_rigor.py', ['cross-validate', '--field', field, '--values', json.dumps(values), '--unit', 'USD_m_or_shares', '--tolerance', 1])
run('financial_rigor.py', ['verify-valuation', '--price', price, '--eps', '29.33',
                          '--bvps', D(272386)*D(1000000)/shares,
                          '--fcf-per-share', D(25126)*D(1000000)/shares, '--dividend', '2.10',
                          '--revenue-per-share', D(241605)*D(1000000)/shares])
run('financial_rigor.py', ['three-scenario', '--price', price, '--eps', eps_model,
                          '--shares', shares/D(100000000), '--growth', '.20', '.12', '-.05',
                          '--pe', 26, 22, 16, '--years', 3, '--currency', 'USD'])
audit_args = ['audit', '--currency', 'USD', '--r', r, '--roic', roic, '--g', '.01,.03,.04',
              '--rf', rf, '--beta', 1, '--discrete-risks',
              'AI投资回报失败:情景,一般广告竞争:情景,法律本金及利息现金:未建模,新增禁令及罚款:未建模,强制拆分:未建模,算力供电中断:未建模,新增ATM及再融资失败:未建模']
run('terminal_value.py', audit_args)
for row in out['ten_year']:
    run('terminal_value.py', ['pe', '--roic', roic, '--g', row['g'], '--r', r])
    run('terminal_value.py', ['irr', '--profit', row['profit10_current_shareholders_m'],
                            '--mcap', mcap, '--pe', row['pe'], '--years', 10, '--payout', k])
for delta in ['.02', '.01']:
    run('terminal_value.py', ['flip', '--config', HERE/'terminal-config.json', '--name', 'Meta',
                            '--r', r, '--delta', delta, '--currency', 'USD', '--g-shift', 0, '--rf', rf])
run('terminal_value.py', audit_args)
(HERE/'tool-validation.txt').write_text('\n'.join(logs))
print(json.dumps(jsonable(out), ensure_ascii=False, indent=2))
