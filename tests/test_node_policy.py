import unittest
from payload_sizing import size_payload
from perched import sensor_node
class NodePolicyTests(unittest.TestCase):
 def case(self,**kw):
  args=dict(hardware_kg=3.8,sensor_kg=.1,minimum_other_kg=1.4,wind=0,tier1_w=1.3,tier2_w=6.4,comms_w=60,good_pct=100,checkins=1,tier2_min_day=1)
  hours=kw.pop('requested_hours',24)
  args.update(kw)
  return size_payload(.5,1,hours,**args)
 def test_station_selection_does_not_resize_aircraft(self):
  a=self.case();b=self.case(requested_hours=72,good_pct=0,tier2_min_day=360,checkins=48)
  self.assertIsNotNone(a);self.assertIsNotNone(b)
  self.assertAlmostEqual(a['result']['mass_lb'],b['result']['mass_lb'])
  self.assertAlmostEqual(a['result']['battery_kg'],b['result']['battery_kg'])
  self.assertFalse(b['result']['good_day_sustainable'])
  self.assertGreater(b['result']['sleep_hours'],0)
 def test_hysteresis_protects_return_with_solar(self):
  r=sensor_node(16,40,24,18,120,90,protected=10,sleep_w=.1,wake_margin_wh=5,sleep_margin_wh=2,start_asleep=True)
  self.assertGreater(r['sleep_hours'],0)
  self.assertGreaterEqual(r['minimum_wh'],10)
  self.assertTrue(any(x['State']=='Active' for x in r['rows']))
 def test_hop_threshold_is_not_protected(self):
  a=self.case()['result']
  self.assertLess(a['recovery_threshold_wh'],a['hop_threshold_wh'])
  self.assertEqual(a['sleep_threshold_wh'],a['recovery_threshold_wh']+3)
