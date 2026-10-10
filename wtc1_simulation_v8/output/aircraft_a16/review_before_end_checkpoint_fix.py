"""A16 native scene balances and layer damage, preserving old A15 criteria."""
import argparse,re,struct,subprocess
import numpy as np
import review_aircraft_a15 as inherited
from run_aircraft_a16 import ROOT,OUT,CFG,RUNTIME,read,dump,rel,now,guard
from audit_aircraft_a05 import vtk

def binary_damage(p):
    b=p.read_bytes();magic,tm=struct.unpack('>if',b[:8]);assert magic==0x542c
    nn,nf,npart,nfun,nefun,nvec,nten,nsk=np.frombuffer(b,dtype='>i4',count=8,offset=291).tolist();off=323+nsk*12+nn*12+nf*16+nf+npart*54+nn*6
    labels=[b[off+i*81:off+(i+1)*81].decode('ascii').rstrip('\x00 ') for i in range(nfun+nefun)];off+=(nfun+nefun)*81+nn*nfun*4
    elem=np.frombuffer(b,dtype='>f4',count=nefun*nf,offset=off).reshape(nefun,nf);idx=[i for i,k in enumerate(labels[nfun:]) if k.startswith('DAMAGE')];D=elem[idx].astype(float);names=[labels[nfun+i] for i in idx]
    off+=nf*nefun*4+nvec*81+nvec*nn*12+nten*81+nten*nf*12+nf*4+nn*4+nn*4
    eid=np.frombuffer(b,dtype='>i4',count=nf,offset=off).astype(int);assert len(set(eid))==nf
    return tm,eid,D,names

def audit(case):
    guard();d=OUT/'r0'/case['id'];inherited.OUT=OUT;inherited.CFG=CFG;inherited.guard=guard
    r=read(d/'review.json') if (d/'review.json').exists() else inherited.audit(case)
    g=read(d/'generation.json');m=read(d/'mesh.json');n=g['name'];radome=set(eid for eid,pid in zip(m['aircraft_triangle_ids'],m['aircraft_triangle_part_ids']) if pid==21)
    assert radome;times=[];damage=[];ids0=None;selected=[];verification=[];full_failure=None;onset=None
    available=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));files=available+sorted(p for p in (d/'observer').glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))
    checkpoints={0,len(files)//2,len(files)-1}
    for i,file in enumerate(files):
        tm,eid,D,names=binary_damage(file)
        if times and abs(tm-times[-1])<1e-6:continue
        mask=np.array([e in radome for e in eid]);rr=eid[mask];z=D[:3,mask];assert len(rr)==len(radome) and D.shape[0]>=3
        assert np.isfinite(D).all() and np.min(D)>=-1e-6 and np.max(D)<=1.000001 and np.all(z[1]==0)
        if ids0 is None:ids0=rr
        else:assert np.array_equal(rr,ids0)
        if i in checkpoints:
            q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(file)],capture_output=True,text=True,check=True,timeout=120).stdout);qi={int(e):j for j,e in enumerate(q['ELEMENT_ID'])};ix=[qi[int(e)] for e in rr];keys=[k for k in q if 'DAMAGE' in k]
            assert len(keys)==len(names);assert np.allclose(z,np.stack([q[k][ix] for k in keys[:3]]),rtol=5e-6,atol=1e-6);verification.append({'file':rel(file),'time_ms':tm,'native_damage_vs_converter_pass':True})
        faces=z[[0,2]];onset=tm if onset is None and np.any(faces>0) else onset;full_failure=tm if full_failure is None and np.any(faces>=.999999) else full_failure
        selected.append({'time_ms':tm,'maximum_skin_damage':float(faces.max()),'skin_layers_with_damage':int(np.count_nonzero(faces>0)),'skin_layers_at_full_failure':int(np.count_nonzero(faces>=.999999)),'total_skin_layer_elements':int(faces.size),'damaged_area_fraction':'not an event probability; counts only'});times.append(tm);damage.append(z.astype(np.float32))
    monotone=bool(np.all(np.diff(np.array(damage),axis=0)>=-1e-6));assert monotone
    np.savez_compressed(d/'native_radome_damage.npz',time_s=np.array(times)*.001,element_ids=ids0,skin_core_skin_damage=np.array(damage),maximum_native_damage=np.array([q['maximum_skin_damage'] for q in selected]))
    ply_events=sorted(set((int(p),int(e)) for p,e in re.findall(r'FAILURE \(ORTHSTRAIN\) OF PLY ID\s+(\d+)\s*,SHELL ELEMENT NUMBER\s+(\d+)',(d/'engine.log').read_text(errors='replace'))));assert all(p in [41,43] and e in radome for p,e in ply_events)
    a={'created_utc':now(),'case':case,'first_saved_skin_damage_ms':onset,'first_saved_full_skin_failure_ms':full_failure,'native_damage_frames':len(times),'native_damage_maximum_history_monotone':monotone,'core_damage_zero':True,'whole_shell_erosion_absent':r['checks']['no_erosion'],'final_skin_counts':selected[-1],'native_logged_failed_plies':len(ply_events),'native_logged_ply_events':ply_events,'DAMA_one_equals_at_least_one_failed_point_not_all_ply_points':True,'raw_effective_stress_not_damaged_force_stress':True,'all_native_scalar_damage_read':True,'reader_validation':verification,'history':selected,'physical_fracture_energy_qualified':False,'topological_fragmentation':False,'physical_impact_qualified':False}
    dump(d/'damage_review.json',a);return r,a

