"""Fresh same-version native probes, with unchanged A31 physical fixture/gates."""
from probe_aircraft_a31_implicit import *
import probe_aircraft_a31_implicit as base
import build_aircraft_a35_mumps as build
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import inspect, ast, subprocess, time, shlex
OUT=build.OUT/'implicit_capability'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a35_implicit_capability.json'
CASES=[{'name':'EXPLICIT','solver_N':0,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8,'dt_ms':1e-5},
 {'name':'EXPLICIT_HALF','solver_N':0,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8,'dt_ms':5e-6},
 {'name':'PCG','solver_N':1,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8,'dt_ms':.001},
 {'name':'MUMPS','solver_N':2,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8,'dt_ms':.001},
 {'name':'MUMPS_HALF','solver_N':2,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8,'dt_ms':.0005}]
def declare():
 assert not OUT.exists() and not CFG.exists();OUT.mkdir();c=read(base.CFG)
 c.update(iteration='AIRCRAFT-A35',declared_utc=now(),seed=1102060,subscope='FreshLinuxcandidateMUMPSwithsame-versionexplicitcontrols',parent_configuration=rel(base.CFG),parent_configuration_sha256=streamsha(base.CFG),cases=CASES,
   build_configuration=rel(build.CFG),source_commit=build.PIN,Windows_restart_reused=False,whole_inputs_changed=False)
 c['implicit']['cases']=CASES;c['execution'].update(binary_changed=True,installation=True,CPU_threads=1,per_process_cap_s=120,estimated_seconds_max=1200)
 c['format_repair']={'record':'NONLIN whitespace-separated all5valueswithin72characters','previous_A31_failures_preserved':True}
 c['additional_acceptance']={'finite_histories':True,'three_field_samples':'ids/finite/coordinate-displacement bound/noerosion','field_reference_final_mm':2e-5,'same_version_energy_difference':'2% +1e-7J at common native history time','temporal_energy_difference':'0.2% +1e-7J at common time','actually_half_implicit_dt_ratio':.6,'scope':'Tinyelasticavailabilityfixture only; no whole contact, plasticity, restart or transition qualification'}
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True});print({'fresh_cases_declared':len(CASES)},flush=True)
def execute(exe,args,d,log,timeout,en):
 if exe.name=='starter_win64.exe' and (OUT/'Windows_Starter_bridge_predeclaration.json').exists():
  return base.execute(exe,args,d,log,timeout,en)
 if exe.name not in ['starter_win64.exe','engine_win64.exe']:
  return base.execute(exe,args,d,log,timeout,en)
 bindir=ROOT/read(build.OUT/'build_finished.json')['binary_directory']
 binary=bindir/('starter_linux64_gf' if exe.name.startswith('starter') else 'engine_linux64_gf_ompi')
 assert binary.is_file()
 env_vars={'OMP_NUM_THREADS':'1','RAD_HMPP_DOMAINS':'1','OPENBLAS_NUM_THREADS':'1','LD_LIBRARY_PATH':build.linux(bindir),'OPENRADIOSS_PATH':build.linux(build.CAND/'source'),'RAD_CFG_PATH':build.linux(build.CAND/'source/hm_cfg_files'),'RAD_H3D_PATH':build.linux(build.CAND/'source/extlib/h3d/lib/linux64')}
 export=' '.join(k+'='+shlex.quote(v) for k,v in env_vars.items())
 command=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5',str(timeout),'bash','-c','cd "$1" && export '+export+' && exec "$2" "${@:3}" >'+shlex.quote(build.linux(d/log))+' 2>&1','probe',build.linux(d),build.linux(binary),*args]
 t=time.perf_counter()
 with (d/(log+'.launcher.log')).open('wb') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=timeout+15)
 dump(d/(log+'.execution.json'),{'created_utc':now(),'argv':command,'environment':env_vars,'exit_code':r.returncode,'seconds':time.perf_counter()-t,'candidate_sha256':streamsha(binary),'CPU_threads':1,'GPU':False});return r.returncode==0
def runner():
 s=inspect.getsource(base.run_one)
 edits={"n='A31_IMPL_'":"n='A35_IMPL_'","ii(0,123)+ff(1e-6,1e-6,1e-6)":"'0 123 1e-6 1e-6 1e-6'","'/IMPL/DTINI',ff(.001)":"'/IMPL/DTINI',ff(case['dt_ms'])",",60,en)":",120,en)"}
 for a,b in edits.items():assert a in s,a;s=s.replace(a,b)
 old="    (d/(n+'_0001.rad')).write_text"
 s=s.replace(old,"    if case['name'].startswith('EXPLICIT'): E=E[E.index('/ANIM/DT'):]+['/DT',ff(.4,0),'/DTIX',ff(case['dt_ms'],case['dt_ms'])]\n"+old)
 s=s.replace("    (d/(n+'_0000.rad')).write_text","    L=L[:-1]+['/TH/NODE/2','PHYSICAL_FACE_REACTIONS',''.join(f'{v:>10}' for v in ['REACX','REACY','REACZ'])]+[ii(j,0) for j in left+right]+['/END']\n    (d/(n+'_0000.rad')).write_text")
 ast.parse(s);dump(OUT/'runner_derivation.json',{'created_utc':now(),'parent_source':rel(Path(base.__file__)),'parent_source_sha256':streamsha(Path(base.__file__)),'changes':edits,'derived_source':s,'thresholds_unchanged':True,'fresh_restart':True});exec(compile(s,__file__+'::candidate','exec'),globals())
