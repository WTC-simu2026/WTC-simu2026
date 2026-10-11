"""Predeclare additional refinement after the 48-to-96 diagnostic failed."""
from refine_aircraft_a32_surface_reference import *

def main():
    guard(); config=ROOT/'wtc1_simulation_v8/data/aircraft_a32_surface_reference_extension.json';dest=OUT/'surface_reference_extension'
    assert not config.exists() and not dest.exists();prior=read(OUT/'surface_bending_diagnostic.json');assert not prior['reference_refinement_checks']['XY']
    dest.mkdir();c={'iteration':'AIRCRAFT-A32','declared_utc':now(),'seed':1102057,'random_draws':0,'before_new_results':True,'previous_XY_fraction':prior['XY_change_48_to_96_fraction'],'reason':'Original2% reference XY diagnostic failed. Continue declared refinement; no threshold change or native gate rewriting.',
        'cases':[{'XY':192,'Z':8,'second_order':True},{'XY':192,'Z':16,'second_order':True}], 'maximum_elements':192*192*16,'estimated_peak_memory_GB':[3,6],'expected_CPU_minutes':[1,10],
        'solver_derivation':rel(DEST/'derivation.json'),'solver_derivation_sha256':streamsha(DEST/'derivation.json'),'XY_fraction':.02,'Z_fraction':.02,'new_native_runs':0}
    dump(config,c);dump(dest/'declaration_guard.json',{'created_utc':now(),'configuration_sha256':streamsha(config),'before_new_results':True})
    s=read(DEST/'derivation.json')['derived_source'];ns=dict(independent.__dict__);ns.update(field=field,second_order=True);exec(compile(s,__file__+'::reference','exec'),ns);C=constitutive();rows=[]
    for nz in [8,16]:
        start=time.perf_counter();X,B,*_=brick_grid([192,192,nz],[-5,-5,-.25],[5,5,.25]);parts=np.ones(len(B),int);bottom=(np.flatnonzero(X[:,2]==-.25)+1).tolist();top=(np.flatnonzero(X[:,2]==.25)+1).tolist();cid=f'N192_Z{nz}_EXACT_FACE'
        try:r=ns['solve'](X,B,parts,C,C,bottom,top,0,0)
        except Exception:dump(dest/(cid+'_failure.json'),{'case':cid,'created_utc':now(),'traceback':traceback.format_exc(),'accepted':False});raise
        dump(dest/(cid+'.json'),{'created_utc':now(),'configuration_sha256':streamsha(config),'case':cid,**r});rows.append({'case':cid,'energy_J':r['energy_J'],'CG_iterations':r['CG_iterations'],'checks':r['checks'],'pass':r['pass'],'assembly_and_solve_seconds':time.perf_counter()-start});print(rows[-1],flush=True)
    e96=read(DEST/'N96_Z8_EXACT_FACE.json')['energy_J'];e8=rows[0]['energy_J'];e16=rows[1]['energy_J'];xy=abs(e96-e8)/e8;zz=abs(e8-e16)/e16
    comparisons=[]
    for branch in ['w0','w1']:
        for n in [6,12]:
            r=read(OUT/branch/f'CONSTRAINED_BENDING_N{n}/review.json');t=r['last_ms']/.1;amp=3*t*t-2*t*t*t;prediction=e16*amp**2
            comparisons.append({'branch':branch,'n':n,'original_gate_pass':r['pass'],'native_elastic_J':r['native_IE_J']+r['native_HE_J'],'independent_surface_prediction_J':prediction,'difference_fraction':(r['native_IE_J']+r['native_HE_J']-prediction)/prediction,'diagnostic_only':True})
    dump(OUT/'surface_bending_extended_diagnostic.json',{'created_utc':now(),'configuration_sha256':streamsha(config),'new_cases':rows,'XY_96_to_192_fraction':xy,'Z_8_to_16_fraction':zz,'reference_refinement_checks':{'XY':xy<.02,'Z':zz<.02},'native_comparisons':comparisons,'original_four_native_failures_unchanged':True,'reference_boundary_issue_does_not_prove_native_equivalence':True,'native_internal_operator_not_directly_observed':True,'whole_insertion_ready':False,'new_native_runs':0})
    print({'extended_reference_finished':True,'XY_fraction':xy,'Z_fraction':zz},flush=True)

if __name__=='__main__':main()
