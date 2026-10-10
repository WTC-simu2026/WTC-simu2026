"""Seal zero-offset test, physical shell-inertia diagnostic and real root inventory."""
from run_aircraft_a25 import *
from finalize_aircraft_a22 import verify_files
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import subprocess
REPORT=OUT/'rapport_aircraft_a25.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A25_HANDOFF.md'

def route():
    return ('AIRCRAFT-A26 : conserver A24/A25 et leurs échecs sans relancer leurs solveurs. Le simple décalage nul ne restaure pas le moment physique. '
      'Les références de coques héritées portent0,1346221J de RKE à10rad/ms, contre0,0003354167J physique transverse et zéro drilling: contrôler le modèle de masse rotative du support avant d’accuser exclusivement Spot25. '
      'Aucune soustraction ou reconstruction RKE dans les bilans, aucune compensation de densité ou ADMAS. Tester une représentation à translations pour les plaques/peaux, ou un raffinement contrôlé, avec mêmes volumes, densités, matériaux, orientations et capacités annoncées. '
      'Les lois orthotropes et la flexion doivent être vérifiées; une conversion de formulation ne qualifie pas automatiquement un matériau. Le noyau A20 reste préservé: toute nouvelle liaison conforme relève d’une déclaration et de témoins distincts. '
      'Le fichier root_geometry_preparation.json donne les24racines et144ancres réelles, avec faces principales, normales et épaisseurs. Leur géométrie native et leur budget restent à construire après qualification du raccordement. '
      'Ensuite nouveau départ entier intact et bilan local, coût réel avant calcul long. Matériaux A21, gravité, intérieur, fracture et contacts de fragments restent ouverts. '
      'Objectif10secondes physiques3D incomplet, meilleur entier A20=20ms; aucun dommage connu comme cible. Publication A24+A25 après intégrité vérifiée.')

