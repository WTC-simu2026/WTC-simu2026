"""Seal the rejected full paired-interface variant and the newly observed assembly fault."""
from probe_aircraft_a52 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a52.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A52_HANDOFF.md'

def route():
 return ('AIRCRAFT-A53 : capturer le bloc réellement passé à ASSEM_C4, pas le dernier CBAKE3 observé. A52 classe les37165messages croisés entre les deux faces de chaque même facette, puis teste un regroupement432→216TYPE2sur une copie entière conservant éléments, matériaux, masses, RBE2/RBE3,TYPE25et conditions initiales. Référence :432appels I2UPDK0/3024attaches natives capturées. La copie groupée s’arrête avant tout appel TYPE2, donc son équivalence d’attaches est inconnue et échouée. Regroupement rejeté, aucune intégration d’impact. Deux Starter dont une tentative avec en-tête manquant conservée, trois Engine nouveaux. CopieR1 : Starter2avertissements/0erreur, masse/centre/ADMAS identiques. Nouvelle capture ASSEMC+0x664 après1579appels :NEL128,ND6,IKPAT1,24paires6/6 et144lignes manquantes, indiceKLT1072066364. Dernier CBAKE3 :NEL8, donc contexte périmé et aucun label de ses huit peaux attribué au vrai bloc fautif. La fonctionASSEM_C4reçoit directementIXC(7,NEL), dont labels d’éléments et nœuds. Pré-déclarer trois observations matérielles ASSEM_C4/ASSEMC_KIJ/IMP_CHKM ; au début de CHECK récupérer ITAB etXglobaux par arguments vérifiés dans la source, puis comparer les128éléments et coordonnées au vrai bloc. Aucun patch source/binaire/données mécaniques, compensation ou critères relâchés. Le regroupement nominal ne résout pas encore le graphe. CHECKforcéPCG/IPREC5,TYPE25ignorés et autres critères échoués restent explicites. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF restent actives et incomplètes. A50+A51 publiées/vérifiées ; A52en attente deA52+A53.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists();assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json') and read(ROOT/'harness/publication_cycle.json')==read(OUT/'before_publication_cycle.json')
 r=read(OUT/'paired_binding_and_sparse_fault_review.json');assert r['candidate_rejected'] and not r['native_binding_comparison_available'];assert r['grouped_sparse_fault']['missing_rows']==144
 oldrows=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
 for row in oldrows:
  st=(ROOT/row['path']).stat()
  if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
 assert not changed,changed
 for f in read(CFG)['source_files'].values():assert streamsha(ROOT/f['path'])==f['sha256']
 assert streamsha(WHOLE)==read(ROOT/'wtc1_simulation_v8/data/aircraft_a49_predeclaration.json')['whole_input_sha256']
 dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(oldrows),'changed_paths':changed,'immutable_SHA256_manifests_retained':True,'fresh_all_old_content_rehash':False,'whole_original_fresh_SHA256':streamsha(WHOLE),'Engine_fresh_SHA256':streamsha(BINARY),'source_archives_not_rescanned':True});h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
 a={'created_utc':now(),'iteration':'AIRCRAFT-A52','status':'completed_full_paired_TYPE2_candidate_rejected__actual_fault_block_mapping_pending','new_Starter_executions':2,'new_Engine_executions':3,'original_native_TYPE2_binding_calls':432,'original_native_secondary_bindings':3024,'all37165cross_TYPE2_messages_within_same_facet_pairs':True,'paired_TYPE2_count':216,'paired_native_binding_calls':0,'paired_native_binding_equivalence_gate_pass':False,'paired_native_CHECK_pass':False,'candidate_rejected':True,'candidate_Starter_warnings':2,'candidate_Starter_errors':0,'Starter_mass_center_and_prescribed_ADMAS_unchanged':True,'new_native_sparse_fault_captured':True,'native_fault_offset':'ASSEMC_KIJ+0x664','assembly_calls_before_fault':1579,'native_NEL':128,'native_ND':6,'native_IKPAT':1,'missing_sparse_pairs':24,'missing_sparse_rows':144,'missing_pair_NDOF':[6,6],'invalid_KLT_index_1based':1072066364,'last_CBAKE3_NEL':8,'last_CBAKE3_context_is_faulting_block':False,'actual_fault_source_elements_or_original_node_labels_mapped':False,'header_only_R1_repair_in_distinct_directory':True,'failed_initial_Starter_attempt_preserved':True,'new_installation_or_compilation':False,'source_binary_or_process_mechanics_patched':False,'mass_or_inertia_compensation':False,'original_whole_input_modified':False,'whole_insertion_ready':False,'new_whole_extension_executed':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'next_iteration':'AIRCRAFT-A53'}
 dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'native_pairing_review':r,'input_preservation':read(OUT/'input_preservation_review.json'),'whole_impact_qualified':False})
 dump(OUT/'runtime_manifest.json',{'created_utc':now(),'executions':[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('*.execution.json'))],'new_Starter_executions':2,'new_Engine_executions':3,'old_successful_solver_replays':0,'new_instrumented_measurements_of_original_or_failed_case':True,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'software_installation_or_compilation':False,'source_binary_or_process_mechanical_data_patched':False})
 dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],'complete':False,'next':route()})
 REPORT.write_text('''# AIRCRAFT-A52 — regroupement TYPE2 entier rejeté, nouveau bloc fautif à identifier

La comparaison native est préparée sur le modèle entier. Le regroupement par facette prépare ses données mais s’arrête avant le contrôle des attaches : il reste rejeté. Une nouvelle mesure capture24paires/144lignes absentes dans un autre bloc d’assemblage. Le dernier bloc de peaux observé ne correspond pas à ce bloc ; aucune attribution de pièce n’est inférée de ce contexte périmé.

## 1. Faits directement observés ou transcrits

Deux Starter et trois Engine nouveaux, un threadCPU, caps180s, sans GPU. Une nouvelle observation du modèle A49non regroupé capture432appels I2UPDK0et3024attaches uniques : labels secondaires et principaux, paramètres CRST, positions natives et DOF. Le moteur termine CHECK avec les erreurs déjà connues, sans nouvelle qualification.

La première préparation de la copie omet l’en-tête obligatoireRADIOSS ; Starter sort2avec erreurs100201/2000. Échec conservé, aucun Engine pour cette tentative. Une versionR1distincte rétablit seulement l’en-tête d’origine et un nouveau nom/dossier, sans modifier paramètres ou critères. StarterR1 :2avertissements de pénétration initiaux,0erreur. Le moteurR1s’arrête avecSIGSEGV/code3avant tout appel d’assemblageTYPE2observé. Il ne produit donc aucune des attaches nécessaires à la comparaison d’équivalence.

Un troisième Engine, nouvelle observation de cette copie rejetée, capture le graphe au signal :1579appels ASSEMC,12CBAKE3observés, faute àASSEMC_KIJ+0x664. NEL128,ND6,IKPAT1,24paires NDOF[6,6] et144lignes sans colonne attendue. Indice d’accèsK_LT1072066364. La panne ne se réduit donc pas à un mélange6/3.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a et symboles du binaireA44inchangé. Les observations TYPE2lisent les arguments deI2UPDK0/I2UPDK1dans notre propre processus fils. Aucune instruction, donnée physique ou binaire modifié ; les signaux sont transmis au moteur.

ASSEM_C4reçoit directementIXC(NIXC,NEL),NIXC7dans la source, puis forme les tableaux de nœuds transmis àASSEMC_KIJ. Cela permet une observation plus directe du vrai bloc que le seul dernierCBAKE3. IMP_CHKMreçoitITABetXglobaux, à observer après vérification de leurs positions dans la signature.

- [Arguments TYPE2 et calcul des coefficients](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/interfaces/interf/i2_imp1.F)
- [Connectivité du bloc réellement assemblé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/assem_c4.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie, vidéo ou source historique inspectée. Archives en lecture seule ; aucun dégât connu ou résultat NIST utilisé comme cible.

## 4. Hypothèses propres au modèle

Graine1102077, zéro tirage. Les37165messages TYPE2entre interfaces distinctes concernent tous les deux côtés d’une même facette, aucune autre facette. Cette précision nouvellement vérifiée motive un test entier direct de216paires, plutôt qu’un nouveau petit reproducer incomplet.

Chaque TYPE2pair reçoit les14secondaires disjoints et les deux parts principales de ses faces inférieure/supérieure. La définition TYPE2impaire est retirée ; ses groupes et surfaces inutilisés restent présents. Tous les autres éléments, coordonnées, matériaux, propriétés, masses, RBE2/RBE3,TYPE25, conditions initiales et appuis sont conservés exactement par sections, sans clé dupliquée. Le regroupement est un candidat diagnostique, pas une équivalence supposée. Les facettes principales ordonnées, paramètres natifs, déports/coordonnées et DOF doivent passer les tolérances déclarées avant intégration.

## 5. Résultats dérivés

Masse Starter191273837,9425g, centre[14245,90260656;−0,00031019191109262;−211,2460794408]mm et ADMAS prescrites100368522,1367g restent exactement ceux d’A49. Ces totaux ne prouvent pas l’inertie redistribuée ni l’équivalence des attaches. La comparaison native est indisponible : zéro appel TYPE2de la copie regroupée avant son arrêt. Son critère d’équivalence est échoué et la copie rejetée.

Le dernierCBAKE3observé porte8éléments, tandis que l’assemblage arrêté en porte128. Ses huit labels de peaux et ses coordonnées ne sont donc pas attribués au vrai bloc. Aucun nœud des24paires manquantes ne dispose de coordonnées dans cette captureCBAKE3périmée. Les indices internes fautifs restent à relier à l’entrée. Le signal au même offset queA48/A49ne prouve pas qu’il concerne les mêmes pièces.

## 6. Contradictions et informations manquantes

La piste des interactions entre TYPE2reste une hypothèse. Le regroupement nominal ne répare pas le graphe et son équivalence physique n’est pas vérifiée. La source prouve déjà que les blocs absents sont ignorés parPUT_KIJ ; ils ne deviennent pas une raideur physique nulle. Les contactsTYPE25ignorés en implicite, les deux avertissements Starter et les autres critères échoués restent explicites. Aucun impact implicite exécuté avec contacts ignorés.

Suite : observerASSEM_C4pour le vraiIXCet récupérerITAB/Xau début deCHECK, puis valider labels/connectivité/coordonnées avant reproducer ou correction. Aucune compensation de masse/inertie, modification arbitraire de matériau ou patch de moteur. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF inchangé et incomplet. Aucun temps de diagnostic crédité.

Anciennes sorties et scripts préservés : tailles/dates comparées avec manifestes existants, sans nouvelle relecture totale ; entrées utilisées et original entier recontrôlés par SHA256. Rapport et harnaisPASSprécèdent l’ajout au registre. A50+A51 sont publiées et leurs deuxCI vérifiées,127anciennes archives conservées ; cela ne valide pas la physique.

'''+route()+'\n',encoding='utf8')
 HANDOFF.write_text('# Reprise AIRCRAFT-A52 → AIRCRAFT-A53\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a52*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a52*.json'))+[HANDOFF]
 dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'A52_prepared':True,'candidate_rejected':True,'actual_fault_block_mapping_pending':True},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
 a=read(OUT/'scientific_assessment.json');t=now();row={'experiment_id':'WTC1-AIRCRAFT-A52','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 old=read(OUT/'before_state.json');st.update(current_iteration='AIRCRAFT-A52',next_iteration='AIRCRAFT-A53',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a52_key_results']=row;st['validated_artifacts'].update(aircraft_a52_report=rel(REPORT),aircraft_a52_results=rel(OUT/'composite_qualification_review.json'),aircraft_a52_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A52');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A52+AIRCRAFT-A53 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy)
 h=harness();tail=reg.read_bytes()[len(prefix):].decode('utf8').splitlines();checks={'hashes':True,'harness':h['Status']=='PASS','registry_single_append':len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A52','prior_results':all(st[k]==old[k] for k in old if k.endswith('_key_results')),'objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'old_outputs_preserved':read(OUT/'preservation_verification.json')['pass'],'route':st['next_iteration']=='AIRCRAFT-A53','pending':cy['pending_iterations']==['AIRCRAFT-A52']};assert all(checks.values()),checks
 dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':n,'checks':checks,'harness':h,'whole_impact_qualified':False,'objective1_complete':False});print({'A52_registered':True,'new_files':n,'next':'AIRCRAFT-A53'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register']);globals()[p.parse_args().action]()
