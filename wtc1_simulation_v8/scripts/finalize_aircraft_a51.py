"""Seal verified call-site semantics and cross-interface hypothesis, preserving rejected interpretations."""
from probe_aircraft_a51 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a51.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A51_HANDOFF.md'

def route():
 return ('AIRCRAFT-A52 : créer un reproducer complet de la dernière facette216, à partir de l’entrée réelle A20/A49 : deux faces de peau, noyau3D, cellules cohésives et RBE2déportés, deux TYPE2originaux16430/16431. A51 corrige les labels du listing : les appels PRINT_WKIJ reçoiventITAB(N), donc les nombres imprimés sont déjà des labels originaux ; les anciennes classifications inverses sont rejetées et conservées. Les15directions suspectes appartiennent aux racines99/103/107/109/111/119. Les49370messages sont répartis en20483paires ordonnées ;37165TYPE2 relient des ensembles TYPE2distincts,11831ontau moins un TYPE2commun ;374sontRBE2. Aucune double contrainte secondaire,96interfaces ont des parents potentiellement dépendants. La sourceIND_KINE_K laisseNMC2=0 et construit les couples secondaires à l’intérieur de chaque TYPE2 avantRBE2. Tester l’interaction réelle de deux TYPE2au travers du même noyau, absente des petits reproducer A49. Comparer ensuite une variante groupée seulement si les facettes principales, coefficients natifs et déports restent équivalents ; ne pas assimiler un groupe de surface potentiel aux vrais poids. Aucun changement entier implicite, ajout de masse/inertie, patch logiciel ou ajustement historique. Coordonnées natives48171nœuds vérifiées au seuil0,003mm : erreur0,00167415mm ; la sortie texte arrondie0,05mm reste rejetée. Les302correspondances natives sont confirmées ; aucun nouveau Engine enA51. CHECKforcéPCG/IPREC5, contactsTYPE25ignorés et15erreurs restent ouverts. A40 chargé/croissance, A34 peaux et A36 raffinement échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF actives et incomplètes. Publier A50+A51 puis poursuivre A52.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists();assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json') and read(ROOT/'harness/publication_cycle.json')==read(OUT/'before_publication_cycle.json')
 m=read(OUT/'full_native_node_order_mapping_r3.json');r=read(OUT/'verified_printed_node_role_review.json');x=read(OUT/'cross_interface_hypothesis_review.json')
 assert m['pass'] and r['pass_printed_label_semantics_and_membership'] and r['original_false_warning_index_interpretation_rejected'];assert sum(r['warning_message_counts'].values())==49370 and len(r['suspect_stiffness_directions'])==15
 assert x['counts']=={'different_declared_TYPE2_sets':37165,'at_least_one_common_declared_TYPE2':11831}
 oldrows=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
 for row in oldrows:
  st=(ROOT/row['path']).stat()
  if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
 assert not changed,changed
 for f in read(CFG)['files'].values():assert streamsha(ROOT/f['path'])==f['sha256']
 dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(oldrows),'changed_paths':changed,'immutable_SHA256_manifests_retained':True,'fresh_all_old_content_rehash':False,'whole_original_fresh_SHA256':streamsha(WHOLE),'original_whole_SHA256_unchanged':streamsha(WHOLE)==read(ROOT/'wtc1_simulation_v8/data/aircraft_a49_predeclaration.json')['whole_input_sha256'],'source_archives_not_rescanned':True})
 assert read(OUT/'preservation_verification.json')['original_whole_SHA256_unchanged'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_analysis.json',h)
 a={'created_utc':now(),'iteration':'AIRCRAFT-A51','status':'completed_verified_printed_label_semantics_and_cross_interface_graph_hypothesis','new_Starter_executions':0,'new_Engine_executions':0,'old_native_solver_replays':0,'cached_native_coordinates_read':48171,'native_coordinate_error_mm':m['maximum_float_export_coordinate_error_mm'],'coordinate_threshold_mm_unchanged':.003,'direct_native_capture_mappings_verified':302,'ASCII_coordinate_gate_pass':False,'ASCII_coordinate_error_mm':.049999999999272404,'native_coordinate_mapping_pass':True,'initial_wrong_printed_index_interpretation_rejected':True,'TYPE2_RBE2_printers_receive_original_ITAB_labels':True,'zero_stiffness_printer_receives_original_ITAB_labels':True,'warning_messages_classified':49370,'unique_ordered_pairs_by_family':20483,'TYPE2_messages_across_distinct_declared_interface_sets':37165,'TYPE2_messages_with_common_declared_interface':11831,'RBE2_warning_messages':374,'suspect_direction_original_nodes':[99,103,107,109,111,119],'multiple_declared_secondary_constraints':0,'nested_TYPE2_potential_parent_groups':96,'source_NMC2_remains_zero_in_IND_KINE_K':True,'cross_interface_graph_hypothesis_proven':False,'actual_TYPE2_RBE3_interpolation_weights_reconstructed':False,'rejected_reader_attempts_retained':True,'software_or_physical_input_patched':False,'new_installation_or_compilation':False,'whole_insertion_ready':False,'new_whole_extension_executed':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'next_iteration':'AIRCRAFT-A52'}
 dump(OUT/'scientific_assessment.json',a)
 dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'verified_role_review':rel(OUT/'verified_printed_node_role_review.json'),'rejected_role_interpretation':rel(OUT/'whole_constraint_role_mapping_review.json'),'native_mapping':{k:v for k,v in m.items() if k!='mapping'},'cross_interface_hypothesis':x,'mapping_call_site_semantics':r['source_call_sites'],'whole_impact_qualified':False})
 dump(OUT/'runtime_manifest.json',{'created_utc':now(),'new_Starter_executions':0,'new_Engine_executions':0,'old_solver_replays':0,'GPU':False,'native_frame_and_302samples_reused':True,'own_reader_repairs_only':True,'retained_failures':['ASCII rounded coordinate threshold','Wrong metadata keys in first native-precision reader','Beam real orientation values parsed as surface nodes in second reader','Printed source labels wrongly interpreted as native indices in the first role review'],'source_runtime_modified':False,'new_installation_or_compilation':False})
 dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],'complete':False,'next':route()})
 REPORT.write_text('''# AIRCRAFT-A51 — labels vérifiés et piste des interfaces croisées

Les messages CHECK identifient déjà les labels d’entrée : leur interprétation initiale comme indices internes est rejetée. Leur classement corrigé situe37165messages entre ensembles TYPE2distincts. La source laisseNMC2à zéro ; cette piste demande un reproducer avec deux interfaces sur le même noyau. Aucun solveur relancé et aucun temps d’impact supplémentaire.

## 1. Faits directement observés ou transcrits

Réemploi du fichier natif à temps zéro A50, produit depuis exactement le même état initial que CHECK A49, vérifié par SHA256. Pour un domaineSPMD, XYZNOD écrit X(:,I) dans l’ordre interne et GENANI écritITAB dans le même ordre. Les48171labels sont uniques et couvrent toute l’entrée. Les302correspondances IXC/X directement capturées en A49 confirment cet ordre.

Le texte VTK échoue au seuil0,003mm : arrondi maximal0,05mm. L’échec et le lecteur original sont conservés. Un lecteur propre, limité au fichier natifv44figé, lit les coordonnées float32 avant cet arrondi ; erreur maximale0,0016741500003263354mm, sous le même seuil. Format vérifié depuis les écrivains de la source figée : en-tête, titres81octets, compteurs, repères six entiers16bits puis coordonnées. Aucun convertisseur, moteur ou fichier natif modifié.

Deux corrections de lecteurs sont aussi conservées dans des versions distinctes : clés de métadonnées native_element/source_nodes, puis exclusion des directions réelles de poutres du lecteur des surfaces coque/solide. Aucun critère physique ajusté et aucun calcul relancé.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Les appels TYPE2/RBE2 à PRINT_WKIJ passentITAB(NI)/ITAB(NJ). Le diagnostic de raideur imprimeITAB(I). Les nombres du listing sont donc déjà les labels originaux ; observer seulement le sous-programme d’impression ne suffisait pas. L’ancienne classification entière en indices internes est conservée comme interprétation rejetée, séparément du vrai tableau d’indices/labels qui reste valide.

IND_KINE_K traite chaque TYPE2 et ses couples secondaires internes, puisRBE2. Son seul affectateurNMC2estNMC2=0, sous un commentaire de couplage entre interfaces. Cela suggère une piste de fermeture du graphe, sans établir à lui seul la cause des blocs manquants.

- [Appels TYPE2, source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/interfaces/interf/i2_imp1.F)
- [Appels RBE2, source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/constraints/general/rbe2/rbe2_imp0.F)
- [Graphe des contraintes, source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/ind_glob_k.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, photographie, vidéo ou PDF inspecté. Archives en lecture seule ; aucun dégât connu utilisé comme cible.

## 4. Hypothèses propres au modèle

Graine1102076, zéro tirage. Lire seulement l’entrée A49, ses listings et les états/captures existants. RôlesRBE2exacts ; pourTYPE2, l’ensemble des nœuds de surface est un ensemble potentiel de parents. PourRBE3, le groupe support ne remplace pas la matrice interpolatoire native. Une appartenance de surface ne prouve pas une facette ou un coefficient réellement choisi. Ces graphes ne prouvent ni conflit mécanique ni mécanisme historique.

Hypothèse suivante : une partie des blocs manquants concerne les interactions entre deux TYPE2opposés liés au même noyau3D, interaction absente des petits cas A49. Un test de la dernière facette216doit copier ses deux peaux, noyau, cellules cohésives, RBE2déportés et TYPE2originaux16430/16431. Un regroupement éventuel est seulement une variante diagnostique ; ses facettes, coefficients et déports natifs doivent être comparés avant tout transfert entier.

## 5. Résultats dérivés

Les49370messages correspondent à20483paires ordonnées en comptant les familles séparément. TYPE2 :37165messages relient des ensembles déclarés distincts,11831ont au moins une interface commune. Les374messagesRBE2relient des nœuds de peau principaux RBE2et des secondaires de racines rigides. Le classement corrigé ne relie aucun message directement à RBE3.

Les15directions suspectes appartiennent aux labels originaux99,103,107,109,111,119, références de racines rigides. L’ancienne conversion erronée les attribuait à des nœuds de noyau428xx ; cette attribution est explicitement rejetée. Les valeurs négatives parfois extrêmes restent un diagnostic d’assemblage non qualifié, pas une preuve d’instabilité physique.

Les3024nœuds secondairesTYPE2 et5136secondairesRBE2 sont uniques et disjoints ; aucun ne partage le rôle de référence dépendanteRBE3. Aucune double contrainte secondaire déclarée. Au total96TYPE2ont des parents de surface potentiellement déjà secondairesRBE2. Leur interpolation exacte et leur fermeture native restent à vérifier.

## 6. Contradictions et informations manquantes

La cause complète n’est pas prouvée. Le défaut de graphe reste réel : PUT_KIJretourne sans ajouter un bloc absent. Les cinq petits reproducer A49 ne contenaient pas cette interaction complète à deuxTYPE2. Ils ne réfutent pas la piste actuelle. Changer /IMPL/SOLVERseul pendantCHECKest neutralisé par les contrôles forcés établis enA50 ; aucune variante inutile exécutée.

A49 :15erreurs mécaniques et cinqTYPE25ignorés en implicite. A50 : bilans et mouvements initiaux identiques à la référence, mais seulement20ns, sans qualification sous charge ou en rotation. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF toujours incomplètes. Aucune suppression de contrainte, compensation de masse/inertie, modification de moteur ou impact implicite avec contacts ignorés.

Toutes les interprétations rejetées et les tentatives de lecteurs sont conservées. Sorties antérieures intactes, audit tailles/dates et manifestes existants ; empreintes des entrées utilisées recontrôlées, sans nouvelle lecture complète des anciens résultats. Rapport, sorties et harnaisPASSprécèdent l’enregistrement.

'''+route()+'\n',encoding='utf8')
 HANDOFF.write_text('# Reprise AIRCRAFT-A51 → AIRCRAFT-A52\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a51*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a51*.json'))+[HANDOFF]
 dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'A51_prepared':True,'labels_corrected_with_source_call_sites':True,'cross_interface_cause_proven':False},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
 a=read(OUT/'scientific_assessment.json');t=now();row={'experiment_id':'WTC1-AIRCRAFT-A51','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 old=read(OUT/'before_state.json');st.update(current_iteration='AIRCRAFT-A51',next_iteration='AIRCRAFT-A52',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a51_key_results']=row;st['validated_artifacts'].update(aircraft_a51_report=rel(REPORT),aircraft_a51_results=rel(OUT/'composite_qualification_review.json'),aircraft_a51_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A51');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A50+AIRCRAFT-A51 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy)
 h=harness();tail=reg.read_bytes()[len(prefix):].decode('utf8').splitlines();checks={'hashes':True,'harness':h['Status']=='PASS','registry_single_append':len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A51','prior_results':all(st[k]==old[k] for k in old if k.endswith('_key_results')),'objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'old_outputs_preserved':read(OUT/'preservation_verification.json')['pass'],'route':st['next_iteration']=='AIRCRAFT-A52','pending':cy['pending_iterations']==['AIRCRAFT-A50','AIRCRAFT-A51']};assert all(checks.values()),checks
 dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':n,'checks':checks,'harness':h,'whole_impact_qualified':False,'objective1_complete':False});print({'A51_registered':True,'new_files':n,'next':'AIRCRAFT-A52'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register']);globals()[p.parse_args().action]()
