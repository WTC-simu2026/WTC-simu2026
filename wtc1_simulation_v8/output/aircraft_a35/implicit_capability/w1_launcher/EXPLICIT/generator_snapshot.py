"""New probe directories after five retained pre-solver shell argument failures."""
from probe_aircraft_a35_mumps import *
import probe_aircraft_a35_mumps as initial
OUT=initial.OUT/'w1_launcher'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a35_launcher_recovery.json'
def declare():
 assert not OUT.exists() and not CFG.exists();OUT.mkdir();c=read(initial.CFG);c.update(declared_utc=now(),subscope='Freshlauncherrepair; physicalfixture/Engine/build/thresholdsunchanged',parent_configuration=rel(initial.CFG),parent_configuration_sha256=streamsha(initial.CFG),launcher='Explicitworkspace.shfile, no WSLbash-cargument forwarding')
 old=read(initial.OUT/'fresh_capability_review.json');assert all(not r['binary_implicit_completion'] for r in old['cases'])
 assert all('exec: : not found' in (initial.OUT/ca['name']/'engine.log').read_text() for ca in CASES)
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True});dump(OUT/'previous_launch_failure_review.json',{'created_utc':now(),'old_cases_retained':True,'five_Windows_Starter_runs_completed':True,'successful_old_Linux_Engine_runs':0,'failure_before_Engine_started':True,'old_report_not_changed':True})
 for name in ['transfer_predeclaration.json','Windows_Starter_bridge_predeclaration.json']:
  q=read(initial.OUT/name);q.update(redeclared_utc=now(),configuration_sha256=streamsha(CFG),parent=rel(initial.OUT/name));dump(OUT/name,q)
 print({'A35_launcher_recovery_declared':True,'old_Linux_Engine_runs':0},flush=True)
def run():
 # Rebind the complete owned generator/audit functions into this new scope.
 for name in ['execute','runner','audit_fields','transfer','comparisons','run']:
  s=inspect.getsource(getattr(initial,name));ast.parse(s);exec(compile(s,__file__+'::'+name,'exec'),globals())
 dump(OUT/'scope_derivation.json',{'created_utc':now(),'parent_script':rel(Path(initial.__file__)),'parent_sha256':streamsha(Path(initial.__file__)),'new_scope':rel(OUT),'unchanged_thresholds':True,'successful_old_solver_reruns':0});globals()['run']()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
