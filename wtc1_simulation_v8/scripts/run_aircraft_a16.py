"""A16 maximum-history skin damage: four checks, then two exploratory scene starts."""
import argparse,copy,json,re,shutil,traceback,urllib.request
from pathlib import Path
import numpy as np
from run_aircraft_a15 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute,env,streamsha,recover
from run_aircraft_a04 import blocks
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a16';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a16_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a15';PARENT=PREV/'r0/IMPACT_10_DT50'

def guard():assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def declare():
    assert not OUT.exists() and not CFG.exists();v=harness();assert v['CurrentIteration']=='AIRCRAFT-A15';OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for fn in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/fn)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a15_predeclaration.json')
    c.update(iteration='AIRCRAFT-A16',declared_utc=now(),seed=1102041,random_draws=0,
        scope='Native maximum-history radome skin damage, incomplete physical fracture model; fresh coupled10ms tests. No ORTHENERG transfer or historical fit.',
        prior_failure_reused={'report':'wtc1_simulation_v8/output/aircraft_a06/rapport_aircraft_a06.md','ORTHENERG_not_transferred':True,'why':'A06 energy depends on size and repeated equal peaks accumulate damage; prior outputs used without rerun'},
        damage={'keyword':'/FAIL/ORTHSTRAIN/4','applies_to':'radome face material4 only; core5 intact','strain_measure':'true strain, Strdef3','tensile_onset':450/22000,'compression_onset':460/22000,'threshold_derivation':'reference uniaxial strength/E; own balanced-woven simplification, not actual aircraft identification or multiaxial strength law','directions':'11 and22 same thresholds; shear and33 unmodelled/disabled1e20','end_strain':'(1+transition_fraction)*onset','transition_fractions':[.02,.2],'transition_provenance':'.2 matches documentation default ratio; .02 own one-decade sensitivity; neither calibrated to damage','maximum_history':True,'rate_effects':False,'size_effects':False,'P_thick_fail':1,'global_stack_P_thick_fail':1,'G_assigned':False,'G_physical_measured':False,'energy':'No entered fracture energy. Work/dissipation checked, implied energy remains mesh-dependent and unqualified. Do not label this regularized physical tearing.',
        'core_crushing':False,'delamination':False,'element_deletion':'not expected: intact8mm core and global thickness threshold1 retained','topological_fragmentation':False},
        witness={'path_time_ms':[0,.25,.5,.75,1],'path_log_strain':[0,.0225,0,.0225,.04],'smooth_each_leg':'cubic3u2-2u3','history_interval_ms':.0001,'animation_interval_ms':.005,'cases':[
            {'id':'CYCLE_L10_R20','L_mm':10,'transition_fraction':.2,'dt_cap_ms':.000025},
            {'id':'CYCLE_L10_R20_HALF','L_mm':10,'transition_fraction':.2,'dt_cap_ms':.0000125},
            {'id':'CYCLE_L20_R20','L_mm':20,'transition_fraction':.2,'dt_cap_ms':.000025},
            {'id':'CYCLE_L10_R02','L_mm':10,'transition_fraction':.02,'dt_cap_ms':.000025}]},
        witness_acceptance={'global_work_balance_fraction':.01,'energy_absolute_J':.001,'native_vs_maximum_history_damage_absolute':.02,'no_damage_at_equal_peak_absolute':.002,'closed_equal_peak_energy_fraction':.02,'affine_displacement_error_mm':.001,'half_dt_final_IE_difference_fraction':.01,'gate_role':'mechanical implementation/history gate only; never physical fracture energy qualification'},
        execution={'cpu_threads':2,'GPU':False,'starter_timeout_s':120,'witness_engine_timeout_s':120,'engine_timeout_s':1200,'converter_timeout_s':120,'estimated_whole_minutes':[10,30],'cases':[
            {'id':'IMPACT_R20_10','dt_scale':.5,'end_ms':10,'transition_fraction':.2},
            {'id':'IMPACT_R02_10','dt_scale':.5,'end_ms':10,'transition_fraction':.02}]},
        output_contract={'history_interval_ms':.01,'animation_interval_ms':.1,'damage':'DAMA/ALL native retained; all native states0.1ms retained, geometry review0.5ms','observer':'native first record only for final energy/time; observer contacts andREAC excluded'},
        qualified_transfer=False,physical_impact_qualified=False,NIST_outcomes_used_as_target=False,
        sources=['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/fail_orthstrain.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_dama_engine_r.htm'],
        qualification_policy={'exploratory_coupled_execution_authorized':True,'old_failed_gates_retained':True,'no_measured_G':True,'no_topological_rupture_claim':True,'no_new_mass_or_erosion':True,'unchanged_facade_and_metal_failure_absent':True,'parallel_module_integrated':False})
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_A16_solver':True})
    sd=OUT/'sources';sd.mkdir();src=[]
    for i,url in enumerate(c['sources']):
        p=sd/f'primary_{i}.html';p.write_bytes(urllib.request.urlopen(url,timeout=60).read());src.append({'path':rel(p),'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party'})
    for p in [PARENT/'generation.json',PARENT/'mesh.json',PARENT/'A15_IMPACT_10_DT50_0000.rad',PREV/'scientific_assessment.json',ROOT/'wtc1_simulation_v8/output/aircraft_a06/rapport_aircraft_a06.md',ROOT/'wtc1_simulation_v8/input/aircraft_a05_sources/hexply913.pdf']:
        src.append({'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':src,'no_new_archive_inspection':True,'material_sources_inherited_A11':True,'NIST_dependency':'representative facade inputs only, no outcome target'})
    print({'declared':'AIRCRAFT-A16','old_files_pinned':len(pins)},flush=True)

