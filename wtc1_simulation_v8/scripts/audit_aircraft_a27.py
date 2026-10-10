"""Audit native composite controls, preserving unsuccessful references and prior files."""
from run_aircraft_a27 import *
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import subprocess

def preserve():
    guard();dest=OUT/'preservation_verification.json';assert not dest.exists()
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for q in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(q)]={'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)}
    rows=list(pins.values());dump(OUT/'preservation_before.json',{'created_utc':now(),'files':rows,'archives_rescanned':False});start=time.perf_counter()
    for i,r in enumerate(rows):
        p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
        if (i+1)%3000==0:print({'old_files':i+1,'of':len(rows)},flush=True)
    dump(dest,{'created_utc':now(),'pass':True,'files':len(rows),'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-start,'sources_not_rescanned':True});print({'preservation_A27':True,'files':len(rows)},flush=True)

def review():
    guard();dest=OUT/'composite_qualification_review.json';assert not dest.exists()
    rows=[{'revision':rev,**r} for rev in ['w1','w2','w3'] for r in read(OUT/f'native_case_summary_{rev}.json')['cases']];assert len(rows)==22
    h={k:v for k,v in np.load(OUT/'w3/FREE_ROTATION_Y_N12/histories_SI.npz').items()};h2={k:v for k,v in np.load(OUT/'w3/FREE_ROTATION_Y_N12_HALF/histories_SI.npz').items()};mask=(h['time_ms']>=h2['time_ms'][0])&(h['time_ms']<=h2['time_ms'][-1]);T=h['time_ms'][mask]
    ld=float(np.linalg.norm(h['physical_L_kg_m2_s'][mask]-np.column_stack([np.interp(T,h2['time_ms'],h2['physical_L_kg_m2_s'][:,a]) for a in range(3)]),axis=1).max());ed=float(abs(h['total_J'][mask]-np.interp(T,h2['time_ms'],h2['total_J'])).max());ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));dt={'actual_dt_ratio':ratio,'physical_L_difference_kg_m2_s':ld,'energy_difference_J':ed,'checks':{'actually_shorter':ratio<.6,'L_converges':bool(ld<.002*np.linalg.norm(h['physical_L_kg_m2_s'][0])+1e-9),'energy_converges':bool(ed<.002*h['total_J'][0]+1e-7)}}
    mesh=[]
    for motion in ['MEMBRANE','BENDING']:
        a=read(OUT/'w3'/f'{motion}_N6/review.json');b=read(OUT/'w3'/f'{motion}_N12/review.json');diff=abs(a['native_elastic_comparison_J']-b['native_elastic_comparison_J'])/b['native_elastic_comparison_J'];mesh.append({'motion':motion,'difference_fraction':diff,'pass':diff<.05,'N6':a,'N12':b})
    quad=[]
    for motion in ['MEMBRANE','BENDING']:
        a=read(OUT/'w2'/f'{motion}_N12/review.json');b=read(OUT/'w3'/f'{motion}_N12/review.json');diff=abs(a['native_elastic_comparison_J']-b['native_elastic_comparison_J'])/b['native_elastic_comparison_J'];quad.append({'motion':motion,'difference_fraction':diff,'previous_spatial_threshold_comparison_pass':diff<.05,'qualification':'diagnostic sensitivity; no originally declared standalone quadrature-pass threshold added','layers':[3,9],'native_J':[a['native_elastic_comparison_J'],b['native_elastic_comparison_J']]})
    samples=[];stress=[];layers=[]
    for rev in ['w1','w2','w3']:
        cfg=read(ROOT/('wtc1_simulation_v8/data/aircraft_a27_regular_layers.json' if rev=='w1' else f'wtc1_simulation_v8/data/aircraft_a27_plane_{rev}.json'));nl=cfg.get('thickness_layers',3)
        for d in sorted((OUT/rev).iterdir()):
            g=read(d/'generation.json');X=np.asarray(g['nodes_mm']);n=g['name'];s=(d/(n+'_0000.out')).read_text();pos=[float(z.replace('D','E')) for z in re.findall(r'POSITION  \(\[-0\.5,\+0\.5\]\).*?=\s*([+\-0-9.E]+)',s)];exp=(np.arange(nl)+.5)/nl-.5;assert len(pos)==nl
            checks={'positions':bool(np.allclose(pos,exp,atol=2e-11,rtol=0)),'zero_warnings':read(d/'starter_gate.json')['pass'],'known_mass':abs(g['known_mass_g']-.0915)<1e-10};layers.append({'revision':rev,'case':d.name,'positions':pos,'expected':exp.tolist(),'checks':checks,'pass':all(checks.values())})
            native=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));assert native
            for p in sorted(set([native[0],native[len(native)//2],native[-1]])):
                ad=OUT/'native_field_audit'/rev/d.name;ad.mkdir(parents=True,exist_ok=True);v=ad/(p.name+'.vtk');assert not v.exists();res=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120);v.write_text(res.stdout,encoding='utf-8');q=vtk(v.read_text(encoding='utf-8'));order=np.argsort(q['NODE_ID']);pts=q['points'].reshape(-1,3)[order];disp=q['Displacement'].reshape(-1,3)[order];vel=q['Velocity'].reshape(-1,3)[order];bound=printed_bound(pts)+printed_bound(disp)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(pts),abs(disp),abs(X)])+1e-8
                checks={'ids':bool(np.array_equal(q['NODE_ID'][order],np.arange(1,len(X)+1))),'finite':bool(np.isfinite(pts).all() and np.isfinite(disp).all() and np.isfinite(vel).all()),'identity_with_printing_bound':bool(np.all(abs(pts-X-disp)<=bound)),'no_eroded_elements':bool(np.all(q['EROSION_STATUS']==1))};samples.append({'revision':rev,'case':d.name,'time_ms':q['time'],'native':rel(p),'native_sha256':streamsha(p),'vtk':rel(v),'vtk_sha256':streamsha(v),'checks':checks,'pass':all(checks.values())})
                if p==native[-1] and d.name=='MEMBRANE_N12':
                    S=q['3DELEM_Stress'].reshape(-1,3,3);stress.append({'revision':rev,'time_ms':q['time'],'vtk':rel(v),'native_global_stress_MPa_mean':S.mean(axis=0).tolist(),'native_global_stress_MPa_min':S.min(axis=0).tolist(),'native_global_stress_MPa_max':S.max(axis=0).tolist(),'qualification':'actual native field; not an independently established complete 3D constitutive matrix'})
    dump(OUT/'native_fields_review.json',{'created_utc':now(),'samples':samples,'pass':all(r['pass'] for r in samples),'solver_thresholds_unchanged':True,'native_reruns':0});dump(OUT/'layer_readback_review.json',{'created_utc':now(),'cases':layers,'pass':all(r['pass'] for r in layers)})
    old=read(OUT/'w1/MEMBRANE_N12/review.json');new=read(OUT/'w2/MEMBRANE_N12/review.json');expected_extra=.5*10000*.00025**2*50*.001
    dump(OUT/'constitutive_observation.json',{'created_utc':now(),'native_stresses':stress,'transverse_loading_diagnostic':{'old_IE_J':old['native_elastic_comparison_J'],'new_IE_J':new['native_elastic_comparison_J'],'difference_J':old['native_elastic_comparison_J']-new['native_elastic_comparison_J'],'candidate_independent_E33_extra_J':expected_extra,'reference_plane_J':old['elastic_reference_J'],'original_failed_reference_preserved':True,'no_old_review_changed':True},'contradiction':'LAW25 theory gives a transverse-Poisson-coupled 3D compliance matrix; actual TYPE22 prescribed membrane shows sigma_z approximately E33*epsilon_z, while plane stresses approximately match the plane constitutive relation. No complete 3D material-equivalence claim. Plane controls are explicitly different boundary conditions.','bending_quadrature':quad,'midpoint_second_moment_is_only_one_error_component':True,'native_material_fields_unchanged':True,'historical_strength_and_fracture_qualified':False})
    actual=ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad';law=parent()['/MAT/LAW25/4'];dump(OUT/'material_source_addendum.json',{'created_utc':now(),'actual_parent_deck':rel(actual),'sha256':streamsha(actual),'bytes':actual.stat().st_size,'native_material_card':law,'material_fields_changed':False,'mass_from_physical_volume_and_source_density_g':.0915,'not_historical_fracture_material':True})
    candidate=[r for r in rows if r['revision']=='w3'];checks={'candidate_all_native_gates':all(r['pass'] for r in candidate),'time_refinement':all(dt['checks'].values()),'spatial_mesh':all(r['pass'] for r in mesh),'native_fields':all(r['pass'] for r in samples),'layer_readback':all(r['pass'] for r in layers)}
    dump(dest,{'created_utc':now(),'cases':rows,'candidate_revision':'w3','refinement':dt,'mesh':mesh,'quadrature_sensitivity':quad,'checks':checks,'composite_prototype_pass':all(checks.values()),'free_and_membrane_scope_pass':all(r['pass'] for r in candidate if not r['case'].startswith('BENDING')),'bending_scope_pass':all(r['pass'] for r in candidate if r['case'].startswith('BENDING')),'original_Starter674_preserved':True,'original_Engine_not_run':True,'whole_insertion_ready':False,'objective1_complete':False});print({'A27_review':checks,'composite_scope_pass':all(checks.values())},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','review']);globals()[p.parse_args().action]()
