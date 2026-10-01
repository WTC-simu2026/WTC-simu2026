"""Small-displacement compression-only slab / truss pair prototype (SI).

No inertia, postbuckling, slab bending or historical conclusion. The strain
energy check is an algebraic state identity, NOT a thermal/dynamic ledger.
"""
from __future__ import annotations

import math
import numpy as np
from v11a_component_model import IN, KIP, KSI, PSF, opposed_angles, steel, warren_geometry


class UnresolvedEquilibrium(RuntimeError):
    pass


def term(identifier, kind, dofs, b, k, e0=0., compression_only=False, **metadata):
    if k <= 0 or not math.isfinite(k):
        raise ValueError("Nonpositive/nonfinite active stiffness")
    return {"id": identifier, "kind": kind, "dofs": list(dofs), "b": list(b),
            "k": float(k), "e0": float(e0), "compression_only": compression_only, **metadata}


def solve_terms(size, terms, force, prescribed=None, tolerance_N=1e-5):
    """Convex piecewise quadratic equilibrium; no tension in slab terms.

    N=k*(B.u-e0); compression-only terms have N=k*min(B.u-e0,0).
    A lost/free degree is reported, never hidden by an artificial spring.
    """
    prescribed = prescribed or {}
    fixed = np.array(sorted(prescribed), dtype=int)
    free = np.array([i for i in range(size) if i not in prescribed], dtype=int)
    force = np.asarray(force, dtype=float)
    if force.shape != (size,) or any(not 0 <= i < size for i in prescribed):
        raise ValueError("Invalid force or prescribed degree")
    active = np.ones(len(terms), dtype=bool)
    seen = set()
    for iteration in range(100):
        key = tuple(active)
        if key in seen:
            raise UnresolvedEquilibrium("COMPRESSION_ACTIVE_SET_CYCLE_NO_PHYSICAL_VERDICT")
        seen.add(key)
        matrix = np.zeros((size, size))
        thermal = np.zeros(size)
        for on, item in zip(active, terms):
            if not on:
                continue
            d, b, k = np.array(item["dofs"]), np.array(item["b"]), item["k"]
            matrix[np.ix_(d, d)] += k * np.outer(b, b)
            thermal[d] += k * item["e0"] * b
        u = np.zeros(size)
        for d, value in prescribed.items():
            u[d] = value
        if len(free):
            kff = matrix[np.ix_(free, free)]
            diagonal = np.diag(kff)
            if np.any(diagonal <= 0):
                raise UnresolvedEquilibrium("DISCONNECTED_DOF_NO_PHYSICAL_COLLAPSE_VERDICT")
            scale = 1. / np.sqrt(diagonal)
            normalized = scale[:, None] * kff * scale[None, :]
            # Explicit rank gate prevents a singular panel being accepted by roundoff.
            eigenvalues = np.linalg.eigvalsh(normalized)
            if eigenvalues[0] <= 1e-11:
                raise UnresolvedEquilibrium("RANK_DEFICIENT_STATIC_SYSTEM_NO_PHYSICAL_COLLAPSE_VERDICT")
            rhs = (force + thermal - matrix @ u)[free]
            u[free] = scale * np.linalg.solve(normalized, scale * rhs)
        extensions = np.array([np.dot(t["b"], u[t["dofs"]]) - t["e0"] for t in terms])
        trial_forces = extensions * np.array([t["k"] for t in terms])
        next_active = active.copy()
        for i, item in enumerate(terms):
            if item["compression_only"]:
                if active[i] and trial_forces[i] > tolerance_N:
                    next_active[i] = False
                elif not active[i] and trial_forces[i] < -tolerance_N:
                    next_active[i] = True
        if np.array_equal(active, next_active):
            break
        active = next_active
    else:
        raise UnresolvedEquilibrium("ACTIVE_SET_ITERATION_LIMIT")
    # Audit using the unilateral law itself, not just the active linear matrix.
    internal = np.zeros(size)
    rows = []
    for item, extension in zip(terms, extensions):
        elastic = min(extension, 0.) if item["compression_only"] else extension
        axial = item["k"] * elastic
        energy = .5 * item["k"] * elastic**2
        internal[item["dofs"]] += axial * np.array(item["b"])
        rows.append({**item, "extension_m": float(extension), "force_N": float(axial),
                     "strain_energy_J": float(energy),
                     "state": "OPEN_ZERO_TENSION" if item["compression_only"] and extension > 0 else "ELASTIC"})
    reaction = internal - force
    energy = sum(r["strain_energy_J"] for r in rows)
    eigen_work = sum(r["force_N"] * r["e0"] for r in rows)
    identity_rhs = float(u @ force + u[fixed] @ reaction[fixed] - eigen_work)
    force_scale = max(1., float(np.sum(np.abs(force))), float(np.sum(np.abs(internal))))
    equilibrium_residual = max(np.abs(reaction[free]), default=0.) / force_scale
    energy_residual = abs(2*energy - identity_rhs) / max(1., 2*energy, abs(identity_rhs))
    return {"u": u, "reaction": reaction, "terms": rows, "strain_energy_J": energy,
            "state_energy_identity_rhs_J": identity_rhs,
            "equilibrium_residual": float(equilibrium_residual),
            "energy_identity_residual": float(energy_residual), "active_set_iterations": iteration+1}


