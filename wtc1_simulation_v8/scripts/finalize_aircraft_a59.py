"""Seal the owned limited surface prototype; no native integration or whole credit."""
from prepare_aircraft_a59_surface import ROOT,OUT,CFG,read,dump,sha,now,rel,harness
from pathlib import Path
import ast,json

REPORT=OUT/'rapport_aircraft_a59.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A59_HANDOFF.md'

def route():
    return ('AIRCRAFT-A60 : prototype propre de surface A59 disponible dans surface_aircraft_a59.py,112contrôles passent dans le domaine déclaré. '
      'Compléter et qualifier les modes mixtes selon SIGEPS117, états d’essai et validation/retour arrière de Newton, repères mobiles et tangente géométrique avant une différence moteur concrète. '
      'Le noyau A59 couvre plans rectangulaires, matrice élastique3axes et tangente ACTIVE de modes purs normaux/cisaillement à adoucissementlinéaire. '
      'Les directions passives gardent le dommage gelé ; cela ne qualifie pas le couplage mixte de LAW117. '
      '112tests :équilibre,intégralefermée, rang12 et translationsnulles, différencesfinies de tangente, adoucissement négatif, rotations de repère3D, quatre témoinsnatifsA57 réutilisés sans rerun, travail et rechargement. '
      'SUSER43 décritSTIFM comme surestimation pour le pas explicite ; ne pas l’assimiler à une tangente implicite cohérente. '
      'Aucun patch moteur proposé/appliqué ou compilationA59, zéro nouveau Engine/Starter ; toute future modification/compilation moteur exige un accord explicite distinct après proposition concrète. '
      'Moteur A57 conservé34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528 ; mémoire du témoin corrigée, mais STOP de jacobienvolumiqueTYPE43 reste. '
      'A58ordre natif surface puis rigidité volumique connu, ne pas le rejouer. CHECKentier15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré, budgets/critèreséchoués conservés. '
      'Meilleur impact entierA20=0,0200001220703125s ; ne pas prolonger cet état horsdomaine vers10s. '
      'Coût historiqueA20=1191,4197075s pour20ms, projection linéaire6,89479jours pour10s est seulement un ordre de grandeur ancien, pas une ETA ni une autorisation d’extension. '
      'A20 ne modélisait pas gravité/intérieurporteur et ses critèreslocaux/matériaux échouaient ; aucune extrapolation de ces lacunes à une nouvelle scène sans inspection. '
      'Objectif1 dix secondes physiques puis vidéo3D incomplet, aucun crédit des témoins ou prototype. PublicationA58+A59 à vérifier, ensuite cadenceA60+A61. Aucun ancien solver rejoué.')

def assess():
    assert not REPORT.exists();assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json');assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    p=read(OUT/'surface_prototype_review.json');extra=read(OUT/'additional_oracle_review.json');assert p['pass'] and extra['pass']
    assert len(p['checks'])==92 and len(extra['checks'])==20
    execution=read(OUT/'prototype_execution.json');assert execution['exit_code']==0 and execution['cap_s']==120 and execution['CPU']==1 and not execution['GPU']
    old_route=ROOT/'wtc1_simulation_v8/output/aircraft_a20/objectif1_route.json';old_assessment=old_route.parent/'scientific_assessment.json';v=read(old_route);a20=read(old_assessment)
    assert v['seconds_extension_allowed'] is False
    dump(OUT/'cached_whole_extension_limit_review.json',{'created_utc':now(),'cached_only_no_new_solver':True,'sources':[{'path':rel(q),'sha256':sha(q)} for q in [old_route,old_assessment]],'A20_horizon_s':v['coverage_s'],'A20_wall_s':v['whole_20ms_wall_s'],'A20_linear_10s_days':v['linear_10s_days'],'linear_projection_is_not_current_ETA':True,'A20_seconds_extension_allowed':False,'A20_gravity_modelled':a20['gravity_modelled'],'A20_tower_interior_modelled':a20['tower_interior_modelled'],'A20_local_energy_pass':a20['local_energy_pass'],'newer_unexecuted_scene_missing_features_not_inferred':True,'original_failed_gates_preserved':a20['failed_whole_checks']})
    old=read(OUT/'preservation_before_metadata.json');changed=[]
    for row in old['files']:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old['files']),'changed_paths':changed,'old_hash_manifests_preserved':True,'all_old_files_rehashed':False,'cached_native_diagnostics_fresh_hash_verified_before_use':True,'archives_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A59','status':'completed_owned_planar_surface_pure_mode_residual_tangent_prototype__native_Engine_integration_unqualified',
       'prototype_checks_pass':112,'initial_oracles_pass':92,'additional_3D_frame_and_reload_checks_pass':20,'cached_native_controls_reused_without_rerun':4,
       'active_pure_mode_tangent_FD_pass':True,'elastic_rank12_closed_integral_and_equilibrium_pass':True,'arbitrary_3D_reference_frame_covariance_pass':True,'native_Engine_executions':0,'Starter_launches':0,
       'mixed_mode_damage_qualified':False,'moving_frames_and_geometric_tangent_qualified':False,'Newton_trial_state_commit_rollback_qualified':False,'native_Engine_surface_integration_ready':False,'new_Engine_patch_or_compile':False,
       'budgets_changed':False,'RKE_added':False,'old_outputs_and_failed_gates_preserved':True,'whole_CHECK_errors_preserved':15,'whole_zero_volume_messages_preserved':624,'TYPE25_ignored_preserved':5,'A52_integrated':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'whole_insertion_ready':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A60'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'initial_oracles':'surface_prototype_review.json','additional_oracles':'additional_oracle_review.json','historical_whole_limits':'cached_whole_extension_limit_review.json','physical_whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A59 — prototype de surface et tangente active en modes purs

