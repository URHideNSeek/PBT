import json
import pandas as pd
import streamlit as st
from mission import size, temperature_capacity_factor, TEMPERATURE_CAPACITY_POINTS
st.set_page_config(page_title='Mission Trade Study',page_icon='📊',layout='wide')
st.title('Mission Trade Study')
st.caption('Choose the capability to offer. See what engineering must achieve.')
STARTUP_PRESET={'mission_mass':12.,'mission_range':.5,'mission_hours':1.,'mission_solar':100,'mission_checkins':1,'mission_tier2':1,'battery_fraction_pct':20,'mission_temperature':(20,25)}
PRESET_VERSION='least-mass-temperature-v2'
def reset_startup_preset():
 for key,value in STARTUP_PRESET.items(): st.session_state[key]=value
 st.session_state.pop('envelope_result',None)
 st.session_state.pop('envelope_inputs',None)
if st.session_state.get('startup_preset_version')!=PRESET_VERSION:
 reset_startup_preset()
 st.session_state['startup_preset_version']=PRESET_VERSION
with st.sidebar:
 st.header('Platform & mission')
 st.button('Reset to least-mass starting case',on_click=reset_startup_preset)
 st.caption('Starting preset: 12 lb · 0.5 mile per leg · 1 hour on target.')
 mass=st.slider('Flight-ready mass, including payload (lb)',8.,19.9,step=.1,key='mission_mass')
 distance=st.slider('Range per leg (statute miles)',0.,10.,step=.5,key='mission_range')
 hours=st.slider('Perched time (hours)',1.,720.,step=1.,key='mission_hours')
 st.caption(f'{hours/24:.2f} days perched; maximum 30 days.')
 good=st.slider('Good solar days (%)',0,100,key='mission_solar')
 st.caption(f'{100-good}% bad solar days. Solar mix is an average, not a weather guarantee.')
 checkins=st.slider('Scheduled communications check-ins per day',0,48,key='mission_checkins')
 if checkins==0: st.caption('Anomaly and sleep-transition reports only. These still consume energy.')
 tier2=st.slider('Tier 2 active minutes per day',0,360,key='mission_tier2')
 temp_low,temp_high=st.slider('Operating temperature range (°C)',-20,50,key='mission_temperature')
 temperature_factor=temperature_capacity_factor(temp_low,temp_high)
 st.caption(f'Temperature capacity: {temperature_factor:.0%} of reference capacity. Uses the worst point in the selected range.')

