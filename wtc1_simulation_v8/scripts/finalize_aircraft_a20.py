"""Seal controls, actual whole outputs and failed gates; no external publication."""
from run_aircraft_a20_whole import *
REPORT=OUT/'rapport_aircraft_a20.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A20_HANDOFF.md'

def check_files(rows):
    for row in rows:
        p=ROOT/row['path'];assert p.is_file() and p.stat().st_size==row['bytes'] and streamsha(p)==row['sha256'],row['path']
    return len(rows)

def next_route(r):
    return ("AIRCRAFT-A21 : objectif vidéo3D10 secondes physiques incomplet. Réutiliser les contrôles LAW28 et sandwich TYPE2 p3 réussis A20, sans relancer A19 ni les anciens témoins. "
        "Lire le rapport A20, review.json, geometric_moment_addendum.json, constraint_mass_listing/constraint_mass_interpretation.json et video/video_audit.json. "
        "Le nez a maintenant648 solides de cœur8mm et1296 peaux0,5mm distinctes, avec432 attaches TYPE2 conservant l'offset0,25mm. Rupture du cœur et des peaux native, seuils hypothétiques; pas de décollement cœur-peau ni densification. "
        "La comparaison CG brute A19 a échoué de0,00119582mm; la nouvelle position correspond à l'intégrale géométrique, sans ajustement de densité/ADMAS, et le défaut de référence parent est conservé. "
        f"Contrôles entiers encore échoués : {', '.join(r['failed_checks'])}. "
        "La somme du champ nodal Starter double-compte1144,1544635g sur les dépendants des24racines RBE2; le détail retrouve la masse matérielle à0,000242g près. La différence supplémentaire1,483474g de l'animation est sous la précisionfloat32. Ne pas additionner ce champ comme une masse physique ou soustraire les secondaires animés pour fermer KE/RKE. "
        "Ne pas prolonger vers100ms,1s ou10s ces états hors domaine. Vérifier le bilan local et les éléments à énergie négative; comparer le transfert d'inertie/impulsion des attaches RBE2 à une solution indépendante avant toute correction. "
        "Ajouter ensuite une rupture mécanique justifiée du métal et de la façade, à partir de sources et de plages pré-déclarées, sans sélectionner les dégâts connus ni inventer une RKE. "
        "Un changement mécanique exige un nouveau départ intact. Gravité, contact des fragments, intérieur porteur et coût de la progression en secondes restent à traiter. "
        "Conserver tous les essais w0/w1/w2/w3 et p0/p1/p2/p3. Les paramètres HRH10 typiques concernent12,7mm et ne prouvent pas le matériau historique8mm ni sa fracture dynamique. "
        "A12+A13 déjà publiés intacts; A14 àA20 restent locaux en attente d'autorisation externe explicite.")

