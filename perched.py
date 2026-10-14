"""Chronological DC-bus energy accounting, daylight-only solar and protected return.
Daily sensing/report energy is spread uniformly; burst power is checked separately.
Solar profile is an explicit 06:00–18:00 boxcar, not a weather forecast.
"""
from functools import lru_cache
from math import ceil

@lru_cache(maxsize=64)
def timeline(hours,arrival,daily_load,harvest_day,charge_limit_w,charge_eff):
 steps=max(1,ceil(hours*12));dt=hours/steps
 total=maximum=minimum=drawdown=harvest=0.;rows=[]
 for i in range(steps):
  clock=(arrival+(i+.5)*dt)%24
  solar=harvest_day/12 if 6<=clock<18 else 0.
  # Solar is DC-bus output; only net surplus passes through the battery charger.
  net=solar-daily_load/24
  delta=(min(net,charge_limit_w)*charge_eff if net>0 else net)*dt
  harvest+=solar*dt;total+=delta;maximum=max(maximum,total);minimum=min(minimum,total)
  drawdown=min(drawdown,total-maximum)
  rows.append(((i+1)*dt,total,maximum))
 return total,maximum,minimum,drawdown,harvest,tuple(rows)

def simulate(initial,capacity,hours,arrival,daily_load,harvest_day,*,protected=0.,charge_limit_w=100.,charge_eff=1.,target=None,inspect_hit=True):
 total,maximum,minimum,drawdown,harvest,rows=timeline(hours,arrival,daily_load,harvest_day,charge_limit_w,charge_eff)
 end=initial+total-max(0.,initial+maximum-capacity)
 lowest=min(initial+minimum,capacity+drawdown,initial)
 spill=max(0.,initial+maximum-capacity)
 hit=None;first_target=0. if target is not None and initial>=target else None
 if (inspect_hit and lowest<protected) or target is not None:
  for t,cum,peak in rows:
   energy=initial+cum-max(0.,initial+peak-capacity)
   if hit is None and energy<protected:hit=max(0.,t-hours/max(1,len(rows)))
   if first_target is None and target is not None and energy>=target-1e-7:first_target=t
 return {'end_wh':end,'minimum_wh':lowest,'harvest_wh':harvest,'spilled_wh':spill,'first_unprotected_h':hit,'target_h':first_target}

def recharge(initial,capacity,protected,target,arrival,daily_load,harvest_day,**kwargs):
 if initial<protected-1e-7 or target>capacity+1e-7:return None
 if initial>=target-1e-7:return 0.
 result=simulate(initial,capacity,24*30,arrival,daily_load,harvest_day,protected=protected,target=target,**kwargs)
 ready=result['target_h'];failure=result['first_unprotected_h']
 return ready if ready is not None and (failure is None or ready<failure) else None