mission_tab,sizing_tab,bom_tab=st.tabs(['Mission & Envelope','Engineering Sizing','BOM Options'])
from components import SENSORS, sensor_plan, bom, match, REQUIRED_SENSOR_HOSTS, FIXED_PERCH_SENSOR_G, FIXED_PERCH_SENSOR_SLEEP_W
from pathlib import Path
with sizing_tab:
 st.subheader('Sensor configuration')
 st.caption('Flight / perching is the locked installed-hardware baseline. Tier 1 and Tier 2 select stationary sensing activity using that same hardware. An unchecked tier means idle/not collecting in that tier; required sensors remain available for flight, perching and protection functions.')
 tier1_keys=[];tier2_keys=[]
 with st.container(border=True):
  cols=st.columns([4,1.5,1,1],gap='small')
  for col,title in zip(cols,['Sensor','Flight / perching','Tier 1','Tier 2']):col.markdown('**'+title+'**')
  for sensor_key,sensor_details in SENSORS.items():
   name_col,flight_col,tier1_col,tier2_col=st.columns([4,1.5,1,1],gap='small',vertical_alignment='center')
   name_col.write(sensor_details[0])
   flight_col.checkbox(sensor_details[0]+' · Flight / perching',value=sensor_key in REQUIRED_SENSOR_HOSTS,disabled=True,key='sensor_flight_'+sensor_key,label_visibility='collapsed')
   if tier1_col.checkbox(sensor_details[0]+' · Tier 1',value=sensor_key in ['environment','pressure','light'],key='sensor_t1_'+sensor_key,label_visibility='collapsed'):tier1_keys.append(sensor_key)
   if tier2_col.checkbox(sensor_details[0]+' · Tier 2',value=sensor_key in ['visible','thermal'],key='sensor_t2_'+sensor_key,label_visibility='collapsed'):tier2_keys.append(sensor_key)
 sensor_duty=st.slider('Tier 1 duty cycle (%)',0,100,100)/100
 profiles={}
 with st.expander('Sensor allocations and minimum selection parameters'):
  st.caption('These are editable allocations. Logged rate means stored/encoded output, not raw bus throughput. Temperature applies to every sourced row.')
  for key in dict.fromkeys([*REQUIRED_SENSOR_HOSTS,*tier1_keys,*tier2_keys]):
   label,sg,sw,ss,srate,interface=SENSORS[key]
   st.markdown('**'+label+'**')
   a,b,c=st.columns(3)
   required=key in REQUIRED_SENSOR_HOSTS
   q=a.number_input('Quantity',1,20,1,key=key+'_q',disabled=required)
   if required:
    allocated=0.;b.caption('Mass included in '+REQUIRED_SENSOR_HOSTS[key]+' host row; one installed device.')
   else:allocated=b.number_input('Mass each (g)',min_value=0.1,value=sg,key=key+'_mass')
   active=c.number_input('Active power allowance (W)',min_value=0.,value=sw,key=key+'_active')
   a,b,c=st.columns(3)
   idle=a.number_input('Sleep power (W)',min_value=0.,value=ss,key=key+'_sleep')
   logged=b.number_input('Logged data rate (Mbps)',min_value=0.,value=srate,format='%.4f',key=key+'_rate')
   rail=c.number_input('Supply rail (V)',min_value=1.,value=5.,key=key+'_rail')
   bus=st.selectbox('Sensor interface',['USB','I2C','SPI','UART','CAN','Ethernet','GPIO'],index=['USB','I2C','SPI','UART','CAN','Ethernet','GPIO'].index(interface),key=key+'_interface')
   perf={};gaps=[]
   if key in ['visible','thermal']:
    a,b,c=st.columns(3)
    perf={'pixels_x':a.number_input('Minimum image width (pixels)',1,10000,1280 if key=='visible' else 640,key=key+'_x'),
          'pixels_y':b.number_input('Minimum image height (pixels)',1,10000,720 if key=='visible' else 480,key=key+'_y'),
          'fps':c.number_input('Minimum frame rate (Hz)',1,240,30,key=key+'_fps')}
    gaps=['Optics / scene coverage / image quality need definition'] if not st.checkbox('Generic imaging is sufficient; no additional optics/scene requirement',value=True,key=key+'_generic') else []
   elif key=='gnss':perf={'accuracy_m':st.number_input('Maximum position error (m)',min_value=.01,value=2.5,key=key+'_accuracy'),'update_hz':5.}
   elif key=='radar':
    perf={'rf_min_mhz':st.number_input('Passive radar lower RF frequency (MHz)',min_value=1.,value=400.,key=key+'_rf_min'), 'rf_max_mhz':st.number_input('Passive radar upper RF frequency (MHz)',min_value=1.,value=1000.,key=key+'_rf_max'), 'rf_bandwidth_mhz':st.number_input('Passive radar instantaneous bandwidth (MHz)',min_value=1.,value=20.,key=key+'_rf_bw'), 'coherent_channels':2}
    gaps=['Reference/surveillance antenna geometry, synchronization and processing/range benchmark need definition']
   else:
    parameters={
     'environment': [('temp_accuracy_c','Maximum temperature error (°C)',.5),('humidity_accuracy_pct','Maximum humidity error (% RH)',3.)],
     'pressure': [('pressure_min_hpa','Required lower pressure (hPa)',300.),('pressure_max_hpa','Required upper pressure (hPa)',1100.),('pressure_accuracy_pa','Maximum pressure error (Pa)',50.)],
     'light': [('lux_max','Required illuminance upper bound (lux)',65000.)],
     'acoustic': [('sample_khz','Minimum sample rate (kHz)',16.),('channels','Minimum microphone channels',1.),('snr_db','Minimum signal-to-noise ratio (dB)',60.)],
     'vibration': [('accel_range_g','Required acceleration range (+/- g)',16.),('bandwidth_hz','Minimum measurement bandwidth (Hz)',100.)],
     'range': [('range_m','Minimum measurable distance (m)',10.),('range_accuracy_cm','Maximum distance error (cm)',5.),('sample_hz','Minimum update rate (Hz)',10.)],
     'rf': [('rf_min_mhz','Required lower RF frequency (MHz)',400.),('rf_max_mhz','Required upper RF frequency (MHz)',6000.),('rf_bandwidth_mhz','Minimum instantaneous bandwidth (MHz)',20.)],
     'radar': [('range_m','Minimum measurement distance (m)',10.),('range_accuracy_cm','Maximum distance error (cm)',10.),('sample_hz','Minimum update rate (Hz)',10.)],
    }
    for attr,caption,value in parameters.get(key,[]):
     perf[attr]=st.number_input(caption,min_value=0.,value=value,key=key+'_'+attr)
    gaps=['Application performance requirements need confirmation'] if not st.checkbox('Use these entered measurement requirements for screening',value=True,key=key+'_screen') else []
   profiles[key]={'quantity':q,'mass_g':allocated,'active_w':active,'sleep_w':idle,'logged_mbps':logged,'supply_v':rail,'interface':bus,'performance':perf,'open_requirements':gaps}
 with st.expander('Installation reserves and component selection assumptions'):
  a,b,c=st.columns(3)
  structure_g=a.number_input('Structure / mounting / mechanisms allocation (g)',min_value=0.,value=750.)
  wires_g=b.number_input('Wires / connectors reserve (g)',min_value=0.,value=150.)
  fasteners_g=c.number_input('Fasteners reserve (g)',min_value=0.,value=100.)
  sealants_g=a.number_input('Sealants / adhesives reserve (g)',min_value=0.,value=25.)
  growth_g=b.number_input('Growth reserve (g)',min_value=0.,value=200.)
  regulator_g=c.number_input('Regulator / distribution allocation (g)',min_value=0.,value=80.)
  navigation_g=a.number_input('Flight GNSS / compass allocation (g)',min_value=0.,value=60.)
  servo_qty=b.number_input('Mechanism actuator count',0,12,2)
  servo_g=c.number_input('Actuator mass each (g)',min_value=0.,value=30.)
  servo_torque=a.number_input('Required actuator torque (kgf cm)',min_value=0.,value=5.)
  servo_v=b.number_input('Actuator supply (V)',min_value=1.,value=6.)
  bus_max=c.number_input('Maximum pack / bus voltage (V)',min_value=1.,value=29.4)
  current_margin=a.number_input('Current rating margin multiplier',min_value=1.,value=1.25)
  compute_w=b.number_input('Payload computer power allowance (W)',min_value=0.,value=3.)
  autopilot_w=c.number_input('Flight controller power allowance (W)',min_value=0.,value=1.)
  ram_gb=a.number_input('Minimum payload-computer RAM (GB)',min_value=.1,value=.5)
  retention_days=b.number_input('Data retention (days)',min_value=1.,value=30.)
  gnss_accuracy=c.number_input('Flight GNSS maximum position error (m)',min_value=.01,value=2.5)
  frequency=a.number_input('Telemetry center frequency (MHz)',min_value=1.,value=915.)
  radio_supply=b.number_input('Telemetry supply (V)',min_value=1.,value=24.)
  link_mbps=c.number_input('Required application telemetry rate (Mbps)',min_value=.001,value=.1)
  st.caption('Structure allowance is split 65% enclosure/mounting and 35% perch/transformation mechanism. Wiring, fasteners and sealants are separate. Controller and field kit are outside the aircraft mass budget.')
  st.caption('Telemetry distance follows range per leg. Antenna-dependent installed range is not proved by a marketing range figure. Motors, ESCs and props require matched test data. Actuator torque must come from mechanism loads.')
 with st.expander('Engineering model assumptions (not mission requirements)'):
  fraction=st.slider('Battery fraction of flight-ready mass (%)',20,75,key='battery_fraction_pct')/100
  good_wh=st.number_input('Battery-delivered harvest on good day (Wh)',min_value=0.,value=90.)
  bad_wh=st.number_input('Battery-delivered harvest on bad day (Wh)',min_value=0.,value=15.)
  housekeeping_extra=st.number_input('Additional housekeeping power (W)',min_value=0.,value=1.)
  st.caption('Tier power is derived from selected sensors and computer/controller/navigation allowances.')
  radio=st.number_input('Active communications power (W)',min_value=0.,value=60.)
  duration=st.number_input('Minutes per scheduled check-in',min_value=0.,value=1.)
  events=st.number_input('Anomaly reports per day',min_value=0.,value=2.)
  event_duration=st.number_input('Minutes per anomaly report',min_value=0.,value=1.)
  sleep=st.number_input('Sleep-transition communication allowance per mission (Wh)',min_value=0.,value=1.)
  hop=distance
  st.caption('Relocation hop equals the initial insertion distance. An outward hop reserves a return from the next perch at twice the insertion distance.')
  wind=st.slider('Steady wind (kt)',0.,30.,20.)
  speed=st.slider('True cruise airspeed (kt)',10.,60.,35.)
  whkg=st.number_input('Assumed installed battery Wh/kg',min_value=50.,max_value=600.,value=322.)
  age_factor=st.slider('Aging/other capacity factor',.1,1.,.9,.05)
  derate=age_factor*temperature_factor
  st.caption(f'Combined capacity factor: {derate:.0%} = temperature {temperature_factor:.0%} × aging/other {age_factor:.0%}. Departure SOC remains 95%.')
  st.dataframe(pd.DataFrame(TEMPERATURE_CAPACITY_POINTS,columns=['Temperature (°C)','Provisional capacity factor']),hide_index=True)
  st.caption('Temperature factors are unvalidated trade assumptions; replace with pack test data. Battery temperature is assumed equal to ambient, without heating/cooling energy. Charging-temperature limits, cold-current capability and thermal transients are not modeled.')
  thermal_unused=st.caption('Detailed flight/prop/solar assumptions remain in advanced_app.py. This mission view is an inverse sizing study, not full feasibility verification.')
  ct=st.number_input('Assumed propeller thrust coefficient CT',min_value=.01,max_value=.3,value=.10,step=.01)
  nominal_v=st.number_input('Assumed nominal battery voltage (V)',min_value=18.,max_value=60.,value=24.,step=1.)


