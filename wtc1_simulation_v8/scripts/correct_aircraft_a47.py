"""Restore declared displacement amplitudes in the correct IMPDISP field, fresh cases only."""
from probe_aircraft_a47 import *
from compare_aircraft_a47 import full_window
DEC=ROOT/'wtc1_simulation_v8/data/aircraft_a47_encoding_repair_predeclaration.json'

def declare():
 guard();assert not DEC.exists();c=read(CFG);rows=[]
 for mode,folder in [('MEMBRANE','MEMBRANE_TRANSLATION_OUTPUT'),('BENDING','BENDING')]:
  src=OUT/folder/'preparation';g=read(src/'generation.json');f=src/(g['name']+'_0000.rad');s=f.read_text().splitlines();cards=[]
  for i,line in enumerate(s):
   if line.startswith('/IMPDISP/'):
    scale=list(map(float,s[i+3].split()));assert len(scale)==4 and scale[1]==1;cards.append({'keyword':line,'old_Ascale_time':scale[0],'old_Fscale_displacement':scale[1],'new_Ascale_time':1.,'new_Fscale_displacement':scale[0]})
  rows.append({'mode':mode,'source':rel(f),'source_sha256':streamsha(f),'cards':cards})
 dump(DEC,{'created_utc':now(),'seed':1102072,'random_draws':0,'iteration':'AIRCRAFT-A47','reason':'Saved native boundary DR at.001ms differs from predeclared amplitudes; direct input inspection and primary IMPDISP documentation prove amplitude was written into time scaling rather than displacement scaling.','primary_source':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impdisp_starter_r.htm','source_formula':'imposed(t)=Fscale_y*curve(t/Ascale_x)','cases':rows,'repair':'Swap erroneous scale fields to time1/displacementdeclaredamplitude. This restores original configuration; no fit to mechanical output or observed historical damage.','all_old_attempts_preserved':True,'original_physical_parameters_and_criteria_unchanged':True,'new_Starter_cases':2,'new_Engine_cases':4,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_s':120,'maximum_s':1080,'conditional_Windows_comparison':'Only if corrected Linux explicit fails; not repeat previously failed physical input.','new_whole_duration_credit_s':0});dump(OUT/'encoding_repair_guard.json',{'created_utc':now(),'sha256':streamsha(DEC),'before_native':True});print({'encoding_repair_declared':True,'intended_input_unchanged':True},flush=True)

def run():
 guard();assert streamsha(DEC)==read(OUT/'encoding_repair_guard.json')['sha256'];dec=read(DEC);rows=[]
 for row in dec['cases']:
  mode=row['mode'];f=ROOT/row['source'];assert streamsha(f)==row['source_sha256'];oldn=f.name[:-9];g=read(f.parent/'generation.json');oldn=g['name'];n='A47_R1_'+mode;d=OUT/'encoding_repair'/mode/'preparation';assert not d.exists();d.mkdir(parents=True);L=f.read_text().splitlines();changes=[]
  for i,line in enumerate(L):
   if line.startswith('/IMPDISP/'):
    v=list(map(float,L[i+3].split()));original=L[i+3];L[i+3]=ff(1,v[0],v[2],v[3]);changes.append({'line':i+4,'original':original,'repaired':L[i+3]})
  L=[x.replace(oldn,n) for x in L];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf8');g.update(name=n,encoding_repair=True,amplitudes_match_original_configuration=True);dump(d/'generation.json',g);dump(d/'literal_encoding_changes.json',{'created_utc':now(),'changes':changes,'other_changes':'Title/root only; source membrane already has observation-only DR omission.','physical_sections_unchanged':True});ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,env());s=(d/'starter.log').read_text();w=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);e=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);strict=ok and w==0 and e==0;dump(d/'starter_gate.json',{'created_utc':now(),'warnings':w,'errors':e,'pass':strict});assert strict
  for method in ['EXPLICIT','IMPLICIT']:
   dst=d.parent/method;dst.mkdir();rst=d/(n+'_0000_0001.rst');shutil.copy2(rst,dst/rst.name);assert streamsha(rst)==streamsha(dst/rst.name);shutil.copy2(d/'generation.json',dst/'generation.json');source=OUT/'BENDING'/method/'A47_BENDING_0001.rad';s=source.read_text().replace('A47_BENDING',n);(dst/(n+'_0001.rad')).write_text(s,encoding='utf8');dump(dst/'initial_state_transfer.json',{'created_utc':now(),'source':rel(rst),'target':rel(dst/rst.name),'sha256':streamsha(rst),'full_unchanged_native_state':True});normal=launcher.execute(dst,n);r=full_window(dst,n);rows.append({'mode':mode,'method':method,'raw_exit_normal':normal,'full_window':r});print({'corrected_case':mode,'method':method,**r},flush=True)
 dump(OUT/'encoding_repair_execution_review.json',{'created_utc':now(),'cases':rows,'all_full_windows_pass':all(r['full_window']['pass'] for r in rows),'whole_impact_qualified':False,'original_physical_acceptance_unchanged':True,'new_whole_time_credit_s':0})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
