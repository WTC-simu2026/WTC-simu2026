"""I durable bounded results, including four raw precision gate failures."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import run_impact_i02i_free_return as i
h=i.h;ROOT,OUT,CFG=i.ROOT,i.OUT,i.CFG
SUMMARY=OUT/'verification_r1/summary.json'
REPORT=OUT/'rapport_impact_i02i_free_return.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_IMPACT_I02I_I_HANDOFF.md'
JPLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_j_plan_from_i.json'
OBJECTIVE='J : diagnostiquer la précision des sorties sauvegardées T01/CSV et vérifier indépendamment IE-U avant nouveau mode mixte. Conserver les quatre échecs I de non-négativité brute et tous les échecs E/F/G ; ne pas corriger, déphaser, clipper ou réétiqueter une sortie. H+I GitHub due après contrôle distant/archives/CI. Conventions NASA ouvertes, Gf30 hypothétique, Gf15/60 différés ; Boeing/façade/feu/effondrement non qualifiés. V11F/V11R/V11S préservés.'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def preservation():
    rows=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in rows if h.sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad;return len(rows)
def failure_map(s):return {name:[k for k,v in r['checks'].items() if not v] for name,r in s['cases'].items()}

def prepare():
    assert not REPORT.exists() and not HANDOFF.exists() and not JPLAN.exists(),'Keep artifacts'
    s=read(SUMMARY);cfg=read(CFG);r=read(OUT/'reference_verification.json');d=read(OUT/'precision_diagnostic_r1.json')
    assert not s['all_declared_checks_pass'] and all(v==['retained_nonnegative'] for v in failure_map(s).values())
    assert s['case_checks_passed']==170 and s['case_checks_total']==174 and s['comparison_checks_passed']==16
    assert r['pass'] and h.sha(OUT/'reference_verification.json')==cfg['reference_guard_sha256']
    count=preservation();hv=h.harness();jobs=[a for p in OUT.glob('*/execution.json') for a in read(p)]
    assert len(jobs)==12 and all(j['returncode']==0 for j in jobs) and s['runtime_seconds']<=600
    plan={'id':'IMPACT-I02I-J_PLAN_FROM_I','created_utc':h.NOW(),'seed':1102018,'random_draws':0,
        'saved_I_summary':h.rel(SUMMARY),'saved_I_sha256':h.sha(SUMMARY),
        'scope':'Resolve output-precision observability before mixed free histories; do not change I failed gates',
        'first_steps':['Read saved TFILE/4 binary structure and converter format from local primary evidence; preserve originals',
            'Independently decode saved T01 if format is established; compare IE, spring IE and force with original CSV without rerun',
            'Predeclare uncertainty-aware new diagnostic before assessment; original fixed 1e-10 J sign gates remain failed',
            'If fresh high-precision output is needed, verify keyword/source support and declare new cases and gates before engine; never alter I or a damaged state'],
        'avoid':['No old solver rerun for publication','No clipping negative work','No selected NASA convention','No fitted time phase'],
        'unchanged':['E sensitivities/coverage','F five OFF/FX failures','G eight historical strict failures',
            'I four raw retained_nonnegative failures','Gf30 hypothetical and Gf15/60 deferred','V11F/V11R/V11S'],
        'deferred':['Mixed free fracture','Plate/connection wavefield and physical calibration','Boeing/facade/fire/collapse'],
        'publication':'H+I ready after I integrity; next pair J+K after two documented and verified iterations'}
    h.dump(JPLAN,plan)
    lines=[]
    for name,c in s['cases'].items():
        a=c['metrics'];f=a['fractions'];lines.append(f"| {name} | {a['maximum_gap_mm']:.10g} | {a['final_v_mm_per_ms']:.10g} | {a['final_IE_J']:.10g} | {100*f['initial_P_impulse']:.7g} | {100*f['energy_balance']:.7g} | {a['minimum_retained_J']:.7g} |")
    ar=cfg['references']['NORMAL_ARREST_RETURN'];el=cfg['references']['NORMAL_SUBPEAK_RETURN']
    report=f'''# WTC1 — IMPACT-I02I-I : arrêt, décharge avec historique et retour

## 1. Faits directement observés ou transcrits

Quatre états neufs, 12 exécutables, {s['runtime_seconds']:.6f} s cumulées. Terminaison normale, aucune alerte starter, masse 0,2 g constante, aucun ajout de masse, une ligne TH par cycle. Le déplacement mobile Y est libre ; seul vY initial est prescrit, X/Z et rotations bloqués. OFF reste 1, aucun cas ne se sépare. Le gap reste positif après la ligne initiale : aucune compression dans la fenêtre calculée.

Les critères sont pré-déclarés dans impact_i02i_i_predeclaration.json après la référence indépendante et avant tout moteur. Résultat : **170/174 critères de cas, 16/16 comparaisons, 16/16 contrôles de référence**. Les quatre échecs concernent exclusivement retained_nonnegative : IE−U descend sous −1e−10 J dans chaque cas. Ils restent échoués ; le succès intégral des critères déclarés vaut false. Aucun seuil, temps ou signe n'est changé après résultat.

## 2. Résultats d'un modèle officiel

Aucun nouveau résultat NIST ni interprétation historique ajouté. La documentation TYPE8/H2 et TH issue des manifestes H/C est réutilisée comme définition logicielle. REACX/REACY est appelé force dans la documentation mais compatible ici avec une impulsion cumulative N ms, vérifiée par intégration de −Fy dt. Le centrage exact de la version TH installée reste non établi. Aucun décalage des séries n'est effectué.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d'archive ni vidéo inspectée. {count} fichiers précédents vérifiés depuis les inventaires sauvegardés, sans archive rescannée. H, les anciens résultats E/F/G, V11F froid, V11R et V11S différée sont conservés. Aucun ancien solveur relancé.

## 4. Hypothèses propres au modèle, propriétés, unités et historique

Liaison numérique TYPE8 à deux nœuds : aire 1 mm², masse mobile m_g=0,1 g, masse d'appui 0,1 g, inertie 0,001 g mm²/nœud, rotations bloquées. Kn=56000 N/mm, Kt=21500 N/mm, pic normal 495 N, Gf=30 N/mm hypothétique ; δ0=0,00883928571429 mm, δf=0,121212121212 mm, pente d'adoucissement ks=4404,97917319 N/mm. H2 normal/tangentiel ; aucune viscosité. La loi de désactivation complète est active mais n'est pas atteinte. Aucune modification de propriété endommagée, restart ou remise à zéro d'historique.

Unités d'entrée : g, mm, ms, N ; N=g mm/ms², N ms=g mm/ms. N mm=mJ et J=0,001 N mm. Une vitesse en mm/ms vaut numériquement celle en m/s ; v0=20 et √20≈4,472135955 concernent uniquement ces témoins, pas l'avion. Le nom delta_max désigne le maximum historique du gap, distinct de la masse m_g.

L'enveloppe est F_env=Knδ pour δ≤δ0, puis ks(δf−δ). En décharge : **F=max(0,F_env(delta_max)+Kn(δ−delta_max))**. delta_max ne décroît jamais. Travail de chargement W(delta_max)=∫F_env dδ ; énergie récupérable U=F²/(2Kn). Travail numérique non récupéré D=W(delta_max)−F_env(delta_max)²/(2Kn). Référence IE=D+U, KE=m_g v²/2 ; multiplier ces énergies N mm par 0,001 pour J. D est une partition de la loi numérique, sans identification à une chaleur, fissure réelle ou dissipation physique mesurée.

Référence d'arrêt : E0=20 N mm=0,02 J, P0=2 N ms ; supérieure au pic élastique mais inférieure aux 30 N mm de séparation. ω=√(Kn/m_g), λ=√(ks/m_g). Avant le pic : δ=v0 sin(ωt)/ω. En adoucissement, x=δf−δ=x0 cosh(λτ)−vpic sinh(λτ)/λ. À l'arrêt xturn=√(2(Gf A−E0)/ks), δturn={ar['turning_gap_mm']:.12g} mm, Fturn={ar['force_at_turn_N']:.12g} N. Décharge élastique depuis cet état : δ=δres+(Fturn/Kn)cos(ω(t−tturn)), avec δres={ar['residual_gap_mm']:.12g} mm ; après annulation de force, δ=δres+vretour(t−tzero), vretour={ar['release_velocity_mm_per_ms']:.12g} mm/ms.

tturn={ar['turn_time_ms']:.12g} ms, tzero={ar['zero_force_time_ms']:.12g} ms. Fin demandée 0,012 ms, première compression prédite {ar['positive_domain_end_ms']:.12g} ms : marge positive vérifiée avant moteur. Uturn={ar['recoverable_at_turn_J']:.12g} J ; après décharge IE=D={ar['retained_work_J']:.12g} J, KE=Uturn, WE=0. La force nulle à gap positif provient de l'historique de décharge, sans OFF.

Contrôle sous pic : E0=0,001 J < 0,002187723214 J de pic élastique, P0=0,4472135955 N ms. Référence sinusoïdale réversible, δmax={el['turning_gap_mm']:.12g} mm, tturn={el['turn_time_ms']:.12g} ms, D=0. Fin demandée 0,004 ms avant la première compression à {el['positive_domain_end_ms']:.12g} ms. Les deux caps sont 25/12,5 ns, contre 50/25 ns pour l'arrêt endommagé.

Référence contrôlée sans moteur : intégration RK4 directe de m_g δ̈=−F avec maximum historique, 4096/8192 pas ; quadrature indépendante du temps jusqu'à l'arrêt, 512/1024/2048/4096 subdivisions ; identité énergétique, équation du mouvement par différences finies, continuités, non-négativité et monotonie de D théorique. Le changement de variable δ=δturn−y² supprime la singularité intégrable du temps à l'arrêt. Tous ces contrôles passent avant déclaration.

Critères : gap/vitesse/force/momentum/impulsions brutes ≤1 % de l'amplitude déclarée ; IE, KE, travail intégré, U, D et bilan ≤0,5 % de E0 ; signe brut IE−U≥−1e−10 J. J_appui=m_g v−P0 ; le résidu audité est J1+J2+P0−P_global. Travail externe nul à l'appui stationnaire ; IE comparée séparément à l'intégrale Fy dδ et à IE(delta,delta_max). Retour repéré par changement de signe de la vitesse, sans ajuster le temps des séries. Comparaisons aux temps communs pré-déclarés couverts, sans extrapolation.

## 5. Résultats dérivés

| Cas | Gap maximal (mm) | Vitesse finale (mm/ms) | IE finale (J) | Résidu impulsion (%) | Bilan énergie (%) | Minimum IE−U (J) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

L'arrêt endommagé restitue environ 0,0007866 J et conserve environ 0,0192134 J de travail numérique. Sa force devient nulle après la décharge, OFF=1, puis son retour se poursuit librement dans le domaine positif. Le contrôle sous pic retrouve la référence réversible aux seuils d'amplitude et d'énergie. Réduire le pas réduit les résidus bruts d'impulsion approximativement de moitié ; maximum 0,935461 % dans le contrôle 25 ns. Les comparaisons entre caps passent à 0,5 %. Ces accords bornés ne ferment pas le critère strict de signe.

Diagnostic séparé, sauvegardé dans precision_diagnostic_r1.json : les minima négatifs, de −1,94060e−10 à −4,50801e−10 J, sont tous compatibles avec la borne de représentation issue du format CSV effectivement observé (.6e) et de TFILE/4 IEEE32 configuré. La borne comprend un demi-ULP binaire plus un demi-pas décimal sur IE et force, puis propage exactement l'erreur de force dans F²/(2Kn). Zéro appartient à l'intervalle de toutes les lignes négatives. **C'est une compatibilité conditionnelle avec l'arrondi, pas la preuve de l'algorithme interne ni une réussite du critère.** Les valeurs brutes restent sauvegardées sans clipping. L'étape J établira d'abord l'observabilité de IE−U à partir des sorties binaires existantes.

## 6. Contradictions et informations manquantes

Les quatre échecs de signe I restent ouverts, malgré de faibles amplitudes et une explication par arrondi plausible. Le sous-modèle n'est donc pas qualifié par l'ensemble des critères déclarés. Les cinq échecs mixtes OFF/FX de F, le réservoir tangentiel supprimé avec l'élément, les huit diagnostics historiques G, le centrage TH et les définitions REACX/REACY restent ouverts. Toutes sensibilités d'inertie/angle et couvertures E restent inchangées. Les deux conventions NASA ne sont pas identifiées ; Gf30 reste hypothétique et Gf15/60 différés.

Aucune plaque, onde de connexion réelle, mode mixte libre ou fracture physiquement calibrée n'est ajouté. L'impact complet Boeing/façade, l'incendie et l'effondrement réel restent non qualifiés. La localisation en flexion après fracture complète n'est pas validée ; température imposée ≠ incendie calculé. Blender reste une visualisation tant que sa dynamique n'est pas reliée à des états mécaniques vérifiés.

## Reproduction et reprise

Configuration JSON, graine 1102017 sans tirage, scripts, référence, decks, exécutables hachés, versions, journaux, T01, CSV, comparaison, diagnostic et rapport conservés. Actions : initialize, référence, declare, run, audit, diagnostic, prepare puis register. Les quatre échecs sont un résultat audité, pas un échec d'intégrité du harnais. Le brouillon de référence qui a échoué lors de la sérialisation d'un booléen NumPy est conservé dans development_r0 ; aucun moteur ni fichier de résultats n'avait été produit alors. La correction ne change aucune équation ou seuil.

Vérification sans moteur : complete_impact_i02i_free_return.py verify. Prochaine étape J : lecture indépendante des T01/CSV sauvegardés et diagnostic de précision avant nouveaux états mixtes. Publication autorisée H+I après contrôle d'intégrité, en conservant les échecs. Aucun message X.
'''
    REPORT.write_text(report,encoding='utf-8',newline='\n')
    HANDOFF.write_text(f'''# Passation compacte — IMPACT-I02I-I vers J

Lire AGENTS.md puis harness/state.json (prioritaire), cette passation et impact_i02i_j_plan_from_i.json. I terminée comme campagne bornée auditable avec quatre échecs de signe brut ; prochaine étape J. H+I publication due, cadence exacte dans harness/publication_cycle.json.

I : quatre cas neufs, 12 jobs, {s['runtime_seconds']:.6f} s ; 170/174 critères, 16/16 comparaisons, 16/16 références. Seuls retained_nonnegative échouent dans les quatre cas ; jamais modifier leurs seuils ou déclarer all_declared_checks_pass. Aucun OFF/compression, masse et énergie globales vérifiées. Arrêt v0=20 : retour ≈−3,966 mm/ms, IE≈0,0192134 J, U finale 0 ; sous-pic v0=√20 : retour réversible borné. Minima IE−U −1,94e−10 à −4,51e−10 J compatibles avec arrondi, non prouvé.

Résultats : wtc1_simulation_v8/output/impact_i02i_free_return/verification_r1/summary.json ; rapport et precision_diagnostic_r1.json dans le même dossier. Configuration impact_i02i_i_predeclaration.json ; scripts *impact_i02i_free_return.py et diagnose_impact_i02i_return_precision.py. Vérifier sans moteur via complete_impact_i02i_free_return.py verify. {count} anciens fichiers épinglés, aucun recalcul ancien, sources lecture seule.

J : inspecter format TFILE/4 et convertisseur à partir de preuves primaires locales, décoder indépendamment T01 sauvegardés si possible, confronter IE/IE spring/F au CSV sans relance. Pré-déclarer tout nouveau diagnostic de précision ; conserver les quatre échecs I. Si précision supérieure nécessite moteur, vérifier support documentaire puis états neufs et plafonds annoncés. Aucun restart/changement de matériau endommagé/clipping/déphasage.

Conserver E/F/G, cinq OFF/FX F, huit diagnostics historiques G, REACX/REACY/centrage TH, conventions NASA, Gf30 hypothétique et Gf15/60 différés, V11F/V11R/V11S. Pas de qualification avion/façade/feu/effondrement, flexion post-fracture non validée, Blender visualisation. Publication suivante J+K après deux itérations vérifiées ; pas de post X.
''',encoding='utf-8',newline='\n')
    h.dump(OUT/'release_audit.json',{'created_utc':h.NOW(),'pass':True,'scope':'Artifact integrity and faithful preservation of successful and failed numerical gates',
        'old_files_preserved':count,'harness':hv,'summary_sha256':h.sha(SUMMARY),'failed_gates':failure_map(s),
        'all_numerical_gates_pass':False,'physical_propagation_qualified':False})
    h.dump(OUT/'harness_after_artifacts.json',h.harness())
    scripts=[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_impact_i02i_free_return.py','reference_impact_i02i_free_return.py',
        'audit_impact_i02i_free_return.py','diagnose_impact_i02i_return_precision.py','complete_impact_i02i_free_return.py']]
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,JPLAN,HANDOFF]+scripts
    h.dump(OUT/'artifact_manifest.json',{'created_utc':h.NOW(),'files':[{'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)} for p in sorted(set(paths))],
        'exclusions':['self','post-registration verification','mutable harness administration']})

def register():
    assert REPORT.exists() and HANDOFF.exists() and JPLAN.exists() and (OUT/'artifact_manifest.json').exists()
    count=preservation();s=read(SUMMARY)
    for name in h.g.f.ADMIN:assert h.sha(ROOT/'harness'/name)==h.sha(OUT/('before_'+Path(name).name)),'Concurrent state change'
    state=read(ROOT/'harness/state.json');cadence=read(ROOT/'harness/publication_cycle.json')
    assert state['current_iteration']=='IMPACT-I02I-H' and state['next_iteration']=='IMPACT-I02I-I' and cadence['pending_iterations']==['IMPACT-I02I-H']
    when=h.NOW();status='completed_bounded_normal_return_with_four_raw_energy_sign_failures'
    record={'experiment_id':'WTC1-IMPACT-I02I-I','registered_at':when,'status':status,'configurations':[h.rel(CFG)],
        'report':h.rel(REPORT),'results':h.rel(SUMMARY),'handoff':h.rel(HANDOFF),'artifact_manifest':h.rel(OUT/'artifact_manifest.json'),
        'source_manifest':h.rel(OUT/'source_manifest.json'),'publication_verification':h.rel(OUT/'publication_verification.json'),'J_plan':h.rel(JPLAN),
        'cases':4,'runtime_seconds':s['runtime_seconds'],'old_files_preserved':count,
        **{k:s[k] for k in ['case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','reference_checks_passed','reference_checks_total',
            'all_declared_checks_pass','numerical_normal_unload_verified','physical_fracture_calibrated','physical_propagation_qualified','mixed_mode_qualified','E_sensitivities_resolved','source_convention_verified']},
        'failed_gates':failure_map(s),'precision_compatible_not_proven':True,'next_iteration':'IMPACT-I02I-J','github_pending_iterations':2}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='IMPACT-I02I-I',current_status=status,next_iteration='IMPACT-I02I-J',next_objective=OBJECTIVE,updated_at=when)
    state['impact_i02i_i_key_results']={k:v for k,v in record.items() if k not in ['experiment_id','registered_at','status','configurations','report','results','handoff','artifact_manifest','source_manifest','publication_verification','J_plan','next_iteration']}
    state['validated_artifacts'].update(impact_i02i_i_report=h.rel(REPORT),impact_i02i_i_results=h.rel(SUMMARY),impact_i02i_i_handoff=h.rel(HANDOFF),
        impact_i02i_i_publication_verification=h.rel(OUT/'publication_verification.json'),impact_i02i_j_plan=h.rel(JPLAN))
    cadence.update(pending_iterations=['IMPACT-I02I-H','IMPACT-I02I-I'],pending_count=2,next_publication_after='H+I due after remote tree, digest and CI checks; keep four I failed gates',updated_at=when)
    h.dump(ROOT/'harness/publication_cycle.json',cadence);temp=ROOT/'harness/state_i02ii_pending.json';h.dump(temp,state);temp.replace(ROOT/'harness/state.json')
    verify(write=True)

def verify(write=False):
    count=preservation();manifest=read(OUT/'artifact_manifest.json');bad=[r['path'] for r in manifest['files'] if h.sha(ROOT/r['path'])!=r['sha256']]
    state=read(ROOT/'harness/state.json');old=read(OUT/'before_state.json');cadence=read(ROOT/'harness/publication_cycle.json');s=read(SUMMARY)
    prefix=(OUT/'before_registry.jsonl').read_bytes();reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();extra=reg[len(prefix):].decode('utf-8').splitlines()
    protected=[k for k in old if k.endswith('_key_results')]+['deferred_thermal_branch','source_archive','evidence_policy','open_limitations']
    pending=cadence['pending_iterations']==['IMPACT-I02I-H','IMPACT-I02I-I'] and cadence['pending_count']==2
    published=cadence['last_published_iteration']=='IMPACT-I02I-I' and cadence['pending_count']==0 and cadence['pending_iterations']==[]
    hv=h.harness();cfg=read(CFG)
    checks={'artifact_hashes':not bad,'old_pins_preserved':True,'registry_prefix':reg.startswith(prefix),
        'one_I_record':len(extra)==1 and json.loads(extra[0])['experiment_id']=='WTC1-IMPACT-I02I-I',
        'state_I_to_J':state['current_iteration']=='IMPACT-I02I-I' and state['next_iteration']=='IMPACT-I02I-J',
        'prior_states_preserved':all(state[k]==old[k] for k in protected),'harness_pass':hv['Status']=='PASS',
        'report_handoff_plan_exist':REPORT.exists() and HANDOFF.exists() and JPLAN.exists(),'cadence_pending_or_published':pending or published,
        'reference_guard':read(OUT/'reference_verification.json')['pass'] and h.sha(OUT/'reference_verification.json')==cfg['reference_guard_sha256'],
        'four_failed_sign_gates_retained':all(v==['retained_nonnegative'] for v in failure_map(s).values()) and not s['all_declared_checks_pass'],
        'audit_counts_unchanged':s['case_checks_passed']==170 and s['case_checks_total']==174 and s['comparison_checks_passed']==16,
        'no_gate_override':not read(OUT/'precision_diagnostic_r1.json')['gate_override'],
        'physical_limits_retained':not s['physical_fracture_calibrated'] and not s['physical_propagation_qualified'] and not s['mixed_mode_qualified'],
        'no_old_solver_rerun':not s['old_solvers_rerun']}
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'scope':'Integrity, not promotion of numerical or physical qualification',
        'checks':checks,'manifest_files_checked':len(manifest['files']),'manifest_failures':bad,'old_files_checked':count,'harness':hv,
        'case_checks':'170/174','comparison_checks':'16/16','reference_checks':'16/16','failed_gates':failure_map(s),
        'all_declared_checks_pass':False,'physical_propagation_qualified':False,'next_iteration':'IMPACT-I02I-J','github_pending_iterations':cadence['pending_count']}
    assert result['pass'],result
    if write:h.dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);a=p.parse_args();globals()[a.action]()
