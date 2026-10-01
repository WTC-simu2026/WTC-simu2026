"""Explicit component prototypes. No global collapse or as-built claim.

SI internally; native source dimensions remain in the exported inventory.
The small-displacement bay solver stops its reported load path at a first
nominal limit. Trial service-load displacements beyond that limit are not a
post-buckling or post-fracture solution.
"""
from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np

IN = 0.0254
FT = 0.3048
KIP = 4448.2216152605
KSI = KIP / IN**2
PSF = (KIP / 1000.0) / FT**2


def steel(temp: float, transfer: dict) -> tuple[float, float]:
    if not 20.0 <= temp <= 600.0:
        raise ValueError("V11A steel modulus is restricted to 20..600 C")
    material = transfer["steel_temperature_model"]
    fy = material["yield_ratio_parameters"]
    ep = material["young_modulus_parameters"]
    def ratio(t: float) -> float:
        return (1.0 - fy["A2"]) * math.exp(-0.5 * (
            (t / fy["s1_c"]) ** fy["m1"] + (t / fy["s2_c"]) ** fy["m2"]
        )) + fy["A2"]
    young = (ep["e0"] + ep["e1"] * temp + ep["e2"] * temp**2 + ep["e3"] * temp**3) * 1e9
    return young, ratio(temp) / ratio(20.0)


def box_shape(segment: dict) -> dict:
    p1, p2 = segment["plates"]
    t1, w1 = p1["t_in"], p1["w_in"]
    t2, h = p2["t_in"], p2["w_in"]
    w = w1 + 2 * t2
    area = 2 * (t1 * w1 + t2 * h)
    ix = 2 * (w1 * t1**3 / 12 + w1 * t1 * ((h - t1) / 2)**2 + t2 * h**3 / 12)
    iy = 2 * (t1 * w1**3 / 12 + h * t2**3 / 12 + h * t2 * ((w - t2) / 2)**2)
    if not math.isclose(area, segment["gross_area_in2"], rel_tol=1e-12):
        raise ValueError("Box plate area does not reproduce the cached transcription")
    return {"area_in2": area, "ix_in4": ix, "iy_in4": iy,
            "depth_in": h, "flange_width_in": w,
            "selection_status": "DERIVED_FROM_TRANSCRIBED_TYPE_300_PLATES"}


def section_si(shape: dict) -> dict:
    return {"area_m2": shape["area_in2"] * IN**2,
            "ix_m4": shape["ix_in4"] * IN**4,
            "iy_m4": shape["iy_in4"] * IN**4}


def column_screen(area: float, imin: float, length: float, k: float,
                  young: float, fy: float) -> tuple[float, float, float]:
    if min(area, imin, length, k, young, fy) <= 0:
        raise ValueError("Non-positive column parameter")
    py = area * fy
    pe = math.pi**2 * young * imin / (k * length)**2
    ratio = py / pe
    pcurve = py * 0.658**ratio if ratio <= 2.25 else 0.877 * pe
    return py, pe, pcurve


def beam_law(shape: dict, length: float, temp: float, factor: float,
             cfg: dict, transfer: dict) -> dict:
    young, ky = steel(temp, transfer)
    fy = cfg["fy_reference_ksi"] * KSI * ky
    bf, tf, tw, d = [shape[k] * IN for k in (
        "flange_width_in", "flange_thickness_in", "web_thickness_in", "depth_in")]
    hw = d - 2 * tf
    ix = shape["ix_in4"] * IN**4
    zx = bf * tf * (d - tf) + tw * hw**2 / 4
    my, mp = fy * ix / (d / 2), fy * zx
    shear = fy / math.sqrt(3) * tw * hw
    stiffness = 12 * young * ix / length**3
    force = min(2 * factor * mp / length, shear)
    du = cfg["relative_rotation_at_fracture_rad"] * length
    dy = force / stiffness
    tangent = cfg["post_yield_tangent_ratio"] * stiffness
    if du <= dy:
        peak = stiffness * du
        energy = 0.5 * stiffness * du**2
    else:
        peak = force + tangent * (du - dy)
        energy = 0.5 * force * dy + force * (du - dy) + 0.5 * tangent * (du - dy)**2
    return {"temperature_c": temp, "connection_moment_factor": factor,
            "young_pa": young, "fy_pa": fy, "elastic_moment_Nm": my,
            "ideal_plastic_moment_Nm": mp, "web_shear_yield_N": shear,
            "relative_vertical_stiffness_N_m": stiffness,
            "ideal_transfer_yield_N": force, "yield_displacement_m": dy,
            "fracture_displacement_m": du, "peak_before_fracture_N": peak,
            "work_to_fracture_single_ideal_spring_J": energy,
            "global_energy_credit_J": 0.0}


