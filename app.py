import json
import pandas as pd
import streamlit as st
from mission import size
st.set_page_config(page_title='Mission Trade Study',page_icon='📊',layout='wide')
st.title('Mission Trade Study')
st.caption('Choose the capability to offer. See what engineering must achieve.')
with st.sidebar:
 st.header('Platform & mission')
 mass=st.slider('Flight-ready mass, including payload (lb)',8.,19.9,19.5,.1)
 distance=st.slider('Range per leg (statute miles)',.5,15.,6.,.5)
 hours=st.number_input('Time on target (hours)',min_value=1.,max_value=720.,value=6.,step=1.)
 good=st.slider('Good solar days (%)',0,100,50)
 st.caption(f'{100-good}% bad solar days. Solar mix is an average, not a weather guarantee.')
 deadline=st.number_input('Desired recharge time before next departure (hours)',min_value=0.,max_value=720.,value=24.,step=1.)
 checkins=st.slider('Scheduled communications check-ins per day',0,48,4)
 if checkins==0: st.caption('Anomaly and sleep-transition reports only. These still consume energy.')
 tier2=st.slider('Tier 2 active minutes per day',0,1440,40)
 with st.expander('Advanced engineering assumptions'):
  fraction=st.slider('Battery fraction of flight-ready mass (%)',20,75,50)/100
  good_wh=st.number_input('Battery-delivered harvest on good day (Wh)',min_value=0.,value=90.)
  bad_wh=st.number_input('Battery-delivered harvest on bad day (Wh)',min_value=0.,value=15.)
  t1=st.number_input('Average Tier 1 + housekeeping power (W)',min_value=0.,value=5.)
  t2=st.number_input('Incremental Tier 2 power (W)',min_value=0.,value=40.)
  radio=st.number_input('Active communications power (W)',min_value=0.,value=60.)
  duration=st.number_input('Minutes per scheduled check-in',min_value=0.,value=1.)
  events=st.number_input('Anomaly reports per day',min_value=0.,value=2.)
  event_duration=st.number_input('Minutes per anomaly report',min_value=0.,value=1.)
  sleep=st.number_input('Sleep-transition communication allowance per mission (Wh)',min_value=0.,value=1.)
  hop=st.number_input('Reposition distance (statute miles)',min_value=0.,value=1.)
  wind=st.slider('Steady wind (kt)',0.,30.,20.)
  speed=st.slider('True cruise airspeed (kt)',10.,60.,35.)
  whkg=st.number_input('Assumed installed battery Wh/kg',min_value=50.,max_value=600.,value=322.)
  derate=st.slider('Temperature/aging capacity factor',.1,1.,.9,.05)
  thermal_unused=st.caption('Detailed flight/prop/solar assumptions remain in advanced_app.py. This mission view is an inverse sizing study, not full feasibility verification.')
try:
 r=size(mass_lb=mass,range_mi=distance,days=hours/24,good_pct=good,checkins=checkins,tier2_min_day=tier2,battery_fraction=fraction,good_wh=good_wh,bad_wh=bad_wh,checkin_min=duration,events_day=events,event_min=event_duration,wake_wh=sleep,tier1_w=t1,tier2_w=t2,comms_w=radio,reposition_mi=hop,wind=wind,speed=speed,whkg=whkg,derate=derate)
