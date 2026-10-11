"""Seal free-interior A33 skin without turning an energy pass into full validation."""
from run_aircraft_a33 import *
from finalize_aircraft_a22 import verify_files
import json
REPORT=OUT/'rapport_aircraft_a33.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A33_HANDOFF.md'

def route():
    return ('AIRCRAFT-A34 : conserver les défauts de relaxation aux bords A33, étudier leur raffinement géométrique et l’opérateur discret avant une prise courbe ou insertion entière. '
       'La référence indépendante A32 à faces prescrites et intérieur libre passe ses contrôles; A33Z4passe l’énergie mais pas le champ intérieur. Une compilation séparée avec MUMPS est proposée dans aircraft_a33/native_build_preflight, soumise à accord explicite Jeremy pour installation/compilation; ne pas l’exécuter sans cet accord. '
       'Après accord, déclarer configuration/source/version et contrôles avant construction et nouveaux calculs; aucune compatibilité de reprise Windows/Linux présumée. '
       'Sans cet accord, les diagnostics et contrôles mécaniques du binaire actuel peuvent continuer. Aucun ajout de masse/densité, RKE inventé ou dommage connu comme cible. '
       'Capacités, décollement et rupture historiques non identifiés; LAW12reste un témoin élastique hypothétique. Meilleur entier A20=20ms; vidéo3D10secondes physiques incomplète. Publication A32+A33 après vérification; cadence suivante A34+A35.')

