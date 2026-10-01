"""Elastic uncracked slab/contact predictor, small displacement and SI.

Concrete cracking ends the predictor domain. No postcracking resistance,
member failure trajectory or physical dynamic fracture is inferred.
"""
from __future__ import annotations
import math
import numpy as np
import v11c_panel_model as previous
from v11a_component_model import IN, KSI, KIP, PSF

UnresolvedEquilibrium = previous.UnresolvedEquilibrium


def term(identifier, kind, dofs, b, k, e0=0., compression_only=False, tension_only=False, **metadata):
    if not math.isfinite(k) or k<=0 or compression_only and tension_only:
        raise ValueError("Invalid stiffness or mutually exclusive branch flags")
    return {"id":identifier,"kind":kind,"dofs":list(dofs),"b":list(b),"k":float(k),"e0":float(e0),
            "compression_only":compression_only,"tension_only":tension_only,**metadata}


def beam_curvature_row(x,L):
    return np.array([-6/L**2+12*x/L**3,-4/L+6*x/L**2,6/L**2-12*x/L**3,-2/L+6*x/L**2])


def beam_terms(prefix,i_w,i_theta,j_w,j_theta,L,EI,curvature=0.):
    if L<=0 or EI<=0: raise ValueError("Invalid beam dimension")
    return [term(f"{prefix}-G{j}","slab_bending",[i_w,i_theta,j_w,j_theta],beam_curvature_row(x,L),
            EI*L/2,curvature,generalized_strain_unit="1/m",generalized_stiffness_unit="N*m^3",
            parent_element=prefix,gauss_x_m=x)
            for j,x in enumerate([L/2-L/(2*math.sqrt(3)),L/2+L/(2*math.sqrt(3))],1)]


def beam_load(L,q):
    return np.array([q*L/2,q*L**2/12,q*L/2,-q*L**2/12])


def recover_beam(u,L,EI,q,curvature=0.):
    """Exact UDL particular solution inside an otherwise cubic beam cell."""
    u=np.asarray(u)
    c0=float(beam_curvature_row(0,L)@u)
    cL=float(beam_curvature_row(L,L)@u)
    points=[0.,L]
    if abs(q)>1e-20:
        stationary=L/2-EI*(cL-c0)/(L*q)
        if 0<stationary<L: points.append(stationary)
    moments=[EI*(float(beam_curvature_row(x,L)@u)-curvature)+q*(L**2-6*L*x+6*x*x)/12 for x in points]
    bubble_energy=q*q*L**5/(1440*EI)
    return {"x_m":points,"moment_Nm":moments,"bubble_energy_J":bubble_energy,
            "bubble_load_work_J":2*bubble_energy}


