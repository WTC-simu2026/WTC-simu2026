"""Seal face-loaded free-interior controls and preserve every failed attempt."""
from run_aircraft_a31 import *
from finalize_aircraft_a22 import verify_files
import json
REPORT=OUT/'rapport_aircraft_a31.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A31_HANDOFF.md'

def route():
    ok=read(OUT/'sandwich_qualification_review.json')['fine_face_loaded_scope_pass']
    return ('AIRCRAFT-A32 : '+('le périmètre élastique du sandwich à intérieur libre passe; préparer les24racines/144ancres courbes réellement inventoriées dans A25, leurs repères, prises et budgets physiques avant un contrôle natif représentatif. ' if ok else 'conserver les critères A31échoués et traiter leur cause avant l\'insertion dans l\'avion. ')+
      'Le coût de10secondes doit être évalué sur la discrétisation réelle; tester une formulation efficace à masse physique inchangée avec référence indépendante si nécessaire. Le binaire installé échoue aux deux sondes implicites avec MUMPSrequired; aucune installation ni modification du solveur effectuée. '
      'Les cartes LAW12, coefficients transverses et collage parfait restent des hypothèses explicites; résistances, décollement et rupture historiques non identifiés. Aucun faux ajout de RKE, correction de densité ou ajustement aux dégâts connus. '
      'Nouveau départ entier après critères locaux, bilans et estimation du coût. Meilleur entierA20=20ms; objectif vidéo3D10secondes physiques incomplet. Publication A30+A31 après vérification, déjà autorisée; cadence suivante A32+A33.')

