"""Explain why changing the solver keyword cannot vary the CHECK assembly path."""
from probe_aircraft_a50 import *

def main():
 guard();target=OUT/'CHECK_effective_controls_addendum.json';assert not target.exists()
 arc=CAND/'source.tar.gz';assert streamsha(arc)==read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/source_archive.json')['sha256']
 paths=['engine/source/input/lectur.F','engine/source/implicit/imp_init.F'];rows=[]
 with tarfile.open(arc,'r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for path in paths:
   b=tar.extractfile(members[path]).read();l=b.decode().splitlines();row={'path':path,'sha256':hashlib.sha256(b).hexdigest(),'raw_source_redistributed':False}
   if path.endswith('lectur.F'):
    i=next(i for i,s in enumerate(l) if 'IF (IMP_CHK > 0)' in s);block=l[i:i+8];assert any('IPREC=5' in s for s in block) and any('ISOLV=1' in s for s in block) and any('ILINE=1' in s for s in block)
    row.update(line_start=i+1,line_end=i+8,behavior='IMP_CHK>0 forces IPREC5, ISOLV1, ILINE1 and D_TOL0, independent of the input solver keyword.')
   else:
    i=next(i for i,s in enumerate(l) if 'IF (IPREC==5)IKPAT=1' in s);row.update(line=i+1,behavior='IPREC5 selects IKPAT1. This matches the native A48/A49 pattern observation.')
   rows.append(row)
 dump(target,{'created_utc':now(),'source_pin':read(CFG)['source_pin'],'files':rows,'CHECK_does_not_run_the_requested_MUMPS_solution':True,'fixed_CHECK_controls':{'ISOLV':1,'IPREC':5,'ILINE':1,'IKPAT':1},'candidate_Engine_contains_MUMPS_but_CHECK_is_not_MUMPS_dynamic_qualification':True,'earlier_reports_or_configs_not_rewritten':True,'proposed_solver_only_CHECK_variation_not_executed':True,'reason':'The pinned code overrides the requested solver during CHECK; changing only /IMPL/SOLVER would not test the intended alternative.','no_implicit_impact_with_ignored_contacts':True,'software_changed':False})
 print({'CHECK_effective_solver_controls_verified':True,'irrelevant_solver_variation_avoided':True},flush=True)

if __name__=='__main__':main()
