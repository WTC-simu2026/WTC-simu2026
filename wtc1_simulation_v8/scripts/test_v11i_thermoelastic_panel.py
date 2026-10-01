"""Numerical and regression checks for the bounded V11I panel coupling."""
from __future__ import annotations

import numpy as np

import v11i_thermoelastic_panel_model as model


def relative(a, b, floor=1e-30):
    return abs(float(a) - float(b)) / max(float(floor), abs(float(a)), abs(float(b)))


def run(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, reference, replay, half_step,
        mesh_runs, comparisons, cached_cold, cold_control, thermo_control):
    tests = []

    def check(name, condition, evidence):
        tests.append({"test": name, "pass": bool(condition), "evidence": evidence})

    by_id = {row["summary"]["id"]: row for row in reference}
    check("three_declared_unique_panel_paths", len(reference) == len(cfg["thermal_cases"]) == len(by_id) == 3,
          {"paths": len(reference), "unique": len(by_id)})
    check("v11f_saved_control_hashes_and_identity", cold_control["status"] == "PASS" and
          all(cold_control["hash_checks"].values()) and all(cold_control["identity_checks"].values()),
          {"status": cold_control["status"], "hashes": len(cold_control["hash_checks"])})
    check("v11h_saved_control_hashes_and_identity", thermo_control["status"] == "PASS" and
          all(thermo_control["hash_checks"].values()) and all(thermo_control["identity_checks"].values()),
          {"status": thermo_control["status"], "hashes": len(thermo_control["hash_checks"])})

    check("deterministic_exact_replay", reference == replay, len(reference))
    histories = [state for run_data in reference + half_step for state in run_data["history"]]
    max_equilibrium = max(state["equilibrium_residual"] for state in histories)
    max_increment_energy = max(state["maximum_increment_energy_residual_relative"] for state in histories)
    max_total_energy = max(state["total_mechanical_energy_residual_relative"] for state in histories)
    check("all_states_equilibrium", max_equilibrium <= cfg["acceptance"]["relative_equilibrium"], max_equilibrium)
    check("all_increments_mechanical_plus_thermal_energy", max_increment_energy <= cfg["acceptance"]["relative_incremental_energy"], max_increment_energy)
    check("all_paths_total_mechanical_plus_thermal_energy", max_total_energy <= cfg["acceptance"]["relative_total_energy"], max_total_energy)
    check("support_work_exactly_zero", all(state["support_work_J"] == 0.0 for state in histories), 0.0)
    check("zero_dissipation_and_global_credit", all(state["dissipated_J"] == 0.0 and state["global_energy_credit_J"] == 0.0 for state in histories), 0.0)

    max_vertical = max(state["vertical_balance_relative"] for state in histories)
    max_horizontal = max(state["horizontal_balance_absolute_N"] for state in histories)
    check("support_reactions_balance_gravity", max_vertical < 1e-8 and max_horizontal < 1e-5,
          {"vertical_relative": max_vertical, "horizontal_absolute_N": max_horizontal})

    cold = by_id["COLD_DELTA_T_ZERO"]
    cold_final = cold["summary"]["final"]
    cold_preload = cold["summary"]["preload"]
    exact_fields = (
        "stored_J", "spring_stored_J", "slab_stored_J", "max_slab_down_m", "max_slab_up_m",
        "max_truss_down_m", "max_opening_m", "max_overlap_m", "seat_vertical_reaction_N",
        "seat_horizontal_reaction_N", "gravity_load_N", "max_DCR"
    )
    cold_exact = {field: abs(cold_final[field] - cold_preload[field]) for field in exact_fields}
    check("delta_t_zero_is_exact_preload_replay", max(cold_exact.values()) == 0.0 and
          cold_final["sensible_enthalpy_J"] == 0.0 and cold_final["thermoelastic_work_J"] == 0.0,
          cold_exact)

    mapping = {
        "stored_J": "stored_J", "spring_stored_J": "spring_stored_J", "slab_stored_J": "slab_stored_J",
        "max_slab_down_m": "max_slab_down_m", "max_truss_down_m": "max_truss_down_m",
        "max_opening_m": "max_opening_m", "max_overlap_m": "max_overlap_m",
        "seat_vertical_reaction_N": "seat_reaction_N", "gravity_load_N": "gravity_load_N",
        "component_max_DCR": "max_DCR",
    }
    floors = cfg["comparison_absolute_floors_si"]
    cold_errors = {}
    for actual, cached in mapping.items():
        floor = floors["displacement_m"] if actual.startswith("max_") and actual.endswith("_m") else floors["energy_J"] if "stored" in actual else floors["force_N"] if actual.endswith("_N") else 1e-9
        cold_errors[actual] = relative(cold_preload[actual], float(cached_cold[cached]), floor)
    discrete = {
        "contact_count": cold_preload["contact_count"] == int(cached_cold["contact_count"]),
        "vertical_tension_count": cold_preload["vertical_tension_count"] == int(cached_cold["vertical_tension_count"]),
        "governing_id": cold_preload["governing_id"] == cached_cold["governing_id"],
        "governing_kind": cold_preload["governing_kind"] == cached_cold["governing_kind"],
    }
    check("cold_v11f_cached_quarter_gravity_regression", max(cold_errors.values()) <= cfg["acceptance"]["cold_v11f_cached_response_relative"] and all(discrete.values()),
          {"maximum_relative": max(cold_errors.values()), "errors": cold_errors, "discrete": discrete})

    tangent_errors = [row["inventory"]["cold_zero_tangent_relative_difference"] for row in reference]
    check("cold_zero_tangent_matches_v11f", max(tangent_errors) <= cfg["acceptance"]["cold_nodal_zero_temperature_exact_replay_relative"], max(tangent_errors))
    inventories = [row["inventory"] for row in reference]
    check("reference_topology_is_one_v11f_panel", all(
        inv["subdivisions"] == 4 and inv["steel_nodes"] == 33 and inv["steel_members"] == 63 and
        inv["slab_nodes"] == 65 and inv["slab_elements"] == 64 and inv["gauss_sections"] == 128 and
        inv["contact_stations"] == 17 for inv in inventories
    ), inventories[0])

    guard = cfg["loading"]["accepted_DCR_guard"]
    guard_tol = cfg["acceptance"]["guard_DCR_absolute_tolerance"]
    max_accepted = max(state["max_DCR"] for state in histories)
    check("accepted_states_stop_below_guard", max_accepted <= guard + guard_tol,
          {"maximum": max_accepted, "guard": guard})
    guard_rows = [row for row in reference if row["summary"]["guard_bracket"] is not None]
    brackets_ok = all(
        row["summary"]["guard_bracket"]["accepted_DCR"] <= guard and
        row["summary"]["guard_bracket"]["rejected_DCR"] >= guard and
        not row["summary"]["guard_bracket"]["rejected_state_committed"] and
        row["summary"]["terminal"] == "SAFE_DCR_GUARD_REACHED_BEFORE_NOMINAL_LIMIT"
        for row in guard_rows
    )
    check("guard_crossing_trials_are_uncommitted", len(guard_rows) >= 1 and brackets_ok,
          [row["summary"]["guard_bracket"] for row in guard_rows])
    check("no_nominal_limit_or_crack_state_accepted", all(state["max_DCR"] < 1.0 for state in histories), max_accepted)

    uniform = by_id["SLAB_UNIFORM_100K"]
    gradient = by_id["SLAB_GRADIENT_TOP_100K"]
    for case_id, data in (("uniform", uniform), ("gradient", gradient)):
        final = data["summary"]["final"]
        check(f"{case_id}_coupling_produces_nonzero_thermal_response",
              final["thermal_scale"] > 0 and abs(final["thermoelastic_work_J"]) > 1e-8 and
              (abs(final["max_slab_up_m"] - cold_preload["max_slab_up_m"]) > 1e-9 or
               abs(final["seat_vertical_reaction_N"] - cold_preload["seat_vertical_reaction_N"]) > 1e-5 or
               abs(final["spring_stored_J"] - cold_preload["spring_stored_J"]) > 1e-7),
              {key: final[key] for key in ("thermal_scale", "thermoelastic_work_J", "max_slab_up_m", "seat_vertical_reaction_N", "spring_stored_J")})

    uniform_final = uniform["summary"]["final"]
    gradient_final = gradient["summary"]["final"]
    check("uniform_and_gradient_temperature_faces_saved",
          abs(uniform_final["slab_top_temperature_c"] - uniform_final["slab_bottom_temperature_c"]) < 1e-12 and
          gradient_final["slab_top_temperature_c"] > gradient_final["slab_bottom_temperature_c"] == 20.0,
          {"uniform": [uniform_final["slab_bottom_temperature_c"], uniform_final["slab_top_temperature_c"]],
           "gradient": [gradient_final["slab_bottom_temperature_c"], gradient_final["slab_top_temperature_c"]]})

    sensible_errors = {}
    for data in reference:
        final = data["summary"]["final"]
        inv = data["inventory"]
        average_delta = 0.5 * (
            data["summary"]["delta_t_bottom_c"] + data["summary"]["delta_t_top_c"]
        ) * final["thermal_scale"]
        expected = inv["section"]["heat_capacity_J_per_m_K"] * inv["span_m"] * average_delta
        sensible_errors[data["summary"]["id"]] = relative(final["sensible_enthalpy_J"], expected, 1.0)
    check("panel_sensible_enthalpy_closed_form_and_separate", max(sensible_errors.values()) < 1e-12, sensible_errors)

    force_signs = all(
        term["force_N"] <= 1e-7 if term["kind"] == "contact" else
        term["force_N"] >= -1e-7 if term["kind"] == "vertical_tie" else True
        for data in reference for term in data["terms"]
    )
    check("unilateral_contact_and_vertical_tie_signs", force_signs, "Contact compression only; tie tension only")
    check("no_actuator_or_prescribed_motion", all(abs(state["support_work_J"]) == 0.0 for state in histories),
          "Only gravity and slab eigenstrain; fixed ground support coordinates do not move")

    half_rows = comparisons["half_step"]
    fine_rows = comparisons["mesh"]["8"]
    check("half_thermal_step_gate", all(row["pass"] for row in half_rows), half_rows)
    check("reference_to_fine_panel_mesh_gate", all(row["pass"] for row in fine_rows), fine_rows)
    check("all_mesh_topologies_declared", set(mesh_runs) == {"2", "8"} and all(len(run) == 3 for run in mesh_runs.values()),
          {key: len(value) for key, value in mesh_runs.items()})

    for data in reference:
        section_inventory = data["inventory"]["section"]
        check("constant_inherited_moduli_" + data["summary"]["id"],
              section_inventory["E_concrete_Pa"] == section_cfg["concrete"]["E20_ksi"] * model.thermo.KSI and
              section_inventory["E_steel_Pa"] == section_cfg["reinforcement"]["E_GPa"] * 1e9,
              {"E_concrete_Pa": section_inventory["E_concrete_Pa"], "E_steel_Pa": section_inventory["E_steel_Pa"]})

    check("scope_flags_remain_closed", not cfg["fire_solved"] and not cfg["heat_transfer_solved"] and
          not cfg["heated_fracture_solved"] and not cfg["material_degradation_solved"] and
          not cfg["geometric_nonlinearity_solved"] and not cfg["blender_changed"] and
          cfg["global_energy_credit_j"] == 0.0,
          "Prescribed-temperature elastic local panel only")
    check("v11h_heat_transfer_fields_remain_null", all(value is None for value in
          thermo_cfg["thermal_properties"]["unused_heat_transfer_fields"].values()),
          thermo_cfg["thermal_properties"]["unused_heat_transfer_fields"])

    return tests
