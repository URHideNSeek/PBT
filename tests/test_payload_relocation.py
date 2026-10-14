import unittest
from mission import size
from envelope import payload_boundary
class PayloadAndReturnTests(unittest.TestCase):
 def test_payload_decreases_with_range(self):
  args=dict(mass_lb=19.5,nonbattery_kg=4.35,sensor_kg=.454,wind=0,tier1_w=1,tier2_w=0,comms_w=0,good_pct=100)
  short=payload_boundary(1,6,**args);long=payload_boundary(6,6,**args)
  self.assertIsNotNone(short);self.assertIsNotNone(long)
  self.assertGreater(short['Payload mass (lb)'],long['Payload mass (lb)'])
  self.assertTrue(long['result']['return_reserve_preserved'])
  gross=19.5*.45359237
  self.assertAlmostEqual(long['result']['battery_kg']+4.35+long['Additional payload (kg)'],gross)
 def test_return_reserve_cannot_be_borrowed_for_persistence(self):
  r=size(range_mi=3,days=30,good_pct=0,tier1_w=1,wind=0)
  self.assertFalse(r['return_reserve_preserved'])
  self.assertFalse(r['mission_energy_feasible'])
  self.assertIsNone(r['relocation_charge_h'])
  self.assertGreaterEqual(r['maximum_protected_perched_hours'],0)
 def test_positive_future_sun_cannot_replace_arrival_return_reserve(self):
  r=size(range_mi=6,whkg=100,good_pct=100,good_wh=1000,days=1,tier1_w=0,tier2_w=0,comms_w=0,wind=0)
  self.assertFalse(r['return_reserve_preserved'])
  self.assertFalse(r['mission_energy_feasible'])
 def test_relocation_protects_next_perch_return(self):
  r=size(range_mi=3,reposition_mi=3,wind=0,tier1_w=1,good_pct=100,good_wh=300)
  self.assertEqual(r['next_perch_return_distance_mi'],3)
  self.assertAlmostEqual(r['relocation_flight_wh'],r['insertion_wh'])
  self.assertAlmostEqual(r['retrieval_wh'],r['insertion_wh'])
  self.assertAlmostEqual(r['relocation_required_wh'],2*r['insertion_wh']+r['engineering']['reserve']+r['battery_capacity_wh']*.2)
  expected=r['relocation_flight_wh']+r['next_perch_return_wh']+r['engineering']['reserve']+r['battery_capacity_wh']*.2
  self.assertAlmostEqual(r['relocation_required_wh'],expected)
 def test_thirty_day_solar_case_can_close_with_low_load(self):
  r=size(range_mi=1,days=30,wind=0,good_pct=100,good_wh=90,tier1_w=1,tier2_w=0,comms_w=0)
  self.assertTrue(r['return_reserve_preserved'])
  self.assertEqual(r['relocation_charge_h'],0)

 def test_symmetric_baseline_with_wind(self):
  r=size(range_mi=2,reposition_mi=2,wind=20)
  self.assertAlmostEqual(r['insertion_wh'],r['retrieval_wh'])
  self.assertAlmostEqual(r['hop_threshold_wh'],2*r['leg_energy_wh']+r['engineering']['reserve']+r['battery_capacity_wh']*.2)
  self.assertAlmostEqual(r['persist_entry_wh'],r['battery_capacity_wh']*.95-r['leg_energy_wh'])
 def test_route_override(self):
  r=size(range_mi=2,reposition_mi=2,next_return_mi=4,symmetric_legs=False,wind=20)
  self.assertEqual(r['next_perch_return_distance_mi'],4)
  self.assertNotEqual(r['insertion_wh'],r['retrieval_wh'])
