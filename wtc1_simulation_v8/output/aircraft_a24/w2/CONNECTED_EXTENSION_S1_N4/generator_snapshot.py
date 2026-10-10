"""Controlled solid-to-shell penalty transmission: no beam inertia or root mass condensation."""
from run_aircraft_a23 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,brick_grid,inertia,prop,group,material,solid_property,skew_card,face_property,histories,SOURCE
import run_aircraft_a23 as A23
import argparse,inspect,json,shutil,re,traceback,time,urllib.request
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a24'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a24_stiffness.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a23'

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A23'
    cy=read(ROOT/'harness/publication_cycle.json');assert cy['last_published_iteration']=='AIRCRAFT-A23' and cy['pending_count']==0
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json')
    cases=['REFERENCE_ROTATION_X','CONNECTED_ROTATION_X','REFERENCE_ROTATION_Y','CONNECTED_ROTATION_Y','REFERENCE_ROTATION_Z','CONNECTED_ROTATION_Z','REFERENCE_EXTENSION','CONNECTED_EXTENSION_N4','CONNECTED_EXTENSION_N8',
       'REFERENCE_FREE_TRANSLATION','CONNECTED_FREE_TRANSLATION','REFERENCE_FREE_ROTATION_X','CONNECTED_FREE_ROTATION_X','REFERENCE_FREE_ROTATION_Y','CONNECTED_FREE_ROTATION_Y','REFERENCE_FREE_ROTATION_Z','CONNECTED_FREE_ROTATION_Z','REFERENCE_ROTATION_Z_HALF','CONNECTED_ROTATION_Z_HALF']
    c.update(iteration='AIRCRAFT-A24',declared_utc=now(),seed=1102049,random_draws=0,parent_configuration_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json'),
      purpose='Solid secondary nodes with translation-only DOF, tied by controlled penalty Spot25; test actual mass tensor, energy and free dynamics without mass condensation. A candidate, never an as-built attachment.',
      cases={'primitive':[],'paired':cases},
      changed_since_A23={'only_new_clip_end_ties':'Spot25, Stfac1, Visc0, Istf2=(main+secondary nodal stiffness)/2, dsearch.8. Optional Iproj2 retained but no claim of penalty mass transfer.',
        'unchanged':'clip, backing and sandwich geometry/material/mass; passed core-to-skin Spot5 A20 unchanged',
        'energy':'include every native contact energy channel, not just structural IE/KE/RKE',
        'free_initial_conditions':'all nodes uniform[-200,5,2]m/s or omega10rad/ms aboutXYZ; angular velocity assigned only to shell nodes, never solid-only nodes',
        'time_refinement':'Z paired half scale /DT.2 instead.4 and dt cap.0000125 instead.000025. Same10ms curve and output cadence.',
        'documentation_limit':'Spot25 is less robust and not recommended for secondary rotational DOF. New clip has only translational DOF. Explicitly test slip and all energy channels; no scientific acceptance inferred from keyword choice.'},
      old_native_solver_reruns=0,whole_insertion_requires_actual_geometry_controls=True,physical_strength_or_fracture_qualified=False,objective1_complete=False)
    c['motion'].update(free_translation_m_s=[-200,5,2],free_fixture_rotation_rad_ms=10,rotation_duration_ms=10)
    c['execution'].update(estimated_minutes=[15,25],per_process_cap_s=600)
    c['acceptance'].update(free_global_energy_fraction=.002,free_linear_momentum_fraction=.002,paired_initial_KE_fraction=.002,half_dt_added_KE_fraction=.01,declared_contact_damping_J=1e-12)
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True})
    sources=[]
    for p in [ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a23.py',PREV/'coupling_summary.json',PREV/'inertia_channels_w1.json',PREV/'paired_w1_cached_audit.json',SOURCE/'mesh.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/sandwich_type2_review.json']:
        sources.append({'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size})
    sd=OUT/'sources';sd.mkdir()
    for name,p,u in [('type2',PREV/'sources/primary_1.html','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm')]:
        dest=sd/(name+'.html');shutil.copy2(p,dest);sources.append({'path':rel(dest),'sha256':streamsha(dest),'bytes':dest.stat().st_size,'url':u,'redistribution':'exclude_third_party'})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'sources_read_only':True,'archive_rescanned':False,'historical_damage_target':False})
    print({'declared':'AIRCRAFT-A24','native_controls':len(cases),'CPU_minutes':[15,25],'whole_not_launched':True},flush=True)

def guard():
    assert streamsha(CFG)==read(OUT/'stiffness_guard.json')['sha256']
    sources=read(OUT/'source_manifest.json')['files'];p=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a23.py';r=next(r for r in sources if r['path']==rel(p));assert streamsha(p)==r['sha256']

def axis(cid):return re.search('ROTATION_([XYZ])',cid).group(1)

def rotation(xyz,T,ax,duration=1):
    X,V,a,w=A23.rotation(xyz,T/duration,ax);return X,V/duration,a,w/duration

def imposed(L,xyz,node_ids,cid,start=10000,rotational_DOF=True):
    T=np.linspace(0,1,10001);D=np.zeros((len(T),len(xyz),3));A=np.zeros_like(D);s=3*T*T-2*T**3;duration=10 if 'ROTATION_' in cid else .1
    if 'ROTATION_' in cid:
        X,V,a,w=rotation(xyz,T,axis(cid));D=X-xyz;A[:,:,'XYZ'.index(axis(cid))]=a[:,None]
    elif 'EXTENSION' in cid:D[:,:,0]=.004*s[:,None]*(np.asarray(node_ids)[None,:]<=8)
    cache={}
    for j,ni in enumerate(node_ids):
        L+=group(ni,f'KNOWN_NODE_{ni}',[int(ni)])
        for ax,direction in enumerate(['X','Y','Z','XX','YY','ZZ'] if rotational_DOF else ['X','Y','Z']):
            val=D[:,j,ax] if ax<3 else A[:,j,ax-3];key=val.tobytes()
            if key not in cache:
                start+=1;cache[key]=start;L+=[f'/FUNCT/{start}',f'KNOWN_SHARED_{start}']+[ff(t*duration,v) for t,v in zip(T,val)]
            fid=cache[key];start+=1
            L+=[f'/IMPDISP/{start}',f'KNOWN_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,int(ni))+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def create_runner():
    s=inspect.getsource(A23.run_one).replace("OUT/'w0'","OUT/'w2'");audit=[]
    replacements=[
      ("free=cid.startswith('FREE_')","free='FREE_' in cid"),
      ("n='A23_'+cid","n='A24_'+cid"),
      ("duration=.05 if free else 1","duration=.05 if free else 10 if 'ROTATION_' in cid else .1"),
      ("ii(sid,sid,1000,5,0,2,1000,0)+ff(.8),ii(0)","ii(sid,sid,1000,25,0,2,1000,0)+ff(.8),ff(stfac,1e-20)+' '*20+ii(2),ii(0)"),
      ("ff(0,.025)","ff(0,.25 if not free and 'ROTATION_' in cid else .025)"),
      ("ff(.4,0)","ff(.2 if cid.endswith('_HALF') else .4,0)"),
      ("ff(.000025,.000025)","ff(.0000125,.0000125) if cid.endswith('_HALF') else ff(.000025,.000025)"),
      ("ff(.001),'/VERS/2026'","ff(.01 if not free and 'ROTATION_' in cid else .001),'/VERS/2026'"),
      (",180,en)",",600,en)"),
      ("omega=np.eye(3)['XYZ'.index(cid[-1])]*10;V=np.cross(omega,xyz)","omega=np.eye(3)['XYZ'.index(axis(cid))]*10 if 'ROTATION_' in cid else np.zeros(3);V=np.cross(omega,xyz) if 'ROTATION_' in cid else np.tile([-200,5,2],(len(xyz),1))"),
      ("else:L=imposed(L,main_xyz,main_ids,cid,rotational_DOF=not primitive)","\n        if 'ROTATION_' in cid:\n            for ni in main_ids:L+=[f'/INIVEL/ROT/{100000+ni}',f'INITIAL_SHELL_ROTATION_{ni}',ff(*omega)+ii(ni,0),ff(0)+ii(0)]\n    else:L=imposed(L,main_xyz,main_ids,cid,rotational_DOF=not primitive)"),
      ("dump(d/'generation.json',generation);en=env()","known=np.zeros(len(xyz));known[:8]=.0915/4;known[8:16]=.0384/8;known[16:20]=.139/4;known[clip_ids-1]=mass;generation.update(known_translational_node_masses_g=known.tolist(),axis=axis(cid) if 'ROTATION_' in cid else None,initial_omega_rad_ms=omega.tolist() if free else None,initial_velocity_m_s=V.tolist() if free else None,root_penalty_parameters={'Spot':25,'Stfac':stfac,'Visc':1e-20,'Istf':2,'dsearch_mm':.8} if connected else None);dump(d/'generation.json',generation);en=env()"),
    ]
    s=s.replace("guard();c=read(CFG);primitive=","guard();c=read(CFG);stfac=int(re.search('_S(1|10|100)(?:_|$)',cid).group(1));primitive=")
    for old,new in replacements:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    s=s.replace("        assert execute(RUNTIME/'engine_win64.exe'","        verify_requested_damping(d,n)\n        assert execute(RUNTIME/'engine_win64.exe'");exec(compile(s,__file__+'::derived_run_one','exec'),globals())
    p=OUT/'runner_w2_derivation.json'
    if not p.exists():dump(p,{'created_utc':now(),'source':rel(Path(A23.__file__)),'source_sha256':streamsha(Path(A23.__file__)),'changes':audit,'derived_function_source':s,'A23_unmodified':True})

def review(d,n):
    guard();g=read(d/'generation.json');c=read(CFG);a=c['acceptance'];cid=g['case'];H=histories(d/(n+'T01.csv'));T=H['time'];xyz=np.asarray(g['nodes_mm']);keys=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(keys)==6*len(xyz);node=np.column_stack([H[k] for k in keys]).reshape(len(T),len(xyz),6);X=xyz+node[:,:,:3];V=node[:,:,3:]
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(H[k] for k in terms)*.001;IE=H['INTERNAL ENERGY']*.001;EW=H['EXTERNAL WORK']*.001;R=E-E[0]-EW;scale=max(float(abs(E).max()),float(abs(EW).max()));contact=H['ELASTIC CONTACT ENERGY']*.001
    checks={'normal_termination':True,'zero_warnings_errors':read(d/'starter_gate.json')['pass'],'declared_mass':abs(H['MASS'][0]-g['expected_mass_g'])<1e-6*g['expected_mass_g'],'constant_mass':abs(H['MASS']-H['MASS'][0]).max()<1e-6*g['expected_mass_g'],'no_added_mass':abs(H['ADDED MASS']).max()<1e-9*g['expected_mass_g'],'native_full_energy_balance':abs(R).max()<.02*scale+1e-7,'nonnegative_IE':IE.min()>-1e-7,'no_undeclared_contact_damping':abs(H['DAMPING CONTACT ENERGY ']).max()*.001<1e-12}
    pe=ve=None;clip_ie=None;ref_ie=None
    if not g['free'] and 'ROTATION_' in cid:
        ex,ev,ang,w=rotation(xyz,T,g['axis'],g['duration_ms']);pe=float(abs(X-ex).max());ve=float(abs(V-ev).max());checks.update(all_nodes_position=pe<.002,all_nodes_velocity=ve<.005,rigid_IE=abs(IE).max()<1e-7)
    if not g['free'] and g['connected'] and 'EXTENSION' in cid:
        from linear_hexa_reference_aircraft_a23 import solve
        q=xyz[np.asarray(g['clip_node_ids'])-1];b=[[v-20 for v in row] for row in g['bricks']];left=[i+1 for i,x in enumerate(q) if abs(x[0]+2)<1e-12];right=[i+1 for i,x in enumerate(q) if abs(x[0]-2)<1e-12];ref=solve(q,b,left,right);dump(d/'independent_rigid_cap_elastic_reference.json',ref);ref_ie=ref['energy_J'];clip_ie=float(next(H[k][-1]*.001 for k in H if k.startswith('FINITE_METAL_CLIP') and k.strip().endswith('IE')));checks['stiff_clip_traction_reference']=abs(clip_ie-ref_ie)<.02*ref_ie+1e-7
    P=np.column_stack([H[ax+'-MOMENTUM'] for ax in 'XYZ'])*.001
    if g['free']:
        checks.update(no_external_work=abs(EW).max()<1e-7,free_energy=abs(E-E[0]).max()<.002*E[0]+1e-7,free_momentum=abs(P-P[0]).max()<.002*float(np.linalg.norm(P[0]))+1e-9)
        if 'TRANSLATION' in cid:
            target=xyz[None,:,:]+T[:,None,None]*np.array([-200,5,2]);pe=float(abs(X-target).max());ve=float(abs(V-np.array([-200,5,2])).max());checks.update(uniform_free_translation_position=pe<.002,uniform_free_translation_velocity=ve<.005)
    checks={k:bool(v) for k,v in checks.items()}
    np.savez_compressed(d/'histories_SI.npz',time_ms=T,total_J=E,IE_J=IE,EW_J=EW,residual_J=R,KE_J=(H['KINETIC ENERGY']+H['ROTATION ENERGY'])*.001,contact_elastic_J=contact,positions_mm=X,velocities_m_s=V,momentum_Ns=P,time_step_ms=H['TIME STEP'])
    r={'created_utc':now(),'case':cid,'rows':len(T),'last_ms':float(T[-1]),'native_mass_g':float(H['MASS'][0]),'native_initial_total_J':float(E[0]),'maximum_residual_J':float(abs(R).max()),'maximum_IE_J':float(IE.max()),'last_clip_IE_J':clip_ie,'rigid_cap_reference_IE_J':ref_ie,'maximum_elastic_contact_J':float(abs(contact).max()),'maximum_position_error_mm':pe,'maximum_velocity_error_m_s':ve,'checks':checks,'pass':all(checks.values()),'physical_strength_or_fracture_qualified':False,'whole_impact_qualified':False};dump(d/'review.json',r);print({'case':cid,'pass':r['pass'],'failed':[k for k,v in checks.items() if not v],'residual_J':r['maximum_residual_J']},flush=True)

def run():
    guard();create_runner()
    for cid in read(CFG)['cases']['paired']:
        d=OUT/'w2'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete native case; no implicit rerun'
        else:run_one(cid)
    rows=[read(OUT/'w2'/cid/'review.json') for cid in read(CFG)['cases']['paired']];dump(OUT/'native_case_summary_w2.json',{'created_utc':now(),'cases':rows,'all_pass':all(r['pass'] for r in rows),'whole_insertion_ready':False,'actual_geometry_controls_required':True,'objective1_complete':False})


def verify_requested_damping(d,n):
    expected=read(CFG)['damping_readback']['requested_w1_positive_coefficient'];text=(d/(n+'_0000.out')).read_text();rows=[]
    for sid in [301,302]:
        block=re.search(r'INTERFACE NUMBER\s*:\s*'+str(sid)+r'\b(.*?)(?=INTERFACE NUMBER|\Z)',text,re.S).group(1)
        value=float(re.search(r'CRITICAL DAMPING FACTOR.*?([+\-]?\d[\d.]*E[+\-]\d+)',block).group(1))
        actual_stiffness=float(re.search(r'STIFFNESS FACTOR.*?([+\-]?\d[\d.]*(?:E[+\-]\d+)?)\s*$',block,re.M).group(1));wanted_stiffness=int(re.search('_S(1|10|100)(?:_|$)',d.name).group(1));rows.append({'interface':sid,'native_damping':value,'expected':expected,'actual_Stfac':actual_stiffness,'wanted_Stfac':wanted_stiffness,'pass':abs(value-expected)<1e-6*expected and actual_stiffness==wanted_stiffness})
    dump(d/'requested_damping_gate.json',{'created_utc':now(),'rows':rows,'pass':all(r['pass'] for r in rows),'before_Engine':True})
    assert all(r['pass'] for r in rows),'Native damping readback differs; preserve Starter and stop before Engine'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run']);globals()[p.parse_args().action]()
