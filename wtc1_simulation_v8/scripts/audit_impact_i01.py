"""Independent saved-history audit, common-time comparisons, no solver rerun."""
import csv,json,re,subprocess,time
import numpy as np
from run_impact_i01 import ROOT,CFG,sha,write_json
cfg=json.loads(CFG.read_text(encoding='utf-8')); out=ROOT/cfg['output_root']; start=time.perf_counter()
audit={}; curves={}; gates=cfg['predeclared_checks']
for case in cfg['cases']:
    d=out/case['id']; gen=json.loads((d/'generation.json').read_text()); run=json.loads((d/'results.json').read_text())
    with (d/(gen['name']+'T01.csv')).open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    # Converter leaves an empty trailing header in the no-contact CSV; not a data channel.
    cols=[k for k in rows[0] if k.strip()]; arr={k:np.asarray([float(r[k]) for r in rows]) for k in cols}
    masscols=[k for k in cols if k.strip().endswith(' MASS')]; hecols=[k for k in cols if k.strip().endswith(' HE')]; erodecols=[k for k in cols if k.strip().endswith(' ERODED')]
    msum=sum(arr[k] for k in masscols); hsum=sum(arr[k] for k in hecols); eroded=sum(arr[k] for k in erodecols)
    base=arr['KINETIC ENERGY'][0]+arr['INTERNAL ENERGY'][0]+arr['ROTATION ENERGY'][0]
    ordinary=arr['KINETIC ENERGY']+arr['INTERNAL ENERGY']+arr['ROTATION ENERGY']-base-arr['EXTERNAL WORK']
    extended=ordinary+arr['CONTACT ENERGY']+hsum
    init_target=gen['box_initial_KE_J']
    deck_lines=(d/(gen['name']+'_0000.rad')).read_text().splitlines()
    velocity_line=deck_lines[deck_lines.index('/INIVEL/TRA/1')+2]
    actual_speed=abs(float(velocity_line[40:60]))
    deck_ke=.5*gen['box_mass_g']*actual_speed**2*.001
    title=next(k for k in cols if k.strip().startswith('WING_BOX_SURROGATE') and k.strip().endswith('ZMOM'))
    if case['contact']: j=np.abs(arr[next(k for k in cols if 'CONTACT_IMPULSE' in k)]); j-=j[0]
    else: j=np.zeros_like(arr['time'])
    dp=arr[title]-arr[title][0]
    # CSV has raw cumulative impulses: no /TH/TITLE, see OpenRadioss maintainers #867/#2451.
    curves[case['id']]={'time_ms':arr['time'].tolist(),'impulse_Ns':(j*.001).tolist()}
    listing=(d/(gen['name']+'_0000.out')).read_text(encoding='utf-8',errors='replace')
    checks={
      'normal_termination':run['normal_termination'],
      'zero_eroded_elements':bool(np.max(eroded)==0),
      'mass_scaling_negligible':bool(np.max(np.abs(arr['ADDED MASS']))/arr['MASS'][0]<=gates['max_added_mass_fraction']),
      'all_part_mass_sum_matches_global':bool(np.max(np.abs(msum-arr['MASS']))/arr['MASS'][0]<1e-6),
      'initial_mass_matches_geometry':run['mass_error_fraction']<1e-6,
      'initial_KE_matches_geometry_and_speed':bool(abs(base*.001-init_target)/init_target<1e-6),
      'initial_KE_matches_actual_rounded_deck_speed':bool(abs(base*.001-deck_ke)/deck_ke<1e-6),
      'conventional_energy_error_within_declared_5pct':bool(np.max(np.abs(ordinary))/base<=gates['max_abs_energy_error_fraction']),
      'part_numerical_energy_within_declared_1pct':bool(np.max(np.abs(hsum))/base<=gates['max_hourglass_over_initial_KE']),
      'final_impulse_momentum_check':run['momentum_balance_error_fraction']<=gates['max_momentum_impulse_relative_error'],
      'geometric_initial_gap_positive':gen['initial_gap_surface_mm']>0,
      'no_fail_cards': '/FAIL/' not in (d/(gen['name']+'_0000.rad')).read_text(),
      'physical_fracture_validation':False
    }
    audit[case['id']]={'checks':checks,'ordinary_energy_max_error_fraction':float(np.max(np.abs(ordinary))/base),'extended_balance_max_residual_fraction':float(np.max(np.abs(extended))/base),'extended_balance_final_residual_J':float(extended[-1]*.001),'max_part_numerical_energy_fraction':float(np.max(np.abs(hsum))/base),'warning_ids':re.findall(r'^WARNING ID\s*:\s*(\d+)',listing,re.M),'last_record_ms':float(arr['time'][-1]),'fixed_geometry_gap_mm':gen['initial_gap_surface_mm'],'final_impulse_Ns':float(j[-1]*.001),'all_output_checks_pass_excluding_physical':all(v for k,v in checks.items() if k!='physical_fracture_validation')}
    audit[case['id']]['input_rounding']={'configured_speed_m_per_s':cfg['speed']['m_per_s'],'deck_speed_m_per_s':actual_speed,'configured_KE_J':init_target,'deck_KE_J':deck_ke,'csv_initial_KE_J':float(base*.001),'relative_error_against_configured_KE':float(abs(base*.001-init_target)/init_target),'disposition':'Original strict check kept failed; additional deck-based check diagnoses general-format rounding. No solver data changed.'}
common=1.15
def value(k):
    c=curves[k]; assert c['time_ms'][0]<=common<=c['time_ms'][-1]
    return float(np.interp(common,c['time_ms'],c['impulse_Ns']))
comparisons={}
for a,b in [('M100','M050'),('M050','M025'),('M025','M0125'),('M050','DT045'),('M050','SKIN008')]:
    va,vb=value(a),value(b); comparisons[a+'_'+b]={'time_ms':common,'first_Ns':va,'second_Ns':vb,'relative_difference_over_second':abs(va-vb)/abs(vb),'interpolation':'Linear interpolation of scalar histories for same-time comparison, not new mechanical states'}
    if b in ['M050','M025','M0125']: comparisons[a+'_'+b]['passes_10pct_gate']=abs(va-vb)/abs(vb)<=gates['max_medium_fine_impulse_difference']
    if b=='DT045': comparisons[a+'_'+b]['passes_5pct_gate']=abs(va-vb)/abs(vb)<=gates['max_half_dt_impulse_difference']
write_json(out/'history_comparisons.json',comparisons)
write_json(out/'campaign_audit.json',{'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seconds':time.perf_counter()-start,'cases':audit,'comparisons':comparisons,'source_hashes':{str(CFG.relative_to(ROOT)):sha(CFG),cfg['inherited_config']:sha(ROOT/cfg['inherited_config']),cfg['inherited_generator']:sha(ROOT/cfg['inherited_generator'])},'qualification':'NUMERICAL_DIAGNOSTIC_ONLY','physical_WTC1_impact_qualified':False,'fracture_qualified':False,'ordinary_and_extended_energy_checks_separate':True,'energy_limit_notes':'TYPE7 damping energy is not supplied in CE_DAMP; nonzero residual retained, not filled by an invented dissipation. QEPH numerical energy from all TH/PART HE, not global HE alone.','impulse_documentation':'https://github.com/orgs/OpenRadioss/discussions/2451','initial_six_case_matrix_kept':True,'additional_fine_case_declared_after_initial_failure':True})
print(json.dumps(comparisons,indent=2))