settings=dict(temp_min_c=temp_low,temp_max_c=temp_high,structure_g=structure_g,wires_g=wires_g,fasteners_g=fasteners_g,sealants_g=sealants_g,growth_g=growth_g,regulator_g=regulator_g,navigation_g=navigation_g,servo_qty=servo_qty,servo_g=servo_g,servo_torque_kgcm=servo_torque,servo_v=servo_v,bus_max_v=bus_max,current_margin=current_margin,compute_w=compute_w,autopilot_w=autopilot_w,ram_gb=ram_gb,retention_days=retention_days,gnss_accuracy_m=gnss_accuracy,radio_w=radio,radio_supply_v=radio_supply,link_range_km=distance*1.609344,link_mbps=link_mbps,frequency_mhz=frequency)
try:
 if bus_max<nominal_v:raise ValueError('Maximum bus voltage must not be below nominal battery voltage.')
 plan=sensor_plan(tier1_keys,tier2_keys,profiles,sensor_duty,tier2,housekeeping_extra+compute_w+autopilot_w+1.5)
except ValueError as e:st.error(str(e));st.stop()
t1,t2=plan['tier1_w'],plan['tier2_w']
installation_kg=(structure_g+wires_g+fasteners_g+sealants_g+growth_g+regulator_g+navigation_g+servo_qty*servo_g+FIXED_PERCH_SENSOR_G)/1000
fixed_nonbattery=installation_kg+1.05+.22+.87+.25+plan['sensor_kg']
component_inputs=dict(sensor_kg=plan['sensor_kg'],minimum_other_kg=installation_kg)
with sizing_tab:
 st.caption(f"Derived stationary loads: Tier 1 + housekeeping {t1:.2f} W; Tier 2 active increment {t2:.2f} W. Selected sensors: {plan['sensor_kg']*1000:.1f} g. Logged data: {plan['daily_gb']:.3f} GB/day.")

