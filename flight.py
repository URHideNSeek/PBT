"""Preliminary rotary-wing induced/profile/parasite electrical-power model.
Structure follows Zeng/Xu/Zhang (2019) and Gao et al. (2020), arXiv:2005.01305.
Coefficients remain planning assumptions until fitted to matched propulsion data.
"""
from math import pi,sqrt

def power(mass_kg,p):
 area=p['rotors']*pi*(p['prop']*.0254/2)**2
 rho=p['rho'];g=9.80665;v=p['speed']*.514444444444
 efficiency=p['eff'];profile_fraction=p.get('profile_fraction',.15)
 tip=p.get('tip_speed_m_s',180.)
 # Calibrate once against reference configuration at sea-level reference density.
 def parts(m,r,a,speed,eta=None):
  eta=efficiency if eta is None else eta
  induced=(m*g)**1.5/sqrt(2*r*a)/eta
  vi=sqrt(m*g/(2*r*a))
  profile=induced*profile_fraction/(1-profile_fraction)*(1+3*(speed/tip)**2)
  inflow=sqrt(1+(speed**4)/(4*vi**4))-speed**2/(2*vi**2)
  return induced*sqrt(max(0.,inflow)),profile,.5*r*p['drag']*speed**3/p['drive_eff']
 refarea=p['rotors']*pi*(p['ref_prop']*.0254/2)**2
 ri,rp,rd=parts(p['ref_kg'],1.225,refarea,p['ref_speed']*.514444444444,.6)
 calibration=max(.01,(p['ref_w']-rd)/(ri+rp))
 i,profile,drag=parts(mass_kg,rho,area,v)
 hi,hp,_=parts(mass_kg,rho,area,0.)
 electronics=p.get('flight_electronics_w',0.)
 return {'hover_w':calibration*(hi+hp)+electronics,'flight_w':calibration*(i+profile)+drag+electronics,
         'induced_w':calibration*i,'profile_w':calibration*profile,'parasite_w':drag,'flight_electronics_w':electronics,'calibration_factor':calibration}