def prepare():
    guard();assert not REPORT.exists();p=read(OUT/'preservation_verification.json');r=read(OUT/'sandwich_qualification_review.json');assert p['pass'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
    st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A30' and cy['pending_iterations']==['AIRCRAFT-A30']
    rows=r['cases'];assert len(rows)==9;support=read(OUT/'cached_support_assessment.json');ex=[{'path':rel(q),**read(q)} for q in sorted(OUT.rglob('*.execution.json'))]
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads_per_solver':1,'GPU':False,'executions':ex,'execution_seconds_sum':sum(x.get('seconds',0) for x in ex),'executables':[{'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size} for q in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A31','status':'completed_face_loaded_free_interior_sandwich__curved_roots_pending' if r['fine_face_loaded_scope_pass'] else 'completed_face_loaded_sandwich__gate_failed','native_controls':9,'native_individual_sets_passed':sum(x['pass'] for x in rows),'native_energy_balances_passed':sum(x['checks']['native_full_balance'] for x in rows),'failed_controls':[{'case':x['case'],'checks':[k for k,v in x['checks'].items() if not v]} for x in rows if not x['pass']],'fine_face_loaded_scope_pass':r['fine_face_loaded_scope_pass'],'native_field_samples':len(read(OUT/'native_fields_review.json')['samples']),'physical_mass_g':.2214,'same_source_core_LAW28':True,'explicit_LAW12_skins':True,'new_perfect_bond_hypothesis':True,'free_interior_transmission_qualified_in_declared_elastic_scope':r['fine_face_loaded_scope_pass'],'implicit_capability_attempts':4,'existing_binary_implicit_route_available':False,'physical_debonding_or_fracture_qualified':False,'whole_insertion_ready':False,'new_whole_impact_executed':False,'whole_aircraft_inputs_changed':False,'old_native_solver_reruns':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A32'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'assessment':a,'results':rel(OUT/'sandwich_qualification_review.json'),'capability':rel(OUT/'implicit_binary_capability_assessment.json'),'failed_gates_preserved':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route(),'cost':read(OUT/'whole_cost_observation.json')})
    table='\n'.join(f"| {x['case']} | {x['maximum_residual_J']:.8g} | {x['maximum_late_static_force_error_N']:.8g} | {x['maximum_interior_displacement_error_mm']:.8g} | {'réussi' if x['pass'] else '**échoué**: '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows)
    spatial='\n'.join(f"| {x['mode']} | {100*x['native_IE_change_fraction']:.6g}% | {100*x['independent_static_IE_change_fraction']:.6g}% | {'réussi' if x['pass'] else '**échoué**'} |" for x in r['mesh'])
    scope='réussi' if r['fine_face_loaded_scope_pass'] else '**échoué**: '+', '.join(k for k,v in r['checks'].items() if not v)
    roots=read(OUT/'curved_root_surface_mapping.json');assert roots['pass'];vol=read(OUT/'whole_volume_geometry_preparation.json');assert vol['geometry_budget_scope_pass']
    REPORT.write_text(f'''# AIRCRAFT-A31 — transmission dans un sandwich à intérieur libre

Neuf nouveaux calculs natifs complets. Périmètre élastique aux faces, intérieur libre et raffinements: {scope}. Les essais implicites séparés échouent sur le binaire installé. L'impact entier et sa vidéo de dix secondes restent à réaliser.

## 1. Faits directement observés ou transcrits

Graine1102056, aucun tirage. Géométrie et matériaux A30 conservés:10×10mm, peaux0,5mm, cœur8mm; volumes50+800+50mm³, densités0,00183et0,000048g/mm³, masse0,2214g. Maillages6/12dans le plan, quatre éléments dans chaque peau et douze dans le cœur. Faces internes partagées par identité des nœuds, sans interface massive ou déport rigide. Seules les faces extérieuresz=−4,5et4,5mm contraignentXYZ; tous les autres nœuds restent libres. Le contrôle des cartes confirme LAW12et LAW28, formulations et repères natifs avant Engine. {a['native_field_samples']}échantillons natifs: finitude, coordonnées/déplacements avec borne d'impression et absence de suppression.

Conservation vérifiée de{p['files']}fichiers antérieurs ({p['bytes_hashed']/1e9:.3f}Go). Aucun ancien calcul relancé. Une erreur de métadonnées avant Starter, puis une erreur de sélection des titres de pièces après le premier calcul, sont conservées avec leurs versions originales. Les reprises complètent les métadonnées puis relisent le calcul déjà terminé; ses entrées et sorties natives ne sont pas réécrites.

## 2. Résultats d'un modèle officiel

[TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm) décrit REAC comme des forces. Dans ce binaire et ces calculs, les sorties brutes vérifient au contraire l'impulsion: sommeQ−Qinitial=variation de quantité de mouvement. L'interprétation alternative par intégration temporelle échoue. Les deux comparaisons et seuils déclarés sont gardés; la réaction est alors dQ/dt, avec retrait explicite de l'inertie des seuls nœuds prescrits pour la comparaison statique. Le travail nodal est comparé au travail externe natif. Le moment cinétique issu des impulsions est un diagnostic séparé, sans critère ajouté après calcul.

La documentation [Newmark](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dyna_2_engine_r.htm) et [solveur implicite](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_solver_engine_r.htm) définit les options des sondes séparées. Leur présence dans la documentation n'établit pas leur disponibilité dans l'exécutable: les nouvelles tentatives PCGet MUMPS échouent effectivement.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse vidéo ou affirmation historique. Sources cœur/peaux réutilisées avec les lacunes A20/A29. Aucune identification d'un matériau, assemblage ou décollement historique d'AA11annoncée. Les24racines/144ancres courbes A25sont mappées sur les faces physiques candidates: épaisseurs2,54mm du corps et0,5mm des peaux, points proches, coordonnées barycentriques et repères orthonormés directs. Les distances minimales sont{roots['gap_range_mm'][0]:.6g}..{roots['gap_range_mm'][1]:.6g}mm. Tous les candidats sont gardés. Cette sélection géométrique ne définit ni empreinte, ni volume, ni masse d'attache; le budget de la prise plate n'est pas reporté. Aucun dommage connu ou résultat NIST comme cible.

Une préparation en cache transforme les1296quads de peau des216facettes réelles en volumes0,5mm, avec faces du cœur intactes et repères matériauxW,−L,nissus de l'orientation source90°. Masse de peau{vol['physical_skin_mass_g']/1000:.9g}kg, identique au budget source à1e−8relatif; tous les jacobiens de Gauss positifs, erreur de plan moyen maximal{vol['worst_source_midplane_identity_mm']:.9g}mm. Centre de masse et tenseurs physiques sont archivés. Les IDs de facettes ne sont pas contigus: une erreur de recherche par position, sans exécution native, est conservée et reprise par dictionnaire d'IDoriginal. Aucun ancien fichier modifié. Ce maillage candidat n'est pas inséré dans l'avion ni qualifié mécaniquement par cette préparation géométrique.

## 4. Hypothèses propres au modèle

LAW12des peaux garde E=[22000,22000,10000]MPa, G=[4000,4000,4000]MPa; nu23=nu31=0,25restent des hypothèses transverses explicites. Les seuils géants maintiennent ce témoin élastique, sans qualifier une rupture historique. Le cœur LAW28source garde E=[1,1,138]et G=[0,5,24,41]MPa, plateaux et seuils précédents; paramètres dans le plan et rupture encore non mesurés. Le collage parfait est une hypothèse A30distincte des anciennes interfaces Spot5.

Rampe0,5ms, déplacement0,009mm, s=3u²−2u³; face inférieure fixe, supérieure mobile dans une seule direction. CisaillementsXZ/YZ, traction et compression normales. Durée et amplitude déclarées avant résultats pour un régime élastique et une faible énergie cinétique finale, adequation contrôlée. Référence3D indépendante hétérogène: hexaèdres8nœuds,2×2×2Gauss, tenseurs des sources, géométrie et conditions aux faces identiques. Matrice symétrique, jacobiens positifs, équilibre intérieur, travail virtuel et somme des énergies par pièce contrôlés. Résolution CG préconditionnée, tolérance1e−10relative+1e−11N, sans opérateur natif ou ajustement de module.

Critères avant exécution: bilans, énergie et réactions2%avec bornes absolues; déplacement intérieur2%de l'amplitude+2e−6mm, KEfinale1%de la référence+1e−7J; travail plastique<1e−7J; convergence spatiale5%, temporelle0,2%, rapport de pas<0,6. Tous les canaux natifs, dont RKEet HE, restent séparés dans le bilan complet. Aucun terme artificiel ajouté.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique max(J) | Erreur réaction tardive max(N) | Erreur déplacement intérieur max(mm) | Résultat |
|---|---:|---:|---:|---|
{table}

{a['native_individual_sets_passed']}/9ensembles individuels et{a['native_energy_balances_passed']}/9bilans complets passent. Les critères originaux des essais grossiers restent gardés séparément. Qualification fine: {scope}.

| Mode | Variation énergétique native6→12 | Variation référence indépendante6→12 | Raffinement |
|---|---:|---:|---|
{spatial}

Rapport de pas demi/initial={r['refinement']['actual_dt_ratio']:.9g}; écart maximal d'énergie={r['refinement']['IE_difference_J']:.9g}J et réaction={r['refinement']['reaction_difference_N']:.9g}N. Valeurs, historiques SI et paramètres effectivement lus sont archivés.

Un addendum relit les27canaux plastiques A30en cache: maximum du travail plastique total={support['A30_maximum_sum_PW_J']:.9g}J. Le diagnostic initial A30avait des dictionnaires vides parce qu'il cherchait le nom de groupe au lieu des titres réels; sa qualification n'avait pas de critère plastique. L'addendum fournit l'observation manquante sans modifier le rapport ou les fichiers A30scellés.

Quatre sondes implicites nouvelles, sur un cube métallique1mm³ à masse0,00278g et intérieur libre: les deux premières s'arrêtent lors de la lecture d'un enregistrement NONLIN de80caractères. Le code amont conservé montre une chaîne TITLEde72caractères, sans preuve d'identité avec ce binaire. La branche distincte à nombres identiques en format compact franchit la lecture, puis les deux modes terminent avec **MUMPSrequired** (8684et2404). Aucun calcul implicite n'est réussi. Aucun composant installé ou exécutable modifié.

## 6. Contradictions et informations manquantes

La transmission élastique dans ce témoin, même réussie, ne qualifie ni les prises courbes réelles, ni la plasticité du nez à grande vitesse, ni le décollement ou la rupture. Les contradictions de libellé REACet les erreurs de préparation/lecture restent documentées. Échecs A21–A30conservés. Façade, gravité, intérieur porteur, contacts de fragments et propriétés historiques restent ouverts.

Le calcul entier A20de20ms a coûté1191,42s; extrapolation linéaire indicative10s≈6,90jours, sans garantie pour une autre discrétisation ou un contact tardif. La voie implicite du binaire actuel n'est pas disponible; une formulation ou résolution spatiale efficace doit conserver masse, tenseur physique et réponse mécanique vérifiée. Meilleur entier20ms, objectif vidéo3D10secondes physiques incomplet.

{route()}
''',encoding='utf-8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A31 → AIRCRAFT-A32\n\nRapport: '+rel(REPORT)+'\nRésultats: '+rel(OUT/'sandwich_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf-8')
    files=[q for q in OUT.rglob('*') if q.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a31*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a31*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)} for q in sorted(set(files))]});print({'A31_prepared':True,'fine_scope_pass':r['fine_face_loaded_scope_pass']},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();rec={'experiment_id':'WTC1-AIRCRAFT-A31','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'sandwich_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A31',next_iteration='AIRCRAFT-A32',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a31_key_results']=rec;st['validated_artifacts'].update(aircraft_a31_report=rel(REPORT),aircraft_a31_results=rel(OUT/'sandwich_qualification_review.json'),aircraft_a31_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A31');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A30+AIRCRAFT-A31 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A31','route':st['current_iteration']=='AIRCRAFT-A31' and st['next_iteration']=='AIRCRAFT-A32','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A30','AIRCRAFT-A31'] and cy['pending_count']==2,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    p={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False};assert p['pass'],checks;dump(OUT/'publication_verification.json',p);print(p,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
