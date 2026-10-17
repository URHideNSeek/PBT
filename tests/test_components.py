import copy,json,unittest
from pathlib import Path
from components import SENSORS,REQUIRED_SENSOR_HOSTS,sensor_plan,bom,match,constraint,evaluate_product
from mission import size
from sizing import derive
ROOT=Path(__file__).resolve().parents[1]
def profile(key):
 _,g,w,s,rate,interface=SENSORS[key]
 return dict(quantity=1,mass_g=g,active_w=w,sleep_w=s,logged_mbps=rate,supply_v=5.,interface=interface,performance={},open_requirements=[])
def settings():
 return dict(temp_min_c=20,temp_max_c=25,structure_g=750.,wires_g=150.,fasteners_g=100.,sealants_g=25.,growth_g=200.,regulator_g=80.,navigation_g=60.,servo_qty=2,servo_g=30.,servo_torque_kgcm=5.,servo_v=6.,bus_max_v=29.4,current_margin=1.25,compute_w=3.,autopilot_w=1.,ram_gb=.5,retention_days=30.,gnss_accuracy_m=2.5,radio_w=60.,radio_supply_v=24.,link_range_km=1.,link_mbps=.1,frequency_mhz=915.)
class ComponentTests(unittest.TestCase):
 def test_shared_sensor_once_and_no_double_active_power(self):
  p=profile('visible');a=sensor_plan(['visible'],[],{'visible':p},1,60,1)
  b=sensor_plan(['visible'],['visible'],{'visible':p},1,60,1)
  self.assertEqual(a['sensor_kg'],b['sensor_kg']);self.assertEqual(b['tier2_w'],0)
  self.assertEqual(a['daily_gb'],b['daily_gb'])
 def test_duty_and_tier2_override(self):
  p=profile('visible');x=sensor_plan(['visible'],['visible'],{'visible':p},.5,360,1)
  self.assertAlmostEqual(x['devices'][0]['active_fraction'],.625)
  self.assertAlmostEqual(x['tier1_w']+x['tier2_w'],1+p['active_w'])
 def test_unused_tier2_is_idle_but_still_installed(self):
  p=profile('thermal');x=sensor_plan([],['thermal'],{'thermal':p},1,0,1)
  self.assertEqual(x['daily_gb'],0);self.assertEqual(x['sensor_kg'],.05)
  self.assertAlmostEqual(x['tier1_w'],1.02)
 def test_selected_sensor_updates_energy(self):
  p=profile('rf');plan=sensor_plan(['rf'],[],{'rf':p},1,1,1)
  a=size(tier1_w=1);b=size(tier1_w=plan['tier1_w'])
  self.assertGreater(b['required_nominal_average_solar_wh'],a['required_nominal_average_solar_wh'])
 def test_bom_mass_no_double_count(self):
  p=profile('visible');plan=sensor_plan([],['visible'],{'visible':p},1,1,1)
  r=size(sensor_kg=plan['sensor_kg']);b=bom(r,derive(r),plan,settings());d={x['id']:x for x in b['rows']}
  expected=(r['battery_kg']+1.05+.22+.87+.25+plan['sensor_kg'])*1000+1455.
  self.assertAlmostEqual(b['allocated_g'],expected)
  for key in ['STR','WIR','FST','SEA','GRO']:self.assertIn(key,d)
  self.assertEqual(sum(x['mass_total_g'] for x in b['rows']),b['allocated_g'])
 def test_retention_and_storage_depend_on_sensors(self):
  p=profile('visible');plan=sensor_plan(['visible'],[],{'visible':p},1,1,1)
  r=size(sensor_kg=plan['sensor_kg']);b=bom(r,derive(r),plan,settings())
  self.assertAlmostEqual(b['storage_required_gb'],plan['daily_gb']*30*1.25)
 def test_no_unknown_specs_or_fake_compliance(self):
  row=dict(category='test',sourcing=True,open_requirements=[],requirements={'mass_g':constraint('<=',10.)})
  candidate=dict(id='a',name='A',category='test',source_url='https://example.org',checked_on='2026-10-14',attributes={})
  self.assertEqual(len(match([row],[candidate])[0]['options']),0)
  candidate['attributes']['mass_g']=5
  self.assertEqual(len(match([row],[candidate])[0]['options']),1)
  self.assertEqual(len(match([row],[candidate],True)[0]['options']),0)
  candidate.update(ndaa=True,blue=True,ndaa_source_url='https://example.org/n',blue_source_url='https://example.org/b')
  self.assertEqual(len(match([row],[candidate],True)[0]['options']),1)
 def test_limit_three_and_range_rejection(self):
  row=dict(category='test',sourcing=True,open_requirements=[],requirements={'mass_g':constraint('<=',10.),'temp_min_c':constraint('<=',-20)})
  products=[dict(id=str(i),name=str(i),category='test',source_url='https://example.org',checked_on='2026-10-14',attributes={'mass_g':i+1,'temp_min_c':-40}) for i in range(5)]
  self.assertEqual(len(match([row],products)[0]['options']),3)
  products[0]['attributes']['temp_min_c']=0
  self.assertTrue(evaluate_product(row,products[0]))
 def test_reserves_are_not_sourced(self):
  row=dict(category='reserve',sourcing=False)
  self.assertEqual(match([row],[])[0]['status'],'Reserved / custom; no COTS search')
 def test_catalog_unique_and_primary_sources(self):
  c=json.loads((ROOT/'catalog.json').read_text());self.assertEqual(len({x['id'] for x in c}),len(c))
  self.assertTrue(all(x['source_url'].startswith('https://') and x['checked_on'] for x in c))
