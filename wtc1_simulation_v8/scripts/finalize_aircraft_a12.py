"""A12 report, preservation, single registry append and coherent state route."""
import argparse,json,shutil
from pathlib import Path
from run_aircraft_a12 import ROOT,OUT,CFG,guard,read,dump,sha,rel,now,harness

REPORT=OUT/'rapport_aircraft_a12.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A12_HANDOFF.md'
NEXT='AIRCRAFT-A13 : repartir des sorties A12, sans relance ancienne. Discriminer la dépendance à la maille du contact TYPE7 et de la formulation triangulaire du radôme : témoin de contact à grande vitesse, option de contact alternative documentée et contrôle de formulation déclaré séparément. Contrôler le décalage temporel des vitesses/énergies et les inerties rotationnelles sans ajouter de terme au ledger. Garder les réactions REAC principales séparées du redémarrage observateur. Aucun allongement avion complet avant fermeture locale et convergence spatiale. Module Boeing parallèle v2 reçu mais contrat inertiel/dynamique libre bloqué ; ne pas l’intégrer silencieusement. Premières secondes, écrasement, rupture et impact historiques non qualifiés.'

def checkrows(rows):
    bad=[r['path'] for r in rows if not (ROOT/r['path']).is_file() or (ROOT/r['path']).stat().st_size!=r['bytes'] or sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad[:30];return len(rows)

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass']
    v=harness();assert v['CurrentIteration']=='AIRCRAFT-A11';dump(OUT/'harness_after_calculations.json',v)
    correction=read(OUT/'preservation_baseline_correction.json');assert sha(OUT/'preservation_before.json')==correction['initial_baseline_sha256'] and sha(OUT/'preservation_initial_conflicts.json')==correction['initial_scan_evidence_sha256'];checkrows([correction['canonical_manifest']]);corrected=checkrows(correction['corrections']);n=correction['files_verified_from_initial_full_scan']+corrected;assert n==len(read(OUT/'preservation_before.json')['files'])
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'files':n,'initial_full_scan_matched_files':correction['files_verified_from_initial_full_scan'],'corrected_legacy_manifest_references':corrected,'canonical_existing_parallel_r1_manifest_used':True,'initial_failed_scan_and_baseline_preserved':True,'cached_full_sha256_scan_reused':True,'old_solver_reruns':0,'sources_and_previous_iterations_unchanged':True,'parallel_module_unchanged':True,'archives_rescanned':False})
    by={r['case']['id']:r for r in s['cases']};fine=by['SAND_FINE3'];half=next(q for q in s['comparisons'] if q['cases']==['SAND_FINE2','SAND_FINE2_HALF']);mesh=next(q for q in s['comparisons'] if q['cases']==['SAND_FINE2','SAND_FINE3']);table='\n'.join(f"| {r['case']['id']} | {r['actual_end_ms']:.9f} | {r['radome_mass_kg']:.6f} | {r['final_impulse_Ns'][0]:.6f} | {r['final_generated_J']:.3f} | {r['final_energy_residual_J']:.3f} | {', '.join(r['failed_checks']) or 'aucun'} |" for r in s['cases'])
    comps='\n'.join(f"| {' / '.join(q['cases'])} | {q['type']} | {q['common_time_ms']:.7f} | {100*q['impulse_difference_fraction']:.5f} | {100*q['generated_difference_fraction']:.5f} | {q['impulse_pass']}/{q['generated_pass']} |" for q in s['comparisons'])
    inertia_error=max(r['native_initial_inertia_audit']['maximum_relative_tensor_error'] for r in s['cases']);inert=by['FREE']['native_initial_inertia_audit']
    REPORT.write_text(f'''# AIRCRAFT-A12 — premier contact du nez, énergie et maillage

A12 est terminée comme campagne de diagnostic reproductible : {s['main_engine_jobs']} nouveaux calculs principaux, dont un premier essai libre conservé avec instrumentation rejetée, puis {s['accepted_instrumented_cases']} cas instrumentés et {s['observer_jobs']} observations de fin séparées. Aucun ancien solveur relancé. Les contrôles d'intégrité passent ; l'ensemble des critères numériques ne passe pas. La fenêtre reste environ **0,4 ms = 0,0004 s**. Les premières secondes de l'impact réel ne sont pas calculées.

Le défaut énergétique se reproduit sans le reste de l'avion, sans RBE3 et avec un témoin LAW1 simple. Le sandwich LAW25 et la redistribution RBE3 ne sont donc pas nécessaires à ce défaut dans cette famille de témoins. Cela ne démontre pas leur innocuité dans l'avion couplé ni une cause unique. Les déficits diminuent au raffinement, mais l'impulsion varie encore de **{100*mesh['impulse_difference_fraction']:.2f} %** entre les deux maillages les plus fins : le contact n'est pas convergé.

## 1. Faits directement observés ou transcrits

Onze Starter sans erreur ni avertissement et onze terminaisons Engine normales dans la révision instrumentée r1. Les terminaisons du premier essai r0 restent conservées. Toutes les valeurs CSV acceptées sont comparées aux records binaires T01 ; la première ligne native T02 fournit l'instant final réel. Les déplacements, connectivités, vitesses et masses nodales des animations sont lus indépendamment, puis archivés en SI. Aucun ajout de masse, aucune érosion, aucun travail externe ni travail plastique dans ces témoins.

Le radôme isolé a une masse {by['FREE']['radome_mass_kg']:.9f} kg ; aucun appoint ne remplace les réserves de l'avion retiré. Son premier contact survient autour de 0,225 ms. Les instants sauvegardés suivent les pas effectifs du solveur : demander 0,0005 ms de sortie ne crée pas des états sous le pas natif. Chaque horizon est un départ neuf intact.

Réactions d'appui : les historiques principaux REAC sont des impulsions cumulées. À la reprise observateur, leur cumul se réinitialise. Les premiers bilans r1 utilisaient cette dernière ligne et restent conservés dans review.json ; authoritative_review.json contrôle les réactions sur **l'historique principal seulement**, indique sa borne temporelle et conserve le saut observé. Aucun cumul de fin n'est inventé ; aucun REAC n'est réintégré comme une force. Les erreurs restantes des cas grossiers restent échouées.

## 2. Résultats d'un modèle officiel

La portion de façade et l'acier héritent des entrées nominales NIST utilisées dans A11 ; dépendance des entrées maintenue, aucun résultat de dommages NIST employé comme cible. La portion présente est découpée puis immobilisée : les résultats de ce témoin ne sont ni les résultats NIST ni une validation du WTC réel. Les sorties sont celles d'OpenRadioss v20260728 installé ; les exécutables, arguments, durées, versions et empreintes sont consignés dans les journaux d'exécution.

## 3. Affirmations provenant des archives locales

Aucune nouvelle inspection vidéo/photo, aucun scan d'archive et aucune modification de source. {n} fichiers antérieurs, sources et livraisons parallèles sont vérifiés par SHA-256. Le premier scan complet de 31,36 Go a révélé deux références héritées du manifeste parallèle r0 : integration_ready.json et finalize_r0.log. Le manifeste r1 déjà présent donne les empreintes exactes des deux fichiers, modifiés le 7 octobre avant la déclaration A12. Leur contenu n'a pas été changé : preservation_initial_conflicts.json et preservation_baseline_correction.json conservent le premier échec et la correction de sélection du manifeste, puis les deux SHA-256 canoniques sont revérifiés. Les 6596 autres résultats du scan complet sont réutilisés. V11F/V11R conservées ; branches V11S et I02I-M différées. Manifestes A11, sources c3inmas.F déjà sauvegardées et données Boeing parallèles réutilisés en lecture seule.

Le module Boeing parallèle v2 est effectivement livré : douze ports aile–pylône–moteur, six témoins constitutifs / 96 contrôles, trois candidats natifs. Son Starter avion conserve douze avertissements d'inertie ; le contrat d'inertie zéro et la dynamique libre restent bloqués. Revue enregistrée dans parallel_module_review.json ; aucune intégration, aucun changement implicite de matériaux ou budgets de masse.

## 4. Hypothèses propres au modèle

Déclaration aircraft_a12_predeclaration.json, graine 1102037, zéro tirage. Extraction exacte des 216 triangles du radôme A11, racine libre. Aucun fuselage, RBE3, ADMAS, poutre ou moteur dans ce témoin. Façade : seuls les segments frontaux x=-50 mm dont les centroïdes satisfont |Y|,|Z|≤3000 mm sont retenus ; 540 quadrilatères, tous leurs nœuds fixés. Ce retrait change les conditions mécaniques et ne donne aucun droit d'extrapoler à l'avion.

Sandwich LAW25 / TYPE51 / TYPE19 conservé avec peaux de 0,5 mm et cœur de 8 mm ; rupture, écrasement de cœur, délamination et auto-contact absents. Vitesse hypothétique [-200,5,2] m/s. Le témoin LAW1 à E=22000 MPa, nu=0,25 et épaisseur 9 mm conserve la masse surfacique, avec rho=(0,00183×1+0,000048×8)/9 g/mm³. Il ne conserve pas les raideurs de membrane, flexion et cisaillement du sandwich et n'est pas un substitut matériau Boeing.

Contact TYPE7 : gap constant 5 mm, Stfac=1, friction=0, VIS_s=1e-20 ; Istf=4 ou 5 testés séparément. [La documentation primaire TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) distingue la raideur minimale et la mise en série ; aucune variante n'est sélectionnée sur un dégât historique. Iform=2 concerne la formulation du frottement, ici nul. Les coefficients de viscosité ne sont pas modifiés pour faire passer un budget.

Chaque subdivision coupe les trois côtés en deux et crée quatre triangles coplanaires. Les niveaux 216/864/3456/13824 triangles conservent aire, forme plane par morceau, matériau et masse surfacique ; le partage nodal et les inerties numériques changent et sont contrôlés. Aucune projection sur une nouvelle forme lissée. Les quatre essais supplémentaires ont été déclarés avant exécution dans spatial_extension.json après les échecs r1.

Énergie globale = KE + RKE global + IE + hourglass + spring + contact élastique/friction/amortissement - travail externe. Chaque terme est compté une fois ; spring=0 dans les témoins. Le travail plastique est déjà dans IE. RKE par pièce et reconstruction indépendante ne comblent jamais le résidu. Les seuils A11 sont conservés séparément. Le témoin A12 utilise un contrôle plus précis : |résidu|≤5 % énergie générée+1 J dès énergie générée>100 J, global≤0,5 % KE initiale ; impulsion/appuis≤0,01 N·s+2 % impulsion. Demi-pas : 5 % impulsion / 10 % énergie ; maillage : 10 % / 10 %. Ni tolérance ni matériau modifiés après calcul.

## 5. Résultats dérivés

| Cas | Fin native ms | Masse radôme kg | Jx façade N·s | Énergie générée J | Résidu final J | Critères échoués après contrôle de reprise |
|---|---:|---:|---:|---:|---:|---|
{table}

| Comparaison | Nature | Temps commun ms | Δimpulsion % | Δénergie % | Critères impulsion/énergie |
|---|---|---:|---:|---:|---|
{comps}

Les comparaisons utilisent le plus petit instant commun des historiques principaux, borné à 0,4 ms ; les réactions de reprise sont exclues. À 3456 triangles, le demi-pas donne Δimpulsion={100*half['impulse_difference_fraction']:.5f} % et Δénergie={100*half['generated_difference_fraction']:.5f} %. Les contrôles temporels passent, les contrôles spatiaux restent échoués. Le changement Istf minimal/série est faible dans cette configuration et ne ferme pas le déficit.

Le résidu final sandwich passe d'environ -5927 à -1470, -293 puis {fine['final_energy_residual_J']:.3f} J au raffinement. Au niveau le plus fin, le ratio final vaut {100*abs(fine['final_energy_residual_J'])/fine['final_generated_J']:.3f} %, mais le maximum dans la fenêtre d'énergie générée>100 J vaut {100*fine['max_local_residual_fraction']:.3f} % : **un ratio final seul masquerait le contrôle local échoué**. Certaines variantes fines passent le seuil A11 moins strict dans le témoin isolé ; cela ne qualifie ni le contact spatial ni l'avion couplé.

Inerties initiales : masses lumpées pondérées par les angles, centres de gravité et tenseurs Starter sont vérifiés indépendamment. L'algorithme sauvegardé c3inmas.F ajoute aux inerties de levier la contribution scalaire des triangles et des couches intégrées ; aucune inertie physique n'est assimilée à cette inertie numérique. Erreur relative maximale de tenseur={inertia_error:.3e}, inférieure à 1e-6 dans tous les témoins. Exemple libre : CG natif {inert['native_CG_m']} m et diagonale du tenseur natif {[inert['native_tensor_kg_m2'][i][i] for i in range(3)]} kg·m². [TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm) décrit l'empilement ; l'algorithme de masse/inertie propre au binaire est confronté à ses valeurs sauvegardées, sans équivalence complète source/binaire démontrée. L'accord initial ne qualifie pas la reconstruction dynamique RKE ; les écarts et les vitesses rotationnelles restent sauvegardés.

Durée native cumulée de tous les essais, observateurs et convertisseurs={s['native_wall_seconds']:.3f} s, deux threads CPU, aucun GPU. Les étapes Python de construction et revue sont distinctes et leurs produits/scripts conservés. Il n'y a eu aucun calcul susceptible de durer des heures. Cette campagne courte ne fournit pas une estimation fiable d'un impact déformant de plusieurs secondes.

Visualisation : visualisation/premier_contact.html utilise les états natifs SAND_FINE2_HALF avec déplacements ×1, temps physique ms et lecture ralentie. visualisation/bilans_maillage.svg compare les quatre maillages sandwich. Données finies, indices, temps et syntaxe JavaScript contrôlés ; le rendu graphique interactif n'est pas encore certifié. La vue ne représente pas un avion complet ni une validation physique. États/bilans et inerties dans r1/*/*.npz ; rapports initiaux et corrigés conservés côte à côte.

## 6. Contradictions, informations manquantes et suite

La cause unique du déficit n'est pas identifiée. Une dépendance au maillage de la pénalité de contact, la formulation triangulaire, les inerties rotationnelles et le décalage temporel des sorties restent à départager. La perte existe aussi avec LAW1 : l'accuser exclusivement du sandwich serait injustifié. Les petits écarts indépendants KE/quantité de mouvement des mailles grossières restent échoués, sans recalage a posteriori.

Erreurs conservées : r0 libre terminé mais nombre de records mal décrit ; deux tentatives de lecture rejetées, réactions Y/Z dépassant les dix colonnes demandées. output_schema_extension.json déclare r1 avec deux groupes de nœuds séparés ; aucun ancien fichier ni résultat natif écrasé. Les premiers reviews r1 ont utilisé les réactions réinitialisées de l'observateur ; la revue corrigée les sépare explicitement et préserve tous les échecs physiques. Le premier contrôle de préservation contre le manifeste parallèle r0 obsolète est conservé et corrigé par sélection du manifeste r1 existant, sans réécriture du module. Les sources héritées ne sont pas réinterprétées comme matériaux historiques.

{NEXT}

Le cycle local de publication reste A12 seule en attente de la paire A12+A13. A10+A11 déjà enregistrées comme publiées dans le cycle ; aucune republication, aucun envoi externe, aucun X/Yoremi. L'impact et l'effondrement historiques restent non qualifiés ; température imposée distincte d'un incendie calculé ; Blender demeure une visualisation.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation AIRCRAFT-A12 → AIRCRAFT-A13

Lire AGENTS.md, harness/state.json, cette passation, harness/publication_cycle.json et output/aircraft_a12/publication_verification.json. A12 diagnostic terminé : {s['main_engine_jobs']} nouveaux Engine principaux (un r0 instrumentation rejetée + onze r1), {s['observer_jobs']} observateurs, zéro ancien relancé. Graine1102037, zéro tirage, CPU2, pasGPU ; temps natif cumulé{s['native_wall_seconds']:.3f}s. Rapport/results/config/manifeste présents. Intégrité passe ; critères scientifiques non tous passés.

Témoin isolé : radôme A11 41,062724kg, racine libre, sans RBE3/ADMAS/restede l'avion ; 540quads frontaux x=-50mm, |centroïdes Y/Z|≤3000mm, tous nœuds de façadefixés. Vitesse[-200,5,2]m/s, TYPE7 gap5mm, Istf4/5 ; sandwich inchangé + LAW1 contrôle à masse surfacique égale (raideursnonéquivalentes). Pas de rupture/délamination/écrasement/selfcontact. Fin≈0,4ms=0,0004s, aucune premièreseconde.

Déficit sansRBE3 et aussi avecLAW1. Mailles216/864/3456/13824 : résidusfinals≈-5927/-1470/-293/-54J. Ratiofinal fin2,59% MAIS maxfenêtre>100J38,576% échoue au seuil5%+1J. Impulsion entre3456/13824 varie44,341% : spatialéchoué. Demi-pas3456 : impulsion0,016856%, énergie0,002013% passent. Aucun terme ou seuil ajusté. Inertiesinitiales sourcec3inmas/Starter cohérentes, erreurmax{inertia_error:.3e}; RKEdynamique/partie toujoursnonqualifiée, jamaisajouté au ledger.

REAC cumulatif principal se réinitialise au redémarrage observateur. Utiliser authoritative_main_history_SI.npz pour réactions/tempscommuns ; dernièreligne observateur conservée mais exclue des critères d'appui. review.json initial conservé ; authoritative_review.json corrigé. r0metadata/schema et erreurs conservées ; output_schema_extension.json déclareles deux TH/NODEgroupes r1. Aucunancien calculrelancé.

{NEXT}

Module parallèle v2 reçu/revu dans parallel_module_review.json : 12 ports, 6 témoins/96 critères constitutifs ; inertie zéro, 12 avertissements Starter et dynamique libre bloqués, aucune intégration. Sources/anciens artifacts/module : {n} fichiers vérifiés. Deux références r0 obsolètes ont été corrigées par sélection du manifeste parallèle r1 existant ; premier échec et baseline d'origine préservés, aucun ancien fichier modifié. Visualisation hors ligne output/aircraft_a12/visualisation/premier_contact.html (états natifs ×1, temps ms), figure bilans_maillage.svg ; syntaxe/données contrôlées, rendu interactif non certifié. Cycle A12 en attente d'A13, pas de publication ce cycle. V11F/V11R préservées ; V11S/I02I-M différées ; aucun scan archive ni X/Yoremi. Blender visualisation, impact historique non qualifié.
''',encoding='utf-8')
    files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_aircraft_a12.py','review_aircraft_a12.py','visualize_aircraft_a12.py','finalize_aircraft_a12.py']]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(files))]})
    print({'prepared':True,'old_files_verified':n,'new_files':len(set(files))},flush=True)

