"""Derive own bounded driver from preserved A75, bind new A77 consent and cached reader repair."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import re,ast,json


def main():
    scripts=ROOT/'wtc1_simulation_v8/scripts';old=scripts/'run_aircraft_a75_TYPE7_compatibility.py'
    target=scripts/'run_aircraft_a77_neighbor_policy.py';assert not target.exists()
    s=old.read_text(encoding='utf8')
    s=re.sub(r'AIRCRAFT-A(?:74|75)',lambda m:{'AIRCRAFT-A74':'AIRCRAFT-A76','AIRCRAFT-A75':'AIRCRAFT-A77'}[m.group()],s)
    s=re.sub(r'aircraft_a(?:74|75)',lambda m:{'aircraft_a74':'aircraft_a76','aircraft_a75':'aircraft_a77'}[m.group()],s)
    edits=[("h['RegistryEntries']==193","h['RegistryEntries']==195"),
        ('seed\':1102100','seed\':1102102'),
        ('Oui, exécuter les deux préparations et CHECK conditionnels A75','Oui, exécuter les préparations et CHECK conditionnels A77'),
        ('request_user_input_async/call_2654b9a2913c4ca9a90d3f46179ecaa0/0','request_user_input_async/call_432df3436b51458fb51e0780402fed83/0'),
        ("output/aircraft_a73/preservation_before_metadata.json","output/aircraft_a75/preservation_before_metadata.json"),
        ('for n in [73,74]:','for n in [75,76]:'),
        ("'no_STOPvolume':'STOP' not in s or 'VOLUME' not in s,",
         "'no_STOPvolume':not re.search(r'(?:STOP[^\\n]*(?:VOLUME|AREA)|(?:VOLUME|AREA)[^\\n]*STOP)',s,re.I),")]
    for oldtext,newtext in edits:
        assert s.count(oldtext)==1,oldtext;s=s.replace(oldtext,newtext)
    begin=s.index('def starter_readback(');end=s.index('def run():',begin)
    s=s[:begin]+"from read_aircraft_a77_Starter import read_starter as starter_readback\n\n\n"+s[end:]
    before="    assert sha(ROOT/c['Starter_binary'])==c['Starter_sha256'];return c"
    after="""    assert sha(ROOT/c['Starter_binary'])==c['Starter_sha256']
    assert sha(ROOT/c['prepared_own_reader'])==c['prepared_own_reader_sha256']
    return c"""
    assert s.count(before)==1;s=s.replace(before,after)
    ast.parse(s);target.write_text(s,encoding='utf8',newline='\n')
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a76_proposal.json';review=read(ROOT/'wtc1_simulation_v8/output/aircraft_a76_preparation/own_Starter_reader_preparation_review.json')
    assert read(plan)['prepared_own_reader_sha256']==review['prepared_reader_sha256']
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a77_driver_derivation.json',{'created_utc':now(),
        'source':rel(old),'source_sha256':sha(old),'derived':rel(target),'derived_sha256':sha(target),
        'plan_sha256':sha(plan),'own_reader':review['prepared_reader'],'own_reader_sha256':review['prepared_reader_sha256'],
        'changes':'Bind new A77 authorization/seed/paths; preserve failed A75; use prepared separate-table reader and line-local STOPvolume detection.',
        'same_two_Starter_two_conditional_CHECK_CPU1_cap180':True,'no_Engine_software_patch_compile_install_GPU':True})
    print(json.dumps({'A77_driver_prepared':True,'old_A75_not_modified':True}),flush=True)


if __name__=='__main__':main()
