"""Derive minimum closing aircraft/battery allocation for a selected payload."""
from math import isfinite
from mission import size
from model import DEFAULTS

def size_payload(payload_kg,range_mi,hours,*,hardware_kg,sensor_kg=0.,**engineering):
 if not all(isfinite(v) for v in [payload_kg,range_mi,hours,hardware_kg,sensor_kg]) or min(payload_kg,range_mi,sensor_kg)<0 or min(hours,hardware_kg)<=0:raise ValueError('Invalid payload-sizing input')
 if payload_kg+1e-9<sensor_kg:return None
 engineering=dict(engineering);engineering.pop('battery_fraction',None)
 maximum=(engineering.get('mass_max',DEFAULTS['mass_max'])*.45359237-hardware_kg-payload_kg)*.999999
 if maximum<=0:return None
 def candidate(battery):
  gross=hardware_kg+payload_kg+battery
  try:r=size(mass_lb=gross/.45359237,range_mi=range_mi,days=hours/24,battery_fraction=battery/gross,sensor_kg=payload_kg,reposition_mi=range_mi,**engineering)
  except ValueError:return None
  p=r['engineering']
  if not (r['mission_energy_feasible'] and p['prop']<p['prop_max'] and p['solar']<p['solar_max'] and r['thrust_per_rotor_kgf']<=p['thrust'] and max(r['hover_w'],r['flight_w'])<=battery*p['wkg'] and r['peak_w']<=battery*p['peak_wkg']):return None
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
   return candidate(hi)
  previous=battery
 return None

def payload_mass_curve(payload_kg,hours,**kwargs):
 return [size_payload(payload_kg,i*.25,hours,**kwargs) for i in range(41)]
