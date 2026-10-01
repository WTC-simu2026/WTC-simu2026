"""Independent V11D beam recovery / assembled-panel review checks.

The expected values use beam closed forms or direct physical inventories.
Passing verifies this bounded implementation, not WTC material calibration.
No output files are written. Public API: run(cfg, cfg_c, base, transfer, seats).
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np


def run(cfg, cfg_c, base, transfer, seats):
    import v11d_panel_model as model

    checks = []

    def check(name, operation):
        try:
            evidence = operation()
            checks.append({"test": "INDEPENDENT_PANEL_REVIEW_" + name,
                           "pass": True, "evidence": evidence})
        except Exception as error:
            checks.append({"test": "INDEPENDENT_PANEL_REVIEW_" + name,
                           "pass": False,
                           "evidence": {"exception": type(error).__name__, "message": str(error)}})

    def close(actual, expected, atol=1e-8, rtol=2e-8):
        actual, expected = np.asarray(actual, float), np.asarray(expected, float)
        if not np.all(np.isfinite(actual)):
            raise AssertionError("Nonfinite quantity")
        error = float(np.max(np.abs(actual-expected), initial=0.))
        scale = float(np.max(np.abs(expected), initial=0.))
        if error > atol + rtol*scale:
            raise AssertionError(f"error={error}; expected scale={scale}; actual={actual}; expected={expected}")
        if actual.size > 12:
            return {"quantity_count": int(actual.size), "maximum_absolute_error": error,
                    "maximum_absolute_expected": scale,
                    "maximum_absolute_actual": float(np.max(np.abs(actual), initial=0.))}
        return {"actual": actual.tolist(), "expected": expected.tolist(), "maximum_absolute_error": error}

    def audit(result):
        names = ["equilibrium_residual", "energy_identity_residual"]
        if "recovered_energy_identity_residual" in result:
            names.append("recovered_energy_identity_residual")
        for name in names:
            if not np.isfinite(result[name]) or result[name] > 1e-8:
                raise AssertionError(f"{name}={result[name]}")
        return {name: result[name] for name in names}

    def panel(spec=None, removed=()):
        return model.build_panel(cfg, cfg_c, base, transfer, seats, spec or {}, removed)

    def evaluate(spec=None, removed=()):
        return model.evaluate_panel(cfg, cfg_c, base, transfer, seats, spec or {}, removed)

    def simply_supported_recovery():
        length, ei, q = 3.7, 2.3e6, -1370.
        rows = model.beam_terms("SS", 0, 1, 2, 3, length, ei)
        r = model.solve_terms(4, rows, model.beam_load(length, q), {0: 0., 2: 0.})
        recovery = model.recover_beam(r["u"], length, ei, q)
        points, moments = np.array(recovery["x_m"]), np.array(recovery["moment_Nm"])
        expected_moments = -q*points*(length-points)/2
        midpoint = int(np.argmin(abs(points-length/2)))
        energy = r["strain_energy_J"] + recovery["bubble_energy_J"]
        return {"moments_Nm": close(moments, expected_moments),
                "extremum_x_m": close(points[midpoint], length/2),
                "midpoint_Nm": close(moments[midpoint], -q*length**2/8),
                "total_energy_J": close(energy, q*q*length**5/(240*ei)),
                "bubble_J": close(recovery["bubble_energy_J"], q*q*length**5/(1440*ei)),
                "bubble_work_J": close(recovery["bubble_load_work_J"], 2*recovery["bubble_energy_J"]),
                **audit(r)}

    check("SINGLE_BEAM_EXACT_UDL_MOMENT_AND_TOTAL_ENERGY", simply_supported_recovery)

    def clamped_bubble():
        length, ei, q = 2.9, 4.8e6, -940.
        r = model.recover_beam(np.zeros(4), length, ei, q)
        expected = [q*length**2/12, q*length**2/12, -q*length**2/24]
        return {"end_end_middle_Nm": close(r["moment_Nm"], expected),
                "all_energy_is_particular_solution_J": close(r["bubble_energy_J"], q*q*length**5/(1440*ei))}

    check("CLAMPED_BEAM_UDL_BUBBLE_RECOVERS_NONZERO_STRESS", clamped_bubble)

    def general_bubble(curvature):
        length, ei, q = 2.3, 2.7e6, -1270.
        u = np.array([-.002, .003, .004, -.001])
        c = 3*(u[2]-u[0])/length**2 - (2*u[1]+u[3])/length
        d = 2*(u[0]-u[2])/length**3 + (u[1]+u[3])/length**2
        r = model.recover_beam(u, length, ei, q, curvature)
        x = np.array(r["x_m"])
        expected = ei*(2*c+6*d*x-curvature)+q*(length**2-6*length*x+6*x*x)/12
        ts = model.beam_terms("GENERAL", 0, 1, 2, 3, length, ei, curvature)
        discrete = model.solve_terms(4, ts, model.beam_load(length, q), dict(enumerate(u)))
        gx, gw = np.polynomial.legendre.leggauss(8)
        xg, wg = (gx+1)*length/2, gw*length/2
        moment = ei*(2*c+6*d*xg-curvature)+q*(length**2-6*length*xg+6*xg*xg)/12
        integrated_energy = float(np.dot(wg, moment*moment/(2*ei)))
        return {"moment_Nm": close(r["moment_Nm"], expected),
                "integrated_recovered_energy_J": close(discrete["strain_energy_J"]+r["bubble_energy_J"], integrated_energy),
                **audit(discrete)}

    for curvature in (0., .0013):
        check("GENERAL_HERMITE_UDL_ENERGY_CURVATURE_" + str(curvature),
              lambda curvature=curvature: general_bubble(curvature))

    def rigid_rotation():
        p = panel({"gravity_factor": 0.})
        omega, tx, ty = .0007, .0013, -.0021
        u = np.zeros(p["size"])
        for i, (x, y) in enumerate(p["nodes"]):
            u[2*i], u[2*i+1] = tx-omega*y, ty+omega*x
        u[p["ux"]] = tx-omega*p["eccentricity_m"]
        u[p["w"]] = ty+omega*p["slab_x_m"]
        u[p["theta"]] = omega
        # Remove ground seat terms: they are external restraints, not rigid modes.
        internal_terms = [t for t in p["terms"] if not t["kind"].startswith("seat_")]
        strains = [float(np.dot(t["b"], u[t["dofs"]])-t["e0"]) for t in internal_terms]
        r = model.solve_terms(p["size"], internal_terms, np.zeros(p["size"]), dict(enumerate(u)))
        return {"all_kinematic_strains": close(strains, np.zeros(len(strains)), atol=2e-14),
                "zero_energy_J": close(r["strain_energy_J"], 0., atol=1e-14), **audit(r)}

    check("RIGID_ROTATION_WITH_UNDERSIDE_ECCENTRICITY", rigid_rotation)

    def assembly_inventory(subdivisions):
        p = panel({"subdivisions": subdivisions})
        contacts = [t for t in p["terms"] if t["kind"] == "contact"]
        vt = [t for t in p["terms"] if t["kind"] == "vertical_tie"]
        ht = [t for t in p["terms"] if t["kind"] == "horizontal_tie"]
        count = cfg_c["panel"]["symmetric_trusses_per_pair"]
        density_count = count*cfg_c["panel"]["span_in"]/cfg_c["panel"]["nominal_knuckle_spacing_in"]
        load_expected = cfg_c["panel"]["load_psf"]*47.88025898033584*count*base["floor_bay"]["width_per_single_truss_in"]*.0254*p["span_m"]
        return {"subdivisions": subdivisions,
                "station_counts": close([len(contacts), len(vt), len(ht)], [p["panels"]+1]*3),
                "equivalent_knuckle_total": close(sum(t["k"] for t in contacts)/cfg["vertical_connection"]["contact_stiffness_per_equivalent_knuckle_N_m"], density_count),
                "gravity_once_N": close(-sum(p["force"][p["w"]]), load_expected),
                "no_load_on_steel_or_slab_axial": close(p["force"][:p["steel_dofs"]].tolist()+p["force"][p["ux"]].tolist(), np.zeros(p["steel_dofs"]+len(p["ux"]))) }

    for sub in (1, 2, 4):
        check(f"FIXED_ATTACHMENT_AND_GRAVITY_INVENTORY_SUB{sub}", lambda sub=sub: assembly_inventory(sub))

    def zero_state():
        r = evaluate({"gravity_factor": 0.})
        return {"all_displacements_zero": close(r["u"], np.zeros_like(r["u"])),
                "zero_demand_and_energy": close([r["max_DCR"], r["strain_energy_J"], r["recovered_total_strain_energy_J"]], [0.,0.,0.]),
                **audit(r)}

    check("ZERO_COLD_LOAD_STATE", zero_state)

    def loaded_panel():
        r = evaluate({"gravity_factor": .1})
        p = r["model"]
        contact = [t for t in r["terms"] if t["kind"] == "contact"]
        ties = [t for t in r["terms"] if t["kind"] == "vertical_tie"]
        if any(t["force_N"] > 1e-9 for t in contact) or any(t["force_N"] < -1e-9 for t in ties):
            raise AssertionError("Wrong unilateral-force sign")
        total_transfer_to_slab = sum(t["force_N"] for t in contact+ties)
        vertical_reactions = [t["force_N"] for t in r["terms"] if t["kind"] == "seat_v"]
        return {"support_sum_N": close(r["total_seat_vertical_reaction_N"], r["total_gravity_load_N"]),
                "slab_to_steel_transfer_N": close(total_transfer_to_slab, -r["total_gravity_load_N"]),
                "symmetric_seat_reaction_N": close(vertical_reactions, [-r["total_gravity_load_N"]/2]*2),
                "symmetric_slab_displacement": close(r["u"][p["w"]], r["u"][p["w"]][::-1], atol=2e-9),
                "symmetric_opposite_rotations": close(r["u"][p["theta"]], -r["u"][p["theta"]][::-1], atol=2e-9),
                "first_domain_ratio": r["max_DCR"], **audit(r)}

    check("COLD_PAIR_REACTIONS_TRANSFER_SYMMETRY_AND_SIGNS", loaded_panel)

    def imposed_panel():
        r = evaluate({"gravity_factor": .1, "prescribed_top_vertical": {5: -.001}})
        p = r["model"]
        right_seat_force = -next(t["force_N"] for t in r["terms"] if t["id"] == "SEAT-V-interior")
        reaction_moment = right_seat_force*p["span_m"] + r["actuator_vertical_reaction_N"]*p["span_m"]*5/p["panels"]
        return {"seat_plus_actuator_N": close(r["total_seat_vertical_reaction_N"]+r["actuator_vertical_reaction_N"], r["total_gravity_load_N"]),
                "moment_about_left_Nm": close(reaction_moment, r["total_gravity_load_N"]*p["span_m"]/2),
                "imposed_node_m": close(r["u"][11], -.001), **audit(r)}

    check("ACTUATOR_REACTION_NOT_OMITTED_FROM_VERTICAL_BALANCE", imposed_panel)

    def temperature_index(mean_c, top_c, bottom_c, expected_kip):
        outputs = []
        for steel_c in (20., 600.):
            p = panel({"steel_c": steel_c, "slab_top_c": top_c, "slab_bottom_c": bottom_c})
            v = next(t for t in p["terms"] if t["id"] == "V-TIE-000")
            expected_count = cfg_c["panel"]["symmetric_trusses_per_pair"]/2
            outputs.append({"steel_c": steel_c,
                            "mean_temperature_C": close(p["slab_mean_c"], mean_c),
                            "end_knuckle_capacity_N": close(v["cap_tension_N"], expected_kip*4448.2216152605*expected_count)})
        return outputs

    for args in ((300., 300., 300., 15.), (450., 600., 300., 12.), (600., 600., 600., 10.)):
        check("PULLOUT_TABLE_USES_MEAN_CONCRETE_C_" + str(args[0]), lambda args=args: temperature_index(*args))

    def gradient_sign():
        p = panel({"steel_c": 20., "slab_top_c": 20., "slab_bottom_c": 300.})
        el = p["elements"][0]
        expected = cfg_c["panel"]["concrete_expansion_per_K"]*280/el["thickness_m"]
        if expected <= 0: raise AssertionError("Expected below-hot positive free curvature")
        return {"curvature_1_m": close(el["curvature_thermal_per_m"], expected)}

    check("HOT_UNDERSIDE_FREE_CURVATURE_SIGN", gradient_sign)

    def removed_station():
        p = panel({"gravity_factor": 0.}, [8])
        ids = {t["id"] for t in p["terms"]}
        if "H-TIE-008" in ids or "V-TIE-008" in ids or "CONTACT-008" not in ids:
            raise AssertionError("Removed attachment does not preserve contact alone")
        results = []
        contact = next(t for t in p["terms"] if t["id"] == "CONTACT-008")
        for gap in (-1e-5, 1e-5):
            u = np.zeros(p["size"])
            u[contact["dofs"][1]] = gap
            r = model.solve_terms(p["size"], p["terms"], p["force"], dict(enumerate(u)))
            t = next(t for t in r["terms"] if t["id"] == "CONTACT-008")
            results.append({"gap_m": gap,
                            "remaining_contact_N": close(t["force_N"], contact["k"]*min(gap, 0.)), **audit(r)})
        return {"surviving_station": "CONTACT-008", "tests": results}

    check("REMOVED_STATION_RETAINS_CONTACT_NOT_TENSION", removed_station)

    def distinct_units():
        p = panel({"gravity_factor": 0.})
        r = model.solve_terms(p["size"], p["terms"], p["force"])
        bending = [t for t in r["terms"] if t["kind"] == "slab_bending"]
        physical = [t for t in r["terms"] if t["kind"] != "slab_bending"]
        if not all(t.get("generalized_strain_unit") == "1/m" and t.get("generalized_stiffness_unit") == "N*m^3" and t.get("generalized_force_unit") == "N*m^2" for t in bending):
            raise AssertionError("Bending quadrature-unit metadata missing")
        if not all(t.get("generalized_force_unit") == "N" for t in physical):
            raise AssertionError("Physical spring/bar force units incorrect")
        return {"bending_terms": len(bending), "physical_terms": len(physical),
                "warning": "Internal legacy force_N key is generalized for bending; consumer must honor unit metadata."}

    check("BENDING_GENERALIZED_QUANTITY_HAS_DISTINCT_UNITS", distinct_units)

    def fiber_combination():
        r = evaluate({"gravity_factor": .1})
        elements = {e["id"]: e for e in r["model"]["elements"]}
        mean_errors, moment_errors = [], []
        for row in r["fiber_rows"]:
            e = elements[row["element_id"]]
            mean_errors.append((row["sigma_top_Pa"]+row["sigma_bottom_Pa"])/2-row["axial_force_N"]/e["A_m2"])
            moment_errors.append((row["sigma_bottom_Pa"]-row["sigma_top_Pa"])*e["I_m4"]/e["thickness_m"]-row["moment_Nm"])
        return {"mean_stress_residual_Pa": close(mean_errors, np.zeros(len(mean_errors)), atol=1e-6),
                "moment_from_fiber_difference_residual_Nm": close(moment_errors, np.zeros(len(moment_errors)), atol=1e-7)}

    check("FIBER_STRESS_COMBINES_AXIAL_AND_BENDING_WITH_SIGN", fiber_combination)
    return checks


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    def read(path):
        return json.loads((root/path).read_text(encoding="utf-8-sig"))
    cfg = read("wtc1_simulation_v8/data/v11d_slab_contact_predeclaration.json")
    cfg_c = read(cfg["base_configuration"])
    rows = run(cfg, cfg_c, read(cfg_c["base_configuration"]),
               read(cfg_c["transfer"]), read(cfg_c["seats"])["floor_truss_seats"])
    print(json.dumps({"passed": sum(r["pass"] for r in rows), "total": len(rows), "tests": rows}, indent=2))
    raise SystemExit(0 if all(r["pass"] for r in rows) else 1)
