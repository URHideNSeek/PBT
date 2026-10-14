"""Mission-dependent component allocations and conservative evidence matching.

Sensor defaults are editable trade assumptions, never supplier specifications.
Catalog attributes must be source-backed. Unknown hard constraints never pass.
"""
from math import ceil, isfinite

# key: label, allocated mass g, active W, sleep W, logged Mbps, interface
SENSORS = {
    'environment': ('Temperature / humidity', 20., .1, .005, .0001, 'I2C'),
    'pressure': ('Barometric pressure', 15., .1, .005, .0001, 'I2C'),
    'light': ('Ambient light', 10., .05, .001, .0001, 'I2C'),
    'acoustic': ('Acoustic microphone', 30., .5, .01, .256, 'USB'),
    'vibration': ('Vibration / acceleration', 20., .2, .005, .01, 'SPI'),
    'visible': ('Visible camera', 75., 3., .02, 8., 'USB'),
    'thermal': ('Thermal camera', 100., 1.5, .02, 8., 'USB'),
    'range': ('Distance / ranging', 40., 1., .02, .1, 'UART'),
    'gnss': ('Additional GNSS receiver', 60., .8, .02, .01, 'CAN'),
    'rf': ('RF measurement receiver', 150., 5., .05, 1., 'USB'),
    'radar': ('Radar sensor', 250., 10., .1, 1., 'USB'),
}

def sensor_plan(tier1, tier2, profiles, duty, tier2_minutes, housekeeping_w):
    if set(tier1) & set(tier2):
        raise ValueError('A sensor cannot be in both tiers. Choose one tier per device type.')
    if not 0 <= duty <= 1 or not 0 <= tier2_minutes <= 1440:
        raise ValueError('Invalid sensor schedule')
    rows = []
    for key in dict.fromkeys([*tier1, *tier2]):
        if key not in SENSORS: raise ValueError('Unknown sensor type')
        p = profiles[key]
        numeric = [p[k] for k in ('mass_g', 'active_w', 'sleep_w', 'logged_mbps', 'quantity')]
        if any(not isinstance(v, (int, float)) or not isfinite(v) or v < 0 for v in numeric) or p['quantity'] < 1 or p['quantity'] != int(p['quantity']):
            raise ValueError('Invalid sensor allocation')
        if p['sleep_w'] > p['active_w']: raise ValueError('Sleep power must not exceed active power')
        active = duty if key in tier1 else tier2_minutes / 1440
        q = int(p['quantity'])
        rows.append({'key': key, 'tier': 1 if key in tier1 else 2, **p,
                     'average_w': q * (p['sleep_w'] + (p['active_w'] - p['sleep_w']) * active),
                     'daily_gb': q * p['logged_mbps'] * 86400 * active / 8000})
    # Tier 2 sleep is charged continuously; its active increment is charged once.
    base = housekeeping_w + sum(r['quantity'] * r['sleep_w'] for r in rows)
    base += sum(r['quantity'] * (r['active_w'] - r['sleep_w']) * duty for r in rows if r['tier'] == 1)
    incremental = sum(r['quantity'] * (r['active_w'] - r['sleep_w']) for r in rows if r['tier'] == 2)
    return {'rows': rows, 'tier1_w': base, 'tier2_w': incremental,
            'sensor_kg': sum(r['quantity'] * r['mass_g'] for r in rows) / 1000,
            'daily_gb': sum(r['daily_gb'] for r in rows),
            'peak_sensor_w': sum(r['quantity'] * r['active_w'] for r in rows)}