def solve_terms(size,terms,force,prescribed=None,tolerance_N=1e-5):
    """Active-set unilateral springs; beam terms remain bilateral.

    At zero gap a matched contact/tie pair uses compression tangent only.
    Singular states are rejected, with no automatic stabilizing springs.
    """
    prescribed=prescribed or {}
    fixed=np.array(sorted(prescribed),dtype=int)
    free=np.array([i for i in range(size) if i not in prescribed],dtype=int)
    force=np.asarray(force,dtype=float)
    if force.shape!=(size,) or not np.all(np.isfinite(force)): raise ValueError("Invalid load vector")
    for i in fixed:
        if i<0 or i>=size: raise ValueError("Invalid prescribed DOF")
    active=np.array([not r.get("tension_only",False) for r in terms])
    seen=set()
    for iteration in range(150):
        key=tuple(active)
        if key in seen: raise UnresolvedEquilibrium("UNILATERAL_ACTIVE_SET_CYCLE_NOT_COLLAPSE")
        seen.add(key)
        matrix=np.zeros((size,size)); eigen=np.zeros(size)
        for on,r in zip(active,terms):
            if not on: continue
            d,b=np.array(r["dofs"]),np.asarray(r["b"])
            matrix[np.ix_(d,d)]+=r["k"]*np.outer(b,b)
            eigen[d]+=r["k"]*r["e0"]*b
        u=np.zeros(size)
        for i,v in prescribed.items(): u[i]=v
        if len(free):
            kff=matrix[np.ix_(free,free)]
            diag=np.diag(kff)
            if np.any(diag<=0): raise UnresolvedEquilibrium("DISCONNECTED_DOF_NOT_PHYSICAL_COLLAPSE")
            scale=1/np.sqrt(diag); scaled=scale[:,None]*kff*scale[None,:]
            if np.linalg.eigvalsh(scaled)[0]<=1e-11: raise UnresolvedEquilibrium("STATIC_RANK_LOSS_NOT_PHYSICAL_COLLAPSE")
            u[free]=scale*np.linalg.solve(scaled,scale*(force+eigen-matrix@u)[free])
        strains=np.array([np.dot(r["b"],u[r["dofs"]])-r["e0"] for r in terms])
        next_active=active.copy()
        for i,r in enumerate(terms):
            trial=r["k"]*strains[i]
            if r.get("compression_only",False):
                if trial>tolerance_N: next_active[i]=False
                elif trial< -tolerance_N: next_active[i]=True
            elif r.get("tension_only",False):
                if trial>tolerance_N: next_active[i]=True
                elif trial< -tolerance_N: next_active[i]=False
        if np.array_equal(active,next_active): break
        active=next_active
    else: raise UnresolvedEquilibrium("UNILATERAL_ITERATION_LIMIT")
    internal=np.zeros(size); absolute_contributions=np.zeros(size); rows=[]
    for r,s in zip(terms,strains):
        elastic=min(s,0.) if r.get("compression_only",False) else max(s,0.) if r.get("tension_only",False) else s
        n=r["k"]*elastic; energy=.5*r["k"]*elastic**2
        internal[r["dofs"]]+=n*np.asarray(r["b"])
        absolute_contributions[r["dofs"]]+=np.abs(n*np.asarray(r["b"]))
        rows.append({**r,"generalized_strain":float(s),"force_N":float(n),
            "generalized_force_unit":"N*m^2" if r["kind"]=="slab_bending" else "N",
            "strain_energy_J":float(energy),"active":bool(elastic!=0.),
            "state":"ZERO_INACTIVE_BRANCH" if (r.get("compression_only") or r.get("tension_only")) and elastic==0. else "ELASTIC"})
    reaction=internal-force
    energy=sum(r["strain_energy_J"] for r in rows)
    eigenwork=sum(r["force_N"]*r["e0"] for r in rows)
    rhs=float(u@force+u[fixed]@reaction[fixed]-eigenwork)
    # Normalize each equation separately: forces and nodal moments are never
    # added together as if they shared units. The floor is1N or1Nm per DOF.
    equation_scales=np.maximum(1.,np.maximum(np.abs(force),absolute_contributions))
    eq=max(np.abs(reaction[free])/equation_scales[free],default=0.)
    er=abs(2*energy-rhs)/max(1.,2*energy,abs(rhs))
    return {"u":u,"reaction":reaction,"terms":rows,"strain_energy_J":energy,
        "energy_identity_rhs_J":rhs,"energy_identity_residual":float(er),"equilibrium_residual":float(eq),
        "active_set_iterations":iteration+1}


