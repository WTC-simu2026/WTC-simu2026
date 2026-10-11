"""Fresh version/refinement witnesses and source-derived implicit reaction budget."""
from probe_aircraft_a35_mumps import *
import probe_aircraft_a35_mumps as previous
from linear_sandwich_reference_aircraft_a31 import solve as conventional
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a36'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a36_predeclaration.json'
CASES=[
 {'name':'WINDOWS_EXPLICIT_N2','N':2,'platform':'Windows','motion':'face','solver_N':0,'dt_ms':1e-5},
 {'name':'WINDOWS_EXPLICIT_N4','N':4,'platform':'Windows','motion':'face','solver_N':0,'dt_ms':1e-5},
 {'name':'LINUX_EXPLICIT_N4','N':4,'platform':'Linux','motion':'face','solver_N':0,'dt_ms':1e-5},
 {'name':'MUMPS_N4','N':4,'platform':'Linux','motion':'face','solver_N':2,'dt_ms':.001},
 {'name':'MUMPS_N4_HALF','N':4,'platform':'Linux','motion':'face','solver_N':2,'dt_ms':.0005},
 {'name':'MUMPS_N8','N':8,'platform':'Linux','motion':'face','solver_N':2,'dt_ms':.001},
 {'name':'WINDOWS_TRANSLATION','N':2,'platform':'Windows','motion':'translation','solver_N':0,'dt_ms':1e-5},
 {'name':'LINUX_TRANSLATION','N':2,'platform':'Linux','motion':'translation','solver_N':0,'dt_ms':1e-5},
 {'name':'MUMPS_TRANSLATION','N':2,'platform':'Linux','motion':'translation','solver_N':2,'dt_ms':.001},
]
for c in CASES:c.update(Iprec=2,It_max=0,Itol=1,Tol=1e-8)
SOURCE_FILES={
 'reaction_accumulation':'engine/source/output/th/bcs1th_imp.F',
 'reaction_nodes':'engine/source/output/th/thbcs_imp.F',
 'reaction_output':'engine/source/output/th/thnod.F',
 'reaction_call':'engine/source/engine/resol.F',
 'boundary_work_inertia':'engine/source/constraints/general/impvel/fv_imp0.F',
 'dynamics_work':'engine/source/implicit/imp_dyna.F',
}

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists()
 h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A35'
 cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A35'
 OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 c=read(previous.CFG);c.update(iteration='AIRCRAFT-A36',declared_utc=now(),seed=1102061,subscope='Independent continuum refinement and source-derived implicit reaction interpretation',cases=CASES,parent_configuration=rel(previous.CFG),parent_configuration_sha256=streamsha(previous.CFG))
 c['execution'].update(estimated_seconds_max=1800,per_process_cap_s=180,CPU_threads=1,GPU=False,installation=False,binary_changed=False)
 c['independent_refinement']={'N':[2,4,8,16],'same_geometry_material_and_face_BCs':True,'operator':'Conventional 8node2x2x2Gauss isotropic elasticity, matrix-free CG; no native stiffness or response fitted','reference_N8_N16_energy_fraction':.005,'reference_N8_N16_displacement_mm':2e-6,'native_N4_N8_energy_fraction':.01,'native_independent_IE_fraction':.02,'native_independent_displacement_mm':2e-5,'original_A35_gates_preserved':True}
 c['reaction_prediction']={'basis':'Pinned BCS1TH_IMP accumulates trapezoidal negative nodal residual A; FV_FINT0 separately adds MS*DY_A for boundary work. Test that implicit TH impulse excludes imposed-node inertia, not a multiplicative factor.','implicit_impulse':'Qsum-Qsum0 + sum(boundary_m * (v-v0)) = Ptotal-Ptotal0','implicit_work':'integral(dQ/dt dot v_boundary) + KEboundary-KEboundary0 = EW','explicit_impulse':'Qsum-Qsum0 = Ptotal-Ptotal0','explicit_work':'integral(dQ/dt dot v_boundary) = EW','tolerances':'Unchanged 2% maxDeltaP +1e-9Ns and 2%maxEW/reference +1e-7J','distinct_witness':'All nodes undergo the same smooth rigid translation; exact IE=0, KE/P from physical nodal masses. Implicit raw Q should vanish, while imposed-node inertia carries all P and work.','not_applied_to_A35_original_reviews':True,'general_constraints_rotational_DOF_or_mass_scaling':False}
 c['version_witness']='Fresh Windows N2 compared to cached A35 Linux N2; then fresh Windows/Linux N4. Same source material and fresh Starter on every case, no successful old Engine rerun.'
 c['sources']=[{'url':f'https://github.com/gabrielrussell/OpenRadioss/blob/{build.PIN}/{p}','local_path':rel(build.CAND/'source'/p),'sha256':streamsha(build.CAND/'source'/p),'redistribution':'reference_only_no_source_copy'} for p in SOURCE_FILES.values()]
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_references_and_native':True})
 pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(build.OUT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=build.OUT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archive_rescanned':False})
 source_review()
 print({'A36_declared':True,'fresh_cases':len(CASES),'maximum_process_s':180},flush=True)

def source_review():
 guard();facts={}
 for k,p in SOURCE_FILES.items():
  f=build.CAND/'source'/p;s=f.read_text(encoding='utf8');assert streamsha(f)==next(r['sha256'] for r in read(CFG)['sources'] if r['local_path']==rel(f))
  facts[k]={'path':p,'sha256':streamsha(f),'url':f'https://github.com/gabrielrussell/OpenRadioss/blob/{build.PIN}/{p}'}
 assert '- A(1,L)*DT3/TWO' in (build.CAND/'source'/SOURCE_FILES['reaction_accumulation']).read_text()
 assert 'A0   = A(J,I)+MS0*DY_A(J,I)' in (build.CAND/'source'/SOURCE_FILES['boundary_work_inertia']).read_text()
 dump(OUT/'primary_source_review.json',{'created_utc':now(),'source_commit':build.PIN,'files':facts,'observed_equations':{'TH':'Qn = Qprev -dt/2 * (A_n + A_prev), FTHDTM stores previous A','boundary_work':'FV_FINT0 forms A0=A+MS*DY_A and averages endpoint values; WFV_IMP uses it for imposed displacement work'},'hypothesis_to_test':'TH excludes imposed boundary nodal inertia; verify additive mass budget using distinct translation and face-loading witnesses. Not a fitted factor2.','source_physics_changed':False})

def references():
 guard();dest=OUT/'independent_reference';assert not dest.exists();dest.mkdir()
 E=73100.;nu=.33;lam=E*nu/((1+nu)*(1-2*nu));mu=E/(2*(1+nu));C=np.zeros((6,6));C[:3,:3]=lam;C[np.diag_indices(3)]+=2*mu;C[3:,3:]=np.eye(3)*mu
 for N in [2,4,8,16]:
  X,B,m,l,r=brick_grid([N]*3,[-.5]*3,[.5]*3);q=conventional(X,B,[1]*len(B),C,C,l,r,0,.001)
  dump(dest/f'N{N}.json',{'created_utc':now(),'N':N,'configuration_sha256':streamsha(CFG),**q})
  print({'reference_N':N,'energy_J':q['energy_J'],'seconds':q['seconds']},flush=True)
 q2=read(dest/'N2.json');X,B,m,l,r=brick_grid([2]*3,[-.5]*3,[.5]*3);old=solve(X,B,l,r,.001)
 assert abs(old['energy_J']-q2['energy_J'])<1e-12
 rows=[]
 for a,b in [(2,4),(4,8),(8,16)]:
  aa,bb=read(dest/f'N{a}.json'),read(dest/f'N{b}.json');ua=np.asarray(aa['displacements_mm']).reshape(a+1,a+1,a+1,3);ub=np.asarray(bb['displacements_mm']).reshape(b+1,b+1,b+1,3)[::b//a,::b//a,::b//a];ed=abs(aa['energy_J']-bb['energy_J'])/bb['energy_J'];ud=float(abs(ua-ub).max());rows.append({'from_N':a,'to_N':b,'energy_fraction':ed,'common_node_displacement_mm':ud,'pass':ed<.005 and ud<2e-6})
 dump(dest/'refinement_review.json',{'created_utc':now(),'comparisons':rows,'N8_N16_pass':rows[-1]['pass'],'dense_original_N2_equivalence':True,'before_native':True})

def reference_for(case,X):
 if case['motion']=='translation':
  u=np.zeros_like(X);u[:,0]=.001;return {'created_utc':now(),'energy_J':0.,'displacements_mm':u.tolist(),'method':'Exact prescribed rigid translation, zero strain; KE and momentum from physical nodal masses'}
 return read(OUT/'independent_reference'/f"N{case['N']}.json")

def execute(exe,args,d,log,timeout,en):
 if exe.name!='engine_win64.exe' or read(d/'generation.json')['case']['platform']=='Windows':return base.execute(exe,args,d,log,timeout,en)
 bindir=ROOT/read(build.OUT/'build_finished.json')['binary_directory'];binary=bindir/'engine_linux64_gf_ompi';assert binary.is_file();assert streamsha(binary)==next(r['sha256'] for r in read(build.OUT/'candidate_binary_review.json')['files'] if r['path']==rel(binary))
 env_vars={'OMP_NUM_THREADS':'1','RAD_HMPP_DOMAINS':'1','OPENBLAS_NUM_THREADS':'1','LD_LIBRARY_PATH':build.linux(bindir),'OPENRADIOSS_PATH':build.linux(build.CAND/'source'),'RAD_CFG_PATH':build.linux(build.CAND/'source/hm_cfg_files'),'RAD_H3D_PATH':build.linux(build.CAND/'source/extlib/h3d/lib/linux64')}
 launch=d/(log+'.launch.sh');assert not launch.exists();launch.write_text('#!/bin/bash\nset -euo pipefail\ncd '+shlex.quote(build.linux(d))+'\nexport '+' '.join(k+'='+shlex.quote(v) for k,v in env_vars.items())+'\nexec '+shlex.quote(build.linux(binary))+' '+' '.join(shlex.quote(a) for a in args)+' >'+shlex.quote(build.linux(d/log))+' 2>&1\n',encoding='utf8',newline='\n')
 command=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5',str(timeout),'bash',build.linux(launch)];t=time.perf_counter()
 with (d/(log+'.launcher.log')).open('wb') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=timeout+15)
 dump(d/(log+'.execution.json'),{'created_utc':now(),'argv':command,'environment':env_vars,'exit_code':r.returncode,'seconds':time.perf_counter()-t,'candidate_sha256':streamsha(binary),'CPU_threads':1,'GPU':False});return r.returncode==0

def runner():
 s=inspect.getsource(base.run_one)
 changes={"n='A31_IMPL_'":"n='A36_'","brick_grid([2,2,2]":"brick_grid([case['N']]*3","ref=solve(X,B,left,right,.001)":"ref=reference_for(case,X)","ii(0,123)+ff(1e-6,1e-6,1e-6)":"'0 123 1e-6 1e-6 1e-6'","'/IMPL/DTINI',ff(.001)":"'/IMPL/DTINI',ff(case['dt_ms'])",",60,en)":",180,en)","for ni in left+right:":"face_nodes=left+right if case['motion']=='face' else list(range(1,len(X)+1))\n    for ni in face_nodes:","fid=101 if ni in right and ax=='X' else 100":"fid=101 if ax=='X' and (ni in right or case['motion']=='translation') else 100","'boundary_nodes':left+right":"'boundary_nodes':face_nodes","if j not in left+right":"if j not in face_nodes"}
 for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
 s=s.replace("    (d/(n+'_0000.rad')).write_text","    L=L[:-1]+['/TH/NODE/2','PHYSICAL_FACE_REACTIONS',''.join(f'{v:>10}' for v in ['REACX','REACY','REACZ'])]+[ii(j,0) for j in face_nodes]+['/END']\n    (d/(n+'_0000.rad')).write_text")
 s=s.replace("    (d/(n+'_0001.rad')).write_text","    if case['solver_N']==0: E=E[E.index('/ANIM/DT'):]+['/DT',ff(.4,0),'/DTIX',ff(case['dt_ms'],case['dt_ms'])]\n    (d/(n+'_0001.rad')).write_text")
 ast.parse(s);dump(OUT/'runner_derivation.json',{'created_utc':now(),'parent':rel(Path(base.__file__)),'parent_sha256':streamsha(Path(base.__file__)),'changes':changes,'source':s,'original_thresholds_preserved':True});exec(compile(s,__file__+'::fresh','exec'),globals())
 s=inspect.getsource(previous.audit_fields);exec(compile(s,__file__+'::fields','exec'),globals())

def transfer(case,d=None):
 d=d or OUT/case['name'];g=read(d/'generation.json');H=histories(d/(g['name']+'T01.csv'));T=H['time'];nk=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];fk=[k for k in H if k.startswith('PHYSICAL_FACE_REACTIONS')];nids=[int(re.match(r'NATIVE_SCOPE_NODES\s+(\d+)\s',k).group(1)) for k in nk][::6];fids=[int(re.match(r'PHYSICAL_FACE_REACTIONS\s+(\d+)\s',k).group(1)) for k in fk][::3];assert set(nids)==set(range(1,len(g['nodes_mm'])+1)) and set(fids)==set(g['boundary_nodes'])
 m=np.asarray(g['nodal_masses_g']);N=np.column_stack([H[k] for k in nk]).reshape(len(T),len(m),6);V=N[:,:,3:];Q=np.column_stack([H[k] for k in fk]).reshape(len(T),len(fids),3);idx={ni:i for i,ni in enumerate(nids)};bi=np.asarray([idx[i] for i in fids]);mb=m[np.asarray(fids)-1];P=np.sum(m[np.asarray(nids)-1][None,:,None]*V,axis=1)*.001;PB=np.sum(mb[None,:,None]*V[:,bi,:],axis=1)*.001;KB=.5*np.sum(mb[None,:,None]*V[:,bi,:]**2,axis=(1,2))*.001;raw=(Q.sum(axis=1)-Q[0].sum(axis=0))*.001;dp=P-P[0];implicit=case['solver_N']!=0;J=raw+(PB-PB[0] if implicit else 0)
 F=np.gradient(Q,T,axis=0,edge_order=2);power=np.sum(F*V[:,bi,:],axis=(1,2));W=np.r_[0.,np.cumsum((power[1:]+power[:-1])*.5*np.diff(T))]*.001+(KB-KB[0] if implicit else 0);EW=H['EXTERNAL WORK']*.001;pt=.02*float(np.linalg.norm(dp,axis=1).max())+1e-9;wt=.02*max(float(abs(EW).max()),read(d/'reference_before_native.json')['energy_J'])+1e-7;je=float(np.linalg.norm(J-dp,axis=1).max());we=float(abs(W-EW).max());rawerr=float(np.linalg.norm(raw-dp,axis=1).max());qfree=float(np.linalg.norm(raw-(dp-PB+PB[0]),axis=1).max())
 checks={'physical_nodal_momentum_matches_global':bool(abs(P-np.column_stack([H[a+'-MOMENTUM'] for a in 'XYZ'])*.001).max()<pt),'source_predicted_impulse':je<pt,'source_predicted_work':we<wt}
 if case['motion']=='translation':checks['implicit_raw_Q_zero' if implicit else 'explicit_raw_Q_is_full_impulse']=bool(np.linalg.norm(raw,axis=1).max()<pt if implicit else rawerr<pt)
 q={'created_utc':now(),'case':case['name'],'checks':checks,'pass':all(checks.values()),'raw_vs_total_impulse_error_Ns':rawerr,'raw_vs_free_impulse_error_Ns':qfree,'source_predicted_total_impulse_error_Ns':je,'tolerance_Ns':pt,'boundary_work_error_J':we,'work_tolerance_J':wt,'boundary_mass_g':float(mb.sum()),'mass_addition':False,'coefficient_fit':False,'source_rule_applied':implicit,'corrected_impulse':'rawQ + measuredPhysicalBoundaryDeltaP' if implicit else 'rawQ','corrected_work':'dQdt_work + measuredPhysicalBoundaryDeltaKE' if implicit else 'dQdt_work'}
 return q

