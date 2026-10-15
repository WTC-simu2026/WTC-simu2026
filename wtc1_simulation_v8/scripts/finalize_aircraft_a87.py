"""Seal the approved isolated build and actual conditional controls, preserving failures."""
from build_aircraft_a87_null_relative import ROOT,OUT,CFG,AUTH,PLAN,CAND,guard,read,dump,sha,now
from build_aircraft_a54_graph import rel,harness
from read_aircraft_a81_th_binary import decode
from pathlib import Path
import json

REPORT=OUT/'rapport_aircraft_a87.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A87_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A88_2026-10-15.md'


def route():
    return ('AIRCRAFT-A88 : après publication A86+A87 vérifiée, analyser en lecture seule les nouveaux états '
        'A87 sauvegardés et leurs critères encore échoués. Distinguer la garde numérique des cas nuls, '
        'les régressions à seuils inchangés, le parcours commandé du coupon et ses qualifications physiques. '
        'Ne pas confondre durée locale en millisecondes et impact avion entier. Rechercher les valeurs de réaction, '
        'énergie et champs réellement disponibles avant une nouvelle proposition ; ne pas rejouer les diagnostics vérifiés. '
        'Aucun nouveau lancement automatique : les places utilisées A87 sont consommées et le CHECK conditionnel '
        'inutilisé ne devient pas un crédit générique. Toute autre modification du moteur ou exécution hors lot '
        'demande une proposition et un accord distinct. Conserver tolérances, budgets physiques, sources, sorties, '
        'critères échoués, cinqTYPE25 ignorés et107391avertissements. Meilleur impact entier0,0200001220703125s ; '
        'dix secondes physiques puis vidéo3D incomplètes.')


