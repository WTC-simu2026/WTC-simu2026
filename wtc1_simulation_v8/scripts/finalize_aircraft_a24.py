"""Seal A24 penalty controls, including converged physical angular-momentum failure."""
from run_aircraft_a24 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a24.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A24_HANDOFF.md'

def route():
    return ('AIRCRAFT-A25 : réemployer les45contrôles A24 et leurs échecs, sans relancer A20–A24. '
      'Spot25 conserve les masses et retrouve l’énergie cinétique initiale ajoutée; Stfac100 retrouve la traction N4/N8, mais le moment cinétique physique libre échoue surXYZ, même au pas réduit. '
      'Ne pas monter cette attache décalée sur l’avion. Tester une transmission des efforts aux points de raccordement, avec surfaces de reprise explicites et aucun bras de levier caché. '
      'Déclarer tout changement de géométrie, de masse nodale et de capacité. Le solide4×1×0,5mm et LAW2 hérité restent des hypothèses de prototype, pas une attache AA11 identifiée. '
      'Vérifier libreXYZ, translation, rigidité3D indépendante, pas et géométrie courbe des24racines/144ancres avant un nouveau départ entier intact. Garder le sandwich et les Spot5 A20 validés. '
      'Si l’on raffine une surface principale, vérifier sa masse, son tenseur et sa rigidité; aucune compensation de densité, ADMAS ou RKE. '
      'Le bilan local A21 reste échoué; matériaux, gravité, intérieur porteur, fracture et contacts des fragments restent ouverts. '
      'Objectif10secondes physiques3D incomplet; meilleur calcul entier20ms A20. Estimer le coût réel du prochain entier avant tout lancement de plusieurs heures. Publication suivante A24+A25 après intégrité vérifiée; aucun dommage connu comme cible.')

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists()
    p=read(OUT/'preservation_verification.json');f=read(OUT/'native_fields_review.json');c=read(OUT/'cached_case_review.json');ang=read(OUT/'physical_angular_momentum_review.json');stiff=read(OUT/'stiffness_review.json');assert p['pass'] and f['pass'] and c['native_controls']==45 and c['native_balances_passed']==45
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
    executions=[{'path':rel(x),**read(x)} for x in sorted(OUT.glob('w*/*/*.execution.json'))]
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads':1,'GPU':False,'execution_seconds_sum':sum(x.get('seconds',0) for x in executions),'executions':executions,'executables':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    rows=c['cases'];failed=[{'revision':r['revision'],'case':r['case'],'checks':[k for k,v in r['checks'].items() if not v]} for r in rows if not r['pass']]
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A24','status':'completed_penalty_transmission_controls__physical_angular_momentum_failed','native_controls':45,'native_energy_balances_passed':45,'native_individual_sets_passed':c['individual_sets_passed'],'native_fields_samples':135,'failed_controls':failed,'paired_initial_added_KE_pass':True,'Stfac100_elastic_reference_and_mesh_pass':stiff['selected_pair_pass'],'physical_free_angular_momentum_pass':ang['pass'],'whole_insertion_ready':False,'new_whole_impact_executed':False,'old_A20_A23_native_solver_reruns':0,'observation_repeats_A24_references':4,'physical_strength_and_fracture_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A25'}
    dump(OUT/'scientific_assessment.json',assessment)
    dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'assessment':assessment,'w2_generation_failure_retained':True,'w2_unexecuted_native_cases':4,'angular_reader_json_failure_retained':True,'physical_angular_review':rel(OUT/'physical_angular_momentum_review.json'),'original_failed_attempts_preserved':True})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'current_whole_physical_s':.0200001220703125,'complete':False,'next':route()})
    table='\n'.join(f"| {r['revision']} / {r['case']} | {r['maximum_residual_J']:.8g} | {'réussi' if r['pass'] else '**échoué**: '+', '.join(k for k,v in r['checks'].items() if not v)} |" for r in rows)
    lt='\n'.join(f"| {r['motion']} | {r['connected']['maximum_L_drift_kg_m2_s']:.9g} | {r['connected']['tolerance_kg_m2_s']:.9g} | {r['maximum_added_L_error_kg_m2_s']:.9g} | {r['added_L_tolerance_kg_m2_s']:.9g} | {'réussi' if r['pass'] else '**échoué**'} |" for r in ang['pairs'])
    it='\n'.join(f"| {r['axis']} | {r['native_added_I_median_g_mm2']:.9g} | {r['known_I_g_mm2']:.9g} | {'réussi' if r['pass'] else 'échoué'} |" for r in read(OUT/'paired_coupling_w1_review.json')['pairs'])
    REPORT.write_text(f'''# AIRCRAFT-A24 — transmission par pénalité et moment cinétique physique

**45 nouveaux contrôles natifs**, tous avec bilan énergétique réussi. La masse et l'énergie cinétique initiale ajoutée sont correctes. La traction de prototype converge avec Stfac100. **Le moment cinétique libre du montage décalé échoue surXYZ**, et cet échec demeure à pas réduit. La liaison n'est pas montée sur l'avion. L'objectif de vidéo3D des10premières secondes physiques reste incomplet; A20 couvre20ms.

## 1. Faits directement observés ou transcrits

Graine1102049, aucun tirage aléatoire. Campagnes w0:19calculs, w1:10, w2:6, w3:10. Chaque calcul conserve entrée Starter/Engine, sorties natives, journaux, code générateur, masses, bilan complet et critères. Aucun nouveau calcul entier, aucun calcul A20–A23 répété. Quatre références A24 sont recalculées sous une déclaration d'observation nouvelle pour obtenir VRX/VRY/VRZ, indisponibles dans l'observation initiale. Les autres références et les six tractions w2 sont réemployées.

Visc=0 est lu par le Starter comme le défaut0,05, avec dissipation native: les échecs du critère de dissipation≤1e-12J sont conservés. w1 utilise une valeur positive1e-20, effectivement relue avant Engine; elle représente une viscosité négligeable, sans prétendre être exactement nulle. Les matériaux, masses et seuils de bilan ne changent pas. w2 fait varier Stfac1/10/100 et contrôle sa relecture. Après ses six tractions, son générateur échoue sur le suffixe S100_X avant tout lancement natif libre. Cette tentative est gardée; w3 déclare une correction explicite de lecture de l'axe et ajoute les vitesses angulaires natives.

Les135champs natifs échantillonnés sont finis, conservent les éléments et passent une identité coordonnées/déplacements bornée par le stockage float32 et l'impression à six chiffres. Cette borne de lecture ne modifie aucun seuil mécanique. Un booléen NumPy empêche la première écriture JSON de l'audit angulaire; le lecteur initial est conservé, puis sa conversion en booléen Python permet l'écriture. Aucun solveur ni résultat antérieur n'est changé. Conservation vérifiée de{p['files']}fichiers antérieurs, soit{p['bytes_hashed']/1e9:.3f}Go.

## 2. Résultats d'un modèle officiel

La documentation primaire [TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm) définit Spot25 comme une pénalité, décrit la rigidité issue des raideurs nodales, et signale ses limites de transmission des moments. Le solide secondaire n'a ici que des translations. Cela ne garantit toutefois pas la conservation du moment physique du montage, qui est mesurée séparément. Le [TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm) fournit les vitesses angulaires VRX/VRY/VRZ. Aucun résultat officiel de dommage n'est pris comme cible. Ces documents décrivent le solveur, pas une attache historique.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de vidéo, photographie ou dommage historique. Réemploi en lecture seule de la géométrie A20 et des sources techniques sauvegardées. Les courbes acier A22 restent non adoptées et leur début de striction n'est pas un seuil de rupture.

## 4. Hypothèses propres au modèle

Solide HA8 TYPE14 à translations,4×1×0,5mm, masse0,00556g, LAW2 hérité rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, sans écrouissage ni rupture. Prototype de capacité axiale162N, sans identification AA11. Support10×10×0,5mm et sandwich A20, masses0,3604g sans et0,36596g avec solide. Les attaches du cœur Spot5 p3 sont inchangées. Seules les deux attaches d'extrémité301/302 utilisent Spot25, Istf2, dsearch0,8mm. Stfac est un paramètre de pénalité, pas une résistance matérielle ajustée. Les zéros hérités des coefficients de viscosité volumique sont des demandes de défaut natif, pas des suppressions affirmées.

Toutes les huit énergies natives sont incluses: cinétique de translation, rotation, interne, hourglass, ressort, contact élastique, contact de frottement et contact amorti. Résidu E(t)−E(0)−travail extérieur; g/mm/ms convertis en J par0,001. Aucune reconstruction RKE, ADMAS, mise à l'échelle ou compensation de densité.

Le moment physique est calculé par Σm r×v et l'inertie propre de l'épaisseur des coques avec leurs vitesses angulaires réellement enregistrées. Le tenseur d'épaisseur est m t²/12(I−n⊗n), sans compter deux fois la distribution dans le plan. Conversion g·mm²/ms vers kg·m²/s par1e-6. Aucun moment n'est déduit d'une énergie RKE scalaire. Ce calcul est un contrôle du modèle discret, pas une validation de l'événement historique.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Critères individuels |
|---|---:|---|
{table}

Les45bilans passent, et{c['individual_sets_passed']}/45ensembles individuels passent. Ces ensembles initiaux n'incluent pas encore le moment physique: l'audit angulaire supplémentaire conserve donc un échec malgré les dix réussites individuelles w3.

| Axe, rotation prescrite w1 | Inertie ajoutée native(g·mm²) | Inertie discrète connue | Critères cinétiques |
|---|---:|---:|---|
{it}

La pénalité élimine le biais cinétique ajouté constaté dans A23 sur les trois axes. Les paires initiales libres passent aussi. Cela ne qualifie pas la transmission des couples. La rotation prescrite w1 à pas réduit passe l'inertie individuelle mais échoue à la convergence de l'énergie ajoutée: écart2,38738149e-7J, seuil1,41149857e-7J. La traction Stfac1 reste trop souple; les deux maillages Stfac100 passent la référence3D rigide et leur écart de maillage est{100*stiff['rows'][-1]['mesh_relative_difference']:.4f}%, sous5%. L'échec initial de traction est conservé.

| Mouvement libre Stfac100 | Dérive du moment total(kg·m²/s) | Seuil total | Erreur du moment ajouté | Seuil ajouté | Résultat |
|---|---:|---:|---:|---:|---|
{lt}

Les trois références sans solide passent le contrôle de moment total. Le montage échoue enXYZ; la translation uniforme passe. Le pas effectif réduit enY vaut{ang['refinement']['actual_dt_ratio']:.9g}fois le pas initial. La différence entre moments des deux pas vaut{ang['refinement']['L_difference_kg_m2_s']:.9g}kg·m²/s, très inférieure à la dérive: celle-ci ne disparaît pas avec le raffinement temporel testé. La convergence du bilan natif et du moment calculé ne signifie pas conservation physique.

## 6. Contradictions et informations manquantes

Une masse correcte, une énergie correcte et une traction convergée ne garantissent pas les couples transmis. Le décalage entre les extrémités solides et la surface principale est une hypothèse de diagnostic; sa responsabilité n'est pas prouvée par le seul échec. Une nouvelle géométrie de reprise des efforts doit être déclarée et testée. La courbure réelle des24racines et les144ancres ne sont pas qualifiées par ce témoin plat. Résistance historique, rupture, arrachement, cisaillement et propriétés à grande vitesse restent inconnus. L'échec local A21 n'est pas expliqué en totalité. Gravité, structure intérieure porteuse et contacts de fragments restent à traiter avant extension aux10secondes. Les anciens calculs et aperçus sont préservés; aucune continuation d'un état invalide.

{route()}
''',encoding='utf-8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A24 → AIRCRAFT-A25\n\nRapport: '+rel(REPORT)+'\nRésultats: '+rel(OUT/'campaign_review.json')+'\n\n'+route()+'\n',encoding='utf-8')
    files=[x for x in OUT.rglob('*') if x.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a24*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a24*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in sorted(set(files))]})
    print({'A24_prepared':True,'controls':45,'physical_angular_momentum_pass':False},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and st['current_iteration']=='AIRCRAFT-A23';reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes() and cy==read(OUT/'before_publication_cycle.json')
    a=read(OUT/'scientific_assessment.json');t=now();record={'experiment_id':'WTC1-AIRCRAFT-A24','registered_at':t,'configuration':rel(CFG),'configurations':[rel(p) for p in sorted((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a24*.json'))],'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A24',next_iteration='AIRCRAFT-A25',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a24_key_results']=record;st['validated_artifacts'].update(aircraft_a24_report=rel(REPORT),aircraft_a24_results=rel(OUT/'campaign_review.json'),aircraft_a24_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A24');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A24+AIRCRAFT-A25 verified')
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_hashes':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_results_and_policies':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A24','route':st['current_iteration']=='AIRCRAFT-A24' and st['next_iteration']=='AIRCRAFT-A25','objective_and_preview_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','one_pending_iteration':cy['pending_iterations']==['AIRCRAFT-A24'] and cy['pending_count']==1,'publication_A23_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False};assert proof['pass'],checks;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
