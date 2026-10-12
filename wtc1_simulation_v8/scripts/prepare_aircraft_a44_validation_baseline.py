"""Verify cached Windows LAW117 references while a separate Engine build awaits approval."""
from preflight_aircraft_a43 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha
from pathlib import Path
from finalize_aircraft_a22 import verify_files
import struct,time,json
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a44'
SOURCE=ROOT/'wtc1_simulation_v8/output/aircraft_a17'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a44_validation_predeclaration.json'

def declare():
 assert not CFG.exists() and not OUT.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A43';state=read(ROOT/'harness/state.json');assert state['next_iteration']=='AIRCRAFT-A44';assert read(ROOT/'outputs/github_publication/updates_2026-10-12_aircraft_a42_a43/final_remote_verification.json')['pass'];assert read(SOURCE/'publication_verification.json')['pass'];cfg17=ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json';a=read(cfg17);OUT.mkdir();dump(OUT/'harness_before_validation_baseline.json',h)
 dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A44','phase':'cached_validation_baseline_only','seed':1102069,'random_draws':0,'purpose':'Reuse qualified Windows LAW117 references instead of rerunning successful native controls. Prepare fair same-input comparisons after an explicitly authorized future separate Engine build.','reference_iteration':'AIRCRAFT-A17','reference_configuration':rel(cfg17),'reference_configuration_sha256':streamsha(cfg17),'reference_manifest':rel(SOURCE/'artifact_manifest.json'),'reference_manifest_sha256':streamsha(SOURCE/'artifact_manifest.json'),'reference_material':a['cohesive'],'cases':a['witness']['cases'],'acceptance':a['acceptance'],'execution':{'native_solver_executions':0,'converter_executions':0,'installations':0,'compilations':0,'read_only_cache_audit':True,'source_archive_rescan':False},'future_comparison_requires_authorized_new_binary':True,'future_Linux_controls':'Cached full native initial states and identical Engine cards, then existing independent analytic work/force/energy/motion/mass/erosion gates and area/half-dt checks. No CSV injection or remapped physical state.','limits':['Uniform opening/shear fixture only, not actual aircraft material identification or mixed-mode/compression qualification.','Fixture uses documented instrument masses, not an aircraft mass-budget change.','TYPE43 Ismstr1 here versus moving whole Ismstr4; whole checks remain separate.','No10s physical credit from these1ms coupon references.'],'objective1_target_physical_s':10,'objective1_complete':False});dump(OUT/'validation_baseline_guard.json',{'sha256':streamsha(CFG),'before_audit':True});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':['A42 andA43 registered161/162 with localized LAW117 and Reader contracts.','A42+A43 GitHub publication verified, both CI successful,121oldarchives retained, cadencepending0.'],'specific_live_process':None,'build_permission_pending':True});print({'A44_baseline_declared':True,'native_or_build_launched':False},flush=True)

