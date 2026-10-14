"""Metric presentation boundary; preserve the validated legacy solver units internally."""
LB_KG=.45359237
MI_KM=1.609344
KT_MS=.514444444444

def conversion(key):
 explicit={'prop':('prop_mm',25.4),'ref_prop':('ref_prop_mm',25.4),'prop_max':('prop_max_mm',25.4),'solar':('solar_diameter_mm',25.4),'solar_max':('solar_max_mm',25.4),'mass_max':('mass_max_kg',LB_KG),'thrust':('thrust_n',9.80665),'speed':('speed_m_s',KT_MS),'wind':('wind_m_s',KT_MS),'ref_speed':('ref_speed_m_s',KT_MS)}
 if key in explicit:return explicit[key]
 for old,new,factor in [('_lb_ft2','_kg_m2',4.882427636),('_kgcm','_nm',.0980665),('_kgf','_n',9.80665),('_in','_mm',25.4),('_mi','_km',MI_KM),('_kt','_m_s',KT_MS),('_lb','_kg',LB_KG)]:
  if key.endswith(old):return key[:-len(old)]+new,factor
 return key,1.

def scale(value,factor):
 if value is None:return None
 if isinstance(value,bool):return value
 if isinstance(value,(int,float)):return value*factor
 if isinstance(value,list):return [scale(x,factor) for x in value]
 if isinstance(value,dict):return {k:scale(v,factor) if k=='value' else v for k,v in value.items()}
 return value

def metric_view(value):
 if isinstance(value,list):return [metric_view(v) for v in value]
 if not isinstance(value,dict):return value
 out={}
 for key,v in value.items():
  name,factor=conversion(key)
  # Prefer an existing exact SI result over a converted duplicate.
  if name!=key and name in value:continue
  out[name]=metric_view(scale(v,factor)) if factor!=1 else metric_view(v)
 return out

def metric_label(label):
 for old,new in [('statute miles','km'),(' kgf',' N'),(' kt',' m/s'),(' in',' mm'),(' lb',' kg')]:label=label.replace(old,new)
 return label

def legacy_parameters(parameters, keys):
 return {key:parameters[conversion(key)[0]]/conversion(key)[1] for key in keys}
