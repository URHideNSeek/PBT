"""Mission-derived COTS allocations and evidence-based product screening.
All default sensor mass, power and logged-rate figures are planning allowances.
A match is a per-row specification screen, not an integrated qualification.
"""
from math import isfinite
# label, installed mass g, active W, sleep W, logged Mbps, interface
SENSORS={
 'environment':('Temperature / humidity',5.,.05,.001,.00001,'I2C'),
 'pressure':('Barometric pressure',5.,.02,.001,.00001,'I2C'),
 'light':('Ambient light',5.,.02,.001,.00001,'I2C'),
 'acoustic':('Acoustic microphone',15.,.3,.01,.256,'USB'),
 'vibration':('Vibration / accelerometer',8.,.05,.001,.005,'SPI'),
 'visible':('Visible camera',30.,2.,.02,2.,'USB'),
 'thermal':('Thermal camera',50.,2.,.02,1.,'USB'),
 'range':('Rangefinder',20.,.5,.01,.002,'UART'),
 'gnss':('Mission GNSS receiver',30.,.5,.01,.001,'UART'),
 'rf':('Passive wideband RF receiver',100.,5.,.05,5.,'USB'),
 'radar':('Passive radar receiver',400.,10.,.1,10.,'USB'),
}

REQUIRED_SENSOR_HOSTS={
 'imu':'FCS','compass':'GPS','pressure':'FCS','gnss':'GPS','visible':'NAVCAM',
 'range':'PRNG','contact':'PCT','latch':'LCK','battery_health':'BAT',
}
# Required devices' mass is already in their host BOM row. Host electronics power
# is covered by the controller/GNSS/BMS baseline; camera/range idle and mission
# activation are separately accounted below.
SENSORS={
 'imu':('IMU — accelerometer / gyroscope',0.,0.,0.,.006,'UART'),
 'compass':('Magnetometer / compass',0.,0.,0.,.001,'UART'),
 'pressure':('Barometer',0.,0.,0.,.00001,'UART'),
 'gnss':('Flight GNSS receiver',0.,0.,0.,.001,'CAN'),
 'visible':('Navigation / perch camera',0.,1.5,.02,2.,'USB'),
 'range':('Perch distance sensor',0.,.5,.01,.002,'UART'),
 'contact':('Perch contact sensor',0.,.01,.005,.00001,'GPIO'),
 'latch':('Grip / latch position sensor',0.,.01,.005,.00001,'GPIO'),
 'battery_health':('Battery voltage / current / temperature',0.,0.,0.,.00001,'UART'),
 **{k:v for k,v in SENSORS.items() if k not in REQUIRED_SENSOR_HOSTS},
}

FIXED_PERCH_SENSOR_G=30.
FIXED_PERCH_SENSOR_SLEEP_W=.02

