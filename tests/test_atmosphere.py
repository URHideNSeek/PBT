import unittest
from atmosphere import conditions
from flight import power
from model import DEFAULTS
class AtmosphereTests(unittest.TestCase):
 def test_standard_sea_level(self):
  r=conditions(0,15)
  self.assertAlmostEqual(r['density_kg_m3'],1.225,places=5)
  self.assertAlmostEqual(r['density_altitude_m'],0,places=5)
 def test_isa_altitude(self):
  r=conditions(2000,15-.0065*2000)
  self.assertAlmostEqual(r['density_altitude_m'],2000,places=5)
 def test_hot_high_requires_more_hover_power(self):
  lo=conditions(0,20);hi=conditions(2000,40)
  self.assertLess(hi['density_kg_m3'],lo['density_kg_m3'])
  self.assertGreater(hi['density_altitude_m'],2000)
  self.assertGreater(power(5.,DEFAULTS|{'rho':hi['density_kg_m3']})['hover_w'],power(5.,DEFAULTS|{'rho':lo['density_kg_m3']})['hover_w'])
 def test_extreme_selectors_remain_in_solver_bounds(self):
  for h in [-500,5000]:
   for t in [-20,50]:self.assertTrue(.5<=conditions(h,t)['density_kg_m3']<=1.5)
