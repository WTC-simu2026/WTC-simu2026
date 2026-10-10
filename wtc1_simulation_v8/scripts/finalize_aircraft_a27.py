"""Seal unsuccessful composite bending qualification without concealing any gate."""
from run_aircraft_a27 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a27.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A27_HANDOFF.md'

def route():
    return ('AIRCRAFT-A28 : reprendre composite_qualification_review.json et constitutive_observation.json. '
      'A26 métal HA8 passe9contrôles isolés; A27 TYPE22 LAW25 conserve masse, énergie, quantité de mouvement et moment physique libresXYZ, mais sa flexion ne passe pas la référence indépendante. '
      'Ne pas sélectionner un nombre de couches pour croiser artificiellement la référence. Les3/9couches sont des subdivisions numériques du même matériau homogène; le passageN6/N12 ne résout pas l’écart. '
      'Comparer maintenant contraintes et moments de flexion natifs à la cinématique réellement interpolée et aux tenseurs constitutifs explicites, puis tester une alternative volumique orthotrope si nécessaire, sans modifier les paramètres pour obtenir le dommage connu. '
      'La matrice3D couplée de la théorie LAW25 et la réponse observée TYPE22 restent à réconcilier; les contrôles planes réussis ne qualifient pas la réponse3D générale ou la rupture historique. '
      'Ensuite seulement vérifier le cœur/sandwich et les24racines/144ancres courbes A25. Aucun montage entier d’une liaison non qualifiée, aucune prolongation A21. '
      'Objectif vidéo3D10secondes physiques incomplet, meilleur entier A20=20ms. Nouveau départ intact après bilans et mesure du coût. '
      'Publication A26+A27 après intégrité; conserver tous les échecs, aucune compensation de masse ou RKE.')

