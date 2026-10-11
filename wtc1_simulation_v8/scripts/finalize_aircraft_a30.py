"""Seal a bounded conformal-sandwich scope, retaining all failures and gaps."""
from run_aircraft_a30 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a30.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A30_HANDOFF.md'

def route():
    return ('AIRCRAFT-A31 : les champs imposés A30 et invariants libres ne qualifient pas encore le transfert par un intérieur libre. '
      'Si le périmètre A30 passe, imposer seulement les faces/prises sur le même sandwich conformal et comparer réaction, travail et déplacements internes à une référence3D indépendante hétérogène, construite à partir des tenseurs et volumes déclarés. '
      'Au minimum cisaillementsXZ/YZ et traction/pression normales, amplitudes restant élastiques et raffinements. Conserver les nouvelles hypothèses LAW12 et liaison parfaite, tous les défauts A21–A30, sans correction RKE ou de masse. '
      'Puis mapper24racines/144ancres courbes A25avec leurs orientations et budget physique réels; aucune racine plate fictive substituée. Nouveau départ entier intact après bilans, critères locaux et estimation de coût. '
      'Meilleur entier20ms; objectif vidéo3D10secondes physiques incomplet. Publication suivante après A30+A31 vérifiées, autorisation déjà donnée. Aucun dommage connu comme cible.')

