"""Seal owned iteration checks and the exact still-unapplied native proposal."""
from prepare_aircraft_a61_surface_iteration import ROOT,OUT,CFG,read,dump,sha,now,rel,harness
import json,ast

REPORT=OUT/'rapport_aircraft_a61.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A61_HANDOFF.md'

def route():
    return ('AIRCRAFT-A62 : correctif A61 prêt, NON appliqué/NON compilé. Proposition : wtc1_simulation_v8/output/aircraft_a61/proposition_correctif_surface_implicite.md. '
      'Demander un accord humain explicite distinct pour la différence exacte de s8zke3.F, sixième moteur isolé, compilation cap1h/CPU6/sansGPU/sansinstallation et au maximum12 Engine CPU1/cap180s. '
      'SHA patch1c2c9b74239d75883234057d2ae0f1e28d0dd017abb5fa99aa8deaad89b3a3b8 ; source proposée53a6d683bff4e2f3124ac98d2743f74777107890031b5e407af489859407f35e. '
      'Branche TYPE43+LAW117+Ismstr1, quatre aires natives de référence et normale courante, matrice symétrique élastique d’itération, forces/loi/histoire natives inchangées ; pas une tangente exacte. '
      '44 contrôles propres A61 passent ; neuf équilibres mixtes à résidu complet avec état validé gelé. Échec bit à bit R0 archivé, R1 applique la tolérance matricielle1e-12 déjà déclarée. '
      'A60 six témoins explicites nouveaux et22contrôles de dérivée passent, pas de nouveau solver A61. Retour arrière des états natifs, convergence et grandes rotations restent non qualifiés et conditionnent les contrôles. '
      'Ne pas seulement ignorer le STOP volume, changer SYM ou inventer une épaisseur. Ne pas intégrer au modèle entier avant contrôles locaux natifs. '
      'Moteur A57inchangé SHA34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528. Anciennes cinq sorties/moteurs, budgets et critères échoués préservés. '
      'CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré. Meilleur impact entierA20=0,0200001220703125s, aucun crédit physique A60/A61. '
      'Objectif dix secondes physiques puis vidéo3D incomplet. PublicationA60+A61 à vérifier, prochaine cadenceA62+A63. Aucun diagnostic ancien à rejouer sans une nouvelle question.')

def assess():
    assert not REPORT.exists() and read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    good=read(OUT/'symmetric_surface_iteration_review_R1.json');bad=read(OUT/'symmetric_surface_iteration_review.json');patch=read(OUT/'surface_patch_proposal_review.json')
    assert good['pass'] and len(good['checks'])==44 and not bad['pass']
    assert not patch['compiled'] and not patch['new_source_patch_applied']
    for path,key in [('patch_path','patch_sha256'),('proposed_source_path','proposed_sha256')]:assert sha(ROOT/patch[path])==patch[key]
    rows=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
    for row in rows:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(rows),'changed_paths':changed,'all_old_files_rehashed':False,'old_manifests_preserved':True,'old_Engine_replays':0,'source_archives_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A61','status':'completed_owned_symmetric_surface_iteration_and_exact_native_patch_proposal__unapplied_uncompiled_awaiting_distinct_approval',
      'owned_checks_pass':44,'mixed_equilibrium_roots_converged':9,'original_bit_equality_failure_preserved':True,'matrix_tolerance_changed':False,
      'native_Engine_runs':0,'Starter_runs':0,'new_Engine_patch_applied':False,'new_Engine_compiled':False,'proposal':rel(OUT/'proposition_correctif_surface_implicite.md'),
      'patch_sha256':patch['patch_sha256'],'proposed_source_sha256':patch['proposed_sha256'],'requires_distinct_human_approval':True,
      'matrix_is_exact_Jacobian':False,'native_residual_history_sources_unchanged':True,'native_Newton_state_rollback_qualified':False,'moving_geometry_native_convergence_qualified':False,'whole_insertion_ready':False,
      'budgets_changed':False,'RKE_added':False,'old_outputs_failed_gates_preserved':True,'whole_CHECK_errors_preserved':15,'whole_zero_volume_messages_preserved':624,'TYPE25_ignored_preserved':5,'A52_integrated':False,
      'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A62'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'owned_prototype':'symmetric_surface_iteration_review_R1.json','preserved_failure':'symmetric_surface_iteration_review.json','source_contract':'surface_patch_source_contract_review.json','exact_patch':'surface_patch_proposal_review.json','whole_impact_qualified':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A61 — matrice surfacique d’itération et proposition native

Une différence exacte du moteur est préparée pour traiter la rigidité surfacique TYPE43/LAW117/Ismstr1.44contrôles propres passent. Aucun patch appliqué, aucune compilation, aucun nouveau Starter/Engine et aucune seconde entière gagnée. L’application/compilation du sixième moteur attend un accord humain distinct.

## 1. Faits directement observés ou transcrits