def core_inventory(cfg: dict, inputs: dict) -> tuple[dict, list, list, list]:
    geometry, schedules = inputs["geometry"], inputs["columns"]["columns"]
    coords = {c["id"]: c for c in geometry["core_layout_reconstruction"]["columns"]}
    shapes = inputs["aisc"]["shapes"]
    heights = {}
    for block in geometry["floor_height_schedule_ft"]:
        for floor in range(block["from"], block["to"] + 1):
            if floor in heights:
                raise ValueError("Overlapping height schedule")
            heights[floor] = block["height"] * FT
    datum = geometry["established_facts"]["roof_height_target_m"] - sum(heights.values())
    z = {f: datum + sum(heights[n] for n in range(1, f + 1)) for f in heights}
    node_floors = sorted(set(cfg["floors"] + [f + 1 for f in cfg["floors"]]))
    nodes = [{"node_id": f"CORE_F{f}_C{cid}", "floor": f, "column_id": cid,
              "x_m": c["x_m"], "y_m": c["y_m"], "z_m": z[f],
              "coordinate_status": "RECONSTRUCTED_APPROXIMATE", "plan_tolerance_m": 0.30}
             for f in node_floors for cid, c in coords.items()]
    column_members, column_rows = [], []
    for floor, column in itertools.product(cfg["floors"], schedules):
        band = "95-92" if floor <= 94 else "98-95" if floor <= 97 else "101-98"
        segment = column["segments"][band]
        shape = shapes[segment["shape"]] if segment["kind"] == "WF" else box_shape(segment)
        props = section_si(shape)
        cid = column["id"]
        member = {"member_id": f"COREVERT_F{floor}_F{floor+1}_C{cid}", "floor": floor,
                  "column_id": cid, "node_i": f"CORE_F{floor}_C{cid}",
                  "node_j": f"CORE_F{floor+1}_C{cid}", "length_m": z[floor+1] - z[floor],
                  "splice_band": band, "section": segment.get("shape", f"BOX-{segment.get('column_type')}"),
                  "native_schedule": segment, "native_section_properties": shape,
                  "source_sheet": column["sheet"], "source_pdf_page": column["pdf_page"],
                  "section_status": "ARCHIVAL_MANUAL_TRANSCRIPTION_NOT_SECOND_PASS_VERIFIED",
                  "damage_state": "INTACT_BASELINE_HYPOTHESIS_NO_IMPACT_DAMAGE_APPLIED",
                  "length_and_splice_status": "STORY_ALIGNED_PROXY_WITH_UNRESOLVED_SPLICE_OFFSETS", **props}
        column_members.append(member)
        for temp, k in itertools.product(cfg["temperature_cases_c"], cfg["column_effective_length_factors"]):
            young, ky = steel(temp, inputs["transfer"])
            fy = segment["fy_ksi"] * KSI * ky
            py, pe, pcurve = column_screen(props["area_m2"], min(props["ix_m4"], props["iy_m4"]),
                                            member["length_m"], k, young, fy)
            column_rows.append({"member_id": member["member_id"], "floor": floor, "column_id": cid,
                                "section": member["section"], "splice_band": band,
                                "temperature_c": temp, "effective_length_factor": k,
                                "length_m": member["length_m"], "area_m2": props["area_m2"],
                                "young_pa": young, "fy_pa": fy, "axial_stiffness_N_m": young * props["area_m2"] / member["length_m"],
                                "squash_load_N": py, "ideal_euler_load_N": pe,
                                "nominal_flexural_buckling_screen_N": pcurve,
                                "capacity_status": "SCREEN_NOT_ALLOWABLE_LOAD_LOCAL_TORSIONAL_SPLICE_FAILURES_UNCHECKED"})
    beams, beam_rows, beam_curves = [], [], []
    for old in inputs["topology"]:
        if not old["element_family"].startswith("core_inplane_"):
            continue
        ci, cj = [int(old[k].rsplit("_C", 1)[1]) for k in ("node_i", "node_j")]
        length = math.hypot(coords[cj]["x_m"] - coords[ci]["x_m"], coords[cj]["y_m"] - coords[ci]["y_m"])
        beam = {"member_id": old["element_id"], "floor": int(old["floor_from"]),
                "node_i": old["node_i"], "node_j": old["node_j"],
                "column_i": ci, "column_j": cj, "length_m": length,
                "topology_family": old["element_family"], "topology_status": old["topology_status"],
                "official_model_reference": old["official_model_reference"],
                "legacy_case_ai_floor96_removed_edge_reference": old["case_ai_floor96_removed_edge_reference"],
                "damage_state": "INTACT_BASELINE_HYPOTHESIS_NO_IMPACT_DAMAGE_APPLIED",
                "bending_axis": cfg["core_beam_law"]["bending_axis"],
                "section_assignment_status": "HYPOTHESIS_NOT_AS_BUILT",
                "section_alternatives": cfg["core_beam_section_hypotheses"],
                "source": old["source_path"]}
        beams.append(beam)
        for shape_name, temp, factor in itertools.product(cfg["core_beam_section_hypotheses"],
                                                         cfg["temperature_cases_c"], cfg["core_beam_connection_moment_factors"]):
            law = beam_law(shapes[shape_name], length, temp, factor, cfg["core_beam_law"], inputs["transfer"])
            beam_rows.append({"member_id": beam["member_id"], "floor": beam["floor"],
                              "column_i": ci, "column_j": cj, "length_m": length,
                              "section_hypothesis": shape_name, "topology_family": beam["topology_family"],
                              "assignment_status": "HYPOTHESIS_NOT_AS_BUILT", **law})
            if beam["floor"] == 96 and (ci, cj) == (603, 604) and shape_name == "14WF136":
                for fraction in [0.0, 0.1, 0.25, 0.5, 0.75, 0.99, 1.0, 1.001]:
                    disp = fraction * law["fracture_displacement_m"]
                    k0, dy = law["relative_vertical_stiffness_N_m"], law["yield_displacement_m"]
                    force = k0 * disp if disp <= dy else law["ideal_transfer_yield_N"] + cfg["core_beam_law"]["post_yield_tangent_ratio"] * k0 * (disp - dy)
                    if fraction >= 1.0:
                        force = 0.0
                    beam_curves.append({"member_id": beam["member_id"], "section_hypothesis": shape_name,
                                        "temperature_c": temp, "connection_moment_factor": factor,
                                        "displacement_m": disp, "force_N": force,
                                        "state": "FRACTURED_IDEAL_RULE" if fraction >= 1 else "ELASTIC" if disp <= dy else "POST_YIELD_IDEAL_RULE",
                                        "not_usable_as_global_resistance_energy": True})
    inventory = {"iteration": "V11A", "coordinate_system": "x east, y north, z up, metres",
                 "roof_datum_offset_m": datum, "roof_target_reproduced_m": z[110],
                 "nodes": nodes, "core_column_segments": column_members, "core_beam_candidates": beams,
                 "floor_bay_assignments": [{"floor": f, "reference": "C32T1_prototype_only",
                     "as_built_bay_assignment": False, "complete_floor_truss_count": None} for f in cfg["floors"]],
                 "excluded_global_components": ["perimeter_plate_schedule", "spandrels", "column_splices",
                     "complete_core_beam_schedule", "all_actual_floor_bays", "slab_openings_and_reinforcement",
                     "hat_truss", "knuckles_studs_anchors_and_full_connection_laws"],
                 "global_collapse_coupling": False}
    return inventory, column_rows, beam_rows, beam_curves


