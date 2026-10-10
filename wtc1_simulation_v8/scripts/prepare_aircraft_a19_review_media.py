"""Derive new A19 reviewers/renderers while preserving every older script."""
from run_aircraft_a19_whole import *

def main():
    whole_guard();base=ROOT/'wtc1_simulation_v8/scripts';dst=base/'review_aircraft_a19.py';assert not dst.exists()
    s=(base/'review_aircraft_a18.py').read_text(encoding='utf-8').replace('from run_aircraft_a18 import *','from run_aircraft_a18 import *\nfrom run_aircraft_a19_whole import OUT,WCFG as CFG,WCASE as CASE,SOURCE,whole_guard as guard')
    s=s.replace("'cohesive_expected_nine_channels'=", "'cohesive_expected_four_channels'=")
    s=s.replace("checks['cohesive_expected_nine_channels']=len(cohkeys)==9","checks['cohesive_expected_four_channels']=len(cohkeys)==4")
    s=s.replace("'iteration':'AIRCRAFT-A18'","'iteration':'AIRCRAFT-A19'")
    dst.write_text(s,encoding='utf-8')
    dst=ROOT/'wtc1_3d_v4/scripts/render_aircraft_a19.py';assert not dst.exists()
    s=(ROOT/'wtc1_3d_v4/scripts/render_aircraft_a18.py').read_text(encoding='utf-8').replace('fresh A18','fresh A19').replace('aircraft_a18','aircraft_a19').replace('aircraft_a19_predeclaration.json','aircraft_a19_whole_declaration.json').replace("OUT/'declaration_guard.json'","OUT/'whole_declaration_guard.json'").replace('A18_exact_native_poses','A19_exact_native_poses')
    dst.write_text(s,encoding='utf-8')
    dst=base/'encode_aircraft_a19.py';assert not dst.exists()
    s=(base/'encode_aircraft_a18.py').read_text(encoding='utf-8').replace('from run_aircraft_a18 import ROOT,OUT,CFG,read,dump,now,guard,execute,env,streamsha','from run_aircraft_a19_whole import ROOT,OUT,WCFG as CFG,read,dump,now,whole_guard as guard,env,streamsha\nfrom run_aircraft_a17 import execute')
    s=s.replace('APERCU_A18_20ms_ralenti','APERCU_A19_20ms_ralenti')
    s=s.replace("c=read(CFG)['video'];d=OUT/'video'", "c=read(CFG)['video'];case_review=read(ROOT/c['source']/'review.json');ener_review=read(OUT/'whole_negative_energy_diagnostic.json');energy_label='bilan local réussi' if case_review['checks']['local_energy'] and ener_review['expected_nonnegative_pass'] else 'bilan énergétique échoué';d=OUT/'video'")
    s=s.replace('bilan énergétique échoué · modèle non validé', '{energy_label} · modèle non validé')
    dst.write_text(s,encoding='utf-8');print({'new_review_renderer_encoder_prepared':True,'old_scripts_unchanged':True},flush=True)

if __name__=='__main__':main()
