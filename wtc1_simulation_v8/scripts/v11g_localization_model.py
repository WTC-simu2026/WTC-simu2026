"""Cold localized series bar and equilibrium-only recovery; V11F is never edited."""
from __future__ import annotations
import math
import numpy as np
import v11e_section_model as material


class Unresolved(RuntimeError):
    pass


def material_inputs(section_cfg):
    c = section_cfg["concrete"]
    return {"original": {k: c[k] for k in ("E20_ksi", "fc20_ksi", "ft20_MPa", "fracture_energy_J_m2")},
            "SI": {"E_Pa": c["E20_ksi"] * material.KSI, "fc_Pa": c["fc20_ksi"] * material.KSI,
                   "ft_Pa": c["ft20_MPa"] * 1e6, "Gf_J_m2": c["fracture_energy_J_m2"]},
            "conversion": {"Pa_per_ksi": material.KSI, "Pa_per_MPa": 1e6},
            "status": "Inherited hypothetical concrete, not measured WTC fracture data"}


def concrete(si, h):
    return material.Concrete(si["E_Pa"], si["ft_Pa"], si["fc_Pa"], si["Gf_J_m2"], h)


def solve_opening(mat, old, opening, options):
    """Scalar monotone compatibility in opening, even when end displacement snaps back."""
    if not math.isfinite(opening) or opening < 0:
        raise ValueError("Nonnegative finite tensile opening required")
    if opening == 0:
        eps = float(old["eps"][0]) if old["r"][0] <= mat.e0 else 0.
        return material.concrete_trial(mat, old, [eps]), 0
    lo = 0.
    hi = max(mat.ef, opening / mat.Lch + mat.e0)
    eps = min(hi, max(mat.e0, float(old["eps"][0])))
    tolerance = options["opening_tolerance_fraction_wc"] * (2 * mat.Gf / mat.ft)
    for iteration in range(options["maximum_iterations"]):
        trial = material.concrete_trial(mat, old, [eps])
        residual = mat.Lch * (eps - float(trial["stress"][0]) / mat.E) - opening
        if abs(residual) <= tolerance:
            return trial, iteration + 1
        if residual > 0:
            hi = eps
        else:
            lo = eps
        tangent = mat.Lch * (1 - float(trial["tangent"][0]) / mat.E)
        proposal = eps - residual / tangent if tangent > 0 else math.nan
        eps = proposal if lo < proposal < hi else (lo + hi) / 2
    raise Unresolved("OPENING_COMPATIBILITY_NOT_CONVERGED; no trial committed")


