"""Seal the read-only source/dependency preflight and reviewable build proposal."""
from preflight_aircraft_a43 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a43.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A43_HANDOFF.md'

def route():
 return ('AIRCRAFT-A44 : après accord humain explicite demandé sur la proposition A43, construire uniquement un moteur MUMPS séparé depuis la source complète3d75ff13d1946f6d28a43920eac4fa2aae41b27a(28juillet2026), sans patch de physique, installation ou remplacement des moteurs. Six threads, plafond1h, dépendance67en cache au lieu de71 explicitement non qualifiée. Le constructeur préparé est figé dans A43. A42 localise l’incompatibilité du nouveau SIGEPS117 avec la préparation Windows; A43 corrobore les21anciens paramètres natifs et identifie cinq interfaces manquantes plus une signature discordante du Reader. Ne créer aucune fonction vide. Après construction, vérifier versions/bibliothèques, LAW117 natif et bilans/comparaisons Windows/Linux, puis démarrage entier explicite et CHECK conditionnel. Toute incompatibilité persistante reste échouée. Ne modifier ni reprise binaire ni masse/matériau/contact pour la contourner. Contact direct A41 qualifié seulement dans son témoin; A40chargé/croissance, A34peaux et A36raffinement restent échoués. Meilleur impact entierA20≈20ms; objectif10sphysiques3D puisMP4/GIF incomplet. Publier la paire A42+A43 avec les échecs et cette proposition, selon autorisation déjà donnée. Pas de nouvelle compilation avant réponse à la question A43.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists();assert read(OUT/'preservation_verification.json')['pass'];assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json');assert read(ROOT/'harness/publication_cycle.json')==read(OUT/'before_publication_cycle.json');h=harness();dump(OUT/'harness_after_calculation.json',h);contract=read(OUT/'legacy_LAW117_input_contract_review.json');proposal=read(OUT/'legacy_build_proposal.json');abi=read(OUT/'Reader_interface_review.json');assert contract['all_21_expected_field_values_match'] and proposal['builder_not_executed'] and abi['no_noop_or_fake_implementation_created'];builder=ROOT/proposal['builder'];assert streamsha(builder)==proposal['builder_sha256']
 a={'created_utc':now(),'iteration':'AIRCRAFT-A43','status':'completed_readonly_legacy_engine_preflight__new_build_awaiting_explicit_authorization','native_controls':0,'software_installation_or_compilation':False,'source_physics_or_binary_changed':False,'Reader_missing_interfaces':5,'additional_Reader_signature_mismatch_localized':True,'candidate_legacy_source_pin':proposal['source_pin'],'legacy_LAW117_21_value_sequence_verified':True,'legacy_source_Git_blobs_reviewed':5,'new_build_proposal_ready':True,'new_build_requires_explicit_authorization':True,'new_build_executed':False,'old_successful_solver_reruns':0,'whole_insertion_ready':False,'new_whole_impact_executed':False,'objective1_complete':False,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'next_iteration':'AIRCRAFT-A44'};dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'Reader_interface':abi,'legacy_source':read(OUT/'legacy_candidate_source_review.json'),'native_legacy_value_contract':contract,'proposal':proposal,'whole_impact_qualified':False,'original_failed_source_assertion_preserved':True});dump(OUT/'runtime_manifest.json',{'created_utc':now(),'native_executions':0,'compilation_executions':0,'installations':0,'read_only_metadata_and_source_inspections':True,'raw_source_cache':'tmp/aircraft_a43_source_review','no_source_archive_rescans':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],'complete':False,'next':route()})
 text='''# AIRCRAFT-A43 — source antérieure et compilation ciblée préparées

A43 vérifie une voie concrète après l’incompatibilité LAW117 localisée A42 : un moteur compilé depuis la source complète du28juillet utilise les21paramètres antérieurs présents dans la reprise Windows. Ce candidat reste à compiler et qualifier. Aucun solveur, compilation ou installation exécuté pendant A43.

## 1. Faits directement observés ou transcrits

La construction Starter A35 a cinq symboles non résolus : cpp_create_rbodies_from_rigid_parts_, cpp_evaluate_rbodies_number_from_rigid_parts_, cpp_is_part_with_elements_, cpp_sale_mesh_create_ et cpp_get_include_file_by_index. Les appels sont présents dans le préparateur figé ; les implementations correspondantes ne figurent pas dans son lecteur ouvert. Une sixième interface, cpp_get_number_of_include_files, reçoit deux arguments côté Fortran bindC, alors que le C++ fourni en reçoit un. Une simple résolution des noms ne suffirait pas à prouver la compatibilité d’appel.

Les métadonnées publiques interrogées renvoient deux miroirs de dépendances, versions59et37. Elles ne fournissent pas la dépendance82 du candidat A35 ni la71 du candidat de juillet. Cela ne prouve pas leur inexistence. La dépendance67 déjà conservée et vérifiée A35 reste disponible localement.

La requête d’historique avant le29juillet renvoie le commit3d75ff13d1946f6d28a43920eac4fa2aae41b27a, daté28juillet2026à15:06:41UTC. L’arbre récursif est complet, et cinq fichiers de revue concordent exactement avec leurs blobs Git : les deux routines LAW117, les configurations moteur et sa licence. Une assertion initiale de revue qui exigeait PARMAT directement dans le moteur est conservée comme erreur de script ; la source reçoit en réalité un tableau utilisateur UPARAM de21entrées. La revue corrigée utilise ce contrat explicite sans modifier la source.

Le constructeur futur est écrit, sa syntaxe analysée et son empreinte enregistrée. Il n’est pas lancé. Il exige un enregistrement d’accord humain précis avant toute écriture dans le nouveau candidat logiciel. Les anciens moteurs, sources, archives et image de travail sont conservés.

## 2. Résultats d’un modèle officiel

Aucun nouveau calcul d’un modèle officiel. La source publiée dans le miroir montre une refonte de LAW117 le5août2026, postérieure au paquet Windows actuel du28juillet. Ce contexte explique le changement d’interface ; il ne prouve pas l’identité exacte entre une source du même jour et un binaire distribué.

- [Source moteur LAW117 antérieure, commit figé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/materials/mat/mat117/sigeps117.F)
- [Source préparateur LAW117 antérieure](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/starter/source/materials/mat/mat117/hm_read_mat117.F)

Le moteur antérieur reçoit21paramètres utilisateur et deux fonctions par son ancien chemin, sans accéder aux nouvelles tables MATPARAM de SIGEPS117_A35. Les options de construction MUMPS existent dans la configuration figée. Ni cette inspection ni la compilation proposée ne constituent une validation mécanique.

## 3. Affirmations provenant des archives locales

Aucune nouvelle inspection d’archive historique, vidéo, image ou PDF. Aucun résultat utilisé pour ajuster une empreinte connue. Les données scientifiques A20–A42 et les critères échoués sont conservés.

## 4. Hypothèses propres au modèle

Graine1102068, zéro tirage. A43 ne change aucune donnée physique. La source candidate doit être utilisée intégralement, sans recopier seulement l’ancienne loi dans un moteur plus récent. Le nouveau moteur resterait séparé ; le préparateur Windows et A35 seraient conservés.

Compilation proposée : double précision, GNU13/OpenMPI4.1.6/MUMPS5.6.2 installés, six threads CPU au maximum, aucun GPU, une heure de construction puis démontage. Nouvelle image indépendante8Gio. Aucun nouveau paquet ou mise à niveau. Dépendance67 déjà contrôlée par Git et empreinte au lieu de71 : différence explicitement non qualifiée, seule métadonnée de construction EXTLIB_VERSION.json remplacée et original conservé. Les sources mécaniques restent celles du commit complet. Aucun faux symbole Reader ou patch de reprise.

Un contrôle après construction doit comparer force, déplacement, énergie, momentum, masse et champs entre les deux moteurs, sur LAW117 déclaré puis sur un démarrage entier borné. Les critères ne sont pas relâchés pour obtenir un calcul. Les limites de compatibilité des cinq TYPE25 restent indépendantes.

## 5. Résultats dérivés

Une séquence unique de21réels big-endian dans la reprise A37 concorde avec l’ordre et les valeurs de l’ancienne source LAW117 :4400,800,1,450,100,1,50,50,4,2,2,1,450/4400,100/800,100/450,1,1,1,1,3,0. Cette corroboration limitée n’est pas un parseur complet de la reprise. Elle distingue les anciens paramètres utilisateur des nouveaux compteurs MATPARAM tous nuls observés A42 ; ces deux stockages ne doivent pas être confondus.

La piste choisie évite une réparation partielle du Reader : compiler uniquement le moteur antérieur complet avec MUMPS, puis tester sa lecture des mêmes états Windows. La proposition, configuration, preuve de source et script futur sont réellement enregistrés avant demande d’accord. L’accord précédent portait sur une autre source et une construction A35 terminée39,29minutes.

## 6. Contradictions et informations manquantes

La compilation du nouveau candidat n’est pas autorisée ni exécutée dans A43. La disponibilité des dépendances originales est non confirmée. La dépendance67 n’est pas présumée équivalente à71. Le code de construction exact du binaire Windows reste inconnu. Les autres lois, conditions, champs, contacts et trajectoires demandent des contrôles natifs ; aucune interopérabilité générale inférée d’une séquence de21valeurs.

Le démarrage Windows A42 n’étend pas A20. Le meilleur impact entier reste≈20ms. A41contact direct qualifié seulement dans son témoin ; A40chargé/croissance, A34peaux et A36raffinement restent échoués. Dix secondes physiques3D puisMP4/GIF demeurent incomplètes. Aucun coût10s annoncé depuis le cube ou cette revue.

'''+route()+'\n';REPORT.write_text(text,encoding='utf8');HANDOFF.write_text('# Reprise AIRCRAFT-A43 → AIRCRAFT-A44\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(OUT/'proposition_compilation_moteur_compatible.md')+'\n\n'+route()+'\n',encoding='utf8');files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a43*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a43*.json'))+[HANDOFF,builder];dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'A43_prepared':True,'new_build_executed':False},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();r={'experiment_id':'WTC1-AIRCRAFT-A43','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 st.update(current_iteration='AIRCRAFT-A43',next_iteration='AIRCRAFT-A44',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a43_key_results']=r;st['validated_artifacts'].update(aircraft_a43_report=rel(REPORT),aircraft_a43_results=rel(OUT/'composite_qualification_review.json'),aircraft_a43_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A43');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A42+AIRCRAFT-A43 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
 guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A43','route':st['current_iteration']=='AIRCRAFT-A43' and st['next_iteration']=='AIRCRAFT-A44','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A42','AIRCRAFT-A43'] and cy['pending_count']==2,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};assert all(checks.values()),checks;dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False});print({'A43_integrity_verified':True,'new_files':n,'next':'AIRCRAFT-A44'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
