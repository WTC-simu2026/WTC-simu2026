"""Close a bounded diagnostic campaign; integrity is separate from scientific convergence."""
from __future__ import annotations
import argparse, json, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy
from run_impact_i02i_fixed_penalty import ROOT,CFG,OUTPUT,dump,sha

SUMMARY=OUTPUT/'verification_r1/summary.json'
REPORT=OUTPUT/'rapport_impact_i02i_fixed_penalty.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_B_HANDOFF.md'
CADENCE=ROOT/'harness/publication_cycle.json'
NOW=lambda:datetime.now(timezone.utc).isoformat()
def rel(p): return Path(p).relative_to(ROOT).as_posix()


def harness():
    process=subprocess.run(['pwsh.exe','-NoProfile','-Command',"& './harness/tools/Test-WtcHarness.ps1' | ConvertTo-Json -Depth 8"],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert process.returncode==0,process.stderr
    result=json.loads(process.stdout); assert result['Status']=='PASS',result
    return result


def validated():
    s=json.loads(SUMMARY.read_text()); cfg=json.loads(CFG.read_text()); protected=json.loads((OUTPUT/'preservation_before.json').read_text())
    assert s['control_pass'] and json.loads((OUTPUT/'reference_checks.json').read_text())['pass']
    assert len(s['cases'])==len(cfg['cases'])==12
    assert all(r['gates']['three_completed_jobs'] and r['gates']['normal_termination'] and r['gates']['preflight_and_no_unreviewed_engine_warnings'] and r['gates']['fixed_penalty_verified'] and r['gates']['refined_domain_retained'] for r in s['cases'].values())
    assert not s['source_convention_verified'] and not s['physical_propagation_qualified']
    assert sha(CFG)==s['config_sha256']
    failures=[r['path'] for r in protected['files'] if sha(ROOT/r['path'])!=r['sha256']]; assert not failures,failures
    return s,cfg,protected


def prepare():
    s,cfg,protected=validated(); assert not REPORT.exists() and not HANDOFF.exists()
    rows=[]
    for name,r in s['cases'].items():
        m=r['metrics']; fail=', '.join(k for k,v in r['gates'].items() if not v) or 'aucun'
        rows.append(f"| {name} | {m['peak_section_force_N']/1000:.4f} | {r['final_state']['displacement_mm']:.5f} | {m['maximum_area_advance_mm']:.4f} | {m['final_external_work_J']:.6f} | {100*m['maximum_kinetic_to_internal_significant_window']:.4f} % | {fail} |")
    comps=[]
    for name,c in s['comparisons'].items():
        def fmt(v): return 'non évalué' if v is None else f'{100*v:.4f} %'
        covered=sum(p['assessed'] for p in c['common_advances']); fail=', '.join(k for k,v in c['checks'].items() if not v) or 'aucun'
        coverage=c['coverage']; comps.append(f"| {name} | {fmt(c['maximum_force_difference_fraction'])} | {fmt(c['maximum_work_difference_fraction'])} | {fmt(c['maximum_ctoa_difference_fraction'])} | {coverage['displacement_points_assessed']}/5 ({coverage['displacement_points_after_first_complete_separation_in_both']} après rupture) | {covered}/3 | {fail} |")
    extrapolated=[k for k,r in s['cases'].items() if r['source_constitutive_domain_exceeded_in_sampled_tip_shells']]
    eng_coarse=s['cases']['ENG_L254_R3']['final_state']; true_coarse=s['cases']['TRUE_L254_R3']['final_state']
    max_spring_quadrature=max(r['metrics']['spring_work_quadrature_error_fraction'] for r in s['cases'].values())
    max_energy=max(r['metrics']['energy_residual_fraction'] for r in s['cases'].values())
    max_actuator=max(r['metrics']['independent_actuator_work_error_fraction'] for r in s['cases'].values())
    failures={k:[g for g,v in r['gates'].items() if not v] for k,r in s['cases'].items() if not r['all_case_gates_pass']}
    checks=sum(sum(r['gates'].values()) for r in s['cases'].values()); total=s['case_checks_total']
    controls=json.loads((OUTPUT/'control_checks.json').read_text()); sensor=s['sensor']
    hcfg=ROOT/'wtc1_simulation_v8/data/impact_i02h_local_cohesive.json'
    hc=json.loads(hcfg.read_text()); geometry_source=hc['sources'][0]
    assert sha(ROOT/geometry_source['path'])==geometry_source['sha256']
    dump(OUTPUT/'source_provenance_supplement.json',{'created_utc':NOW(),'geometry_inherited_from':{'path':rel(hcfg),'sha256':sha(hcfg),'geometry':hc['geometry'],'mesh':hc['mesh']},'geometry_primary_source':geometry_source,'use':'Reuse already saved bounded geometry; no new PDF inspection, no stable-tearing physical comparator used here.','material_source_manifest':rel(ROOT/'wtc1_simulation_v8/output/impact_i02i_material/source_manifest.json'),'existing_new_docs_manifest':rel(OUTPUT/'source_manifest.json')})
    report=f'''# IMPACT-I02I-B : éprouvette à raideurs cohésives fixes

Date : {NOW()}. Campagne bornée terminée et auditée. La qualification de propagation physique reste ouverte ; les critères échoués ou non évalués sont conservés. Cette étape suit IMPACT-I02I-A. Contrôle froid V11F et branche thermique V11R → V11S préservés. Aucun calcul historique relancé.

## 1. Faits directement observés ou transcrits

Douze essais neufs ont terminé normalement. Les contrôles élastiques passent 28/28 critères, avec 5/5 contrôles de campagne et un test de capteur. Ensemble : {checks}/{total} critères de cas ; comparaisons : {s['comparison_checks_passed']}/{s['comparison_checks_total']}. Ces totaux ne sont pas une validation de l'événement réel. {len(protected['files'])} anciens fichiers épinglés ont été vérifiés inchangés, sans rescanner les archives.

Le test de capteur s'arrête à t={sensor['end_ms']:.6f} ms, distance={sensor['end_distance_mm']:.8f} mm, pour un seuil 10,01 mm et une fin demandée 4,4 ms. Son historique est clôturé et converti. Les éprouvettes fissurantes emploient le même mécanisme d'arrêt, aux deux limites x=±22,86 mm ; il arrête réellement le moteur si la distance des nœuds de couture atteint 0,8 δf. Il ne s'agit pas d'un recadrage des résultats.

## 2. Sources primaires et résultats de modèles officiels

Les données matériau et leurs deux conversions réutilisent exclusivement le manifeste borné de [I02I-A](../impact_i02i_material/rapport_impact_i02i_material.md), fondé sur les pages 178–182 et 196 du [document NASA STAGS](https://ntrs.nasa.gov/api/citations/20060008654/downloads/20060008654.pdf). La convention nominale/vraie et la contradiction décimale restent ouvertes. Aucune nouvelle lecture globale de ce PDF, aucune donnée Boeing nouvellement identifiée, aucun résultat de modèle officiel du WTC.

La géométrie est reprise de la configuration I02H et de sa source NASA CR-191523 sauvegardée, dont l'empreinte est revérifiée dans `source_provenance_supplement.json`. La liste initiale de sources B décrivait le matériau et les nouvelles cartes ; ce supplément rend explicite l'origine distincte de la géométrie, sans nouvelle inspection du PDF ni utilisation de ses comparateurs de déchirure stable.

Les pages primaires [TYPE8](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm), [historiques de ressort](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm), [capteur de distance](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/sensor_dist_starter_r.htm) et [arrêt par capteur](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stop_lsensor_engine_r.htm) ont été consultées et sauvegardées. TYPE8 décrit des modes indépendants et des options d'écrouissage ; H=2 est ici conservé. La carte n'est pas une loi cohésive mixte calibrée, et l'intégrale triangulaire en ouverture monotone ne suffit pas à prouver sa dissipation lors de retours ou de glissement.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation issue de vidéo, photographie ou archive n'est ajoutée. L'identification d'un mécanisme historique, l'applicabilité aux composants d'un avion et la chaîne d'effondrement ne sont pas déduites de ces essais numériques.

## 4. Hypothèses propres au modèle, propriétés et unités

Éprouvette générique plane 76,2 × 300 × 2,3 mm ; fissure centrale initiale de longueur totale 25,4 mm. E=71 400 MPa, ν=0,3, ρ=0,00278 g/mm³, masse initiale {cfg['geometry']['width_mm']*cfg['geometry']['length_mm']*cfg['geometry']['thickness_mm']*cfg['material']['density_g_per_mm3']:.6f} g. QEPH : Ishell24, Ismstr4, Ithick1, Iplas1, N5 ; états initiaux neufs, sans remplacement de matériau ni de son historique. Aucun calcul thermique. Options homogènes vérifiées en A ; leur usage près d'une fissure reste à évaluer.

Unités : g–mm–ms ; N ; MPa=N/mm² ; énergie brute N·mm, convertie par 0,001 en J ; impulsion N·ms. Interprétation ENG : e=ln(1+εsource), σ=σsource(1+εsource), p=max(0,e−σ/E). Interprétation TRUE : e=εsource, σ=σsource, p=max(0,e−σ/E). Cinq points source inchangés ; clipping du premier p et prolongement constant final explicités dans chaque `conversion_ledger`. La source n'est pas choisie comme une vérité mesurée.

Kn=56 000 N/mm³ et Kt=21 500 N/mm³, indépendants du pas et de la branche matériau. Le connecteur i reçoit ki=K Ai en N/mm, Ai=2,3 mm × largeur tributaire initiale. Cette aire reste fixe lorsque la coque s'amincit : il s'agit d'une loi définie sur l'aire de référence, pas d'une traction recalculée sur l'aire courante. Ces pénalités sont des choix numériques. Pic normal 495 MPa, Gf=30 N/mm hypothétique, δ0=495/56000={495/56000:.12f} mm, δf=60/495={60/495:.12f} mm. L'intégrale d'une charge normale monotone jusqu'à δf vaut Gf Ai ; somme sur le ligament entier : 3,5052 J. Dix vérifications indépendantes de partition, dimensions et invariance de δ0 passent, sans lancer le solveur des jeux de référence.

Pas locaux h=2,54 ; 1,27 ; 0,635 mm, même domaine raffiné et même éloignement des mors. Géométrie hors zone raffinée héritée d'I02H. Ressorts sans masse de translation ; inertie de rotation 10⁻²⁰ g·mm², égale au remplacement du solveur, rotations contraintes. Le précontrôle accepte uniquement l'avertissement 445 « NULL INERTIA » attendu une fois par ressort et documenté ; tout autre avertissement ou erreur bloque le moteur. R1 et R2 rejetés avant moteur restent sauvegardés. Le contrôle de masse vérifie ensuite l'absence d'ajout de masse.

Mors inférieur fixe y ; mors supérieur déplacé y ; un nœud supprime la translation x, z et rotations bloqués. Charge quintique u=u_max(10s³−15s⁴+6s⁵), 800 subdivisions ; contrôles 0,02 mm en 6/12 ms ; autres essais 1,2 mm en 12 ms, témoin lent 24 ms. Facteur de pas 0,9 et témoin 0,45, sans mass scaling, un thread CPU. Historiques demandés tous les 0,004 ms, multipliés par le facteur de durée ; temps réellement émis enregistrés. Aucun amortissement ajouté, aucune animation Blender.

Arrêt de domaine : ouverture-distance aux nœuds x=±22,86 mm. Distance euclidienne inclut le glissement et peut déclencher plus tôt que le seuil en ouverture normale. Le contrôle est discret au pas moteur ; les distances finales peuvent dépasser légèrement le seuil d'activation, leurs maxima sont sauvegardés. L'avance maximale admissible par côté est 10,16 mm ; les connecteurs de garde doivent rester actifs. Un arrêt de domaine borne l'essai numérique et n'est pas un arrêt physique de fissure.

## 5. Résultats dérivés, réactions, énergies et comparaisons

Le fichier brut sans titres contient REACY cumulatif J(t), confirmé par les deux durées élastiques : ratio d'impulsion {s['duration_impulse_ratio']:.8f}, écart de travail {100*s['duration_work_difference_fraction']:.6f} %. Force moyenne d'intervalle = ΔJ/Δt ; travail indépendant des mors = Σn,i(ΔJn/Δt) Δun × 0,001 J. Les déplacements du mors inférieur sont nuls. Les forces d'intervalle et incréments de travail sont sauvegardés, sans traiter J comme une force instantanée.

Bilan global contrôlé : Wext−IE−KE, normalisé par le pic énergétique propre. IE inclut déjà les ressorts ; leur énergie n'est pas ajoutée une deuxième fois. Somme des IE des ressorts confrontée au canal global SPRING ENERGY, puis quadrature Σ½(Fi+Fi-1)ΔLi sur les composantes x/y enregistrée comme diagnostic distinct. Elle n'est pas assimilée d'office à une énergie de fracture. Impulsions signées des deux mors confrontées au quantité de mouvement globale PY ; résidu absolu et résidu divisé par l'impulsion maximale d'un mors sont tous deux conservés. Cette normalisation ne mesure pas une petite erreur relative sur le quantité de mouvement nette lorsque les réactions se compensent.

Le rapport d'inertie KE/IE utilise toute la fenêtre IE≥1 % de son pic, y compris les pointes de fracture. Critère ≤1 %. Bilan global ≤0,5 %, travail indépendant ≤1 %, masse ≤10⁻⁵ ; critères complets dans la configuration, sans ajustement après calcul.

Écarts maximaux : bilan global {100*max_energy:.6f} %, travail indépendant des appuis {100*max_actuator:.6f} %. La quadrature du travail des ressorts diffère jusqu'à {100*max_spring_quadrature:.6f} % de leur IE enregistrée, tandis que la somme des IE rejoint son canal global. Ce diagnostic n'avait pas de critère de réussite pré-déclaré ; il doit être résolu ou borné avant de qualifier Gf comme une énergie dissipée effective. Une sortie plus fine, les sauts de désactivation et la définition de IE sous H=2 sont des pistes à vérifier, pas une cause déjà démontrée.

| Cas | pic de force de section kN | u final mm | avance maximale par côté mm | Wext final J | max KE/IE fenêtre | critères échoués |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

La force de section est ΣFY des ressorts ; la contrainte nominale associée emploie l'aire initiale 76,2×2,3 mm². Elle est distincte de la réaction moyenne des mors pendant les transitoires.

À u=1,2 mm dans les deux cas grossiers, l'avance d'aire moyenne est {eng_coarse['area_advance_mm']:.4f} mm en ENG contre {true_coarse['area_advance_mm']:.4f} mm en TRUE. Cette différence illustre la sensibilité couplée à la convention source, dans ces cas neufs identiquement discrétisés ; elle n'identifie pas la bonne convention ni un mécanisme historique. Les cas arrêtés avant 1,2 mm ne sont pas extrapolés pour produire cette comparaison.

Deux proxys d'avance restent distincts : somme des largeurs tributaires rompues contiguës (première cellule h/2), et dernier nœud rompu contigu moins la pointe initiale (première rupture : 0). Les angles CTOA sont des indicateurs géométriques calculés derrière la pointe issue du proxy d'aire, à distances B=2,3 mm et 2B ; ils ne constituent pas un critère matériau identifié.

Comparaisons à u=0,2 ; 0,5 ; 0,8 ; 1 ; 1,2 mm dans le recouvrement réel seulement. Forces/travail interpolés en u ; aucun prolongement hors domaine. Comparaisons CTOA aux avances nodales exactes 2,54 ; 5,08 ; 7,62 mm, lorsque les deux côtés atteignent cette valeur dans un événement sauvegardé. Un saut qui omet une valeur ou un arrêt avant celle-ci donne « non évalué », jamais « réussi ». L'indicateur d'aire diffère de h/2 à avance nodale identique ; cette incertitude de localisation est conservée. Les différences de force sont divisées par le pic commun, celles de travail par le maximum des travaux finaux et celles d'angle par la valeur maximale des deux angles.

| Comparaison | max Δforce / pic | max Δtravail / échelle | max ΔCTOA relatif | déplacements évalués (après rupture) | avances exactes évaluées | critères échoués / non évalués |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(comps)}

Les critères force/travail se limitent aux points réellement évalués ; leur réussite ne vaut pas une couverture de tous les déplacements demandés. Lorsque les arrêts précèdent les premiers déplacements communs après séparation complète, ces critères décrivent essentiellement l'état avant propagation. Le nombre de points après rupture est explicité pour empêcher une promotion indue en convergence de propagation.

## 6. Contradictions, informations manquantes et suite

Critères de cas non satisfaits : `{json.dumps(failures,ensure_ascii=False)}`. Tous les essais restent conservés. Critères de comparaison entièrement satisfaits : {sum(c['all_comparison_checks_pass'] for c in s['comparisons'].values())}/{len(s['comparisons'])}. Une comparaison partielle ou non évaluée n'est pas déclarée convergée.

Le dépassement KE/IE retire le crédit quasi statique déclaré pour ces cas ; il ne démontre pas à lui seul une erreur du solveur. Le demi-pas satisfait les quatre critères de comparaison temporelle dans le recouvrement disponible, mais le cas reste au-dessus du seuil d'inertie. La durée doublée ne supprime pas ce dépassement et échoue au critère d'angle. Aucune qualification complète de propagation n'en est tirée.

Cas dépassant le dernier point source de déformation plastique dans les coques échantillonnées près des pointes : `{json.dumps(extrapolated)}`. {'Le prolongement numérique constant est sollicité dans ces cas et ne constitue pas une courbe mesurée.' if extrapolated else 'Le prolongement numérique constant prévu dans la configuration n’est pas sollicité dans cet échantillon.'} L'échantillonnage couvre les coques dont |ycentre|≤2h et a0−h≤|xcentre|≤22,86 ; son maximum n'est pas une borne du maillage entier. La convention source demeure indéterminée, les décimales et arrondis MPa/psi ne sont pas résolus.

IMPACT-I02I-C doit partir des résultats sauvegardés : examiner en priorité les critères échoués, l'écart de travail des ressorts et les états communs manquants, choisir une extension bornée de qualification de pénalité/domaine/vitesse ou d'échantillonnage, puis seulement comparer Gf=15/30/60 sans modification d'un état endommagé. La sensibilité temporelle est effectuée uniquement pour ENG au pas médian ; TRUE ne reçoit pas de qualification temporelle par analogie. Le domaine d'arrêt et le proxy de pointe peuvent limiter les comparaisons ; la convention matériau reste une sensibilité distincte.

Une température imposée n'est pas un incendie calculé. Localisation en flexion après fracture complète non validée. Aucun résultat ne valide l'impact historique d'un Boeing, une aile réelle, la façade ou l'effondrement du WTC1. Blender reste une visualisation.

## Reproductibilité, coût et publication

Configuration R1, R2 et R3 conservées ; R3 effective : `{rel(CFG)}`. Scripts `run_impact_i02i_fixed_penalty.py`, `audit_impact_i02i_fixed_penalty.py`, `test_impact_i02i_fixed_penalty.py` et `complete_impact_i02i_fixed_penalty.py`. Graine 1102010 ; aucun tirage. Python {platform.python_version()}, NumPy {numpy.__version__}, OpenRadioss v20260728-win64 ; empreintes des exécutables et durées par travail dans chaque `execution.json`. Douze cas : {s['runtime_seconds']:.6f} s ; estimation annoncée 30–60 minutes, plafonds 30 minutes par cas et 90 minutes pour la campagne, sans calcul GPU. Préflights et capteur séparés dans le bilan administratif.

Audit effectif : `verification_r1/summary.json`, historiques JSON et forces d'intervalle CSV par cas. Diagnostics élastiques intermédiaires conservés ; r1 interrompu à la sérialisation d'un booléen NumPy, r2 lit les mêmes CSV sans relancer de solveur. Le test de capteur R1 est un échec de préparation Python avant solveur, R2 est réussi. Manifeste source, références, protection antérieure, empreintes et vérification finale dans ce dossier. Revérifier avec le mode `--verify` du script de clôture ; une nouvelle réanalyse doit créer un nouveau dossier.

Publication autorisée sur [WTC-simu2026](https://github.com/WTC-simu2026/WTC-simu2026) après chaque paire d'itérations auditée. Baseline publiée : IMPACT-I02I-A. Après clôture vérifiée de B : compteur 1/2 ; prochaine mise à jour après C vérifiée. Aucun envoi GitHub n'est effectué pour B seule. Les vérifications d'intégrité du dépôt restent distinctes de la validation scientifique.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# WTC1 : IMPACT-I02I-B terminée, prochaine IMPACT-I02I-C

Lire AGENTS.md, harness/state.json, ce fichier, puis {rel(OUTPUT/'publication_verification.json')}. L'état local fait autorité ; V8H/V11H sont historiques. V11F froid et branche thermique V11R → V11S préservés. Pas de reprise thermique dans B.

## Acquis à réutiliser

12 cas neufs, deux conventions engineering/true_total, trois pas locaux 2,54/1,27/0,635 mm ; Kn=56000 et Kt=21500 N/mm³ identiques, aire initiale fixe. Options QEPH explicites Ismstr4/Ithick1/Iplas1. Gf30 hypothétique. Témoins élastiques 28/28 et contrôles 5/5 ; capteur d'arrêt réel vérifié. Réactions REACY brutes = impulsions N·ms ; forces ΔJ/Δt, travail indépendant ΣFΔu. Mors inférieur ajouté pour le bilan d'impulsion. Aucun état ancien modifié, {len(protected['files'])} empreintes anciennes protégées.

Campagne : {checks}/{total} contrôles de cas ; {s['comparison_checks_passed']}/{s['comparison_checks_total']} de comparaison. Voir les échecs et non-évaluations dans summary.json. Source convention et propagation physique non qualifiées. Maxima plastiques échantillonnés, prolongement numérique constant signalé lorsqu'utilisé. Sensibilité demi-pas/durée double uniquement ENG médian.

## Suite bornée

IMPACT-I02I-C : lire les historiques sauvegardés et traiter les critères échoués / avances communes manquantes avant de choisir une nouvelle campagne. Quadrature du travail des ressorts : écart max {100*max_spring_quadrature:.5f} %, diagnostic à borner avant de qualifier Gf comme dissipation effective. Demi-pas : 4/4 critères dans le recouvrement, inertie toujours >1 % ; durée double : angle hors seuil et inertie persistante. Comparer pénalités, domaine et échantillonnage sans dépendance au maillage ; Gf15/30/60 reste une hypothèse à explorer lorsque les contrôles le permettent. Pré-déclarer durée/coût et états neufs ; ne pas remplacer une loi sur un état déjà endommagé. Ne pas relancer B, A, I02H, V11F ou V11R pour relecture.

Cadence GitHub : voir harness/publication_cycle.json ; baseline publiée A, B compte 1/2. Après C auditée et vérifiée, publier la paire sur https://github.com/WTC-simu2026/WTC-simu2026 avec paramètres, résultats, échecs et limites. Cette autorisation est acquise ; pas de publication X autorisée.

## Chemins et vérification

{rel(CFG)}
{rel(REPORT)}
{rel(SUMMARY)}
{rel(OUTPUT/'artifact_manifest.json')}
{rel(OUTPUT/'publication_verification.json')}

`harness/tools/Test-WtcHarness.ps1` puis `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_fixed_penalty.py --verify` : contrôles du cache, aucun solveur lancé. Une réanalyse des CSV utilise un nouveau dossier. Préflights R1/R2 et diagnostics partiels restent conservés. Archives/sources en lecture seule ; aucun nouveau scan. {s['runtime_seconds']/60:.3f} minutes pour les 12 cas.

Température imposée ≠ incendie ; flexion après fracture complète non validée ; éprouvette générique ≠ événement réel ; Blender reste visualisation.
''',encoding='utf-8',newline='\n')
    dump(OUTPUT/'release_audit.json',{'pass':True,'created_utc':NOW(),'integrity_checks':{'complete_bounded_campaign':True,'controls':True,'analytic_reference':True,'previous_hashes':True,'report_handoff':True},'scientific_all_gates_pass':s['all_case_gates_pass'] and s['all_comparison_gates_pass'],'scientific_failures_retained':failures,'physical_propagation_qualified':False,'checks_passed':checks,'checks_total':total})
    dump(OUTPUT/'software.json',{'python':sys.version,'numpy':numpy.__version__,'platform':platform.platform(),'runtime':'v20260728-win64','threads':1,'random_seed':cfg['seed'],'random_draws':0})
    print(json.dumps({'prepared':True,'previous_files_verified':len(protected['files']),'science_converged':False}))


