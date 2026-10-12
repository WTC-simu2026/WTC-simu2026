"""Input-only constant LAW117 tables; preserve strengths, geometry and prior attempts."""
from probe_aircraft_a42 import *
from probe_aircraft_a37 import env
import re, math

DEC=OUT/'constant_tables_predeclaration.json'
NAME='A42_WHOLE_CONST_TABLES'
SOURCE_DECK=SOURCE/'A37_WHOLE_CHECK_0000.rad'

def declare():
 guard();assert not DEC.exists();h=harness();dump(OUT/'harness_before_constant_tables.json',h)
 lines=SOURCE_DECK.read_text().splitlines();idx=lines.index('/MAT/LAW117/117');assert lines[idx+4].split()==['0','0','450','100','1']
 ids=[int(x) for x in re.findall(r'^/FUNCT/(\d+)', '\n'.join(lines),re.M)];assert ids==list(range(280,286));assert sum(x.startswith('/MAT/LAW117/') for x in lines)==1
 numeric={'EN':4400.,'ET':800.,'TN':450.,'TT':100.,'GIC':50.,'GIIC':50.,'Fscale_x':1.,'curve_ordinate':1.,'curve_abscissae':[0.,1e12]}
 comparisons=[]
 for mode,k,t,g in [('normal',4400.,450.,50.),('shear',800.,100.,50.)]:
  peak=t*1.;old=[t,t/k,2*g/t];new=[peak,peak/k,2*g/peak];assert old==new
  comparisons.append({'mode':mode,'old_peak_initiation_ultimate':[float(v) for v in old],'table_peak_initiation_ultimate':[float(v) for v in new],'exact_algebraic_equality':True,'unchanged_energy_above_minimum':g>=t*t/(2*k)})
 sources=[build.CAND/'source'/x for x in ['engine/source/materials/mat/mat117/sigeps117.F90','starter/source/materials/mat/mat117/hm_read_mat117.F90','starter/source/materials/tools/mat_table_copy.F90']]
 dump(DEC,{'created_utc':now(),'before_native':True,'iteration':'AIRCRAFT-A42','seed':1102067,'random_draws':0,'source_deck':rel(SOURCE_DECK),'source_sha256':streamsha(SOURCE_DECK),'fresh_Starter_required':True,'function_ids':[286,287],'changed_physical_data_family':'LAW117 optional table representation only','numeric_parameters':numeric,'equivalence':comparisons,'curve_units':{'x':'element size mm','y':'dimensionless scale; TN/TT remain450/100MPa'},'physical_parameters_unchanged':True,'mass_material_geometry_contact_BCS_unchanged':True,'source_commit':build.PIN,'source_files':[{'path':rel(p),'sha256':streamsha(p)} for p in sources],'documentation':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm','native_engine_sha256':streamsha(build.CAND/'isolated_exec/engine_linux64_gf_ompi'),'execution':{'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'explicit_end_ms':1e-5,'CHECK_only_if_explicit_completes':True,'new_software_install_or_build':False},'limits':'An input-level algebraic equivalence is not proof of native-state compatibility or physical whole-model qualification.'})
 dump(OUT/'constant_tables_guard.json',{'sha256':streamsha(DEC)})

def normalized_deck():
 assert streamsha(DEC)==read(OUT/'constant_tables_guard.json')['sha256'];assert streamsha(SOURCE_DECK)==read(DEC)['source_sha256'];lines=SOURCE_DECK.read_text().splitlines();original=lines.copy();assert lines[2]==lines[7]=='A37_WHOLE_CHECK';lines[2]=lines[7]=NAME;idx=lines.index('/MAT/LAW117/117');assert lines[idx+4][:20].split()==['0','0'];lines[idx+4]=native37.ii(286,287)+lines[idx+4][20:]
 changed=[i+1 for i,(a,b) in enumerate(zip(original,lines)) if a!=b];assert changed==[3,8,idx+5]
 end=lines.index('/END');cards=[]
 for f in [286,287]:cards += [f'/FUNCT/{f}','CONSTANT_UNIT_SCALE_LAW117',ff(0,1),ff(1e12,1)]
 lines[end:end]=cards;recovered=lines.copy();del recovered[end:end+len(cards)];recovered[2]=recovered[7]='A37_WHOLE_CHECK';recovered[idx+4]=original[idx+4];assert recovered==original
 return '\n'.join(lines)+'\n',changed,end+1

def run():
 guard();dec=read(DEC);assert dec['before_native'];d=OUT/'WHOLE_CONST_TABLES_W1';assert not d.exists();d.mkdir();text,changed,inserted=normalized_deck();n=NAME;(d/(n+'_0000.rad')).write_text(text,encoding='utf8');g=read(SOURCE/'generation.json');g.update(name=n,case={'platform':'Linux'},input_representation='two constant unit tables with unchanged TN/TT',supplemental_configuration_sha256=streamsha(DEC));dump(d/'generation.json',g)
 dump(d/'input_diff_review.json',{'source':rel(SOURCE_DECK),'source_sha256':streamsha(SOURCE_DECK),'new_sha256':streamsha(d/(n+'_0000.rad')),'changed_original_line_numbers':changed,'inserted_curves_before_original_line':inserted,'full_original_recovered_after_removing_declared_representation':True,'new_function_ids':[286,287],'algebraic_equivalence':dec['equivalence'],'physical_changes':False})
 cards=(OUT/'WHOLE_EXPLICIT_READ/A37_WHOLE_CHECK_0001.rad').read_text().replace('A37_WHOLE_CHECK',n);(d/(n+'_0001.rad')).write_text(cards,encoding='utf8');en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');ok=native37.win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,en);s=(d/'starter.log').read_text(errors='replace');w=re.findall(r'(\d+) WARNING\(S\)',s);e=re.findall(r'(\d+) ERROR\(S\)',s);check={'exit_ok':ok,'warnings':int(w[-1]) if w else None,'errors':int(e[-1]) if e else None};check['prepared']=ok and check['errors']==0 and (d/(n+'_0000_0001.rst')).exists();check['strict_pass']=check['prepared'] and check['warnings']==0;dump(d/'starter_gate.json',check);print({'fresh_Starter':check},flush=True)
 native=False
 if check['prepared']:native=native37.native(d,n,1)
 dump(d/'review.json',{'created_utc':now(),'starter':check,'native_explicit_completed':native,'input_algebraic_equivalence':True,'native_physical_equivalence_qualified':False,'whole_impact_qualified':False,'new_physical_duration_credit_s':0});print({'constant_table_explicit_completed':native},flush=True)
 if native:
  q=OUT/'WHOLE_CONST_TABLES_CHECK';q.mkdir();initial=d/(n+'_0000_0001.rst');shutil.copy2(initial,q/initial.name);dump(q/'generation.json',g);native37.CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json';s='/IMPL/RREF/LIMIT\n'+ff(1,1e30)+'\n'+PARENT_CARDS(n,1,'I',.001,.001,'FREE',True);(q/(n+'_0001.rad')).write_text(s,encoding='utf8');complete=native37.native(q,n,1);log=(q/'engine.log').read_text(errors='replace');dump(q/'review.json',{'created_utc':now(),'native_completed':complete,'check_report_begins':'BEGIN IMPLICIT MODEL CHECKING' in log,'check_report_ends':'END IMPLICIT MODEL CHECKING' in log,'initial_state_copied_hash_equal':streamsha(initial)==streamsha(q/initial.name),'whole_impact_qualified':False});print({'constant_table_CHECK_completed':complete},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
