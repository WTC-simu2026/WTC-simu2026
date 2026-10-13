"""Seal the new surface/volume dispatch audit and keep its rejected ordering hypothesis."""
from probe_aircraft_a58_geometry import ROOT,OUT,CFG,read,dump,sha,now,rel,harness,engine
from pathlib import Path
import ast,json,re
import numpy as np

REPORT=OUT/'rapport_aircraft_a58.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A58_HANDOFF.md'

def route():
    return ('AIRCRAFT-A59 : préparer un traitement mécanique de surface TYPE43/LAW117 avec aire positive, forces et tangente cohérente, '
      'à partir des sourcesSUSER43/SIGEPS117 et de l’assemblageS8ZKE3. D’abord un prototype propre et des oracles d’équilibre/travail/tangente, '
      'puis une différence source concrète et contrôles de transfert ; demander accord explicite avant toute application/compilation d’un nouveau moteur. '
      'A58 nouveau témoin unique confirme SUSER43 appelé AVANT S8ZKE3(TYPE43/LAW117,ISMSTR1,JHBE0)→S8ZDERICT3→SCHKJAB3(DET0,OFF1,élément1). '
      'L’hypothèse de diagnostic « volume avant toute loi de surface » est rejetée et conservée ; la phase de rigidité volumique est bien observée. '
      'Face100mm² et hauteur0, légitimes pour un témoin de surface, mais incompatibles avec ce jacobien de solide ; ne pas simplement supprimer STOP ou ajouter une épaisseur fictive. '
      'Dans le fichierMMATS inspecté, aucune branche spécifique117 ; chemin générique isotrope repéré, sans preuve de support pour tout le programme. '
      'Moteur A57 conservé34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528, défaut mémoire observé corrigé ; aucune nouvelle compilation A58. '
      'Une Engine cap180s/CPU1/sansGPU, aucun Starter, aucun changement physique oubudget, pas d’extension entière. '
      'Cohésion implicite chargée toujourséchouée ; CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés et A52nonintégré restent. '
      'Meilleur impact entier A20=0,0200001220703125s, objectif1 dix secondes physiques puis vidéo3D incomplet. '
      'A56+A57 publiées/vérifiées36a34d712f04f1c58d5d23ccbcb221919c7e6fc4 ; prochaine cadence A58+A59 vérifiées. Ne rejouer aucun ancien diagnostic vérifié.')

def assess():
    candidate,binary=engine();assert not REPORT.exists();v=read(OUT/'NATIVE_TYPE43_GEOMETRY_DISPATCH/geometry_dispatch_result.json');events=v['events']
    names=[r['function'] for r in events];assert names==['suser43_','s8zke3_','s8zderict3_','schkjab3_']
    material=events[1]['native_arguments'];geom=events[3];assert material['IGTYP']==43 and material['MTN']==117 and material['NEL']==1 and geom['DET']==[0] and geom['OFF']==[1] and geom['element_labels']==[1]
    inherited=read(ROOT/'wtc1_simulation_v8/output/aircraft_a57/implicit_cohesive_controls/w0/NORMAL_L10/generation.json');X=np.asarray(inherited['nodes_mm'],dtype=float)
    area=.5*(np.linalg.norm(np.cross(X[1]-X[0],X[2]-X[0]))+np.linalg.norm(np.cross(X[2]-X[0],X[3]-X[0])))
    assert area==100 and np.max(abs(X[:4]-X[4:]))==0
    log=(OUT/'NATIVE_TYPE43_GEOMETRY_DISPATCH/engine.log').read_text(encoding='utf8');assert 'USER BREAK' in log and 'STOP: ZERO OR NEGATIVE VOLUME' in log
    times=re.findall(r'NC=\s*\d+ T=\s*([\d.E+-]+)',log);assert float(times[-1])==0 and v['Engine_exit_code']==0
    dump(OUT/'native_dispatch_review.json',{'created_utc':now(),'native_observation_integrity_pass':True,'events':events,'hypothesis_volume_before_surface_material_call_pass':False,'hypothesis_failed_and_preserved':True,'actual_surface_function_entry_precedes_stiffness':True,'volumetric_derivative_and_ZERO_DET_CHECK_proven':True,'geometry':{'face_area_mm2':float(area),'height_mm':0,'volumetric_DET_mm3':0},'native_SIGEPS117_call_not_instrumented':True,'SUSER43_LAW117_call_is_source_supported_inference':True,'loaded_response_obtained':False,'last_time_ms':0,'USER_BREAK':True,'normal_termination_and_exit_zero_are_not_pass':True})
    old=read(OUT/'preservation_before_metadata.json');changed=[]
    for row in old['files']:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old['files']),'changed_paths':changed,'old_hash_manifests_preserved':True,'all_old_files_rehashed':False,'A57_binary_fresh_hash_pass':True,'archives_not_rescanned':True})
    execution=read(OUT/'NATIVE_TYPE43_GEOMETRY_DISPATCH/engine.execution.json');assert execution['cap_s']==180 and execution['CPU_threads']==1
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'native_Engine_executions':1,'Starter_launches':0,'execution':execution,'actual_Engine_exit_code':v['Engine_exit_code'],'old_native_Engine_replays':0,'software_patch_or_compilation':False,'GPU':False})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A58','status':'completed_native_surface_then_volumetric_stiffness_dispatch_audit__loaded_implicit_response_still_failed',
       'native_Engine_executions':1,'Starter_launches':0,'source_routines_audited':7,'same_A57_binary_preserved':True,'native_TYPE43':43,'native_LAW117':117,'native_zero_DET_mm3':0,'face_area_mm2':100,'height_mm':0,'surface_entry_before_volumetric_stiffness_observed':True,
       'original_dispatch_order_hypothesis_pass':False,'original_hypothesis_failure_preserved':True,'native_SIGEPS117_entry_instrumented':False,'loaded_implicit_mechanical_gate_pass':False,
       'whole_CHECK_errors_preserved':15,'whole_zero_volume_messages_preserved':624,'implicit_TYPE25_ignored_preserved':5,'budgets_changed':False,'RKE_added':False,'new_software_patch_or_compilation':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'A52_integrated':False,'whole_insertion_ready':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A59'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'source_review':'source_capability_review.json','native_review':'native_dispatch_review.json','physical_qualification':False,'failed_hypothesis_and_physical_gates_retained':True})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A58 — loi de surface appelée, puis rigidité volumique de déterminant nul

