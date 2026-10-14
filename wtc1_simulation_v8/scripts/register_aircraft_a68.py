"""Register only sealed read-only audit and prepared new measurements; no A69 execution."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a68_check_audit import OUT,CFG,REPORT,HANDOFF,route
import json

def main():
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json') and cycle['pending_iterations']==[]
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    manifest=OUT/'artifact_manifest_r2.json';m=read(manifest)
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256'],r['path']
    assert read(ROOT/'wtc1_simulation_v8/output/aircraft_a69_preparation/independent_preparation_review.json')['pass']
    assert not (ROOT/'wtc1_simulation_v8/output/aircraft_a69').exists()
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A68','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(manifest),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A68',next_iteration='AIRCRAFT-A69',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a68_key_results']=row;state['validated_artifacts'].update(aircraft_a68_report=rel(REPORT),aircraft_a68_results=rel(OUT/'composite_qualification_review.json'),aircraft_a68_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A68'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A68+AIRCRAFT-A69 verified')
    for p,v in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==187
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'files_verified':len(m['files']),'harness':h,
        'new_native':0,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A69'})
    print(json.dumps({'A68_registered':True,'registry_entries':187,'pending_publication_count':1,'A69_native_not_executed':True}),flush=True)

if __name__=='__main__':main()
