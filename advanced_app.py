import json
import pandas as pd
import streamlit as st
from model import F, DEFAULTS, MASS, validate, evaluate
st.set_page_config(page_title='Platform Trade Engine',page_icon='📊',layout='wide')
st.title('Platform · Trade Engine')
st.caption('Aircraft + unattended perched sensor · performance sizing before parts selection')
st.info('All defaults are assumptions. PASS means preliminary model closure; packaging, perch strength, motor/ESC limits and sensor effectiveness remain unmodeled.')
if 'scenarios' not in st.session_state: st.session_state.scenarios=[]
with st.sidebar:
 st.header('Design parameters')
 uploaded=st.file_uploader('Import individual scenario JSON',type=['json'])
 if st.button('Load imported scenario',disabled=uploaded is None):
  try:
   s=json.load(uploaded)
   if s.get('schema_version')!=1: raise ValueError('Unsupported schema version')
   validate(s['parameters'])
   for k,v in s['parameters'].items(): st.session_state[k]=float(v)
   st.session_state['name']=str(s.get('name','Imported'))
   st.success('Loaded')
  except (ValueError,TypeError,KeyError) as e: st.error(str(e))
 if st.button('Reset design exercise'):
  for k,v in DEFAULTS.items(): st.session_state[k]=v
 p={}
 for group in ['Limits','Mass','Battery','Flight','Mission','Station','Solar','Data','Thermal']:
  with st.expander(group,expanded=group=='Mission'):
   for k,(label,value,lo,hi,g) in F.items():
    if group==g:
     if k not in st.session_state: st.session_state[k]=value
     p[k]=st.number_input(label,min_value=lo,max_value=hi,key=k,format='%.3f')
try: r=evaluate(p)
except ValueError as e: st.error(str(e)); st.stop()
a,b,c,d=st.columns(4)
a.metric('Aircraft mass',f"{r['mass_lb']:.2f} lb")
b.metric('Nominal / usable energy',f"{r['nominal_wh']:.0f} / {r['usable_wh']:.0f} Wh")
c.metric('Mission energy margin',f"{r['margin_wh']:.0f} Wh" if r['margin_wh'] is not None else 'Infeasible route')
d.metric('Calculated checks',f"{sum(r['checks'].values())} / {len(r['checks'])}")
tabs=st.tabs(['Mission & closure','Trade matrix','Sensitivity','Model & assumptions'])
with tabs[0]:
 left,right=st.columns([2,1])
 with left:
  if r['trace']:
   st.subheader('Energy during Persist')
   st.line_chart(pd.DataFrame(r['trace']).set_index('Station hour'))
   st.caption('Recovery protection includes return energy, reserve and SOC floor. Solar is normalized across 06:00–18:00. Activity is spread uniformly; real early activity may lower minimum energy.')
  values=[{'Metric':k.replace('_',' '),'Value':None if v is None else round(v,2)} for k,v in r.items() if k not in ['checks','trace']]
  st.dataframe(pd.DataFrame(values),hide_index=True,width='stretch')
 with right:
  st.subheader('Closure checks')
  st.dataframe(pd.DataFrame([{'Check':k,'Status':'PASS' if v else 'FAIL'} for k,v in r['checks'].items()]),hide_index=True,width='stretch')
  st.bar_chart(pd.DataFrame({'kg':{F[k][0]:p[k] for k in MASS}}))
with tabs[1]:
 name=st.text_input('Scenario name',value='Design exercise',key='name')
 current={'schema_version':1,'name':name,'parameters':p.copy(),'basis':'Assumed / user-entered'}
 if st.button('Save to comparison matrix'):
  st.session_state.scenarios=[s for s in st.session_state.scenarios if s['name']!=name]+[current]
 st.caption('Same-name saves replace the existing row. Download JSON to preserve session-local scenarios.')
 st.download_button('Download current scenario JSON',json.dumps(current,indent=2),file_name='scenario.json')
 rows=[]
 for s in st.session_state.scenarios:
  q=evaluate(s['parameters'])
  rows.append({'Scenario':s['name'],**{k:q[k] for k in ['mass_lb','nominal_wh','flight_w','station_wh','solar_daily_wh','margin_wh']},'Checks passed':sum(q['checks'].values()),'All calculated checks pass':all(q['checks'].values())})
 if rows:
  frame=pd.DataFrame(rows).set_index('Scenario'); st.dataframe(frame.T,width='stretch')
  st.download_button('Download matrix CSV',frame.to_csv(),file_name='trade_matrix.csv')
  st.download_button('Download scenario bundle',json.dumps(st.session_state.scenarios,indent=2),file_name='scenarios.json')
  if st.button('Clear matrix'): st.session_state.scenarios=[]; st.rerun()
 else: st.info('Save multiple designs to compare them here.')
with tabs[2]:
 key=st.selectbox('Sweep parameter',list(F),format_func=lambda k:F[k][0])
 lo=st.number_input('Sweep minimum',value=float(max(F[key][2],p[key]*.8)))
 hi=st.number_input('Sweep maximum',value=float(min(F[key][3],p[key]*1.2)))
 rows=[]
 if hi>=lo:
  for i in range(21):
   value=lo+(hi-lo)*i/20
   if key=='rotors': value=float(round(value))
   try:
    q=evaluate(p | {key:value})
    rows.append({'Parameter':value,'Energy margin Wh':q['margin_wh'],'Mass lb':q['mass_lb'],'Flight W':q['flight_w'],'Checks passed':sum(q['checks'].values())})
   except ValueError: pass
 if rows:
  frame=pd.DataFrame(rows).drop_duplicates('Parameter').set_index('Parameter')
  st.line_chart(frame[['Energy margin Wh']]); st.dataframe(frame,width='stretch')
  st.download_button('Download sensitivity CSV',frame.to_csv(),file_name='sensitivity.csv')
 else: st.warning('No valid configurations in this sweep')
with tabs[3]:
 st.markdown('''### Model basis
- Installed mass includes growth. Battery nominal Wh = installed kg × installed Wh/kg.
- Capacity derating and the initial-to-minimum SOC window determine available Wh. The Wh reserve is added once.
- Hover power = weight^(3/2) / sqrt(2 × density × total rotor area), divided by assumed overall efficiency.
- Cruise is a reference-calibrated sensitivity model: nondrag power scales with mass^(3/2)/diameter; drag power scales with CdA × airspeed³. It is not a validated forward-flight rotor model.
- A single steady wind vector applies to reciprocal legs. Crosswind requires crab; impossible track or nonpositive ground speed fails.
- Solar uses active area, cell/charger efficiency, shading and equivalent sunlight. A flat 12-hour daylight profile is simulated at five-minute resolution. Harvest above battery capacity is discarded.
- Tier 2 and radio power are incremental above shared and Tier 1 loads; they may overlap. Extra activity is distributed uniformly. No automatic shutdown or ACK policy is modeled.
- Station thermal is a conservative steady peak estimate treating active loads as internal heat. Transient cooling is not modeled.

### Additional engineering needed
Folding/packaging/CG, perch and gust loads, motor/ESC voltage and thermal limits, battery sag, sensor detection performance, RF link budgets, detailed activity scheduling and weather profiles. RPM and acoustic predictions require data and are not fabricated. There is no procurement model.
''')
 st.dataframe(pd.DataFrame([{'Parameter':F[k][0],'Value':v,'Basis':'Assumed / user-entered'} for k,v in p.items()]),hide_index=True,width='stretch')
