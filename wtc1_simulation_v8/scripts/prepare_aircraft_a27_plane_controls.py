"""Declare plane-loading and quadrature controls before new native executions.

Material fields, density, volume, and all acceptance thresholds are unchanged.
The original transverse imposed displacement is kept in w1, with failed gates.
"""
from run_aircraft_a27 import *

def main():
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_plane_controls.json',h)
    assert len(read(OUT/'native_case_summary_w1.json')['cases'])==9
    base=Path(__file__).with_name('test_aircraft_a27_regular_layers.py')
    source=base.read_text(encoding='utf-8')
    docs=[]
    for name,url in [
        ('tsai_wu','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tsai_wu_formulation_starter_r.htm'),
        ('law25_theory','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/law25_composite_material_r.htm')]:
        q=OUT/'sources'/(name+'.html');assert not q.exists();q.write_bytes(urllib.request.urlopen(url,timeout=45).read());docs.append({'url':url,'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size,'redistribution':'exclude_third_party'})
    dump(OUT/'plane_control_sources.json',{'created_utc':now(),'files':docs})
    for rev,layers in [('w2',3),('w3',9)]:
        cfg=ROOT/f'wtc1_simulation_v8/data/aircraft_a27_plane_{rev}.json';target=base.with_name(f'test_aircraft_a27_plane_{rev}.py');assert not cfg.exists() and not target.exists()
        c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a27_regular_layers.json')
        c.update(revision=rev,declared_utc=now(),parent_configuration_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a27_regular_layers.json'),thickness_layers=layers,
          purpose='Isolate the imposed transverse strain, then refine homogeneous through-thickness quadrature without changing material parameters, physical layers, mass or target response.',
          constitutive_reference={'status':'explicit thick-shell block constitutive hypothesis, not inferred historical material',
            'normal_stiffness_MPa':[[22000/(1-.25**2),.25*22000/(1-.25**2),0],[.25*22000/(1-.25**2),22000/(1-.25**2),0],[0,0,10000]],
            'shear_moduli_MPa':[4000,4000,4000],
            'qualification_limit':'LAW25 theory page shows transverse Poisson coupling for 3D law; actual inherited TYPE22 w1 stress is near sigma_x22, sigma_y0, sigma_z-2.5 MPa under imposed epsilon[.001,-.00025,-.00025]. Candidate tests explicitly separate plane response from transverse strain; general 3D material equivalence remains unqualified.'},
          loading={'membrane':'ux=.001*x, uy=-.00025*y, uz=0; no imposed transverse contraction',
            'bending':'ux=-k*x*z-k²*x³/6, uy=0, uz=k*x²/2, k=.001/mm; transverse strain term removed. Expected plane bending D11 from unchanged E11, E22 and nu12. Small geometric and shear discretization remain explicit.'},
          quadrature={'layers':layers,'Ipos':0,'Inpts':200+10*layers+2,'relative_thickness':1/layers,'automatic_centers_expected':[((i+.5)/layers-.5) for i in range(layers)],
            'midpoint_second_moment_fraction':1-1/layers**2,'continuous_bending_quadrature_deficit_fraction':1/layers**2,
            'selection':'3 retained as diagnostic;9 chosen before new runs since uniform midpoint second-moment error1/N² is below previously fixed2% elastic threshold. No stiffness or strength fitting; homogeneous physical continuum unchanged.'},
          whole_insertion_ready=False,objective1_complete=False)
        if rev=='w2':c['cases']=['MEMBRANE_N6','MEMBRANE_N12','BENDING_N6','BENDING_N12']
        dump(cfg,c);dump(OUT/f'plane_{rev}_guard.json',{'created_utc':now(),'sha256':streamsha(cfg),'before_new_native_solvers':True})
        a=[];s=source
        old_imposed=s[s.index('def imposed('):s.index('\ndef review(')]
        new_imposed="""def imposed(L,X,cid):
    # Explicit plane displacement control; no alteration of constitutive fields.
    s=inspect.getsource(metal.imposed).replace('-.00033*y','-.00025*y').replace('-.00033*z','0*z').replace('.33/(1-.33)*.001*z*z/2','0*z')
    namespace=dict(globals());exec(compile(s,__file__+'::imposed','exec'),namespace);return namespace['imposed'](L,X,cid)
"""
        replacements=[('aircraft_a27_regular_layers.json',f'aircraft_a27_plane_{rev}.json'),("OUT/'regular_layers_guard.json'",f"OUT/'plane_{rev}_guard.json'"),("OUT/'w1'",f"OUT/'{rev}'"),("OUT/'native_case_summary_w1.json'",f"OUT/'native_case_summary_{rev}.json'"),("OUT/'runner_w1_derivation.json'",f"OUT/'runner_{rev}_derivation.json'"),("OUT/'review_w1_derivation.json'",f"OUT/'review_{rev}_derivation.json'"),(old_imposed,new_imposed),('ii(10,232,0)',f'ii(10,{200+10*layers+2},0)'),('[(1/3,0)]*3',f'[(1/{layers},0)]*{layers}')]
        for old,new in replacements:
            count=s.count(old);assert count>0,old;s=s.replace(old,new);a.append({'old':old,'new':new,'count':count})
        ast.parse(s);target.write_text(s,encoding='utf-8',newline='\n');dump(OUT/f'plane_{rev}_derivation.json',{'created_utc':now(),'source':rel(base),'source_sha256':streamsha(base),'target':rel(target),'target_sha256':streamsha(target),'changes':a,'material_and_thresholds_unchanged':True,'old_native_solver_reruns':0})
    print({'A27_plane_controls_declared':True,'w2_native_cases':4,'w3_native_cases':9,'CPU_minutes':[4,10]},flush=True)

if __name__=='__main__':main()
