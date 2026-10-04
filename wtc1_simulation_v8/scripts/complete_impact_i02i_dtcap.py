"""Prepare, register and verify I02I-F from saved results only."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import run_impact_i02i_dtcap as f

ROOT,OUT,CFG=f.ROOT,f.OUT,f.CFG
SUMMARY=OUT/'verification_r1/summary.json'
REPORT=OUT/'rapport_impact_i02i_dtcap.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_F_HANDOFF.md'
GPLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_g_plan_from_f.json'

def preservation():
    rows=json.loads((OUT/'preservation_before.json').read_text(encoding='utf-8'))['files']
    bad=[r['path'] for r in rows if f.sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(rows)

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists() and not GPLAN.exists(),'Preserve iterations'
    s=json.loads(SUMMARY.read_text(encoding='utf-8'));cfg=json.loads(CFG.read_text(encoding='utf-8'))
    hv=f.harness();count=preservation()
    assert len(s['cases'])==len(cfg['cases'])==8 and not s['old_solvers_rerun']
    assert all(v['checks']['preflight'] and v['checks']['normal_termination'] and v['checks']['TH_every_cycle'] for v in s['cases'].values())
    execution=[r for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text())]
    assert len(execution)==24 and all(r['returncode']==0 for r in execution)
    assert sum(r['seconds'] for r in execution)<=cfg['execution']['maximum_campaign_wall_seconds']
    assert all(sum(r['seconds'] for r in json.loads(p.read_text()))<=cfg['execution']['maximum_case_wall_seconds'] for p in OUT.glob('*/execution.json'))
    rows=[];phase=[];failures=[]
    for n,v in s['cases'].items():
        q=v['sampling'];m=v['metrics'];bad=[k for k,ok in v['checks'].items() if not ok]
        failures.append({'case':n,'failed_gates':bad})
        rows.append(f"| {n} | {q['maximum_saved_solver_dt_ms']*1e6:g} | {q['rows']} | {100*m['energy_residual_fraction']:.6g} | {100*m['boundary_work_error_fraction']:.6g} | {100*v['momentum']['X']['raw_boundary_residual_fraction']:.6g} | {m['final_IE_J']:.9g} | {', '.join(bad) or 'aucun'} |")
        for e in v['events']:
            phase.append(f"| {n} | {e['OFF_time_ms']:.8g} | {e['lag_rows']} | {e['lag_ms']*1e6:.7g} | {e['FX_at_OFF_N']:.8g} | {e['U_shear_before_J']:.8g} | {e['IE_settled_minus_last_active_J']:.8g} | {e['KE_settled_minus_last_active_J']:.8g} | {e['WE_settled_minus_last_active_J']:.8g} |")
    f.dump(OUT/'retained_failed_gates.json',{'created_utc':f.NOW(),'cases':failures,
        'scientific_all_gates_pass':False,'no_gate_relaxed_or_rephased':True})
    plateau=json.loads((OUT/'residual_plateau_diagnostic.json').read_text())
    pv=plateau['cases']['AFTER_CAP050NS'];near=pv['rows_near_maximum'];center=2
    pleft=near[center-1]['node2_velocity_mm_per_ms']*.1
    pright=near[center+1]['node2_velocity_mm_per_ms']*.1
    mean=.5*(pleft+pright)
    f.dump(OUT/'plateau_point_inference.json',{'created_utc':f.NOW(),
        'time_ms':pv['time_ms'],'left_nodal_momentum_N_ms':pleft,'right_nodal_momentum_N_ms':pright,
        'adjacent_velocity_average_momentum_N_ms':mean,'saved_global_momentum_N_ms':pv['global_momentum_N_ms'],
        'difference_N_ms':pv['global_momentum_N_ms']-mean,
        'post_declared_diagnostic_only':True,'gates_changed':False,
        'interpretation':'Agreement at this point suggests output/time centering at a piecewise-linear knot. Exact engine algorithm is not established.'})
    plan={'id':'IMPACT-I02I-G_PLAN_FROM_F','declared_utc':f.NOW(),'seed':1102015,'random_draws':0,
        'scope':'Close input-table and free elastic inertia controls before any free fracture or aircraft impact',
        'saved_F_baselines':['AFTER_CAP100NS','AFTER_CAP050NS'],
        'saved_baseline_summary':f.rel(SUMMARY),'saved_baseline_sha256':f.sha(SUMMARY),
        'stage_1':{'fresh_after_failure_controls':[
            {'subdivisions_per_segment':1600,'maximum_dt_ms':.0001},
            {'subdivisions_per_segment':1600,'maximum_dt_ms':.00005},
            {'subdivisions_per_segment':3200,'maximum_dt_ms':.0001},
            {'subdivisions_per_segment':3200,'maximum_dt_ms':.00005}],
            'unchanged':'1 ms segments, same 0.02 mm displacement, same connector law/mass, fresh histories',
            'question':'Does the unshifted residual plateau scale with the input-table spacing?',
            'rule':'Define all new force/work/momentum gates before execution; compare old F without rerun or forced rephasing'},
        'stage_2':{'fresh_free_elastic_witness':True,'moving_nodal_mass_g':.1,
            'fixed_nodal_mass_g':.1,'tangent_stiffness_N_per_mm':21500.,
            'initial_velocity_mm_per_ms':1.,'initial_displacement_mm':0.,
            'maximum_dt_ms':[.0001,.00005],'duration_in_analytic_periods':8,
            'analytic_reference':'omega=sqrt(k/m), u=v0/omega*sin(omega*t), v=v0*cos(omega*t), E=0.5*m*v0^2; include initial momentum in impulse balance',
            'precondition':'Verify primary keyword and output time-centering definitions before generating a fresh deck; no restart, imposed moving X or fracture in the free witness'},
        'cost':{'maximum_case_wall_seconds':90,'maximum_campaign_wall_seconds':600,'announce_before_run':True},
        'invariants':['No mass scaling','Fresh states only','No damaged-property replacement',
            'Raw OFF/force/impulse histories kept','No source convention selection','No Gf calibration'],
        'deferred':['All E inertia/angle/coverage failures','Gf15/60','Free fracture transfer','Aircraft/facade/fire/collapse qualification'],
        'publication':'F pending 1/2; publish F+G only after verified G; current public baseline E retained'}
    f.dump(GPLAN,plan)
    e=json.loads((OUT/'cached_E_sensitivity_review.json').read_text())
    edomain=e['cases']['ENG_DOMAIN_R1'];ehalf=e['cases']['ENG_PENALTY_HALF_R1']
    after=s['F_after_failure_X_raw_boundary_residual_fractions']
    report=f'''# WTC1 — IMPACT-I02I-F : pas plafonné après désactivation

## 1. Faits directement observés ou transcrits

Huit témoins neufs terminent normalement, leurs 24 exécutables étant sauvegardés : {s['runtime_seconds']:.6f} s, plafond 600 s/campagne et 90 s/cas. Aucune alerte starter n'est acceptée. Les colonnes TIME STEP enregistrent exactement les plafonds 200, 100 ou 50 ns avant et après la désactivation. Une ligne TH correspond à chaque cycle ; les derniers états restent ceux enregistrés. Aucun point terminal n'est extrapolé, même si certaines dernières lignes précèdent la fin demandée d'un pas. Aucun ajout de masse mesuré.

La [documentation primaire /DTIX]({f.SOURCE_URL}) donne les pas initial et maximal du run. Une copie datée et son SHA-256 sont dans `{f.rel(OUT/'source_manifest.json')}` ; ce document sous copyright est exclu de la redistribution. Il n'est pas utilisé pour affirmer le phasage exact de l'algorithme interne.

## 2. Résultats d'un modèle officiel

Aucun résultat NIST ou calcul officiel du WTC1 n'est ajouté. /DTIX est une définition de logiciel, pas une preuve concernant l'événement. Les deux interprétations NASA de E demeurent conservées et non identifiées ; aucun matériau avion n'est choisi à partir de ces tests.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive n'est évaluée. {count} fichiers antérieurs sont contrôlés par leurs inventaires sauvegardés. D et E sont réutilisés sans ancien solveur relancé ; aucune archive source n'est rescannée ou modifiée. L'administration GitHub reste séparée des sorties scientifiques.

## 4. Hypothèses propres au modèle, propriétés, unités et critères

Deux nœuds coïncidents reliés par un TYPE8, aire initiale 1 mm², masse totale 0,2 g répartie 0,1 g/nœud, inertie de rotation 0,001 g mm² et rotations bloquées. Kn=56000 N/mm et Kt=21500 N/mm ; pic normal hypothétique 495 N, Gf=30 N/mm pour l'aire de référence, δ0=495/56000 mm, δf=60/495≈0,121212 mm. Lois H2 normale et tangentielle inchangées, aucune viscosité, aucune masse ajoutée, aucun état endommagé repris. L'énergie normale intégrée de séparation vaut 30 N mm=0,03 J ; cisaillement à 0,02 mm : U=Kt δ²/2=4,3 N mm=0,0043 J.

Unités : g, mm, ms, N ; N mm=mJ, J=0,001 N mm ; impulsion N ms=g mm/ms. Un pas 0,0002 ms vaut 200 ns, 0,0001 ms vaut 100 ns, 0,00005 ms vaut 50 ns. La même loi H2 définit le déchargement, U=Fn²/(2Kn)+Ft²/(2Kt) hors ligne de transition ; IE−U demeure un travail numérique non récupéré, pas une énergie de fracture mixte mesurée.

Nœud 1 fixé ; déplacement X/Y du nœud 2 imposé par trajectoires quintiques tabulées, 800 subdivisions par segment de 1 ms. Les cas reprennent les trajectoires D : cisaillement fixé avant rupture normale, mouvement proportionnel, cisaillement après rupture normale et retour élastique sans rupture. L'intervalle TH demandé 0,000001 ms est inférieur au pas résolu ; TIME STEP et nombre de cycles confirment l'échantillonnage. Les fichiers ne décalent ni OFF, ni force, ni impulsion, ni vitesse.

Critères pré-déclarés : force/travail/énergie hérités ≤0,5 %, masse relative ≤1e-5, absence de masse ajoutée ≤1e-12 g ; pas sauvegardé ≤plafond×(1+1e-5), différences de temps CSV avec tolérance déclarée 0,000002 ms ; couverture de fin à deux pas sans extrapolation. Somme signée des impulsions d'appuis comparée au momentum global, résidu brut ≤1 % du plus grand des pics d'impulsions d'appuis ; momentum nodal m1v1+m2v2 comparé au global ≤1 % de son pic. Le résidu rapporté au petit momentum net est aussi conservé sans correction de quantification ; il ne remplace pas ces normalisations.

Les contrôles additionnels aux temps communs demandés 1,1/1,25/1,5/1,75/1,9/2 ms sont inscrits dans la configuration avant solveur. La première déclaration et le script associé sont conservés avant cet alignement administratif. Génération par fonction D immuable sur états entièrement neufs, puis nom F et /DTIX ; la sortie et la configuration redirigées dans ce processus ne modifient aucun fichier D. Les fonctions de chargement, les versions et leurs SHA-256 sont sauvegardés.

## 5. Résultats dérivés

{s['case_checks_passed']}/{s['case_checks_total']} critères de cas et {s['comparison_checks_passed']}/{s['comparison_checks_total']} comparaisons passent. Cinq critères stricts OFF/FX sur la même ligne demeurent échoués, sans relaxation. La passation d'intégrité est distincte du succès scientifique global.

| Cas | Max pas résolu ns | Lignes/cycles | Résidu énergie % | Erreur travail appuis % | Résidu impulsion X / pic appui % | IE finale J | Critères échoués |
|---|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

| Cas | OFF ms | Retard lignes | Retard ns | FX sur ligne OFF N | U tangent avant J | ΔIE avant→stabilisé J | ΔKE avant→stabilisé J | ΔWE avant→stabilisé J |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(phase)}

Le témoin de cisaillement après rupture avait dans D un résidu brut X de {100*s['cached_D_after_failure_X_raw_boundary_residual_fraction']:.7g} % du pic d'impulsion d'appui. F : 100 ns={100*after['AFTER_CAP100NS']:.7g} %, 50 ns={100*after['AFTER_CAP050NS']:.7g} %. Les six temps communs sont tous couverts et l'impulsion y coïncide à la précision des sorties ; cela reste un test imposé, pas un corps libre. La borne passe mais le plateau non nul subsiste.

Diagnostic ajouté après pré-déclaration, sans nouveau critère : maximum X à t={pv['time_ms']:.7g} ms, exactement sur un point de la trajectoire tabulée, résidu {pv['residual_N_ms']:.9g} N ms aux deux pas. Momentum nodal à gauche {pleft:.9g}, à droite {pright:.9g}, moyenne {mean:.9g} N ms ; momentum global {pv['global_momentum_N_ms']:.9g}, écart à cette moyenne {pv['global_momentum_N_ms']-mean:.9g} N ms. Cela suggère un centrage temporel de sortie au changement de pente ; l'algorithme interne exact et une causalité unique ne sont pas établis. Aucune correction ni translation temporelle des données n'est appliquée.

Les cas de cisaillement fixé conservent IE=0,0343 J aux trois pas ; les 0,0043 J tangents récupérables avant désactivation ne deviennent pas une hausse de KE à la précision enregistrée, et leur suppression ne réduit pas IE. Ce modèle stocke ce travail dans IE, sans identifier une dissipation physique. Le cas proportionnel ajoute pendant la ligne de transition ≈0,85 µJ à 100 ns et ≈0,42 µJ à 50 ns, avec travail extérieur correspondant et KE inchangée à la précision enregistrée. Le retour élastique termine près de zéro IE, conformément à la restitution attendue.

Les grandes impulsions opposées limitent aussi la lecture du petit momentum net : cas fixé, résidu X≈2,8–2,9 % du pic net, somme d'ULP float32≈3,26 % de ce pic. Ce diagnostic ne démontre pas que toute l'erreur vient de la quantification ; le phasage peut intervenir. Les valeurs brutes et les normalisations figurent dans chaque audit, et aucune de ces limites ne qualifie une libération libre.

Revue E sauvegardée : ENG domaine max KE/IE={100*edomain['maximum_KE_IE_fraction']:.6g} %, CTOA domaine écart={100*edomain['maximum_ctoa_difference_fraction']:.6g} %, CTOA pénalité moitié écart={100*ehalf['maximum_ctoa_difference_fraction']:.6g} %. Toutes les couvertures et tous les échecs E demeurent ouverts dans `{f.rel(OUT/'cached_E_sensitivity_review.json')}`. F ne répare pas une avancée ou un déplacement absent.

## 6. Contradictions, informations manquantes et suite

Le critère strict de force sur la même ligne OFF échoue dans cinq cas, avec retard d'un cycle dont la durée se réduit 200→100→50 ns. Le centrage exact des grandeurs du moteur n'est pas établi par un code primaire vérifié. Une bonne fermeture énergie/impulsion sous déplacement imposé ne valide pas la libération d'un corps libre ni une énergie de fracture mixte physique. Gf réel, convention NASA, sensibilité spatiale E et ses couvertures restent non identifiés.

G : plan `{f.rel(GPLAN)}`. Étudier d'abord 1600/3200 subdivisions de la trajectoire sur témoins neufs, puis un oscillateur élastique libre à référence analytique avec momentum initial inclus, après vérification des mots-clés primaires. Conserver les sorties F ; ne pas relancer huit cas pour les lire. Pré-déclarer les critères avant tout nouveau solveur. Aucun transfert à un impact libre avec fracture avant ces contrôles. Gf15/60 différés.

V11F froid et V11R/V11S différée préservés. Température imposée ≠ incendie calculé ; localisation en flexion après fracture complète non validée ; tests numériques ≠ validation d'un effondrement réel ; Blender reste une visualisation. Aucun Boeing complet, façade ou pénétration historique qualifié. F=1/2 pour GitHub ; publication F+G après une G vérifiée, compte WTC-simu2026, sans post X.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# WTC1 — I02I-F terminée, prochaine I02I-G

Lire AGENTS.md, harness/state.json, cette passation puis `{f.rel(OUT/'publication_verification.json')}`. État local prioritaire. Rapport `{f.rel(REPORT)}`, résultats `{f.rel(SUMMARY)}`, configuration `{f.rel(CFG)}`, plan G `{f.rel(GPLAN)}`.

F : 8 témoins neufs, 24 jobs normaux, {s['runtime_seconds']:.3f} s ; {s['case_checks_passed']}/{s['case_checks_total']} critères et {s['comparison_checks_passed']}/{s['comparison_checks_total']} comparaisons. /DTIX vérifié dans TIME STEP : 200/100/50 ns, TH chaque cycle, aucune masse ajoutée. Critère strict OFF/FX échoué dans cinq cas ; retard d'un cycle conservé. IE sous cisaillement fixé reste 0,0343 J, sans restitution de 0,0043 J tangent dans KE observée. Travail non récupéré numérique, aucune dissipation mixte physique calibrée.

Cisaillement imposé après rupture : résidu impulsion X D≈14,205 % → F≈0,192454 % à 100 et 50 ns ; plateau non nul. Maximum à 1,7875 ms sur un point tabulé, momentum global compatible avec moyenne des vitesses adjacentes ; diagnostic ajouté après déclaration, pas preuve du code interne ni correction d'un critère. Les grandes impulsions opposées ont aussi une limite float32. Réutiliser `residual_plateau_diagnostic.json`, `plateau_point_inference.json` et les CSV sauvegardés.

G : trajectoires 1600/3200 subdivisions à états neufs, puis témoin élastique libre analytique avec momentum initial ; documenter les mots-clés avant solveur et déclarer les critères. Toutes les sensibilités/angles/couvertures E restent ouverts (`cached_E_sensitivity_review.json`), Gf15/60 différés, deux conventions NASA conservées. Pas de propriété remplacée sur état endommagé, aucun impact libre avec fracture qualifié.

{count} anciens fichiers épinglés, aucune archive rescannée ni ancien solveur relancé. Vérification sans solveur : `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_dtcap.py verify`. V11F/V11R/V11S préservés ; température imposée ≠ incendie, flexion post-fracture non validée, Blender visualisation.

Publication : cadence dans harness/publication_cycle.json ; F pending 1/2, envoi après G vérifiée. Dernière publication D+E du 3 octobre 2026 conservée. Compte/identité WTC-simu2026 ; administration privée exclue, aucun post sur X autorisé.
''',encoding='utf-8',newline='\n')
    f.dump(OUT/'release_audit.json',{'created_utc':f.NOW(),'pass':True,
        'definition':'Integrity of bounded completed diagnostics, failed scientific gates retained',
        'old_files_preserved':count,'harness':hv,'config_sha256':f.sha(CFG),
        'summary_sha256':f.sha(SUMMARY),'report_sha256':f.sha(REPORT),'handoff_sha256':f.sha(HANDOFF),
        'physical_propagation_qualified':False,'free_body_inertia_qualified':False})
    f.dump(OUT/'harness_after_artifacts.json',f.harness())
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/name for name in ['run_impact_i02i_dtcap.py',
        'audit_impact_i02i_dtcap.py','inspect_impact_i02i_dtcap_plateau.py','complete_impact_i02i_dtcap.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,GPLAN,HANDOFF]+scripts
    f.dump(OUT/'artifact_manifest.json',{'created_utc':f.NOW(),
        'files':[{'path':f.rel(p),'bytes':p.stat().st_size,'sha256':f.sha(p)} for p in sorted(set(paths))],
        'exclusions':['self','post-registration verification','mutable administrative harness metadata'],
        'scope':'All new F inputs, outputs, sources, revisions, audits, scripts, report, handoff and G plan'})

def register():
    assert REPORT.exists() and HANDOFF.exists() and (OUT/'artifact_manifest.json').exists()
    preservation();s=json.loads(SUMMARY.read_text(encoding='utf-8'))
    for name in f.ADMIN:assert f.sha(ROOT/'harness'/name)==f.sha(OUT/('before_'+Path(name).name)),'Concurrent harness change'
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    cadence=json.loads((ROOT/'harness/publication_cycle.json').read_text(encoding='utf-8'));assert cadence['pending_iterations']==[]
    when=f.NOW();status='completed_bounded_post_deactivation_step_controls_with_failed_same_row_force_gates'
    record={'experiment_id':'WTC1-IMPACT-I02I-F','registered_at':when,'status':status,
        'configuration':f.rel(CFG),'report':f.rel(REPORT),'results':f.rel(SUMMARY),'handoff':f.rel(HANDOFF),
        'artifact_manifest':f.rel(OUT/'artifact_manifest.json'),'source_manifest':f.rel(OUT/'source_manifest.json'),
        'publication_verification':f.rel(OUT/'publication_verification.json'),'G_plan':f.rel(GPLAN),
        'cases':len(s['cases']),'case_checks_passed':s['case_checks_passed'],'case_checks_total':s['case_checks_total'],
        'comparison_checks_passed':s['comparison_checks_passed'],'comparison_checks_total':s['comparison_checks_total'],
        'runtime_seconds':s['runtime_seconds'],'old_files_preserved':preservation(),
        'source_convention_verified':False,'physical_propagation_qualified':False,'free_body_inertia_qualified':False,
        'mixed_mode_dissipation_calibrated':False,'E_sensitivities_resolved':False,
        'strict_same_row_OFF_FX_failed_cases':s['strict_same_row_OFF_FX_failed_cases'],
        'after_failure_X_raw_boundary_residual_fractions':s['F_after_failure_X_raw_boundary_residual_fractions'],
        'next_iteration':'IMPACT-I02I-G','github_pending_iterations':1}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as file:file.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-F',current_status=status,next_iteration='IMPACT-I02I-G',updated_at=when,
        next_objective='Réutiliser F sauvegardée : pas post-OFF plafonné vérifié, résidu X après rupture 0,192454 % mais plateau aux points tabulés et OFF/FX un cycle encore ouverts. Pré-déclarer témoins neufs de raffinement des trajectoires puis oscillateur élastique libre analytique, avec momentum initial et mots-clés primaires vérifiés, avant impact libre avec fracture. Conserver toutes sensibilités/couvertures E, deux conventions NASA, Gf30 hypothétique, Gf15/60 différés. F=1/2 GitHub, publication F+G après vérification. V11F/V11R/V11S préservés.')
    state['impact_i02i_f_key_results']={k:record[k] for k in ['cases','case_checks_passed','case_checks_total',
        'comparison_checks_passed','comparison_checks_total','runtime_seconds','old_files_preserved',
        'source_convention_verified','physical_propagation_qualified','free_body_inertia_qualified',
        'mixed_mode_dissipation_calibrated','E_sensitivities_resolved','strict_same_row_OFF_FX_failed_cases',
        'after_failure_X_raw_boundary_residual_fractions','github_pending_iterations']}
    state['validated_artifacts'].update(impact_i02i_f_report=f.rel(REPORT),impact_i02i_f_results=f.rel(SUMMARY),
        impact_i02i_f_handoff=f.rel(HANDOFF),impact_i02i_f_publication_verification=f.rel(OUT/'publication_verification.json'),impact_i02i_g_plan=f.rel(GPLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-F'],pending_count=1,
        next_publication_after='After a verified G: publish F+G, preserving E baseline and raw failed gates',updated_at=when)
    f.dump(ROOT/'harness/publication_cycle.json',cadence)
    temp=ROOT/'harness/state_i02if_pending.json';f.dump(temp,state);temp.replace(ROOT/'harness/state.json')
    verify(write=True)

def verify(write=False):
    count=preservation();m=json.loads((OUT/'artifact_manifest.json').read_text(encoding='utf-8'))
    bad=[r['path'] for r in m['files'] if f.sha(ROOT/r['path'])!=r['sha256']]
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'));old=json.loads((OUT/'before_state.json').read_text(encoding='utf-8'))
    reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes()
    extra=reg[len(prefix):].decode('utf-8').splitlines();cadence=json.loads((ROOT/'harness/publication_cycle.json').read_text(encoding='utf-8'))
    s=json.loads(SUMMARY.read_text(encoding='utf-8'));hv=f.harness()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    checks={'new_artifact_hashes':not bad,'old_pinned_files_preserved':True,'registry_prefix':reg.startswith(prefix),
        'one_F_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-F',
        'state_F_to_G':state['current_iteration']=='IMPACT-I02I-F' and state['next_iteration']=='IMPACT-I02I-G',
        'prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS',
        'report_handoff_plan_exist':REPORT.exists() and HANDOFF.exists() and GPLAN.exists(),
        'cadence_F_one_pending':cadence['pending_iterations']==['IMPACT-I02I-F'] and cadence['pending_count']==1,
        'failed_force_gates_retained':len(s['strict_same_row_OFF_FX_failed_cases'])==5 and not s['all_scientific_checks_pass'],
        'new_step_mass_impulse_gates_pass':all(all(ok for k,ok in v['checks'].items() if k!='strict_same_row_OFF_FX') for v in s['cases'].values()),
        'unqualified_physics_retained':not s['physical_propagation_qualified'] and not s['free_body_inertia_qualified'] and not s['E_sensitivities_resolved'],
        'no_old_solver_rerun':not s['old_solvers_rerun']}
    result={'created_utc':f.NOW(),'pass':all(checks.values()),'checks':checks,
        'manifest_files_checked':len(m['files']),'manifest_failures':bad,'old_files_checked':count,'harness':hv,
        'scientific_all_gates_pass':s['all_scientific_checks_pass'],'physical_propagation_qualified':False,
        'free_body_inertia_qualified':False,'case_checks':f"{s['case_checks_passed']}/{s['case_checks_total']}",
        'comparison_checks':f"{s['comparison_checks_passed']}/{s['comparison_checks_total']}",
        'next_iteration':'IMPACT-I02I-G','github_pending_iterations':1}
    assert result['pass'],result
    if write:f.dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()