def prepare():
    guard();assert not REPORT.exists();p=read(OUT/'preservation_verification.json');r=read(OUT/'composite_qualification_review.json');assert p['pass'] and not r['composite_prototype_pass'] and r['free_and_membrane_scope_pass'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
    st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A26' and cy['pending_iterations']==['AIRCRAFT-A26'];assert (ROOT/'harness/experiments/registry.jsonl').read_bytes()==(OUT/'before_registry.jsonl').read_bytes()
    rows=r['cases'];executions=[{'path':rel(x),**read(x)} for x in sorted(OUT.glob('w*/*/*.execution.json'))];dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads':1,'GPU':False,'execution_seconds_sum':sum(x.get('seconds',0) for x in executions),'executions':executions,'executables':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A27','status':'completed_composite_controls__bending_reference_failed','native_controls':len(rows),'native_individual_sets_passed':sum(x['pass'] for x in rows),'native_energy_balances_passed':sum(x['checks']['native_full_balance'] for x in rows),'failed_controls':[{'revision':x['revision'],'case':x['case'],'checks':[k for k,v in x['checks'].items() if not v]} for x in rows if not x['pass']],'Starter_only_failed_attempts':1,'native_field_samples':len(read(OUT/'native_fields_review.json')['samples']),'free_and_plane_membrane_scope_pass':r['free_and_membrane_scope_pass'],'composite_bending_qualified':False,'general_3D_constitutive_equivalence_qualified':False,'whole_insertion_ready':False,'new_whole_impact_executed':False,'old_native_solver_reruns':0,'physical_strength_and_fracture_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A28'};dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'assessment':a,'composite_qualification_review':rel(OUT/'composite_qualification_review.json'),'failed_attempts_preserved':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route()})
    table='\n'.join(f"| {x['revision']} / {x['case']} | {x['maximum_residual_J']:.9g} | {'réussi' if x['pass'] else '**échoué**: '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows)
    elastic='\n'.join(f"| {x['revision']} / {x['case']} | {x['native_elastic_comparison_J']:.10g} | {x['elastic_reference_J']:.10g} | {100*(x['native_elastic_comparison_J']/x['elastic_reference_J']-1):.6g}% |" for x in rows if not x['case'].startswith('FREE'))
    obs=read(OUT/'constitutive_observation.json')
    REPORT.write_text(f'''# AIRCRAFT-A27 — contrôle volumique de la peau composite

**22 nouveaux calculs natifs complets**, une tentative Starter conservée. Les22bilans complets natifs passent; les mouvements libres conservent la masse et les moments. La traction plane corrigée passe. **La flexion échoue encore**, au critère indépendant conservé: la peau composite et le raccordement entier ne sont pas qualifiés.

## 1. Faits directement observés ou transcrits

Graine1102052, aucun tirage aléatoire. Plaque10×10×0,5mm, volume50mm³. LAW25/4 hérité inchangé:rho0,00183g/mm³, masse0,0915g, E11=E22=22000MPa, nu12=0,25, E33=10000MPa, G12=G23=G31=4000MPa. Le matériau et les paramètres de l'avion entier restent intacts. TYPE22 HA8 à translations, direction d'épaisseur s (Icstr010), angle90°. Aucune rotation nodale indépendante, RKE nulle, aucun ajout de masse, aucune mise à l'échelle.

w0 utilise des positions/poids Gauss proposés comme données de couches: le Starter refuse ces rapports irréguliers (avertissement674). Entrée et sortie conservées, aucun Engine lancé. w1 remplace ces données par3subdivisions homogènes régulières avec positions automatiques; neuf calculs exécutés. w2 conserve3subdivisions et change seulement le déplacement transversal imposé dans quatre contrôles élastiques. w3 utilise9subdivisions et les chargements planes corrigés; neuf nouveaux calculs. Toutes les configurations et critères sont déclarés avant leurs calculs. Les22lectures natives des positions et masses passent. CPU1thread, aucun GPU.

Les{a['native_field_samples']}échantillons de champs sont finis, sans suppression d'élément, et passent l'identité coordonnées=données initiales+déplacement avec borne d'impression explicite. Les seuils physiques restent inchangés. Préservation vérifiée de{p['files']}fichiers antérieurs, soit{p['bytes_hashed']/1e9:.3f}Go; aucune archive source rescannée.

## 2. Résultats d'un modèle officiel

[TYPE22](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type22_tsh_comp_starter_r.htm) définit des rapports d'épaisseur et positions de couches, et non une entrée libre de poids Gauss. Les lectures Starter confirment les centres réguliers3/9. [LAW25 Tsai-Wu](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tsai_wu_formulation_starter_r.htm) distingue la direction transverse élastique des critères de plasticité du plan. La [théorie LAW25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/law25_composite_material_r.htm) montre une matrice de compliance3D avec couplage transverse de Poisson. Sa correspondance complète avec cette réponse TYPE22 n'est pas établie. Documentation et observations natives sont gardées séparément; aucun modèle NIST ou dommage connu n'est ajusté.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo, photographie ou affirmation historique. Le fichier A20 effectivement utilisé et sa carte LAW25 sont identifiés par SHA256 dans material_source_addendum.json. Cette carte est une référence élastique: résistances numériques très élevées et rupture inactive; elle n'est pas une identification de peau Boeing réelle. Les24racines/144ancres A25 restent disponibles, sans insertion d'une nouvelle liaison.

## 4. Hypothèses propres au modèle

Les3/9subdivisions traversent un même milieu homogène, avec même densité, orientation et volume. Elles n'affirment pas un empilement physique mesuré. Les masses nodales sont intégrées avec la densité source; leur changement par rapport au témoin métallique0,139g correspond à un autre matériau explicitement déclaré, sans compensation.

Rotations libres10rad/ms surXYZ pendant0,05ms, translation[-200,5,2]m/s, contrôleY à pas réduit. w1 impose en traction epsilon=[0,001;−0,00025;−0,00025]. La référence initiale ne contient que l'énergie de traction plane. w2/w3 imposent uz=0, avec ux=0,001x, uy=−0,00025y. La flexion utilise ux=−kxz−k²x³/6, uy=0, uz=kx²/2, k=0,001/mm. Le terme z² retiré par rapport à w1 est constant aux deux faces du maillage géométrique à une couche; sa suppression ne corrige donc pas la flexion interpolée dans l'épaisseur.

Références indépendantes conservées: traction0,5E11·epsilon²·volume et flexion0,5D11·k²·aire, D11=E11t³/[12(1−nu12nu21)]. Hypothèse de réponse plane précisée dans les configurations, sans extrapolation à la matrice3D générale. Le choix9subdivisions précède les nouveaux calculs: l'erreur de second moment par centres uniformes vaut théoriquement1/N², soit1/81<2%. Ce calcul est **un composant d'erreur de quadrature**, pas une prédiction suffisante de l'énergie HA8 totale. Aucun nombre intermédiaire n'est recherché pour rejoindre la référence.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
{table}

| Contrôle élastique | Energie native(J) | Référence plane(J) | Ecart |
|---|---:|---:|---:|
{elastic}

La différence de traction w1−w2 vaut{obs['transverse_loading_diagnostic']['difference_J']:.10g}J, proche de0,5E33·epsilon_z²·volume={obs['transverse_loading_diagnostic']['candidate_independent_E33_extra_J']:.10g}J. Les contraintes natives globales w1 sont proches de[22;0;−2,5]MPa; w2/w3 montrent la suppression de sigma_z. Cela étaye le diagnostic de chargement transverse, sans établir toute une matrice constitutive. Les anciens contrôles w1 et leurs quatre échecs de référence ne sont pas réécrits.

La flexion3subdivisions reste environ6,89% sous la référence; avec9subdivisions elle est environ3,45% au-dessus. Les deux choix échouent au seuil2%+1e−7J. L'écart spatialN6/N12 est faible et passe5%, alors que la sensibilité3/9dans l'épaisseur reste importante. Une convergence spatiale faible ne supprime pas le défaut de référence. Le pas réduitY w3 vaut{r['refinement']['actual_dt_ratio']:.9g}fois l'initial, avec différence de moment{r['refinement']['physical_L_difference_kg_m2_s']:.10g}kg·m²/s et d'énergie{r['refinement']['energy_difference_J']:.10g}J: critères temporels réussis. Aucun terme RKE inventé ou retrait du bilan natif.

## 6. Contradictions et informations manquantes

La peau TYPE22 ne satisfait pas encore la rigidité de flexion de référence. Les effets de cinématique interpolée, intégration volumique et traitement constitutif doivent être séparés. L'interprétation globale de la compliance3D officielle et celle observée dans ce témoin restent à réconcilier; la traction plane réussie ne permet pas d'annoncer une équivalence3D générale. La résistance et la rupture réelles, les liaisons courbes, le cœur, la façade, la gravité, l'intérieur porteur et les contacts de fragments restent ouverts. A26 métal reste qualifié seulement dans son domaine de plaque isolée. Aucun nouvel impact entier n'a été lancé; le meilleur entier reste A20=20ms, avec échecs locaux A21 préservés. Vidéo10secondes physiques incomplète.

{route()}
''',encoding='utf-8');HANDOFF.write_text('# Reprise AIRCRAFT-A27 → AIRCRAFT-A28\n\nRapport: '+rel(REPORT)+'\nRésultats: '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf-8')
    files=[x for x in OUT.rglob('*') if x.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a27*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a27*.json'))+[HANDOFF];dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in sorted(set(files))]});print({'A27_prepared':True,'composite_bending_pass':False,'failed_gates_preserved':True},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();record={'experiment_id':'WTC1-AIRCRAFT-A27','registered_at':t,'configuration':rel(CFG),'configurations':[rel(q) for q in sorted((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a27*.json'))],'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A27',next_iteration='AIRCRAFT-A28',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a27_key_results']=record;st['validated_artifacts'].update(aircraft_a27_report=rel(REPORT),aircraft_a27_results=rel(OUT/'composite_qualification_review.json'),aircraft_a27_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A27');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A26+AIRCRAFT-A27 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A27','route':st['current_iteration']=='AIRCRAFT-A27' and st['next_iteration']=='AIRCRAFT-A28','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A26','AIRCRAFT-A27'] and cy['pending_count']==2,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};p={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'composite_bending_qualified':False,'whole_insertion_ready':False,'objective1_complete':False};assert p['pass'],checks;dump(OUT/'publication_verification.json',p);print(p,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
