import unittest,math
from mission import size
from sizing import derive
class SizingTests(unittest.TestCase):
 def test_disk_loading(self):
  r=size();s=derive(r)
  self.assertAlmostEqual(s['disk_loading_kg_m2']*s['total_disk_area_m2'],s['flight_ready_kg'])
 def test_rpm_coefficient_scaling(self):
  r=size();a=derive(r,thrust_coefficient=.1);b=derive(r,thrust_coefficient=.2)
  self.assertAlmostEqual(a['estimated_hover_rpm']/b['estimated_hover_rpm'],math.sqrt(2))
 def test_inverse_thrust(self):
  r=size();s=derive(r);p=r['engineering'];d=p['prop']*.0254
  t=s['assumed_thrust_coefficient']*p['rho']*(s['estimated_hover_rpm']/60)**2*d**4
  self.assertAlmostEqual(t,s['hover_thrust_per_rotor_kgf']*9.80665)
 def test_voltage_accounting(self):
  s=derive(size(),nominal_voltage=24)
  self.assertAlmostEqual(s['required_pack_ah_average_solar']*24,s['battery_nominal_required_average_solar_wh'])
  self.assertAlmostEqual(s['peak_battery_current_a']*18,s['estimated_maneuver_electrical_w'])
 def test_ui_tabs(self):
  from pathlib import Path
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=20)
  self.assertEqual(len(a.exception),0)
  self.assertEqual([x.label for x in a.tabs],['Mission & Envelope','Engineering Sizing','BOM Options'])
  next(b for b in a.button if b.label=='Save mission to comparison').click().run()
  next(w for w in a.selectbox if w.label=='Sizing for').set_value('Saved: Mission concept').run()
  self.assertEqual(len(a.exception),0)
class EnvelopeSizingUI(unittest.TestCase):
 def test_select_boundary_case(self):
  from pathlib import Path
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=20)
  next(b for b in a.button if b.label=='Calculate payload envelope').click().run(timeout=20)
  next(w for w in a.selectbox if w.label=='Sizing for').set_value('Envelope point').run(timeout=20)
  self.assertEqual(len(a.exception),0)
  self.assertTrue(any(w.label=='Envelope range per leg (km)' for w in a.selectbox))
class AssumptionValidation(unittest.TestCase):
 def test_nominal_cannot_be_below_loaded_voltage(self):
  with self.assertRaises(ValueError):derive(size(),nominal_voltage=12)