def build_panel(cfg, base, transfer, seats, spec, removed=()):
    panel, bay, bond = cfg["panel"], base["floor_bay"], cfg["bond"]
    p = int(spec.get("panels", panel["panels"]))
    span = panel["span_in"] * IN
    nodes, members = warren_geometry(span, bay["nominal_depth_model_in"]*IN, p)
    count = panel["symmetric_trusses_per_pair"]
    size_steel = 2*len(nodes)
    size = size_steel + p+1
    ts, tc, tb = [spec.get(k, 20.) for k in ("steel_c", "slab_c", "support_c")]
    if not 20 <= tc <= 600 or not 20 <= tb <= 600:
        raise ValueError("V11C concrete/support comparison domain is 20..600 C")
    young, ky = steel(ts, transfer)
    fy = panel["fy_ksi"]*KSI*ky
    diameter = panel["web_diameter_in"]
    shapes = {kind: opposed_angles(bay[kind+"_angle_in"], diameter)
              for kind in ("top_chord", "bottom_chord")}
    shapes["web"] = (math.pi*(diameter*IN)**2/4, math.pi*(diameter*IN)**4/64)
    terms = []
    for index, (i, j, kind) in enumerate(members):
        delta = nodes[j]-nodes[i]
        length = float(np.linalg.norm(delta))
        c, s = delta/length
        area, imin = [value*count for value in shapes[kind]]
        py, pe = area*fy, math.pi**2*young*imin/length**2
        if kind == "top_chord" and spec.get("ideal_lateral_bracing", panel["top_chord_laterally_braced"]):
            pe = py  # Explicit ideal diagnostic only; never inferred from bond stiffness.
        terms.append(term(f"STEEL-{index+1:03d}", kind, [2*i,2*i+1,2*j,2*j+1], [-c,-s,c,s],
            young*area/length, panel["steel_expansion_per_K"]*(ts-20)*length,
            cap_tension_N=py, cap_compression_N=min(py,pe), length_m=length,
            node_i=i, node_j=j, nominal_limit_only=True))
    concrete = bay["concrete_hypotheses"]
    ec = concrete["elastic_modulus_20c_ksi"]*KSI*np.interp(tc,concrete["temperature_knots_c"],concrete["modulus_ratios"])
    fc = concrete["compression_strength_20c_ksi"]*KSI*np.interp(tc,concrete["temperature_knots_c"],concrete["compression_ratios"])
    ac = count*bay["width_per_single_truss_in"]*bay["equivalent_slab_thickness_in"]*IN**2
    dx = span/p
    for i in range(p):
        terms.append(term(f"SLAB-{i+1:03d}", "slab", [size_steel+i,size_steel+i+1], [-1,1],
            ec*ac/dx, panel["concrete_expansion_per_K"]*(tc-20)*dx, True,
            cap_compression_N=fc*ac, length_m=dx, node_i=i, node_j=i+1))
    unit_capacity = np.interp(tc,bond["concrete_temperature_c"],bond["shear_per_knuckle_kip"])*KIP
    for i in range(p+1):
        identifier = f"BOND-{i:03d}"
        if identifier in removed:
            continue
        tributary = dx*(.5 if i in (0,p) else 1.)
        equivalent_count = count*tributary/(panel["nominal_knuckle_spacing_in"]*IN)
        terms.append(term(identifier,"bond",[2*i,size_steel+i],[-1,1],
            spec.get("bond_k_N_m",bond["reference_stiffness_N_m"])*equivalent_count,
            cap_abs_N=unit_capacity*equivalent_count*spec.get("bond_strength_factor",1.),
            equivalent_knuckles=equivalent_count, tributary_m=tributary, node_i=i,
            breakable_horizontal_only=True, capacity_temperature_c=tc))
    kv = spec.get("kv_N_m",panel["vertical_support_stiffness_pair_N_m"])
    kh = spec.get("kh_N_m",panel["horizontal_support_stiffness_pair_N_m"])
    for side, i, tension_sign in (("exterior",0,1),("interior",p,-1)):
        detail = panel["seat_detail_"+side]
        capv = np.interp(tb,seats["temperatures_c"],seats[side+"_vertical_capacity_kip"][detail])*KIP
        hdata = (seats["interior_horizontal_tension_capacity_kip"] if side=="interior"
                 else base["new_source_transcription"]["exterior_horizontal_tension_capacity_kip"][detail])
        caph = np.interp(tb,seats["temperatures_c"],hdata)*KIP
        terms.append(term("SEAT-V-"+side,"seat_v",[2*i+1],[1],kv,
            spec.get(side+"_anchor_y_m",0.), cap_compression_N=float(capv), side=side, detail=detail))
        if side=="exterior" or spec.get("horizontal_mode","roller")=="restrained":
            terms.append(term("SEAT-H-"+side,"seat_h",[2*i],[1],kh,
                spec.get("right_anchor_x_m",0.) if side=="interior" else 0.,
                cap_signed_tension_N=float(caph), tension_sign=tension_sign, side=side, detail=detail))
    force = np.zeros(size)
    line_load = count*bay["width_per_single_truss_in"]*IN*panel["load_psf"]*PSF*spec.get("gravity_factor",1.)
    for i in range(p+1):
        force[2*i+1] = -line_load*dx*(.5 if i in (0,p) else 1.)
    return {"nodes": nodes, "members": members, "size": size, "steel_dofs": size_steel,
            "terms": terms, "force": force, "spec": spec, "span_m": span, "panels": p}


