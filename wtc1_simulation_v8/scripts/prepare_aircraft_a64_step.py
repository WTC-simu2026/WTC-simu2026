"""Prepare exact next bounded controls; do not execute beyond the consumed12 budget."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import copy,json,shutil

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a64_preparation'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a64_proposal.json'

def main():
    assert not PREP.exists() and not PLAN.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A63'
    base=read(ROOT/'wtc1_simulation_v8/data/aircraft_a63_predeclaration.json');disp=read(ROOT/'wtc1_simulation_v8/output/aircraft_a63/dispersion_and_next_step_review.json');pair=disp['proposed_next_pair_dt_ms'];cases=[]
    for identifier,dt in [('FREE_REFINED',pair[0]),('FREE_REFINED_HALF',pair[1])]:
        c=copy.deepcopy(base['cases'][0]);c.update(id=identifier,dt_cap_ms=dt);cases.append(c)
    whole=[]
    for identifier,file,keys in [('WHOLE_ORIGINAL','aircraft_a53_write_watch_predeclaration.json','source_files'),('WHOLE_PAIRED','aircraft_a53_predeclaration.json','files')]:
        c=read(ROOT/'wtc1_simulation_v8/data'/file);inputs=c[keys][:2]
        for row in inputs:assert sha(ROOT/row['path'])==row['sha256']
        card=next(ROOT/r['path'] for r in inputs if r['path'].endswith('_0001.rad'));assert '/IMPL/CHECK' in card.read_text(encoding='utf8')
        whole.append({'id':identifier,'name':c['name'],'files':inputs,'unchanged_cached_CHECK_cards':True})
    PREP.mkdir();dump(PREP/'harness_before_preparation.json',h)
    plan={**base,'created_utc':now(),'future_iteration':'AIRCRAFT-A64','iteration':'AIRCRAFT-A64_PROPOSAL','seed':1102089,'cases':cases,'whole_CHECK_cases':whole,
      'purpose':'Reduce measured Newmark phase error, keep the failed coarse criterion and all mechanical budgets. Then inspect whole-model geometry on the current binary only if the refined local gate passes.',
      'new_human_authorization_required':'A61 agreed maximum12 native controls are consumed; this is a separate bounded next lot, not a renewed compilation request.',
      'maximum_new_native_runs':4,'minimum_new_native_runs':2,'conditional_whole_CHECK':'Only after free case conservation/analytical and unchanged half-dt criteria all pass.',
      'expected_total_minutes':[1,5],'each_cap_s':180,'CPU':1,'GPU':False,'new_software_change_or_compilation':False,'new_installation':False,
      'exact_refinement_basis':'dispersion_aircraft_a63.py, exact linear scheme bound, parameter fittingfalse','prior_native_cap_consumed':12,
      'no_full_dynamic_whole_extension_authorized_by_this_lot':True,'physical_whole_budgets_changed':False,'objective1_complete':False}
    dump(PLAN,plan);dump(PREP/'plan_guard.json',{'created_utc':now(),'plan_sha256':sha(PLAN),'proposal_only_no_native_execution':True})
    for case in whole:
        card=next(ROOT/r['path'] for r in case['files'] if r['path'].endswith('_0001.rad'));shutil.copy2(card,PREP/(case['id']+'_unchanged_CHECK.rad'))
    (PREP/'proposition_etape_a64.md').write_text('''# Étape A64 proposée — raffinement et CHECK, moteur existant

Préparée, aucun calcul lancé. Le lot A61 de12contrôles est consommé ; cette nouvelle étape demande un accord distinct sur son budget.

Deux essais libres sur le moteur A62 inchangé, avec pas0,000125 et0,0000625ms. Matériau, surface, masse instrumentale8g, vitesse initiale1mm/ms, supports, durée1ms et seuils de conservation/comparaison sont identiques à A63. Seul le pas change selon la borne analytique du schéma, sans ajustement aux dégâts ni aux paramètres physiques. L’échec des pas0,001/0,0005ms reste conservé.

Si les bilans et la comparaison demi-pas passent tous, deux CHECK du modèle entier sont lancés sur le même moteur : scène originale et paireA53, avec exactement les anciens états initiaux/cartes, vérifiés par SHA256. Leur but est de mesurer l’effet du traitement surfacique sur le blocage géométrique ; aucune dynamique entière prolongée et aucun passage inféré de NORMAL/code0. TYPE25, bilans locaux, domaines matériaux et autres critères échoués restent bloquants.

Au maximum4 nouveaux Engine, un CPU, plafond180s chacun, sansGPU, installation ou compilation. Estimation1–5minutes ; aucun calcul de plusieurs heures. Les deux dernières vérifications sont conditionnelles au passage local. Les paramètres et le lanceur sont sauvegardés, l’application logicielle du moteur reste inchangée.

L’objectif reste dix secondes physiques d’impact puis vidéo3D. Meilleure fenêtre entière actuelle0,0200001220703125s ; aucune seconde manquante interpolée ou créditée par ces témoins.
''',encoding='utf8')
    dump(PREP/'preparation_review.json',{'created_utc':now(),'pass':True,'plan':rel(PLAN),'plan_sha256':sha(PLAN),'proposal':rel(PREP/'proposition_etape_a64.md'),'proposal_sha256':sha(PREP/'proposition_etape_a64.md'),'old_initial_states_and_CHECK_cards_hash_verified':True,'A64_natives_executed':0,'new_software_or_compilation':False,'harness':harness()})
    print(json.dumps({'A64_prepared_not_executed':True,'maximum_new_native':4,'same_binary':True}),flush=True)

if __name__=='__main__':main()
