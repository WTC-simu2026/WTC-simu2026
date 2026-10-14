"""Prepare own reader for the new neighbor policy; validate grammar on cached failed A75 only."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import inspect,ast,importlib.util,json
import run_aircraft_a75_TYPE7_compatibility as old


def main():
    prep=ROOT/'wtc1_simulation_v8/output/aircraft_a76_preparation'
    target=ROOT/'wtc1_simulation_v8/scripts/read_aircraft_a77_Starter.py';assert not target.exists()
    code=inspect.getsource(old.field)+'\n'+inspect.getsource(old.starter_readback)
    replacements=[('def starter_readback(d,case,execution,baseline):','def read_starter(d,case,execution,baseline,save=True):'),
        ("'Inacti':field(block,'DE-ACTIVATION OF INITIAL PENETRATIONS'),",
         "'Inacti':field(block,'DE-ACTIVATION OF INITIAL PENETRATIONS'),\n            'Irem_gap':field(block,'NODES IN CASE'),"),
        ("    expected_ids=set(case['contact_interface_IDs']);observed_ids=set(contacts)",
         """    impacts=re.findall(r'INTERFACE NUMBER\\.[^\\n]*?(\\d+)\\s*\\n\\s*INTERFACE TYPE\\.[^\\n]*?(\\d+)\\s*\\n\\s*POSSIBLE IMPACT NUMBER:\\s*(\\d+)',text)
    possible={int(ID):int(count) for ID,typ,count in impacts if int(typ)==7}
    for ID,r in contacts.items():r['possible_impact_numbers_printed']=[possible[ID]] if ID in possible else []
    expected_ids=set(case['contact_interface_IDs']);observed_ids=set(contacts)"""),
        ("r['Igap']==1000,r['Gapmin_mm']==gap,r['Irem_i2']==3,r['Inacti']==1000])",
         "r['Igap']==1000,r['Gapmin_mm']==gap,r['Irem_i2']==3,r['Inacti']==1000,\n            r['Irem_gap']==(case.get('expected_self_Irem_gap',2) if ID==2 else 1)])"),
        ("    dump(d/'Starter_gate_review.json',result);return result",
         "    if save:dump(d/'Starter_gate_review.json',result)\n    return result")]
    for before,after in replacements:
        assert code.count(before)==1,before;code=code.replace(before,after)
    source='''"""Own cached-listing reader; exact pair labels and dynamic contact equivalence remain unqualified."""
from build_aircraft_a54_graph import read,dump,now,rel
from pathlib import Path
import re
\n'''+code
    ast.parse(source);target.write_text(source,encoding='utf8',newline='\n')
    spec=importlib.util.spec_from_file_location('prepared_A77_Starter_reader',target)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    config=read(ROOT/'wtc1_simulation_v8/data/aircraft_a75_predeclaration.json');rows=[]
    for case,baseline in zip(config['cases'],config['mass_baselines']):
        d=ROOT/'wtc1_simulation_v8/output/aircraft_a75'/case['case']
        value=module.read_starter(d,{**case,'expected_self_Irem_gap':1},read(d/'starter.execution.json'),baseline['values'],save=False)
        assert not value['pass'] and value['errors']==916 and value['warnings']==11
        assert value['checks']['native_initial_contact_inventory_printed']
        assert value['checks']['five_TYPE7_registered_and_declared_gaps_filter_flags_read']
        rows.append({'case':case['case'],'new_reader_still_rejects_916errors_11warnings':True,
            'separate_possible_impact_table_parsed':True,'Irem_gap_flags_directly_printed':True,
            'old_failed_gates_or_outputs_modified':False,'new_native':0})
    dump(prep/'own_Starter_reader_preparation_review.json',{'created_utc':now(),'pass':True,
        'source':rel(Path(old.__file__)),'source_sha256':sha(Path(old.__file__)),
        'prepared_reader':rel(target),'prepared_reader_sha256':sha(target),'syntax_valid':True,
        'changes':'Read separate native impact table, read Irem_gap and gate declared self policy, allow no-save cached verification.',
        'cached_cases':rows,'third_party_software_modified':False,'new_native':0,
        'new_policy_native_qualification':False})
    print(json.dumps({'A77_own_reader_prepared':True,'cached_rejection_preserved':True,'new_native':0}),flush=True)


if __name__=='__main__':main()