def register():
    guard();count=checkrows(read(OUT/'artifact_manifest.json')['files']);assert REPORT.exists() and HANDOFF.exists();s=read(OUT/'authoritative_review.json');state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A11' and cycle['pending_iterations']==[] and cycle['last_published_iteration']=='AIRCRAFT-A11';assert harness()['Status']=='PASS';reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
    t=now();rec={'experiment_id':'WTC1-AIRCRAFT-A12','registered_at':t,'status':'completed_isolated_nose_native_inertia_and_four_mesh_diagnostic_with_retained_local_energy_and_spatial_failures','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'authoritative_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':True,'all_declared_checks_pass':False,'main_engine_jobs':s['main_engine_jobs'],'accepted_instrumented_cases':s['accepted_instrumented_cases'],'observer_jobs':s['observer_jobs'],'old_solver_reruns':0,'old_files_preserved':read(OUT/'preservation_verification.json')['files'],'branch_iteration_count':12,'whole_aircraft_iteration_count':10,'native_initial_inertia_consistent_in_all_witnesses':s['native_initial_inertia_consistent_in_all_witnesses'],'local_energy_ledger_qualified':False,'spatial_convergence_qualified':False,'native_dynamic_RKE_ledger_qualified':False,'seconds_impact_calculated':False,'physical_impact_qualified':False,'parallel_module_delivered_and_reviewed':True,'parallel_module_integrated':False,'NIST_outcomes_used_as_target':False,'next_iteration':'AIRCRAFT-A13'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A12',next_iteration='AIRCRAFT-A13',current_status=rec['status'],next_objective=NEXT,updated_at=t);state['aircraft_a12_key_results']=rec;state['validated_artifacts'].update(aircraft_a12_report=rel(REPORT),aircraft_a12_results=rel(OUT/'authoritative_review.json'),aircraft_a12_handoff=rel(HANDOFF));state['user_steering_2026_10_08']={'request':'continuer la creation des premieres secondes de impact','implemented':'isolated nose controls, native initial inertia and four spatial levels; physical seconds blocked by retained failed gates','next':'AIRCRAFT-A13'}
    cycle.update(pending_iterations=['AIRCRAFT-A12'],pending_count=1,next_publication_after='AIRCRAFT-A13 verified completes authorized pair A12+A13; retain failed scientific checks',updated_at=t);dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(count)

def verify(count=None):
    guard();count=count or checkrows(read(OUT/'artifact_manifest.json')['files']);before=read(OUT/'before_state.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_files_hashes_verified':True,'old_preservation_pass':read(OUT/'preservation_verification.json')['pass'],'past_results_and_policies_unchanged':all(st[k]==before[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A12','state_route':st['current_iteration']=='AIRCRAFT-A12' and st['next_iteration']=='AIRCRAFT-A13','publication_pending_pair':cy['pending_iterations']==['AIRCRAFT-A12'] and cy['pending_count']==1,'publication_last_published_unchanged':cy['last_published_commit']==read(OUT/'before_publication_cycle.json')['last_published_commit'],'report_and_handoff_exist':REPORT.exists() and HANDOFF.exists(),'failed_gates_retained':not read(OUT/'authoritative_review.json')['all_declared_checks_pass'],'harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':count,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':v,'physical_impact_qualified':False,'seconds_impact_calculated':False,'next_iteration':'AIRCRAFT-A13'};assert result['pass'],result;dump(OUT/'publication_verification.json',result);print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
