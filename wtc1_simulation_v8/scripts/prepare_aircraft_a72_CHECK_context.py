"""Read-only correction proposal: use explicit CHECK context, reuse qualified input states, capture globals next time."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import copy,json,tarfile,hashlib,re,difflib

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a72_preparation';PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a72_CHECK_context_proposal'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a72_proposal.json'

def common_order(text,name):
    lines=text.splitlines();i=next(i for i,l in enumerate(lines) if re.search(r'COMMON\s*/'+name+r'/',l,re.I));s=lines[i].split('/',2)[2];j=i+1
    while j<len(lines) and len(lines[j])>5 and lines[j][5]=='.':s+=lines[j][6:];j+=1
    return [v.strip() for v in s.replace(' ','').split(',') if v.strip()]

def main():
    assert not any(p.exists() for p in [PREP,PRIVATE,PLAN]);assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A71'
    PREP.mkdir();PRIVATE.mkdir();cfg=read(ROOT/'wtc1_simulation_v8/data/aircraft_a71_predeclaration.json');current=cfg['check_zero_residual_patch'];base=ROOT/current['proposed_source']
    assert sha(base)==read(ROOT/'wtc1_simulation_v8/output/aircraft_a71/exact_CHECK_policy_patch_application.json')['applied_source_sha256']
    before=base.read_text(encoding='utf8');start=before.index('      SUBROUTINE IMP_CHKM(');end=before.index('\n      END\n',start)+len('\n      END\n');body=before[start:end]
    old='        ELSEIF(IDYNA==2.AND.IQSTAT==0.AND.TT==ZERO.AND.';new='        ELSEIF(IDYNA==2.AND.IQSTAT==0.AND.IMP_CHK>0.AND.'
    assert body.count(old)==1 and body.count('#include "com08_c.inc"\n')==1
    changed=body.replace(old,new).replace('#include "com08_c.inc"\n','');after=before[:start]+changed+before[end:]
    assert changed.replace(new,old).replace('#include "com04_c.inc"\n','#include "com04_c.inc"\n#include "com08_c.inc"\n',1)==body
    dest=PRIVATE/'imp_solv.proposed.F';dest.write_text(after,encoding='utf8',newline='\n')
    diff=PRIVATE/'explicit_CHECK_context.patch';diff.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='engine/source/implicit/imp_solv.F',tofile='engine/source/implicit/imp_solv.F')),encoding='utf8',newline='\n')
    assert len(new)<=72
    globals_meta={};archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    with tarfile.open(archive) as t:
        for name,block,fields in [('impl1_c.inc','IMPL1',['IDYNA','IQSTAT','IMP_CHK']),('com01_c.inc','COM01',['NCYCLE']),('com08_c.inc','COM08',['TT'])]:
            m=next(m for m in t.getmembers() if m.name.endswith('/engine/share/includes/'+name));b=t.extractfile(m).read();text=b.decode('utf8');(PRIVATE/name).write_bytes(b)
            order=common_order(text,block);kind='f64' if block=='COM08' else 'i32';width=8 if kind=='f64' else 4
            assert all('(' not in v for v in order[:max(order.index(f) for f in fields)+1])
            for f in fields:globals_meta[f]={'symbol':block.lower()+'_','byte_offset':width*order.index(f),'kind':kind,'declaration_source':name,'source_sha256':hashlib.sha256(b).hexdigest()}
    oldplan=read(ROOT/'wtc1_simulation_v8/data/aircraft_a70_proposal_r4.json');cases=copy.deepcopy(oldplan['controls']['cases'])
    for c in cases:
        if c['case']=='STATIC_POSITIVE_LOAD_CHECK':
            d=ROOT/'wtc1_simulation_v8/output/aircraft_a71/STATIC_POSITIVE_LOAD_CHECK';paths=[d/(c['name']+'_0000_0001.rst'),d/(c['name']+'_0001.rad')]
            c.update(inputs=[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths],new_Starter=False,
                accepted_cached_Starter_A71_reused=True,expected='R2=4, no loading error or initial-zero INFO; same validated positive control inputs')
        elif c['case']=='FREE_INITIAL_ZERO_CHECK':c['expected']='R2=0, IDYNA2/IQSTAT0/IMP_CHK>0, INFO1/ERROR0 regardless absolute TT; flags/time directly read'
        elif c['case'].startswith('WHOLE_'):c['expected']='Observe flags/R2 and explicit CHECK diagnostic with unchanged cards; TYPE25 and all warnings preserved, physical whole remains blocked'
        for r in c['inputs']:assert sha(ROOT/r['path'])==r['sha256']
    assert all(not c['new_Starter'] for c in cases)
    chronology=read(ROOT/'wtc1_simulation_v8/output/aircraft_a71/CHECK_call_order_review.json');assert chronology['TT_advances_before_CHECK_call']
    checks={'only_guard_line_replaced_and_unused_common_removed':True,'only_IMP_CHKM_changed':after[:start]==before[:start] and after[after.index('\n      END\n',start):]==before[end-len('\n      END\n'):],
        'literal_TT0_guard_failure_preserved_in_A71':True,'CHECK_positive_call_context_source_verified':True,'IMP_CHK_already_declared_in_existing_IMPL1':True,
        'native_clock_not_assumed_zero':True,'all_force_material_history_stiffness_dynamics_routines_byte_preserved':True,'static_zero_and_nonfinite_out_of_range_branches_preserved':True,
        'old_INFO_message_kept_explicit':True,'connection_and_TYPE25_warnings_preserved':True,'exact_six_input_sets_hash_verified':True,
        'qualified_A71_positive_initial_state_cached_no_Starter_repeat':True,'five_global_fields_have_pinned_typed_offsets':len(globals_meta)==5,'no_new_native_source_application_or_compilation':True}
    assert all(checks.values())
    plan={'created_utc':now(),'iteration':'AIRCRAFT-A72_PROPOSAL','seed':1102097,'random_draws':0,'source_pin':cfg['source_pin'],
        'patch':{'target':'engine/source/implicit/imp_solv.F','current_source':rel(base),'current_sha256':sha(base),'proposed_source':rel(dest),'proposed_sha256':sha(dest),'patch':rel(diff),'patch_sha256':sha(diff),
            'scope':'IMP_CHKM only: change TT==0 to explicit IMP_CHK>0; remove now-unused added COM08 declaration. All other paths/functions exact.',
            'explicit_new_admissibility_in_CHECK_Newmark2_QSTAT0_R2exact0':True,'applied':False,'compiled':False,'past_TT0_failed_gates_not_relabelled':True},
        'build':{'future_iteration':'AIRCRAFT-A73','future_Engine_number':9,'future_candidate':'wtc1_simulation_v8/openradioss_runtime/a73_CHECK_context_candidate',
            'maximum_s':3600,'CPU_threads':6,'GPU':False,'installation':False,'retain_all_A71_recipe_then_exact_new_diff':True,'estimate_minutes':[5,15]},
        'controls':{'maximum_Engine':6,'maximum_Starter':0,'CPU_threads':1,'each_cap_s':180,'GPU':False,'whole_dynamic_extension':False,'cases':cases,
            'acceptance':oldplan['controls']['acceptance'],'observe_native_globals':globals_meta,'read_only_globals_at_existing_breakpoints':True,
            'five_TYPE25_and_old_warnings_preserved_blocking':True,'new_binary_symbols_and_Common_sizes_must_be_guarded':True,
            'legacy_node_reduced_equation_map_missing_IKC_remains_unqualified':True},
        'previous_A71_Engine_budget_remaining':0,'new_explicit_human_authorization_required':True,'new_whole_force_mass_material_or_inertia_budgets_changed':False,
        'RKE_added':False,'whole_integration_ready':False,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(PLAN,plan);proposal=PREP/'proposition_contexte_CHECK_explicite.md'
    proposal.write_text('''# AIRCRAFT-A72 — proposition de contexte CHECK explicite, non appliquée

A71 compile et ses six contrôles sont terminés, mais la garde TT==0 reste échouée dans le témoin zéro dynamique et les deux scènes entières. Le résidu vaut bien zéro. La source RESOL avance TT avant CALL IMP_CHKM sous IF(IMP_CHK>0), puis arrête le CHECK par MSTOP2. Le contrôle du premier état ne se déroule donc pas sous une horloge absolue nulle.

La proposition remplace uniquement TT==0 par IMP_CHK>0 dans la garde et retire l’inclusion COM08 devenue inutile dans cette routine. IDYNA2, IQSTAT0 et R2 exactement zéro restent exigés. Le diagnostic explicite INFO est conservé ; zéro statique, autres méthodes/quasi-statique et R2 hors plage/non fini gardent leurs anciennes branches. Tous les anciens CHECK échoués restent conservés. Aucune force, matrice, matière, histoire, masse, inertie ou dynamique modifiée. Les107391 avertissements et cinq contactsTYPE25 restent présents/bloquants, sans substitution ni compensationRKE.

Source/différence exactes en copie privéeAGPL. Plan : wtc1_simulation_v8/data/aircraft_a72_proposal.json. Neuvième moteur isolé A73 proposé, toutes les corrections A71 conservées, compilation plafond1h/sixCPU, sansGPU ni installation, estimation5–15minutes. Aucun patch appliqué, aucun nouveau moteur compilé.

Puis maximum six Engine sur unCPU/plafond180s, zéro Starter : les six mêmes références instrumentales/entières sur le nouveau binaire. Le Starter positif A71 validé est réutilisé sans répétition, cartes/état initial vérifiés par empreintes. Les observations ajoutent les valeurs natives IDYNA, IQSTAT, IMP_CHK, NCYCLE et TT aux lectures de R2/diagonales, aux mêmes points d’arrêt matériels ; offsets et types sont dérivés des déclarations figées, bornes/taille des symboles contrôlées avant lecture. Aucun logiciel à installer, code/instruction/état mécanique de l’enfant modifié.

Le témoin zéro dynamique doit afficher INFO1/ERROR0, le zéro statique rester refusé, le contrôle chargé garder R2=4, la dynamique libre1ms conserver ses critères et les CHECK entiers garder leurs contacts/avertissements. Aucun temps de témoin crédité à l’impact entier, aucune extension vers10s dans ce lot. Réussite d’un contrôle de chargement ne qualifie pas l’impact physique ; les contacts/inerties/matériaux/bilans entiers restent à traiter.

Un nouvel accord distinct est requis : l’accord A71 couvrait la source exacte TT0 et ses six Engine/unStarter, tous consommés. AGENTS.md demande une autorisation pour toute nouvelle modification/compilation. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.
''',encoding='utf8')
    dump(PREP/'independent_scope_review.json',{'created_utc':now(),'pass':True,'checks':checks,'plan_sha256':sha(PLAN),'source_sha256':sha(dest),'patch_sha256':sha(diff),
        'source_chronology':rel(ROOT/'wtc1_simulation_v8/output/aircraft_a71/CHECK_call_order_review.json'),'new_global_offsets':globals_meta,
        'native_global_observation_not_yet_qualified':True,'source_not_applied_or_compiled':True})
    dump(PREP/'preparation_review.json',{'created_utc':now(),'pass':True,'proposal':rel(proposal),'plan_sha256':sha(PLAN),'new_native':0,'new_Starter':0,
        'new_compilation':False,'new_software_not_applied':True,'six_Engine_proposed_only':True,'old_positive_Starter_reused_not_replayed':True})
    print(json.dumps({'A72_context_proposal_ready':True,'scope_checks':len(checks),'native_flag_fields':len(globals_meta),'applied':False,'compiled':False}),flush=True)

if __name__=='__main__':main()
