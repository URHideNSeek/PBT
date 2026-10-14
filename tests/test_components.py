import sys,unittest,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from components import sensor_plan,bom,match,SENSORS
from mission import size
from sizing import derive

def profile(key):
 _,m,a,s,r,b=SENSORS[key]
 return dict(quantity=1,mass_g=m,active_w=a,sleep_w=s,logged_mbps=r,supply_v=5.,interface=b,performance={},open_requirements=[])
class Components(unittest.TestCase):
 def test_duty_and_increment_no_double_count(self):
  p=sensor_plan(['environment'],['thermal'],{k:profile(k) for k in ['environment','thermal']},.5,60,5.)
  expected=5+(.1+.005)/2+.02+(1.5-.02)/24
  self.assertAlmostEqual(p['tier1_w']+p['tier2_w']/24,expected)
  self.assertAlmostEqual(p['sensor_kg'],.12)
 def test_overlap_rejected(self):
  with self.assertRaises(ValueError):sensor_plan(['thermal'],['thermal'],{'thermal':profile('thermal')},1,60,5)
 def test_mass_reserve_blocks_infeasible_trade(self):
  with self.assertRaises(ValueError):size(mass_lb=12,battery_fraction=.5,minimum_other_kg=2.)
 def test_match_responds_to_temperature_mass_power_compliance(self):
  c=json.loads((Path(__file__).parents[1]/'catalog.json').read_text())
  row=dict(id='sensor_thermal',sourcing=True,mass_each_g=100.,requirements=dict(temp_min_c=20,temp_max_c=25,supply_v=5.,power_w_max=1.5,interface='USB',pixels_x=640,pixels_y=480,fps=30),open_requirements=[])
  self.assertEqual(len(match([row],c,False)[0]['options']),1)
  self.assertEqual(len(match([row],c,True)[0]['options']),0)
  for k,v in [('temp_min_c',-30),('power_w_max',.5),('pixels_x',1280)]:
   r=copy.deepcopy(row);r['requirements'][k]=v
   self.assertFalse(match([r],c,False)[0]['options'])
  row['mass_each_g']=5;self.assertFalse(match([row],c,False)[0]['options'])
 def test_unknown_and_open_requirements_block(self):
  row=dict(id='battery',sourcing=True,mass_each_g=100,requirements={'capacity_wh':100},open_requirements=['Test'])
  c=[dict(id='fake',category='battery',source_url='https://example.com',verified_on='2026-10-14',attributes={'mass_g':50,'capacity_wh':200})]
  self.assertFalse(match([row],c,False)[0]['options'])
 def test_option_cap_and_dedupe(self):
  row=dict(id='sensor_light',sourcing=True,mass_each_g=100,requirements={},open_requirements=[])
  c=[dict(id=str(i),category='sensor_light',source_url='https://example.com',verified_on='2026-10-14',attributes={'mass_g':i+1}) for i in range(10)]
  self.assertEqual(len(match([row],c+c,False)[0]['options']),3)
if __name__=='__main__':unittest.main()
