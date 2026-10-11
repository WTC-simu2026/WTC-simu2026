"""Distinct observable rigid translation, preserving the nine original witnesses."""
from probe_aircraft_a36 import *
import probe_aircraft_a36 as original
OUT=original.OUT/'w1_observable'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a36_observable_translation.json'
CASES=[{'name':'MUMPS_TRANSLATION_DT100','N':2,'platform':'Linux','motion':'translation','solver_N':2,'dt_ms':.0001,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8},
 {'name':'MUMPS_TRANSLATION_DT050','N':2,'platform':'Linux','motion':'translation','solver_N':2,'dt_ms':.00005,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8}]

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();OUT.mkdir();c=read(original.CFG)
 c.update(declared_utc=now(),subscope='Observable rigid translation and temporal refinement, original failed case retained',parent_configuration=rel(original.CFG),parent_configuration_sha256=streamsha(original.CFG),cases=CASES)
 c['motion'].update(displacement_mm=.1,duration_ms=.05)
 c['distinct_scope']={'displacement_change':'Rigid prescribed translation100timeslarger, strain remainszero; samephysicalmass, no nativeinputmass/materialchange','reason':'Original rigid translation KE1.25e-9J belowabsolute1e-7J; cannot qualify measurable KE/work from that gate alone. Original global momentum failed and remains failed.','physical_nodal_KE_vs_native':'2% of peak known-mass KE +1e-7J','observable_peak_KE_min_J':1e-6,'TH_global_momentum':'Same original2%maxDeltaP+1e-9Ns','dt_refinement':'Two prospectivelydeclared smallerNewmarksteps; no outputmatching factor or changedtolerances','all_original_case_reviews_preserved':True}
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True});print({'observable_translation_declared':True,'cases':2},flush=True)

def reference_for(case,X):
 u=np.zeros_like(X);u[:,0]=.1;return {'created_utc':now(),'energy_J':0.,'displacements_mm':u.tolist(),'method':'Exact zero-strain rigid translation; physical nodal masses independently determine KE/P.'}

def run():
 guard()
 for name in ['execute','runner','transfer']:
  s=inspect.getsource(getattr(original,name));exec(compile(s,__file__+'::'+name,'exec'),globals())
 runner();s=read(OUT/'runner_derivation.json')['source'];assert '.001*u' in s;s=s.replace('.001*u','.1*u');exec(compile(s,__file__+'::observable_amplitude','exec'),globals())
 dump(OUT/'amplitude_derivation.json',{'created_utc':now(),'parent_script_sha256':streamsha(Path(original.__file__)),'single_generator_change':'Prescribed translation amplitude .001→.1 mm; zero strains, no physical density or mass change','derived_generator':s,'before_native':True})
 rows=[];trs=[]
 for c in CASES:
  run_one(c);r=audit_fields(c);d=OUT/c['name'];q=transfer(c);g=read(d/'generation.json');H=histories(d/(g['name']+'T01.csv'));m=np.asarray(g['nodal_masses_g']);keys=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];ids=[int(re.match(r'NATIVE_SCOPE_NODES\s+(\d+)\s',k).group(1)) for k in keys][::6];N=np.column_stack([H[k] for k in keys]).reshape(len(H['time']),len(m),6);ke=.5*np.sum(m[np.asarray(ids)-1][None,:,None]*N[:,:,3:]**2,axis=(1,2))*.001;native=H['KINETIC ENERGY']*.001;peak=float(ke.max());error=float(abs(ke-native).max());tol=.02*peak+1e-7
  q['checks'].update(observable_peak_KE=peak>1e-6,known_mass_nodal_KE_matches_native=error<tol);q.update(physical_nodal_peak_KE_J=peak,native_KE_max_error_J=error,native_KE_tolerance_J=tol);q['pass']=all(q['checks'].values());dump(d/'source_predicted_transfer.json',q);rows.append(r);trs.append(q)
  print({'observable_case':c['name'],'transfer_checks':q['checks'],'KE_error_J':error},flush=True)
 dump(OUT/'native_review.json',{'created_utc':now(),'cases':rows,'transfer':trs,'old_case_reviews_preserved':True,'whole_impact_qualified':False})
 h=[]
 for c in CASES:
  d=OUT/c['name'];H=histories(d/(read(d/'generation.json')['name']+'T01.csv'));h.append(H)
 t=min(H['time'][-1] for H in h);kk=[float(np.interp(t,H['time'],H['KINETIC ENERGY']))*.001 for H in h];ratio=float(np.median(h[1]['TIME STEP'][1:])/np.median(h[0]['TIME STEP'][1:]));df=abs(kk[0]-kk[1]);tol=.002*max(kk)+1e-7;dump(OUT/'comparison_review.json',{'created_utc':now(),'common_time_ms':float(t),'energies_J':kk,'difference_J':df,'tolerance_J':tol,'actual_half_dt_ratio':ratio,'checks':{'temporal_energy':df<tol,'actual_half_dt':ratio<.6},'pass':df<tol and ratio<.6})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