def fields():
    samples=[]
    for d in sorted((OUT/'w0').iterdir()):
        g=read(d/'generation.json');xyz=np.asarray(g['nodes_mm']);n=g['name'];native=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))
        for p in sorted(set([native[0],native[len(native)//2],native[-1]])):
            ad=OUT/'native_field_audit'/d.name;ad.mkdir(parents=True,exist_ok=True);v=ad/(p.name+'.vtk');assert not v.exists();res=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120);v.write_text(res.stdout,encoding='utf-8');q=vtk(v.read_text(encoding='utf-8'));order=np.argsort(q['NODE_ID']);pts=q['points'].reshape(-1,3)[order];disp=q['Displacement'].reshape(-1,3)[order];vel=q['Velocity'].reshape(-1,3)[order];delta=abs(pts-xyz-disp);bound=printed_bound(pts)+printed_bound(disp)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(pts),abs(disp),abs(xyz)])+1e-8
            checks={'node_ids':bool(np.array_equal(q['NODE_ID'][order],np.arange(1,len(xyz)+1))),'finite':bool(np.isfinite(pts).all() and np.isfinite(disp).all() and np.isfinite(vel).all()),'coordinate_identity_with_printing_bound':bool(np.all(delta<=bound)),'no_eroded_elements':bool(np.all(q['EROSION_STATUS']==1))};samples.append({'case':d.name,'time_ms':q['time'],'native':rel(p),'native_sha256':streamsha(p),'vtk':rel(v),'vtk_sha256':streamsha(v),'checks':checks,'pass':all(checks.values())})
    out={'created_utc':now(),'samples':samples,'pass':all(r['pass'] for r in samples),'solver_thresholds_unchanged':True,'native_reruns':0};dump(OUT/'native_fields_review.json',out);assert out['pass'];return out

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists();p=read(OUT/'preservation_verification.json');assert p['pass'];f=fields();r=read(OUT/'coupling_review.json');i=read(OUT/'shell_inertia_diagnostic.json');mapping=read(OUT/'root_geometry_preparation.json');rows=read(OUT/'native_case_summary.json')['cases'];assert len(rows)==7 and all(x['checks']['native_full_energy_balance'] for x in rows);h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
    executions=[{'path':rel(x),**read(x)} for x in sorted(OUT.glob('w0/*/*.execution.json'))];dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native double precision win64 20260728','CPU_threads':1,'GPU':False,'execution_seconds_sum':sum(x.get('seconds',0) for x in executions),'executions':executions,'executables':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe',RUNTIME/'anim_to_vtk_win64.exe']]})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A25','status':'completed_zero_offset_controls__physical_angular_failure_and_shell_inertia_excess','native_controls':7,'native_energy_balances_passed':7,'native_individual_sets_passed':sum(x['pass'] for x in rows),'physical_free_angular_momentum_pass':False,'physical_initial_shell_RKE_pass':False,'elastic_footprint_reference_pass':False,'curved_roots_inventoried':24,'distinct_skin_anchor_nodes':144,'curved_native_controls_executed':False,'native_field_samples':len(f['samples']),'old_A20_A24_native_solver_reruns':0,'new_whole_impact_executed':False,'whole_insertion_ready':False,'physical_strength_and_fracture_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A26'};dump(OUT/'scientific_assessment.json',a);dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'assessment':a,'coupling_review':rel(OUT/'coupling_review.json'),'shell_inertia_diagnostic':rel(OUT/'shell_inertia_diagnostic.json'),'original_failed_gates_preserved':True});dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'complete':False,'next':route()})
    table='\n'.join(f"| {x['case']} | {x['maximum_residual_J']:.9g} | {'réussi' if x['pass'] else '**échoué**: '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in rows);lt='\n'.join(f"| {x['motion']} | {x['connected']['maximum_drift_kg_m2_s']:.9g} | {x['connected']['limit_kg_m2_s']:.9g} | {x['maximum_added_L_error_kg_m2_s']:.9g} | {x['added_L_limit_kg_m2_s']:.9g} | {'réussi' if x['pass'] else '**échoué**'} |" for x in r['pairs'])
    REPORT.write_text(f'''# AIRCRAFT-A25 — raccordement sans décalage et inertie des coques

**Sept nouveaux contrôles natifs**, tous avec bilan énergétique réussi. La mise à zéro du décalage initial ne restaure pas le moment cinétique physique. Les références de coques héritées présentent aussi une énergie initiale de rotation très supérieure à celle de leur seule épaisseur physique. **Aucune insertion entière ni extension temporelle**. L'objectif10secondes physiques3D reste incomplet; A20 couvre20ms.

## 1. Faits directement observés ou transcrits

Graine1102050, aucun tirage aléatoire. Volume4×1×0,5mm et masse0,00556g conservés, mais ruban déplacé de+0,25mm en z. Sa face supérieure z=−4,25mm coïncide avec les surfaces médianes du support et de la peau inférieure. Seuls les nœuds supérieurs x≤−1mm et x≥1mm sont attachés. Deux surfaces de reprise remplacent les deux extrémités décalées. La distance initiale aux surfaces est nulle, contrôlée avant Engine; dsearch1e-5mm, Stfac100 et Visc1e-20 sont effectivement relus. Les témoins libres XYZ, translation et pas réduitY utilisent les références A24 enregistrées avec vitesses angulaires natives. Deux tractions utilisent une nouvelle rigidité3D indépendante aux nœuds réellement attachés. Aucun solveur A20–A24 répété.

La première substitution du centre de masse dans le générateur ne trouve pas son expression conditionnelle et s'arrête avant tout cas natif. Le script est conservé puis la substitution est corrigée; configuration et dimensions inchangées. Les{len(f['samples'])}champs natifs échantillonnés passent finitude, identités bornées par l'impression et absence de suppression. Conservation vérifiée de{p['files']}fichiers antérieurs, soit{p['bytes_hashed']/1e9:.3f}Go. Le harnais passe.

## 2. Résultats d'un modèle officiel

La [théorie primaire des coques](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_mechanical_prop_r.htm) décrit une inertie nodale sphérique régularisée contenant un terme lié à l'aire de l'élément, en plus de l'épaisseur. Elle ne doit pas être identifiée à la seule inertie physique d'épaisseur. [TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm) décrit les limites de la pénalité Spot25. Les propriétés [solid-shell TYPE20](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type20_tshell_starter_r.htm) et [LAW25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law25_compsh_starter_r.htm) sont conservées comme pistes de nouvelle formulation. Leur simple disponibilité ne constitue pas une validation d'une conversion. Aucun dommage officiel n'est une cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo, photographie ou identification historique. Les24racines et144nœuds de peau sont inventoriés depuis la géométrie A20 en lecture seule, avec triangles du fuselage, quads de peau, normales, offsets et épaisseurs2,54/0,5mm. Il s'agit de la géométrie du modèle A20, pas d'une mesure nouvelle de l'attache réelle. Aucun RBE2 du fichier source n'est supprimé à ce stade.

## 4. Hypothèses propres au modèle

Matériau de ruban LAW2 hérité, rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, sans écrouissage ni rupture; résistance historique inconnue. Support et sandwich A20 inchangés, mêmes masses0,3604g sans et0,36596g avec ruban. Le déplacement de géométrie change le centre de masse et le tenseur du ruban; ils ne sont pas compensés. La reprise sur surfaces médianes est une idéalisation qui comporte un recouvrement géométrique de demi-épaisseur avec les coques, explicitement déclaré. Aucune application directe à AA11. Le budget0,80064g pour144rubans plats identiques serait une simple extrapolation: la masse des futurs rubans courbes n'est pas encore définie.

Le moment physique emploie les masses nodales, positions, vitesses et vitesses angulaires natives, avec l'inertie propre d'épaisseur des coques; conversion g·mm²/ms vers kg·m²/s par1e-6. Les huit canaux d'énergie natifs restent tous dans le bilan, y compris RKE. Aucune inertie n'est ajoutée, retirée ou ajustée dans le calcul. Le diagnostic compare une énergie native à une référence physique distincte, sans reconstruire le bilan.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Critères individuels initiaux |
|---|---:|---|
{table}

| Mouvement | Dérive du moment total(kg·m²/s) | Seuil total | Erreur du moment ajouté | Seuil ajouté | Résultat supplémentaire |
|---|---:|---:|---:|---:|---|
{lt}

Le pasY réduit vaut{r['refinement']['actual_dt_ratio']:.9g}fois le pas initial. Les différences entre pas passent, mais le moment physique demeure non conservé: la convergence n'est pas conservation. La translation uniforme et l'énergie cinétique initiale ajoutée passent. Les deux tractions échouent à la référence rigide des surfaces de reprise: la pénalité reste assez souple pour changer la réponse, même àStfac100. L'écart N4/N8 vaut{100*r['elastic_mesh_difference']:.4f}%, sous5%; ce seuil de maillage ne remplace pas les références échouées.

Dans les trois références A24 à10rad/ms, la RKE initiale native est0,1346221J identique enXYZ. L'énergie propre de l'épaisseur physique des coques métalliques/composites, de masse0,322g et d'épaisseur0,5mm, vaut0,000335416667J enX/Y et zéro pour une rotation normaleZ. L'énergie native transverse est environ401fois cette référence. La masse répartie dans le plan est déjà représentée par les translations nodales. La RKE native reste néanmoins intégralement dans tous les bilans; sa suppression serait une réparation comptable sans justification.

Cette observation montre que le sous-modèle de support n'a pas encore une inertie rotative physique vérifiée. Elle invalide l'attribution exclusive de l'échec de moment au décalage de l'attache. Le tenseur natif par nœud et l'effet du cœur TYPE2 ne sont pas encore lus; ce diagnostic ne prouve pas que la totalité de la dérive ou du déficit local A21 provient des coques.

## 6. Contradictions et informations manquantes

La nouvelle géométrie échoue à son hypothèse suffisante: distance initiale nulle et bon bilan énergétique ne suffisent pas. Le support rotatif doit être vérifié séparément avec inertie physique, rigidité de membrane et de flexion, avant de déclarer une attache valide. Une nouvelle représentation volumique doit conserver volumes, masses, orientations et propriétés, avec contrôles de compatibilité et convergence; aucune conversion implicite. Les144ancres réelles sont préparées mais aucun ruban courbe n'est lancé ou inséré. Résistance, fracture, arrachement, grande vitesse, matériaux A21, gravité, intérieur porteur et contacts de fragments restent ouverts. La vidéo de10secondes physiques n'est pas produite par ce témoin.

{route()}
''',encoding='utf-8');HANDOFF.write_text('# Reprise AIRCRAFT-A25 → AIRCRAFT-A26\n\nRapport: '+rel(REPORT)+'\nRésultats: '+rel(OUT/'campaign_review.json')+'\n\n'+route()+'\n',encoding='utf-8')
    files=[x for x in OUT.rglob('*') if x.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a25*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a25*.json'))+[HANDOFF];dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in sorted(set(files))]});print({'A25_prepared':True,'controls':7,'physical_inertia_and_angular_gates':False},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st==read(OUT/'before_state.json') and st['current_iteration']=='AIRCRAFT-A24';reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes() and cy==read(OUT/'before_publication_cycle.json');a=read(OUT/'scientific_assessment.json');t=now();record={'experiment_id':'WTC1-AIRCRAFT-A25','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A25',next_iteration='AIRCRAFT-A26',current_status=a['status'],next_objective=route(),updated_at=t);st['aircraft_a25_key_results']=record;st['validated_artifacts'].update(aircraft_a25_report=rel(REPORT),aircraft_a25_results=rel(OUT/'campaign_review.json'),aircraft_a25_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A25');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A24+AIRCRAFT-A25 now verified');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_hashes':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_results_and_policies':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A25','route':st['current_iteration']=='AIRCRAFT-A25' and st['next_iteration']=='AIRCRAFT-A26','objective_and_preview_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','two_pending':cy['pending_iterations']==['AIRCRAFT-A24','AIRCRAFT-A25'] and cy['pending_count']==2,'publication_A23_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_insertion_ready':False,'objective1_complete':False};assert proof['pass'],checks;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
