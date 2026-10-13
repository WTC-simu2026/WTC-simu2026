"""Qualify unaffected explicit and TYPE7 paths on the new binary, no old Engine runs."""
from probe_aircraft_a62_surface import ROOT,OUT,RUNTIME,engine,read,dump,sha,now,rel,run_native
from audit_aircraft_a05 import histories
import shutil,json,time,subprocess,numpy as np,ast,argparse

def explicit():
    engine();root=OUT/'explicit_regressions';assert not root.exists();root.mkdir();old=ROOT/'wtc1_simulation_v8/output/aircraft_a60'
    identifiers=['MIX_B05_L10','MIX_B05_HALF','MIX_B05_L20'];rows=[]
    dump(root/'predeclaration.json',{'created_utc':now(),'iteration':'AIRCRAFT-A62','seed':1102087,'random_draws':0,'cases':identifiers,'scope':'Regression of the new A62 binary: approved change is implicit-only; compare every native channel against sealed accepted A60 mixed outputs.','initial_states_and_cards_unchanged':True,'CSV_precision_comparison_relative_to_channel_peak':6e-7,'literal_bit_comparison_separate':True,'mechanical_acceptance_thresholds_unchanged':True,'old_Engine_runs':0,'each_cap_s':180,'CPU':1,'GPU':False,'counts_towards_maximum12':True})
    for identifier in identifiers:
        prior=old/'native'/identifier;generation=read(prior/'generation.json');name=generation['name'];d=root/identifier;d.mkdir()
        inputs=[prior/(name+'_0000_0001.rst'),prior/(name+'_0001.rad'),prior/(name+'T01.csv')]
        pin=[{'path':rel(p),'sha256':sha(p)} for p in inputs];dump(d/'generation.json',{'created_utc':now(),'name':name,'original_inputs':pin,'new_binary_sha256':sha(engine()[1])})
        for p in inputs[:2]:shutil.copy2(p,d/p.name)
        result=run_native(d,name)
        if result['parent_exit_code']!=0 or not result['normal_termination'] or not result['no_USER_BREAK_or_STOP']:
            rows.append({'case':identifier,'pass':False,'completion':result});continue
        start=time.perf_counter();r=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,check=True,timeout=60);(d/'converter.log').write_bytes(r.stdout+r.stderr);dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':60})
        before=histories(inputs[2]);after=histories(d/(name+'T01.csv'));assert list(before)==list(after)
        tt=after['time'];assert tt[-1]>=before['time'][-1]-2.5e-5
        comparisons=[]
        for key in before:
            reference=np.interp(tt,before['time'],before[key]);error=float(abs(after[key]-reference).max());scale=max(float(abs(before[key]).max()),1e-30)
            comparisons.append({'channel':key,'maximum_difference':error,'peak_normalized_difference':error/scale,'precision_pass':error<=6e-7*scale,'literal_bit_equal':bool(len(tt)==len(before['time']) and np.array_equal(after[key],before[key]))})
        passed=all(c['precision_pass'] for c in comparisons);row={'case':identifier,'pass':passed,'channels':comparisons,'every_channel_literal_bit_equal':all(c['literal_bit_equal'] for c in comparisons),'mechanical_reference_accepted':read(prior/'mixed_review.json')['checks'],'cached_completion_accepted':read(prior/'completion_field_review.json')['checks'],'old_endpoint_failure_preserved':True,'no_relabelling_of_old_physical_pass':True,'new_whole_credit_s':0}
        dump(d/'regression_review.json',row);rows.append(row);print(json.dumps({'explicit_regression':identifier,'pass':passed,'literal_bit_equal':row['every_channel_literal_bit_equal']}),flush=True)
    dump(root/'regression_review.json',{'created_utc':now(),'pass':len(rows)==3 and all(r['pass'] for r in rows),'cases':rows,'implicit_cohesion_pass_not_inferred':True,'new_whole_credit_s':0})

# Reuse only the audited TYPE7 contact procedure, with A62 launch accounting.
source=(ROOT/'wtc1_simulation_v8/scripts/regress_aircraft_a57.py').read_text(encoding='utf8')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='contact')
s=ast.get_source_segment(source,node).replace('AIRCRAFT-A57','AIRCRAFT-A62').replace('1102082','1102087')
exec(compile(s,__file__,'exec'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['explicit','contact']);globals()[p.parse_args().action]()
