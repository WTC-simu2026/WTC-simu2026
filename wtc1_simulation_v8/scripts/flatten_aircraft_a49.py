"""Compose fully constrained rigid-body chains without discarding offsets, lever effects or masses."""
from probe_aircraft_a49 import *
import numpy as np,math
from probe_aircraft_a48 import check_cards
from audit_aircraft_a05 import histories
DEC=ROOT/'wtc1_simulation_v8/data/aircraft_a49_flatten_predeclaration.json'

def relations():
 sec=sections();groups={int(k.split('/')[-1]):[int(v) for row in rows[1:] for v in row.split()] for k,rows in sec.items() if k.startswith('/GRNOD/NODE/')};outer={}
 for key,rows in sec.items():
  if key.startswith('/RBE2/') and rows[0]=='DECLARED_IDEAL_ROOT_ATTACHMENT':
   v=rows[1].split();assert v[1:4]==['111','111','0'] and v[-1]=='0'
   for n in groups[int(v[4])]:assert n not in outer;outer[n]={'keyword':key,'main':int(v[0]),'definition':rows}
 out=[]
 for key,rows in sec.items():
  if key.startswith('/RBE2/') and rows[0].startswith('MASSLESS_COH_OFFSET_FROM_'):
   v=rows[1].split();mid=int(v[0])
   if mid in outer:
    assert v[1:4]==['111','000','0'] and v[-1]=='0';out.append({'keyword':key,'intermediate':mid,'direct_main':outer[mid]['main'],'outer':outer[mid]['keyword'],'outer_definition':outer[mid]['definition'],'inner_definition':rows,'secondary_group':int(v[4]),'secondary_nodes':groups[int(v[4])]})
 return out

def declare():
 guard();assert not DEC.exists();mapped=read(OUT/'native_to_source_mapping_review.json');sec=sections();links=relations();assert len(links)==144;nodes={int(r[:10]):[float(x) for x in r[10:].split()] for r in sec['/NODE']};bad=[x for x in mapped['all_entries'] if 'missing_sparse_pair' in x];covered={x['intermediate'] for x in links};assert all(x['missing_sparse_pair']['original_nodes'][0] in covered for x in bad);dump(DEC,{'created_utc':now(),'iteration':'AIRCRAFT-A49','seed':1102074,'random_draws':0,'case':'WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK','reason':'All26missing pairs have a skin node simultaneously fully dependent on a root rigid body and main of an offset rigid body. Minimal reduced scenes and drilling switch do not reproduce/fix whole fault. Compose only these fully constrained rigid chains with exact original lever effects.','relations':links,'source':rel(WHOLE),'source_sha256':streamsha(WHOLE),'changes':'144inner rigid-body reference node IDs redirected to original outer roots; dependent groups/masks/Iflag/skews and every physical node/material/mass/property/contact/RBE3 remain unchanged.','formal_velocity_identity':'v_mid=v_outer+omega_outer cross(Xmid-Xouter); omega_mid=omega_outer. Then v_slave=v_outer+omega_outer cross(Xslave-Xouter).','formal_force_moment_identity':'(Xmid-Xouter) cross F+(Xslave-Xmid) cross F=(Xslave-Xouter) cross F. Fully constrained intermediate rotation/translation only; no weaker translational link or lost .25mm offset.','finite_pose_identity':'Xslave(t)=Xouter(t)+R(t)*(Xslave0-Xouter0), with identical full outer/intermediate rotation and common zero skew.','algebra_audit':{'poses':8,'maximum_angle_rad':.7,'velocity_and_force_draws':8,'rng_seed':1102074,'position_velocity_absolute_tolerance':1e-8,'moment_absolute_tolerance_Nmm':1e-7},'independent_dynamic_budget_and_local_work_checks_required_before_impact':True,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_s':60,'maximum_total_s':360,'new_installation_or_compilation':False,'whole_original_not_overwritten':True,'new_whole_duration_credit_s':0,'objective1_complete':False});dump(OUT/'flatten_guard.json',{'created_utc':now(),'sha256':streamsha(DEC),'before_new_native':True});print({'equivalent_rigid_chains_declared':len(links),'missing_pairs_covered':len(bad)},flush=True)

def algebra():
 guard();c=read(DEC);assert streamsha(DEC)==read(OUT/'flatten_guard.json')['sha256'];sec=sections();X={int(r[:10]):np.asarray([float(v) for v in r[10:].split()]) for r in sec['/NODE']};rng=np.random.default_rng(c['algebra_audit']['rng_seed']);maxp=maxv=maxm=0.;samples=0
 for reln in c['relations']:
  outer=X[reln['direct_main']];mid=X[reln['intermediate']]
  for _ in range(8):
   axis=rng.normal(size=3);axis/=np.linalg.norm(axis);theta=rng.uniform(-.7,.7);K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]]);R=np.eye(3)+math.sin(theta)*K+(1-math.cos(theta))*(K@K);origin=outer+rng.normal(size=3);vm=rng.normal(size=3);omega=rng.normal(size=3)
   for n in reln['secondary_nodes']:
    slave=X[n];r1=R@(mid-outer);r2=R@(slave-mid);direct=R@(slave-outer);hier=origin+r1+r2;flat=origin+direct;v1=vm+np.cross(omega,r1);vh=v1+np.cross(omega,r2);vf=vm+np.cross(omega,direct);F=rng.normal(size=3)*1000;Mh=np.cross(r1,F)+np.cross(r2,F);Mf=np.cross(direct,F);maxp=max(maxp,float(abs(hier-flat).max()));maxv=max(maxv,float(abs(vh-vf).max()));maxm=max(maxm,float(abs(Mh-Mf).max()));samples+=1
 a=c['algebra_audit'];checks={'finite_pose_composition':maxp<=a['position_velocity_absolute_tolerance'],'velocity_lever_composition':maxv<=a['position_velocity_absolute_tolerance'],'force_moment_lever_composition':maxm<=a['moment_absolute_tolerance_Nmm']};result={'created_utc':now(),'checks':checks,'pass':all(checks.values()),'samples':samples,'rng_seed':a['rng_seed'],'maximum_position_error_mm':maxp,'maximum_velocity_error_mm_ms':maxv,'maximum_moment_error_Nmm':maxm,'offsets_not_dropped':True,'known_damage_or_solver_output_not_used_as_target':True,'scope':'Independent rigid-equation identities; not native force, mass redistribution or impact qualification.'};p=OUT/'rigid_chain_algebra_review.json';assert not p.exists();dump(p,result);assert result['pass'];print(result,flush=True)

