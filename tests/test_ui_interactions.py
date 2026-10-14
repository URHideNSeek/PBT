import itertools,unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
class InteractionTests(unittest.TestCase):
 def test_all_controls_and_pair_triple_interactions(self):
  a=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=20)
  definitions=[]
  for kind in ['slider','number_input']:
   for w in getattr(a,kind):
    values=[(w.min,w.min),w.value,(w.max,w.max)] if isinstance(w.value,tuple) else [w.min,w.value,w.max if w.max is not None else max(1000.,w.value*10)]
    if w.label in {"Flight-ready mass, including payload (lb)","Range per leg (statute miles)","Perched time (hours)","Good solar days (%)","Scheduled communications check-ins per day","Tier 2 active minutes per day","Operating temperature range (°C)"}: definitions.append((kind,w.label,w.value,values))
  self.assertEqual(len(definitions),7)
  def set_value(kind,label,value):
   next(w for w in getattr(a,kind) if w.label==label).set_value(value)
  def run():
   a.run(timeout=20);self.assertEqual(len(a.exception),0)
  for kind,label,default,values in definitions:
   for v in sorted(set(values)):
    if isinstance(default,int):v=int(v)
    set_value(kind,label,v);run()
   set_value(kind,label,default)
  # Exercise all pairs/triples of the seven customer controls at endpoint mixtures.
  labels={'Flight-ready mass, including payload (lb)','Range per leg (statute miles)','Perched time (hours)','Good solar days (%)','Scheduled communications check-ins per day','Tier 2 active minutes per day','Operating temperature range (°C)'}
  core=[d for d in definitions if d[1] in labels]
  for n in [2,3]:
   for subset in itertools.combinations(core,n):
    for i,(kind,label,default,values) in enumerate(subset):
     v=values[0 if i%2==0 else 2]
     set_value(kind,label,int(v) if isinstance(default,int) else v)
    run()
    for kind,label,default,_ in subset:set_value(kind,label,default)
  for endpoint in [0,2]:
   for kind,label,default,values in definitions:
    v=values[endpoint];set_value(kind,label,int(v) if isinstance(default,int) else v)
   run()
  for kind,label,default,_ in definitions:set_value(kind,label,default)
  run()
  save=next(b for b in a.button if b.label=='Save mission to comparison');save.click();run()
  save=next(b for b in a.button if b.label=='Save mission to comparison');save.click();run()
  self.assertEqual(len(a.session_state['mission_scenarios']),1)
class DetailedUIBoundaryTests(unittest.TestCase):
 def test_all_detailed_parameter_boundaries(self):
  from model import F
  a=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'advanced_app.py')).run(timeout=20)
  for key,(_,default,low,high,_) in F.items():
   for value in sorted(set([low,default,high])):
    a.number_input(key=key).set_value(float(value)).run(timeout=20)
    self.assertEqual(len(a.exception),0)
   a.number_input(key=key).set_value(float(default))
  a.run(timeout=20);self.assertEqual(len(a.exception),0)
