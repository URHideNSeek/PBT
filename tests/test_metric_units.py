import unittest
from metric_units import metric_view
class MetricTests(unittest.TestCase):
 def test_nested_constraints(self):
  v=metric_view({'mass_lb':12.,'range_mi':6.,'engineering':{'prop':10.,'wind':20.},'requirements':{'torque_kgcm':{'op':'>=','value':5.},'diameter_in':{'op':'==','value':10.}}})
  self.assertAlmostEqual(v['mass_kg'],5.44310844)
  self.assertAlmostEqual(v['range_km'],9.656064)
  self.assertEqual(v['engineering']['prop_mm'],254.)
  self.assertAlmostEqual(v['requirements']['torque_nm']['value'],.4903325)
 def test_exact_si_preferred(self):
  self.assertEqual(metric_view({'flight_ready_kg':5.,'flight_ready_lb':12.}),{'flight_ready_kg':5.})
