"""Seal A32 without concealing its four original bending failures."""
from run_aircraft_a32 import *
from finalize_aircraft_a22 import verify_files
import json
REPORT=OUT/'rapport_aircraft_a32.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A32_HANDOFF.md'

def route():
    return ('AIRCRAFT-A33 : tester une peau TYPE6/Isolid24 à plusieurs cellules physiques dans l’épaisseur, faces seules chargées et intérieur libre, avec la référence continuum indépendante A32 désormais raffinée. '
       'Déclarer avant les sorties les contrôles de flexion, inertie libre, affine transverse et raffinements; conserver les quatre échecs A32. Puis tester la transmission du sandwich et les prises courbes avant insertion entière. '
       'Aucun ajout de masse, changement de densité ou terme RKE artificiel. LAW12 et ses coefficients transverses restent des hypothèses élastiques; résistance, décollement et rupture historiques non identifiés. '
       'L’implicite du binaire installé réclame MUMPS; aucune installation ou modification de solveur autorisée ou effectuée. Meilleur impact entier A20=20ms, objectif vidéo3D10secondes physiques incomplet. Publication suivante A32+A33 après vérification.')

def prepare():
    guard();assert not REPORT.exists();p=read(OUT/'preservation_verification.json');r=read(OUT/'composite_qualification_review.json');d=read(OUT/'surface_bending_extended_diagnostic.json');assert p['pass'] and all(d['reference_refinement_checks'].values())
    st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A31' and cy['pending_count']==0
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h);rows=r['cases'];assert len(rows)==30
    ex=[{'path':rel(q),**read(q)} for q in sorted(OUT.rglob('*.execution.json'))];dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads_per_solver':1,'GPU':False,'executions':ex,'execution_seconds_sum':sum(x.get('seconds',0) for x in ex),'executables':[{'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size} for q in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A32','status':'completed_efficient_volume_controls__bending_reference_and_native_equivalence_unqualified','native_controls':30,'native_individual_sets_passed':sum(x['pass'] for x in rows),'native_energy_balances_passed':sum(x['checks']['native_full_balance'] for x in rows),'failed_controls':r['failed_controls'],'native_field_samples':len(read(OUT/'native_fields_review.json')['samples']),'free_scope_pass':r['free_scope_pass'],'affine_scope_pass':r['affine_scope_pass'],'membrane_scope_pass':r['membrane_scope_pass'],'bending_scope_pass':False,'surface_reference_refinement_pass':True,'original_reference_failures_retained':True,'physical_mass_g':.0915,'source_LAW12_unchanged':True,'whole_insertion_ready':False,'new_whole_impact_executed':False,'whole_aircraft_inputs_changed':False,'old_native_solver_reruns':0,'physical_strength_and_fracture_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A33'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'assessment':a,'results':rel(OUT/'composite_qualification_review.json'),'independent_diagnostic':rel(OUT/'surface_bending_extended_diagnostic.json'),'failed_gates_preserved':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route(),'whole_cost_not_estimated_from_coupon_step_alone':True})
    table='\n'.join(f"| {x['revision']} | {x['case']} | {x['maximum_residual_J']:.8g} | {'réussi' if x['pass'] else '**échoué** : '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows)
    comparisons='\n'.join(f"| {x['branch']} | {x['n']} | {x['native_elastic_J']:.9g} | {x['independent_surface_prediction_J']:.9g} | {100*x['difference_fraction']:.6g}% |" for x in d['native_comparisons'])
    REPORT.write_text(f'''# AIRCRAFT-A32 — formulations volumiques efficaces, flexion non qualifiée

Trente nouveaux calculs natifs complets, vingt-six ensembles individuels réussis, quatre flexions échouées et trente bilans énergétiques réussis. Les quatre échecs originaux restent inchangés. Le diagnostic indépendant révèle une référence initiale incompatible avec une relaxation transverse admissible, mais ne démontre pas l’équivalence des formulations natives à un continuum à intérieur libre. L’objectif de dix secondes physiques reste incomplet.

## 1. Faits directement observés ou transcrits

Graine 1102057, aucun tirage. Plaque 10×10×0,5 mm, volume 50 mm³, densité 0,00183 g/mm³, masse 0,0915 g. Une cellule géométrique dans l’épaisseur et maillages 6/12 dans le plan. w0 emploie TYPE21/HSEPH15, neuf points dans l’épaisseur; w1 TYPE6/HEPH24. Les deux conservent LAW12, ses constantes, ses axes Y,−X,Z et le budget physique. Aucun ADMAS, aucun RKE ajouté ou compensé. Les cartes et paramètres sont contrôlés dans les sorties Starter réelles avant Engine.

{a['native_field_samples']} échantillons natifs passent les contrôles d’identifiants, finitude, coordonnées−déplacements avec borne d’impression et absence d’élément supprimé. Les raffinements temporels et spatiaux passent dans leur périmètre; une convergence entre deux calculs ne remplace pas l’accord avec une référence indépendante. Conservation vérifiée de {p['files']} fichiers antérieurs ({p['bytes_hashed']/1e9:.3f} Go), sans nouveau balayage des archives ni ancien solveur relancé.

La première lecture w0 s’est arrêtée avant Engine parce que le lecteur attendait le tableau TYPE6 à neuf colonnes. TYPE21 imprime cinq colonnes Isolid/Ismstr/Icpre/NPT/ICONTROL, valeurs 15/4/3/9/0. La version erronée et l’échec sont conservés. La reprise corrige seulement cette lecture, utilise les mêmes entrées et achève les calculs w0 encore non exécutés, sans répéter w1. NPT n’est pas Iframe. Le résumé après reprise est l’autorité; l’ancien résumé reste une trace historique.

## 2. Résultats d’un modèle officiel

La documentation primaire [TYPE21](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type21_tsh_orth_starter_r.htm) décrit HSEPH15 et les points dans l’épaisseur; [TYPE6](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm) décrit HEPH24 à stabilisation physique. Ces descriptions ne prouvent pas leur équivalence à une discrétisation conventionnelle pour les conditions imposées ici. Aucun résultat NIST ni dégât observé n’entre dans la référence ou les seuils.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse vidéo ou affirmation historique. Sources matérielles et budgets hérités de A20/A29, géométrie des 24 racines et 144 ancres conservée dans A31. Aucun assemblage AA11 réel n’est identifié par ces plaques. Les inventaires et sources sont réutilisés en lecture seule.

## 4. Hypothèses propres au modèle

LAW12 reste un témoin élastique explicite : E=[22000,22000,10000] MPa, G=[4000,4000,4000] MPa, coefficients transverses 0,25. Ses seuils géants ne constituent pas une résistance physique ou une loi de rupture historique. Rotation libre Ω=10 rad/ms, translation [−200,5,2] m/s; durée 0,05 ms. Champs affines et membrane/bending : rampe s=3u²−2u³ sur 0,1 ms. Les déplacements des nœuds de flexion sont ux=−κxz−κ²x³/6, uy=0, uz=κx²/2, κ=0,001/mm. Avec une seule cellule dans l’épaisseur, tous les nœuds appartiennent aux faces externes; leur contrainte n’impose pas nécessairement εzz en chaque point intérieur d’une formulation enrichie.

Les seuils originaux sont conservés : énergie élastique 2%+10⁻⁷ J, bilan complet 2%+10⁻⁷ J, raffinements spatial 5% et temporel 0,2%, rapport de pas réduit <0,6. IE et HE restent séparés dans le bilan; leur somme est la comparaison élastique déclarée. Aucun terme énergétique inventé.

Après les résultats originaux, un diagnostic séparé prescrit les deux faces physiques sur un continuum 3D conventionnel, avec tous les nœuds intérieurs libres. Le champ admissible uz=κx²/2+(Czx/Czz)κ(z²−t²/4)/2 conserve uz aux deux faces mais autorise εzz=(Czx/Czz)κz et σzz=0. Il démontre une possibilité mathématique, sans identifier l’opérateur interne natif. La référence analytique condensée vaut 1,22222222×10⁻⁵ J, contre 1,33490023×10⁻⁵ J pour Cxx plein, à amplitude finale de premier ordre. Les bords libres et la correction du second ordre sont traités par la référence 3D indépendante, sans ajustement de module.

Le sixième calcul indépendant initial s’est arrêté au travail virtuel. Les cinq références acceptées sont conservées. Une déclaration distincte resserre uniquement la résolution CG de 10⁻¹⁰ relatif+10⁻¹¹ N à 10⁻¹³ relatif+10⁻¹⁴ N, sans modifier les contrôles de symétrie, équilibre, travail virtuel ou somme des énergies. Le raffinement XY 48→96 échoue au seuil diagnostic 2% (2,442014%). Une extension séparée 192×192×8/16 est déclarée avant ses résultats; aucun ancien critère n’est remplacé rétrospectivement.

## 5. Résultats dérivés

| Branche | Contrôle | Résidu énergétique maximal (J) | Ensemble original |
|---|---|---:|---|
{table}

La référence exacte aux faces atteint 1,18892058968×10⁻⁵ J avec 192×192×16 éléments. Variation XY 96→192 à Z8 : {100*d['XY_96_to_192_fraction']:.6g}%; variation Z8→16 à XY192 : {100*d['Z_8_to_16_fraction']:.6g}%. Les deux critères diagnostics 2% passent, avec les contrôles indépendants inchangés. Les références grossières étaient sensibles au cisaillement induit par leur interpolation du déplacement quadratique; raffiner uniquement Z ne suffisait pas.

| Branche | Maillage XY natif | IE+HE natif (J) | Référence raffinée au temps natif (J) | Écart diagnostic |
|---|---:|---:|---:|---:|
{comparisons}

Ces écarts restent un diagnostic après exécution. Les quatre échecs à la référence Cxx originale sont conservés et aucune qualification de flexion n’est accordée. Le fait que les deux formulations donnent presque la même énergie ne prouve pas leur équivalence au continuum à intérieur libre. Les pas natifs d’environ 4,79×10⁻⁵ ms sont environ quatre fois ceux du témoin A31 fin; cela ne permet pas d’estimer directement le coût d’un avion entier avec contacts.

## 6. Contradictions et informations manquantes

La référence Cxx supposait une contrainte transverse point par point absente des conditions nodales réellement imposées à une peau d’une cellule. Sa correction analytique ne ferme cependant pas l’écart avec le continuum à bords et intérieur libres. La prochaine étape doit permettre ces degrés de liberté physiques et contrôler leur effet avant une insertion entière. Champs de contraintes moyens aux points natifs archivés, mais opérateurs de déformation enrichie non directement observés.

Masse, matériaux, capacités des prises courbes, plasticité, décollement, rupture, façade et contacts de fragments restent à traiter dans leurs périmètres. Les seuils géants LAW12 ne sont pas transférables comme résistance physique. Le binaire implicite installé échoue avec MUMPSrequired; aucun logiciel installé, compilé ou modifié. A20 reste le meilleur impact entier à 20 ms, et son coût ne garantit pas celui de dix secondes. Aucune prolongation balistique ou animation inventée ne remplace les états calculés.

{route()}
''',encoding='utf-8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A32 → AIRCRAFT-A33\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\nDiagnostic : '+rel(OUT/'surface_bending_extended_diagnostic.json')+'\n\n'+route()+'\n',encoding='utf-8')
    files=[q for q in OUT.rglob('*') if q.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a32*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a32*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)} for q in sorted(set(files))]});print({'A32_prepared':True,'bending_qualified':False},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();rec={'experiment_id':'WTC1-AIRCRAFT-A32','registered_at':t,'configuration':rel(CFG),'configurations':[rel(q) for q in sorted((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a32*.json'))],'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A32',next_iteration='AIRCRAFT-A33',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a32_key_results']=rec;st['validated_artifacts'].update(aircraft_a32_report=rel(REPORT),aircraft_a32_results=rel(OUT/'composite_qualification_review.json'),aircraft_a32_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A32');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A32+AIRCRAFT-A33 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A32','route':st['current_iteration']=='AIRCRAFT-A32' and st['next_iteration']=='AIRCRAFT-A33','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A32'] and cy['pending_count']==1,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    p={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False};assert p['pass'],checks;dump(OUT/'publication_verification.json',p);print({'A32_integrity_verified':True,'new_files':n,'old_files':p['old_files_verified'],'current':'AIRCRAFT-A32','next':'AIRCRAFT-A33','physical_bending_qualified':False},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
