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

def sensor_node(initial,capacity,hours,arrival,active_day,harvest_day,*,protected,sleep_w=.2,wake_margin_wh=5.,sleep_margin_wh=3.,start_asleep=False,charge_limit_w=100.,charge_eff=1.):
 if sleep_w<0 or sleep_margin_wh<0 or wake_margin_wh<=sleep_margin_wh:raise ValueError('Wake margin must exceed nonnegative sleep margin')
 from math import isfinite
 if not all(isfinite(x) for x in [sleep_w,wake_margin_wh,sleep_margin_wh]):raise ValueError('Invalid sleep assumptions')
 steps=max(1,ceil(hours*12));dt=hours/steps
 energy=minimum=initial;harvest=spill=used=sleep_hours=0.;hit=None;asleep=start_asleep;rows=[]
 wake=protected+wake_margin_wh;low=protected+sleep_margin_wh
 for i in range(steps):
  clock=(arrival+(i+.5)*dt)%24
  solar=harvest_day/12 if 6<=clock<18 else 0.
  if asleep and energy>=wake:asleep=False
  if not asleep and energy+(solar-active_day/24)*dt<low:asleep=True
  load=sleep_w if asleep else active_day/24
  net=solar-load
  delta=(min(net,charge_limit_w)*charge_eff if net>0 else net)*dt
  next_energy=energy+delta
  if next_energy<protected-1e-7:
   hit=i*dt
   rows.append({'Perched hour':i*dt,'Battery energy (Wh)':energy,'Protected return energy (Wh)':protected,'State':'Recovery required'})
   break
  spill+=max(0.,next_energy-capacity);energy=min(capacity,next_energy)
  minimum=min(minimum,energy);harvest+=solar*dt;used+=load*dt
  if asleep:sleep_hours+=dt
  if hit is None and energy<protected-1e-7:hit=i*dt
  rows.append({'Perched hour':(i+1)*dt,'Battery energy (Wh)':energy,'Protected return energy (Wh)':protected,'State':'Sleep' if asleep else 'Active'})
 return {'end_wh':energy,'minimum_wh':minimum,'harvest_wh':harvest,'spilled_wh':spill,'first_unprotected_h':hit,'sleep_hours':sleep_hours,'consumed_wh':used,'wake_threshold_wh':wake,'sleep_threshold_wh':low,'rows':rows}
