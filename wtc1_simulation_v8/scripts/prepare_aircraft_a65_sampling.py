"""Prepare a separately authorized output-only native control lot; no native execution."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import copy,difflib,re,json

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a65_preparation'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a65_proposal.json'

def updated_cards(text,dt):
    text,n=re.subn(r'(/TFILE/4\s*\n)[^\n]+',lambda m:m.group(1)+f'{dt/2:20.12g}',text);assert n==1
    text,n=re.subn(r'(/RUN/[^\n]+\n)[^\n]+',lambda m:m.group(1)+f'{1+dt/2:20.12g}',text);assert n==1
    return text

def main():
    assert not PREP.exists() and not PLAN.exists()
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A64'
    assessment=read(ROOT/'wtc1_simulation_v8/output/aircraft_a64/scientific_assessment.json')
    assert not assessment['refined_free_composite_pass'] and not assessment['new_whole_CHECK']
    cfg=copy.deepcopy(read(ROOT/'wtc1_simulation_v8/data/aircraft_a64_proposal.json'))
    cfg.update(iteration='AIRCRAFT-A65_PROPOSAL',future_iteration='AIRCRAFT-A65',seed=1102090,created_utc=now(),
        purpose='Record every actual integration step and the target boundary, preserving physical inputs and acceptance. Then conditional whole CHECK.',
        A64_native_executed=2,A64_unused_conditional_whole_controls=2,prior_controls_not_reset=True,
        new_human_authorization_required='New maximum4 control lot; failed A64 local gate prevents using its conditional whole slots for replacement local runs.',
        requested_maximum_new_native_runs=4,maximum_new_native_runs=4,minimum_new_native_runs=2,
        target_native_free_ms=1,stop_boundary_rule_ms='1+dt/2; save actual target state within the unchanged one-step overshoot bound.',
        new_software_change_or_compilation=False,new_software_changes_or_compilation=False,new_installation=False,
        source_patch=False,GPU=False,CPU=1,each_cap_s=180,expected_total_minutes=[2,5],
        software_binary_unchanged=True,acceptance_thresholds_changed=False,physical_parameters_changed=False,
        data_recording_changes_only=['TFILE frequency dt/2 instead of0.0001ms','RUN stop1+dt/2 to save target boundary'],
        whole_CHECK_inputs_and_cards_unchanged=True,new_whole_credit_s=0,objective1_complete=False)
    PREP.mkdir();dump(PREP/'harness_before_preparation.json',h);dump(PLAN,cfg)
    dump(PREP/'plan_guard.json',{'created_utc':now(),'plan_sha256':sha(PLAN),'before_any_A65_native_execution':True})
    diffs=[]
    for c in cfg['cases']:
        old=ROOT/'wtc1_simulation_v8/output/aircraft_a64/native'/c['id'];name=read(old/'generation.json')['name']
        text=(old/(name+'_0001.rad')).read_text(encoding='utf8');new=updated_cards(text,c['dt_cap_ms'])
        card=PREP/(c['id']+'_Engine.proposed.rad');card.write_text(new,encoding='utf8',newline='\n')
        diff=''.join(difflib.unified_diff(text.splitlines(True),new.splitlines(True),fromfile=name+'_0001.rad',tofile=card.name))
        (PREP/(c['id']+'_output_only.diff')).write_text(diff,encoding='utf8',newline='\n')
        diffs.append({'case':c['id'],'original':rel(old/(name+'_0001.rad')),'original_sha256':sha(old/(name+'_0001.rad')),
                      'proposed':rel(card),'proposed_sha256':sha(card),'only_TFILE_and_RUN_values_changed':True,
                      'target_ms':1,'requested_stop_ms':1+c['dt_cap_ms']/2,'TFILE_ms':c['dt_cap_ms']/2})
    source_path=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a64_step.py';source=source_path.read_text(encoding='utf8')
    derived=source.replace('prepare_aircraft_a64_step','prepare_aircraft_a65_sampling').replace('aircraft_a64','aircraft_a65').replace('AIRCRAFT-A64','AIRCRAFT-A65').replace("name='A64_'","name='A65_'")
    derived=derived.replace("h['CurrentIteration']=='AIRCRAFT-A63'","h['CurrentIteration']=='AIRCRAFT-A64'").replace("['pending_iterations']==[]","['pending_iterations']==['AIRCRAFT-A64']")
    derived=derived.replace("old=ROOT/'wtc1_simulation_v8/output/aircraft_a63'","old=ROOT/'wtc1_simulation_v8/output/aircraft_a64'")
    marker="exec(compile(s,__file__,'exec'))"
    assert derived.count(marker)==1
    wrapper='''
generate_original=generate
def generate(case):
    d,name=generate_original(case)
    from prepare_aircraft_a65_sampling import updated_cards
    card=d/(name+'_0001.rad');before=card.read_text(encoding='utf8');after=updated_cards(before,case['dt_cap_ms'])
    prepared=read(PREP/'preparation_review.json');row=next(r for r in prepared['card_changes'] if r['case']==case['id'])
    expected=(ROOT/row['proposed']).read_text(encoding='utf8').replace('A64_'+case['id'],'A65_'+case['id'])
    assert after==expected
    (d/'Engine_original_before_recording_change.rad').write_text(before,encoding='utf8',newline='\\n')
    card.write_text(after,encoding='utf8',newline='\\n')
    dump(d/'recording_change_review.json',{'created_utc':now(),'proposed_card_sha256':sha(ROOT/row['proposed']),
        'actual_card_sha256':sha(card),'card_matches_predeclared_except_case_name':True,
        'source_patch':False,'mechanical_inputs_or_thresholds_changed':False})
    return d,name
'''
    derived=derived.replace(marker,marker+'\n'+wrapper)
    script=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a65_sampling.py';assert not script.exists();compile(derived,str(script),'exec');script.write_text(derived,encoding='utf8',newline='\n')
    proposal=PREP/'proposition_sorties_completes_a65.md'
    proposal.write_text('''# A65 proposée — enregistrer les pas et la frontière cible

A64 : deux nouveaux calculs terminent normalement, mais la sortieTH0,0001ms omet6000pas intermédiaires du second essai au pas0,0000625ms. Le lecteur exige chaque pas ; son premier résultat et l’absence du champ terminal à1ms restent des échecs conservés. Aux cycles effectivement enregistrés, les déplacements et compteurs natifs concordent avec la solution analytique ; cela ne suffit pas pour qualifier le composé.

Proposition : deux essais sur le même moteur A62, avec les mêmes matériaux, surface, masses8g, vitesse initiale, supports, pas et seuils. Seuls deux réglages de sortie changent : fréquenceTH=dt/2 pour ne manquer aucun cycle ; arrêt1+dt/2 afin de sauvegarder la frontière cible1ms, au plus un pas supplémentaire réel. Le seuil d’overshoot préexistant reste inchangé. Les champs proviendront du moteur ; aucun état manquant extrapolé.

Si tous les critères locaux passent, deux CHECK entiers sur les mêmes anciennes entrées originales/appariées vérifiées par empreintes. Aucun impact entier prolongé, aucune qualification entière inférée du témoin. Les blocsTYPE25, budgets, bilans locaux et autres critères échoués restent ouverts.

Nouveau lot demandé : maximum4Engine, CPU1, plafond180s chacun, estimation2–5minutes. Sans nouvelle modification du moteur, compilation, installation ouGPU. A64 a utilisé2contrôles ; ses deux CHECK conditionnels n’ont pas été lancés et ne sont pas convertis en essais de remplacement. L’ancien lotA61 de12 reste consommé.

Les cartes exactes, différences et lanceur sont prêts. Dix secondes physiques d’impact puis vidéo3D restent l’objectif ; meilleur impact entier0,0200001220703125s.
''',encoding='utf8')
    dump(PREP/'preparation_review.json',{'created_utc':now(),'pass':True,'plan':rel(PLAN),'plan_sha256':sha(PLAN),
        'proposal':rel(proposal),'proposal_sha256':sha(proposal),'card_changes':diffs,
        'runner':rel(script),'runner_sha256':sha(script),'derived_from':rel(source_path),'derived_from_sha256':sha(source_path),
        'A65_native_runs_executed':0,'source_patch_applied':False,'acceptance_unchanged':cfg['acceptance']==read(ROOT/'wtc1_simulation_v8/data/aircraft_a64_proposal.json')['acceptance'],
        'cohesive_parameters_unchanged':cfg['cohesive']==read(ROOT/'wtc1_simulation_v8/data/aircraft_a64_proposal.json')['cohesive'],
        'harness':harness()})
    print(json.dumps({'A65_prepared':True,'native_executed':0,'maximum_requested':4,'no_Engine_patch':True}),flush=True)

if __name__=='__main__':main()