with mission_tab:

 st.divider()
 st.subheader('Payload mass versus range')
 st.caption('At the selected flight-ready mass and perched duration, available mass is traded between battery and payload. Payload includes selected mission sensors plus unpowered extra payload; installed flight/perch hardware and all reserves remain fixed.')
 calculate_envelope=st.button('Calculate payload envelope')
 envelope_inputs=(json.dumps(plan,sort_keys=True),json.dumps(settings,sort_keys=True),mass,fixed_nonbattery,plan['sensor_kg'],temp_low,temp_high,hours,good,checkins,tier2,good_wh,bad_wh,duration,events,event_duration,sleep,t1,t2,radio,wind,speed,whkg,derate)
 model_inputs=dict(**component_inputs,good_pct=good,checkins=checkins,tier2_min_day=tier2,good_wh=good_wh,bad_wh=bad_wh,checkin_min=duration,events_day=events,event_min=event_duration,wake_wh=sleep,tier1_w=t1,tier2_w=t2,comms_w=radio,wind=wind,speed=speed,whkg=whkg,derate=derate)
 if calculate_envelope or 'envelope_result' not in st.session_state or st.session_state.get('envelope_inputs')!=envelope_inputs or st.session_state['envelope_result'].get('kind')!='payload':
  from envelope import payload_curve
  points=payload_curve(hours,mass_lb=mass,nonbattery_kg=fixed_nonbattery,**model_inputs)
  data=[{k:v for k,v in x.items() if k!='result'} if x else {'Range per leg (mi)':i*.25,'Payload mass (lb)':None,'Additional payload (kg)':None,'Battery fraction':None} for i,x in enumerate(points)]
  frame=pd.DataFrame(data)
  st.session_state['envelope_inputs']=envelope_inputs
  st.session_state['envelope_result']={'kind':'payload','frame':frame,'points':points,'settings':{'mass_lb':mass,'selected_hours':hours,'nonbattery_kg':fixed_nonbattery,'good_solar_pct':good,'checkins_day':checkins,'tier2_min_day':tier2,'temperature_min_c':temp_low,'temperature_max_c':temp_high,'capacity_factor':derate},'component_plan':plan,'component_settings':settings,'model_inputs':model_inputs}
 saved=st.session_state['envelope_result']
 if not any(x is not None for x in saved['points']):st.warning('No payload/range combination closes this perched duration at the selected takeoff mass while preserving return energy.')
 st.vega_lite_chart(saved['frame'],{'mark':{'type':'line','point':True},'encoding':{'x':{'field':'Range per leg (mi)','type':'quantitative','title':'Initial hop / return range (statute miles)'},'y':{'field':'Payload mass (lb)','type':'quantitative','title':'Maximum mission payload mass (lb)'},'tooltip':[{'field':'Range per leg (mi)'},{'field':'Payload mass (lb)'},{'field':'Additional payload (kg)'},{'field':'Battery fraction'}]}},width='stretch')
 st.caption(f'Selected perched time: {hours:g} hours ({hours/24:.2f} days). Missing points cannot complete that mission while preserving return energy. Extra powered payload needs its electrical load entered before using this boundary. Recharge time does not gate this curve.')
 st.download_button('Download payload envelope CSV',saved['frame'].to_csv(index=False),file_name='payload_envelope.csv')

