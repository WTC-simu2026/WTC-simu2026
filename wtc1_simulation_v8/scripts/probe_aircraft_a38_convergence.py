"""Target first-step convergence seen in A38 native trace, with fixed physics."""
from diagnose_aircraft_a38 import *
import diagnose_aircraft_a38 as diagnostics
NEW_CASES=[{'name':'FREE_DISPLACEMENT_I','scope':'FREE','mode':'I','dt_ms':.001,'variant':'DISPLACEMENT','end_ms':.1},{'name':'FREE_TRACE_INITIAL_I','scope':'FREE','mode':'I','dt_ms':.001,'variant':'TRACE_INITIAL','end_ms':.004}]

def declare():
 guard();p=OUT/'first_step_convergence_predeclaration.json';assert not p.exists();trace=OUT/'FREE_TRACE_I/phase1/A38_FREE_TRACE_I_0001.out';s=trace.read_text();assert re.search(r'0\s+Y\s+1.000E\+00\s+3.750E-12\s+1.000E\+00\s+C',s)
 dump(p,{'created_utc':now(),'seed':1102063,'parent_configuration_sha256':streamsha(CFG),'cases':NEW_CASES,'trigger':'First native nonlinear iteration accepted at displacement ratio1 and energy ratio1 while force ratio3.75e-12 under criteria123. Determine whether selecting displacement-only criterion changes initial dynamics.','DISPLACEMENT':'Only nonlinear Itol123 to3, tolerance1e-6 unchanged for selected displacement criterion; model/output/binary unchanged. Full original physical gates still used.','TRACE_INITIAL':'Only acquisition of initial stiffness at NC1/IT0 instead ofIT1 and animation every.001ms; same failed 4-step dynamics. Needed observations not present in cached first trace.','before_new_native':True,'per_process_cap_s':180,'physical_data_fit':False,'docs':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_nonlin_engine_r.htm'})

def cards2(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode!='I':return s
 if VARIANT=='DISPLACEMENT':s=s.replace('0 123 1e-6 1e-6 1e-6','0 3 1e-6 1e-6 1e-6')
 elif VARIANT=='TRACE_INITIAL':
  s=s.replace(ff(end)+'\n/TFILE',ff(.004)+'\n/TFILE').replace('/ANIM/DT\n'+ff(0,.01),'/ANIM/DT\n'+ff(0,.001));s='/IMPL/PRINT/NONLIN/1\n/IMPL/PRINT/STIFFNESS\n1e-30 1 0\n'+s
 else:raise ValueError(VARIANT)
 return s

def run():
 global VARIANT
 guard();assert read(OUT/'first_step_convergence_predeclaration.json')['before_new_native'];experiment.install_runner();native37.engine_cards=cards2;rows=[]
 for c in NEW_CASES:
  VARIANT=c['variant'];native37.start_case(c);native37.audit_case(c);rows.append(read(OUT/c['name']/'review.json'))
 dump(OUT/'first_step_convergence_review.json',{'created_utc':now(),'cases':rows,'unchanged_physical_gates':True,'whole_insertion_ready':False})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
