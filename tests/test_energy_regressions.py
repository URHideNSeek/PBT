import unittest
from mission import size
class EnergyRegressions(unittest.TestCase):
 def test_later_solar_cannot_rescue_insertion(self):
  r=size(range_mi=15,whkg=50,good_pct=100,good_wh=1000,days=30,tier1_w=0,tier2_w=0,comms_w=0)
  self.assertFalse(r['mission_energy_feasible'])
  self.assertIsNone(r['recovery_charge_h'])
 def test_capacity_clipping(self):
  r=size(range_mi=15,whkg=100,good_pct=100,good_wh=1000,days=30,tier1_w=0,tier2_w=0,comms_w=0,wind=0)
  self.assertLess(r['energy_margin_average_wh'],0)
 def test_empty_station_cannot_wait_for_sun(self):
  r=size(days=30,good_pct=100,good_wh=200,tier1_w=10)
  self.assertFalse(r['station_energy_feasible'])
  self.assertIsNone(r['recovery_charge_h'])
 def test_radio_cannot_run_more_than_day(self):
  with self.assertRaises(ValueError): size(checkins=48,checkin_min=60)
 def test_comms_accounting_sleep_once(self):
  a=size(wake_wh=1);b=size(wake_wh=11)
  self.assertAlmostEqual(a['energy_margin_average_wh']-b['energy_margin_average_wh'],10)
class SizingInvariants(unittest.TestCase):
 def test_more_range_more_no_solar_battery(self):
  last=0
  for i in range(1,31):
   r=size(range_mi=i*.5)
   self.assertGreater(r['required_nominal_no_solar_wh'],last);last=r['required_nominal_no_solar_wh']
 def test_more_good_sun_never_requires_more_battery(self):
  last=float('inf')
  for pct in range(101):
   r=size(good_pct=pct)
   self.assertLessEqual(r['required_nominal_average_solar_wh'],last+1e-8);last=r['required_nominal_average_solar_wh']
 def test_higher_capacity_never_reduces_margin(self):
  last=-float('inf')
  for whkg in range(50,601,5):
   r=size(whkg=whkg)
   self.assertGreaterEqual(r['energy_margin_average_wh'],last-1e-8);last=r['energy_margin_average_wh']
 def test_reposition_wind_cost(self):
  a=size(wind=0,good_pct=100,good_wh=300,days=.25)
  b=size(wind=20,good_pct=100,good_wh=300,days=.25)
  self.assertGreaterEqual(b['reposition_charge_h'] or 0,a['reposition_charge_h'] or 0)
 def test_nonfinite_rejected(self):
  for value in [float('nan'),float('inf'),-float('inf')]:
   with self.assertRaises(ValueError):size(checkins=value)
