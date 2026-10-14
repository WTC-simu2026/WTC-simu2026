"""Seal cached read-only finite-formulation audit/prototype/proposal after pair publication."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a66'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a66_predeclaration.json'
PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a66_preparation_r1'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a66_proposal.json'
REPORT=OUT/'rapport_aircraft_a66.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A66_HANDOFF.md'

def route():
    return ('AIRCRAFT-A67 : septième moteur isolé proposé, non appliqué/non compilé ; '
      'attendre un nouvel accord humain explicite sur le correctif Ismstr4 et le plan borné avant toute modification/compilation. '
      'Source/différence exactes et52contrôles propres préparés en A66, actuelle brancheIsmstr1 conservée exactement. '
      'Ismstr4 requiert les aires Gauss projetées courantes, pas le tamponVOL de référence. '
      'Plafond compilation1hCPU6, puis maximum8EngineCPU1/cap180s, sansGPU/installation ; six témoins et deuxCHECK, aucune dynamique entière prolongée. '
      'Les cinqTYPE25 restent inchangés/bloquants et doivent faire l’objet d’une variante déclarée/contrôlée séparément. '
      'Conserver échecs, budgets, anciennes sorties, aucunRKE compensateur. '
      'Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.')

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness()
    assert h['CurrentIteration']=='AIRCRAFT-A65' and read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-14_aircraft_a64_a65/final_remote_verification.json');assert proof['pass']
    prep=read(PREP/'preparation_review.json');assert prep['pass'] and prep['plan_sha256']==sha(PLAN)
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(CFG,{**read(PLAN),'iteration':'AIRCRAFT-A66','created_utc':now(),'cached_preparation':rel(PREP),
        'successful_preparation_reused_without_rerun':True,'new_native_executions':0})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_sealing_no_native':True})
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a65';pins={r['path']:r for r in read(prior/'preservation_before_metadata.json')['files']}
    for row in read(prior/'artifact_manifest.json')['files']:pins[row['path']]=row
    for p in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':[{**r,'mtime_ns_before':(ROOT/r['path']).stat().st_mtime_ns} for r in pins.values()]})

def assess():
    assert not REPORT.exists() and read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];cfg=read(CFG);prep=read(PREP/'preparation_review.json')
    domain=read(PREP/'whole_domain_and_geometry_review.json');proto=read(PREP/'current_area_iteration_prototype_review.json')
    assert domain['pass'] and proto['pass'] and len(proto['checks'])==52
    assert sha(ROOT/cfg['patch']['proposed_source'])==cfg['patch']['proposed_sha256']
    assert sha(ROOT/cfg['patch']['patch'])==cfg['patch']['patch_sha256']
    for m in domain['models']:assert sha(ROOT/m['path'])==m['sha256']
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
    for row in old:
        s=(ROOT/row['path']).stat()
        if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'changed_paths':changed,'old_files_metadata_checked':len(old),
        'old_diagnostics_replayed':False,'whole_inputs_rehashed':True,'archives_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A66','status':'completed_finite_formulation_current_area_audit_and_exact_guarded_patch_proposal__not_applied_or_compiled',
       'new_native_Engine_or_Starter':0,'native_or_software_source_modified':False,'new_compilation':False,
       'flagged_whole_elements_mapped':624,'whole_formulation_Ismstr':4,'current_A62_scope_Ismstr':1,
       'minimum_current_Gauss_area_mm2':domain['minimum_current_GP_area_mm2'],'maximum_pair_height_mm':domain['maximum_pair_height_mm'],
       'native_Ismstr4_uses_current_AREAP':True,'reference_VOL_initialized_for_Ismstr1_only':True,
       'prototype_checks':52,'prototype_pass':True,'matrix_is_exact_Jacobian':False,
       'previous_Ismstr1_helper_byte_preserved':True,'new_source_patch':cfg['patch'],
       'patch_applied':False,'compiled_or_native_Ismstr4_qualified':False,
       'R0_R1_R2_R3_preparation_failures_preserved':True,'successful_prototype_replayed':False,
       'TYPE25_ignored_per_whole_scene_still_blocking':5,'whole_integration_ready':False,'whole_budgets_changed':False,'RKE_added':False,
       'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A67'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'geometry':rel(PREP/'whole_domain_and_geometry_review.json'),
        'prototype':rel(PREP/'current_area_iteration_prototype_review.json'),'proposal':prep['proposal'],
        'native_qualification_not_inferred_from_static_checks':True})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text(f'''# AIRCRAFT-A66 — formulation finie et aire courante, proposition non appliquée

Les624surfaces signalées par les nouveaux CHECK A65 sontTYPE43/LAW117/Ismstr4 ; la branche corrigéeA62 couvre seulementIsmstr1. Leur aire projetée est positive. Le contrôle volumique reste donc atteint dans le domaine non couvert. Un simple élargissement du test serait incorrect : le tamponVOL d’aire de référence n’est initialisé parSUSER43 que pourIsmstr1 ; Ismstr4 utiliseAREAPcourante.

## 1. Faits directement observés ou transcrits

L’audit relie exactement lesID60001–60624 des journaux/listings A65 aux624entréesBRICK du matériau117/propriétéTYPE43 Ismstr4 des deux anciennes scènes. Même géométrie cohésive entre original/apparié. Minimum d’aire Gauss projetée={domain['minimum_current_GP_area_mm2']:.12g}mm² ; hauteur maximale entre faces={domain['maximum_pair_height_mm']:.12g}mm. CinqTYPE25 présents, ignorés dans chaque CHECK et toujoursbloquants.

Les sources figées SUSER43/SCOOR43/SDET43/IMP_GLOB_K/IMP_SOLV sont lues depuis le cache local déclaré. SUSER43 écritVOL sousISMSTR1/TIME0 et emploieAREAP dans l’autre branche. A62 ne sélectionne le helper de surface que pourIsmstr1. Aucun nouveau Starter/Engine, aucune application/compilation. Les tentatives propres R0(parseBRICK), R1(ancre), R2(indentation), R3(recherche de signature) sont conservées ; leurs échecs précèdent toute application. Audit/prototype R1 réussi réutilisé sans recalcul, préparation exacte R4 réussie.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Pin source{cfg['source_pin']} et empreintes natives dans le plan. Les formules géométriques sources sont confrontées à une quadrature bilinéaire indépendante de l’aire projetée. Le moteurA62 actuellement qualifié dans le domaine libre élastiqueIsmstr1 reste inchangé. Aucun résultat de prototype propre n’est présenté comme un résultat natif du futur moteur.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photo ou PDF inspecté/modifié. Les matériaux d’interface restent des hypothèses numériques et ne sont pas identifiés par des dégâts connus.

## 4. Hypothèses propres au modèle

Graine1102091, zéro tirage ; aire enmm², matrice enN/mm, poids deGauss sur face médiane courante. Normale commune issue des directions bilinéaires de la face. La matrice symétrique conserve l’élasticitéENnormale/ETtangente, ne prend pas les dérivées de dommage/repère/aire et reste une matrice d’itération, pas un jacobien exact. Seuils du prototype A61 conservés ; références de comparaison nouvelles : aires nativesSDET43, évolution d’aire et surfaces entières réelles du fichier.

## 5. Résultats dérivés

Les52contrôles propres passent : identité des quatre aires projetées, symétrie/positivité, covariance en rotation, translations communes nulles, facteur d’aire4pour un facteur de longueur2, équilibre/traction de saut uniforme, points désactivés et rejet de géométries effondrées/croisées. La proposition ajoute une branche43/117/4 et un helper indépendant utilisant ces aires courantes, sans lireVOL. L’ancienne branche/helperIsmstr1 est conservée exactement, ainsi que résiduSIGEPS117, matériaux et histoire. Aires actives invalides/non finies ou agencements invalides arrêtent le candidat code66. Aucun volume/épaisseur fictif ni message d’erreur masqué. Sources/différences proposées sont isolées sousAGPL, hors livrablesMIT ; empreintes exactes disponibles.

## 6. Contradictions et informations manquantes

Patch non appliqué/non compilé. NativeIsmstr4, convergence avec aire évolutive, changement de repère, dommage général et retour arrière restent non qualifiés. La future compilation et ses contrôles ont besoin d’un accord distinct ; les quatre EngineA65 sont consommés. TYPE25 demeure bloquant même si la nouvelle branche résout les surfaces ; aucun remplacement silencieux. Domaines matériaux/inerties/bilans locaux entiers et échecsA62/A63/A64 conservés. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. PublicationA64+A65 vérifiée avant déclarationA66, intégrité distincte de validation physique.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A66 → AIRCRAFT-A67\n\nRapport : '+rel(REPORT)+'\nProposition : '+prep['proposal']+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a66*.py'))+[CFG,PLAN,HANDOFF]
    for folder in [ROOT/'wtc1_simulation_v8/output/aircraft_a66_preparation',PREP]:files.extend(p for p in folder.rglob('*') if p.is_file())
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'owned_output_and_scripts_only_raw_AGPL_source_patch_excluded':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A66_assessed':True,'prototype_checks':52,'new_native':0,'patch_applied':False}),flush=True)

def register():
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json') and cycle['pending_iterations']==[]
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A66','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
      'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
      'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A66',next_iteration='AIRCRAFT-A67',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a66_key_results']=row;state['validated_artifacts'].update(aircraft_a66_report=rel(REPORT),aircraft_a66_results=rel(OUT/'composite_qualification_review.json'),aircraft_a66_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A66'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A66+AIRCRAFT-A67 verified')
    for p,v in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==185
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':len(m['files']),
        'harness':h,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A67'})
    print(json.dumps({'A66_registered':True,'registry_entries':185,'pending_publication_count':1}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','assess','register']);globals()[p.parse_args().action]()
