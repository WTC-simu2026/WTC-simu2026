"""Zero initial lever arm penalty footprints, declared mechanics before curved root mapping."""
from run_aircraft_a24 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,brick_grid,inertia,prop,group,material,solid_property,skew_card,face_property,histories,SOURCE
import run_aircraft_a23 as A23
import test_aircraft_a24_angular as A24
import argparse,inspect,json,shutil,re,traceback,time
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a25'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a25_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a24'

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A24';OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a24_angular.json')
    c.update(iteration='AIRCRAFT-A25',declared_utc=now(),seed=1102050,random_draws=0,purpose='Test the explicit hypothesis that the initial offset of Spot25 creates a missing lever moment. Tie only top footprint nodes initially on the main midsurfaces, rather than offset end-cap nodes. Candidate lap ribbon, not historical identification.',
      cases={'primitive':[],'paired':['CONNECTED_FREE_ROTATION_X','CONNECTED_FREE_ROTATION_Y','CONNECTED_FREE_ROTATION_Z','CONNECTED_FREE_TRANSLATION','CONNECTED_FREE_ROTATION_Y_HALF','CONNECTED_EXTENSION_N4','CONNECTED_EXTENSION_N8']},
      changed_since_A24={'geometry':'same4x1x.5mm ribbon shifted+0.25mm in z, top at lower-skin/backing midsurface z=-4.25; central bridge unbonded, top x<=-1 bonded to backing and x>=1 to lower skin','mass':'same.00556g; CG and inertia explicitly changed by geometric translation, not compensated','root_ties':'Spot25 Stfac100 Istf2 Visc1e-20; search1e-5mm, initial projection distance must be zero; footprint not offset cap','reference':'reuse A24w3 native free references with shell angular observations; new reference stiffness uses actual bonded top-node sets','limitations':'midsurface lap ribbon idealizes shell thickness and includes half-thickness geometric overlap. Strength, fracture, fatigue, rivet pattern and as-built root are unknown; no whole insertion inferred from flat controls'},
      native_reference_paths={f'ROTATION_{a}':rel(PREV/'w3'/f'REFERENCE_FREE_ROTATION_S100_{a}') for a in 'XYZ'},
      actual_root_mapping_required=True,whole_insertion_ready=False,objective1_complete=False,old_A20_A24_native_solver_reruns=0)
    c['fixture']['clip_bounds_mm']=[[-2,4.5,-4.75],[2,5.5,-4.25]]
    c['native_reference_paths'].update(TRANSLATION=rel(PREV/'w3/REFERENCE_FREE_TRANSLATION_S100'),ROTATION_Y_HALF=rel(PREV/'w3/REFERENCE_FREE_ROTATION_S100_Y_HALF'))
    c['execution'].update(estimated_minutes=[3,8],per_process_cap_s=600,CPU_threads=1,GPU=False)
    c['acceptance'].update(physical_angular_total_fraction=.002,physical_angular_added_fraction=.02,physical_angular_absolute_kg_m2_s=1e-9,initial_projection_mm=1e-8)
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True})
    paths=[Path(A23.__file__),Path(A24.__file__),SOURCE/'mesh.json',PREV/'scientific_assessment.json',PREV/'physical_angular_momentum_review.json',PREV/'stiffness_review.json']
    paths+=list({ROOT/p for p in c['native_reference_paths'].values()})
    sources=[]
    for p in paths:
        for q in ([p] if p.is_file() else [p/'generation.json',p/'review.json',p/'histories_SI.npz']):sources.append({'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)})
    sd=OUT/'sources';sd.mkdir();q=sd/'type2.html';shutil.copy2(PREV/'sources/type2.html',q);sources.append({'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q),'url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm','redistribution':'exclude_third_party'})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'historical_damage_target':False,'archive_rescanned':False});print({'declared':'AIRCRAFT-A25','native_cases':7,'CPU_minutes':[3,8]},flush=True)

def guard():
    assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def axis(cid):return re.search(r'ROTATION_([XYZ])',cid).group(1)

def imposed(L,xyz,node_ids,cid,start=10000,rotational_DOF=True):
    assert 'EXTENSION' in cid;T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;cache={}
    for ni in node_ids:
        L+=group(ni,f'KNOWN_NODE_{ni}',[int(ni)])
        for ax,direction in enumerate(['X','Y','Z','XX','YY','ZZ'] if rotational_DOF else ['X','Y','Z']):
            val=.004*s if ni<=8 and ax==0 else np.zeros(len(T));key=val.tobytes()
            if key not in cache:
                start+=1;cache[key]=start;L+=[f'/FUNCT/{start}',f'KNOWN_SHARED_{start}']+[ff(t,v) for t,v in zip(T,val)]
            fid=cache[key];start+=1;L+=[f'/IMPDISP/{start}',f'KNOWN_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,int(ni))+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def create_runner():
    s=inspect.getsource(A23.run_one);audit=[]
    replacements=[
      ("free=cid.startswith('FREE_')","free='FREE_' in cid"),
      ("n='A23_'+cid","n='A25_'+cid"),
      ("duration=.05 if free else 1","duration=.05 if free else .1"),
      ("clip_ids=np.arange(21,21+len(clip));xyz=np.vstack([xyz,clip]);materials+=", "top=np.flatnonzero(abs(clip[:,2]+4.25)<1e-12)+21;left=top[clip[top-21,0]<=-1].tolist();right=top[clip[top-21,0]>=1].tolist();clip_ids=np.arange(21,21+len(clip));xyz=np.vstack([xyz,clip]);materials+="),
      ("ii(sid,sid,1000,5,0,2,1000,0)+ff(.8),ii(0)","ii(sid,sid,1000,25,0,2,1000,0)+ff(1e-5),ff(100,1e-20)+' '*20+ii(2),ii(0)"),
      ("ff(.4,0)","ff(.2 if cid.endswith('_HALF') else .4,0)"),
      ("ff(.000025,.000025)","ff(.0000005,.0000005) if cid.endswith('_HALF') else ff(.000025,.000025)"),
      (",180,en)",",600,en)"),
      ("omega=np.eye(3)['XYZ'.index(cid[-1])]*10;V=np.cross(omega,xyz)","omega=np.eye(3)['XYZ'.index(axis(cid))]*10 if 'ROTATION_' in cid else np.zeros(3);V=np.cross(omega,xyz) if 'ROTATION_' in cid else np.tile([-200,5,2],(len(xyz),1))"),
      ("else:L=imposed(L,main_xyz,main_ids,cid,rotational_DOF=not primitive)","\n        if 'ROTATION_' in cid:\n            for ni in main_ids:L+=[f'/INIVEL/ROT/{100000+ni}',f'INITIAL_SHELL_ROTATION_{ni}',ff(*omega)+ii(ni,0),ff(0)+ii(0)]\n    else:L=imposed(L,main_xyz,main_ids,cid,rotational_DOF=not primitive)"),
      ("np.array([0,5,-4.75])","np.array([0,5,-4.5])"),
      ("'VX','VY','VZ'","'VX','VY','VZ','VRX','VRY','VRZ'"),
      ("dump(d/'generation.json',generation);en=env()","known=np.zeros(len(xyz));known[:8]=.0915/4;known[8:16]=.0384/8;known[16:20]=.139/4;known[clip_ids-1]=mass;generation.update(known_translational_node_masses_g=known.tolist(),axis=axis(cid) if 'ROTATION_' in cid else None,initial_omega_rad_ms=omega.tolist() if free else None,initial_velocity_m_s=V.tolist() if free else None,bonded_footprint_nodes={'body':left,'skin':right},root_penalty_parameters={'Spot':25,'Stfac':100,'Visc':1e-20,'Istf':2,'dsearch_mm':1e-5},initial_projection_distance_mm=float(abs(xyz[np.asarray(left+right)-1,2]+4.25).max()));dump(d/'generation.json',generation);en=env()"),
    ]
    for old,new in replacements:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    s=s.replace("        assert execute(RUNTIME/'engine_win64.exe'","        verify_parameters(d,n)\n        assert execute(RUNTIME/'engine_win64.exe'");exec(compile(s,__file__+'::derived_run_one','exec'),globals())
    p=OUT/'runner_derivation.json'
    if not p.exists():dump(p,{'created_utc':now(),'source':rel(Path(A23.__file__)),'source_sha256':streamsha(Path(A23.__file__)),'changes':audit,'derived_function_source':s,'A23_unmodified':True})

def verify_parameters(d,n):
    g=read(d/'generation.json');assert g['initial_projection_distance_mm']<1e-8;text=(d/(n+'_0000.out')).read_text();rows=[]
    for sid in [301,302]:
        b=re.search(r'INTERFACE NUMBER\s*:\s*'+str(sid)+r'\b(.*?)(?=INTERFACE NUMBER|\Z)',text,re.S).group(1);v=float(re.search(r'CRITICAL DAMPING FACTOR.*?([+\-]?\d[\d.]*E[+\-]\d+)',b).group(1));sf=float(re.search(r'STIFFNESS FACTOR.*?([+\-]?\d[\d.]*(?:E[+\-]\d+)?)\s*$',b,re.M).group(1));rows.append({'interface':sid,'native_Visc':v,'native_Stfac':sf,'pass':abs(v-1e-20)<1e-26 and sf==100})
    dump(d/'parameters_gate.json',{'created_utc':now(),'rows':rows,'initial_projection_distance_mm':g['initial_projection_distance_mm'],'pass':all(r['pass'] for r in rows),'before_Engine':True});assert all(r['pass'] for r in rows)

def review(d,n):
    guard();g=read(d/'generation.json');H=histories(d/(n+'T01.csv'));T=H['time'];xyz=np.asarray(g['nodes_mm']);keys=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(keys)==9*len(xyz);node=np.column_stack([H[k] for k in keys]).reshape(len(T),len(xyz),9);X=xyz+node[:,:,:3];V=node[:,:,3:6];W=node[:,:,6:9]
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=sum(H[k] for k in terms)*.001;IE=H['INTERNAL ENERGY']*.001;EW=H['EXTERNAL WORK']*.001;R=E-E[0]-EW;scale=max(float(abs(E).max()),float(abs(EW).max()));P=np.column_stack([H[a+'-MOMENTUM'] for a in 'XYZ'])*.001
    checks={'normal_termination':True,'zero_warnings_errors':read(d/'starter_gate.json')['pass'],'parameters_readback':read(d/'parameters_gate.json')['pass'],'declared_mass':abs(H['MASS'][0]-.36596)<1e-6*.36596,'constant_mass':abs(H['MASS']-H['MASS'][0]).max()<1e-6*.36596,'no_added_mass':abs(H['ADDED MASS']).max()<1e-9*.36596,'native_full_energy_balance':abs(R).max()<.02*scale+1e-7,'nonnegative_IE':IE.min()>-1e-7,'no_undeclared_contact_damping':abs(H['DAMPING CONTACT ENERGY ']).max()*.001<1e-12};clip_ie=None;ref_ie=None
    if g['free']:
        checks.update(initial_shell_rotational_velocity_readback=abs(W[0,np.asarray(g['main_node_ids'])-1]-np.asarray(g['initial_omega_rad_ms'])).max()<1e-6,no_external_work=abs(EW).max()<1e-7,free_energy=abs(E-E[0]).max()<.002*E[0]+1e-7,free_momentum=abs(P-P[0]).max()<.002*np.linalg.norm(P[0])+1e-9)
        if 'TRANSLATION' in g['case']:
            checks.update(uniform_free_translation_position=abs(X-(xyz[None,:,:]+T[:,None,None]*np.array([-200,5,2]))).max()<.002,uniform_free_translation_velocity=abs(V-np.array([-200,5,2])).max()<.005)
    else:
        from linear_hexa_reference_aircraft_a23 import solve
        q=xyz[np.asarray(g['clip_node_ids'])-1];bricks=[[v-20 for v in row] for row in g['bricks']];left=[i-20 for i in g['bonded_footprint_nodes']['body']];right=[i-20 for i in g['bonded_footprint_nodes']['skin']];ref=solve(q,bricks,left,right);dump(d/'independent_footprint_elastic_reference.json',ref);ref_ie=ref['energy_J'];clip_ie=float(next(H[k][-1]*.001 for k in H if k.startswith('FINITE_METAL_CLIP') and k.strip().endswith('IE')));checks['footprint_elastic_reference']=abs(clip_ie-ref_ie)<.02*ref_ie+1e-7
    checks={k:bool(v) for k,v in checks.items()};np.savez_compressed(d/'histories_SI.npz',time_ms=T,total_J=E,IE_J=IE,EW_J=EW,residual_J=R,KE_J=(H['KINETIC ENERGY']+H['ROTATION ENERGY'])*.001,positions_mm=X,velocities_m_s=V,angular_velocity_rad_ms=W,momentum_Ns=P,time_step_ms=H['TIME STEP'])
    r={'created_utc':now(),'case':g['case'],'rows':len(T),'last_ms':float(T[-1]),'native_mass_g':float(H['MASS'][0]),'maximum_residual_J':float(abs(R).max()),'native_initial_total_J':float(E[0]),'last_clip_IE_J':clip_ie,'independent_reference_IE_J':ref_ie,'checks':checks,'pass':all(checks.values()),'whole_impact_qualified':False,'physical_strength_or_fracture_qualified':False};dump(d/'review.json',r);print({'case':g['case'],'pass':r['pass'],'failed':[k for k,v in checks.items() if not v]},flush=True)

def run():
    guard();create_runner()
    for cid in read(CFG)['cases']['paired']:
        d=OUT/'w0'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case, no implicit rerun'
        else:run_one(cid)
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'cases':[read(OUT/'w0'/c/'review.json') for c in read(CFG)['cases']['paired']],'whole_insertion_ready':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
