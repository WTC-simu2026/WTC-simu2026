"""Independent numerical checks for the bounded V11H thermoelastic kernel."""
from __future__ import annotations

import math
import numpy as np

import v11h_thermomechanical_model as model


def relative(a, b, floor=1e-30):
    return abs(float(a) - float(b)) / max(floor, abs(float(a)), abs(float(b)))


def run(cfg, section_cfg, reference, replay, half_step, mesh_runs, bar, cached_bar, cold_control):
    tests = []

    def check(name, condition, evidence):
        tests.append({"test": name, "pass": bool(condition), "evidence": evidence})

    by_id = {row["summary"]["id"]: row for row in reference}
    replay_by_id = {row["summary"]["id"]: row for row in replay}
    half_by_id = {row["summary"]["id"]: row for row in half_step}
    acceptance = cfg["acceptance"]

    check("declared_case_count_and_unique_ids", len(reference) == len(cfg["cases"]) == len(by_id),
          {"cases": len(reference), "unique": len(by_id)})
    check("v11f_cold_control_hashes", cold_control["status"] == "PASS" and all(cold_control["hash_checks"].values()),
          {"status": cold_control["status"], "hashes": len(cold_control["hash_checks"])})
    check("v11f_cold_control_identity", all(cold_control["identity_checks"].values()), cold_control["identity_checks"])

    replay_equal = all(a["summary"] == replay_by_id[a["summary"]["id"]]["summary"] and
                       a["history"] == replay_by_id[a["summary"]["id"]]["history"] and
                       a["peak_fibers"] == replay_by_id[a["summary"]["id"]]["peak_fibers"]
                       for a in reference)
    check("deterministic_exact_replay", replay_equal, len(reference))

    max_energy = max(row["summary"]["maximum_energy_residual_relative"] for row in reference + half_step)
    check("thermoelastic_energy_identity_all_states", max_energy <= acceptance["energy_relative"], max_energy)
    max_free = max(row["summary"]["maximum_free_resultant_residual_relative"] for row in reference + half_step)
    check("free_generalized_resultants_all_states", max_free <= acceptance["free_resultant_relative"], max_free)
    max_mechanical_work = max(abs(state["cumulative_external_mechanical_work_J_per_m"])
                              for row in reference for state in row["history"])
    check("fixed_supports_and_free_coordinates_do_zero_mechanical_work", max_mechanical_work < 1e-7, max_mechanical_work)
    check("all_dissipation_exactly_zero", all(state["dissipated_J_per_m"] == 0.0 for row in reference for state in row["history"]), 0.0)

    cold = by_id["COLD_R02_FREE"]["summary"]["peak"]
    cold_fields = [cold[k] for k in ("eps0", "kappa_per_m", "N_N", "M_Nm", "stored_mechanical_J_per_m",
                                      "cumulative_thermoelastic_work_J_per_m", "sensible_enthalpy_change_J_per_m")]
    check("new_section_cold_limit_is_zero", max(abs(v) for v in cold_fields) < 1e-12, cold_fields)

    plain_free = by_id["PLAIN_UNIFORM_FREE"]
    inv = plain_free["inventory"]
    peak = plain_free["summary"]["peak"]
    alpha_c = cfg["thermal_properties"]["concrete"]["thermal_expansion_per_k"]
    delta_t = 100.0
    expected_eps = alpha_c * delta_t
    expected_extension = expected_eps * cfg["geometry"]["span_m"]
    closed_errors = {
        "eps0": relative(peak["eps0"], expected_eps, 1e-15),
        "kappa": abs(peak["kappa_per_m"]),
        "extension": relative(peak["centroid_extension_m"], expected_extension, 1e-15),
        "stress": abs(peak["maximum_absolute_stress_Pa"]) / max(1.0, inv["E_concrete_Pa"] * expected_eps),
        "stored": abs(peak["stored_mechanical_J_per_m"]) / max(
            1.0, 0.5 * inv["section_stiffness"]["K_N"] * expected_eps**2
        ),
    }
    check("homogeneous_uniform_free_closed_form", max(closed_errors.values()) <= acceptance["closed_form_relative"], closed_errors)

    restrained = by_id["PLAIN_UNIFORM_FULLY_RESTRAINED"]
    peak = restrained["summary"]["peak"]
    ea = inv["section_stiffness"]["K_N"]
    expected_n = -ea * expected_eps
    expected_u = 0.5 * ea * expected_eps**2
    errors = {
        "N": relative(peak["N_N"], expected_n, 1e-12),
        "reaction": relative(peak["support_reaction_N"], -expected_n, 1e-12),
        "U": relative(peak["stored_mechanical_J_per_m"], expected_u, 1e-12),
        "thermal_work": relative(peak["cumulative_thermoelastic_work_J_per_m"], expected_u, 1e-12),
        "eps0": abs(peak["eps0"]), "kappa": abs(peak["kappa_per_m"]),
    }
    check("homogeneous_uniform_restrained_closed_form", max(errors.values()) <= acceptance["closed_form_relative"], errors)

    gradient = by_id["PLAIN_GRADIENT_FREE"]
    peak = gradient["summary"]["peak"]
    h = gradient["inventory"]["equivalent_thickness_m"]
    expected_gradient_eps0 = alpha_c * delta_t / 2
    expected_kappa = -alpha_c * delta_t / h
    expected_bow = abs(expected_kappa) * cfg["geometry"]["span_m"]**2 / 8
    errors = {
        "eps0": relative(peak["eps0"], expected_gradient_eps0, 1e-15),
        "kappa": relative(peak["kappa_per_m"], expected_kappa, 1e-15),
        "bow": relative(peak["simply_supported_free_bow_midspan_m"], expected_bow, 1e-15),
        "stress": abs(peak["maximum_absolute_stress_Pa"]) / max(1.0, gradient["inventory"]["E_concrete_Pa"] * expected_gradient_eps0),
        "stored": abs(peak["stored_mechanical_J_per_m"]) / max(1.0, 0.5 * gradient["inventory"]["section_stiffness"]["K_N"] * expected_gradient_eps0**2),
    }
    check("homogeneous_through_depth_gradient_free_closed_form", max(errors.values()) <= acceptance["closed_form_relative"], errors)

    expected_sensible_uniform = (cfg["thermal_properties"]["concrete"]["density_kg_m3"] *
                                 cfg["thermal_properties"]["concrete"]["specific_heat_j_kg_k"] *
                                 inv["concrete_area_m2"] * delta_t)
    expected_sensible_gradient = expected_sensible_uniform / 2
    sensible_errors = {
        "uniform": relative(plain_free["summary"]["peak"]["sensible_enthalpy_change_J_per_m"], expected_sensible_uniform, 1e-9),
        "gradient": relative(gradient["summary"]["peak"]["sensible_enthalpy_change_J_per_m"], expected_sensible_gradient, 1e-9),
    }
    check("homogeneous_sensible_enthalpy_closed_form", max(sensible_errors.values()) <= acceptance["closed_form_relative"], sensible_errors)

    common = by_id["R02_COMMON_ALPHA_GRADIENT_FREE"]["summary"]["peak"]
    check("common_alpha_composite_free_gradient_is_stress_free",
          common["maximum_absolute_stress_Pa"] < 1e-4 and common["stored_mechanical_J_per_m"] < 1e-10,
          {"stress_Pa": common["maximum_absolute_stress_Pa"], "U_J_m": common["stored_mechanical_J_per_m"]})
    differential = by_id["R02_GRADIENT_FREE"]["summary"]["peak"]
    check("differential_alpha_free_gradient_is_self_equilibrated_not_stress_free",
          differential["maximum_absolute_stress_Pa"] > 1.0 and
          max(differential["free_axial_residual_relative"], differential["free_moment_residual_relative"]) < acceptance["free_resultant_relative"],
          {"stress_Pa": differential["maximum_absolute_stress_Pa"], "N": differential["N_N"], "M": differential["M_Nm"]})

    uniform_axial = by_id["R02_UNIFORM_AXIAL_RESTRAINED"]["summary"]["peak"]
    check("uniform_axial_restraint_generates_reaction_without_rotation_work",
          uniform_axial["support_reaction_N"] > 0 and abs(uniform_axial["M_Nm"]) < 1e-6 and
          abs(uniform_axial["cumulative_external_mechanical_work_J_per_m"]) < 1e-7,
          {k: uniform_axial[k] for k in ("support_reaction_N", "M_Nm", "cumulative_external_mechanical_work_J_per_m")})
    gradient_fixed = by_id["R02_GRADIENT_FULLY_RESTRAINED"]["summary"]["peak"]
    check("gradient_full_restraint_generates_force_and_moment_reactions",
          abs(gradient_fixed["support_reaction_N"]) > 1 and abs(gradient_fixed["support_reaction_Nm"]) > 1,
          {"reaction_N": gradient_fixed["support_reaction_N"], "reaction_Nm": gradient_fixed["support_reaction_Nm"]})

    cycle_ids = ["R02_UNIFORM_RESTRAINED_CYCLE", "R02_GRADIENT_FREE_CYCLE"]
    cycle_evidence = {}
    cycle_ok = True
    for case_id in cycle_ids:
        final = by_id[case_id]["summary"]["final"]
        values = {
            "eps0": abs(final["eps0"]), "kappa": abs(final["kappa_per_m"]),
            "stress": abs(final["maximum_absolute_stress_Pa"]), "stored": abs(final["stored_mechanical_J_per_m"]),
            "thermal_work": abs(final["cumulative_thermoelastic_work_J_per_m"]),
            "sensible": abs(final["sensible_enthalpy_change_J_per_m"]),
        }
        cycle_evidence[case_id] = values
        cycle_ok &= max(values["eps0"], values["kappa"]) <= acceptance["cycle_return_absolute_strain"]
        cycle_ok &= max(values["stored"], values["thermal_work"], values["sensible"]) <= acceptance["cycle_return_energy_j_per_m"]
        cycle_ok &= values["stress"] < 1e-4
    check("elastic_thermal_cycles_return_without_residual_state_or_dissipation", cycle_ok, cycle_evidence)

    half_errors = {}
    floors = acceptance["comparison_absolute_floors_si"]
    for case_id, row in by_id.items():
        other = half_by_id[case_id]
        for label in ("peak", "final"):
            for field in ("eps0", "kappa_per_m", "N_N", "M_Nm", "stored_mechanical_J_per_m",
                          "cumulative_thermoelastic_work_J_per_m", "sensible_enthalpy_change_J_per_m"):
                a = row["summary"][label][field]
                b = other["summary"][label][field]
                key = f"{case_id}:{label}:{field}"
                half_errors[key] = relative(a, b, floors[field])
    check("temperature_half_step_endpoint_invariance", max(half_errors.values()) <= acceptance["half_step_relative"],
          {"maximum": max(half_errors.values()), "field_count": len(half_errors)})

    mesh_errors = {}
    for case_id, row in by_id.items():
        fine = mesh_runs["320"][case_id]
        for field in ("eps0", "kappa_per_m", "N_N", "M_Nm", "stored_mechanical_J_per_m",
                      "sensible_enthalpy_change_J_per_m"):
            a = row["summary"]["peak"][field]
            b = fine["summary"]["peak"][field]
            error = relative(a, b, floors[field])
            mesh_errors[f"{case_id}:{field}"] = error
    check("reference_to_320_fiber_refinement", max(mesh_errors.values()) <= acceptance["reference_to_320_relative"],
          {"maximum": max(mesh_errors.values()), "field_count": len(mesh_errors)})

    bar_errors = {
        "uniform_free": relative(bar["uniform_free_tip_displacement_mm"], cached_bar["recomputed"]["uniform_free_tip_displacement_mm"]),
        "restrained_force": relative(bar["uniform_restrained_force_magnitude_N"], cached_bar["recomputed"]["uniform_restrained_force_magnitude_n"]),
        "restrained_stress": relative(bar["uniform_restrained_stress_MPa"], cached_bar["recomputed"]["uniform_restrained_axial_stress_mpa"]),
        "axial_gradient": relative(bar["axial_linear_gradient_free_tip_displacement_mm"], cached_bar["recomputed"]["axial_linear_gradient_free_tip_displacement_mm"]),
        "energy_identity": relative(bar["uniform_restrained_stored_energy_J"], bar["uniform_restrained_thermoelastic_work_J"]),
    }
    check("cached_v10w_bar_reference_reproduced", max(bar_errors.values()) <= acceptance["closed_form_relative"], bar_errors)

    expected_area = section_cfg["section"]["width_in"] * model.IN * section_cfg["section"]["equivalent_thickness_in"] * model.IN
    area_errors = [relative(row["inventory"]["gross_area_m2"], expected_area) for row in reference]
    check("gross_section_area_and_units", max(area_errors) < 1e-14, {"area_m2": expected_area, "maximum_error": max(area_errors)})
    stiffness_checks = []
    for case in cfg["cases"]:
        section = model.ElasticThermoSection(section_cfg, cfg, case, cfg["discretization"]["reference_concrete_fibers"])
        stiffness_checks.append(bool(np.allclose(section.K, section.K.T) and np.min(np.linalg.eigvalsh(section.K)) > 0))
    check("all_section_stiffness_matrices_symmetric_positive_definite", all(stiffness_checks), len(stiffness_checks))

    check("temperature_and_energy_scopes_remain_bounded",
          not cfg["fire_solved"] and not cfg["heat_transfer_solved"] and not cfg["heated_fracture_solved"] and
          not cfg["full_panel_thermomechanical_coupling_solved"] and not cfg["blender_changed"] and
          cfg["global_energy_credit_j"] == 0.0,
          "Prescribed-temperature elastic section only; no fire, heat transfer, fracture, panel solve or global credit")
    check("heat_transfer_properties_not_silently_invented",
          all(v is None for v in cfg["thermal_properties"]["unused_heat_transfer_fields"].values()) and
          cfg["thermal_properties"]["concrete"]["conductivity_w_m_k"] is None and
          cfg["thermal_properties"]["reinforcement"]["conductivity_w_m_k"] is None,
          cfg["thermal_properties"]["unused_heat_transfer_fields"])
    check("constant_elastic_properties_are_inherited_not_degraded",
          all(row["inventory"]["E_concrete_Pa"] == section_cfg["concrete"]["E20_ksi"] * model.KSI for row in reference),
          section_cfg["concrete"]["E20_ksi"])

    return tests, {"half_step": half_errors, "mesh_160_to_320": mesh_errors}
