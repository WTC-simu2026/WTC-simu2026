"""Preserve, report and register the completed A21 numerical investigation without publication."""
from run_aircraft_a21_halfdt import *
import time
REPORT=OUT/'rapport_aircraft_a21.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A21_HANDOFF.md'

def verify_files(rows):
    for i,row in enumerate(rows):
        p=ROOT/row['path'];assert p.is_file() and p.stat().st_size==row['bytes'] and streamsha(p)==row['sha256'],row['path']
        if (i+1)%1000==0:print({'files_verified':i+1,'of':len(rows)},flush=True)
    return len(rows)

def preserve():
    hguard();assert not (OUT/'preservation_verification.json').exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows);dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'verification_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'all_pinned_old_artifacts_unchanged':True});print({'old_files_preserved':n},flush=True)

def route(r):
    return ('AIRCRAFT-A22 : objectif vidéo3D de10 secondes physiques incomplet. Lire le rapport A21, r0/HALF_DT_12/review.json, native_precision_review.json, root_structural_review.json, control_channel_audit.json et cached_skin_negative_localization.json. '
        'A21 est un nouveau départ intact de12ms, mêmes entrées mécaniques A20, pas0,25 contre0,5. Impulsion et énergie finale convergent mais le bilan local reste faux au nez et au contact du fuselage. Ne pas relancer A20/A21 ou leurs témoins. '
        'Réutiliser les contrôles cœur LAW28 et sandwich TYPE2 Spot5 p3 A20 réussis; ne pas remplacer sans preuve Spot5 par Spot2. Les témoins de rotation RBE2 échouent avec ou sans peau de fuselage; aucune cause complète du déficit entier n’est prouvée. '
        'Les TYPE2 testés à la racine ne sont pas qualifiés: extrapolation de bord, énergie/inertie ou hiérarchie556. Les prototypes Spot2, même en référence sans nouvelle racine, échouent au bilan de rotation; cela ne remet pas silencieusement à zéro les réussites Spot5 p3. '
        'Priorité: comparer une attache mécanique finie, avec masse et inertie explicites, à un témoin indépendant de translation/rotation et dynamique libre. Pré-déclarer géométrie, capacité et incertitudes; conserver le budget initial ou annoncer explicitement toute masse ajoutée, sans ajuster ADMAS/densité pour fermer un bilan. '
        'Seulement après réussite des témoins, construire un départ intact et vérifier bilan local, matériaux et contact avant extension. Préparer en parallèle une rupture métallique/acier à partir de références et plages déclarées, sans cible de dommage. La référence NASA ATR42 à9,14m/s est une source de modèle différente, pas une mesure de fracture AA11 à200m/s. '
        'Ne pas prolonger les états invalides vers100ms,1s ou10s et ne pas inventer une RKE. Gravité, intérieur porteur et contacts des fragments restent nécessaires. '
        'Le lecteur CSV place les champs PART avant NODE: sélectionner les titres de groupes. Les erreurs de génération/lecture et tous les témoins refusés sont conservés. '
        'Le MP4/GIF A20 demeure le dernier aperçu:20ms physiques ralentis. A12+A13 sont déjà publiés; A14 àA21 restent locaux, sans nouvelle autorisation externe.')