Un seul nouveau témoin instrumenté établit l'ordre réel : SUSER43, puis S8ZKE3(TYPE43/LAW117), S8ZDERICT3 et SCHKJAB3 avecDET=0. Le défaut mémoire observé reste corrigé ; la dynamique implicite reste arrêtée àT=0. L'hypothèse initiale de volume contrôlé avant toute loi de surface est rejetée et conservée. Aucun nouveau correctif ou moteur compilé.

## 1. Faits directement observés ou transcrits

Une Engine, aucune Starter, binaireA57 intact, CPU1/cap180s, sans GPU. Quatre premières entrées natives capturées par surveillance matérielle sans modifier les données mécaniques. S8ZKE3 reçoitNEL1,MTN117,IGTYP43,ISMSTR1,JHBE0,JCVT1,ISORTH0,IREP0. SCHKJAB3 reçoitDET0,OFF1, élément1. Code0/NORMAL suivi deUSER BREAK, STOP volume nul, temps0. La sonde ne capture pas directementSIGEPS117 ; l'appel de cette loi parSUSER43 est une inférence appuyée par sa branche source et le matériau du cas, pas une cinquième capture native.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel. Sept routines de la source figée sont inspectées en lecture seule, empreintes et numéros de ligne conservés :S8ZKE3,S8ZDERICT3,SCHKJAB3,MMATS,MMSTIFS,SUSER43,SIGEPS117. S8ZDERICT3 construit un déterminant volumique et appelleSCHKJAB3. SUSER43 possède une branche117 appelantSIGEPS117 avecAREA. DansMMATS inspecté, aucune branche spécifique117 ; les branches génériques calculent des modules isotropes. Cette absence est limitée à ce fichier et ne prouve pas l'absence universelle d'une capacité dans le programme.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie, vidéo ou PDF inspecté ou modifié. Les archives sources restent en lecture seule. Aucun dégât connu utilisé comme cible.

## 4. Hypothèses propres au modèle

Graine1102083, aucun tirage. Le témoin hérité possède deux faces coïncidentes d'aire100mm², hauteur0, huit masses d'instrument de1g. Ces masses ne sont pas des paramètres d'avion. Entrée et cartes copiées exactement, aucune variation d'épaisseur, masse, matériau, contact ou critère. Une géométrie de surface peut avoir une aire positive et un volume nul ; cela ne rend pas son utilisation comme solide volumique valide.

## 5. Résultats dérivés

Le STOP suivant la correction mémoire appartient à la phase de rigidité volumique, tandis qu'une entrée de la fonction de surface a déjà eu lieu. Il faut donc examiner forces, état constitutif et tangente ensemble ; retirer un message ou ajouter une épaisseur fictive ne qualifie pas une surface. Les oracles futurs doivent vérifier équilibre, travail, état irréversible, tangente, rechargement, aire et demi-pas, puis la connexion native, avec les anciens seuils et échecs conservés.

Sources brutesAGPL non copiées dans le manifesteMIT : métadonnées d'empreintes, termes recherchés et numéros de ligne seulement. Préservation par métadonnées et manifestes antérieurs, hash neuf du binaireA57, harnaisPASS. A56+A57 publiées et vérifiées avant cette déclaration, confirmation36a34d712f04f1c58d5d23ccbcb221919c7e6fc4.

## 6. Contradictions et informations manquantes

L'ordre « volume avant toute surface » était faux. Une fonction de surface appelée ne prouve pas une tangente implicite correcte ni une réponse chargée. Les critères entiersA57 restent15erreurs/624volumes/cinqTYPE25 ignorés ; A52 non intégré, couverture des travaux/inerties et énergie locale entière manquante. Meilleur impact entierA20=0,0200001220703125s, aucun temps de ce diagnostic crédité. L'objectif des dix secondes physiques puis vidéo3D demeure incomplet. A59 prépare un prototype/une proposition mécanique de surface ; toute modification du moteur et compilation future nécessitera un accord explicite distinct.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A58 → AIRCRAFT-A59\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a58*.py'))+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'raw_AGPL_sources_not_in_MIT_manifest':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A58_assessed':True,'native_events':4,'ordering_hypothesis_pass':False,'objective1_complete':False}),flush=True)

source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a55.py').read_text(encoding='utf8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='register');s=ast.get_source_segment(source,node)
s=s.replace('AIRCRAFT-A56','AIRCRAFT-A59').replace('AIRCRAFT-A55','AIRCRAFT-A58').replace('aircraft_a55','aircraft_a58').replace('A55_registered','A58_registered').replace('174','177')
s=s.replace("assert cycle['pending_iterations']==['AIRCRAFT-A54']","assert cycle['pending_iterations']==[]").replace("pending_iterations=['AIRCRAFT-A54','AIRCRAFT-A58'],pending_count=2","pending_iterations=['AIRCRAFT-A58'],pending_count=1").replace('AIRCRAFT-A54+AIRCRAFT-A58 verified','AIRCRAFT-A58+AIRCRAFT-A59 verified').replace("'pending_publication_count':2","'pending_publication_count':1")
exec(compile(s,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
