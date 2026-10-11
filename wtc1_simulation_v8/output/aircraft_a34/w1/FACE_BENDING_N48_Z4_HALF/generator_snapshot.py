"""Bounded refinement of the observed free-edge defect; installed binary only."""
import run_aircraft_a33 as previous_skin
from run_aircraft_a33 import *
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a34'
PREV=previous_skin.OUT
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a34_predeclaration.json'
CASES=['FREE_ROTATION_Y_N48_Z4','FACE_BENDING_N48_Z4','FACE_BENDING_N48_Z8','FACE_BENDING_N48_Z4_HALF']

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A33';assert read(PREV/'publication_verification.json')['pass'];cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A33'
    assert read(ROOT/'outputs/github_publication/updates_2026-10-11_aircraft_a32_a33/final_remote_verification.json')['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c=read(previous_skin.CFG);c.update(iteration='AIRCRAFT-A34',declared_utc=now(),seed=1102059,cases=CASES,parent_configuration=rel(previous_skin.CFG),parent_configuration_sha256=streamsha(previous_skin.CFG),negative_control=None,
       purpose='TheA33largestdisplacementerrorsoccuronfreeedges. RefineXY24to48andphysicalZ4to8atunchangedgeometry,tensor,mass andoriginalfieldthreshold. Evaluateindependentreferencefielduncertaintyfromcachedrefinements before nativecontrols. This cannot prove whole10s feasibility.',
       inherited_failed_A33_gates_preserved=True,software_installation_or_compilation=False,software_build_permission_not_assumed=True)
    c['geometry'].update(XY=[48],physical_Z_cells=[4,8]);c['acceptance']['scope']='Allfourdeclarednativecases,independentcachedreferencefieldchecks and XY/Z/time comparisons; no postrunthresholdrelaxation';c['execution'].update(estimated_minutes=[3,15]);c['reference']['field_uncertainty_protocol']='Atmatchingnativephysicalinteriornodes,comparecachedN192Z8vsZ16andN96Z8vsN192Z8; sametolerance2%ofreferenceinteriorrelaxation+2e-6mm, diagnosticdoesnotrewriteA33.'
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_reference_analysis_and_native':True})
    files=[previous_skin.CFG,Path(previous_skin.__file__),PREV/'publication_verification.json',PREV/'interior_error_location_diagnostic.json',REFERENCE,ROOT/'wtc1_simulation_v8/output/aircraft_a32/surface_reference_extension/N192_Z8_EXACT_FACE.json',ROOT/'wtc1_simulation_v8/output/aircraft_a32/surface_reference_refinement/N96_Z8_EXACT_FACE.json']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in files],'source_archives_rescanned':False});print({'A34_declared':True,'cases':len(CASES),'CPU_minutes':[3,15],'software_modifications':False},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def cached_reference_field_check():
    guard();rows=[]
    refs={key:np.asarray(read(p)['displacements_mm']).reshape(nz+1,n+1,n+1,3) for key,p,n,nz in [('fine',REFERENCE,192,16),('Z8',ROOT/'wtc1_simulation_v8/output/aircraft_a32/surface_reference_extension/N192_Z8_EXACT_FACE.json',192,8),('XY96',ROOT/'wtc1_simulation_v8/output/aircraft_a32/surface_reference_refinement/N96_Z8_EXACT_FACE.json',96,8)]}
    for z in [4,8]:
        X,*_=brick_grid([48,48,z],[-5,-5,-.25],[5,5,.25]);ix=np.rint((X[:,0]+5)*192/10).astype(int);iy=np.rint((X[:,1]+5)*192/10).astype(int);iz=np.rint((X[:,2]+.25)*16/.5).astype(int);fine=refs['fine'][iz,iy,ix];z8=refs['Z8'][iz//2,iy,ix];xy96=refs['XY96'][iz//2,iy//2,ix//2];free=np.flatnonzero(abs(X[:,2])<.25);warp=float(abs(fine[free]-field(X,True)[free]).max());tol=.02*warp+2e-6;dz=float(abs(fine[free]-z8[free]).max());dxy=float(abs(z8[free]-xy96[free]).max());rows.append({'physical_Z_cells':z,'reference_relaxation_mm':warp,'tolerance_mm':tol,'Z8_to16_field_change_mm':dz,'XY96_to192_atZ8_field_change_mm':dxy,'checks':{'Z_field':dz<tol,'XY_field':dxy<tol},'pass':dz<tol and dxy<tol})
    dump(OUT/'cached_reference_field_review.json',{'created_utc':now(),'rows':rows,'pass':all(r['pass'] for r in rows),'old_native_solver_runs':0,'acceptance_unchanged':True});print({'A34_reference_field':rows},flush=True)

def create_runner():
    s=inspect.getsource(previous_skin.review).replace("'A33':cid","'A34':cid");ast.parse(s);exec(compile(s,__file__+'::review','exec'),globals())
    s=inspect.getsource(previous.run_one);changes={"n='A32_'":"n='A34_'", "ncell=int(re.search(r'_N(6|12)',cid).group(1))":"ncell=int(re.search(r'_N(\\d+)',cid).group(1));nz=int(re.search(r'_Z(\\d+)',cid).group(1))",'brick_grid([ncell,ncell,1]':'brick_grid([ncell,ncell,nz]',"'geometric_Z_elements':1":"'geometric_Z_elements':nz"}
    for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
    ast.parse(s);exec(compile(s,__file__+'::run_one','exec'),globals());dump(OUT/'runner_derivation.json',{'created_utc':now(),'source':rel(Path(previous.__file__)),'source_sha256':streamsha(Path(previous.__file__)),'derived_source':s,'literal_changes':changes,'review_source':rel(Path(previous_skin.__file__)),'review_source_sha256':streamsha(Path(previous_skin.__file__)),'original_review_checks_retained':True,'old_native_solver_runs':0})

def run():
    guard();cached_reference_field_check();create_runner();rows=[]
    for cid in read(CFG)['cases']:
        run_one('w1',cid);r=read(OUT/'w1'/cid/'review.json');rows.append(r);assert r['checks']['native_full_balance'] and r['checks']['finite_histories']
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'cases':rows,'completed':True,'whole_insertion_ready':False,'objective1_complete':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
