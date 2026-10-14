"""Preliminary coupled sizing; defaults are assumptions, not verified performance."""
from math import pi,sqrt,cos,radians,isfinite
# label, default, min, max, section
F={
'battery_kg':('Installed battery kg',4.5,.1,10.,'Mass'),
'other_kg':('Structure / mechanisms / wiring / exterior kg',1.27,0.,8.,'Mass'),
'propulsion_kg':('Installed propulsion kg',1.05,.1,5.,'Mass'),
'sensor_kg':('Installed sensor payload kg',.454,0.,5.,'Mass'),
'compute_kg':('Compute / navigation kg',.22,0.,3.,'Mass'),
'comms_kg':('Installed communications kg',.87,0.,4.,'Mass'),
'solar_kg':('Installed solar / charger kg',.25,0.,3.,'Mass'),
'growth_kg':('Growth allowance kg',.236,0.,3.,'Mass'),
'whkg':('Installed battery Wh/kg',322.,50.,600.,'Battery'),
'soc':('Operator departure SOC %',95.,1.,100.,'Battery'),
'floor':('Analysis minimum SOC %',20.,0.,90.,'Battery'),
'derate':('Temperature / age capacity factor',.9,.01,1.,'Battery'),
'voltage':('Minimum loaded bus voltage V',18.,5.,60.,'Battery'),
'wkg':('Battery continuous W/kg',1000.,100.,5000.,'Battery'),
'peak_wkg':('Battery peak W/kg',1500.,100.,8000.,'Battery'),
'prop':('Assembled prop diameter in',11.5,3.,24.,'Flight'),
'rotors':('Rotor count',4.,2.,12.,'Flight'),
'rho':('Air density kg/m³',1.225,.5,1.5,'Flight'),
'eff':('Hover ideal-to-electrical efficiency',.6,.1,.9,'Flight'),
'thrust':('Continuous thrust per rotor at scenario conditions kgf',3.5,.1,10.,'Flight'),
'ratio':('Required thrust-to-weight ratio',1.5,1.,3.,'Flight'),
'ref_w':('Reference cruise propulsion power W',1800.,100.,6000.,'Flight'),
'ref_kg':('Reference cruise mass kg',8.85,.5,15.,'Flight'),
'ref_prop':('Reference prop diameter in',11.5,3.,24.,'Flight'),
'ref_speed':('Reference airspeed kt',35.,5.,80.,'Flight'),
'drag':('Effective drag area CdA m²',.06,0.,.5,'Flight'),
'drive_eff':('Drag electrical efficiency',.75,.2,1.,'Flight'),
'speed':('True airspeed kt',35.,5.,80.,'Mission'),
'wind':('Steady wind kt',20.,0.,50.,'Mission'),
'angle':('Wind FROM angle vs outbound track deg',0.,0.,180.,'Mission'),
'out_mi':('Insertion statute miles',6.,0.,50.,'Mission'),
'back_mi':('Reciprocal retrieval statute miles',6.,0.,50.,'Mission'),
'hover_min':('Total approach / hover min',1.,0.,30.,'Mission'),
'climb_m':('Total positive climb m',20.,0.,1000.,'Mission'),
'transition_wh':('Perch / transform / release Wh',20.,0.,200.,'Mission'),
'reserve':('Landing / contingency reserve Wh',100.,0.,1000.,'Mission'),
'hours':('Persist duration h',6.,0.,720.,'Station'),
'base_w':('Shared stationary housekeeping W',1.,0.,100.,'Station'),
't1_w':('Incremental Tier 1 active W',4.,0.,100.,'Station'),
'duty':('Tier 1 duty %',100.,0.,100.,'Station'),
 't2_w':('Incremental Tier 2 W',40.,0.,200.,'Station'),
 't2_min':('Total Tier 2 min per mission',10.,0.,1000.,'Station'),
 'radio_w':('Incremental communications W',60.,0.,200.,'Station'),
 'radio_min':('Total communications min per mission',10.,0.,1000.,'Station'),
 'solar':('Solar surface diameter in',15.5,1.,30.,'Solar'),
 'active':('Solar active area fraction',.82,0.,1.,'Solar'),
 'cell_eff':('Cell efficiency',.24,.01,.5,'Solar'),
 'charger_eff':('Solar-to-battery efficiency',.9,.1,1.,'Solar'),
 'shade':('Orientation / shading factor',.75,0.,1.,'Solar'),
 'sun_h':('Equivalent full sun hours/day',5.,0.,12.,'Solar'),
 'arrival':('Station arrival local solar hour',9.,0.,23.99,'Solar'),
 'mb':('Encoded transfer decimal MB',2.5,0.,1000.,'Data'),
 'kbps':('Effective application uplink kbps',100.,.1,100000.,'Data'),
 'storage':('Usable storage decimal GB',64.,.1,2000.,'Data'),
 'data_rate':('Stored data MB/h',20.,0.,10000.,'Data'),
 'ambient':('Station ambient °C',30.,-40.,70.,'Thermal'),
 'thermal_r':('Enclosure thermal resistance °C/W',1.,.01,10.,'Thermal'),
 'sun_heat':('Absorbed solar heat W',5.,0.,200.,'Thermal'),
 'temp_max':('Internal operating limit °C',60.,0.,120.,'Thermal'),
 'mass_max':('Strict aircraft limit lb',20.,1.,55.,'Limits'),
 'prop_max':('Strict prop limit in',12.,2.,30.,'Limits'),
 'solar_max':('Strict solar limit in',16.,2.,40.,'Limits')}
