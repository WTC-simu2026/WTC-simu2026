"""Declared observation repair and same-state Windows diagnostic, retaining original failures."""
from probe_aircraft_a47 import *
from audit_aircraft_a05 import histories
from pathlib import Path
DEC=ROOT/'wtc1_simulation_v8/data/aircraft_a47_followup_predeclaration.json'

def declare():
 guard();assert not DEC.exists();cfg=read(CFG);w=RUNTIME/'engine_win64.exe';source=OUT/'BENDING/EXPLICIT';n=read(source/'generation.json')['name'];dump(DEC,{'created_utc':now(),'iteration':'AIRCRAFT-A47','seed':1102072,'random_draws':0,'reason':'Membrane Starter rejects three DR outputs because rotational displacement not computed; bending Linux explicit reaches energy-killed inf at .010ms and Linux implicit stops before first accepted step. Distinguish observation-only warning and input/Windows-vs-Linux issue.','cases':['MEMBRANE_TRANSLATION_OUTPUT','BENDING_WINDOWS_REFERENCE'],'membrane_change':'Only remove DRX DRY DRZ requests; no material, mass, property, loading, supports, timestep or criterion changed.','Windows_comparison':'Fresh Windows Engine on exact same A47 bending initial state and exact explicit Engine cards, not an old successful simulation rerun.','Windows_Engine':rel(w),'Windows_Engine_sha256':streamsha(w),'bending_initial_state_sha256':streamsha(source/(n+'_0000_0001.rst')),'bending_explicit_cards_sha256':streamsha(source/(n+'_0001.rad')),'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_s':120,'maximum_total_s':540,'physical_acceptance':cfg['acceptance'],'strict_completion':'Exit0 AND NORMAL AND no RUN KILLED/USER BREAK AND recorded last time reaches requested12ms. Original raw completion.json retained; it is not full-horizon evidence.','old_failures_retained':True,'whole_time_credit_s':0})
 dump(OUT/'followup_declaration_guard.json',{'created_utc':now(),'sha256':streamsha(DEC),'before_native':True});print({'followup_declared':True,'no_physics_changes':True},flush=True)

def prepare_membrane():
 c=read(CFG);base=OUT/'MEMBRANE/preparation';oldn=read(base/'generation.json')['name'];newn='A47_MEMBRANE_TRANSLATION_OUTPUT';d=OUT/'MEMBRANE_TRANSLATION_OUTPUT/preparation';assert not d.exists();d.mkdir(parents=True);s=(base/(oldn+'_0000.rad')).read_text();old=''.join(f'{v:>10}' for v in ['DX','DY','DZ','DRX','DRY','DRZ']);new=''.join(f'{v:>10}' for v in ['DX','DY','DZ']);assert s.count(old)==1;s=s.replace(old,new).replace(oldn,newn);(d/(newn+'_0000.rad')).write_text(s,encoding='utf8');g=read(base/'generation.json');g.update(name=newn,observation_only_change=True,old_failures_retained=True);dump(d/'generation.json',g);ok=win_execute(RUNTIME/'starter_win64.exe',['-i',newn+'_0000.rad','-np','1'],d,'starter.log',180,env());txt=(d/'starter.log').read_text();w=int(re.findall(r'(\d+) WARNING\(S\)',txt)[-1]);e=int(re.findall(r'(\d+) ERROR\(S\)',txt)[-1]);strict=ok and w==0 and e==0;dump(d/'starter_gate.json',{'created_utc':now(),'warnings':w,'errors':e,'pass':strict});return d,newn,strict

def convert(d,n):
 for f in sorted(d.glob(n+'T[0-9][0-9]')):
  if not f.with_suffix('.csv').exists():win_execute(RUNTIME/'th_to_csv_win64.exe',[f.name],d,f.name+'.converter.log',120,env())

def full_window(d,n):
 txt=(d/'engine.log').read_text(errors='replace');convert(d,n);files=sorted(d.glob(n+'T[0-9][0-9].csv'));last=max((float(histories(f)['time'][-1]) for f in files if len(histories(f)['time'])),default=None);early='USER BREAK' in txt or 'RUN KILLED' in txt;result={'created_utc':now(),'requested_end_ms':12,'actual_last_history_ms':last,'early_kill_or_user_break':early,'normal_marker':'NORMAL TERMINATION' in txt,'pass':last is not None and last>=12-1e-6 and not early and 'NORMAL TERMINATION' in txt,'raw_native_completion_preserved':True};dump(d/'full_window_review.json',result);return result

def run():
 guard();assert streamsha(DEC)==read(OUT/'followup_declaration_guard.json')['sha256'];dec=read(DEC);source=OUT/'BENDING/EXPLICIT';n=read(source/'generation.json')['name'];d=OUT/'BENDING_WINDOWS_REFERENCE';assert not d.exists();d.mkdir()
 for suffix,key in [('_0000_0001.rst','bending_initial_state_sha256'),('_0001.rad','bending_explicit_cards_sha256')]:
  f=source/(n+suffix);assert streamsha(f)==dec[key];shutil.copy2(f,d/f.name);assert streamsha(d/f.name)==dec[key]
 shutil.copy2(source/'generation.json',d/'generation.json');assert streamsha(RUNTIME/'engine_win64.exe')==dec['Windows_Engine_sha256'];en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');win_execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',180,en);r=full_window(d,n);print({'case':'BENDING_WINDOWS_REFERENCE',**r},flush=True)
 prep,n,strict=prepare_membrane();rows=[]
 if strict:
  for method in ['EXPLICIT','IMPLICIT']:
   target=prep.parent/method;target.mkdir();shutil.copy2(prep/(n+'_0000_0001.rst'),target/(n+'_0000_0001.rst'));shutil.copy2(prep/'generation.json',target/'generation.json');old=OUT/'BENDING'/method/'A47_BENDING_0001.rad';s=old.read_text().replace('A47_BENDING',n);(target/(n+'_0001.rad')).write_text(s,encoding='utf8');ok=launcher.execute(target,n);r=full_window(target,n);rows.append({'method':method,'native_exit_normal':ok,'full_window':r});print({'case':'MEMBRANE_TRANSLATION_OUTPUT','method':method,**r},flush=True)
 dump(OUT/'followup_execution_review.json',{'created_utc':now(),'Windows_bending_full_window':r if False else read(d/'full_window_review.json'),'membrane_observation_Starter_pass':strict,'membrane_cases':rows,'whole_impact_qualified':False,'no_old_native_replays':True})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