def prepare():
    hguard();assert not REPORT.exists() and not HANDOFF.exists();p=read(OUT/'preservation_verification.json');assert p['pass'];r=read(D/'review.json');raw=read(OUT/'native_precision_review.json');skin=read(OUT/'cached_skin_negative_localization.json');root=read(OUT/'root_structural_review.json');channel=read(OUT/'control_channel_audit.json');mat=read(OUT/'material_reference_assessment.json');assert mat['table_render_visually_inspected'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h);nxt=route(r)
    controls=[];failures=[]
    for rev in ['w0','w1','w2','w3','w4','w5','w6','w7','w8']:
        q=OUT/rev
        if not q.exists():continue
        for d in sorted(q.iterdir()):
            if not d.is_dir():continue
            controls.append({'revision':rev,'case':d.name,'review':rel(d/'review.json') if (d/'review.json').exists() else None,'Starter_gate':rel(d/'starter_gate.json') if (d/'starter_gate.json').exists() else None,'native_Engine_executed':(d/'engine.log').exists(),'native_normal_termination':(d/'engine.log').exists() and 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace'),'original_gate_pass':read(d/'review.json').get('pass') if (d/'review.json').exists() else False})
            failures += [rel(f) for f in d.glob('retained_failure_*.json')]
    dump(OUT/'campaign_review.json',{'created_utc':now(),'fresh_whole':r,'native_controls':controls,'retained_failure_records':failures,'all_declared_checks_pass':False,'whole_root_cause_proven':False,'physical_impact_qualified':False,'objective1_complete':False,'old_solver_reruns':0})
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A21','status':'completed_cached_diagnosis_root_controls_and_fresh_halfdt12ms__local_energy_and_material_gates_failed','fresh_intact_native_horizon_s':r['end_ms']*.001,'main_engine_wall_s':r['main_engine_seconds'],'same_A20_geometry_material_mass_CG_inertia':True,'native_CSV_precision_alone_explains_deficit':False,'halfdt_impulse_relative_difference':r['comparison']['end_impulse_relative_difference'],'halfdt_generated_relative_difference':r['comparison']['end_generated_relative_difference'],'local_energy_pass':r['checks']['native_local_energy'],'failed_whole_checks':r['failed_checks'],'root_RBE2_rotational_controls_pass':root['all_pass'],'root_surface_tie_qualified':False,'specific_whole_energy_cause_proven':False,'negative_A20_skin_element_localized':skin['minimum_record'],'control_csv_node_mapping_addendum':rel(OUT/'control_channel_audit.json'),'material_reference':rel(OUT/'material_reference_assessment.json'),'physical_impact_qualified':False,'objective1_target_s':10,'objective1_complete':False,'seconds_extension_allowed':False,'old_failed_gates_retained':True,'old_solver_reruns':0,'NIST_damage_fitted':False}
    dump(OUT/'scientific_assessment.json',assessment);dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'latest_diagnostic_native_s':r['end_ms']*.001,'retained_A20_video_physical_s':.0200001220703125,'new_10s_video_created':False,'complete':False,'next':nxt})
    table='\n'.join(f"| {k} | {'réussi' if v else '**échoué**'} |" for k,v in r['checks'].items());pairtable='\n'.join(f"| {q['axis']} | {q['reference_peak_total_J']:.8g} | {q['RBE2_peak_total_J']:.8g} | {q['maximum_energy_difference_J']:.8g} | {'réussi' if q['RBE2_energy_balance_pass'] else '**échoué**'} |" for q in root['pairs']);worst=skin['minimum_record'];c=r['comparison'];wa=raw['windows'];wn=r['windows']
    REPORT.write_text(f'''# AIRCRAFT-A21 — précision temporelle et transfert des attaches

Un nouvel impact intact atteint **{r['end_ms']:.9f} ms physiques**, avec un pas deux fois plus fin et les mêmes entrées mécaniques qu’A20. L'impulsion finale varie de **{c['end_impulse_relative_difference']*100:.4f}%**, l'énergie générée de **{c['end_generated_relative_difference']*100:.4f}%**. Le bilan local échoue encore. Les attaches ont un défaut de rotation reproductible sur témoins; aucune correction complète n'est qualifiée. **La vidéo de10 secondes physiques reste à produire.** Le dernier MP4/GIF conservé A20 couvre20 ms et son ralenti ne vaut pas10 secondes simulées.

## 1. Faits directement observés ou transcrits

Graine1102046, zéro tirage. Analyse des données A20 en cache, déclarations immuables avant les nouveaux témoins et le nouveau solveur. Un seul nouveau cas entier, HALF_DT_12: pas0,25 au lieu de0,5, horizon12 ms au lieu de20 ms; aucun redémarrage depuis l'état final invalide A20. Vitesse[-200;5;2]m/s, masses, géométrie, matériaux, attaches, contacts, appuis, intervalles de sorties identiques. Starter confirme masse, CG et inertie strictement identiques. Les deux avertissements de voisinage1166/343 restent présents et le contrôle zéro avertissement reste faux.

Calcul entier sur2threads CPU: **{r['main_engine_seconds']:.3f}s**, soit {r['main_engine_seconds']/60:.2f}min. Fin native et observateur terminal enregistrés; tous les champs CSV confrontés aux données binaires, sans relancer l'ancien solveur. Coordonnées et vitesses confrontées à un second lecteur sur4états natifs. Tous les champs d'énergie de peau conservés sont examinés.

Dans A20, {raw['source_rows']}lignes brutes confirment le défaut: l'impression CSV peut déplacer le résidu de {raw['maximum_printed_CSV_residual_difference_J']:.3f}J au maximum, contre un excès de contrôle de {wa[1]['maximum_gate_excess_J']:.3f}J au contact du fuselage. La quantification binaire de KE vaut262,144J à l'énergie initiale≈2,441GJ. Les seuils restent5% de l'énergie générée +1000J lorsque celle-ci dépasse1000J.

L'énergie négative A20 se trouve dans la peau supérieure, facette{worst['facet']}, élément{worst['element_id']}: {worst['IE_J']:.9f}J à{worst['time_ms']:.9f}ms. Il est encore intact et son champ de dommage est nul. Aire initiale{worst['initial_area_mm2']:.6f}mm², déformée{worst['deformed_area_mm2']:.6f}mm². Cela localise le défaut et ne prouve ni une cause ni une énergie physique négative. Onze états conservés contiennent cet élément négatif.

## 2. Résultats d'un modèle officiel

Aucun dommage NIST ou historique n'a servi de cible. La documentation primaire décrit les [RBE2 à inertie scalaire](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm) et les [liaisons TYPE2 avec hiérarchie](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm). La hiérarchie TYPE2 testée est refusée par le binaire556, malgré les niveaux explicites et les champs lus correctement; sa compatibilité n'est pas qualifiée. Le passage de Spot5 à Spot2 échoue également au bilan du témoin de référence. Il ne remplace pas les contrôles Spot5 p3 A20 réussis.

Le modèle NASA d'un essai ATR42 à9,14m/s utilise des propriétés estimées depuis MIL-HDBK-5H. Le tableau1 de la pagePDF5, vérifié visuellement, donne pour2024-T3 E66,33GPa, seuil243MPa, module d'écrouissage826,7MPa et déformation ultime14,63%; pour7075-T6 E71,02GPa, seuil360MPa, écrouissage1001,8MPa et déformation ultime4,49%. Ce sont des paramètres du modèle d'un autre avion, pas des mesures de fracture d'AA11 à200m/s. Aucune valeur n'est adoptée silencieusement; conversions conservées dans material_reference_assessment.json. [Publication NASA originale](https://ntrs.nasa.gov/api/citations/20040086484/downloads/20040086484.pdf).

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie ou vidéo historique analysée. Réemploi en lecture seule des sources et sorties A20. Acquisition séparée du PDF primaire NASA et de la documentation des contraintes; manifestes SHA256. La première autre URL NASA n'a pas fourni un document accepté par le contrôle d'acquisition; aucun paramètre n'en est tiré. Conservation vérifiée de **{p['files']} fichiers antérieurs**, {p['bytes_hashed']/1e9:.3f}Go. A12+A13 publiés restent intacts, A14 àA21 locaux.

## 4. Hypothèses propres au modèle

Le modèle entier garde ses limites: cœur LAW28 fini mais sans densification ni G mesuré, peaux et joints à seuils déclarés hypothétiques,24attaches de racine RBE2 idéales, matériaux métalliques parfaitement plastiques sans fracture finie, absence de gravité, d'intérieur porteur et de contact complet des fragments. Les témoins sont des contrôles d'implémentation et ne prouvent pas les propriétés de l'assemblage historique.

Les témoins de masse ponctuelle utilisent les six offsets réels de la première racine et des masses connues indépendantes; ils ne modifient pas la masse de l'avion. La référence structurale ajoute une peau de fuselage10×10mm d'épaisseur2,54mm, matériau hérité. Les variantes TYPE2 de bord, puis sandwich/cœur/peau/racine, sont déclarées et archivées séparément. Aucune extrapolation refusée ou mise à l'échelle de masse n'est cachée. Aucun terme RKE n'est inventé pour fermer un bilan.

## 5. Résultats dérivés

La translation de l'attache transmet correctement masse, mouvement et impulsion. Les rotations de la géométrie ponctuelle sont justes, mais le total énergétique natif omet l'énergie attendue; l'inertie sphérique est216,75g·mm² contre2,60441g·mm² autour deY pour les masses ponctuelles connues. Avec une peau de fuselage et une référence cinématique indépendante identique, la référence conserve son énergie et les trois RBE2 échouent:

| Axe | Pic référence(J) | Pic RBE2(J) | Écart maximal(J) | Bilan RBE2 |
|---|---:|---:|---:|---|
{pairtable}

La comparaison TYPE2 n'a pas abouti à une attache qualifiée: recherche améliorée laisse4points hors bord; recherche ancienne les lie mais avertit et les variantes échouent à des contrôles d'énergie et d'inertie. Le contrôle de masse ajoutée exactement nulle échoue sur un champ de7,1×10⁻¹⁵g, alors que la masse globale est constante et le seuil relatif A21 pré-déclaré passe. L'échec brut reste conservé dans l'addendum de précision, sans modifier la masse ni les seuils. Les interfaces imbriquées refusent le démarrage556. Les témoins de référence Spot2 ont eux-mêmes un résidu de≈0,142122J, malgré une IE quasi nulle et des mouvements corrects. Le lecteur CSV met PART avant NODE; un addendum vérifie les21histoires mixtes en sélectionnant les titres de groupes. Les premiers contrôles de mouvement erronés restent conservés; les énergies globales nommées et le diagnostic entier n'étaient pas affectés.

Les refus initiaux sont distingués des défauts physiques: témoin sans PART1114, points de bord1079/86, omission de6courbes de matériau126 corrigée dans une copie, hiérarchie556, double comptage du résumé d'avertissements corrigé sans relancer Starter. Les anciens fichiers et résultats faux ne sont pas écrasés.

Sur le cas entier, avant10ms, l'excès maximal du contrôle local passe de{wa[0]['maximum_gate_excess_J']:.3f}J à{wn[0]['maximum_gate_excess_J']:.3f}J. Le nombre de lignes brutes en échec passe de{wa[0]['failed_rows']} à{wn[0]['native_failed_rows']}. Dès le contact du fuselage, le pas fin ne répare pas le bilan: excès maximal{wn[1]['maximum_gate_excess_J']:.3f}J, résidu{wn[1]['residual_at_worst_J']:.3f}J pour{wn[1]['generated_at_worst_J']:.3f}J générés à{wn[1]['worst_time_ms']:.9f}ms. Le pas de temps seul n'explique pas le défaut.

À la fin: énergie générée{r['final_native_generated_J']:.3f}J, résidu{r['final_native_residual_J']:.3f}J. Au temps commun11,98007ms, l'impulsion varie de{c['end_impulse_relative_difference']*100:.6f}%; l'énergie à12ms varie de{c['end_generated_relative_difference']*100:.6f}%. Ces deux contrôles de demi-pas passent. Erreurs de quantité de mouvement globale/appuis{r['global_support_momentum_error_Ns']:.6f}N·s et façade/contact{r['facade_contact_momentum_error_Ns']:.6f}N·s, sous le seuil inchangé. Les réussites globales ne remplacent pas le contrôle local.

Plasticité maximale échantillonnée: métal{r['maximum_metal_plastic_strain']:.6g}, façade{r['maximum_facade_plastic_strain']:.6g}, poutres{r['maximum_beam_plastic_strain']:.6g}, au-delà du seuil diagnostique0,1. Minimum d'énergie de peau sauvegardée{r['minimum_saved_skin_element_IE_J']:.9f}J. À12ms,1065peaux,607cœurs et605joints sont supprimés nativement. Les états sont finis et leur connectivité est conservée, sans rendre intact un élément supprimé.

| Contrôle entier A21 | Résultat |
|---|---|
{table}

## 6. Contradictions et informations manquantes

La cause complète du résidu entier n'est pas isolée. Le transfert d'inertie et l'énergie des attaches exigent une correction contrôlée; les témoins faux ne sont pas une solution prête à insérer. La déformation temporelle converge sur certains indicateurs alors que le bilan local reste faux. Les paramètres d'écrouissage, rupture ductile, dépendance au taux, état de contrainte et longueur de maille restent à définir pour le métal et la façade. La petite variation d'aire de l'élément négatif n'établit pas sa cause. Une rotation correcte n'est pas une conservation d'énergie ni une validation physique.

{nxt}
''',encoding='utf-8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A21 → AIRCRAFT-A22\n\nRapport: '+rel(REPORT)+'. Résultats: '+rel(D/'review.json')+'. Objectif10s incomplet.\n\n'+nxt+'\n',encoding='utf-8')
    scripts=list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a21*.py'));cfgs=list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a21*.json'));files=[p for p in OUT.rglob('*') if p.is_file()]+scripts+cfgs+[HANDOFF];dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'prepared_A21':True,'new_files':len(set(files)),'old_files_preserved':p['files']},flush=True)