try:
 r=size(**component_inputs,mass_lb=mass,range_mi=distance,days=hours/24,good_pct=good,checkins=checkins,tier2_min_day=tier2,battery_fraction=fraction,good_wh=good_wh,bad_wh=bad_wh,checkin_min=duration,events_day=events,event_min=event_duration,wake_wh=sleep,tier1_w=t1,tier2_w=t2,comms_w=radio,reposition_mi=hop,wind=wind,speed=speed,whkg=whkg,derate=derate)
except ValueError as e: st.error(str(e)); st.stop()
with mission_tab:

 a,b,c=st.columns(3)
 a.metric('Required nominal battery · no solar credit',f"{r['required_nominal_no_solar_wh']:.0f} Wh")
 b.metric('Required battery · average solar credit',f"{r['required_nominal_average_solar_wh']:.0f} Wh")
 c.metric('Station daily energy balance',f"{r['daily_balance_wh']:+.0f} Wh/day")
 st.caption(f"Temperature-adjusted battery capacity: {r['battery_capacity_wh']:.0f} Wh; energy at 95% departure SOC: {r['battery_capacity_wh']*.95:.0f} Wh. Temperature affects capacity, not the 95% dispatch threshold.")
 st.subheader('Recharge time needed for relocation')
 wait=r['relocation_charge_h']
 if wait is None:st.warning('Relocation cannot become energy-ready under the selected battery capacity, solar mix and continuing sensor/communications schedule.')
 else:st.metric('Recharge time needed for relocation',f'{wait:.1f} hours',help='Calculated after the selected perched duration; return energy remains protected.')
 st.caption(f'Relocation: {distance:g} miles. Protected return from the new perch: {2*distance:g} miles, plus landing reserve. Recharge uses net solar after ongoing stationary loads. Zero means no additional charging wait is required.')
 if not r['return_reserve_preserved']:
  st.error('The requested perched duration would consume protected return energy. The aircraft must recover or reduce activity before reaching that limit.')
  if r['maximum_protected_perched_hours'] is not None:st.write(f"Maximum perched duration before the return-energy limit: {r['maximum_protected_perched_hours']:.1f} hours under the average-solar model.")
 st.caption('Solar is averaged across good/bad days; nighttime, weather sequences and actual charging temperature limits still require verification.')
 if not r['insertion_energy_feasible']: st.error('Insertion needs more energy than the assumed battery can provide before solar charging.')
 if not r['station_energy_feasible']: st.error('Battery crosses the analysis minimum during the station mission. Recharge readiness is not claimed.')
 if not r['mission_energy_feasible']: st.error(f"Assumed battery does not close the mission. Recovery energy margin: {r['energy_margin_average_wh']:.0f} Wh.")
 else: st.success(f"Average-solar energy margin: {r['energy_margin_average_wh']:.0f} Wh. Weather sequencing and other closure checks still require review.")
 st.info('Mass includes payload. Battery mass and flight power remain coupled. The solar mix averages good and bad days; a string of bad days may fail even when the average passes. Six-hour missions use fractional-day schedules. Tier 2/radio loads are incremental. No supplier capabilities are assumed.')
 if 'mission_scenarios' not in st.session_state: st.session_state.mission_scenarios=[]
 name=st.text_input('Trade name','Mission concept')
 record={'name':name,'mission':{'mass_lb':mass,'range_mi':distance,'hours':hours,'perched_days':hours/24,'good_solar_pct':good,'checkins_day':checkins,'tier2_min_day':tier2,'battery_fraction':fraction,'temperature_min_c':temp_low,'temperature_max_c':temp_high,'temperature_capacity_factor':temperature_factor,'aging_capacity_factor':age_factor,'good_wh_day':good_wh,'bad_wh_day':bad_wh,'tier1_w':t1,'tier2_w':t2,'comms_w':radio,'checkin_min':duration,'anomaly_reports_day':events,'event_min':event_duration,'sleep_report_wh':sleep,'reposition_mi':hop},'results':{k:v for k,v in r.items() if k!='engineering'},'engineering':r['engineering'],'component_plan':plan,'component_settings':settings}
 if st.button('Save mission to comparison'):
  st.session_state.mission_scenarios=[x for x in st.session_state.mission_scenarios if x['name']!=name]+[record]
 if st.session_state.mission_scenarios:
  frame=pd.DataFrame([{'Trade':x['name'],**x['mission'],'Required battery Wh':x['results']['required_nominal_average_solar_wh'],'Recharge time needed for relocation h':x['results'].get('relocation_charge_h')} for x in st.session_state.mission_scenarios]).set_index('Trade')
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
 target_plan=plan
 target_settings=settings
 if selected.startswith('Saved: '):
  chosen=next(x for x in st.session_state.mission_scenarios if 'Saved: '+x['name']==selected)
  target=chosen['results'] | {'engineering':chosen['engineering']}
  if 'component_plan' not in chosen:
   st.warning('This older saved trade has no sensor/BOM snapshot. Re-save it under the new configuration before sourcing.');st.stop()
  target_plan=chosen['component_plan'];target_settings=chosen['component_settings']
  st.caption('Saved mission parameters are frozen; CT and nominal-voltage assumptions below apply to this sizing view.')
 if selected=='Envelope point':
  envelope=st.session_state['envelope_result']
  feasible=[x for x in envelope['points'] if x is not None]
  if not feasible:st.warning('No feasible payload envelope point for this perched duration.');st.stop()
  point_range=st.selectbox('Envelope range per leg (mi)',[x['Range per leg (mi)'] for x in feasible])
  point=next(x for x in feasible if x['Range per leg (mi)']==point_range)
  target=point['result'].copy();target['additional_payload_kg']=point['Additional payload (kg)']
  target_plan=envelope['component_plan'];target_settings=envelope['component_settings'] | {'link_range_km':point_range*1.609344}
  st.caption(f"Payload boundary: {point['Payload mass (lb)']:.2f} lb total mission payload, {point_range:g} miles per leg, {envelope['settings']['selected_hours']:g} hours perched. Battery allocation is solved from remaining mass.")
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
 st.warning('RPM uses T = CT × air density × (RPM/60)² × diameter⁴. CT is an assumed static thrust coefficient. This is not measured motor performance or a blade/hub rating, and it does not predict cruise RPM. Confirm with matched motor/ESC/prop curves.')
 st.caption('Pack Ah uses nominal voltage; current uses minimum loaded voltage. Required pack mass is compared with the allocated mass at the selected aircraft weight; adding battery changes aircraft mass and requires a new trade. Peak assembly W is electrical input, not motor shaft power.')
 st.download_button('Download engineering sizing CSV',frame.to_csv(index=False),file_name='engineering_sizing.csv')
 st.download_button('Download engineering sizing JSON',json.dumps({'mission':target,'sizing':calculated,'status':'Derived estimates, not approved requirements'},indent=2),file_name='engineering_sizing.json')

