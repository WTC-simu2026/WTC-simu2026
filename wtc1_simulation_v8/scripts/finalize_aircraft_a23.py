"""Seal solid mass/inertia and actual skin coupling controls, preserving all failures."""
from run_aircraft_a23 import *
from finalize_aircraft_a22 import verify_files
REPORT=OUT/'rapport_aircraft_a23.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A23_HANDOFF.md'

def route():
    return ('AIRCRAFT-A24 : reprendre coupling_summary.json, inertia_channels_w1.json et paired_w1_cached_audit.json, sans relancer A20–A23. '
      'Le solide HA8 conserve la masse et le tenseur physique en libre sur le maillage12³; les tractions N4/N8 correspondent à une rigidité3D indépendante. '
      'Le montage aux peaux Spot5 Iproj2 conserve les26bilans mais son énergie cinétique globale ajoutée échoue surXYZ, même en rotation lente10ms; le canal PART du solide reste correct. '
      'Ne pas transférer ce connecteur à l’avion entier, ni reconstruire une RKE ou compenser la masse. Tester une transmission sans condensation de masse, par maillage conforme ou attache de pénalité contrôlée, en gardant le cœur/Spot5 A20 intact. '
      'Si une formulation de pénalité est testée, déclarer sa rigidité et sa viscosité, inclure toutes ses énergies natives, contrôler glissement, bilan, inertie, dynamique libre et sensibilité au pas. La documentation Spot25 la déconseille: résultat à vérifier, pas choix validé. '
      'Après réussite des témoins, vérifier la géométrie réelle inclinée, les14? non:144points de peau des24racines, les capacités/budgets et la dynamique libre avant départ entier intact. Les dimensions4×1×0,5mm, masse0,00556g et capacité162N sont celles d’un prototype, pas une attache AA11 identifiée; la masse A22 de0,334g ne s’applique pas au nouveau solide. '
      'Les matériaux A21, la gravité, l’intérieur porteur et les contacts de fragments restent ouverts. Les courbes acier A22 et la striction ne sont pas des lois de rupture validées. Aucun dommage connu comme cible. '
      'Objectif10secondes physiques3D incomplet; dernier aperçu entier A20 de20ms. Publication A22+A23 autorisée par la cadence après intégrité vérifiée.').replace('les14? non:144points','les144points')

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists();p=read(OUT/'preservation_verification.json');assert p['pass'];precision=read(OUT/'native_reader_precision_addendum.json');assert precision['pass'];r=read(OUT/'coupling_summary.json');pairs=read(OUT/'paired_w1_cached_audit.json');channels=read(OUT/'inertia_channels_w1.json')
    rows=[]
    for revision,cfg in [('w0',CFG),('w1',ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json')]:
        c=read(cfg)
        for cid in c['cases']['primitive']+c['cases']['paired']:rows.append({'revision':revision,**read(OUT/revision/cid/'review.json')})
    assert len(rows)==26 and all(x['checks']['native_energy_balance'] for x in rows)
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
    executions=[{'path':rel(x),**read(x)} for x in OUT.glob('w*/*/*.execution.json')]
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss2026 native double precision win64','runtime_release_path':rel(RUNTIME),'CPU_threads':1,'GPU':False,'execution_seconds_sum':sum(x['seconds'] for x in executions),'executions':executions,
       'executables':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    failed=[{'revision':x['revision'],'case':x['case'],'checks':[k for k,v in x['checks'].items() if not v]} for x in rows if not x['pass']]
    a={'created_utc':now(),'iteration':'AIRCRAFT-A23','status':'completed_solid_and_skin_coupling_controls__global_added_inertia_failed',
       'native_controls':26,'native_case_gates_passed':sum(x['pass'] for x in rows),'native_energy_balances_passed':26,'failed_controls':failed,
       'paired_added_KE_all_axes_pass':False,'native_fields_bounded_precision_samples':78,'primitive_free_physical_tensor_pass':True,
       'corrected_elastic_extension_pass':True,'new_whole_impact_executed':False,'previous_A21_local_energy_failure_preserved':True,
       'physical_strength_and_fracture_qualified':False,'whole_insertion_ready':False,'whole_impact_qualified':False,
       'objective1_complete':False,'old_solver_reruns':0,'next_iteration':'AIRCRAFT-A24'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'assessment':a,'coupling_summary':rel(OUT/'coupling_summary.json'),'original_failed_attempts_preserved':True})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'current_whole_video_physical_s':.0200001220703125,'complete':False,'next':route()})
    table='\n'.join(f"| {x['revision']} / {x['case']} | {x['maximum_residual_J']:.8g} | {'réussi' if x['pass'] else '**échoué**: '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows)
    inertia_table='\n'.join(f"| {x['axis']} | {x['independent_clip_lumped_I_g_mm2']:.9g} | {x['native_clip_part_I_median_g_mm2']:.9g} | {x['native_added_global_I_median_g_mm2']:.9g} | {100*(x['native_added_global_I_median_g_mm2']/x['independent_clip_lumped_I_g_mm2']-1):.4f}% |" for x in channels['rows'])
    pair_table='\n'.join(f"| {x['axis']} | {x['maximum_added_KE_error_J']:.9g} | {x['tolerance_J']:.9g} | **échoué** |" for x in pairs['pairs'])
    REPORT.write_text(f'''# AIRCRAFT-A23 — solide à translations et transmission aux peaux

**26 nouveaux contrôles natifs**, tous avec bilan énergétique réussi. Le solide isolé passe les contrôles de masse, d'inertie physique et de traction. Le montage aux peaux conserve la masse totale mais **échoue à l'énergie cinétique globale ajoutée surXYZ**. Il n'est pas inséré dans l'avion entier. L'objectif vidéo3D des10premières secondes physiques reste incomplet; l'aperçu entier disponible A20 couvre20ms.

## 1. Faits directement observés ou transcrits

Graine1102048, aucun tirage aléatoire. Solide HA8 TYPE14, intégration2×2×2, uniquement trois degrés de liberté de translation par nœud. Dimensions4×1×0,5mm, masse0,00556g. Rotations prescrites90° surXYZ, traction élastique N4 puis N8, rotations libres à10rad/ms sur le maillage12³, puis montage avec et sans connecteur sur une peau métallique et le sandwich A20. Les attaches du cœur restent les Spot5 p3 A20. Un thread CPU, aucun GPU ni mise à l'échelle de masse. Entrées en g/mm/ms, conversions énergétiques en J par facteur0,001.

Le premier témoin de traction w0 déplace par erreur les nœuds18/19 du bord de support àx=0, sélectionnés par x>=0. Le support se déforme, avec0,000328088J d'énergie interne. Le déplacement relatif des extrémités du solide n'est que0,0008mm; ses énergies N4/N8 correspondent alors à la référence adaptée à ces conditions à1,151%/0,528%. Ces calculs et leurs critères échoués sont conservés. La nouvelle déclaration w1 fixe tout le support et déplace uniquement les peaux de0,004mm; elle compare le canal PART du solide à la rigidité3D indépendante.

Les rotations reliées w0 sur1ms échouent à la vitesse rigide de tous les nœuds. Les extrémités restent dans0,005m/s, mais l'intérieur atteint0,06158/0,01421/0,01506m/s d'écart enXYZ. La rotation w1 sur10ms garde angle, masse, matériaux, maillage, interfaces et seuils; les neuf contrôles individuels w1 passent. Ce résultat ne qualifie pas le mouvement rapide w0. Les26bilans passent;21/26ensembles de critères individuels passent. La comparaison indépendante avec/sans connecteur échoue encore.

Deux interruptions de post-traitement sont documentées, sans interruption ni répétition des solveurs: w0 supposait des temps TFILE strictement égaux; w1 conservait un chemin w0 pour la traction. Un nouveau lecteur en cache utilise le support temporel commun et vérifie une borne d'erreur de recalage. Le lecteur de champs initial rechargeait le NPZ pour chaque composante: il a été arrêté puis corrigé pour charger une seule fois les tableaux, en réutilisant les VTK déjà produits. Les78échantillons natifs sont finis et sans suppression d'élément. Le critère textuel initial d'identité des coordonnées2e-5mm échoue sur certains champs imprimés à six chiffres significatifs; cet échec est conservé, avec un addendum fondé sur une borne explicite d'arrondi et de stockage float32. Aucun seuil des calculs mécaniques n'est élargi.

Conservation vérifiée de{p['files']}fichiers antérieurs, soit{p['bytes_hashed']/1e9:.3f}Go; les archives sources ne sont pas rescannées.

## 2. Résultats d'un modèle officiel

La documentation primaire [TYPE14](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type14_solid_starter_r.htm) décrit la formulation volumique. [TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm) décrit Spot5 et Iproj2. La [théorie TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_kinematic_tied_interface_r.htm) décrit le transfert des masses secondaires aux nœuds principaux selon les fonctions de forme, ainsi que les termes d'inertie liés aux offsets. Une telle distribution peut conserver la masse tout en modifiant un tenseur diagonal discrétisé. Cette indication est une piste pour le diagnostic local, pas une preuve de la cause complète du déficit A21. Aucun résultat de dommage NIST n'est utilisé comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de vidéo ou photographie historique. Réemploi en lecture seule des entrées A20, de l'audit A22 et des sources techniques déjà conservées. Les courbes acier A22 restent non adoptées; leur début de striction n'est pas converti en seuil de rupture.

## 4. Hypothèses propres au modèle

LAW2/1 hérité:rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, écrouissage nul et fracture absente. Capacité axiale de prototype162N. Dimensions, capacité et matériau d'attache non identifiés pour AA11. Aucun ajout à l'avion entier. La masse0,334g du prototype à poutres A22 n'est pas le budget du nouveau solide. Support10×10×0,5mm, sandwich10×10×9mm, solide adjacent à la peau extérieure inférieure et deux attaches d'extrémité Spot5 Iproj2, dsearch0,8mm. Masse de référence0,3604g, avec solide0,36596g; aucune ADMAS ni compensation de densité/inertie.

La rigidité de traction indépendante utilise une élasticité isotrope3D à petits déplacements, des fonctions hexaédriques et huit points de Gauss. Les rotations libres utilisent un tenseur continu indépendant et la masse nodale lumped explicitement assemblée. Le maillage12³ réduit l'erreur d'inertie continue à1,389%, dans le seuil2%. Les maillages prescrits4×2×2/8×4×4 comparent leur propre masse discrète; leur inertie intrinsèque continue ne doit pas être déclarée convergée à partir de ces seuls contrôles.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Critères individuels |
|---|---:|---|
{table}

La traction corrigée donne une différence de maillage de{100*r['elastic_mesh_relative_difference']:.4f}%, sous le seuil5%, et passe les références indépendantes. Les trois rotations libres conservent énergie, quantité de mouvement et moment cinétique, sans canal RKE de solide artificiel.

En rotation lente, la cinématique et le canal cinétique propre au solide retrouvent la référence discrète. Le canal global supplémentaire reste biaisé:

| Axe | Tenseur discret connu(g·mm²) | Tenseur issu du PART solide | Tenseur issu de l'ajout global | Écart global |
|---|---:|---:|---:|---:|
{inertia_table}

| Axe | Écart maximal d'énergie ajoutée(J) | Seuil2%+1e-7J | Résultat |
|---|---:|---:|---|
{pair_table}

Le recalage temporel w1 passe sa borne explicite et ne suffit pas à expliquer ces écarts. Les canaux natifs sont conservés dans inertia_channels_w0/w1.json; aucun terme n'est reconstruit, ajouté ou retiré du bilan. Tous les témoins gardent leur masse totale. L'écart cinétique global rend le montage non qualifié malgré les bilans corrects. La transmission des masses et offsets TYPE2 doit être testée séparément.

## 6. Contradictions et informations manquantes

L'inertie correcte du solide seul ne garantit pas celle du montage. Une énergie interne quasi nulle et un bilan natif correct ne suffisent pas à qualifier la masse dynamique distribuée. L'attache mécanique historique, les propriétés à grand taux de déformation, l'arrachement, le cisaillement, la fracture et la correspondance des nuances restent inconnus. La géométrie inclinée des24racines de l'avion n'a pas été remplacée. Le bilan local entier A21 et ses limites matérielles restent échoués. Gravité, structure intérieure porteuse et contacts de fragments sont à compléter avant extension temporelle. Ni le solide isolé ni son témoin plat n'identifie un mécanisme historique.

{route()}
''',encoding='utf-8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A23 → AIRCRAFT-A24\n\nRapport: '+rel(REPORT)+'. Résultats: '+rel(OUT/'coupling_summary.json')+'.\n\n'+route()+'\n',encoding='utf-8')
    files=[x for x in OUT.rglob('*') if x.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a23*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a23*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in sorted(set(files))]})
    print({'A23_prepared':True,'native_controls':26,'paired_inertia_pass':False},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');old=read(OUT/'before_state.json');assert st==old and st['current_iteration']=='AIRCRAFT-A22';reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();assert cy==read(OUT/'before_publication_cycle.json')
    a=read(OUT/'scientific_assessment.json');t=now();record={'experiment_id':'WTC1-AIRCRAFT-A23','registered_at':t,'configuration':rel(CFG),'configuration_w1':rel(ROOT/'wtc1_simulation_v8/data/aircraft_a23_coupling_w1.json'),'report':rel(REPORT),'results':rel(OUT/'coupling_summary.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A23',next_iteration='AIRCRAFT-A24',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a23_key_results']=record;st['validated_artifacts'].update(aircraft_a23_report=rel(REPORT),aircraft_a23_results=rel(OUT/'coupling_summary.json'),aircraft_a23_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A23');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A22+AIRCRAFT-A23 now verified')
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness()
    protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_hashes':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_results_and_policies':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A23','route':st['current_iteration']=='AIRCRAFT-A23' and st['next_iteration']=='AIRCRAFT-A24','goal_incomplete_and_video_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','two_pending_iterations':cy['pending_iterations']==['AIRCRAFT-A22','AIRCRAFT-A23'] and cy['pending_count']==2,'A21_publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_impact_qualified':False,'objective1_complete':False};assert proof['pass'],checks;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
