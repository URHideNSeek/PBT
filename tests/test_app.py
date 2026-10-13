import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
class AppTests(unittest.TestCase):
 def test_edit_and_save(self):
  a=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=20)
  self.assertEqual(len(a.exception),0)
  a.number_input(key='wind').set_value(0.).run()
  self.assertEqual(len(a.exception),0)
  next(b for b in a.button if b.label=='Save to comparison matrix').click().run()
  self.assertEqual(len(a.session_state['scenarios']),1); self.assertEqual(len(a.exception),0)
