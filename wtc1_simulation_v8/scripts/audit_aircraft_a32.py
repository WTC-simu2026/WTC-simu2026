"""Audit cached A32 native outputs; never repeat a solver or change failed gates."""
from run_aircraft_a32 import *
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import subprocess,time

def preserve():
    guard();dest=OUT/'preservation_verification.json';assert not dest.exists()
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json',ROOT/'outputs/github_publication/updates_2026-10-11_aircraft_a30_a31/final_remote_verification.json']:
        pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    rows=list(pins.values());dump(OUT/'preservation_before.json',{'created_utc':now(),'files':rows,'archives_rescanned':False});start=time.perf_counter()
    for i,r in enumerate(rows):
        p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
        if (i+1)%3000==0:print({'old_files':i+1,'of':len(rows)},flush=True)
    dump(dest,{'created_utc':now(),'pass':True,'files':len(rows),'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-start,'sources_not_rescanned':True});print({'A32_preserved':len(rows)},flush=True)

def review():
    guard();dest=OUT/'composite_qualification_review.json';assert not dest.exists()
    rows=[{'revision':d.parent.name,**read(d/'review.json')} for d in sorted(OUT.glob('w*/*')) if (d/'review.json').exists()];assert len(rows)==30
    samples=[];cards=[];frames=[];stress=[]
    for d in sorted(OUT.glob('w*/*')):
        if not (d/'review.json').exists():continue
        g=read(d/'generation.json');rev=d.parent.name;n=g['name'];X=np.asarray(g['nodes_mm']);text=(d/(n+'_0000.rad')).read_text(encoding='utf-8');expected='\n'.join(source_skin.law12_card())+'\n'
        checks={'source_LAW12_card':expected in text,'physical_mass':abs(g['known_mass_g']-.0915)<1e-10,'one_physical_thickness_cell':g['geometric_Z_elements']==1,'no_mass_scaling_card':'/DT/NODA/CST' not in text and '/ADMAS' not in text};cards.append({'revision':rev,'case':d.name,'checks':checks,'pass':all(checks.values())})
        frames.append({'revision':rev,'case':d.name,**read(d/'native_frame_gate.json')})
        native=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));assert len(native)>=3
        for p in sorted(set([native[0],native[len(native)//2],native[-1]])):
            ad=OUT/'native_field_audit'/rev/d.name;ad.mkdir(parents=True,exist_ok=True);v=ad/(p.name+'.vtk');assert not v.exists()
            res=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120);v.write_text(res.stdout,encoding='utf-8');q=vtk(res.stdout);order=np.argsort(q['NODE_ID']);pts=q['points'].reshape(-1,3)[order];disp=q['Displacement'].reshape(-1,3)[order];vel=q['Velocity'].reshape(-1,3)[order]
            bound=printed_bound(pts)+printed_bound(disp)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(pts),abs(disp),abs(X)])+1e-8
            checks={'ids':bool(np.array_equal(q['NODE_ID'][order],np.arange(1,len(X)+1))),'finite':bool(np.isfinite(pts).all() and np.isfinite(disp).all() and np.isfinite(vel).all()),'identity_with_printing_bound':bool(np.all(abs(pts-X-disp)<=bound)),'no_eroded_elements':bool(np.all(q['EROSION_STATUS']==1))};samples.append({'revision':rev,'case':d.name,'time_ms':q['time'],'native':rel(p),'native_sha256':streamsha(p),'vtk':rel(v),'vtk_sha256':streamsha(v),'checks':checks,'pass':all(checks.values())})
            if p==native[-1] and d.name.startswith(('PATCH_','CONSTRAINED_BENDING')):
                s=q.get('3DELEM_Stress');stress.append({'revision':rev,'case':d.name,'time_ms':q['time'],'native_stress_available':s is not None,'native_stress_MPa_mean':np.asarray(s).reshape(-1,3,3).mean(axis=0).tolist() if s is not None else None,'diagnostic_only':True,'native_enhanced_strain_not_directly_observed':True})
    dump(OUT/'native_fields_review.json',{'created_utc':now(),'samples':samples,'pass':all(r['pass'] for r in samples),'old_solvers_rerun':0,'printing_bound_is_not_physical_tolerance':True})
    dump(OUT/'material_readback_review.json',{'created_utc':now(),'cases':cards,'pass':all(r['pass'] for r in cards),'source_cards_not_modified':True})
    dump(OUT/'native_frame_review.json',{'created_utc':now(),'cases':frames,'pass':all(r['pass'] for r in frames),'TYPE21_reader_failure_retained':True})
    dump(OUT/'native_stress_observation.json',{'created_utc':now(),'cases':stress,'no_post_run_acceptance_criterion':True})
    dt=[];mesh=[]
    for rev in ['w0','w1']:
        h=dict(np.load(OUT/rev/'FREE_ROTATION_Y_N12/histories_SI.npz'));h2=dict(np.load(OUT/rev/'FREE_ROTATION_Y_N12_HALF/histories_SI.npz'));mask=(h['time_ms']>=h2['time_ms'][0])&(h['time_ms']<=h2['time_ms'][-1]);T=h['time_ms'][mask]
        ld=float(np.linalg.norm(h['physical_L_kg_m2_s'][mask]-np.column_stack([np.interp(T,h2['time_ms'],h2['physical_L_kg_m2_s'][:,a]) for a in range(3)]),axis=1).max());ed=float(abs(h['total_J'][mask]-np.interp(T,h2['time_ms'],h2['total_J'])).max());ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));checks={'actually_shorter':ratio<.6,'L_converges':ld<.002*np.linalg.norm(h['physical_L_kg_m2_s'][0])+1e-9,'energy_converges':ed<.002*h['total_J'][0]+1e-7};dt.append({'revision':rev,'actual_dt_ratio':ratio,'physical_L_difference_kg_m2_s':ld,'energy_difference_J':ed,'checks':{k:bool(v) for k,v in checks.items()},'pass':all(checks.values())})
        for motion in ['MEMBRANE','CONSTRAINED_BENDING']:
            a=read(OUT/rev/f'{motion}_N6/review.json');b=read(OUT/rev/f'{motion}_N12/review.json');ea=a['native_IE_J']+a['native_HE_J'];eb=b['native_IE_J']+b['native_HE_J'];diff=abs(ea-eb)/eb;mesh.append({'revision':rev,'motion':motion,'native_elastic_J':[ea,eb],'difference_fraction':diff,'pass':diff<.05,'original_individual_gates':[a['pass'],b['pass']]})
    C=constitutive();failed=[{'revision':r['revision'],'case':r['case'],'checks':[k for k,v in r['checks'].items() if not v]} for r in rows if not r['pass']]
    checks={'all_original_native_gates':all(r['pass'] for r in rows),'time_refinement':all(r['pass'] for r in dt),'spatial_refinement':all(r['pass'] for r in mesh),'native_fields':all(r['pass'] for r in samples),'native_frame':all(r['pass'] for r in frames),'material_readback':all(r['pass'] for r in cards),'positive_symmetric_tensor':bool(np.linalg.eigvalsh(C).min()>0 and np.allclose(C,C.T))}
    dump(dest,{'created_utc':now(),'cases':rows,'refinement':dt,'mesh':mesh,'checks':checks,'prototype_pass':all(checks.values()),'failed_controls':failed,'free_scope_pass':all(r['pass'] for r in rows if r['case'].startswith('FREE')),'affine_scope_pass':all(r['pass'] for r in rows if r['case'].startswith('PATCH_')),'membrane_scope_pass':all(r['pass'] for r in rows if r['case'].startswith('MEMBRANE')),'bending_scope_pass':False,'whole_insertion_ready':False,'new_whole_impact_executed':False,'old_native_solver_reruns':0,'objective1_complete':False})
    print({'A32_review':checks,'native_samples':len(samples),'failed_controls':failed},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','review']);globals()[p.parse_args().action]()
