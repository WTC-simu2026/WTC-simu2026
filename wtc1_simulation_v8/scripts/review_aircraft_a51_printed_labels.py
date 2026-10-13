"""Correct printed-node semantics at the call sites, retaining the earlier wrong index interpretation."""
from probe_aircraft_a51_native_precision_r3 import ROOT,OUT,CFG,CAND,read,dump,rel,now,streamsha,guard,parse,roles
from collections import Counter,defaultdict
import re,tarfile,hashlib

def main():
 guard();target=OUT/'verified_printed_node_role_review.json';assert not target.exists();c=read(CFG)
 mapping=read(OUT/'full_native_node_order_mapping_r3.json');assert mapping['pass'];inverse={r['original_node_label']:r['internal_index_1based'] for r in mapping['mapping']}
 source=[]
 with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for path in ['engine/source/interfaces/interf/i2_imp1.F','engine/source/constraints/general/rbe2/rbe2_imp0.F','engine/source/implicit/imp_solv.F']:
   b=tar.extractfile(members[path]).read();lines=b.decode().splitlines();row={'path':path,'sha256':hashlib.sha256(b).hexdigest(),'raw_source_redistributed':False}
   if path.endswith('imp_solv.F'):
    writes=[{'line':i+1,'arguments':s.strip()} for i,s in enumerate(lines) if 'WRITE(IOUT,100' in s and 'ITAB(I),DIR' in s];assert len(writes)==4;row['zero_stiffness_and_mass_diagnostic_writes']=writes
   else:
    calls=[{'line':i+1,'arguments':s.strip()} for i,s in enumerate(lines) if 'CALL PRINT_WKIJ' in s];assert calls and all('PRINT_WKIJ(ITAB(' in r['arguments'] for r in calls);row['all_PRINT_WKIJ_calls_pass_original_ITAB_labels']=calls
   source.append(row)
 declaration=ROOT/'wtc1_simulation_v8/data/aircraft_a51_printed_label_correction_predeclaration.json';assert not declaration.exists();dump(declaration,{'created_utc':now(),'iteration':'AIRCRAFT-A51','seed':1102076,'random_draws':0,'source_call_sites':source,'correction':'The printer itself receives NI/NJ unchanged, but TYPE2/RBE2 callers pass ITAB(NI)/ITAB(NJ), so printed numbers are original source labels. Zero-stiffness printer also uses ITAB(I). Earlier reinterpretation as internal indices is rejected.','original_role_review_retained':rel(OUT/'whole_constraint_role_mapping_review.json'),'native_coordinate_and_index_map_remains_valid':True,'no_criteria_physics_or_solver_change':True,'before_corrected_role_analysis':True})
 S=parse(ROOT/c['files']['input']['path']);rr,parents,refs=roles(S);text=(ROOT/c['files']['CHECK_listing']['path']).read_text();counts=Counter();pairs=Counter();summary=Counter()
 pattern=r'IN (INTERFACE TYPE 2|RBE2) CONDENSATION:\s*\*\*\* NO CONNECTIVITY BETWEEN NODES:\s*(\d+)\s+(\d+)'
 for family,v,w in re.findall(pattern,text):
  n,m=int(v),int(w);assert n in inverse and m in inverse;pairs[(family,n,m)]+=1;counts[family]+=1
 assert sum(counts.values())==49370
 def tag(n):return '+'.join(sorted({r['family']+':'+r['role'] for r in rr[n]})) or 'independent_declared_node'
 details=[]
 for (f,n,m),number in pairs.items():
  summary[(f,tag(n),tag(m))]+=number;details.append({'family':f,'original_nodes':[n,m],'native_internal_indices':[inverse[n],inverse[m]],'messages':number,'roles':[rr[n],rr[m]]})
 X={int(row[:10]):[float(v) for v in row[10:].split()] for row in S['/NODE']};suspect=[]
 for v,kind,axis,value in re.findall(r'NODE NUM\.\s*=\s*(\d+)\s+(TRA|ROT)_DIR\s*=\s*([XYZ])\s+VAL\.\s*=\s*([\d.E+\-]+)',text):
  n=int(v);assert n in inverse;suspect.append({'original_node':n,'native_internal_index':inverse[n],'kind':kind,'axis':axis,'value_native':float(value),'roles':rr[n],'coordinates_mm':X[n]})
 assert len(suspect)==15
 secondary=defaultdict(list)
 for r in refs:
  for n in r['secondary_nodes']:secondary[n].append(r['constraint'])
 nesting=[]
 for r in refs:
  inherited=[n for n in r['main_nodes'] if n in secondary]
  if inherited:nesting.append({'constraint':r['constraint'],'family':r['family'],'potential_parent_nodes_also_dependent':inherited,'parent_constraints':sorted({k for n in inherited for k in secondary[n]}),'exact_parents':r['parents_exact']})
 result={'created_utc':now(),'pass_printed_label_semantics_and_membership':True,'source_call_sites':source,'original_false_warning_index_interpretation_rejected':True,'original_false_review_retained':rel(OUT/'whole_constraint_role_mapping_review.json'),'native_index_map_valid_for_reverse_lookup':True,'warning_message_counts':dict(counts),'unique_ordered_pairs_by_family':len(pairs),'role_message_summary':[{'family':f,'first_role':r,'second_role':s,'messages':v} for (f,r,s),v in summary.items()],'suspect_stiffness_directions':suspect,'pairs':details,'multiple_declared_secondary_constraints':[{'node':n,'constraints':v} for n,v in secondary.items() if len(v)>1],'nested_constraints':nesting,'actual_native_TYPE2_RBE3_interpolation_weights_reconstructed':False,'missing_graph_cause_uniquely_proven':False,'physical_instability_claim':False,'new_native_solver_executions':0,'software_or_physics_changed':False,'whole_impact_qualified':False,'new_whole_duration_credit_s':0}
 dump(target,result);print({'source_label_semantics_verified':True,'messages':sum(counts.values()),'unique_pairs':len(pairs),'suspect_original_nodes':sorted({r['original_node'] for r in suspect}),'role_summary':result['role_message_summary'],'nested_by_family':dict(Counter(r['family'] for r in nesting))},flush=True)

if __name__=='__main__':main()