with sizing_tab:
 st.subheader('Allocated bill of materials')
 allocated=bom(target,calculated,target_plan,target_settings)
 table=[{'Component':x['component'],'Quantity':x['quantity'],'Mass each (g)':round(x['mass_each_g'],2),'Mass row (g)':round(x['mass_total_g'],2),'Selection parameters':'; '.join(f"{k} {v['op']} {v['value']}" for k,v in x['requirements'].items()),'Needs definition / verification':'; '.join(x['open_requirements'])} for x in allocated['rows']]
 st.dataframe(pd.DataFrame(table),hide_index=True,width='stretch')
 a,b,c=st.columns(3)
 a.metric('Allocated BOM mass',f"{allocated['allocated_g']/1000:.3f} kg")
 b.metric('Flight-ready mass',f"{allocated['flight_ready_g']/1000:.3f} kg")
 c.metric('Remaining mass',f"{allocated['margin_g']:.1f} g")
 if not allocated['closed']:st.error('BOM exceeds the selected flight-ready mass. No viable complete BOM can be claimed.')
 st.caption('Battery is allocated from mission mass fraction; propulsion/compute/comms/solar are split into explicit rows. Remaining mass is unused headroom already included in the flight-ready mass. Sensor power, logged rate and installation reserves are assumptions until replaced by measured product data. Per-row matches do not prove whole-system interoperability.')
 st.download_button('Download allocated BOM CSV',pd.DataFrame(table).to_csv(index=False),'allocated_bom.csv')
 st.download_button('Download BOM requirements JSON',json.dumps({'sizing_for':selected,'plan':target_plan,'settings':target_settings,'bom':allocated},indent=2),'bom_requirements.json')