def opposed_angles(dim: dict, gap_in: float) -> tuple[float, float]:
    """Two mirrored rectangular angles; no overlapping material, no fillets."""
    b, h, t = [dim[k] * IN for k in ("horizontal_leg", "vertical_leg", "thickness")]
    gap = gap_in * IN
    rectangles = []
    for sign in (-1, 1):
        rectangles.extend([(b, t, sign * (gap/2 + b/2), t/2),
                           (t, h-t, sign * (gap/2 + t/2), t+(h-t)/2)])
    area = sum(w * h0 for w, h0, _, _ in rectangles)
    zbar = sum(w * h0 * z for w, h0, _, z in rectangles) / area
    ix = sum(w*h0**3/12 + w*h0*(z-zbar)**2 for w, h0, _, z in rectangles)
    iy = sum(h0*w**3/12 + w*h0*x*x for w, h0, x, _ in rectangles)
    return area, min(ix, iy)


def warren_geometry(span: float, depth: float, panels: int) -> tuple[np.ndarray, list]:
    nodes = [(i * span/panels, 0.0) for i in range(panels+1)]
    nodes += [((i+0.5) * span/panels, -depth) for i in range(panels)]
    members = [(i, i+1, "top_chord") for i in range(panels)]
    members += [(panels+1+i, panels+2+i, "bottom_chord") for i in range(panels-1)]
    for i in range(panels):
        members.extend([(i, panels+1+i, "web"), (i+1, panels+1+i, "web")])
    return np.array(nodes, dtype=float), members


