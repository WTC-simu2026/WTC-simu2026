"""Seal the native formulation diagnostic with failed gates retained."""
from run_aircraft_a28 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a28.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A28_HANDOFF.md'

def route():
    return ('AIRCRAFT-A29 : reprendre assumed_strain_diagnostic.json, shear_balance_diagnostic.json et composite_qualification_review.json. '
      'Le terme transverse ASQBI E33*(nu/(1-nu))² prédit les6historiques de flexion A27 sans ajustement; il explique une sur-rigidité4,73485% superposée à la quadrature. '
      'Le /DEF_SOLID Icpre1 A28 est écrasé par Icpre3 dans la pièce TYPE22: ne pas l’interpréter comme une suppression effective des termes de Poisson. '
      'HSEPH source préserve les mouvements libres et la membrane mais échoue en flexion et au bilan du cisaillement transverse avec Ashear5/6; aucun correctif comptable. '
      'Tester une branche volumique orthotrope TYPE6 Isolid18 avec même carte LAW25, même volume/densité, orientation90° explicite, tenseur3D documenté et4couches géométriques dans l’épaisseur. '
      'Elle représente une nouvelle hypothèse constitutive3D, pas une équivalence automatique de la peau TYPE22. Vérifier d’abord les6modes affines, puis mouvements libres, flexion plane avec contraction transverse issue du tenseur indépendant, bilans et raffinements. '
      'Si nécessaire tester une loi3D orthotrope explicitement définie, sans caler propriétés ou densité. Puis cœur/sandwich et24racines/144ancres courbes A25. '
      'Nouveau départ entier intact uniquement après bilans et estimation du coût; aucun état A21 prolongé. Objectif vidéo3D10secondes physiques incomplet, meilleur entier20ms. '
      'Publication suivante A28+A29 après intégrité; tous les échecs et bilans natifs conservés, aucun dommage connu comme cible.')