def prepare():
    whole_guard();assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists()
    r=read(D/'review.json');v=read(OUT/'video/video_audit.json');c=read(OUT/'core_verified_review.json');s=read(OUT/'sandwich_type2_review.json');p=read(OUT/'preservation_verification.json');mom=read(D/'geometric_moment_addendum.json');massproof=read(D/'constraint_mass_listing/constraint_mass_interpretation.json')
    assert p['pass'] and v['pass'] and c['pass'] and s['pass'] and read(OUT/'visual_QA.json')['decoded_contact_sheet_inspected'];h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
    wall=read(D/'engine.log.execution.json')['seconds'];nxt=next_route(r)
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A20','core_native_controls_pass':c['pass'],'skin_core_offset_controls_pass':s['pass'],'whole_impact_qualified':False,'all_declared_whole_checks_pass':r['all_declared_checks_pass'],
        'failed_whole_checks':r['failed_checks'],'global_energy_pass':r['checks']['global_energy'],'local_energy_pass':r['checks']['local_energy'],'native_horizon_s':r['end_ms']*.001,'main_engine_wall_s':wall,
        'core_finite_yield_and_native_deletion_verified':True,'skin_native_deletion_verified':True,'same_physical_material_budget':True,'no_density_ADMAS_compensation':True,
        'original_parent_CG_gate_failed_and_retained':True,'geometric_moment_reference_addendum_pass':mom['geometric_reference_addendum_pass'],'animation_mass_difference_kg':r['animation_mass_difference_kg'],'initial_nodal_mass_double_count_reconciled':massproof['pass'],'animation_mass_as_physical_total_qualified':False,
        'core_fracture_energy_measured':False,'core_skin_debonding_modelled':False,'core_densification_modelled':False,'metal_fracture_modelled':False,'tower_interior_modelled':False,'gravity_modelled':False,
        'historical_conditions_identified':False,'objective1_target_s':10,'objective1_complete':False,'NIST_damage_fitted':False,'old_failed_gates_retained':True,'old_solver_reruns':0}
    dump(OUT/'scientific_assessment.json',assessment);dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'coverage_s':v['physical_duration_s'],'display_s':v['display_duration_s'],'complete':False,'next':nxt,
        'whole_20ms_wall_s':wall,'linear_10s_days':wall/.02*10/86400,'linear_projection_is_not_ETA':True,'seconds_extension_allowed':False})
    table='\n'.join(f"|{k}|{'réussi' if val else '**échoué**'}|" for k,val in r['checks'].items())
    paneltable='\n'.join(f"|{a['case']}|{a['last_IE_J']:.10g}|{a['maximum_energy_residual_J']:.6g}|{'réussi' if a['pass'] else '**échoué**'}|" for a in s['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A20 — cœur en3D, peaux distinctes et nouvel impact exploratoire

Un nouveau départ intact couvre **{r['end_ms']:.9f}ms physiques**, avec un MP4 et un GIF montrant les positions et suppressions natives des éléments. Le cœur du nez présente désormais un cisaillement et un écrasement finis vérifiés sur témoins. **L'objectif des10 secondes physiques reste incomplet.** Les réussites d'implémentation ne qualifient pas le choc historique ni les bilans entiers échoués.

## 1. Faits directement observés ou transcrits

Graine1102045, zéro tirage. Déclarations préalables du cœur, du sandwich et de l'intégration; revisions d'axes et de couplage conservées. Nouveau modèle:48171nœuds,648solides HA8 de cœur8mm,1296coques de peau0,5mm,432attaches TYPE2. Chaque ancien triangle est subdivisé en3quadrilatères puis extrudé; les deux peaux ont leurs plans moyens à±4,25mm, les faces du cœur à±4mm. Épaisseur matérielle totale9mm. Aire18,5468484323m²; masse41,0627224292kg, budget initial2,214kg/m² conservé. Aucun changement de densité, ADMAS, vitesse[-200;5;2]m/s, autres matériaux, poutres, RBE3, façade ou appuis.

Starter: zéro erreur et deux avertissements1166/343 concernant1803paires initiales de l'autocontact du nez. Le contrôle zéro avertissement reste échoué. Les4contacts extérieurs TYPE25 sont inchangés; l'autocontact des peaux réelles utilise un écart0,5mm, issu des demi-épaisseurs0,25mm de chacune. L'absence d'avertissement incompatible ne qualifie pas le contact des fragments sur plusieurs secondes.

Temps du nouvel impact sur2threads CPU:{wall:.3f}s. Fin native{r['end_ms']:.9f}ms, observateur terminal isolé et fichiers principaux conservés. Les histoires binaires sont confrontées auCSV; coordonnées et vitesses sont confrontées à un second lecteur. Géométrie examinée sur{r['verified_geometry_states']}états, énergie de peau lue dans tous les états conservés. Les états supprimés ne sont pas dessinés comme des solides intacts. Aucun ancien solveur relancé.

## 2. Résultats d'un modèle officiel

Aucun résultat de dommage officiel n'a servi de cible. La documentation primaire Altair précise les entrées du [cœur LAW28](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law28_honeycomb_starter_r.htm), des [solides orthotropes TYPE6](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm) et des [attaches TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm). Les axes locaux ont été contrôlés dans le binaire; SKEW/FIX attendY etZ, d'où la conservation des premiers essais mal orientés. La référence générale nominale de façade héritée n'est pas une identification indépendante de tous les détails historiques.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie ou vidéo historique analysée. La fiche Hexcel HRH10 p4 déjà acquise fournit pour le produit de référence3.2-48 des valeurs typiques à température ambiante:rho48kg/m³,E33=138MPa,G31=41/G23=24MPa,τ31=1,21/τ23=0,69MPa,compression nue2,07MPa. Les essais concernent12,7mm; le modèle8mm et le matériau AA11 ne sont pas identifiés par cette fiche. Sources en lecture seule, hashes enregistrés. Les{p['files']}anciens fichiers épinglés ({p['bytes_hashed']/1e9:.3f}Go) sont conservés sans modification constatée.

## 4. Hypothèses propres au modèle

LAW28 à orthotropie découplée, plateaux constants sans densification ni dépendance au taux. E11/E22=1MPa,G12=0,5MPa et résistances dans le plan sont des substituts déclarés. Seuils de rupture normaux[0,2;0,2;0,05],cisaillement[0,1;0,06;0,06]hypothétiques, avec contrôles0,03/0,06/0,12. Le déclenchement natif est vérifié; l'interprétation exacte comme déformation plastique ou totale n'est pas prouvée. AucunG mesuré, ni transfert de ces valeurs vers une assertion historique.

Les peaux réutilisent LAW25 et leurs seuils déclarés. Attaches cœur-peau TYPE2 sans décollement,1320RBE2 dont24attaches idéales de racine. Les solides du cœur sont continus dans chaque facette, séparés entre facettes; les peaux et joints portent les efforts d'arête. La fracture cohésive624bandes conserve ses anciens paramètres hypothétiques. Pas de rupture du métal ou de la façade, de gravité, d'intérieur porteur ni de carburant résolu.

## 5. Résultats dérivés

Le cœur isolé reproduit les énergies élastiques et les plateaux de force attendus dans les directions testées. La rotation90° a une IE≈1,77×10⁻¹⁰J. Le demi-pas reproduit l'IE finale de cisaillement à≈10⁻⁶relatif. Le témoin haut0,12 ne se supprime pas sur le trajetγ0,15; cet échec d'attente reste enregistré. Un trajetγ0,35 pré-déclaré confirme la suppression au chargement supérieur. La réaction TH/NODE du binaire se comporte ici comme une impulsion: la comparaison à la quantité de mouvement et sa dérivée, après retrait de l'inertie imposée, étayent les plateaux; elle n'est pas lue directement comme une force.

Les premiers panneaux sont conservés:offset TYPE51 p1 échoue sur l'énergie de flexion; RBE2 p2 échoue sur le bilan de rotation. Le couplage TYPE2 p3 à offset physique0,25mm passe les quatre contrôles sans ajout de masse:

|Témoin p3|IE finale(J)|Résidu énergétique maximal(J)|Contrôle|
|---|---:|---:|---|
{paneltable}

La comparaison initiale brute àA19 échoue de0,00119582mm sur le CGx. La pièce A19 avait un centre natifx1053,83601mm, tandis que l'intégrale de l'aire triangulaire inchangée donne1048,265705615mm. Cœur et peaux A20 concordent avec cette intégrale. Le remplacement du seul moment du nez prédit le CG global avec une erreurx{mom['CG_prediction_error_mm'][0]:.9g}mm, sous le même seuil0,001mm. L'ancien contrôle échoué n'est pas écrasé et la cause exacte de son moment natif n'est pas établie; aucune modification de masse ou de position ne cherche à le reproduire.

À la fin du nouvel impact:IE cœur{r['final_core_IE_J']:.6f}J,peaux{r['final_skins_IE_J']:.6f}J,joints{r['final_cohesive_IE_J']:.6f}J. Énergie générée totale{r['final_generated_energy_J']:.6f}J;résidu final{r['final_energy_residual_J']:.6f}J. Minimum par élément peau sauvegardé{r['minimum_saved_skin_element_IE_J']:.6f}J, cœur échantillonné{r['minimum_sampled_core_element_IE_J']:.6f}J. Ruptures finales:{r['final_deleted_geometry']['deleted_skin_quads']}/1296peaux,{r['final_deleted_geometry']['deleted_core_bricks']}/648cœurs,{r['final_deleted_geometry']['deleted_cohesive_strips']}/624joints.

|Contrôle entier|Résultat|
|---|---|
{table}

La masse physique native initiale vaut{r['total_mass_kg']:.9f}kg. La somme du champ nodal d'animation diffère de{r['animation_mass_difference_kg']:.9f}kg après application des contraintes. Le détail Starter supplémentaire Ipri6 montre que la somme NODAL MASSES conserve les masses des secondaires de racine, déjà transportées vers les principaux RBE2. Après identification de ces {massproof['duplicated_root_dependent_mass_g']:.9f}g, le résidu de masse imprimée vaut {massproof['printed_balance_residual_g']:.9f}g. Le champ d'animation diffère encore de la somme imprimée de {massproof['float32_animation_sum_rounding_g']:.9f}g, dans sa précision float32. Ce champ n'est donc pas un total de masse matérielle. Les masses nodales individuelles subissent ensuite le transfert TYPE2: soustraire les secondaires animés courants serait injustifié. L'ancien contrôle brut est conservé; aucune correction de KE/impulsion ni RKE n'est ajoutée pour fermer le bilan. Plasticité maximale métal{r['maximum_metal_plastic_strain']:.6g},façade{r['maximum_facade_plastic_strain']:.6g},poutres{r['maximum_beam_plastic_strain']:.6g};seuil diagnostique0,1inchangé.

Le MP4/GIF ralentit{v['physical_duration_s']:.9f}s physiques en{v['display_duration_s']:.1f}s de lecture. Deux vues, déplacement×1, couleur du cœur et peaux distinctes, suppressions natives et horloge explicite. Encodage/décodage et inspection des images première/milieu/dernière vérifiés. Blender n'effectue aucune dynamique ni extrapolation; la lectureGUI n'est pas certifiée. Les10secondes demandées ne sont pas couvertes.

## 6. Contradictions et informations manquantes

Les contrôles locaux réussis n'effacent pas les défauts du modèle entier. Il manque les courbes après pic, effets de taux, énergie de fracture, décollement cœur-peau, qualification du transfert d'inertie aux racines, rupture ductile du métal, intérieur et qualification des fragments. La duplication initiale du champ de masse est expliquée, sans reconstruire une KE matérielle ou valider les inerties sphériques RBE2 en rotation. Le bilan doit passer avant prolongation. Les premiers axes et couplages échoués, ainsi que la comparaison parent-CG échouée, sont explicitement conservés. L'intégrité des fichiers est distincte de la qualification physique.

{nxt}
''',encoding='utf-8')
    HANDOFF.write_text(f'# Reprise AIRCRAFT-A20 → AIRCRAFT-A21\n\nRapport:{rel(REPORT)}. Résultats:{rel(D/"review.json")}. Vidéo:{rel(OUT/"video")}. Objectif10s incomplet.\n\n{nxt}\n',encoding='utf-8')
    scripts=list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a20*.py'));cfgs=list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a20*.json'))
    files=[p for p in OUT.rglob('*') if p.is_file()]+scripts+cfgs+[HANDOFF,ROOT/'wtc1_3d_v4/scripts/render_aircraft_a20.py']
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]});print({'prepared':True,'files':len(set(files))},flush=True)

def register():
    whole_guard();n=check_files(read(OUT/'artifact_manifest.json')['files']);assert harness()['CurrentIteration']=='AIRCRAFT-A19'
    st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert st['next_iteration']=='AIRCRAFT-A20';reg=ROOT/'harness/experiments/registry.jsonl';assert reg.read_bytes()==(OUT/'before_registry.jsonl').read_bytes()
    a=read(OUT/'scientific_assessment.json');v=read(OUT/'video/video_audit.json');r=read(D/'review.json');nxt=next_route(r);t=now()
    rec={'experiment_id':'WTC1-AIRCRAFT-A20','registered_at':t,'status':'completed_finite_3D_core_controls_and_fresh_whole20ms_MP4_GIF__failed_whole_gates_and_10s_goal_open',
        'configuration':rel(CFG),'whole_configuration':rel(WCFG),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a,'next_iteration':'AIRCRAFT-A21'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A20',next_iteration='AIRCRAFT-A21',current_status=rec['status'],next_objective=nxt,updated_at=t);st['aircraft_a20_key_results']=rec
    st['objective1_video_10s']={'requested_physical_duration_s':10,'current_native_whole_duration_s':v['physical_duration_s'],'status':'active_incomplete','interim_MP4':v['files'][0]['path'],'interim_GIF':v['files'][1]['path'],'route':rel(OUT/'objectif1_route.json'),'physical_goal_complete':False}
    st['validated_artifacts'].update(aircraft_a20_report=rel(REPORT),aircraft_a20_results=rel(OUT/'campaign_review.json'),aircraft_a20_handoff=rel(HANDOFF))
    assert 'AIRCRAFT-A20' not in cy['pending_iterations'];cy['pending_iterations'].append('AIRCRAFT-A20');cy.update(pending_count=len(cy['pending_iterations']),updated_at=t,next_publication_after='A14 throughA20 pending; explicit external publication authorization required for these files')
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(n)

def verify(n=None):
    whole_guard();n=n or check_files(read(OUT/'artifact_manifest.json')['files']);st=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cy=read(ROOT/'harness/publication_cycle.json');oc=read(OUT/'before_publication_cycle.json')
    prefix=(OUT/'before_registry.jsonl').read_bytes();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();h=harness();protected=[k for k in old if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'artifact_hashes':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'old_policies_results_preserved':all(st[k]==old[k] for k in protected),'single_registry_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A20',
        'route':st['current_iteration']=='AIRCRAFT-A20' and st['next_iteration']=='AIRCRAFT-A21','10s_goal_incomplete':not st['objective1_video_10s']['physical_goal_complete'],'harness_pass':h['Status']=='PASS','publication_pending_preserved':cy['pending_iterations']==oc['pending_iterations']+['AIRCRAFT-A20'] and cy['pending_count']==len(cy['pending_iterations']),
        'remote_baseline_unchanged':all(cy[k]==oc[k] for k in ['last_published_iteration','last_published_commit','last_published_release'])}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':n,'old_files_verified':read(OUT/'preservation_verification.json')['files'],'harness':h,'external_publication_performed':False,'physical_impact_qualified':False,'objective1_complete':False};assert proof['pass'];dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
