"""Separate native formulation and strain-update flags at unchanged physics."""
import run_aircraft_a34 as old_refinement
import run_aircraft_a33 as face_runner
import run_aircraft_a32 as template
from run_aircraft_a34 import *
import time
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a35'
PREV=old_refinement.OUT
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a35_predeclaration.json'
CASES=['PATCH_NORMAL_Z_N12_Z4','FREE_ROTATION_Y_N24_Z4','FACE_BENDING_N24_Z4','FACE_BENDING_N48_Z4','FACE_BENDING_N48_Z4_HALF']
DEADLINE=None
native_execute=execute

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A34';assert read(PREV/'publication_verification.json')['pass'];cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_iterations']==['AIRCRAFT-A34']
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c=read(old_refinement.CFG);c.update(iteration='AIRCRAFT-A35',declared_utc=now(),seed=1102060,parent_configuration=rel(old_refinement.CFG),parent_configuration_sha256=streamsha(old_refinement.CFG),cases=CASES,
        purpose='Disentangle the A34freeedge defect from native formulation/strain flags. w0uses sourceIsolid18/Ismstr0(auto2),w1uses sourceHEPH24with onlyIsmstr4->2. SameLAW12,skew,volume,density,mass,faceconditions,independentC/continuum andunchangedacceptance. Prior24/4cases staycachedandfailed,notrerun.',
        branches={'w0':{'formulation':'SourceA29 TYPE6 Isolid18 Ismstr0(auto2) Icpre3 Iframe2','expected_native_flags':[18,2,3,2],'cases':CASES},'w1':{'formulation':'SourceA32 TYPE6 Isolid24 Ismstr2 Icpre3 Iframe2; otherparametersunchanged','expected_native_flags':[24,2,3,2],'cases':CASES}},
        strain_flag_interpretation='PreservedprimaryTYPE6defines2and4asfullgeometricnonlinearities;2allowsEngine/DT/BRICK/CSTswitching,4doesnot. No/DT/BRICK/CSTinoursources. Do not label2assmallstrain or claim a cause before new native evidence.',
        cached_baseline={'iteration':'A34','flags':[24,4,3,2],'cases':['FACE_BENDING_N48_Z4','FACE_BENDING_N48_Z4_HALF'],'original_failed_gates_unchanged':True},
        stop_rule='PerbranchstoponStarter/Enginefatal,nonfiniteoutput,fullbalancefailureorfailedfirstaffinegate. Keepattemptsandcachedoldresults. Theotherdeclaredbranchmayproceed. Remainingelasticfailuresarediagnosticandmustnotbeconvertedtopasses.',
        software_installation_or_compilation=False,software_build_permission_not_assumed=True,whole_aircraft_inputs_changed=False,whole_insertion_ready=False)
    c['geometry'].update(XY=[12,24,48],physical_Z_cells=[4]);c['acceptance']['scope']='Eachcandidatebranchrequiresallfiveoriginalcasegates,ownXY/time refinements,nativefieldaudit,cards/readback and sourcephysicalmass. Passing a fine energy alone is not whole qualification.';c['execution'].update(estimated_minutes=[10,30],per_process_cap_s=900,whole_campaign_wall_cap_s=2700)
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_results':True})
    files=[old_refinement.CFG,Path(old_refinement.__file__),Path(face_runner.__file__),Path(template.__file__),Path(source_skin.__file__),PREV/'publication_verification.json',PREV/'composite_qualification_review.json',REFERENCE,ROOT/'wtc1_simulation_v8/output/aircraft_a34/cached_reference_field_review.json',ROOT/'wtc1_simulation_v8/output/aircraft_a32/sources/type6.html']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in files],'source_archive_rescanned':False,'known_damage_target':False})
    print({'A35_declared':True,'maximum_new_controls':10,'CPU_minutes':[10,30],'campaign_wall_cap_minutes':45,'software_modifications':False},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def property_card(branch):
    if branch=='w0':return source_skin.property_card()
    p=template.property_card('w1');a=ii(24,4);b=ii(24,2);assert sum(x.count(a) for x in p)==1
    return [x.replace(a,b) for x in p]

def native_frame(d,n,branch):
    t=(d/(n+'_0000.out')).read_text();m=re.search(r'SKEW SYSTEM SETS.*?\n\s*1\s+0\s+0\s+0\s+([^\n]+)\n\s+([^\n]+)\n\s+([^\n]+)',t,re.S);assert m;axes=np.asarray([[float(v) for v in x.split()][:3] for x in m.groups()]);header='Isolid  Ismstr   Icpre  Iframe    IHKT Itetra4 Itetra10 IMATVIS ICONTROL';m=re.search(re.escape(header)+r'\s+'+r'\s+'.join([r'(\d+)']*9),t);assert m;flags=list(map(int,m.groups()));expected=read(CFG)['branches'][branch]['expected_native_flags'];checks={'material_axes':bool(np.allclose(axes,[[0,1,0],[-1,0,0],[0,0,1]],atol=1e-6,rtol=0)),'declared_native_flags':flags[:4]==expected,'no_unannounced_strain_switch':True};dump(d/'native_frame_gate.json',{'created_utc':now(),'flags':flags,'expected_first4':expected,'axes_rows':axes.tolist(),'checks':checks,'pass':all(checks.values()),'before_Engine':True});assert all(checks.values()),checks

def execute(exe,args,d,log,timeout,en):
    remaining=DEADLINE-time.perf_counter();assert remaining>0,'Declaredcampaignwallcapreached;noimplicitrestart';return native_execute(exe,args,d,log,min(timeout,900,max(1,remaining)),en)

def create_runner():
    s=inspect.getsource(face_runner.review).replace("'A33':cid","'A35':cid").replace("'branch':'w1'","'branch':g['branch']");ast.parse(s);exec(compile(s,__file__+'::review','exec'),globals())
    s=inspect.getsource(template.run_one);changes={"n='A32_'":"n='A35_'", "ncell=int(re.search(r'_N(6|12)',cid).group(1))":"ncell=int(re.search(r'_N(\\d+)',cid).group(1));nz=int(re.search(r'_Z(\\d+)',cid).group(1))",'brick_grid([ncell,ncell,1]':'brick_grid([ncell,ncell,nz]',"'geometric_Z_elements':1":"'geometric_Z_elements':nz"}
    for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
    ast.parse(s);exec(compile(s,__file__+'::run_one','exec'),globals());dump(OUT/'runner_derivation.json',{'created_utc':now(),'source':rel(Path(template.__file__)),'source_sha256':streamsha(Path(template.__file__)),'derived_source':s,'literal_changes':changes,'review_source':rel(Path(face_runner.__file__)),'review_source_sha256':streamsha(Path(face_runner.__file__)),'review_original_gates_retained':True,'only_flags_geometricmeshes_caseids_changed':True,'old_native_runs':0})

def run():
    global DEADLINE
    guard();DEADLINE=time.perf_counter()+2700;create_runner();branches=[]
    for branch,setting in read(CFG)['branches'].items():
        rows=[];stopped=None
        for cid in setting['cases']:
            try:
                run_one(branch,cid);r=read(OUT/branch/cid/'review.json');rows.append(r)
                if not r['checks']['native_full_balance'] or not r['checks']['finite_histories'] or (cid.startswith('PATCH_') and not r['pass']):stopped={'case':cid,'reason':'Originalfullbalance/finite/firstaffinegatefailed'};break
            except Exception:stopped={'case':cid,'reason':'Nativeorreaderfailure','traceback':traceback.format_exc()};break
        summary={'created_utc':now(),'branch':branch,'cases':rows,'stopped':stopped,'completed_all_declared':len(rows)==5 and stopped is None};dump(OUT/(branch+'_case_summary.json'),summary);branches.append(summary)
        if time.perf_counter()>=DEADLINE:break
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'branches':branches,'whole_insertion_ready':False,'objective1_complete':False});print({'A35_campaign_terminal':True,'new_native_reviews':sum(len(x['cases']) for x in branches),'branch_completion':[x['completed_all_declared'] for x in branches]},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