def localized_bar(cfg, si, length, cells, path, step_factor=1.):
    if cfg["solver"]["temperature_c"] != 20.:
        raise ValueError("V11G benchmark is cold only")
    if cells < 3 or cells % 2 != 1 or cfg["bar"]["crack_position_fraction"] != .5:
        raise ValueError("Odd mesh and central prescribed crack required")
    if step_factor <= 0 or not math.isfinite(step_factor):
        raise ValueError("Positive step factor required")
    area = cfg["bar"]["area_m2"]
    h = length / cells
    mat = concrete(si, h)
    wc = 2 * mat.Gf / mat.ft
    band = cells // 2
    identifier = f"L{length:g}_N{cells}_{path.upper()}"
    old = material.zero_concrete(1)
    history = []
    external = 0.
    external_abs = 0.
    old_P = old_delta = 0.
    max_opening = 0.

    def commit(state, phase, parameter, opening, iterations, analytical_stress):
        nonlocal old, old_P, old_delta, external, external_abs, max_opening
        sigma = float(state["stress"][0])
        strains = np.full(cells, sigma / mat.E)
        strains[band] = state["eps"][0]
        u = np.r_[0., np.cumsum(strains * h)]
        actual_strain = np.diff(u) / h
        forces = area * mat.E * actual_strain
        forces[band] = area * sigma
        force = area * sigma
        nodal = np.zeros(cells + 1)
        nodal[:-1] -= forces
        nodal[1:] += forces
        nodal[0] += force
        nodal[-1] -= force
        bulk_U = .5 * sigma**2 / mat.E * area * (length - h)
        stored = bulk_U + float(state["stored"][0]) * area * h
        dissipated = float(state["dissipated"][0]) * area * h
        internal_work = bulk_U + float(state["work"][0]) * area * h
        delta = float(u[-1])
        dw = .5 * (force + old_P) * (delta - old_delta)
        external += dw
        external_abs += abs(dw)
        max_opening = max(max_opening, opening)
        expected_delta = length * analytical_stress / mat.E + opening
        row = {"phase": phase, "phase_parameter": parameter, "opening_m": opening,
               "max_opening_m": max_opening, "stress_Pa": sigma, "force_N": force, "end_displacement_m": delta,
               "band_strain": float(state["eps"][0]), "band_damage": float(state["damage"][0]), "band_max_strain": float(state["r"][0]),
               "bulk_stored_J": bulk_U, "stored_J": stored, "dissipated_J": dissipated, "internal_work_J": internal_work,
               "external_work_J": external, "external_absolute_work_J": external_abs,
               "exact_energy_error_relative_AGf": abs(internal_work-stored-dissipated)/(area*mat.Gf),
               "external_energy_error_relative_AGf": abs(external-internal_work)/(area*mat.Gf),
               "force_error_relative_Aft": abs(sigma-analytical_stress)/mat.ft,
               "displacement_error_relative_wc": abs(delta-expected_delta)/wc,
               "equilibrium_relative_Aft": float(np.max(abs(nodal)))/(area*mat.ft),
               "opening_error_relative_wc": abs(h*(float(state["eps"][0])-sigma/mat.E)-opening)/wc,
               "iterations": iterations, "global_energy_credit_J": 0.}
        history.append(row)
        old, old_P, old_delta = state, force, delta

    steps = math.ceil(cfg["bar"]["elastic_loading_steps"] / step_factor)
    for t in np.linspace(0., 1., steps + 1):
        state = material.concrete_trial(mat, old, [mat.e0 * t])
        commit(state, "elastic", float(t), 0., 0, mat.ft * t)
    vertices = cfg["bar"][path + "_opening_fractions"]
    for segment, (a, b) in enumerate(zip(vertices[:-1], vertices[1:], strict=True)):
        count = math.ceil(cfg["bar"]["steps_per_opening_segment"] / step_factor)
        for parameter in np.linspace(0., 1., count + 1)[1:]:
            opening = wc * (a + (b-a) * parameter)
            state, iterations = solve_opening(mat, old, opening, cfg["solver"])
            reference_max = max(max_opening, opening)
            envelope = mat.ft * max(0., 1-reference_max/wc)
            expected = envelope * opening / reference_max if reference_max > 0 else mat.ft
            commit(state, f"opening_{segment}", float(parameter), opening, iterations, expected)
    final_sigma = float(old["stress"][0])
    strains = np.full(cells, final_sigma / mat.E)
    strains[band] = old["eps"][0]
    u = np.r_[0., np.cumsum(strains * h)]
    Lcrit = mat.E * wc / mat.ft
    maxima = {k: max(r[k] for r in history) for k in history[0] if "error_relative" in k or k == "equilibrium_relative_Aft"}
    summary = {"id": identifier, "length_m": length, "area_m2": area, "cells": cells, "path": path,
               "band_index": band, "band_center_m": (band+.5)*h, "band_length_m": h,
               "critical_opening_m": wc, "critical_bar_length_m": Lcrit, "expected_snapback": length > Lcrit,
               "observed_postpeak_negative_delta_steps": sum(b["end_displacement_m"] < a["end_displacement_m"]-1e-14
                   for a,b in zip(history[:-1],history[1:],strict=True) if b["phase"]=="opening_0"),
               "state_count": len(history), "final_dissipation_J": history[-1]["dissipated_J"],
               "target_single_fracture_energy_J": area * mat.Gf,
               "final_force_N": history[-1]["force_N"], "maxima": maxima, "global_energy_credit_J": 0.}
    return {"summary": summary, "history": history, "final_node_displacement_m": u.tolist(), "final_cell_strain": strains.tolist()}


