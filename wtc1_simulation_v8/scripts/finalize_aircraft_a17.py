"""Register cohesive implementation and movie pipeline;10s goal remains open."""
import argparse,json,shutil
from run_aircraft_a17 import ROOT,OUT,CFG,PREV,read,dump,now,guard,harness,streamsha,rel

REPORT=OUT/'rapport_aircraft_a17.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A17_HANDOFF.md'
NEXT="AIRCRAFT-A18 : objectif utilisateur prioritaire = vidéo 3D des10 premières secondes physiques. L'export MP4/GIF A17 existe mais couvre seulement10ms issus d'A16. Passer maintenant de la liaison cohésive native contrôlée à une séparation dans le contact couplé avion/façade ; aucun ancien Engine relancé. Déclarer avant calcul une topologie adaptée et vérifier masses/CG/inertie, interface/rotations/contacts et travail des connexions ; la LAW117 est vérifiée en traction/cisaillement uniformes, pas en mode mixte, compression ou dans le radôme réel. Les50N/mm sont un essai numérique non mesuré. Ne pas ajouter un G pour compenser le maillage, ni reprendre ORTHENERG rejetée. Partir intact, conserver toutes limites A16, viser un premier20ms borné et continuable, puis100ms/1s/10s suivant le domaine atteint. Étendre la structure intérieure et la gravité avant de présenter les secondes suivantes comme des conditions réalistes. Sauvegarder les checkpoints et réduire la cadence de sorties sans changer les équations pour permettre les calculs longs. Coût observé10ms≈8,3min/2threads, projection linéaire10s≈5,8jours, pas une ETA fiable. Rendu Blender de données natives à échelle1, aucun mouvement extrapolé ni cinématique choisie pour une perforation. Histoire énergétique globale/locale, masse, quantité de mouvement et fragments doivent être auditables. L'objectif10s reste actif et incomplet. Publication A14+A15 toujours due, A16+A17 également en attente ; intégrité de publication distincte de qualification physique."

