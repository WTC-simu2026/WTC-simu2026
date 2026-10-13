"""Resume saved native contact outputs after supplying required analysis completion metadata."""
from probe_aircraft_a54 import ROOT,OUT,read,dump,sha,now,engine,run_native
from pathlib import Path
import shutil,json
import numpy as np


def main():
    engine();inherited=read(OUT/'contact_controls_predeclaration.json');root=OUT/'contact_controls'
    proof=OUT/'contact_analysis_bridge.json';assert not proof.exists()
    dump(proof,{'created_utc':now(),'reason':'The inherited auditor requires phase1/completion.json, while the new launcher writes completion_review.json. The first native Engine completed normally; the initial analysis skipped conversion and raised StopIteration.',
        'initial_analysis_preserved':True,'old_native_solver_rerun':False,'new_initial_contact_solver_rerun':False,
        'repair':'Supply an explicit completion.json bridge from the saved native execution. Preserve raw review.json and create a separate corrected analysis file.',
        'physical_inputs_or_acceptance_thresholds_changed':False})
    import probe_aircraft_a37 as auditor
    import read_aircraft_a41_newmark as reader
    auditor.OUT=root;auditor.CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json';auditor.guard=lambda:engine()
    original_dump=auditor.dump
    auditor.dump=lambda path,value: original_dump(Path(path).with_name('review_after_completion_metadata.json') if Path(path).name=='review.json' else path,value)
    original_read=reader.read
    reader.OUT=root
    reader.read=lambda path:original_read(Path(path).with_name('review_after_completion_metadata.json') if Path(path).name=='review.json' else path)
    rows=[]
    for row in inherited['cases']:
        case=row['case'];d=root/case['name'];p=d/'phase1'
        if not d.exists():
            p.mkdir(parents=True)
            for entry in row['inputs']:
                source=ROOT/entry['path'];assert sha(source)==entry['sha256']
                target=d/'generation.json' if source.name=='generation.json' else p/source.name
                shutil.copy2(source,target);assert sha(target)==entry['sha256']
            generation=read(d/'generation.json');completion=run_native(p,generation['name'])
            if completion['parent_exit_code']==0 and completion['normal_termination']:
                dump(d/'run_completed.json',{'created_utc':now(),'pass':True,'new_binary_sha256':sha(engine()[1])})
        else:
            completion=read(p/'completion_review.json')
        ok=completion['parent_exit_code']==0 and completion['normal_termination']
        dump(p/'completion.json',{'created_utc':now(),'pass':ok,'exit_ok':completion['parent_exit_code']==0,
            'normal_termination':completion['normal_termination'],'bridged_from':'completion_review.json','no_solver_rerun':True})
        if ok:
            auditor.audit_case(case);result=reader.review(case,True);rows.append(result)
        else:rows.append({'case':case['name'],'pass':False,'reason':'Native Engine incomplete'})
        print(json.dumps({'contact_case':case['name'],'physical_gate_pass':rows[-1]['pass']}),flush=True)
    comparison=[]
    if all(row['pass'] for row in rows):
        histories=[auditor.histories(next((root/row['case']['name']/'phase1').glob('*.csv'))) for row in inherited['cases']]
        tt=histories[0]['time'];tt=tt[tt<=min(h['time'][-1] for h in histories)]
        K0=read(root/inherited['cases'][0]['case']['name']/'generation.json')['kinetic_energy_J']
        tolerance=inherited['acceptance']['half_dt_energy_relative']*K0+inherited['acceptance']['comparison_energy_absolute_J']
        for key in ['KINETIC ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']:
            values=[np.interp(tt,h['time'],h[key])*.001 for h in histories]
            error=float(abs(values[0]-values[1]).max())
            comparison.append({'channel':key,'maximum_difference_J':error,'tolerance_J':tolerance,'pass':error<tolerance})
    dump(root/'contact_review.json',{'created_utc':now(),'cases':rows,'time_step_comparison':comparison,
        'pass':len(rows)==2 and all(row['pass'] for row in rows) and bool(comparison) and all(row['pass'] for row in comparison),
        'raw_missing_metadata_and_secant_field_failures_preserved':True,
        'same_source_defined_Newmark_reader_and_original_physical_thresholds':True,
        'whole_TYPE25_qualified':False,'whole_impact_qualified':False,'new_whole_physical_duration_credit_s':0})


if __name__=='__main__':main()