def uniform_negative_control(cfg, si):
    rows = []
    length = cfg["bar"]["lengths_m"][0]
    area = cfg["bar"]["area_m2"]
    for cells in cfg["bar"]["cells"]:
        for gauss in (1, 2):
            count = cells * gauss
            h = length / count
            mat = concrete(si, h)
            state = material.zero_concrete(count)
            previous_delta = previous_force = work = 0.
            # Include the elastic/softening corner explicitly; exact trapezoids for this branch.
            for eps in (0., mat.e0, mat.ef, mat.ef*1.1):
                trial = material.concrete_trial(mat, state, np.full(count, eps))
                force = float(np.mean(trial["stress"])) * area
                delta = eps * length
                work += .5 * (force + previous_force) * (delta - previous_delta)
                state = trial
                previous_delta, previous_force = delta, force
            dissipation = float(np.sum(state["dissipated"])) * area * h
            rows.append({"cells": cells, "gauss_per_cell": gauss, "simultaneous_numerical_bands": count,
                         "length_m": length, "Lch_m": h, "D_J": dissipation, "external_work_J": work,
                         "one_crack_target_J": area*mat.Gf, "expected_multi_band_energy_J": count*area*mat.Gf,
                         "ratio_to_one_crack_energy": dissipation/(area*mat.Gf),
                         "single_crack_interpretation": "REJECTED_MULTIPLE_SIMULTANEOUS_BANDS",
                         "scope": "Prescribed homogeneous strain branch; no spontaneous localization prediction",
                         "global_energy_credit_J": 0.})
    return rows


def equilibrated_resultants(x, q, point_loads):
    axial = moment = 0.
    for p in point_loads:
        if p["x_m"] <= x:
            axial -= p["Fx_N"]
            moment += p["Fy_N"] * (x-p["x_m"]) - p["couple_Nm"]
    return axial, moment + q*x*x/2


