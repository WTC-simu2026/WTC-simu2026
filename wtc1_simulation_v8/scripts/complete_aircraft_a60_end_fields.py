"""Independent final native field completion; preserve the earlier CSV endpoint failure."""
from probe_aircraft_a60 import ROOT,OUT,CFG,RUNTIME,read,dump,sha,now,rel,engine
from probe_aircraft_a37 import vtk
from material_aircraft_a60 import path_values
import re,json,subprocess,time
import numpy as np

def main():
    engine();cfg=read(CFG);raw=read(OUT/'mixed_native_review.json');rows=[]
    dump(OUT/'end_field_review_predeclaration.json',{'created_utc':now(),'reason':'TH cadence ends at0.9999ms although requested end is1ms. Verify the saved final animation clock and field motion instead of treating the last TH sample as Engine completion.','old_CSV_endpoint_failed_gate_preserved':True,'requested_physical_end_ms':1,'end_clock_tolerance_ms':1e-6,'motion_tolerance_mm':cfg['acceptance']['prescribed_motion_mm'],'old_native_Engine_replays':0,'physical_thresholds_unchanged':True})
    for old in raw['cases']:
        case=old['case'];d=OUT/'native'/case['id'];n=read(d/'generation.json')['name'];last=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))[-1]
        start=time.perf_counter();r=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(last)],capture_output=True,check=True,timeout=60);p=d/'final_state.vtk';p.write_bytes(r.stdout)
        dump(d/'final_state_conversion.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':60,'native_animation':rel(last),'animation_sha256':sha(last)})
        field=vtk(r.stdout.decode('utf8'));order=np.argsort(field['NODE_ID']);U=field['Displacement'].reshape(-1,3)[order];expected=path_values(np.array([1.]),case,cfg['cohesive'])[0]
        motion=float(abs(U[4:]-expected).max());end=float(field['time']);checks={key:value for key,value in old['checks'].items() if key!='native_loaded_end_time'}
        checks.update(native_final_field_clock_reaches_requested_end=abs(end-1)<=1e-6,native_final_prescribed_vector_motion=motion<=cfg['acceptance']['prescribed_motion_mm'],native_bottom_supports_fixed=bool(np.all(U[:4]==0)))
        row={'case':case['id'],'initial_CSV_endpoint_gate':old['checks']['native_loaded_end_time'],'native_end_time_ms':end,'maximum_final_motion_error_mm':motion,'checks':checks,'pass':all(checks.values()),'physical_thresholds_unchanged':True,'time_credit_to_whole_impact_s':0};dump(d/'completion_field_review.json',row);rows.append(row)
    additional={k:v for k,v in raw['checks'].items() if k!='all_new_cases_pass'}
    result={'created_utc':now(),'cases':rows,'discretization_checks':additional,'mechanical_witness_domain_pass':all(r['pass'] for r in rows) and all(additional.values()),'initial_failed_CSV_endpoint_gate_retained':True,'TH_clock_not_relabelled':True,'new_whole_impact_credit_s':0,'native_implicit_transfer_ready':False}
    dump(OUT/'mixed_review_with_final_fields.json',result);print(json.dumps({'mixed_domain_pass':result['mechanical_witness_domain_pass'],'final_field_cases':len(rows),'original_CSV_gate_preserved':True}),flush=True)

if __name__=='__main__':main()
