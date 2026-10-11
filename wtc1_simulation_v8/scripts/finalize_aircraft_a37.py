"""Seal native transition failures without extending the unqualified whole model."""
from probe_aircraft_a37 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a37.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A37_HANDOFF.md'

def route():
 return ('AIRCRAFT-A38 : reprendre les états et diagnostics A37, sans répéter les campagnes. La copie complète des reprises natives et les champs à la jonction passent dans les témoins libres et en contact; les deux contrôles explicites passent. Les six voies implicites échouent aux budgets : vitesse libre finale -3 fois la vitesse initiale et KE9 fois initiale, contact actif hors énergie et demi-pas. Départ implicite direct échoue aussi; ne pas attribuer ces effets au seul fichier de reprise. Tester une cause d’initialisation à la fois, dont AUTOSPC par défaut et l’initialisation Newmark, avec le même moteur figé, mêmes masses/matériaux/velocités et référence libre exacte. Arrêter une branche si les budgets échouent. Le contrôle entier /IMPL/CHECK a avorté avant son compte rendu; cause non identifiée. Les cinq contacts TYPE25 ne figurent pas parmi les contacts implicites documentés; ne pas les remplacer silencieusement. Aucun coût entier ni dix secondes ne doit être projeté depuis ces cubes. A34 mécanique des peaux et raffinement A36 restent échoués séparément. Compilation A35 terminée; aucune nouvelle installation/compilation engagée. Préserver tous les échecs. Meilleur impact entier A20=20ms; objectif dix secondes physiques 3D puis vidéo/GIF toujours incomplet. A36+A37 prêtes pour publication autorisée après leur intégrité.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists();assert read(OUT/'preservation_verification.json')['pass'];st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');h=harness();dump(OUT/'harness_after_calculation.json',h)
 r=read(OUT/'native_review.json');assert len(r['cases'])==8;cp=read(OUT/'comparison_review.json');details=[];fields=[]
 for row in r['cases']:
  name=row['case'];d=OUT/name if name.startswith('FREE') else OUT/'w2_front_facets'/name;raw=read(d/'review.json');details.append({'case':name,'checks':row['checks'],'histories':raw['histories'],'junction':row['junction']});fields+=row['fields']
 histories_all=[q for x in details for q in x['histories']];wc=OUT/'whole_compatibility';ex=read(wc/'engine.log.execution.json');checktext=(wc/'A37_WHOLE_CHECK_0001.out').read_text(errors='replace');whole={'created_utc':now(),'input_sha256':streamsha(WHOLE),'generation':read(wc/'generation.json'),'native_check_exit_code':ex['exit_code'],'check_mode_readback':'CHECK' in checktext,'checking_report_entered':'BEGIN IMPLICIT MODEL' in checktext,'normal_termination':read(wc/'completion.json')['normal_termination'],'pass':False,'cause':'Not identified: MPI_ABORT code3 before model-check report. Cannot infer a TYPE25-specific native diagnosis from this abort.','documented_contact_support':[5,7,10,11],'whole_TYPE25_count':read(wc/'features.json')['type25_contacts'],'documentation':DOCS['compatibility'],'new_whole_physical_seconds':0}
 dump(wc/'compatibility_review.json',whole)
 failed=[{'case':x['case'],'checks':[k for k,v in x['checks'].items() if not v]} for x in r['cases'] if not x['pass']]
 a={'created_utc':now(),'iteration':'AIRCRAFT-A37','status':'completed_native_restart_junction__implicit_dynamics_failed','native_controls':8,'native_individual_sets_passed':sum(x['pass'] for x in r['cases']),'native_dynamics_phases':14,'native_junction_observers':3,'failed_Starter_preparations_retained':8,'fresh_Windows_Starter_executions':17,'native_field_samples':len(fields),'native_fields_pass':all(f['pass'] for f in fields),'native_history_sets':len(histories_all),'native_energy_balances_passed':sum(q['checks']['full_native_energy_balance'] for q in histories_all),'mass_and_no_added_mass_pass':all(q['checks']['mass'] and q['checks']['no_added_mass'] for q in histories_all),'native_junctions_passed':sum(x['junction'] is not None and x['junction']['pass'] for x in r['cases']),'native_junctions_total':6,'active_contact_join_pass':all(x['checks']['active_contact_at_join'] for x in r['cases'] if x['case'].startswith('CONTACT') and not x['case'].endswith('_I')),'free_transition_qualified':False,'contact_transition_qualified':False,'transition_qualified':False,'comparisons_pass':cp['pass'],'whole_check_pass':False,'whole_inputs_changed':False,'new_whole_impact_executed':False,'whole_insertion_ready':False,'physical_strength_and_fracture_qualified':False,'old_native_solver_reruns':0,'mass_or_material_input_changes':False,'software_build_or_installation':False,'objective1_complete':False,'best_whole_physical_s':.0200001220703125,'next_iteration':'AIRCRAFT-A38','failed_controls':failed}
 dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'native_cases':details,'comparisons':cp,'whole_compatibility':whole,'failed_gates_preserved':True,'whole_impact_qualified':False});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route()})
 dump(OUT/'runtime_manifest.json',{'created_utc':now(),'executions':[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('*.execution.json'))],'source_commit':build.PIN,'Linux_engine_sha256':streamsha(build.CAND/'isolated_exec/engine_linux64_gf_ompi'),'CPU_threads_per_process':1,'GPU':False,'new_installation_or_compilation':False,'old_solver_reruns':0})
 text='''# AIRCRAFT-A37 — états natifs transférés, dynamique implicite échouée

Huit nouveaux témoins natifs sont terminés. Les copies complètes des fichiers de reprise conservent les champs à la jonction, y compris pendant un contact actif. Les deux contrôles explicites respectent leurs budgets. Les six voies implicites échouent : le mouvement libre acquiert une vitesse finale de signe opposé et de norme triple, et une énergie cinétique neuf fois initiale. Le contact implicite échoue également au bilan énergétique. Un départ implicite direct reproduit le défaut libre; aucune prolongation de l’impact entier n’est autorisée par ces résultats. La compilation autorisée A35 reste terminée à39,29min.

## 1. Faits directement observés ou transcrits

Quatre témoins libres et quatre témoins de collision fermée utilisent le même moteur Linux MUMPS A35 et des préparations Windows fraîches. Sept phases libres, sept phases de contact et trois observateurs d’un seul cycle sont terminés. Huit préparations de contact initiales échouent avant le moteur et restent conservées : identifiant d’historique partagé puis extraction automatique de surface solide. Une représentation explicite des quatre facettes avant physiques et un identifiant d’historique distinct corrigent ces entrées. Aucun état natif ancien réussi n’est recalculé.

Le contrôle du modèle avion–façade entier utilise les mêmes cartes physiques A20, seules deux lignes de nom changent. Le préparateur termine avec les deux avertissements conservés. Le moteur lit le mode CHECK puis avorte avec code3 avant le compte rendu de contrôle. Son échec ne constitue pas une mesure du coût de la dynamique entière ni un diagnostic natif spécifique du TYPE25.

## 2. Résultats d’un modèle officiel

La documentation Altair décrit l’activation implicite par fichier Engine et la vérification seule par /IMPL/CHECK. Elle liste les contacts implicites TYPE5/7/10/11 : les cinq contacts TYPE25 du modèle entier ne figurent pas dans cette liste. Les432 liaisons TYPE2/Spot5 sont cinématiques; elles ne sont pas assimilées aux liaisons par pénalité. Cette documentation doit être distinguée du comportement du moteur OpenRadioss figé au commit bad6688602d770e019b75773d2d5a48b4f9bd918, dont les empreintes sont déclarées.

Sources primaires :

'''
 for key,url in DOCS.items():text+=f'- [{key}]({url})\n'
 text+='''
Les sources FREIMPL/imp_solv/imp_dyna enregistrent l’activation, la dynamique Newmark et l’initialisation. Leur inspection ne prouve pas à elle seule la cause de la vitesse erronée. Aucun code physique du solveur n’est modifié; aucun résultat NIST n’est utilisé comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle consultation d’archive, photographie ou vidéo historique. Aucun nouveau fait AA11 transcrit. Aucune ressemblance visuelle n’est utilisée pour qualifier le moteur ou la chaîne causale.

## 4. Hypothèses propres au modèle

Graine1102062, zéro tirage. Cube libre1mm N2,27nœuds/8HA8, masse0,00278g. Collision de deux cubes identiques, masse totale0,00556g,54nœuds/16HA8. LAW2 source inchangée : E73100MPa,ν0,33,densité0,00278g/mm³,yield324MPa; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Aucun ajout de masse, changement de densité, mécanisme de rupture ou inertie artificielle.

Mouvement libre initial[-200,5,2]mm/ms, reprise0,04ms et fin0,1ms, KE initiale0,05564031J. Collision symétrique à±5mm/ms, intervalle initial0,1mm, gap de contact0,01mm; reprise demandée0,0092ms, reprise native réelle0,00920457ms, fin0,015ms. KE initiale6,95×10⁻⁵J. Le TYPE7 sans frottement de ce témoin n’est pas une substitution silencieuse aux TYPE25 de l’avion. Le témoin vise la compatibilité numérique élastique, sans résistance historique qualifiée.

Pas explicite maximal10⁻⁵ms. Newmarkγ0,5/β0,25, MUMPS, pas libres0,001/0,0005ms, pas contacts0,00005/0,000025ms, contrôle de pas déclaré avec bornes. Seuil énergie2% de KE initiale+10⁻⁷J; momentum2% de la somme des normes initiales+10⁻⁹Ns. Demi-pas énergétique0,5%+10⁻⁷J. Les seuils ne sont pas ajustés aux sorties.

Chaque reprise copie intégralement les fichiers natifs fraîchement produits, avec empreintes identiques, sans injection de champs CSV. Les sorties des phases résident dans des dossiers distincts. L’animation de phase1 n’avait pas enregistré exactement la fin de contact : les différences entre temps distincts restent dans les diagnostics initiaux. Trois observateurs explicites d’un cycle lisent les reprises et fournissent les champs à l’instant initial exact, avant leur propre avance. Leur cycle n’est pas crédité à l’impact entier. L’identité coordonnées/déplacement est également examinée séparément avec la borne documentée d’impression à six chiffres et de stockage float32; les critères littéraux initiaux sont conservés.

## 5. Résultats dérivés

'''
 text+='| Cas | Jonction | Budgets et champs de la voie |\n|---|---|---|\n'
 for x in r['cases']:text+=f"| {x['case']} | {'sans changement' if x['junction'] is None else 'réussie' if x['junction']['pass'] else 'échouée'} | {'réussis' if x['pass'] else 'échoués'} |\n"
 text+=f"\n{a['native_individual_sets_passed']}/8 ensembles complets passent; {a['native_energy_balances_passed']}/{a['native_history_sets']} jeux d’historiques énergétiques passent; {a['native_field_samples']} champs et six jonctions passent. Masses et absence de masse ajoutée passent dans tous les historiques. Le contact est actif aux trois jonctions : stress et énergie interne sont observables.\n\n"
 text+='''La vitesse libre native passe de[-200,5,2] à[600,-15,-6]mm/ms et KE atteint0,5007628J. Les historiques et animations indépendamment lus confirment le défaut; il ne s’agit pas du seul ordre des colonnes. Les reprises au demi-pas et le départ implicite direct échouent aussi. Pendant la collision, les résidus énergétiques maximaux après reprise sont environ1,0987×10⁻⁵J et5,0013×10⁻⁶J, contre un seuil1,49×10⁻⁶J. Les comparaisons explicite–implicite, demi-pas et départ direct échouent. Un fichier de reprise identique et une jonction correcte ne suffisent donc pas à qualifier la dynamique ultérieure.

## 6. Contradictions et informations manquantes

La cause exacte du défaut libre reste à isoler : initialisation Newmark, interactions avec les options de contraintes automatiques et état de démarrage du moteur. Le paramètre AUTOSPC par défaut n’est pas une cause confirmée. Le contrôle entier avorte avant son rapport; compatibilité générale du pont Windows–Linux et des lois/interfaces complexes non établie. La documentation TYPE25 fournit une limite distincte, pas une explication confirmée de l’avortement.

Les échecs des peaux A34, de référence et raffinement A36 restent conservés. Aucune insertion mécanique entière ni nouvelle simulation de10s. Le meilleur impact entier reste A20=20ms. Aucun ralentissement vidéo, extrapolation balistique ou succès de compilation ne remplace dix secondes de dynamique physique.

'''+route()+'\n'
 REPORT.write_text(text,encoding='utf8');HANDOFF.write_text('# Reprise AIRCRAFT-A37 → AIRCRAFT-A38\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a37*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a37*.json'))+[HANDOFF]
 dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'A37_prepared':True,'qualified':False},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();r={'experiment_id':'WTC1-AIRCRAFT-A37','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 st.update(current_iteration='AIRCRAFT-A37',next_iteration='AIRCRAFT-A38',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a37_key_results']=r;st['validated_artifacts'].update(aircraft_a37_report=rel(REPORT),aircraft_a37_results=rel(OUT/'composite_qualification_review.json'),aircraft_a37_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A37');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A36+AIRCRAFT-A37 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
 guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A37','route':st['current_iteration']=='AIRCRAFT-A37' and st['next_iteration']=='AIRCRAFT-A38','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A36','AIRCRAFT-A37'] and cy['pending_count']==2,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};assert all(checks.values()),checks
 dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False});print({'A37_integrity_verified':True,'new_files':n,'next':'AIRCRAFT-A38'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
