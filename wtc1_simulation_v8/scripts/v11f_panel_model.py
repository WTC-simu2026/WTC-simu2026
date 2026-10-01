"""Small-strain cold fiber slab / truss / unilateral interface coupling.

No exact-UDL elastic bubble is added to nonlinear fiber stresses or energy.
Longitudinal integration converts section J/m to local PANEL J only.
"""
from __future__ import annotations
import math
import numpy as np
import v11d_panel_model as elastic
import v11e_section_model as section


class Unresolved(RuntimeError): pass


def beam_B(x,L):
    B=np.zeros((2,6));B[0,[0,3]]=[-1/L,1/L]
    B[1,[1,2,4,5]]=elastic.beam_curvature_row(x,L)
    return B


class Panel:
    def __init__(self,cfg,inputs,case,subdivisions=None):
        self.cfg=cfg;self.case=dict(case);self.inputs=inputs
        if cfg["loading"]["temperature_c"]!=20.: raise ValueError("V11F is cold only")
        sub=cfg["discretization"]["reference_subdivisions_per_steel_panel"] if subdivisions is None else subdivisions
        if not isinstance(sub,int) or sub<2 or sub%2: raise ValueError("Even subdivisions retain the prescribed mid-bay actuator")
        if cfg["discretization"]["longitudinal_gauss_points_per_element"]!=2: raise ValueError("Only declared two-point Gauss rule implemented")
        self.spec={"subdivisions":sub,"gravity_factor":1.,"horizontal_mode":"roller"}
        self.model=elastic.build_panel(inputs["d"],inputs["c"],inputs["a"],inputs["transfer"],inputs["seats"],self.spec)
        self.size=self.model["size"];self.force_unit=self.model["force"].copy()
        self.terms=[t for t in self.model["terms"] if t["kind"] not in ("slab_axial","slab_bending")]
        if any(t["e0"]!=0 for t in self.terms): raise ValueError("Thermal/moving-anchor eigenstrain unsupported in V11F")
        self.term_B=np.zeros((len(self.terms),self.size))
        for j,t in enumerate(self.terms):self.term_B[j,t["dofs"]]=t["b"]
        self.term_k=np.array([t["k"] for t in self.terms])
        self.compression=np.array([t.get("compression_only",False) for t in self.terms])
        self.tension=np.array([t.get("tension_only",False) for t in self.terms])
        self.dx=self.model["span_m"]/(len(self.model["w"])-1)
        if cfg["discretization"]["Lch_policy"]!="QUADRATURE_TRIBUTARY_LENGTH": raise ValueError("Unknown crack-band length rule")
        self.Lch=self.dx/2
        self.section=section.Section(inputs["e"],{**case,"Lch_m":self.Lch},cfg["discretization"]["concrete_depth_fibers"])
        self.dofs=[];self.B=[];self.x=[];self.element=[];self.Bends=[]
        for j,el in enumerate(self.model["elements"]):
            d=[self.model["ux"][j],self.model["w"][j],self.model["theta"][j],
               self.model["ux"][j+1],self.model["w"][j+1],self.model["theta"][j+1]]
            self.Bends.append([beam_B(0,self.dx),beam_B(self.dx,self.dx)])
            for local_x in (self.dx*(.5-.5/math.sqrt(3)),self.dx*(.5+.5/math.sqrt(3))):
                self.dofs.append(d);self.B.append(beam_B(local_x,self.dx));self.x.append(j*self.dx+local_x);self.element.append(j)
        self.dofs=np.array(self.dofs,dtype=int);self.B=np.array(self.B);self.x=np.array(self.x);self.element=np.array(self.element)
        self.Bends=np.array(self.Bends);self.weights=np.full(len(self.x),self.dx/2)
        self.assembly_i=np.repeat(self.dofs,6,axis=1).ravel();self.assembly_j=np.tile(self.dofs,(1,6)).ravel()
        self.slab_actuator_node=int(cfg["loading"]["slab_actuator_steel_bay_coordinate"]*sub)
        if self.slab_actuator_node!=cfg["loading"]["slab_actuator_steel_bay_coordinate"]*sub: raise ValueError("Actuator not exactly on mesh")
        self.slab_actuator=int(self.model["w"][self.slab_actuator_node])
        self.truss_actuator=2*cfg["loading"]["truss_actuator_station"]+1
        cold=self.evaluate(self.zero(),np.zeros(self.size),0.,{})
        self.scale=1/np.sqrt(np.diag(cold["K"]))

    def zero(self):
        n=len(self.x);s=self.section
        return {"u":np.zeros(self.size),"c":section.zero_concrete((n,s.n)),"s":section.zero_steel((n,len(s.ys)))}

    def batch(self,old,q):
        s=self.section
        c=section.concrete_trial(s.concrete,old["c"],q[:,0,None]-q[:,1,None]*s.yc)
        steel=section.steel_trial(s.steel,old["s"],q[:,0,None]-q[:,1,None]*s.ys)
        N=c["stress"]@s.Ac+steel["stress"]@s.As
        M=-(c["stress"]*s.yc)@s.Ac-(steel["stress"]*s.ys)@s.As
        K=np.zeros((len(q),2,2))
        for material,A,y in ((c,s.Ac,s.yc),(steel,s.As,s.ys)):
            K[:,0,0]+=material["tangent"]@A
            K[:,0,1]-=material["tangent"]@(A*y)
            K[:,1,1]+=material["tangent"]@(A*y*y)
        K[:,1,0]=K[:,0,1]
        energy={key:c[key]@s.Ac+steel[key]@s.As for key in ("stored","dissipated","work")}
        return {"q":q,"c":c,"s":steel,"Q":np.column_stack((N,M)),"Ksec":K,**energy,
                "Dc":c["dissipated"]@s.Ac,"Ds":steel["dissipated"]@s.As}

    def evaluate(self,old,u,gravity,prescribed):
        u=np.asarray(u,dtype=float)
        if u.shape!=(self.size,) or not np.isfinite(u).all():raise ValueError("Invalid displacement vector")
        q=np.einsum("pai,pi->pa",self.B,u[self.dofs]);bs=self.batch(old,q)
        internal=np.zeros(self.size);absolute=np.zeros(self.size);K=np.zeros((self.size,self.size))
        local=np.einsum("pai,pa,p->pi",self.B,bs["Q"],self.weights)
        np.add.at(internal,self.dofs.ravel(),local.ravel())
        ab=np.einsum("pai,pa,p->pi",abs(self.B),abs(bs["Q"]),self.weights)
        np.add.at(absolute,self.dofs.ravel(),ab.ravel())
        local_K=np.einsum("pai,pab,pbj,p->pij",self.B,bs["Ksec"],self.B,self.weights)
        np.add.at(K,(self.assembly_i,self.assembly_j),local_K.ravel())
        gap=self.term_B@u
        strain=np.where(self.compression,np.minimum(gap,0.),np.where(self.tension,np.maximum(gap,0.),gap))
        force=self.term_k*strain
        active=np.where(self.compression,gap<=0.,np.where(self.tension,gap>0.,True))
        internal+=self.term_B.T@force
        absolute+=abs(self.term_B).T@abs(force)
        K+=self.term_B.T@((self.term_k*active)[:,None]*self.term_B)
        spring_U=float(.5*np.dot(self.term_k,strain**2))
        energies={key:float(self.weights@bs[key]) for key in ("stored","dissipated","work")}
        stored=energies["stored"]+spring_U;work=energies["work"]+spring_U
        F=gravity*self.force_unit;R=internal-F
        free=np.array([i for i in range(self.size) if i not in prescribed],dtype=int)
        eqscale=np.maximum(1.,np.maximum(abs(F),absolute))
        error=float(max(abs(R[free])/eqscale[free],default=0.))
        limits=[];dcrs=[]
        for j,(t,n) in enumerate(zip(self.terms,force,strict=True)):
            kind=t["kind"];dcr=0.
            if kind=="horizontal_tie":dcr=abs(n)/t["cap_abs_N"]
            elif kind=="vertical_tie":dcr=max(n,0.)/t["cap_tension_N"]
            elif kind=="seat_v":dcr=max(-n,0.)/t["cap_compression_N"]
            elif kind=="seat_h":dcr=max(n*t["tension_sign"],0.)/t["cap_signed_tension_N"]
            elif kind in ("top_chord","bottom_chord","web"):dcr=abs(n)/(t["cap_compression_N"] if n<0 else t["cap_tension_N"])
            dcrs.append(float(dcr));limits.append({"id":t["id"],"kind":kind,"DCR":float(dcr)})
        # Exact extremes of the FE's linear curvature at element ends. No elastic UDL bubble.
        endq=np.einsum("ejai,ei->eja",self.Bends,u[self.dofs[::2]])
        face_compression=np.maximum(0.,-self.section.concrete.E*(endq[:,:,0]-abs(endq[:,:,1])*self.section.h/2))
        cr=float(np.max(face_compression)/self.section.concrete.fc)
        if len(self.section.ys):sr=float(np.max(abs(endq[:,:,0,None]-endq[:,:,1,None]*self.section.ys))/self.section.steel_strain_limit)
        else:sr=0.
        limits.extend([{"id":"SLAB-END-FACE","kind":"slab_compression_domain","DCR":cr},
                       {"id":"REBAR-END","kind":"rebar_strain_domain","DCR":sr}]);limits.sort(key=lambda v:(-v["DCR"],v["id"]))
        mask_contact=np.array([t["kind"]=="contact" for t in self.terms]);mask_vtie=np.array([t["kind"]=="vertical_tie" for t in self.terms])
        seat=sum(-n for t,n in zip(self.terms,force,strict=True) if t["kind"]=="seat_v")
        actuator=sum(R[d] for d in prescribed)
        return {"u":u.copy(),"c":bs["c"],"s":bs["s"],"batch":bs,"K":K,"force":F,"reaction":R,
                "free":free,"eq_scale":eqscale,"equilibrium_residual":error,"term_force":force,"term_gap":gap,"term_DCR":dcrs,
                "stored_J":stored,"spring_stored_J":spring_U,"slab_stored_J":energies["stored"],"dissipated_J":energies["dissipated"],
                "concrete_dissipated_J":float(self.weights@bs["Dc"]),"steel_dissipated_J":float(self.weights@bs["Ds"]),"exact_internal_work_J":work,
                "exact_energy_residual":abs(work-stored-energies["dissipated"])/max(1.,abs(work),stored+energies["dissipated"]),
                "max_DCR":limits[0]["DCR"],"governing":limits[0],"compression_ratio":cr,"rebar_strain_ratio":sr,
                "max_slab_down_m":float(max(-u[self.model["w"]])),"max_truss_down_m":float(max(-u[1:self.model["steel_dofs"]:2])),
                "max_opening_m":float(max(0.,max(gap[mask_contact]))),"max_overlap_m":float(max(0.,max(-gap[mask_contact]))),
                "contact_count":int(sum(force[mask_contact]<-1e-5)),"vertical_tension_count":int(sum(force[mask_vtie]>1e-5)),
                "seat_reaction_N":float(seat),"actuator_reaction_N":float(actuator),"gravity_load_N":float(-sum(F[self.model["w"]])),
                "support_uplift_unchecked":any(n>1e-5 for t,n in zip(self.terms,force,strict=True) if t["kind"]=="seat_v"),
                "support_horizontal_compression_unchecked":any(n*t["tension_sign"]<-1e-5 for t,n in zip(self.terms,force,strict=True) if t["kind"]=="seat_h")}

    def solve(self,old,gravity,prescribed=None,initial=None):
        prescribed=prescribed or {};u=old["u"].copy() if initial is None else np.array(initial,copy=True)
        vertical=set(range(1,self.model["steel_dofs"],2))|set(map(int,self.model["w"]))
        if any(d not in vertical or not math.isfinite(v) for d,v in prescribed.items()):
            raise ValueError("V11F actuator accounting supports finite vertical prescriptions only")
        for d,value in prescribed.items():u[d]=value
        opt=self.cfg["solver"];free=np.array([i for i in range(self.size) if i not in prescribed],dtype=int)
        sc=self.scale[free]
        for iteration in range(opt["maximum_newton_iterations"]):
            r=self.evaluate(old,u,gravity,prescribed)
            scaled=sc[:,None]*r["K"][np.ix_(free,free)]*sc[None,:]
            if r["equilibrium_residual"]<=opt["relative_equilibrium_tolerance"]:
                r["minimum_scaled_tangent_eigenvalue"]=float(np.linalg.eigvalsh(scaled)[0])
                r["newton_iterations"]=iteration+1;return r
            try:delta=sc*np.linalg.solve(scaled,-sc*r["reaction"][free])
            except np.linalg.LinAlgError as error:raise Unresolved("SINGULAR_NEWTON_NOT_COLLAPSE") from error
            merit=float(np.linalg.norm(sc*r["reaction"][free]));accepted=False
            for halvings in range(opt["maximum_line_search_halvings"]+1):
                candidate=u.copy();candidate[free]+=delta*2.**(-halvings)
                rr=self.evaluate(old,candidate,gravity,prescribed)
                if float(np.linalg.norm(sc*rr["reaction"][free]))<merit*(1-1e-4*2.**(-halvings)) or rr["equilibrium_residual"]<=opt["relative_equilibrium_tolerance"]:
                    u=candidate;accepted=True;break
            if not accepted:raise Unresolved("NEWTON_LINE_SEARCH_EXHAUSTED_NOT_COLLAPSE")
        raise Unresolved("NEWTON_ITERATION_LIMIT_NOT_COLLAPSE")

    def inventory(self):
        return {"case":self.case,"subdivisions":self.model["subdivisions"],"degrees_of_freedom":self.size,
                "steel_nodes":len(self.model["nodes"]),"steel_members":len(self.model["steel_members"]),
                "slab_nodes":len(self.model["w"]),"slab_elements":len(self.model["elements"]),"gauss_sections":len(self.x),
                "contact_stations":sum(t["kind"]=="contact" for t in self.terms),"section":self.section.inventory(),
                "Lch_m":self.Lch,"span_m":self.model["span_m"],"quadrature_weight_sum_m":float(sum(self.weights)),
                "slab_actuator_x_m":float(self.model["slab_x_m"][self.slab_actuator_node]),
                "slab_actuator_dof":self.slab_actuator,"truss_actuator_dof":self.truss_actuator,
                "total_reference_gravity_N":float(-sum(self.force_unit[self.model["w"]])),"global_energy_credit_J":0.}


