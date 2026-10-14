"""Read-only downstream engineering sizing, not independently approved requirements."""
from math import pi,sqrt,isfinite

def derive(result, *, thrust_coefficient=.10, nominal_voltage=24.):
 if not all(isfinite(x) and x>0 for x in [thrust_coefficient,nominal_voltage]): raise ValueError('Sizing assumptions must be positive and finite')
 p=result['engineering']
 if nominal_voltage<p['voltage']: raise ValueError('Nominal battery voltage must not be below minimum loaded voltage')
 m=result['mass_lb']*.45359237;d=p['prop']*.0254;n=int(p['rotors']);area=n*pi*(d/2)**2
 thrust=m*9.80665/n;continuous=thrust*p['ratio']
 rpm=lambda force:60*sqrt(force/(thrust_coefficient*p['rho']*d**4))
 hover_rpm=rpm(thrust);continuous_rpm=rpm(continuous)
 return {
 'flight_ready_kg':m,'flight_ready_lb':result['mass_lb'],'battery_allocation_kg':result['battery_kg'],
 'nonbattery_allocation_kg':result['nonbattery_kg'],'rotor_count':n,'assumed_prop_diameter_in':p['prop'],
 'total_disk_area_m2':area,'disk_loading_kg_m2':m/area,'disk_loading_N_m2':m*9.80665/area,
 'disk_loading_lb_ft2':result['mass_lb']/(area*10.7639104167),
 'hover_thrust_per_rotor_kgf':m/n,'continuous_thrust_per_rotor_kgf':result['thrust_per_rotor_kgf'],
 'estimated_hover_rpm':hover_rpm,'estimated_continuous_thrust_rpm':continuous_rpm,
 'estimated_tip_speed_m_s':pi*d*continuous_rpm/60,
 'estimated_hover_electrical_w':result['hover_w'],'estimated_cruise_electrical_w':result['flight_w'],
 'estimated_maneuver_electrical_w':result['peak_w'],'estimated_hover_per_rotor_w':result['hover_w']/n,
 'estimated_peak_per_rotor_w':result['peak_w']/n,
 'allocated_propulsion_assembly_per_rotor_g':p['propulsion_kg']*1000/n,
 'required_continuous_pack_specific_power_wkg':max(result['hover_w'],result['flight_w'])/result['battery_kg'],
 'required_peak_pack_specific_power_wkg':result['peak_w']/result['battery_kg'],
 'continuous_battery_current_a':max(result['hover_w'],result['flight_w'])/p['voltage'],
 'peak_battery_current_a':result['peak_w']/p['voltage'],
 'battery_nominal_assumed_wh':result['battery_kg']*p['whkg'],
 'battery_nominal_required_average_solar_wh':result['required_nominal_average_solar_wh'],
 'battery_nominal_required_no_solar_wh':result['required_nominal_no_solar_wh'],
 'battery_usable_assumed_wh':result['battery_kg']*p['whkg']*p['derate']*(p['soc']-p['floor'])/100,
 'required_installed_specific_energy_whkg':result['required_installed_whkg'],
 'required_pack_ah_average_solar':result['required_nominal_average_solar_wh']/nominal_voltage,
 'required_pack_mass_kg_average_solar':result['required_nominal_average_solar_wh']/p['whkg'],
 'station_consumption_wh_day':result['station_wh_day'],'average_solar_harvest_wh_day':result['solar_wh_day'],
 'solar_surface_area_m2':pi*(p['solar']*.0254/2)**2,
 'active_solar_area_m2':pi*(p['solar']*.0254/2)**2*p['active'],
 'estimated_peak_battery_delivered_solar_w':pi*(p['solar']*.0254/2)**2*p['active']*1000*p['cell_eff']*p['charger_eff'],
 'assumed_nominal_voltage_v':nominal_voltage,'assumed_min_loaded_voltage_v':p['voltage'],
 'assumed_thrust_coefficient':thrust_coefficient,
 }
