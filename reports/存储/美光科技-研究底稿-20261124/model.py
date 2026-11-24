"""MU dated research arithmetic; USD billions unless stated. Not a forecast service."""
import contextlib
import importlib.util
import io
import json
from decimal import Decimal as D, getcontext
from pathlib import Path

getcontext().prec = 40
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

rigor = module('financial_rigor')
terminal = module('terminal_value')
price, shares = D('707.70'), D('1.131423212')
mcap = price * shares
cash, debt, deposit = D('73.453'), D('5.179'), D('12.747')
reserve_cash = cash - debt - deposit
log = io.StringIO()
out = {'price':price, 'shares_billion':shares, 'mcap_billion':mcap,
       'net_cash':cash-debt, 'reserve_cash':reserve_cash}

with contextlib.redirect_stdout(log):
    rigor.verify_market_cap(float(price), float(shares*D(10)**9), 800708207133, 'USD')
    for field, a, b in [('FY26收入',133188,133188),('FY26净利润',84969,84969),
                        ('FY26现金及可交易证券',73453,73453),('FY26CFO',89675,89675),
                        ('FY26总现金CapEx',30712,30712),('FY26FCF',58963,58963),
                        ('FY26债务含融资租赁',5179,5179),('10月2日在外股数',1131423212,1131423212)]:
        sources = {'SEC10K':a, 'StockAnalysis':b}
        if '股数' in field: sources={'SEC10K':a,'TMX_QuoteMedia':b}
        rigor.cross_validate(field, sources, '股' if '股数' in field else 'USDm', 1)
    bvps=D('138.378')/shares
    fcfps=D('58.963')/shares
    revps=D('133.188')/shares
    rigor.verify_valuation(float(price),74.33,float(bvps),float(fcfps),.6,float(revps))
    rigor.three_scenario_valuation(707.70,50,float(shares*10),.18,.06,-.20,18,15,10,3,'USD')
    for expr in ['707.70*1131423212','89675-30712','73453-5179-12747',
                 '58963-1333','14761-1254','1084078/1124128357*100',
                 '(355146+607075)/1131423212*100','0.0492+1*0.0508']:
        rigor.exact_calc(expr)

out['valuation'] = {'pe_eps':price/D('74.33'),'pe_aggregate':mcap/D('84.969'),
    'pb':mcap/D('138.378'),'ps':mcap/D('133.188'),
    'pfcf':mcap/D('58.963'),'fcf_yield_pct':D('58.963')/mcap*100,
    'ev_revenue':(mcap-(cash-debt))/D('133.188'),
    'fcf_sbc':D('58.963')-D('1.333'),'pfcf_sbc':mcap/(D('58.963')-D('1.333')),
    'eps_normalization_profit':shares*50,'eps_normalization_margin_pct':shares*50/150*100,
    'rf_pct':D('4.92'),'erp_pct':D('5.08'),
    'tax_cash_gap':D('14.761')-D('1.254'),
    'ceo_proxy_pct':D(1084078)/D(1124128357)*100,
    'ceo_latest_common_pct':D(355146+607075)/(shares*D(10)**9)*100}

years = [2022,2023,2024,2025,2026]
rev=[30758,15540,25111,37378,133188]
ni=[8687,-5833,778,8539,84969]
gm=[13898,-1416,5613,14873,107504]
op=[9702,-5745,1304,9770,99340]
cfo=[15181,1559,8507,17525,89675]
capex=[12067,7676,8386,15857,30712]
out['history']=[{'fy':y,'revenue_m':r,'net_income_m':n,'gross_margin_pct':D(g)/D(r)*100,
    'op_margin_pct':D(o)/D(r)*100,'cfo_m':cf,'gross_capex_m':cx,'fcf_m':cf-cx}
    for y,r,n,g,o,cf,cx in zip(years,rev,ni,gm,op,cfo,capex)]
out['segment_share_pct']={k:D(v)/D('133188')*100 for k,v in
    [('CMBU',43085),('CDBU',37592),('MCBU',36601),('AEBU',15886),('Other',24)]}
out['annual_revenue_growth_pct']=(D('133188')/D('37378')-1)*100
out['annual_earnings_growth_pct']=(D('84969')/D('8539')-1)*100