Calcul propre CPU1/sansGPU/plafond120s, deux exécutions de moins d’une seconde. R0 échoue uniquement à une égalité bit à bit de reconstruction triangulaire sur les poids non uniformes : erreur relative5,3812e-17. R0, script, résultat et journal sont conservés. R1 utilise la tolérance matricielle1e-12 déjà déclarée ; aucun seuil changé.44contrôles passent : matrices symétriques et non négatives, rang12, translations nulles, forces équilibrées, aire uniforme/nonuniforme, covariance sous rotation3D, reconstruction par blocs triangulaires, retrait des points supprimés, géométries invalides rejetées. Neuf résolutions approximatives gardent le résidu mixte complet et l’état validé gelé, convergent au même équilibre que les cibles déclarées. La matrice approximative se distingue explicitement de la dérivée exacte mixte.

## 2. Résultats d’un modèle officiel

Aucune nouvelle simulation historique officielle. Dix fichiers primaires du logiciel figé sont inspectés en lecture seule ; empreintes/lignes et contrats consignés. Le chemin surfacique utilise effectivement ASSEM_KII/ASSEM_KIJ ; A60 avait inspecté les variantes ASSEMC, et A61 confirme la même limite triangulaire dans les routines réellement appelées. SUSER43 sauvegarde quatre aires de référence dans LBUF%VOL à T=0 pour Ismstr1 ; SDEF43 donne les quatre colonnes de forme ; SCOOR43 utilise le plan moyen courant et SUSER43 appelle SIGEPS117. Les sources de copie d’états sont repérées mais leur ordre complet de restauration Newton n’est pas qualifié.

## 3. Affirmations provenant des archives locales

Aucune archive historique, image, vidéo ou PDF consulté/modifié. Dégâts observés non utilisés comme cible.

## 4. Hypothèses propres au modèle

Graine1102086, aucun tirage ; paramètres cohésifs A60 conservés. Matrice d’itération élastique Bᵀ[ET I+(EN−ET)n nᵀ]B intégrée sur les quatre aires de référence, avec points actifs natifs. Normale du plan moyen courant, cisaillement isotrope. Elle omet les dérivées du dommage et de la géométrie : approximation d’itération explicitement distincte d’une tangente cohérente. Le contrôle d’équilibre utilise une rigidité extérieure fictive4×la rigidité matérielle, uniquement pour tester numériquement les itérations ; aucun paramètre avion/façade ajouté. L’état validé est gelé dans le prototype propre, sans preuve du comportement natif.

## 5. Résultats dérivés

La proposition modifie seulement s8zke3.F dans une copie préparatoire hors des livrables MIT. Une routine ajoutée au même fichier est appelée avant la rigidité volumique dans la branche déclarée, puis assemble les blocs surfaciques. Les forces natives, SIGEPS117, les états et l’énergie ne sont pas réécrits. Les configurations non admissibles provoquent un arrêt fermé code61, qui restera un échec. Aucun volume/épaisseur fictif, changement de masse/matériau, RKE ajouté, drapeau MUMPS changé ou seuil physique assoupli. Différence/source proposées et empreintes exactes sauvegardées, code nouveau à72colonnes contrôlé statiquement, aucune compilation Fortran revendiquée.

Une compilation isolée AIRCRAFT-A62 est proposée : sixième moteur, trois anciens correctifs conservés, estimation5–15minutes/plafond1h/CPU6/sansGPU/sansinstallation ; puis au maximum12 nouveaux contrôles natifs CPU1/plafond180s chacun. Les anciens cinq moteurs restent intacts. La proposition concrète exige l’accord explicite distinct prévu par AGENTS.md avant application/compilation. Préservation/harnais PASS, aucune publication de source brute/différence AGPL dans l’archive MIT.

## 6. Contradictions et informations manquantes

La matrice approchée peut ralentir/échouer en adoucissement ou grandes rotations ; la convergence native et le retour arrière d’état doivent être mesurés. Le candidat peut rencontrer un agencement natif différent et s’arrêter code61. Ces risques ne sont pas masqués par le prototype. Branches Ismstr autres que1 non traitées. Aucun patch logiciel appliqué/compilé et aucune intégration entière qualifiée. CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, A52 non intégré, critères locaux/matériaux échoués conservés. Meilleure fenêtre entière0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D toujours incomplet.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A61 → AIRCRAFT-A62\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(OUT/'proposition_correctif_surface_implicite.md')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a61*.py'))+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'raw_AGPL_source_and_patch_excluded':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A61_assessed':True,'owned_checks':44,'new_Engine':0,'patch_applied':False}),flush=True)

source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a60.py').read_text(encoding='utf8')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='register')
s=ast.get_source_segment(source,node)
s=s.replace('AIRCRAFT-A61','AIRCRAFT-A62').replace('AIRCRAFT-A60','AIRCRAFT-A61').replace('aircraft_a60','aircraft_a61').replace('179','180').replace('A60_registered','A61_registered')
s=s.replace("cycle['pending_iterations']==[]","cycle['pending_iterations']==['AIRCRAFT-A60']")
s=s.replace("pending_iterations=['AIRCRAFT-A61'],pending_count=1","pending_iterations=['AIRCRAFT-A60','AIRCRAFT-A61'],pending_count=2")
s=s.replace('AIRCRAFT-A61+AIRCRAFT-A62 verified','AIRCRAFT-A60+AIRCRAFT-A61 verified').replace("'pending_publication_count':1","'pending_publication_count':2")
exec(compile(s,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
