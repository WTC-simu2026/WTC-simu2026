"""Seal new mixed witnesses, derivative and symmetric-assembly limitation."""
from probe_aircraft_a60 import ROOT,OUT,CFG,read,dump,sha,now,rel,harness
import json

REPORT=OUT/'rapport_aircraft_a60.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A60_HANDOFF.md'

def route():
    return ('AIRCRAFT-A61 : préparer une matrice surfacique symétrique d’itération avec forces natives LAW117 conservées, puis une différence moteur concrète et bornée. '
      'A60 six nouveaux témoins explicites mixtes/nonproportionnels/compression passent traction, travail et énergie ; 22 contrôles de dérivée complète et état d’essai passent. '
      'La dérivée mixte est généralement non symétrique ; ASSEMC_KIJ stocke un triangle, IMP_MUMPS1 appelle SYM1, IMP_BUCK appelle SYM2 dans les répertoires implicites inspectés. '
      'Ne pas assimiler une matrice symétrique d’itération à la dérivée exacte, ni modifier seulement le drapeau MUMPS. '
      'État d’essai natif/retour arrière, repères mobiles et convergence native restent à qualifier. Toute nouvelle modification/compilation moteur exige un accord humain distinct sur une proposition concrète. '
      'Moteur A57 SHA256 34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528 inchangé. '
      'Fin native des témoins1ms à un pas près, historique0,9999ms inchangé ; anciens échecs d’égalité temporelle préservés et correction d’observable séparée après calcul. '
      'CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré, bilans locaux et domaines matériaux échoués conservés. '
      'Meilleur impact entierA20 0,0200001220703125s, aucun crédit des témoins ; objectif dix secondes physiques puis vidéo3D incomplet. '
      'Pas de prolongation A20 hors domaine ni de répétition des diagnostics acquis. Publication après paireA60+A61 vérifiée.')

def assess():
    assert not REPORT.exists()
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    native=read(OUT/'mixed_review_terminal_time_interval.json');mat=read(OUT/'material_Jacobian_state_review.json');execution=read(OUT/'native_execution_review.json')
    assert native['mechanical_witness_domain_pass'] and mat['pass'] and len(mat['checks'])==22 and execution['all_complete']
    assert read(OUT/'terminal_clock_reproduction_review.json')['saved_analysis_reproduced']
    assert read(OUT/'mixed_native_review.json')['pass'] is False
    assert read(OUT/'mixed_review_with_final_fields.json')['mechanical_witness_domain_pass'] is False
    old=read(OUT/'preservation_before_metadata.json');changed=[]
    for row in old['files']:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old['files']),'changed_paths':changed,'old_hash_manifests_preserved':True,'all_old_files_rehashed':False,'old_solver_reruns':0,'archive_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A60','status':'completed_new_explicit_mixed_cohesive_witnesses_and_full_material_derivative__symmetric_native_assembly_limitation_identified',
       'new_Engine_runs':6,'new_Starter_runs':6,'new_compilations':0,'old_Engine_replays':0,'explicit_mixed_witnesses_pass':6,'material_derivative_and_trial_state_checks_pass':22,
       'half_dt_and_area_checks_pass':True,'mechanical_thresholds_unchanged':True,'initial_endpoint_failures_preserved':True,'terminal_clock_interval_correction_after_runs':True,
       'maximum_native_traction_relative_error':max(r['maximum_traction_relative_error'] for r in read(OUT/'mixed_native_review.json')['cases']),
       'full_mixed_derivative_generally_nonsymmetric':True,'symmetric_assembly_exact_derivative_compatible':False,
       'native_trial_state_rollback_qualified':False,'moving_frame_geometry_qualified':False,'native_surface_implicit_integration_qualified':False,
       'mass_material_budgets_changed':False,'RKE_added':False,'old_outputs_and_failed_gates_preserved':True,'whole_CHECK_errors_preserved':15,'whole_zero_volume_messages_preserved':624,'TYPE25_ignored_preserved':5,'A52_integrated':False,
       'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'whole_insertion_ready':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A61'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'mixed_cases':'mixed_review_terminal_time_interval.json','material_derivative':'material_Jacobian_state_review.json','symmetric_native_assembly':'native_symmetry_compatibility_review.json','original_endpoint_failures':['mixed_native_review.json','mixed_review_with_final_fields.json'],'whole_impact_qualified':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A60 — modes mixtes et limite de l’assemblage implicite

Six nouveaux témoins explicites chargés concordent avec le contrat propre de la branche mixte LAW117 déclarée. La dérivée exacte mixte est généralement non symétrique, incompatible avec son insertion directe dans l’assemblage symétrique inspecté. Aucun correctif moteur appliqué ou compilé ; aucune seconde d’impact entier supplémentaire.

## 1. Faits directement observés ou transcrits

