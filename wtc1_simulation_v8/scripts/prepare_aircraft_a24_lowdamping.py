"""Preserve default damping controls; declare near-zero positive damping and gate native readback."""
from run_aircraft_a24 import ROOT,OUT,CFG,read,dump,rel,now,streamsha,harness
import ast,re

def main():
    nc=ROOT/'wtc1_simulation_v8/data/aircraft_a24_lowdamping.json';dest=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a24_lowdamping.py'
    assert not nc.exists() and not dest.exists()
    d=OUT/'w0/CONNECTED_ROTATION_X';text=(d/'A24_CONNECTED_ROTATION_X_0000.out').read_text();parsed=[]
    for sid in [301,302]:
        block=re.search(r'INTERFACE NUMBER\s*:\s*'+str(sid)+r'\b(.*?)(?=INTERFACE NUMBER|\Z)',text,re.S).group(1)
        value=float(re.search(r'CRITICAL DAMPING FACTOR.*?([+\-]?\d[\d.]*E[+\-]\d+)',block).group(1));assert value==.05;parsed.append({'interface':sid,'input_Visc':0,'native_Visc':value})
    c=read(CFG);c.update(revision='w1',declared_utc=now(),parent_configuration_sha256=streamsha(CFG),
      purpose='Same candidate transmission with positive1e-20 damping to avoid the native zero=>default.05 convention. No mass or inertia compensation; preserve default damping w0 as sensitivity control.',
      damping_readback={'observed_w0':parsed,'source_listing_sha256':streamsha(d/'A24_CONNECTED_ROTATION_X_0000.out'),'requested_w1_positive_coefficient':1e-20,'verify_before_each_Engine':True,'near_zero_not_exact_zero':True},
      old_solver_reruns=0,reuse_reference_cases_from='aircraft_a24/w0',source_generator_sha256=streamsha(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a24.py'))
    c['cases']={'primitive':[],'paired':[cid for cid in c['cases']['paired'] if cid.startswith('CONNECTED_')]}
    c['changed_since_A23']['only_new_clip_end_ties']='Spot25, Stfac1, positive Visc1e-20, Istf2, dsearch.8. Actual damping readback required before Engine. w0 input0 activated native.05 and remains an independent damping sensitivity.'
    c['execution']['estimated_minutes']=[10,20]
    dump(nc,c);dump(OUT/'lowdamping_guard.json',{'created_utc':now(),'sha256':streamsha(nc),'before_new_w1_native_cases':True});dump(OUT/'harness_before_w1.json',harness())
    src=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a24.py';s=src.read_text(encoding='utf-8');audit=[]
    replacements=[
       ('data/aircraft_a24_predeclaration.json','data/aircraft_a24_lowdamping.json'),
       ("read(OUT/'declaration_guard.json')","read(OUT/'lowdamping_guard.json')"),
       ("s=inspect.getsource(A23.run_one);audit=[]","s=inspect.getsource(A23.run_one).replace(\"OUT/'w0'\",\"OUT/'w1'\");audit=[]"),
       ("ff(1,0)+' '*20+ii(2)","ff(1,1e-20)+' '*20+ii(2)"),
       ("'Visc':0,'Istf':2","'Visc':1e-20,'Istf':2"),
       ("d=OUT/'w0'/cid","d=OUT/'w1'/cid"),
       ("read(OUT/'w0'/cid/'review.json')","read(OUT/'w1'/cid/'review.json')"),
       ('runner_derivation.json','runner_w1_derivation.json'),
       ('native_case_summary.json','native_case_summary_w1.json'),
       ("exec(compile(s,__file__+'::derived_run_one','exec'),globals())","s=s.replace(\"        assert execute(RUNTIME/'engine_win64.exe'\",\"        verify_requested_damping(d,n)\\n        assert execute(RUNTIME/'engine_win64.exe'\");exec(compile(s,__file__+'::derived_run_one','exec'),globals())"),
       ("choices=['declare','run']","choices=['run']"),
    ]
    for old,new in replacements:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    helper='''
def verify_requested_damping(d,n):
    expected=read(CFG)['damping_readback']['requested_w1_positive_coefficient'];text=(d/(n+'_0000.out')).read_text();rows=[]
    for sid in [301,302]:
        block=re.search(r'INTERFACE NUMBER\\s*:\\s*'+str(sid)+r'\\b(.*?)(?=INTERFACE NUMBER|\\Z)',text,re.S).group(1)
        value=float(re.search(r'CRITICAL DAMPING FACTOR.*?([+\\-]?\\d[\\d.]*E[+\\-]\\d+)',block).group(1))
        rows.append({'interface':sid,'native_damping':value,'expected':expected,'pass':abs(value-expected)<1e-6*expected})
    dump(d/'requested_damping_gate.json',{'created_utc':now(),'rows':rows,'pass':all(r['pass'] for r in rows),'before_Engine':True})
    assert all(r['pass'] for r in rows),'Native damping readback differs; preserve Starter and stop before Engine'

'''
    s=s.replace("if __name__=='__main__':",helper+"if __name__=='__main__':");ast.parse(s);dest.write_text(s,encoding='utf-8')
    dump(OUT/'lowdamping_derivation.json',{'created_utc':now(),'source':rel(src),'source_sha256':streamsha(src),'derived':rel(dest),'derived_sha256':streamsha(dest),'replacements':audit,'old_inputs_outputs_unmodified':True})
    print({'declared':'A24_w1','new_connected_cases':len(c['cases']['paired']),'reference_cases_reused':9,'requested_damping':1e-20},flush=True)

if __name__=='__main__':main()
