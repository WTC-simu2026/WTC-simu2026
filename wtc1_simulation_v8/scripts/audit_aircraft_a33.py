"""Cached field/refinement audit; retain all A33 native failures."""
from run_aircraft_a33 import *
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import audit_aircraft_a32 as old
import subprocess,time

def preserve():
    s=inspect.getsource(old.preserve).replace('A32_preserved','A33_preserved');exec(compile(s,__file__+'::preserve','exec'),globals());globals()['preserve']()

def review():
    guard();dest=OUT/'composite_qualification_review.json';assert not dest.exists()
    s=inspect.getsource(old.review).split('    dt=[];mesh=[]')[0];s=s.replace('assert len(rows)==30','assert len(rows)==8').replace("g['geometric_Z_elements']==1","g['geometric_Z_elements'] in [1,2,4]").replace("'one_physical_thickness_cell'","'declared_physical_thickness_cells'")
    s=s.replace('def review():','def cached_fields():');ast.parse(s);exec(compile(s,__file__+'::cached_fields','exec'),globals());globals()['cached_fields']();dump(OUT/'field_audit_derivation.json',{'created_utc':now(),'source':rel(Path(old.__file__)),'source_sha256':streamsha(Path(old.__file__)),'derived_source':s,'meaning':'Reuse printing/identity/frame/card gates, change only declared case count and physical Z mesh; no old converter or native rerun'})
    rows=read(OUT/'native_case_summary.json')['cases'];assert len(rows)==8
    h=dict(np.load(OUT/'w1/FACE_BENDING_N24_Z2/histories_SI.npz'));h2=dict(np.load(OUT/'w1/FACE_BENDING_N24_Z2_HALF/histories_SI.npz'));mask=(h['time_ms']>=h2['time_ms'][0])&(h['time_ms']<=h2['time_ms'][-1]);T=h['time_ms'][mask];elastic=h['IE_J']+h['HE_J'];elastic2=h2['IE_J']+h2['HE_J'];ed=float(abs(elastic[mask]-np.interp(T,h2['time_ms'],elastic2)).max());ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));dt={'actual_dt_ratio':ratio,'elastic_energy_difference_J':ed,'checks':{'actually_shorter':ratio<.6,'energy_converges':bool(ed<.002*float(abs(elastic).max())+1e-7)}}
    mesh=[]
    for label,aa,bb in [('XY12_to24','FACE_BENDING_N12_Z2','FACE_BENDING_N24_Z2'),('Z2_to4','FACE_BENDING_N24_Z2','FACE_BENDING_N24_Z4')]:
        a=read(OUT/'w1'/aa/'review.json');b=read(OUT/'w1'/bb/'review.json');ea=a['native_IE_J']+a['native_HE_J'];eb=b['native_IE_J']+b['native_HE_J'];diff=abs(ea-eb)/eb;mesh.append({'refinement':label,'cases':[aa,bb],'native_elastic_J':[ea,eb],'difference_fraction':diff,'pass':diff<.05,'individual_gate_pass':[a['pass'],b['pass']]})
    fields=read(OUT/'native_fields_review.json');cards=read(OUT/'material_readback_review.json');frames=read(OUT/'native_frame_review.json');candidate=[r for r in rows if not r['negative_control']];checks={'candidate_original_gates':all(r['pass'] for r in candidate),'time_refinement':all(dt['checks'].values()),'spatial_refinement':all(r['pass'] for r in mesh),'native_fields':fields['pass'],'native_cards':cards['pass'],'native_frames':frames['pass']}
    failures=[{'case':r['case'],'negative_control':r['negative_control'],'checks':[k for k,v in r['checks'].items() if not v]} for r in rows if not r['pass']]
    dump(dest,{'created_utc':now(),'cases':rows,'refinement':dt,'mesh':mesh,'checks':checks,'prototype_pass':all(checks.values()),'failed_controls':failures,'candidate_cases':len(candidate),'negative_controls':1,'free_scope_pass':all(r['pass'] for r in candidate if r['case'].startswith('FREE')),'affine_scope_pass':all(r['pass'] for r in candidate if r['case'].startswith('PATCH')),'bending_scope_pass':False,'Z4_energy_gate_pass':read(OUT/'w1/FACE_BENDING_N24_Z4/review.json')['checks']['independent_elastic_energy'],'interior_relaxation_qualified':False,'native_field_samples':len(fields['samples']),'whole_insertion_ready':False,'new_whole_impact_executed':False,'old_native_solver_reruns':0,'objective1_complete':False});print({'A33_audit':checks,'native_field_samples':len(fields['samples']),'failures':failures},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','review']);globals()[p.parse_args().action]()