DEFAULTS={k:v[1] for k,v in F.items()}
MASS=[k for k in F if k.endswith('_kg') and k!='ref_kg']
def validate(p):
 if set(p)!=set(F): raise ValueError('Scenario does not match parameter schema')
 for k,v in p.items():
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) or not F[k][2]<=v<=F[k][3]: raise ValueError('Invalid parameter: '+k)
 if p['rotors']!=int(p['rotors']): raise ValueError('Rotor count must be integral')
 if p['soc']<=p['floor']: raise ValueError('Departure SOC must exceed analysis floor')
 if max(p['t2_min'],p['radio_min'])>p['hours']*60: raise ValueError('Activity exceeds Persist duration')
def evaluate(p):
 validate(p)
 m=sum(p[k] for k in MASS); area=p['rotors']*pi*(p['prop']*.0254/2)**2
 hover=(m*9.80665)**1.5/sqrt(2*p['rho']*area)/p['eff']
 drag=lambda kt:.5*p['rho']*p['drag']*(kt*.514444)**3/p['drive_eff']
 flight=max(0.,p['ref_w']-drag(p['ref_speed']))*(m/p['ref_kg'])**1.5*p['ref_prop']/p['prop']+drag(p['speed'])
 head=p['wind']*cos(radians(p['angle'])); cross2=max(0.,p['wind']**2-head**2)
 along=sqrt(max(0.,p['speed']**2-cross2)); go=along-head; back=along+head
 possible=cross2<p['speed']**2 and min(go,back)>0
 nominal=p['battery_kg']*p['whkg']; capacity=nominal*p['derate']; floor=capacity*p['floor']/100; start=capacity*p['soc']/100
 aux=hover*p['hover_min']/60+m*9.80665*p['climb_m']/3600/p['drive_eff']+p['transition_wh']
 load=p['base_w']+p['t1_w']*p['duty']/100
 extra=(p['t2_w']*p['t2_min']+p['radio_w']*p['radio_min'])/60
 station=load*p['hours']+extra
 peak=pi*(p['solar']*.0254/2)**2*p['active']*1000*p['cell_eff']*p['charger_eff']; daily=peak*p['sun_h']*p['shade']
 trace=[]; harvest=0.; spill=0.; margin=None; mission=None; minutes=None; minimum=None
 if possible:
  out_h=p['out_mi']/1.150779/go; back_h=p['back_mi']/1.150779/back; minutes=(out_h+back_h)*60
  insertion=flight*out_h+aux/2; retrieval=flight*back_h+aux/2
  energy=start-insertion; minimum=energy; protected=floor+retrieval+p['reserve']
  trace=[{'Station hour':0.,'Battery Wh':energy,'Recovery protected Wh':protected}]
  steps=max(1,int(p['hours']*12+.999999)); dt=p['hours']/steps
  for i in range(steps):
   hour=(p['arrival']+(i+.5)*dt)%24
   incoming=daily/12*dt if 6<=hour<18 else 0.; harvest+=incoming
   next_energy=energy+incoming-load*dt-(extra*dt/p['hours'] if p['hours'] else 0.)
   spill+=max(0.,next_energy-capacity); energy=min(capacity,next_energy); minimum=min(minimum,energy)
   trace.append({'Station hour':(i+1)*dt,'Battery Wh':energy,'Recovery protected Wh':protected})
  margin=energy-retrieval-floor-p['reserve']; mission=flight*(out_h+back_h)+aux+station+p['reserve']
 required=m*p['ratio']/p['rotors']; peak_w=hover*p['ratio']**1.5
 transfer=p['mb']*8000/p['kbps']/60
 temp=p['ambient']+p['thermal_r']*(p['base_w']+p['t1_w']+p['t2_w']+p['radio_w']+p['sun_heat'])
 checks={'Mass':m*2.2046226218<p['mass_max'],'Prop diameter':p['prop']<p['prop_max'],'Solar diameter':p['solar']<p['solar_max'],'Route wind':possible,'Continuous thrust':p['thrust']>=required,'Continuous battery power':p['battery_kg']*p['wkg']>=max(hover,flight),'Peak battery power':p['battery_kg']*p['peak_wkg']>=peak_w,'Mission energy':possible and margin>=0,'Station SOC floor':possible and minimum>=floor,'Transfer deadline':transfer<=p['radio_min'],'Storage':p['data_rate']*p['hours']<=p['storage']*1000,'Peak station thermal':temp<=p['temp_max']}
 return dict(mass_lb=m*2.2046226218,mass_kg=m,nominal_wh=nominal,usable_wh=start-floor,hover_w=hover,flight_w=flight,peak_w=peak_w,peak_current_a=peak_w/p['voltage'],thrust_required_kgf=required,disk_loading_kg_m2=m/area,outbound_ground_kt=go,return_ground_kt=back,flight_minutes=minutes,mission_wh=mission,station_wh=station,solar_peak_w=peak,solar_daily_wh=daily,harvest_wh=harvest,spill_wh=spill,margin_wh=margin,required_whkg_no_solar=mission/(p['battery_kg']*p['derate']*(p['soc']-p['floor'])/100) if possible else None,transfer_min=transfer,temperature_c=temp,checks=checks,trace=trace)
