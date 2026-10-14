"""Mission-first inverse sizing using explicit engineering assumptions."""
from math import isfinite
from model import DEFAULTS,evaluate
from perched import simulate, timeline, recharge as chronological_recharge

def size(mass_lb=19.5,range_mi=6.,days=.25,good_pct=50.,checkins=4,tier2_min_day=40.,battery_fraction=.5,good_wh=90.,bad_wh=15.,checkin_min=1.,events_day=2.,event_min=1.,wake_wh=1.,tier1_w=5.,tier2_w=40.,comms_w=60.,reposition_mi=1.,**engineering):
 vals=[mass_lb,range_mi,days,good_pct,battery_fraction,good_wh,bad_wh,checkin_min,events_day,event_min,wake_wh,tier1_w,tier2_w,comms_w,reposition_mi,tier2_min_day]
 if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not isfinite(x) for x in vals) or isinstance(checkins,bool) or not isinstance(checkins,(int,float)) or not isfinite(checkins) or mass_lb<=0 or range_mi<0 or days<=0 or not 0<=good_pct<=100 or not 0<battery_fraction<1 or min(vals[5:])<0 or not 0<=tier2_min_day<=1440 or checkins<0 or checkins!=int(checkins): raise ValueError('Invalid mission input')
 flight_electronics_w=engineering.pop('flight_electronics_w',6.)
 arrival_hour=engineering.pop('arrival_hour',9.)
 charge_limit_w=engineering.pop('charge_limit_w',100.)
 charge_eff=engineering.pop('charge_eff',1.)
 charge_temperature_c=engineering.pop('charge_temperature_c',20.)
 charge_min_c=engineering.pop('charge_min_c',0.)
 charge_max_c=engineering.pop('charge_max_c',45.)
 if not all(isfinite(x) for x in [charge_temperature_c,charge_min_c,charge_max_c]) or charge_min_c>charge_max_c:raise ValueError('Invalid charging temperature limits')
 charging_allowed=charge_min_c<=charge_temperature_c<=charge_max_c
 if not charging_allowed:charge_limit_w=0.
 calculate_recharge=engineering.pop('calculate_recharge',True)
 if not all(isfinite(x) for x in [flight_electronics_w,arrival_hour,charge_limit_w,charge_eff]) or flight_electronics_w<0 or not 0<=arrival_hour<24 or charge_limit_w<0 or not 0<charge_eff<=1:raise ValueError('Invalid flight/charging assumption')
 minimum_other_kg=engineering.pop("minimum_other_kg",0.)
 if not isfinite(minimum_other_kg) or minimum_other_kg<0: raise ValueError("Invalid structure and installation reserve")
 m=mass_lb*.45359237;p=DEFAULTS|engineering
 p.update(battery_kg=m*battery_fraction,other_kg=0.,growth_kg=0.,out_mi=range_mi,back_mi=range_mi,hours=0.,t2_min=0.,radio_min=0.)
 # Fixed nonbattery mass is allocated by the remaining mass; this does not prove packaging.
 remainder=m-sum(p[k] for k in ['battery_kg','propulsion_kg','sensor_kg','compute_kg','comms_kg','solar_kg'])
 if remainder<minimum_other_kg: raise ValueError('Mass target cannot accommodate battery, selected sensors and installation reserves. Reduce allocations or change the mission mass/battery fraction.')
 p['other_kg']=remainder
 p['flight_electronics_w']=flight_electronics_w
 r=evaluate(p)
 if r['mission_wh'] is None: raise ValueError('Wind and airspeed make the selected route infeasible')
 scheduled_min=checkins*checkin_min
 anomaly_min=events_day*event_min
 comms_min=scheduled_min+anomaly_min
 if comms_min>1440: raise ValueError('Communications activity exceeds 24 hours per day')
 # Tier2 power is incremental above continuously scheduled Tier1.
 daily_load=tier1_w*24+tier2_w*tier2_min_day/60+comms_w*comms_min/60
 requested_solar=(good_pct*good_wh+(100-good_pct)*bad_wh)/100
 weather_solar=min(requested_solar,r['solar_peak_w']*12)
 # Solar geometric/electrical potential is independent of the weather-harvest assumption.
 station_energy=daily_load*days+wake_wh
 energy_needed=r['mission_wh']+station_energy
 net=simulate(0.,1e12,24,arrival_hour,daily_load,weather_solar,charge_limit_w=charge_limit_w,charge_eff=charge_eff,inspect_hit=False)['end_wh']
 solar_credit=weather_solar*days
 window=p['derate']*(p['soc']-p['floor'])/100
 required_no_solar=energy_needed/window
 # Solar cannot be spent before insertion or stored above derated capacity.
 out_h=range_mi/1.150779/r['outbound_ground_kt']
 return_h=range_mi/1.150779/r['return_ground_kt']
 auxiliary=r['mission_wh']-p['reserve']-r['flight_w']*(out_h+return_h)
 insertion=r['flight_w']*out_h+auxiliary/2
 retrieval=r['flight_w']*return_h+auxiliary/2
 capacity=p['battery_kg']*p['whkg']*p['derate']
 floor=capacity*p['floor']/100
 arrival_energy=capacity*p['soc']/100-insertion
 # Sleep/report allowance is charged before average stationary harvest.
 after_report=arrival_energy-wake_wh
 recovery_required=retrieval+p['reserve']+floor
 station=simulate(after_report,capacity,days*24,arrival_hour,daily_load,weather_solar,protected=recovery_required,charge_limit_w=charge_limit_w,charge_eff=charge_eff,inspect_hit=calculate_recharge)
 end_energy=station['end_wh'];spilled=station['spilled_wh'];minimum=station['minimum_wh']
 solar_credit=station['harvest_wh']
 insertion_ok=arrival_energy>=floor
 station_ok=insertion_ok and minimum>=floor
 recovery_required=retrieval+p['reserve']+floor
 return_protected=insertion_ok and minimum>=recovery_required
 margin=end_energy-recovery_required
 mission_ok=station_ok and return_protected and margin>=0
 # Exact nominal energy capacity bound for this repeating daylight/load profile.
 _,_,minimum_cumulative,max_drawdown,_,_=timeline(days*24,arrival_hour,daily_load,weather_solar,charge_limit_w,charge_eff)
 required_average=max((insertion+wake_wh+retrieval+p['reserve']-minimum_cumulative)/window,
                      (retrieval+p['reserve']-max_drawdown)/(p['derate']*(1-p['floor']/100)))
 # Reposition follows the outbound track under the same steady wind.
 relocation_wh=r['flight_w']*reposition_mi/1.150779/r['outbound_ground_kt']+auxiliary
 next_return_wh=r['flight_w']*(range_mi+reposition_mi)/1.150779/r['return_ground_kt']+auxiliary/2
 reposition_required=relocation_wh+next_return_wh+p['reserve']+floor
 def recharge(target):
  if not return_protected or not calculate_recharge:return None
  return chronological_recharge(end_energy,capacity,recovery_required,target,(arrival_hour+days*24)%24,daily_load,weather_solar,charge_limit_w=charge_limit_w,charge_eff=charge_eff)
 protected_h=station['first_unprotected_h']
 full_h=recharge(capacity)
 arrival_full_h=chronological_recharge(after_report,capacity,recovery_required,capacity,arrival_hour,daily_load,weather_solar,charge_limit_w=charge_limit_w,charge_eff=charge_eff) if calculate_recharge else None
 return dict(requested_solar_wh_day=requested_solar,solar_profile_capped=requested_solar>weather_solar,charging_allowed=charging_allowed,charge_temperature_c=charge_temperature_c,charge_min_c=charge_min_c,charge_max_c=charge_max_c,flight_electronics_w=flight_electronics_w,arrival_hour=arrival_hour,charge_limit_w=charge_limit_w,charge_eff=charge_eff,energy_model='Separate flight and chronological perched states; 5-minute solar/load steps',recharge_to_full_h=full_h,arrival_to_full_h=arrival_full_h,return_reserve_preserved=return_protected,return_protected_wh=recovery_required,maximum_protected_perched_hours=protected_h,relocation_required_wh=reposition_required,relocation_charge_h=recharge(reposition_required),relocation_flight_wh=relocation_wh,next_perch_return_wh=next_return_wh,relocation_distance_mi=reposition_mi,next_perch_return_distance_mi=range_mi+reposition_mi,insertion_energy_feasible=insertion_ok,station_energy_feasible=station_ok,mission_energy_feasible=mission_ok,battery_capacity_wh=capacity,arrival_energy_wh=arrival_energy,minimum_station_energy_wh=minimum,end_station_energy_wh=end_energy,spilled_solar_wh=spilled,recovery_required_wh=recovery_required,solar_credit_wh=solar_credit,station_energy_wh=station_energy,insertion_wh=insertion,retrieval_wh=retrieval,mass_lb=mass_lb,battery_kg=p['battery_kg'],nonbattery_kg=m-p['battery_kg'],required_nominal_no_solar_wh=required_no_solar,required_nominal_average_solar_wh=required_average,required_installed_whkg=required_average/p['battery_kg'],station_wh_day=daily_load,solar_wh_day=weather_solar,daily_balance_wh=net,energy_margin_average_wh=margin,recovery_charge_h=recharge(recovery_required),reposition_charge_h=recharge(reposition_required),required_energy_neutral_good_day_wh=(daily_load-(1-good_pct/100)*bad_wh)/(good_pct/100) if good_pct else None,flight_w=r['flight_w'],hover_w=r['hover_w'],thrust_per_rotor_kgf=r['thrust_required_kgf'],peak_w=r['peak_w'],comms_min_day=comms_min,scheduled_checkins_day=checkins,anomaly_reports_day=events_day,engineering=p)

# Provisional trade-study assumptions, not measured cell or pack data.
TEMPERATURE_CAPACITY_POINTS=((-20.,.60),(-10.,.75),(0.,.85),(10.,.95),(20.,1.),(40.,1.),(50.,.90))
def temperature_capacity_factor(low_c,high_c):
 """Worst interpolated capacity across the range; assumes cell equals ambient."""
 if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and isfinite(x) for x in (low_c,high_c)) or not -20<=low_c<=high_c<=50:
  raise ValueError('Temperature range must lie within -20 to 50 C')
 def at(t):
  for (a,fa),(b,fb) in zip(TEMPERATURE_CAPACITY_POINTS,TEMPERATURE_CAPACITY_POINTS[1:]):
   if a<=t<=b:return fa+(fb-fa)*(t-a)/(b-a)
 samples=[at(low_c),at(high_c)]+[f for t,f in TEMPERATURE_CAPACITY_POINTS if low_c<=t<=high_c]
 return min(samples)