class ComponentUI(unittest.TestCase):
 def test_sensors_bom_and_sourcing(self):
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30);self.assertFalse(a.exception)
  self.assertEqual([x.label for x in a.tabs],['Mission & Envelope','Engineering Sizing','BOM Options'])
  before=a.session_state['envelope_result']['settings']['nonbattery_kg']
  a.slider(key='mission_payload').set_value(.2).run(timeout=30)
  a.checkbox(key='sensor_t2_rf').check().run(timeout=30)
  self.assertFalse(a.exception)
  self.assertGreater(a.session_state['envelope_result']['settings']['nonbattery_kg'],before)
  next(x for x in a.selectbox if x.label=='Component sourcing').set_value('Unrestricted sourcing').run(timeout=30)
  self.assertFalse(a.exception)
  self.assertTrue(any(x.label=='COTS rows with at least one specification match' and x.value.startswith('1 /') for x in a.metric))
  next(x for x in a.button if x.label=='Save mission to comparison').click().run(timeout=30)
  self.assertIn('component_plan',a.session_state['mission_scenarios'][0])

class LockedSensorsUI(unittest.TestCase):
 def test_required_sensors_remain_checked_with_no_mission_payload(self):
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
  for key in REQUIRED_SENSOR_HOSTS:
   w=a.checkbox(key='sensor_flight_'+key)
   self.assertTrue(w.value);self.assertTrue(w.disabled)
  for key in SENSORS:
   if key=='perch_camera':continue
   a.checkbox(key='sensor_t1_'+key).uncheck()
   a.checkbox(key='sensor_t2_'+key).uncheck()
  a.slider(key='mission_tier2').set_value(0).run(timeout=30)
  self.assertFalse(a.exception)
  self.assertTrue(all(a.checkbox(key='sensor_flight_'+key).value for key in REQUIRED_SENSOR_HOSTS))
  self.assertTrue(any('Required perch distance sensor' in str(x.value) for x in a.dataframe))

  a.slider(key='mission_payload').set_value(.2).run(timeout=30)
  before=a.session_state['envelope_result']['settings']['nonbattery_kg']
  a.checkbox(key='sensor_t1_visible').check().run(timeout=30)
  self.assertFalse(a.exception)
  self.assertAlmostEqual(a.session_state['envelope_result']['settings']['nonbattery_kg']-before,.03)
  self.assertGreater(a.session_state['envelope_result']['component_plan']['daily_gb'],0)

class CandidateScreening(unittest.TestCase):
 def setUp(self):
  self.row=dict(category='test',sourcing=True,open_requirements=[],requirements={'mass_g':constraint('<=',10.)})
  self.product=dict(id='a',name='A',category='test',source_url='https://example.org',checked_on='2026-10-16',attributes={})
 def test_missing_data_is_pending_not_failed(self):
  m=match([self.row],[self.product])[0]
  self.assertEqual(len(m['candidates']),1);self.assertFalse(m['options']);self.assertFalse(m['rejected'])
 def test_known_mismatch_is_excluded_even_with_unknowns(self):
  self.product['attributes']['mass_g']=11;self.row['open_requirements']=['Installed qualification']
  m=match([self.row],[self.product])[0]
  self.assertFalse(m['candidates']);self.assertEqual(len(m['rejected']),1)
 def test_compliance_pending_and_explicit_failure(self):
  self.product['attributes']['mass_g']=5
  self.assertEqual(len(match([self.row],[self.product],True)[0]['candidates']),1)
  self.product['ndaa']=False
  self.assertEqual(len(match([self.row],[self.product],True)[0]['rejected']),1)
  self.assertEqual(len(match([self.row],[self.product],False)[0]['options']),1)
 def test_open_integration_is_pending(self):
  self.product['attributes']['mass_g']=5;self.row['open_requirements']=['Installed test']
  self.assertEqual(len(match([self.row],[self.product])[0]['candidates']),1)
 def test_all_bom_and_sensor_categories_researched(self):
  catalog=json.loads((ROOT/'catalog.json').read_text());categories={k for p in catalog for k in p['categories']}
  plan=sensor_plan([],[],{},1,1,1);r=size(sensor_kg=plan['sensor_kg'])
  rows=bom(r,derive(r),plan,settings())['rows']
  self.assertTrue({row['category'] for row in rows if row['sourcing']}<=categories)
  self.assertTrue({'acoustic','vibration','rf','radar','thermal','environment','pressure','light'}<=categories)

