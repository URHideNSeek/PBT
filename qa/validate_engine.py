"""Reproducible combinatorial checks. Exhaustive singles; finite representative interactions."""
import itertools,json,math,random,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mission import size
from model import F,DEFAULTS,evaluate
BASE=dict(mass_lb=19.5,range_mi=6.,days=.25,good_pct=50.,deadline=24.,checkins=4,tier2_min_day=40.,battery_fraction=.5,good_wh=90.,bad_wh=15.,tier1_w=5.,tier2_w=40.,comms_w=60.,checkin_min=1.,events_day=2.,event_min=1.,wake_wh=1.,reposition_mi=1.,wind=20.,speed=35.,whkg=322.,derate=.9)
GRID={
'mass_lb':[round(8+.1*i,1) for i in range(120)],'range_mi':[.5*(i+1) for i in range(30)],
'days':[i/24 for i in range(1,721)],'good_pct':list(range(101)), 'deadline':list(range(721)),
'checkins':list(range(49)),'tier2_min_day':list(range(1441)), 'battery_fraction':[i/100 for i in range(20,76)],
'wind':[i/100 for i in range(3001)],'speed':[10+i/100 for i in range(5001)],
'whkg':[50+i/100 for i in range(55001)], 'derate':[round(.1+.05*i,2) for i in range(19)]}
for key in BASE:
 if key not in GRID: GRID[key]=sorted(set([0.,.01,BASE[key],100.,1000.]))
LEVELS={k:sorted(set([v[0],BASE[k],v[-1]])) for k,v in GRID.items()}
EXPECTED=['Mass target cannot accommodate','Invalid parameter:','Wind and airspeed','Communications activity exceeds','Invalid mission input']
counts={}; failures=[]; rng=random.Random(1729)
def finite_walk(x):
 if isinstance(x,dict):
  for v in x.values(): finite_walk(v)
 elif isinstance(x,(int,float)) and not isinstance(x,bool): assert math.isfinite(x)
def check(p,stage):
 entry=counts.setdefault(stage,{'cases':0,'accepted':0,'rejected':0,'feasible':0});entry['cases']+=1
 q=p.copy();deadline=q.pop('deadline')
 try:
  r=size(**q)
 except ValueError as e:
  if not any(str(e).startswith(x) for x in EXPECTED): failures.append({'stage':stage,'parameters':p,'error':str(e)})
  entry['rejected']+=1;return
 except Exception as e:
  failures.append({'stage':stage,'parameters':p,'error':repr(e)});return
 entry['accepted']+=1
 try:
  finite_walk(r)
  assert math.isclose(r['battery_kg']+r['nonbattery_kg'],p['mass_lb']*.45359237,rel_tol=1e-10)
  assert r['required_nominal_average_solar_wh']<=r['required_nominal_no_solar_wh']+1e-7
  assert r['end_station_energy_wh']<=r['battery_capacity_wh']+1e-7
  # Independent physical-energy accounting, including rejected/spilled solar.
  capacity=r['battery_capacity_wh']; floor=capacity*r['engineering']['floor']/100
  expected=capacity*r['engineering']['soc']/100-r['insertion_wh']+r['solar_credit_wh']-r['station_energy_wh']-r['spilled_solar_wh']-r['retrieval_wh']-r['engineering']['reserve']-floor
  assert math.isclose(expected,r['energy_margin_average_wh'],abs_tol=1e-6,rel_tol=1e-10)
  assert r['comms_min_day']<=1440
  if not r['station_energy_feasible']: assert r['recovery_charge_h'] is None and r['reposition_charge_h'] is None
  if r['mission_energy_feasible']:
   assert r['insertion_energy_feasible'] and r['station_energy_feasible'] and r['energy_margin_average_wh']>=0
   assert r['recovery_charge_h']==0
   entry['feasible']+=1
  for k in ['recovery_charge_h','reposition_charge_h']:
   if r[k] is not None: assert r[k]>=0
  # Strict JSON serialization must never emit NaN/Infinity.
  json.dumps(r,allow_nan=False)
  assert deadline>=0
 except Exception as e: failures.append({'stage':stage,'parameters':p,'error':repr(e)})

def run():
 started=time.time()
 for key,values in GRID.items():
  for v in values: check(BASE|{key:v},'single-input grid')
 print('Singles complete',flush=True)
 for n in [2,3]:
  for keys in itertools.combinations(BASE,n):
   for values in itertools.product(*(LEVELS[k] for k in keys)): check(BASE|dict(zip(keys,values)),f'{n}-input representative combinations')
  print(f'{n}-input combinations complete',flush=True)
 # All 128 endpoint corners of the seven mission controls.
 core=list(BASE)[:7]
 for values in itertools.product(*( [GRID[k][0],GRID[k][-1]] for k in core)):
  check(BASE|dict(zip(core,values)),'7-control endpoint corners')
 for _ in range(10000): check({k:rng.choice(v) for k,v in GRID.items()},'22-input seeded configurations')
 # Original detailed model: all bounds/default values, including controlled invalid cross-fields.
 detail={'cases':0,'accepted':0,'rejected':0}
 for k,(_,default,lo,hi,_) in F.items():
  for v in sorted(set([lo,default,hi])):
   detail['cases']+=1
   try:
    r=evaluate(DEFAULTS|{k:v});finite_walk(r);json.dumps(r,allow_nan=False);detail['accepted']+=1
   except ValueError: detail['rejected']+=1
   except Exception as e: failures.append({'stage':'detailed model boundaries','parameter':k,'value':v,'error':repr(e)})
 counts['detailed model boundaries']=detail
 report={'coverage':counts,'failures':failures,'elapsed_seconds':round(time.time()-started,2),'seed':1729,
 'limits':['Single-input grid covers every slider tick and integer increment for bounded numeric inputs; bounded numeric controls use their declared increments; typed off-grid decimals and unbounded fields cannot be exhausted.','Pairs/triples cover all parameter subsets at minimum/default/maximum representative levels, not every Cartesian tick.','Full configurations cover seven-control endpoint corners and 10,000 seeded 22-input configurations.','This checks model mathematics and software behavior; physical models remain preliminary.']}
 Path('qa/results.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({'coverage':counts,'failures':len(failures),'elapsed_seconds':report['elapsed_seconds']},indent=2),flush=True)
 if failures: raise SystemExit(1)
if __name__=='__main__':run()
