"""Register native startup evidence, retaining the original topology gate and CHECK limitations."""
from probe_aircraft_a50 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a50.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A50_HANDOFF.md'

def route():
 return ('AIRCRAFT-A51 : analyser la construction du graphe et la composition des contraintes du modèle entier, depuis la source figée et les messages49370TYPE2/RBE2 du CHECK A49. A50 confirme les bilans et mouvements du démarrage explicite composé sur deux histoires0/10ns et trois animations0/10/20ns, avec TYPE25 conservés ; cela ne qualifie pas l’inertie en rotation ou les efforts sous charge. Les384extrémités de traits de liaison changent exactement comme les144chaînes pré-déclarées ; éléments physiques et autres liaisons restent identiques. L’égalité brute de tout le tableau topologique reste échouée, l’audit supplémentaire de la topologie physique passe. Le compteur natifADDED MASS=0,0002019107g est minuscule mais non nul et identique à la référence A45 ; aucune nouvelle compensation. PUT_KIJ retourne sans ajouter un bloc quand une colonne est absente. /IMPL/CHECK forceISOLV1/IPREC5/ILINE1 puisIKPAT1 : changer seulement le mot-clé de solveur ne teste pas un autre chemin, et CHECK ne qualifie pas MUMPS sous charge. Ne pas relancer une variante ainsi neutralisée. Identifier les contraintes imbriquées et leur fermeture du graphe, en distinguant indices internes et labels originaux, puis tester une composition équivalente explicitement déclarée ou préparer un correctif logiciel concret si nécessaire. Aucun patch moteur, ajout de masse/inertie ou impact implicite avec contacts ignorés. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF inchangé et incomplet. A48+A49 publiées/vérifiées, A50 en attente deA50+A51.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists()
 assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json') and read(ROOT/'harness/publication_cycle.json')==read(OUT/'before_publication_cycle.json')
 initial=read(OUT/'explicit_startup_budget_review.json');top=read(OUT/'declared_constraint_glyph_topology_addendum.json');controls=read(OUT/'CHECK_effective_controls_addendum.json');source=read(OUT/'remaining_condensation_source_review.json')
 assert not initial['startup_budget_and_field_comparison_pass'] and top['startup_budget_and_physical_field_supplemental_pass']
 assert controls['fixed_CHECK_controls']=={'ISOLV':1,'IPREC':5,'ILINE':1,'IKPAT':1}
 old=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
 for row in old:
  st=(ROOT/row['path']).stat()
  if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
 assert not changed,changed
 dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),'changed_paths':changed,'immutable_SHA256_manifests_retained':True,'fresh_all_old_content_rehash':False,'whole_original_fresh_SHA256':streamsha(WHOLE),'Engine_fresh_SHA256':streamsha(BINARY),'source_archives_not_rescanned':True})
 d=OUT/'WHOLE_EQUIVALENT_CHAIN_EXPLICIT_STARTUP';H=histories(d/(read(CFG)['name']+'T01.csv'));mass=float(H['MASS'][0]);added=float(abs(H['ADDED MASS']).max())
 dump(OUT/'native_mass_counter_addendum.json',{'created_utc':now(),'native_history_mass_g':mass,'native_Engine_ADDED_MASS_g':added,'same_counter_as_cached_A45':True,'new_mass_difference_g':0,'counter_fraction_of_mass':added/mass,'original_nominal_mass_scaling_false_means_no_new_scaling_prescription':True,'counter_is_not_exactly_zero':True,'not_a_rotation_inertia_qualification':True})
 h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
 execution=read(d/'engine.log.execution.json');executions=[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('*.execution.json'))]
 dump(OUT/'runtime_manifest.json',{'created_utc':now(),'executions':executions,'new_Starter_executions':0,'new_Engine_executions':1,'old_Engine_replays':0,'cached_reference_native_files_converted_in_new_directory':4,'Engine_CPU_threads':1,'GPU':False,'per_Engine_cap_s':180,'Engine_wall_s':execution['wall_s'],'native_initial_state_reused_unchanged':True,'new_software_installation_or_compilation':False})
 a={'created_utc':now(),'iteration':'AIRCRAFT-A50','status':'completed_equivalent_chain_explicit_startup_budgets__whole_stiffness_graph_unqualified','new_Starter_executions':0,'new_Engine_executions':1,'old_solver_replays':0,'native_normal_completion':True,'native_cycles':3,'TYPE25_preserved_and_not_ignored':True,'native_history_samples':2,'native_history_last_s':1e-8,'native_animation_states':3,'native_animation_last_s':2e-8,'native_mass_g_at_recorded_precision':mass,'native_added_mass_counter_g':added,'new_mass_difference_from_reference_g':0,'startup_global_mass_energy_momentum_comparison_pass':True,'saved_coordinate_displacement_velocity_maximum_difference':0,'original_full_topology_array_gate_pass':False,'supplemental_physical_topology_and_declared_link_glyph_gate_pass':True,'predeclared_reference_changes':144,'declared_link_glyph_endpoint_changes_per_frame':384,'physical_element_topology_unchanged':True,'native_rotating_inertia_or_loaded_work_qualified':False,'CHECK_effective_solver_controls_verified':True,'CHECK_forces_ISOLV1_IPREC5_ILINE1_IKPAT1':True,'CHECK_missing_column_blocks_not_assembled':True,'software_source_binary_or_process_data_patched':False,'new_installation_or_compilation':False,'mass_or_inertia_compensation':False,'historical_damage_used_as_target':False,'whole_insertion_ready':False,'new_whole_impact_extension_executed':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'next_iteration':'AIRCRAFT-A51'}
 dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'original_startup_comparison':initial,'topology_addendum_summary':{k:v for k,v in top.items() if k!='frames'},'topology_addendum_complete':rel(OUT/'declared_constraint_glyph_topology_addendum.json'),'source_condensation_review':source,'CHECK_control_addendum':controls,'mass_counter_addendum':read(OUT/'native_mass_counter_addendum.json'),'whole_impact_qualified':False})
 dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],'complete':False,'next':route()})
 REPORT.write_text('''# AIRCRAFT-A50 — bilans natifs au démarrage et limites du contrôle d’assemblage

La copie à chaînes rigides composées démarre en explicite avec les contacts d’origine. Ses bilans et mouvements initiaux correspondent aux résultats A45 conservés. La fenêtre est20ns, pas une extension de l’impact. La source précise également pourquoi CHECK ne teste pas le solveur demandé et pourquoi ses blocs manquants empêchent de qualifier la raideur.

## 1. Faits directement observés ou transcrits

Un seul Engine nouveau, un thread CPU, sans GPU, cap180s, temps écoulé17,858s. Aucun nouveau Starter : l’état initial natif fraîchement produit en A49 est transféré intégralement, avec SHA256 identique. Le contrôle explicite reprend les paramètres A45, seul le nom /RUN change. Terminaison normale/code0, trois cycles, aucun USERBREAK/SIGSEGV ni TYPE25 ignoré. Les résultats A45 sont copiés et convertis dans un nouveau dossier ; aucun ancien Engine relancé.

Deux histoires natives enregistrent0et10ns ; les trois animations sont0,10,20ns. Tous les champs comparés sont finis, avec mêmes labels, temps, éléments et parts. Les neuf canaux masse, masse ajoutée, énergies cinétique/rotation/interne, travail externe et impulsionsXYZ ont un écart nul à la précision enregistrée. Positions, déplacements et vitesses des48171nœuds ont aussi un écart nul sur les trois états. Aucune érosion.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Inspection en lecture seule de la source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a : PUT_KIJ retourne IERR1 avant d’ajouter le bloc lorsqu’une colonne attendue est absente. Les49370messages du CHECK A49 signalent donc des blocs non assemblés ; ils ne valident pas une raideur nulle physique.

Dans lectur.F, IMP_CHK>0 impose ISOLV1, IPREC5, ILINE1 et D_TOL0. imp_init.F associeIPREC5àIKPAT1, comme les captures A48/A49. CHECK ne résout donc pas une dynamique MUMPS parce que /IMPL/SOLVER/2 apparaît dans la carte. Changer ce mot-clé seul ne permet pas de tester un autre chemin CHECK. La source évite cette variante sans effet ; aucun logiciel modifié. Les anciens rapports sont conservés, l’addendum précise la portée des contrôles.

- [Ajout de blocs et messages : source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/imp_glob_k.F)
- [Contrôles effectifs de CHECK : source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/input/lectur.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle source historique, photographie ou vidéo inspectée. Aucun dégât réel ou résultat NIST utilisé pour ajuster la copie. Archives sources en lecture seule.

## 4. Hypothèses propres au modèle

Graine1102075, zéro tirage. Même modèle et état initial A49 à144références rigides composées, mêmes cinq TYPE25 et budgets physiques. Pas explicite fixé1e−5ms, fin nominale1e−5ms comme A45 ; le moteur écrit aussi l’état suivant2e−5ms. Conversion native g/mm/ms vers SI : masse×0,001kg, énergieNmm×0,001J, impulsiongmm/ms×0,001Ns. Les seuils sont déclarés avant le lancement et ne sont pas modifiés.

La comparaison brute de toute la topologie inclut les traits de visualisation des contraintes, dont les références changent par conception en A49. Son échec reste conservé. Un audit supplémentaire distinct confronte chaque extrémité changée à la liste pré-déclarée :144relations et384traits par état. Tous les types, identifiants d’élément/part, cellules physiques et autres traits restent identiques. Aucune nouvelle dynamique n’est lancée pour corriger la lecture de ces représentations.

## 5. Résultats dérivés

Les bilans globaux et mouvements passent les critères du démarrage. L’égalité brute topologique reste échouée ; l’audit supplémentaire de topologie physique et des384changements exactement déclarés passe. Les changements ne sont pas une modification cachée des éléments.

La masse de l’histoire est191273800g à sa précision d’écriture, cohérente avec les191273837,9425g du Starter. Énergie cinétique initiale2,441026e9J. Le compteur natif ADDED MASS vaut0,0002019107g : minuscule, mais non nul, identique à la référence A45. Aucun nouvel ajout compensatoire ou écart de masse n’est introduit ; ne pas confondre ce compteur avec les100368522,1367g d’ADMAS non structurelles prescrites. Le paramètre nominal sans nouvelle prescription de mise à l’échelle n’autorise pas à déclarer ce compteur observé égal à zéro.

Ces états sont essentiellement une translation initiale, sans charge mécanique significative. Ni l’inertie en rotation, ni les efforts/travaux locaux sous charge, ni les20ms de l’impact antérieur ne sont validés par cette égalité. Le convertisseur d’animation ne fournit pas de tensor d’inertie ou champ de masse nodale dans ces sorties ; aucun n’est inventé.

## 6. Contradictions et informations manquantes

Le démarrage passe, le graphe de raideur entier reste non qualifié. CHECK A49 conserve15erreurs, cinq avertissements récapitulatifs et49370messages de connectivité TYPE2/RBE2, ainsi que cinq TYPE25 ignorés en implicite. Les indices imprimés NI/NJ ne sont pas assimilés aux labels originaux sans correspondance indépendante. Aucun impact implicite lancé en ignorant ses contacts.

A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués ; structure intérieure, gravité, ruptures et bilans entiers restent ouverts. Meilleur impact entierA20=0,0200001220703125s. Objectif dix secondes physiques3D puisMP4/GIF toujours incomplet, aucun crédit des20ns de diagnostic.

Anciennes sorties préservées : audit tailles/dates et manifestes SHA256 existants, sans nouvelle lecture de tous les contenus. Original entier et moteur recontrôlés. Rapport, sorties et validation du harnais précèdent le registre. A48+A49 sont publiées, deux archives complémentaires et125anciennes archives vérifiées, deuxCI réussies ; cette intégrité ne valide pas la physique.

'''+route()+'\n',encoding='utf8')
 HANDOFF.write_text('# Reprise AIRCRAFT-A50 → AIRCRAFT-A51\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a50*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a50*.json'))+[HANDOFF]
 dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'A50_prepared':True,'startup_supplemental_pass':True,'whole_impact_qualified':False},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
 assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
 a=read(OUT/'scientific_assessment.json');t=now();row={'experiment_id':'WTC1-AIRCRAFT-A50','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 old=read(OUT/'before_state.json');st.update(current_iteration='AIRCRAFT-A50',next_iteration='AIRCRAFT-A51',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a50_key_results']=row;st['validated_artifacts'].update(aircraft_a50_report=rel(REPORT),aircraft_a50_results=rel(OUT/'composite_qualification_review.json'),aircraft_a50_handoff=rel(HANDOFF))
 cy['pending_iterations'].append('AIRCRAFT-A50');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A50+AIRCRAFT-A51 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy)
 h=harness();tail=reg.read_bytes()[len(prefix):].decode('utf8').splitlines();checks={'hashes':True,'harness':h['Status']=='PASS','registry_single_append':len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A50','prior_results':all(st[k]==old[k] for k in old if k.endswith('_key_results')),'objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'old_outputs_preserved':read(OUT/'preservation_verification.json')['pass'],'route':st['next_iteration']=='AIRCRAFT-A51','pending':cy['pending_iterations']==['AIRCRAFT-A50']};assert all(checks.values()),checks
 dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':n,'checks':checks,'harness':h,'whole_impact_qualified':False,'objective1_complete':False});print({'A50_registered':True,'new_files':n,'next':'AIRCRAFT-A51'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register']);globals()[p.parse_args().action]()
