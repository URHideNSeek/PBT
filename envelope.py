"""Conditional mass/range envelope; mission activities follow the selected schedule."""
from mission import size

def maximum_range(mass_lb, hours, *, nonbattery_kg=4.35, good_pct=100.,checkins=1,tier2_min_day=1.,min_range=.5,max_range=15.,recharge_limit_h=1.,**engineering):
 if min(hours,min_range)<=0 or min(good_pct,checkins,tier2_min_day,recharge_limit_h)<0: raise ValueError('Invalid envelope mission selections')
 if max_range<min_range or nonbattery_kg<=0: raise ValueError('Invalid envelope bounds')
 mass_kg=mass_lb*.45359237
 fraction=(mass_kg-nonbattery_kg)/mass_kg
 if not .2<=fraction<=.75: return None
 def feasible(distance):
  try:r=size(mass_lb=mass_lb,range_mi=distance,days=hours/24,good_pct=good_pct,checkins=checkins,tier2_min_day=tier2_min_day,battery_fraction=fraction,**engineering)
  except ValueError:return False
  p=r['engineering']
  return (mass_lb<p['mass_max'] and p['prop']<p['prop_max'] and p['solar']<p['solar_max'] and r['mission_energy_feasible'] and r['thrust_per_rotor_kgf']<=p['thrust'] and max(r['hover_w'],r['flight_w'])<=r['battery_kg']*p['wkg'] and r['peak_w']<=r['battery_kg']*p['peak_wkg'] and r['recovery_charge_h'] is not None and r['recovery_charge_h']<=recharge_limit_h)
 if not feasible(min_range):return None
 if feasible(max_range):return max_range
 lo,hi=min_range,max_range
 for _ in range(24):
  mid=(lo+hi)/2
  if feasible(mid):lo=mid
  else:hi=mid
 return lo

def curve(hours,**kwargs):
 return [{'Mass lb':round(8+i*.1,1),'Max range per leg mi':maximum_range(round(8+i*.1,1),hours,**kwargs)} for i in range(120)]


def payload_boundary(range_mi,hours,*,mass_lb,nonbattery_kg,sensor_kg=0.,**engineering):
 """Max total mission payload; remaining mass buys battery. Extra payload is unpowered."""
 gross=mass_lb*.45359237
 minimum_other=engineering.get('minimum_other_kg',0.)
 high=gross*.8-nonbattery_kg
 if high<0:return None
 def evaluate(extra):
  fraction=(gross-nonbattery_kg-extra)/gross
  if not .2-1e-9<=fraction<=.75+1e-9:return None
  try:r=size(mass_lb=mass_lb,range_mi=range_mi,days=hours/24,battery_fraction=fraction,sensor_kg=sensor_kg+extra,reposition_mi=range_mi,**engineering)
  except ValueError:return None
  p=r['engineering']
  ok=r['mission_energy_feasible'] and mass_lb<p['mass_max'] and p['prop']<p['prop_max'] and p['solar']<p['solar_max'] and r['thrust_per_rotor_kgf']<=p['thrust'] and max(r['hover_w'],r['flight_w'])<=r['battery_kg']*p['wkg'] and r['peak_w']<=r['battery_kg']*p['peak_wkg']
  if not ok:return None
  return {'Range per leg (mi)':range_mi,'Payload mass (lb)':(sensor_kg+extra)/.45359237,'Additional payload (kg)':extra,'Battery fraction':fraction,'result':r}
 if evaluate(0) is None:return None
 lo=0.;hi=high
 if evaluate(hi) is not None:lo=hi
 else:
  for _ in range(24):
   mid=(lo+hi)/2
   if evaluate(mid) is not None:lo=mid
   else:hi=mid
 return evaluate(lo)

def payload_curve(hours,**kwargs):
 return [payload_boundary(i*.25,hours,**kwargs) for i in range(41)]
