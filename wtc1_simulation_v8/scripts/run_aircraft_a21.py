"""A21: preserve A20, localize its missing energy, then declare targeted controls."""
from run_aircraft_a20 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,histories,vtk,fast
import argparse,json,re,shutil,subprocess,traceback
from pathlib import Path
import numpy as np

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a21'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a21_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a20'
SOURCE=PREV/'r0/CORE3D_TIED_20'

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A20'
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    c={'iteration':'AIRCRAFT-A21','declared_utc':now(),'seed':1102046,'random_draws':0,'source':rel(SOURCE),
        'goal':{'physical_target_s':10,'current_whole_duration_s':.0200001220703125,'complete':False},
        'scope':'Diagnose cached A20 local-energy failure before changing mechanics. Independently test transfer of root inertia and impulse; prepare finite metal/facade fracture from declared material assumptions and primary sources. No fitting to known damage.',
        'cached_analysis':{'all_history_rows':True,'time_windows_ms':[[0,10],[10,20.0002]],'selection':'First and worst gate violations, plus phase boundaries, only for numerical diagnosis. Not selection by observed historical damage.',
            'energy_ledger':'Native global KE,RKE,IE,HG,springs,contact once; compare summed distinct part IE/HE/PW and cumulative external/support momentum. Do not add any inferred RKE.',
            'part_energy_sum_relative_tolerance':1e-5,'part_energy_sum_absolute_J':.1,
            'skin_negative_energy':'All retained shell states. Locate minimum and compare to deformation, damage, erosion and own original geometry; no new whole solve.'},
        'acceptance':read(ROOT/'wtc1_simulation_v8/data/aircraft_a20_whole_declaration.json')['acceptance'],
        'next_controls':'Separate immutable declaration after cached diagnosis; local witnesses before fresh intact coupled impact. Reuse passing A20 controls without rerun.',
        'no_density_material_mass_ADMAS_fit':True,'no_mass_scaling':True,'NIST_damage_fitted':False,'old_failed_gates_retained':True,
        'sources_read_only':True,'old_solver_reruns':0,'physical_impact_qualified':False,'no_seconds_extension_of_invalid_A20':True}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_A21_analysis_or_native_execution':True})
    src=[]
    for p in [SOURCE/'review.json',SOURCE/'balance_history_SI.npz',SOURCE/'mesh.json',SOURCE/'generation.json',SOURCE/'history_recovery.json',SOURCE/'constraint_mass_listing/constraint_mass_interpretation.json']:
        src.append({'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':src,'no_archive_scan':True,'cached_A20_only':True})
    print({'declared':'AIRCRAFT-A21','old_files_pinned':len(pins)},flush=True)

