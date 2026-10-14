import unittest
from envelope import maximum_range
class EnvelopeTests(unittest.TestCase):
 def test_zero_scheduled_activity(self):
  self.assertIsNotNone(maximum_range(19,6,checkins=0,tier2_min_day=0))
 def test_mass_shortfall(self):self.assertIsNone(maximum_range(10,6))
 def test_longer_station_less_range(self):self.assertLess(maximum_range(19.5,72),maximum_range(19.5,6))
 def test_more_solar_more_range(self):self.assertGreaterEqual(maximum_range(19.5,24,good_pct=100),maximum_range(19.5,24,good_pct=50))
 def test_boundary(self):
  from mission import size
  m=19.5;rng=maximum_range(m,6);fraction=(m*.45359237-4.35)/(m*.45359237)
  self.assertTrue(size(mass_lb=m,range_mi=rng,days=.25,battery_fraction=fraction,good_pct=100,checkins=1,tier2_min_day=1)['mission_energy_feasible'])
  self.assertFalse(size(mass_lb=m,range_mi=rng+.001,days=.25,battery_fraction=fraction,good_pct=100,checkins=1,tier2_min_day=1)['mission_energy_feasible'])
class EnvelopeUI(unittest.TestCase):
 def test_calculate_and_store_chart(self):
  from pathlib import Path
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=20)
  next(b for b in a.button if b.label=='Calculate mass envelope').click().run(timeout=20)
  self.assertEqual(len(a.exception),0)
  self.assertEqual(a.session_state['envelope_result']['frame'].shape,(120,5))