except ValueError as e: st.error(str(e)); st.stop()
a,b,c=st.columns(3)
a.metric('Required nominal battery · no solar credit',f"{r['required_nominal_no_solar_wh']:.0f} Wh")
b.metric('Required battery · average solar credit',f"{r['required_nominal_average_solar_wh']:.0f} Wh")
c.metric('Station daily energy balance',f"{r['daily_balance_wh']:+.0f} Wh/day")
st.subheader('Design specifications engineering must meet')
rows=[('Installed battery mass allocation',r['battery_kg'],'kg'),('Nonbattery mass allocation',r['nonbattery_kg'],'kg'),('Required installed battery specific energy with average solar',r['required_installed_whkg'],'Wh/kg'),('Continuous thrust required per rotor',r['thrust_per_rotor_kgf'],'kgf'),('Estimated hover power',r['hover_w'],'W'),('Estimated cruise power',r['flight_w'],'W'),('Estimated maneuver electrical power',r['peak_w'],'W'),('Station consumption',r['station_wh_day'],'Wh/day'),('Average solar harvest',r['solar_wh_day'],'Wh/day'),('Good-day harvest needed for energy-neutral station operation',r['required_energy_neutral_good_day_wh'],'Wh/day'),('Scheduled + anomaly communications duration',r['comms_min_day'],'min/day')]
st.dataframe(pd.DataFrame([{'Specification':k,'Value':'Not applicable at 0% good days' if v is None else f'{v:.2f}','Units':u} for k,v,u in rows]),hide_index=True,width='stretch')
st.subheader('Ready to move?')
for label,key in [('Recover to operator','recovery_charge_h'),('Reposition to next perch','reposition_charge_h')]:
 v=r[key]
 if v is None: st.warning(label+': cannot recharge to readiness under the assumed battery capacity and continuing station schedule.')
 else:
  st.write(f'**{label}: {v:.1f} hours recharge** after the selected time on target.')
  if v>deadline: st.warning(f'Exceeds the {deadline:g}-hour desired recharge time.')
st.caption('Recharge uses average net solar after continuing sensing/communications loads. Zero means energy-ready, not departure clearance. Negative daily balance can be tolerated for a finite mission but is not indefinite persistence.')
if not r['insertion_energy_feasible']: st.error('Insertion needs more energy than the assumed battery can provide before solar charging.')
if not r['station_energy_feasible']: st.error('Battery crosses the analysis minimum during the station mission. Recharge readiness is not claimed.')
if not r['mission_energy_feasible']: st.error(f"Assumed battery does not close the mission. Recovery energy margin: {r['energy_margin_average_wh']:.0f} Wh.")
else: st.success(f"Average-solar energy margin: {r['energy_margin_average_wh']:.0f} Wh. Weather sequencing and other closure checks still require review.")
st.info('Mass includes payload. Battery mass and flight power remain coupled. The solar mix averages good and bad days; a string of bad days may fail even when the average passes. Six-hour missions use fractional-day schedules. Tier 2/radio loads are incremental. No supplier capabilities are assumed.')
if 'mission_scenarios' not in st.session_state: st.session_state.mission_scenarios=[]
name=st.text_input('Trade name','Mission concept')
record={'name':name,'mission':{'mass_lb':mass,'range_mi':distance,'hours':hours,'good_solar_pct':good,'checkins_day':checkins,'tier2_min_day':tier2,'desired_recharge_h':deadline,'battery_fraction':fraction,'good_wh_day':good_wh,'bad_wh_day':bad_wh,'tier1_w':t1,'tier2_w':t2,'comms_w':radio,'checkin_min':duration,'anomaly_reports_day':events,'event_min':event_duration,'sleep_report_wh':sleep,'reposition_mi':hop},'results':{k:v for k,v in r.items() if k!='engineering'},'engineering':r['engineering']}
if st.button('Save mission to comparison'):
 st.session_state.mission_scenarios=[x for x in st.session_state.mission_scenarios if x['name']!=name]+[record]
if st.session_state.mission_scenarios:
 frame=pd.DataFrame([{'Trade':x['name'],**x['mission'],'Required battery Wh':x['results']['required_nominal_average_solar_wh'],'Recovery recharge h':x['results']['recovery_charge_h'],'Reposition recharge h':x['results']['reposition_charge_h']} for x in st.session_state.mission_scenarios]).set_index('Trade')
 st.dataframe(frame.T,width='stretch')
 st.download_button('Download mission comparison CSV',frame.to_csv(),file_name='mission_trades.csv')
st.download_button('Download current mission and engineering assumptions',json.dumps(record,indent=2),file_name='mission_trade.json')
