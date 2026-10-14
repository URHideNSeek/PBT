import unittest
from payload_sizing import size_payload
class PayloadSizingTests(unittest.TestCase):
 def solve(self,payload=.5,distance=.5):
  return size_payload(payload,distance,6,hardware_kg=3.8,sensor_kg=.1,minimum_other_kg=1.41,wind=0,tier1_w=1.3,tier2_w=6.4,comms_w=60,good_pct=100,checkins=1,tier2_min_day=1)
 def test_mass_closes_and_payload_counted_once(self):
  r=self.solve()['result']
  self.assertAlmostEqual(r['mass_lb']*.45359237,3.8+.5+r['battery_kg'])
  self.assertAlmostEqual(r['additional_payload_kg'],.4)
  self.assertTrue(r['mission_energy_feasible'])
 def test_more_payload_requires_more_aircraft_mass(self):
  self.assertGreater(self.solve(1.)['result']['mass_lb'],self.solve(.5)['result']['mass_lb'])
 def test_more_range_requires_more_battery(self):
  self.assertGreaterEqual(self.solve(distance=2.)['result']['battery_kg'],self.solve()['result']['battery_kg'])
 def test_payload_cannot_be_less_than_selected_sensors(self):
  self.assertIsNone(self.solve(0))
