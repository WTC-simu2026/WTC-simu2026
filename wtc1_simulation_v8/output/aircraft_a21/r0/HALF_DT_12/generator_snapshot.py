"""One fresh intact twelve-ms impact: halve only A20's explicit time-step scale."""
from run_aircraft_a21 import *
from run_aircraft_a18 import blocks
from audit_aircraft_a02 import numbers_after
from recover_aircraft_a05_history import records
import csv

HC=ROOT/'wtc1_simulation_v8/data/aircraft_a21_halfdt_declaration.json'
D=OUT/'r0/HALF_DT_12'; N='A21_HALF_DT_12'; PN='A20_CORE3D_TIED_20'

def hguard():
    guard(); assert streamsha(HC)==read(OUT/'halfdt_guard.json')['sha256']
    assert all(streamsha(ROOT/x['path'])==x['sha256'] for x in read(HC)['source_pins'])

def declare():
    guard(); assert not HC.exists(); h=harness(); assert h['Status']=='PASS'
    assert not read(OUT/'native_precision_review.json')['printed_CSV_precision_alone_explains_failure']
    reused=[PREV/'core_verified_review.json',PREV/'sandwich_type2_review.json']
    assert all(read(p)['pass'] for p in reused)
    paths=[SOURCE/(PN+'_0000.rad'),SOURCE/(PN+'_0001.rad'),SOURCE/'mesh.json',SOURCE/'generation.json',SOURCE/'native_insertion_gate.json']+reused
    c={'iteration':'AIRCRAFT-A21','case':'HALF_DT_12','declared_utc':now(),'seed':1102046,'random_draws':0,
       'purpose':'Separate explicit time-integration sensitivity from new material, rupture or attachment hypotheses. Fresh intact same A20 scene; no continuation of invalid A20 checkpoint.',
       'changed_mechanics':False,'only_engine_changes':['DT scale 0.5 to0.25','requested horizon20 to12ms','case name'],
       'unchanged':['all Starter mechanical cards including root RBE2','all geometry and material mass budgets','all four external contacts and radome self-contact','velocity -200,5,2 m/s','no gravity or interior added','output intervals0.02ms history0.2ms animation'],
       'sources':read(CFG)['source'],'source_pins':[{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in paths],
       'local_controls_reused':[rel(p) for p in reused],'local_controls_rerun':False,
       'execution':{'CPU_threads':2,'GPU':False,'estimated_minutes':[20,35],'engine_cap_s':2700,'end_ms':12,'dt_scale':.25,'history_dt_ms':.02,'animation_dt_ms':.2},
       'acceptance':read(CFG)['acceptance'],'comparison':{'common_horizon_ms':12,'old_A20_not_rerun':True,'global_ledger':'native float32 records plus printed CSV independently; do not change existing thresholds or infer RKE','separate_windows_ms':[[0,10],[10,12.0001]],'impulse_relative_limit':.05,'generated_energy_relative_limit':.1},
       'no_mass_scaling':True,'no_material_density_ADMAS_change':True,'old_failed_gates_retained':True,'physical_impact_qualified':False,'objective1_complete':False,'seconds_extension_allowed':False,'NIST_damage_fitted':False}
    dump(HC,c);dump(OUT/'halfdt_guard.json',{'created_utc':now(),'sha256':streamsha(HC),'before_any_new_halfdt_solver':True});dump(OUT/'harness_before_halfdt.json',h)
    print({'declared':N,'reused_local_controls':len(reused),'only_numerical_step_changed':True},flush=True)

def build():
    hguard(); assert not D.exists(); D.mkdir(parents=True)
    src=(SOURCE/(PN+'_0000.rad')).read_text(); dst=src.replace(PN,N)
    assert dst.replace(N,PN)==src
    (D/(N+'_0000.rad')).write_text(dst,encoding='utf-8')
    original=blocks((SOURCE/(PN+'_0001.rad')).read_text().splitlines()); engine=[]; changed=[]
    for old in original:
        b=old.copy()
        if b[0]=='/DT':b[1]=ff(.25,0)
        elif b[0].startswith('/RUN/'):
            b[0]=f'/RUN/{N}/1';b[1]=ff(12)
        if b!=old:changed.append(b[0])
        engine+=b
    assert changed==['/DT',f'/RUN/{N}/1']
    (D/(N+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8'); observer=[]
    for old in blocks(engine):
        b=old.copy()
        if b[0].startswith('/RUN/'):b[0]=f'/RUN/{N}/2';b[1]=ff(12.000001)
        observer+=b
    (D/(N+'_0002.rad')).write_text('\n'.join(observer)+'\n',encoding='utf-8')
    shutil.copy2(SOURCE/'mesh.json',D/'mesh.json');g=read(SOURCE/'generation.json')
    dump(D/'generation.json',{**g,'created_utc':now(),'name':N,'case':'HALF_DT_12','parent':rel(SOURCE),'configuration_sha256':streamsha(HC),'mechanical_scene_unchanged':True,'old_solver_reruns':0,'new_solver_run':True,'generator_sha256':streamsha(Path(__file__))})
    shutil.copy2(__file__,D/'generator_snapshot.py');dump(D/'scene_audit.json',{'created_utc':now(),'pass':True,'every_starter_card_identical_except_name':True,'changed_engine_cards':changed,'no_restart_from_A20':True,'mechanical_scene_unchanged':True})
    print({'built':N,'mechanical_scene_identical':True},flush=True)

def starter():
    hguard();assert not (D/'starter.log').exists()
    ok=execute(RUNTIME/'starter_win64.exe',['-i',N+'_0000.rad','-np','1'],D,'starter.log',180,env())
    s=(D/'starter.log').read_text(errors='replace'); nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);ids=re.findall(r'WARNING ID\s*:\s*(\d+)',s)
    text=(D/(N+'_0000.out')).read_text(errors='replace'); old=(SOURCE/(PN+'_0000.out')).read_text(errors='replace')
    mc=np.asarray(numbers_after(text,'TOTAL MASS AND MASS CENTER',4)); prior=np.asarray(numbers_after(old,'TOTAL MASS AND MASS CENTER',4)); I=np.asarray(numbers_after(text,'TOTAL INERTIA',6)); Iold=np.asarray(numbers_after(old,'TOTAL INERTIA',6))
    checks={'exit_ok':ok,'zero_errors':ne==0,'only_inherited_initial_self_warnings':nw==2 and ids==['1166','343'],'physical_mass_and_CG_identical':bool(np.array_equal(mc,prior)),'physical_inertia_identical':bool(np.array_equal(I,Iold)),'passing_core_and_sandwich_controls_reused':True,'Starter_mechanics_identical':read(D/'scene_audit.json')['pass']}
    r={'created_utc':now(),'checks':checks,'exploratory_engine_allowed':all(checks.values()),'strict_zero_warning_pass':nw==0,'warnings':nw,'errors':ne,'warning_ids':ids,'mass_CG':mc.tolist(),'same_A20_model_limitations_retained':True,'physical_impact_qualified':False}
    dump(D/'starter_gate.json',r);print(r,flush=True);assert r['exploratory_engine_allowed']

def recover():
    H=histories(D/(N+'T01.csv')); v=np.column_stack(list(H.values())); rr=records(D/(N+'T01')); nr=14;h=len(rr)-len(v)*nr
    assert h==read(SOURCE/'history_recovery.json')['header_records']
    sizes=[len(x) for x in rr[h:h+nr]]; assert sizes==read(SOURCE/'history_recovery.json')['sizes']
    raw=np.array([np.concatenate([np.frombuffer(x,dtype='>f4').astype(float) for x in rr[h+i*nr:h+(i+1)*nr]]) for i in range(len(v))])
    assert raw.shape==v.shape and np.allclose(raw,v,rtol=6e-7,atol=1e-12)
    ro=records(D/'observer'/(N+'T02'));assert len(ro)==h+nr
    end=np.concatenate([np.frombuffer(x,dtype='>f4').astype(float) for x in ro[h:]])
    with (D/'observer'/(N+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(list(H));w.writerow([format(x,'.9g') for x in end])
    np.savez_compressed(D/'native_global_history.npz',columns=list(H)[:23],values=np.vstack([raw[:,:23],end[:23]]))
    dump(D/'history_recovery.json',{'created_utc':now(),'pass':True,'records_per_frame':nr,'header_records':h,'sizes':sizes,'rows':len(v),'channels':v.shape[1],'all_main_CSV_binary_channels_agree':True,'native_end_ms':float(end[0])})

def engine():
    hguard(); assert read(D/'starter_gate.json')['exploratory_engine_allowed'];assert not (D/'engine.log').exists();shutil.copy2(__file__,D/'engine_driver_snapshot.py')
    try:
        assert execute(RUNTIME/'engine_win64.exe',['-i',N+'_0001.rad'],D,'engine.log',read(HC)['execution']['engine_cap_s'],env())
        s=(D/'engine.log').read_text(errors='replace'); assert 'NORMAL TERMINATION' in s and 'TIME STEP LESS OR EQUAL ZERO' not in s
        o=D/'observer';o.mkdir();shutil.copy2(D/(N+'_0002.rad'),o/(N+'_0002.rad'))
        for p in D.glob(N+'_0001_*.rst'):shutil.copy2(p,o/p.name)
        pins={p.name:streamsha(p) for p in D.iterdir() if p.is_file()}
        assert execute(RUNTIME/'engine_win64.exe',['-i',N+'_0002.rad'],o,'observer.log',60,env())
        assert all(streamsha(D/p)==sha for p,sha in pins.items());dump(D/'observer_preservation.json',{'pass':True,'main_outputs_unchanged':True})
        assert execute(RUNTIME/'th_to_csv_win64.exe',[N+'T01'],D,'converter.log',180,env());recover(); print({'finished':N},flush=True)
    except Exception:
        dump(D/('retained_failure_'+now().replace(':','-')+'.json'),{'created_utc':now(),'traceback':traceback.format_exc(),'physical_impact_qualified':False});raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','starter','engine']);globals()[p.parse_args().action]()
