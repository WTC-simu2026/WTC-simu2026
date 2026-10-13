"""New bounded question: obtain nonlinear iteration diagnostics for A62 T=0 stop."""
from probe_aircraft_a62_surface import ROOT,OUT,engine,read,dump,sha,now,rel,run_native
import shutil,json

def main():
    engine();original=OUT/'native/ELASTIC_NORMAL';d=OUT/'NEWTON_LOG_NORMAL';assert not d.exists();d.mkdir()
    name=read(original/'generation.json')['name'];initial=original/(name+'_0000_0001.rst');cards=original/(name+'_0001.rad')
    shutil.copy2(initial,d/initial.name);text=cards.read_text(encoding='utf8');new='/IMPL/PRINT/NONLIN/1\n'+text;(d/cards.name).write_text(new,encoding='utf8')
    dump(d/'predeclaration.json',{'created_utc':now(),'iteration':'AIRCRAFT-A62','seed':1102087,'random_draws':0,'purpose':'First A62 normal witness now passes the volumetric stop but cuts dt at T0; expose nonlinear diagnostics only, no mechanical or tolerance change.','original_initial_state':rel(initial),'sha256':sha(initial),'original_cards_sha256':sha(cards),'only_added_card':'/IMPL/PRINT/NONLIN/1','source_and_solver_unchanged':True,'original_failed_run_preserved':True,'cap_s':180,'CPU':1,'GPU':False,'counts_towards_maximum12':True})
    result=run_native(d,name);dump(OUT/'Newton_log_execution_review.json',{'created_utc':now(),'result':result,'mechanical_qualification_not_inferred':True});print(json.dumps(result),flush=True)

if __name__=='__main__':main()