def sensor_plan(tier1,tier2,profiles,duty,tier2_min_day,base_w):
 if not 0<=duty<=1 or not 0<=tier2_min_day<=1440 or base_w<0:raise ValueError('Invalid sensor duty or base power')
 t2_fraction=tier2_min_day/1440
 keys=list(dict.fromkeys([*[k for k in REQUIRED_SENSOR_HOSTS if k in profiles],*tier1,*tier2]));devices=[]
 baseline=base_w;increment=0.;daily_gb=0.;mass=0.
 for key in keys:
  if key not in SENSORS:raise ValueError('Unknown sensor selection')
  p=profiles[key].copy();q=p['quantity']
  if key in REQUIRED_SENSOR_HOSTS:
   p['mass_g']=0.;p['quantity']=1;q=1
  if isinstance(q,bool) or int(q)!=q or q<1:raise ValueError('Sensor quantities must be positive integers')
  for name in ['mass_g','active_w','sleep_w','logged_mbps','supply_v']:
   if not isfinite(p[name]) or p[name]<0:raise ValueError('Invalid sensor allocation: '+name)
  if p['sleep_w']>p['active_w']:raise ValueError('Sensor sleep power cannot exceed active power')
  in1=key in tier1;in2=key in tier2
  # Tier 2 overrides idle periods for a shared device; installed mass is counted once.
  b=p['sleep_w']+(p['active_w']-p['sleep_w'])*(duty if in1 else 0)
  extra=(p['active_w']-b) if in2 else 0
  active_fraction=(duty if in1 else 0)+(1-(duty if in1 else 0))*t2_fraction*in2
  baseline+=q*b;increment+=q*extra;mass+=q*p['mass_g']
  gb=q*p['logged_mbps']*86400/8000*active_fraction;daily_gb+=gb
  devices.append({'key':key,'name':SENSORS[key][0],'required_flight_perch':key in REQUIRED_SENSOR_HOSTS,**p,'tier1':in1,'tier2':in2,'active_fraction':active_fraction,'daily_gb':gb})
 return {'devices':devices,'sensor_kg':mass/1000,'tier1_w':baseline,'tier2_w':increment,'daily_gb':daily_gb,'tier1_duty':duty,'tier2_min_day':tier2_min_day,'base_w':base_w,'status':'Provisional sensor allocations'}

def constraint(op,value):return {'op':op,'value':value}

