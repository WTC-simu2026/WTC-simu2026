"""Numerical acceptance checks for the bounded V11K surface-exchange coupon."""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def run(
    configuration: dict[str, Any],
    inherited_configuration: dict[str, Any],
    reference_runs: list[dict[str, Any]],
    replay_runs: list[dict[str, Any]],
    space: dict[str, Any],
    temporal: dict[str, Any],
    sensitivity: list[dict[str, Any]],
    controls: dict[str, Any],
    reference_digest: str,
    replay_digest: str,
) -> list[dict[str, Any]]:
    acceptance = configuration["acceptance"]
    cases = configuration["cases"]
    summaries = {item["summary"]["id"]: item["summary"] for item in reference_runs}
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, evidence: Any) -> None:
        checks.append({"test": name, "pass": bool(condition), "evidence": evidence})

    expected_ids = [item["id"] for item in cases]
    actual_ids = list(summaries)
    check(
        "iteration_seed_and_no_random_draw",
        configuration["iteration"] == "V11K"
        and configuration["random_seed"] == 1101111
        and not configuration["random_draw_used"],
        {"iteration": configuration["iteration"], "seed": configuration["random_seed"]},
    )
    conversion_error = abs(
        float(configuration["geometry"]["equivalent_thickness_in"])
        * float(configuration["geometry"]["inch_to_m"])
        - float(configuration["geometry"]["thickness_m"])
    )
    check(
        "geometry_conversion",
        conversion_error <= acceptance["geometry_conversion_absolute_m"],
        {"absolute_error_m": conversion_error},
    )
    own = configuration["constant_properties"]
    inherited = inherited_configuration["constant_properties"]
    property_errors = {
        "density": abs(float(own["density_kg_m3"]) - float(inherited["density_kg_m3"])),
        "specific_heat": abs(float(own["specific_heat_j_kg_k"]) - float(inherited["specific_heat_j_kg_k"])),
        "conductivity": abs(float(own["conductivity_w_m_k"]) - float(inherited["reference_conductivity_w_m_k"])),
    }
    check(
        "v11j_constant_properties_preserved",
        max(property_errors.values()) <= acceptance["constant_property_match_absolute"],
        property_errors,
    )
    volumetric_error = abs(
        float(own["density_kg_m3"]) * float(own["specific_heat_j_kg_k"])
        - float(own["volumetric_heat_capacity_j_m3_k"])
    )
    check(
        "volumetric_capacity_units",
        volumetric_error <= acceptance["constant_property_match_absolute"],
        {"absolute_j_m3_k": volumetric_error},
    )
    sigma_error = abs(float(configuration["surface_exchange"]["stefan_boltzmann_w_m2_k4"]) - 5.670374419e-8)
    check(
        "codata_stefan_boltzmann_constant",
        sigma_error <= acceptance["stefan_boltzmann_absolute"],
        {"absolute_error": sigma_error},
    )
    check(
        "absolute_temperature_conversion_declared",
        configuration["surface_exchange"]["celsius_to_kelvin_offset"] == 273.15
        and "kelvin" in configuration["numerical_method"]["absolute_temperature_policy"].lower(),
        configuration["numerical_method"]["absolute_temperature_policy"],
    )
    check(
        "six_unique_declared_cases",
        actual_ids == expected_ids and len(actual_ids) == len(set(actual_ids)) == 6,
        actual_ids,
    )
    check(
        "primary_official_source_manifest",
        len(configuration["method_sources"]) == 3
        and all("nist" in item["url"].lower() for item in configuration["method_sources"]),
        [item["id"] for item in configuration["method_sources"]],
    )
    check(
        "saved_v11j_control",
        controls["V11J"]["status"] == "PASS" and not controls["old_driver_reexecuted"],
        controls,
    )
    check(
        "deterministic_replay_digest",
        reference_digest == replay_digest,
        {"reference": reference_digest, "replay": replay_digest},
    )

    equilibrium = summaries["COMBINED_EQUILIBRIUM_CONTROL"]
    equilibrium_temperature_error = max(
        abs(equilibrium["final_minimum_temperature_c"] - 60.0),
        abs(equilibrium["final_maximum_temperature_c"] - 60.0),
    )
    equilibrium_flux = max(
        abs(equilibrium[key])
        for key in (
            "final_bottom_convective_inward_flux_w_m2",
            "final_bottom_radiative_inward_flux_w_m2",
            "final_top_convective_inward_flux_w_m2",
            "final_top_radiative_inward_flux_w_m2",
        )
    )
    check(
        "combined_equilibrium_temperature",
        equilibrium_temperature_error <= acceptance["equilibrium_temperature_absolute_k"],
        {"maximum_error_k": equilibrium_temperature_error},
    )
    check(
        "combined_equilibrium_zero_components",
        equilibrium_flux <= acceptance["equilibrium_flux_absolute_w_m2"],
        {"maximum_component_w_m2": equilibrium_flux},
    )
    check(
        "combined_equilibrium_zero_energy",
        abs(equilibrium["enthalpy_change_j_m2"]) <= acceptance["total_energy_absolute_j_m2"]
        and abs(equilibrium["cumulative_total_inward_heat_j_m2"]) <= acceptance["total_energy_absolute_j_m2"],
        {
            "enthalpy_j_m2": equilibrium["enthalpy_change_j_m2"],
            "heat_j_m2": equilibrium["cumulative_total_inward_heat_j_m2"],
        },
    )

    steady_ids = [
        "CONVECTION_STEADY_TWO_SIDED",
        "RADIATION_STEADY_TWO_SIDED",
        "COMBINED_STEADY_TWO_SIDED",
    ]
    steady_temperature_errors = {name: summaries[name]["terminal_field_linf_error_k"] for name in steady_ids}
    check(
        "three_steady_linear_fields",
        max(float(value) for value in steady_temperature_errors.values()) <= acceptance["steady_temperature_linf_k"],
        steady_temperature_errors,
    )
    steady_flux_errors = {
        name: max(
            abs(summaries[name]["final_top_total_inward_flux_w_m2"] - summaries[name]["steady_reference"]["heat_rate_top_to_bottom_w_m2"]),
            abs(summaries[name]["final_bottom_total_inward_flux_w_m2"] + summaries[name]["steady_reference"]["heat_rate_top_to_bottom_w_m2"]),
        )
        for name in steady_ids
    }
    check(
        "three_steady_opposite_face_fluxes",
        max(steady_flux_errors.values()) <= acceptance["steady_flux_absolute_w_m2"],
        steady_flux_errors,
    )
    convection = summaries["CONVECTION_STEADY_TWO_SIDED"]
    length = float(configuration["geometry"]["thickness_m"])
    conductivity = float(own["conductivity_w_m_k"])
    expected_convection_rate = 100.0 / (1.0 / 15.0 + length / conductivity + 1.0 / 25.0)
    convection_rate_error = abs(convection["steady_reference"]["heat_rate_top_to_bottom_w_m2"] - expected_convection_rate)
    check(
        "convection_closed_resistance_reference",
        convection_rate_error <= acceptance["steady_flux_absolute_w_m2"],
        {"calculated": convection["steady_reference"]["heat_rate_top_to_bottom_w_m2"], "closed_form": expected_convection_rate},
    )
    convection_radiation_leak = max(
        abs(convection["final_bottom_radiative_inward_flux_w_m2"]),
        abs(convection["final_top_radiative_inward_flux_w_m2"]),
    )
    check(
        "convection_only_has_zero_radiation",
        convection_radiation_leak <= acceptance["equilibrium_flux_absolute_w_m2"],
        {"maximum_radiative_flux_w_m2": convection_radiation_leak},
    )
    radiation = summaries["RADIATION_STEADY_TWO_SIDED"]
    radiation_convection_leak = max(
        abs(radiation["final_bottom_convective_inward_flux_w_m2"]),
        abs(radiation["final_top_convective_inward_flux_w_m2"]),
    )
    check(
        "radiation_only_has_zero_convection",
        radiation_convection_leak <= acceptance["equilibrium_flux_absolute_w_m2"],
        {"maximum_convective_flux_w_m2": radiation_convection_leak},
    )

    eigenmode = summaries["CONVECTION_EIGENMODE_TRANSIENT"]
    check(
        "robin_eigenmode_terminal_field",
        eigenmode["terminal_field_linf_error_k"] <= acceptance["eigenmode_reference_linf_k"],
        {"linf_k": eigenmode["terminal_field_linf_error_k"]},
    )
    check(
        "robin_eigenmode_terminal_mean",
        abs(eigenmode["terminal_mean_error_k"]) <= acceptance["eigenmode_mean_absolute_k"],
        {"absolute_k": abs(eigenmode["terminal_mean_error_k"])},
    )

    maximum_surface_balance = max(item["maximum_surface_balance_residual_w_m2"] for item in summaries.values())
    check(
        "massless_surface_balances",
        maximum_surface_balance <= acceptance["surface_balance_absolute_w_m2"],
        {"maximum_w_m2": maximum_surface_balance},
    )
    maximum_nonlinear_residual = max(item["maximum_nonlinear_residual_w_m2"] for item in summaries.values())
    check(
        "global_nonlinear_residual",
        maximum_nonlinear_residual <= acceptance["nonlinear_residual_absolute_w_m2"],
        {"maximum_w_m2": maximum_nonlinear_residual},
    )
    maximum_newton_iterations = max(item["maximum_newton_iterations"] for item in summaries.values())
    check(
        "newton_iteration_gate",
        maximum_newton_iterations <= acceptance["maximum_newton_iterations"],
        {"maximum_iterations": maximum_newton_iterations},
    )
    maximum_increment_absolute = max(item["maximum_increment_energy_residual_absolute_j_m2"] for item in summaries.values())
    maximum_increment_relative = max(item["maximum_increment_energy_residual_relative"] for item in summaries.values())
    check(
        "increment_energy_balance",
        maximum_increment_absolute <= acceptance["increment_energy_absolute_j_m2"]
        and maximum_increment_relative <= acceptance["increment_energy_relative"],
        {"absolute_j_m2": maximum_increment_absolute, "relative": maximum_increment_relative},
    )
    maximum_total_absolute = max(item["maximum_total_energy_residual_absolute_j_m2"] for item in summaries.values())
    relative_energy_cases = [
        item["maximum_total_energy_residual_relative"]
        for item in summaries.values()
        if abs(item["enthalpy_change_j_m2"]) > 1.0
    ]
    maximum_total_relative = max(relative_energy_cases, default=0.0)
    check(
        "total_energy_balance",
        maximum_total_absolute <= acceptance["total_energy_absolute_j_m2"]
        and maximum_total_relative <= acceptance["total_energy_relative"],
        {"absolute_j_m2": maximum_total_absolute, "relative": maximum_total_relative},
    )
    component_ledger = max(item["maximum_component_ledger_residual_j_m2"] for item in summaries.values())
    check(
        "convective_radiative_component_ledger",
        component_ledger <= acceptance["component_ledger_absolute_j_m2"],
        {"absolute_j_m2": component_ledger},
    )
    maximum_principle = max(item["maximum_principle_violation_k"] for item in summaries.values())
    check(
        "temperature_maximum_principle",
        maximum_principle <= acceptance["maximum_principle_tolerance_k"],
        {"maximum_violation_k": maximum_principle},
    )
    step = summaries["COMBINED_STEP_TRANSIENT"]
    check(
        "combined_step_heats_monotonically",
        step["mean_temperature_changes_monotonic_nonnegative"]
        and step["final_mean_temperature_c"] > step["initial_mean_temperature_c"],
        {"initial_c": step["initial_mean_temperature_c"], "final_c": step["final_mean_temperature_c"]},
    )
    check(
        "combined_step_positive_top_components",
        step["final_top_convective_inward_flux_w_m2"] > 0.0
        and step["final_top_radiative_inward_flux_w_m2"] > 0.0,
        {
            "convective_w_m2": step["final_top_convective_inward_flux_w_m2"],
            "radiative_w_m2": step["final_top_radiative_inward_flux_w_m2"],
        },
    )
    combined_case = next(item for item in cases if item["id"] == "COMBINED_STEP_TRANSIENT")
    surface_c = step["final_top_surface_temperature_c"]
    boundary = combined_case["top_boundary"]
    sigma = float(configuration["surface_exchange"]["stefan_boltzmann_w_m2_k4"])
    recomputed_radiation = float(boundary["emissivity"]) * sigma * (
        (float(boundary["radiative_temperature_c"]) + 273.15) ** 4
        - (surface_c + 273.15) ** 4
    )
    radiation_formula_error = abs(recomputed_radiation - step["final_top_radiative_inward_flux_w_m2"])
    check(
        "radiation_fourth_power_kelvin_formula",
        radiation_formula_error <= acceptance["steady_flux_absolute_w_m2"],
        {"absolute_w_m2": radiation_formula_error},
    )

    space_errors = [float(item["linf_error_k"]) for item in space["rows"]]
    space_orders = [float(value) for value in space["observed_orders"]]
    check(
        "space_errors_decrease",
        all(fine < coarse for coarse, fine in zip(space_errors, space_errors[1:])),
        space_errors,
    )
    check(
        "space_orders_second_order",
        min(space_orders) >= acceptance["minimum_space_order"]
        and max(space_orders) <= acceptance["maximum_space_order"],
        space_orders,
    )
    time_errors = [float(item["linf_error_k"]) for item in temporal["rows"]]
    time_orders = [float(value) for value in temporal["observed_orders"]]
    check(
        "time_errors_decrease",
        all(fine < coarse for coarse, fine in zip(time_errors, time_errors[1:])),
        time_errors,
    )
    check(
        "backward_euler_time_orders",
        min(time_orders) >= acceptance["minimum_time_order"]
        and max(time_orders) <= acceptance["maximum_time_order"],
        time_orders,
    )

    h_rows = sorted((item for item in sensitivity if item["parameter"] == "top_h_w_m2_k"), key=lambda item: item["value"])
    emissivity_rows = sorted((item for item in sensitivity if item["parameter"] == "top_emissivity"), key=lambda item: item["value"])
    h_enthalpy = [float(item["enthalpy_change_j_m2"]) for item in h_rows]
    emissivity_enthalpy = [float(item["enthalpy_change_j_m2"]) for item in emissivity_rows]
    check(
        "top_h_sensitivity_monotonic",
        len(h_rows) == 3 and all(high > low for low, high in zip(h_enthalpy, h_enthalpy[1:])),
        [{"h": item["value"], "enthalpy_j_m2": item["enthalpy_change_j_m2"]} for item in h_rows],
    )
    check(
        "top_emissivity_sensitivity_monotonic",
        len(emissivity_rows) == 3 and all(high > low for low, high in zip(emissivity_enthalpy, emissivity_enthalpy[1:])),
        [{"emissivity": item["value"], "enthalpy_j_m2": item["enthalpy_change_j_m2"]} for item in emissivity_rows],
    )
    zero_emissivity_radiation = abs(emissivity_rows[0]["cumulative_top_radiative_j_m2"])
    check(
        "zero_emissivity_zero_top_radiation",
        emissivity_rows[0]["value"] == 0.0
        and zero_emissivity_radiation <= acceptance["total_energy_absolute_j_m2"],
        {"radiative_j_m2": zero_emissivity_radiation},
    )
    check(
        "sensitivity_is_conditional_not_probability",
        "synthetic" in configuration["surface_exchange"]["coefficient_status"].lower()
        and not acceptance["require_historical_outcome"],
        configuration["surface_exchange"]["coefficient_status"],
    )
    check(
        "no_mechanical_or_fire_coupling",
        configuration["fire_solved"] is False
        and configuration["panel_coupled"] is False
        and configuration["thermal_strain_solved"] is False
        and configuration["heated_fracture_solved"] is False
        and configuration["global_energy_credit_j"] == 0.0,
        {
            "fire": configuration["fire_solved"],
            "panel": configuration["panel_coupled"],
            "global_energy_credit_j": configuration["global_energy_credit_j"],
        },
    )
    check(
        "no_property_degradation_or_blender_change",
        configuration["material_properties_degraded"] is False
        and configuration["blender_changed"] is False,
        {
            "degraded": configuration["material_properties_degraded"],
            "blender_changed": configuration["blender_changed"],
        },
    )
    check(
        "stored_histories_have_fixed_count",
        all(len(item["history"]) == 41 for item in reference_runs),
        {item["summary"]["id"]: len(item["history"]) for item in reference_runs},
    )
    return checks
