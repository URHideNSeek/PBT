"""Dry-air tropospheric ISA pressure with user temperature; elevations in metres MSL."""
from math import isfinite
R=287.05287
T0=288.15
P0=101325.
L=.0065
G=9.80665
RHO0=P0/(R*T0)

def conditions(elevation_m,temperature_c):
 if not all(isfinite(x) for x in [elevation_m,temperature_c]) or not -500<=elevation_m<=5000 or not -20<=temperature_c<=50:raise ValueError('Atmosphere outside supported elevation/temperature bounds')
 pressure=P0*(1-L*elevation_m/T0)**(G/(R*L))
 rho=pressure/(R*(temperature_c+273.15))
 density_altitude=T0/L*(1-(rho/RHO0)**(1/(G/(R*L)-1)))
 return {'site_elevation_m':elevation_m,'temperature_c':temperature_c,'pressure_pa':pressure,'density_kg_m3':rho,'density_altitude_m':density_altitude,'basis':'Dry air; ISA pressure at site elevation; weather pressure and humidity excluded'}
