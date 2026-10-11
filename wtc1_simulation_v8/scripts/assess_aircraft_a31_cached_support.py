"""Read cached A30 plastic work and retain the native implicit capability limits."""
from run_aircraft_a31 import *

def main():
    guard();dest=OUT/'cached_support_assessment.json';assert not dest.exists();rows=[]
    for d in sorted((PREV/'w0').iterdir()):
        if not d.is_dir():continue
        g=read(d/'generation.json');q=d/(g['name']+'T01.csv');H=histories(q);keys=[k for k in H if k.startswith(('LOWER_VOLUME_SKIN','UPPER_VOLUME_SKIN','UNCHANGED_SOURCE_CORE')) and k.strip().endswith('PW')];assert len(keys)==3
        rows.append({'case':d.name,'csv':rel(q),'csv_sha256':streamsha(q),'part_keys':keys,'maximum_absolute_part_PW_J':{k:float(abs(H[k]).max()*.001) for k in keys},'maximum_sum_PW_J':float(abs(sum(H[k] for k in keys)).max()*.001)})
    assert len(rows)==9
    dump(OUT/'a30_cached_plastic_work_addendum.json',{'created_utc':now(),'rows':rows,'omission':'A30 diagnostic selected THgroupname rather than actual part titles, producing empty PW dictionaries. Its qualification did not declare a plastic-work gate. This separately stored cached read supplies the missing diagnostic without rewriting sealed A30 evidence.','old_native_solver_reruns':0,'old_files_modified':False,'maximum_all_cases_sum_PW_J':max(r['maximum_sum_PW_J'] for r in rows),'qualification_of_A30_not_rewritten':True})
    p=OUT/'implicit_capability';both=[]
    for branch in [p,p/'w1_compact']:
        for name in ['PCG','MUMPS']:
            d=branch/name;t=(d/'engine.log').read_text(errors='replace');both.append({'case':rel(d),'starter_pass':read(d/'starter_gate.json')['pass'],'native_completed':read(d/'review.json')['binary_implicit_completion'],'engine_log_sha256':streamsha(d/'engine.log'),'native_fatal_MUMPS_required':bool(re.search(r'Fatal error: MUMPS required',t)),'native_error_termination':'ERROR TERMINATION' in t,'parser_internal_EOF':'end-of-file during read' in t})
    assert all(x['native_fatal_MUMPS_required'] and x['native_error_termination'] for x in both[-2:])
    dump(OUT/'implicit_binary_capability_assessment.json',{'created_utc':now(),'cases':both,'existing_binary_implicit_route_available':False,'conclusion':'Original80charNONLINrecord fails before native setup. Independent preserved upstream parser declares TITLE*72; compact equivalent record removes that parser failure. Both compact PCG and direct MUMPS probes terminate natively with MUMPS required (8684 and2404). This installed executable does not demonstrate an implicit continuation route.','whole_restart_contact_or_regime_transition_tested':False,'solver_binary_changed':False,'software_installed':False,'old_runs_retained':True,'source_snapshot_matches_binary_not_claimed':True})
    dump(dest,{'created_utc':now(),'A30_cached_parts_observed':27,'A30_maximum_sum_PW_J':max(r['maximum_sum_PW_J'] for r in rows),'implicit_new_attempts':4,'implicit_completed':0,'existing_binary_implicit_route_available':False,'no_whole_impact_executed':True,'objective1_complete':False});print(read(dest),flush=True)

if __name__=='__main__':main()