def evaluate_panel(cfg, base, transfer, seats, spec, removed=()):
    model = build_panel(cfg,base,transfer,seats,spec,removed)
    result = solve_terms(model["size"],model["terms"],model["force"],
                         tolerance_N=cfg["acceptance"]["active_set_force_tolerance_N"])
    limits = []
    for row in result["terms"]:
        n = row["force_N"]
        if row["kind"] == "bond":
            demand, cap = abs(n),row["cap_abs_N"]
        elif row["kind"] == "seat_h":
            demand, cap = max(0.,n*row["tension_sign"]),row["cap_signed_tension_N"]
        elif n < 0:
            demand, cap = -n,row.get("cap_compression_N",math.inf)
        else:
            demand, cap = n,row.get("cap_tension_N",math.inf)
        row["DCR"] = demand/cap
        limits.append({"id":row["id"],"kind":row["kind"],"DCR":row["DCR"]})
    limits.sort(key=lambda r:(-r["DCR"],r["id"]))
    vertical = [r for r in result["terms"] if r["kind"]=="seat_v"]
    horizontal = [r for r in result["terms"] if r["kind"]=="seat_h"]
    max_displacement = max(abs(result["u"][:model["steel_dofs"]]), default=0.)
    uplift = max([r["force_N"] for r in vertical], default=0.)
    result.update({"model":model, "limits":limits, "max_DCR":limits[0]["DCR"],
        "max_down_m":float(max(-result["u"][1:model["steel_dofs"]:2])),
        "max_slip_m":max(abs(r["extension_m"]) for r in result["terms"] if r["kind"]=="bond"),
        "vertical_pair_reaction_N":float(sum(-r["force_N"] for r in vertical)),
        "left_horizontal_reaction_N":float(-next(r["force_N"] for r in horizontal if r["side"]=="exterior")),
        "right_horizontal_reaction_N":float(-next((r["force_N"] for r in horizontal if r["side"]=="interior"),0.)),
        "support_compression_capacity_unchecked":any(r["force_N"]*r["tension_sign"] < -1e-5 for r in horizontal),
        "unsupported_vertical_uplift":bool(uplift > 1e-5),
        "large_displacement_warning":bool(max_displacement > model["span_m"]/100),
        "removed_horizontal_bonds":list(removed)})
    return result