def run():
 guard();c=read(DEC);assert read(OUT/'rigid_chain_algebra_review.json')['pass'];assert streamsha(WHOLE)==c['source_sha256'];d=OUT/c['case'];assert not d.exists();d.mkdir();n='A49_EQUIVALENT_RIGID_CHAINS';orig=WHOLE.read_text().splitlines();lines=orig.copy();changed=[]
 for item in c['relations']:
  i=lines.index(item['keyword'])+2;old=lines[i];assert int(old[:10])==item['intermediate'];lines[i]=ii(item['direct_main'])+old[10:];changed.append({'line':i+1,'keyword':item['keyword'],'old_reference':item['intermediate'],'new_reference':item['direct_main'],'rest_of_definition_unchanged':lines[i][10:]==old[10:]})
 for key in ['/BEGIN','/TITLE']:i=lines.index(key)+1;lines[i]=n
 assert sum(a!=b for a,b in zip(orig,lines))==146;(d/(n+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf8');(d/(n+'_0001.rad')).write_text(check_cards(n),encoding='utf8');dump(d/'input_equivalence_review.json',{'created_utc':now(),'pass':True,'changed_reference_nodes':changed,'only_other_changes':'Two root/title names','physical_sections_masks_groups_offsets_contacts_RBE3_unchanged':True,'rigid_chain_algebra':rel(OUT/'rigid_chain_algebra_review.json')});dump(d/'generation.json',{'created_utc':now(),'name':n,'configuration_sha256':streamsha(DEC),'new_physical_duration_credit_s':0,'equivalent_constraint_representation_candidate':True});en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,en);log=(d/'starter.log').read_text();w=int(re.findall(r'(\d+) WARNING\(S\)',log)[-1]);e=int(re.findall(r'(\d+) ERROR\(S\)',log)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'pass':ok and w==0 and e==0,'warnings':w,'errors':e,'strict_warning_gate_retained':True});ref=read(ROOT/'wtc1_simulation_v8/data/aircraft_a49_standard_implicit_predeclaration.json');start=(d/(n+'_0000.out')).read_text();mm=re.search(r'TOTAL MASS AND MASS CENTER.*?\n\s*([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)\s+([\d.E+\-]+)',start,re.S);mass=float(mm.group(1));center=[float(v) for v in mm.groups()[1:]];ad=float(re.search(r'TOTAL ADDED MASS\s*=\s*([\d.E+\-]+)',start).group(1));mp=abs(mass-ref['reference_mass_g'])<=1e-6*ref['reference_mass_g'] and ad==ref['reference_prescribed_ADMAS_g'];dump(d/'mass_review.json',{'created_utc':now(),'pass':mp,'mass_g':mass,'reference_mass_g':ref['reference_mass_g'],'center_mm':center,'reference_center_mm':ref['reference_center_mm'],'prescribed_ADMAS_g':ad,'no_mass_or_inertia_compensation':True,'redistributed_native_mass_tensor_not_assumed_identical':True});assert mp
 import probe_aircraft_a45 as launch
 normal=launch.execute(d,n) if ok and e==0 else False;txt=(d/'engine.log').read_text() if (d/'engine.log').exists() else '';ce=re.search(r'(\d+) ERRORS',txt);cw=re.search(r'(\d+) WARNINGS',txt);history=None
 for f in d.glob(n+'T[0-9][0-9]'):
  if win_execute(RUNTIME/'th_to_csv_win64.exe',[f.name],d,f.name+'.converter.log',120,en):
   H=histories(f.with_suffix('.csv'));history={'samples':len(H['time']),'first_ms':float(H['time'][0]) if len(H['time']) else None,'mass_g':float(H['MASS'][0]) if len(H['time']) else None,'added_mass_scaling_g':float(abs(H['ADDED MASS']).max()) if len(H['time']) else None}
  else:history={'converter_failed':True,'native_history_retained':True}
 result={'created_utc':now(),'native_NORMAL_exit0':normal,'CHECK_begin_end':'BEGIN IMPLICIT MODEL CHECKING' in txt and 'END IMPLICIT MODEL CHECKING' in txt,'ASSEMC_KIJ_abort_seen':'assemc_kij_' in txt,'TYPE25_ignored_warnings':txt.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),'Starter_warnings':w,'Starter_errors':e,'CHECK_errors':int(ce.group(1)) if ce else None,'CHECK_warnings':int(cw.group(1)) if cw else None,'mass_input_pass':mp,'history':history,'source_rigid_equation_identity_pass':True,'whole_impact_qualified':False,'new_physical_duration_credit_s':0};dump(d/'equivalent_chain_CHECK_review.json',result);print(result,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','algebra','run']);globals()[p.parse_args().action]()