def cached():
    guard();assert not (OUT/'cached_energy_localization.json').exists();H=histories(SOURCE/'A20_CORE3D_TIED_20T01.csv');Ho=histories(SOURCE/'observer/A20_CORE3D_TIED_20T02_recovered.csv')
    def series(k):return np.r_[H[k],Ho[k][0]]
    T=series('time');cols={k:series(k) for k in H};a=read(CFG)['acceptance'];terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(cols[k] for k in terms)*.001;R=E-E[0]-cols['EXTERNAL WORK']*.001;G=sum(cols[k] for k in terms if k!='KINETIC ENERGY')*.001
    active=G>a['local_energy_comparison_minimum_J'];excess=abs(R)-a['local_energy_residual_generated_energy_fraction']*G-a['CSV_KE_precision_allowance_J'];bad=active&(excess>0)
    iekeys=[k for k in H if k.strip().endswith(' IE')];hekeys=[k for k in H if k.strip().endswith(' HE')];pwkeys=[k for k in H if k.strip().endswith(' PW')];partIE=sum(cols[k] for k in iekeys)*.001;partHE=sum(cols[k] for k in hekeys)*.001;partPW=sum(cols[k] for k in pwkeys)*.001
    groups={'core':lambda k:k.startswith('RADOME_CORE_FACET_'),'skins':lambda k:k.startswith(('RADOME_LOWER_FACET_','RADOME_UPPER_FACET_')),'cohesive':lambda k:k.startswith('RADOME_EDGE_COHESIVE'),'facade':lambda k:k.startswith('FACADE_')}
    ledger={label:{channel:sum((cols[k] for k in keys if predicate(k)),np.zeros(len(T)))*.001 for channel,keys in [('IE',iekeys),('HE',hekeys),('PW',pwkeys)]} for label,predicate in groups.items()}
    ledger['other_aircraft']={channel:sum((cols[k] for k in keys if not any(p(k) for p in groups.values())),np.zeros(len(T)))*.001 for channel,keys in [('IE',iekeys),('HE',hekeys),('PW',pwkeys)]}
    indices={0,len(T)-1,int(np.argmax(excess)),int(np.argmax(abs(R))),int(np.argmin(abs(T-10)))}
    if bad.any():indices.add(int(np.flatnonzero(bad)[0]))
    if active.any():indices.add(int(np.flatnonzero(active)[np.argmax(abs(R[active])/G[active])]))
    samples=[]
    for i in sorted(indices):samples.append({'time_ms':float(T[i]),'residual_J':float(R[i]),'generated_energy_J':float(G[i]),'gate_excess_J':float(excess[i]),'failed':bool(bad[i]),
        'native_terms_J':{k:float(cols[k][i])*.001 for k in terms},'part_sum_IE_J':float(partIE[i]),'native_IE_J':float(cols['INTERNAL ENERGY'][i])*.001,
        'groups':{label:{ch:float(v[i]) for ch,v in channels.items()} for label,channels in ledger.items()}})
    windows=[]
    for lo,hi in read(CFG)['cached_analysis']['time_windows_ms']:
        mask=(T>=lo)&(T<=hi);indices2=np.flatnonzero(mask);first,last=indices2[0],indices2[-1]
        windows.append({'window_ms':[lo,hi],'failed_rows':int(bad[mask].sum()),'first_failure_ms':float(T[np.flatnonzero(mask&bad)[0]]) if (mask&bad).any() else None,
            'maximum_gate_excess_J':float(excess[mask].max()),'delta_residual_J':float(R[last]-R[first]),'delta_generated_energy_J':float(G[last]-G[first])})
    err=partIE-cols['INTERNAL ENERGY']*.001;tol=read(CFG)['cached_analysis']['part_energy_sum_absolute_J']+read(CFG)['cached_analysis']['part_energy_sum_relative_tolerance']*abs(cols['INTERNAL ENERGY']*.001)
    r={'created_utc':now(),'history_rows':len(T),'part_IE_channels':len(iekeys),'part_HE_channels':len(hekeys),'part_PW_channels':len(pwkeys),'part_titles':iekeys,
        'maximum_native_part_IE_sum_error_J':float(abs(err).max()),'native_part_IE_sum_pass':bool(np.all(abs(err)<=tol)),
        'local_energy_failed_rows':int(bad.sum()),'samples':samples,'windows':windows,'specific_cause_identified':False,'native_terms_not_modified':True,'inferred_RKE_added':False,'old_solver_reruns':0,'physical_impact_qualified':False}
    dump(OUT/'cached_energy_localization.json',r);np.savez_compressed(OUT/'cached_energy_ledger_SI.npz',time_ms=T,residual_J=R,generated_energy_J=G,gate_excess_J=excess,part_IE_sum_J=partIE,part_HE_sum_J=partHE,part_PW_sum_J=partPW,**{f'{label}_{ch}_J':x for label,z in ledger.items() for ch,x in z.items()})
    print({k:r[k] for k in ['history_rows','part_IE_channels','maximum_native_part_IE_sum_error_J','native_part_IE_sum_pass','local_energy_failed_rows','windows']},flush=True);print({'samples':samples},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','cached']);globals()[p.parse_args().action]()
