"""Metal solid-shell qualification scope and immutable prior-file preservation."""
from run_aircraft_a26 import *
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import subprocess

def preserve():
    guard();dest=OUT/'preservation_verification.json';assert not dest.exists();pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for q in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(q)]={'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)}
    rows=list(pins.values());dump(OUT/'preservation_before.json',{'created_utc':now(),'files':rows,'archives_rescanned':False});start=time.perf_counter()
    for i,r in enumerate(rows):
        p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
        if (i+1)%3000==0:print({'old_files':i+1,'of':len(rows)},flush=True)
    dump(dest,{'created_utc':now(),'pass':True,'files':len(rows),'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-start,'sources_not_rescanned':True});print({'preservation_A26':True,'files':len(rows)},flush=True)

def review():
    guard();dest=OUT/'metal_qualification_review.json';assert not dest.exists();rows=read(OUT/'native_case_summary_w2.json')['cases'];assert len(rows)==9;g=read(OUT/'w2/FREE_ROTATION_Y_N12/generation.json');h={k:v for k,v in np.load(OUT/'w2/FREE_ROTATION_Y_N12/histories_SI.npz').items()};h2={k:v for k,v in np.load(OUT/'w2/FREE_ROTATION_Y_N12_HALF/histories_SI.npz').items()};mask=(h['time_ms']>=h2['time_ms'][0])&(h['time_ms']<=h2['time_ms'][-1]);T=h['time_ms'][mask];ld=float(np.linalg.norm(h['physical_L_kg_m2_s'][mask]-np.column_stack([np.interp(T,h2['time_ms'],h2['physical_L_kg_m2_s'][:,a]) for a in range(3)]),axis=1).max());ed=float(abs(h['total_J'][mask]-np.interp(T,h2['time_ms'],h2['total_J'])).max());ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));dt={'actual_dt_ratio':ratio,'physical_L_difference_kg_m2_s':ld,'energy_difference_J':ed,'checks':{'actually_shorter':ratio<.6,'L_converges':bool(ld<.002*np.linalg.norm(h['physical_L_kg_m2_s'][0])+1e-9),'energy_converges':bool(ed<.002*h['total_J'][0]+1e-7)}}
    mesh=[]
    for motion in ['MEMBRANE','BENDING']:
        a=read(OUT/'w2'/f'{motion}_N6/review.json');b=read(OUT/'w2'/f'{motion}_N12/review.json');diff=abs(a['native_elastic_comparison_J']-b['native_elastic_comparison_J'])/b['native_elastic_comparison_J'];mesh.append({'motion':motion,'difference_fraction':diff,'pass':diff<.05,'N6':a,'N12':b})
    samples=[]
    for revision in ['w0','w2']:
        for d in sorted((OUT/revision).iterdir()):
            g=read(d/'generation.json');X=np.asarray(g['nodes_mm']);n=g['name'];native=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));assert native
            for p in sorted(set([native[0],native[len(native)//2],native[-1]])):
                ad=OUT/'native_field_audit'/revision/d.name;ad.mkdir(parents=True,exist_ok=True);v=ad/(p.name+'.vtk');assert not v.exists();res=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120);v.write_text(res.stdout,encoding='utf-8');q=vtk(v.read_text(encoding='utf-8'));order=np.argsort(q['NODE_ID']);pts=q['points'].reshape(-1,3)[order];disp=q['Displacement'].reshape(-1,3)[order];vel=q['Velocity'].reshape(-1,3)[order];bound=printed_bound(pts)+printed_bound(disp)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(pts),abs(disp),abs(X)])+1e-8;checks={'ids':bool(np.array_equal(q['NODE_ID'][order],np.arange(1,len(X)+1))),'finite':bool(np.isfinite(pts).all() and np.isfinite(disp).all() and np.isfinite(vel).all()),'identity_with_printing_bound':bool(np.all(abs(pts-X-disp)<=bound)),'no_eroded_elements':bool(np.all(q['EROSION_STATUS']==1))};samples.append({'revision':revision,'case':d.name,'time_ms':q['time'],'native':rel(p),'native_sha256':streamsha(p),'vtk':rel(v),'vtk_sha256':streamsha(v),'checks':checks,'pass':all(checks.values())})
    dump(OUT/'native_fields_review.json',{'created_utc':now(),'samples':samples,'pass':all(r['pass'] for r in samples),'solver_thresholds_unchanged':True,'native_reruns':0})
    old=read(OUT/'native_case_summary.json')['cases'];checks={'all_HA8_native_gates':all(r['pass'] for r in rows),'time_refinement':all(dt['checks'].values()),'elastic_mesh':all(r['pass'] for r in mesh),'native_fields':all(r['pass'] for r in samples)};dump(dest,{'created_utc':now(),'native_HA8_cases':rows,'DKT_cases_preserved':old,'DKT_original_failed_gate_count':sum(not r['pass'] for r in old),'w1_Starter_warning_retained':True,'w1_Engine_not_run':True,'refinement':dt,'mesh':mesh,'checks':checks,'metal_prototype_pass':all(checks.values()),'mass_geometry_material_same_between_DKT_and_HA8':True,'nodal_lumping_differs_and_is_explicit':True,'composite_skin_not_qualified':True,'whole_insertion_ready':False,'objective1_complete':False});print({'A26_metal_qualification':checks,'pass':all(checks.values())},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','review']);globals()[p.parse_args().action]()