def state_row(path_id, parameter, result, state="BELOW_FIRST_NOMINAL_LIMIT"):
    spec = result["model"]["spec"]
    return {"path_id":path_id,"parameter":float(parameter),"state":state,
        "gravity_factor":spec.get("gravity_factor",1.),"steel_c":spec.get("steel_c",20.),
        "slab_c":spec.get("slab_c",20.),"support_c":spec.get("support_c",20.),
        "right_anchor_x_m":spec.get("right_anchor_x_m",0.),
        **{k:result[k] for k in ("max_DCR","max_down_m","max_slip_m","strain_energy_J",
            "equilibrium_residual","energy_identity_residual","vertical_pair_reaction_N",
            "left_horizontal_reaction_N","right_horizontal_reaction_N",
            "support_compression_capacity_unchecked","unsupported_vertical_uplift","large_displacement_warning")},
        "governing_id":result["limits"][0]["id"],"governing_kind":result["limits"][0]["kind"],
        "open_slab_segments":sum(t["state"]=="OPEN_ZERO_TENSION" for t in result["terms"]),
        "global_energy_credit_J":0.}


def trace_path(path_id, cfg, base, transfer, seats, make_spec, end, step):
    """Bracket first event on a declared monotone parameter path.

    A constant force ramp at cold has proportional demands; varying-temperature
    crossings are step-bracketed then bisected. No claim about unsampled peaks.
    """
    history = []
    last_parameter = 0.
    last = evaluate_panel(cfg,base,transfer,seats,make_spec(0.))
    history.append(state_row(path_id,0.,last))
    terminal = "PARAMETER_END_BELOW_CHECKED_LIMITS_NOT_PROOF_OF_SAFETY"
    bracket = None
    if last["max_DCR"] >= 1:
        terminal = "PRELOAD_ALREADY_AT_OR_ABOVE_FIRST_LIMIT_NO_PATH"
    else:
        for raw in np.arange(step,end+step/2,step):
            value = min(float(raw),end)
            trial = evaluate_panel(cfg,base,transfer,seats,make_spec(value))
            if trial["max_DCR"] >= 1:
                low,high = last_parameter,value
                for _ in range(50):
                    if high-low <= cfg["acceptance"]["first_event_parameter_bracket_tolerance"]:
                        break
                    mid = (low+high)/2
                    candidate = evaluate_panel(cfg,base,transfer,seats,make_spec(mid))
                    if candidate["max_DCR"] >= 1:
                        high,trial = mid,candidate
                    else:
                        low,last = mid,candidate
                bracket = [low,high]
                last_parameter,last = high,trial
                terminal = "FIRST_NOMINAL_LIMIT_NO_POST_MEMBER_CONTINUATION"
                history.append(state_row(path_id,high,last,terminal))
                break
            last_parameter,last = value,trial
            history.append(state_row(path_id,value,last))
    history[-1]["state"] = terminal
    release = None
    if terminal.startswith("FIRST") and last["limits"][0]["kind"] == "bond":
        # Damage at a first bond event only, not past an earlier member threshold.
        broken = [r["id"] for r in last["limits"] if r["kind"]=="bond" and r["DCR"]>=1-1e-6]
        removed_energy = sum(r["strain_energy_J"] for r in last["terms"] if r["id"] in broken)
        release = {"path_id":path_id,"parameter":last_parameter,"removed_ids":broken,
            "pre_strain_energy_J":last["strain_energy_J"],"removed_spring_stored_energy_J":removed_energy,
            "dynamic_fracture_dissipation_J":None,"global_energy_credit_J":0.,"post_state":None}
        try:
            post = evaluate_panel(cfg,base,transfer,seats,make_spec(last_parameter),broken)
            post_state = "DAMAGED_SAME_LOAD_STATIC_DIAGNOSTIC"
            if post["max_DCR"] >= 1:
                post_state += "_FURTHER_LIMIT_EXCEEDED_NOT_VALID_CONTINUATION"
            release["post_state"] = state_row(path_id,last_parameter,post,post_state)
            release["post_strain_energy_J"] = post["strain_energy_J"]
            release["post_minus_pre_strain_energy_J_NOT_DISSIPATION"] = post["strain_energy_J"]-last["strain_energy_J"]
        except UnresolvedEquilibrium as error:
            release["post_status"] = str(error)
    summary = {**history[-1],"point_count":len(history),"first_event_bracket":bracket,
               "bond_k_N_m":make_spec(0.).get("bond_k_N_m",cfg["bond"]["reference_stiffness_N_m"]),
               "bond_strength_factor":make_spec(0.).get("bond_strength_factor",1.),
               "horizontal_mode":make_spec(0.).get("horizontal_mode","roller")}
    return summary,history,last,release