def truss_solve(nodes: np.ndarray, members: list, ea: list, force: np.ndarray,
                fixed_dofs: list[int]) -> dict:
    size = 2 * len(nodes)
    stiffness = np.zeros((size, size))
    geometry = []
    for (i, j, _), axial in zip(members, ea, strict=True):
        delta = nodes[j] - nodes[i]
        length = float(np.linalg.norm(delta))
        if length <= 0 or axial <= 0:
            raise ValueError("Invalid truss element")
        c, s = delta / length
        b = np.array([-c, -s, c, s])
        dofs = np.array([2*i, 2*i+1, 2*j, 2*j+1])
        stiffness[np.ix_(dofs, dofs)] += axial / length * np.outer(b, b)
        geometry.append((length, b, dofs))
    free = np.array([i for i in range(size) if i not in fixed_dofs])
    disp = np.zeros(size)
    disp[free] = np.linalg.solve(stiffness[np.ix_(free, free)], force[free])
    reaction = stiffness @ disp - force
    axial_forces = [axial/length * float(b @ disp[dofs]) for axial, (length, b, dofs) in zip(ea, geometry, strict=True)]
    internal_energy = sum(n*n*length/(2*axial) for n, axial, (length, _, _) in zip(axial_forces, ea, geometry, strict=True))
    ramp_work = 0.5 * float(force @ disp)
    residual = float(np.max(np.abs(reaction[free]))) / max(1.0, float(np.sum(np.abs(force))))
    energy_residual = abs(internal_energy-ramp_work) / max(1.0, abs(internal_energy), abs(ramp_work))
    return {"displacement": disp, "reaction": reaction, "axial_force": axial_forces,
            "member_lengths": [g[0] for g in geometry], "elastic_energy_J": internal_energy,
            "equilibrium_residual": residual, "energy_residual": energy_residual}


def seat_table(cfg: dict, inputs: dict) -> list:
    seats = inputs["seats"]["floor_truss_seats"]
    rows = []
    for side in ("interior", "exterior"):
        for detail, vertical in seats[f"{side}_vertical_capacity_kip"].items():
            horizontal = seats["interior_horizontal_tension_capacity_kip"] if side == "interior" else cfg["new_source_transcription"]["exterior_horizontal_tension_capacity_kip"][detail]
            for temp, v, h in zip(seats["temperatures_c"], vertical, horizontal, strict=True):
                rows.append({"side": side, "detail": detail, "temperature_c": temp,
                             "vertical_kip": v, "vertical_N": v*KIP,
                             "horizontal_tension_kip": h, "horizontal_tension_N": h*KIP,
                             "capacity_applies_to": "PAIRED_TRUSSES_COMPLETE_SEAT",
                             "source_status": "OFFICIAL_MODEL_COMPUTED_NOT_AS_BUILT_ASSIGNMENT",
                             "combined_V_H_law": "NOT_AVAILABLE"})
    return rows


