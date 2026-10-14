import unittest
from mission import temperature_capacity_factor,size
class TemperatureTests(unittest.TestCase):
 def test_worst_range_and_interpolation(self):
  self.assertEqual(temperature_capacity_factor(20,25),1.)
  self.assertEqual(temperature_capacity_factor(-20,50),.6)
  self.assertAlmostEqual(temperature_capacity_factor(-5,25),.8)
  with self.assertRaises(ValueError):temperature_capacity_factor(25,20)
 def test_cold_capacity_and_pack_sizing(self):
  warm=size(derate=.9)
  cold=size(derate=.9*temperature_capacity_factor(-20,25))
  self.assertLess(cold['battery_capacity_wh'],warm['battery_capacity_wh'])
  self.assertGreater(cold['required_nominal_average_solar_wh'],warm['required_nominal_average_solar_wh'])
  self.assertEqual(cold['engineering']['soc'],95.)
 def test_slider_updates_envelope_and_saved_trade(self):
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(__import__('pathlib').Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
  self.assertFalse(a.exception)
  before=a.session_state['envelope_result']['frame'].copy()
  a.slider(key='mission_temperature').set_value((-20,25)).run(timeout=30)
  self.assertFalse(a.exception)
  self.assertAlmostEqual(a.session_state['envelope_result']['settings']['capacity_factor'],.54)
  self.assertFalse(before.equals(a.session_state['envelope_result']['frame']))
  next(b for b in a.button if b.label=='Save mission to comparison').click().run(timeout=30)
  self.assertEqual(a.session_state['mission_scenarios'][0]['mission']['temperature_min_c'],-20)