three=[]
for name,g,pe,prob in [('bear','-.20',10,'.25'),('base','.06',15,'.50'),('bull','.18',18,'.25')]:
    eps=D(50)*(1+D(g))**3
    end=eps*pe
    # Annual $0.60 dividend assumed paid at year ends, not reinvested.
    pv=end/D('1.1')**3+sum(D('.6')/D('1.1')**t for t in range(1,4))
    three.append({'name':name,'g':D(g),'pe':pe,'p':D(prob),'eps_year3':eps,
                  'target_year3':end,'present_value':pv,'capital_return_pct':(end/price-1)*100,
                  'annual_total_return_pct':((end+D('1.8'))/price)**(D(1)/3)*100-100})
out['three_year']=three
out['three_year_weighted_pv']=sum(s['p']*s['present_value'] for s in three)

def irr(flows, end_value):
    low, high=D('-.99'),D('2')
    for _ in range(220):
        rate=(low+high)/2
        npv=sum(f/(1+rate)**t for t,f in enumerate(flows,1))+end_value/(1+rate)**10-mcap
        if npv>0:low=rate
        else:high=rate
    return (low+high)/2*100

specs=[('bear','25','0.01',[60,40,20,10,10,12,14,16,18,20],'.25'),
       ('base','100','0.025',[65,70,55,45,50,55,60,65,70,75],'.50'),
       ('bull','180','0.035',[75,85,90,95,100,105,110,120,130,140],'.25')]
ten=[]
for name,profit,g,flows,p in specs:
    profit,g,p=D(profit),D(g),D(p)
    pe=(1-g/D('.18'))/(D('.10')-g)
    proxy=D(str(terminal.irr_from_terminal(float(profit),float(mcap),float(pe))))*100
    f=[D(v) for v in flows]
    # Net financial assets are reserved against deposits and released only at year 10.
    tv=profit*pe
    pv=sum(x/D('1.1')**t for t,x in enumerate(f,1))+(tv+reserve_cash)/D('1.1')**10
    ten.append({'name':name,'profit2036':profit,'g':g,'p':p,'pe':pe,
                'spread_pp':(D('.10')-g)*100,'fcfe_path':f,'terminal_proxy_irr_pct':proxy,
                'full_cash_irr_pct':irr(f,tv+reserve_cash),'pv_per_share':pv/shares})
out['ten_year']=ten
out['ten_year_weighted_pv']=sum(s['p']*s['pv_per_share'] for s in ten)
out['weighted_full_cash_irr_pct']=sum(s['p']*s['full_cash_irr_pct'] for s in ten)
out['weighted_terminal_proxy_pct']=sum(s['p']*s['terminal_proxy_irr_pct'] for s in ten)
out['full_cash_sensitivity']=[]
for r in map(D,['.08','.09','.10','.11','.12']):
    irrs=[]
    for s in ten:
        pe=(1-s['g']/D('.18'))/(r-s['g'])
        irrs.append(irr(s['fcfe_path'],s['profit2036']*pe+reserve_cash))
    out['full_cash_sensitivity'].append({'r':r,'scenario_irrs':irrs,
        'weighted_irr':sum(s['p']*v for s,v in zip(ten,irrs))})

# Reverse DCF: normalized first-year owner FCFE40B, constant h for years2-10.
lo,hi=D('-.5'),D('.5')
for _ in range(180):
    h=(lo+hi)/2
    f=[D(40)*(1+h)**i for i in range(10)]
    val=sum(x/D('1.1')**t for t,x in enumerate(f,1))+(f[-1]/D('.075')+reserve_cash)/D('1.1')**10
    if val<mcap:lo=h
    else:hi=h
out['reverse_dcf']={'fcfe_year1':40,'growth_year2to10':h,'fcfe_year10':f[-1],
    'terminal_normal_profit':f[-1]/(1-D('.025')/D('.18'))}
out['buy_band_margin_pct']={str(v):(1-D(v)/out['three_year_weighted_pv'])*100 for v in [500,540]}

def encode(value):
    if isinstance(value,D):return str(value)
    raise TypeError(type(value).__name__)
(HERE/'model-output.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=encode)+'\n')
(HERE/'tool-verification.log').write_text(log.getvalue())
config={'Micron':{'roic':.18,'g':[.01,.025,.035],'p':[.25,.5,.25],
    'irr10':[float(s['terminal_proxy_irr_pct']) for s in ten],'k':0}}
(HERE/'terminal-config.json').write_text(json.dumps(config,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['history','full_cash_sensitivity']},ensure_ascii=False,indent=2,default=encode))
