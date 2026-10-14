import unittest
from mission import size
class MissionTests(unittest.TestCase):
 def test_more_range_requires_energy(self): self.assertGreater(size(range_mi=8)['required_nominal_no_solar_wh'],size(range_mi=6)['required_nominal_no_solar_wh'])
 def test_zero_checkins_retains_events(self):
  r=size(checkins=0); self.assertEqual(r['comms_min_day'],2.)
 def test_weather_changes_recharge(self): self.assertGreater(size(good_pct=100)['daily_balance_wh'],size(good_pct=0)['daily_balance_wh'])
 def test_more_tier2_more_energy(self): self.assertGreater(size(tier2_min_day=60)['station_wh_day'],size(tier2_min_day=10)['station_wh_day'])
 def test_mass_includes_allocations(self):
  r=size(); self.assertAlmostEqual(r['battery_kg']+r['nonbattery_kg'],19.5*.45359237)
 def test_impossible_mass(self):
  with self.assertRaises(ValueError): size(mass_lb=8,battery_fraction=.75)
