"""Isolate native shell stiffness assembly using source-identical facade patches."""
from probe_aircraft_a45 import ROOT,RUNTIME,CAND,BINARY,read,dump,rel,now,streamsha,harness
import probe_aircraft_a45 as launcher
from probe_aircraft_a37 import WHOLE,ii,ff,group,env,win_execute
from pathlib import Path
import argparse,shutil,json,re,tarfile,hashlib,numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a46'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a46_predeclaration.json'
CASES=['FACADE_PATCH_FREE','FACADE_PATCH_FIXED_EDGE']

def guard():
 assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256'];launcher.guard()

def sections():
 result={};key=None;rows=[]
 for line in WHOLE.read_text(encoding='utf8').splitlines():
  if line.startswith('/'):
   if key:result[key]=rows
   key=line;rows=[]
  else:rows.append(line)
 if key:result[key]=rows
 return result

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();st=read(ROOT/'harness/state.json');assert h['Status']=='PASS' and st['current_iteration']=='AIRCRAFT-A45';assert read(ROOT/'wtc1_simulation_v8/output/aircraft_a45/publication_verification.json')['pass'];cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A45'
 OUT.mkdir();dump(OUT/'harness_before.json',h)
 for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
 prior=ROOT/'wtc1_simulation_v8/output/aircraft_a45';pins={r['path']:r for n in ['preservation_before.json','artifact_manifest.json'] for r in read(prior/n)['files']}
 for n in ['artifact_manifest.json','publication_verification.json']:
  f=prior/n;pins[rel(f)]={'path':rel(f),'bytes':f.stat().st_size,'sha256':streamsha(f)}
 protected=[]
 for r in pins.values():
  stat=(ROOT/r['path']).stat();assert stat.st_size==r['bytes'];protected.append({**r,'mtime_ns_before':stat.st_mtime_ns})
 dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':protected,'SHA256_proofs_reused':rel(prior/'preservation_verification.json'),'prior_all_old_hashes_verified':read(prior/'preservation_verification.json')['pass'],'method':'Existing immutable SHA256 manifests retained; current before/after bytes and mtime audit. This is not a fresh full-content rehash of all older files.','source_archives_not_rescanned':True})
 sec=sections();el=[list(map(int,r.split())) for r in sec['/SHELL/31'][:4]];nodes=sorted({n for e in el for n in e[1:]});node={int(r[:10]):[float(x) for x in r[10:].split()] for r in sec['/NODE']};xyz=np.array([node[n] for n in nodes]);patch={'original_elements':el,'original_node_ids':nodes,'coordinates_mm':xyz.tolist(),'material_section':'/MAT/LAW2/3','property_section':'/PROP/TYPE1/31','part_section':'/PART/31','zero_initial_velocity':True,'whole_boundary_not_inherited':True};area=0
 for e in el:
  x=np.array([node[n] for n in e[1:]]);area+=np.linalg.norm(np.cross(x[1]-x[0],x[2]-x[0]))/2+np.linalg.norm(np.cross(x[2]-x[0],x[3]-x[0]))/2
 patch.update(area_mm2=float(area),expected_mass_g=float(area*7.9375*.00786))
 dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A46','seed':1102071,'random_draws':0,'purpose':'Separate source-identical Ishell24 facade stiffness assembly from whole-model topology; compare free/fixed-edge CHECK only. No physical impact extension.','parent':'AIRCRAFT-A45','source_whole':rel(WHOLE),'source_whole_sha256':streamsha(WHOLE),'Engine_sha256':streamsha(BINARY),'cases':CASES,'patch':patch,'case_difference':'Only a declared fixed edge BCS added to second isolated patch. Original geometry, shell connectivity, steel density/material/property copied unchanged.','CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_wall_s':60,'maximum_total_wall_s':720,'no_new_installation_or_compilation':True,'whole_input_not_modified':True,'acceptance':{'Starter_errors':0,'Starter_warnings':0,'Engine_exit':0,'normal_termination':True,'CHECK_begin_end':True,'mass_relative':1e-6,'added_mass_relative':1e-9,'no_physical_duration_credit':True},'sources':[{'path':rel(ROOT/'wtc1_simulation_v8/output/aircraft_a45/WHOLE_IMPLICIT_CHECK/engine.log'),'sha256':streamsha(ROOT/'wtc1_simulation_v8/output/aircraft_a45/WHOLE_IMPLICIT_CHECK/engine.log')},{'path':rel(CAND/'source.tar.gz'),'sha256':read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/source_archive.json')['sha256']}],'source_inspection_scope':['engine/source/implicit/imp_glob_k.F','engine/source/implicit/assem_c4.F','engine/source/elements/shell/coqueba/cbake3.F'],'whole_implicit_qualified':False,'objective1_complete':False})
 dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True});print({'A46_declared':True,'native_shell_CHECK_cases':2,'whole_physics_unchanged':True},flush=True)

