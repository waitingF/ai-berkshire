"""JD 2026-11-24 reproducible arithmetic; CNY million unless stated.
No source texts, credentials, or external requests are stored here.
"""
from decimal import Decimal, getcontext
from pathlib import Path
import sys, json, subprocess, importlib.util, contextlib, io
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from financial_rigor import exact
from terminal_value import exit_pe,irr_from_terminal
getcontext().prec=40
D=exact
OUT=Path(__file__).parent
M={}
def put(k,v):M[k]=v;return v
price=D('97.05');fx=D('0.85587');usd=D('6.7111');shares=D('2691')
p=put('price_cny',price*fx)
mc=put('market_cap_cny_m',p*shares)
put('market_cap_hkd_m',price*shares)
put('market_cap_usd_m',mc/usd)
put('implied_ads_usd',p*2/usd)
put('vendor_mcap_difference_pct',{v:(D(v)/M['market_cap_hkd_m']-1)*100 for v in ['267070','273520']})
put('latest_segment_revenue_growth_pct',[(D(v)/D(prior)-1)*100 for v,prior in [('257966','250577'),('63953','55084'),('7831','15592')]])
ni=put('ttm_attributable_net_income',D('19631')-D('22344')+D('18734'))
rev=put('ttm_revenue',D('1309085')-D('956801')+D('971688'))
op=put('ttm_operating_income',D('2774')-D('8623')+D('13508'))
eps=put('eps_snapshot',ni/shares)
put('sum_quarterly_diluted_ads_eps',D('-2.07')+D('3.54')+D('5.01')+D('4.59'))
cash=put('cash_sti_ex_restricted',D('82637')+D('121860'))
debt=put('interest_bearing_debt',sum(map(D,['7226','13422','16535','36484'])))
lease=put('lease_liabilities',D('10648')+D('26222'))
net=put('net_cash_ex_restricted_ex_leases',cash-debt)
put('net_cash_ex_restricted_incl_leases',net-lease)
put('gross_incl_restricted',cash+D('10166'))
put('ceconomy_consideration_cny_m',D('1335')*D('7.3008'))
put('net_cash_after_deal_static_illustration',net-M['ceconomy_consideration_cny_m'])
put('ap_decline_qoq',D('197596')-D('228961'))
put('ap_above_yearend',D('197596')-D('188379'))
put('inventory_growth_ytd_pct',(D('116166')/D('95428')-1)*100)
put('new_loss_qoq_improvement_pct',(D('9854')-D('9642'))/D('9854')*100)
put('new_loss_yoy_improvement_pct',(D('15736')-D('9642'))/D('15736')*100)
put('q3_revenue_growth_pct',(D('309593')/D('299059')-1)*100)
put('q3_net_profit_growth_pct',(D('6503')/D('5276')-1)*100)
put('ttm_fcf_net_capex_before_receivables',D('40444')-D('20898'))
put('ttm_fcf_company',D('40444')-D('20898')-D('743'))
put('9m_fcf_company',D('19565')-D('16114')-D('1958'))
put('q3_fcf_company',D('-18708')-D('5531')+D('378'))
put('ttm_non_gaap',D('27032')-D('25948')+D('24636'))
put('pe_current_share_basis',mc/ni)
put('pe_fy25',mc/D('19631'))
put('pe_nongaap',mc/M['ttm_non_gaap'])
put('pb_attributable',mc/D('224843'))
put('ps',mc/rev)
put('fcf_yield_company_pct',M['ttm_fcf_company']/mc*100)
put('ev_revenue_diagnostic_with_nci',(mc+D('64448')+debt-cash)/rev)
div=D('0.5')*usd
put('annual_dividend_assumption_cny_ordinary',div)
put('dividend_yield_pct',div/p*100)
put('fcf_company_vs_dividend_proxy',M['ttm_fcf_company']/(div*shares))
# Equity earnings already include subsidiary attribution and cash interest: never add cash/sub values again.
scenarios=[]
for name,prob,g,pe,annual_div in [('悲观','.25','-.10','8','1'),('基准','.50','.20','12',str(div)),('乐观','.25','.35','15',str(div))]:
 future=eps*(1+D(g))**3
 end=future*D(pe)
 divpv=sum((D(annual_div)/(1+D('.08'))**t for t in range(1,4)),D(0))
 pv=end/(1+D('.08'))**3+divpv
 scenarios.append(dict(name=name,p=prob,g=g,pe=pe,eps=future,profit=future*shares,terminal_cny=end,terminal_hkd=end/fx,pv_hkd=pv/fx,pv_cny=pv,div_pv_cny=divpv,total_return_pct=((end+D(annual_div)*3)/p-1)*100))
