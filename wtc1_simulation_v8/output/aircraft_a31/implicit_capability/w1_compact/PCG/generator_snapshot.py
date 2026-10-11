"""Separate compact-input probe, preserving the original parser failures."""
from probe_aircraft_a31_implicit import *
import probe_aircraft_a31_implicit as initial
import inspect,ast
OUT=initial.OUT/'w1_compact'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a31_implicit_compact.json'

def declare():
    assert not CFG.exists() and not OUT.exists();assert harness()['Status']=='PASS';OUT.mkdir()
    c=read(initial.CFG);c.update(declared_utc=now(),subscope='existing-binary implicit capability: compact input after preserved parser failure',parent_configuration=rel(initial.CFG),parent_configuration_sha256=streamsha(initial.CFG))
    c['format_repair']={'only_changed_record':'NONLIN numeric parameters, fixed-width80chars -> whitespace-separated23chars','values_unchanged':True,'old_inputs_results_preserved':True,'native_solver_reruns':0,
       'source_diagnosis':'Preserved upstream freimpl.F has CHARACTER TITLE*72 followed by list-directed internal reads including5items for Itol123; original80charrecord ends its fifth item at80. This source snapshot is not proven identical to the installed binary. A new native case tests the inference.',
       'source_url':'https://github.com/gabrielrussell/OpenRadioss/blob/bad6688602d770e019b75773d2d5a48b4f9bd918/engine/source/input/freimpl.F'}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True})
    sources=[initial.OUT/'sources/freimpl.F',initial.OUT/'sources/lectur.F',initial.OUT/'sources/lecinp.F',initial.OUT/'sources/preserved_source_tree.json',initial.OUT/'capability_review.json',Path(initial.__file__)]
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p),'redistribution':'exclude_third_party' if p.suffix=='.F' or p.name=='preserved_source_tree.json' else 'own_evidence'} for p in sources],'native_source_identity_not_claimed':True})
    print({'compact_probe_declared':True,'physical_parameters_unchanged':True},flush=True)

def run():
    guard();s=inspect.getsource(initial.run_one);old="ii(0,123)+ff(1e-6,1e-6,1e-6)";new="'0 123 1e-6 1e-6 1e-6'";assert s.count(old)==1;s=s.replace(old,new);ast.parse(s)
    dump(OUT/'runner_derivation.json',{'created_utc':now(),'parent_source_sha256':streamsha(Path(initial.__file__)),'old':old,'new':new,'derived_source':s,'numerical_options_unchanged':True});exec(compile(s,__file__+'::compact_runner','exec'),globals())
    for case in read(CFG)['implicit']['cases']:run_one(case)
    rows=[read(OUT/x['name']/'review.json') for x in read(CFG)['implicit']['cases']];dump(OUT/'capability_review.json',{'created_utc':now(),'cases':rows,'existing_binary_support_demonstrated':any(x['binary_implicit_completion'] for x in rows),'old_parser_failures_preserved':True,'whole_impact_qualified':False,'installation_or_binary_edits':False});dump(OUT/'harness_after.json',harness())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
