"""Form a bounded cross-interface graph hypothesis from verified labels and pinned source."""
from probe_aircraft_a51 import *

def main():
 guard();target=OUT/'cross_interface_hypothesis_review.json';assert not target.exists();r=read(OUT/'verified_printed_node_role_review.json');assert r['pass_printed_label_semantics_and_membership'];counts=Counter();examples=[]
 for p in r['pairs']:
  if p['family']!='INTERFACE TYPE 2':continue
  sets=[{x['constraint'] for x in roles if x['family']=='TYPE2'} for roles in p['roles']]
  if not all(sets):key='not_both_directly_in_declared_TYPE2'
  elif sets[0]&sets[1]:key='at_least_one_common_declared_TYPE2'
  else:key='different_declared_TYPE2_sets'
  counts[key]+=p['messages']
  if key=='different_declared_TYPE2_sets' and len(examples)<8:examples.append({k:p[k] for k in ['original_nodes','messages','roles']})
 path='engine/source/implicit/ind_glob_k.F'
 with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
  m=next(x for x in tar if x.name.endswith('/'+path));b=tar.extractfile(m).read();l=b.decode().splitlines()
  assignments=[{'line':i+1,'statement':s.strip()} for i,s in enumerate(l) if re.search(r'\bNMC2\s*=',s)];assert len(assignments)==1 and assignments[0]['statement']=='NMC2=0'
  begin=next(i for i,s in enumerate(l) if 'SUBROUTINE IND_KINE_K' in s);type2=next(i for i,s in enumerate(l[begin:],begin) if 'DO J=1,NINT2' in s);rbe2=next(i for i,s in enumerate(l[begin:],begin) if 'DO N=1,NRBE2' in s)
 dump(target,{'created_utc':now(),'verified_printed_source_labels':True,'TYPE2_messages_classified':sum(counts.values()),'counts':dict(counts),'examples':examples,'source':{'path':path,'sha256':hashlib.sha256(b).hexdigest(),'NMC2_assignments':assignments,'IND_KINE_K_TYPE2_loop_line':type2+1,'RBE2_loop_line':rbe2+1,'raw_source_redistributed':False},'hypothesis':'The graph builder handles each TYPE2 group and its within-group secondary pairs before RBE2; the explicit cross-interface count NMC2 remains0 in this routine. Missing cross-interface blocks are a candidate explanation, to test on one complete physical facet with the actual two opposing TYPE2 interfaces and cohesive-offset RBE2s.','surface_membership_is_not_native_interpolation_weights':True,'cause_proven':False,'next_minimal_test':'Copy final facet216 from the real input. Compare same native geometry/materials/offsets/core with original two TYPE2 groups and a single grouped alternative. Grouping is not mechanically qualified unless native selected main facets, weights and offsets match; no whole impact or silent substitution.','known_damage_or_fit_target':False,'new_Engine_executions':0,'software_or_physics_changed':False})
 print({'TYPE2_message_classification':dict(counts),'cross_interface_count_NMC2_assignments':assignments,'cause_proven':False},flush=True)

if __name__=='__main__':main()
