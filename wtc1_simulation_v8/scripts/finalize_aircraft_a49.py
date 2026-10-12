"""Seal source-mapped native diagnostics and an algebraically equivalent rigid-chain candidate."""
from probe_aircraft_a49 import *
from finalize_aircraft_a22 import verify_files
REPORT = OUT/'rapport_aircraft_a49.md'
HANDOFF = ROOT/'harness/handoffs/WTC1_AIRCRAFT_A49_HANDOFF.md'

def route():
 return ('AIRCRAFT-A50 : partir de la copie A49 à chaînes rigides composées, qui termine désormais CHECK sans SIGSEGV. Les144références internes sont redirigées vers leur racine entièrement rigide, sans perdre offsets, bras de levier, masses ou matériaux. Les cinq petits reproducer ne reproduisent pas la panne ; Idrill1 reçu par le moteur ne la corrige pas. La copie entière conserve RBE3 et TYPE25, mais CHECK reste échoué :15directions de raideur suspectes et49370messages de connectivité, dont48996TYPE2 et374RBE2. Vérifier dans un lancement explicite entier très court et borné les masses/inerties/énergies natives après redistribution, avec les TYPE25 conservés, par comparaison aux sorties A45 déjà en cache ; aucun ancien calcul réussi à relancer. Identifier ensuite les nœuds et contraintes des messages TYPE2/RBE2 et leur construction du graphe depuis la source figée. Ne pas lancer un impact implicite avec contacts ignorés, supprimer des contraintes, ajouter des masses, ajuster les matériaux ou contourner une panne logicielle. Les équations rigides composées sont vérifiées, leur implémentation native chargée reste à qualifier. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF actif et incomplet. Publier A48+A49 avec tous les échecs puis continuer A50.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists()
 assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
 assert read(ROOT/'harness/publication_cycle.json')==read(OUT/'before_publication_cycle.json')
 mapped=read(OUT/'native_to_source_mapping_review.json');small=read(OUT/'targeted_root_reproducer_review.json');nested=read(OUT/'nested_cohesive_root_review.json')
 standard=read(OUT/'WHOLE_STANDARD_DRILL_CHECK/standard_variant_review.json');buffer=read(OUT/'standard_variant_native_buffer_review.json')
 flat=read(OUT/'WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK/equivalent_chain_CHECK_review.json');algebra=read(OUT/'rigid_chain_algebra_review.json')
 assert mapped['pass'] and algebra['pass'] and flat['native_NORMAL_exit0'] and flat['CHECK_begin_end']
 assert flat['CHECK_errors']==15 and flat['CHECK_warnings']==5 and not flat['ASSEMC_KIJ_abort_seen']
 assert standard['ASSEMC_KIJ_abort_seen'] and buffer['effective_IPARG41']==1 and buffer['missing_pairs']==26
 oldrows=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
 for r in oldrows:
  st=(ROOT/r['path']).stat()
  if st.st_size!=r['bytes'] or st.st_mtime_ns!=r['mtime_ns_before']:changed.append(r['path'])
 assert not changed,changed
 assert streamsha(WHOLE)==read(CFG)['whole_input_sha256']
 dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(oldrows),'changed_paths':changed,'immutable_SHA256_manifests_retained':True,'fresh_all_old_content_rehash':False,'whole_original_fresh_SHA256':streamsha(WHOLE),'Engine_fresh_SHA256':streamsha(BINARY),'source_archives_not_rescanned':True})
 d=OUT/'WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK';listing=(d/'A49_EQUIVALENT_RIGID_CHAINS_0001.out').read_text()
 pairs=re.findall(r'NO CONNECTIVITY BETWEEN NODES:\s*(\d+)\s+(\d+)',listing)
 diagnostics={'created_utc':now(),'messages':len(pairs),'unique_ordered_pairs':len(set(pairs)),'TYPE2_condensation_messages':listing.count('IN INTERFACE TYPE 2 CONDENSATION'),'RBE2_condensation_messages':listing.count('IN RBE2 CONDENSATION'),'suspect_stiffness_lines':re.findall(r'^ NODE NUM\. =.*$',listing,re.M),'symbolic_matrix':'ND257154/NZ6819585','final_matrix':'ND227010/NZ5841201','positive_native_equivalence_qualified':False,'listing_retained':rel(d/'A49_EQUIVALENT_RIGID_CHAINS_0001.out')}
 assert diagnostics['messages']==49370 and len(diagnostics['suspect_stiffness_lines'])==15
 dump(OUT/'whole_completed_CHECK_diagnostics.json',diagnostics)
 # TYPE19 starts with a material ID; do not infer integration points from it or from CBAKE3 NPT.
 sec=sections();ply=sec['/PROP/TYPE19/41'];v=ply[1].split();assert v[0]=='4' and v[5]=='3'
 dump(OUT/'property_interpretation_addendum.json',{'created_utc':now(),'original_declarations_retained':True,'source_keyword':'/PROP/TYPE19/41','raw_definition':ply,'mat_ID':4,'Npt_ply':3,'TYPE51_last_row_fields':['Pply_ID','phi','Z','Pthickfail','Fweight'],'native_CBAKE3_NPT_not_assumed_equal_to_Npt_ply':True,'correction':'Any earlier wording taking the leading4 of TYPE19 as integration count is incorrect:4 is material ID; the declared ply Npt_ply is3. No input property was changed.','primary_documentation':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm'})
 executions=[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('*.execution.json'))]
 starters=[r for r in executions if r['path'].endswith('/starter.log.execution.json')]
 engines=[r for r in executions if r['path'].endswith('/engine.log.execution.json') or r['path'].endswith('/trace.launcher.execution.json')]
 assert len(starters)==7 and len(engines)==9
 threads=[]
 for r in starters:
  p=ROOT/r['path'].replace('.execution.json','');t=p.read_text();threads+=re.findall(r'STARTER RUNNING ON\s+(\d+) THREAD',t)
 assert len(threads)==7 and set(threads)=={'1'},threads
 dump(OUT/'runtime_manifest.json',{'created_utc':now(),'executions':executions,'fresh_Starter_preparations':7,'native_Engine_executions':9,'Starter_threads_observed':1,'Engine_threads':1,'per_process_cap_s':180,'GPU':False,'trace_parent_exit_is_not_Engine_exit':True,'instrumentation':'Owned Linux child, hardware debug registers and bounded reads only. No instruction or mechanics data patch, installation or compilation.','native_trace_exits':[{'path':rel(p),'Engine_exit_code':read(p)['Engine_exit_code']} for p in sorted(OUT.rglob('trace_result.json'))]})
 h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
 a={'created_utc':now(),'iteration':'AIRCRAFT-A49','status':'completed_native_source_mapping_and_equivalent_chain_assembly__whole_mechanical_CHECK_failed','fresh_Starter_preparations':7,'actual_Engine_executions':9,'Starter_threads_observed':1,'Engine_threads':1,'mapped_native_elements':128,'mapped_internal_nodes':302,'maximum_coordinate_error_mm':0,'missing_sparse_pairs_source_mapped':26,'nested_rigid_main_secondary_role_localized':True,'small_reproducer_controls':5,'small_reproducer_fault_reproduced':False,'Idrill1_effectively_received':True,'Idrill1_whole_abort_removed':False,'rigid_chain_reference_nodes_composed':144,'rigid_chain_algebra_samples':algebra['samples'],'rigid_chain_equation_identity_pass':True,'whole_equivalent_chain_assembly_COMPLETED':True,'whole_equivalent_chain_SIGSEGV':False,'whole_CHECK_errors':15,'whole_CHECK_summary_warnings':5,'whole_connectivity_warning_messages':49370,'TYPE2_connectivity_warning_messages':48996,'RBE2_connectivity_warning_messages':374,'whole_Starter_warnings':2,'whole_mass_center_and_prescribed_ADMAS_unchanged':True,'native_redistributed_mass_tensor_or_work_equivalence_qualified':False,'clean_whole_mechanical_CHECK_pass':False,'TYPE25_ignored_count':5,'new_installation_or_compilation':False,'source_binary_or_process_mechanics_patched':False,'original_whole_input_overwritten':False,'mass_or_inertia_compensation':False,'historical_damage_used_as_target':False,'whole_insertion_ready':False,'new_whole_impact_executed':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'next_iteration':'AIRCRAFT-A50'}
 dump(OUT/'scientific_assessment.json',a)
 dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'source_mapping':{k:v for k,v in mapped.items() if k not in ['all_entries','first_mapped_missing']},'small_reproducer':small,'nested_reproducer':nested,'failed_standard_numerical_variant':standard,'effective_standard_option_observed':{k:v for k,v in buffer.items() if k!='entries'},'rigid_chain_algebra':algebra,'whole_equivalent_chain_CHECK':flat,'remaining_whole_CHECK_diagnostics':diagnostics,'full_physical_qualification':False})
 dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],'complete':False,'next':route()})
 text='''# AIRCRAFT-A49 — correspondance native et composition exacte des chaînes rigides

Le bloc fautif est identifié dans les peaux inférieures du radôme. Une copie distincte compose144chaînes déjà entièrement rigides : l’assemblage entier atteint désormais la fin de CHECK sans SIGSEGV, avec les RBE3 conservés. Cette avancée logicielle ne qualifie pas le modèle :15directions suspectes et49370messages de connectivité restent présents. Aucun temps d’impact supplémentaire.

## 1. Faits directement observés ou transcrits

Sept préparations Starter et neuf Engine nouveaux, un thread CPU chacun, sans GPU, caps180s. Les lancements instrumentés observent uniquement notre processus fils ; le code de sortie du parent n’est pas assimilé à celui du moteur. Trois observations entières conservent SIGSEGV/code3 : mapping de la variante A48 sans RBE3, variante originale entière avec Idrill1, puis observation de cette option effective. Les petits reproducer et le dernier CHECK entier terminent normalement.

La capture CBAKE3/ASSEMC_KIJ conserve les identifiants originaux IXC(7,I), indices internes et coordonnées. Les128éléments et302nœuds internes correspondent exactement à l’entrée, erreur maximale0mm. Premier élément70513, /SHELL/12171, RADOME_LOWER_FACET_171, propriétéTYPE51/122 et matériauLAW25/4. La paire interne[41005,41002] correspond aux labels[46990,46993]. Le premier nœud est secondaire de la racineRBE2/6014 entièrement rigide et principal du déport cohésifRBE2/3126. Les26paires manquantes partagent ce double rôle. Les déports cohésifs sont non nuls ; ils ne sont pas supprimés.

Les cinq petits cas copient une coque hôte, la coque fautive, et selon le cas une brique cohésive avec deux nœuds déportés contraints. Chaque Starter est sans erreur/avertissement, masse878,5142410262g ; chaque CHECK termine et l’observateur ne trouve aucune colonne manquante. Ils ne reproduisent pas la panne entière. Les autres nœuds cohésifs libres excluent leur emploi comme dynamique de substitution.

La variante entière Idrill2→1 dans les propriétés122/123 conserve masse et centre, mais s’arrête encore au même offset+0x664. L’observation indépendante vérifie IPARG41=1 réellement reçu ; les26paires/156lignes manquantes persistent avec NDOF[6,6]. Le mélange6/3 seul ne suffit donc pas à expliquer la panne.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat d’un modèle historique officiel. La source figée du moteur et sa documentation servent uniquement à interpréter données et contraintes. IXC(7,I) est l’identifiant utilisateur, distinct des indices internes /NODE. Le premier champ de TYPE19 est mat_ID4 ; Npt_ply est3. Un addendum corrige toute confusion antérieure avec4points d’intégration, sans changer l’entrée ou effacer les déclarations. Le NPT natif CBAKE3 n’est pas assimilé à Npt_ply.

- [RBE2 : masques et déports](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm)
- [TYPE51 : empilement et champs des plis](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm)
- [Source figée CBACOORK](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/elements/shell/coqueba/cbacoork.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle photographie, vidéo, archive ou source historique inspectée. Aucun dégât observé ni résultat NIST utilisé comme cible. Les archives restent en lecture seule.

## 4. Hypothèses propres au modèle

Graine1102074. Les déclarations propres à chaque diagnostic sont enregistrées avant son lancement. Pour144liaisons internes uniquement, la référence est redirigée du nœud intermédiaire vers la racine qui impose déjà ses six mouvements. Les masques111/000 de la liaison interne,111/111 de la racine, Iflag0 et skew0 sont vérifiés. Les groupes secondaires, positions, matériaux, propriétés, masses, RBE3 et contacts restent identiques. Seuls144labels de référence et deux titres changent dans la copie entière originale. Aucune masse ou inertie compensatoire.

Équations composées : v_m=v_r+Ω_r×(X_m−X_r), Ω_m=Ω_r ; puis v_s=v_m+Ω_m×(X_s−X_m)=v_r+Ω_r×(X_s−X_r). La pose finie et les moments composent les mêmes bras de levier. Une simple suppression du déport ou une liaison translatoire sans rotation n’est pas cette transformation. Huit poses aléatoires par branche, angles±0,7rad, vitesses et efforts indépendants, servent de contrôles algébriques ; aucune sortie mécanique ne sert de cible.

## 5. Résultats dérivés

Les3072échantillons d’identité rigide passent les seuils pré-déclarés : erreur maximale de pose2,27e−13mm, de vitesse3,55e−15mm/ms, de moment3,64e−12Nmm. Cela vérifie les équations, pas leur élimination native ni la réponse chargée. La masse Starter reste191273837,9425g, centre[14245,90260656;−0,00031019191109262;−211,2460794408]mm et ADMAS prescrites100368522,1367g, exactement comme la référence enregistrée.

La copie entière termine BEGIN/END CHECK, code0/NORMAL en7,39s natives, sans l’arrêt ASSEMC_KIJ. Matrice symboliqueND257154/NZ6819585, finaleND227010/NZ5841201. Le compte rendu conserve15erreurs et5avertissements récapitulatifs. Le listing contient49370messages de connectivité :48996lors de la condensationTYPE2 et374lors deRBE2. Ces messages ne sont pas réduits aux seuls cinq avertissements du récapitulatif. Quinze directions de raideur suspectes sont listées aux nœuds119,111,109,107,103,99, avec valeurs négatives parfois extrêmes. Ils ne prouvent pas un mécanisme physique : l’assemblage condensé reste suspect.

Le Starter entier conserve les deux avertissements initiaux et0erreur. Les cinqTYPE25 sont ignorés en implicite. La conversion de l’histoire initiale CHECK échoue ; fichier natif et échec conservés. Aucune valeur d’inertie redistribuée ou de compteur EngineADDED MASS n’est inférée d’une histoire illisible.

## 6. Contradictions et informations manquantes

La composition des chaînes supprime cet arrêt d’assemblage dans la copie entière. La cause logicielle amont complète n’est pas prouvée, et les petits reproducer négatifs restent explicites. Aucune qualification de raideur, de masse/inertie redistribuée, de travail local ou d’impact chargé ne découle de la terminaison. Le test natif explicite suivant doit conserver les contacts originaux et examiner les bilans. Les TYPE2/RBE2 sans connectivité nécessitent une analyse du graphe ; aucune suppression de contraintes ou modification arbitraire des budgets n’est autorisée par ces diagnostics.

A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués ; structure intérieure, gravité, ruptures et bilan entier restent ouverts. Meilleur impact entierA20=0,0200001220703125s. Objectif : dix secondes physiques puis vidéo3DMP4/GIF, toujours incomplet. Aucun diagnostic ou petit panneau crédité à cet objectif.

Les anciennes empreintes sont conservées ; tailles/dates sont comparées sans nouvelle lecture de tous les contenus anciens. L’original entier et le moteur sont revérifiés par SHA256. Aucun patch logiciel, installation, compilation, écriture d’instructions ou de données mécaniques dans le processus. Rapport, sorties et validation du harnais précèdent l’ajout au registre.

'''+route()+'\n'
 REPORT.write_text(text,encoding='utf8')
 HANDOFF.write_text('# Reprise AIRCRAFT-A49 → AIRCRAFT-A50\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a49*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a49*.json'))+[HANDOFF]
 dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]})
 print({'A49_prepared':True,'whole_assembly_completed':True,'clean_mechanical_CHECK_pass':False},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files'])
 st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
 assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json')
 reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
 a=read(OUT/'scientific_assessment.json');t=now();row={'experiment_id':'WTC1-AIRCRAFT-A49','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 old=read(OUT/'before_state.json');st.update(current_iteration='AIRCRAFT-A49',next_iteration='AIRCRAFT-A50',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a49_key_results']=row
 st['validated_artifacts'].update(aircraft_a49_report=rel(REPORT),aircraft_a49_results=rel(OUT/'composite_qualification_review.json'),aircraft_a49_handoff=rel(HANDOFF))
 cy['pending_iterations'].append('AIRCRAFT-A49');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A48+AIRCRAFT-A49 verified')
 dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy)
 h=harness();tail=reg.read_bytes()[len(prefix):].decode('utf8').splitlines()
 checks={'hashes':True,'harness':h['Status']=='PASS','registry_single_append':len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A49','prior_results':all(st[k]==old[k] for k in old if k.endswith('_key_results')),'objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'old_outputs_preserved':read(OUT/'preservation_verification.json')['pass'],'route':st['next_iteration']=='AIRCRAFT-A50','pending':cy['pending_iterations']==['AIRCRAFT-A48','AIRCRAFT-A49']}
 assert all(checks.values()),checks
 dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':n,'checks':checks,'harness':h,'whole_impact_qualified':False,'objective1_complete':False})
 print({'A49_registered':True,'new_files':n,'next':'AIRCRAFT-A50'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register']);globals()[p.parse_args().action]()
