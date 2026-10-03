"""Close bounded I02I-C with explicit failed gates and a reusable handoff."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from run_impact_i02i_sampling import ROOT,CFG,OUT,B,NOW,dump,sha,rel,harness
SUMMARY=OUT/'verification_r2/summary.json'
REPORT=OUT/'rapport_impact_i02i_sampling.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_C_HANDOFF.md'
CADENCE=ROOT/'harness/publication_cycle.json'

def validated():
 s=json.loads(SUMMARY.read_text());cfg=json.loads(CFG.read_text());protected=json.loads((OUT/'preservation_before.json').read_text())
 assert sha(CFG)==s['config_sha256'] and len(s['controls'])==6 and len(s['cases'])==2
 assert all(v['checks']['three_jobs'] and v['checks']['preflight'] and v['checks']['normal_termination'] for v in s['controls'].values())
 assert all(v['gates']['three_completed_jobs'] and v['gates']['normal_termination'] and v['gates']['preflight_and_no_unreviewed_engine_warnings'] and v['gates']['fixed_penalty_verified'] and v['gates']['refined_domain_retained'] for v in s['cases'].values())
 assert not s['source_convention_verified'] and not s['physical_propagation_qualified']
 assert all(v['dense_output_covers_each_solver_step'] and v['cached_B_exact_timestamp_matches']['all_rows_matched'] for v in s['sampling'].values())
 failures=[r['path'] for r in protected['files'] if sha(ROOT/r['path'])!=r['sha256']];assert not failures,failures
 return s,cfg,protected

def prepare():
 s,cfg,protected=validated();assert not REPORT.exists() and not HANDOFF.exists(),'Never overwrite the report'
 controls=s['controls'];eng=s['cases']['ENG_DENSE_R1'];true=s['cases']['TRUE_DENSE_R1'];e=s['sampling']['ENG_DENSE_R1'];t=s['sampling']['TRUE_DENSE_R1'];ec=s['comparisons']['ENG_DENSE_R1'];tc=s['comparisons']['TRUE_DENSE_R1']
 sampling_rows=[]
 for label,v in [('ENG',e),('TRUE_TOTAL',t)]:
  sampling_rows.append(f"| {label} | Dense : {v['rows']} lignes | {100*v['spring_work_error_fraction']:.9g} % |")
  for dt,w in v['downsampled_same_trajectory'].items():sampling_rows.append(f"| {label} | {dt} ms : {w['rows']} lignes | {100*w['spring_work_error_fraction']:.9g} % |")
 control_rows=[]
 for label,v in controls.items():
  failed=', '.join(k for k,z in v['checks'].items() if not z) or 'aucun'
  control_rows.append(f"| {label} | {sum(v['checks'].values())}/{len(v['checks'])} | {v['work_diagnostic']['final_trapezoid_work_J']:.9g} | {failed} |")
 report=f'''# IMPACT-I02I-C — travail des connecteurs et échantillonnage

Huit calculs neufs : six connecteurs TYPE8 et deux répliques M(T) de B. C isole la fréquence d’enregistrement, sans changer géométrie, matériau, aire initiale, pénalités, Gf, vitesse, pas mécanique ou limites du domaine des éprouvettes. Les calculs B ne sont pas relancés. Coût des trois exécutables par cas : {s['runtime_seconds']:.3f} s ({s['runtime_seconds']/60:.3f} min), hors lecture des résultats, audit et empaquetage. Plafond pré-déclaré : 30 minutes de solveur.

**Résultat borné : l’écart entre travail trapézoïdal et IE des connecteurs est un effet de sous-échantillonnage sur les deux cas médians testés.** Les enregistrements denses abaissent cet écart sous 0,00001 %. Les mêmes trajectoires, sous-échantillonnées à 0,004 ms, reproduisent les écarts B. Ce résultat ne qualifie ni Gf comme propriété réelle, ni la propagation physique. C conserve {s['control_checks_passed']}/{s['control_checks_total']} critères scalaires, {s['case_checks_passed']}/{s['case_checks_total']} critères d’éprouvette et {s['comparison_checks_passed']}/{s['comparison_checks_total']} critères de comparaison B/C. Les échecs et non-évaluations sont conservés.

## 1. Faits observés ou transcrits

Il s’agit d’observations numériques, sans nouvelle observation du WTC. Les listings donnent QEPH Ishell24, Ismstr4, NPT5, ITHK1, IPLAS1 et Idril2 résolu par défaut. Le nombre de lignes denses égale le nombre de cycles moteur : {e['rows']} ENG et {t['rows']} TRUE_TOTAL. Les temps CSV ont sept chiffres significatifs : un incrément arrondi peut dépasser légèrement le pas mécanique. Le diagnostic R1 basé sur ce seul rapport était insuffisant ; R1 et son script sont conservés, R2 vérifie les cycles et les lignes. Il n’y a pas de nouveau calcul entre ces deux audits.

Toutes les lignes B retrouvent un temps exactement enregistré dans C. Les différences maximales sont documentées dans `cached_B_exact_timestamp_matches` : forces, travail externe, avance et CTOA. Ce contrôle distingue la trajectoire calculée de son observation plus ou moins fréquente.

Dans MIXED, OFF devient nul à 0,8145134 ms, avec FX=409,6267 N encore présent sur cette ligne ; FX est nul à la ligne suivante 0,8149292 ms. Le critère indépendant « FX=Kt·x tant qu’actif, zéro dès OFF=0 » échoue. Le décalage est conservé ; aucun filtrage ne transforme cet échec en réussite.

## 2. Résultats de modèles officiels et documentation primaire

Aucun nouveau résultat NIST ou modèle officiel de l’événement n’est importé. La source NASA et ses deux interprétations restent celles de B. La convention de la courbe n’est pas déterminée.

[TYPE8 Altair](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm) décrit les modes indépendants et les raideurs de décharge. [La documentation H2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stiffness_formulation_spring_hardening_r.htm) décrit un chargement sur fonction, une décharge linéaire et une plage sans force après son annulation en déplacement positif. [TH/SPRING](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm) fournit OFF, forces, allongements et énergie. Le contrôle utilise ces définitions ; elles ne calibrent pas une loi cohésive multiaxiale.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation des archives n’est évaluée. Les archives et copies de sources demeurent en lecture seule. Les documents NASA bornés et les manifests de B sont réutilisés ; la seule nouvelle copie documentaire est la page primaire H2, enregistrée avec URL, date et SHA-256 et exclue de la redistribution scientifique.

## 4. Hypothèses, propriétés, unités et références indépendantes

Unités solveur : g, mm, ms ; N, MPa=N/mm² ; énergie N·mm=mJ, conversion J=0,001 N·mm ; réaction nodale brute = impulsion N·ms. Force moyenne d’appui=ΔJ/Δt et travail d’appui=Σ(ΔJ/Δt)Δu. IE globale inclut déjà l’énergie des connecteurs : elle n’est pas additionnée une seconde fois.

Sur les éprouvettes : Kn=56000 et Kt=21500 N/mm³, aire initiale Ai fixe, kn=Kn·Ai et kt=Kt·Ai en N/mm. Traction maximale 495 MPa ; Gf=30 N/mm hypothétique. Maillage local 1,27 mm, domaine et arrêt sur capteurs inchangés. Les options explicites, la loi LAW36, les deux conversions de la courbe et les contrôles froids sont conservés. Aucun état endommagé n’est importé ni modifié.

Sur le connecteur isolé : aire 1 mm² ; masse de connecteur 0,2 g, inertie rotationnelle 0,001 g·mm² ; rotations et z bloqués, nœud1 fixe, x/y du nœud2 imposés. Ces inerties positives sont propres à ces nouveaux contrôles, sans modification des ressorts B. Aucun ajout automatique de masse. Déplacement lissé par quintique, 800 subdivisions par segment de 1 ms ; échelle mécanique 0,2, puis 0,1 pour les deux témoins de demi-pas.

δ0=495/56000={495/56000:.12g} mm ; δf=2·30/495={60/495:.12g} mm. Traction monotone : aire du triangle ½·495·δf=30 N·mm=0,03 J. Cisaillement seul : ½·21500·0,02²=4,3 N·mm=0,0043 J. Référence H2 positive : m=max historique de δ ; force sur enveloppe à m, puis F=max(0,F(m)+kn(δ−m)) sur décharge/recharge en dessous de m. Pas de compression testée. Le cycle 0→0,6δf→0,2δf→0,6δf→1,05δf conserve cet historique ; la boucle de retour ne rajoute pas de nouvelle aire à la traction finale.

Le cas mixte n’a pas de référence Gf multiaxiale calibrée : un travail tangent positif précède la désactivation. IE finale ne distingue pas automatiquement énergie encore stockable et énergie irréversiblement dissipée. Aucun bilan thermique ou incendie n’est déduit de cette IE.

## 5. Résultats dérivés et bilans

| Contrôle isolé | Critères réussis | Travail intégré final (J) | Échec |
|---|---:|---:|---|
{chr(10).join(control_rows)}

Les essais purs retrouvent 0,03 J normal et 0,0043 J tangent, avec une erreur de quadrature inférieure à 0,0001 %. La décharge H2 retrouve sa plage sans force ; le demi-pas conserve le résultat. MIXED conserve 0,03390335 J dans IE et le travail, tout en échouant au critère de force au passage OFF. Tous les bilans scalaires globaux, masses et travaux des appuis passent leurs seuils pré-déclarés.

Quadrature indépendante : Σ½(Fᵢ+Fᵢ₋₁)·(uᵢ−uᵢ₋₁), deux composantes, convertie en J. Écart maximum rapporté au maximum de |ΣIE ressorts|. Sous-échantillonnage : premier état, première ligne à/après chaque cible temporelle uniforme, dernier état ; aucun événement de rupture ajouté spécialement.

| Branche | Enregistrement de la même trajectoire | Erreur maximum de travail |
|---|---|---:|
{chr(10).join(sampling_rows)}

L’ENG dense réduit l’écart B de {100*e['cached_B_error_fraction']:.6g} % à {100*e['spring_work_error_fraction']:.9g} %. TRUE_TOTAL passe de {100*t['cached_B_error_fraction']:.6g} % à {100*t['spring_work_error_fraction']:.9g} %. Les autres maillages B ne sont pas réexécutés : le maximum 3,04655 % de la campagne entière n’est pas directement résolu cas par cas dans C.

ENG : travail externe final {eng['metrics']['final_external_work_J']:.8g} J, travail d’appui indépendant {eng['metrics']['final_actuator_work_J']:.10g} J, erreur d’énergie globale {100*eng['metrics']['energy_residual_fraction']:.6g} %, max KE/IE={100*eng['metrics']['maximum_kinetic_to_internal_significant_window']:.6g} % dans la fenêtre IE≥1 % du pic. Le seuil inertiel 1 % échoue. TRUE_TOTAL : travail externe {true['metrics']['final_external_work_J']:.8g} J, travail indépendant {true['metrics']['final_actuator_work_J']:.10g} J, erreur d’énergie {100*true['metrics']['energy_residual_fraction']:.6g} %, max KE/IE={100*true['metrics']['maximum_kinetic_to_internal_significant_window']:.6g} %, seuil inertiel réussi. Masse nominale 146,16684 g ; écart maximum relatif {100*eng['metrics']['mass_error_fraction']:.6g} %. Les impulsions signées des deux appuis sont comparées à PY, séparément du travail et de la force de section.

B/C aux déplacements communs : ENG {ec['coverage']['displacement_points_assessed']}/16 points, dont {ec['coverage']['displacement_points_after_first_complete_separation_in_both']} après première séparation dans les deux historiques ; TRUE_TOTAL {tc['coverage']['displacement_points_assessed']}/16, dont {tc['coverage']['displacement_points_after_first_complete_separation_in_both']}. Pas d’extrapolation après l’arrêt ENG. Différence maximale de force normalisée par pic : ENG {100*ec['maximum_force_difference_fraction']:.6g} %, TRUE_TOTAL {100*tc['maximum_force_difference_fraction']:.6g} %. Les trajectoires aux mêmes temps sont comparées séparément : la différence due à interpolation/échantillonnage n’est pas une nouvelle sensibilité matérielle.

Avances nodales communes 2,54/5,08/7,62 mm : ENG 3/3 disponibles, mais différence CTOA maximale B/C {100*ec['maximum_ctoa_difference_fraction']:.6g} % > seuil10 %. L’événement dense et le premier événement enregistré grossièrement ne sont pas au même instant. TRUE_TOTAL 1/3 seulement ; 5,08 et 7,62 mm ne sont pas atteints par ce calcul borné. Les états de fissure ne sont pas interpolés pour inventer les deux valeurs absentes.

## 6. Contradictions, manques et étape suivante

L’énergie de connecteurs pure normale est vérifiée numériquement sur cette loi et ces cas ; ce n’est pas une identification de Gf réel. Le statut/force tangent à la désactivation mixte, la distinction stockage/dissipation, l’inertie ENG, la couverture des avances et la convergence des angles restent ouverts. Les maxima plastiques portent uniquement sur les coques sélectionnées ; ils ne bornent pas toute l’éprouvette. La source reste indéterminée et aucune propagation physique avion/façade n’est qualifiée.

I02I-D : partir de ces sorties sauvegardées. Clarifier le décalage OFF/FX par une étude ciblée de l’algorithme TYPE8 ou de nouveaux témoins mixtes pré-déclarés ; séparer le travail normal, le travail tangent et le statut. Pour les éprouvettes, annoncer une campagne bornée de vitesse/pénalité/domaine avec histories denses avant Gf15/60 ; comparer forces/travaux à déplacements communs et angles à événements définis précisément. Une extension du domaine doit être un nouvel état et ne doit pas prolonger un coupon déjà endommagé. Pas de reprise de V11F ou V11R pour relecture.

La localisation en flexion après fracture complète demeure non validée. Température imposée ≠ incendie calculé. Succès numérique ≠ validation de l’effondrement historique. Blender reste visualisation. Source NASA et résultats NIST, lorsqu’ils servent d’entrée, ne deviennent pas observations indépendantes.

## Reproduction et artefacts

Configuration : `{rel(CFG)}` ; seed1102011, aucun tirage aléatoire. Scripts run/audit/complete `impact_i02i_sampling.py` ; les dépendances B sont épinglées par SHA-256. OpenRadioss win64 v20260728, /VERS2026, un thread ; exécutables épinglés dans chaque execution.json. Python/NumPy et durées dans summary.json. Les decks, sorties brutes T01/CSV/listings, préflights, journaux, génération, bilans, diagnostics R1 et audit R2 sont conservés.

Les scripts de génération de B sont réutilisés en lecture seule ; leurs anciens champs config/générateur sont conservés dans `predecessor_metadata_hashes`, et les empreintes C sont ajoutées explicitement. Aucune animation, GPU ou branche thermique exécutée. Les {len(protected['files'])} fichiers précédemment épinglés sont vérifiés avant/après ; aucun scan intégral de l’archive.

La vérification d’intégrité `publication_verification.json` contrôle les octets, registre et état, sans relancer de solveur. La cadence GitHub conserve B+C en attente jusqu’à confirmation distante du commit, des archives et du contrôle CI ; cette intégrité ne transforme pas les critères scientifiques échoués en réussite.
'''
 REPORT.write_text(report,encoding='utf-8',newline='\n')
 handoff=f'''# WTC1 — IMPACT-I02I-C terminée, prochaine I02I-D

Lire AGENTS.md, harness/state.json, cette passation, puis `{rel(OUT/'publication_verification.json')}`. L’état local fait autorité. V8H/V11H sont historiques ; V11F froid et V11R → V11S sont préservés.

## À réutiliser

C : six connecteurs TYPE8 neufs et deux éprouvettes médianes ENG/TRUE_TOTAL neuves, identiques à B sauf fréquence TH. {s['runtime_seconds']/60:.3f} min de calcul. Rapport `{rel(REPORT)}`, résultats `{rel(SUMMARY)}`, config `{rel(CFG)}`. {s['control_checks_passed']}/{s['control_checks_total']} contrôles scalaires ; {s['case_checks_passed']}/{s['case_checks_total']} critères éprouvettes ; {s['comparison_checks_passed']}/{s['comparison_checks_total']} comparaisons B/C. Les échecs restent des échecs.

Travail de ressorts : dense ENG {100*e['spring_work_error_fraction']:.9g} %, TRUE_TOTAL {100*t['spring_work_error_fraction']:.9g} % d’erreur ; sous-échantillonner les mêmes lignes à 0,004 ms reproduit B ({100*e['cached_B_error_fraction']:.6g}/{100*t['cached_B_error_fraction']:.6g} %). {e['rows']}/{t['rows']} lignes = cycles moteur ; toutes les lignes B correspondent à des temps denses. R1 et script conservés ; R2 corrige le diagnostic de cadence basé sur les incréments CSV arrondis. Aucun solveur relancé pour cette correction.

Références : normale 0,03 J, cisaillement0,0043 J, cycle H2 conserve l’historique et retrouve la plage sans force ; demi-pas concordant. MIXED : OFF nul une ligne avant FX nul, critère de force échoué, travail/IE ≈0,03390335 J ; ne pas assimiler l’énergie tangentielle à une dissipation calibrée.

ENG conserve max KE/IE={100*eng['metrics']['maximum_kinetic_to_internal_significant_window']:.6g} % >1 %, CTOA B/C jusqu’à {100*ec['maximum_ctoa_difference_fraction']:.6g} % aux premières observations d’un même niveau d’avance. TRUE_TOTAL n’atteint que 2,54 mm parmi les avances2,54/5,08/7,62 ; les deux absences restent non évaluées. Kn56000/Kt21500 N/mm³, Gf30 hypothétique, deux conventions séparées, QEPH explicite et aire initiale fixe. Source et propagation physique non qualifiées.

## I02I-D

Analyser OFF/FX et stockage/dissipation en mixte ; pré-déclarer des témoins supplémentaires ou une lecture ciblée du code primaire TYPE8. Pré-déclarer une extension bornée vitesse/pénalité/domaine à états neufs et histoires denses avant Gf15/60. Garder comparaisons à déplacements communs et événements de fissure précisément définis ; ne pas interpoler une topologie absente. Préserver V11F/V11R et les anciens résultats. Ne pas relancer B/C pour une relecture ; réanalyse CSV uniquement dans un nouveau dossier si nécessaire.

## GitHub et contrôles

`harness/publication_cycle.json` fait autorité : après C la paire B+C est due. La publication est autorisée toutes les deux itérations ; confirmer commit distant, empreintes d’archives et CI avant d’effacer l’attente. L’authentification doit être WTC-simu2026, identité Git pseudonyme. Aucun post X autorisé. Préparation privée : outputs/github_publication/update_i02i_bc.py, réutiliser son plan sauvegardé. Ne jamais reconstruire les 23 archives A ni publier le dossier privé d’administration.

`harness/tools/Test-WtcHarness.ps1`, puis `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_sampling.py --verify` : aucun solveur. Archives/sources en lecture seule ; {len(protected['files'])} fichiers anciens épinglés. Température imposée ≠ incendie, coupon ≠ événement réel, flexion après fracture complète non validée, Blender visualisation.
'''
 HANDOFF.write_text(handoff,encoding='utf-8',newline='\n')
 audit={'created_utc':NOW(),'pass':True,'valid_completed_cases':8,'old_files_preserved':len(protected['files']),'config_sha256':sha(CFG),'summary_sha256':sha(SUMMARY),'report_sha256':sha(REPORT),'handoff_sha256':sha(HANDOFF),'scientific_all_gates_pass':False,'failed_gates_retained':True,'source_convention_verified':False,'physical_propagation_qualified':False,'definition':'Integrity and bounded experiment completion; no scientific gate promotion'}
 dump(OUT/'release_audit.json',audit);dump(OUT/'harness_after_artifacts.json',harness())

def manifest():
 paths=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json','publication_verification.json']]
 paths+=[CFG,HANDOFF]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*impact_i02i_sampling.py'))
 dump(OUT/'artifact_manifest.json',{'created_utc':NOW(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(paths))],'exclusions':['self','post-registration publication_verification.json','mutable harness state/registry/cadence checked separately'],'scope':'All C fresh cases, both read-only audits, rejected gates, references, configuration, scripts, report and handoff'})

def register():
 s,cfg,protected=validated();assert REPORT.exists() and HANDOFF.exists() and json.loads((OUT/'release_audit.json').read_text())['pass']
 statepath=ROOT/'harness/state.json';reg=ROOT/'harness/experiments/registry.jsonl'
 for p,backup in [(statepath,'before_state.json'),(reg,'before_registry.jsonl'),(CADENCE,'before_publication_cycle.json')]:assert sha(p)==sha(OUT/backup),'Concurrent harness change'
 state=json.loads(statepath.read_text());assert state['current_iteration']=='IMPACT-I02I-B' and state['next_iteration']=='IMPACT-I02I-C';cadence=json.loads(CADENCE.read_text());assert cadence['pending_iterations']==['IMPACT-I02I-B']
 manifest();when=NOW();status='completed_bounded_sampling_diagnostic_with_failed_or_unassessed_qualification_gates'
 record={'experiment_id':'WTC1-IMPACT-I02I-C','registered_at':when,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(SUMMARY),'handoff':rel(HANDOFF),'source_manifest':rel(OUT/'source_manifest.json'),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'release_audit':rel(OUT/'release_audit.json'),'publication_verification':rel(OUT/'publication_verification.json'),'cases':8,'control_checks_passed':s['control_checks_passed'],'control_checks_total':s['control_checks_total'],'case_checks_passed':s['case_checks_passed'],'case_checks_total':s['case_checks_total'],'comparison_checks_passed':s['comparison_checks_passed'],'comparison_checks_total':s['comparison_checks_total'],'old_files_preserved':len(protected['files']),'source_convention_verified':False,'physical_propagation_qualified':False,'next_iteration':'IMPACT-I02I-D','github_pending_iterations':2,'caveat':'Sampling resolved on two median coupons only. Mixed OFF/FX transition, inertia ENG, event observation bias and missing advances retained.'}
 prefix=reg.read_bytes();assert prefix.endswith(b'\n')
 with reg.open('ab') as f:f.write((json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'))
 state.update(updated_at=when,current_iteration='IMPACT-I02I-C',current_status=status,next_iteration='IMPACT-I02I-D',next_objective='Réutiliser C sauvegardée : clarifier OFF/FX et stockage/dissipation en mixte ; pré-déclarer étude bornée vitesse/pénalité/domaine à états neufs et historiques denses avant Gf15/60. Inertie ENG, angles et avances absentes non qualifiés. Conserver deux conventions, QEPH, aire initiale fixe, impulsions et travail des appuis. La paire B+C est due sur GitHub : confirmer commit, archives et CI avant remise à zéro de la cadence. V11F et V11R/V11S préservés.')
 state['impact_i02i_c_key_results']={k:record[k] for k in ['cases','control_checks_passed','control_checks_total','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','old_files_preserved','source_convention_verified','physical_propagation_qualified']}
 state['impact_i02i_c_key_results'].update(runtime_seconds=s['runtime_seconds'],maximum_dense_connector_work_error_fraction=max(v['spring_work_error_fraction'] for v in s['sampling'].values()),dense_work_sampling_verified_on_two_median_coupons=s['all_dense_work_gates_pass'],all_controls_pass=s['all_controls_pass'],mixed_OFF_FX_gate_pass=False,ENG_inertia_gate_pass=False,cold_V11F_preserved=True,thermal_V11R_preserved=True,github_pending_iterations=2)
 state['validated_artifacts'].update(latest_sampling_configuration=rel(CFG),latest_sampling_report=rel(REPORT),latest_sampling_summary=rel(SUMMARY),latest_sampling_handoff=rel(HANDOFF),latest_sampling_publication_verification=rel(OUT/'publication_verification.json'))
 state['open_limitations'].append('I02I-C: dense output resolves connector quadrature on two median coupons; mixed OFF/FX one-row transition, recoverable versus dissipated work, ENG inertia and common-event angle coverage remain unqualified. No physical fracture or real collapse validation.')
 cadence.update(pending_iterations=['IMPACT-I02I-B','IMPACT-I02I-C'],pending_count=2,next_publication_after='Due now: B+C audited; remote commit/assets/CI and anonymous owner login required before clearing pending pair',updated_at=when)
 dump(CADENCE,cadence);temp=ROOT/'harness/state_i02ic_pending.json';dump(temp,state);temp.replace(statepath)
 print(json.dumps(verify(write=True),indent=2))

def verify(write=False):
 s,cfg,protected=validated();ma=json.loads((OUT/'artifact_manifest.json').read_text());fails=[r['path'] for r in ma['files'] if sha(ROOT/r['path'])!=r['sha256']]
 state=json.loads((ROOT/'harness/state.json').read_text());old=json.loads((OUT/'before_state.json').read_text());reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();extra=reg[len(prefix):].decode().splitlines();cadence=json.loads(CADENCE.read_text());hv=harness()
 prior=['v11f_key_results','v11r_key_results','deferred_thermal_branch','impact_i02h_key_results','impact_i02i_a_key_results','impact_i02i_b_key_results','source_archive','evidence_policy']
 checks={'all_new_artifact_hashes':not fails,'old_pinned_files_preserved':True,'registry_prefix_preserved':reg.startswith(prefix),'exactly_one_C_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-C','correct_state':state['current_iteration']=='IMPACT-I02I-C' and state['next_iteration']=='IMPACT-I02I-D','prior_cold_thermal_and_impact_state_preserved':all(state[k]==old[k] for k in prior),'harness_pass':hv['Status']=='PASS','report_and_handoff_present':REPORT.exists() and HANDOFF.exists(),'bounded_claims':not s['source_convention_verified'] and not s['physical_propagation_qualified'],'sampling_diagnostic_verified':s['all_dense_work_gates_pass'],'failed_qualification_gates_retained':not s['all_controls_pass'] and not s['cases']['ENG_DENSE_R1']['gates']['inertia_significant_window'],'cadence_pair_pending_or_verified_published':cadence['pending_iterations']==['IMPACT-I02I-B','IMPACT-I02I-C'] or cadence['last_published_iteration']=='IMPACT-I02I-C'}
 result={'created_utc':NOW(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(ma['files']),'manifest_failures':fails,'prior_files_checked':len(protected['files']),'harness':hv,'scientific_control_checks':f"{s['control_checks_passed']}/{s['control_checks_total']}",'scientific_case_checks':f"{s['case_checks_passed']}/{s['case_checks_total']}",'scientific_comparison_checks':f"{s['comparison_checks_passed']}/{s['comparison_checks_total']}",'scientific_all_gates_pass':False,'source_convention_verified':False,'physical_propagation_qualified':False,'next_iteration':'IMPACT-I02I-D','github_remote_publication_confirmed':cadence['last_published_iteration']=='IMPACT-I02I-C'}
 if write:dump(OUT/'publication_verification.json',result)
 assert result['pass'],result;return result

if __name__=='__main__':
 p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group(required=True);group.add_argument('--prepare',action='store_true');group.add_argument('--register',action='store_true');group.add_argument('--verify',action='store_true');a=p.parse_args()
 if a.prepare:prepare()
 elif a.register:register()
 else:print(json.dumps(verify(),indent=2))
