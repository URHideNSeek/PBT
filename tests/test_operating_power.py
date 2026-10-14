import unittest
from components import SENSORS,sensor_plan,operating_power
from mission import size
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
def plan(t2=10,t1=None):
 keys=['environment','visible','thermal'];profiles={}
 for k in keys:
  _,g,w,s,r,b=SENSORS[k]
  profiles[k]=dict(quantity=1,mass_g=g,active_w=w,sleep_w=s,logged_mbps=r,supply_v=5.,interface=b,performance={},open_requirements=[])
 return sensor_plan(t1 or ['environment'],['visible','thermal'],profiles,1,t2,0.)
class OperatingPowerTests(unittest.TestCase):
 def test_sleep_baseline_and_tier2_wake(self):
  x=operating_power(plan())
  self.assertLess(x['tier1_w'],1.5)
  self.assertAlmostEqual(x['tier2_compute_increment_w'],2.95)
 def test_continuous_tier1_camera_keeps_compute_awake(self):
  x=operating_power(plan(t1=['visible']))
  self.assertEqual(x['computer_baseline_w'],3)
  self.assertEqual(x['tier2_compute_increment_w'],0)
  self.assertEqual(x['comms_compute_increment_w'],0)
 def test_counts_minutes_drive_daily_energy(self):
  x=operating_power(plan(t2=0));y=operating_power(plan(t2=60))
  a=size(tier1_w=x['tier1_w'],tier2_w=x['tier2_w'],tier2_min_day=0,comms_w=x['comms_increment_w'],checkins=0,events_day=0)
  b=size(tier1_w=x['tier1_w'],tier2_w=x['tier2_w'],tier2_min_day=0,comms_w=x['comms_increment_w'],checkins=12,checkin_min=2,events_day=0)
  self.assertAlmostEqual(b['station_wh_day']-a['station_wh_day'],x['comms_increment_w']*24/60)
  c=size(tier1_w=y['tier1_w'],tier2_w=y['tier2_w'],tier2_min_day=60,comms_w=y['comms_increment_w'],checkins=0,events_day=0)
  self.assertAlmostEqual(c['station_wh_day']-a['station_wh_day'],y['tier2_w'])
 def test_recharge_full_and_no_net_solar(self):
  a=size(range_mi=1,wind=0,tier1_w=1.2,tier2_min_day=10,good_pct=100,good_wh=90,tier2_w=5,comms_w=60)
  self.assertGreater(a['daily_balance_wh'],0)
  self.assertIsNotNone(a['recharge_to_full_h'])
  self.assertAlmostEqual(a['recharge_to_full_h'],(a['battery_capacity_wh']-a['end_station_energy_wh'])/a['daily_balance_wh']*24)
  b=size(range_mi=1,wind=0,tier1_w=1.2,good_pct=0,bad_wh=0)
  self.assertIsNone(b['recharge_to_full_h'])
 def test_ui_schedule_and_two_mass_series(self):
  a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
  self.assertFalse(a.exception)
  before=float(next(x for x in a.metric if x.label=='Perched consumption').value.split()[0])
  self.assertIn('Total aircraft mass (lb)',a.session_state['envelope_result']['frame'])
  a.slider(key='mission_checkins').set_value(12).run(timeout=30)
  after=float(next(x for x in a.metric if x.label=='Perched consumption').value.split()[0])
  self.assertGreater(after,before)
  a.slider(key='mission_tier2').set_value(360).run(timeout=30)
  self.assertFalse(a.exception)
  self.assertGreater(float(next(x for x in a.metric if x.label=='Perched consumption').value.split()[0]),after)