def build_panel(cfg,cfg_c,base,transfer,seats,spec,removed_stations=()):
    slab=cfg["slab"]; conn=cfg["vertical_connection"]
    ts=spec.get("steel_c",20.); tt=spec.get("slab_top_c",20.); tb=spec.get("slab_bottom_c",20.); tc=(tt+tb)/2
    if not 20<=tt<=600 or not 20<=tb<=600: raise ValueError("Slab face temperatures outside20..600C")
    old_spec={**spec,"slab_c":tc}
    old=previous.build_panel(cfg_c,base,transfer,seats,old_spec)
    panel=cfg_c["panel"]; bay=base["floor_bay"]
    sub=int(spec.get("subdivisions",slab["subdivisions_per_steel_panel"]))
    if sub<1 or sub!=spec.get("subdivisions",sub): raise ValueError("Positive integer slab subdivisions required")
    p=old["panels"]; n=p*sub+1; ns=old["steel_dofs"]; size=ns+3*n
    ux=np.arange(ns,ns+n,dtype=int); w=np.arange(ns+n,ns+2*n,dtype=int); theta=np.arange(ns+2*n,size,dtype=int)
    terms=[{**r,"tension_only":False} for r in old["terms"] if r["kind"] not in ("slab","bond")]
    # Steel and seats retained; the prior slab axial law and perfect vertical load path are not reused.
    width=panel["symmetric_trusses_per_pair"]*bay["width_per_single_truss_in"]*IN
    thickness=bay["equivalent_slab_thickness_in"]*IN; area=width*thickness; inertia=width*thickness**3/12
    con=bay["concrete_hypotheses"]
    ec=float(con["elastic_modulus_20c_ksi"]*KSI*np.interp(tc,con["temperature_knots_c"],con["modulus_ratios"]))
    fc=float(con["compression_strength_20c_ksi"]*KSI*np.interp(tc,con["temperature_knots_c"],con["compression_ratios"]))
    ft=spec.get("ft_MPa",slab["tensile_screen_20c_MPa"])*1e6*np.interp(tc,slab["tensile_temperature_c"],slab["tensile_reduction_ratios"])
    alpha=panel["concrete_expansion_per_K"]; curvature=-alpha*(tt-tb)/thickness
    dx=old["span_m"]/(n-1); force=np.zeros(size); elements=[]
    q=-panel["load_psf"]*PSF*width*spec.get("gravity_factor",1.)
    for j in range(n-1):
        identifier=f"SLAB-{j:03d}"; dofs=[int(w[j]),int(theta[j]),int(w[j+1]),int(theta[j+1])]
        terms.append(term(identifier+"-AX","slab_axial",[int(ux[j]),int(ux[j+1])],[-1,1],ec*area/dx,alpha*(tc-20)*dx))
        terms.extend(beam_terms(identifier,*dofs,dx,ec*inertia,curvature))
        force[dofs]+=beam_load(dx,q)
        elements.append({"id":identifier,"dofs":dofs,"axial_id":identifier+"-AX","length_m":dx,
            "EI_Nm2":ec*inertia,"E_Pa":ec,"A_m2":area,"I_m4":inertia,"thickness_m":thickness,
            "curvature_thermal_per_m":curvature,"line_load_N_m":q,"fc_Pa":fc,"ft_Pa":float(ft)})
    e=spec.get("eccentricity_fraction",slab["attachment_eccentricity_fraction_of_thickness"])*thickness
    v_unit=np.interp(tc,cfg_c["bond"]["concrete_temperature_c"],cfg_c["bond"]["vertical_pullout_per_knuckle_kip_reference_only"])*KIP
    for old_bond in (r for r in old["terms"] if r["kind"]=="bond"):
        i=old_bond["node_i"]; j=i*sub; count=old_bond["equivalent_knuckles"]
        vertical_dofs=[2*i+1,int(w[j])]
        terms.append(term(f"CONTACT-{i:03d}","contact",vertical_dofs,[-1,1],
            conn["contact_stiffness_per_equivalent_knuckle_N_m"]*count,compression_only=True,station=i))
        if i not in removed_stations:
            terms.append(term(f"H-TIE-{i:03d}","horizontal_tie",[2*i,int(ux[j]),int(theta[j])],[-1,1,e],
                old_bond["k"],cap_abs_N=old_bond["cap_abs_N"],station=i,eccentricity_m=e))
            terms.append(term(f"V-TIE-{i:03d}","vertical_tie",vertical_dofs,[-1,1],
                spec.get("tie_k_N_m",conn["tension_stiffness_per_equivalent_knuckle_N_m"])*count,
                tension_only=True,cap_tension_N=float(v_unit*count*spec.get("vertical_strength_factor",conn["capacity_strength_factor"])),station=i))
    prescribed={2*int(i)+1:float(value) for i,value in spec.get("prescribed_top_vertical",{}).items()}
    return {"terms":terms,"force":force,"prescribed":prescribed,"nodes":old["nodes"],"steel_members":old["members"],
        "size":size,"steel_dofs":ns,"ux":ux,"w":w,"theta":theta,"slab_x_m":np.linspace(0,old["span_m"],n),
        "elements":elements,"span_m":old["span_m"],"panels":p,"subdivisions":sub,"spec":spec,
        "slab_mean_c":tc,"eccentricity_m":e,"removed_stations":list(removed_stations)}


