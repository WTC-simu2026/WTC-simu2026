"""Seal local A19 findings and move the durable route only after reviewed artifacts exist."""
from run_aircraft_a19 import *
from run_aircraft_a19_whole import WCFG,WCASE,D,whole_guard
REPORT=OUT/'rapport_aircraft_a19.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A19_HANDOFF.md'
NEXT="AIRCRAFT-A20 : objectif vidéo3D10 secondes physiques actif/incomplet. A19 a localisé99,75% de l'IE négative A18 dans12 facettes, vérifié les vrais champs ply42 (le legacy layer2 nul ne représente pas le cœur), effectué4 contrôles de triangle réussis et un nouveau départ intact20ms Ish3n31. IE totale radôme devenue positive328236J mais16 facettes négatives à la fin, minimum transitoire-49669J; local_energy échoué et domaines métal/façade dépassés. La rupture de cisaillement LAW25 gamma_ini/gamma_max lue par Starter ne s'active pas dans les2 témoins TYPE51: conserver ces échecs, ne pas l'intégrer comme correction. Lire source_inspection.json: appel m25delam limité àigmat0 dans le code public épinglé; équivalence avec le binaire non prouvée. Prochaine modification : traiter explicitement le cœur en3D (LAW28 ou loi compatible vérifiée) et le couplage aux peaux, avec cisaillement/crushing fini, pas seulement changer Ish3n. Fiche HRH10 p4 fournitrho48,E33=138,G31=41,G23=24MPa,tau31=1.21,tau23=.69MPa,compression nue2.07MPa, essais12.7mm; épaisseur8mm et branches postpic/G sont hypothèses, pas valeurs mesurées AA11. Déclarer les plages avant calcul, garder masse/CG/inertie/énergie et fragments/contact contrôlés; aucun retrait de cœur ou RKE inventé. Une modification mécanique exige un nouveau départ intact. Ne prolonger les20ms invalides vers100ms sans correction des déficits matériels/énergétiques. Ensuite100ms,1s,10s avec gravité/intérieur réellement modélisé, checkpoints, cadence de sorties réduite, coût annoncé et pas de mass scaling. Réutiliser les sorties et les contrôles A19 sans les relancer. Publication A12+A13 intacte; A14 àA19 en attente."

def check_files(rows):
    for r in rows:
        p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
    return len(rows)

