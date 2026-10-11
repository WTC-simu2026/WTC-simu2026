"""Post-run independent boundary-condition diagnosis; never rewrite original gates."""
from run_aircraft_a32 import *
import linear_sandwich_reference_aircraft_a31 as independent
import inspect,ast
DIAG=ROOT/'wtc1_simulation_v8/data/aircraft_a32_surface_bending_diagnostic.json'

def field(X,second_order):
    x,y,z=X.T;u=np.zeros_like(X);u[:,0]=-.001*x*z-(.001**2*x**3/6 if second_order else 0);u[:,2]=.001*x*x/2;return u

def main():
    guard();dest=OUT/'surface_bending_diagnostic.json';assert not DIAG.exists() and not dest.exists();C=constitutive();Dfull=C[0,0]*.5**3/12;Drelaxed=(C[0,0]-C[0,2]**2/C[2,2])*.5**3/12
    c={'iteration':'AIRCRAFT-A32','declared_utc':now(),'seed':1102057,'random_draws':0,'diagnostic_declared_after_original_native_results':True,'before_new_independent_reference':True,
       'question':'All nodes of a one-thickness-cell skin are on its two external faces. Does their prescribed bending constrain interior epsilonZZ pointwise, as the original Cxx reference presumed? Compare an independent finer3D continuum with only those physical faces constrained and all interior nodes free.',
       'native_gates_unchanged':True,'geometry_mm':[10,10,.5],'XY_meshes':[6,12],'Z_meshes':[4,8,16],'full_C_MPa':C.tolist(),'boundary':'allXYZofboth z=+-.25faces prescribed; remaining nodes free','variants':['first_order_bending','actual_prescribed_second_order_correction'],
       'analytical_admissible_bubble':'uz=k*x²/2+(Czx/Czz)*k*(z²-t²/4)/2; equals original uz on external faces, permits epsilonZZ=(Czx/Czz)*k*z in the interior and sigmaZZ=0. It does not prove the actual native enhanced-strain operator.',
       'energy_reference':'For first-order cylindrical field:0.5*k²*area*(Cxx-Cxz²/Czz)*t³/12, derived solely from source tensor and geometry; independent finite continuum checks edge effects and discretization. No acceptance threshold newly substituted.',
       'analytical_full_Cxx_J':float(.5*.001**2*100*Dfull*.001),'analytical_free_transverse_J':float(.5*.001**2*100*Drelaxed*.001),'source':rel(Path(independent.__file__)),'source_sha256':streamsha(Path(independent.__file__)),'new_native_runs':0,'whole_insertion_ready':False}
    dump(DIAG,c);dump(OUT/'surface_diagnostic_declaration_guard.json',{'created_utc':now(),'sha256':streamsha(DIAG),'before_new_reference':True})
    s=inspect.getsource(independent.solve);old='u[3*(np.asarray(top)-1)+axis]=displacement';new='u[fixed]=field(np.asarray(xyz),second_order).ravel()[fixed]';assert s.count(old)==1;s=s.replace(old,new);old='.5*displacement*reaction*.001';assert s.count(old)==1;s=s.replace(old,'.5*float(u[fixed]@F[fixed])*.001');ast.parse(s);ns=dict(independent.__dict__);ns.update(field=field);exec(compile(s,__file__+'::surface_reference','exec'),ns);dump(OUT/'surface_reference_derivation.json',{'created_utc':now(),'source':rel(Path(independent.__file__)),'source_sha256':streamsha(Path(independent.__file__)),'derived_source':s,'changes':['prescribe the actual bending field on both faces instead of one scalar displacement','virtual work uses all prescribed face coordinates'],'reference_not_fitted':True})
    rows=[];rd=OUT/'surface_references';rd.mkdir()
    for n in [6,12]:
        for nz in [4,8,16]:
            X,B,m,left,right=brick_grid([n,n,nz],[-5,-5,-.25],[5,5,.25]);parts=np.ones(len(B),int);bottom=[j+1 for j,x in enumerate(X) if x[2]==-.25];top=[j+1 for j,x in enumerate(X) if x[2]==.25];cached=independent.assemble(X,B,parts,C,C)
            for second_order in [False,True]:
                ns['second_order']=second_order;r=ns['solve'](X,B,parts,C,C,bottom,top,0,0,cached);cid=f'N{n}_Z{nz}_'+('EXACT_FACE' if second_order else 'FIRST_ORDER');q=rd/(cid+'.json');dump(q,{'created_utc':now(),'configuration_sha256':streamsha(DIAG),'case':cid,**r});rows.append({'case':cid,'n':n,'nz':nz,'second_order':second_order,'energy_J':r['energy_J'],'CG_iterations':r['CG_iterations'],'seconds':r['seconds'],'checks':r['checks'],'pass':r['pass']});print({'independent_surface':cid,'energy_J':r['energy_J'],'CG':r['CG_iterations']},flush=True)
    comparison=[]
    for branch in ['w0','w1']:
        for n in [6,12]:
            r=read(OUT/branch/f'CONSTRAINED_BENDING_N{n}/review.json');T=r['last_ms']/.1;amp=3*T*T-2*T*T*T;pred=[{'reference_case':x['case'],'predicted_J':x['energy_J']*amp**2,'native_minus_reference_fraction':(r['native_IE_J']+r['native_HE_J']-x['energy_J']*amp**2)/(x['energy_J']*amp**2)} for x in rows if x['n']==n];comparison.append({'branch':branch,'n':n,'original_gate_pass':r['pass'],'native_elastic_J':r['native_IE_J']+r['native_HE_J'],'original_full_Cxx_reference_J':r['independent_reference_J'],'all_independent_surface_predictions':pred})
    dump(dest,{'created_utc':now(),'configuration_sha256':streamsha(DIAG),'analytical_full_Cxx_J':c['analytical_full_Cxx_J'],'analytical_free_transverse_J':c['analytical_free_transverse_J'],'independent_cases':rows,'native_comparison':comparison,'original_failed_gates_retained':True,'no_gate_rewritten':True,'no_native_solver_reruns':True,'native_internal_enhanced_strain_not_directly_observed':True,'physical_scope_qualification_changed':False,'whole_insertion_ready':False,'next':'A separately predeclared face-loaded bending benchmark with independently converged3D surface reference and native fields is required before qualification; no retrospective pass.'});print({'surface_diagnostic_done':True,'original_gates_unchanged':True},flush=True)

if __name__=='__main__':main()
