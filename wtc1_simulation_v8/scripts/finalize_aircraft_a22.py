"""Seal A22 controls and source preparation, preserving failures and the incomplete10s goal."""
from run_aircraft_a22 import *
REPORT=OUT/'rapport_aircraft_a22.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A22_HANDOFF.md'

def verify_files(rows):
    for i,r in enumerate(rows):
        p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
        if (i+1)%1000==0:print({'files_verified':i+1,'of':len(rows)},flush=True)
    return len(rows)

def preserve():
    guard();p=OUT/'preservation_verification.json';assert not p.exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows)
    dump(p,{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'old_artifacts_unchanged':True})

def route(review):
    return ('AIRCRAFT-A23 : reprendre les témoins finis A22, sans relancer les anciens calculs. Lire connector_review.json, native_inertia_audit.json, les énergies et les champs natifs de chaque cas, ainsi que material_preparation.json. '
            'Les poutres sont une hypothèse de connecteur, pas une attache historique identifiée. Aucune RKE reconstruite ni compensation de masse. Réutiliser le cœur et Spot5 p3 A20 réussis. '
            'A22 conserve les21bilans natifs mais l’inertie physique échoue enY sur8segments et sur le mouvement libre observable. Le champ RKE révèle une inertie scalaire identique enXYZ,0,000783173g·mm² contre une section physique enY0,000429749; cela ne prouve pas la cause du déficit entier A21. Comparer un connecteur volumique à degrés de liberté de translation et une référence indépendante, avec géométrie et budget déclarés, avant insertion. '
            'Si tous les contrôles d’implémentation passent, vérifier ensuite la transmission à une peau réelle et sa dynamique libre avant un départ intact entier; la masse de24racines serait explicitement ajoutée,0,334061g, pas masquée. '
            'Le tableau acier3-13 donne des paramètres d’écrouissage estimés et un début de striction, pas une fracture. Les courbes préparées sont des candidats non insérés; vérifier la conversion et la correspondance des nuances, puis témoins élastique/plastique, décharge, taux, maille et rupture énergétique. '
            'NASA ATR42 à9,14m/s reste un autre modèle, pas la rupture AA11 à200m/s. Les bilans local et matériaux A21 restent échoués. Gravité, intérieur porteur et contact des fragments à compléter avant10s. '
            'Objectif vidéo3D10secondes physiques incomplet; le MP4/GIF A20 couvre20ms. A14–A21 publiés et vérifiés; A22 seule locale, prochaine publication après A23 vérifiée.')

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists();p=read(OUT/'preservation_verification.json');assert p['pass'];r=read(OUT/'connector_review.json');mat=read(OUT/'material_preparation.json');audit=read(OUT/'native_inertia_audit.json');assert len(r['cases'])==21 and mat['source']['visually_inspected'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h);c=read(CFG);nxt=route(r)
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'software':'OpenRadioss native2026 double precision win64','runtime_release_path':rel(RUNTIME),'executables':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',RUNTIME/'th_to_csv_win64.exe']],'CPU_threads':1,'GPU':False})
    failed=[{'case':x['case'],'nseg':x['nseg'],'checks':[k for k,v in x['checks'].items() if not v]} for x in r['cases'] if not x['pass']]
    status='completed_finite_connector_controls_and_material_source_preparation__'+('implementation_controls_pass_strength_unqualified' if r['all_pass'] else 'connector_controls_failed')
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A22','status':status,'native_controls':len(r['cases']),'all_native_controls_pass':r['all_pass'],'failed_controls':failed,'root_added_mass_g_if_integrated':c['mass_budget']['24_roots_added_g_if_integrated'],'new_whole_impact_executed':False,'old_solver_reruns':0,'previous_A21_local_energy_failure_preserved':True,'strength_and_fracture_qualified':False,'steel_source_table_visually_checked':True,'necking_not_fracture':True,'material_values_adopted_in_whole':False,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A23'}
    dump(OUT/'scientific_assessment.json',assessment);dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'current_video_physical_s':.0200001220703125,'new_10s_video_created':False,'complete':False,'next':nxt})
    table='\n'.join(f"| {x['case']} | {x['nseg']} | {x['maximum_residual_J']:.8g} | {'réussi' if x['pass'] else '**échoué**: '+', '.join(k for k,v in x['checks'].items() if not v)} |" for x in r['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A22 — attache finie et préparation des matériaux

{len(r['cases'])} nouveaux contrôles natifs d'une attache mécanique finie sont conservés. Tous les contrôles d'implémentation: **{'réussis' if r['all_pass'] else 'non réussis'}**. L'attache et la fracture physiques restent non qualifiées. Le dernier aperçu A20 couvre20ms physiques; la vidéo des10premières secondes reste incomplète.

## 1. Faits directement observés ou transcrits

Graine1102047, zéro tirage. Six offsets réels de la première racine A20, chacun subdivisé en4 puis8segments, diamètre circulaire déclaré0,5mm. Translation prescrite, trois rotations prescrites90°, translation libre, trois rotations libres et traction axiale élastique indépendante, soit18contrôles. Trois nouveaux mouvements libres à10rad/ms, au lieu de0,1, rendent l'énergie10000fois plus grande et observable au-dessus du seuil absolu inchangé. Un thread CPU, aucun GPU ni mise à l'échelle de masse. Histoires natives en unités g/mm/ms converties explicitement en J. Les champs de nœuds sont sélectionnés par le titre du groupe, sans supposer qu'ils précèdent PART. Aucun ancien solveur relancé.

La première entrée de translation libre w0 est refusée par26avertissements100217: la seconde ligne requise INIVEL, tempsinitial0/capteur0, avait été omise. Aucun Engine exécuté sur cette entrée. L'erreur, les entrées et le refus restent conservés; une nouvelle copie w1 corrige seulement le format. Les quatre calculs w0 terminés sont réutilisés sans répétition.

La mise à jour GitHub A14–A21 est publiée avant la déclaration A22. Elle contient7917fichiers nouveaux ou actualisés,21archives complémentaires lossless, tous les critères échoués et l'aperçu A20. La vérification distante des tailles, SHA256, auteurs, arbres Git et contrôles automatiques confirme l'intégrité; elle ne qualifie pas la physique. Conservation locale vérifiée de{p['files']}fichiers antérieurs, {p['bytes_hashed']/1e9:.3f}Go.

## 2. Résultats d'un modèle officiel

La documentation primaire décrit les [poutres finies TYPE3](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type3_beam_starter_r.htm) et leur [masse répartie aux nœuds](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/beam_elements_r.htm). Les recommandations de longueur et de section sont vérifiées dans les configurations; elles ne constituent pas une qualification du connecteur.

La pagePDF100 du document NIST NCSTAR1-3D (pageimprimée66) donne des paramètres estimés d'écrouissage Voce pour les aciers de façade. La pagePDF101 précise que epsilon_max est la déformation vraie au maximum de traction et au début de striction. Ces pages ont été rendues et vérifiées visuellement. Les dix familles préparées couvrent un début de striction0,070–0,259; ce n'est pas une plage de rupture. L'élasticité de205GPa et les coefficients en ksi, convertis en MPa avec6,894757293168361, restent des candidats de source, sans affectation à la façade du calcul. Les corrections de nuance et de taux, la rupture après striction et sa régularisation restent ouvertes. [Source primaire](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101021).

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de photographie, vidéo historique ou archive. Lecture seule du PDF de matériau déjà présent dans work/official_sources; son SHA256 est conservé. Réemploi de l'inspection NASA A21, du cœur LAW28 et du sandwich Spot5 p3 A20 réussis. Aucun résultat de dommage NIST ou observé utilisé comme cible.

## 4. Hypothèses propres au modèle

Le diamètre0,5mm, les six connexions ponctuelles et la capacité sont des hypothèses de prototype. Matériau LAW2/1 hérité: rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, écrouissage nul et fracture absente. La capacité axiale élastique par brin est{c['capacity']['elastic_axial_yield_N_per_spoke']:.8g}N; elle ne représente pas une fixation historique mesurée. Les calculs isolés ne changent pas l'avion. Une insertion future ajouterait explicitement **{c['mass_budget']['24_roots_added_g_if_integrated']:.9g}g** aux24racines, sans ADMAS ni compensation de densité.

Les inerties de centre de ligne discret et de cylindres continus sont calculées indépendamment. La contribution de section physique est utilisée comme référence analytique, jamais ajoutée artificiellement au bilan natif. Les mouvements prescrits constituent une référence de cinématique et non une preuve de transmission à la peau de l'avion.

## 5. Résultats dérivés

| Contrôle | Segments/brin | Résidu énergétique maximal(J) | Résultat |
|---|---:|---:|---|
{table}

Tous les seuils sont pré-déclarés. Les21bilans énergétiques natifs passent. Les trois rotations prescrites échouent à l'inertie physique sur4segments. Sur8segments,X etZ passent, maisY garde un écart de14,37% sur le pic cinétique; la nouvelle rotation libreY confirme un écart d'énergie initiale au-dessus du seuil absolu. Le contrôle axial conserve la réponse analytique élastique et les translations conservent leur masse et leur mouvement.

L'audit en cache des six rotations sépare les canaux natifs: la contribution RKE correspond à une inertie identique surXYZ de0,002480230g·mm² pour4segments et0,000783173g·mm² pour8segments. Les cylindres indépendants donnent0,000219535/0,000429749/0,000220667g·mm² pour la seule section physique. Le raffinement réduit l'écart scalaire sans qualifierY. Ce sont des diagnostics des champs natifs; aucun terme n'est ajouté au bilan, aucun seuil élargi, aucune densité ajustée. Le défaut local entier A21 n'est pas expliqué par ce seul témoin. Les mouvements libres à0,1rad/ms ont une énergie enY inférieure au seuil absolu; leur réussite littérale est conservée mais ne qualifie pas l'inertie.

Les fichiers natifs, les entrées, le script utilisé, les champs convertis, les masses, les inerties et chaque échec sont conservés. Voir connector_review.json, native_inertia_audit.json et les review.json individuels. Dix courbes d'écrouissage acier sont préparées uniquement comme candidats bornés avant striction, dans steel_hardening_candidates.json; aucune n'est insérée dans le solveur entier. La conversion en déformation plastique au début de striction comporte une hypothèse explicite de contrainte d'ingénieur au pic, à confirmer avant emploi.

## 6. Contradictions et informations manquantes

Les contrôles de cinématique, d'énergie et de matériau sont distincts. La transmission à une peau réelle, les surfaces de contact/bearing, la capacité en cisaillement et arrachement, les modes de rupture et le budget de masse de l'attache restent à vérifier. Aucun contrôle isolé ne prouve la cause complète du déficit A21. Les limites matérielles et le bilan local de l'avion entier restent échoués. Les données NASA d'un essai ATR42 à9,14m/s ne mesurent pas la fracture AA11 à200m/s. La correspondance des nuances d'acier, l'écrouissage de l'aluminium, le taux, la triaxialité, la maille et l'énergie de rupture restent nécessaires. Gravité, intérieur porteur et contact des fragments n'ont pas été ajoutés par ces témoins.

{nxt}
''',encoding='utf-8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A22 → AIRCRAFT-A23\n\nRapport: '+rel(REPORT)+'. Résultats: '+rel(OUT/'connector_review.json')+'.\n\n'+nxt+'\n',encoding='utf-8')
    files=[x for x in OUT.rglob('*') if x.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a22*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a22*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(x),'bytes':x.stat().st_size,'sha256':streamsha(x)} for x in sorted(set(files))]});print({'prepared_A22':True,'native_controls':len(r['cases']),'implementation_all_pass':r['all_pass']},flush=True)

def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');old=read(OUT/'before_state.json');assert st==old and st['current_iteration']=='AIRCRAFT-A21' and st['next_iteration']=='AIRCRAFT-A22';reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();assert cy==read(OUT/'before_publication_cycle.json')
    a=read(OUT/'scientific_assessment.json');t=now();record={'experiment_id':'WTC1-AIRCRAFT-A22','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'connector_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A22',next_iteration='AIRCRAFT-A23',current_status=a['status'],next_objective=route(read(OUT/'connector_review.json')),updated_at=t);st['aircraft_a22_key_results']=record;st['objective1_video_10s'].update(status='active_incomplete',physical_goal_complete=False);st['validated_artifacts'].update(aircraft_a22_report=rel(REPORT),aircraft_a22_results=rel(OUT/'connector_review.json'),aircraft_a22_handoff=rel(HANDOFF));cy['pending_iterations'].append('AIRCRAFT-A22');cy.update(pending_count=1,updated_at=t,next_publication_after='AIRCRAFT-A22+AIRCRAFT-A23 after two verified iterations')
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    guard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness()
    protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_hashes':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_results_and_policies':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A22','route':st['current_iteration']=='AIRCRAFT-A22' and st['next_iteration']=='AIRCRAFT-A23','goal_incomplete_and_video_preserved':st['objective1_video_10s']==old['objective1_video_10s'],'harness':h['Status']=='PASS','one_pending_iteration':cy['pending_iterations']==['AIRCRAFT-A22'] and cy['pending_count']==1,'A21_publication_preserved':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'whole_impact_qualified':False,'objective1_complete':False};assert proof['pass'],checks;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','prepare','register','verify']);globals()[p.parse_args().action]()