put('three_year',scenarios)
weighted=sum((D(x['p'])*x['pv_hkd'] for x in scenarios),D(0))
put('three_year_weighted_pv_hkd',weighted)
put('three_year_margin25_buyline_hkd',weighted*D('.75'))
put('base_pv_with_10pct_extra_dilution_hkd',scenarios[1]['pv_hkd']/D('1.1'))
put('implied_2029_earnings_cny_m_at_12pe_after_div', (mc-sum((div*shares/(1+D('.08'))**t for t in range(1,4)),D(0)))*(1+D('.08'))**3/D('12'))
put('zero_growth_cash_required_cny_m',mc*D('.08'))
put('bands_usd_ads', {str(x):D(str(x))*fx*2/usd for x in [85,93,140]})
# Ten-year terminal pressure: k=3% is dividend minus dilution assumption, excludes buybacks.
roic=.12;gs=[0,.015,.02];probs=[.25,.5,.25];profits=[8000,32000,60000];k=.03
anchors=[]; rows=[]
def cash_irr(terminal,initial,yield_):
 lo=D('-.99');hi=D('2');coupon=initial*D(str(yield_))
 for _ in range(220):
  mid=(lo+hi)/2
  pv=sum((coupon/(1+mid)**t for t in range(1,11)),D(0))+terminal/(1+mid)**10
  if pv>initial:lo=mid
  else:hi=mid
 return (lo+hi)/2
for name,g,pr in zip(['悲观','基准','乐观'],gs,profits):
 pe10=exit_pe(roic,g,.10)[0]
 anchors.append(irr_from_terminal(pr,float(mc),pe10,payout=k)*100)
 pe8=exit_pe(roic,g,.08)[0]
 rows.append(dict(name=name,profit=pr,g=g,pe=pe8,spread=.08-g,tool_approx_irr_pct=irr_from_terminal(pr,float(mc),pe8,payout=k)*100,constant_cash_irr_pct=cash_irr(D(str(pr))*D(str(pe8)),mc,k)*100))
put('ten_year',rows)
cash_sensitivity=[]
for rate in [.06,.07,.08,.09,.10]:
 vals=[cash_irr(D(str(pr))*D(str(exit_pe(roic,g,rate)[0])),mc,k)*100 for g,pr in zip(gs,profits)]
 cash_sensitivity.append(dict(r=rate,weighted_cash_irr_pct=sum((D(str(pp))*vv for pp,vv in zip(probs,vals)),D(0))))
put('cash_irr_sensitivity',cash_sensitivity)
put('ten_year_cash_irr_weighted_pct',sum((D(str(p0))*r['constant_cash_irr_pct'] for p0,r in zip(probs,rows)),D(0)))
config={'京东集团':{'roic':roic,'g':gs,'p':probs,'irr10':anchors,'k':k}}
(OUT/'terminal-config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
def encode(v):
 if isinstance(v,Decimal):return str(v)
 raise TypeError
(OUT/'results.json').write_text(json.dumps(M,default=encode,ensure_ascii=False,indent=2)+'\n')
# All standard checks retain real CLI output.
def run(args):
 p0=subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True)
 if p0.returncode:raise RuntimeError(p0.stdout+p0.stderr)
 return '$ '+' '.join(args)+'\n'+p0.stdout+p0.stderr
log=[]
log.append(run(['tools/financial_rigor.py','verify-market-cap','--price','97.05','--shares','2691000000','--reported','261161550000','--currency','HKD']))
log.append(run(['tools/financial_rigor.py','cross-validate','--field','FY2025收入','--values',json.dumps({'IR':1309085,'StockAnalysis':1309085}),'--unit','CNY million','--tolerance','1']))
for field,a,b in [('FY2025归母',19631,19631),('FY2025现金短投不含受限',213232,213232),('TTM归母',16021,16021),('Q3归母',6503,6500),('普通股百万股_第二源ADS四舍五入乘2',2691,2700)]:
 log.append(run(['tools/financial_rigor.py','cross-validate','--field',field,'--values',json.dumps({'IR':a,'StockAnalysis_or_Google':b}),'--unit','million','--tolerance','1']))
log.append(run(['tools/financial_rigor.py','verify-valuation','--price',str(p),'--eps',str(eps),'--bvps',str(D('224843')/shares),'--fcf-per-share',str(M['ttm_fcf_company']/shares),'--dividend',str(div),'--revenue-per-share',str(rev/shares)]))
log.append(run(['tools/financial_rigor.py','three-scenario','--price',str(p),'--eps',str(eps),'--shares','26.91','--growth','.35','.20','-.10','--pe','15','12','8','--years','3','--currency','CNY/ordinary share']))
(OUT/'financial-rigor.log').write_text('\n'.join(log))
risks='外卖持续亏损:情景,欧洲整合失利:情景,监管罚款及劳动成本:情景,VIE失效及中美金融制裁:未建模'
audit=['tools/terminal_value.py','audit','--currency','CNY','--r','.08','--roic','.12','--g','0,.015,.02','--rf','.018','--beta','1','--discrete-risks',risks]
log=[run(audit)]
for g,pr in zip(gs,profits):
 log.append(run(['tools/terminal_value.py','pe','--roic','.12','--g',str(g),'--r','.08']))
 log.append(run(['tools/terminal_value.py','irr','--profit',str(pr),'--mcap',str(mc),'--pe',str(exit_pe(roic,g,.08)[0]),'--years','10','--payout','.03']))
for delta in ['.02','.01']:
 log.append(run(['tools/terminal_value.py','flip','--config',str(OUT.relative_to(ROOT)/'terminal-config.json'),'--name','京东集团','--r','.08','--delta',delta,'--currency','CNY','--g-shift','0','--rf','.018']))
log.append(run(audit))
(OUT/'terminal-value.log').write_text('\n'.join(log))
print(json.dumps(M,default=encode,ensure_ascii=False,indent=2))