def prepare():
    guard();assert not REPORT.exists();p=read(OUT/'preservation_verification.json');r=read(OUT/'composite_qualification_review.json');a0=read(OUT/'assumed_strain_diagnostic.json');assert p['pass'] and a0['prediction_matches_all'] and not r['composite_prototype_pass'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A27' and cy['pending_count']==0
    rows=r['cases'];ex=[{'path':rel(q),**read(q)} for q in sorted(OUT.glob('w*/*/*.execution.json'))];dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads_per_solver':1,'GPU':False,'executions':ex,'execution_seconds_sum':sum(x.get('seconds',0) for x in ex),'executables':[{'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size} for q in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A28','status':'completed_assumed_strain_diagnostic__thickshell_bending_and_shear_failed','native_controls':22,'native_individual_sets_passed':sum(x['pass'] for x in rows),'native_energy_balances_passed':sum(x['checks']['native_full_balance'] for x in rows),'failed_controls':[{'revision':x['revision'],'case':x['case'],'checks':[k for k,v in x['checks'].items() if not v]} for x in rows if not x['pass']],'cached_native_histories_read':6,'cached_ASQBI_prediction_matches_all':True,'global_pressure_override_applied_to_part':False,'native_field_samples':len(read(OUT/'native_fields_review.json')['samples']),'free_and_membrane_scope_pass':r['free_and_membrane_scope_pass'],'bending_scope_pass':False,'transverse_shear_scope_pass':False,'whole_insertion_ready':False,'new_whole_impact_executed':False,'old_native_solver_reruns':0,'physical_strength_and_fracture_qualified':False,'general_3D_constitutive_equivalence_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A29'};dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'assessment':a,'results':rel(OUT/'composite_qualification_review.json'),'failed_gates_preserved':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route()})
    table='\n'.join(f"| {x['revision']} / {x['case']} | {x['maximum_residual_J']:.9g} | {'réussi' if x['pass'] else '**échoué**: '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows)
    pred='\n'.join(f"| {x['revision']} / N{x['mesh_n']} / {x['layers']}subdivisions | {x['native_final_IE_J']:.9g} | {x['ASQBI_transverse_prediction_final_J']:.9g} | {x['maximum_all_history_difference_J']:.9g} |" for x in a0['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A28 — déformations reconstruites et cohérence du cisaillement

**22 nouveaux calculs natifs complets** et lecture de six historiques A27 conservés. La formule ASQBI documentée prédit l'écart de flexion sans ajuster le matériau. Les alternatives testées ne qualifient pas la peau: flexion et cisaillement transverse restent en échec. Aucun nouveau calcul entier ou vidéo10secondes.

## 1. Faits directement observés ou transcrits

Graine1102053, aucun tirage. Plaque10×10×0,5mm, volume50mm³, masse0,0915g. Carte LAW25/4 source inchangée:rho0,00183g/mm³, E11=E22=22000MPa, nu12=0,25, E33=10000MPa, G12=G23=G31=4000MPa. Orientation90° et9subdivisions homogènes régulières. Aucun ajout de masse, RKE ou échelle temporelle. Les anciens solveurs ne sont pas relancés.

w0: sept contrôles HA8 avec /DEF_SOLID Icpre1. Le Starter lit1au défaut global mais **3dans la pièce TYPE22**; le changement n'a pas été appliqué dans la pièce. w1: quinze contrôles HSEPH TYPE22 Isolid15, mêmes matériaux et géométrie, amortissement de stabilisation demandé et lu1e−20. Tous les Starters et Engines terminent normalement sans avertissement. Des corrections de syntaxe/réservation de colonne ont précédé toute exécution et leurs versions sont conservées.

Les{a['native_field_samples']}échantillons de champs passent finitude, identités géométriques avec borne d'impression et absence de suppression. Les propriétés natives et positions de couches sont vérifiées. Préservation de{p['files']}fichiers antérieurs, {p['bytes_hashed']/1e9:.3f}Go. Le dépôt OpenRadioss n'a pas fourni son code courant via l'accès essayé (réponse404); une inspection Git restée en attente est arrêtée. Aucun code source ou logiciel de solveur n'est modifié, aucune compilation ni équivalence source/binaire annoncée.

## 2. Résultats d'un modèle officiel

La [formulation ASQBI](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_assumed_strain_rate.htm) ajoute des termes transverses avec nu/(1−nu) dans les modes de flexion. Ils évitent des verrouillages dans les éléments; ils ne sont pas une mesure de déformation physique indépendante. [TYPE22](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type22_tsh_comp_starter_r.htm) propose HA8 et HSEPH, le second avec stabilisation physique. Les [valeurs globales /DEF_SOLID](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/def_solid_starter_r.htm) peuvent être écrasées: seule la lecture effective de pièce prouve leur application. Ces définitions guident les essais; aucun dommage NIST ou historique n'est ciblé.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation historique ou analyse de vidéo. La carte élastique et le fichier A20 effectivement utilisés sont épinglés par SHA256. Ce matériau est un témoin de référence, pas une identification de rupture de Boeing réel. Inventaire A25 des24racines/144ancres conservé, sans insertion dans l'avion entier.

## 4. Hypothèses propres au modèle

Pour la flexion cylindrique en xz, la composante reconstruite est epsilon_z=−[nu/(1−nu)]epsilon_x. Le bloc constitutif TYPE22 déclaré sépare le plan de E33. Son application donne une rigidité supplémentaire E33[nu/(1−nu)]²=1111,111111MPa, soit4,734848485% de la rigidité plane23466,666667MPa. Les centres de subdivisions intègrent z²; leur déficit de second moment est1/N². Ces coefficients sont issus des entrées et de la formule publiée, sans estimation sur les valeurs natives. Les amplitudes suivent le déplacement effectivement prescrit et l'instant natif.

La référence de matrice3D couplée publiée pour LAW25 reste distincte du bloc observé dans TYPE22. Les neuf sous-couches sont une quadrature d'un milieu homogène, pas un empilement historique. La référence HSEPH utilise IE+HE, la stabilisation physique étant un terme élastique; les canaux natifs restent séparés et le bilan complet inclut tous les termes sans correction. Ici HE vaut zéro dans les valeurs examinées. Les seuils2%+1e−7J élastiques et du bilan complet,0,2% pour les invariants libres, ainsi que les seuils de masse/inertie et raffinements A26 sont conservés.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
{table}

| Historique A27 | IE finale native(J) | Prédiction ASQBI(J) | Ecart maximal sur tout l'historique(J) |
|---|---:|---:|---:|
{pred}

Les six prédictions passent le seuil initial2%+1e−7J; écart maximal d'environ7,7e−9J. Cette concordance explique une composante numérique de l'écart; les anciens critères de flexion demeurent échoués. Le changement de défaut global w0 n'est pas une perturbation effective de cette composante.

HSEPH conserve les mouvements libres, la traction et les trois modes affines normaux. La flexion demeure environ3,45% au-dessus de la référence et échoue. Les cisaillementsXZ/YZ échouent **également au bilan natif complet**: résidu maximal1,388099897e−5J. IE finale6,940505e−5J est proche du carré de Ashear5/6 multiplié par la référence G; le travail suit un facteur simple. Ce constat ne justifie aucun ajout d'énergie. Le facteur5/6 venait d'une hypothèse de peau/coque; son emploi dans une représentation volumique doit être vérifié séparément.

Le raffinement temporelY vaut{r['refinement']['actual_dt_ratio']:.9g}fois le pas initial et passe ses critères; les écarts spatiauxN6/N12 passent5%. Ces réussites ne valident pas les critères de flexion ou de cisaillement qui échouent. {a['native_energy_balances_passed']}bilans sur22passent, {a['native_individual_sets_passed']}ensembles individuels sur22passent.

## 6. Contradictions et informations manquantes

L'hypothèse d'un mécanisme numérique transverse est étayée par la formule et les six historiques, sans preuve de toute la chaîne causale A21. Le réglage Icpre global n'a pas modifié la pièce: ses résultats ne peuvent falsifier les termes ASQBI. La variante HSEPH conserve l'écart de flexion et présente un défaut énergétique transverse; elle n'est pas prête pour le montage entier. Il faut une formulation volumique sans correction de cisaillement héritée et un tenseur3D explicite, vérifiée avant transfert. Aucun matériau n'est ajusté pour réussir un dommage connu. Rupture historique, attaches, cœur, façade, gravité, intérieur porteur et fragments restent ouverts. Meilleur calcul entier A20=20ms; vidéo10secondes physiques incomplète.

{route()}
''',encoding='utf-8');HANDOFF.write_text('# Reprise AIRCRAFT-A28 → AIRCRAFT-A29\n\nRapport: '+rel(REPORT)+'\nRésultats: '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf-8');files=[q for q in OUT.rglob('*') if q.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a28*.py'))+[CFG,HANDOFF];dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)} for q in sorted(set(files))]});print({'A28_prepared':True,'failed_gates_retained':True},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();rec={'experiment_id':'WTC1-AIRCRAFT-A28','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A28',next_iteration='AIRCRAFT-A29',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a28_key_results']=rec;st['validated_artifacts'].update(aircraft_a28_report=rel(REPORT),aircraft_a28_results=rel(OUT/'composite_qualification_review.json'),aircraft_a28_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A28');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A28+AIRCRAFT-A29 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A28','route':st['current_iteration']=='AIRCRAFT-A28' and st['next_iteration']=='AIRCRAFT-A29','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A28'] and cy['pending_count']==1,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};p={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False};assert p['pass'],checks;dump(OUT/'publication_verification.json',p);print(p,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