def main():
    guard();assert not (OUT/'campaign_review.json').exists();rows=[];dam=[];rejected=[]
    cfg=read(CFG);assert all((OUT/'r0'/c['id']/'history_recovery.json').exists() or list((OUT/'r0'/c['id']).glob('retained_failure_*.json')) for c in cfg['execution']['cases'])
    for c in cfg['execution']['cases']:
        d=OUT/'r0'/c['id']
        if not (d/'history_recovery.json').exists():rejected.append({'case':c,'failure_files':[rel(p) for p in d.glob('retained_failure_*.json')]});continue
        if (d/'damage_review.json').exists():r,a=read(d/'review.json'),read(d/'damage_review.json')
        else:r,a=audit(c)
        rows.append(r);dam.append(a)
    baseline=np.load(ROOT/'wtc1_simulation_v8/output/aircraft_a15/r0/IMPACT_10_DT50/balance_history_SI.npz');comparisons=[]
    for r in rows:
        z=np.load(OUT/'r0'/r['case']['id']/'balance_history_SI.npz');tc=min(float(z['time_s'][-1]),float(baseline['time_s'][-1]));j=np.array([np.interp(tc,z['time_s'],z['contact_impulse_Ns'][:,i]) for i in range(3)]);b=np.array([np.interp(tc,baseline['time_s'],baseline['contact_impulse_Ns'][:,i]) for i in range(3)]);G=float(np.interp(tc,z['time_s'],z['generated_energy_J']));BG=float(np.interp(tc,baseline['time_s'],baseline['generated_energy_J']));comparisons.append({'case':r['case']['id'],'cached_baseline':'A15_IMPACT_10_DT50','common_time_ms':tc*1000,'impulse_difference_fraction':float(np.linalg.norm(j-b)/np.linalg.norm(b)),'generated_energy_difference_fraction':abs(G-BG)/BG,'parameter_sensitivity_not_convergence':True,'baseline_solver_rerun':False})
    req=['native_binary_CSV','normal_termination','requested_horizon_reached','original_connectivity','finite_native_states','all_boundary_supports_fixed','mass_matches_expected','independent_native_mass_matches','native_nodal_mass_unchanged','no_added_mass','no_erosion','no_external_work']
    s={'iteration':'AIRCRAFT-A16','created_utc':now(),'cases':rows,'damage':dam,'rejected_cases':rejected,'comparisons_with_cached_A15':comparisons,'integrity_only_pass':not rejected and len(rows)==2 and all(all(r['checks'][k] for k in req) for r in rows),'mechanical_maximum_history_gate_pass':read(OUT/'witness_review.json')['mechanical_gate_pass'],'all_declared_checks_pass':not rejected and len(rows)==2 and all(r['all_declared_checks_pass'] for r in rows),'physical_impact_qualified':False,'physical_fracture_energy_qualified':False,'topological_fragmentation':False,'whole_aircraft_exploratory_damage_impacts_executed':len(rows),'NIST_outcomes_used_as_target':False,'old_solver_reruns':0,'old_ORTHENERG_and_A11_A15_failures_retained':True,'seconds_impact_calculated':False}
    dump(OUT/'campaign_review.json',s);print({k:v for k,v in s.items() if k not in ['cases','damage']},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case');a=p.parse_args();audit(next(c for c in read(CFG)['execution']['cases'] if c['id']==a.case)) if a.case else main()
