"""Cached native field inspection and stiffness trend; preserve every failed gate."""
from run_aircraft_a24 import *
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import subprocess

def main():
    guard(); dest=OUT/'native_fields_review.json'; assert not dest.exists(); rows=[]; cases=[]
    for d in sorted(OUT.glob('w*/*')):
        if not (d/'review.json').exists():continue
        g=read(d/'generation.json'); r=read(d/'review.json'); cases.append({'revision':d.parent.name,**r})
        xyz=np.asarray(g['nodes_mm']); n=g['name']; native=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name)); assert native
        for p in sorted(set([native[0],native[len(native)//2],native[-1]])):
            ad=OUT/'native_field_audit'/d.parent.name/d.name; ad.mkdir(parents=True,exist_ok=True); v=ad/(p.name+'.vtk'); reused=v.exists()
            if not reused:
                result=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120);v.write_text(result.stdout,encoding='utf-8')
            q=vtk(v.read_text(encoding='utf-8')); order=np.argsort(q['NODE_ID']); ids=q['NODE_ID'].astype(int)[order];pts=q['points'].reshape(-1,3)[order];disp=q['Displacement'].reshape(-1,3)[order];vel=q['Velocity'].reshape(-1,3)[order]
            diff=abs(pts-xyz-disp);bound=printed_bound(pts)+printed_bound(disp)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(pts),abs(disp),abs(xyz)])+1e-8
            checks={'node_ids':bool(np.array_equal(ids,np.arange(1,len(xyz)+1))),'finite':bool(np.isfinite(pts).all() and np.isfinite(vel).all() and np.isfinite(disp).all()),'coordinate_identity_with_printing_bound':bool(np.all(diff<=bound)),'no_eroded_elements':bool(np.all(q['EROSION_STATUS']==1))}
            rows.append({'revision':d.parent.name,'case':d.name,'time_ms':q['time'],'native':rel(p),'native_sha256':streamsha(p),'vtk':rel(v),'vtk_sha256':streamsha(v),'maximum_identity_error_mm':float(diff.max()),'maximum_bound_mm':float(bound.max()),'checks':checks,'pass':all(checks.values()),'reused_conversion':reused})
        print({'field_case':d.name,'samples':len(rows)},flush=True)
    assert len(cases)==45
    dump(dest,{'created_utc':now(),'samples':rows,'cases':len(cases),'pass':all(r['pass'] for r in rows),'printing_precision_explicit':True,'solver_thresholds_unchanged':True,'native_solver_reruns':0,'physical_validation':False})
    stiffness=[]
    for st in [1,10,100]:
        cr=[read(OUT/'w2'/f'CONNECTED_EXTENSION_S{st}_N{n}'/'review.json') for n in [4,8]]
        stiffness.append({'Stfac':st,'cases':cr,'mesh_relative_difference':abs(cr[1]['last_clip_IE_J']-cr[0]['last_clip_IE_J'])/cr[1]['last_clip_IE_J'],'both_reference_gates':all(r['pass'] for r in cr)})
    dump(OUT/'stiffness_review.json',{'created_utc':now(),'rows':stiffness,'selected_for_further_controls':100,'selected_pair_pass':stiffness[-1]['both_reference_gates'] and stiffness[-1]['mesh_relative_difference']<.05,'stiffness_is_numerical_not_material_fit':True,'angular_failure_overrides_selection_for_whole':True})
    dump(OUT/'cached_case_review.json',{'created_utc':now(),'cases':cases,'native_controls':45,'native_balances_passed':sum(r['checks']['native_full_energy_balance'] for r in cases),'individual_sets_passed':sum(r['pass'] for r in cases),'original_failed_gates_preserved':True})
    dump(OUT/'postprocessor_recovery.json',{'created_utc':now(),'angular_reader_json_error':'NumPy bool in refinement checks; converted to Python bool. No native computation or existing result was repeated or changed.','original_script':'angular_audit_before_json_fix.py','corrected_script':rel(ROOT/'wtc1_simulation_v8/scripts/audit_aircraft_a24_angular.py'),'native_generator_error_w2':'S100 axis suffix not accepted by old parser. Preserved empty generation-failure directory; w3 uses explicit parser and new declarations. Six w2 native extension results reused.','native_solver_reruns_A20_A23':0})
    print({'native_field_samples':len(rows),'pass':all(r['pass'] for r in rows),'native_controls':45},flush=True)

if __name__=='__main__':main()
