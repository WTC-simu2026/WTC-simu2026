"""Fresh A06 starts; no old Engine, no damaged material edits, no event fitting."""
import argparse, json, shutil, os, re, csv
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute
from run_aircraft_a04 import blocks
from run_aircraft_a05 import elastic_ortho
from recover_aircraft_a05_history import records
from audit_aircraft_a05 import histories
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a06_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a06';PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a05'
def preserved():
    rows=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in rows if sha(ROOT/r['path'])!=r['sha256']];assert not bad,bad;return len(rows)
def guard():assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def initialize():
    assert not OUT.exists(); v=harness();assert v['CurrentIteration']=='AIRCRAFT-A05';OUT.mkdir()
    dump(OUT/'harness_before.json',v)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/name)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_new_solver':True})
    files=list((ROOT/'wtc1_simulation_v8/input/aircraft_a06_sources').glob('*'))+[ROOT/read(CFG)['inherited_configuration'],PREV/'case_selection.json',PREV/'cached_review/review.json']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size,'redistribution':'exclude_external_code' if p.suffix in ['.F','.cfg'] else 'own_provenance'} for p in files],'primary_links':read(CFG)['sources'],'archive_rescanned':False,'source_binary_equivalence_established':False})
    print({'initialized':'A06','old_files_pinned':preserved()},flush=True)
def failure():
    f=read(CFG)['failure'];v=lambda t,c:ff(t,f['G_N_mm'])+ii(f['shape'])+ff(c,f['G_N_mm'])+ii(f['shape'])
    return ['/FAIL/ORTHENERG/4',ff(f['P_thick_fail'])+' '*60+ii(f['NMOD'],0),v(f['sigma_t_MPa'],f['sigma_c_MPa']),v(f['sigma_t_MPa'],f['sigma_c_MPa']),'',v(f['sigma_shear_MPa'],f['sigma_shear_MPa']),'','']
def env():
    e=os.environ.copy();e.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='2',KMP_STACKSIZE='400m');return e
def start_engine(d,n):
    guard();e=read(CFG)['execution'];assert not (d/'starter.log').exists()
    ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',e['starter_timeout_s'],env())
    s=(d/'starter.log').read_text(encoding='utf-8',errors='replace');wa=re.findall(r'(\d+) WARNING\(S\)',s);er=re.findall(r'(\d+) ERROR\(S\)',s)
    if not ok or not wa or not er or int(wa[-1]) or int(er[-1]):print({'starter_rejected':n});return False
    ok=execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',e['engine_timeout_s'],env());print({'engine':n,'normal_exit':ok},flush=True);return ok