def evaluate_panel(cfg,cfg_c,base,transfer,seats,spec,removed_stations=()):
    model=build_panel(cfg,cfg_c,base,transfer,seats,spec,removed_stations)
    r=solve_terms(model["size"],model["terms"],model["force"],model["prescribed"],cfg["acceptance"]["force_active_set_tolerance_N"])
    byid={t["id"]:t for t in r["terms"]}; limits=[]; fiber_rows=[]; bubble=0.
    for t in r["terms"]:
        n=t["force_N"]; kind=t["kind"]; dcr=0.
        if kind=="horizontal_tie": dcr=abs(n)/t["cap_abs_N"]
        elif kind=="vertical_tie": dcr=max(n,0)/t["cap_tension_N"]
        elif kind=="seat_h": dcr=max(0,n*t["tension_sign"])/t["cap_signed_tension_N"]
        elif kind=="seat_v": dcr=max(0,-n)/t["cap_compression_N"]
        elif kind in ("top_chord","bottom_chord","web"):
            dcr=abs(n)/(t["cap_compression_N"] if n<0 else t["cap_tension_N"])
        t["DCR"]=dcr
        if kind not in ("slab_axial","slab_bending","contact"):
            limits.append({"id":t["id"],"kind":kind,"DCR":dcr,"station":t.get("station")})
    for el in model["elements"]:
        axial=byid[el["axial_id"]]["force_N"]
        recovery=recover_beam(r["u"][el["dofs"]],el["length_m"],el["EI_Nm2"],el["line_load_N_m"],el["curvature_thermal_per_m"])
        bubble+=recovery["bubble_energy_J"]
        for x,moment in zip(recovery["x_m"],recovery["moment_Nm"]):
            sigma_top=axial/el["A_m2"]-moment*el["thickness_m"]/(2*el["I_m4"])
            sigma_bottom=axial/el["A_m2"]+moment*el["thickness_m"]/(2*el["I_m4"])
            dt=max(0.,sigma_top,sigma_bottom)/el["ft_Pa"]
            dc=max(0.,-sigma_top,-sigma_bottom)/el["fc_Pa"]
            limits.extend([{"id":el["id"],"kind":"slab_first_cracking","DCR":dt,"station":None},
                           {"id":el["id"],"kind":"slab_compression_screen","DCR":dc,"station":None}])
            fiber_rows.append({"element_id":el["id"],"x_in_element_m":float(x),"axial_force_N":axial,
                "moment_Nm":float(moment),"sigma_top_Pa":float(sigma_top),"sigma_bottom_Pa":float(sigma_bottom),
                "tensile_DCR":float(dt),"compressive_DCR":float(dc),"ft_hypothesis_Pa":el["ft_Pa"],"fc_hypothesis_Pa":el["fc_Pa"]})
    limits.sort(key=lambda t:(-t["DCR"],t["id"],t["kind"]))
    contact=[t for t in r["terms"] if t["kind"]=="contact"]
    ties=[t for t in r["terms"] if t["kind"]=="vertical_tie"]
    v_seats=[t for t in r["terms"] if t["kind"]=="seat_v"]
    h_seats=[t for t in r["terms"] if t["kind"]=="seat_h"]
    corrected_energy=r["strain_energy_J"]+bubble
    corrected_rhs=r["energy_identity_rhs_J"]+2*bubble
    r.update({"model":model,"fiber_rows":fiber_rows,"limits":limits,"max_DCR":float(limits[0]["DCR"]),
        "slab_bubble_strain_energy_J":bubble,"recovered_total_strain_energy_J":corrected_energy,
        "recovered_energy_identity_residual":abs(2*corrected_energy-corrected_rhs)/max(1.,2*corrected_energy,abs(corrected_rhs)),
        "max_slab_nodal_down_m":float(max(-r["u"][model["w"]])),
        "max_truss_nodal_down_m":float(max(-r["u"][1:model["steel_dofs"]:2])),
        "max_opening_m":max([0.]+[t["generalized_strain"] for t in contact]),
        "max_contact_overlap_m":max([0.]+[-t["generalized_strain"] for t in contact]),
        "compressed_contact_count":sum(t["force_N"]< -1e-5 for t in contact),
        "tension_tie_count":sum(t["force_N"]>1e-5 for t in ties),
        "total_seat_vertical_reaction_N":sum(-t["force_N"] for t in v_seats),
        "actuator_vertical_reaction_N":sum(r["reaction"][d] for d in model["prescribed"]),
        "total_gravity_load_N":-sum(model["force"][model["w"]]),
        "support_horizontal_compression_capacity_unchecked":any(t["force_N"]*t["tension_sign"]< -1e-5 for t in h_seats),
        "support_uplift_unchecked":any(t["force_N"]>1e-5 for t in v_seats),
        "global_energy_credit_J":0.})
    return r


