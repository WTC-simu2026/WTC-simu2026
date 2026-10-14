"""Correct two prepared artifact names before declaration; retain unrun R0 driver."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import ast,json


def main():
    source=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a77_neighbor_policy.py'
    target=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a77_neighbor_policy_r1.py'
    assert not target.exists() and not (ROOT/'wtc1_simulation_v8/data/aircraft_a77_predeclaration.json').exists()
    s=source.read_text(encoding='utf8')
    changes=[('aircraft_a76_preparation/variant_scope_review.json','aircraft_a76_preparation/neighbor_policy_scope_review.json'),
        ('aircraft_a76_preparation/proposition_compatibilite_contacts_TYPE7.md','aircraft_a76_preparation/proposition_filtrage_voisinage_local_TYPE7.md'),
        ('immutable_A74_variants_only','immutable_A76_variants_only'),('A75_declared','A77_declared'),('A75_native_finished','A77_native_finished')]
    for before,after in changes:
        assert s.count(before)==1,before;s=s.replace(before,after)
    ast.parse(s);target.write_text(s,encoding='utf8',newline='\n')
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a77_driver_derivation_r1.json',{'created_utc':now(),
        'source':rel(source),'source_sha256':sha(source),'derived':rel(target),'derived_sha256':sha(target),
        'changes':'Correct two existing A76 artifact basenames and labels before declaration; same authorized inputs/readers/budget.',
        'old_R0_unrun_and_preserved':True,'new_native':0,'source_Engine_changed':False})
    print(json.dumps({'A77_driver_R1_ready':True,'new_native':0}),flush=True)


if __name__=='__main__':main()
