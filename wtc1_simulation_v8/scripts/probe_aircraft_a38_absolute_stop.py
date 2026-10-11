"""Test the pinned nonlinear driver's absolute-residual shortcut, without a rebuild."""
from probe_aircraft_a38 import *
import probe_aircraft_a38 as experiment

CASE={'name':'FREE_TIGHT_I','scope':'FREE','mode':'I','dt_ms':.001,'variant':'TIGHT','end_ms':.1}

def declare():
 guard();p=OUT/'absolute_stop_predeclaration.json';assert not p.exists();h=harness();assert h['Status']=='PASS'
 files=['engine/source/implicit/nl_solv.F','engine/source/implicit/imp_init.F','engine/source/implicit/imp_dyna.F','engine/source/implicit/imp_solv.F']
 dump(p,{'created_utc':now(),'seed':1102063,'random_draws':0,'parent_configuration_sha256':streamsha(CFG),'case':CASE,'before_new_native':True,'harness_before':h,'source_commit':build.PIN,'source_files':[{'path':rel(build.CAND/'source'/f),'sha256':streamsha(build.CAND/'source'/f),'url':f'https://github.com/gabrielrussell/OpenRadioss/blob/{build.PIN}/{f}'} for f in files],'trigger':'nl_solv.F192-211 returns at IT0 when R01*NL_TOL<=EM12 and NL_TOL>EM10 and IDIV/=10. The cached first trace has R01=3.750E-12. This shortcut precedes CRIT_ITE and explains why criterion3 alone did not suppress the trace. Its causal role in erroneous free dynamics still needs a native test.','numeric_change':{'nonlinear_tolerances_before':[1e-6]*3,'nonlinear_tolerances_after':[1e-11]*3,'reason':'Disable the source shortcut guard NL_TOL>EM10 by stricter relative tolerance; no physical threshold relaxed.','linear_tolerance':1e-8,'same_Newmark_gamma_beta':[.5,.25],'same_MUMPS':True,'same_dt_ms':.001},'acquisition_change':'Nonlinear trace and native animation every .001ms, to inspect initial steps and endpoint.','physical_inputs_changed':False,'physical_gates_changed':False,'new_build_or_installation':False,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'conditional_next':'Only a passing complete free witness permits a new declared half-step and contact qualification in A39; this experiment alone does not qualify the whole model.'})
 print({'absolute_stop_declared':True},flush=True)

def cards_tight(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode=='I':
  assert '0 123 1e-6 1e-6 1e-6' in s
  s=s.replace('0 123 1e-6 1e-6 1e-6','0 123 1e-11 1e-11 1e-11').replace('/ANIM/DT\n'+ff(0,.01),'/ANIM/DT\n'+ff(0,.001))
  s='/IMPL/PRINT/NONLIN/1\n'+s
 return s

def run():
 guard();assert read(OUT/'absolute_stop_predeclaration.json')['before_new_native'];experiment.install_runner();native37.engine_cards=cards_tight
 native37.start_case(CASE);native37.audit_case(CASE);r=read(OUT/CASE['name']/'review.json')
 dump(OUT/'absolute_stop_review.json',{'created_utc':now(),'cases':[r],'unchanged_physical_gates':True,'whole_insertion_ready':False})
 print({'tight_free_pass':r['pass'],'checks':r['checks']},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