Six Starter sans erreur/avertissement puis six Engine A57 normaux, un CPU/sans GPU, plafonds180s chacun. Historiques natifs binaires et CSV concordants ; trois axes de déplacements, vitesses et impulsions de réaction contrôlés. Tractions, travail externe, énergie interne, bilan global, masse instrumentale8g et absence de masse ajoutée passent les seuils A17 inchangés. Erreur maximale relative de traction0,000891. Demi-pas et aire×4 concordent. Deux ratios mixtes, azimuts distincts, décharge/recharge, trajet non proportionnel et compression après endommagement constituent de nouvelles questions ; aucun ancien témoin rejoué.

L’historique termine à0,9999ms, et échoue au contrôle initial de fin1ms. Les champs finaux sauvegardés indiquent1,0ms dans cinq cas,1,00001ms pour le demi-pas. Le premier contrôle d’égalité stricte échoue dans ce dernier cas. Ces analyses initiales restent intactes. Une analyse séparée, après calcul, compare la fin réelle à[1ms,1ms+pas déclaré], avec1e-6ms de lecture : six fins atteignent la cible dans un pas. Le script reproduit exactement cette correction d’observable ; ni horloge ni pas ni seuil mécanique ni horizon demandé n’est modifié. Aucun temps de témoin crédité à l’impact entier.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Sources primaires du logiciel figé3d75ff13d1946f6d28a43920eac4fa2aae41b27a lues en cache, empreintes et lignes consignées. SIGEPS117 décrit la branche mixte testée. Dans les répertoires implicites inspectés, IMP_MUMPS1 initialise SYM1 et IMP_BUCK SYM2. ASSEMC_KIJ utilise un triangle et une transposition de bloc ; la matrice non symétrique entière n’y est pas conservée. Cette constatation ne revendique pas une inspection de tous les chemins solveur. Les sources AGPL ne sont pas copiées dans les livrables publics MIT.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF consulté/modifié. Aucun ajustement aux dégâts connus.

## 4. Hypothèses propres au modèle

Graine1102085, zéro tirage, unités g/mm/ms, travail Nmm vers J×0,001. EN4400N/mm³,ET800N/mm³,TN450MPa,TT100MPa,GI/GII50N/mm conservés ; paramètres témoins sans fracture historique mesurée. Contrat propre limité au critère en déplacement, évolution linéaire, mélange en puissance d’exposant2 et compression asymétrique. Aucune qualification des autres branches LAW117. La différentiation automatique dérive les trois composantes avec l’état validé gelé pendant un essai. Repère matériel fixe, pas de dérivée géométrique native.

## 5. Résultats dérivés

Vingt-deux contrôles propres passent : différences finies des neuf dérivées, monotonicité des états, abandon d’essai sans pollution, pentes pures indépendantes, trois résolutions Newton revenant au même équilibre. Un contrôle négatif qui valide le dommage à chaque essai donne un mauvais équilibre et reste archivé. Ces contrôles qualifient le contrat propre, pas le retour arrière du moteur. La dérivée exacte non symétrique nécessite une autre méthode d’itération ou un assemblage différent ; changer uniquement SYM ne suffit pas. Une matrice surfacique symétrique d’itération peut être étudiée en conservant le résidu natif complet et en exigeant sa convergence.

Préservation des anciennes sorties/critères par métadonnées et manifestes ; configuration figée, rapports et empreintes propres enregistrés, harnais PASS. Aucun budget avion/façade, matériau ou RKE modifié.

## 6. Contradictions et informations manquantes

Convergence implicite native, validation/retour arrière des états et repères mobiles non qualifiés. Les fins d’historique/égalité stricte initialement échouées restent visibles ; le nouveau critère d’intervalle est une correction analytique postérieure explicitement déclarée. CHECK entier15erreurs/624volumes/cinq TYPE25 ignorés, A52 non intégré et critères locaux/matériaux entiers échoués conservés. A20 reste0,0200001220703125s et hors domaine pour une prolongation ; dix secondes physiques et leur vidéo3D restent incomplètes. Toute nouvelle modification/compilation du moteur exigera un accord distinct sur une proposition concrète.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A60 → AIRCRAFT-A61\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a60*.py'))+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'third_party_raw_source_excluded':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A60_assessed':True,'new_Engine':6,'whole_credit':0}),flush=True)

def register():
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json')
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl') and cycle['pending_iterations']==[]
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A60','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A60',next_iteration='AIRCRAFT-A61',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a60_key_results']=row
    state['validated_artifacts'].update(aircraft_a60_report=rel(REPORT),aircraft_a60_results=rel(OUT/'composite_qualification_review.json'),aircraft_a60_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A60'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A60+AIRCRAFT-A61 verified')
    for p,v in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==179
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':len(m['files']),'harness':h,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A61'})
    print(json.dumps({'A60_registered':True,'registry_entries':179,'pending_publication_count':1}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