def state_row(path_id,parameter,r,status="WITHIN_UNCRACKED_CHECKED_DOMAIN"):
    s=r["model"]["spec"]
    return {"path_id":path_id,"parameter":float(parameter),"state":status,
        "gravity_factor":s.get("gravity_factor",1.),"steel_c":s.get("steel_c",20.),
        "slab_top_c":s.get("slab_top_c",20.),"slab_bottom_c":s.get("slab_bottom_c",20.),
        "subdivisions":r["model"]["subdivisions"],"eccentricity_m":r["model"]["eccentricity_m"],
        "governing_id":r["limits"][0]["id"],"governing_kind":r["limits"][0]["kind"],
        **{k:r[k] for k in ("max_DCR","max_slab_nodal_down_m","max_truss_nodal_down_m","max_opening_m",
            "max_contact_overlap_m","compressed_contact_count","tension_tie_count","strain_energy_J",
            "slab_bubble_strain_energy_J","recovered_total_strain_energy_J","equilibrium_residual",
            "energy_identity_residual","recovered_energy_identity_residual","total_seat_vertical_reaction_N",
            "actuator_vertical_reaction_N","total_gravity_load_N","support_horizontal_compression_capacity_unchecked",
            "support_uplift_unchecked","global_energy_credit_J")}}


def trace_path(path_id,cfg,cfg_c,base,transfer,seats,make_spec,end,step):
    r=evaluate_panel(cfg,cfg_c,base,transfer,seats,make_spec(0.)); last_p=0.
    history=[state_row(path_id,0.,r)]; bracket=None
    status="PARAMETER_END_WITHIN_CHECKED_DOMAIN_NOT_SAFETY_PROOF"
    if r["max_DCR"]>=1: status="PRELOAD_OUTSIDE_UNCRACKED_DOMAIN_NO_PATH"
    else:
        for raw in np.arange(step,end+step/2,step):
            p=min(float(raw),end); trial=evaluate_panel(cfg,cfg_c,base,transfer,seats,make_spec(p))
            if trial["max_DCR"]>=1:
                lo,hi=last_p,p
                while hi-lo>cfg["acceptance"]["first_event_parameter_tolerance"]:
                    mid=(lo+hi)/2; test=evaluate_panel(cfg,cfg_c,base,transfer,seats,make_spec(mid))
                    if test["max_DCR"]>=1: hi,trial=mid,test
                    else: lo=mid
                last_p,r=hi,trial; bracket=[lo,hi]
                status="FIRST_LIMIT_ENDS_PREDICTOR_NOT_FLOOR_FAILURE"
                history.append(state_row(path_id,last_p,r,status)); break
            last_p,r=p,trial; history.append(state_row(path_id,p,r))
    history[-1]["state"]=status
    release=None
    if status.startswith("FIRST") and r["limits"][0]["kind"] in ("horizontal_tie","vertical_tie"):
        stations=sorted(set(t["station"] for t in r["limits"] if t["kind"] in ("horizontal_tie","vertical_tie") and t["DCR"]>=1-1e-6))
        release={"path_id":path_id,"parameter":last_p,"removed_stations":stations,
            "pre_discrete_strain_energy_J":r["strain_energy_J"],"post_state":None,
            "deleted_tie_stored_energy_J":sum(t["strain_energy_J"] for t in r["terms"] if t["kind"] in ("horizontal_tie","vertical_tie") and t["station"] in stations),
            "fracture_dynamic_dissipation_J":None,"contact_preserved":True}
        try:
            post=evaluate_panel(cfg,cfg_c,base,transfer,seats,make_spec(last_p),stations)
            label="DAMAGED_SAME_LOAD_STATIC_DIAGNOSTIC"
            if post["max_DCR"]>=1: label+="_OUTSIDE_PREDICTOR_DOMAIN"
            release["post_state"]=state_row(path_id,last_p,post,label)
        except UnresolvedEquilibrium as error: release["unresolved_static_status"]=str(error)
    summary={**history[-1],"first_event_bracket":bracket,"point_count":len(history)}
    return summary,history,r,release
