"""Derive minimum closing aircraft/battery allocation for a selected payload."""
from math import isfinite
from mission import size
from model import DEFAULTS

def flight_inputs(engineering):
 inputs=engineering.copy()
 inputs.update(manage_sleep=False,tier1_w=0.,tier2_w=0.,comms_w=0.,wake_wh=1.,good_wh=0.,bad_wh=0.,checkins=0,events_day=0)
 return inputs

def flight_checks(r,energy=True):
 p=r['engineering'];battery=r['battery_kg']
 return {'Insertion and recovery energy':r['mission_energy_feasible'] if energy else r['insertion_energy_feasible'],
         'Propeller diameter':p['prop']<p['prop_max'],'Solar diameter':p['solar']<p['solar_max'],
         'Continuous rotor thrust':r['thrust_per_rotor_kgf']<=p['thrust'],
         'Continuous battery power':max(r['hover_w'],r['flight_w'])<=battery*p['wkg'],
         'Peak battery power':r['peak_w']<=battery*p['peak_wkg']}

def size_payload(payload_kg,range_mi,hours,*,hardware_kg,sensor_kg=0.,**engineering):
 if not all(isfinite(v) for v in [payload_kg,range_mi,hours,hardware_kg,sensor_kg]) or min(payload_kg,range_mi,sensor_kg)<0 or min(hours,hardware_kg)<=0:raise ValueError('Invalid payload-sizing input')
 if payload_kg+1e-9<sensor_kg:return None
 engineering=dict(engineering);engineering.pop('battery_fraction',None)
 maximum=(engineering.get('mass_max',DEFAULTS['mass_max'])*.45359237-hardware_kg-payload_kg)*.999999
 if maximum<=0:return None
 def candidate(battery,full=False):
  inputs=engineering.copy()
  if not full:inputs=flight_inputs(engineering)
  else:inputs.setdefault('manage_sleep',True)
  gross=hardware_kg+payload_kg+battery
  try:r=size(mass_lb=gross/.45359237,range_mi=range_mi,days=hours/24 if full else 1./24,battery_fraction=battery/gross,sensor_kg=payload_kg,reposition_mi=range_mi,calculate_recharge=full,**inputs)
  except ValueError:return None
  p=r['engineering']
  if not all(flight_checks(r,energy=not full).values()):return None
  r['additional_payload_kg']=max(0.,payload_kg-sensor_kg)
  return {'Range per leg (mi)':range_mi,'Payload mass (lb)':payload_kg/.45359237,'Additional payload (kg)':r['additional_payload_kg'],'Battery fraction':battery/gross,'result':r}
 previous=.001
 # Scan rather than assuming feasibility is monotonic over the entire mass range.
 for i in range(1,201):
  battery=.001+(maximum-.001)*i/200
  found=candidate(battery)
  if found:
   lo,hi=previous,battery
   for _ in range(22):
    mid=(lo+hi)/2
    if candidate(mid):hi=mid
    else:lo=mid
   return candidate(hi,True)
  previous=battery
 return None

def payload_mass_curve(payload_kg,hours,**kwargs):
 return [size_payload(payload_kg,i*.25,hours,**kwargs) for i in range(41)]


def diagnose_payload(payload_kg,range_mi,*,hardware_kg,sensor_kg=0.,**engineering):
 """Sample the same flight-only constraints; explain failure without relaxing limits."""
 if payload_kg+1e-9<sensor_kg:return {'reason':'Selected sensors exceed payload allowance','sensor_kg':sensor_kg,'payload_kg':payload_kg}
 maximum=engineering.get('mass_max',DEFAULTS['mass_max'])*.45359237
 budget=maximum-hardware_kg-payload_kg
 if budget<=0:return {'reason':'Hardware and payload exceed the aircraft mass limit','mass_limit_kg':maximum,'hardware_kg':hardware_kg,'payload_kg':payload_kg}
 inputs=flight_inputs(engineering);inputs.pop('battery_fraction',None)
 best=None;errors=set()
 for i in range(1,401):
  battery=budget*i/401;gross=hardware_kg+payload_kg+battery
  try:r=size(mass_lb=gross/.45359237,range_mi=range_mi,days=1/24,battery_fraction=battery/gross,sensor_kg=payload_kg,reposition_mi=range_mi,calculate_recharge=False,**inputs)
  except ValueError as e:errors.add(str(e));continue
  checks=flight_checks(r)
  rank=(sum(not passed for name,passed in checks.items() if name!='Insertion and recovery energy'),-r['energy_margin_average_wh'])
  if best is None or rank<best[0]:best=(rank,r,checks)
 if best is None:return {'reason':'No valid flight configuration could be evaluated','details':sorted(errors),'mass_limit_kg':maximum}
 _,r,checks=best;p=r['engineering']
 failed=[name for name,passed in checks.items() if not passed]
 return {'reason':', '.join(failed) if failed else 'Sampled candidate is feasible; sizing search needs review',
         'checks':checks,'mass_limit_kg':maximum,'sampled_aircraft_kg':r['mass_lb']*.45359237,'sampled_battery_kg':r['battery_kg'],
         'usable_flight_energy_wh':r['battery_capacity_wh']*(p['soc']-p['floor'])/100,
         'required_flight_energy_wh':r['insertion_wh']+r['retrieval_wh']+p['reserve']+1.,
         'energy_margin_wh':r['energy_margin_average_wh'],'peak_power_w':r['peak_w'],'available_peak_w':r['battery_kg']*p['peak_wkg'],
         'planning_headwind_m_s':p['wind']*.514444444444,'cruise_speed_m_s':p['speed']*.514444444444,
         'sampling_note':'Best sampled energy margin among configurations with the fewest non-energy failures; not a certified optimizer.'}
