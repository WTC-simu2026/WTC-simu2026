"""Seal the authorized Newton print observation without a native retry."""
from run_aircraft_a83_newton_print import ROOT,OUT,CFG,AUTH,PLAN,guard,read,dump,sha,now,rel,harness
from read_aircraft_a81_th_binary import decode
from pathlib import Path
import json,re,math,csv

REPORT=OUT/'rapport_aircraft_a83.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A83_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A84_2026-10-15.md'


def route():
    return ('AIRCRAFT-A84 : après publication A82+A83 vérifiée, examiner en lecture seule les normalisations '
        'des critères Newton de déplacement et énergie et les références au premier pas imposé. '
        'A83 imprime31lignes, itérations0à30 : force normalisée0 dès1, énergie Infinity de1à30, '
        'déplacement NaN de2à30, puis maximum d’itérations et limite de pas79/ISTOP−2. '
        'Numérateurs/dénominateurs bruts et temps/cycle tenté ne sont pas imprimés ; aucune cause unique encore prouvée. '
        'Préparer une proposition concrète avant toute nouvelle exécution ou modification du moteur. '
        'Le seul Engine A83 est consommé, zéro Starter ; aucun réessai. Ne pas neutraliser les critères, '
        'abaisser silencieusement le minimum ou attribuer une trajectoire à l’état initial. '
        'Compression, rupture et refermeture restent non mesurées. Conserver anciennes sorties, budgets, '
        '107391avertissements et critères échoués. Meilleur impact entier0,0200001220703125s ; '
        'dix secondes physiques puis vidéo3D incomplètes.')


