"""Analytic and independent-integration checks, not experimental validation."""
import copy
import math
import numpy as np
import v11e_section_model as m


def run(cfg):
    tests=[]
    def check(name,ok,evidence): tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    def close(name,a,b,tol=1e-10):
        error=float(np.max(np.abs(np.asarray(a)-np.asarray(b)))/max(1.,float(np.max(np.abs(b)))))
        check(name,error<=tol,{"relative_error":error,"tolerance":tol})
    c=m.Concrete(20e9,2e6,25e6,100.,.1)
    z=m.zero_concrete(1)
    for eps,expected,label in ((-.0002,-4e6,"compression"),(.25*c.e0,.5e6,"elastic_tension"),
                                (c.e0,c.ft,"peak"),((c.e0+c.ef)/2,c.ft/2,"softening"),(1.2*c.ef,0.,"fully_open")):
        result=m.concrete_trial(c,z,[eps])
        close("concrete_"+label,result["stress"],[expected])
        close("concrete_energy_"+label,result["work"],result["stored"]+result["dissipated"])
    peak=(c.e0+c.ef)/2
    cracked=m.concrete_trial(c,z,[peak])
    unload=m.concrete_trial(c,cracked,[peak/3])
    close("secant_unloading",unload["stress"],cracked["stress"]/3)
    close("no_dissipation_on_elastic_unloading",unload["dissipated"],cracked["dissipated"])
    closed=m.concrete_trial(c,unload,[-.0002])
    close("closure_restores_compression",closed["stress"],[-4e6])
    reloaded=m.concrete_trial(c,closed,[peak])
    close("reloading_not_healing",reloaded["damage"],cracked["damage"])
    close("closed_cycle_energy",reloaded["work"],reloaded["stored"]+reloaded["dissipated"])
    fully=m.concrete_trial(c,z,[c.ef*1.1])
    repeat=m.concrete_trial(c,m.concrete_trial(c,fully,[-.0003]),[c.ef*.3])
    close("fully_cracked_no_residual_tensile_floor",repeat["stress"],[0.])
    close("no_second_fracture_energy_after_recontact",repeat["dissipated"],[c.Gf/c.Lch])
    bad=False
    try: m.Concrete(1e9,10e6,20e6,1.,1.)
    except ValueError: bad=True
    check("invalid_crack_band_rejected",bad,"epsf must exceed ft/E")
    for length in (.05,.1,.2):
        mat=m.Concrete(c.E,c.ft,c.fc,c.Gf,length)
        # Separate manual piecewise curve, including the pre-peak triangle.
        strains=np.r_[np.linspace(0,mat.e0,101),np.linspace(mat.e0,mat.ef,301)[1:]]
        stresses=np.where(strains<=mat.e0,mat.E*strains,mat.ft*(mat.ef-strains)/(mat.ef-mat.e0))
        integral=float(np.trapezoid(stresses,strains))*length
        close(f"crack_band_Gf_integral_L{length}",integral,mat.Gf)
        final=m.concrete_trial(mat,m.zero_concrete(1),[mat.ef])
        close(f"crack_band_dissipation_L{length}",final["dissipated"]*length,[mat.Gf])
        opening=length*(strains-stresses/mat.E)
        mask=strains>=mat.e0
        close(f"stress_opening_linear_L{length}",stresses[mask],mat.ft*(1-opening[mask]/(2*mat.Gf/mat.ft)))
    # Direct stress integration along a cyclic material path, independent of the work primitive.
    old=m.zero_concrete(1); work=0.;min_d=0.
    for a,b in zip([0,peak,0,-.0002,0,1.2*c.ef,0],[peak,0,-.0002,0,1.2*c.ef,0,-.0001],strict=True):
        points=sorted(set([a,b]+[float(v) for v in (0,c.e0,c.ef,old["r"][0]) if min(a,b)<v<max(a,b)]))
        if b<a: points.reverse()
        part=0.
        for lo,hi in zip(points[:-1],points[1:],strict=True):
            e=(lo+hi)/2
            r=max(old["r"][0],e,0.)
            env=c.E*r if r<=c.e0 else max(0.,c.ft*(c.ef-r)/(c.ef-c.e0))
            sigma=c.E*e if e<0 or r==0 else env*e/r
            part+=sigma*(hi-lo)
        nxt=m.concrete_trial(c,old,[b]);work+=part
        min_d=min(min_d,float(nxt["dissipated"][0]-old["dissipated"][0]))
        old=nxt
    close("concrete_cyclic_independent_stress_integral",old["work"],[work])
    check("concrete_dissipation_monotone",min_d>=-1e-10,min_d)
    steel=m.Steel(200e9,400e6);ey=steel.fy/steel.E
    virgin=m.zero_steel(1)
    s1=m.steel_trial(steel,virgin,[3*ey])
    close("steel_yield_plateau",s1["stress"],[steel.fy])
    close("steel_return_mapping",s1["plastic"],[2*ey])
    close("steel_plastic_dissipation",s1["dissipated"],[steel.fy*2*ey])
    s2=m.steel_trial(steel,s1,[2*ey])
    close("steel_residual_strain_at_zero_stress",s2["stress"],[0.])
    s3=m.steel_trial(steel,s2,[-2*ey])
    close("steel_reverse_yield",s3["stress"],[-steel.fy])
    close("steel_reverse_energy",s3["work"],s3["stored"]+s3["dissipated"])
    old=virgin
    verts=[0,3*ey,-3*ey,3*ey]
    dense_work=0.
    for a,b in zip(verts[:-1],verts[1:],strict=True):
        # Include exact yield crossing; stress is then linear or constant.
        yy=float(old["plastic"][0]+math.copysign(ey,b-a))
        points=sorted(set([a,b]+([yy] if min(a,b)<yy<max(a,b) else [])),reverse=b<a)
        for lo,hi in zip(points[:-1],points[1:],strict=True):
            sl=np.clip(steel.E*(lo-old["plastic"][0]),-steel.fy,steel.fy)
            sh=np.clip(steel.E*(hi-old["plastic"][0]),-steel.fy,steel.fy)
            dense_work+=(sl+sh)*(hi-lo)/2
        old=m.steel_trial(steel,old,[b])
    close("steel_cycle_independent_polygon_integral",old["work"],[dense_work])
    # Elastic section formulas include the midpoint quadrature inertia exactly.
    for layout in ("symmetric","top","bottom"):
        section=m.Section(cfg,{"rho_total":.002,"layout":layout})
        Ac=sum(section.Ac);I=Ac*section.h**2/12*(1-1/section.n**2)
        ea=section.concrete.E*Ac+section.steel.E*sum(section.As)
        eay=section.steel.E*float(section.As@section.ys)
        eiy=section.concrete.E*I+section.steel.E*float(section.As@section.ys**2)
        expected=np.array([[ea,-eay],[-eay,eiy]])
        q=np.array([1e-6,1e-5]);r=section.trial(section.zero(),q)
        close("elastic_section_matrix_"+layout,r["K"],expected)
        close("elastic_section_resultants_"+layout,[r["N"],r["M"]],expected@q)
        rr,info=section.solve_axial(section.zero(),1e-5,123.)
        close("elastic_N_control_"+layout,rr["q"][0],(123+eay*1e-5)/ea,tol=1e-14)
        close("steel_area_not_added_to_gross_concrete_"+layout,Ac+sum(section.As),section.width*section.h)
    section=m.Section(cfg,{"rho_total":.002,"layout":"symmetric"})
    committed=section.zero();backup=copy.deepcopy(committed)
    _=section.trial(committed,(.0001,.03));_=section.solve_axial(committed,.04)
    unchanged=all(np.array_equal(committed[k][f],backup[k][f]) for k in ("c","s") for f in committed[k])
    unchanged=unchanged and np.array_equal(committed["q"],backup["q"])
    check("trial_and_root_search_do_not_commit_state",unchanged,"All original history arrays unchanged")
    # Independent bracketed bisection, not the production breakpoint sweep.
    state=section.zero();errors=[]
    for k in (.002,.011,.037,.01,-.018,-.042,0.):
        r,info=section.solve_axial(state,k,0.)
        lo=-.02;hi=.02
        def direct_n(e0):
            eps=e0-section.yc*k;hist=np.maximum(state["c"]["r"],np.maximum(eps,0.))
            cc=section.concrete
            env=np.where(hist<=cc.e0,cc.E*hist,np.maximum(0.,cc.ft*(cc.ef-hist)/(cc.ef-cc.e0)))
            kk=np.divide(env,hist,out=np.full_like(hist,cc.E),where=hist>0)
            cs=np.where(eps<0,cc.E*eps,kk*eps)
            ss=np.clip(section.steel.E*(e0-section.ys*k-state["s"]["plastic"]),-section.steel.fy,section.steel.fy)
            return float(section.Ac@cs+section.As@ss)
        for _ in range(85):
            mid=(lo+hi)/2
            if direct_n(mid)>0: hi=mid
            else: lo=mid
        errors.append(abs(r["q"][0]-(lo+hi)/2))
        state=r
    check("piecewise_axial_roots_against_independent_bisection",max(errors)<1e-11,max(errors))
    # Fully precracked rectangular compression zone, one elastic tensile layer.
    bottom=m.Section(cfg,{"rho_total":.002,"layout":"bottom"},640)
    damaged=bottom.zero();damaged["c"]["r"][:]=bottom.concrete.ef
    damaged["c"]["work"][:]=bottom.concrete.Gf/bottom.concrete.Lch
    k=.0001;d=bottom.h/2-bottom.ys[0];b=bottom.width*(1-.002)
    esa=bottom.steel.E*sum(bottom.As);ecb=bottom.concrete.E*b
    depth=(-esa+math.sqrt(esa**2+2*ecb*esa*d))/ecb
    expected_m=esa*k*(d-depth)*(d-depth/3)
    r,_=bottom.solve_axial(damaged,k)
    close("precracked_RC_analytic_neutral_axis",bottom.h/2-r["q"][0]/k,depth,tol=2e-6)
    close("precracked_RC_analytic_moment",r["M"],expected_m,tol=2e-5)
    # Consistent tangent away from switching points, including negative concrete slope.
    old=section.trial(section.zero(),(.0002,.009))
    q=np.array([.00025,.017]);r=section.trial(old,q);numeric=np.zeros((2,2))
    for j,h in enumerate((1e-9,1e-8)):
        dq=np.zeros(2);dq[j]=h
        plus=section.trial(old,q+dq);minus=section.trial(old,q-dq)
        numeric[:,j]=(np.array([plus["N"],plus["M"]])-np.array([minus["N"],minus["M"]]))/(2*h)
    close("consistent_tangent_finite_difference",r["K"],numeric,tol=1e-6)
    close("section_tangent_symmetry",r["K"],r["K"].T)
    # External work of a prescribed straight segment, integrated in strain space.
    q1=np.array([.0004,.044]);dq=q1-old["q"];cuts=[0.,1.]
    for yy,rr in zip(section.yc,old["c"]["r"],strict=True):
        a=old["q"][0]-yy*old["q"][1];change=dq[0]-yy*dq[1]
        if change:
            cuts.extend((v-a)/change for v in (0.,section.concrete.e0,rr,section.concrete.ef) if 0<(v-a)/change<1)
    for yy,pp in zip(section.ys,old["s"]["plastic"],strict=True):
        a=old["q"][0]-yy*old["q"][1];change=dq[0]-yy*dq[1]
        if change:
            cuts.extend((v-a)/change for v in (pp-section.steel.fy/section.steel.E,pp+section.steel.fy/section.steel.E) if 0<(v-a)/change<1)
    cuts=sorted(set(cuts));work=0.
    for a,b in zip(cuts[:-1],cuts[1:],strict=True):
        at=section.trial(old,old["q"]+(a+b)/2*dq)
        work+=(at["N"]*dq[0]+at["M"]*dq[1])*(b-a)
    final=section.trial(old,q1)
    close("section_work_independent_generalized_force_integral",final["work"]-old["work"],work)
    # An axial tensile load above the reinforcement plateau has no root, not a collapse verdict.
    _,info=section.solve_axial(section.zero(),0.,2*section.steel.fy*sum(section.As)+2*section.concrete.ft*sum(section.Ac))
    check("no_axial_root_reported_not_stabilized",info["status"]=="NO_POSITIVE_AXIAL_ROOT",info)
    # Artificial low limits test domain detection without modifying production cases.
    low=copy.deepcopy(cfg);low["paths"]["monotonic_end_curvature_per_m"]=.005;low["concrete"]["fc20_ksi"]=.05
    lowcase={"id":"DOMAIN_TEST","rho_total":.002,"layout":"symmetric","kind":"monotonic"}
    trace=m.trace(low,lowcase)
    check("compression_domain_stops_at_boundary",trace["summary"]["terminal"]=="CONCRETE_COMPRESSION_DOMAIN" and abs(trace["summary"]["last_domain_ratio"]-1)<1e-8,trace["summary"])
    low2=copy.deepcopy(cfg);low2["reinforcement"]["absolute_mechanical_strain_domain_limit"]=.0001
    trace2=m.trace(low2,lowcase)
    check("steel_strain_domain_stops_at_boundary",trace2["summary"]["terminal"]=="STEEL_STRAIN_DOMAIN" and abs(trace2["summary"]["last_domain_ratio"]-1)<1e-8,trace2["summary"])
    coarse=m.Section(cfg,{"rho_total":0.,"layout":"symmetric"},2)
    rr=coarse.trial(coarse.zero(),(0.,.01))
    close("compression_screen_at_outer_face_not_midpoint",rr["compression_face_stress_Pa"],coarse.concrete.E*coarse.h*.01/2)
    close("face_screen_recovers_missing_midpoint_extreme",rr["compression_ratio"],2*rr["sampled_compression_ratio"])
    badtemp=copy.deepcopy(cfg);badtemp["section"]["temperature_c"]=200.
    rejected=False
    try: m.Section(badtemp,{"rho_total":.002,"layout":"symmetric"})
    except ValueError: rejected=True
    check("unverified_thermal_history_rejected",rejected,"Only20C supported by V11E")
    rejected=False
    try: m.Section(cfg,{"rho_total":.002,"layout":"symmetric"},0)
    except ValueError: rejected=True
    check("zero_fiber_request_rejected_not_silently_replaced",rejected,"Explicit zero is not the default mesh")
    return tests
