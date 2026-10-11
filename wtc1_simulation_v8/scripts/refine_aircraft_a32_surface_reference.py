"""Separately declared precision/XY refinement; keep original failed gates."""
from run_aircraft_a32 import *
import linear_sandwich_reference_aircraft_a31 as independent
from diagnose_aircraft_a32_surface_bending import field
import inspect, ast, time

CONFIG=ROOT/'wtc1_simulation_v8/data/aircraft_a32_surface_reference_refinement.json'
DEST=OUT/'surface_reference_refinement'

def main():
    guard(); assert not CONFIG.exists() and not DEST.exists()
    DEST.mkdir()
    original=ROOT/'wtc1_simulation_v8/scripts/diagnose_aircraft_a32_surface_bending.py'
    shutil.copy2(original,DEST/'original_diagnostic.py')
    cached=sorted((OUT/'surface_references').glob('*.json')); assert len(cached)==5
    pins=[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in cached]
    cases=[(6,16,True),(12,8,False),(12,8,True),(24,8,False),(24,8,True),(48,8,False),(48,8,True),(96,8,False),(96,8,True),(96,4,True)]
    c={'iteration':'AIRCRAFT-A32','declared_utc':now(),'seed':1102057,'random_draws':0,
       'diagnostic_after_original_results':True,'before_new_reference':True,'original_native_gates_unchanged':True,
       'original_reference_failure':{'case':'N6_Z16_EXACT_FACE','gate':'virtual_work','evidence':rel(ROOT/'harness/handoffs/WTC1_AIRCRAFT_A32_LIVE_HANDOFF.md'),'accepted_output_exists':False,'original_traceback_file_available':False},
       'cached_accepted_references':pins,'cases':[{'XY':n,'Z':z,'second_order':v} for n,z,v in cases],
       'CG_relative':1e-13,'CG_absolute_N':1e-14,'CG_max_iterations':12000,'all_original_verification_thresholds_retained':True,
       'geometry_mm':[10,10,.5],'boundary':'Both outer z faces prescribe XYZ field; all interior nodes free',
       'reference':'Conventional8-node2x2x2Gauss source3D stiffness; no native assumed strain or measured response',
       'XY_convergence_diagnostic_fraction':.02,'Z_convergence_diagnostic_fraction':.02,
       'reason':'Coarse standard continuum interpolation of quadratic face uz produces transverse shear; XY and Z refinements are distinct. Refine XY rather than fitting a modulus or relaxing native gates.',
       'maximum_mesh_elements':96*96*8,'expected_CPU_minutes':[1,10],'new_native_runs':0,'whole_insertion_ready':False}
    dump(CONFIG,c);dump(DEST/'declaration_guard.json',{'created_utc':now(),'configuration_sha256':streamsha(CONFIG),'before_new_results':True})
    s=inspect.getsource(independent.solve)
    changes={'u[3*(np.asarray(top)-1)+axis]=displacement':'u[fixed]=field(np.asarray(xyz),second_order).ravel()[fixed]',
             '.5*displacement*reaction*.001':'.5*float(u[fixed]@F[fixed])*.001',
             '1e-10*scale+1e-11':'1e-13*scale+1e-14'}
    for a,b in changes.items(): assert s.count(a)==1; s=s.replace(a,b)
    ast.parse(s);ns=dict(independent.__dict__);ns['field']=field
    exec(compile(s,__file__+'::reference','exec'),ns)
    dump(DEST/'derivation.json',{'source':rel(Path(independent.__file__)),'source_sha256':streamsha(Path(independent.__file__)),'derived_source':s,'literal_changes':changes,'native_operator_used':False})
    C=constitutive();rows=[];assembled=None;key=None
    for n,z,v in cases:
        cid=f'N{n}_Z{z}_'+('EXACT_FACE' if v else 'FIRST_ORDER');start=time.perf_counter()
        if key!=(n,z):
            assembled=None
            X,B,*_=brick_grid([n,n,z],[-5,-5,-.25],[5,5,.25]);parts=np.ones(len(B),int)
            bottom=(np.flatnonzero(X[:,2]==-.25)+1).tolist();top=(np.flatnonzero(X[:,2]==.25)+1).tolist()
            assembled=independent.assemble(X,B,parts,C,C);key=(n,z)
        ns['second_order']=v
        try:
            r=ns['solve'](X,B,parts,C,C,bottom,top,0,0,assembled)
            dump(DEST/(cid+'.json'),{'created_utc':now(),'configuration_sha256':streamsha(CONFIG),'case':cid,**r})
            row={k:r[k] for k in ['energy_J','CG_iterations','seconds','checks','pass']};row.update(case=cid,n=n,nz=z,second_order=v,assembly_and_solve_seconds=time.perf_counter()-start);rows.append(row)
            print({'independent_reference':cid,'energy_J':r['energy_J'],'CG':r['CG_iterations'],'seconds':row['assembly_and_solve_seconds']},flush=True)
        except Exception:
            dump(DEST/(cid+'_failure.json'),{'created_utc':now(),'configuration_sha256':streamsha(CONFIG),'case':cid,'traceback':traceback.format_exc(),'accepted':False});raise
    E={r['case']:r['energy_J'] for r in rows}
    xy=abs(E['N96_Z8_EXACT_FACE']-E['N48_Z8_EXACT_FACE'])/E['N96_Z8_EXACT_FACE']
    zz=abs(E['N96_Z8_EXACT_FACE']-E['N96_Z4_EXACT_FACE'])/E['N96_Z8_EXACT_FACE']
    comparisons=[]
    for branch in ['w0','w1']:
        for n in [6,12]:
            r=read(OUT/branch/f'CONSTRAINED_BENDING_N{n}/review.json');t=r['last_ms']/.1;s=3*t*t-2*t*t*t;pred=E['N96_Z8_EXACT_FACE']*s*s
            comparisons.append({'branch':branch,'n':n,'original_pass':r['pass'],'native_J':r['native_IE_J']+r['native_HE_J'],'converged_reference_prediction_J':pred,'difference_fraction':(r['native_IE_J']+r['native_HE_J']-pred)/pred,'diagnostic_only':True})
    for p in pins: assert streamsha(ROOT/p['path'])==p['sha256']
    dump(OUT/'surface_bending_diagnostic.json',{'created_utc':now(),'configuration_sha256':streamsha(CONFIG),'cases':rows,'cached_five_references_unchanged':True,'XY_change_48_to_96_fraction':xy,'Z_change_4_to_8_fraction':zz,'reference_refinement_checks':{'XY':xy<.02,'Z':zz<.02},'analytical_first_order_free_transverse_J':read(ROOT/'wtc1_simulation_v8/data/aircraft_a32_surface_bending_diagnostic.json')['analytical_free_transverse_J'],'native_comparisons':comparisons,'original_failed_gates_retained':True,'native_enhanced_strain_operator_not_directly_observed':True,'qualification_changed':False,'new_native_runs':0,'whole_insertion_ready':False})
    print({'A32_diagnostic_finished':True,'XY_fraction':xy,'Z_fraction':zz,'original_native_gates_unchanged':True},flush=True)

if __name__=='__main__':main()