def run():
 guard();cfg=read(CFG);sec=sections();patch=cfg['patch'];ids=patch['original_node_ids'];coords=patch['coordinates_mm'];mapping={n:i+1 for i,n in enumerate(ids)};rows=[]
 archive=CAND/'source.tar.gz';assert streamsha(archive)==cfg['sources'][1]['sha256'];source_rows=[]
 with tarfile.open(archive,'r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for f in cfg['source_inspection_scope']:
   data=tar.extractfile(members[f]).read();source_rows.append({'path':f,'sha256':hashlib.sha256(data).hexdigest(),'source_pin':read(ROOT/'wtc1_simulation_v8/data/aircraft_a45_predeclaration.json')['build']['complete_source_pin'],'raw_source_redistributed':False})
 dump(OUT/'stiffness_source_review.json',{'created_utc':now(),'files':source_rows,'observed_calls':'CBAKE3 assembles four-node shell stiffness through ASSEM_C4 then ASSEMC_KIJ; six nominal shell DOF blocks, NDOF controls active rows.','hypothesis':'Whole topology, boundary constraints or mixed DOF graph may differ from isolated shell; source branch alone does not identify the failing native element.','known_missing_guard':'ASSEMC_KIJ searches JDIK for a block then uses JDL without an explicit not-found branch. No source patch and no proven missing block in native whole state.','physical_cause_inferred':False})
 for name in CASES:
  d=OUT/name;assert not d.exists();d.mkdir();n='A46_'+name
  L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*x) for i,x in enumerate(coords)]
  for key in ['/MAT/LAW2/3','/PROP/TYPE1/31','/PART/31']:L+=[key]+sec[key]
  L+=['/SHELL/31']+[ii(i+1,*[mapping[n] for n in e[1:]]) for i,e in enumerate(patch['original_elements'])]
  if name.endswith('FIXED_EDGE'):
   # Original first patch edge: element20001 local nodes1,2.
   edge=patch['original_elements'][0][1:3];L+=group(900,'DECLARED_DIAGNOSTIC_FIXED_EDGE',[mapping[n] for n in edge])+['/BCS/900','DECLARED_FIXED_EDGE','   111 111'+ii(0,900)]
  L+=['/TH/PART/31','PATCH_ENERGY',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(31),'/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf8')
  E='/IMPL/RREF/LIMIT\n'+ff(1,1e30)+'\n/IMPL/NONLIN/1\n0 123 1e-11 1e-11 1e-11\n/IMPL/SOLVER/2\n'+ii(2,0,1)+ff(1e-8)+'\n/IMPL/DTINI\n'+ff(.001)+'\n/IMPL/DYNA/2\n'+ff(.5,.25)+'\n/IMPL/CHECK\n/PRINT/-100/100\n/RUN/'+n+'/1\n'+ff(.001)+'\n/TFILE/4\n'+ff(.001)+'\n/VERS/2026\n';(d/(n+'_0001.rad')).write_text(E,encoding='utf8');dump(d/'generation.json',{'created_utc':now(),'name':n,'patch':patch,'boundary_case':name,'configuration_sha256':streamsha(CFG),'whole_physics_unchanged':True,'physical_time_credit_s':0})
  ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,env());log=(d/'starter.log').read_text(errors='replace');warnings=int(re.findall(r'(\d+) WARNING\(S\)',log)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',log)[-1]);strict=ok and warnings==0 and errors==0;dump(d/'starter_gate.json',{'warnings':warnings,'errors':errors,'pass':strict})
  finished=launcher.execute(d,n) if strict else False;txt=(d/'engine.log').read_text(errors='replace') if (d/'engine.log').exists() else '';report=(d/(n+'_0001.out')).read_text(errors='replace') if (d/(n+'_0001.out')).exists() else '';checking='BEGIN IMPLICIT MODEL CHECKING' in txt and 'END IMPLICIT MODEL CHECKING' in txt;result={'case':name,'strict_Starter':strict,'native_completed':finished,'CHECK_report_begin_end':checking,'pass':strict and finished and checking,'physical_time_credit_s':0,'report':rel(d/(n+'_0001.out')),'unsupported_TYPE25_count':txt.count('INTERFACE TYPE 25 IS NOT AVAILABLE')};dump(d/'review.json',result);rows.append(result);print(result,flush=True)
 dump(OUT/'patch_CHECK_review.json',{'created_utc':now(),'cases':rows,'all_pass':all(r['pass'] for r in rows),'whole_CHECK_fixed':False,'whole_implicit_qualified':False,'physical_time_credit_s':0,'interpretation':'An isolated shell pass cannot identify whole mixed-topology failure; actual CHECK termination and report assessed independently.'})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
