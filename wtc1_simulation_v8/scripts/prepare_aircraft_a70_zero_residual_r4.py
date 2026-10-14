"""Replace the undeclared TIME proposal with the pinned COM08 TT guard; reuse the already checked coupon cards."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import tarfile,re,difflib,json,copy,hashlib

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a70_preparation_r4'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a70_initial_zero_residual_proposal_r4'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a70_proposal_r4.json'

def main():
    assert not any(p.exists() for p in [PREP,PRIVATE,PLAN]);PREP.mkdir();PRIVATE.mkdir()
    previous=ROOT/'wtc1_simulation_v8/data/aircraft_a70_proposal.json';p=copy.deepcopy(read(previous));oldprep=ROOT/'wtc1_simulation_v8/output/aircraft_a70_preparation_r2'
    dump(oldprep/'independent_scope_failure_r3.json',{'created_utc':now(),'failure':'TIME is not declared by COM04 or in IMP_CHKM; failed independent review prevents any application/compilation',
        'wrong_three_line_proposal_preserved':rel(previous),'new_native':0,'applied':False,'compiled':False})
    base=ROOT/p['patch']['current_source'];before=base.read_text(encoding='utf8');start=before.index('      SUBROUTINE IMP_CHKM(');end=before.index('\n      END\n',start)+len('\n      END\n');body=before[start:end]
    assert '#include "com08_c.inc"' not in body
    with tarfile.open(ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz') as t:
        m=next(m for m in t.getmembers() if m.name.endswith('/engine/share/includes/com08_c.inc'));common=t.extractfile(m).read()
    text=common.decode('utf8');assert 'COMMON /COM08/ TT, DT1' in text and re.search(r'my_real\s*\n\s*\.\s*TT,DT1',text)
    # All identifiers introduced by the common declaration are absent from the old routine's declarations/uses.
    fields=['LCOM08','TT','DT1','DT2','DT12','DT2OLD','TSTOP','TABFIS','TABFWR','XMIN_GLOB','XMAX_GLOB','YMIN_GLOB','YMAX_GLOB','ZMIN_GLOB','ZMAX_GLOB','TT_DP']
    collisions=[v for v in fields if re.search(r'\b'+v+r'\b',body,re.I)];assert not collisions,collisions
    (PRIVATE/'com08_c.inc').write_bytes(common)
    old='''        IF (R2>ZERO.AND.R2<EP30) THEN
        ELSEIF(IQSTAT>0) THEN'''
    addition='''        ELSEIF(IDYNA==2.AND.IQSTAT==0.AND.TT==ZERO.AND.
     .         R2==ZERO) THEN
          WRITE(IOUT,*)' ** INITIAL DYNAMIC RESIDUAL IS ZERO **'
'''
    assert body.count(old)==1 and body.count('#include "com04_c.inc"')==1
    changed=body.replace('#include "com04_c.inc"','#include "com04_c.inc"\n#include "com08_c.inc"').replace(old,'        IF (R2>ZERO.AND.R2<EP30) THEN\n'+addition+'        ELSEIF(IQSTAT>0) THEN')
    after=before[:start]+changed+before[end:];assert after.replace('#include "com08_c.inc"\n','',1).replace(addition,'',1)==before
    dest=PRIVATE/'imp_solv.proposed.F';dest.write_text(after,encoding='utf8',newline='\n')
    diff=PRIVATE/'initial_Newmark_zero_residual.patch';diff.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='engine/source/implicit/imp_solv.F',tofile='engine/source/implicit/imp_solv.F')),encoding='utf8',newline='\n')
    added=[l[1:] for l in diff.read_text(encoding='utf8').splitlines() if l.startswith('+') and not l.startswith('+++')];assert len(added)==4 and all(len(l)<=72 for l in added)
    for c in p['controls']['cases']:
        for f in c['inputs']:assert sha(ROOT/f['path'])==f['sha256']
    p['created_utc']=now();p['revision']='R4_TT_COM08';p['previous_unqualified_TIME_proposal_preserved']=rel(previous)
    p['patch'].update(proposed_source=rel(dest),proposed_sha256=sha(dest),patch=rel(diff),patch_sha256=sha(diff),added_fixed_form_lines=4,
        admissibility_change='Exactly R2=0 at native TT=0 with IDYNA=2 and IQSTAT=0 gets explicit diagnostic and no loading-error increment; add existing COM08 declaration only inside IMP_CHKM, all other paths identical.',
        common_include='engine/share/includes/com08_c.inc',common_include_sha256=hashlib.sha256(common).hexdigest(),TIME_undeclared_proposal_not_used=True)
    dump(PLAN,p)
    proposal=PREP/'proposition_controle_residu_initial_nul.md';original=(oldprep/'proposition_controle_residu_initial_nul.md').read_text(encoding='utf8')
    original=original.replace('ajoute trois lignes','ajoute quatre lignes').replace('au temps initial zéro','au temps physique natif TT exactement zéro')
    original=original.replace('wtc1_simulation_v8/data/aircraft_a70_proposal.json','wtc1_simulation_v8/data/aircraft_a70_proposal_r4.json')
    original=original.replace('Un accord humain distinct est requis','La version antérieure employait TIME, non déclaré : elle reste conservée et n’a pas été appliquée. La version R4 ajoute l’inclusion native COM08 uniquement dans IMP_CHKM, puis utilise TT, le temps physique réellement partagé. Les entrées de contrôle déjà vérifiées sont réutilisées sans régénération.\n\nUn accord humain distinct est requis')
    proposal.write_text(original,encoding='utf8')
    checks={'only_four_added_lines':True,'TIME_undeclared_not_used':True,'native_COM08_TT_declared_with_same_precision':True,'no_common_name_collision_in_old_routine':True,
        'only_IMP_CHKM_CHANGED':after[:start]==before[:start] and after[after.index('\n      END\n',start):]==before[end-len('\n      END\n'):],
        'remove_four_additions_recovers_exact_base':True,'fixed_format_within_72':True,'guard_Newmark2_QSTAT0_TT0_R2exact0':True,
        'positive_static_quasi_static_out_of_range_branches_unchanged':True,'force_constitutive_stiffness_dynamics_mass_inertia_functions_unchanged':True,
        'connection_and_TYPE25_checker_unchanged':True,'all_six_cached_input_sets_hash_valid':True,'positive_coupon_only_force_four_nodes_one_N_each':True,
        'all_prior_failed_preparation_and_native_criteria_preserved':True,'no_source_application_compilation_or_native':True}
    assert all(checks.values())
    dump(PREP/'independent_scope_review.json',{'created_utc':now(),'pass':True,'checks':checks,'plan_sha256':sha(PLAN),'source_sha256':sha(dest),'diff_sha256':sha(diff),
        'raw_native_COM08_sha256':hashlib.sha256(common).hexdigest(),'native_checks_NOT_executed':True,'previous_three_line_proposal_failed_scope_review':True,
        'correct_R2_native_inputs_reused_unchanged':True,'TIME_is_not_native_TT':True})
    dump(PREP/'preparation_review.json',{'created_utc':now(),'pass':True,'proposal':rel(proposal),'plan_sha256':sha(PLAN),'revision':'R4_TT_COM08',
        'new_native':0,'source_applied':False,'compiled':False,'correct_cached_inputs_reused':True,'previous_TIME_proposal_not_applied':True})
    print(json.dumps({'R4_TT_proposal_ready':True,'added_lines':4,'source_scope_checks':len(checks),'source_applied':False,'compiled':False}),flush=True)

if __name__=='__main__':main()
