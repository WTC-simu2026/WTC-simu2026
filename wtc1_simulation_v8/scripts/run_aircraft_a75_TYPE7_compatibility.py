"""Approved two Starter and at most two conditional CHECKs, A73 Engine unchanged."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from probe_aircraft_a54 import RUNTIME
from run_aircraft_a17 import env
from pathlib import Path
import json,shutil,re,subprocess,time,math
import probe_aircraft_a54 as launcher

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a75'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a75_predeclaration.json'
AUTH=ROOT/'wtc1_simulation_v8/data/aircraft_a75_authorization.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a74_proposal.json'


def declare():
    assert not any(p.exists() for p in [OUT,CFG,AUTH])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A74' and h['RegistryEntries']==193
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==['AIRCRAFT-A74']
    p=read(PLAN);review=ROOT/'wtc1_simulation_v8/output/aircraft_a74_preparation/variant_scope_review.json'
    proposal=ROOT/'wtc1_simulation_v8/output/aircraft_a74_preparation/proposition_compatibilite_contacts_TYPE7.md'
    assert read(review)['pass'] and read(review)['plan_sha256']==sha(PLAN)
    assert sha(ROOT/p['binary'])==p['binary_sha256'] and p['maximum_Starter']==p['maximum_Engine']==2
    for c in p['cases']:
        for row in c['inputs']:
            assert sha(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']
    auth={'created_utc':now(),'explicit_human_authorization':True,
        'answer':'Oui, exécuter les deux préparations et CHECK conditionnels A75',
        'question_item':'request_user_input_async/call_2654b9a2913c4ca9a90d3f46179ecaa0/0',
        'plan_sha256':sha(PLAN),'scope_review_sha256':sha(review),'proposal_sha256':sha(proposal),
        'maximum_Starter':2,'maximum_Engine':2,'CPU_threads':1,'each_cap_s':180,'GPU':False,
        'Engine_only_if_own_Starter_gate_passes':True,'source_Engine_patch':False,'compilation':False,
        'installation':False,'whole_dynamic_extension':False,'prior_budgets_not_reset':True}
    dump(AUTH,auth);OUT.mkdir()
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(OUT/'harness_before.json',h);dump(OUT/'authorization.json',auth)
    mass_paths=[ROOT/'wtc1_simulation_v8/output/aircraft_a49/WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK/mass_review.json',
        ROOT/'wtc1_simulation_v8/output/aircraft_a52/mass_review.json']
    cfg={**p,'iteration':'AIRCRAFT-A75','declared_utc':now(),'seed':1102100,'random_draws':0,
        'authorization':auth,'new_explicit_human_authorization_required':False,
        'Starter_binary':rel(RUNTIME/'starter_win64.exe'),'Starter_sha256':sha(RUNTIME/'starter_win64.exe'),
        'mass_baselines':[{'path':rel(f),'sha256':sha(f),'values':read(f)} for f in mass_paths],
        'immutable_A74_variants_only':True,'new_contact_dynamics_or_full_physical_credit':False}
    dump(CFG,cfg);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_native':True})
    pins={r['path']:r for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a73/preservation_before_metadata.json')['files']}
    for n in [73,74]:
        folder=ROOT/f'wtc1_simulation_v8/output/aircraft_a{n}'
        for row in read(folder/'artifact_manifest.json')['files']:pins[row['path']]=row
        for f in [folder/'artifact_manifest.json',folder/'publication_verification.json']:
            pins[rel(f)]={'path':rel(f),'bytes':f.stat().st_size,'sha256':sha(f)}
    for f in (ROOT/'wtc1_simulation_v8/openradioss_runtime').glob('*/isolated_exec/engine_linux64_gf_ompi'):
        pins[rel(f)]={'path':rel(f),'bytes':f.stat().st_size,'sha256':sha(f)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes']
        rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'all_failed_gates_and_budgets_retained':True})
    print(json.dumps({'A75_declared':True,'maximum_Starter':2,'maximum_Engine_CHECK':2,'no_compile':True}),flush=True)


def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    c=read(CFG);assert c['authorization']['explicit_human_authorization']
    assert sha(PLAN)==c['authorization']['plan_sha256']
    assert sha(ROOT/c['binary'])==c['binary_sha256']
    assert sha(ROOT/c['Starter_binary'])==c['Starter_sha256'];return c


def engine():
    c=guard();binary=ROOT/c['binary'];return binary.parent.parent,binary


def field(block,label):
    lines=[l for l in block.splitlines() if l.strip().startswith(label)]
    if len(lines)!=1:return None
    m=re.search(r'([+\-]?\d+(?:\.\d*)?(?:[EDed][+\-]?\d+)?)\s*$',lines[0])
    return float(m[1].replace('D','E').replace('d','e')) if m else None


def starter_readback(d,case,execution,baseline):
    name=case['name'];listing=d/(name+'_0000.out')
    text=listing.read_text(encoding='utf8',errors='replace') if listing.exists() else ''
    log=(d/'starter.log').read_text(encoding='utf8',errors='replace')
    errors=re.findall(r'(\d+)\s+ERROR\(S\)',log);warnings=re.findall(r'(\d+)\s+WARNING\(S\)',log)
    mass=re.search(r'TOTAL MASS AND MASS CENTER.*?\n\s*([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)',text,re.S)
    added=re.search(r'TOTAL ADDED MASS\s*=\s*([\d.E+\-]+)',text)
    observed_mass=float(mass[1]) if mass else None
    observed_added=float(added[1]) if added else None
    observed_center=[float(v) for v in mass.groups()[1:]] if mass else None
    headings=list(re.finditer(r'^\s*INTERFACE NUMBER\s*:\s*(\d+)\s+([^\n]*)$',text,re.M))
    contacts={}
    for i,h in enumerate(headings):
        if not h[2].startswith('A75_DECLARED_TYPE7_'):continue
        block=text[h.end():headings[i+1].start() if i+1<len(headings) else len(text)]
        contacts[int(h[1])]={'native_title':h[2].strip(),'TYPE7_printed':'TYPE==7' in block,
            'Istf':field(block,'STIFFNESS FORMULATION.'),'Stfac':field(block,'STIFFNESS FACTOR.'),
            'Fric':field(block,'FRICTION FACTOR'),'Igap':field(block,'VARIABLE GAP FLAG'),
            'Gapmin_mm':field(block,'MINIMUM GAP '),'Irem_i2':field(block,'DE-ACTIVATION FLAG IF CONFLICT'),
            'Inacti':field(block,'DE-ACTIVATION OF INITIAL PENETRATIONS'),
            'initial_penetration_factor':field(block,'MAXIMUM INITIAL PENETRATION FACTOR'),
            'possible_impact_numbers_printed':[int(v) for v in re.findall(r'POSSIBLE IMPACT NUMBER:\s*(\d+)',block)],
            'exact_filtered_pair_labels_not_available_from_this_listing_reader':True}
    expected_ids=set(case['contact_interface_IDs']);observed_ids=set(contacts)
    readback_pass=observed_ids==expected_ids
    for ID,r in contacts.items():
        gap=.5 if ID==2 else 5.
        readback_pass=readback_pass and all([r['TYPE7_printed'],r['Istf']==4,r['Stfac']==1,r['Fric']==0,
            r['Igap']==1000,r['Gapmin_mm']==gap,r['Irem_i2']==3,r['Inacti']==1000])
    checks={'normal_and_code0':execution['exit_code']==0 and not execution['timed_out'] and 'NORMAL TERMINATION' in log,
        'errors_zero':bool(errors) and int(errors[-1])==0,
        'warnings_strict_zero':bool(warnings) and int(warnings[-1])==0,
        'mass_same_declared_relative':observed_mass is not None and abs(observed_mass-baseline['mass_g'])<=1e-6*baseline['mass_g'],
        'ADMAS_exact':observed_added==baseline['prescribed_ADMAS_g'],
        'five_TYPE7_registered_and_declared_gaps_filter_flags_read':bool(readback_pass),
        'all_references_valid_no_Starter_error':bool(errors) and int(errors[-1])==0,
        'initial_filter_configuration_read':observed_ids==expected_ids and all(r['Inacti'] is not None for r in contacts.values()),
        'native_initial_contact_inventory_printed':observed_ids==expected_ids and all(r['possible_impact_numbers_printed'] for r in contacts.values()),
        'fresh_initial_restart_exists':(d/(name+'_0000_0001.rst')).exists()}
    result={'created_utc':now(),'pass':bool(all(checks.values())),'checks':checks,
        'failed_checks':[k for k,v in checks.items() if not v],'warnings':int(warnings[-1]) if warnings else None,
        'errors':int(errors[-1]) if errors else None,'mass_g':observed_mass,'center_mm':observed_center,
        'prescribed_ADMAS_g':observed_added,'native_contact_readback':contacts,'listing':rel(listing),
        'full_dynamic_pair_filtering_or_equivalence_qualified':False,'whole_credit_s':0}
    dump(d/'Starter_gate_review.json',result);return result


def run():
    c=guard();assert not list(OUT.rglob('starter_launch_declaration.json'))
    launcher.engine=engine;rows=[];Engine_used=0
    for ordinal,case in enumerate(c['cases'],1):
        guard();assert ordinal<=2 and ordinal==len(list(OUT.rglob('starter_launch_declaration.json')))+1
        d=OUT/case['case'];assert not d.exists();d.mkdir()
        for row in case['inputs']:
            assert sha(ROOT/row['path'])==row['sha256'];target=d/Path(row['path']).name
            shutil.copy2(ROOT/row['path'],target);assert sha(target)==row['sha256']
        dump(d/'starter_launch_declaration.json',{'created_utc':now(),'ordinal':ordinal,'maximum':2,
            'counts_even_if_failure':True,'CPU_threads':1,'GPU':False,'cap_s':180,'config_sha256':sha(CFG)})
        en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1',OPENBLAS_NUM_THREADS='1')
        argv=[str(ROOT/c['Starter_binary']),'-i',case['name']+'_0000.rad','-np','1']
        start=time.perf_counter();code=None;timed=False
        with (d/'starter.log').open('x',encoding='utf8') as f:
            try:code=subprocess.run(argv,cwd=d,env=en,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
            except subprocess.TimeoutExpired:timed=True
        execution={'created_utc':now(),'argv':argv,'exit_code':code,'wall_s':time.perf_counter()-start,
            'timed_out':timed,'CPU_threads':1,'GPU':False,'cap_s':180,'binary_sha256':c['Starter_sha256']}
        dump(d/'starter.execution.json',execution)
        g=starter_readback(d,case,execution,c['mass_baselines'][ordinal-1]['values'])
        row={'case':case['case'],'Starter_pass':g['pass'],'Starter_warnings':g['warnings'],
            'Starter_errors':g['errors'],'Starter_failed_checks':g['failed_checks'],'Engine_executed':False}
        print(json.dumps(row),flush=True)
        if g['pass']:
            Engine_used+=1;assert Engine_used<=2
            dump(d/'Engine_launch_declaration.json',{'created_utc':now(),'ordinal':Engine_used,'maximum':2,
                'CPU_threads':1,'GPU':False,'cap_s':180,'counts_even_if_failure':True,
                'own_Starter_gate_sha256':sha(d/'Starter_gate_review.json'),'binary_sha256':c['binary_sha256']})
            completed=launcher.run_native(d,case['name'])
            listing=d/(case['name']+'_0001.out');s=listing.read_text(encoding='utf8',errors='replace') if listing.exists() else ''
            log=(d/'engine.log').read_text(encoding='utf8',errors='replace')
            checks={'normal_and_code0':completed['parent_exit_code']==0 and completed['normal_termination'],
                'CHECK_started_ended':completed['CHECK_started'] and completed['CHECK_ended'],
                'no_unsupported_ignored_contacts':completed['TYPE25_ignored']==0 and 'IT WILL BE IGNORED' not in log,
                'zero_loading_error':'** ERROR :IMPLICIT LOADING DATA **' not in s,
                'no_STOPvolume':'STOP' not in s or 'VOLUME' not in s,
                'five_TYPE7_in_own_Starter':len(g['native_contact_readback'])==5}
            e={'created_utc':now(),**completed,'checks':checks,'compatibility_control_pass':bool(all(checks.values())),
                'loading_errors':s.count('** ERROR :IMPLICIT LOADING DATA **'),
                'connection_warnings':len(re.findall(r'NODE NUM\.\s*=.*?VAL\.',s)),
                'whole_physical_qualification':False,'whole_credit_s':0}
            dump(d/'Engine_CHECK_review.json',e);row.update(Engine_executed=True,Engine_control_pass=e['compatibility_control_pass'])
        else:
            dump(d/'Engine_skipped.json',{'created_utc':now(),'reason':'Own strict Starter gate failed; conditional Engine not authorized',
                'failed_checks':g['failed_checks'],'counts_as_Engine_launch':False,'slot_not_reassigned':True})
        dump(d/'case_execution_review.json',row);rows.append(row)
    dump(OUT/'native_execution_review.json',{'created_utc':now(),'cases':rows,'new_Starter':2,'new_Engine':Engine_used,
        'Starter_remaining':0,'Engine_conditionally_unused':2-Engine_used,'unused_slots_not_reassigned':True,
        'maximum_four_native_processes_respected':True,'source_patch_compilation_install_GPU':False,
        'whole_dynamic_extension':False,'whole_credit_s':0})
    print(json.dumps({'A75_native_finished':True,'new_Starter':2,'new_Engine':Engine_used,'conditional_UNUSED':2-Engine_used}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['declare','run'])
    globals()[parser.parse_args().action]()
