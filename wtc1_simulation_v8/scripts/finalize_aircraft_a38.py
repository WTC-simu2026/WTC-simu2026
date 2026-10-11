"""Seal startup diagnostics; retain every failed numerical gate."""
from probe_aircraft_a38 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a38.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A38_HANDOFF.md'

def route():
 return ('AIRCRAFT-A39 : comparer le témoin libre PCG Linux échoué A38 à une préparation et un moteur Windows cohérents déjà présents, à mêmes masses, matériaux, vitesses et pas. Vérifier avant calcul que ce contrôle précis n’existe pas déjà; utiliser les résultats mis en cache s’ils existent. Ce changement de plateforme/version est un diagnostic de compatibilité, pas une preuve unique de la cause. Le compteur NINVEL27 est conservé dans les dix reprises inspectées; cela ne qualifie pas tout le pont binaire. Le raccourci de convergence absolue du premier pas est confirmé, mais le désactiver par tolérance plus stricte ne suffit pas : erreur énergétique globale annoncée -75%, décalage de déplacement environ0,000293mm; vitesses et KE nodales correctes aux douze animations partielles. Branche arrêtée, pas de terminaison normale. Ne pas rescaler la vitesse ni modifier la masse, les matériaux ou les reprises. Tout contrôle libre doit conserver les champs, KE/P et déplacement exact; un succès seul permet un nouveau témoin de transition/contact et demi-pas. Les états initiaux/predictors et le calcul global de KE restent à isoler sans nouvelle compilation automatique. La compilation A35 autorisée est terminée39,29min; aucune nouvelle installation ou compilation engagée. Compatibilité implicite entière, peaux A34 et raffinement A36 restent non qualifiés. Meilleur impact entier A20=20ms; objectif dix secondes physiques 3D puis MP4/GIF incomplet. A36+A37 publiées et vérifiées; A38 sera publiée avec A39 après intégrité des deux.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists();assert read(OUT/'preservation_verification.json')['pass'];st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');h=harness();dump(OUT/'harness_after_calculation.json',h)
 a=read(OUT/'scientific_assessment.json');r=read(OUT/'composite_qualification_review.json');assert a['native_controls']==8 and a['native_individual_sets_passed']==0
 dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],'complete':False,'next':route()})
 dump(OUT/'runtime_manifest.json',{'created_utc':now(),'executions':[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('*.execution.json'))],'source_commit':build.PIN,'Linux_engine_sha256':streamsha(build.CAND/'isolated_exec/engine_linux64_gf_ompi'),'CPU_threads_per_process':1,'per_process_cap_s':180,'GPU':False,'new_installation_or_compilation':False,'old_solver_reruns':0,'failed_tight_route_stopped_after_observed_energy_error':True})
 text='''# AIRCRAFT-A38 — diagnostic du premier pas, dynamique libre toujours échouée

Huit nouveaux témoins ont été déclarés puis exécutés avec le moteur Linux séparé A35 et des préparations Windows fraîches. Sept terminent normalement ; le huitième est arrêté après une perte énergétique native de75%, avant sa limite180s. Aucun ne respecte l’ensemble des critères du mouvement libre. Le compteur des vitesses initiales est conservé dans dix reprises inspectées. Un raccourci absolu de convergence est identifié au premier pas ; le contourner par tolérance plus stricte engage la résolution mais ne rétablit pas la dynamique. Aucun nouvel impact entier ni vidéo de dix secondes physiques.

## 1. Faits directement observés ou transcrits

Les trois premières variantes changent séparément AUTOSPC, le solveur linéaire MUMPS→PCG, puis Newmark→HHTα−0,05. Les préparations fraîches terminent sans avertissement ni erreur. Les trois dynamiques terminent et échouent aux historiques énergétiques et de quantité de mouvement ainsi qu’aux vitesses/déplacements exacts. Les options testées ne suffisent donc pas isolément à corriger le défaut.

Deux extensions acquièrent la trace non linéaire sur quatre pas et testent une voie linéaire. Deux autres testent le critère de déplacement seul et l’acquisition du premier pas avec une sortie native tous les0,001ms. Les quatre terminent et échouent également. Le mode LINEAR réalise un seul pas de0,1ms : il ne fournit pas cent pas. La première acquisition TRACE ne possède qu’une animation àt0 ; ses historiques atteignent0,004ms et montrent le défaut. Ce manque d’animation finale est conservé.

Les reprises sont lues sans aucune modification. Leur en-tête contient27nœuds et un compteur NINVEL27 dans les six fichiers frais des trois premières variantes et les quatre états A37 avant/après transfert explicite→implicite. La présence de ce compteur réfute sa seule disparition dans ces fichiers, sans démontrer la compatibilité complète des versions.

Le témoin TIGHT conserve la physique et resserre les trois tolérances non linéaires de10⁻⁶ à10⁻¹¹. MUMPS intervient au premier pas ; le moteur annonce ensuite une erreur énergétique globale de−75% et réduit son pas à environ4,8828×10⁻⁷ms. La branche est arrêtée par signal TERM après observation de cet échec : le moteur journalise un arrêt utilisateur puis MPI_ABORT3. Ce code n’est pas présenté comme un nouvel avortement indépendant de la demande d’arrêt. Temps de lancement76,02s, dernière ligne de progressiont≈0,011623ms, douze animations partielles conservées. Pas de terminaison normale ni d’état final à0,1ms crédité.

## 2. Résultats d’un modèle officiel

La documentation des cartes AUTOSPC, SOLVER, DYNA, NONLIN et LINEAR définit les options utilisées. Elle ne constitue pas une qualification de cette compilation OpenRadioss ni une observation de l’événement historique.

'''
 docs={**DOCS,'nonlinear':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_nonlin_engine_r.htm','linear':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_linear_engine_r.htm','trace':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_print_nonlin_engine_r.htm'}
 text+=''.join(f'- [{k}]({u})\n' for k,u in docs.items())
 text+='''
L’inspection de la source figée bad6688602d770e019b75773d2d5a48b4f9bd918 montre dans NL_SOLV un retour àitération0 lorsque R01×NL_TOL≤10⁻¹² et NL_TOL>10⁻¹⁰, sous les conditions supplémentaires enregistrées dans source_startup_review.json. Ce retour précède CRIT_ITE : sélectionner le déplacement seul ne l’empêche pas. Dans cette branche particulière, R01 est la norme absolue du résidu, malgré l’intitulé relatif de la colonne imprimée. Le premier affichage0/Y/1/3,750×10⁻¹²/1/C concorde avec cette règle. Ce constat source est distinct de la cause complète de la vitesse fausse. Les empreintes et liens primaires des sept fichiers inspectés sont enregistrés ; aucune source tierce brute ni modification du code physique n’est incorporée à cette itération.

## 3. Affirmations provenant des archives locales

Aucune nouvelle lecture d’archive, photographie, vidéo historique ou PDF. Aucun nouveau fait sur AA11 transcrit. Les résultats de ces cubes numériques ne sont pas des probabilités de l’événement réel.

## 4. Hypothèses propres au modèle

Graine1102063, zéro tirage. Même cube libre1mm N2 :27nœuds,8HA8, masse0,00278g ; LAW2 avec densité0,00278g/mm³, E73100MPa,ν0,33 et yield324MPa ; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Vitesse initiale[-200,5,2]mm/ms, KE initiale0,05564031J. Sans charge ni contact, l’oracle est V=V0, U=tV0, P et KE constantes, énergie interne nulle.

Mêmes critères physiques déclarés : erreur énergétique<2%KE0+10⁻⁷J, vitesse<2×10⁻⁴mm/ms, déplacement<2×10⁻⁵mm, absence de masse ajoutée et vérification séparée des grandeurs nodales et globales. Aucun seuil physique élargi, ajout de masse, rescaling de vitesse, modification de matériau ou patch de reprise. Les cartes numériques et limites de temps sont pré-déclarées avant chaque supplément. Les sorties de chaque variante restent séparées. Aucun ancien calcul natif réussi n’est relancé.

## 5. Résultats dérivés

| Témoin | Terminaison normale | Critères complets |
|---|---|---|
'''
 for row in r['cases']:text+=f"| {row['case']['name']} | {'oui' if row['checks']['native_completed'] else 'non, arrêté sur échec énergétique'} | échoués |\n"
 text+=f"\n{a['native_history_sets']} historiques complets échouent au bilan énergétique ; {a['native_field_samples_of_completed_runs']} champs des sept calculs terminés passent les contrôles de lecture, identifiants, finitude et cohérence coordonnées/déplacement. Ces contrôles de champs ne valident pas le mouvement physique. Les masses et l’absence de masse ajoutée passent dans ces historiques. Les douze animations du calcul arrêté sont analysées séparément comme sorties partielles.\n\n"
 text+='''AUTOSPC/OFF, PCG et le critère de déplacement seul reproduisent la vitesse finale[600,−15,−6]mm/ms et KE0,5007628J, soit9KE0. HHT finit vers[525,622,−13,1405,−5,25622] et KE0,3843055J calculée depuis les masses physiques nodales. LINEAR immobilise pratiquement le corps et perd son énergie initiale. La comparaison indépendante aux champs confirme les défauts ; le seul décodeur d’historiques ne les explique pas.

La trace avec tolérance stricte montre que le raccourci peut être évité. Les douze animations partielles gardent V=[−200,5,2]mm/ms et KE nodale0,05564031J. Cela contredit l’erreur énergétique globale annoncée−75%, qui n’est donc pas assimilée à une perte physique nodale démontrée. Le déplacement garde néanmoins un décalage initial maximal d’environ0,000293mm, supérieur au seuil0,00002mm. Ce témoin ne qualifie pas le démarrage ni l’intervalle complet ; les comparaisons au demi-pas et en contact prévues conditionnellement ne sont donc pas exécutées. Tous les échecs initiaux, les acquisitions manquantes et l’arrêt explicite restent dans les sorties.

## 6. Contradictions et informations manquantes

Le défaut complet d’initialisation des prédicteurs, le traitement du premier incrément et la compatibilité entre préparateur Windows et moteur Linux restent à départager. La présence de NINVEL ne garantit pas l’identité de toutes les données de reprise. L’absence d’un appel DYNA_INIV dans l’arbre inspecté est une piste de source, pas une preuve de correction à appliquer. Une comparaison cohérente Windows avec le témoin PCG Linux conservé peut isoler une dépendance de plateforme/version avant toute nouvelle compilation.

Les échecs de qualification mécanique A34 et de raffinement A36 restent conservés. Le contrôle implicite entier A37 a avorté avant son compte rendu, avec cause non identifiée ; les limites documentées des TYPE25 sont distinctes. Aucun nouveau coût de calcul entier n’est projeté depuis ce témoin. Le meilleur impact entier reste20ms A20, et son aperçu ralenti ne représente pas dix secondes physiques.

'''+route()+'\n'
 REPORT.write_text(text,encoding='utf8');HANDOFF.write_text('# Reprise AIRCRAFT-A38 → AIRCRAFT-A39\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a38*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a38*.json'))+[HANDOFF]
 dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'A38_prepared':True,'qualified':False},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();r={'experiment_id':'WTC1-AIRCRAFT-A38','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 st.update(current_iteration='AIRCRAFT-A38',next_iteration='AIRCRAFT-A39',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a38_key_results']=r;st['validated_artifacts'].update(aircraft_a38_report=rel(REPORT),aircraft_a38_results=rel(OUT/'composite_qualification_review.json'),aircraft_a38_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A38');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A38+AIRCRAFT-A39 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
 guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A38','route':st['current_iteration']=='AIRCRAFT-A38' and st['next_iteration']=='AIRCRAFT-A39','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A38'] and cy['pending_count']==1,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};assert all(checks.values()),checks
 dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False});print({'A38_integrity_verified':True,'new_files':n,'next':'AIRCRAFT-A39'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
