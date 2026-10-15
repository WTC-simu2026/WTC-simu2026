"""Preserve the failed fixed-step A81 attempt; no native retry or invented history."""
from run_aircraft_a81_cohesive_loop import ROOT,OUT,CFG,AUTH,PLAN,CASE,NAME,guard,read,dump,sha,now,rel,harness
from read_aircraft_a81_th_binary import decode
from pathlib import Path
import json,re,csv
import numpy as np

REPORT=OUT/'rapport_aircraft_a81.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A81_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A82_2026-10-15.md'


def route():
    return ('AIRCRAFT-A82 : après publication A80+A81 vérifiée, diagnostiquer en lecture seule l’arrêt '
        'au premier pas imposé A81, message79/ISTOP−2, sans rupture ni refermeture observées. '
        'Préparer une observation des critères de convergence au premier essai, avec impression nonlinéaire détaillée '
        'et restart initial A81 réutilisé, sans modifier le chargement, les tolérances, le minimum/maximum de pas, '
        'le moteur ou les paramètres physiques. Toute nouvelle exécution nécessite une proposition concrète et accord distinct : '
        'les1Starter+1Engine A81 sont consommés. Ne pas abaisser silencieusement le pas minimum ni compter l’état initial '
        'comme trajectoire. Les impulsions de plateau, USR, dégâts, compression après rupture et retour en contact restent non mesurés. '
        'Conserver erreurs, avertissements, refus R0, limites et budgets antérieurs. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def assess():
    c=guard();assert not REPORT.exists();d=OUT/CASE
    native=read(OUT/'native_execution_review.json');sg=read(d/'starter_gate_review.json')
    assert native['new_Starter']==native['new_Engine']==1 and sg['pass']
    execution=read(d/'engine.execution.json');assert execution['parent_exit_code']==2 and not execution['timed_out']
    listing=d/(NAME+'_0001.out');text=listing.read_text(encoding='utf8',errors='replace')
    assert 'SOLVER IMPLICIT STOPPED DUE TO TIMESTEP LIMIT' in text and 'ISTOP=-2' in text
    p=d/(NAME+'T01');meta,arrays,flat=decode(p)
    t=arrays['time'][:,0];assert len(t)==1 and t[0]==0
    names=['time']+['global_var'+str(k) for k in meta['global_ids']]
    for part in meta['parts']:names += ['part'+str(part['id'])+'_var'+str(k) for k in part['variables']]
    for sub in meta['subsets']:names += ['subset'+str(sub['id'])+'_var'+str(k) for k in sub['variables']]
    for g in meta['groups']:
        for e in g['entities']:names += ['group'+str(g['id'])+'_entity'+str(e['id'])+'_var'+str(k) for k in g['variables']]
    assert len(names)==flat.shape[1]
    with (d/(NAME+'T01_python_records.csv')).open('x',encoding='utf8',newline='') as f:
        w=csv.writer(f);w.writerow(names);w.writerows(flat)
    np.savez_compressed(d/'initial_TH_binary_arrays.npz',**arrays)
    checks={'Starter_strict_pass':sg['pass'],'normal_Engine_termination':False,'actual_saved_target_state':False,
        'complete_5200_step_trajectory':False,'compression_before_opening_plateau_observed':False,
        'rupture_native_certified':False,'post_rupture_reclosure_observed':False,'USR_population_qualified':False}
    dump(OUT/'observation_review.json',{'created_utc':now(),'pass_observation':False,'physical_pass':False,
        'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],
        'native_history_rows':1,'native_last_time_ms':0,'native_accepted_nonzero_states':0,
        'binary_schema':meta,'CSV_origin':'Own Python decode of actual records; cached A67 native CSV validated before use',
        'new_converter_or_native_launched':False,'first_user_field_values_not_damage_qualification':True,
        'plateau_forces_N':{'before':None,'after':None},'damage':None,'fracture_work_J':None,
        'timestep_limit_preserved':True,'extra_Engine_warnings':['PARITH/ON incompatible with implicit','ISOLID0 stiffness uses generic formulation'],
        'native_step_min_ms':.000125,'native_step_max_ms':.000125,'stop_message':79,'ISTOP':-2,
        'matrix_negative_pivots_printed':0,'matrix_free_unknowns_printed':8,
        'matrix_factorization_success_does_not_qualify_convergence':True,'cause_of_first_nonlinear_failure_not_directly_observed':True})
    changed=[];old=read(OUT/'preservation_before_metadata.json')['files']
    for row in old:
        s=(ROOT/row['path']).stat()
        if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed
    for row in c['unchanged_software']:assert sha(ROOT/row['path'])==row['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),
        'changed_paths':changed,'both_binaries_rehashed':True,'old_native_replayed':False,'historical_archive_rescanned':False})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A81','status':'completed_bounded_cohesive_attempt__Starter_pass__Engine_timestep_limit_before_first_saved_step',
        'explicit_authorization':c['authorization'],'new_Starter':1,'new_Engine':1,'Starter_remaining':0,'Engine_remaining':0,
        'Starter_wall_s':native['starter_execution']['wall_s'],'Engine_wall_s':execution['wall_s'],
        'CPU_threads':1,'each_cap_s':180,'Starter_pass':True,'Starter_errors':0,'Starter_warnings':0,
        'Engine_pass':False,'observation_pass':False,'physical_pass':False,'last_saved_coupon_time_ms':0,
        'saved_nonzero_time_states':0,'stop_message':79,'ISTOP':-2,'timestep_min_and_max_ms':.000125,
        'native_material_defaults_confirmed':sg['native_material_values'],'native_mass_g':8,'native_ADMAS_g':8,
        'compression_rupture_reclosure_remain_unmeasured':True,'no_newton_cause_claim_from_generic_stop':True,
        'own_driver_parser_R0_ambiguity_preserved_and_fixed_before_launch':True,
        'software_patch_compilation_GPU_installation':False,'no_retry_or_budget_reset':True,'all_old_gates_preserved':True,
        'whole_dynamic_extension':False,'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,
        'objective1_complete':False,'next_iteration':'AIRCRAFT-A82'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'observation':rel(OUT/'observation_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text(f'''# AIRCRAFT-A81 — préparation propre, arrêt sur la limite de pas

Le lot autorisé est terminé : un Starter et un Engine consommés, aucun relancement. La préparation passe mais le calcul s’arrête avant le premier état sauvegardé à temps positif. Compression, rupture et refermeture restent non observées.

## 1. Faits directement observés ou transcrits

Accord « Oui, exécuter le témoin A81 après vérification de la publication », receipt request_user_input_async/call_a5c8cd61518347429f6bb01020760042/0. Publication A78+A79 vérifiée avant déclaration et exécution. Entrées A80 exactes, logiciels inchangés et empreintes contrôlées. UnCPU, plafond180s chacun, zéro GPU/installation/correctif/compilation/extension entière. Starter{native['starter_execution']['wall_s']:.3f}s, code0, zéro erreur/zéro avertissement, restart initial valide. Matériau LAW117, critères1/1, ISYM0, EN4400, ET800, TN450, TT100, GI/GII50 et seuilmodeI0,2222222mm réellement imprimés. Masse8g et ADMAS8g instrumentaux.

Engine{execution['wall_s']:.3f}s, code2, aucun dépassement. MESSAGE79 : arrêt implicite sur limite de pas, ISTOP−2. Les minima et maxima0,000125ms sont conservés. La matrice libre a huit inconnues ; factorisation MUMPS sans pivot négatif imprimé. Cela ne prouve pas la convergence non linéaire. Les avertissements PARITH/ON incompatible et formulationISOLID0 générique sont conservés séparément.

## 2. Résultats d’un modèle officiel

Aucun résultat historique officiel nouveau. Les définitions logicielles documentées et le modèle de sortie TH3040 servent à lire les observations, sans être assimilés à une validation mécanique. Les valeurs de la carte courte sont cette fois vérifiées dans la sortie native propre au témoin.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source réanalysée ou modifiée. Les copies privées de sources logicielles sont distinctes, sans modification de binaire. Aucun dégât connu ajusté.

## 4. Hypothèses propres au modèle

Graine1102092, zéro tirage, unitésg/mm/ms. Coupon indépendant8nœuds/100mm², cartes cohésives actuelles exactes, aucune compensation de masse de l’avion. La trajectoire prévue−0,05/+0,3/−0,05mm et l’horizon0,65ms ne sont pas des résultats : ils n’ont pas été parcourus. La borne minimale égale au pas initial devait arrêter une réduction ; ce refus reste un résultat, sans abaissement après coup. La cause précise du premier refus non linéaire n’est pas déduite du seul message générique.

## 5. Résultats dérivés

Le fichier TH natif contient exactement un état, à0ms. Son schéma lie les groupes, nœuds, variables et élément présents ; le lecteur Python a été comparé au CSV natif A67 sauvegardé sur8001lignes/99colonnes, sans exécution native rejouée. Le CSV A81 est une transcription du binaire initial, pas un second convertisseur ni un historique reconstruit. Une seule animation initiale est présente. Aucun plateau, force après rupture, travail de fracture ou dommage n’est qualifié ; les zéros USR initiaux ne signifient pas que leur peuplement est validé.

Le premier contrôle du nouveau lecteur de préparation confondait les lignes de seuil et de fonction de seuil TN/TT : R0 est conservé, la sélection de préfixe a été corrigée et testée sur la sortie A67 sauvegardée avant tout lancement. Ce correctif de lecteur propre n’a changé aucune carte physique, binaire ou budget.

## 6. Contradictions et informations manquantes

L’objectif du coupon n’est pas atteint. Ni rupture ni compression après refermeture ne sont mesurées ; aucune conclusion sur la politique de contact n’est autorisée à partir de l’état initial. La tolérance énergétique A67 de1e−7J est conservée, sans faux succès d’un bilan portant seulement sur0ms. L’Engine ne disposait pas d’impression détaillée des critères Newton ; il faut les observer avant de modifier les pas ou les tolérances. Les deux places natives sont consommées ; aucun remplacement automatique. A75/A77/A79,107391avertissements A73, limites et budgets restent conservés. Meilleur impact entier0,0200001220703125s ; dix secondes puis vidéo3D incomplètes.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A81 → AIRCRAFT-A82\n\nRapport : '+rel(REPORT)+'\nObservation : '+rel(OUT/'observation_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence locaux puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(OUT/'observation_review.json')+' et '+rel(HANDOFF)+'.\nA81terminée,1Starter+1Engineconsommés, aucun calcul en cours ; vérifier publication A80+A81 avant A82.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    evidence=OUT/'own_parser_development_evidence';evidence.mkdir()
    for p in (ROOT/'tmp/aircraft_a81_driver_parser').iterdir():
        if p.is_file():__import__('shutil').copy2(p,evidence/p.name)
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a81*.py'))
    files += list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a81*.json'))+[HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_only_no_raw_AGPL':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A81_assessed':True,'observation_pass':False,'last_saved_ms':0,'native_budget_consumed':2}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert cycle['pending_iterations']==['AIRCRAFT-A80']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A81','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A81',next_iteration='AIRCRAFT-A82',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a81_key_results']=entry;s['validated_artifacts'].update(aircraft_a81_report=rel(REPORT),aircraft_a81_results=rel(OUT/'composite_qualification_review.json'),aircraft_a81_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A80','AIRCRAFT-A81'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A80+AIRCRAFT-A81 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==200
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,
        'files_verified':len(m['files']),'native_observation_complete':False,'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A82'})
    print(json.dumps({'A81_registered':True,'registry':200,'pending_publication':2}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