def check_files(rows):
    for r in rows:
        p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
    return len(rows)

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists();p=read(OUT/'preservation_verification.json');w=read(OUT/'cohesive_review.json');v=read(OUT/'video/video_audit.json');r=read(OUT/'video/render_manifest.json');cfg=read(CFG);assert p['pass'] and w['mechanical_implementation_gate_pass'] and v['pass'] and not v['objective1_complete'];assert harness()['Status']=='PASS'
    dump(OUT/'visual_QA.json',{'created_utc':now(),'decoded_contact_sheet_inspected':True,'inspected_frames':[0,94,188],'labels_legible':True,'whole_and_nose_views_present':True,'model_motion_and_damage_from_saved_states':True,'no_GUI_playback_claim':True})
    table='\n'.join(f"| {x['case']['id']} | {x['final_surface_work_N_mm']:.6f} | {x['equal_peak_IE_difference_fraction']:.9g} | {x['maximum_work_energy_residual_J']:.9g} | {100*x['maximum_traction_relative_error']:.6f}% | {'aucun' if not x['failed_checks'] else '; '.join(x['failed_checks'])} |" for x in w['cases'])
    assessment={'created_utc':now(),'cohesive_native_implementation_pass':True,'native_separation_and_element_deletion_verified':True,'native_total_surface_work_matches_entered_G':True,'same_peak_no_new_work_checked':True,'uniform_interface_area_and_half_dt_checks_pass':True,'physical_G_measured':False,'actual_radome_material_identified':False,'mixed_mode_and_compression_qualified':False,'whole_aircraft_cohesive_transfer_qualified':False,'whole_aircraft_physical_horizon_extended':False,'cached_physical_horizon_s':v['physical_duration_s'],'objective1_target_s':10,'objective1_complete':False,'whole_aircraft_impact_qualified':False,'old_material_and_energy_failures_retained':True,'old_solver_reruns':0,'NIST_damage_fitting':False,'Blender_physics_execution':False};dump(OUT/'scientific_assessment.json',assessment)
    REPORT.write_text(f'''# AIRCRAFT-A17 — séparation énergétique native et premier export vidéo 3D

**L'export MP4 et GIF fonctionne. Il présente les états A16 sur 10 ms physiques, ralentis sur 6,3 s de lecture. L'objectif utilisateur de 10 secondes physiques reste actif et incomplet.** A17 prépare le prolongement : quatre témoins natifs de liaison cohésive passent le bilan, l'énergie par surface, la recharge au même maximum, le demi-pas et le changement d'aire. Aucun ancien impact relancé.

## 1. Faits directement observés ou transcrits

Pré-déclaration immutable, graine 1102042, zéro tirage. Quatre Starter sans erreur ni avertissement ; quatre Engines natifs normaux. Histoire binaire/CSV intégrale contrôlée sur 10000 lignes par cas, tous les canaux. Les messages natifs déclarent la rupture des quatre points d'intégration et la suppression de l'élément de connexion. Statut final d'érosion égal à zéro, lu via le convertisseur natif.

Le film présente 21 états géométriques A16 enregistrés, deux caméras, 42 rendus natifs Blender. Les coordonnées exportées en mètres ont un écart absolu maximal de {r['native_coordinate_max_abs_error_m']:.9g} m à la précision flottante du rendu. Déplacements ×1, aucune interpolation de déformation et aucun solveur Blender. Les couleurs du nez proviennent des indices de dommage A16 ; elles ne créent ni trou ni fragment. La façade est représentée par ses arêtes rendues de 8 mm d'épaisseur visuelle ; cette épaisseur ne modifie pas le calcul.

MP4 H.264 2560×720, 30 images/s, 189 images, 6,3 s de lecture ; GIF 1280×360, 21 images de 300 ms. Décodeur vidéo et métadonnées contrôlés. Images décodées initiale, médiane et finale inspectées : légendes lisibles, temps simulé présent, deux vues. Lecture interactive GUI non certifiée. L'état final est {v['physical_duration_s']:.12f} s physique. Il ne représente pas les 10 premières secondes demandées.

## 2. Résultats d'un modèle officiel et sources primaires

Le solveur est OpenRadioss v20260728-win64 conservé. Aucun résultat NIST de dégâts n'est une cible. La façade nominale A16 garde sa dépendance d'entrée NIST signalée ; ce film ne constitue pas une reconstruction officielle.

La [loi LAW117](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm) est une relation cohésive à deux modes utilisant rigidité d'interface, traction maximale et énergie surfacique. Elle permet de relier ouverture et réduction des efforts. Elle emploie des briques [TYPE43](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm), dont la hauteur peut être nulle et dont la stabilité dépend des masses nodales. Ces sources décrivent une implémentation ; elles n'identifient pas les propriétés du radôme Boeing.

## 3. Affirmations des archives locales

Aucune nouvelle vidéo/photographie d'archive ni nouveau PDF source analysé. Archive et sources officielles en lecture seule. **{p['files']} fichiers antérieurs, {p['bytes_hashed']/1e9:.3f} Go**, recontrôlés entièrement par SHA-256 sans différence. Les états, rapports, limites et critères échoués A06–A16 restent intacts. Le contrat analytique A07 est réutilisé ; ORTHENERG rejetée ne reçoit aucune nouvelle qualification.

Les premiers rendus et l'encodage ont réussi à créer leurs sorties, puis leur wrapper de journalisation a échoué : il exigeait un exécutable situé sous le workspace, contrairement à Blender/FFmpeg installés. Journaux et ancien encodeur conservés. Le helper A17 accepte maintenant ces chemins ; les rendus/MP4 existants sont vérifiés sans écrasement ni relance inutile. Les codes natifs et durées exactes de ces deux premières commandes n'ont pas été journalisés ; cette lacune reste explicite. Durée interne de rendu enregistrée : {r['render_seconds']:.3f} s. L'avertissement d'écriture d'une miniature Blender hors workspace n'a pas empêché les PNG et le fichier blend sous A17. Aucun logiciel installé/modifié et aucune publication externe nouvelle.

## 4. Hypothèses propres au modèle et protocole

Référence cohésive numérique issue du contrat A07 : EN=22000/5=4400 N/mm³, ET=4000/5=800 N/mm³ ; pic normal 450 MPa, pic tangent 100 MPa ; GI=GII=50 N/mm=50 kJ/m². **G et le pic de cisaillement ne sont pas mesurés pour le radôme réel.** Le pic normal reprend une résistance uniaxiale d'un tissu de référence, pas une résistance d'adhésif identifiée. La longueur 5 mm choisie sert seulement à la rigidité du témoin, indépendamment de son aire. Aucun paramètre adapté à la perforation ou aux dégâts observés.

Un élément cohésif carré de côté 10 ou 20 mm, huit nœuds distincts, hauteur initiale nulle. Ismstr=1, aire initiale, Imass=1, Idel=4, Irupt=1. Densité surfacique numérique 1e−20 g/mm² ; masses instrumentales de 1 g par nœud, aucune masse ajoutée automatiquement. Face inférieure fixe ; face supérieure imposée en traction Z ou cisaillement X, autres directions bloquées. Ces masses et déplacements appartiennent au contrôle de la loi et ne deviennent pas des paramètres de l'avion.

Trajet d'ouverture : 0→(δdébut+δfin)/2→0→même pic→1,1δfin aux temps 0/0,25/0,5/0,75/1 ms ; interpolation cubique lisse sur chaque branche. δdébut=T/K, δfin=2G/T. Déformation irréversible fondée sur l'ouverture maximale ; contrainte résistante (1−D)Kδ. Énergie stockée ψ=½(1−D)Kδ² ; dissipation référencée comme travail de l'enveloppe jusqu'au maximum moins ψ à ce maximum. Comparaison séparée avec IE native. PW n'est pas ajouté à IE. Réactions lues comme impulsions : travail Σv·ΔR ; leur dérivée sur les appuis donne l'effort, sans inertie d'appui mobile.

Critères avant calcul : bilan/référence IE ≤1% du travail cible +0,001 J ; travail surfacique/G ≤2% ; recharge au même pic ≤0,5% ; effort/référence ≤2% du pic ; position ≤0,0001 mm ; demi-pas et normalisation d'aire ≤0,5%. Pas maximum 25 ns, cas demi-pas 12,5 ns ; TH 0,1 µs ; images 5 µs. Deux threads CPU, plafond 180 s par Engine. Il n'y a pas de nouveau calcul de l'avion entier dans A17.

## 5. Résultats dérivés

| Cas | Travail final / aire N/mm | Écart IE à même pic (fraction) | Max résidu J | Max écart effort / pic | Critères échoués |
|---|---:|---:|---:|---:|---|
{table}

Le travail final par aire vaut 50 N/mm dans les quatre cas. Écart final demi-pas et normalisation d'aire : {w['half_dt_final_work_difference_fraction']:.9g} et {w['area_normalized_work_difference_fraction']:.9g}. Les éléments de connexion se séparent réellement dans ces témoins, avec énergie de rupture incluse dans le bilan ; pas de perte inventée ni de RKE reconstruit. Cette réussite contrôle une interface uniforme et une implémentation, **pas la convergence spatiale de l'avion ou la ténacité réelle de son radôme**. Mode mixte, compression et effets de rotation encore ouverts.

Le MP4 et le GIF sont des aperçus des sorties A16 mises en cache. Sélection du premier cas déclaré R20, sans classement selon une ressemblance historique. Les 21 poses tiennent chacune neuf images à 30 Hz ; ralentissement de lecture seul. Le fichier blend contient ces poses natives à interpolation constante, ouvert sur la pose finale. Les couleurs finales y sont sauvegardées ; pour les actualiser avec le temps, réutiliser le script de rendu, car elles ne sont pas un nouveau champ mécanique Blender.

Coût mesuré du solveur A16 : {cfg['cost_estimate']['observed_10ms_seconds'][0]:.3f} et {cfg['cost_estimate']['observed_10ms_seconds'][1]:.3f} s pour 10 ms. Projection linéaire jusqu'à 10 s : **{cfg['cost_estimate']['linear_10s_days']:.3f} jours sur deux threads**, avant nouvelles interactions et modifications du modèle. Ce n'est pas une ETA fiable. Réduire la fréquence des sorties peut réduire stockage/I/O ; cela ne justifie pas d'augmenter le pas ou la masse pour masquer un défaut mécanique.

## 6. Contradictions, données manquantes et suite

Le premier export fonctionne ; l'objectif de 10 secondes physiques n'est pas réalisé. L'horizon couplé reste A16≈0,01 s. La nouvelle liaison n'est pas encore intégrée au radôme, aux métaux ou à la façade. Sa géométrie de séparation, ses propriétés réelles, le mode mixte, la compression, les rotations, l'autocontact des fragments et l'effet sur les masses/assemblages restent à contrôler. Le cœur, l'intérieur de la tour, les planchers/noyau, la gravité, le carburant et les conditions historiques ne sont pas ajoutés par une animation.

Les limites A16 et ses critères matériels ne sont pas transformés en réussite. Une reprise native intacte avec topologie déclarée est nécessaire ; aucune transformation arbitraire du dernier état en fragments. La suite vise un impact couplé de 20 ms, continuable puis prolongé selon le domaine atteint, avec temps/coût/conditions toujours explicites.

{NEXT}
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Reprise WTC1 — AIRCRAFT-A17 → AIRCRAFT-A18

Objectif utilisateur : vidéo 3D des 10 premières secondes physiques, pas 10 secondes de lecture d'un aperçu. Objectif actif, incomplet. Couverture actuelle : {v['physical_duration_s']:.12f} s issue du cas A16R20 conservé.

Rapport : {rel(REPORT)} ; config : {rel(CFG)} ; témoins : {rel(OUT/'cohesive_review.json')} ; route : {rel(OUT/'objectif1_route.json')} ; vidéo : {rel(OUT/'video/APERCU_A16_10ms_ralenti.mp4')} ; GIF : {rel(OUT/'video/APERCU_A16_10ms_ralenti.gif')}.

Quatre contrôles natifs LAW117/TYPE43 passent : travail50N/mm, recharge au même pic, deux aires et demi-pas. En traction et cisaillement purs, éléments supprimés, bilans conformes. Aucun G mesuré ; propriétés pas identifiées au vrai avion ; mode mixte/compression/rotation non qualifiés. N'intégrer que dans un nouveau départ intact après vérification explicite de la topologie et des masses/contacts.

MP4 H2642560×720/30Hz/189 images/6,3s de lecture ; GIF21 poses/300ms. Temps réel simulé0,01s indiqué. Exactes poses natives Blender, ×1, aucune interpolation de géométrie. PNG décodés inspectés ; lecture GUI non certifiée. Échec de journalisation externe initial conservé et helper corrigé ; aucune relance de rendu/ancien Engine.

{p['files']} anciens fichiers protégés, {p['bytes_hashed']/1e9:.3f}Go, vérifiés. {NEXT}
''',encoding='utf-8')
    names=['run_aircraft_a17.py','review_aircraft_a17.py','encode_aircraft_a17.py','verify_aircraft_a17_preservation.py','finalize_aircraft_a17.py'];files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in names]+[ROOT/'wtc1_3d_v4/scripts/render_aircraft_a17.py']
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'prepared':True,'files':len(set(files)),'objective1_complete':False},flush=True)

