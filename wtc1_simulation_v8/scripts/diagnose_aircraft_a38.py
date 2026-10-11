"""Read restart header without mutation and acquire bounded startup diagnostics."""
import probe_aircraft_a38 as experiment
from probe_aircraft_a38 import *
from probe_aircraft_a37 import histories,vtk
import re

EXTRA=[{'name':'FREE_TRACE_I','scope':'FREE','mode':'I','dt_ms':.001,'variant':'TRACE','end_ms':.004},{'name':'FREE_LINEAR_I','scope':'FREE','mode':'I','dt_ms':.001,'variant':'LINEAR','end_ms':.1}]

def declare():
 guard();assert read(OUT/'startup_review.json')['passing_variants']==[];p=OUT/'startup_extension_predeclaration.json';assert not p.exists()
 dump(p,{'created_utc':now(),'seed':1102063,'random_draws':0,'parent_configuration_sha256':streamsha(CFG),'cases':EXTRA,'purpose':'Three separate options failed. Record iteration diagnostics during only four initial steps; separately determine whether failure depends on nonlinear startup driver, with unforced linear-exact translation.','TRACE':'Same Newmark/MUMPS dynamics, short .004ms; /IMPL/PRINT/NONLIN/1 and initial stiffness matrix output; output-only variation','LINEAR':'Replace /IMPL/NONLIN/1 and its tolerance row with /IMPL/LINEAR; /IMPL/DYNA/2 retained. No whole/contact substitution. Native may use single full-time step; report actual time sampling.','references':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_print_nonlin_engine_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_linear_engine_r.htm'],'before_new_native':True,'per_process_cap_s':180,'no_build':True})

def headers():
 guard();rows=[]
 files=[f for c in CASES for f in (OUT/c['name']/'phase1').glob('*.rst')]
 files+=list((PARENT_OUT/'FREE_EI/phase1').glob('*.rst'))+list((PARENT_OUT/'FREE_EI/phase2').glob('*.rst'))
 for p in files:
  b=p.read_bytes();prefix_end=next(i for i,v in enumerate(b) if v==0);title_offset=prefix_end;title=np.frombuffer(b,dtype='>i4',count=100,offset=title_offset);assert all(0<=x<=127 for x in title);offset=title_offset+400;L=int(np.frombuffer(b,dtype='>i4',count=1,offset=offset)[0]);assert 1<=L<=100;head=np.frombuffer(b,dtype='>i4',count=L,offset=offset+4);assert int(head[1])==101 and int(head[13])<=4000;v=np.frombuffer(b,dtype='>i4',count=int(head[13]),offset=offset+4+4*L)
  row={'path':rel(p),'sha256':streamsha(p),'prefix':b[:prefix_end].decode('ascii'),'title':''.join(chr(x) for x in title).rstrip(),'LHEADER':L,'header':head.tolist(),'LVARINT':int(head[13]),'NUMNOD_TABVINT239':int(v[238]),'NINVEL_TABVINT250':int(v[249]),'read_only':True};assert row['NUMNOD_TABVINT239']==27 and row['NINVEL_TABVINT250']==27;rows.append(row)
 source_files=['engine/source/output/restart/rdresa.F','engine/source/output/restart/rdcomm.F','common_source/tools/input_output/write_routines.c','common_source/modules/names_and_titles_mod.F','engine/source/output/restart/wrrest.F']
 dump(OUT/'restart_header_review.json',{'created_utc':now(),'pass':True,'files':rows,'reader_rule':'Raw restart prefix followed by100big-endian int title chars, LHEADER, TABHEAD, then LVARINT big-endian ints. Verified primary C READ_I_C/Fortran RDRESA/RDCOMI; no binary changes.','finding':'Initial-velocity count27 is present in each fresh Starter and Engine state inspected. Loss of NINVEL alone does not explain startup. This does not prove full binary compatibility.','source_files':[{'path':rel(build.CAND/'source'/f),'sha256':streamsha(build.CAND/'source'/f),'url':f'https://github.com/gabrielrussell/OpenRadioss/blob/{build.PIN}/{f}'} for f in source_files]})
 print({'restart_headers_read':len(rows),'NINVEL_preserved':True},flush=True)

def extra_cards(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode!='I':return s
 if VARIANT=='TRACE':
  s=s.replace(ff(end)+'\n/TFILE',ff(.004)+'\n/TFILE');s='/IMPL/PRINT/NONLIN/1\n/IMPL/PRINT/STIFFNESS\n1e-30 1 1\n'+s
 elif VARIANT=='LINEAR':
  token='/IMPL/NONLIN/1\n0 123 1e-6 1e-6 1e-6';assert token in s;s=s.replace(token,'/IMPL/LINEAR')
 else:raise ValueError(VARIANT)
 return s

def run():
 global VARIANT
 guard();assert read(OUT/'startup_extension_predeclaration.json')['before_new_native'];experiment.install_runner();native37.engine_cards=extra_cards;rows=[]
 for c in EXTRA:
  VARIANT=c['variant'];native37.start_case(c);native37.audit_case(c);rows.append(read(OUT/c['name']/'review.json'))
 dump(OUT/'startup_extension_review.json',{'created_utc':now(),'cases':rows,'whole_insertion_ready':False})

def endpoints():
 guard();rows=[]
 for c in CASES+EXTRA:
  d=OUT/c['name'];g=read(d/'generation.json');m=np.asarray(g['nodal_masses_g']);X=np.asarray(g['nodes_mm']);V0=np.asarray(g['initial_velocity_mm_ms']);files=sorted((d/'phase1').glob('*.vtk'));q=vtk(files[-1].read_text());order=np.argsort(q['NODE_ID']);V=q['Velocity'].reshape(-1,3)[order];U=q['Displacement'].reshape(-1,3)[order];K=float(.5*np.sum(m[:,None]*V**2)*.001);dv=float(abs(V-V0).max());du=float(abs(U-q['time']*V0).max());expected_end=c.get('end_ms',.1);ck={'end_time_reached':abs(q['time']-expected_end)<1e-5,'endpoint_velocity':dv<2e-4,'endpoint_displacement':du<2e-5,'endpoint_physical_KE':abs(K-g['kinetic_energy_J'])<.02*g['kinetic_energy_J']+1e-7};h=histories(next((d/'phase1').glob('*.csv')));row={'case':c['name'],'vtk':rel(files[-1]),'time_ms':q['time'],'velocity_first_node':V[0].tolist(),'KE_from_physical_nodes_J':K,'expected_initial_KE_J':g['kinetic_energy_J'],'maximum_velocity_error_mm_ms':dv,'maximum_displacement_error_mm':du,'native_history_samples':len(h['time']),'history_last_ms':float(h['time'][-1]),'checks':ck,'pass':all(ck.values())};rows.append(row)
 dump(OUT/'endpoint_review.json',{'created_utc':now(),'cases':rows,'pass':all(r['pass'] for r in rows),'independent_free_oracle':True});print({'endpoint_passes':sum(r['pass'] for r in rows),'cases':len(rows)},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','headers','run','endpoints']);globals()[p.parse_args().action]()
