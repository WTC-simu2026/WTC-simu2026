"""Independent read-back audit for serialized V11J artifacts.

The conduction kernel is deliberately not imported.  Analytical fields,
enthalpy arithmetic, convergence orders and hashes are reconstructed here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11j_transient_conduction_predeclaration.json"


def read(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def analytic_field(
    case: dict[str, Any],
    x: list[float],
    time_s: float,
    length: float,
    rho: float,
    cp: float,
    conductivity: float,
    terms: int,
) -> list[float] | None:
    case_id = case["id"]
    if case_id == "UNIFORM_ADIABATIC_CONTROL":
        return [float(case["initial"]["temperature_c"])] * len(x)
    if case_id == "LINEAR_DIRICHLET_STEADY_CONTROL":
        bottom = float(case["initial"]["bottom_temperature_c"])
        top = float(case["initial"]["top_temperature_c"])
        return [bottom + (top - bottom) * value / length for value in x]
    alpha = conductivity / (rho * cp)
    if case_id == "SINE_DIRICHLET_TRANSIENT":
        reference = float(case["initial"]["reference_temperature_c"])
        amplitude = float(case["initial"]["amplitude_k"])
        mode = int(case["initial"].get("mode", 1))
        decay = math.exp(-alpha * (mode * math.pi / length) ** 2 * time_s)
        return [reference + amplitude * math.sin(mode * math.pi * value / length) * decay for value in x]
    if case_id == "CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC":
        return None
    if case_id == "TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC":
        initial = float(case["initial"]["temperature_c"])
        surface = float(case["top_boundary"]["temperature_c"])
        if time_s <= 0.0:
            return [initial] * len(x)
        fourier = alpha * time_s / length**2
        values = []
        for location in x:
            theta = math.fsum(
                2.0
                * ((-1.0) ** n)
                * math.cos((n + 0.5) * math.pi * location / length)
                * math.exp(-((n + 0.5) * math.pi) ** 2 * fourier)
                / ((n + 0.5) * math.pi)
                for n in range(terms)
            )
            values.append(surface + (initial - surface) * theta)
        return values
    raise ValueError(case_id)


def analytic_mean(
    case: dict[str, Any],
    time_s: float,
    length: float,
    rho: float,
    cp: float,
    conductivity: float,
    terms: int,
) -> float:
    case_id = case["id"]
    if case_id == "UNIFORM_ADIABATIC_CONTROL":
        return float(case["initial"]["temperature_c"])
    if case_id == "LINEAR_DIRICHLET_STEADY_CONTROL":
        return 0.5 * (
            float(case["initial"]["bottom_temperature_c"])
            + float(case["initial"]["top_temperature_c"])
        )
    alpha = conductivity / (rho * cp)
    if case_id == "SINE_DIRICHLET_TRANSIENT":
        reference = float(case["initial"]["reference_temperature_c"])
        amplitude = float(case["initial"]["amplitude_k"])
        mode = int(case["initial"].get("mode", 1))
        mode_average = 0.0 if mode % 2 == 0 else 2.0 / (mode * math.pi)
        return reference + amplitude * mode_average * math.exp(-alpha * (mode * math.pi / length) ** 2 * time_s)
    if case_id == "CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC":
        initial = float(case["initial"]["temperature_c"])
        flux = float(case["top_boundary"]["inward_flux_w_m2"])
        return initial + flux * time_s / (rho * cp * length)
    if case_id == "TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC":
        initial = float(case["initial"]["temperature_c"])
        surface = float(case["top_boundary"]["temperature_c"])
        if time_s <= 0.0:
            return initial
        fourier = alpha * time_s / length**2
        theta = math.fsum(
            2.0 * math.exp(-((n + 0.5) * math.pi) ** 2 * fourier) / ((n + 0.5) * math.pi) ** 2
            for n in range(terms)
        )
        return surface + (initial - surface) * theta
    raise ValueError(case_id)


def observed_orders(rows: list[dict[str, Any]], error_key: str, resolution_key: str) -> list[float]:
    values = []
    for coarse, fine in zip(rows, rows[1:]):
        values.append(
            math.log(float(coarse[error_key]) / float(fine[error_key]))
            / math.log(float(fine[resolution_key]) / float(coarse[resolution_key]))
        )
    return values


def audit(directory: Path) -> dict[str, Any]:
    configuration = read(CONFIG)
    manifest = read(directory / "offline_manifest.json")
    result = read(directory / "results_v11j.json")
    cases_saved = read(directory / "conduction_cases.json")
    convergence = read(directory / "space_time_convergence.json")
    sensitivity = read(directory / "conductivity_sensitivity.json")
    controls = read(directory / "inherited_controls.json")
    ledger = read(directory / "thermal_property_ledger.json")
    numerical = read(directory / "numerical_audit.json")
    source = read(directory / "source_manifest.json")
    profiles_csv = csv_rows(directory / "temperature_profiles.csv")
    flux_csv = csv_rows(directory / "boundary_flux_history.csv")
    energy_csv = csv_rows(directory / "energy_ledger.csv")
    convergence_csv = csv_rows(directory / "space_time_convergence.csv")
    sensitivity_csv = csv_rows(directory / "conductivity_sensitivity.csv")
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, evidence: Any) -> None:
        checks.append({"test": name, "pass": bool(condition), "evidence": evidence})

    output_hashes = {
        name: (directory / name).is_file() and sha(directory / name) == expected
        for name, expected in manifest["output_sha256"].items()
    }
    input_hashes = {
        name: (ROOT / name).is_file() and sha(ROOT / name) == expected
        for name, expected in manifest["input_sha256"].items()
    }
    check(
        "saved_output_hashes",
        all(output_hashes.values()),
        {"count": len(output_hashes), "failed": [name for name, passed in output_hashes.items() if not passed]},
    )
    check(
        "frozen_input_and_protected_hashes",
        all(input_hashes.values()),
        {"count": len(input_hashes), "failed": [name for name, passed in input_hashes.items() if not passed]},
    )
    check(
        "manifest_identity_and_integrity",
        manifest["iteration"] == "V11J"
        and manifest["implementation_status"] == "PASS"
        and manifest["input_and_protected_unchanged"]
        and manifest["manifest_excludes_itself"]
        and "offline_manifest.json" not in manifest["output_sha256"],
        {
            "iteration": manifest["iteration"],
            "status": manifest["implementation_status"],
            "unchanged": manifest["input_and_protected_unchanged"],
        },
    )
    check(
        "implementation_tests_saved_as_pass",
        result["iteration"] == numerical["iteration"] == "V11J"
        and result["status"] == numerical["status"] == "PASS"
        and result["test_count"] == result["tests_passed"] == numerical["test_count"]
        and len(numerical["tests"]) == numerical["test_count"]
        and all(item["pass"] for item in numerical["tests"]),
        {"tests": result["test_count"], "passed": result["tests_passed"], "status": result["status"]},
    )

    case_ids = [item["summary"]["id"] for item in cases_saved]
    declared_ids = [item["id"] for item in configuration["cases"]]
    state_count = sum(len(item["history"]) for item in cases_saved)
    check(
        "saved_case_and_state_counts",
        case_ids == declared_ids
        and len(case_ids) == len(set(case_ids)) == result["case_count"] == 5
        and state_count == result["reference_state_count"] == 205,
        {"ids": case_ids, "states": state_count},
    )
    expected_profile_rows = sum(
        len(item["profiles"]) * int(item["summary"]["cell_count"])
        for item in cases_saved
    )
    check(
        "saved_csv_row_counts",
        len(profiles_csv) == expected_profile_rows
        and len(flux_csv) == len(energy_csv) == state_count
        and len(convergence_csv) == 12
        and len(sensitivity_csv) == 3,
        {
            "profiles": len(profiles_csv),
            "expected_profiles": expected_profile_rows,
            "flux": len(flux_csv),
            "energy": len(energy_csv),
            "convergence": len(convergence_csv),
            "sensitivity": len(sensitivity_csv),
        },
    )
    reconstructed_numeric = digest({
        "reference_summaries": [item["summary"] for item in cases_saved],
        "space_refinement": convergence["space"],
        "time_refinement": convergence["time"],
        "conductivity_sensitivity": sensitivity,
    })
    check(
        "saved_numerical_digest_reconstructed",
        reconstructed_numeric == result["numerical_digest_sha256"],
        {"saved": result["numerical_digest_sha256"], "reconstructed": reconstructed_numeric},
    )
    reference_digest = digest(cases_saved)
    check(
        "saved_reference_digest_reconstructed",
        reference_digest == numerical["reference_digest_sha256"] == numerical["replay_digest_sha256"],
        {
            "saved_reference": numerical["reference_digest_sha256"],
            "saved_replay": numerical["replay_digest_sha256"],
            "reconstructed": reference_digest,
        },
    )

    geometry = configuration["geometry"]
    properties = configuration["constant_properties"]
    length = float(geometry["thickness_m"])
    rho = float(properties["density_kg_m3"])
    cp = float(properties["specific_heat_j_kg_k"])
    k = float(properties["reference_conductivity_w_m_k"])
    terms = int(configuration["analytical_series_terms"])
    check(
        "geometry_and_property_arithmetic",
        abs(float(geometry["equivalent_thickness_in"]) * float(geometry["inch_to_m"]) - length)
        <= float(configuration["acceptance"]["geometry_conversion_absolute_m"])
        and abs(rho * cp - float(properties["volumetric_heat_capacity_j_m3_k"]))
        / (rho * cp)
        <= float(configuration["acceptance"]["volumetric_capacity_relative"]),
        {"length_m": length, "rho_cp_j_m3_k": rho * cp, "k_w_m_k": k},
    )

    cases_by_id = {case["id"]: case for case in configuration["cases"]}
    analytic_differences = {}
    analytic_errors = {}
    mean_differences = {}
    for saved in cases_saved:
        summary = saved["summary"]
        case = cases_by_id[summary["id"]]
        terminal = saved["profiles"][-1]
        reconstructed = analytic_field(
            case, terminal["x_m"], float(terminal["time_s"]), length, rho, cp, k, terms
        )
        reconstructed_mean = analytic_mean(case, float(summary["duration_s"]), length, rho, cp, k, terms)
        mean_differences[summary["id"]] = abs(reconstructed_mean - float(summary["analytical_final_mean_temperature_c"]))
        if reconstructed is None:
            analytic_differences[summary["id"]] = None
            analytic_errors[summary["id"]] = None
        else:
            saved_analytic = terminal["analytical_temperature_c"]
            analytic_differences[summary["id"]] = max(
                abs(float(a) - float(b)) for a, b in zip(reconstructed, saved_analytic)
            )
            numerical_temperature = terminal["temperature_c"]
            linf = max(abs(float(a) - float(b)) for a, b in zip(numerical_temperature, reconstructed))
            analytic_errors[summary["id"]] = abs(linf - float(summary["terminal_field_linf_error_k"]))
    check(
        "independent_analytical_fields_reconstructed",
        max(value for value in analytic_differences.values() if value is not None) <= 2e-13
        and max(value for value in analytic_errors.values() if value is not None) <= 2e-13,
        {"field_values": analytic_differences, "reported_errors": analytic_errors},
    )
    check(
        "independent_analytical_means_reconstructed",
        max(mean_differences.values()) <= 2e-13,
        mean_differences,
    )

    summary_by_id = {item["summary"]["id"]: item["summary"] for item in cases_saved}
    uniform = summary_by_id["UNIFORM_ADIABATIC_CONTROL"]
    linear = next(item for item in cases_saved if item["summary"]["id"] == "LINEAR_DIRICHLET_STEADY_CONTROL")
    flux = summary_by_id["CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC"]
    linear_terminal = linear["history"][-1]
    check(
        "saved_uniform_and_linear_controls",
        abs(float(uniform["final_mean_temperature_c"]) - 60.0) <= 1e-12
        and uniform["enthalpy_change_j_m2"] == uniform["cumulative_inward_heat_j_m2"] == 0.0
        and abs(float(linear_terminal["net_inward_flux_w_m2"])) <= 1e-9
        and abs(float(linear_terminal["bottom_inward_flux_w_m2"]) + k * 100.0 / length) <= 1e-9
        and abs(float(linear_terminal["top_inward_flux_w_m2"]) - k * 100.0 / length) <= 1e-9,
        {
            "uniform_mean_c": uniform["final_mean_temperature_c"],
            "linear_bottom_w_m2": linear_terminal["bottom_inward_flux_w_m2"],
            "linear_top_w_m2": linear_terminal["top_inward_flux_w_m2"],
        },
    )
    flux_case = cases_by_id["CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC"]
    expected_flux_energy = float(flux_case["top_boundary"]["inward_flux_w_m2"]) * float(flux_case["duration_s"])
    expected_flux_mean = float(flux_case["initial"]["temperature_c"]) + expected_flux_energy / (rho * cp * length)
    check(
        "saved_constant_flux_reference",
        abs(float(flux["enthalpy_change_j_m2"]) - expected_flux_energy) <= 1e-5
        and abs(float(flux["cumulative_inward_heat_j_m2"]) - expected_flux_energy) <= 1e-5
        and abs(float(flux["final_mean_temperature_c"]) - expected_flux_mean) <= 1e-9,
        {
            "expected_energy_j_m2": expected_flux_energy,
            "saved_energy_j_m2": flux["enthalpy_change_j_m2"],
            "expected_mean_c": expected_flux_mean,
            "saved_mean_c": flux["final_mean_temperature_c"],
        },
    )

    energy_residuals = []
    saved_residual_differences = []
    exact_zero_mechanical = True
    exact_zero_global = True
    for item in cases_saved:
        exact_zero_mechanical &= item["summary"]["mechanical_energy_j_m2"] == 0.0
        exact_zero_global &= item["summary"]["global_energy_credit_j"] == 0.0
        for row in item["history"]:
            reconstructed = (
                float(row["enthalpy_change_j_m2"])
                - float(row["cumulative_inward_heat_j_m2"])
            )
            energy_residuals.append(abs(reconstructed))
            saved_residual_differences.append(abs(reconstructed - float(row["total_energy_residual_j_m2"])))
    check(
        "saved_flux_enthalpy_identity",
        max(energy_residuals) <= float(configuration["acceptance"]["total_energy_absolute_j_m2"])
        and max(saved_residual_differences) <= 1e-12,
        {
            "maximum_residual_j_m2": max(energy_residuals),
            "maximum_saved_difference_j_m2": max(saved_residual_differences),
        },
    )
    check(
        "mechanical_and_global_energy_exactly_zero",
        exact_zero_mechanical
        and exact_zero_global
        and ledger["mechanical_energy_j_m2"] == ledger["global_energy_credit_j"] == 0.0,
        {
            "summary_mechanical_zero": exact_zero_mechanical,
            "summary_global_zero": exact_zero_global,
            "ledger_mechanical": ledger["mechanical_energy_j_m2"],
            "ledger_global": ledger["global_energy_credit_j"],
        },
    )

    space = convergence["space"]
    reconstructed_space_orders = observed_orders(
        space["rows"], "terminal_field_linf_error_k", "cell_count"
    )
    time_order_differences = {}
    time_errors_monotonic = {}
    for case_id, data in convergence["time"].items():
        reconstructed = observed_orders(data["rows"], "terminal_field_linf_error_k", "step_count")
        time_order_differences[case_id] = max(abs(a - b) for a, b in zip(reconstructed, data["observed_orders"]))
        errors = [float(row["terminal_field_linf_error_k"]) for row in data["rows"]]
        time_errors_monotonic[case_id] = all(fine < coarse for coarse, fine in zip(errors, errors[1:]))
    check(
        "saved_convergence_orders_reconstructed",
        max(abs(a - b) for a, b in zip(reconstructed_space_orders, space["observed_orders"])) <= 1e-13
        and max(time_order_differences.values()) <= 1e-13,
        {"space": reconstructed_space_orders, "time_max_differences": time_order_differences},
    )
    check(
        "space_and_time_convergence_gates",
        all(
            float(configuration["acceptance"]["minimum_space_order"])
            <= float(value)
            <= float(configuration["acceptance"]["maximum_space_order"])
            for value in space["observed_orders"]
        )
        and all(time_errors_monotonic.values())
        and all(
            float(configuration["acceptance"]["minimum_time_order"])
            <= float(value)
            <= float(configuration["acceptance"]["maximum_time_order"])
            for data in convergence["time"].values()
            for value in data["observed_orders"]
        ),
        {
            "space_orders": space["observed_orders"],
            "time_orders": {key: value["observed_orders"] for key, value in convergence["time"].items()},
        },
    )

    conductivities = [float(row["conductivity_w_m_k"]) for row in sensitivity]
    means = [float(row["final_mean_temperature_c"]) for row in sensitivity]
    bottoms = [float(row["final_bottom_cell_temperature_c"]) for row in sensitivity]
    centroids = [float(row["thermal_centroid_depth_from_top_m"]) for row in sensitivity]
    check(
        "saved_conductivity_sensitivity_ordering",
        conductivities == sorted(conductivities)
        and all(b > a for a, b in zip(means, means[1:]))
        and all(b > a for a, b in zip(bottoms, bottoms[1:]))
        and all(b > a for a, b in zip(centroids, centroids[1:])),
        {"k": conductivities, "mean_c": means, "bottom_c": bottoms, "centroid_m": centroids},
    )
    check(
        "inherited_saved_controls_pass",
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
    check(
        "primary_source_scope_is_explicit",
        source["internet_source_used"]
        and source["primary_sources_only"]
        and not source["remote_sources_downloaded"]
        and len(source["primary_method_sources"]) == 3
        and all("nist" in entry["url"].lower() for entry in source["primary_method_sources"]),
        [entry["url"] for entry in source["primary_method_sources"]],
    )
    check(
        "thermal_only_scope_flags",
        result["one_dimensional_constant_property_conduction_qualified"]
        and result["boundary_conditions_are_synthetic"]
        and not result["temperature_history_coupled_to_panel"]
        and not result["fire_solved"]
        and not result["surface_convection_solved"]
        and not result["surface_radiation_solved"]
        and not result["moisture_or_phase_change_solved"]
        and not result["temperature_dependent_properties_solved"]
        and not result["thermal_strain_or_mechanics_solved"]
        and not result["heated_fracture_solved"]
        and not result["material_properties_degraded"]
        and not result["aircraft_impact_computed"]
        and not result["collapse_validated"]
        and not result["blender_changed"]
        and result["global_energy_credit_j"] == 0.0,
        {
            key: result[key]
            for key in (
                "one_dimensional_constant_property_conduction_qualified",
                "boundary_conditions_are_synthetic",
                "temperature_history_coupled_to_panel",
                "fire_solved", "surface_convection_solved", "surface_radiation_solved",
                "heated_fracture_solved", "collapse_validated", "blender_changed",
                "global_energy_credit_j",
            )
        },
    )
    report_text = (directory / "rapport_v11j_conduction_transitoire.md").read_text(encoding="utf-8")
    check(
        "report_preserves_required_interpretation_limits",
        all(
            phrase in report_text
            for phrase in (
                "pas un incendie WTC",
                "Aucune température V11J n'est appliquée au panneau V11I",
                "Aucune propriété mécanique ou endommagée n'est changée",
                "Blender reste une visualisation inchangée",
            )
        ),
        "four mandatory scope statements",
    )
    check(
        "runtime_and_randomness_declared",
        result["runtime"]["seconds"] > 0.0
        and result["runtime"]["seconds"] < float(configuration["expected_cpu_seconds_under"])
        and configuration["random_seed"] == 1101010
        and not configuration["random_draw_used"]
        and not configuration["gpu"]
        and not configuration["external_solver"]
        and not configuration["software_installation"],
        {
            "seconds": result["runtime"]["seconds"],
            "limit_seconds": configuration["expected_cpu_seconds_under"],
            "seed": configuration["random_seed"],
        },
    )

    script = Path(__file__).resolve()
    return {
        "iteration": "V11J",
        "status": "PASS" if all(item["pass"] for item in checks) else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "check_count": len(checks),
        "checks": checks,
        "output_hash_count": len(output_hashes),
        "input_hash_count": len(input_hashes),
        "audit_script": script.relative_to(ROOT).as_posix(),
        "audit_script_sha256": sha(script),
        "scope": "Independent hashes, analytical fields, flux-enthalpy arithmetic, convergence and scope flags; no import of the V11J conduction kernel or external validation.",
        "maximum_saved_flux_enthalpy_residual_j_m2": max(energy_residuals),
        "global_energy_credit_j": 0.0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    directory = (ROOT / args.directory).resolve()
    roots = [
        (ROOT / "tmp/v11j_transient_conduction").resolve(),
        (ROOT / "wtc1_simulation_v8/output/v11j_transient_conduction").resolve(),
    ]
    if not any(directory == root or root in directory.parents for root in roots):
        raise ValueError("Outside V11J output roots")
    result = audit(directory)
    if args.write:
        output = directory / "release_audit.json"
        if output.exists():
            raise FileExistsError("Existing release audit preserved")
        output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({key: value for key, value in result.items() if key != "checks"}, indent=2, ensure_ascii=False))
    if result["status"] != "PASS":
        print(json.dumps([item for item in result["checks"] if not item["pass"]], indent=2, ensure_ascii=False))
        raise SystemExit(1)
