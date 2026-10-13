"""Seal two exact discrete/free-conservation passes and preserved temporal failure."""
from free_aircraft_a63_cohesive import ROOT,OUT,CFG,read,dump,sha,now,rel,harness
import json,ast

REPORT=OUT/'rapport_aircraft_a63.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A63_HANDOFF.md'

def route():
    return ('AIRCRAFT-A64 : douze Engine autorisés A61 consommés au total A62(10)+A63(2). Ne pas dépasser ce budget sans nouvel accord. '
      'Préparer puis demander un accord pour deux témoins libres raffinés dt0,000125/0,0000625ms, CPU1/cap180s chacun, sur le moteur A62 inchangé, sans compilation/GPU/installation ; si leurs critères passent, deux CHECK entiers bornés original/paireA53 avec les mêmes entrées, aucune extension dynamique. '
      'A63 chaque trajectoire libre concorde avec la solution Newmark discrète exacte et les bilans physiques K/P/support/IE ; maxrésidu énergie8,82e-9J, impulsion1,10e-8Ns. '
      'Mais comparaison demi-pas0,001/0,0005ms échoue : différence KE/IE~0,00034846J >tol1,01e-5J. Échec conservé ; dispersion temporelle théorique explique le déphasage, pas de modification du seuil. '
      'Le nouveau pas proposé vient de l’erreur du modèle analytique prédeclared, sans ajuster matériau/masse ni dégâts ; ne pas le transposer à l’avion puisque les masses instrumentales sont artificielles. '
      'A62 : correctif surfacique compilé, sixième moteur SHAd36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235. Démarrage au repos NaN/Infinity et observables imposés KE/P restent échoués/non qualifiés ; les variantes chargées passent traction/travail, pas une qualification entière. '
      'Trois régressions explicites297canaux bits identiques, deux TYPE7/MUMPS source énergie/momentum et demi-pas passent, échecs bruts conservés. '
      'CHECK entiercached15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré ; aucun nouveau CHECK ni extension. Budgets/anciennes sorties et critères préservés, aucun RKE compensateur. '
      'Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. PublicationA62+A63 à vérifier, prochaine cadenceA64+A65. '
      'Toute future modification/compilation moteur supplémentaire demande un accord distinct sur une proposition concrète.')

def assess():
    assert not REPORT.exists() and read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];r=read(OUT/'free_cohesive_qualification_review.json');disp=read(OUT/'dispersion_and_next_step_review.json')
    assert all(c['pass'] for c in r['cases']) and not r['pass'] and all(not c['pass'] for c in r['half_dt_energy_comparisons'])
    assert len(list(OUT.rglob('engine.execution.json')))==2
    assert len(list((ROOT/'wtc1_simulation_v8/output/aircraft_a62').rglob('engine.execution.json')))==10
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
    for row in old:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),'changed_paths':changed,'old_manifests_and_failed_gates_preserved':True,'all_old_files_rehashed':False,'old_Engine_replays':0,'archives_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A63','status':'completed_free_cohesive_native_conservation_and_exact_discrete_solution__half_dt_temporal_gate_failed',
      'new_Engine_runs':2,'new_Starter_runs':2,'new_software_changes_or_compilation':False,'A62_A63_native_total':12,'original_A61_native_authorized_cap':12,'authorized_controls_remaining':0,
      'native_free_case_checks_pass':2,'all_free_case_boolean_checks_pass':sum(len(c['checks']) for c in r['cases']),'maximum_energy_residual_J':max(c['maximum_energy_residual_J'] for c in r['cases']),
      'maximum_support_momentum_residual_Ns':max(c['maximum_support_momentum_residual_Ns'] for c in r['cases']),
      'physical_free_velocity_energy_momentum_source_interpretation_pass':True,'exact_linear_Newmark_solution_pass':True,'half_dt_temporal_pass':False,
      'half_dt_maximum_energy_difference_J':max(c['maximum_difference_J'] for c in r['half_dt_energy_comparisons']),'half_dt_tolerance_J':r['half_dt_energy_comparisons'][0]['tolerance_J'],
      'next_refined_dt_pair_ms':disp['proposed_next_pair_dt_ms'],'threshold_changed':False,'parameter_or_mass_fitting':False,'initial_generation_failure_preserved':True,
      'A62_at_rest_and_prescribed_counter_failures_preserved':True,'mixed_damage_large_rotations_native_rollback_or_whole_qualified':False,'new_whole_CHECK':False,'A52_integrated':False,
      'whole_budgets_changed':False,'RKE_added':False,'old_outputs_failures_preserved':True,'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A64'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'native':'free_cohesive_qualification_review.json','dispersion':'dispersion_and_next_step_review.json','input_generation_failure':'generation_R0_failure_review.json','whole_impact_qualified':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A63 — dynamique libre exacte, convergence temporelle échouée

Les deux derniers contrôles autorisés du moteur A62 passent séparément les bilans physiques de dynamique libre et la solution Newmark discrète exacte. Leur comparaison demi-pas échoue : le déphasage temporel est encore trop grand. Aucun seuil modifié ni ancien échec effacé, aucun crédit d’impact entier.

