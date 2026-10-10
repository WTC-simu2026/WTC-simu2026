"""Declare penalty stiffness convergence at short quasi-static loading, not damage fitting."""
from run_aircraft_a24 import ROOT,OUT,read,dump,rel,now,streamsha,harness
import ast

def main():
    nc=ROOT/'wtc1_simulation_v8/data/aircraft_a24_stiffness.json';dest=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a24_stiffness.py';assert not nc.exists() and not dest.exists()
    parent=ROOT/'wtc1_simulation_v8/data/aircraft_a24_lowdamping.json';c=read(parent)
    cases=[f'CONNECTED_EXTENSION_S{s}_N{n}' for s in [1,10,100] for n in [4,8]]+[f'CONNECTED_FREE_ROTATION_S100_{a}' for a in 'XYZ']+['CONNECTED_FREE_TRANSLATION_S100']
    c.update(revision='w2',declared_utc=now(),parent_configuration_sha256=streamsha(parent),
       purpose='Test the intended stiff-connection limit without mass condensation. Stfac1,10,100 are numerical convergence controls, not measured joint strengths or a fit to historical damage.',
       cases={'primitive':[],'paired':cases},stiffness_scaling=[1,10,100],
       loading_duration_ms=.1,physical_reason_for_short_loading='Elastic clip axial wave period about .0035ms; .1ms remains slow relative to this scale. Native energy and endpoint stiffness checks unchanged; dynamic error remains measured.',
       whole_strength_or_geometry_identified=False,old_native_solver_reruns=0)
    c['motion']['prescribed_duration_ms']=.1;c['execution'].update(estimated_minutes=[5,15],per_process_cap_s=600)
    c['changed_since_A23']['only_new_clip_end_ties']='Spot25; positive Visc1e-20 with native readback; Stfac1/10/100 with native readback; unchanged material/mass. Core Spot5 unchanged.'
    dump(nc,c);dump(OUT/'stiffness_guard.json',{'created_utc':now(),'sha256':streamsha(nc),'before_new_w2_cases':True});dump(OUT/'harness_before_w2.json',harness())
    src=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a24_lowdamping.py';s=src.read_text(encoding='utf-8');audit=[]
    replacements=[
      ('data/aircraft_a24_lowdamping.json','data/aircraft_a24_stiffness.json'),
      ("read(OUT/'lowdamping_guard.json')","read(OUT/'stiffness_guard.json')"),
      ('"OUT/\'w1\'"','"OUT/\'w2\'"'),
      ("d=OUT/'w1'/cid","d=OUT/'w2'/cid"),
      ("read(OUT/'w1'/cid/'review.json')","read(OUT/'w2'/cid/'review.json')"),
      ('runner_w1_derivation.json','runner_w2_derivation.json'),
      ('native_case_summary_w1.json','native_case_summary_w2.json'),
      ("duration=.05 if free else 10 if 'ROTATION_' in cid else 1","duration=.05 if free else 10 if 'ROTATION_' in cid else .1"),
      ("duration=10 if 'ROTATION_' in cid else 1","duration=10 if 'ROTATION_' in cid else .1"),
      ("ff(1,1e-20)+' '*20+ii(2)","ff(stfac,1e-20)+' '*20+ii(2)"),
      ("'Stfac':1,'Visc':1e-20","'Stfac':stfac,'Visc':1e-20"),
      ("for old,new in replacements:","s=s.replace(\"guard();c=read(CFG);primitive=\",\"guard();c=read(CFG);stfac=int(re.search('_S(1|10|100)(?:_|$)',cid).group(1));primitive=\")\n    for old,new in replacements:"),
      ("rows.append({'interface':sid,'native_damping':value,'expected':expected,'pass':abs(value-expected)<1e-6*expected})",
       "actual_stiffness=float(re.search(r'STIFFNESS FACTOR.*?([+\\-]?\\d[\\d.]*(?:E[+\\-]\\d+)?)\\s*$',block,re.M).group(1));wanted_stiffness=int(re.search('_S(1|10|100)(?:_|$)',d.name).group(1));rows.append({'interface':sid,'native_damping':value,'expected':expected,'actual_Stfac':actual_stiffness,'wanted_Stfac':wanted_stiffness,'pass':abs(value-expected)<1e-6*expected and actual_stiffness==wanted_stiffness})"),
    ]
    for old,new in replacements:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    ast.parse(s);dest.write_text(s,encoding='utf-8')
    dump(OUT/'stiffness_derivation.json',{'created_utc':now(),'source':rel(src),'source_sha256':streamsha(src),'derived':rel(dest),'derived_sha256':streamsha(dest),'replacements':audit,'old_inputs_outputs_unchanged':True})
    print({'declared':'A24_w2','cases':len(cases),'Stfac':[1,10,100],'short_elastic_ms':.1,'native_parameter_gate':True},flush=True)

if __name__=='__main__':main()
