"""Seal qualified fixed free dynamics and unqualified adaptive/contact scopes separately."""
from probe_aircraft_a40 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a40.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A40_HANDOFF.md'

def route():
 return ('AIRCRAFT-A41 : utiliser la voie fixe MUMPS/Newmark avec /IMPL/RREF/LIMIT1,1e30 et tolérances1e-11, qui passe le mouvement libre exact et sa reprise native complète au demi-pas A40. Ne pas utiliser la croissance adaptative : vitesse observéeV0/1,5 pendant croissance1,5 puis décalage de déplacement environ0,2mm. Aucun code ou binaire modifié. Les quatre jonctions natives passent, mais le contact repris échoue encore à l’énergie et au demi-pas : résidus1,0987e-5/5,0013e-6J contre1,49e-6J. Inspecter le sens et le temps des vitesses nodales, déplacements et KE dans INTEGRATOR/TH et Newmark, puis déclarer un contact démarré directement en implicite depuis la géométrie initiale, mêmes TYPE7, masses/matériaux/vitesses et pas, afin de séparer contact implicite et initialisation E→I déjà chargé. Réutiliser les résultats explicites A37 vérifiés; ne pas recalculer les témoins réussis, injecter des champs ou inventer un terme RKE. Vérifier séparément le modèle de contrôle /IMPL/CHECK et son rapport avant toute hypothèse sur l’avortement entier A37. Les cinq TYPE25 entiers ne sont pas documentés parmi les contacts implicites; aucune substitution silencieuse. Peaux A34 et raffinement A36 restent échoués. Compilation A35 terminée39,29min; aucune nouvelle compilation/installation ou patch physique automatique. Meilleur impact entier A20=20ms; dix secondes physiques 3D puis vidéo/GIF restent incomplètes. A38+A39 publiées et vérifiées; A40 à publier avec A41 après intégrité des deux.')

