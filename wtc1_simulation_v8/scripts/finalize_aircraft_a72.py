"""Seal A72 read-only proposal; no Engine source application, build or native run."""
from build_aircraft_a54_graph import ROOT, read, dump, sha, now, rel, harness
from pathlib import Path
import json
import shutil

OUT = ROOT / 'wtc1_simulation_v8/output/aircraft_a72'
PREP = ROOT / 'wtc1_simulation_v8/output/aircraft_a72_preparation'
PLAN = ROOT / 'wtc1_simulation_v8/data/aircraft_a72_proposal.json'
OBSERVER = ROOT / 'wtc1_simulation_v8/data/aircraft_a72_observer_plan.json'
CFG = ROOT / 'wtc1_simulation_v8/data/aircraft_a72_predeclaration.json'
REPORT = OUT / 'rapport_aircraft_a72.md'
HANDOFF = ROOT / 'harness/handoffs/WTC1_AIRCRAFT_A72_HANDOFF.md'
PROMPT = ROOT / 'harness/handoffs/PROMPT_REPRISE_A73_2026-10-14.md'
PROPOSAL = PREP / 'proposition_contexte_CHECK_explicite.md'


def route():
    return ('AIRCRAFT-A73 proposée seulement : neuvième moteur isolé avec le correctif exact A72, '
        'garde CHECK IMP_CHK>0 à la place de TT==0 dans IMP_CHKM, suppression de COM08 devenue inutile. '
        'Nouvel accord explicite distinct requis avant application/compilation et six nouveaux Engine. '
        'Compilation plafond1h/sixCPU, estimation5–15min ; six Engine au maximum, unCPU/plafond180s chacun, '
        'zéro Starter, sans GPU ni installation, aucun prolongement dynamique entier. '
        'Starter positif qualifié A71 réutilisé ; entrées et seuils conservés, flags natifs et horloge à mesurer. '
        'A71 gardeTT0 échouée et budgets sixEngine/unStarter entièrement consommés, sorties/échecs inchangés. '
        'Les107391 avertissements et cinq TYPE25 par scène restent bloquants. '
        'Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. '
        'Ne pas créditer les témoins, modifier implicitement les budgets, compenser par RKE ou viser des dégâts connus.')


