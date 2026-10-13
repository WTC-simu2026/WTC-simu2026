"""Map every completed-CHECK warning using cached native node ordering; audit declared constraint roles."""
from probe_aircraft_a50 import ROOT,RUNTIME,CAND,BINARY,WHOLE,read,dump,rel,now,streamsha,harness
from audit_aircraft_a05 import vtk
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,shutil,re,tarfile,hashlib
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a51';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a51_predeclaration.json';PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a50'

def parse(p):
 result={};key=None
 for line in p.read_text().splitlines():
  if line.startswith('/'):key=line;result[key]=[]
  elif key:result[key].append(line)
 return result

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A50';assert read(PREV/'publication_verification.json')['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 old=ROOT/'wtc1_simulation_v8/output/aircraft_a49';d=old/'WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK';e=PREV/'WHOLE_EQUIVALENT_CHAIN_EXPLICIT_STARTUP';n='A49_EQUIVALENT_RIGID_CHAINS'
 files={'input':d/(n+'_0000.rad'),'CHECK_listing':d/(n+'_0001.out'),'CHECK_initial_state':d/(n+'_0000_0001.rst'),'explicit_initial_state':e/(n+'_0000_0001.rst'),'native_animation':e/(n+'A001'),'converted_animation':e/(n+'A001.vtk'),'mapped_trace':old/'native_to_source_mapping_review.json'}
 assert streamsha(files['CHECK_initial_state'])==streamsha(files['explicit_initial_state'])
 c={'created_utc':now(),'iteration':'AIRCRAFT-A51','seed':1102076,'random_draws':0,'purpose':'Translate all49370CHECK connectivity messages and15suspect directions to original source labels via an unchanged full native initial state and its zero-time animation. Audit potential constraint nesting before any correction.','files':{k:{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for k,p in files.items()},'source_archive_sha256':streamsha(CAND/'source.tar.gz'),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','source_paths':['engine/source/output/anim/generate/xyznod.F','engine/source/output/anim/generate/genani.F','engine/source/implicit/ind_glob_k.F','engine/source/interfaces/interf/i2_imp1.F','engine/source/constraints/general/rbe2/rbe2_imp0.F'],'acceptance':{'zero_time_ms':0,'nodes':48171,'all_original_labels_unique':True,'coordinate_export_tolerance_mm':.003,'native_trace_mapping_matches':True,'warning_messages':49370,'suspect_directions':15},'mapping_basis':'One SPMD domain: XYZNOD writes X(:,I) for I=1..NUMNOD and GENANI writes ITAB,NUMNOD; VTK preserves point/label order. Verify sampled direct native IXC/X mapping and every source coordinate.','dependency_scope':'RBE2 masks/root groups exact; TYPE2 surface nodes are a conservative parent set, not actual native interpolation weights. RBE3 potential support group only. Graph paths do not imply mechanical contradiction or a proven cause.','native_solver_replays':0,'new_Starter_or_Engine':0,'software_or_physical_input_patch':False,'source_archives_not_inspected':True,'new_whole_physical_duration_credit_s':0,'objective1_complete':False}
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_analysis':True})
 pins={r['path']:r for f in ['preservation_before_metadata.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
 for f in ['artifact_manifest.json','publication_verification.json']:
  p=PREV/f;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 rows=[]
 for r in pins.values():
  s=(ROOT/r['path']).stat();assert s.st_size==r['bytes'];rows.append({**r,'mtime_ns_before':s.st_mtime_ns})
 dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'method':'Before/after metadata and retained immutable hash manifests','source_archives_not_rescanned':True});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','same_external_blocker':False,'evidence':'A50 registered169, native startup budgets/motions match cached reference, exact384declared link glyph changes identified, CHECK fixed solver override and skipped stiffness blocks established. Cached zero-time native node order now permits full warning mapping without another Engine.'})
 print({'A51_declared':True,'new_native_solver_executions':0,'native_mapping_available_from_cache':True},flush=True)

def roles(S):
 groups={int(k.split('/')[-1]):[int(v) for row in rows[1:] for v in row.split()] for k,rows in S.items() if k.startswith('/GRNOD/NODE/')};out=defaultdict(list);parents=defaultdict(set)
 partnodes=defaultdict(set)
 for key,rows in S.items():
  if key.startswith(('/SHELL/','/SH3N/','/BRICK/','/BEAM/','/TRUSS/')):
   part=int(key.split('/')[-1])
   for row in rows:
    if row.strip():partnodes[part].update(int(v) for v in row.split()[1:])
 surfaces={int(k.split('/')[-1]):set().union(*(partnodes[int(v)] for row in rows[1:] for v in row.split())) for k,rows in S.items() if k.startswith('/SURF/PART/')}
 refs=[]
 for key,rows in S.items():
  if key.startswith('/RBE2/'):
   v=rows[1].split();main=int(v[0]);dep=groups[int(v[4])];entry={'constraint':key,'family':'RBE2','main_nodes':[main],'secondary_nodes':dep,'translation_mask':v[1],'rotation_mask':v[2],'Iflag':int(v[3]),'parents_exact':True};refs.append(entry);out[main].append({'constraint':key,'role':'main','family':'RBE2'})
   for n in dep:out[n].append({'constraint':key,'role':'secondary','family':'RBE2'});parents[n].add(main)
  elif key.startswith('/INTER/TYPE2/'):
   v=rows[1].split();dep=groups[int(v[0])];masters=sorted(surfaces[int(v[1])]);entry={'constraint':key,'family':'TYPE2','main_nodes':masters,'secondary_nodes':dep,'Spotflag':int(v[3]),'parents_exact':False,'scope':'All main surface nodes; actual native facet/weights not inferred'};refs.append(entry)
   for n in masters:out[n].append({'constraint':key,'role':'potential_main','family':'TYPE2'})
   for n in dep:out[n].append({'constraint':key,'role':'secondary','family':'TYPE2'});parents[n].update(masters)
  elif key.startswith('/RBE3/'):
   main=int(rows[1][:10]);gid=int(rows[2].split()[-1]);masters=groups[gid];refs.append({'constraint':key,'family':'RBE3','main_nodes':masters,'secondary_nodes':[main],'parents_exact':False,'scope':'Support group; interpolation weights/DOF projection not reconstructed'});out[main].append({'constraint':key,'role':'reference_dependent','family':'RBE3'})
   for n in masters:out[n].append({'constraint':key,'role':'support','family':'RBE3'})
   parents[main].update(masters)
 return out,parents,refs

def analyze():
 guard();c=read(CFG)
 for r in c['files'].values():assert streamsha(ROOT/r['path'])==r['sha256']
 assert streamsha(CAND/'source.tar.gz')==c['source_archive_sha256'];source=[]
 with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for path in c['source_paths']:
   data=tar.extractfile(members[path]).read();t=data.decode();lines=t.splitlines();source.append({'path':path,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'raw_source_redistributed':False})
   if path.endswith('xyznod.F'):assert 'DO I=1,NUMNOD' in t and 'R4 = X(1,I)' in t;source[-1]['mono_domain_point_order']='Writes each X(:,I) in increasing internal I.'
   if path.endswith('genani.F'):assert 'CALL WRITE_I_C(ITAB,NUMNOD)' in t;source[-1]['mono_domain_label_order']='Writes ITAB in the same increasing internal I.'
 dump(OUT/'source_order_and_graph_review.json',{'created_utc':now(),'source_pin':c['source_pin'],'files':source,'raw_source_redistributed':False,'software_changed':False})
 S=parse(ROOT/c['files']['input']['path']);X={int(row[:10]):np.array([float(v) for v in row[10:].split()]) for row in S['/NODE']};Q=vtk((ROOT/c['files']['converted_animation']['path']).read_text());ids=Q['NODE_ID'].astype(int);coords=Q['points'].reshape(-1,3);a=c['acceptance'];assert len(ids)==a['nodes'] and len(set(ids))==len(ids) and set(ids)==set(X);assert Q['time']==0
 error=float(abs(coords-np.array([X[int(n)] for n in ids])).max());assert error<=a['coordinate_export_tolerance_mm'],error
 mapped=read(ROOT/c['files']['mapped_trace']['path']);sample={}
 for entry in mapped['all_entries']:
  for ni,label in zip(entry['native']['native_node_indices'],entry['source']['nodes']):
   assert int(ids[ni-1])==label,(ni,int(ids[ni-1]),label);sample[ni]=label
 assert len(sample)==302
 dump(OUT/'full_native_node_order_mapping.json',{'created_utc':now(),'pass':True,'nodes':len(ids),'maximum_float_export_coordinate_error_mm':error,'direct_native_capture_correspondences_verified':len(sample),'same_initial_state_SHA256':c['files']['CHECK_initial_state']['sha256'],'mapping':[{'internal_index_1based':i+1,'original_node_label':int(n)} for i,n in enumerate(ids)],'source_order_verified':True})
 rr,parents,refs=roles(S);text=(ROOT/c['files']['CHECK_listing']['path']).read_text();counts=Counter();pairs=Counter();unmapped=[]
 pattern=r'IN (INTERFACE TYPE 2|RBE2) CONDENSATION:\s*\*\*\* NO CONNECTIVITY BETWEEN NODES:\s*(\d+)\s+(\d+)'
 for family,s1,s2 in re.findall(pattern,text):
  i,j=int(s1),int(s2);assert 1<=i<=len(ids) and 1<=j<=len(ids);n,m=int(ids[i-1]),int(ids[j-1]);pairs[(family,i,j,n,m)]+=1;counts[family]+=1
 assert sum(counts.values())==a['warning_messages']
 summary=Counter();details=[]
 def tag(n):return '+'.join(sorted({r['family']+':'+r['role'] for r in rr[n]})) or 'independent_declared_node'
 for (family,i,j,n,m),number in pairs.items():
  summary[(family,tag(n),tag(m))]+=number;details.append({'family':family,'internal_nodes':[i,j],'original_nodes':[n,m],'messages':number,'node_roles':[rr[n],rr[m]]})
 suspect=[]
 for ni,kind,axis,val in re.findall(r'NODE NUM\.\s*=\s*(\d+)\s+(TRA|ROT)_DIR\s*=\s*([XYZ])\s+VAL\.\s*=\s*([\d.E+\-]+)',text):
  i=int(ni);n=int(ids[i-1]);suspect.append({'internal_node':i,'original_node':n,'kind':kind,'axis':axis,'value_native':float(val),'roles':rr[n],'coordinates_mm':X[n].tolist()})
 assert len(suspect)==a['suspect_directions']
 # Static conservative role graph: this does not reconstruct the actual native interpolation matrix.
 secondary=defaultdict(list)
 for r in refs:
  for n in r['secondary_nodes']:secondary[n].append(r['constraint'])
 overlap=[{'node':n,'constraints':v} for n,v in secondary.items() if len(v)>1];nesting=[]
 for r in refs:
  prior=[n for n in r['main_nodes'] if n in secondary]
  if prior:nesting.append({'constraint':r['constraint'],'family':r['family'],'potential_parent_nodes_also_dependent':prior,'parent_constraints':sorted({k for n in prior for k in secondary[n]}),'exact_parents':r['parents_exact']})
 result={'created_utc':now(),'warning_message_counts':dict(counts),'unique_ordered_native_pairs_by_family':len(pairs),'mapped_original_labels_verified':True,'role_message_summary':[{'family':f,'first_role':r,'second_role':s,'messages':v} for (f,r,s),v in summary.items()],'suspect_stiffness_directions':suspect,'pairs':details,'constraint_family_counts':dict(Counter(r['family'] for r in refs)),'multiple_declared_secondary_constraints':overlap,'nested_constraints':nesting,'actual_native_interpolation_weights_reconstructed':False,'missing_graph_cause_uniquely_proven':False,'physical_instability_claim':False,'new_solver_executions':0,'whole_impact_qualified':False,'new_whole_duration_credit_s':0}
 dump(OUT/'whole_constraint_role_mapping_review.json',result);dump(OUT/'declared_constraint_dependency_graph.json',{'created_utc':now(),'constraints':refs,'secondary_parent_graph':[{'node':n,'potential_parents':sorted(v)} for n,v in parents.items()],'exact_only_for_RBE2':True,'actual_TYPE2_RBE3_weights_not_inferred':True})
 print({'all_warning_messages_mapped':sum(counts.values()),'unique_pairs':len(pairs),'suspect_original_nodes':sorted({r['original_node'] for r in suspect}),'multiple_secondary_constraints':len(overlap),'nested_constraints':len(nesting),'role_summary':result['role_message_summary']},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','analyze']);globals()[p.parse_args().action]()
