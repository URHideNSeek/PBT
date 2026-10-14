import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from streamlit.testing.v1 import AppTest
class UI(unittest.TestCase):
 def test_full_flow(self):
  app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
  self.assertFalse(app.exception)
  self.assertEqual([x.label for x in app.tabs],['Mission & Envelope','Engineering Sizing','BOM Options'])
  self.assertTrue(any('Wires / connectors reserve' in str(x.value) for x in app.dataframe))
  selector=next(x for x in app.selectbox if x.label=='Component sourcing')
  selector.set_value('Unrestricted sourcing').run()
  self.assertFalse(app.exception)
  self.assertTrue(any('Option 1' in x.value.columns and x.value['Option 1'].str.contains('RPX EmbIR UAV-640').any() for x in app.dataframe))
  next(x for x in app.slider if x.label=='Operating temperature range (°C)').set_value((-20,50)).run()
  self.assertFalse(app.exception)
  next(x for x in app.multiselect if x.label=='Tier 1 sensors').set_value(['thermal']).run()
  self.assertFalse(app.exception)
  self.assertTrue(any('both tiers' in x.value for x in app.error))
if __name__=='__main__':unittest.main()
