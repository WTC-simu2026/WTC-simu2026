"""Declare native shell rotational output and angular momentum controls before whole transfer."""
from run_aircraft_a24 import ROOT,OUT,read,dump,rel,now,streamsha,harness
import ast,urllib.request

def main():
    nc=ROOT/'wtc1_simulation_v8/data/aircraft_a24_angular.json';dest=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a24_angular.py';assert not nc.exists() and not dest.exists()
    parent=ROOT/'wtc1_simulation_v8/data/aircraft_a24_stiffness.json';c=read(parent)
    cases=[f'{kind}_FREE_ROTATION_S100_{a}' for a in 'XYZ' for kind in ['REFERENCE','CONNECTED']]+[f'{kind}_FREE_TRANSLATION_S100' for kind in ['REFERENCE','CONNECTED']]+[f'{kind}_FREE_ROTATION_S100_Y_HALF' for kind in ['REFERENCE','CONNECTED']]
    c.update(revision='w3',declared_utc=now(),parent_configuration_sha256=streamsha(parent),cases={'primitive':[],'paired':cases},
      purpose='Before whole insertion, measure physical angular momentum including actual native shell rotational velocities. Translation-only output could not prove this. Stfac100 candidate and reference, native9-field output; also an effective shorter time step control on freeY.',
      angular_reference={'translational':'actual lumped masses, actual nodal positions and velocities','rotational':'physical shell through-thickness inertia m*t^2/12 transverse to current shell normal, t.5mm; no arbitrary scalar RKE term','SI_conversion_g_mm2_per_ms':1e-6,'global_conservation_fraction':.002,'paired_added_conservation_fraction':.02,'absolute_kg_m2_s':1e-9,'baseline_core_Spot5_retained':True,'native_scalar_RKE_not_used_to_repair_reference':True},
      necessary_observation_repeats_of_A24_reference_scenarios=4,old_A20_A23_solver_reruns=0,
      w2_generation_failure='S100 was placed between ROTATION and axis; old axis parser expected immediate XYZ. Input generation of first free case stopped before Starter. All six completed stiffness witnesses retained and reused.',
      half_step_cap_ms=.0000005,all_previous_thresholds_retained=True)
    c['execution'].update(estimated_minutes=[3,8]);dump(nc,c);dump(OUT/'angular_guard.json',{'created_utc':now(),'sha256':streamsha(nc),'before_new_w3_controls':True});dump(OUT/'harness_before_w3.json',harness())
    failed=OUT/'w2/CONNECTED_FREE_ROTATION_S100_X';assert failed.exists() and not (failed/'starter.log').exists();dump(failed/'retained_generation_failure.json',{'created_utc':now(),'native_Starter_or_Engine_not_executed':True,'error':'old axis regex did not allow S100 between ROTATION and X','completed_six_w2_cases_unchanged':True,'next':'new w3 declaration includes proper axis parser and native rotational observation'})
    src=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a24_stiffness.py';s=src.read_text(encoding='utf-8');audit=[]
    replacements=[
      ('data/aircraft_a24_stiffness.json','data/aircraft_a24_angular.json'),
      ("read(OUT/'stiffness_guard.json')","read(OUT/'angular_guard.json')"),
      ('"OUT/\'w2\'"','"OUT/\'w3\'"'),
      ("d=OUT/'w2'/cid","d=OUT/'w3'/cid"),
      ("read(OUT/'w2'/cid/'review.json')","read(OUT/'w3'/cid/'review.json')"),
      ('runner_w2_derivation.json','runner_w3_derivation.json'),
      ('native_case_summary_w2.json','native_case_summary_w3.json'),
      ("re.search('ROTATION_([XYZ])',cid)","re.search('ROTATION_(?:S(?:1|10|100)_)?([XYZ])',cid)"),
      ('ff(.0000125,.0000125) if','ff(.0000005,.0000005) if'),
      ('assert len(keys)==6*len(xyz)','assert len(keys)==9*len(xyz)'),
      ('reshape(len(T),len(xyz),6)','reshape(len(T),len(xyz),9)'),
      ('V=node[:,:,3:]','V=node[:,:,3:6];W=node[:,:,6:9]'),
      ('velocities_m_s=V,momentum_Ns=P','velocities_m_s=V,angular_velocity_rad_ms=W,momentum_Ns=P'),
      ('if g[\'free\']:\n        checks.update',"if g['free']:\n        checks['initial_shell_rotational_velocity_readback']=bool(abs(W[0,np.asarray(g['main_node_ids'])-1]-np.asarray(g['initial_omega_rad_ms'])).max()<1e-6)\n        checks.update"),
      ("exec(compile(s,__file__+'::derived_run_one','exec'),globals())","s=s.replace(\"['DX','DY','DZ','VX','VY','VZ']\",\"['DX','DY','DZ','VX','VY','VZ','VRX','VRY','VRZ']\");exec(compile(s,__file__+'::derived_run_one','exec'),globals())"),
      ('def verify_requested_damping(d,n):\n',"def verify_requested_damping(d,n):\n    if not read(d/'generation.json')['connected']:\n        dump(d/'requested_damping_gate.json',{'created_utc':now(),'root_not_present':True,'pass':True,'before_Engine':True});return\n"),
    ]
    for old,new in replacements:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    ast.parse(s);dest.write_text(s,encoding='utf-8');dump(OUT/'angular_derivation.json',{'created_utc':now(),'source':rel(src),'source_sha256':streamsha(src),'derived':rel(dest),'derived_sha256':streamsha(dest),'changes':audit,'no_prior_native_result_overwritten':True})
    url='https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm';p=OUT/'sources/th_node.html';assert not p.exists();p.write_bytes(urllib.request.urlopen(url,timeout=40).read());dump(OUT/'angular_source_manifest.json',{'url':url,'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party','requested_native_fields':['VRX','VRY','VRZ']})
    print({'declared':'A24_w3','cases':len(cases),'native_rotational_fields':3,'reference_observation_repeats':4,'half_cap_ms':.0000005},flush=True)

if __name__=='__main__':main()
