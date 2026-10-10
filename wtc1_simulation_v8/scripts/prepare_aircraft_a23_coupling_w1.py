"""Declare boundary correction and rotation time scaling without touching w0 evidence."""
import json,sys
from pathlib import Path
from run_aircraft_a23 import ROOT,OUT,CFG,read,dump,streamsha,rel,now,harness

def prepare():
    nc=ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json'
    dest=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a23_coupling_w1.py'
    assert not nc.exists() and not dest.exists()
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_w1.json',h)
    c=read(CFG);c.update(revision='w1',declared_utc=now(),parent_configuration_sha256=streamsha(CFG),
      changes={'extension_selector':'all skin main IDs1..8 move .004mm; all backing IDs17..20 remain fixed. w0 x>=0 selection incorrectly moved backing boundary nodes18/19.',
      'elastic_reference_channel':'compare native FINITE_METAL_CLIP IE with independent clip stiffness, separately report global IE; w0 global IE included distorted backing.',
      'rotation_scaling':'same cubic angle90degrees in10ms vs1ms. Identical material, geometry, mass, interfaces and all acceptance thresholds. Boundary acceleration reduces100x; errors must be measured, not assumed.',
      'paired_times':'native sampling occurs at first step after target time. Interpolate reference within common temporal support, retain timestamps and maximum time shift; do not alter native samples or energy.'})
    c['cases']={'primitive':[],'paired':['REFERENCE_ROTATION_X','CONNECTED_ROTATION_X','REFERENCE_ROTATION_Y','CONNECTED_ROTATION_Y','REFERENCE_ROTATION_Z','CONNECTED_ROTATION_Z','REFERENCE_EXTENSION','CONNECTED_EXTENSION_N4','CONNECTED_EXTENSION_N8']}
    c['motion'].update(rotation_duration_ms=10,prescribed_duration_ms=1)
    c['execution'].update(per_process_cap_s=600,estimated_minutes=[10,20],rotation_history_dt_ms=.01,rotation_animation_dt_ms=.25)
    c.update(fast_w0_velocity_failures_retained=True,whole_insertion_requires_actual_geometry_controls=True,old_native_solver_reruns=0)
    dump(nc,c);dump(OUT/'coupling_w1_guard.json',{'created_utc':now(),'sha256':streamsha(nc),'before_new_native_cases':True})
    src=(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a23.py').read_text(encoding='utf-8')
    changes=[
      ("data/aircraft_a23_predeclaration.json","data/aircraft_a23_coupling_w1.json"),
      ("read(OUT/'declaration_guard.json')","read(OUT/'coupling_w1_guard.json')"),
      ("def rotation(xyz,T,axis):","def rotation(xyz,T,axis,duration=1):\n    T=T/duration"),
      ("w=np.pi/2*(6*T-6*T*T)","w=np.pi/2*(6*T-6*T*T)/duration"),
      ("D[:,:,0]=.004*s[:,None]*(xyz[None,:,0]>=0)","D[:,:,0]=.004*s[:,None]*(np.asarray(node_ids)[None,:]<=8)"),
      ("for t,v in zip(T,val)","for t,v in zip(T*(10 if 'ROTATION_' in cid else 1),val)"),
      ("OUT/'w0'","OUT/'w1'"),
      ("OUT/'w0/","OUT/'w1/"),
      ("duration=.05 if free else 1","duration=.05 if free else 10 if 'ROTATION_' in cid else 1"),
      ("n='A23_'+cid","n='A23_w1_'+cid"),
      ("ff(0,.025)","ff(0,.25 if 'ROTATION_' in cid else .025)"),
      ("ff(.001),'/VERS/2026'","ff(.01 if 'ROTATION_' in cid else .001),'/VERS/2026'"),
      (",180,en)",",600,en)"),
      ("rotation(xyz,T,cid[-1]);expected=","rotation(xyz,T,cid[-1],duration=g['duration_ms']);expected="),
      ("rotation(xyz,T,cid[-1]);position_err=","rotation(xyz,T,cid[-1],duration=g['duration_ms']);position_err="),
      ("checks['independent_static_IE']=bool(abs(IE[-1]-analytic)","clip_IE=next(H[k]*.001 for k in H if k.startswith('FINITE_METAL_CLIP') and k.strip().endswith('IE'));checks['independent_static_IE']=bool(abs(clip_IE[-1]-analytic)"),
      ("'last_IE_J':float(IE[-1]),","'last_IE_J':float(IE[-1]),'last_clip_IE_J':float(clip_IE[-1]) if g['connected'] and 'EXTENSION' in cid else None,"),
      ("assert np.allclose(T,ref['time_ms'],atol=1e-9,rtol=0);X,V,angle,w=rotation(q,T,axis);","mask=(T>=ref['time_ms'][0])&(T<=ref['time_ms'][-1]);T=T[mask];X,V,angle,w=rotation(q,T,axis,duration=g['duration_ms']);"),
      ("actual=con['KE_J']-ref['KE_J']","actual=con['KE_J'][mask]-np.interp(T,ref['time_ms'],ref['KE_J'])"),
      ("'maximum_added_KE_error_J':difference,","'maximum_added_KE_error_J':difference,'maximum_native_time_shift_ms':float(abs(con['time_ms']-ref['time_ms']).max()),'common_rows':int(mask.sum()),"),
      ("['last_IE_J'];e8=","['last_clip_IE_J'];e8="),
      ("N8/review.json')['last_IE_J']","N8/review.json')['last_clip_IE_J']"),
      ("paired_coupling_review.json","paired_coupling_w1_review.json"),
      ("campaign_review.json","campaign_w1_review.json"),
    ]
    audit=[]
    for old,new in changes:
        count=src.count(old);assert count>0,old;src=src.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    # This derivative uses its explicit w1 declaration; the old declaration function is never called.
    src=src.replace("choices=['declare','run']","choices=['run']")
    dest.write_text(src,encoding='utf-8')
    compile(src,str(dest),'exec')
    dump(OUT/'coupling_w1_derivation.json',{'created_utc':now(),'original':rel(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a23.py'),'original_sha256':streamsha(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a23.py'),'derived':rel(dest),'derived_sha256':streamsha(dest),'replacements':audit,'parent_not_modified':True})
    print({'declared':'AIRCRAFT-A23_w1','new_cases':9,'rotation_physical_ms':10,'native_strength_qualified':False},flush=True)

if __name__=='__main__':prepare()