def manifest():
    paths=[p for p in OUTPUT.rglob('*') if p.is_file() and p.name not in ['artifact_manifest.json','publication_verification.json']]
    paths += [p for p in (ROOT/'wtc1_simulation_v8/data').glob('impact_i02i_fixed_penalty*.json')]
    paths += [p for p in (ROOT/'wtc1_simulation_v8/scripts').glob('*impact_i02i_fixed_penalty.py')]+[HANDOFF]
    dump(OUTPUT/'artifact_manifest.json',{'created_utc':NOW(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(paths))],'exclusions':['self hash','post-registration publication_verification.json','mutable state, registry and publication cadence checked separately'],'scope':'all fresh raw cases, failed preflights, references, primary pages, scripts and report'})


def register():
    s,cfg,protected=validated(); assert REPORT.exists() and HANDOFF.exists() and json.loads((OUTPUT/'release_audit.json').read_text())['pass']
    dump(OUTPUT/'harness_after_artifacts_before_registration.json',harness())
    statepath=ROOT/'harness/state.json'; registry=ROOT/'harness/experiments/registry.jsonl'
    assert sha(statepath)==sha(OUTPUT/'before_state.json') and sha(registry)==sha(OUTPUT/'before_registry.jsonl'),'Concurrent change: do not overwrite'
    state=json.loads(statepath.read_text()); assert state['current_iteration']=='IMPACT-I02I-A' and state['next_iteration']=='IMPACT-I02I-B'
    assert not CADENCE.exists(),'Existing cadence needs deliberate update'
    manifest(); when=NOW()
    status='completed_bounded_fixed_penalty_campaign_with_failed_or_unassessed_qualification_gates'
    record={'experiment_id':'WTC1-IMPACT-I02I-B','registered_at':when,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(SUMMARY),'handoff':rel(HANDOFF),'source_manifest':rel(OUTPUT/'source_manifest.json'),'artifact_manifest':rel(OUTPUT/'artifact_manifest.json'),'release_audit':rel(OUTPUT/'release_audit.json'),'publication_verification':rel(OUTPUT/'publication_verification.json'),'cases':12,'case_checks_passed':s['case_checks_passed'],'case_checks_total':s['case_checks_total'],'comparison_checks_passed':s['comparison_checks_passed'],'comparison_checks_total':s['comparison_checks_total'],'controls_pass':s['control_pass'],'old_files_preserved':len(protected['files']),'source_convention_verified':False,'physical_propagation_qualified':False,'cold_V11F_preserved':True,'thermal_V11R_preserved':True,'next_iteration':'IMPACT-I02I-C','github_pending_iterations':1,'caveat':'Fixed penalty only, hypothetical Gf30, generic plane coupon. All numerical failures and unassessed common advances retained. Source convention and physical propagation remain unqualified.'}
    prefix=registry.read_bytes(); assert prefix.endswith(b'\n')
    with registry.open('ab') as f: f.write((json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'))
    state.update(updated_at=when,current_iteration='IMPACT-I02I-B',current_status=status,next_iteration='IMPACT-I02I-C',next_objective='Réutiliser B sauvegardée : traiter inertie, écart de quadrature du travail des ressorts et avances communes non évaluées ; pré-déclarer une extension bornée de pénalité/domaine/vitesse/échantillonnage à états neufs avant Gf15/30/60. Conserver les deux conventions, QEPH explicite, Kn/Kt indépendants du maillage et travail des appuis depuis impulsions. Source et propagation physique non qualifiées. Après C auditée, publier B+C sur GitHub (cadence 2). V11F et V11R/V11S préservés.')
    state['impact_i02i_b_key_results']={k:record[k] for k in ['cases','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','controls_pass','old_files_preserved','source_convention_verified','physical_propagation_qualified','cold_V11F_preserved','thermal_V11R_preserved']}
    state['impact_i02i_b_key_results'].update(normal_penalty_N_per_mm3=56000.,tangent_penalty_N_per_mm3=21500.,reference_area_fixed=True,hypothetical_Gf_N_per_mm=30.,runtime_seconds=s['runtime_seconds'],all_case_gates_pass=s['all_case_gates_pass'],all_comparison_gates_pass=s['all_comparison_gates_pass'],github_pending_iterations=1)
    state['impact_i02i_b_key_results'].update(maximum_global_energy_residual_fraction=max(r['metrics']['energy_residual_fraction'] for r in s['cases'].values()),maximum_independent_boundary_work_error_fraction=max(r['metrics']['independent_actuator_work_error_fraction'] for r in s['cases'].values()),maximum_connector_work_quadrature_error_fraction=max(r['metrics']['spring_work_quadrature_error_fraction'] for r in s['cases'].values()),maximum_kinetic_to_internal_significant_window=max(r['metrics']['maximum_kinetic_to_internal_significant_window'] for r in s['cases'].values()),inertia_failures=sum(not r['gates']['inertia_significant_window'] for r in s['cases'].values()),all_prior_source_and_output_hashes_verified=True)
    state['validated_artifacts'].update(latest_fixed_penalty_configuration=rel(CFG),latest_fixed_penalty_report=rel(REPORT),latest_fixed_penalty_summary=rel(SUMMARY),latest_fixed_penalty_handoff=rel(HANDOFF),latest_fixed_penalty_publication_verification=rel(OUTPUT/'publication_verification.json'),github_publication_cycle=rel(CADENCE))
    state['open_limitations'].append('I02I-B fixed initial-area penalty campaign is a bounded generic plane coupon. Failed numerical gates and missing exact advance comparisons remain explicit; source interpretation, tip plastic extrapolation and physical propagation remain unqualified.')
    dump(CADENCE,{'schema_version':1,'repository':'https://github.com/WTC-simu2026/WTC-simu2026','user_authorization':'2026-10-02: updates GitHub toutes les 2 iterations','every_verified_iterations':2,'last_published_iteration':'IMPACT-I02I-A','last_published_commit':'dd58cc439cd9b9094af5bc12c49f4b396d946021','last_published_release':'snapshot-2026-10-01-impact-i02i-a','pending_iterations':['IMPACT-I02I-B'],'pending_count':1,'next_publication_after':'IMPACT-I02I-C audited and integrity verified','require_before_publication':['harness PASS','source and old output preservation','saved configuration/results/report/handoff','anonymous account commit identity','scientific failures and limitations included','remote commit/release hashes and CI verified'],'updated_at':when,'post_to_X_authorized':False})
    temp=ROOT/'harness/state_i02ib_pending.json'; dump(temp,state); temp.replace(statepath)
    print(json.dumps(verify(write=True),indent=2))


def verify(write=False):
    s,cfg,protected=validated(); ma=json.loads((OUTPUT/'artifact_manifest.json').read_text()); failures=[r['path'] for r in ma['files'] if sha(ROOT/r['path'])!=r['sha256']]
    state=json.loads((ROOT/'harness/state.json').read_text()); oldstate=json.loads((OUTPUT/'before_state.json').read_text()); registry=(ROOT/'harness/experiments/registry.jsonl').read_bytes(); oldreg=(OUTPUT/'before_registry.jsonl').read_bytes(); extra=registry[len(oldreg):].decode().splitlines(); records=[json.loads(v) for v in registry.decode().splitlines() if v.strip()]
    prior=['v11f_key_results','v11r_key_results','deferred_thermal_branch','impact_i02h_key_results','impact_i02i_a_key_results','source_archive','evidence_policy']; hv=harness(); cadence=json.loads(CADENCE.read_text())
    checks={'manifest_hashes':not failures,'prior_files_preserved':True,'registry_prefix_preserved':registry.startswith(oldreg),'exactly_one_new_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-B','single_B_record':sum(r['experiment_id']=='WTC1-IMPACT-I02I-B' for r in records)==1,'correct_state':state['current_iteration']=='IMPACT-I02I-B' and state['next_iteration']=='IMPACT-I02I-C','cold_thermal_and_A_preserved':all(state[k]==oldstate[k] for k in prior),'harness_pass':hv['Status']=='PASS','bounded_claims':not s['source_convention_verified'] and not s['physical_propagation_qualified'],'report_handoff_present':REPORT.exists() and HANDOFF.exists(),'publication_cadence_1_of_2':cadence['pending_iterations']==['IMPACT-I02I-B'] and cadence['every_verified_iterations']==2 and cadence['last_published_iteration']=='IMPACT-I02I-A'}
    result={'created_utc':NOW(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(ma['files']),'manifest_failures':failures,'prior_files_checked':len(protected['files']),'harness':hv,'scientific_case_checks':f"{s['case_checks_passed']}/{s['case_checks_total']}",'scientific_comparison_checks':f"{s['comparison_checks_passed']}/{s['comparison_checks_total']}",'scientific_all_gates_pass':s['all_case_gates_pass'] and s['all_comparison_gates_pass'],'source_convention_verified':False,'physical_propagation_qualified':False,'github_pending_iterations':1,'next_iteration':'IMPACT-I02I-C'}
    if write: dump(OUTPUT/'publication_verification.json',result)
    assert result['pass'],result; return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); group=p.add_mutually_exclusive_group(required=True); group.add_argument('--prepare',action='store_true'); group.add_argument('--register',action='store_true'); group.add_argument('--verify',action='store_true'); a=p.parse_args()
    if a.prepare: prepare()
    elif a.register: register()
    else: print(json.dumps(verify(),indent=2))