def prepare():
    guard();whole_guard();assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists()
    p=read(OUT/'preservation_verification.json');r=read(D/'review.json');v=read(OUT/'video/video_audit.json');a0=read(OUT/'cached_fragment_diagnostic.json');a1=read(OUT/'whole_fragment_diagnostic.json');neg=read(OUT/'whole_negative_energy_diagnostic.json');tri=read(OUT/'triangle_review.json');core=read(OUT/'core_shear_review.json');ini=read(D/'initial_native_review.json')
    assert p['pass'] and v['pass'] and not v['objective1_complete'] and read(OUT/'visual_QA.json')['decoded_contact_sheet_inspected'];assert harness()['Status']=='PASS';wall=read(D/'engine.log.execution.json')['seconds'];old=read(SOURCE/'review.json')
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A19','new_whole_aircraft_jobs':1,'new_triangle_witnesses':4,'new_core_shear_witnesses':3,'cached_A18_frames_read':a0['native_frames_read'],'fresh_A19_frames_read':a1['native_frames_read'],'isolated_end_observer_diagnostics':1,'old_solver_reruns':0,
      'native_horizon_s':r['end_ms']*.001,'main_engine_wall_s':wall,'all_declared_whole_checks_pass':r['all_declared_checks_pass'],'failed_whole_checks':r['failed_checks'],'global_energy_pass':r['checks']['global_energy'],'local_energy_pass':r['checks']['local_energy'],
      'element_IE_nonnegative_pass':neg['expected_nonnegative_pass'],'final_radome_IE_J':neg['native_radome_part_final_IE_J'],'final_negative_radome_elements':neg['negative_final_element_count'],'minimum_radome_element_IE_J':neg['native_element_minimum_IE_J'],
      'triangle_witnesses_pass':tri['pass'],'core_shear_witnesses_pass':core['pass'],'finite_core_shear_keyword_effective':False,'core_fracture_or_crushing_modelled':False,'initial_mass_CG_inertia_pass':all(ini['checks'].values()),'mass_bearing_shells_not_deleted':r['checks']['mass_bearing_shells_not_deleted'],
      'native_detached_groups':r['final_fragment_connectivity']['detached_components'],'same_mass_material_contact_conditions':True,'only_whole_mechanical_change':'radome TYPE51 Ish3n2 to31',
      'native_source_binary_equivalence_verified':False,'unique_negative_energy_cause_identified':False,'whole_aircraft_impact_qualified':False,'physical_G_measured':False,'metal_fracture_modelled':False,'tower_interior_modelled':False,'gravity_modelled':False,'historical_conditions_identified':False,'objective1_target_s':10,'objective1_complete':False,'NIST_outcomes_used_as_target':False,'old_failed_gates_retained':True}
    dump(OUT/'scientific_assessment.json',assessment);dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'coverage_s':v['physical_duration_s'],'display_s':v['display_duration_s'],'complete':False,'new_defect_diagnosis_complete':True,'numerical_and_material_qualification':False,'next':NEXT,'horizon_steps_s':[.02,.1,1,10],'new_20ms_wall_s':wall,'linear_10s_days':wall/20*10000/86400,'linear_projection_is_not_ETA':True})
    table='\n'.join(f"| {k} | {'réussi' if val else '**échoué**'} |" for k,val in r['checks'].items());ctable='\n'.join(f"| {q['case']} | {q['last_IE_J']:.6f} | {q['final_shell_alive']} | {'réussi' if q['pass'] else '**échoué**'} |" for q in core['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A19 — localisation du défaut du nez et comparaison native20ms

Un nouveau calcul couplé et son MP4/GIF couvrent **{r['end_ms']:.9f}ms physiques**. La formulation alternative réduit fortement le défaut mais ne le résout pas. **L'objectif des10 premières secondes physiques reste actif et incomplet.** Le bilan local, certains bilans par facette et les domaines matériels échouent encore.

## 1. Faits directement observés ou transcrits

Graine1102044, zéro tirage. Quatre déclarations complémentaires immuables précèdent les nouveaux contrôles, l'observateur et l'impact; la déclaration générale A19 précède l'analyse des sorties conservées. Aucun ancien impact relancé.101 états natifs A18 lus puis101 états du nouvel impact. Lecture indépendante des coordonnées, masses, vitesses, contraintes/déformations et énergie spécifique confrontée au convertisseur natif. Un observateur isolé de l'ancien checkpoint final fournit les neuf points de ply41/42/43 sans changer ce checkpoint ni les sorties principales.

La facette174 A18 porte-41,656353MJ à20ms, s'étire56,50fois et atteint152,40fois son aire initiale. Les12 facettes les plus négatives portent99,75% de l'énergie négative finale. Le champ legacy «layer2» nul ne pouvait pas être identifié comme le cœur: la demande explicite **ply42, point2** donne des déformations natives[3,982207;-1,101313;11,694304] et des contraintes[4,320553;-1,119560;10,704959]MPa. Les deux peaux ont dommage1 et le cœur dommage0. Les anciens zéros sont conservés avec une correction de leur interprétation, sans écraser l'analyse originale.

Un nouvel impact entier dure{wall:.3f}s sur2threads CPU, fin normale43187cycles. Géométrie, matériau, masse, épaisseur, résistances, G cohésif, contacts, appuis et vitesse[-200;5;2]m/s identiques àA18. Une seule carte mécanique change: TYPE51/21, Ish3n2→31. Les masses et moments initiaux passent les contrôles natifs et indépendants. Starter conserve les deux avertissements1166/343 associés aux576 coins d'autocontact initialement coïncidents; le critère zéro avertissement reste échoué.

La fiche locale Hexcel HRH10 p4 donne pour le produit de référence3.2-48: densité48kg/m³, E33=138MPa, G31=41/G23=24MPa, cisaillement1,21/0,69MPa, compression nue2,07MPa. Ces valeurs typiques sont mesurées avec une épaisseur12,7mm à température ambiante. Elles n'identifient pas le radôme historique ni une courbe dynamique de rupture.

## 2. Résultats d'un modèle officiel

Aucune sortie de dommages NIST n'est utilisée pour sélectionner les paramètres, les facettes ou le film. Les références Altair décrivent les commandes du solveur: [TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm), [sorties explicites par ply](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_idply_restype_engine_r.htm), [LAW25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tsai_wu_formulation_starter_r.htm). Ce sont des spécifications et non des résultats de l'impact réel.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, vidéo ou photographie n'a été analysée. Le diagnostic s'appuie sur les fichiers natifs conservés, la fiche matériau déjà acquise et une inspection ciblée du code public. Les sources restent en lecture seule. La vérification SHA256 porte sur{p['files']}anciens fichiers, {p['bytes_hashed']/1e9:.3f}Go, sans modification constatée.

## 4. Hypothèses propres au modèle

Le sandwich0,5/8/0,5mm, ses orientations, le cœur élastique à faibles rigidités dans son plan et la fracture des peaux restent des hypothèses. G des arêtes50N/mm n'est pas mesuré. La façade couvre trois niveaux représentatifs, sans intérieur de tour, gravité, carburant résolu ni identification complète des conditions historiques. Les fissures suivent les arêtes de triangles et l'autocontact initial n'est pas qualifié.

Les témoins de cisaillement testent un cœur8mm seul, avec rayon de déclenchement min(1,21/41;0,69/24)=0,02875 et deux phases de dégradation de2% et20%: ce dernier choix est hypothétique, sans G mesuré. Ils ne sont pas transférés au modèle complet.

## 5. Résultats dérivés

Les quatre témoins de triangle réussissent: rotation rigide90° à énergie interne quasi nulle et traction biaxiale0,001 à énergie1,320832J, référence analytique1,320392J, pour Ish3n2 et31. Ces contrôles couvrent une rotation rigide et une petite déformation; ils ne qualifient pas un cœur écrasé ou étiré à plusieurs centaines de pour cent.

| Grandeur à20ms | A18 conservé | A19 neuf |
|---|---:|---:|
| IE totale radôme (J) | -42148524 | {neg['native_radome_part_final_IE_J']:.3f} |
| Facette la plus négative à la fin (J) | -41656353 | {neg['native_element_final_minimum_IE_J']:.3f} |
| Résidu global final (J) | {old['final_energy_residual_J']:.3f} | {r['final_energy_residual_J']:.3f} |
| Erreur maximale d'offset(mm) | {old['maximum_RBE2_offset_distance_error_mm']:.9f} | {r['maximum_RBE2_offset_distance_error_mm']:.9f} |
| Groupes radôme détachés |168|{r['final_fragment_connectivity']['detached_components']}|

La somme native des énergies de216facettes vaut328236,100009J; la part vaut328236,096J, écart0,004009J. **Une somme positive ne masque pas les16facettes encore négatives**: minimum sur tout le parcours{neg['native_element_minimum_IE_J']:.3f}J. L'étirement maximal atteint10,305fois la longueur initiale. La facette162 la plus négative en fin de calcul a encore ses deux peaux rompues et son cœur intact. Les624liaisons ne sont pas toutes rompues:620supprimées,168groupes détachés. Tous les éléments porteurs de masse restent présents.

Les témoins de cœur reproduisent le cisaillement élastique attendu(1,38375J à0,015rad), mais **les deux seuils finis lus correctement par Starter ne déclenchent aucune dégradation ni suppression**:

| Témoin |IE finale(J)|Coque encore présente|Contrôle complet|
|---|---:|---|---|
{ctable}

Le code public épinglé contient un appel de délaminage hérité conditionné par igmat0, cohérent avec cette absence d'effet dans la branche à plies distinctes: [mulawc.F90](https://github.com/OpenCourant/OpenCourant/blob/0168ab344bd743051e996d90c7c8d80728bb04a8/engine/source/materials/mat_share/mulawc.F90). **L'équivalence du code avec le binaire local n'est pas établie**, et aucun logiciel n'a été modifié. Le comportement observé du binaire fait foi pour ces témoins.

| Contrôle impact A19 | Résultat |
|---|---|
{table}

Le contrôle séparé de non-négativité des facettes échoue aussi. Le résidu local maximal normalisé vaut{r['maximum_local_residual_fraction']:.6f}; le seuil et la tolérance de précision sont hérités et restent inchangés. Aucune correction par une RKE inventée, changement de masse ou sélection d'une ressemblance historique.

Le MP4 et le GIF montrent21poses natives à échelle1, sans extrapolation, interpolateur de trajectoire ni physique Blender. **{v['physical_duration_s']:.9f}s physiques** sont ralenties en{v['display_duration_s']:.1f}s de lecture. Les images portent la durée, le défaut énergétique et la qualification exploratoire. Contrôles d'encodage, décodage première/milieu/dernière et inspection visuelle enregistrés; lecture GUI non certifiée.

## 6. Contradictions et informations manquantes

Le changement de triangle contribue nettement au défaut mais ne démontre pas sa cause unique. Le cœur substitut non fissuré autorise encore des distorsions hors domaine, et la commande de rupture essayée n'agit pas dans cette configuration. La couverture legacy layer2 s'est révélée ambiguë; les sorties nouvelles utilisent explicitement ply42. La non-négativité par facette, le bilan local, le domaine métal/poutres et la référence de résistance des peaux restent échoués. Les anciens critères échoués A18, y compris la couverture annoncée de9canaux, sont intacts; A19 déclare correctement les4canaux natifs disponibles.

La prochaine étape doit représenter le cœur en3D avec un comportement compatible vérifié, traiter son couplage aux peaux et conserver les budgets de masse et d'énergie. Les données de rupture et de compression après le pic restent manquantes et devront apparaître comme plages déclarées, jamais comme paramètres ajustés au dommage connu. [LAW28](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law28_honeycomb_starter_r.htm) constitue une piste à vérifier, sans intégration déjà qualifiée.

{NEXT}
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Reprise AIRCRAFT-A19 → AIRCRAFT-A20

État local fait foi. Rapport:{rel(REPORT)}. Résultats:{rel(OUT/'campaign_review.json')}. Déclarations A19 générale, triangles, cœur et impact sous data/. Vidéo/GIF20ms:{rel(OUT/'video')}. Objectif10s actif, incomplet.

Lire cached_fragment_diagnostic.json, field_mapping_correction.json, whole_fragment_diagnostic.json, whole_negative_energy_diagnostic.json, core_shear_review.json et source_inspection.json. Aucun ancien Engine à relancer.7témoins courts +1impact neuf20ms, paramètres source non ajustés. Bilans numériques et validation physique séparés. Anciennes sorties:{p['files']}fichiers intacts.

{NEXT}
''',encoding='utf-8')
    scripts=[p for p in (ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a19*.py')];cfgs=[CFG,WCFG,ROOT/'wtc1_simulation_v8/data/aircraft_a19_ply_observer.json',ROOT/'wtc1_simulation_v8/data/aircraft_a19_triangle_declaration.json',ROOT/'wtc1_simulation_v8/data/aircraft_a19_core_shear_declaration.json']
    files=[p for p in OUT.rglob('*') if p.is_file()]+cfgs+scripts+[HANDOFF,ROOT/'wtc1_3d_v4/scripts/render_aircraft_a19.py'];dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'prepared':True,'new_files':len(set(files))},flush=True)

def register():
    guard();n=check_files(read(OUT/'artifact_manifest.json')['files']);assert harness()['CurrentIteration']=='AIRCRAFT-A18';st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st['next_iteration']=='AIRCRAFT-A19';reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
    t=now();a=read(OUT/'scientific_assessment.json');v=read(OUT/'video/video_audit.json');rec={'experiment_id':'WTC1-AIRCRAFT-A19','registered_at':t,'status':'completed_cached_defect_localization_fresh_DKT31_whole20ms_and_MP4_GIF__10s_goal_open','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a,'next_iteration':'AIRCRAFT-A20'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A19',next_iteration='AIRCRAFT-A20',current_status=rec['status'],next_objective=NEXT,updated_at=t);st['aircraft_a19_key_results']=rec;st['objective1_video_10s']={'requested_physical_duration_s':10,'current_native_whole_duration_s':v['physical_duration_s'],'status':'active_incomplete','interim_MP4':v['files'][0]['path'],'interim_GIF':v['files'][1]['path'],'route':rel(OUT/'objectif1_route.json'),'physical_goal_complete':False};st['validated_artifacts'].update(aircraft_a19_report=rel(REPORT),aircraft_a19_results=rel(OUT/'campaign_review.json'),aircraft_a19_handoff=rel(HANDOFF))
    assert 'AIRCRAFT-A19' not in cy['pending_iterations'];cy['pending_iterations'].append('AIRCRAFT-A19');cy.update(pending_count=len(cy['pending_iterations']),updated_at=t,next_publication_after='A14+A15, A16+A17 and A18+A19 pending; explicit external publication authorization required for these files');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or check_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_artifact_hashes':True,'all_old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_policies_and_results_preserved':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A19','route':st['current_iteration']=='AIRCRAFT-A19' and st['next_iteration']=='AIRCRAFT-A20','10s_objective_incomplete':not st['objective1_video_10s']['physical_goal_complete'],'harness_pass':v['Status']=='PASS','pending_prior_preserved':cy['pending_iterations']==oc['pending_iterations']+['AIRCRAFT-A19'] and cy['pending_count']==len(cy['pending_iterations']),'remote_baseline_unchanged':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':v,'external_publication_performed':False,'objective1_complete':False,'physical_impact_qualified':False};assert proof['pass'];dump(OUT/'publication_verification.json',proof);print({k:proof[k] for k in ['pass','new_files_verified','old_files_verified','harness']},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
