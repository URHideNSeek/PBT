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
   a.checkbox(key='sensor_t1_'+key).uncheck()
   a.checkbox(key='sensor_t2_'+key).uncheck()
  a.slider(key='mission_tier2').set_value(0).run(timeout=30)
  self.assertFalse(a.exception)
  self.assertTrue(all(a.checkbox(key='sensor_flight_'+key).value for key in REQUIRED_SENSOR_HOSTS))
  self.assertTrue(any('Required perch distance sensor' in str(x.value) for x in a.dataframe))

  before=a.session_state['envelope_result']['settings']['nonbattery_kg']
  a.checkbox(key='sensor_t1_visible').check().run(timeout=30)
  self.assertFalse(a.exception)
  self.assertEqual(a.session_state['envelope_result']['settings']['nonbattery_kg'],before)
  self.assertGreater(a.session_state['envelope_result']['component_plan']['daily_gb'],0)