def failure(ratio):
    f=read(CFG)['damage'];t=f['tensile_onset'];c=f['compression_onset']
    line=lambda td,cd:ff(td,td*(1+ratio))+ii(0)+ff(cd,cd*(1+ratio))+ii(0)
    return ['/FAIL/ORTHSTRAIN/4',' '*20+ff(1)+' '*50+ii(3),ff(0,1e30),ii(0)+ff(1,1),line(t,c),line(t,c),line(1e20,1e20),line(1e20,1e20),line(1e20,1e20),line(1e20,1e20)]

def start(d,n,cap):
    assert not (d/'starter.log').exists();assert execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,env())
    log=(d/'starter.log').read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',log)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',log)[-1])==0,log[-2500:]
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',cap,env())
    log=(d/'engine.log').read_text(errors='replace');assert 'NORMAL TERMINATION' in log and 'TIME STEP LESS OR EQUAL ZERO' not in log

def witness(case):
    guard();cfg=read(CFG);d=OUT/'w0'/case['id'];assert not d.exists();d.mkdir(parents=True);n='A16_'+case['id'];L=case['L_mm'];orig={b[0]:b for b in blocks((PARENT/'A15_IMPACT_10_DT50_0000.rad').read_text().splitlines())}
    xyz=[[0,0,0],[L,0,0],[L,L,0],[0,L,0]]
    lines=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
    for key in ['/MAT/LAW25/4','/MAT/LAW25/5','/PROP/TYPE19/41','/PROP/TYPE19/42','/PROP/TYPE19/43','/PROP/TYPE51/21','/PART/21']:lines+=orig[key]
    lines+=['/SH3N/21',ii(1,1,2,3),ii(2,1,3,4)]+failure(case['transition_fraction'])
    for gid,ids in [(1,[1,2,3,4]),(2,[1,4]),(3,[2,3]),(4,[1,2]),(5,[3,4])]:lines += [f'/GRNOD/NODE/{gid}',f'GROUP_{gid}',ii(*ids)]
    lines+=['/BCS/1','FIX_Z_AND_ROT','   001 111'+ii(0,1),'/BCS/2','LEFT_X','   100 000'+ii(0,2),'/BCS/3','BOTTOM_Y','   010 000'+ii(0,4)]
    w=cfg['witness'];ts=np.linspace(0,1,10001);ep=np.zeros_like(ts)
    for ta,tb,ea,eb in zip(w['path_time_ms'][:-1],w['path_time_ms'][1:],w['path_log_strain'][:-1],w['path_log_strain'][1:]):
        ix=(ts>=ta)&(ts<=tb);u=(ts[ix]-ta)/(tb-ta);ep[ix]=ea+(eb-ea)*(3*u*u-2*u*u*u)
    for fid,di,gid,dis in [(90,'X',3,L*np.expm1(ep)),(91,'Y',5,L*np.expm1(-.25*ep))]:
        lines += [f'/FUNCT/{fid}',f'AFFINE_{di}']+[ff(t,x) for t,x in zip(ts,dis)]+[f'/IMPDISP/{fid}',f'IMPOSE_{di}',ii(fid)+f'{di:>10}'+ii(0,0,gid)+' '*10+ii(0),ff(1,1,0,1e30)]
    lines+=['/TH/PART/1','SANDWICH',''.join(f'{s:>10}' for s in ['IE','KE','HE','PW']),ii(21),'/TH/NODE/2','AFFINE_NODES',''.join(f'{s:>10}' for s in ['DX','DY','VX','VY','REACX','REACY'])]+[ii(i,0) for i in range(1,5)]+['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    E=['/ANIM/DT',ff(0,w['animation_interval_ms']),'/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/SHELL/TENS/STRESS/UPPER','/ANIM/SHELL/TENS/STRAIN/UPPER','/ANIM/SHELL/DAMA/ALL','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(case['dt_cap_ms'],case['dt_cap_ms']),'/MON/ON','/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(w['history_interval_ms']),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');dump(d/'generation.json',{'name':n,'case':case,'created_utc':now(),'nodes_mm':xyz,'configuration_sha256':sha(CFG),'fresh_intact_start':True,'prescribed_motion_only_in_witness':True})
    start(d,n,120);assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());print({'witness_finished':case['id']},flush=True)

