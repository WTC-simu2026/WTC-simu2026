"""G report, compact H handoff, registration and hash verification, no solve."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import run_impact_i02i_table_free as g
ROOT,OUT,CFG=g.ROOT,g.OUT,g.CFG
SUMMARY=OUT/'verification_r1/summary.json'
REPORT=OUT/'rapport_impact_i02i_table_free.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_G_HANDOFF.md'
PLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_h_plan_from_g.json'

def preservation():
    rows=json.loads((OUT/'preservation_before.json').read_text(encoding='utf-8'))['files']
    bad=[r['path'] for r in rows if g.sha(ROOT/r['path'])!=r['sha256']];assert not bad,bad;return len(rows)

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists() and not PLAN.exists(),'Preserve iteration'
    s=json.loads(SUMMARY.read_text(encoding='utf-8'));cfg=json.loads(CFG.read_text(encoding='utf-8'))
    hv=g.harness();count=preservation();assert len(s['cases'])==len(cfg['cases'])==6
    execution=[r for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text())]
    assert len(execution)==18 and all(r['returncode']==0 for r in execution)
    assert sum(r['seconds'] for r in execution)<=600 and all(sum(r['seconds'] for r in json.loads(p.read_text()))<=90 for p in OUT.glob('*/execution.json'))
    assert all(v['checks']['preflight'] and v['checks']['normal_termination'] and v['checks']['TH_every_cycle'] for v in s['cases'].values())
    table=[]
    for c in s['comparisons']:
        table.append(f"| {c['case']} | {100*c['G_raw_residual_fraction']:.9g} | {c['ratio_G_to_F']:.9g} | {c['expected_ratio']:.3g} | {100*c['ratio_relative_error']:.6g} |")
    free=[];strict=[]
    for name,v in s['cases'].items():
        if v['case']['stage']!='free':continue
        m=v['metrics']
        free.append(f"| {name} | {100*m['displacement_fraction']:.7g} | {100*m['nodal_velocity_fraction']:.7g} | {100*m['global_momentum_fraction']:.7g} | {100*m['raw_initial_momentum_impulse_fraction']:.7g} | {100*m['energy_residual_fraction']:.7g} | {100*m['period_fraction']:.7g} |")
        strict.append({'case':name,'failed_1pct_diagnostics':[k for k,v in v['strict_raw_1pct_diagnostics'].items() if not v]})
    g.dump(OUT/'retained_limitations.json',{'created_utc':g.NOW(),'strict_1pct_diagnostics':strict,
        'inherited_F_same_row_OFF_FX_failures':s['F_same_row_OFF_FX_failures_still_open'],
        'E_review':s['cached_E_review_path'],'E_review_sha256':s['cached_E_review_sha256'],
        'no_gate_relaxed_after_execution':True,'no_history_rephased':True,
        'free_fracture_qualified':False,'physical_propagation_qualified':False})
    plan={'id':'IMPACT-I02I-H_PLAN_FROM_G','created_utc':g.NOW(),'seed':1102016,'random_draws':0,
        'saved_G_summary':g.rel(SUMMARY),'saved_G_summary_sha256':g.sha(SUMMARY),
        'scope':'First tighten raw free elastic impulse/velocity accuracy before a minimal fresh free normal fracture witness',
        'stage_1':{'fresh_cases':'Same free X elastic oscillator, 8 periods, caps 25 and 12.5 ns; no restart or prescribed X',
            'maximum_dt_ms':[.000025,.0000125],'strict_raw_amplitude_tolerance_fraction':.01,
            'rule':'Predeclare all tolerances and reference before engines. Retain all raw fields and include P0. Reuse G 100/50 ns, no rephasing to close a gate.',
            'question':'Do raw nodal/global momentum and support impulse fall below 1% as step decreases? Exact internal TH centering remains unverified.'},
        'stage_2_if_stage_1_passes':{'fresh_free_normal_witness':True,'moving_mass_g':.1,'initial_vY_mm_per_ms':30.,
            'X_blocked_Y_free':True,'Kn_N_per_mm':56000.,'peak_normal_N':495.,'Gf_N_per_mm':30.,'reference_area_mm2':1.,
            'initial_energy_J':.045,'monotone_normal_work_J':.03,'ideal_post_failure_velocity_mm_per_ms':17.32050807568877,
            'proposed_maximum_dt_ms':[.00005,.000025],
            'precondition':'Before declaring solve, derive/check piecewise cohesive W(delta), quadrature t(delta)=integral d(delta)/sqrt(v0^2-2W(delta)/m), impulse and E0=KE+IE; distinguish numerical IE retention from physical fracture calibration.',
            'rule':'Fresh initial histories only, no property replacement. No shear energy reservoir, aircraft, mixed-mode calibration or Gf15/60 in this witness. Do not execute stage 2 if strict elastic controls fail.'},
        'cost':{'maximum_case_wall_seconds':90,'maximum_campaign_wall_seconds':600,'announce_before_run':True},
        'still_open':['F strict same-row OFF/FX mismatch','TH/REACX documentation-runtime discrepancy and precise output centering',
            'All E inertia/angle/missing coverage limitations','NASA nominal/true convention unidentified','Gf15/60','Mixed-mode physical dissipation','Aircraft/façade/fire/collapse'],
        'publication':'F+G due only after G integrity verification; after verified publication H will be pending 1/2',
        'preserved':['V11F cold control','V11R and deferred V11S','No source/archive edits','Blender visual only']}
    g.dump(PLAN,plan)
    r=cfg['free_reference']
    report=f'''# WTC1 — IMPACT-I02I-G : résolution des trajectoires et témoin élastique libre

## 1. Faits directement observés ou transcrits

Six états neufs, 18 exécutables, terminaison normale et aucune alerte starter : {s['runtime_seconds']:.6f} s au total, limites 90 s/cas et 600 s/campagne. Pas global sauvegardé plafonné à 100 ou 50 ns, une ligne TH par cycle ; aucune masse ajoutée, aucune extrapolation terminale. Les deux fonctions imposées des cas N1600 comptent 3201 points chacune, celles des cas N3200 6401 points chacune. Le script historique avait 800 subdivisions codées en dur : le nouveau générateur utilise réellement N et contrôle les fonctions sérialisées, sans modifier les anciens scripts.

Les définitions primaires consultées sont [/INIVEL]({g.SOURCES[0][1]}), [/TH/NODE]({g.SOURCES[1][1]}) et la [théorie dynamique Radioss 2017]({g.SOURCES[2][1]}). /INIVEL/TRA définit une vitesse initiale sur un groupe de nœuds. La théorie emploie des vitesses à demi-pas. La documentation TH nomme REACX « réaction », avec unité de force, alors que les essais sauvegardés de cette version sont compatibles avec une impulsion cumulative N ms. Le témoin libre compare de nouveau cette colonne à l'intégrale de −FX et à P−P0. Cette contradiction est conservée ; ni le code exact ni le centrage temporel de toutes les sorties 2026 ne sont établis par ces pages. Les copies locales datées et leurs SHA-256 sont dans source_manifest.json ; documents sous copyright exclus de redistribution.

## 2. Résultats d'un modèle officiel

Aucun résultat NIST ni modèle officiel du WTC1 ajouté. La documentation d'un solveur sert à définir les entrées et la référence numérique. Les deux conventions NASA antérieures restent non identifiées ; aucune branche de matériau avion n'est choisie par ces contrôles.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive testée, aucune vidéo relue ni archive rescannée. {count} fichiers anciens contrôlés à partir des inventaires sauvegardés, dont F et ses prédécesseurs. Les anciens solveurs ne sont pas relancés. Le contrôle froid V11F, V11R et V11S différée restent inchangés.

## 4. Hypothèses propres au modèle, unités et références

Cas imposés : même liaison TYPE8 à deux nœuds coïncidents, aire initiale 1 mm², masse totale 0,2 g (0,1 g/nœud), inertie 0,001 g mm², Kn=56000 N/mm, Kt=21500 N/mm, pic normal hypothétique 495 N, Gf=30 N/mm. δ0=495/56000 mm, δf=60/495 mm ; loi normale H2 et désactivation complète identiques à F. Rupture normale pendant 0–1 ms puis déplacement X 0→0,02 mm pendant 1–2 ms, quintique tabulée à 1600 ou 3200 subdivisions par segment. Historiques neufs, aucune substitution de propriété sur matériau endommagé.

Cas libres : même masse 0,1 g mobile et 0,1 g fixe, X libre, Y/Z et rotations bloqués, Kt=21500 N/mm, liaison linéaire symétrique sans rupture. u0=0, v0=1 mm/ms, aucun déplacement imposé, amortissement nul et aucun travail externe. Référence : ω=√(k/m)={r['omega_rad_per_ms']:.12g} rad/ms, T=2π/ω={r['period_ms']:.12g} ms, u=v0 sin(ωt)/ω, v=v0 cos(ωt), F=ku. Amplitude={r['amplitude_mm']:.12g} mm, force amplitude={r['force_amplitude_N']:.12g} N. P0=mv0=0,1 N ms, E0=mv0²/2=0,05 N mm=0,00005 J ; bilan brut J1+J2+P0−P et E0+WE−IE−KE. Énergie élastique U=ku²/2 ; période évaluée sur les passages croissants par zéro sans ajuster la phase.

Unités : g, mm, ms, N ; N=g mm/ms², N ms=g mm/ms et N mm=mJ. 0,0001 ms=100 ns ; les huit périodes demandées couvrent {r['duration_periods']*r['period_ms']:.12g} ms. Dernières lignes à 0,1084 ms, conservées sans extrapolation.

Tous les seuils sont déclarés avant moteur dans le JSON : 1 % en déplacement et momentum global ; 3 % pour vitesse nodale, force et impulsion brute, 0,5 % en énergie et période. Le seuil 3 % repose sur la borne prudente de demi-pas ωh/2≈0,023184 rad plus dispersion sur huit périodes ≈0,004505 rad à 100 ns. Il ne constitue pas une qualification à 1 %. Des diagnostics bruts plus stricts à 1 % sont enregistrés et restent échoués. Pour la tabulation, hypothèse testée de résidu proportionnel à 1/N, ratio à ±10 %. Aucun seuil modifié après exécution, aucun décalage des séries.

## 5. Résultats dérivés

Tous les {s['case_checks_total']} critères déclarés de cas et {s['comparison_checks_total']} critères de comparaison passent. Ils ne ferment pas les échecs stricts de F ni les sensibilités E.

### Trajectoires imposées après désactivation

F N800 : résidu X brut maximal / impulsion de bord maximale = 0,192454154 %. Les nouveaux résultats sont :

| Cas | Résidu brut (%) | Ratio G/F | Ratio 800/N attendu | Écart relatif du ratio (%) |
|---|---:|---:|---:|---:|
{chr(10).join(table)}

Le résidu diminue quasiment comme 1/N, indépendamment du passage 100→50 ns aux résolutions testées. Cette observation soutient une erreur liée aux points de la trajectoire imposée ; elle ne prouve pas le détail de l'implémentation interne. Les bilans IE finaux restent 0,03 J et les forces X restent nulles après désactivation : aucune réapparition de liaison. Le résidu n'est pas nul, et ces mouvements demeurent imposés.

### Oscillations libres, erreurs brutes normalisées

| Cas | u (%) | vitesse nodale (%) | momentum global (%) | J+P0−P (%) | bilan énergie (%) | période (%) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(free)}

Le déplacement et momentum global convergent approximativement en h² ; vitesse nodale et résidu d'impulsion environ en h. E0 est conservée à 0,0537857 % à 100 ns et 0,0134491 % à 50 ns ; WE=0, masse inchangée. IE suit ku²/2 à moins de 0,000065 % de E0. La période analytique est retrouvée à 0,008975 % puis 0,0022395 %. Les colonnes nodales et impulsions dépassent encore 1 % : environ 2,319 % puis 1,159 %, compatible avec un décalage de demi-pas, sans prouver ni corriger son origine. Les huit diagnostics à 1 % échoués (quatre par cas) figurent dans retained_limitations.json. Aucun succès uniforme à 1 % n'est affirmé.

Ces résultats vérifient un oscillateur élastique libre limité aux conditions testées et aux tolérances déclarées. Ils ne qualifient pas l'inertie libre après fracture, la dissipation mixte ni la pénétration d'un avion.

## 6. Contradictions et informations manquantes

Restent ouverts : le phasage exact TH, la désignation REACX force/impulsion, les cinq échecs stricts OFF/FX de F, la conservation numérique du réservoir tangentiel lors de désactivation complète, les échecs d'inertie et angles et les points non couverts de E. Réutiliser son review sauvegardé plutôt que recalculer. Gf30 est une hypothèse, Gf15/60 différés ; convention nominale/vraie NASA non identifiée.

H resserrera d'abord le témoin libre élastique à 25 et 12,5 ns, avec critères bruts à 1 %, puis pourra déclarer un témoin neuf de rupture normale libre seulement si ce contrôle passe et si sa référence analytique travail/impulsion/énergie est vérifiée. Aucun calcul de fracture libre exécuté en G. Impact Boeing/façade complet, feu et effondrement ne sont pas atteints. Localisation en flexion après fracture complète non validée ; température imposée ≠ incendie calculé ; Blender reste une visualisation.

## Reproduction, contrôle et publication

Configuration JSON, graines sans tirage aléatoire, fonctions sérialisées, scripts générateurs et d'audit, journaux, empreintes des exécutables, CSV bruts et comparaisons analytiques sont conservés. Summary : verification_r1/summary.json. Vérification sans moteur : `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_table_free.py verify`. Le manifeste épingle les artefacts ; le harnais et les anciens fichiers sont contrôlés avant/après. La vérification d'intégrité ne valide pas la physique du WTC1.

F+G atteint la cadence de deux itérations. Publication autorisée sur WTC-simu2026 ; ancienne release E et ses archives conservées. La cadence reste pending 2/2 jusqu'à vérification du dépôt distant, des archives et des deux CI. Aucun post sur X.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# Passation WTC1 — G terminée, H suivante

Lire AGENTS.md puis harness/state.json (prioritaire), ce fichier et data/impact_i02i_h_plan_from_g.json. Contrôle du harnais avant/après ; aucune archive rescannée ni ancien solveur relancé.

G : six états neufs, 18 jobs, {s['runtime_seconds']:.3f} s, {s['case_checks_passed']}/{s['case_checks_total']} critères et 8/8 comparaisons. Résidu X après rupture imposée : F N800 0,192454 % → N1600 0,0962401 % → N3200 0,0481333 %, identique aux caps 100/50 ns ; soutient l'origine tabulée sans établir le code interne. IE finale 0,03 J, forces X post-OFF nulles.

Oscillateur libre élastique sans fracture, m mobile 0,1 g, k=21500 N/mm, v0=1 mm/ms, T=0,0135506659245 ms, E0=0,00005 J, P0=0,1 N ms ; huit périodes. u erreur 0,450436/0,112566 %, bilan énergie 0,0537857/0,0134491 %, à 100/50 ns. Impulsion brute/nodal/global encore 2,319/1,159 % : succès au seuil déclaré 3 %, huit diagnostics stricts 1 % échoués conservés, aucun déphasage corrigé. TH/REACX documentation force vs runtime impulsion toujours contradictoire.

H : pré-déclarer d'abord mêmes témoins neufs à 25 et 12,5 ns, tous champs bruts au seuil 1 %, momentum initial inclus. Si succès, dériver/vérifier référence pièce par pièce d'un témoin neuf de rupture normale libre (m=0,1 g, v0Y=30 mm/ms, E0=0,045 J, travail normal hypothétique 0,03 J, v finale idéale √300 mm/ms), puis seulement déclarer calcul borné. Pas de cisaillement stocké ni de changement de propriété sur état endommagé. Conserver les anciens contrôles et échecs F ; G ne ferme pas les sensibilités/couvertures E ou les deux conventions NASA. Gf15/60 différés.

Rapport/results : wtc1_simulation_v8/output/impact_i02i_table_free/rapport_impact_i02i_table_free.md et verification_r1/summary.json ; {count} anciens fichiers épinglés. Vérification sans solveur : complete_impact_i02i_table_free.py verify. V11F/V11R/V11S conservés. Boeing complet/feu/effondrement non validés ; flexion post-fracture non validée ; température imposée ≠ incendie ; Blender visualisation.

GitHub : F+G pending 2/2 avant confirmation distante, cadence réelle dans harness/publication_cycle.json. Dernière release E conservée. Après confirmation F+G, H sera 1/2 ; auteur WTC-simu2026 et administration privée exclue. Aucun envoi X autorisé.
''',encoding='utf-8',newline='\n')
    g.dump(OUT/'release_audit.json',{'created_utc':g.NOW(),'pass':True,'definition':'Bounded G integrity, conservative predeclared gates and stricter failed diagnostics retained',
        'old_files_preserved':count,'harness':hv,'summary_sha256':g.sha(SUMMARY),'report_sha256':g.sha(REPORT),'handoff_sha256':g.sha(HANDOFF),
        'free_fracture_qualified':False,'physical_propagation_qualified':False})
    g.dump(OUT/'harness_after_artifacts.json',g.harness())
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,HANDOFF,PLAN]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_impact_i02i_table_free.py','audit_impact_i02i_table_free.py','complete_impact_i02i_table_free.py']]
    g.dump(OUT/'artifact_manifest.json',{'created_utc':g.NOW(),'files':[{'path':g.rel(p),'bytes':p.stat().st_size,'sha256':g.sha(p)} for p in sorted(set(paths))],
        'exclusions':['self','post-registration verification','mutable harness administration']})

def register():
    assert REPORT.exists() and HANDOFF.exists() and (OUT/'artifact_manifest.json').exists()
    preservation();s=json.loads(SUMMARY.read_text(encoding='utf-8'))
    for n in g.f.ADMIN:assert g.sha(ROOT/'harness'/n)==g.sha(OUT/('before_'+Path(n).name)),'Concurrent administrative change'
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'));cadence=json.loads((ROOT/'harness/publication_cycle.json').read_text(encoding='utf-8'))
    assert state['current_iteration']=='IMPACT-I02I-F' and cadence['pending_iterations']==['IMPACT-I02I-F']
    when=g.NOW();status='completed_bounded_table_resolution_and_free_elastic_controls_with_stricter_raw_accuracy_open'
    record={'experiment_id':'WTC1-IMPACT-I02I-G','registered_at':when,'status':status,
        'configuration':g.rel(CFG),'report':g.rel(REPORT),'results':g.rel(SUMMARY),'handoff':g.rel(HANDOFF),
        'artifact_manifest':g.rel(OUT/'artifact_manifest.json'),'source_manifest':g.rel(OUT/'source_manifest.json'),
        'publication_verification':g.rel(OUT/'publication_verification.json'),'H_plan':g.rel(PLAN),
        'cases':6,'case_checks_passed':s['case_checks_passed'],'case_checks_total':s['case_checks_total'],
        'comparison_checks_passed':s['comparison_checks_passed'],'comparison_checks_total':s['comparison_checks_total'],
        'runtime_seconds':s['runtime_seconds'],'old_files_preserved':preservation(),'free_fracture_qualified':False,
        'physical_propagation_qualified':False,'E_sensitivities_resolved':False,'source_convention_verified':False,
        'strict_1pct_failed_diagnostics':8,'table_residuals':{c['case']:c['G_raw_residual_fraction'] for c in s['comparisons']},
        'next_iteration':'IMPACT-I02I-H','github_pending_iterations':2}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as file:file.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-G',current_status=status,next_iteration='IMPACT-I02I-H',updated_at=when,
        next_objective='Réutiliser G : résidu de trajectoire imposée ~1/N ; oscillateur libre élastique vérifié aux seuils déclarés, diagnostics bruts impulsion/vitesse à 1 % encore échoués. H : états neufs à 25/12,5 ns, critères bruts 1 % et P0 inclus ; si succès dériver référence puis déclarer témoin neuf de rupture normale libre. Conserver échecs OFF/FX F, toutes sensibilités/couvertures E, conventions NASA, Gf30 hypothétique et Gf15/60 différés. Paire F+G GitHub due après contrôle distant/archives/CI. V11F/V11R/V11S préservés.')
    state['impact_i02i_g_key_results']={k:record[k] for k in ['cases','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','runtime_seconds','old_files_preserved','free_fracture_qualified','physical_propagation_qualified','E_sensitivities_resolved','source_convention_verified','strict_1pct_failed_diagnostics','table_residuals','github_pending_iterations']}
    state['validated_artifacts'].update(impact_i02i_g_report=g.rel(REPORT),impact_i02i_g_results=g.rel(SUMMARY),impact_i02i_g_handoff=g.rel(HANDOFF),impact_i02i_g_publication_verification=g.rel(OUT/'publication_verification.json'),impact_i02i_h_plan=g.rel(PLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-F','IMPACT-I02I-G'],pending_count=2,next_publication_after='Publish verified F+G; reset cadence only after remote tree, release digests and both CI pass',updated_at=when)
    g.dump(ROOT/'harness/publication_cycle.json',cadence);temp=ROOT/'harness/state_i02ig_pending.json';g.dump(temp,state);temp.replace(ROOT/'harness/state.json')
    verify(write=True)

def verify(write=False):
    count=preservation();m=json.loads((OUT/'artifact_manifest.json').read_text(encoding='utf-8'))
    bad=[r['path'] for r in m['files'] if g.sha(ROOT/r['path'])!=r['sha256']]
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'));old=json.loads((OUT/'before_state.json').read_text(encoding='utf-8'))
    reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines()
    cadence=json.loads((ROOT/'harness/publication_cycle.json').read_text(encoding='utf-8'));s=json.loads(SUMMARY.read_text(encoding='utf-8'));hv=g.harness()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    checks={'artifact_hashes':not bad,'old_pinned_files_preserved':True,'registry_prefix':reg.startswith(prefix),
        'one_G_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-G',
        'state_G_to_H':state['current_iteration']=='IMPACT-I02I-G' and state['next_iteration']=='IMPACT-I02I-H',
        'prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS',
        'report_handoff_plan':REPORT.exists() and HANDOFF.exists() and PLAN.exists(),
        'cadence':cadence['pending_iterations'] in [['IMPACT-I02I-F','IMPACT-I02I-G'],[]] and cadence['pending_count']==len(cadence['pending_iterations']),
        'declared_gates_pass':s['all_scientific_checks_pass'],
        'strict_1pct_failures_retained':sum(sum(not ok for ok in v.get('strict_raw_1pct_diagnostics',{}).values()) for v in s['cases'].values())==8,
        'inherited_F_failures_retained':len(s['F_same_row_OFF_FX_failures_still_open'])==5,
        'unqualified_physics':not s['free_fracture_qualified'] and not s['physical_propagation_qualified'] and not s['E_sensitivities_resolved'],
        'no_old_solver_rerun':not s['old_solvers_rerun']}
    result={'created_utc':g.NOW(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(m['files']),
        'manifest_failures':bad,'old_files_checked':count,'harness':hv,'all_declared_G_gates_pass':s['all_scientific_checks_pass'],
        'strict_raw_1pct_failures':8,'free_fracture_qualified':False,'physical_propagation_qualified':False,
        'next_iteration':'IMPACT-I02I-H','github_pending_iterations':cadence['pending_count']}
    assert result['pass'],result
    if write:g.dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()
