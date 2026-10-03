"""Finish, register and verify I02I-E only from existing saved audits.

Integrity completion never promotes failed scientific or missing-coverage
gates. Publication cadence is advanced after verified local artifacts exist.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from run_impact_i02i_sensitivity import ROOT,CFG,OUT,C,D,PLAN,NOW,sha,dump,rel,harness

SUMMARY=OUT/'verification_r1/summary.json'
REPORT=OUT/'rapport_impact_i02i_sensitivity.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_E_HANDOFF.md'
CADENCE=ROOT/'harness/publication_cycle.json'

def preservation():
    rows=json.loads((OUT/'preservation_before.json').read_text(encoding='utf-8'))['files']
    bad=[r['path'] for r in rows if sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(rows)

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists(),'Preserve completed iterations'
    s=json.loads(SUMMARY.read_text(encoding='utf-8'));cfg=json.loads(CFG.read_text(encoding='utf-8'));count=preservation();hv=harness()
    assert s['completed_audited_cases']>0 and s['no_old_solver_rerun'] and not s['physical_propagation_qualified']
    assert all(v['case_audit']['gates']['preflight_and_no_unreviewed_engine_warnings'] and v['case_audit']['gates']['normal_termination'] for v in s['cases'].values())
    case_lines=[];comparison_lines=[];failures=[]
    serialized=[]
    for case in cfg['cases']:
        p=OUT/case['id']/'generation.json'
        if p.exists():serialized.extend(json.loads(p.read_text(encoding='utf-8')).get('normal_curve_serialization_corrections',[]))
    max_serialization_change=max((abs(v['relative_gap_change']) for v in serialized),default=0.)
    assert max_serialization_change<=1e-10,'Declared precision correction bound'
    rejected_seconds=sum(r['seconds'] for p in (OUT/'rejected_preflight').rglob('execution.json') for r in json.loads(p.read_text(encoding='utf-8')))
    for name,v in s['cases'].items():
        r=v['case_audit'];m=r['metrics'];q=v['comparison'];coverage=q['coverage']
        bad=[k for k,ok in r['gates'].items() if not ok];cbad=[k for k,ok in q['checks'].items() if not ok]
        failures.append({'case':name,'case_gates':bad,'comparison_gates':cbad})
        case_lines.append(f"| {name} | {100*m['maximum_kinetic_to_internal_significant_window']:.5g} | {100*m['energy_residual_fraction']:.5g} | {100*m['independent_actuator_work_error_fraction']:.5g} | {r['final_state']['displacement_mm']:.7g} | {r['final_state']['nodal_advance_mm']:.7g} | {', '.join(bad) or 'aucun'} |")
        pct=lambda x:'non évalué' if x is None else f'{100*x:.5g}'
        comparison_lines.append(f"| {name} | {pct(q['maximum_force_difference_fraction'])} | {pct(q['maximum_work_difference_fraction'])} | {pct(q['maximum_ctoa_difference_fraction'])} | {coverage['displacement_points_assessed']}/{coverage['displacement_points_requested']} | {coverage['advance_points_assessed']}/{coverage['advance_points_requested']} | {', '.join(cbad) or 'aucun'} |")
    dump(OUT/'retained_failed_and_unassessed_gates.json',{'created_utc':NOW(),'cases':failures,'missing_cases':s['missing_cases'],'unassessed_is_not_pass':True})
    speed_lines=[]
    for name,v in s['cases'].items():
        if v['case']['factor']=='speed':
            baseline=json.loads((C/'verification_r2'/v['case']['cached_C_case']/'case_audit.json').read_text(encoding='utf-8'))
            speed_lines.append(f"- {v['case']['interpretation']} : max KE/IE passe de {100*baseline['metrics']['maximum_kinetic_to_internal_significant_window']:.6g} % à {100*v['case_audit']['metrics']['maximum_kinetic_to_internal_significant_window']:.6g} %, avec seuil déclaré 1 %. Comparaison valable sur les déplacements et événements effectivement couverts, sans extrapolation.")
    domain_lines=[]
    for name,v in s['cases'].items():
        if v['case']['factor']=='domain':
            r=v['case_audit'];meta=json.loads((OUT/name/'generation.json').read_text(encoding='utf-8'));threshold=meta['guards'][0]['threshold_mm']
            domain_lines.append(f"- {v['case']['interpretation']} : domaine étendu, dernière ouverture/distance de garde maximale {r['metrics']['max_guard_distance_mm']:.7g} mm pour seuil {threshold:.7g} mm ; max KE/IE {100*r['metrics']['maximum_kinetic_to_internal_significant_window']:.6g} %, déplacement terminal enregistré {r['final_state']['displacement_mm']:.7g} mm, avance nodale {r['final_state']['nodal_advance_mm']:.7g} mm. La garde est un arrêt numérique avec dépassement échantillonné, pas une limite physique exacte.")
    report=f'''# WTC1 — IMPACT-I02I-E : sensibilités bornées sur éprouvettes

## 1. Faits observés ou transcrits

{s['completed_audited_cases']}/{s['planned_cases']} nouveaux cas ont leurs trois exécutables terminés et leur audit sauvegardé. Temps des exécutables des cas acceptés : {s['runtime_seconds']:.3f} s ({s['runtime_seconds']/60:.3f} min), plus {rejected_seconds:.3f} s de précontrôle rejeté. Cas non audités : {', '.join(s['missing_cases']) or 'aucun'}. Configuration `{rel(CFG)}`, plan antérieur de D `{rel(PLAN)}`, résultats `{rel(SUMMARY)}`. Les coordonnées et la topologie sont conservées pour vitesse et pénalité ; l'extension du domaine raffiné est déclarée séparément. Deux préparations avant solveur ont été rejetées pour une comparaison tuples/listes ; les decks et scripts sont conservés dans `rejected_generation/`. Aucune physique n'a été calculée dans ces tentatives.

Un premier précontrôle de pénalité doublée a aussi été rejeté : arrondir δ0 à 12 chiffres significatifs vers le bas faisait dépasser à la pente de la fonction la raideur déclarée d'environ 6×10⁻¹³ relatif ; le starter tentait d'augmenter automatiquement K (avertissement 506). Ce starter et son script sont conservés dans `rejected_preflight/`. Les nouveaux états neufs écrivent δ0=peak sérialisé/K sérialisé, arrondi décimal vers le haut à 14 chiffres ; variation relative maximale d'ouverture {max_serialization_change:.9g}, sous la borne pré-déclarée 10⁻¹⁰. Kn, peak, Gf et aire initiale restent déclarés identiques. Aucun état endommagé n'est réutilisé et l'avertissement n'est pas autorisé pour masquer un changement de propriété.

Cette **vitesse est celle du chargement d'une éprouvette**, pas celle du Boeing. Les anciens impacts locaux à 198,03072 m/s ne sont ni modifiés ni relancés. Un succès sur ce coupon ne qualifie pas un avion contre une façade.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle NIST ou résultat officiel de l'événement n'est importé. Les fenêtres NASA bornées et leurs conversions sont celles des itérations A/B/C. Les deux interprétations engineering et true_total restent conservées ; aucune n'est déclarée être la convention expérimentale certaine. Les valeurs de courbe, unités initiales et conversions stress/déformation sont enregistrées dans chaque `generation.json`.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation des archives n'est testée. {count} fichiers antérieurs épinglés sont vérifiés par SHA-256 ; aucune archive source ni tout l'historique n'est rescanné. Les résultats B/C/D servent de références sauvegardées ; aucun ancien solveur ne tourne. La copie source NASA, les documents primaires et les anciens rendus restent en lecture seule.

## 4. Hypothèses propres au modèle, unités et critères

Éprouvette M(T) nominale : largeur 76,2 mm, longueur 300 mm, épaisseur 2,3 mm, fissure centrale initiale totale 25,4 mm. Coques QEPH24 avec Ismstr4, Ithick1, Iplas1, cinq points d'intégration, z et rotations bloqués ; bord inférieur y fixé et déplacement y supérieur quintique 0→1,2 mm. Matériau LAW36 : densité 0,00278 g/mm³, E=71400 MPa, ν=0,3 ; courbe NASA avec deux conventions conservées, sans remplacement d'un historique endommagé.

Unités : g/mm/ms/N, MPa=N/mm², énergie solveur N mm=mJ, énergie rapport J=0,001 N mm. Pénalités par aire initiale Kn=56000 et Kt=21500 N/mm³ en référence ; chaque connecteur reçoit K=penalité×aire initiale fixe (épaisseur initiale×largeur tributaire). Traction normale maximale hypothétique 495 MPa, Gf=30 N/mm maintenu ; δ0=traction/Kn, δf=2Gf/traction. Avec cette aire, l'intégrale normale est Gf×aire ; ce n'est pas une identification de fracture mixte. D montre que la suppression d'un effort tangent peut conserver du travail numérique dans IE.

Facteurs : durée 12→24 ms (vitesse moitié), Kn/Kt ×0,5 ou ×2 à géométrie identique, domaine raffiné ±22,86→±30,48 mm avec garde déplacée et largeur physique 76,2 mm inchangée. Aucun facteur n'est cumulé avec un autre dans un cas. h local=1,27 mm, Gf15/60 différés. Histoire demandée fixe 0,00001 ms, indépendante de la durée de chargement ; vérifier intervalle inférieur au pas minimum et nombre de lignes égal aux cycles. Aucun ajout de masse. Plafonds : 900 s/cas, 2400 s cumulées pour les exécutables.

Critères déclarés : max KE/IE ≤1 % sur toute fenêtre IE≥1 % du pic, résidu global énergie ≤0,5 %, travail indépendant des appuis ≤1 %, impulsion signée comparée au momentum ≤1 % des grandes impulsions d'appuis (résidu absolu aussi conservé), somme IE ressort ≤0,1 %, quadrature dense ressort ≤0,5 %. Comparaisons à déplacements communs : force ≤5 % du maximum des pics, travail ≤5 % du maximum des travaux finaux, angles à avances nodales exactes ≤10 %. Absence d'une avance ou d'un déplacement demandé demeure une absence ; le nouveau contrôle de couverture les rend visibles.

## 5. Résultats dérivés

Critères de cas : {s['case_checks_passed']}/{s['case_checks_total']}. Comparaisons : {s['comparison_checks_passed']}/{s['comparison_checks_total']}. Les échecs et non-évaluations sont conservés dans `{rel(OUT/'retained_failed_and_unassessed_gates.json')}`.

| Cas | Max KE/IE % | Résidu énergie % | Travail appuis erreur % | Dernier déplacement mm | Avance nodale moyenne mm | Critères de cas échoués |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(case_lines)}

| Variante / référence C | Écart force % | Écart travail % | Écart CTOA % | Déplacements couverts | Avances couvertes | Critères de comparaison échoués |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(comparison_lines)}

{chr(10).join(speed_lines)}

{chr(10).join(domain_lines)}

Les tableaux de comparaison donnent le maximum sur les seuls points réellement disponibles. Leur faible écart ne remplace pas une couverture manquante. Les événements de départ sont les premières lignes d'avance contiguë, conservées comme diagnostic distinct. Les derniers états sont les derniers enregistrements, pas une extrapolation à la fin demandée. Les CTOA sont des angles géométriques du chemin de fissure imposé, pas une mesure indépendante de tunnel de fissure 3D.

## 6. Contradictions, informations manquantes et suite

La convention de source, Gf réel, la dissipation mixte et la propagation physique restent non identifiés. Les maxima plastiques portent sur un sous-ensemble de coques près de la pointe ; leur borne ne vaut pas pour toute l'éprouvette. Une sensibilité de pénalité ou de domaine reflète une dépendance du modèle, pas une probabilité de l'événement. Le témoin D conserve une limite d'impulsion après suppression quand le pas augmente ; E ne remplace pas le témoin neuf à pas post-rupture contrôlé nécessaire avant un impact libre.

I02I-F devra traiter les sensibilités ou domaines encore ouverts à partir de ces résultats, puis vérifier le phasage force/état/impulsion et la libération d'énergie avant transfert à un sous-modèle d'impact libre. Réutiliser les courbes E ; ne pas relancer huit cas pour relire leurs résultats. Si une portion de campagne a été différée par le plafond, elle reste explicitement à exécuter depuis le plan initial. Gf15/60 restent différés tant que leurs dépendances sont ouvertes.

V11F froid et V11R/V11S préservés. Température imposée ≠ incendie calculé ; flexion après fracture complète non validée ; tests numériques ≠ validation de l'effondrement réel ; Blender reste une visualisation. D+E constituent la paire GitHub suivante, après vérification d'intégrité ; la confirmation administrative B+C déjà préparée doit être incluse. Aucun post sur X autorisé.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# WTC1 — IMPACT-I02I-E terminée, prochaine I02I-F

Lire AGENTS.md, harness/state.json, cette passation puis `{rel(OUT/'publication_verification.json')}`. État local prioritaire. Rapport `{rel(REPORT)}`, résultats `{rel(SUMMARY)}`, config `{rel(CFG)}`, plan D `{rel(PLAN)}`.

E : {s['completed_audited_cases']}/{s['planned_cases']} nouveaux cas audités, {s['runtime_seconds']/60:.3f} min exécutables acceptés (+{rejected_seconds:.3f} s starter rejeté), {s['case_checks_passed']}/{s['case_checks_total']} critères et {s['comparison_checks_passed']}/{s['comparison_checks_total']} comparaisons. Vitesse de chargement d'éprouvette moitié, Kn/Kt ×0,5/2, domaine raffiné ±30,48 mm ; deux conventions NASA, Gf30, QEPH24 Ismstr4 Ithick1 Iplas1, aire initiale fixe, histoires à chaque cycle. Cas non audités : {', '.join(s['missing_cases']) or 'aucun'}. Deux tentatives de comparaison de format rejetées avant solveur sont conservées. Précontrôle 506 rejeté pour arrondi δ0 : nouveaux decks de pénalité doublée sérialisent peak/K vers le haut à 14 chiffres, variation ≤{max_serialization_change:.6g}, borne 1e-10 pré-déclarée, aucune propriété d'état endommagé remplacée.

Réutiliser E et les audits C/D sauvegardés. F : traiter les sensibilités dominantes et couvertures manquantes puis préparer un témoin neuf à pas post-désactivation contrôlé avant impact libre ; D révèle travail tangent non récupéré et phasage OFF/FX d'un cycle, impulsion post-suppression non qualifiée. Lire `retained_failed_and_unassessed_gates.json` et les couvertures ; aucun point ni topologie absent ne doit être extrapolé. Gf15/60 restent hypothétiques et différés. Ne pas changer les propriétés d'un état endommagé. Aucune convention de source ni propagation Boeing/façade/pénétration historique qualifiée.

{count} anciens fichiers épinglés ; aucun ancien solveur relancé ou archive rescannée. Harnais PASS ; vérifier sans solveur avec `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_sensitivity.py --verify`. V11F/V11R/V11S préservés ; température imposée ≠ incendie, flexion post-fracture non validée, Blender visualisation.

Publication : `harness/publication_cycle.json` fait autorité, paire D+E due tant que distant/archives/CI ne sont pas vérifiés. Inclure métadonnées B+C préparées dans outputs/github_publication/anonymous_repository (ancien pin corrigé, aucune ancienne archive à reconstruire). Compte/identité WTC-simu2026, administration privée exclue, pas de post X. Préparer et vérifier tout avant éventuelle nouvelle authentification ; ne pas utiliser le connecteur Yoremi pour écrire.
''',encoding='utf-8',newline='\n')
    dump(OUT/'release_audit.json',{'created_utc':NOW(),'pass':True,'definition':'Integrity and saved bounded execution, no scientific gate promotion','old_files_preserved':count,'completed_cases':s['completed_audited_cases'],'missing_cases':s['missing_cases'],'config_sha256':sha(CFG),'summary_sha256':sha(SUMMARY),'report_sha256':sha(REPORT),'handoff_sha256':sha(HANDOFF),'source_convention_verified':False,'physical_propagation_qualified':False,'harness':hv})
    dump(OUT/'harness_after_artifacts.json',harness())
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,Path(__file__),ROOT/'wtc1_simulation_v8/scripts/run_impact_i02i_sensitivity.py',ROOT/'wtc1_simulation_v8/scripts/audit_impact_i02i_sensitivity.py',HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':NOW(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(paths))],'exclusions':['self','post-registration verification','mutable administrative harness state/registry/cadence'],'scope':'All E inputs, attempted/rejected artifacts, solver outputs, audits, scripts, report and handoff'})

def register():
    assert REPORT.exists() and HANDOFF.exists() and (OUT/'artifact_manifest.json').exists()
    s=json.loads(SUMMARY.read_text(encoding='utf-8'));preservation()
    for name in ['state.json','experiments/registry.jsonl','publication_cycle.json']:assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+Path(name).name)),'Concurrent harness change'
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'));cadence=json.loads(CADENCE.read_text(encoding='utf-8'));assert cadence['pending_iterations']==['IMPACT-I02I-D']
    status='completed_bounded_sensitivity_with_failed_or_unassessed_qualification_gates';when=NOW()
    record={'experiment_id':'WTC1-IMPACT-I02I-E','registered_at':when,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(SUMMARY),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'source_manifest':rel(OUT/'source_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'completed_cases':s['completed_audited_cases'],'planned_cases':s['planned_cases'],'missing_cases':s['missing_cases'],'case_checks_passed':s['case_checks_passed'],'case_checks_total':s['case_checks_total'],'comparison_checks_passed':s['comparison_checks_passed'],'comparison_checks_total':s['comparison_checks_total'],'runtime_seconds':s['runtime_seconds'],'old_files_preserved':preservation(),'source_convention_verified':False,'physical_propagation_qualified':False,'next_iteration':'IMPACT-I02I-F','github_pending_iterations':2}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-E',current_status=status,next_iteration='IMPACT-I02I-F',next_objective='Réutiliser E sauvegardée : traiter sensibilités vitesse/pénalité/domaine et couvertures encore ouvertes. Préparer témoin neuf à pas post-rupture contrôlé et vérifier phasage force/état/impulsion/libération d’énergie avant impact libre. Deux conventions NASA, Gf30 hypothétique, aire initiale fixe, QEPH et bilans appuis conservés ; Gf15/60 différés. Paire D+E GitHub due après contrôle distant/archives/CI. V11F/V11R/V11S préservés.',updated_at=when)
    state['impact_i02i_e_key_results']={k:record[k] for k in ['completed_cases','planned_cases','missing_cases','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','runtime_seconds','old_files_preserved','source_convention_verified','physical_propagation_qualified','github_pending_iterations']}
    state['impact_i02i_e_key_results']['inertia_fractions_by_case']={k:v['case_audit']['metrics']['maximum_kinetic_to_internal_significant_window'] for k,v in s['cases'].items()}
    state['impact_i02i_e_key_results']['failed_case_gates_by_case']={k:[n for n,ok in v['case_audit']['gates'].items() if not ok] for k,v in s['cases'].items()}
    state['validated_artifacts'].update(impact_i02i_e_report=rel(REPORT),impact_i02i_e_results=rel(SUMMARY),impact_i02i_e_handoff=rel(HANDOFF),impact_i02i_e_publication_verification=rel(OUT/'publication_verification.json'))
    cadence.update(pending_iterations=['IMPACT-I02I-D','IMPACT-I02I-E'],pending_count=2,next_publication_after='Pair D+E verified locally; publication due; include saved B+C confirmation metadata',updated_at=when)
    dump(CADENCE,cadence);temp=ROOT/'harness/state_i02ie_pending.json';dump(temp,state);temp.replace(ROOT/'harness/state.json');verify(write=True)

def verify(write=False):
    count=preservation();manifest=json.loads((OUT/'artifact_manifest.json').read_text(encoding='utf-8'));bad=[r['path'] for r in manifest['files'] if sha(ROOT/r['path'])!=r['sha256']]
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'));old=json.loads((OUT/'before_state.json').read_text(encoding='utf-8'));reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines();cadence=json.loads(CADENCE.read_text(encoding='utf-8'));s=json.loads(SUMMARY.read_text(encoding='utf-8'));hv=harness()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy']
    checks={'new_artifact_hashes':not bad,'old_pinned_files_preserved':True,'registry_prefix':reg.startswith(prefix),'one_E_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-E','correct_state':state['current_iteration']=='IMPACT-I02I-E' and state['next_iteration']=='IMPACT-I02I-F','prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS','artifacts_exist':REPORT.exists() and HANDOFF.exists(),'cadence_pending_or_verified_published':cadence['pending_iterations']==['IMPACT-I02I-D','IMPACT-I02I-E'] or cadence['last_published_iteration']=='IMPACT-I02I-E','bounded_claims':not s['source_convention_verified'] and not s['physical_propagation_qualified'],'no_old_solver_rerun':s['no_old_solver_rerun']}
    versions={sha(ROOT/'wtc1_simulation_v8/scripts/run_impact_i02i_sensitivity.py')}
    versions.update(sha(p) for folder in ['rejected_generation','rejected_preflight'] for p in (OUT/folder).glob('*.py'))
    checks['generator_versions_preserved']=all(json.loads(p.read_text(encoding='utf-8'))['generator_sha256'] in versions for p in OUT.glob('*/generation.json') if p.parent.name in s['cases'])
    result={'created_utc':NOW(),'pass':all(checks.values()),'checks':checks,'manifest_files_checked':len(manifest['files']),'manifest_failures':bad,'old_files_checked':count,'harness':hv,'scientific_all_case_gates_pass':s['all_case_gates_pass'],'scientific_all_comparison_gates_pass':s['all_comparison_gates_pass'],'source_convention_verified':False,'physical_propagation_qualified':False,'next_iteration':'IMPACT-I02I-F','github_pending_iterations':cadence['pending_count'],'github_remote_pair_confirmed':cadence['last_published_iteration']=='IMPACT-I02I-E'}
    assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()

if __name__=='__main__':main()