def snapshot(model,r,phase,parameter,gravity,offset,external,external_abs):
    bs=r["batch"];cracked=np.any(bs["c"]["damage"]>1e-10,axis=1)
    row={"case_id":model.case["id"],"phase":phase,"phase_progress":parameter,"gravity_factor":gravity,"actuator_offset_m":offset,
         "external_work_J":external,"external_absolute_work_J":external_abs,
         "external_energy_residual":abs(external-r["exact_internal_work_J"])/max(1.,external_abs,abs(r["exact_internal_work_J"])),
         "max_damage":float(np.max(bs["c"]["damage"])),"cracked_sections":int(sum(cracked)),
         "cracked_quadrature_length_m":float(sum(model.weights[cracked])),
         "reinforcement_plastic_points":int(np.count_nonzero(bs["s"]["accumulated_plastic"]>1e-12)),
         "governing_kind":r["governing"]["kind"],"governing_id":r["governing"]["id"],"global_energy_credit_J":0.}
    fields=("equilibrium_residual","exact_energy_residual","stored_J","spring_stored_J","slab_stored_J","dissipated_J","concrete_dissipated_J",
            "steel_dissipated_J","exact_internal_work_J","max_DCR","compression_ratio","rebar_strain_ratio","max_slab_down_m","max_truss_down_m",
            "max_opening_m","max_overlap_m","contact_count","vertical_tension_count","seat_reaction_N","actuator_reaction_N","gravity_load_N",
            "minimum_scaled_tangent_eigenvalue","newton_iterations","support_uplift_unchecked","support_horizontal_compression_unchecked")
    row.update({k:r[k] for k in fields});return row