def panel_recovery(data, label, eccentricity_fraction, point_gate):
    """Reconstruct slab-only statics from actual interfaces, without a V11F import."""
    summary, inv = data["summary"], data["inventory"]
    sections, terms = data["sections"], data["terms"]
    L, sub = inv["span_m"], inv["subdivisions"]
    n = inv["slab_nodes"]
    dx = L / (n-1)
    station_spacing = L / (inv["contact_stations"]-1)
    e = inv["section"]["equivalent_thickness_m"] * eccentricity_fraction
    q = -float(summary["gravity_load_N"]) / L
    points = []
    internal = np.zeros((n,3))
    absolute = np.zeros_like(internal)
    external = np.zeros_like(internal)
    for r in terms:
        if r["kind"] not in ("contact", "vertical_tie", "horizontal_tie"):
            continue
        station = int(r["station"])
        node = station * sub
        force = float(r["force_N"])
        px = -force if r["kind"]=="horizontal_tie" else 0.
        py = -force if r["kind"]!="horizontal_tie" else 0.
        couple = -e*force if r["kind"]=="horizontal_tie" else 0.
        points.append({"id":r["id"],"x_m":station*station_spacing,"Fx_N":px,"Fy_N":py,"couple_Nm":couple})
        value = np.array([px,py,couple])
        external[node] += value
    if summary["kind"].startswith("slab_"):
        x = inv["slab_actuator_x_m"]
        node = round(x/dx)
        force = float(summary["actuator_reaction_N"])
        points.append({"id":"SLAB_ACTUATOR","x_m":x,"Fx_N":0.,"Fy_N":force,"couple_Nm":0.})
        external[node,1] += force
    for el in range(n-1):
        external[el,1] += q*dx/2
        external[el+1,1] += q*dx/2
        external[el,2] += q*dx*dx/12
        external[el+1,2] -= q*dx*dx/12
    rows = []
    for r in sections:
        el, x, weight = int(r["element"]), float(r["x_m"]), float(r["weight_m"])
        N, M = float(r["N_N"]), float(r["M_Nm"])
        a = (x-el*dx)/dx
        bv = np.array([(12*a-6)/dx**2,(6*a-4)/dx,(6-12*a)/dx**2,(6*a-2)/dx])
        local = weight*np.array([-N/dx,bv[0]*M,bv[1]*M,N/dx,bv[2]*M,bv[3]*M]).reshape(2,3)
        internal[el:el+2] += local
        absolute[el:el+2] += abs(local)
        nb,mb = equilibrated_resultants(x,q,points)
        rows.append({"point":int(r["point"]),"element":el,"x_m":x,"weight_m":weight,
                     "N_constitutive_N":N,"N_equilibrated_N":nb,"N_error_N":N-nb,
                     "M_constitutive_Nm":M,"M_equilibrated_Nm":mb,"M_error_Nm":M-mb})
    force_scale = max(1.,sum(abs(p["Fx_N"])+abs(p["Fy_N"]) for p in points),abs(q*L))
    moment_scale = max(1.,sum(abs(p["Fy_N"]*p["x_m"])+abs(p["couple_Nm"]) for p in points),abs(q*L*L/2))
    FX = sum(p["Fx_N"] for p in points)
    FY = sum(p["Fy_N"] for p in points)+q*L
    MOM = sum(p["Fy_N"]*p["x_m"]+p["couple_Nm"] for p in points)+q*L*L/2
    nscale = max(1.,max(abs(r["N_equilibrated_N"]) for r in rows))
    mscale = max(1.,max(abs(r["M_equilibrated_Nm"]) for r in rows))
    ne = max(abs(r["N_error_N"]) for r in rows)
    me = max(abs(r["M_error_Nm"]) for r in rows)
    nrel, mrel = ne/nscale, me/mscale
    weak = float(np.max(abs(internal-external)/np.maximum(1.,np.maximum(absolute,abs(external)))))
    metrics = {"case_id":summary["id"],"run":label,"subdivisions":sub,"gauss_points":len(rows),
               "terminal":summary["terminal"],"actuator_offset_m":summary["actuator_offset_m"],
               "has_cracking":summary["cracked_sections"]>0,"weak_nodal_relative":weak,
               "slab_horizontal_error_N":FX,"slab_vertical_error_N":FY,"slab_moment_error_Nm":MOM,
               "slab_global_force_relative":max(abs(FX),abs(FY))/force_scale,
               "slab_global_moment_relative":abs(MOM)/moment_scale,
               "N_max_absolute_error_N":ne,"M_max_absolute_error_Nm":me,
               "N_peak_equilibrated_N":nscale,"M_peak_equilibrated_Nm":mscale,
               "N_max_relative":nrel,"M_max_relative":mrel,
               "N_weighted_rms_error_N":math.sqrt(sum(r["weight_m"]*r["N_error_N"]**2 for r in rows)/L),
               "M_weighted_rms_error_Nm":math.sqrt(sum(r["weight_m"]*r["M_error_Nm"]**2 for r in rows)/L),
               "uniform_q_linear_M_interpolation_endpoint_gap_Nm":abs(q)*dx*dx/12,
               "moment_sampling_caveat":"With constant q and no interior concentrated action, the quadratic equilibrium moment and its two-Gauss linear interpolant coincide at both Gauss points. Their endpoint gap is abs(q)*dx^2/12. This extra diagnostic is not a recovered nonlinear material stress or a change to the declared sampled gate.",
               "sampled_pointwise_gate_pass":nrel<=point_gate["panel_fine_pointwise_N_relative"] and mrel<=point_gate["panel_fine_pointwise_M_relative"],
               "global_energy_credit_J":0.}
    return {"summary":metrics,"point_loads_on_slab":points,"uniform_q_N_m":q,"point_comparisons":rows,
            "nodal_residual_ux_w_theta":(internal-external).tolist(),
            "warning":"Equilibrated recovered resultants are diagnostic only, not constitutively compatible replacement stresses or new energy/capacity."}