def register():
    hguard();n=verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st['current_iteration']=='AIRCRAFT-A20' and st['next_iteration']=='AIRCRAFT-A21';reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes();a=read(OUT/'scientific_assessment.json');t=now();nxt=route(read(D/'review.json'));rec={'experiment_id':'WTC1-AIRCRAFT-A21','registered_at':t,'status':a['status'],'configuration':rel(CFG),'halfdt_configuration':rel(HC),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a,'next_iteration':'AIRCRAFT-A22'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A21',next_iteration='AIRCRAFT-A22',current_status=rec['status'],next_objective=nxt,updated_at=t);st['aircraft_a21_key_results']=rec;st['objective1_video_10s'].update(latest_numerical_diagnostic_s=a['fresh_intact_native_horizon_s'],latest_numerical_diagnostic_report=rel(REPORT),status='active_incomplete',physical_goal_complete=False);st['validated_artifacts'].update(aircraft_a21_report=rel(REPORT),aircraft_a21_results=rel(OUT/'campaign_review.json'),aircraft_a21_handoff=rel(HANDOFF));assert 'AIRCRAFT-A21' not in cy['pending_iterations'];cy['pending_iterations'].append('AIRCRAFT-A21');cy.update(pending_count=len(cy['pending_iterations']),updated_at=t,next_publication_after='A14 throughA21 pending; explicit external publication authorization required for these files');dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    hguard();n=n or verify_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json');prefix=(OUT/'before_registry.jsonl').read_bytes();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];checks={'new_artifact_hashes':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_policies_results_preserved':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A21','route':st['current_iteration']=='AIRCRAFT-A21' and st['next_iteration']=='AIRCRAFT-A22','10s_goal_incomplete':not st['objective1_video_10s']['physical_goal_complete'],'A20_video_preserved':all(st['objective1_video_10s'][k]==old['objective1_video_10s'][k] for k in ['current_native_whole_duration_s','interim_MP4','interim_GIF']),'harness_pass':h['Status']=='PASS','publication_pending_preserved':cy['pending_iterations']==oc['pending_iterations']+['AIRCRAFT-A21'],'remote_baseline_unchanged':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])};proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'external_publication_performed':False,'physical_impact_qualified':False,'objective1_complete':False};assert proof['pass'],checks;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','prepare','register','verify']);globals()[p.parse_args().action]()
