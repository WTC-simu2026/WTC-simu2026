"""V11E: trial/commit 1D materials and isolated N-M fiber section, SI units.

No FE panel, fire, crushing/postbuckling, gravity or global energy credit.
Energy densities: Pa = J/m3. Section energies: J/m, not J or N*m moments.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

IN = 0.0254
KSI = 4448.2216152605 / IN**2


@dataclass(frozen=True)
class Concrete:
    E: float
    ft: float
    fc: float
    Gf: float
    Lch: float

    def __post_init__(self):
        if not all(math.isfinite(v) and v > 0 for v in (self.E,self.ft,self.fc,self.Gf,self.Lch)):
            raise ValueError("Concrete parameters must be positive finite SI numbers")
        if self.ef <= self.e0:
            raise ValueError("Crack band too long: epsf must exceed elastic peak strain")

    @property
    def e0(self): return self.ft / self.E

    @property
    def ef(self): return 2*self.Gf/(self.ft*self.Lch)

    @property
    def soft(self): return -self.ft/(self.ef-self.e0)

    def envelope(self, r):
        r = np.maximum(r,0.)
        return np.where(r <= self.e0,self.E*r,np.maximum(0.,self.ft+self.soft*(r-self.e0)))

    def secant(self, r):
        raw=np.divide(self.envelope(r),r,out=np.full_like(np.asarray(r,dtype=float),self.E),where=np.asarray(r)>0)
        return np.where(np.asarray(r)<=self.e0,self.E,raw)

    def envelope_work(self,r):
        z = np.clip(r,self.e0,self.ef)-self.e0
        return np.where(np.asarray(r)<=self.e0,.5*self.E*np.asarray(r)**2,
                        .5*self.ft*self.e0+self.ft*z+.5*self.soft*z*z)

    def dissipation(self,r):
        return .5*self.ft*self.ef/(self.ef-self.e0)*np.clip(np.asarray(r)-self.e0,0.,self.ef-self.e0)

    def primitive(self,eps,r):
        """Integral of the actual stress path from zero with OLD history r.

        Includes secant branch up to r and envelope above r. This computes
        work independently of the stored-energy/dissipation identity.
        """
        positive = np.maximum(eps,0.)
        k = self.secant(r)
        return np.where(np.asarray(eps)<0,.5*self.E*np.asarray(eps)**2,
                        .5*k*np.minimum(positive,r)**2 + self.envelope_work(np.maximum(positive,r))-self.envelope_work(r))


@dataclass(frozen=True)
class Steel:
    E: float
    fy: float

    def __post_init__(self):
        if not all(math.isfinite(v) and v>0 for v in (self.E,self.fy)):
            raise ValueError("Steel parameters must be positive finite SI numbers")


def concrete_trial(mat,old,eps):
    eps=np.asarray(eps,dtype=float)
    r=np.maximum(old["r"],np.maximum(eps,0.))
    k=mat.secant(r)
    stress=np.where(eps<0,mat.E*eps,k*eps)
    active=(eps>old["r"]) & (eps>mat.e0) & (eps<mat.ef)
    tangent=np.where(eps<0,mat.E,np.where(active,mat.soft,k))
    work=old["work"]+mat.primitive(eps,old["r"])-mat.primitive(old["eps"],old["r"])
    return {"eps":eps.copy(),"r":r,"stress":stress,"tangent":tangent,
            "stored":.5*stress*eps,"dissipated":mat.dissipation(r),"work":work,
            "damage":1.-k/mat.E}


def steel_trial(mat,old,eps):
    eps=np.asarray(eps,dtype=float)
    trial=mat.E*(eps-old["plastic"])
    stress=np.clip(trial,-mat.fy,mat.fy)
    yielded=np.abs(trial)>mat.fy
    plastic=np.where(yielded,eps-stress/mat.E,old["plastic"])
    dp=plastic-old["plastic"]
    sy=np.where(trial>=0,mat.fy,-mat.fy)
    yield_eps=old["plastic"]+sy/mat.E
    old_stress=mat.E*(old["eps"]-old["plastic"])
    dw=np.where(yielded,.5*(old_stress+sy)*(yield_eps-old["eps"])+sy*(eps-yield_eps),
                .5*(old_stress+stress)*(eps-old["eps"]))
    return {"eps":eps.copy(),"plastic":plastic,"stress":stress,"tangent":np.where(yielded,0.,mat.E),
            "accumulated_plastic":old["accumulated_plastic"]+np.abs(dp),
            "stored":.5*stress**2/mat.E,"dissipated":old["dissipated"]+mat.fy*np.abs(dp),"work":old["work"]+dw}


def zero_concrete(n):
    return {k:np.zeros(n) for k in ("eps","r","work","stress","stored","dissipated","damage")}


def zero_steel(n):
    return {k:np.zeros(n) for k in ("eps","plastic","accumulated_plastic","work","stress","stored","dissipated")}


class Section:
    def __init__(self,cfg,case,nfibers=None):
        self.case=dict(case)
        g=cfg["section"]; c=cfg["concrete"]; s=cfg["reinforcement"]
        self.width=g["width_in"]*IN; self.h=g["equivalent_thickness_in"]*IN
        count=g["reference_concrete_fibers"] if nfibers is None else nfibers
        self.n=int(count)
        rho=case["rho_total"]
        cover=s["layer_center_distance_from_face_mm"]/1000.
        if self.n!=count or self.n<2 or self.width<=0 or not 0<=rho<1 or not 0<cover<self.h/2:
            raise ValueError("Invalid section discretization, steel ratio or layer location")
        if g["temperature_c"]!=20.:
            raise ValueError("V11E is isothermal at 20 C, no unverified temperature history")
        self.yc=(np.arange(self.n)+.5)*self.h/self.n-self.h/2
        self.Ac=np.full(self.n,self.width*self.h*(1-rho)/self.n)
        if case["layout"] not in ("symmetric","top","bottom"):
            raise ValueError("Unknown reinforcement layout")
        ys=[] if rho==0 else ([self.h/2-cover,cover-self.h/2] if case["layout"]=="symmetric" else
                              [self.h/2-cover if case["layout"]=="top" else cover-self.h/2])
        self.ys=np.array(ys)
        self.As=np.full(len(ys),self.width*self.h*rho/max(1,len(ys)))
        self.concrete=Concrete(c["E20_ksi"]*KSI,c["ft20_MPa"]*1e6,c["fc20_ksi"]*KSI,
                               case.get("Gf_J_m2",c["fracture_energy_J_m2"]),case.get("Lch_m",c["characteristic_length_m"]))
        self.steel=Steel(s["E_GPa"]*1e9,s["fy_MPa"]*1e6)
        self.steel_strain_limit=s["absolute_mechanical_strain_domain_limit"]
        self.root_force_tolerance=1e-8

    def zero(self):
        return {"q":np.zeros(2),"c":zero_concrete(self.n),"s":zero_steel(len(self.ys))}

    def trial(self,old,q):
        q=np.asarray(q,dtype=float)
        if q.shape!=(2,) or not np.isfinite(q).all(): raise ValueError("Finite eps0,kappa pair required")
        c=concrete_trial(self.concrete,old["c"],q[0]-self.yc*q[1])
        s=steel_trial(self.steel,old["s"],q[0]-self.ys*q[1])
        Nc=float(c["stress"]@self.Ac); Ns=float(s["stress"]@self.As)
        Mc=float(-(c["stress"]*self.yc)@self.Ac); Ms=float(-(s["stress"]*self.ys)@self.As)
        K=np.zeros((2,2))
        for A,y,m in ((self.Ac,self.yc,c),(self.As,self.ys,s)):
            B=np.stack((np.ones_like(y),-y),axis=1)
            K+=B.T@((A*m["tangent"])[:,None]*B)
        energies={key:float(self.Ac@c[key]+self.As@s[key]) for key in ("stored","dissipated","work")}
        energy_scale=max(1.,abs(energies["work"]),energies["stored"]+energies["dissipated"])
        # Compression is elastic and plane-section strain is linear: recover
        # the exact OUTER FACE extreme, not the first interior midpoint fiber.
        face_compression=max(0.,-self.concrete.E*(q[0]-abs(q[1])*self.h/2))
        comp=face_compression/self.concrete.fc
        steel_strain=float(max(abs(s["eps"]),default=0.))/self.steel_strain_limit
        return {"q":q.copy(),"c":c,"s":s,"N":Nc+Ns,"M":Mc+Ms,"Nc":Nc,"Ns":Ns,"Mc":Mc,"Ms":Ms,
                "K":K,**energies,"Dc":float(self.Ac@c["dissipated"]),"Ds":float(self.As@s["dissipated"]),
                "energy_residual":abs(energies["work"]-energies["stored"]-energies["dissipated"])/energy_scale,
                "compression_ratio":comp,"steel_strain_ratio":steel_strain,
                "compression_face_stress_Pa":face_compression,
                "sampled_compression_ratio":max(0.,float(-min(c["stress"]))) / self.concrete.fc,
                "domain_ratio":max(comp,steel_strain),
                "domain_kind":"CONCRETE_COMPRESSION_DOMAIN" if comp>=steel_strain else "STEEL_STRAIN_DOMAIN",
                "force_scale":max(1.,float(self.Ac@np.abs(c["stress"])+self.As@np.abs(s["stress"]))) }

    def axial_breakpoints(self,old,kappa):
        """All changes of axial tangent at fixed curvature and old state.

        Sum piecewise-linear contributions instead of a nonlinear root guess.
        No constitutive history is changed during an equilibrium search.
        """
        c=self.concrete; r=old["c"]["r"]; k=c.secant(r)
        virgin=r<=c.e0; partial=(r>c.e0)&(r<c.ef); full=r>=c.ef
        points=[]; deltas=[]
        def add(mask,offset,delta):
            v=np.broadcast_to(offset,r.shape); d=np.broadcast_to(delta,r.shape)
            points.extend((self.yc[mask]*kappa+v[mask]).tolist())
            deltas.extend((self.Ac[mask]*d[mask]).tolist())
        add(virgin,c.e0,c.soft-c.E);add(virgin,c.ef,-c.soft)
        add(partial,0.,k-c.E);add(partial,r,c.soft-k);add(partial,c.ef,-c.soft)
        add(full,0.,-c.E)
        for y,A,p in zip(self.ys,self.As,old["s"]["plastic"],strict=True):
            points.extend((y*kappa+p-self.steel.fy/self.steel.E,y*kappa+p+self.steel.fy/self.steel.E))
            deltas.extend((A*self.steel.E,-A*self.steel.E))
        unique,inverse=np.unique(points,return_inverse=True)
        slope_delta=np.bincount(inverse,weights=deltas,minlength=len(unique))
        # At far negative axial strain, concrete is elastic in compression and steel is on its negative plateau.
        initial_slope=float(c.E*sum(self.Ac))
        return unique,slope_delta,initial_slope

    def solve_axial(self,old,kappa,target_N=0.):
        p,ds,initial_slope=self.axial_breakpoints(old,kappa)
        pad=max(.02,abs(target_N)/initial_slope+.01)
        x=np.r_[p[0]-pad,p,p[-1]+pad]
        slopes=np.r_[initial_slope,initial_slope+np.cumsum(ds)]
        n0=self.trial(old,(x[0],kappa))["N"]-target_N
        residuals=np.r_[n0,n0+np.cumsum(slopes*np.diff(x))]
        candidates=[]; neutral=0
        for i,slope in enumerate(slopes):
            if slope>1e-9*initial_slope:
                root=x[i]-residuals[i]/slope
                if x[i]-1e-13<=root<=x[i+1]+1e-13:
                    if not candidates or abs(root-candidates[-1])>1e-11: candidates.append(float(root))
            elif abs(slope)<1e-9*initial_slope and max(abs(residuals[i]),abs(residuals[i+1]))<1e-6:
                neutral+=1
        if len(candidates)!=1:
            return None,{"status":"MULTIPLE_POSITIVE_AXIAL_ROOTS" if len(candidates)>1 else "NO_POSITIVE_AXIAL_ROOT",
                         "positive_roots":len(candidates),"neutral_intervals":neutral,"root_eps0":candidates}
        root=candidates[0]
        # Remove accumulated summation roundoff using direct constitutive residuals.
        for _ in range(4):
            result=self.trial(old,(root,kappa)); error=result["N"]-target_N
            if abs(error)<1e-10*result["force_scale"]: break
            if result["K"][0,0]<=0: break
            root-=error/result["K"][0,0]
        result=self.trial(old,(root,kappa))
        info={"status":"UNIQUE_POSITIVE_AXIAL_ROOT","positive_roots":1,"neutral_intervals":neutral,
              "axial_residual":abs(result["N"]-target_N)/max(result["force_scale"],abs(target_N),1.)}
        if info["axial_residual"]>self.root_force_tolerance:
            raise ArithmeticError(f"Axial equilibrium not verified: {info}")
        return result,info

    def inventory(self):
        return {"case":self.case,"width_m":self.width,"equivalent_thickness_m":self.h,
                "concrete_fibers":self.n,"concrete_area_m2":float(sum(self.Ac)),"steel_area_m2":float(sum(self.As)),
                "steel_layers":[{"y_m":float(y),"area_m2":float(a)} for y,a in zip(self.ys,self.As,strict=True)],
                "E_concrete_Pa":self.concrete.E,"fc_Pa":self.concrete.fc,"ft_Pa":self.concrete.ft,
                "Gf_J_m2":self.concrete.Gf,"Lch_m":self.concrete.Lch,"elastic_peak_strain":self.concrete.e0,
                "zero_tensile_stress_strain":self.concrete.ef,"E_steel_Pa":self.steel.E,"fy_Pa":self.steel.fy,
                "temperature_c":20.,"energy_units":"J/m longitudinal length; multiply by a declared length for J, no global credit"}


def snapshot(case_id,index,segment,result,info,external,external_abs):
    c=result["c"];s=result["s"]
    scale=max(1.,external_abs,abs(result["work"]))
    return {"case_id":case_id,"step":index,"segment":segment,"eps0":float(result["q"][0]),
            "kappa_per_m":float(result["q"][1]),"N_N":result["N"],"M_Nm":result["M"],
            "concrete_N_N":result["Nc"],"steel_N_N":result["Ns"],"concrete_M_Nm":result["Mc"],"steel_M_Nm":result["Ms"],
            "stored_J_per_m":result["stored"],"dissipated_J_per_m":result["dissipated"],
            "concrete_dissipated_J_per_m":result["Dc"],"steel_dissipated_J_per_m":result["Ds"],
            "exact_material_work_J_per_m":result["work"],"external_trapezoid_work_J_per_m":external,
            "external_absolute_trapezoid_work_J_per_m":external_abs,
            "external_energy_residual":abs(external-result["work"])/scale,
            "exact_energy_residual":result["energy_residual"],"axial_residual":info["axial_residual"],
            "max_damage":float(max(c["damage"])),"cracked_fiber_count":int(np.count_nonzero(c["damage"]>1e-10)),
            "steel_ever_plastic_layers":int(np.count_nonzero(s["accumulated_plastic"]>1e-12)),
            "max_steel_absolute_strain":float(max(abs(s["eps"]),default=0.)),
            "compression_ratio":result["compression_ratio"],"steel_strain_ratio":result["steel_strain_ratio"],
            "compression_face_stress_Pa":result["compression_face_stress_Pa"],"sampled_compression_ratio":result["sampled_compression_ratio"],
            "domain_ratio":result["domain_ratio"],"positive_axial_roots":info["positive_roots"],
            "neutral_axial_intervals":info["neutral_intervals"],"global_energy_credit_J":0.}


def trace(cfg,case,nfibers=None,step_factor=1.):
    if not math.isfinite(step_factor) or step_factor<=0:
        raise ValueError("Positive finite loading step factor required")
    model=Section(cfg,case,nfibers); state=model.trial(model.zero(),(0.,0.))
    history=[]; states_at_vertices=[]; external=0.;external_abs=0.;terminal="END_WITHIN_DECLARED_SECTION_DOMAIN"
    axial_target=-case.get("compression_fraction_fc_Ac",0.)*model.concrete.fc*sum(model.Ac)
    vertices=cfg["paths"]["cyclic_vertices_per_m"] if case["kind"]=="cyclic" else [0.,case.get("direction",1)*cfg["paths"]["monotonic_end_curvature_per_m"]]
    targets=[(-1,0.,float(n)) for n in np.linspace(0.,axial_target,cfg["paths"]["axial_preload_steps"]+1)[1:]] if axial_target else []
    step=cfg["paths"]["curvature_step_per_m"]*step_factor
    for segment,(a,b) in enumerate(zip(vertices[:-1],vertices[1:],strict=True)):
        targets.extend((segment,float(k),axial_target) for k in np.linspace(a,b,max(1,int(math.ceil(abs(b-a)/step)))+1)[1:])
    info={"axial_residual":0.,"positive_roots":1,"neutral_intervals":0}
    history.append(snapshot(case["id"],0,-1,state,info,0.,0.))
    stop_info=None
    for segment,k,n in targets:
        result,info=model.solve_axial(state,k,n)
        if result is None:
            terminal=info["status"];stop_info={**info,"attempted_kappa_per_m":k,"attempted_N_N":n};break
        if result["domain_ratio"]>=1.:
            lo=0.;hi=1.;old_k=state["q"][1];old_n=state["N"]
            for _ in range(55):
                mid=(lo+hi)/2
                candidate,ci=model.solve_axial(state,old_k+mid*(k-old_k),old_n+mid*(n-old_n))
                if candidate is None: raise ArithmeticError("Axial branch lost while locating domain boundary")
                if candidate["domain_ratio"]>=1.: hi=mid
                else: lo=mid
                if hi-lo<1e-11: break
            result,info=model.solve_axial(state,old_k+hi*(k-old_k),old_n+hi*(n-old_n))
            terminal=result["domain_kind"]
        dq=result["q"]-state["q"]
        dw=.5*((result["N"]+state["N"])*dq[0]+(result["M"]+state["M"])*dq[1])
        external+=dw;external_abs+=abs(dw)
        state=result  # Commit only this accepted equilibrium, never search trials.
        history.append(snapshot(case["id"],len(history),segment,state,info,external,external_abs))
        if any(abs(state["q"][1]-v)<1e-12 for v in vertices):
            states_at_vertices.append(history[-1])
        if terminal!="END_WITHIN_DECLARED_SECTION_DOMAIN": break
    first_crack=next((r for r in history if r["cracked_fiber_count"]),None)
    first_yield=next((r for r in history if r["steel_ever_plastic_layers"]),None)
    summary={**case,"terminal":terminal,"states":len(history),"last_kappa_per_m":float(state["q"][1]),
             "last_M_Nm":state["M"],"peak_absolute_M_Nm":max(abs(r["M_Nm"]) for r in history),
             "first_sampled_crack_kappa_per_m":first_crack["kappa_per_m"] if first_crack else None,
             "first_sampled_steel_yield_kappa_per_m":first_yield["kappa_per_m"] if first_yield else None,
             "last_concrete_dissipation_J_per_m":state["Dc"],"last_steel_dissipation_J_per_m":state["Ds"],
             "max_axial_residual":max(r["axial_residual"] for r in history),
             "max_exact_energy_residual":max(r["exact_energy_residual"] for r in history),
             "max_external_energy_residual":max(r["external_energy_residual"] for r in history),
             "last_domain_ratio":state["domain_ratio"],"stop_info":stop_info,"global_energy_credit_J":0.}
    fibers=[]
    for kind,y,A,m in (("concrete",model.yc,model.Ac,state["c"]),("reinforcement",model.ys,model.As,state["s"])):
        for i in range(len(y)):
            fibers.append({"case_id":case["id"],"kind":kind,"fiber":i,"y_m":float(y[i]),"area_m2":float(A[i]),
                           "strain":float(m["eps"][i]),"stress_Pa":float(m["stress"][i]),
                           "stored_J_m3":float(m["stored"][i]),"dissipated_J_m3":float(m["dissipated"][i]),
                           "damage":float(m["damage"][i]) if kind=="concrete" else None,
                           "plastic_strain":float(m["plastic"][i]) if kind=="reinforcement" else None})
    return {"summary":summary,"history":history,"vertices":states_at_vertices,"fibers":fibers,"inventory":model.inventory()}