def bom(result, sizing, plan, settings):
    p = result['engineering']; n = int(p['rotors']); rows = []
    common = {'temp_min_c': settings['temp_min_c'], 'temp_max_c': settings['temp_max_c']}
    def add(key, label, q, mass, requirements, open_requirements=(), sourcing=True):
        if q == 0: return
        rows.append({'id': key, 'component': label, 'quantity': q,
                     'mass_each_g': mass, 'mass_total_g': q * mass,
                     'requirements': {**common, **requirements} if sourcing else {},
                     'open_requirements': list(open_requirements), 'sourcing': sourcing,
                     'basis': 'Editable design allocation; not a measured product mass'})
    v = sizing['assumed_nominal_voltage_v']; bus_max = settings['bus_max_v']
    add('battery', 'Battery pack / BMS', 1, result['battery_kg']*1000,
        {'capacity_wh': result['required_nominal_average_solar_wh'],
         'continuous_a': sizing['continuous_battery_current_a'] * settings['current_margin'],
         'peak_a': sizing['peak_battery_current_a'] * settings['current_margin'],
         'nominal_v': v, 'max_voltage_v': bus_max}, ['Charging temperature / sag / connector verification'])
    propulsion_g = p['propulsion_kg'] * 1000
    add('motor', 'Motor', n, propulsion_g*.60/n,
        {'thrust_kgf': sizing['continuous_thrust_per_rotor_kgf'],
         'input_power_w': sizing['estimated_peak_per_rotor_w'], 'prop_diameter_in': p['prop'],
         'nominal_v': v}, ['Matched motor / ESC / prop test curve at selected voltage and air density'])
    add('esc', 'ESC', n, propulsion_g*.30/n,
        {'continuous_a': sizing['continuous_battery_current_a']/n*settings['current_margin'],
         'peak_a': sizing['peak_battery_current_a']/n*settings['current_margin'],
         'input_min_v': p['voltage'], 'input_max_v': bus_max, 'interface': 'PWM'},
        ['Motor compatibility / transient verification'])
    add('propeller', 'Propeller / hub', n, propulsion_g*.10/n,
        {'prop_diameter_in': p['prop'], 'rated_rpm': sizing['estimated_continuous_thrust_rpm']},
        ['Matched motor performance / hub bore / rotation and folding clearance'])
    compute_g = p['compute_kg']*1000
    add('autopilot', 'Flight controller', 1, compute_g*.35,
        {'supply_v': 5., 'power_w_max': settings['autopilot_w'], 'pwm_outputs': n+settings['servo_qty'], 'interface': 'CAN'},
        ['Firmware / failsafe / port allocation verification'])
    add('compute', 'Payload computer / carrier / cooling', 1, compute_g*.55,
        {'supply_v': 5., 'power_w_max': settings['compute_w'], 'ram_gb': settings['ram_gb'], 'interface': 'USB'},
        ['Workload benchmark / simultaneous sensor bandwidth / carrier and cooling'])
    add('storage', 'Data storage', 1, compute_g*.10,
        {'storage_gb': plan['daily_gb']*settings['retention_days']*1.2,
         'write_mbps': sum(r['quantity']*r['logged_mbps'] for r in plan['rows']), 'interface': 'microSD'},
        ['Endurance rating / file-system power-loss behavior'])
    add('navigation', 'Flight GNSS / compass', 1, settings['navigation_g'],
        {'supply_v': 5., 'power_w_max': 1.5, 'accuracy_m': settings['gnss_accuracy_m'], 'update_hz': 5., 'interface': 'CAN'})
    add('radio', 'Telemetry radio', 1, p['comms_kg']*1000*.85,
        {'power_w_max': settings['radio_w'], 'range_km': settings['link_range_km'],
         'throughput_mbps': settings['link_mbps'], 'supply_v': settings['radio_supply_v'], 'interface': 'UART'},
        ['Band / jurisdiction / antenna-dependent link budget and installed range'])
    add('antenna', 'Radio antenna / RF mounting', 1, p['comms_kg']*1000*.15,
        {'frequency_mhz': settings['frequency_mhz'], 'impedance_ohm': 50.}, ['Connector / installed pattern / RF losses'])
    add('solar', 'Solar panel', 1, p['solar_kg']*1000*.70,
        {'output_w': sizing['estimated_peak_battery_delivered_solar_w']/p['charger_eff'],
         'area_m2_max': sizing['solar_surface_area_m2']}, ['Voltage-temperature curve / shape / mounting / shading'])
    add('charger', 'Solar charge controller', 1, p['solar_kg']*1000*.30,
        {'output_v': bus_max, 'power_w': sizing['estimated_peak_battery_delivered_solar_w']},
        ['Panel Voc / MPPT window / chemistry / temperature-inhibited charging'])
    # This reserve is explicit rather than hidden in a catch-all structure mass.
    add('regulator', 'Power regulation / distribution', 1, settings['regulator_g'],
        {'input_min_v': p['voltage'], 'input_max_v': bus_max, 'output_v': 5.,
         'output_a': (settings['compute_w']+settings['autopilot_w']+plan['peak_sensor_w']+1.5)/5*settings['current_margin']},
        ['Rail-by-rail currents / startup transients / servo and radio rails'])
    add('servo', 'Mechanism actuator', settings['servo_qty'], settings['servo_g'],
        {'torque_kgcm': settings['servo_torque_kgcm'], 'supply_v': settings['servo_v'], 'interface': 'PWM'},
        ['Mechanism load / leverage / stall-current / retention verification'])
    for r in plan['rows']:
        add('sensor_'+r['key'], SENSORS[r['key']][0]+f" · Tier {r['tier']}", r['quantity'], r['mass_g'],
            {'supply_v': r['supply_v'], 'power_w_max': r['active_w'], 'interface': r['interface'], **r.get('performance', {})},
            r.get('open_requirements', []))
    for key in ('structure', 'wires', 'fasteners', 'sealants', 'growth'):
        add(key, {'structure':'Structure / mounting', 'wires':'Wires / connectors reserve',
                  'fasteners':'Fasteners reserve', 'sealants':'Sealants / adhesives reserve', 'growth':'Unassigned mass reserve'}[key],
            1, settings[key+'_g'], {}, sourcing=False)
    total = sum(r['mass_total_g'] for r in rows)
    return {'rows': rows, 'allocated_g': total, 'flight_ready_g': sizing['flight_ready_kg']*1000,
            'margin_g': sizing['flight_ready_kg']*1000-total,
            'closed': total <= sizing['flight_ready_kg']*1000}

