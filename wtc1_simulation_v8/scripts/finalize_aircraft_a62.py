"""Seal the authorized sixth Engine and ten bounded tests, preserving open gates."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from build_aircraft_a62_surface import OUT,CFG
import json,ast

REPORT=OUT/'rapport_aircraft_a62.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A62_HANDOFF.md'

def route():
    return ('AIRCRAFT-A63 : moteur A62 compilé et conservé, SHA d36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235. '
      'Accord A61 exécuté : différence exacte initiale puis corrections de déclaration/interface Fortran seulement, équations du helper inchangées ; R0/R1 échecs conservés, R2 réussit dans le plafond initial1h/CPU6, sansGPU/installation. '
      'Dix nouveaux Engine A62 sur douze autorisés consommés, plafond180s/CPU1 chacun. A63 peut utiliser les DEUX contrôles restants sur ce binaire pour un oscillateur cohésif LIBRE élastique et son demi-pas, sans mouvement imposé et sans compilation. Ne pas réinitialiser cette limite. '
      'A62 : au repos critère123 produit NaN/Infinity malgré résidu de force0, puis STOP pas minimal àT0 ; son log supplémentaire localise cette normalisation. '
      'Trois témoins à petite vitesse initialeY libre0,01mm/ms terminent normalement à1ms, traction/travail/G/recharge/demi-pas concordants ; rapports initiaux et analyses corrigées distincts. '
      'Les contrôles supplémentaires de KE/P reconstruits et somme de toutes les REAC échouent : ces conventions sous mouvements imposés restent NON qualifiées, ne pas inventer de RKE ni terme compensateur. '
      'La seule impulsion des supports sur Y libre concorde avec la quantité de mouvement reconstruite à~1,6e-10Ns, mais cette observation exploratoire ne ferme pas les trois directions imposées. '
      'Trois régressions explicites mixtes :297canaux égaux bit à bit aux A60 ; deux témoins TYPE7/MUMPS et demi-pas passent les critères source/énergie/momentum A45. Échecs bruts de champs natifs de l’auditeur historique conservés, qualification publiée limitée au lecteur source. '
      'Aucun nouveau CHECK entier ou longue extension car l’intégration locale complète reste non qualifiée. CHECK entier cached15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré. '
      'Meilleur impact entierA20=0,0200001220703125s, aucun crédit des témoins ; objectif dix secondes physiques puis vidéo3D incomplet. Publication prochaine après paireA62+A63. '
      'Toute nouvelle modification/compilation de moteur hors interface déjà réparée exige une proposition concrète et un accord distinct.')

def assess():
    assert not REPORT.exists() and read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    built=read(OUT/'build_finished.json');assert built['build_success'] and built['within_original_hour'] and built['CPU_threads']==6 and not built['GPU']
    assert read(OUT/'exact_surface_patch_application.json')['matches_approved_A61_source_exactly']
    assert read(OUT/'exact_interface_declaration_R2_application.json')['same_helper_code_and_mechanical_equations']
    auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a62_authorization.json');assert auth['explicit_human_authorization']
    native=list(OUT.rglob('engine.execution.json'));assert len(native)==10
    for p in native:assert read(p)['cap_s']==180 and read(p)['CPU_threads']==1 and not read(p)['GPU']
    explicit=read(OUT/'explicit_regressions/regression_review.json');contact=read(OUT/'contact_controls/contact_review.json');obs=read(OUT/'initial_free_motion_source_observable_review.json')
    assert explicit['pass'] and all(c['every_channel_literal_bit_equal'] for c in explicit['cases']) and contact['pass']
    assert not obs['pass'] and len(obs['cases'])==3
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
    for row in old:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),'changed_paths':changed,'all_old_files_rehashed':False,'old_Engine_hashes_verified_during_build':built['old_Engines_hash_verified'],'old_native_Engine_replays':0,'old_manifests_and_failures_preserved':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A62','status':'completed_authorized_sixth_Engine_surface_iteration_and_loaded_witnesses__full_implicit_observables_remain_unqualified',
      'binary_sha256':built['binary_sha256'],'candidate_directory':built['candidate_directory'],'build_wall_s_including_interface_repair':built['wall_s_from_original_start'],'within_original_hour':True,'CPU_build':6,'GPU':False,'installation':False,
      'exact_A61_source_initially_applied':True,'compiler_interface_only_repair':True,'helper_executable_equations_unchanged':True,'R0_R1_compile_failures_preserved':True,
      'new_Engine_runs':10,'new_Starter_runs':4,'native_controls_authorized_maximum':12,'authorized_native_controls_remaining':2,
      'at_rest_zero_reference_convergence_failed':True,'initial_motion_loaded_cases_normal':3,'cohesive_traction_work_G_reload_checks_pass':True,'source_observable_composite_pass':False,'prescribed_KE_P_and_total_REAC_interpretation_qualified':False,
      'explicit_regression_cases_pass':3,'explicit_channels_bit_equal':297,'TYPE7_native_contact_cases_pass':2,'TYPE7_half_dt_pass':True,
      'native_material_state_rollback_directly_qualified':False,'large_rotations_qualified':False,'whole_insertion_ready':False,'new_whole_CHECK_executed':False,
      'physical_whole_budgets_changed':False,'RKE_added':False,'failed_criteria_preserved':True,'whole_CHECK_cached_errors':15,'whole_cached_zero_volume_messages':624,'whole_cached_TYPE25_ignored':5,'A52_integrated':False,
      'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A63'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'build':'build_finished.json','at_rest_failure':'elastic_mechanical_review.json','convergence_log':'Newton_log_execution_review.json','explicit':'explicit_regressions/regression_review.json','TYPE7':'contact_controls/contact_review.json','loaded_initial_motion':'initial_free_motion_source_observable_review.json','raw_aggregate_JSON_serialization_failure_preserved':'initial_free_motion_mechanical_review.json','whole_impact_qualified':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A62 — sixième moteur et réponse cohésive chargée limitée

Le correctif surfacique autorisé est appliqué et le sixième moteur isolé compilé. Trois témoins chargés avec petite vitesse initiale libre atteignent1ms et concordent sur les tractions et le travail cohésif. La qualification implicite complète reste ouverte : démarrage au repos et certains observables cinétiques/impulsions échouent. Aucun temps d’impact entier gagné.

## 1. Faits directement observés ou transcrits

Accord humain A61 reçu et sauvegardé avant l’application. R0 applique exactement la source approuvée puis échoue à la compilation : interface explicite requise pour l’argument TARGET. R1 ajoute cette déclaration mais suppose un type WP absent ; cet échec est conservé. R2 utilise la macro native my_real. Seules les déclarations d’interface sont réparées, aucune équation exécutable du helper changée. Reprise du même sixième chantier partiel, plafond initial1h inchangé, CPU6/sansGPU/installation. Anciennes empreintes de moteurs vérifiées. Binaire d36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235, image de compilation démontée après chaque tentative.

Dix nouveaux Engine CPU1/plafond180s chacun, quatre nouveaux Starter propres. Le témoin normal au repos et sa variante de journal Newton s’arrêtent code2, après réductions du pas jusqu’à la limite, àT=0. Plus de STOP volume nul ; factorisation/solve MUMPS observés sans pivot négatif. Le journal montre résidu relatif de force0, déplacement NaN et énergie Infinity, puis limite de30itérations. L’échec initial n’est pas déclaré corrigé.

Trois nouveaux témoins normal élastique/mixte cyclique/mixte demi-pas gardent les trois critères123 et tolérances1e-11. La seule nouvelle condition est une vitesse initiale0,01mm/ms sur Y libre des quatre nœuds supérieurs instrumentaux : énergie initiale2e-7J déclarée, masse8g constante. Ils terminent normalement ; tractions trois axes, travail cohésif, bilan global natif, G mixte, recharge et demi-pas passent. Les directions imposées sont conformes ; Y est libre et dérive après séparation. Les trois régressions explicites du nouveau binaire sont égales bit à bit aux297canaux A60. Deux témoins TYPE7/MUMPS et demi-pas passent les contrôles source de cinématique/énergie/momentum A45.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Sources logicielles figées et trois anciens correctifs conservés. Dépendances legacyMUMPS installées déjà disponibles, aucune installation ; différence déclarée71/67 du cache de dépendances conservée. Sources/différences brutes AGPL restent hors des livrables publics MIT. Le lecteur source A41 décrit les vitesses TH Newmark comme sécantes, avec reconstruction des vitesses physiques pour les degrés libres ; appliquer cette reconstruction sans distinction à des déplacements imposés n’a pas validé tous les compteurs. Les échecs bruts de champs natifs du vieil auditeur TYPE7 restent archivés ; le passage des témoins est celui de son lecteur source/compteurs, pas une nouvelle qualification de tous les champs bruts.

## 3. Affirmations provenant des archives locales

Aucune archive historique, image, vidéo ou PDF consulté/modifié. Aucun ajustement à des dégâts connus.

## 4. Hypothèses propres au modèle

Graine1102087, aucun tirage. Surface TYPE43/LAW117/Ismstr1 à hauteur nulle, EN/ET/TN/TT/G inchangés, masse instrumentale8g ; petite vitesseY ajoutée uniquement dans des variantes déclarées, aucun budget avion/façade changé. Matrice symétrique d’itération élastique, pas une tangente cohérente de dommage/géométrie. La qualification chargée reste plane et prescrite dans les directions principales. Les autres cas initialement prévus sont arrêtés après le premier échec au repos ; dommage non proportionnel sans mouvement initial non exécuté. Deux contrôles natifs restent dans la limite totale autorisée12, sans la réinitialiser.

## 5. Résultats dérivés

Le STOP volumique du témoin est franchi par la branche surfacique, avec réponse chargée limitée obtenue ensuite. Les bilans traction/travail natifs passent dans les variantes déclarées. Une analyse initiale compare à tort tous les axes à la trajectoire imposée, puis une analyse source séparée distingue Y libre, utilise déplacement×impulsion pour le travail et conserve les échecs. Le demi-pas dispose d’une animation finale0,9955ms et d’un échantillon nodal TH binaire/CSV complet à1ms ; ce champ réel est consigné sans extrapolation ni modification d’horloge. Erreurs relatives de traction≤0,003939, travail externe/cohésif concordant, énergie finale mixte~5,2219J et demi-pas concordant.

Une analyse supplémentaire reconstruit les vitesses des trois directions et somme toutes les REAC : ses critères KE/P/impulsion échouent et restent ouverts. Observation exploratoire distincte : sur Y libre, la quantité de mouvement reconstruite concorde avec le seul support inférieur à~1,6e-10Ns ; sommer aussi les nœuds libres annule l’impulsion interne et ne donne pas le bilan externe. Les directions imposées exigent encore une interprétation source complète. Aucun terme RKE, masse ou compensation ajouté pour fermer ces déficits. Une erreur de sérialisation numpy.bool produit un JSON agrégé partiel, conservé comme échec technique ; analyses ultérieures valides dans leurs fichiers séparés.

## 6. Contradictions et informations manquantes

Démarrage exact au repos, compteurs dans les directions imposées, retour arrière d’état directement observé et grandes rotations restent non qualifiés. Les données limitées ne valident pas une loi de fracture physique Boeing/WTC1 ou un impact entier. Aucun nouveau CHECK entier/extension longue. Ancien CHECK15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré et critères locaux/matériaux entiers échoués conservés. Meilleure fenêtre entière0,0200001220703125s ; dix secondes physiques puis vidéo3D restent incomplètes. A63 utilise les deux contrôles restants pour vérifier une dynamique libre cohésive sans ambiguïté de mouvement imposé.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A62 → AIRCRAFT-A63\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a62*.py'))+[CFG,ROOT/'wtc1_simulation_v8/data/aircraft_a62_authorization.json',ROOT/'wtc1_simulation_v8/data/aircraft_a62_builder_derivation.json',HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'raw_AGPL_source_patch_and_binary_outside_public_MIT_manifest':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A62_assessed':True,'new_native_Engine':10,'remaining_authorized':2,'whole_credit':0}),flush=True)

source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a60.py').read_text(encoding='utf8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='register');s=ast.get_source_segment(source,node)
s=s.replace('AIRCRAFT-A61','AIRCRAFT-A63').replace('AIRCRAFT-A60','AIRCRAFT-A62').replace('aircraft_a60','aircraft_a62').replace('179','181').replace('A60_registered','A62_registered').replace('AIRCRAFT-A62+AIRCRAFT-A63 verified','AIRCRAFT-A62+AIRCRAFT-A63 verified')
exec(compile(s,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
