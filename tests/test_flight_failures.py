import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from atmosphere import conditions
from payload_sizing import size_payload,diagnose_payload
ROOT=Path(__file__).resolve().parents[1]
class FlightFailureTests(unittest.TestCase):
 def args(self,wind):
  return dict(hardware_kg=3.845,sensor_kg=.06,minimum_other_kg=1.455,rho=conditions(0,25)['density_kg_m3'],wind=wind,tier1_w=1.23,tier2_w=6.41,comms_w=62.9,good_pct=100,checkins=1,tier2_min_day=1)
 def test_screenshot_closes_in_still_air(self):
  for payload in [.5,.55]:
   r=size_payload(payload,8.2/1.609344,1,**self.args(0))
   self.assertIsNotNone(r)
   self.assertLess(r['result']['mass_lb'],20)
 def test_headwind_is_a_real_energy_limit(self):
  args=self.args(20)
  self.assertIsNone(size_payload(.55,8.2/1.609344,1,**args))
  d=diagnose_payload(.55,8.2/1.609344,**args)
  self.assertEqual(d['reason'],'Insertion and recovery energy')
  self.assertLess(d['energy_margin_wh'],0)
  self.assertTrue(d['checks']['Peak battery power'])
  self.assertAlmostEqual(d['usable_flight_energy_wh']-d['required_flight_energy_wh'],d['energy_margin_wh'])
 def test_ui_can_recover_from_a_failure(self):
  a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
  self.assertEqual(a.slider(key='mission_wind').value,0.)
  a.slider(key='mission_payload').set_value(.55);a.slider(key='mission_range').set_value(8.2);a.slider(key='mission_wind').set_value(10.3);a.run(timeout=30)
  self.assertFalse(a.exception)
  self.assertTrue(any('Insertion and recovery energy' in x.value for x in a.error))
  self.assertTrue(any(x.label=='Payload computer power allowance (W)' for x in a.number_input))
  self.assertTrue(a.get('vega_lite_chart'))
  self.assertFalse(any(x.label=='Calculated total aircraft mass' for x in a.metric))
  a.slider(key='mission_wind').set_value(0.).run(timeout=30)
  self.assertFalse(a.exception)
  self.assertTrue(any(x.label=='Calculated total aircraft mass' for x in a.metric))
