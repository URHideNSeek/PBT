import unittest
from model import DEFAULTS,evaluate
class Tests(unittest.TestCase):
 def case(self,**kw): return evaluate(DEFAULTS|kw)
 def test_mass(self): self.assertAlmostEqual(self.case()['mass_kg'],8.85)
 def test_wind(self):
  r=self.case(); self.assertAlmostEqual(r['outbound_ground_kt'],15); self.assertAlmostEqual(r['return_ground_kt'],55)
 def test_impossible(self): self.assertFalse(self.case(wind=35.)['checks']['Route wind'])
 def test_crosswind(self): self.assertFalse(self.case(wind=40.,angle=90.)['checks']['Route wind'])
 def test_reserve_once(self):
  a=self.case(shade=0.); b=self.case(shade=0.,reserve=200.)
  self.assertAlmostEqual(a['margin_wh'],a['usable_wh']-a['mission_wh']); self.assertAlmostEqual(a['margin_wh']-b['margin_wh'],100.)
 def test_coupling(self): self.assertGreater(self.case(battery_kg=5.)['flight_w'],self.case()['flight_w'])
 def test_strict(self): self.assertFalse(self.case(prop=12.)['checks']['Prop diameter'])
 def test_night(self): self.assertEqual(self.case(arrival=19.)['harvest_wh'],0.)
 def test_validation(self):
  with self.assertRaises(ValueError): self.case(hours=.1)
 def test_soc(self):
  with self.assertRaises(ValueError): self.case(soc=10.)
 def test_zero_station(self): self.assertEqual(self.case(hours=0.,t2_min=0.,radio_min=0.)['station_wh'],0.)