def register():
    guard();n=check_files(read(OUT/'artifact_manifest.json')['files']);assert harness()['CurrentIteration']=='AIRCRAFT-A16';st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st['next_iteration']=='AIRCRAFT-A17' and cy['pending_iterations']==['AIRCRAFT-A14','AIRCRAFT-A15','AIRCRAFT-A16'];reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
    v=read(OUT/'video/video_audit.json');a=read(OUT/'scientific_assessment.json');t=now();rec={'experiment_id':'WTC1-AIRCRAFT-A17','registered_at':t,'status':'completed_native_cohesive_energy_history_controls_and_interim_3D_MP4_GIF_10ms__10s_goal_open','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'cohesive_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'native_witnesses':4,'new_whole_aircraft_jobs':0,'branch_iteration_count':17,'whole_aircraft_iteration_count':12,**a,'next_iteration':'AIRCRAFT-A18'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A17',next_iteration='AIRCRAFT-A18',current_status=rec['status'],next_objective=NEXT,updated_at=t);st['aircraft_a17_key_results']=rec;st['objective1_video_10s']={'requested_physical_duration_s':10,'current_native_whole_duration_s':v['physical_duration_s'],'status':'active_incomplete','interim_MP4':v['files'][0]['path'],'interim_GIF':v['files'][1]['path'],'route':rel(OUT/'objectif1_route.json'),'physical_goal_complete':False};st['validated_artifacts'].update(aircraft_a17_report=rel(REPORT),aircraft_a17_results=rel(OUT/'cohesive_review.json'),aircraft_a17_handoff=rel(HANDOFF))
    cy.update(pending_iterations=['AIRCRAFT-A14','AIRCRAFT-A15','AIRCRAFT-A16','AIRCRAFT-A17'],pending_count=4,updated_at=t,next_publication_after='A14+A15 and A16+A17 pairs pending; preserve scientific failures and incomplete physical10s objective');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or check_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_artifact_hashes_pass':True,'all_old_protected_files_pass':read(OUT/'preservation_verification.json')['pass'],'old_policies_and_results_preserved':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A17','route':st['current_iteration']=='AIRCRAFT-A17' and st['next_iteration']=='AIRCRAFT-A18','objective10s_recorded_incomplete':st['objective1_video_10s']['requested_physical_duration_s']==10 and not st['objective1_video_10s']['physical_goal_complete'],'harness_pass':v['Status']=='PASS','publication_pending_preserved':cy['pending_count']==4 and cy['pending_iterations']==['AIRCRAFT-A14','AIRCRAFT-A15','AIRCRAFT-A16','AIRCRAFT-A17'],'remote_baseline_unchanged':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':v,'external_publication_performed':False,'objective1_complete':False,'physical_impact_qualified':False};assert proof['pass'];dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