with bom_tab:
 st.subheader('BOM Options')
 sourcing=st.selectbox('Component sourcing',['NDAA + Blue UAS evidence required','Unrestricted sourcing'])
 st.caption('Controlled sourcing requires source-backed NDAA evidence AND model-specific Blue UAS Framework evidence. Manufacturer declarations are identified as such; they do not constitute aircraft approval. Unrestricted sourcing removes those two gates; it does not mean a product is noncompliant. Unknown specifications are never a match.')
 catalog=json.loads((Path(__file__).parent/'catalog.json').read_text())
 matches=match(allocated['rows'],catalog,sourcing.startswith('NDAA'))
 st.caption(f"Sizing for: {selected}. Catalog sources checked October 14, 2026; {len(catalog)} named candidates. This is a curated evidence catalog, not an exhaustive live search. New products require source-backed catalog entries.")
 st.dataframe(pd.DataFrame([{'Component':m['row']['component'],'Qty':m['row']['quantity'],'Mass each (g)':round(m['row']['mass_each_g'],2),'Mass row (g)':round(m['row']['mass_total_g'],2),'Option 1':m['options'][0]['name'] if len(m['options'])>0 else '', 'Option 2':m['options'][1]['name'] if len(m['options'])>1 else '', 'Option 3':m['options'][2]['name'] if len(m['options'])>2 else '', 'Status':m['status']} for m in matches]),hide_index=True,width='stretch')
 if not allocated['closed']:st.error('Mass closure fails. Individual parameter matches below do not constitute a viable assembled BOM.')
 for item in matches:
  if not item['row']['sourcing']:continue
  with st.expander(item['row']['component']+' · '+item['status']):
   st.write('**Requirements**');st.json(item['row']['requirements'])
   if item['row']['open_requirements']:st.write('**Still to define / verify:** '+'; '.join(item['row']['open_requirements']))
   for product in item['options']:
    st.markdown('**'+product['name']+'**');st.link_button('Manufacturer evidence',product['source_url']);st.json(product['attributes']);st.caption(product.get('notes',''))
    st.caption('NDAA evidence: '+str(product.get('ndaa_source_url') or 'Not established')+' · Blue evidence: '+str(product.get('blue_source_url') or 'Not established'))
   if not item['options']:st.write('No product with complete evidence meets this row under the active constraints.')
   for entry in item['rejected']:
    st.markdown('**Candidate, excluded: '+entry['product']['name']+'**')
    st.write('; '.join(entry['reasons']));st.link_button('Candidate source',entry['product']['source_url'],key='source_'+item['row']['id']+'_'+entry['product']['id'])
   if not item['options'] and not item['rejected']:st.caption('Catalog gap: no sourced candidate entered for this category yet. Request vendor data for the requirements above.')
 count=sum(bool(x['options']) for x in matches if x['row']['sourcing']);needed=sum(x['row']['sourcing'] for x in matches)
 st.metric('COTS rows with at least one specification match',f'{count} / {needed}')
 st.caption('Zero means no evidenced match in this catalog under the active requirements, not proof that no product exists. Missing requirements and specifications are listed under each row.')
 st.download_button('Download BOM option evidence',json.dumps({'sourcing':sourcing,'sizing_for':selected,'mass_closed':allocated['closed'],'matches':matches},indent=2),'bom_options.json')
