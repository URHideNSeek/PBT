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
 distance=st.slider('Range per leg (statute miles)',0.,10.,6.,.5)
 hours=st.number_input('Time on target (hours)',min_value=1.,max_value=720.,value=6.,step=1.)
 good=st.slider('Good solar days (%)',0,100,50)
 st.caption(f'{100-good}% bad solar days. Solar mix is an average, not a weather guarantee.')
 deadline=st.number_input('Desired recharge time before next departure (hours)',min_value=0.,max_value=720.,value=24.,step=1.)
 checkins=st.slider('Scheduled communications check-ins per day',0,48,4)
 if checkins==0: st.caption('Anomaly and sleep-transition reports only. These still consume energy.')
 tier2=st.slider('Tier 2 active minutes per day',0,360,40)

mission_tab,sizing_tab=st.tabs(['Mission & Envelope','Engineering Sizing'])
with sizing_tab:
 with st.expander('Engineering model assumptions (not mission requirements)'):
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
  ct=st.number_input('Assumed propeller thrust coefficient CT',min_value=.01,max_value=.3,value=.10,step=.01)
  nominal_v=st.number_input('Assumed nominal battery voltage (V)',min_value=18.,max_value=60.,value=24.,step=1.)

with mission_tab:

 st.divider()
 st.subheader('Mass envelope')
 st.caption('Maximum achievable range per leg versus flight-ready mass, for several times on target. All mission activities remain nonzero.')
 ec1,ec2,ec3=st.columns(3)
 env_good=ec1.slider('Envelope good-solar days (%)',1,100,100,key='env_good')
 env_check=ec2.number_input('Envelope check-ins per day',min_value=1,max_value=48,value=1,key='env_check')
 env_t2=ec3.number_input('Envelope Tier 2 minutes per day',min_value=1,max_value=360,value=1,key='env_t2')
 env_deadline=st.number_input('Envelope recharge deadline (hours)',min_value=1.,max_value=720.,value=1.,step=1.,key='env_deadline')
 st.caption('This envelope uses the current Advanced power, wind and battery assumptions. It allocates remaining mass to battery after reserving 4.35 kg for all nonbattery equipment. Lower activity defaults show an optimistic boundary, not a guaranteed operating envelope.')
 if st.button('Calculate mass envelope'):
  from envelope import curve
  lines={}
  for target_h in [1,6,24,72]:
   points=curve(target_h,good_pct=env_good,checkins=env_check,tier2_min_day=env_t2,recharge_limit_h=env_deadline,good_wh=good_wh,bad_wh=bad_wh,checkin_min=duration,events_day=events,event_min=event_duration,wake_wh=sleep,tier1_w=t1,tier2_w=t2,comms_w=radio,reposition_mi=hop,wind=wind,speed=speed,whkg=whkg,derate=derate)
   lines[f'{target_h} hours on target']=[x['Max range per leg mi'] for x in points]
  frame=pd.DataFrame(lines,index=[x['Mass lb'] for x in points]);frame.index.name='Flight-ready mass (lb)'
  st.session_state['envelope_result']={'frame':frame,'settings':{'good_solar_pct':env_good,'checkins_day':env_check,'tier2_min_day':env_t2,'wind_kt':wind,'airspeed_kt':speed,'battery_whkg':whkg,'capacity_factor':derate,'nonbattery_kg':4.35,'recharge_limit_h':env_deadline},'model_inputs':dict(good_pct=env_good,checkins=env_check,tier2_min_day=env_t2,good_wh=good_wh,bad_wh=bad_wh,checkin_min=duration,events_day=events,event_min=event_duration,wake_wh=sleep,tier1_w=t1,tier2_w=t2,comms_w=radio,reposition_mi=hop,wind=wind,speed=speed,whkg=whkg,derate=derate)}
 if 'envelope_result' in st.session_state:
  saved=st.session_state['envelope_result']
  st.line_chart(saved['frame'],x_label='Flight-ready mass (lb)',y_label='Maximum range per leg (statute miles)')
  st.caption('Showing the last calculated envelope. Recalculate after changing any input. Each curve is a conditional boundary; lower range down to 0.5 mile is energy-feasible under those assumptions. Missing points are infeasible. Range is capped at the 15-mile search limit.')
  st.json(saved['settings'],expanded=False)
  st.download_button('Download envelope CSV',saved['frame'].to_csv(),file_name='mass_envelope.csv')
try:
 r=size(mass_lb=mass,range_mi=distance,days=hours/24,good_pct=good,checkins=checkins,tier2_min_day=tier2,battery_fraction=fraction,good_wh=good_wh,bad_wh=bad_wh,checkin_min=duration,events_day=events,event_min=event_duration,wake_wh=sleep,tier1_w=t1,tier2_w=t2,comms_w=radio,reposition_mi=hop,wind=wind,speed=speed,whkg=whkg,derate=derate)