MINIMUM = {'capacity_wh','continuous_a','peak_a','thrust_kgf','input_power_w','rated_rpm',
           'sample_hz','sample_khz','channels','snr_db','range_m','bandwidth_hz','lux_max','rf_max_mhz','rf_bandwidth_mhz','pressure_max_hpa','accel_range_g','pwm_outputs','ram_gb','storage_gb','write_mbps','update_hz','range_km','throughput_mbps',
           'output_w','power_w','output_a','torque_kgcm','pixels_x','pixels_y','fps'}
MAXIMUM = {'power_w_max','area_m2_max','accuracy_m','temp_accuracy_c','humidity_accuracy_pct','pressure_accuracy_pa','range_accuracy_cm','rf_min_mhz','pressure_min_hpa'}

def assess(row, product, controlled):
    gaps=[]; a=product.get('attributes', {})
    if product.get('category') != row['id']: return ['Different component category']
    if not product.get('source_url') or not product.get('verified_on'): gaps.append('Product source not verified')
    if controlled and not (product.get('ndaa_verified') is True and product.get('blue_verified') is True and product.get('compliance_source_url')):
        gaps.append('Exact model NDAA and Blue UAS evidence missing')
    if a.get('mass_g') is None: gaps.append('Missing installed product mass')
    elif a['mass_g'] > row['mass_each_g']: gaps.append('Exceeds per-unit mass allocation')
    for key, required in row['requirements'].items():
        actual=a.get(key)
        if actual is None: gaps.append('Missing '+key); continue
        if key=='temp_min_c': ok=actual<=required
        elif key=='temp_max_c': ok=actual>=required
        elif key=='input_min_v': ok=actual<=required
        elif key=='input_max_v': ok=actual>=required
        elif key=='max_voltage_v': ok=actual<=required
        elif key=='supply_v': ok=isinstance(actual,(list,tuple)) and actual[0]<=required<=actual[1]
        elif key=='interface': ok=required in actual if isinstance(actual,list) else required==actual
        elif key in MINIMUM: ok=actual>=required
        elif key in MAXIMUM: ok=actual<=required
        elif key=='nominal_v': ok=abs(actual-required)<=.05*required
        else: ok=actual==required
        if not ok:gaps.append('Fails '+key)
    gaps += row.get('open_requirements', [])
    return gaps

def match(rows, catalog, controlled):
    result=[]
    for row in rows:
        if not row['sourcing']:
            result.append({'row':row,'options':[],'rejected':[],'status':'Allowance; no product search'});continue
        candidates=[p for p in catalog if p.get('category')==row['id']]
        passed=[]; rejected=[]
        for p in candidates:
            reasons=assess(row,p,controlled)
            if reasons: rejected.append({'product':p,'reasons':reasons})
            else: passed.append(p)
        unique={p['id']:p for p in passed}
        options=sorted(unique.values(),key=lambda p:(p['attributes']['mass_g'],p['id']))[:3]
        result.append({'row':row,'options':options,'rejected':rejected,
                       'status':f'{len(options)} parameter-qualified options' if options else 'No verified match'})
    return result
