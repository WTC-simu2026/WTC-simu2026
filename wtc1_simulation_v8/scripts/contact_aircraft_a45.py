"""Fresh legacy-MUMPS contact controls using immutable cached initial states."""
from probe_aircraft_a45 import *
import tarfile,hashlib,numpy as np
DECL=ROOT/'wtc1_simulation_v8/data/aircraft_a45_contact_predeclaration.json'
NAMES=['CONTACT_RREF_DIRECT_EIGHTH','CONTACT_RREF_DIRECT_SIXTEENTH']

def declare():
 guard();assert not DECL.exists()
 archive=CAND/'source.tar.gz';assert streamsha(archive)==read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/source_archive.json')['sha256']
 files=read(ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json')['source_inspection'];rows=[]
 with tarfile.open(archive,'r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for row in files:
   suffix=row['path'].split('/source/',1)[1];data=tar.extractfile(members[suffix]).read();prior=(ROOT/row['path']).read_bytes();same=data==prior
   rows.append({'path':suffix,'legacy_sha256':hashlib.sha256(data).hexdigest(),'prior_sha256':row['sha256'],'byte_identical':same,'source_pin':read(CFG)['build']['complete_source_pin']})
 assert all(r['byte_identical'] for r in rows),rows
 pins={r['path']:r for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a41/artifact_manifest.json')['files']};cases=[]
 for name in NAMES:
  old=ROOT/'wtc1_simulation_v8/output/aircraft_a41'/name;g=read(old/'generation.json');n=g['name'];inputs=[]
  for f in [old/'generation.json',old/'phase1'/f'{n}_0000_0001.rst',old/'phase1'/f'{n}_0001.rad',old/'phase1/starter_gate.json']:
   entry=pins[rel(f)];assert streamsha(f)==entry['sha256'];inputs.append(entry)
  cases.append({'case':g['case'],'inputs':inputs})
 dump(DECL,{'created_utc':now(),'iteration':'AIRCRAFT-A45','seed':1102070,'random_draws':0,'purpose':'Qualify actual new legacy-MUMPS contact factorization and conservation independently of unsupported whole CHECK.','same_physics_and_Engine_cards_as_A41':True,'same_initial_native_states':True,'cases':cases,'source_velocity_protocol_files':rows,'source_velocity_protocol_unchanged':True,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_s':60,'maximum_total_s':360,'acceptance':read(ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json')['acceptance'],'new_whole_time_credit_s':0,'software_install_or_compile':False})
 dump(OUT/'contact_declaration_guard.json',{'created_utc':now(),'sha256':streamsha(DECL),'before_native':True});print({'contact_declared':True,'source_protocol_files_identical':len(rows)},flush=True)

def run():
 guard();assert streamsha(DECL)==read(OUT/'contact_declaration_guard.json')['sha256'];decl=read(DECL);rows=[]
 import probe_aircraft_a37 as auditor
 import read_aircraft_a41_newmark as reader
 auditor.OUT=OUT;auditor.CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json';auditor.guard=guard
 reader.OUT=OUT
 for row in decl['cases']:
  c=row['case'];d=OUT/c['name'];assert not d.exists();p=d/'phase1';p.mkdir(parents=True);transfers=[]
  for entry in row['inputs']:
   f=ROOT/entry['path'];assert streamsha(f)==entry['sha256'];target=d/'generation.json' if f.name=='generation.json' else p/f.name;shutil.copy2(f,target);assert streamsha(target)==entry['sha256'];transfers.append({'source':entry['path'],'target':rel(target),'sha256':entry['sha256'],'bytes':entry['bytes']})
  dump(d/'cached_input_transfer.json',{'created_utc':now(),'files':transfers,'fresh_Starter_executions':0,'old_Engine_replays':0,'new_binary_comparison':True});g=read(d/'generation.json');ok=execute(p,g['name'])
  if ok:
   dump(d/'run_completed.json',{'created_utc':now(),'pass':True,'new_binary_sha256':streamsha(BINARY)});auditor.audit_case(c);r=reader.review(c,True);rows.append(r)
  else:rows.append({'case':c['name'],'pass':False,'reason':'Native Engine did not complete'})
  print({'legacy_MUMPS_contact':c['name'],'pass':rows[-1]['pass']},flush=True)
 comparison=[]
 if len(rows)==2 and all(r['pass'] for r in rows):
  hs=[auditor.histories(next((OUT/n/'phase1').glob('*.csv'))) for n in NAMES];tt=hs[0]['time'];tt=tt[tt<=min(h['time'][-1] for h in hs)];K0=read(OUT/NAMES[0]/'generation.json')['kinetic_energy_J'];tol=decl['acceptance']['half_dt_energy_relative']*K0+decl['acceptance']['comparison_energy_absolute_J']
  for key in ['KINETIC ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']:
   vals=[np.interp(tt,h['time'],h[key])*.001 for h in hs];error=float(abs(vals[0]-vals[1]).max());comparison.append({'channel':key,'maximum_difference_J':error,'tolerance_J':tol,'pass':error<tol})
 dump(OUT/'legacy_MUMPS_contact_review.json',{'created_utc':now(),'cases':rows,'time_step_comparison':comparison,'pass':len(rows)==2 and all(r['pass'] for r in rows) and bool(comparison) and all(r['pass'] for r in comparison),'whole_impact_qualified':False,'new_whole_time_credit_s':0,'source_defined_velocity_interpretation_verified_before_run':True})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