def bom(result,sizing,plan,settings):
 p=result['engineering'];rows=[];g=p['rotors'];maxbus=settings['bus_max_v'];minbus=p['voltage']
 def add(id,name,category,qty,total_g,requirements=None,open_requirements=None,sourcing=True):
  if qty<=0:return
  req={'mass_g':constraint('<=',total_g/qty)} if sourcing else {}
  if sourcing:
   req.update(temp_min_c=constraint('<=',settings['temp_min_c']),temp_max_c=constraint('>=',settings['temp_max_c']))
  req.update(requirements or {})
  rows.append({'id':id,'component':name,'category':category,'quantity':int(qty),'mass_each_g':total_g/qty,'mass_total_g':total_g,'requirements':req,'open_requirements':open_requirements or [],'sourcing':sourcing})
 def bus():return {'voltage_min_v':constraint('<=',minbus),'voltage_max_v':constraint('>=',maxbus)}
 def rail(v):return {'voltage_min_v':constraint('<=',v),'voltage_max_v':constraint('>=',v)}
 margin=settings['current_margin'];pack_cont=sizing['continuous_battery_current_a']*margin;pack_peak=sizing['peak_battery_current_a']*margin
 add('BAT','Flight battery pack','battery',1,p['battery_kg']*1000,{
  'nominal_wh':constraint('>=',sizing['battery_nominal_required_average_solar_wh']),
  'nominal_voltage_v':constraint('between',[sizing['assumed_nominal_voltage_v']*.9,sizing['assumed_nominal_voltage_v']*1.1]),
  'voltage_min_v':constraint('>=',minbus),'voltage_max_v':constraint('<=',maxbus),
  'continuous_a':constraint('>=',pack_cont),'peak_a':constraint('>=',pack_peak),
  'voltage_sensing':constraint('==',True),'current_sensing':constraint('==',True),'temperature_sensing':constraint('==',True)},['Pack temperature capacity/power curves and allowed charging temperatures require verification'])
 prop_g=p['propulsion_kg']*1000
 add('MOT','Brushless motors','motor',int(g),prop_g*.65,{**bus(),'thrust_kgf':constraint('>=',sizing['continuous_thrust_per_rotor_kgf']),
  'tested_prop_in':constraint('==',p['prop']),'tested_voltage_v':constraint('between',[minbus,maxbus]),
  'continuous_w':constraint('>=',max(result['hover_w'],result['flight_w'])/g),'peak_w':constraint('>=',result['peak_w']/g),
  'rpm_max':constraint('>=',sizing['estimated_continuous_thrust_rpm'])},['Matched motor/ESC/prop test curve at required conditions; hub interface and thermal limits'])
 add('ESC','4-channel motor ESC','esc',1,prop_g*.12,{**bus(),'channels':constraint('>=',int(g)),
  'continuous_a_per_channel':constraint('>=',pack_cont/g),'peak_a_per_channel':constraint('>=',pack_peak/g),
  'protocols':constraint('contains_any',['DShot','PWM'])})
 add('PRO','Folding propellers with hubs','propeller',int(g),prop_g*.15,{
  'diameter_in':constraint('==',p['prop']),'folding':constraint('==',True),
  'rpm_max':constraint('>=',sizing['estimated_continuous_thrust_rpm']),
  'thrust_kgf':constraint('>=',sizing['continuous_thrust_per_rotor_kgf'])},['Rated folding hub/blade speed, motor mount and matched thrust evidence'])
 add('PMT','Motor mounts / rotating hardware','reserve',1,prop_g*.08,sourcing=False)
 comp_g=p['compute_kg']*1000
 add('FCS','Flight controller','flight_controller',1,comp_g*.1,{**bus(),'active_w':constraint('<=',settings['autopilot_w']),
  'pwm_outputs':constraint('>=',int(g)+settings['servo_qty']),'protocols':constraint('contains_any',['PX4','ArduPilot']),
  'interfaces':constraint('contains_all',['UART','CAN']),
  'accelerometer':constraint('==',True),'gyroscope':constraint('==',True),'barometer':constraint('==',True)})
 interfaces=sorted(set(['UART','USB']+[d['interface'] for d in plan['devices'] if d['key'] not in REQUIRED_SENSOR_HOSTS]))
 add('CMP','Payload computer','compute',1,comp_g*.65,{**rail(5.),'active_w':constraint('<=',settings['compute_w']),
  'ram_gb':constraint('>=',settings['ram_gb']),'interfaces':constraint('contains_all',interfaces)},['Processing throughput for selected sensors needs benchmark evidence'])
 storage=max(.1,plan['daily_gb']*settings['retention_days']*1.25)
 data_mbps=sum(d['logged_mbps']*d['quantity'] for d in plan['devices'])
 add('MEM','Data storage','storage',1,comp_g*.1,{'capacity_gb':constraint('>=',storage),
  'write_mbps':constraint('>=',data_mbps*1.25),'interface':constraint('in',['microSD','USB','NVMe'])})
 add('NAVCAM','Navigation / perch camera','visible',1,comp_g*.15,{**rail(5.),'active_w':constraint('<=',1.5),'interface':constraint('in',['USB','CSI']),
  'pixels_x':constraint('>=',1280),'pixels_y':constraint('>=',720),'fps':constraint('>=',30)},['Perch detection, field of view, low light and landing accuracy need definition'])
 add('GPS','Flight GNSS / compass','gnss',1,settings['navigation_g'],{**rail(5.),'active_w':constraint('<=',1.5),'accuracy_m':constraint('<=',settings['gnss_accuracy_m']),
  'update_hz':constraint('>=',5.),'interface':constraint('in',['UART','CAN']),'compass':constraint('==',True)})
 add('PRNG','Required perch distance sensor','range',1,20.,{**rail(5.),'active_w':constraint('<=',.5),'interface':constraint('in',['UART','I2C']),
  'range_m':constraint('>=',10.),'range_accuracy_cm':constraint('<=',5.),'sample_hz':constraint('>=',10.)},['Perch geometry, reflectivity, field of view and approach performance require verification'])
 add('PCT','Required perch contact sensor','contact',1,5.,{'interface':constraint('==','GPIO')},['Contact force/travel and debounce requirements need mechanism definition'])
 add('LCK','Required grip / latch position sensor','position_sensor',1,5.,{'interface':constraint('==','GPIO')},['Locked-position tolerance, independent secured-state verification and mechanism interface'])
 comm_g=p['comms_kg']*1000
 add('RF','Terrestrial mesh radio','radio',1,comm_g*.12,{**rail(settings['radio_supply_v']),'active_w':constraint('<=',settings['radio_w']),
  'frequency_min_mhz':constraint('<=',settings['frequency_mhz']),'frequency_max_mhz':constraint('>=',settings['frequency_mhz']),
  'application_mbps':constraint('>=',settings['link_mbps']),'installed_range_km':constraint('>=',settings['link_range_km']),
  'mesh_nodes':constraint('>=',6)},['Installed link budget with antennas, obscuration and selected band; peer/controller radio required'])
 add('LTE','Cellular modem','cellular',1,comm_g*.12,{**rail(5.),'active_w':constraint('<=',settings['radio_w']),
  'application_mbps':constraint('>=',settings['link_mbps']),'interface':constraint('in',['USB','Ethernet'])},['Carrier, coverage, certified bands, SIM and antenna installation'])
 add('SAT','Satellite modem / terminal','satcom',1,comm_g*.46,{**rail(settings['radio_supply_v']),'active_w':constraint('<=',settings['radio_w']),
  'application_mbps':constraint('>=',settings['link_mbps'])},['Satellite service, sky view, packet size/latency and installed antenna compatibility'])
 add('ANT','Communications antenna set','antenna_set',1,comm_g*.30,{'frequency_mhz':constraint('contains',settings['frequency_mhz'])},['Antenna gain/pattern, coax loss, LTE/SAT bands and mechanical envelope need allocation'])
 sol_g=p['solar_kg']*1000
 add('SOL','Solar cells / array','solar',1,sol_g*.72,{'installed_peak_w':constraint('>=',sizing['estimated_peak_battery_delivered_solar_w']/p['charger_eff']),
  'fit_area_m2':constraint('<=',sizing['active_solar_area_m2']),'fits_circular_diameter_in':constraint('<=',p['solar'])},['Installed array packing, IV curve, orientation and daily battery-delivered harvest qualification'])
 add('CHG','Solar MPPT charger','charger',1,sol_g*.28,{'output_voltage_max_v':constraint('>=',maxbus),
  'input_power_w':constraint('>=',sizing['estimated_peak_battery_delivered_solar_w']/p['charger_eff']),
  'mppt':constraint('==',True)},['Solar IV/input range, battery chemistry/BMS coordination and charge temperature cutoff'])
 station_peak=plan['tier1_w']+plan['tier2_w']+settings['radio_w']
 add('PWR','Power conversion / distribution','power',1,settings['regulator_g'],{**bus(),
  'output_power_w':constraint('>=',station_peak*margin),'output_rails_v':constraint('contains_all',sorted(set([5.,settings['servo_v']]+[d['supply_v'] for d in plan['devices']])))},['Branch current/inrush and actuator supply draw; protective devices and connector pinouts'])
 add('ACT','Perch / transformation actuators','actuator',settings['servo_qty'],settings['servo_qty']*settings['servo_g'],{**rail(settings['servo_v']),
  'torque_kgcm':constraint('>=',settings['servo_torque_kgcm']),'interface':constraint('==','PWM')},['Travel/speed, holding duty, actuator peak current, linkage loads and secured latch verification'])
 for d in plan['devices']:
  req={**rail(d['supply_v']),'active_w':constraint('<=',d['active_w']),'sleep_w':constraint('<=',d['sleep_w']),'interface':constraint('==',d['interface'])}
  lower={'pixels_x','pixels_y','fps','update_hz','lux_max','sample_khz','channels','snr_db','accel_range_g','bandwidth_hz','range_m','sample_hz','rf_max_mhz','rf_bandwidth_mhz','coherent_channels'}
  upper={'accuracy_m','temp_accuracy_c','humidity_accuracy_pct','pressure_min_hpa','pressure_accuracy_pa','range_accuracy_cm','rf_min_mhz'}
  for k,v in d['performance'].items():req[k]=constraint('>=' if k in lower or k=='pressure_max_hpa' else '<=' if k in upper else '==',v)
  if d['key'] in REQUIRED_SENSOR_HOSTS:
   host=next(x for x in rows if x['id']==REQUIRED_SENSOR_HOSTS[d['key']])
   # Reuse installed hardware; merge measurement constraints into its host row.
   for k in d['performance']:
    if k in host['requirements']:
     old=host['requirements'][k];new=req[k]
     if old['op']==new['op'] and new['op'] in ['>=','<=']:
      new['value']=(max if new['op']=='>=' else min)(old['value'],new['value'])
    host['requirements'][k]=req[k]
   host['open_requirements']=list(dict.fromkeys(host['open_requirements']+d['open_requirements']))
   continue
  add('SEN-'+d['key'],d['name']+' sensor ('+'/'.join(x for x,on in [('Tier 1',d['tier1']),('Tier 2',d['tier2'])] if on)+')',d['key'],d['quantity'],d['quantity']*d['mass_g'],req,d['open_requirements'])
 for id,name,k in [('STR','Structure / enclosure / mounting','structure_g'),('WIR','Wires / connectors reserve','wires_g'),('FST','Fasteners reserve','fasteners_g'),('SEA','Sealants / adhesives reserve','sealants_g'),('GRO','Growth reserve','growth_g')]:
  add(id,name,'reserve',1,settings[k]*(.65 if id=='STR' else 1),sourcing=False)
 add('MECH','Perch / transformation mechanism allowance','reserve',1,settings['structure_g']*.35,sourcing=False)
 if result.get('additional_payload_kg',0)>0:add('PLD','Additional unpowered payload allowance','reserve',1,result['additional_payload_kg']*1000,sourcing=False)
 total=sum(r['mass_total_g'] for r in rows);flight=result['mass_lb']*.45359237*1000
 return {'rows':rows,'allocated_g':total,'flight_ready_g':flight,'margin_g':flight-total,'closed':total<=flight+1e-6,'storage_required_gb':storage,'peak_station_w':station_peak,'status':'Allocations and provisional selection requirements'}