def run():
 guard();assert (OUT/'independent_reference/refinement_review.json').exists();runner();rows=[];trs=[]
 for c in CASES:
  run_one(c);r=audit_fields(c);rows.append(r)
  if r['binary_implicit_completion']:q=transfer(c);dump(OUT/c['name']/'source_predicted_transfer.json',q);trs.append(q)
 dump(OUT/'native_review.json',{'created_utc':now(),'cases':rows,'transfer':trs,'old_successful_solver_reruns':0,'whole_impact_qualified':False})
 compare()

def compare():
 guard();rows=[]
 pairs=[('WINDOWS_EXPLICIT_N2',previous.OUT/'w1_launcher/EXPLICIT','Windows_Linux_N2',.02),('WINDOWS_EXPLICIT_N4',OUT/'LINUX_EXPLICIT_N4','Windows_Linux_N4',.02),('LINUX_EXPLICIT_N4',OUT/'MUMPS_N4','explicit_implicit_N4',.02),('MUMPS_N4',OUT/'MUMPS_N4_HALF','implicit_half_dt',.002),('MUMPS_N4',OUT/'MUMPS_N8','native_N4_N8',.01)]
 for a,bd,label,frac in pairs:
  ds=[OUT/a,bd];hh=[histories(d/(read(d/'generation.json')['name']+'T01.csv')) for d in ds];t=min(h['time'][-1] for h in hh);ee=[float(np.interp(t,h['time'],h['INTERNAL ENERGY']+h['HOURGLASS ENERGY']))*.001 for h in hh];df=abs(ee[0]-ee[1]);tol=frac*max(ee)+1e-7;rows.append({'comparison':label,'time_ms':float(t),'energies_J':ee,'difference_J':df,'tolerance_J':tol,'pass':df<tol})
 dump(OUT/'comparison_review.json',{'created_utc':now(),'pairs':rows,'pass':all(r['pass'] for r in rows),'availability_only_whole_not_qualified':True})
 print({'A36_comparisons':[(r['comparison'],r['pass']) for r in rows]},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','references','run','compare']);globals()[p.parse_args().action]()