def assess():
    c=guard();assert not REPORT.exists();d=OUT/c['case'];execution=read(d/'engine.execution.json')
    assert execution['parent_exit_code']==2 and not execution['timed_out']
    listing=d/(c['name']+'_0001.out');text=listing.read_text(encoding='utf8',errors='replace')
    assert re.search(r'PRINTOUT FREQUENCY FOR NON-LINEAR SOLVER\s*\.\s*-1',text)
    assert 'SOLVER IMPLICIT STOPPED DUE TO TIMESTEP LIMIT' in text and 'ISTOP=-2' in text
    token=r'(?:[+-]?(?:\d+\.\d*(?:E[+-]?\d+)?|Infinity)|NaN)'
    pattern=re.compile(r'^\s*(\d+)\s+(?:(Y)\s+)?('+token+r')\s+('+token+r')\s+('+token+r')\s*$')
    lines=text.splitlines();start=next(i for i,l in enumerate(lines) if '|du|/|u|' in l);rows=[]
    def value(s):
        v=float(s);return {'printed':s,'class':'NaN' if math.isnan(v) else 'positive_infinity' if math.isinf(v) and v>0 else 'negative_infinity' if math.isinf(v) else 'finite','finite_value':v if math.isfinite(v) else None}
    for i,line in enumerate(lines[start+1:],start+2):
        m=pattern.fullmatch(line)
        if m:rows.append({'line_1based':i,'iteration':int(m[1]),'matrix_reformed':m[2]=='Y',
            'displacement_ratio':value(m[3]),'force_ratio':value(m[4]),'energy_ratio':value(m[5]),'raw_line':line})
    assert [r['iteration'] for r in rows]==list(range(31))
    assert rows[0]['force_ratio']['finite_value']==1 and rows[1]['displacement_ratio']['finite_value']==1
    assert all(r['force_ratio']['finite_value']==0 for r in rows[1:])
    assert all(r['energy_ratio']['class']=='positive_infinity' for r in rows[1:])
    assert all(r['displacement_ratio']['class']=='NaN' for r in rows[2:])
    dump(OUT/'newton_printed_rows.json',{'created_utc':now(),'source':rel(listing),'sha256':sha(listing),'rows':rows,
        'nonfinite_values_are_strings_and_classes_not_JSON_numbers':True,'raw_references_not_printed':True})
    with (OUT/'newton_printed_rows.csv').open('x',encoding='utf8',newline='') as f:
        w=csv.writer(f);w.writerow(['line','iteration','matrix_reformed','displacement_printed','force_printed','energy_printed'])
        for r in rows:w.writerow([r['line_1based'],r['iteration'],r['matrix_reformed'],*[r[k]['printed'] for k in ['displacement_ratio','force_ratio','energy_ratio']]])
    meta,arrays,flat=decode(d/(c['name']+'T01'));times=arrays['time'][:,0]
    assert len(times)==1 and times[0]==0
    animations=list(d.glob(c['name']+'A[0-9][0-9][0-9]'));assert len(animations)==1
    checks={'native_NPRINT_minus1_confirmed':True,'all_printed_Newton_rows_transcribed':True,
        'all_nonfinite_ratios_classified':True,'first_nonlinear_iteration_observed':True,
        'raw_numerators_and_references_observed':False,'attempted_cycle_and_time_directly_printed':False,
        'stops_warnings_actual_saved_states_preserved':True,'physical_inputs_unchanged':True}
    review={'created_utc':now(),'pass_observation':False,'partial_observation_useful':True,'physical_pass':False,
        'checks':checks,'failed_observation_checks':[k for k,v in checks.items() if not v],
        'native_NPRINT':-1,'printed_iterations':31,'iteration_range':[0,30],
        'energy_positive_infinity_iterations':[1,30],'displacement_NaN_iterations':[2,30],
        'force_printed_zero_iterations':[1,30],'no_raw_zero_residual_or_division_by_zero_cause_claim':True,
        'maximum_iterations_reached':'--ITERATION DIVERGE with MAX_ITER REACHED--' in text,
        'reset_requested':'--RESET ITERATION WITH NEW TIMESTEP--' in text,
        'stop_message':79,'ISTOP':-2,'native_history_rows':meta['rows'],'native_last_saved_time_ms':0,
        'accepted_nonzero_saved_states':0,'animation_files':len(animations),'native_TH_schema':meta,
        'attempted_cycle_and_time_directly_observed':False,'inferred_first_trial_time_ms':.000125,
        'inferred_time_is_not_a_saved_or_directly_printed_state':True,
        'unchanged_dt_min_max_ms':[.000125,.000125],'unchanged_three_tolerances':1e-11,
        'warnings_retained':['PARITH/ON incompatible with implicit; reset OFF','ISOLID0 generic stiffness formulation'],
        'wall_s':execution['wall_s'],'new_Engine':1,'Engine_remaining':0,'new_Starter':0,'no_native_retry':True}
    dump(OUT/'observation_review.json',review)
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
    for r in old:
        st=(ROOT/r['path']).stat()
        if st.st_size!=r['bytes'] or st.st_mtime_ns!=r['mtime_ns_before']:changed.append(r['path'])
    assert not changed
    for r in c['unchanged_software']:assert sha(ROOT/r['path'])==r['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),
        'changed_paths':changed,'both_software_binaries_rehashed':True,'old_native_replayed':False})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A83',
        'status':'completed_authorized_Newton_print__nonfinite_energy_displacement__partial_observation_only',
        'explicit_authorization':c['authorization'],'new_Engine':1,'new_Starter':0,'Engine_remaining':0,
        'CPU_threads':1,'cap_s':180,'Engine_wall_s':execution['wall_s'],'Engine_pass':False,
        'observation_pass':False,'partial_observation_useful':True,'physical_pass':False,
        'native_NPRINT':-1,'printed_Newton_rows':31,'first_energy_infinity_iteration':1,
        'first_displacement_NaN_iteration':2,'force_ratio_printed_zero_from_iteration':1,
        'raw_references_and_attempted_cycle_time_not_observed':True,'saved_nonzero_time_states':0,
        'last_saved_coupon_time_ms':0,'stop_message':79,'ISTOP':-2,'no_unique_initial_failure_cause_proven':True,
        'compression_rupture_reclosure_remain_unmeasured':True,'no_physical_or_numerical_criterion_changed':True,
        'source_patch_compilation_GPU_installation':False,'whole_dynamic_extension':False,
        'all_prior_budgets_failed_gates_and_outputs_preserved':True,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A84'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'observation':rel(OUT/'observation_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text(f'''# AIRCRAFT-A83 — valeurs non finies dans les critères Newton

L’unique Engine autorisé est terminé. L’impression détaillée fournit les premières valeurs manquantes, mais aucune trajectoire à temps positif. Le succès complet de l’observation reste refusé : les références brutes et le temps/cycle tenté ne sont pas imprimés.

## 1. Faits directement observés ou transcrits

Accord A83 reçu, receipt request_user_input_async/call_3e99b79a34d14243b0cdbbaca9e5799b/0 ; publication A80+A81 vérifiée avant déclaration. Un EngineCPU1/plafond180s, zéro Starter/correctif/compilation/GPU/installation. Durée{execution['wall_s']:.3f}s, code2, aucun dépassement. Restart initial exact du Starter A81 et carte Engine identique sauf /IMPL/PRINT/NONLIN/-1. La sortie confirme NPRINT−1, les trois tolérances1e−11 et les deux bornes de pas0,000125ms.

La table donne31lignes, itérations0à30. À0 : déplacement0, force1, énergie0. À1 : déplacement1, force0, énergieInfinity. De2à30 : déplacementNaN, force0, énergieInfinity. Ce sont des ratios nativement imprimés à leur précision, pas des valeurs de forces ou déplacements bruts. Les reformations de matrice sont marquées0,1,7,13,19,25. Le message « MAX_ITER REACHED » précède « RESET ITERATION WITH NEW TIMESTEP », puis MESSAGE79/ISTOP−2. Les avertissements PARITH/ON et ISOLID0 restent conservés.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La fonction d’impression logicielle révèle des valeurs de convergence du modèle numérique courant ; elle ne qualifie aucun mécanisme physique réel. Aucune correspondance avec des dégâts connus recherchée.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie ou vidéo réanalysée ou modifiée. Aucun ancien diagnostic natif rejoué. Les sources logicielles privées épinglées restent distinctes des sources historiques.

## 4. Hypothèses propres au modèle

Graine1102105, zéro tirage, unitésg/mm/ms et hypothèses A81 conservées. Le premier temps tenté0,000125ms est une inférence du pas initial et du restart à0, pas une ligne temps/cycle imprimée ou un état accepté. Un ratio de force affiché0 ne prouve pas un résidu brut exactement nul. Infinity et NaN ne permettent pas d’attribuer seuls une division par zéro ou sa cause à un champ précis.

## 5. Résultats dérivés

Les31lignes sont transcrites avec numéros de ligne, chaînes d’origine et classes finite/NaN/positive_infinity, dans JSON strict et CSV. Le fichier TH contient un unique état réel à0ms ; une animation initiale seulement existe. L’impression a donc fourni une observation partielle utile : la normalisation énergie devient non finie dès1, puis déplacement dès2, avant le refus à30. Les numérateurs et références bruts n’étant pas imprimés, le critère complet d’observation reste échoué. Le prochain travail doit examiner leur définition et les conditions au premier pas, sans modifier les tolérances ou masquer les non-finis.

## 6. Contradictions et informations manquantes

Aucun état à temps positif accepté et sauvegardé ; compression, rupture, refermeture, impulsions de plateau, travail de fracture et peuplementUSR restent non mesurés. La cause unique n’est pas établie. Le seul Engine A83 est consommé, sans remplacement ni relance ; A81 et anciens budgets restent consommés. Aucun correctif du moteur n’est autorisé par ce lot. Échecs antérieurs,107391avertissements A73, budgets et sorties conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A83 → AIRCRAFT-A84\n\nRapport : '+rel(REPORT)+'\nObservation : '+rel(OUT/'observation_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence locaux puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(OUT/'observation_review.json')+' et '+rel(HANDOFF)+'.\nA83terminée,1Engineconsommé, zéroStarter, aucun calcul en cours. Vérifier publication A82+A83.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,AUTH,Path(__file__),ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a83_newton_print.py',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_only_no_raw_AGPL':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A83_assessed':True,'partial_observation':True,'full_observation':False,'physical_pass':False,'last_saved_ms':0}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert cycle['pending_iterations']==['AIRCRAFT-A82']
    m=read(OUT/'artifact_manifest.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A83','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A83',next_iteration='AIRCRAFT-A84',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a83_key_results']=entry;s['validated_artifacts'].update(aircraft_a83_report=rel(REPORT),aircraft_a83_results=rel(OUT/'composite_qualification_review.json'),aircraft_a83_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A82','AIRCRAFT-A83'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A82+AIRCRAFT-A83 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==202
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,
        'files_verified':len(m['files']),'partial_native_observation':True,'complete_observation_pass':False,
        'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A84'})
    print(json.dumps({'A83_registered':True,'registry':202,'pending_publication':2}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