def floor_cases(cfg: dict, inputs: dict) -> tuple[list, list, list, list, dict]:
    bay = cfg["floor_bay"]
    seats = inputs["seats"]["floor_truss_seats"]
    case_rows, member_rows, seat_rows, curves, geometries = [], [], [], [], {}
    iterator = itertools.product(bay["span_cases_in"], bay["panel_count_cases"],
        cfg["temperature_cases_c"], bay["truss_yield_strength_cases_ksi"],
        bay["web_diameter_cases_in"], bay["composite_modes"])
    for index, (span_in, panels, temp, fy_ksi, diameter, mode) in enumerate(iterator, 1):
        case_id = f"BAY-{index:04d}"
        span = span_in * IN
        nodes, members = warren_geometry(span, bay["nominal_depth_model_in"]*IN, panels)
        geometry_id = f"L{span_in:g}_P{panels}"
        if geometry_id not in geometries:
            geometries[geometry_id] = {"nodes_m": nodes.tolist(), "members": [list(m) for m in members],
                                      "hypothetical_panel_layout": True, "single_truss_only": True}
        young, ky = steel(temp, inputs["transfer"])
        fy = fy_ksi * KSI * ky
        sections = {key: opposed_angles(bay[f"{key}_angle_in"], diameter) for key in ("top_chord", "bottom_chord")}
        sections["web"] = (math.pi * (diameter*IN)**2 / 4, math.pi * (diameter*IN)**4 / 64)
        concrete = bay["concrete_hypotheses"]
        ec = concrete["elastic_modulus_20c_ksi"] * KSI * float(np.interp(temp, concrete["temperature_knots_c"], concrete["modulus_ratios"]))
        fc = concrete["compression_strength_20c_ksi"] * KSI * float(np.interp(temp, concrete["temperature_knots_c"], concrete["compression_ratios"]))
        ac = bay["width_per_single_truss_in"] * bay["equivalent_slab_thickness_in"] * IN**2
        ea = [young * sections[kind][0] + (ec*ac if kind == "top_chord" and mode == "ideal_compression_slab" else 0)
              for _, _, kind in members]
        force = np.zeros(2 * len(nodes))
        line_load = bay["service_gravity_load_psf"] * PSF * bay["width_per_single_truss_in"] * IN
        for i in range(panels+1):
            force[2*i+1] = -line_load * span / panels * (0.5 if i in (0, panels) else 1.0)
        result = truss_solve(nodes, members, ea, force, [0, 1, 2*panels+1])
        limits = []
        for mi, ((i, j, kind), n, length, axial) in enumerate(zip(members, result["axial_force"], result["member_lengths"], ea, strict=True), 1):
            area, imin = sections[kind]
            py = area * fy
            k_eff = bay["web_effective_length_factor"] if kind == "web" else bay["bare_chord_effective_length_factor"]
            pe = math.pi**2 * young * imin / (k_eff*length)**2
            nsteel, nconcrete = n, 0.0
            if kind == "top_chord" and mode == "ideal_compression_slab":
                if n > 1e-6:
                    raise ValueError("Compression-only slab branch has a tensile top chord")
                steel_share, concrete_share = young*area/axial, ec*ac/axial
                nsteel, nconcrete = n*steel_share, n*concrete_share
                candidates = [(py/steel_share, "steel_yield_ideal_braced_top"),
                              (fc*ac/concrete_share, "concrete_compression_hypothesis")]
            else:
                candidates = [(py, "steel_axial_yield")]
                if n < 0:
                    candidates.append((pe, "ideal_euler_compression_screen"))
            cap, mechanism = min(candidates)
            dcr = abs(n) / cap
            limit = 1/dcr if dcr > 1e-14 else None
            if limit is not None:
                limits.append((limit, f"M{mi:03d}", kind, mechanism))
            member_rows.append({"case_id": case_id, "member_id": f"M{mi:03d}", "family": kind,
                "node_i": i, "node_j": j, "length_m": length, "steel_area_m2": area,
                "steel_Imin_m4": imin, "effective_EA_N": axial, "trial_axial_force_single_N": n,
                "trial_steel_force_single_N": nsteel, "trial_concrete_force_single_N": nconcrete,
                "trial_axial_force_pair_N": 2*n, "steel_squash_N": py, "ideal_Euler_N": pe,
                "governing_nominal_capacity_single_N": cap, "nominal_limit_mode": mechanism,
                "service_trial_DCR": dcr, "load_multiplier_first_member_limit": limit,
                "post_limit_solution": False})
        first_member, governing_member, governing_family, mechanism = min(limits)
        pair = bay["single_trusses_per_pair"]
        rleft, rright = [pair*float(result["reaction"][d]) for d in (1, 2*panels+1)]
        int_caps = {key: float(np.interp(temp, seats["temperatures_c"], v))*KIP for key, v in seats["interior_vertical_capacity_kip"].items()}
        ext_caps = {key: float(np.interp(temp, seats["temperatures_c"], v))*KIP for key, v in seats["exterior_vertical_capacity_kip"].items()}
        combined = []
        for int_id, ext_id in itertools.product(int_caps, ext_caps):
            seat_limit = min(int_caps[int_id]/rright, ext_caps[ext_id]/rleft)
            first_limit = min(first_member, seat_limit)
            combined.append(first_limit)
            seat_rows.append({"case_id": case_id, "interior_detail_hypothesis": int_id,
                              "exterior_detail_hypothesis": ext_id, "temperature_c": temp,
                              "interior_paired_reaction_N": rright, "exterior_paired_reaction_N": rleft,
                              "interior_vertical_capacity_N": int_caps[int_id], "exterior_vertical_capacity_N": ext_caps[ext_id],
                              "seat_only_limit_load_factor": seat_limit, "first_member_limit_load_factor": first_member,
                              "combined_first_limit_load_factor": first_limit,
                              "governing": "MEMBER" if first_member <= seat_limit else "VERTICAL_SEAT",
                              "as_built_seat_assignment": False})
        first_low, first_high = min(combined), max(combined)
        down = -result["displacement"][1::2]
        max_down = float(max(down))
        total_pair = pair * line_load * span
        balance = abs(rleft+rright-total_pair)/total_pair
        case_rows.append({"case_id": case_id, "geometry_id": geometry_id, "span_in": span_in,
            "span_m": span, "panels_hypothesis": panels, "temperature_c": temp, "fy_hypothesis_ksi": fy_ksi,
            "web_diameter_hypothesis_in": diameter, "composite_mode": mode,
            "service_load_psf": bay["service_gravity_load_psf"], "paired_total_load_N": total_pair,
            "paired_exterior_reaction_kip": rleft/KIP, "paired_interior_reaction_kip": rright/KIP,
            "maximum_elastic_trial_deflection_m": max_down,
            "first_member_limit_factor": first_member, "governing_member": governing_member,
            "governing_member_family": governing_family, "governing_member_screen": mechanism,
            "first_limit_factor_weakest_seats": first_low, "first_limit_factor_strongest_seats": first_high,
            "first_limit_pressure_weakest_seats_psf": first_low*bay["service_gravity_load_psf"],
            "first_limit_deflection_weakest_seats_m": first_low*max_down,
            "service_trial_status": "BELOW_MODEL_FIRST_LIMIT" if first_low >= 1 else "ELASTIC_TRIAL_EXCEEDS_FIRST_LIMIT",
            "paired_elastic_energy_at_service_trial_J": pair*result["elastic_energy_J"],
            "equilibrium_residual": result["equilibrium_residual"], "energy_residual": result["energy_residual"],
            "reaction_balance_residual": balance,
            "global_collapse_energy_credit_J": 0.0})
        for fraction in np.linspace(0, 1, 11):
            load_factor = float(fraction) * first_low
            curves.append({"case_id": case_id, "load_factor": load_factor,
                "paired_gravity_load_N": total_pair*load_factor, "maximum_deflection_m": max_down*load_factor,
                "paired_elastic_strain_energy_J": pair*result["elastic_energy_J"]*load_factor**2,
                "state": "FIRST_NOMINAL_LIMIT_NO_CONTINUATION" if fraction == 1 else "LINEAR_ELASTIC",
                "global_energy_credit_J": 0.0})
    return case_rows, member_rows, seat_rows, curves, geometries