def generate_witness(revision,case):
    guard();c=read(CFG);base=OUT/revision;base.mkdir(exist_ok=True);d=base/case['id'];assert not d.exists();d.mkdir();L=case['L_mm'];n='A06_'+case['id'];old=read(ROOT/c['inherited_configuration'])
    parent=PREV/read(PREV/'case_selection.json')['case_directories']['COMP_SELF'];bb=blocks((parent/'A05_COMP_SELF_0000.rad').read_text(encoding='utf-8').splitlines());pb={b[0]:b for b in bb}
    lines=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']
    xyz=[[0,0,0],[L,0,0],[L,L,0],[0,L,0]];lines+=[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
    for key in ['/MAT/LAW25/4','/MAT/LAW25/5','/PROP/TYPE19/41','/PROP/TYPE19/42','/PROP/TYPE19/43','/PROP/TYPE51/21','/PART/21']:lines+=pb[key]
    lines+=['/SH3N/21',ii(1,1,2,3),ii(2,1,3,4)]
    if case['failure']:lines+=failure()
    for gid,ids in [(1,[1,2,3,4]),(2,[1,4]),(3,[2,3]),(4,[1,2]),(5,[3,4])]:lines += [f'/GRNOD/NODE/{gid}',f'GROUP_{gid}',ii(*ids)]
    lines+=['/BCS/1','FIX_Z_AND_ROT',f"{'001':>6}{'111':>4}"+ii(0,1),'/BCS/2','LEFT_X',f"{'100':>6}{'000':>4}"+ii(0,2),'/BCS/3','BOTTOM_Y',f"{'010':>6}{'000':>4}"+ii(0,4)]
    w=c['witness'];ts=np.linspace(0,1,2001);ep=np.interp(ts,w['path_time_ms'],w['path_log_strain'])
    for fid,di,gid,dis in [(90,'X',3,L*np.expm1(ep)),(91,'Y',5,L*np.expm1(-old['sandwich']['face']['nu12']*ep))]:
        lines += [f'/FUNCT/{fid}',f'AFFINE_{di}']+[ff(t,x) for t,x in zip(ts,dis)]
        lines += [f'/IMPDISP/{fid}',f'IMPOSE_{di}',ii(fid)+f'{di:>10}'+ii(0,0,gid)+' '*10+ii(0),ff(1,1,0,1e30)]
    lines+=['/TH/PART/1','SANDWICH',''.join(f'{s:>10}' for s in ['IE','KE','HE','PW']),ii(21),'/TH/NODE/2','AFFINE_NODES',''.join(f'{s:>10}' for s in ['DX','DY','VX','VY','REACX','REACY'])]+[ii(i,0) for i in range(1,5)]+['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    engine=['/ANIM/DT',ff(0,w['animation_dt_ms']),'/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/SHELL/TENS/STRESS/UPPER','/ANIM/SHELL/TENS/STRAIN/UPPER','/ANIM/SHELL/DAMA/ALL','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(case['dt_cap_ms'],case['dt_cap_ms']),'/MON/ON','/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(w['history_dt_ms']),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8');dump(d/'generation.json',{'name':n,'case':case,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'nodes_mm':xyz,'fresh_intact_start':True,'history_path_is_imposed_only_in_witness':True});return d,n
def witnesses(revision):
    for c in read(CFG)['witness']['cases']:
        d,n=generate_witness(revision,c)
        if start_engine(d,n):assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',90,env())
    dump(OUT/revision/'harness_after.json',harness())
def build_whole(revision):
    guard();assert (OUT/'witness_review.json').exists();base=OUT/revision;assert not base.exists();base.mkdir();c=read(CFG);sel=read(PREV/'case_selection.json')['case_directories']
    for case in c['whole_aircraft']['cases']:
        p=PREV/sel[case['parent']];oldg=read(p/'generation.json');oldn=oldg['name'];d=base/case['id'];d.mkdir();n='A06_'+case['id'];source=blocks((p/(oldn+'_0000.rad')).read_text(encoding='utf-8').splitlines());out=[];changed=[]
        for b0 in source:
            b=b0.copy()
            if b[0]=='/BEGIN':b[1]=f'{n:<80}'
            elif b[0]=='/TITLE':b[1]=n
            elif b[0].startswith('/PROP/TYPE1/'):
                assert len(b[4])>=100;b[4]=b[4][:60]+ff(1e-20,1e-20)+b[4][100:];changed.append(b[0])
            out+=b
        assert changed and not any(b[0].startswith('/FAIL/') for b in source)
        (d/(n+'_0000.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8');shutil.copy2(p/'mesh.json',d/'mesh.json')
        for suffix in ['_0001.rad','_0002.rad']:
            text=(p/(oldn+suffix)).read_text(encoding='utf-8').replace(oldn,n);(d/(n+suffix)).write_text(text,encoding='utf-8')
        newbs={b[0]:b for b in blocks(out)};oldbs={b[0]:b for b in source}
        assert all(oldbs[k]==newbs[k] for k in oldbs if k not in changed+['/BEGIN','/TITLE'])
        dump(d/'generation.json',{**oldg,'name':n,'case':{**oldg['case'],'id':case['id']},'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'parent_deck':rel(p/(oldn+'_0000.rad')),'parent_deck_sha256':sha(p/(oldn+'_0000.rad')),'only_mechanical_changed_cards':changed,'explicit_metal_dm_dn':1e-20,'failure_transfer_enabled':False,'fresh_intact_start':True})
    dump(base/'harness_after_generation.json',harness());print({'whole_cases_built':len(c['whole_aircraft']['cases'])})
def recover_end(d,n):
    H=histories(d/(n+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(n+'T01'));nr=9;header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[0]==4 and sizes[1]==88 and all([len(q) for q in f]==sizes for f in frames)
    nat=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert nat.shape==v.shape and np.allclose(nat,v,rtol=6e-7,atol=1e-12)
    ro=records(d/'observer'/(n+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]]);assert end[0]>v[-1,0]
    with (d/'observer'/(n+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:wr=csv.writer(f);wr.writerow(list(H));wr.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'pass':True,'all_main_rows_matched':len(v),'records_per_frame':nr,'sizes':sizes,'no_T02_converter_attempt':'Known A05 one-row crash; direct validated schema instead','observer_row_only':True,'end_ms':float(end[0]),'synthetic_steps':0})
def run_whole(revision,caseid):
    d=OUT/revision/caseid;n=read(d/'generation.json')['name']
    if start_engine(d,n):
        pins={rel(p):sha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(n+'_0002.rad'),o/(n+'_0002.rad'))
        for p in d.glob(n+'_0001_*.rst'):shutil.copy2(p,o/p.name)
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],o,'observer.log',60,env());changed=[p for p,h in pins.items() if sha(ROOT/p)!=h];assert not changed;dump(d/'observer_preservation.json',{'main_outputs_unchanged':True,'changed':changed})
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',90,env());recover_end(d,n)
        dump(d/'execution_summary.json',{'main_normal_termination':True,'verified_end_possible':True,'partial_data_only':False})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['initialize','witnesses','build_whole','run_whole']);p.add_argument('--revision',default='w0');p.add_argument('--case',default='ZERO_DM');a=p.parse_args()
    if a.action=='initialize':initialize()
    elif a.action=='witnesses':witnesses(a.revision)
    elif a.action=='build_whole':build_whole(a.revision)
    else:run_whole(a.revision,a.case)
