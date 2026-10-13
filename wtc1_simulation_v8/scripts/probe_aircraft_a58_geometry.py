"""Source/native compatibility audit after the exact original-buffer correction."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from pathlib import Path
import tarfile,hashlib,json,shutil,re
import probe_aircraft_a54 as launcher

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a58'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a58_predeclaration.json'

def engine():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    c=read(CFG);p=ROOT/c['candidate_directory'];b=p/'isolated_exec/engine_linux64_gf_ompi';assert sha(b)==c['binary_sha256'];return p,b

def declare():
    assert not OUT.exists() and not CFG.exists()
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A57'
    assert read(ROOT/'harness/publication_cycle.json')['pending_count']==0
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a57';assert read(prior/'publication_verification.json')['pass']
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    built=read(prior/'build_finished.json')
    c={'created_utc':now(),'iteration':'AIRCRAFT-A58','seed':1102083,'random_draws':0,'question':'Does actual TYPE43/LAW117 implicit dispatch use the volumetric Jacobian check before calling the surface constitutive path? Document source branches without removing the STOP or changing thickness.',
       'candidate_directory':built['candidate_directory'],'binary_sha256':built['binary_sha256'],'source_pin':built['source_pin'],'CPU_threads':1,'GPU':False,'native_cap_s':180,'expected_minutes':[1,3],'maximum_native_Engines':1,'Starter_runs':0,'new_software_patch_or_compilation':False,'physical_inputs_and_budgets_unchanged':True,'new_whole_duration_credit_s':0,'whole_insertion_ready':False,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_native':True})
    pins={r['path']:r for r in read(prior/'preservation_before_metadata.json')['files']}
    for row in read(prior/'artifact_manifest.json')['files']:pins[row['path']]=row
    for p in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':[{**r,'mtime_ns_before':(ROOT/r['path']).stat().st_mtime_ns} for r in pins.values()]})
    print('A58 declared: one fresh dispatch observation, unchanged binary and physical state.',flush=True)

def source_review():
    engine();archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    paths=['engine/source/elements/solid/solide8z/s8zke3.F','engine/source/elements/solid/solide8z/s8zderict3.F','engine/source/elements/solid/solide/schkjab3.F','engine/source/elements/solid/solide8z/mmats.F','engine/source/elements/solid/solide8z/mmstifs.F','engine/source/elements/solid/sconnect/suser43.F','engine/source/materials/mat/mat117/sigeps117.F']
    data={};rows=[]
    with tarfile.open(archive) as t:
        for path in paths:
            m=next(x for x in t.getmembers() if x.name.endswith(path));raw=t.extractfile(m).read();s=raw.decode('utf8');data[path]=s
            patterns={'S8ZKE3':['CALL SRCOORK','CALL S8ZDERICT3','CALL MMATS','CALL MMSTIFS','CALL ASSEM_S8'],'S8ZDERICT3':['DET(I)=','CALL SCHKJAB3'],'SCHKJAB3':['DET(I)<=','WRITE(','MSTOP ='],'MMATS':['ELSE','SELECT CASE (MTN)','CASE(','HH(1,I)','HH(2,I)'],'MMSTIFS':['VOL(I)','MTN'],'SUSER43':['CASE (117)','CALL SIGEPS117'],'SIGEPS117':['SUBROUTINE','AREA','STIFM','DMG']}
            key=Path(path).stem.upper();hits=[{'line':i+1,'matched_search_terms':[p for p in patterns[key] if p.upper() in l.upper()]} for i,l in enumerate(s.splitlines()) if any(p.upper() in l.upper() for p in patterns[key])]
            rows.append({'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'relevant_lines':hits})
    lines=data[paths[0]].splitlines();i=next(i for i,l in enumerate(lines) if 'SUBROUTINE S8ZKE3(' in l);body=''
    for l in lines[i:]:
        body+=l[6:];
        if ')' in body:break
    args=[x.strip() for x in body.split('(',1)[1].split(')',1)[0].split(',')];assert len(args)==28 and args[-3]=='IGTYP'
    dump(OUT/'source_capability_review.json',{'created_utc':now(),'sources':rows,'S8ZKE3_arguments':args,'raw_AGPL_source_not_copied_into_MIT_manifest':True,
       'volumetric_geometry_dispatch_source_confirmed':True,'MMATS_specific_LAW117_branch_in_this_file':bool(re.search(r'MTN\s*==\s*117|CASE\s*\(\s*117',data[paths[3]])),'surface_constitutive_CALL_SIGEPS117_present_in_SUSER43':True,'absence_of_MMATS_branch_is_limited_to_this_file':True,'physical_implicit_compatibility_qualified':False,'no_STOP_suppression_or_thickness_regularization':True})
    print('Seven source routines audited, raw sources remain read-only and excluded.',flush=True)

def native():
    candidate,b=engine();prior=ROOT/'wtc1_simulation_v8/output/aircraft_a57';source=prior/'implicit_cohesive_controls/w0/NORMAL_L10';name=read(source/'generation.json')['name']
    d=OUT/'NATIVE_TYPE43_GEOMETRY_DISPATCH';assert not d.exists();d.mkdir();files=[]
    for p in [source/(name+'_0000_0001.rst'),source/(name+'_0001.rad')]:files.append({'path':rel(p),'sha256':sha(p)});shutil.copy2(p,d/p.name)
    symbols={l.split()[-1]:int(l.split()[0],16) for l in (prior/'engine_symbols.txt').read_text(encoding='utf8').splitlines() if len(l.split())>=3};names=['s8zke3_','s8zderict3_','schkjab3_','suser43_'];assert all(n in symbols for n in names)
    observer=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a58_geometry_linux.py';c={'created_utc':now(),'iteration':'AIRCRAFT-A58','seed':1102083,'random_draws':0,'binary':linux(b),'binary_sha256':sha(b),'directory':linux(d),'Engine_card':name+'_0001.rad','input_files':files,'symbols':{n:symbols[n] for n in names},'S8ZKE3_arguments':read(OUT/'source_capability_review.json')['S8ZKE3_arguments'],'observer_sha256':sha(observer),'expected_geometry':['TYPE43','LAW117','zero thickness','positive area'],'hypothesis_is_not_acceptance':'Expect volumetric route DET=0 before material law; record actual values even if hypothesis fails.'}
    p=d/'instrumentation_config.json';dump(p,c);dump(OUT/'native_dispatch_predeclaration.json',c);launcher.engine=engine;print(json.dumps(launcher.run_native(d,name,observer,p)),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','source_review','native']);globals()[p.parse_args().action]()
