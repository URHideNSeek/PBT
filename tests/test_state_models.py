import unittest
from model import DEFAULTS
from flight import power
from perched import simulate,recharge
from mission import size
class StateModelTests(unittest.TestCase):
 def test_reference_calibration(self):
  self.assertAlmostEqual(power(DEFAULTS['ref_kg'],DEFAULTS)['flight_w'],DEFAULTS['ref_w']+DEFAULTS['flight_electronics_w'])
 def test_low_density_affects_cruise(self):
  self.assertGreater(power(8.85,DEFAULTS|{'rho':.9})['flight_w'],power(8.85,DEFAULTS)['flight_w'])
 def test_hover_continuity(self):
  self.assertAlmostEqual(power(8.85,DEFAULTS|{'speed':0})['flight_w'],power(8.85,DEFAULTS)['hover_w'])
 def test_night_and_capacity_spill(self):
  night=simulate(100,100,6,19,24,90)
  self.assertAlmostEqual(night['end_wh'],94)
  day=simulate(99,100,6,9,24,90)
  self.assertEqual(day['end_wh'],100)
  self.assertGreater(day['spilled_wh'],0)
 def test_positive_daily_balance_does_not_protect_the_night(self):
  x=simulate(25,100,24,18,48,90,protected=10)
  self.assertLess(x['minimum_wh'],10)
  self.assertGreater(x['end_wh'],25)
 def test_charge_limits_and_efficiency(self):
  a=simulate(0,1000,6,9,0,120,charge_limit_w=2,charge_eff=.5)
  self.assertAlmostEqual(a['end_wh'],6)
 def test_cannot_recharge_before_sunrise(self):
  wait=recharge(50,100,10,60,19,24,120)
  self.assertGreater(wait,11)
 def test_flight_avionics_are_not_perched_loads(self):
  a=size(range_mi=1,wind=0,flight_electronics_w=0)
  b=size(range_mi=1,wind=0,flight_electronics_w=20)
  self.assertGreater(b['insertion_wh'],a['insertion_wh'])
  self.assertEqual(a['station_wh_day'],b['station_wh_day'])

 def test_temperature_disables_charging(self):
  r=size(range_mi=1,wind=0,charge_temperature_c=-10)
  self.assertFalse(r['charging_allowed'])
  self.assertEqual(r['charge_limit_w'],0)
 def test_array_peak_caps_harvest(self):
  r=size(range_mi=1,wind=0,good_pct=100,good_wh=10000)
  self.assertTrue(r['solar_profile_capped'])
  self.assertLess(r['solar_wh_day'],10000)