def evaluate_product(row,product,strict=False):
 reasons=[]
 if row['open_requirements']:reasons+=['Open requirement: '+x for x in row['open_requirements']]
 if strict:
  for gate in ['ndaa','blue']:
   if product.get(gate) is not True or not product.get(gate+'_source_url'):reasons.append('Missing '+gate.upper()+' exact-model evidence')
 if not product.get('source_url') or not product.get('checked_on'):reasons.append('Missing source/date')
 attrs=product.get('attributes',{})
 for key,c in row['requirements'].items():
  a=attrs.get(key);v=c['value'];op=c['op']
  if a is None:reasons.append('Unknown '+key);continue
  try:
   ok={'<=':lambda:a<=v+1e-9,'>=':lambda:a+1e-9>=v,'==':lambda:a==v,'between':lambda:v[0]<=a<=v[1],
    'in':lambda:a in v,'contains':lambda:v in a,'contains_all':lambda:all(x in a for x in v),'contains_any':lambda:any(x in a for x in v)}[op]()
  except (TypeError,KeyError):ok=False
  if not ok:reasons.append(f'{key}: {a} does not meet {op} {v}')
 return reasons

def match(rows,catalog,strict=False):
 output=[]
 for row in rows:
  if not row['sourcing']:
   output.append({'row':row,'options':[],'rejected':[],'status':'Reserved / custom; no COTS search'});continue
  good=[];rejected=[]
  for product in catalog:
   if row['category'] not in product.get('categories',[product.get('category')]):continue
   reasons=evaluate_product(row,product,strict)
   if reasons:rejected.append({'product':product,'reasons':reasons})
   else:good.append(product)
  good=list({x['id']:x for x in good}.values())
  good.sort(key=lambda x:(x['attributes'].get('mass_g',float('inf')),x['id']))
  output.append({'row':row,'options':good[:3],'rejected':rejected,'status':f'{min(3,len(good))} specification matches' if good else '0 viable options / evidence gaps'})
 return output
