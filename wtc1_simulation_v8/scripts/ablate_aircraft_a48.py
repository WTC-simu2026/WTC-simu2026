"""Single-family whole-model RBE3 ablation for assembly diagnosis; never an impact candidate."""
from probe_aircraft_a48 import *
from audit_aircraft_a05 import histories
DEC=ROOT/'wtc1_simulation_v8/data/aircraft_a48_whole_ablation_predeclaration.json'

def declare():
 guard();assert not DEC.exists();assert read(OUT/'coupling_CHECK_review.json')['all_assembly_and_mass_pass'];p=ROOT/'wtc1_simulation_v8/output/aircraft_a37/whole_compatibility/A37_WHOLE_CHECK_0000.out';s=p.read_text();m=re.search(r'TOTAL MASS AND MASS CENTER.*?\n\s*([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)',s,re.S);dump(DEC,{'created_utc':now(),'iteration':'AIRCRAFT-A48','seed':1102073,'random_draws':0,'case':'WHOLE_NO_RBE3_CHECK','reason':'Four small single-family coupling assemblies complete CHECK; simple presence of each constraint family does not reproduce whole fault. Remove only whole RBE3 definitions in a fresh diagnostic copy to test involvement in sparse shell graph.','before_native':True,'source':rel(WHOLE),'source_sha256':streamsha(WHOLE),'removed_keyword_prefix':'/RBE3/','expected_removed_sections':368,'only_other_changed_lines':['BEGIN root','TITLE root'],'materials_properties_nodes_elements_masses_groups_other_constraints_unchanged':True,'constraints_and_mass_redistribution_changed_explicitly':True,'reference_Starter_report':rel(p),'reference_Starter_report_sha256':streamsha(p),'reference_Starter_mass_g':float(m.group(1)),'reference_Starter_center_mm':[float(x) for x in m.groups()[1:]],'mass_relative_tolerance':1e-6,'added_mass_relative_tolerance':1e-9,'per_process_cap_s':180,'Starter_CPU_threads':1,'Engine_CPU_threads':1,'GPU':False,'expected_wall_s':60,'maximum_total_s':360,'whole_impact_qualification':False,'new_physical_duration_credit_s':0,'five_TYPE25_retained_and_implicit_warning_not_suppressed':True,'no_new_installation_or_compilation':True});dump(OUT/'whole_ablation_guard.json',{'created_utc':now(),'sha256':streamsha(DEC),'before_native':True});print({'whole_ablation_declared':True,'RBE3_sections_to_remove':368},flush=True)

def run():
 guard();assert streamsha(DEC)==read(OUT/'whole_ablation_guard.json')['sha256'];c=read(DEC);assert streamsha(WHOLE)==c['source_sha256'];d=OUT/c['case'];assert not d.exists();d.mkdir();n='A48_WHOLE_NO_RBE3';orig=WHOLE.read_text().splitlines();kept=[];removed=[];i=0
 while i<len(orig):
  if orig[i].startswith('/RBE3/'):
   j=i+1
   while j<len(orig) and not orig[j].startswith('/'):j+=1
   removed.append({'keyword':orig[i],'source_first_line':i+1,'lines':orig[i:j]});i=j
  else:kept.append(orig[i]);i+=1
 assert len(removed)==368
 for keyword in ['/BEGIN','/TITLE']:j=kept.index(keyword);kept[j+1]=n
 def blocks(lines):
  result=[];key=None;rows=[]
  for line in lines:
   if line.startswith('/'):
    if key:result.append((key,rows))
    key=line;rows=[]
   else:rows.append(line)
  if key:result.append((key,rows))
  return result
 expected=[(k,[n]+r[1:] if k in ['/BEGIN','/TITLE'] else r) for k,r in blocks(orig) if not k.startswith('/RBE3/')];assert blocks(kept)==expected
 (d/(n+'_0000.rad')).write_text('\n'.join(kept)+'\n',encoding='utf8');(d/(n+'_0001.rad')).write_text(check_cards(n),encoding='utf8');dump(d/'input_ablation_review.json',{'created_utc':now(),'pass':True,'source':rel(WHOLE),'source_sha256':streamsha(WHOLE),'removed_sections':removed,'only_other_changes':'BEGIN/TITLE roots','all_other_keyword_sections_identical':True,'whole_original_file_not_modified':True,'diagnostic_only':True});dump(d/'generation.json',{'created_utc':now(),'name':n,'source':rel(WHOLE),'source_sha256':streamsha(WHOLE),'removed_RBE3_definitions':368,'physical_time_credit_s':0,'whole_impact_candidate':False})
 en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,en);log=(d/'starter.log').read_text(errors='replace');w=int(re.findall(r'(\d+) WARNING\(S\)',log)[-1]);e=int(re.findall(r'(\d+) ERROR\(S\)',log)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'pass':ok and w==0 and e==0,'execution_ok':ok,'warnings':w,'errors':e,'zero_warning_gate_retained':True});start=(d/(n+'_0000.out')).read_text();m=re.search(r'TOTAL MASS AND MASS CENTER.*?\n\s*([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)',start,re.S);mass=float(m.group(1));center=[float(x) for x in m.groups()[1:]];ad=float(re.search(r'TOTAL ADDED MASS\s*=\s*([\d.E+\-]+)',start).group(1));mp=abs(mass-c['reference_Starter_mass_g'])<=c['mass_relative_tolerance']*c['reference_Starter_mass_g'] and abs(ad)<=c['added_mass_relative_tolerance']*mass;dump(d/'mass_review.json',{'created_utc':now(),'pass':mp,'reference_mass_g':c['reference_Starter_mass_g'],'variant_mass_g':mass,'added_mass_g':ad,'reference_center_mm':c['reference_Starter_center_mm'],'variant_center_mm':center,'inertia_redistribution_not_assumed_unchanged':True,'no_added_mass_compensation':True});assert mp
 # This declared diagnostic records the known original whole Starter warnings;
 # they prohibit physical qualification but do not hide the graph test.
 finished=launcher.execute(d,n) if ok and e==0 else False;txt=(d/'engine.log').read_text(errors='replace') if (d/'engine.log').exists() else '';node_mass=None
 for f in d.glob(n+'T[0-9][0-9]'):
  converted=win_execute(RUNTIME/'th_to_csv_win64.exe',[f.name],d,f.name+'.converter.log',120,en)
  if converted:
   H=histories(f.with_suffix('.csv'));node_mass=float(H['MASS'][0])
 result={'created_utc':now(),'Starter_errors':e,'Starter_warnings':w,'native_NORMAL_exit0':finished,'CHECK_begin_end':'BEGIN IMPLICIT MODEL CHECKING' in txt and 'END IMPLICIT MODEL CHECKING' in txt,'ASSEMC_KIJ_abort_seen':'assemc_kij_' in txt,'TYPE25_implicit_ignored_warnings':txt.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),'Starter_mass_pass':mp,'native_initial_global_mass_g':node_mass,'native_mass_matches_declared_total':node_mass is not None and abs(node_mass-mass)<=1e-6*mass,'RBE3_removed':368,'causal_uniqueness_proven':False,'whole_impact_qualified':False,'physical_time_credit_s':0};dump(d/'ablation_result.json',result);print(result,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