Un prototype propre utilisant l'aire de la surface passe112contrôles dans son domaine limité et concorde avec les quatre témoins explicites natifsA57 réutilisés. Il n'est ni une implémentation complète deLAW117 ni un correctif intégré au moteur. Aucun nouveau calcul Engine, aucune compilation, aucun temps physique d'impact entier supplémentaire.

## 1. Faits directement observés ou transcrits

Exécution Python propre, CPU1/sansGPU, plafond120s, résultats en moins d'une seconde.92contrôles initiaux passent, puis20contrôles additionnels répondent aux questions de rotation arbitraire3D et de courbe entière de travail/rechargement. Les quatre fichiers natifs en cache sont vérifiés par empreintes, aucun solver rejoué. Vérifications :équilibre nodal, translations nulles, matrice élastique d'intégrale fermée, rang12, spectre élastique non négatif, pente active négative en adoucissement, différences finies de la tangente active, covariance des forces/matrices sous rotation, traction native, travail de séparation, dommage irréversible et retour au même pic.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel ou solveur tiers exécuté. Les sources figéesSIGEPS117/SUSER43 indiquent une loi de traction surfacique et ses états internes ; SUSER43 décritSTIFM comme une surestimation destinée au pas de temps explicite. Il ne s'agit pas de sa tangente cohérente. Les branches mixtes et variablesUVAR deSIGEPS117 restent à transférer avec un traitement d'état correct avant tout patch natif.

## 3. Affirmations provenant des archives locales

Aucune archive historique, image, vidéo ouPDF consulté ou modifié. Aucun objectif de dégâts connus.

## 4. Hypothèses propres au modèle

Graine1102084, aucun tirage. Deux faces planes rectangulaires à hauteur nulle, quadrature2×2, repère de référence fixe. Le résidu est l'intégrale surfacique des tractions, la matrice active leur dérivée. Paramètres témoinsA17 conservés :EN4400N/mm³,ET800N/mm³,TN450MPa,TT100MPa,GI/GII50N/mm ; valeurs de référence sans fracture historique mesurée. Les modes purs normaux/cisaillement utilisent une enveloppe bilinéaire et un maximum irréversible. Les directions passives gardent ce dommage gelé : aucun couplage mixteLAW117 n'est qualifié. Les quatre points de Gauss partagent une histoire uniforme seulement dans les témoins en cache.

## 5. Résultats dérivés

Le noyau surfacique possède une rigidité non nulle sans volume fictif, avec équilibre et travail contrôlés dans ce domaine. Les différences finies actives et la matrice analytique donnent des références indépendantes pour une future connexion au moteur. Les seuils de traction, travail et rechargement sont ceux d'A17, inchangés. Aucun budget mécanique, masse, matériau ouRKE n'est modifié.

Un rappel ciblé de sortiesA20 déjà vérifiées conserve ses limites :1191,4197075s pour20ms, projection linéaire ancienne6,89479jours pour10s, explicitement pas une ETA actuelle. Cette ancienne scène ne modélisait ni gravité ni intérieur porteur et restait hors domaine sur plusieurs critères. Son fichier de route interdisait sa prolongation ; aucune prolongation ou répétition exécutée et aucune lacune déduite pour une scène plus récente non inspectée. Préservation par métadonnées/manifestes antérieurs, empreintes des fichiers natifs utilisés, harnaisPASS.

## 6. Contradictions et informations manquantes

Modes mixtes, repères mobiles, tangente géométrique, état d'essai/retour arrièreNewton et assemblage natif ne sont pas qualifiés. Le prototype passe ses propres contrôles mais ne valide pas l'impact entier. Les critèresA57/A58 restentéchoués : cohésion implicite àT=0, CHECK entier15erreurs/624volumes et cinqTYPE25 ignorés. A52 non intégré ; bilans locaux, domaines de matériau et autres travaux/inerties entiers restent ouverts. Meilleure fenêtre entière0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. Tout futur correctif logiciel demandera une proposition concrète et un accord explicite distinct avant application/compilation.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A59 → AIRCRAFT-A60\n\nRapport : '+rel(REPORT)+'\nPrototype : wtc1_simulation_v8/scripts/surface_aircraft_a59.py\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a59*.py'))+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'owned_prototype_only_no_external_engine_source':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A59_assessed':True,'prototype_checks':112,'native_transfer_qualified':False}),flush=True)

source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a55.py').read_text(encoding='utf8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='register');s=ast.get_source_segment(source,node)
s=s.replace('AIRCRAFT-A56','AIRCRAFT-A60').replace('AIRCRAFT-A55','AIRCRAFT-A59').replace('aircraft_a55','aircraft_a59').replace('A55_registered','A59_registered').replace('174','178')
s=s.replace("assert cycle['pending_iterations']==['AIRCRAFT-A54']","assert cycle['pending_iterations']==['AIRCRAFT-A58']").replace("pending_iterations=['AIRCRAFT-A54','AIRCRAFT-A59']","pending_iterations=['AIRCRAFT-A58','AIRCRAFT-A59']").replace('AIRCRAFT-A54+AIRCRAFT-A59 verified','AIRCRAFT-A58+AIRCRAFT-A59 verified')
exec(compile(s,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
