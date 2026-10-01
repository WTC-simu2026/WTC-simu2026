"""Numerical and scope checks for the bounded V11J conduction coupon."""
from __future__ import annotations

import math
from typing import Any


CASE_IDS = [
    "UNIFORM_ADIABATIC_CONTROL",
    "LINEAR_DIRICHLET_STEADY_CONTROL",
    "SINE_DIRICHLET_TRANSIENT",
    "CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC",
    "TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC",
]


def _finite(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, dict):
        return all(_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(item) for item in value)
    return True


def run(
    configuration: dict[str, Any],
    inherited_thermomechanical: dict[str, Any],
    reference_runs: list[dict[str, Any]],
    replay_runs: list[dict[str, Any]],
    space_refinement: dict[str, Any],
    time_refinement: dict[str, Any],
    sensitivity: list[dict[str, Any]],
    controls: dict[str, Any],
    reference_digest: str,
    replay_digest: str,
) -> list[dict[str, Any]]:
    acceptance = configuration["acceptance"]
    geometry = configuration["geometry"]
    properties = configuration["constant_properties"]
    by_id = {item["summary"]["id"]: item for item in reference_runs}
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, evidence: Any) -> None:
        checks.append({"test": name, "pass": bool(condition), "evidence": evidence})

    converted = float(geometry["equivalent_thickness_in"]) * float(geometry["inch_to_m"])
    check(
        "geometry_units_and_conversion",
        abs(converted - float(geometry["thickness_m"]))
        <= float(acceptance["geometry_conversion_absolute_m"])
        and float(geometry["coupon_area_m2"]) == 1.0,
        {"converted_m": converted, "declared_m": geometry["thickness_m"], "area_m2": geometry["coupon_area_m2"]},
    )
    reconstructed_capacity = float(properties["density_kg_m3"]) * float(properties["specific_heat_j_kg_k"])
    check(
        "constant_property_units_and_capacity",
        abs(reconstructed_capacity - float(properties["volumetric_heat_capacity_j_m3_k"]))
        / reconstructed_capacity
        <= float(acceptance["volumetric_capacity_relative"])
        and all(float(value) > 0.0 for value in properties["conductivity_sensitivity_w_m_k"]),
        {
            "rho_kg_m3": properties["density_kg_m3"],
            "cp_j_kg_k": properties["specific_heat_j_kg_k"],
            "rho_cp_j_m3_k": reconstructed_capacity,
            "k_w_m_k": properties["reference_conductivity_w_m_k"],
        },
    )
    check(
        "v11h_properties_inherited_without_relabeling",
        float(properties["density_kg_m3"])
        == float(inherited_thermomechanical["thermal_properties"]["concrete"]["density_kg_m3"])
        and float(properties["specific_heat_j_kg_k"])
        == float(inherited_thermomechanical["thermal_properties"]["concrete"]["specific_heat_j_kg_k"])
        and inherited_thermomechanical["thermal_properties"]["concrete"]["conductivity_w_m_k"] is None,
        {
            "v11h_rho": inherited_thermomechanical["thermal_properties"]["concrete"]["density_kg_m3"],
            "v11h_cp": inherited_thermomechanical["thermal_properties"]["concrete"]["specific_heat_j_kg_k"],
            "v11h_k": inherited_thermomechanical["thermal_properties"]["concrete"]["conductivity_w_m_k"],
        },
    )
    reference_ids = [item["summary"]["id"] for item in reference_runs]
    replay_ids = [item["summary"]["id"] for item in replay_runs]
    check(
        "declared_cases_are_unique_and_complete",
        reference_ids == replay_ids == CASE_IDS
        and reference_ids == [case["id"] for case in configuration["cases"]]
        and len(reference_ids) == len(set(reference_ids)),
        reference_ids,
    )
    check(
        "reference_and_replay_are_byte_stable_numerically",
        reference_digest == replay_digest,
        {"reference": reference_digest, "replay": replay_digest},
    )
    check(
        "all_numerical_outputs_are_finite",
        _finite(reference_runs)
        and _finite(replay_runs)
        and _finite(space_refinement)
        and _finite(time_refinement)
        and _finite(sensitivity),
        "reference, replay, convergence and sensitivity structures",
    )
    check(
        "saved_v11h_and_v11i_controls_pass",
        controls["V11H"]["status"] == controls["V11I"]["status"] == "PASS"
        and all(controls["V11H"]["hash_checks"].values())
        and all(controls["V11I"]["hash_checks"].values())
        and not controls["old_drivers_reexecuted"],
        {
            "V11H": controls["V11H"]["status"],
            "V11I": controls["V11I"]["status"],
            "old_drivers_reexecuted": controls["old_drivers_reexecuted"],
        },
    )

    uniform = by_id["UNIFORM_ADIABATIC_CONTROL"]
    uniform_summary = uniform["summary"]
    check(
        "uniform_adiabatic_temperature_exact",
        float(uniform_summary["terminal_field_linf_error_k"])
        <= float(acceptance["uniform_temperature_absolute_k"])
        and abs(float(uniform_summary["final_mean_temperature_c"]) - 60.0)
        <= float(acceptance["uniform_temperature_absolute_k"]),
        {
            "linf_k": uniform_summary["terminal_field_linf_error_k"],
            "mean_c": uniform_summary["final_mean_temperature_c"],
        },
    )
    check(
        "uniform_adiabatic_zero_flux_and_enthalpy_change",
        uniform_summary["enthalpy_change_j_m2"] == 0.0
        and uniform_summary["cumulative_inward_heat_j_m2"] == 0.0
        and all(
            row["bottom_inward_flux_w_m2"] == row["top_inward_flux_w_m2"] == 0.0
            for row in uniform["history"]
        ),
        {
            "delta_h_j_m2": uniform_summary["enthalpy_change_j_m2"],
            "q_j_m2": uniform_summary["cumulative_inward_heat_j_m2"],
        },
    )

    linear = by_id["LINEAR_DIRICHLET_STEADY_CONTROL"]
    linear_summary = linear["summary"]
    linear_terminal = linear["history"][-1]
    check(
        "linear_dirichlet_profile_exact",
        float(linear_summary["terminal_field_linf_error_k"])
        <= float(acceptance["linear_temperature_absolute_k"])
        and abs(float(linear_summary["final_mean_temperature_c"]) - 70.0)
        <= float(acceptance["linear_temperature_absolute_k"]),
        {
            "linf_k": linear_summary["terminal_field_linf_error_k"],
            "mean_c": linear_summary["final_mean_temperature_c"],
        },
    )
    check(
        "linear_dirichlet_equal_opposite_face_fluxes",
        abs(float(linear_terminal["net_inward_flux_w_m2"]))
        <= float(acceptance["steady_net_flux_absolute_w_m2"])
        and abs(float(linear_terminal["bottom_inward_flux_w_m2"]) + 100.0 / float(geometry["thickness_m"]))
        <= float(acceptance["steady_net_flux_absolute_w_m2"])
        and abs(float(linear_terminal["top_inward_flux_w_m2"]) - 100.0 / float(geometry["thickness_m"]))
        <= float(acceptance["steady_net_flux_absolute_w_m2"]),
        {
            "bottom_w_m2": linear_terminal["bottom_inward_flux_w_m2"],
            "top_w_m2": linear_terminal["top_inward_flux_w_m2"],
            "net_w_m2": linear_terminal["net_inward_flux_w_m2"],
        },
    )

    sine_summary = by_id["SINE_DIRICHLET_TRANSIENT"]["summary"]
    check(
        "sine_transient_analytical_field",
        float(sine_summary["terminal_field_linf_error_k"])
        <= float(acceptance["reference_sine_linf_k"])
        and abs(float(sine_summary["terminal_mean_error_k"]))
        <= float(acceptance["reference_analytic_mean_absolute_k"]),
        {
            "linf_k": sine_summary["terminal_field_linf_error_k"],
            "mean_error_k": sine_summary["terminal_mean_error_k"],
            "fourier": sine_summary["terminal_fourier_number"],
        },
    )

    flux_run = by_id["CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC"]
    flux_summary = flux_run["summary"]
    check(
        "constant_flux_mean_temperature_analytical",
        abs(float(flux_summary["terminal_mean_error_k"]))
        <= float(acceptance["flux_mean_temperature_absolute_k"]),
        {
            "numerical_c": flux_summary["final_mean_temperature_c"],
            "analytical_c": flux_summary["analytical_final_mean_temperature_c"],
            "error_k": flux_summary["terminal_mean_error_k"],
        },
    )
    expected_flux_energy = (
        float(next(case for case in configuration["cases"] if case["id"] == flux_summary["id"])["top_boundary"]["inward_flux_w_m2"])
        * float(flux_summary["duration_s"])
    )
    check(
        "constant_flux_enthalpy_gain_analytical",
        abs(float(flux_summary["enthalpy_change_j_m2"]) - expected_flux_energy)
        <= float(acceptance["total_energy_absolute_j_m2"])
        and abs(float(flux_summary["cumulative_inward_heat_j_m2"]) - expected_flux_energy)
        <= float(acceptance["total_energy_absolute_j_m2"]),
        {
            "expected_j_m2": expected_flux_energy,
            "delta_h_j_m2": flux_summary["enthalpy_change_j_m2"],
            "integrated_flux_j_m2": flux_summary["cumulative_inward_heat_j_m2"],
        },
    )

    step_summary = by_id["TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC"]["summary"]
    check(
        "mixed_boundary_step_analytical_field",
        float(step_summary["terminal_field_linf_error_k"])
        <= float(acceptance["reference_step_linf_k"])
        and abs(float(step_summary["terminal_mean_error_k"]))
        <= float(acceptance["reference_analytic_mean_absolute_k"]),
        {
            "linf_k": step_summary["terminal_field_linf_error_k"],
            "mean_error_k": step_summary["terminal_mean_error_k"],
            "fourier": step_summary["terminal_fourier_number"],
        },
    )

    energy_rows = [item["summary"] for item in reference_runs]
    incremental_pass = all(
        float(row["maximum_increment_energy_residual_absolute_j_m2"])
        <= float(acceptance["increment_energy_absolute_j_m2"])
        or float(row["maximum_increment_energy_residual_relative"])
        <= float(acceptance["increment_energy_relative"])
        for row in energy_rows
    )
    total_pass = all(
        float(row["maximum_total_energy_residual_absolute_j_m2"])
        <= float(acceptance["total_energy_absolute_j_m2"])
        or float(row["maximum_total_energy_residual_relative"])
        <= float(acceptance["total_energy_relative"])
        for row in energy_rows
    )
    check(
        "all_incremental_flux_enthalpy_balances",
        incremental_pass,
        {
            row["id"]: {
                "absolute_j_m2": row["maximum_increment_energy_residual_absolute_j_m2"],
                "relative": row["maximum_increment_energy_residual_relative"],
            }
            for row in energy_rows
        },
    )
    check(
        "all_total_flux_enthalpy_balances",
        total_pass,
        {
            row["id"]: {
                "absolute_j_m2": row["maximum_total_energy_residual_absolute_j_m2"],
                "relative": row["maximum_total_energy_residual_relative"],
            }
            for row in energy_rows
        },
    )
    check(
        "discrete_maximum_principle",
        max(float(row["maximum_principle_violation_k"]) for row in energy_rows)
        <= float(acceptance["maximum_principle_tolerance_k"]),
        {row["id"]: row["maximum_principle_violation_k"] for row in energy_rows},
    )
    check(
        "stored_histories_cover_initial_and_terminal_states",
        all(
            item["history"][0]["step"] == 0
            and item["history"][-1]["step"] == item["summary"]["step_count"]
            and item["history"][0]["time_s"] == 0.0
            and item["history"][-1]["time_s"] == item["summary"]["duration_s"]
            and len(item["history"]) == configuration["discretization"]["stored_history_intervals"] + 1
            for item in reference_runs
        ),
        {item["summary"]["id"]: len(item["history"]) for item in reference_runs},
    )
    check(
        "profile_coordinates_and_counts",
        all(
            len(item["profiles"]) == len(item["history"])
            and all(len(profile["x_m"]) == item["summary"]["cell_count"] for profile in item["profiles"])
            for item in reference_runs
        ),
        {
            item["summary"]["id"]: {
                "snapshots": len(item["profiles"]),
                "cells": item["summary"]["cell_count"],
            }
            for item in reference_runs
        },
    )

    space_rows = space_refinement["rows"]
    space_errors = [float(row["terminal_field_linf_error_k"]) for row in space_rows]
    space_orders = [float(value) for value in space_refinement["observed_orders"]]
    check(
        "spatial_operator_error_decreases_monotonically",
        all(fine < coarse for coarse, fine in zip(space_errors, space_errors[1:])),
        space_errors,
    )
    check(
        "spatial_operator_second_order",
        all(
            float(acceptance["minimum_space_order"]) <= order <= float(acceptance["maximum_space_order"])
            for order in space_orders
        ),
        space_orders,
    )
    for case_id, data in time_refinement.items():
        errors = [float(row["terminal_field_linf_error_k"]) for row in data["rows"]]
        orders = [float(value) for value in data["observed_orders"]]
        check(
            f"time_error_decreases_{case_id.lower()}",
            all(fine < coarse for coarse, fine in zip(errors, errors[1:])),
            errors,
        )
        check(
            f"backward_euler_first_order_{case_id.lower()}",
            all(
                float(acceptance["minimum_time_order"]) <= order <= float(acceptance["maximum_time_order"])
                for order in orders
            ),
            orders,
        )

    conductivity_values = [float(row["conductivity_w_m_k"]) for row in sensitivity]
    sensitivity_means = [float(row["final_mean_temperature_c"]) for row in sensitivity]
    sensitivity_bottoms = [float(row["final_bottom_cell_temperature_c"]) for row in sensitivity]
    sensitivity_centroids = [float(row["thermal_centroid_depth_from_top_m"]) for row in sensitivity]
    check(
        "conductivity_sensitivity_declared_order",
        conductivity_values == sorted(float(value) for value in properties["conductivity_sensitivity_w_m_k"]),
        conductivity_values,
    )
    check(
        "conductivity_sensitivity_heating_is_monotonic",
        all(fine > coarse for coarse, fine in zip(sensitivity_means, sensitivity_means[1:]))
        and all(fine > coarse for coarse, fine in zip(sensitivity_bottoms, sensitivity_bottoms[1:]))
        and all(fine > coarse for coarse, fine in zip(sensitivity_centroids, sensitivity_centroids[1:])),
        {
            "mean_c": sensitivity_means,
            "bottom_cell_c": sensitivity_bottoms,
            "thermal_centroid_depth_m": sensitivity_centroids,
        },
    )
    check(
        "constant_flux_and_step_means_do_not_decrease",
        flux_summary["minimum_mean_step_change_k"] >= -1e-12
        and step_summary["minimum_mean_step_change_k"] >= -1e-12,
        {
            "flux_minimum_step_k": flux_summary["minimum_mean_step_change_k"],
            "step_minimum_step_k": step_summary["minimum_mean_step_change_k"],
        },
    )
    check(
        "primary_method_sources_and_context_limits_declared",
        len(configuration["method_sources"]) == 3
        and all(source["url"].startswith("https://") for source in configuration["method_sources"])
        and "not a calibrated property" in properties["conductivity_status"],
        [source["id"] for source in configuration["method_sources"]],
    )
    check(
        "thermal_only_scope_and_zero_global_credit",
        configuration["heat_transfer_solved"]
        and not configuration["fire_solved"]
        and not configuration["panel_coupled"]
        and not configuration["thermal_strain_solved"]
        and not configuration["heated_fracture_solved"]
        and not configuration["material_properties_degraded"]
        and not configuration["blender_changed"]
        and float(configuration["global_energy_credit_j"]) == 0.0
        and all(
            float(item["summary"]["mechanical_energy_j_m2"]) == 0.0
            and float(item["summary"]["global_energy_credit_j"]) == 0.0
            for item in reference_runs
        ),
        {
            "heat_transfer_solved": configuration["heat_transfer_solved"],
            "fire_solved": configuration["fire_solved"],
            "panel_coupled": configuration["panel_coupled"],
            "heated_fracture_solved": configuration["heated_fracture_solved"],
            "global_energy_credit_j": configuration["global_energy_credit_j"],
        },
    )
    return checks