class PhaseCommunicationsTests(unittest.TestCase):
 def test_all_phase_selections_count_hardware_once(self):
  from itertools import product
  from components import COMMS_PHASES,COMMS_DEFAULTS,communications_plan
  slots=[(phase,key) for phase in COMMS_PHASES for key in COMMS_DEFAULTS]
  for flags in product([False,True],repeat=len(slots)):
   selection={phase:[] for phase in COMMS_PHASES}
   for enabled,(phase,key) in zip(flags,slots):
    if enabled:selection[phase].append(key)
   c=communications_plan(selection,COMMS_DEFAULTS)
   fitted=set().union(*(set(v) for v in selection.values()))
   self.assertEqual(set(c['installed']),fitted)
   self.assertAlmostEqual(c['mass_g'],sum(COMMS_DEFAULTS[k]['mass_g']+COMMS_DEFAULTS[k]['antenna_g'] for k in fitted))
   self.assertAlmostEqual(c['flight_w'],sum(COMMS_DEFAULTS[k]['active_w'] for k in selection['flight']))
 def test_separate_scheduled_and_anomaly_energy(self):
  from components import COMMS_DEFAULTS,communications_plan,communications_schedule
  c=communications_plan({'passive':['rf'],'active':['satcom']},COMMS_DEFAULTS)
  p={'comms_compute_increment_w':2.}
  s=communications_schedule(c,p,6,2,3,1)
  self.assertAlmostEqual(s['scheduled_wh_day'],(8-.02+2)*12/60)
  self.assertAlmostEqual(s['event_wh_day'],(15-.02+2)*3/60)
  self.assertAlmostEqual(s['equivalent_increment_w']*15/60,s['scheduled_wh_day']+s['event_wh_day'])
 def test_no_links_no_reports_or_installed_mass(self):
  from components import COMMS_DEFAULTS,communications_plan,communications_schedule
  c=communications_plan({},COMMS_DEFAULTS);s=communications_schedule(c,{'comms_compute_increment_w':3},48,1,2,1)
  self.assertEqual(c['mass_g'],0);self.assertEqual(c['standby_w'],0)
  self.assertEqual(s['checkins'],0);self.assertEqual(s['events'],0);self.assertEqual(s['equivalent_increment_w'],0)
 def test_landing_camera_cannot_be_allocated_to_tiers(self):
  self.assertNotIn('visible',REQUIRED_SENSOR_HOSTS);self.assertIn('perch_camera',REQUIRED_SENSOR_HOSTS)
  with self.assertRaisesRegex(ValueError,'landing-only'):sensor_plan(['perch_camera'],[],{'perch_camera':profile('perch_camera')},1,10,0)
 def test_visual_camera_separate_from_landing_bom(self):
  plan=sensor_plan([],['visible'],{'visible':profile('visible'),'perch_camera':profile('perch_camera')},1,10,0)
  self.assertAlmostEqual(plan['sensor_kg'],.03)
  r=size(sensor_kg=plan['sensor_kg']);rows=bom(r,derive(r),plan,settings())['rows']
  self.assertTrue({'NAVCAM','SEN-visible'}<={x['id'] for x in rows})
 def test_disabled_radios_absent_from_bom(self):
  from components import COMMS_DEFAULTS,communications_plan
  c=communications_plan({'flight':['rf'],'passive':['rf']},COMMS_DEFAULTS)
  plan=sensor_plan([],[],{},1,1,0);r=size(comms_kg=c['mass_g']/1000)
  cfg=settings();cfg['communications']=c
  rows=bom(r,derive(r),plan,cfg)['rows'];ids={x['id'] for x in rows}
  self.assertTrue({'RF','ANT'}<=ids);self.assertTrue({'LTE','SAT'}.isdisjoint(ids))
  self.assertAlmostEqual(sum(x['mass_total_g'] for x in rows if x['id'] in {'RF','ANT'}),c['mass_g'])
 def test_ui_landing_lock_visual_payload_and_comms(self):
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30);self.assertFalse(a.exception)
  for tier in ['t1','t2']:
   w=a.checkbox(key='sensor_'+tier+'_perch_camera');self.assertFalse(w.value);self.assertTrue(w.disabled)
  self.assertFalse(a.checkbox(key='sensor_flight_visible').value)
  a.slider(key='mission_payload').set_value(.2).run(timeout=30)
  a.checkbox(key='sensor_t2_visible').check().run(timeout=30);self.assertFalse(a.exception)
  self.assertTrue(any('Visual ISR camera' in str(d.value) for d in a.dataframe))
  before=a.session_state['envelope_result']['settings']['nonbattery_kg']
  for phase in ['prep','flight','passive','active']:a.checkbox(key='comms_'+phase+'_satcom').uncheck()
  a.run(timeout=30);self.assertFalse(a.exception)
  after=a.session_state['envelope_result']['settings']['nonbattery_kg']
  self.assertAlmostEqual(before-after,.4872)