def whole(case):
    guard();assert read(OUT/'witness_review.json')['mechanical_gate_pass'];d=OUT/'r0'/case['id'];assert not d.exists();d.mkdir(parents=True);g=read(PARENT/'generation.json');n='A16_'+case['id'];B=blocks((PARENT/(g['name']+'_0000.rad')).read_text().splitlines());lines=[]
    for b0 in B:
        b=b0.copy()
        if b[0] in ['/BEGIN','/TITLE']:b[1]=n
        if b[0]=='/END':continue
        lines+=b
    lines+=failure(case['transition_fraction'])+['/END']
    orig={b[0]:b for b in B if b[0] not in ['/BEGIN','/TITLE','/END']};new={b[0]:b for b in blocks(lines)};assert all(new[k]==v for k,v in orig.items())
    (d/(n+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for job in [1,2]:
        E=blocks((PARENT/(g['name']+f'_000{job}.rad')).read_text().replace(g['name'],n).splitlines());out=[]
        for b in E:out+=b
        out+=['/ANIM/SHELL/DAMA/ALL'];(d/(n+f'_000{job}.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8')
    shutil.copy2(PARENT/'mesh.json',d/'mesh.json');shutil.copy2(__file__,d/'generator_snapshot.py')
    dump(d/'generation.json',{**g,'name':n,'case':case,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'parent':rel(PARENT),'only_new_mechanical_card':'/FAIL/ORTHSTRAIN/4','full_historical_impact':False,'history_records_per_frame':14})
    start(d,n,1200);pins={p.name:streamsha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(n+'_0002.rad'),o/(n+'_0002.rad'))
    for p in d.glob(n+'_0001_*.rst'):shutil.copy2(p,o/p.name)
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],o,'observer.log',60,env());assert all(streamsha(d/p)==h for p,h in pins.items());dump(d/'observer_preservation.json',{'main_outputs_unchanged':True,'pass':True})
    assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());recover(d,n);print({'whole_finished':case['id']},flush=True)

def batch(which):
    guard();cases=read(CFG)['witness']['cases'] if which=='witnesses' else read(CFG)['execution']['cases'];folder='w0' if which=='witnesses' else 'r0'
    for c in cases:
        d=OUT/folder/c['id']
        try:witness(c) if which=='witnesses' else whole(c)
        except Exception:
            d.mkdir(parents=True,exist_ok=True);dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'case':c,'traceback':traceback.format_exc(),'not_qualified':True});print(traceback.format_exc(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','witnesses','whole']);a=p.parse_args();declare() if a.action=='declare' else batch(a.action)