def verify():
 assert streamsha(CFG)==read(OUT/'validation_baseline_guard.json')['sha256'];assert not (OUT/'cached_Windows_LAW117_reference_review.json').exists();cfg=read(CFG);manifest=read(ROOT/cfg['reference_manifest']);assert streamsha(ROOT/cfg['reference_manifest'])==cfg['reference_manifest_sha256'];pins={r['path']:r for r in manifest['files']};rows=[r for r in manifest['files'] if r['path'].startswith(rel(SOURCE/'w0')+'/') or r['path'] in [cfg['reference_configuration'],rel(SOURCE/'cohesive_review.json'),rel(SOURCE/'scientific_assessment.json'),rel(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a17.py'),rel(ROOT/'wtc1_simulation_v8/scripts/review_aircraft_a17.py')]];assert rows;t=time.perf_counter();n=verify_files(rows);review=read(SOURCE/'cohesive_review.json');assert review['mechanical_implementation_gate_pass'] and all(review['checks'].values());assert len(review['cases'])==4;expected=[4400.,800.,1.,450.,100.,1.,50.,50.,4.,2.,2.,1.,450/4400,100/800,100/450,1.,1.,1.,1.,3.,0.];pattern=struct.pack('>21d',*expected);cases=[]
 for case in cfg['cases']:
  d=SOURCE/'w0'/case['id'];generation=read(d/'generation.json');name=generation['name'];initial=d/(name+'_0000_0001.rst');cards=d/(name+'_0001.rad');execution=read(d/'engine.log.execution.json');assert execution['sha256']==streamsha(RUNTIME/'engine_win64.exe') and execution['exit_code']==0;binary=initial.read_bytes();offset=binary.find(pattern);assert offset>=0 and binary.find(pattern,offset+1)==-1;result=next(r for r in review['cases'] if r['case']['id']==case['id']);assert all(result['checks'].values());files=[initial,cards,d/'generation.json',d/(name+'T01'),d/(name+'T01.csv'),d/'cohesive_diagnostics.npz',d/'review.json',d/'engine.log',d/'engine.log.execution.json'];last_animation=sorted(d.glob(name+'A[0-9][0-9][0-9]'))[-1];files.append(last_animation);assert all(rel(p) in pins for p in files)
  cases.append({'case':case,'cached_generation':generation,'initial_state':pins[rel(initial)],'Engine_cards':pins[rel(cards)],'reference_files':[pins[rel(p)] for p in files],'original_native_execution':execution,'reference_all_gates_pass':True,'legacy_21_parameter_sequence_unique':True,'sequence_offset':offset,'legacy_values_21':expected,'native_history_rows':result['native_history_rows'],'native_surface_work_N_mm':result['final_surface_work_N_mm'],'original_reference_result':result,'physical_G_measured':False,'whole_transfer_qualified':False})
 result={'created_utc':now(),'pass':True,'verified_cached_files':n,'verified_cached_bytes':sum(r['bytes'] for r in rows),'wall_s':time.perf_counter()-t,'cached_cases':cases,'cached_area_and_half_dt_checks':review['checks'],'new_native_or_converter_executions':0,'old_successful_solver_replays':0,'native_restart_modified':False,'physical_parameters_changed':False,'whole_insertion_ready':False,'new_binary_compatibility_qualified':False,'new_software_build_executed':False,'objective1_complete':False};dump(OUT/'cached_Windows_LAW117_reference_review.json',result);dump(OUT/'cached_reference_verified_inventory.json',{'created_utc':now(),'files':rows,'pass':True});dump(OUT/'harness_after_validation_baseline.json',harness());text='''# A44 — références Windows LAW117 réutilisables

## 1. Faits directement observés ou transcrits

Les quatre témoins A17 sont vérifiés par leurs empreintes conservées, sans relancer solveur ou convertisseur : traction10mm, demi-pas, traction20mm et cisaillement10mm. Même moteur Windows actuellement installé. Chaque état initial contient une séquence unique des21paramètres antérieurs LAW117 attendus. Les quatre bilans et contrôles d’ouverture, force, travail, recharge au même pic et suppression d’élément étaient réussis et leurs fichiers sont inchangés.

## 2. Résultats d’un modèle officiel

Aucun nouveau calcul officiel. La référence analytique de l’interface et les critères existants A17 sont conservés. L’ancien contrat logiciel est corroboré par les fichiers natifs ; il ne valide pas un nouveau binaire.

## 3. Affirmations provenant des archives locales

Aucune nouvelle inspection historique ou de vidéo. Aucune propriété historique identifiée par ces témoins.

## 4. Hypothèses propres au modèle

Graine1102069, zéro tirage. Paramètres et seuils A17 inchangés : EN4400,ET800,TN450MPa,TT100MPa,GIC/GIIC50N/mm. Les masses instrumentales de1g/nœud appartiennent uniquement au témoin ; aucun budget d’avion modifié. TYPE43 Ismstr1 de ce témoin ne qualifie pas l’Ismstr4 du modèle mobile entier. Courbe imposée1ms avec ouverture/décharge/recharge/rupture ; durée non créditée à l’impact.

## 5. Résultats dérivés

Ces états, cartes Engine et données de référence peuvent être réutilisés après construction du futur moteur Linux pour des comparaisons à entrées physiques identiques, sans nouvelle préparation ou répétition Windows. Les critères indépendants A17, le demi-pas et l’aire doivent passer avant des contrôles entiers séparés. Aucune copie d’historique CSV dans un solveur.

## 6. Contradictions et informations manquantes

La compatibilité du futur binaire reste à tester. Les propriétés réelles du radôme, le mode mixte, la compression et le transfert entier restent non qualifiés. La nouvelle compilation demeure en attente d’accord explicite selon AGENTS.md ; aucun candidat logiciel n’a été créé. A44 n’est pas enregistrée comme itération terminée. Le meilleur impact entier reste20ms et l’objectif10s3D puisMP4/GIF reste incomplet.

''';(OUT/'references_Windows_verifiees.md').write_text(text,encoding='utf8');files=[CFG,Path(__file__),*OUT.glob('*.json'),OUT/'references_Windows_verifiees.md'];dump(OUT/'validation_baseline_artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in files]});print({'cached_windows_cases_verified':4,'cached_files':n,'new_native_runs':0,'native_or_build_launched':False},flush=True)

if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','verify']);globals()[p.parse_args().action]()
