"""Audit saved solver states. Keep literal predeclared failures visible."""
from pathlib import Path
import argparse,csv,json,re,subprocess,time
import numpy as np
from run_aircraft_a02 import ROOT,CFG,OUT,RUNTIME,read,dump,sha,rel,now
from export_impact_i02a import parse_vtk
def numbers_after(s,title,count):
    tail=s[s.index(title)+len(title):]
    for line in tail.splitlines():
        words=line.split()
        if len(words)==count:
            try: return [float(x) for x in words]
            except ValueError: pass
    raise ValueError(title)
def audit_case(revision,case):
    cfg=read(CFG);a=cfg['acceptance'];d=OUT/revision/case['id'];n=read(d/'generation.json')['name'];mesh=read(OUT/revision/'solver_mesh.json')
    assert not (d/'audit.json').exists(),'audit output is immutable'
    listing=(d/(n+'_0000.out')).read_text(encoding='utf-8',errors='replace')
    native=numbers_after(listing,'TOTAL MASS AND MASS CENTER',4);iv=numbers_after(listing,'TOTAL INERTIA',6)
    nativeI=np.array([[iv[0],iv[3],iv[5]],[iv[3],iv[1],iv[4]],[iv[5],iv[4],iv[2]]])*1e-9
    ref=read(OUT/revision/'mapping_audit.json')['reference_A01'];M=ref['total_kg'];cgerr=float(np.linalg.norm(np.array(native[1:])*0.001-ref['CG_m']))
    Ierr=float(np.linalg.norm(nativeI-np.array(ref['inertia_CG_kg_m2']))/np.linalg.norm(ref['inertia_CG_kg_m2']))
    rows=list(csv.DictReader((d/(n+'T01.csv')).open(encoding='utf-8-sig')));T=np.array([float(r['time']) for r in rows]);V=np.array(case['velocity_m_s'])
    KE=np.array([float(r['KINETIC ENERGY'])*.001 for r in rows]);RE=np.array([float(r['ROTATION ENERGY'])*.001 for r in rows]);IE=np.array([float(r['INTERNAL ENERGY'])*.001 for r in rows]);EW=np.array([float(r['EXTERNAL WORK'])*.001 for r in rows]);HE=np.array([float(r['HOURGLASS ENERGY'])*.001 for r in rows]);AM=np.array([float(r['ADDED MASS']) for r in rows]);P=np.array([[float(r[k+'-MOMENTUM'])*.001 for k in 'XYZ'] for r in rows])
    initialKE=.5*M*float(V@V);initialP=M*V;E=KE+RE+IE+HE;drift=float(np.max(np.abs(E-E[0]-EW))/initialKE);pdrift=float(np.max(np.linalg.norm(P-P[0],axis=1))/np.linalg.norm(initialP))
    samples=[];statepaths=[];positions=[];velocities=[];displacements=[];times=[];nodeids=None;maxD=0.;maxV=0.;maxRel=0.;maxCoord=0.
    for animation in sorted(d.glob(n+'A*')):
        if not re.fullmatch(re.escape(n)+r'A\d{3}',animation.name): continue
        start=time.perf_counter();p=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(animation)],capture_output=True,text=True,encoding='utf-8',timeout=cfg['execution']['converter_timeout_s'])
        assert p.returncode==0,p.stderr;q=parse_vtk(p.stdout)
        ids=q['NODE_ID'].astype(int);x=q['points'].reshape(-1,3);disp=q['Displacement'].reshape(-1,3);vel=q['Velocity'].reshape(-1,3);tm=q['time']
        if nodeids is None: nodeids=ids
        assert np.array_equal(ids,nodeids) and np.array_equal(np.sort(ids),np.arange(1,len(mesh['nodes_m'])+1))
        derr=float(np.max(np.abs(disp-tm*V)));verr=float(np.max(np.abs(vel-V)));rerr=float(np.max(np.ptp(disp,axis=0)))
        # Native binary uses float32, ASCII VTK rounds coordinates to six significant digits.
        cerr=float(np.max(np.abs(x-np.array(mesh['nodes_m'])[ids-1]*1000-disp)))
        maxD=max(maxD,derr);maxV=max(maxV,verr);maxRel=max(maxRel,rerr);maxCoord=max(maxCoord,cerr)
        samples.append({'time_ms':tm,'nodes':len(ids),'maximum_translation_error_mm':derr,'maximum_velocity_error_mm_ms':verr,'maximum_relative_displacement_mm':rerr,'coordinate_serialization_identity_error_mm':cerr,'converter_seconds':time.perf_counter()-start})
        positions.append(x);velocities.append(vel);displacements.append(disp);times.append(tm);statepaths.append({'path':rel(animation),'sha256':sha(animation)})
    assert samples
    np.savez_compressed(d/'verified_states_SI.npz',time_s=np.array(times)*.001,node_ids=nodeids,positions_m=np.array(positions)*.001,velocity_m_s=np.array(velocities),displacement_m=np.array(displacements)*.001)
    engine=(d/'engine.log').read_text();starter=(d/'starter.log').read_text();warnings=int(re.findall(r'(\d+) WARNING\(S\)',starter)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',starter)[-1]);lastT=times[-1];e=cfg['execution'];generation=read(d/'generation.json')
    checks={
        'native_mass_matches_A01':abs(native[0]*.001-M)/M<a['mass_relative_error'],
        'native_CG_matches_strict_A01_tolerance':cgerr<a['CG_error_m'],
        'native_inertia_within_declared_one_percent':Ierr<a['input_lumped_inertia_relative_norm_error'],
        'initial_KE_matches_mass_and_velocity':abs(KE[0]-initialKE)/initialKE<a['initial_KE_relative_error'],
        'initial_momentum_matches_mass_and_velocity':float(np.linalg.norm(P[0]-initialP)/np.linalg.norm(initialP))<a['initial_momentum_relative_norm_error'],
        'global_energy_conserved':drift<a['energy_drift_relative'],
        'global_momentum_conserved':pdrift<a['momentum_drift_relative_norm'],
        'internal_energy_negligible':float(np.max(abs(IE)))/initialKE<a['internal_energy_to_initial_KE'],
        'rotation_energy_negligible':float(np.max(abs(RE)))/initialKE<a['rotation_energy_to_initial_KE'],
        'external_work_zero':bool(np.all(EW==0)),
        'hourglass_energy_zero':bool(np.all(HE==0)),
        'added_mass_below_literal_absolute_tolerance':float(np.max(abs(AM)))<a['added_mass_g'],
        'all_3228_nodes_exported':len(nodeids)==len(mesh['nodes_m']),
        'node_translation_matches_actual_timestamp':maxD<a['node_translation_error_mm'],
        'node_velocity_uniform':maxV<a['node_velocity_error_mm_per_ms'],
        'no_relative_deformation':maxRel<a['node_translation_error_mm'],
        'end_time_within_literal_absolute_tolerance':abs(lastT-e['end_ms'])<a['end_time_error_ms'],
        'engine_normal_termination':'NORMAL TERMINATION' in engine,
        'starter_zero_errors':errors==0,
        'starter_zero_warnings':warnings==0,
        'no_external_force_or_global_rigid_body':all(generation[k] for k in ['no_BCS','no_RBODY','no_contact','no_gravity','no_mass_scaling'])
    }
    checks={k:bool(v) for k,v in checks.items()}
    flightkeys=['initial_KE_matches_mass_and_velocity','initial_momentum_matches_mass_and_velocity','global_energy_conserved','global_momentum_conserved','internal_energy_negligible','rotation_energy_negligible','external_work_zero','hourglass_energy_zero','all_3228_nodes_exported','node_translation_matches_actual_timestamp','node_velocity_uniform','no_relative_deformation','engine_normal_termination','starter_zero_errors','no_external_force_or_global_rigid_body']
    result={'created_utc':now(),'case':case,'revision':revision,'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_literal_checks_pass':all(checks.values()),
        'whole_aircraft_uniform_translation_checks_pass':all(checks[k] for k in flightkeys),'native_mass_kg':native[0]*.001,'native_CG_m':(np.array(native[1:])*.001).tolist(),'native_CG_error_m':cgerr,'native_inertia_CG_kg_m2':nativeI.tolist(),'native_inertia_relative_norm_error':Ierr,
        'expected_KE_J':initialKE,'initial_KE_J':float(KE[0]),'initial_momentum_Ns':P[0].tolist(),'energy_drift_fraction_in_saved_history':drift,'momentum_drift_fraction_in_saved_history':pdrift,
        'maximum_internal_energy_J':float(np.max(abs(IE))),'maximum_rotation_energy_J':float(np.max(abs(RE))),'maximum_added_mass_g':float(np.max(abs(AM))),'maximum_added_mass_fraction':float(np.max(abs(AM))/(M*1000)),
        'actual_final_time_ms':lastT,'requested_final_time_ms':e['end_ms'],'history_final_time_ms':float(T[-1]),'history_samples':len(T),'state_samples':samples,'states':statepaths,
        'literal_failed_checks':[k for k,v in checks.items() if not v],'starter_warnings':warnings,'starter_errors':errors,
        'qualification':'Unforced translation only. No rotation, structural load, impact, crushing or fracture qualification; strict CG/added-mass/end-time criteria not silently relaxed.',
        'coordinate_serialization_maximum_identity_error_mm':maxCoord,
        'runtime':[read(d/(n+'.execution.json')) for n in ['starter.log','engine.log','converter.log']]}
    dump(d/'audit.json',result);return result
def main(revision):
    cfg=read(CFG);results=[]
    for case in cfg['execution']['cases']:
        d=OUT/revision/case['id']
        if (d/(read(d/'generation.json')['name']+'T01.csv')).exists():
            results.append(read(d/'audit.json') if (d/'audit.json').exists() else audit_case(revision,case))
    assert not (OUT/revision/'summary.json').exists()
    checks=read(OUT/revision/'mapping_audit.json')['checks'];allchecks={**{'mapping_'+k:v for k,v in checks.items()},**{r['case']['id']+'_'+k:v for r in results for k,v in r['checks'].items()}}
    summary={'created_utc':now(),'iteration':'AIRCRAFT-A02','revision':revision,'cases':results,'checks':allchecks,'checks_passed':sum(allchecks.values()),'checks_total':len(allchecks),'all_literal_checks_pass':all(allchecks.values()),
        'whole_aircraft_uniform_translation_checks_pass':len(results)==2 and all(r['whole_aircraft_uniform_translation_checks_pass'] and r['starter_warnings']==0 for r in results),
        'solver_jobs':len(results),'old_solver_reruns':0,'impact_qualified':False,'whole_aircraft_deformation_qualified':False,'whole_aircraft_mass_mapping_fully_qualified':False,'NIST_outcomes_used':False}
    dump(OUT/revision/'summary.json',summary);print(json.dumps({k:summary[k] for k in ['revision','checks_passed','checks_total','all_literal_checks_pass','whole_aircraft_uniform_translation_checks_pass']},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--revision',default='r1');args=ap.parse_args();main(args.revision)
