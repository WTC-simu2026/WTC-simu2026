"""Prepare five scalar reads at the existing observer stop; no new native probe or software build."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import ast,json

def main():
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a72_proposal.json';p=read(plan);prep=ROOT/'wtc1_simulation_v8/output/aircraft_a72_preparation'
    source=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a71_check_linux.py';dest=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a73_context_linux.py'
    assert not dest.exists();s=source.read_text(encoding='utf8').replace('new_A71_explicit_human_consent','new_A73_explicit_human_consent')
    marker="                a=args(r,15);n=i32(pid,a[1]);assert 0<n<=300000";assert s.count(marker)==1
    extra='''                context={}
                for label,description in c['native_globals'].items():
                    symbol=c['global_symbols'][description['symbol']]
                    width=8 if description['kind']=='f64' else 4
                    assert 0<=description['byte_offset'] and description['byte_offset']+width<=symbol['bytes']
                    address=base+symbol['offset']+description['byte_offset']
                    value=bulk(address,1,'d' if description['kind']=='f64' else 'i')[0]
                    context[label]=value if not isinstance(value,float) or math.isfinite(value) else repr(value)
                events.append({'native_CHECK_context':context,'scalar_reads_only_no_native_data_write':True})
'''
    s=s.replace(marker,marker+'\n'+extra.rstrip('\n'));ast.parse(s)
    dest.write_text(s,encoding='utf8',newline='\n')
    supplementary=ROOT/'wtc1_simulation_v8/data/aircraft_a72_observer_plan.json'
    dump(supplementary,{'created_utc':now(),'main_plan':rel(plan),'main_plan_sha256':sha(plan),'inherited_observer':rel(source),'inherited_sha256':sha(source),
        'prepared_observer':rel(dest),'prepared_observer_sha256':sha(dest),'native_globals':p['controls']['observe_native_globals'],
        'global_symbols_must_be_resolved_from_new_A73_binary':True,'per_symbol_range_guards_required':True,'same_existing_five_CHECK_native_runs_no_extra_process':True,
        'memory_read_only_and_same_hardware_breakpoint_contract':True,'new_native':0,'native_runtime_qualification':False})
    dump(prep/'observer_preparation_review.json',{'created_utc':now(),'pass':True,'syntax_valid':True,'own_observer_source_hash':sha(dest),
        'scalar_fields':5,'all_previous_memory_and_budget_guards_retained':True,'source_Engine_not_modified':True,'new_native':0,
        'additional_parent_breakpoints_or_software_installation':False,'main_plan_unchanged':sha(plan)==read(supplementary)['main_plan_sha256']})
    print(json.dumps({'A73_observer_prepared_only':True,'five_scalar_fields':True,'new_native':0}),flush=True)

if __name__=='__main__':main()