## 1. Faits directement observés ou transcrits

Deux nouveaux Starter sans erreur/avertissement, deux Engine A62 CPU1/plafond180s/sansGPU, terminés normalement. La limite autorisée A61 est consommée : A62 dix Engine+A63 deux=12. Aucun ancien Engine rejoué, aucun patch/compilation supplémentaire. Une première préparation propre omettait un import de générateur, échouant avant Starter/Engine ; script/dossier/erreur conservés, dépendances importées, aucune entrée ni critère modifié.

Chaque essai passe22contrôles : canaux binaires/CSV, grille/pas/horloges natives, identité sécante, vitesse physique reconstruite, énergie cinétique et quantité de mouvement comparées aux compteurs natifs, conservation énergétique et impulsion des seuls supports, masse8g, masse ajoutée0, travail externe0, réponse analytique du ressort surfacique, tractions et domaine élastique. Erreur de déplacement analytique≤7,24e-10mm, vitesse≤2,35e-6mm/ms ; résidu énergétique≤8,82e-9J et quantité de mouvement/support≤1,10e-8Ns. Les sorties réelles atteignent1ms ; horloges ANIM/TH distinctes conservées.

Cependant KE et IE diffèrent jusqu’à0,00034846J entre les pas0,001 et0,0005ms, pour une tolérance déclarée1,01e-5J : les deux critères de comparaison échouent. Le composé global est FALSE, malgré les passages par cas.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Le moteur A62 inchangé conserve ses sources figées/correctifs précédemment autorisés. Le protocole Newmark gamma0,5/beta0,25 reconstruit les vitesses physiques depuis les sécantes TH sur les degrés réellement libres ; les compteurs natifs concordent ici, indépendamment des sorties sous mouvements imposés A62. La formule de phase exacte du schéma linéaire est utilisée comme référence mathématique, sans ajustement aux sorties :2atan(omega·dt/2).

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF consulté/modifié. Aucun dégât connu ciblé.

## 4. Hypothèses propres au modèle

Graine1102088, zéro tirage. Face10×10mm, matériau témoin A60/A62 conservé ; quatre nœuds supérieurs de1g libres, quatre inférieurs de1g fixes, vitesse initialeY1mm/ms. Aucun déplacement/vitesse imposé durant le calcul, travail externe nul. Raideur surfacique totale80000N/mm, masse mobile4g, omega=sqrt(80000/4)ms⁻¹. Le maximum de cisaillement reste sous le seuil élastique. Cette masse instrumentale et ces propriétés ne représentent pas l’avion réel et ne déterminent pas son futur pas de calcul.

## 5. Résultats dérivés

La branche native surfacique donne la bonne dynamique libre dans son domaine élastique, avec conservation vérifiée et réponse conforme au schéma discret. Elle ne démontre pas la convergence temporelle au pas courant. La dispersion exacte explique le déphasage cumulé sur1ms ; les seuils de comparaison restent inchangés. Une étude analytique détermine la première paire plus fine dont la borne de différence énergétique respecte cette tolérance :0,000125/0,0000625ms. Aucun matériau/masse/géométrie ajusté, aucune tentative native supplémentaire lancée au-delà de12. Les paramètres, scripts, références et anciennes sorties sont préservés, harnais PASS.

## 6. Contradictions et informations manquantes

Échec demi-pas conservé ; un accord supplémentaire est requis pour dépasser le lot de12contrôles accepté. Démarrage exact au repos et observables prescrits A62 restent échoués/non qualifiés. Retour arrière natif d’état, dommage général et grandes rotations non qualifiés. Aucun nouveau CHECK entier ou insertion A52. Ancien CHECK15erreurs/624volumes/cinqTYPE25 ignorés, budgets et critères locaux/matériaux échoués conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D restent incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A63 → AIRCRAFT-A64\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a63*.py'))+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'owned_results_only_no_third_party_binary_source_or_patch':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A63_assessed':True,'case_checks_pass':44,'half_dt_pass':False,'authorized_native_remaining':0}),flush=True)

source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a61.py').read_text(encoding='utf8')
register_source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a60.py').read_text(encoding='utf8');node=next(n for n in ast.parse(register_source).body if isinstance(n,ast.FunctionDef) and n.name=='register');s=ast.get_source_segment(register_source,node)
s=s.replace('AIRCRAFT-A61','AIRCRAFT-A64').replace('AIRCRAFT-A60','AIRCRAFT-A63').replace('aircraft_a60','aircraft_a63').replace('179','182').replace('A60_registered','A63_registered')
s=s.replace("cycle['pending_iterations']==[]","cycle['pending_iterations']==['AIRCRAFT-A62']").replace("pending_iterations=['AIRCRAFT-A63'],pending_count=1","pending_iterations=['AIRCRAFT-A62','AIRCRAFT-A63'],pending_count=2").replace('AIRCRAFT-A63+AIRCRAFT-A64 verified','AIRCRAFT-A62+AIRCRAFT-A63 verified').replace("'pending_publication_count':1","'pending_publication_count':2")
exec(compile(s,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