except ValueError as e: st.error(str(e)); st.stop()
with mission_tab:

 a,b,c=st.columns(3)
 a.metric('Required nominal battery · no solar credit',f"{r['required_nominal_no_solar_wh']:.0f} Wh")
 b.metric('Required battery · average solar credit',f"{r['required_nominal_average_solar_wh']:.0f} Wh")
 c.metric('Station daily energy balance',f"{r['daily_balance_wh']:+.0f} Wh/day")
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

with sizing_tab:
 from sizing import derive
 st.subheader('Derived engineering sizing')
 st.caption('These outputs flow from the active mission and engineering assumptions. They are design allocations and sizing estimates, not independent driving requirements or approved shall statements.')
 options=['Current mission']+[f"Saved: {x['name']}" for x in st.session_state.mission_scenarios]
 if 'envelope_result' in st.session_state: options.append('Envelope point')
 selected=st.selectbox('Sizing for',options)
 target=r
 if selected.startswith('Saved: '):
  chosen=next(x for x in st.session_state.mission_scenarios if 'Saved: '+x['name']==selected)
  target=chosen['results'] | {'engineering':chosen['engineering']}
  st.caption('Saved mission parameters are frozen; CT and nominal-voltage assumptions below apply to this sizing view.')
 if selected=='Envelope point':
  envelope=st.session_state['envelope_result']
  series=st.selectbox('Envelope time on target',list(envelope['frame'].columns))
  candidates=[float(m) for m,v in envelope['frame'][series].items() if pd.notna(v)]
  if not candidates: st.warning('No feasible sizing points on this curve.'); st.stop()
  point_mass=st.selectbox('Envelope mass (lb)',candidates)
  point_range=float(envelope['frame'].loc[point_mass,series])
  battery_fraction=(point_mass*.45359237-4.35)/(point_mass*.45359237)
  target=size(mass_lb=point_mass,range_mi=point_range,days=int(series.split()[0])/24,battery_fraction=battery_fraction,**envelope['model_inputs'])
  st.caption(f'Sizing at the last calculated envelope boundary: {point_mass:g} lb, {point_range:.2f} miles per leg, {series}. Uses the frozen envelope assumptions.')
 try: calculated=derive(target,thrust_coefficient=ct,nominal_voltage=nominal_v)
 except ValueError as e: st.error(str(e)); st.stop()
 rows=[]
 for key,value in calculated.items():
  basis='Assumption' if key.startswith('assumed_') else 'Propeller-model estimate' if 'rpm' in key or 'tip_speed' in key else 'Derived sizing / allocation'
  units={'_lb_ft2':'lb/ft²','_kg_m2':'kg/m²','_N_m2':'N/m²','_wh_day':'Wh/day','_m_s':'m/s','_wkg':'W/kg','_whkg':'Wh/kg','_kgf':'kgf','_rpm':'RPM','_m2':'m²','_kg':'kg','_lb':'lb','_wh':'Wh','_ah':'Ah','_in':'in','_w':'W','_a':'A','_v':'V','_g':'g'}
  suffix=next((x for x in units if key.endswith(x)),None)
  label=key[:-len(suffix)] if suffix else key
  if key=='required_pack_ah_average_solar': label='Required pack capacity (average solar)'; suffix='_ah'
  if key=='required_pack_mass_kg_average_solar': label='Required pack mass (average solar)'; suffix='_kg'
  rows.append({'Sizing characteristic':label.replace('_',' ').capitalize(),'Value':f'{value:.3f}','Units':units.get(suffix,''),'Basis':basis})
 frame=pd.DataFrame(rows)
 st.dataframe(frame,hide_index=True,width='stretch')
 st.warning('Direct drive is assumed (motor RPM equals propeller RPM). RPM uses T = CT × air density × (RPM/60)² × diameter⁴. CT is an assumed static thrust coefficient. This is not measured motor performance or a blade/hub rating, and it does not predict cruise RPM. Confirm with matched motor/ESC/prop curves.')
 st.caption('Pack Ah uses nominal voltage; current uses minimum loaded voltage. Required pack mass is compared with the allocated mass at the selected aircraft weight; adding battery changes aircraft mass and requires a new trade. Peak assembly W is electrical input, not motor shaft power.')
 st.download_button('Download engineering sizing CSV',frame.to_csv(index=False),file_name='engineering_sizing.csv')
 st.download_button('Download engineering sizing JSON',json.dumps({'mission':target,'sizing':calculated,'status':'Derived estimates, not approved requirements'},indent=2),file_name='engineering_sizing.json')