def trace(cfg,inputs,case,subdivisions=None,step_factor=1.):
    if step_factor<=0:raise ValueError("Positive step factor required")
    model=Panel(cfg,inputs,case,subdivisions);state=model.solve(model.zero(),0.)
    ext=0.;ext_abs=0.;history=[snapshot(model,state,"preload",0.,0.,0.,ext,ext_abs)]
    rejects=[];status="END_WITHIN_CHECKED_LOCAL_DOMAIN_NOT_SAFETY_PROOF";last_boundary={};last_gravity=0.;last_offset=0.
    load=cfg["loading"];opt=cfg["solver"];kind=case["kind"]
    endg=case.get("gravity_end",load["preload_gravity_factor"])
    phases=[("gravity",0.,endg,max(1,int(math.ceil(endg/(load["gravity_step"]*step_factor)))))]
    base_u=None
    if kind in ("slab_actuator","slab_cycle","truss_actuator","truss_cycle"):
        vertices=load["truss_cycle_offset_vertices_m"] if kind=="truss_cycle" else load["slab_cycle_offset_vertices_m"] if kind=="slab_cycle" else [0.,load["truss_actuator_end_offset_m"] if kind=="truss_actuator" else load["slab_actuator_end_offset_m"]]
        phases += [(f"actuator_{j}",a,b,int(math.ceil(load["steps_per_actuator_segment"]/step_factor))) for j,(a,b) in enumerate(zip(vertices[:-1],vertices[1:],strict=True))]
    for phase,a,b,nsteps in phases:
        if phase!="gravity" and base_u is None:base_u=state["u"].copy()
        actuator=model.truss_actuator if kind.startswith("truss_") else model.slab_actuator
        def target(p):
            if phase=="gravity": return a+(b-a)*p,{},0.
            offset=a+(b-a)*p
            return endg,{actuator:float(base_u[actuator]+offset)},offset
        p=0.;dp=1/nsteps
        while p<1-1e-12:
            pn=min(1.,p+dp);g,fixed,offset=target(pn)
            try:
                candidate=model.solve(state,g,fixed)
                du=candidate["u"]-state["u"]
                dw=float(.5*(candidate["force"]+state["force"])@du)
                dw+=sum(.5*(candidate["reaction"][d]+state["reaction"][d])*du[d] for d in fixed)
                local_error=abs(dw-(candidate["exact_internal_work_J"]-state["exact_internal_work_J"]))/max(opt["increment_energy_floor_J"],abs(dw),abs(candidate["exact_internal_work_J"]-state["exact_internal_work_J"]))
                if local_error>opt["increment_external_energy_tolerance"]:raise Unresolved("INCREMENT_WORK_REQUIRES_CUTBACK")
            except Unresolved as error:
                rejects.append({"phase":phase,"from":p,"attempt":pn,"reason":str(error),"state_committed":False})
                dp/=2
                if dp<opt["minimum_phase_step"]:
                    status="UNRESOLVED_CONTINUATION_NOT_COLLAPSE";break
                continue
            event=None
            if candidate["minimum_scaled_tangent_eigenvalue"]<=opt["scaled_tangent_minimum"]:event="NONPOSITIVE_TANGENT_DIAGNOSTIC_NOT_COLLAPSE"
            elif candidate["max_DCR"]>=1.:event="FIRST_NOMINAL_OR_MATERIAL_DOMAIN_LIMIT"
            if event:
                lo,hi=p,pn;best=candidate
                while hi-lo>opt["event_phase_bracket_tolerance"]:
                    mid=(lo+hi)/2;mg,mfix,mo=target(mid)
                    try:trial=model.solve(state,mg,mfix)
                    except Unresolved:hi=mid;continue
                    if trial["max_DCR"]>=1 or trial["minimum_scaled_tangent_eigenvalue"]<=opt["scaled_tangent_minimum"]:hi=mid;best=trial
                    else:lo=mid
                # Only promote an actually converged target; no failed upper bracket is fabricated.
                g,fixed,offset=target(hi)
                try:candidate=model.solve(state,g,fixed)
                except Unresolved:
                    status="UNRESOLVED_EVENT_BRACKET_NOT_COLLAPSE";break
                pn=hi;du=candidate["u"]-state["u"]
                dw=float(.5*(candidate["force"]+state["force"])@du)+sum(.5*(candidate["reaction"][d]+state["reaction"][d])*du[d] for d in fixed)
                local_error=abs(dw-(candidate["exact_internal_work_J"]-state["exact_internal_work_J"]))/max(opt["increment_energy_floor_J"],abs(dw),abs(candidate["exact_internal_work_J"]-state["exact_internal_work_J"]))
                if local_error>opt["increment_external_energy_tolerance"]:
                    rejects.append({"phase":phase,"from":p,"attempt":pn,"reason":"EVENT_INCREMENT_WORK_REQUIRES_CUTBACK","state_committed":False})
                    dp/=2
                    if dp<opt["minimum_phase_step"]:status="UNRESOLVED_CONTINUATION_NOT_COLLAPSE";break
                    continue
                if candidate["minimum_scaled_tangent_eigenvalue"]<=opt["scaled_tangent_minimum"]:event="NONPOSITIVE_TANGENT_DIAGNOSTIC_NOT_COLLAPSE"
                elif candidate["max_DCR"]>=1-1e-7:event="FIRST_NOMINAL_OR_MATERIAL_DOMAIN_LIMIT"
                else:status="UNRESOLVED_EVENT_BRACKET_NOT_COLLAPSE";break
                status=event
            ext+=dw;ext_abs+=abs(dw);state=candidate;last_boundary=fixed;last_gravity=g;last_offset=offset;p=pn
            history.append(snapshot(model,state,phase,p,g,offset,ext,ext_abs))
            if event:break
            dp=min(1/nsteps,dp*1.5)
        if status!="END_WITHIN_CHECKED_LOCAL_DOMAIN_NOT_SAFETY_PROOF":break
    summary={**case,"terminal":status,"point_count":len(history),"rejected_trials":len(rejects),**history[-1]}
    first=next((r for r in history if r["cracked_sections"]),None)
    summary["first_sampled_crack"]=None if first is None else {k:first[k] for k in ("phase","phase_progress","gravity_factor","actuator_offset_m")}
    summary["max_path_external_energy_residual"]=max(r["external_energy_residual"] for r in history)
    summary["max_path_equilibrium_residual"]=max(r["equilibrium_residual"] for r in history)
    summary["max_path_exact_energy_residual"]=max(r["exact_energy_residual"] for r in history)
    q=state["batch"];section_rows=[]
    for p in range(len(model.x)):
        section_rows.append({"case_id":case["id"],"point":p,"element":int(model.element[p]),"x_m":float(model.x[p]),"weight_m":float(model.weights[p]),"Lch_m":model.Lch,
                             "eps0":float(q["q"][p,0]),"kappa_per_m":float(q["q"][p,1]),"N_N":float(q["Q"][p,0]),"M_Nm":float(q["Q"][p,1]),
                             "stored_J_per_m":float(q["stored"][p]),"dissipated_J_per_m":float(q["dissipated"][p]),"work_J_per_m":float(q["work"][p]),
                             "max_damage":float(max(q["c"]["damage"][p])),"concrete_dissipated_J_per_m":float(q["Dc"][p]),"steel_dissipated_J_per_m":float(q["Ds"][p])})
    term_rows=[{"case_id":case["id"],"id":t["id"],"kind":t["kind"],"force_N":float(state["term_force"][j]),"extension_or_gap_m":float(state["term_gap"][j]),"DCR":state["term_DCR"][j],"station":t.get("station")} for j,t in enumerate(model.terms)]
    nodes=[{"case_id":case["id"],"node":j,"x_m":float(x),"axial_m":float(state["u"][model.model["ux"][j]]),"vertical_m":float(state["u"][model.model["w"][j]]),"rotation_rad":float(state["u"][model.model["theta"][j]])} for j,x in enumerate(model.model["slab_x_m"])]
    return {"summary":summary,"history":history,"sections":section_rows,"terms":term_rows,"slab_nodes":nodes,"rejected_trials":rejects,"inventory":model.inventory()},model,state