def prepare():
    guard();assert not REPORT.exists();p=read(OUT/'preservation_verification.json');r=read(OUT/'sandwich_qualification_review.json');assert p['pass'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A29' and cy['pending_count']==0
    rows=r['cases'];assert len(rows)==9;ex=[{'path':rel(q),**read(q)} for q in sorted(OUT.glob('w*/*/*.execution.json'))];dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads_per_solver':1,'GPU':False,'executions':ex,'execution_seconds_sum':sum(x.get('seconds',0) for x in ex),'executables':[{'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size} for q in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A30','status':'completed_conformal_sandwich_manufactured_controls__free_interior_transmission_pending' if r['sandwich_manufactured_scope_pass'] else 'completed_conformal_sandwich_controls__gate_failed','native_controls':9,'native_individual_sets_passed':sum(x['pass'] for x in rows),'native_energy_balances_passed':sum(x['checks']['native_full_balance'] for x in rows),'failed_controls':[{'case':x['case'],'checks':[k for k,v in x['checks'].items() if not v]} for x in rows if not x['pass']],'sandwich_manufactured_scope_pass':r['sandwich_manufactured_scope_pass'],'native_field_samples':len(read(OUT/'native_fields_review.json')['samples']),'physical_mass_g':.2214,'same_source_core_LAW28':True,'explicit_LAW12_skins':True,'new_perfect_bond_hypothesis':True,'free_rotation_omega_rad_ms':1,'free_interior_transmission_qualified':False,'physical_debonding_or_fracture_qualified':False,'whole_insertion_ready':False,'new_whole_impact_executed':False,'whole_aircraft_inputs_changed':False,'old_native_solver_reruns':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A31'};dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'assessment':a,'results':rel(OUT/'sandwich_qualification_review.json'),'failed_gates_preserved':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route()})
    table='\n'.join(f"| {x['case']} | {x['maximum_residual_J']:.9g} | {'réussi' if x['pass'] else '**échoué**: '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows);scope='réussi' if r['sandwich_manufactured_scope_pass'] else 'échoué: '+', '.join(k for k,v in r['checks'].items() if not v)
    REPORT.write_text(f'''# AIRCRAFT-A30 — sandwich volumique conformal

**Neuf nouveaux calculs natifs complets** sur deux peaux et leur cœur. Périmètre des invariants libres et champs élastiques imposés: {scope}. La transmission dans un intérieur libre, les attaches courbes et l'impact entier restent à vérifier.

## 1. Faits directement observés ou transcrits

Graine1102055, aucun tirage. Géométrie10×10mm; peau inférieurez=−4,5..−4mm, cœur−4..4mm, peau supérieure4..4,5mm. Volumes50+800+50mm³, densités0,00183et0,000048g/mm³, masse0,2214g. Les maillages6/12dans le plan comprennent4éléments par peau et12dans le cœur. Les facesz±4partagent les mêmes nœuds; aucune coordonnée dupliquée, masse d'interface, rotation indépendante ou déport rigide ajouté. Les anciennes entrées Spot5et l'avion entier restent conservés.

Les peaux utilisent la branche LAW12/TYPE6 Isolid18A29, avec axesY,−X,Z. Le cœur garde sa carte LAW28/28source et ses six courbes plateau; TYPE6 Isolid14, axesXYZ. Avant chaque Engine, le Starter confirme repères et formulations effectifs. Les{a['native_field_samples']}échantillons natifs contrôlent finitude, identité géométrique avec borne d'impression et absence de suppression. Les cartes effectives et les faces partagées sont vérifiées séparément. Conservation de{p['files']}fichiers antérieurs, {p['bytes_hashed']/1e9:.3f}Go. Aucun ancien calcul relancé. Publication A28+A29effectivement confirmée avant cette déclaration.

## 2. Résultats d'un modèle officiel

[LAW12](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law12_3d_comp_starter_r.htm) définit l'orthotropie3D des peaux; sa conformité numérique locale a été vérifiée dans A29. [LAW28](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law28_honeycomb_starter_r.htm) décrit un cœur orthotrope à réponses directionnelles. Les contrôles de matériau A20en cache sont réutilisés, avec leurs limites et leurs anciens critères échoués. Aucune forme de dommage NIST ou connue n'est utilisée comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de vidéo ou affirmation historique. Les propriétés de référence du cœur HRH10et leurs paramètres non mesurés restent celles documentées dans A20. Aucune identification du matériau d'AA11ou de son décollement n'est annoncée. L'inventaire A25des24racines/144ancres est conservé; aucune racine fictive n'est insérée.

## 4. Hypothèses propres au modèle

La liaison peau/cœur par faces communes est une **nouvelle hypothèse de collage parfait**, distincte des anciennes interfaces Spot5. Elle ne donne pas de résistance de décollement. Les modules,densitéetnu12source des peaux sont conservés; nu23=nu31=0,25restent les hypothèses transverses explicites d'A29. Les seuils géants de LAW12maintiennent les témoins élastiques, sans capacité historique de rupture. Le cœur garde E=[1,1,138]MPa et G=[0,5,24,41]MPa; ses faibles propriétés dans le plan et ses seuils de rupture restent hypothétiques.

La rotation libre commence avec omega1rad/ms sur0,05ms: amplitude déclarée pour garder le cœur faible dans un régime élastique, différente des témoins de peau A29à10rad/ms. La translation−200,5,2m/s teste l'invariance. Les champs élastiques prescrivent tous les nœuds sur0,1ms: extensionepsilon_x=0,001, epsilon_y=epsilon_z=0; flexion cylindriqueκ=0,0001/mm, extension transverse contrainte. Cette courbure fixe une déformation de peau maximale4,5e−4, choisie avant calcul pour rester dans le même ordre élastique. Ces champs ne sont pas un test d'intérieur libre ou de flexion plane libre.

Référence d'extension:0,5epsilon_x²ΣCxx·volume. Référence de flexion:0,5κ²·aire·Σ[Cxx·intégrale(z²dz)]. Cdes peaux provient de la compliance A29, Cdu cœur est diagonal. Chaque région garde son volume,densitéetposition réels. Le tenseur d'inertie continu est la somme analytique de ses prismes avec déport physique; masse nodale issue des volumes, tensor discret séparé. Aucun module n'est ajusté à une sortie. Les seuils énergétiques/élastiques2%+1e−7J, invariants libres0,2%, inertie continue2%, raffinement spatial5% et rapport de pas<0,6sont conservés.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
{table}

{a['native_individual_sets_passed']}ensembles individuels sur9et{a['native_energy_balances_passed']}bilans natifs sur9passent. Les RKE natives restent séparées dans tous les bilans; aucun terme inventé. Pas médian demi-pas/initial={r['refinement']['actual_dt_ratio']:.9g}; différence de moment cinétique={r['refinement']['physical_L_difference_kg_m2_s']:.9g}kg·m²/s, énergie={r['refinement']['energy_difference_J']:.9g}J. Les références et écarts6/12sont conservés dans sandwich_qualification_review.json. Le travail plastique natif par pièce est enregistré comme diagnostic, sans seuil ajouté après exécution.

## 6. Contradictions et informations manquantes

Les essais vérifient les invariants physiques du montage libre et sa réponse à des champs imposés. Ils ne démontrent pas le transfert des charges par des nœuds intérieurs libres: cette question est l'étape suivante. La liaison parfaite ignore le décollement; coefficients transverses, faible plan du cœur, rupture et assemblage réel restent à identifier. La réussite du témoin n'autorise pas encore un remplacement dans l'avion entier. Les échecs antérieurs restent conservés. Gravité, façade, intérieur porteur et contacts de fragments restent ouverts. Meilleur entierA20=20ms, vidéo10secondes physiques incomplète.

{route()}
''',encoding='utf-8');HANDOFF.write_text('# Reprise AIRCRAFT-A30 → AIRCRAFT-A31\n\nRapport: '+rel(REPORT)+'\nRésultats: '+rel(OUT/'sandwich_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf-8');files=[q for q in OUT.rglob('*') if q.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a30*.py'))+[CFG,HANDOFF];dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)} for q in sorted(set(files))]});print({'A30_prepared':True,'limited_scope_pass':r['sandwich_manufactured_scope_pass']},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json');reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();rec={'experiment_id':'WTC1-AIRCRAFT-A30','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'sandwich_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A30',next_iteration='AIRCRAFT-A31',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a30_key_results']=rec;st['validated_artifacts'].update(aircraft_a30_report=rel(REPORT),aircraft_a30_results=rel(OUT/'sandwich_qualification_review.json'),aircraft_a30_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A30');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A30+AIRCRAFT-A31 verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_preservation':read(OUT/'preservation_verification.json')['pass'],'old_results':all(st[k]==old[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A30','route':st['current_iteration']=='AIRCRAFT-A30' and st['next_iteration']=='AIRCRAFT-A31','objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','pending':cy['pending_iterations']==['AIRCRAFT-A30'] and cy['pending_count']==1,'publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};p={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False};assert p['pass'],checks;dump(OUT/'publication_verification.json',p);print(p,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