def prepare():
 guard();assert not REPORT.exists() and not HANDOFF.exists();assert read(OUT/'preservation_verification.json')['pass'];st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');h=harness();dump(OUT/'harness_after_calculation.json',h);a=read(OUT/'scientific_assessment.json');r=read(OUT/'composite_qualification_review.json');assert a['native_controls']==9 and a['native_individual_sets_passed']==4
 dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],'complete':False,'next':route()});dump(OUT/'runtime_manifest.json',{'created_utc':now(),'executions':[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('*.execution.json'))],'source_commit':build.PIN,'Linux_engine_sha256':streamsha(build.CAND/'isolated_exec/engine_linux64_gf_ompi'),'CPU_threads_per_process':1,'per_process_cap_s':180,'GPU':False,'fresh_Starter_preparations':5,'cached_explicit_state_reuses':4,'old_successful_solver_reruns':0,'new_installation_or_compilation':False,'solver_source_or_binary_changed':False})
 text='''# AIRCRAFT-A40 — mouvement libre et reprise à pas constant qualifiés ; contact échoué

La voie implicite MUMPS à pas constant conserve enfin le mouvement libre exact dans les témoins déclarés, avec un plancher explicite de normalisation de force. Les deux pas directs et les deux reprises complètes depuis l’explicite passent leurs critères et comparaisons. Les essais adaptatifs et les deux contacts repris échouent séparément. Aucun nouvel impact entier ni dix secondes physiques produits ; aucun changement de masse, de matériau ou de logiciel.

## 1. Faits directement observés ou transcrits

Neuf nouveaux calculs moteur sont exécutés : huit terminent normalement, le premier s’arrête àt0 sur limite de pas. Cinq préparations Windows fraîches passent sans avertissement ni erreur. Quatre phases implicites réutilisent intégralement des états explicites Linux A37 vérifiés, au lieu de relancer ces calculs réussis. Les empreintes de chaque copie native sont identiques avant/après exécution. Les quatre jonctions conservent coordonnées, déplacement, vitesse, contraintes, énergie spécifique et érosion au même instant, y compris pendant un contact actif.

Le premier pas très fin avec tolérances10⁻¹¹, sans plancher de référence, ne converge pas : résidu relatif extrêmement grand et Infinity dans la trace, réductions du pas jusqu’à environ1,22×10⁻¹²ms, puis ERROR TERMINATION. Aucune avance physique créditée. La branche au demi-pas prévue conditionnellement n’est pas lancée après cet échec.

Avec /IMPL/RREF/LIMIT, les deux essais adaptatifs terminent mais leur mouvement reste faux. Pendant une croissance de pas1,5, la vitesse nodale enregistrée devient approximativement la vitesse initiale divisée par1,5 ; elle redevient la vitesse initiale au pas maximal fixe. Le décalage de déplacement persiste vers0,2mm. La KE globale annoncée ne suffit pas à détecter ce défaut de trajectoire.

Les deux départs implicites à pas constant et leurs deux reprises libres depuis l’explicite terminent et respectent les vitesses, déplacements et budgets. Le contact repris aux deux pas termine avec contact observable et jonction correcte, mais dépasse le budget énergétique et ne passe pas le raffinement.

## 2. Résultats d’un modèle officiel

La documentation /IMPL/RREF/LIMIT prévoit des bornes sur la force de référence utilisée par les critères non linéaires. Le plancher facilite la convergence lorsque cette référence est proche de zéro ; il n’applique pas de charge physique. La documentation /IMPL/DT/1 décrit la croissance du pas selon le nombre d’itérations.

- [Référence de force /IMPL/RREF/LIMIT](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_rref_limit_engine_r.htm)
- [Pas initial /IMPL/DTINI](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dtini_engine_r.htm)
- [Croissance /IMPL/DT/1](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_1_engine_r.htm)

Dans la source figée bad6688602d770e019b75773d2d5a48b4f9bd918, DYNA_INA construit les prédicteurs avec DT2 ; son appel dans IMP_SOLV est limité au premier cycle, et INTE_DYNA prépare le prédicteur suivant avec le pas courant. Une dépendance au pas précédent est une hypothèse de source cohérente avec la trajectoire observée en croissance. Aucun patch natif ni preuve unique de cause interne n’est revendiqué. Le garde-fou d’initialisation des forces TT==DT2 ou IMPL_S0==0 doit aussi être distingué du comportement observé après une reprise àtemps non nul.

Les cartes documentées et le code OpenRadioss ne constituent pas un résultat d’un modèle officiel historique. Aucun résultat NIST utilisé comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle consultation d’archive, photographie, vidéo ou PDF. Aucun nouveau fait historique transcrit. Une réussite de ces cubes ne valide pas une chaîne d’impact ou d’effondrement réelle.

## 4. Hypothèses propres au modèle

Graine1102065, zéro tirage. Même cube libre1mm N2,27nœuds,8HA8, masse0,00278g et V0=[−200,5,2]mm/ms, KE0=0,05564031J. Collision fermée de deux cubes identiques, masse0,00556g,54nœuds,16HA8, vitesses initiales±5mm/ms, KE0=6,95×10⁻⁵J. LAW2 inchangée : densité0,00278g/mm³, E73100MPa,ν0,33,yield324MPa ; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. TYPE7 du témoin inchangé : mêmes facettes, gap0,01mm, sans frottement, amortissement déclaré quasi nul. Il ne remplace pas les TYPE25 du modèle entier.

La référence minimale1g·mm/ms² équivaut à1N ; maximum10³⁰. Les témoins qualifiés utilisent les trois tolérances non linéaires10⁻¹¹, MUMPS, Newmarkγ0,5/β0,25 et un pas constant. Le plancher est une normalisation numérique, sans changement de charge, masse, densité ou résistance. Un essai adaptatif séparé conserve la tolérance originelle10⁻⁶ ; il échoue également. Aucun critère physique élargi ni correction artificielle de temps, position, vitesse ou énergie.

Départs libres à0,001/0,0005ms, terme0,1ms. Reprises libres à0,04ms, mêmes pas et terme. Reprises de contact àtemps natif0,00920457ms, pas0,00005/0,000025ms, terme0,015ms. Énergie2%KE0+10⁻⁷J ; momentum2% de la somme des normes initiales+10⁻⁹Ns ; vitesse libre2×10⁻⁴mm/ms ; déplacement libre2×10⁻⁵mm ; comparaison énergétique au demi-pas0,5%KE0+10⁻⁷J. Tous les paramètres et suppléments sont déclarés avant leurs exécutions.

Les états donneurs A37 restent inchangés. Leur revue finale qualifiée et leurs empreintes sont utilisées ; les diagnostics initiaux d’acquisition et de coordonnées, conservés dans les revues brutes A37, ne sont pas effacés. Les nouveaux champs sont aussi examinés séparément avec la borne de six chiffres significatifs et de stockage float32 déjà définie en A23/A37. Les critères littéraux de coordonnées échoués restent présents ; cette vérification de format ne change aucun budget physique.

## 5. Résultats dérivés

| Cas | Critères complets dans le domaine déclaré |
|---|---|
'''
 for q in r['cases']:text+=f"| {q['case']} | {'réussis' if q['qualified_after_separate_reader_review'] else 'échoués'} |\n"
 text+=f"\n{a['native_individual_sets_passed']}/9 ensembles passent ; {a['native_energy_balances_passed']}/{a['native_history_sets']} historiques passent le budget global. {a['native_field_samples']} champs passent la vérification de format distincte. Les masses et l’absence d’ADMAS passent dans tous les historiques complets ; quatre jonctions passent.\n\n"
 text+='''Les quatre voies libres à pas constant conservent V0, U=tV0, P0 et KE0 dans la précision et la durée déclarées. Le résidu énergétique maximal est environ6,94×10⁻¹⁸J à la précision des données publiées, sans revendiquer cette précision pour le calcul interne. Le demi-pas direct et celui de reprise passent ; aucune continuité de fichier seule n’est utilisée comme qualification. Ce succès est limité au mouvement libre élastique déclaré.

Pendant le contact repris, les résidus sont1,0987056×10⁻⁵J et5,00131×10⁻⁶J contre1,49×10⁻⁶J admis. La réduction du pas améliore l’écart sans satisfaire les critères. Les KE nodales calculées depuis les vitesses publiées ne coïncident pas avec les KE globales ; momentum total et absence de travail extérieur passent. Les comparaisons des composantes énergétiques au demi-pas échouent. Aucun terme RKE ou facteur empirique ne referme ces budgets.

## 6. Contradictions et informations manquantes

Une normalisation correcte de la référence rend le mouvement libre exploitable à pas constant, mais ne qualifie pas la croissance de pas ni le contact chargé repris. Il faut inspecter le sens temporel des vitesses/déplacements/KE publiés et tester un contact démarré directement en implicite, pour distinguer défaut de reprise et défaut du contact/dynamique. L’initialisation d’accélération après changement de régime reste une hypothèse, pas une cause confirmée.

Les propriétés et raffinements A34/A36 restent non qualifiés séparément. L’avortement /IMPL/CHECK entier A37 n’a pas de cause identifiée ; les TYPE25 ne figurent pas parmi les contacts implicites documentés. Aucun coût entier n’est extrapolé depuis ce cube. La compilation A35 reste terminée en39,29min ; aucune nouvelle compilation, installation ou modification de logiciel. Le meilleur impact entier reste A20≈20ms ; la vidéo3D de dix secondes physiques n’est pas achevée.

'''+route()+'\n'
 REPORT.write_text(text,encoding='utf8');HANDOFF.write_text('# Reprise AIRCRAFT-A40 → AIRCRAFT-A41\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
 files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a40*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a40*.json'))+[HANDOFF]
 dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'A40_prepared':True,'fixed_free_qualified':True,'whole_qualified':False},flush=True)

def register():
 guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();r={'experiment_id':'WTC1-AIRCRAFT-A40','registered_at':t,'configuration':rel(CFG),'supplemental_predeclarations':[rel(OUT/n) for n in ['reference_floor_predeclaration.json','fixed_step_predeclaration.json','transition_predeclaration.json']],'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
 with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 st.update(current_iteration='AIRCRAFT-A40',next_iteration='AIRCRAFT-A41',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a40_key_results']=r;st['validated_artifacts'].update(aircraft_a40_report=rel(REPORT),aircraft_a40_results=rel(OUT/'composite_qualification_review.json'),aircraft_a40_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A40');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A40+AIRCRAFT-A41 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
 guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A40','route':st['current_iteration']=='AIRCRAFT-A40' and st['next_iteration']=='AIRCRAFT-A41','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A40'] and cy['pending_count']==1,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};assert all(checks.values()),checks
 dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False});print({'A40_integrity_verified':True,'new_files':n,'next':'AIRCRAFT-A41'},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
