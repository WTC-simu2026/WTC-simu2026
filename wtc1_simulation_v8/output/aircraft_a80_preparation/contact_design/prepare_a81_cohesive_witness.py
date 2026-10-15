"""Prepare A81 only: no process launch, source edit, compilation or native run."""
from pathlib import Path
import hashlib, json, math

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'witness_preparation'
BASE = ROOT / 'wtc1_simulation_v8/output/aircraft_a67/native/FREE_Ismstr4'
WHOLE = ROOT / 'wtc1_simulation_v8/output/aircraft_a79/SELF_PAIR_PRINT/A79_SELF_PAIR_PRINT_0000.rad'
NAME = 'A81_COHESIVE_COMPRESSION_PARTIAL_OPEN_RECLOSE'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def blocks(text):
    result = {}
    key = None
    for line in text.splitlines():
        if line.startswith('/'):
            key = line
            assert key not in result, key
            result[key] = []
        elif key is not None:
            result[key].append(line)
    return result

def write(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(data)

def dump(path, data):
    write(path, json.dumps(data, ensure_ascii=True, indent=2) + '\n')

def main():
    assert not OUT.exists(), 'preserve old preparation'
    OUT.mkdir()
    f = lambda *v: ''.join(f'{x:20.12g}' for x in v)
    i = lambda *v: ''.join(f'{x:10d}' for x in v)
    base0 = BASE / 'A67_FREE_Ismstr4_0000.rad'
    base1 = BASE / 'A67_FREE_Ismstr4_0001.rad'
    b = blocks(base0.read_text(encoding='utf-8-sig'))
    w = blocks(WHOLE.read_text(encoding='utf-8-sig'))
    assert b['/MAT/LAW117/1'][1:] == w['/MAT/LAW117/117'][1:]
    assert b['/PROP/TYPE43/1'][1:] == w['/PROP/TYPE43/117'][1:]
    dt = .000125
    end = .65
    stop = end + dt/2
    knots = [(0.,0.),(.08,-.05),(.10,-.05),(.18,0.),(.20,0.),(.40,.30),(.42,.30),(.62,-.05),(.65,-.05),(.651,-.05)]
    def displacement(t):
        for (a,x),(z,y) in zip(knots, knots[1:]):
            if t <= z:
                q = min(1., max(0., (t-a)/(z-a)))
                smooth = 10*q**3 - 15*q**4 + 6*q**5
                return x+(y-x)*smooth
        return knots[-1][1]
    rows = ['#RADIOSS STARTER']
    for key, lines in b.items():
        if key.startswith('/INIVEL/') or key == '/END':
            continue
        rows.append(key)
        if key in ['/BEGIN','/TITLE']:
            lines = [NAME] + lines[1:]
        rows += lines
    rows += ['/FUNCT/92','TOP_Z_COMPRESSION_OPEN_RECLOSE']
    samples = [(n*dt/2, displacement(n*dt/2)) for n in range(int(round(.651/(dt/2)))+1)]
    rows += [f(t,x) for t,x in samples]
    rows += ['/IMPDISP/92','TOP_Z_ONLY_XY_FREE',i(92)+f'{"Z":>10}'+i(0,0,2)+' '*10+i(0),f(1,1,0,1e30)]
    rows += ['/TH/BRIC/10','COHESIVE_STATUS_STRESS_USER_FIELDS', ''.join(f'{q:>10}' for q in ['OFF','SZ','USR1','USR4','USR5','USR6','USR9','USR12']),i(1)]
    rows += ['/TH/NODE/11','ALL_NODE_NORMAL_ACCELERATION',f'{"AZ":>10}']+[i(j,0) for j in range(1,9)]
    rows += ['/END']
    input0 = '\n'.join(rows)+'\n'
    e = blocks(base1.read_text(encoding='utf-8-sig'))
    engine = []
    for key, lines in e.items():
        if key.startswith('/RUN/'):
            key = f'/RUN/{NAME}/1'; lines = [f(stop)]
        elif key == '/IMPL/DT/STOP':
            lines = [f(dt,dt)]
        elif key == '/ANIM/DT':
            lines = [f(0,dt/2)]
        elif key == '/TFILE/4':
            lines = [f(dt/2)]
        elif key.startswith('/PRINT/'):
            key = '/PRINT/-1/1'
        engine += [key]+lines
    engine += ['/ANIM/BRICK/OFF','/ANIM/BRICK/USR1','/ANIM/BRICK/USR4','/ANIM/BRICK/USR5','/ANIM/BRICK/USR6','/ANIM/BRICK/USR9','/ANIM/BRICK/USR12']
    input1 = '\n'.join(engine)+'\n'
    p0 = OUT/(NAME+'_0000.rad'); p1 = OUT/(NAME+'_0001.rad')
    write(p0,input0); write(p1,input1)
    bb = blocks(input0); ee = blocks(input1)
    checks = {
      'native_runs_zero':True,
      'exact_A79_material_numeric_lines':bb['/MAT/LAW117/1'][1:]==w['/MAT/LAW117/117'][1:],
      'exact_A79_property_numeric_lines':bb['/PROP/TYPE43/1'][1:]==w['/PROP/TYPE43/117'][1:],
      'exact_A67_nodes':bb['/NODE']==b['/NODE'],
      'exact_A67_brick':bb['/BRICK/1']==b['/BRICK/1'],
      'exact_A67_instrument_ADMAS':bb['/ADMAS/5/1']==b['/ADMAS/5/1'],
      'all_8_nodes_1g_each':len(bb['/ADMAS/5/1'][1:])==8 and all(float(x[:20])==1 for x in bb['/ADMAS/5/1'][1:]),
      'bottom_fixed_top_rotations_fixed_XY_free':bb['/BCS/1']==b['/BCS/1'] and bb['/BCS/2']==b['/BCS/2'],
      'top_Z_prescribed_only':sum(k.startswith('/IMPDISP/') for k in bb)==1 and bb['/IMPDISP/92'][1][10:20].strip()=='Z',
      'no_general_contact':not any(k.startswith('/INTER/') for k in bb),
      'no_initial_velocity':not any(k.startswith('/INIVEL/') for k in bb),
      'same_Newmark':ee['/IMPL/DYNA/2']==e['/IMPL/DYNA/2'],
      'same_nonlinear_tolerances':ee['/IMPL/NONLIN/1']==e['/IMPL/NONLIN/1'],
      'same_linear_solver':ee['/IMPL/SOLVER/2']==e['/IMPL/SOLVER/2'],
      'same_dt_cap_as_A67':float(ee['/IMPL/DTINI'][0])==dt,
      'fixed_dt_or_stop':list(map(float,ee['/IMPL/DT/STOP'][0].split()))==[dt,dt],
      'TH_and_ANIM_half_dt':float(ee['/TFILE/4'][0])==dt/2 and list(map(float,ee['/ANIM/DT'][0].split()))==[0,dt/2],
      'maximum_opening_less_than_gap':max(x for _,x in samples)<.5 and math.isclose(max(x for _,x in samples),.3),
      'terminal_negative_closure':math.isclose(displacement(.65),-.05),
      'no_new_material_parameters':len(bb['/MAT/LAW117/1'])==len(b['/MAT/LAW117/1']),
    }
    assert all(checks.values()), checks
    starter=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64/starter_win64.exe'
    binary=ROOT/'wtc1_simulation_v8/openradioss_runtime/a73_CHECK_context_candidate/isolated_exec/engine_linux64_gf_ompi'
    assert sha(starter)=='961eca1640c321b0cb4893c8481942e5162e89ea292d64e964deea1b5ead96d6'
    assert sha(binary)=='09a2f856d0eddb13ba56c80c578a12d058cb2cee1e403d46074b1b77b29aa158'
    cfg={
      'iteration':'AIRCRAFT-A81_PROPOSAL','status':'prepared_not_authorized_not_run','seed':1102092,'random_draws':0,
      'name':NAME,'new_native_started':0,'maximum_native_processes':2,'Starter':1,'Engine_conditional':1,
      'cpu':1,'each_cap_s':180,'GPU':False,'source_patch':False,'compile':False,'installation':False,'whole_impact_extension':False,
      'expected_total_minutes':[1,5],'purpose':'Observe cohesive compression, rupture below nominal contact gap, and reclosure after rupture before any contact lifecycle development.',
      'units':{'mass':'g','length':'mm','time':'ms','force':'N','stress':'N/mm2','cohesive_stiffness':'N/mm3','energy':'Nmm','energy_to_J':.001},
      'geometry':'A67 FREE_Ismstr4 eight-node zero-height square10x10mm, oneTYPE43 brick, currentA79LAW117 numerical card',
      'area_mm2':100,'instrument_nodal_masses_g':[1]*8,'instrument_mass_g':8,'cohesive_area_density_g_mm2':1e-20,'whole_mass_compensation':False,
      'material':{'LAW':117,'EN_N_mm3':4400,'ET_N_mm3':800,'TN_MPa':450,'TT_MPa':100,'GI_N_mm':50,'GII_N_mm':50,'Imass':1,'Idel':4,'Irupt':1,'Ismstr':4,'true_thickness':0},
      'conditional_documented_pure_mode_I_reference':{'initiation_mm':450/4400,'failure_mm':2*50/450,'fracture_work_Nmm':100*50,'intact_compression_force_magnitude_at_minus005_N':100*4400*.05,'nominal_contact_gap_mm_for_comparison_only_not_a_contact_card':.5},
      'load':{'top_Z_only':True,'top_XY_free':True,'bottom_fixed':True,'knots_ms_mm':knots,'interpolation':'sampledC2quintic transitions; FUNCT uses native linear interpolation between the dt/2 tabulated samples','no_general_contact':True},
      'time':{'target_ms':end,'RUN_stop_ms':stop,'dt_cap_ms':dt,'dt_min_ms':dt,'dt_reduction_causes_stop':True,'TH_ms':dt/2,'ANIM_ms':dt/2,'maximum_nominal_accepted_steps_before_one_step_overshoot':5201},
      'Starter_gate':{'normal_exit_required':True,'syntax_reference_mass_and_property_checks_required':True,'unclassified_errors_or_warnings_block_Engine':True,'known_generic_ISOLID0_informational_message_not_relabelled_warning':True,'native_mat_defaults_must_be_recorded_if_printed':True,'conditional_Engine_not_reassigned_on_failure':True},
      'observation_gate':{'all_actual_accepted_steps_required':True,'saved_actual_state_at_target_required':True,'fields':['all8DX_DY_DZ_VX_VY_VZ_REACX_REACY_REACZ_AZ','partIE_KE_HE_PW','brickOFF_SZ','brickUSR1_USR4_USR5_USR6_USR9_USR12_TH_and_ANIM'],'USR_population_not_assumed':True,'zero_or_absent_user_outputs_not_damage_zero':True,'if_output_population_or_domain_unqualified':'observation_gate_fail_preserve_no_retry','post_deletion_missing_fields_not_interpreted_as_healing':True},
      'physical_gates_separate_from_observation':{'reference_force_and_damage_curve_required':True,'fixed_bottom_reaction_is_independent_cohesive_force_measurement':True,'top_reaction_must_separate_prescribed_inertia_using_measured_acceleration':True,'action_reaction_plus_inertia_and_external_work_balance_required':True,'no_initial_spurious_impulse_or_energy_required':True,'no_nonphysical_healing_or_missing_mass_concealment':True,'failure_before_half_mm_and_reclosure_reaction_recorded_not_assumed':True,'do_not_claim_contact_validated_from_absent_contact':True,'A67_small_elastic_thresholds_preserved_not_silently_relaxed':True,'new_non_linear_qualification_not_inferred_from_exit0':True},
      'observation_not_physical_qualification':True,'constitutive_failure_unknown_in_current_native_engine':True,'contact_policy_WAITING_until_gap_exit_not_retained':True,
      'source_limit':'Pinned software source and official documentation motivate formulas/defaults; identity with WindowsStarter binary is not assumed; native material/default observations remain required.',
      'inputs':[{'path':p.name,'sha256':sha(p)} for p in [p0,p1]],
      'sources':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)} for p in [base0,base1,WHOLE]],
      'unchanged_software':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)} for p in [starter,binary]],
      'source_evidence':['starter/source/materials/mat/mat117/hm_read_mat117.F:141-159,211-240,315-336','engine/source/materials/mat/mat117/sigeps117.F:175-189,362-381,455-467','hm_cfg_files/config/CFG/radioss2612/MAT/mat117.cfg:77-84','A67rapport limits damage rollback and nonlinear domains'],
      'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False}
    dump(OUT/'configuration_A81_proposed.json',cfg)
    dump(OUT/'scope_review.json',{'pass':True,'checks':checks,'native_started':0,'requires_new_human_authorization':True,'static_only':True,'source_identification_not_native_default_qualification':True})
    dump(OUT/'load_samples.json',{'time_unit':'ms','displacement_unit':'mm','samples':samples})
    print(json.dumps({'prepared':True,'static_checks':len(checks),'native_started':0,'max_requested_native':2,'Engine_conditional':True}))

if __name__ == '__main__':
    main()