def declare():
    assert not OUT.exists() and not CFG.exists()
    h = harness()
    assert h['CurrentIteration'] == 'AIRCRAFT-A71' and h['RegistryEntries'] == 190
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations'] == []
    proof = read(ROOT/'outputs/github_publication/updates_2026-10-14_aircraft_a70_a71/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count'] == 0
    assert proof['scientific_ci']['conclusion'] == proof['final_ci']['conclusion'] == 'success'
    scope = read(PREP/'independent_scope_review.json')
    obs = read(PREP/'observer_preparation_review.json')
    assert scope['pass'] and scope['plan_sha256'] == sha(PLAN)
    assert obs['pass'] and obs['new_native'] == 0
    assert read(OBSERVER)['main_plan_sha256'] == sha(PLAN)
    OUT.mkdir()
    dump(OUT/'harness_before.json', h)
    for n in ['state.json', 'publication_cycle.json', 'experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n, OUT/('before_'+Path(n).name))
    dump(CFG, {**read(PLAN), 'iteration': 'AIRCRAFT-A72', 'declared_utc': now(),
        'observer_plan': rel(OBSERVER), 'observer_plan_sha256': sha(OBSERVER),
        'new_native_Engine': 0, 'new_Starter': 0, 'source_patch_applied': False,
        'new_compilation': False, 'source_references': [
            'wtc1_simulation_v8/output/aircraft_a71/CHECK_call_order_review.json',
            'wtc1_simulation_v8/output/aircraft_a71/scientific_assessment.json',
            rel(PLAN), rel(OBSERVER)],
        'source_archive_policy': 'read-only; no historical archive inspection',
        'units': 'Existing native inputs g/mm/ms, unchanged; TT native ms, R2 native squared residual units.'})
    dump(OUT/'declaration_guard.json', {'created_utc': now(), 'sha256': sha(CFG), 'before_sealing': True})


def assess():
    assert not REPORT.exists()
    assert read(ROOT/'harness/state.json') == read(OUT/'before_state.json')
    assert sha(CFG) == read(OUT/'declaration_guard.json')['sha256']
    p = read(PLAN); scope = read(PREP/'independent_scope_review.json'); obs = read(OBSERVER)
    assert scope['pass'] and scope['plan_sha256'] == sha(PLAN)
    assert obs['main_plan_sha256'] == sha(PLAN)
    assert sha(ROOT/obs['prepared_observer']) == obs['prepared_observer_sha256']
    for key in ['current_source', 'proposed_source', 'patch']:
        expected = p['patch'][{'current_source':'current_sha256', 'proposed_source':'proposed_sha256', 'patch':'patch_sha256'}[key]]
        assert sha(ROOT/p['patch'][key]) == expected
    for case in p['controls']['cases']:
        for row in case['inputs']:
            assert sha(ROOT/row['path']) == row['sha256'] and (ROOT/row['path']).stat().st_size == row['bytes']
    prior = ROOT/'wtc1_simulation_v8/output/aircraft_a71'
    manifest = read(prior/'artifact_manifest.json')
    for row in manifest['files']:
        assert sha(ROOT/row['path']) == row['sha256']
    engine = ROOT/'wtc1_simulation_v8/openradioss_runtime/a71_initial_zero_residual_candidate/isolated_exec/engine_linux64_gf_ompi'
    assert sha(engine) == '61b9b1d613267ad24ad8bde41e00496399ba5ba5e0808f8e3bead9b161c99a7e'
    a71 = read(prior/'scientific_assessment.json')
    assert not a71['initial_zero_CHECK_policy_pass'] and a71['controls_remaining'] == a71['Starter_remaining'] == 0
    chronology = read(prior/'CHECK_call_order_review.json')
    assert chronology['pass_read_only_source_chronology'] and chronology['TT_advances_before_CHECK_call']
    dump(OUT/'preservation_verification.json', {'created_utc': now(), 'pass': True,
        'A71_sealed_files_rehashed': len(manifest['files']), 'A71_binary_rehashed_unchanged': True,
        'A71_failed_policy_and_consumed_budgets_preserved': True, 'six_future_input_sets_hash_verified': True,
        'old_native_diagnostics_replayed': False, 'source_archives_not_rescanned': True,
        'physical_budgets_and_failed_criteria_preserved': True, 'new_native': 0})
    a = {'created_utc': now(), 'iteration': 'AIRCRAFT-A72',
        'status': 'completed_read_only_explicit_CHECK_context_proposal__not_applied_or_compiled',
        'source_pin': p['source_pin'], 'new_native_Engine': 0, 'new_Starter': 0,
        'source_patch_applied': False, 'new_compilation': False, 'patch': p['patch'],
        'independent_scope_checks': len(scope['checks']), 'independent_scope_pass': True,
        'TT_advance_before_CHECK_source_verified': True, 'native_flags_not_observed_or_invented': True,
        'own_observer_prepared_syntax_pass': True, 'observer_native_runtime_qualified': False,
        'future_native_scalar_fields': list(obs['native_globals']), 'future_Engine_number': 9,
        'future_Engine_maximum': 6, 'future_Starter_maximum': 0, 'future_build_maximum_s': 3600,
        'future_build_CPU': 6, 'future_native_CPU': 1, 'each_native_cap_s': 180,
        'new_explicit_consent_received': False, 'old_positive_Starter_reused_not_replayed': True,
        'A71_failed_TT0_policy_preserved': True, 'A71_Engine_and_Starter_remaining': 0,
        'all_prior_failed_CHECK_results_preserved': True, 'whole_CHECK_pass': False,
        'TYPE25_ignored_per_scene': 5, 'possible_connection_warnings_per_scene': 107391,
        'whole_mass_material_inertia_budgets_changed': False, 'whole_force_added': False,
        'RKE_added': False, 'whole_integration_ready': False, 'best_whole_physical_s': .0200001220703125,
        'new_whole_credit_s': 0, 'objective1_complete': False, 'next_iteration': 'AIRCRAFT-A73'}
    dump(OUT/'scientific_assessment.json', a)
    dump(OUT/'composite_qualification_review.json', {'created_utc': now(), 'assessment': a,
        'proposal': rel(PROPOSAL), 'independent_scope_review': rel(PREP/'independent_scope_review.json'),
        'observer_preparation_review': rel(PREP/'observer_preparation_review.json'), 'whole_qualification': False})
    dump(OUT/'objectif1_route.json', {'created_utc': now(), 'target_physical_s': 10,
        'best_whole_physical_s': .0200001220703125, 'new_physical_duration_credit_s': 0,
        'complete': False, 'next': route()})
    REPORT.write_text('''# AIRCRAFT-A72 — proposition de contexte CHECK explicite

Proposition concrète et vérifiée en lecture seule. Aucun correctif appliqué au moteur, aucune compilation, aucun nouveau Starter/Engine. L’échec de la garde TT0 en A71 est conservé. La proposition utilise le contexte CHECK existant et prépare l’observation native des paramètres manquants.

## 1. Faits directement observés ou transcrits

A71 a consommé ses six Engine et son unique Starter autorisés. Le témoin zéro dynamique et les deux CHECK entiers mesurent R2=0 mais gardent une erreur de chargement et aucun nouveau diagnostic : la nouvelle garde TT0 a échoué. Le témoin statique chargé mesure R2=4, le zéro statique reste refusé, la dynamique libre1ms passe23critères. Ces résultats sont mis en cache, recontrôlés par empreintes, sans répétition de calcul.

La chronologie de la source figée RESOL place l’avance TT ligne8605 avant le contexte IMP_CHK>0 ligne8734 et CALL IMP_CHKM ligne8735, puis MSTOP2 ligne8756. Cette relation est une observation de source. Les valeurs exactes IDYNA/IQSTAT/IMP_CHK/NCYCLE/TT à l’appel n’ont pas encore été lues nativement ; aucune valeur n’est inventée.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat de modèle historique officiel. Le pin logiciel OpenRadioss reste3d75ff13d1946f6d28a43920eac4fa2aae41b27a. Les déclarations communes figées fournissent les types et offsets des cinq scalaires à lire ; elles ne fournissent pas leurs valeurs en exécution. Sources brutes et différence exactes restent en copie privée AGPL, séparées des scripts propres du harnais.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée, modifiée ou réanalysée. Aucune nouvelle vidéo source lue, aucun ajustement à des dégâts connus. Les copies logicielles figées ne sont pas des observations historiques de l’impact.

## 4. Hypothèses propres au modèle

Graine1102097, zéro tirage ; entrées et unitésg/mm/ms conservées. R2 exactement nul devient admissible uniquement dans le CHECK Newmark IDYNA2/IQSTAT0/IMP_CHK>0, avec diagnostic explicite. Cette modification d’admissibilité est annoncée : elle ne qualifie ni les contacts ni la scène entière. Les branches zéro statique, quasi-statique, autres méthodes, valeurs hors plage/non finies et résidus positifs restent inchangées. Aucun terme RKE, chargement entier, budget masse/matière/inertie ou dynamique n’est modifié.

## 5. Résultats dérivés

Quatorze critères de portée passent sur la source proposée : seule IMP_CHKM change, la condition TT==0 est remplacée par IMP_CHK>0 et l’inclusion COM08 ajoutée en A71 devenue inutile est retirée. Les autres routines restent identiques. Les six ensembles d’entrées sont vérifiés par empreintes, avec le Starter positif A71 réutilisé.

Le neuvième moteur isolé A73 est proposé avec toutes les corrections A71 conservées : compilation plafond1h/sixCPU, estimation5–15min, sans GPU ni installation. Maximum six Engine sur unCPU/plafond180s, zéro Starter : zéro dynamique, zéro statique refusé, charge positive R2=4, régression libre1ms aux seuils A67, deux CHECK entiers. Il s’agit de contrôles du nouveau binaire, pas de répétitions de l’ancien lot. Aucun prolongement dynamique entier autorisé dans ce lot.

L’observateur propre est préparé et sa syntaxe passe. Aux mêmes points d’arrêt matériels que les cinq CHECK futurs, il lira directement IDYNA/IQSTAT/IMP_CHK/NCYCLE/TT par mémoire de son enfant en lecture seule. Les symboles et tailles doivent être résolus dans le nouveau binaire et les bornes contrôlées avant lecture ; aucun point d’arrêt, processus ou contrôle natif supplémentaire. Cette observation n’est pas encore qualifiée en exécution.

## 6. Contradictions et informations manquantes

Une revue statique n’est pas une réussite native : A71 a compilé après15critères de portée, puis sa garde a échoué. Les107391 avertissements de coefficients transformés et cinq contacts TYPE25 ignorés par scène restent présents et bloquants. Les inerties, matériaux, contacts et bilans entiers restent non qualifiés. Toute intégration ou simulation entière ultérieure reste conditionnelle aux critères physiques conservés.

L’accord A71 concernait exactement la garde TT0 et son budget épuisé. Le nouveau correctif, sa compilation et six nouveaux contrôles exigent un accord distinct selon AGENTS.md. La publication A70+A71 est vérifiée avant déclaration A72 : empreintes, anciennes archives et deux CI passent. Cette intégrité de publication ne valide pas la physique. Meilleur impact entier0,0200001220703125s ; les dix secondes physiques et leur vidéo3D restent incomplètes. Aucun temps des témoins ou temps interpolé n’est crédité.

'''+route()+'\n', encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A72 → AIRCRAFT-A73\n\nRapport : '+rel(REPORT)+
        '\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\nObservateur : '+rel(OBSERVER)+
        '\n\n'+route()+'\n', encoding='utf8')
    PROMPT.write_text('Reprends WTC1 dans '+ROOT.as_posix()+'.\nLis AGENTS.md, harness/state.json, '
        'harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+
        ', '+rel(PROPOSAL)+', '+rel(PLAN)+', '+rel(OBSERVER)+' et '+rel(HANDOFF)+'.\n'
        'L’état local prime ; aucun calcul en cours. A70+A71 publiées/vérifiées ; A72 seule en attente de cadence.\n'+
        route()+'\nNouvelles courtes en français ; ne pas rejouer les diagnostics déjà vérifiés.\n', encoding='utf8')
    dump(OUT/'harness_after_analysis.json', harness())
    files = [p for p in OUT.rglob('*') if p.is_file()] + [p for p in PREP.rglob('*') if p.is_file()]
    files += list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a72*.py'))
    files += [CFG, PLAN, OBSERVER, ROOT/obs['prepared_observer'], HANDOFF, PROMPT]
    dump(OUT/'artifact_manifest.json', {'created_utc': now(),
        'own_output_script_inputs_only_AGPL_raw_source_patch_excluded': True,
        'files': [{'path': rel(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A72_assessed': True, 'scope_checks': len(scope['checks']), 'new_native': 0,
        'source_applied': False, 'compiled': False}), flush=True)


def register():
    s = read(ROOT/'harness/state.json'); c = read(ROOT/'harness/publication_cycle.json')
    assert s == read(OUT/'before_state.json') and c == read(OUT/'before_publication_cycle.json')
    assert c['pending_iterations'] == []
    m = read(OUT/'artifact_manifest.json')
    for row in m['files']:
        assert sha(ROOT/row['path']) == row['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl') == sha(OUT/'before_registry.jsonl')
    a = read(OUT/'scientific_assessment.json'); stamp = now()
    row = {'experiment_id': 'WTC1-AIRCRAFT-A72', 'registered_at': stamp, 'configuration': rel(CFG),
        'report': rel(REPORT), 'results': rel(OUT/'composite_qualification_review.json'),
        'handoff': rel(HANDOFF), 'artifact_manifest': rel(OUT/'artifact_manifest.json'),
        'publication_verification': rel(OUT/'publication_verification.json'), **a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a', encoding='utf8', newline='\n') as f:
        f.write(json.dumps(row, ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A72', next_iteration='AIRCRAFT-A73', current_status=a['status'],
        next_objective=route(), updated_at=stamp)
    s['aircraft_a72_key_results'] = row
    s['validated_artifacts'].update(aircraft_a72_report=rel(REPORT),
        aircraft_a72_results=rel(OUT/'composite_qualification_review.json'), aircraft_a72_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A72'], pending_count=1, updated_at=stamp,
        next_publication_after='AIRCRAFT-A72+AIRCRAFT-A73 verified')
    for path, value in [(ROOT/'harness/state.json', s), (ROOT/'harness/publication_cycle.json', c)]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    h = harness(); assert h['RegistryEntries'] == 191 and h['CurrentIteration'] == 'AIRCRAFT-A72'
    dump(OUT/'publication_verification.json', {'created_utc': now(), 'pass': True, 'integrity_only': True,
        'files_verified': len(m['files']), 'harness': h, 'new_native': 0, 'whole_qualified': False,
        'objective1_complete': False, 'next_iteration': 'AIRCRAFT-A73'})
    print(json.dumps({'A72_registered': True, 'registry_entries': 191, 'pending_publication': 1}), flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['declare', 'assess', 'register'])
    globals()[parser.parse_args().action]()