def audit_fields(case):
 d=OUT/case['name'];g=read(d/'generation.json');n=g['name'];r=read(d/'review.json');rows=[];checks={}
 if r['binary_implicit_completion']:
  H=histories(d/(n+'T01.csv'));checks['finite_histories']=all(np.isfinite(v).all() for v in H.values());X=np.asarray(g['nodes_mm']);ref=read(d/'reference_before_native.json');reference=np.asarray(ref['displacements_mm'])
  natives=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))
  checks['at_least_three_fields']=len(natives)>=3
  for p in sorted(set([natives[0],natives[len(natives)//2],natives[-1]])):
   res=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=60);v=d/(p.name+'.vtk');v.write_text(res.stdout,encoding='utf8');q=vtk(res.stdout);order=np.argsort(q['NODE_ID']);pts=q['points'].reshape(-1,3)[order];u=q['Displacement'].reshape(-1,3)[order];vel=q['Velocity'].reshape(-1,3)[order]
   bound=printed_bound(pts)+printed_bound(u)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(pts),abs(u),abs(X)])+1e-8
   ck={'ids':bool(np.array_equal(q['NODE_ID'][order],np.arange(1,len(X)+1))),'finite':bool(np.isfinite(pts).all() and np.isfinite(u).all() and np.isfinite(vel).all()),'coordinate_displacement_identity':bool(np.all(abs(pts-X-u)<=bound)),'no_erosion':bool(np.all(q['EROSION_STATUS']==1))}
   tt=q['time']/.05;ss=3*tt*tt-2*tt*tt*tt;error=float(abs(u-reference*ss).max());rows.append({'time_ms':q['time'],'native_sha256':streamsha(p),'vtk_sha256':streamsha(v),'checks':ck,'reference_displacement_error_mm':error,'pass':all(ck.values())})
  checks['native_fields']=all(x['pass'] for x in rows);checks['independent_displacement']=rows[-1]['reference_displacement_error_mm']<2e-5
 r['additional_checks']=checks;r['native_scope_pass']=r['all_declared_checks_pass'] and all(checks.values()) and bool(checks);dump(d/'field_review.json',{'created_utc':now(),'fields':rows,'review':r,'whole_impact_qualified':False});return r
def declare_transfer():
 guard();p=OUT/'transfer_predeclaration.json';assert not p.exists()
 dump(p,{'created_utc':now(),'before_native':True,'seed':1102060,'configuration_sha256':streamsha(CFG),'reaction_cases':CASES,'TH_NODE_group':'Boundary-onlyREACXYZ, independentfromfullnodeDX/DY/DZ/VX/VY/VZ','momentum_tolerance':'2% of maxDeltaP +1e-9Ns, inheritedA33','reaction_units':'Compare rawsum difference and force-integral to DeltaP independently; require exactlyoneinterpretation. Do not assume Windowsreaction semantics in Linux implicit.','work_tolerance':'2%maxEW/reference +1e-7J inheritedA31/A33','compare_energy':'2% +1e-7J at commonnative time; time refinement0.2% +1e-7J','implicit_dt_half_ratio_max':.6,'scope':'Nativeavailability/transferelasticfixture; wholeimpactfalse'})
 print({'transfer_protocol_declared':True},flush=True)
def transfer(case):
 d=OUT/case['name'];r=read(d/'field_review.json')['review']
 if not r['binary_implicit_completion']:return {'case':case['name'],'pass':False,'reason':'native_not_complete'}
 H=histories(d/(read(d/'generation.json')['name']+'T01.csv'));g=read(d/'generation.json');T=H['time'];m=np.asarray(g['nodal_masses_g']);nodes=np.column_stack([H[k] for k in H if k.startswith('NATIVE_SCOPE_NODES')]).reshape(len(T),len(m),6);V=nodes[:,:,3:];P=np.sum(m[None,:,None]*V,axis=1)*.001;faces=np.asarray(g['boundary_nodes'])-1;Q=np.column_stack([H[k] for k in H if k.startswith('PHYSICAL_FACE_REACTIONS')]).reshape(len(T),len(faces),3)
 def trap(y):return np.concatenate([np.zeros_like(y[:1]),np.cumsum((y[1:]+y[:-1])*.5*np.diff(T).reshape((-1,)+(1,)*(y.ndim-1)),axis=0)],axis=0)
 dp=P-P[0];a=float(np.linalg.norm((Q.sum(axis=1)-Q[0].sum(axis=0))*.001-dp,axis=1).max());b=float(np.linalg.norm(trap(Q.sum(axis=1))*.001-dp,axis=1).max());tol=.02*float(np.linalg.norm(dp,axis=1).max())+1e-9;imp=a<tol;force=b<tol;unique=imp!=force;F=np.gradient(Q,T,axis=0,edge_order=2) if imp and not force else Q;W=trap(np.sum(F*V[:,faces,:],axis=(1,2)))*.001;EW=H['EXTERNAL WORK']*.001;wtol=.02*max(float(abs(EW).max()),read(d/'reference_before_native.json')['energy_J'])+1e-7;we=float(abs(W-EW).max());ck={'unique_reaction_interpretation':unique,'native_reaction_work':unique and we<wtol,'global_history_momentum_matches_nodes':bool(np.max(abs(P-np.column_stack([H[ax+'-MOMENTUM'] for ax in 'XYZ'])*.001))<tol)}
 q={'created_utc':now(),'case':case['name'],'checks':ck,'pass':all(ck.values()),'raw_impulse_error_Ns':a,'force_integral_error_Ns':b,'tolerance_Ns':tol,'interpretation':'impulse' if imp and not force else 'force' if force and not imp else 'undetermined','boundary_work_error_J':we,'work_tolerance_J':wtol,'native_diagnostics_scope_only':True};dump(d/'transfer_review.json',q);return q
def comparisons():
 guard();rows=[]
 for a,b,label,frac in [('EXPLICIT','EXPLICIT_HALF','explicit_time',.002),('MUMPS','MUMPS_HALF','implicit_time',.002),('EXPLICIT','MUMPS','same_version_explicit_implicit',.02),('PCG','MUMPS','same_version_PCG_MUMPS',.02)]:
  ds=[OUT/n for n in [a,b]]
  if not all(read(d/'review.json')['binary_implicit_completion'] for d in ds):rows.append({'comparison':label,'pass':False,'reason':'case_not_completed'});continue
  hs=[histories(d/(read(d/'generation.json')['name']+'T01.csv')) for d in ds];t=min(h['time'][-1] for h in hs);e=[float(np.interp(t,h['time'],h['INTERNAL ENERGY']+h['HOURGLASS ENERGY']))*.001 for h in hs];diff=abs(e[0]-e[1]);tol=frac*max(e)+1e-7;ratio=float(np.median(hs[1]['TIME STEP'][1:])/np.median(hs[0]['TIME STEP'][1:]));ck={'elastic_energy':diff<tol}
  if label.endswith('_time'):ck['actual_half_step']=ratio<.6
  rows.append({'comparison':label,'common_time_ms':float(t),'energies_J':e,'difference_J':diff,'tolerance_J':tol,'actual_dt_ratio':ratio,'checks':ck,'pass':all(ck.values())})
 dump(OUT/'same_version_comparisons.json',{'created_utc':now(),'comparisons':rows,'pass':all(r['pass'] for r in rows),'whole_impact_qualified':False});return rows
def run():
 guard();assert (OUT/'transfer_predeclaration.json').exists();f=read(build.OUT/'build_finished.json');assert f.get('engine_built') or f['build_commands_completed'];runner();rows=[]
 for case in CASES:run_one(case);rows.append(audit_fields(case))
 tr=[transfer(c) for c in CASES];cp=comparisons();dump(OUT/'fresh_capability_review.json',{'created_utc':now(),'cases':rows,'transfer':tr,'comparisons':cp,'native_scope_pass':all(r['native_scope_pass'] for r in rows) and all(t['pass'] for t in tr) and all(c['pass'] for c in cp),'whole_impact_qualified':False,'requested_physical_horizon_s':.00005,'last_history_times_ms':{r['name']:read(OUT/r['name']/'native_diagnostics.json')['last_ms'] for r in rows if (OUT/r['name']/'native_diagnostics.json').exists()}});dump(OUT/'harness_after.json',harness())
def declare_bridge():
 guard();p=OUT/'Windows_Starter_bridge_predeclaration.json';assert not p.exists() and not (OUT/'EXPLICIT').exists()
 dump(p,{'declared_utc':now(),'before_native':True,'reason':'NativeLinuxStarterlink failed. Use unchangedWindowsStarter for freshnewsmallfixtures, then newLinuxEngine for BOTH explicit andimplicit; testcross-version/platformcompatibility inthisscope,neverassumeallrestartcompatibility.','configuration_sha256':streamsha(CFG),'Windows_Starter':{'path':rel(RUNTIME/'starter_win64.exe'),'sha256':streamsha(RUNTIME/'starter_win64.exe')},'Linux_engine':{'path':read(build.OUT/'build_finished.json')['binary_directory']+'/engine_linux64_gf_ompi','sha256':streamsha(ROOT/read(build.OUT/'build_finished.json')['binary_directory']/'engine_linux64_gf_ompi')},'old_restart_reused':False,'same_version_explicit_implicit':'SamecompiledLinuxEngine andsameWindowsStarter for allfivefreshcases','gates_unchanged':True,'whole_impact_qualified':False,'Linux_Starter_build_success':False})
 print({'fresh_compatibility_bridge_declared':True,'old_restart_reused':False},flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','declare_transfer','declare_bridge','run']);globals()[p.parse_args().action]()