def unit_tests(cfg: dict, inputs: dict) -> list:
    tests = []
    def check(name: str, ok: bool, evidence: Any) -> None:
        tests.append({"test": name, "pass": bool(ok), "evidence": evidence})
    nodes = np.array([[0., 0.], [2., 0.], [1., 1.]])
    members = [(0, 1, "bar"), (0, 2, "bar"), (1, 2, "bar")]
    ea = [2e8] * 3
    force = np.array([0., 0., 0., 0., 0., -10000.])
    r = truss_solve(nodes, members, ea, force, [0, 1, 3])
    expected = np.array([5000., -10000/math.sqrt(2), -10000/math.sqrt(2)])
    check("independent_triangle_analytical_member_forces", np.allclose(r["axial_force"], expected, rtol=1e-12),
          {"computed_N": r["axial_force"], "expected_N": expected.tolist()})
    analytical_energy = (5000**2*2 + 2*(10000/math.sqrt(2))**2*math.sqrt(2))/(2*2e8)
    check("independent_triangle_virtual_work_energy", math.isclose(r["elastic_energy_J"], analytical_energy, rel_tol=1e-12), analytical_energy)
    zero = truss_solve(nodes, members, ea, np.zeros(6), [0, 1, 3])
    check("zero_load_has_zero_force_displacement_energy", max(abs(zero["displacement"])) == 0 and zero["elastic_energy_J"] == 0, zero["axial_force"])
    young20, ky20 = steel(20, inputs["transfer"])
    check("yield_reduction_normalized_at_20C", ky20 == 1.0, ky20)
    rejected = False
    try:
        steel(601, inputs["transfer"])
    except ValueError:
        rejected = True
    check("reject_modulus_extrapolation_above_600C", rejected, "601 C rejected")
    values = [steel(t, inputs["transfer"]) for t in cfg["temperature_cases_c"]]
    check("steel_E_and_yield_decrease_on_test_grid", all(values[i][0] >= values[i+1][0] and values[i][1] >= values[i+1][1] for i in range(len(values)-1)), values)
    check("units_inch_foot_kip_psf", math.isclose(12*IN, FT) and math.isclose(PSF, 47.88025898033584, rel_tol=1e-12), {"in_m": IN, "kip_N": KIP, "psf_Pa": PSF})
    top_area, _ = opposed_angles(cfg["floor_bay"]["top_chord_angle_in"], 1.09)
    check("nonoverlapping_double_angle_area", math.isclose(top_area/IN**2, 1.625, rel_tol=1e-12), top_area/IN**2)
    py, pe, p1 = column_screen(.01, 1e-5, 3.6576, 1, young20, 36*KSI)
    _, pe2, p2 = column_screen(.01, 1e-5, 3.6576, 2, young20, 36*KSI)
    check("column_K_doubling_quarters_Euler_and_reduces_capacity", math.isclose(pe2/pe, .25) and p2 < p1 <= min(py, pe), {"P1": p1, "P2": p2})
    s = inputs["aisc"]["shapes"]["14WF136"]
    b1 = beam_law(s, 5, 20, 1, cfg["core_beam_law"], inputs["transfer"])
    b2 = beam_law(s, 10, 20, 1, cfg["core_beam_law"], inputs["transfer"])
    check("beam_L_doubling_divides_stiffness_by_8", math.isclose(b2["relative_vertical_stiffness_N_m"]/b1["relative_vertical_stiffness_N_m"], 1/8), b2["relative_vertical_stiffness_N_m"]/b1["relative_vertical_stiffness_N_m"])
    return tests