def prepare():
    guard();assert not REPORT.exists();p=read(OUT/'preservation_verification.json');r=read(OUT/'composite_qualification_review.json');assert p['pass'];st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A32' and cy['pending_iterations']==['AIRCRAFT-A32']
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h);rows=r['cases'];assert len(rows)==8;ex=[{'path':rel(q),**read(q)} for q in sorted(OUT.rglob('*.execution.json'))]
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads_per_solver':1,'GPU':False,'executions':ex,'execution_seconds_sum':sum(x.get('seconds',0) for x in ex),'executables':[{'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size} for q in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A33','status':'completed_free_interior_efficient_skin__edge_relaxation_failed','native_controls':8,'native_individual_sets_passed':sum(x['pass'] for x in rows),'native_energy_balances_passed':sum(x['checks']['native_full_balance'] for x in rows),'failed_controls':r['failed_controls'],'native_field_samples':r['native_field_samples'],'free_scope_pass':r['free_scope_pass'],'affine_scope_pass':r['affine_scope_pass'],'Z4_energy_gate_pass':r['Z4_energy_gate_pass'],'interior_relaxation_qualified':False,'physical_mass_g':.0915,'source_LAW12_unchanged':True,'implicit_build_proposal_prepared':True,'implicit_build_or_installation_performed':False,'whole_insertion_ready':False,'new_whole_impact_executed':False,'whole_aircraft_inputs_changed':False,'old_native_solver_reruns':0,'physical_strength_and_fracture_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A34'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'assessment':a,'results':rel(OUT/'composite_qualification_review.json'),'failed_gates_preserved':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route(),'implicit_proposal':rel(OUT/'native_build_preflight/build_proposal.json')})
    table='\n'.join(f"| {x['case']} | {x['native_IE_J']+x['native_HE_J']:.8g} | {x['independent_reference_J'] if x['independent_reference_J'] is not None else 'sans objet'} | {x['maximum_residual_J']:.8g} | {'réussi' if x['pass'] else '**échoué** : '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows)
    location=read(OUT/'interior_error_location_diagnostic.json');loc='\n'.join(f"| {x['case']} | {x['coordinate_mm']} | {x['axis']} | {x['error_mm']:.9g} |" for x in location['cases'])
    z4=read(OUT/'w1/FACE_BENDING_N24_Z4/review.json');relative=(z4['native_IE_J']+z4['native_HE_J']-z4['independent_reference_J'])/z4['independent_reference_J']
    REPORT.write_text(f'''# AIRCRAFT-A33 — peau à intérieur libre, relaxation aux bords non qualifiée

Huit nouveaux calculs natifs complets : trois ensembles individuels passent, cinq échouent, huit bilans énergétiques passent. Une peau à quatre cellules dans l’épaisseur passe la comparaison énergétique mais échoue au champ intérieur. Aucun ancien critère n’est réécrit et aucun nouvel impact entier n’est exécuté.

## 1. Faits directement observés ou transcrits

Graine 1102058, aucun tirage. Même plaque 10×10×0,5 mm, volume 50 mm³, densité 0,00183 g/mm³, masse 0,0915 g. TYPE6/Isolid24, Ismstr4, Icpre3, Iframe2, axes Y,−X,Z et carte LAW12 source inchangés. Une, deux ou quatre cellules géométriques dans l’épaisseur; maillage 12/24 dans le plan. Les flexions prescrivent uniquement les deux faces extérieures; les autres nœuds sont effectivement libres. Le contrôle affine transverse prescrit tous les nœuds et reste un témoin distinct. Aucun transfert dans les fichiers de l’avion entier.

Les 24 échantillons de champs natifs passent : identifiants, finitude, identité coordonnées−déplacements avec borne d’impression, absence de suppression. Cartes, formulations et masses vérifiées. {p['files']} anciens fichiers conservés par empreintes ({p['bytes_hashed']/1e9:.3f} Go); aucun ancien solveur relancé, aucune archive source balayée.

## 2. Résultats d’un modèle officiel

[TYPE6](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm) documente Isolid24 à stabilisation physique; cela ne qualifie pas automatiquement son champ intérieur. Le protocole de réaction hérité de A31 distingue les impulsions effectivement sorties par ce binaire du libellé force de [TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm). Pour chaque flexion, la somme des réactions brutes suit la variation de quantité de mouvement; leur interprétation en forces intégrées échoue. Pour le patch affine symétrique à quantité de mouvement nette nulle, seule la cohérence de somme et le travail aux limites sont contrôlés; aucune interprétation autonome non ambiguë n’est annoncée.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation historique ou analyse vidéo. Les sources matérielles, budgets et cartographie des 24 racines/144 ancres courbes restent ceux des sorties conservées. Aucun dégât connu, observation vidéo ou résultat NIST utilisé comme cible. Les propriétés historiques de rupture restent non identifiées.

## 4. Hypothèses propres au modèle

LAW12 est le témoin 3D élastique A29 : E=[22000,22000,10000] MPa, G=[4000,4000,4000] MPa, coefficients transverses explicites 0,25. Ses seuils géants ne sont pas une loi physique de rupture de l’avion. Rampe 0,1 ms, κ=0,001/mm et champ aux faces ux=−κxz−κ²x³/6, uy=0, uz=κx²/2, multiplié par s=3u²−2u³. Mouvements libres ΩY=10 rad/ms et translation [−200,5,2] m/s pendant 0,05 ms. Les maillages supplémentaires partagent les mêmes volumes et densités; aucune masse ou inertie compensée.

Référence indépendante fixée avant les sorties A33 : calcul conventionnel 192×192×16 A32, énergie 1,18892058968×10⁻⁵ J, contrôles de Jacobien, symétrie, équilibre, travail virtuel et énergie, raffinements XY/Z 0,65%/0,34%. Les nœuds A33 coïncident avec ceux de cette grille imbriquée; les déplacements correspondants sont lus directement, sans ajustement. Les faces physiques ont les mêmes conditions et l’intérieur est libre.

Seuils déclarés : comparaison élastique 2%+10⁻⁷ J, bilan complet 2%+10⁻⁷ J, raffinement spatial 5%, temporel 0,2%, rapport de pas <0,6, KE finale 1% de la référence+10⁻⁷ J, travail plastique <10⁻⁷ J. La tolérance du champ intérieur est 2% de la relaxation indépendante par rapport au prolongement du champ imposé aux faces, plus 2×10⁻⁶ mm. Ce contrôle distingue la petite relaxation de la courbure globale prescrite; aucun seuil élargi après les résultats.

## 5. Résultats dérivés

| Contrôle | IE+HE natif (J) | Référence au temps natif (J) | Résidu bilan maximal (J) | Ensemble original |
|---|---:|---:|---:|---|
{table}

Le témoin à une seule cellule est déclaré comme contrôle négatif séparé et échoue encore à l’énergie; son résultat A32 n’est pas remplacé. Avec deux cellules, l’énergie et le champ intérieur échouent. Avec quatre cellules, l’écart énergétique est {100*relative:.6g}%, mais l’erreur maximale du champ intérieur vaut {z4['diagnostics']['maximum_interior_displacement_error_mm']:.9g} mm pour une tolérance {z4['diagnostics']['interior_tolerance_mm']:.9g} mm. Tous les travaux aux faces, bilans et contrôles de KE finale passent, avec travail plastique nul. L’accord énergétique seul ne suffit donc pas.

| Contrôle | Coordonnée de l’erreur maximale (mm) | Composante | Erreur (mm) |
|---|---|---|---:|
{loc}

Les plus grands écarts se situent à x=5 mm, sur un bord libre dans l’épaisseur. Cette localisation est une observation du cache, pas une cause démontrée. Les maillages et opérateurs discrets peuvent encore influencer cette relaxation. Le rapport de pas demi/initial est {r['refinement']['actual_dt_ratio']:.9g}; la différence énergétique temporelle vaut {r['refinement']['elastic_energy_difference_J']:.9g} J. Les variations énergétiques XY/Z passent les seuils spatiaux, mais les critères individuels échoués restent contraignants.

Une inspection logicielle en lecture seule trouve Ubuntu 24.04.4 WSL avec CMake/GCC/Make, sans GFortran ou MPI sur PATH et sans paquet MUMPS inventorié. Les documents du miroir OpenRadioss figé au commit bad6688602d770e019b75773d2d5a48b4f9bd918 sont contrôlés par empreintes de blobs Git. Sa licence AGPL-3.0 est conservée; identité avec le binaire Windows non démontrée. La construction MUMPS documentée demande double précision et MPI. Une proposition séparée décrit outils manquants, espace, limite de calcul, empreintes et nouveaux témoins. Aucune installation, compilation, modification ou publication de binaire réalisée.

## 6. Contradictions et informations manquantes

Quatre cellules améliorent l’énergie sans satisfaire le déplacement intérieur aux bords. Deux cellules plus efficaces ne passent pas; cette piste n’est pas qualifiée pour l’impact entier. Résistance, décollement, rupture, prises courbes, façade et contacts de fragments restent ouverts. Aucun ajout RKE, densité modifiée, masse inventée ou prolongation balistique non calculée.

Le binaire actuel refuse l’implicite avec MUMPSrequired dans les sondes A31 conservées. Installer et compiler un solveur séparé nécessite une demande explicite de Jeremy selon AGENTS.md; la proposition existe, l’autorisation supplémentaire n’est pas présumée. Sa réussite ne garantirait ni l’accélération ni la qualification du modèle entier. Un nouveau binaire doit être contrôlé séparément, et aucun restart Windows n’est présumé compatible.

Meilleur impact entier A20 : 20 ms physiques. La vidéo de dix secondes physiques reste à produire; les aperçus ralentis ne remplissent pas cet objectif.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A33 → AIRCRAFT-A34\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\nProposition : '+rel(OUT/'native_build_preflight/build_proposal.json')+'\n\n'+route()+'\n',encoding='utf8')
    files=[q for q in OUT.rglob('*') if q.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a33*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a33*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)} for q in sorted(set(files))]});print({'A33_prepared':True,'interior_relaxation_qualified':False},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();rec={'experiment_id':'WTC1-AIRCRAFT-A33','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A33',next_iteration='AIRCRAFT-A34',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a33_key_results']=rec;st['validated_artifacts'].update(aircraft_a33_report=rel(REPORT),aircraft_a33_results=rel(OUT/'composite_qualification_review.json'),aircraft_a33_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A33');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A32+AIRCRAFT-A33 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A33','route':st['current_iteration']=='AIRCRAFT-A33' and st['next_iteration']=='AIRCRAFT-A34','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A32','AIRCRAFT-A33'] and cy['pending_count']==2,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    p={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False};assert p['pass'],checks;dump(OUT/'publication_verification.json',p);print({'A33_integrity_verified':True,'new_files':n,'old_files':p['old_files_verified'],'current':'AIRCRAFT-A33','next':'AIRCRAFT-A34','physical_skin_qualified':False},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