def assess():
    c=guard();assert not REPORT.exists()
    build=read(OUT/'build_finished.json');controls=read(OUT/'controls_execution_review.json')
    binary=CAND/'isolated_exec/engine_linux64_gf_ompi'
    assert build['build_success'] and build['exact_A86_null_relative_applied'] and sha(binary)==build['binary_sha256']
    assert controls['new_Starter']==0 and controls['new_Engine']<=4 and not controls['whole_dynamic_extension']
    rows=controls['results'];loopdir=OUT/'native/COMPRESSION_RUPTURE_RECLOSE';loop=None
    if (loopdir/'loop_review.json').exists():loop=read(loopdir/'loop_review.json')
    last=0.;states=0
    if loopdir.exists() and list(loopdir.glob('*T01')):
        meta,a,flat=decode(next(loopdir.glob('*T01')));last=float(a['time'][-1,0]);states=int((a['time'][:,0]>0).sum())
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[];binaries=0
    for row in old:
        p=ROOT/row['path'];st=p.stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
        if p.name=='engine_linux64_gf_ompi':assert sha(p)==row['sha256'];binaries+=1
    assert not changed
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),
        'changed_paths':changed,'prior_Engine_binaries_rehashed':binaries,'old_Engines_sources_and_failures_preserved':True,
        'old_native_replayed':False,'new_binary_regressions_not_old_binary_reruns':True})
    status='completed_tenth_isolated_Engine_and_bounded_controls__physical_qualification_incomplete'
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A87','status':status,'explicit_authorization':c['authorization'],
        'Engine_number':10,'build_success':True,'build_wall_s':build['wall_s_from_original_start'],'build_CPU':6,'build_cap_s':3600,
        'new_binary_sha256':sha(binary),'exact_A86_patch_applied':True,'new_Starter':0,'new_Engine':controls['new_Engine'],
        'maximum_Engine':4,'unconsumed_conditional_slots':controls['unconsumed_conditional_slots'],
        'unconsumed_slots_not_reassigned':True,'native_CPU':1,'each_cap_s':180,'native_cases':rows,
        'first_two_regressions_pass':len(rows)>=2 and all(r['pass'] for r in rows[:2]),
        'last_saved_coupon_time_ms':last,'saved_coupon_nonzero_states':states,
        'local_loop_review':rel(loopdir/'loop_review.json') if loop else None,
        'local_physical_qualification':bool(loop and loop['pass']),'whole_CHECK_executed':controls['whole_CHECK_executed'],
        'whole_dynamic_extension':False,'GPU_installation':False,'new_native_converter':0,
        'relative_degenerate_criterion_definition_changed':True,'physical_thresholds_not_relaxed':True,
        'all_old_failed_gates_outputs_and_budgets_preserved':True,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A88'}
    dump(OUT/'scientific_assessment.json',assessment)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':assessment,'controls':rel(OUT/'controls_execution_review.json'),
        'whole_qualification':False,'publication_integrity_is_not_physical_validation':True})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    case_lines=[]
    for row in rows:
        d=OUT/'native'/row['case'];execution=read(d/'engine.execution.json')
        case_lines.append(f"- {row['case']} : code{execution['parent_exit_code']}, {execution['wall_s']:.3f}s ; porte locale={row['pass']}.")
    detail='Aucune boucle locale complète qualifiée. Les données réelles restent disponibles pour analyse.'
    if loop:
        detail=(f"La boucle enregistre{loop['native_rows']}états TH, dernier temps{loop['last_saved_ms']:.9g}ms, "
            f"marqueurs de garde{loop['zero_denominator_guard_marker_count']}. Force de plateau avant={loop['pre_compression_force_N']}N, "
            f"après refermeture={loop['post_reclosure_force_N']}N, par pente de l’impulsion de réaction des supports. "
            f"Résidu énergétique maximal calculé={loop['global_energy_residual_J_max']:.9g}J pour le seuil inchangé1e−7J ; "
            f"différence KE nodale reconstruite/native={loop['KE_reconstruction_vs_native_J_max']:.9g}J. "
            'Les contrôles échoués sont : '+', '.join(loop['failed_checks'])+'. '
            'Les plages natives de chaque champ sont conservées ; leur présence ou un changement ne certifie pas seul le dommage. '
            'Le travail indépendant des réactions et la sémantique des champs doivent être examinés sans crédit physique implicite.')
    REPORT.write_text(f'''# AIRCRAFT-A87 — dixième moteur isolé et contrôles bornés

Le correctif autorisé A86 est appliqué et compilé dans un nouveau moteur isolé. Les résultats locaux et critères encore échoués restent séparés de l’objectif des dix secondes d’impact entier.

## 1. Faits directement observés ou transcrits

Accord « Oui, appliquer le correctif A86, compiler et exécuter A87 », receipt request_user_input_async/call_a7e8e12bd9604e8ea2f8c1de6ddb4d3f/0. Publication A84+A85 vérifiée avant déclaration. Diff exact, un seul nouveau fichier moteurNL_SOLV ; toutes les corrections A73 précédentes conservées. Compilation{build['wall_s_from_original_start']:.3f}s, sixCPU, dans le plafond1h, sans GPU/installation/Starter compilé. BinaireSHA256{sha(binary)}. Neuf anciens moteurs conservés.

{chr(10).join(case_lines)}

{controls['new_Engine']}Engine utilisés sur4maximum, unCPU/plafond180s chacun, zéro Starter/convertisseur natif. Places conditionnelles inutilisées={controls['unconsumed_conditional_slots']}, non réaffectées. CHECK entier exécuté={controls['whole_CHECK_executed']}. Aucun prolongement dynamique entier.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Le solveur est une variante locale documentée, sous licence source. Ses régressions utilisent les cartes et résultats numériques A67 sauvegardés, pas des dégâts historiques comme cible. Une compilation ou une terminaison normale ne valide pas sa mécanique.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie ou vidéo réanalysée/modifiée. Le cache logiciel est réutilisé à empreintes vérifiées ; aucun téléchargement ou changement de dépendance. Les sources et binaires tiers restent dans les répertoires privés, séparés des livrables propres. Aucun ancien calcul rejoué : les régressions évaluent le nouveau binaire face aux anciens résultats sauvegardés.

## 4. Hypothèses propres au modèle

Graine1102110, zéro tirage, unitésg/mm/ms conservées. La nouvelle garde définit les deux ratios relatifs à0 seulement dans le sous-espace libre exactement nul, sous les restrictions A86 ; elle change explicitement cette définition dégénérée, sans modifier les tolérances ou le chemin non nul. L’itération1 conserve sonInfinity possible. La garde ne calcule pas l’énergie totale physique ou le travail imposé. Masses, cartes matérielles et chargements sont ceux des cas référencés ; la masse8g du coupon est instrumentale.

## 5. Résultats dérivés

Les histoires nouvelles sont décodées en Python, sans convertisseur natif. Les deux régressions comparent chaque canal au binaire sauvegardé, puis reprennent l’analyse mécanique A67 et ses seuils d’origine sur les nouvelles sorties. La transcription CSV porte explicitement son originePython, avec labels liés au schéma natif exact.

{detail}

Dernier temps local sauvegardé{last:.9g}ms, {states}états positifs. Cette durée locale n’ajoute aucun temps à l’impact entier et ne constitue pas un film de dix secondes.

## 6. Contradictions et informations manquantes

Qualification physique locale incomplète ; les échecs sont conservés. La fermeture énergétique indépendante, les champsUSR/dommage et la compression après rupture doivent être évalués selon les observations réellement disponibles. Aucun bilan ne sera fermé avec un termeRKE inventé, ni avec un seuil accru après coup. Le CHECK conditionnel ne peut pas être exécuté si les critères locaux restent échoués. Les cinqTYPE25 ignorés,107391avertissements et tous anciens budgets/échecs restent bloquants. Les places conditionnelles non utilisées ne deviennent pas des crédits pour un autre essai. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A87 → AIRCRAFT-A88\n\nRapport : '+rel(REPORT)+'\nContrôles : '+rel(OUT/'controls_execution_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(OUT/'controls_execution_review.json')+' et '+rel(HANDOFF)+'.\nA87terminée, aucun calcul en cours ; vérifier publication A86+A87.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,AUTH,ROOT/'wtc1_simulation_v8/data/aircraft_a87_controls.json',
        Path(__file__),ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a87_null_relative.py',ROOT/'wtc1_simulation_v8/scripts/control_aircraft_a87_null_relative.py',
        ROOT/'wtc1_simulation_v8/scripts/authorize_aircraft_a87.py',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_only_no_raw_AGPL_source_or_binary':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A87_assessed':True,'new_Engine':controls['new_Engine'],'local_time_ms':last,'physical_qualification':False}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert cy['pending_iterations']==['AIRCRAFT-A86']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A87','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A87',next_iteration='AIRCRAFT-A88',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a87_key_results']=entry;s['validated_artifacts'].update(aircraft_a87_report=rel(REPORT),aircraft_a87_results=rel(OUT/'composite_qualification_review.json'),aircraft_a87_handoff=rel(HANDOFF))
    cy.update(pending_iterations=['AIRCRAFT-A86','AIRCRAFT-A87'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A86+AIRCRAFT-A87 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cy)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==206
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,
        'files_verified':len(m['files']),'build_and_controls_archived':True,'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A88'})
    print(json.dumps({'A87_registered':True,'registry':206,'pending_publication':2}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
