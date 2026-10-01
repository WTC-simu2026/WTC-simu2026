"""Independent read-back audit for serialized V11K artifacts.

The V11K physics module is deliberately not imported.  Hashes, surface laws,
steady references, energy arithmetic and convergence orders are reconstructed.
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
CONFIG = ROOT / "wtc1_simulation_v8/data/v11k_surface_exchange_predeclaration.json"


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


def environment_flux(
    surface_c: float,
    boundary: dict[str, Any],
    sigma: float,
) -> tuple[float, float, float]:
    convection = float(boundary["h_w_m2_k"]) * (float(boundary["gas_temperature_c"]) - surface_c)
    radiation = float(boundary["emissivity"]) * sigma * (
        (float(boundary["radiative_temperature_c"]) + 273.15) ** 4
        - (surface_c + 273.15) ** 4
    )
    return convection, radiation, convection + radiation


def inverse_environment_flux(
    boundary: dict[str, Any],
    target: float,
    sigma: float,
) -> float:
    low = -273.15 + 1e-7
    high = 3000.0

    def residual(value: float) -> float:
        return environment_flux(value, boundary, sigma)[2] - target

    if residual(low) < 0.0 or residual(high) > 0.0:
        raise ArithmeticError("Independent surface root not bracketed")
    for _ in range(180):
        middle = 0.5 * (low + high)
        if residual(middle) > 0.0:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def steady_reference(configuration: dict[str, Any], case: dict[str, Any]) -> dict[str, float]:
    length = float(configuration["geometry"]["thickness_m"])
    conductivity = float(configuration["constant_properties"]["conductivity_w_m_k"])
    sigma = float(configuration["surface_exchange"]["stefan_boltzmann_w_m2_k4"])

    def evaluate(rate: float) -> tuple[float, float, float]:
        bottom = inverse_environment_flux(case["bottom_boundary"], -rate, sigma)
        top = inverse_environment_flux(case["top_boundary"], rate, sigma)
        return conductivity * (top - bottom) / length - rate, bottom, top

    zero = evaluate(0.0)
    if abs(zero[0]) <= 1e-12:
        return {"rate": 0.0, "bottom": zero[1], "top": zero[2]}
    low, high = 0.0, 1000.0
    while evaluate(high)[0] > 0.0:
        high *= 2.0
    for _ in range(180):
        middle = 0.5 * (low + high)
        if evaluate(middle)[0] > 0.0:
            low = middle
        else:
            high = middle
    rate = 0.5 * (low + high)
    _, bottom, top = evaluate(rate)
    return {"rate": rate, "bottom": bottom, "top": top}


def orders(rows: list[dict[str, Any]]) -> list[float]:
    return [
        math.log(float(coarse["linf_error_k"]) / float(fine["linf_error_k"]))
        / math.log(float(fine["resolution"]) / float(coarse["resolution"]))
        for coarse, fine in zip(rows, rows[1:])
    ]


def audit(directory: Path) -> dict[str, Any]:
    configuration = read(CONFIG)
    manifest = read(directory / "offline_manifest.json")
    result = read(directory / "results_v11k.json")
    cases_saved = read(directory / "surface_exchange_cases.json")
    convergence = read(directory / "space_time_convergence.json")
    sensitivity = read(directory / "surface_exchange_sensitivity.json")
    controls = read(directory / "inherited_control.json")
    ledger = read(directory / "thermal_property_ledger.json")
    numerical = read(directory / "numerical_audit.json")
    source = read(directory / "source_manifest.json")
    profiles_csv = csv_rows(directory / "temperature_profiles.csv")
    history_csv = csv_rows(directory / "surface_exchange_history.csv")
    energy_csv = csv_rows(directory / "energy_ledger.csv")
    convergence_csv = csv_rows(directory / "space_time_convergence.csv")
    sensitivity_csv = csv_rows(directory / "surface_exchange_sensitivity.csv")
    report = (directory / "rapport_v11k_surface_exchange.md").read_text(encoding="utf-8-sig")
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
        manifest["iteration"] == "V11K"
        and manifest["implementation_status"] == "PASS"
        and manifest["input_and_protected_unchanged"]
        and manifest["manifest_excludes_itself"]
        and "offline_manifest.json" not in manifest["output_sha256"]
        and "release_audit.json" not in manifest["output_sha256"],
        {
            "iteration": manifest["iteration"],
            "status": manifest["implementation_status"],
            "unchanged": manifest["input_and_protected_unchanged"],
        },
    )
    check(
        "implementation_tests_saved_as_pass",
        result["iteration"] == numerical["iteration"] == "V11K"
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
        and len(case_ids) == len(set(case_ids)) == result["case_count"] == 6
        and state_count == result["reference_state_count"] == 246,
        {"ids": case_ids, "states": state_count},
    )
    expected_profile_rows = sum(
        len(item["profiles"]) * int(item["summary"]["cell_count"])
        for item in cases_saved
    )
    check(
        "saved_csv_row_counts",
        len(profiles_csv) == expected_profile_rows
        and len(history_csv) == len(energy_csv) == state_count
        and len(convergence_csv) == 8
        and len(sensitivity_csv) == len(sensitivity) == 6,
        {
            "profiles": len(profiles_csv),
            "history": len(history_csv),
            "energy": len(energy_csv),
            "convergence": len(convergence_csv),
            "sensitivity": len(sensitivity_csv),
        },
    )
    check(
        "v11j_saved_control_readback",
        controls["V11J"]["status"] == manifest["V11J_control_status"] == result["inherited_V11J_control_status"] == "PASS"
        and controls["old_driver_reexecuted"] is False
        and all(controls["V11J"]["hash_checks"].values())
        and all(controls["V11J"]["identity_checks"].values()),
        {"status": controls["V11J"]["status"], "old_driver_reexecuted": controls["old_driver_reexecuted"]},
    )

    summaries = {item["summary"]["id"]: item["summary"] for item in cases_saved}
    sigma = float(configuration["surface_exchange"]["stefan_boltzmann_w_m2_k4"])
    formula_errors = []
    balance_errors = []
    for saved_case, declared_case in zip(cases_saved, configuration["cases"]):
        terminal = saved_case["history"][-1]
        for side in ("bottom", "top"):
            surface_c = float(terminal[f"{side}_surface_temperature_c"])
            convection, radiation, total = environment_flux(surface_c, declared_case[f"{side}_boundary"], sigma)
            formula_errors.extend([
                abs(convection - float(terminal[f"{side}_convective_inward_flux_w_m2"])),
                abs(radiation - float(terminal[f"{side}_radiative_inward_flux_w_m2"])),
                abs(total - float(terminal[f"{side}_total_inward_flux_w_m2"])),
            ])
            balance_errors.append(abs(float(terminal[f"{side}_surface_balance_residual_w_m2"])))
    check(
        "independent_kelvin_surface_laws",
        max(formula_errors) <= configuration["acceptance"]["steady_flux_absolute_w_m2"],
        {"maximum_absolute_w_m2": max(formula_errors)},
    )
    check(
        "serialized_massless_surface_balances",
        max(balance_errors) <= configuration["acceptance"]["surface_balance_absolute_w_m2"],
        {"maximum_absolute_w_m2": max(balance_errors)},
    )

    equilibrium = summaries["COMBINED_EQUILIBRIUM_CONTROL"]
    check(
        "independent_equilibrium_control",
        max(
            abs(equilibrium["final_minimum_temperature_c"] - 60.0),
            abs(equilibrium["final_maximum_temperature_c"] - 60.0),
            abs(equilibrium["cumulative_total_inward_heat_j_m2"]),
        ) <= configuration["acceptance"]["total_energy_absolute_j_m2"],
        {
            "minimum_c": equilibrium["final_minimum_temperature_c"],
            "maximum_c": equilibrium["final_maximum_temperature_c"],
            "heat_j_m2": equilibrium["cumulative_total_inward_heat_j_m2"],
        },
    )
    steady_errors = {}
    for case in configuration["cases"]:
        if case["initial"]["kind"] != "steady_reference":
            continue
        independent = steady_reference(configuration, case)
        saved = summaries[case["id"]]
        steady_errors[case["id"]] = max(
            abs(independent["rate"] - saved["steady_reference"]["heat_rate_top_to_bottom_w_m2"]),
            abs(independent["bottom"] - saved["steady_reference"]["bottom_surface_temperature_c"]),
            abs(independent["top"] - saved["steady_reference"]["top_surface_temperature_c"]),
        )
    check(
        "independent_three_steady_references",
        max(steady_errors.values()) <= configuration["acceptance"]["steady_flux_absolute_w_m2"],
        steady_errors,
    )
    convection = summaries["CONVECTION_STEADY_TWO_SIDED"]
    closed_rate = 100.0 / (
        1.0 / 15.0
        + float(configuration["geometry"]["thickness_m"]) / float(configuration["constant_properties"]["conductivity_w_m_k"])
        + 1.0 / 25.0
    )
    check(
        "independent_closed_convection_resistance",
        abs(closed_rate - convection["steady_reference"]["heat_rate_top_to_bottom_w_m2"])
        <= configuration["acceptance"]["steady_flux_absolute_w_m2"],
        {"closed_w_m2": closed_rate, "saved_w_m2": convection["steady_reference"]["heat_rate_top_to_bottom_w_m2"]},
    )

    component_residuals = []
    enthalpy_residuals = []
    for row in energy_csv:
        components = sum(float(row[name]) for name in (
            "cumulative_bottom_convective_j_m2",
            "cumulative_bottom_radiative_j_m2",
            "cumulative_top_convective_j_m2",
            "cumulative_top_radiative_j_m2",
        ))
        cumulative = float(row["cumulative_total_inward_heat_j_m2"])
        component_residuals.append(abs(components - cumulative))
        enthalpy_residuals.append(abs(float(row["enthalpy_change_j_m2"]) - cumulative - float(row["total_energy_residual_j_m2"])))
    check(
        "independent_component_energy_ledger",
        max(component_residuals) <= configuration["acceptance"]["component_ledger_absolute_j_m2"]
        and max(enthalpy_residuals) <= configuration["acceptance"]["component_ledger_absolute_j_m2"],
        {"component_j_m2": max(component_residuals), "enthalpy_identity_j_m2": max(enthalpy_residuals)},
    )
    check(
        "saved_energy_and_newton_gates",
        result["maxima"]["energy_total_absolute_j_m2"] <= configuration["acceptance"]["total_energy_absolute_j_m2"]
        and result["maxima"]["energy_relative"] <= configuration["acceptance"]["total_energy_relative"]
        and result["maxima"]["nonlinear_residual_w_m2"] <= configuration["acceptance"]["nonlinear_residual_absolute_w_m2"]
        and result["maxima"]["newton_iterations"] <= configuration["acceptance"]["maximum_newton_iterations"],
        result["maxima"],
    )

    space_rows = convergence["space"]["rows"]
    time_rows = convergence["time"]["rows"]
    independent_space_orders = orders(space_rows)
    independent_time_orders = orders(time_rows)
    check(
        "independent_convergence_orders",
        max(abs(a - b) for a, b in zip(independent_space_orders, convergence["space"]["observed_orders"])) <= 1e-12
        and max(abs(a - b) for a, b in zip(independent_time_orders, convergence["time"]["observed_orders"])) <= 1e-12,
        {"space": independent_space_orders, "time": independent_time_orders},
    )
    check(
        "convergence_acceptance_readback",
        all(fine["linf_error_k"] < coarse["linf_error_k"] for coarse, fine in zip(space_rows, space_rows[1:]))
        and all(fine["linf_error_k"] < coarse["linf_error_k"] for coarse, fine in zip(time_rows, time_rows[1:]))
        and min(independent_space_orders) >= configuration["acceptance"]["minimum_space_order"]
        and max(independent_space_orders) <= configuration["acceptance"]["maximum_space_order"]
        and min(independent_time_orders) >= configuration["acceptance"]["minimum_time_order"]
        and max(independent_time_orders) <= configuration["acceptance"]["maximum_time_order"],
        {"space": independent_space_orders, "time": independent_time_orders},
    )

    h_rows = sorted((item for item in sensitivity if item["parameter"] == "top_h_w_m2_k"), key=lambda item: item["value"])
    epsilon_rows = sorted((item for item in sensitivity if item["parameter"] == "top_emissivity"), key=lambda item: item["value"])
    check(
        "independent_sensitivity_monotonicity",
        len(h_rows) == len(epsilon_rows) == 3
        and all(high["enthalpy_change_j_m2"] > low["enthalpy_change_j_m2"] for low, high in zip(h_rows, h_rows[1:]))
        and all(high["enthalpy_change_j_m2"] > low["enthalpy_change_j_m2"] for low, high in zip(epsilon_rows, epsilon_rows[1:]))
        and abs(epsilon_rows[0]["cumulative_top_radiative_j_m2"]) <= configuration["acceptance"]["total_energy_absolute_j_m2"],
        {
            "h_enthalpy_j_m2": [item["enthalpy_change_j_m2"] for item in h_rows],
            "epsilon_enthalpy_j_m2": [item["enthalpy_change_j_m2"] for item in epsilon_rows],
        },
    )

    numerical_payload = {
        "reference_summaries": result["case_summaries"],
        "space_refinement": convergence["space"],
        "time_refinement": convergence["time"],
        "surface_exchange_sensitivity": sensitivity,
    }
    check(
        "independent_numerical_digest",
        digest(numerical_payload) == result["numerical_digest_sha256"] == numerical["numerical_payload_digest_sha256"],
        {"recomputed": digest(numerical_payload), "saved": result["numerical_digest_sha256"]},
    )
    check(
        "source_scope_and_primary_status",
        source["primary_sources_only"]
        and source["internet_source_used"]
        and not source["remote_sources_downloaded"]
        and not source["new_archive_pdf_photo_or_video_analysis"]
        and len(source["primary_method_sources"]) == 3
        and all("nist" in item["url"].lower() for item in source["primary_method_sources"]),
        source["source_scope"],
    )
    check(
        "property_history_and_energy_boundary",
        ledger["surface_storage_j_m2"] == 0.0
        and ledger["mechanical_energy_j_m2"] == 0.0
        and ledger["global_energy_credit_j"] == 0.0
        and ledger["no_damage_history_or_property_updated"]
        and not ledger["temperature_history_coupled_to_panel"],
        {
            "surface_storage_j_m2": ledger["surface_storage_j_m2"],
            "global_energy_credit_j": ledger["global_energy_credit_j"],
        },
    )
    check(
        "result_scope_flags",
        result["surface_conditions_are_synthetic"]
        and not result["temperature_history_coupled_to_panel"]
        and not result["fire_solved"]
        and not result["temperature_dependent_properties_solved"]
        and not result["thermal_strain_or_mechanics_solved"]
        and not result["heated_fracture_solved"]
        and not result["material_properties_degraded"]
        and not result["collapse_validated"]
        and not result["blender_changed"]
        and result["global_energy_credit_j"] == 0.0,
        {key: result[key] for key in (
            "surface_conditions_are_synthetic", "fire_solved", "temperature_history_coupled_to_panel",
            "heated_fracture_solved", "collapse_validated", "blender_changed", "global_energy_credit_j",
        )},
    )
    report_lower = report.lower()
    required_phrases = [
        "n'est pas un incendie calculé",
        "kelvins absolus",
        "constantes v11j sont inchangées",
        "aucun champ v11k n'est appliqué",
        "blender reste inchangé",
        "localisation après fracture",
        "tests numériques réussis",
    ]
    missing_phrases = [phrase for phrase in required_phrases if phrase not in report_lower]
    check(
        "report_scope_language",
        not missing_phrases and "## 1." in report and "## 6." in report,
        {"missing": missing_phrases},
    )
    check(
        "next_iteration_is_bounded_v11l",
        result["next_iteration"] == "V11L"
        and "unidirectionnel" in result["next_objective"].lower()
        and "non endommagé" in result["next_objective"].lower()
        and "non-wtc" in result["next_objective"].lower(),
        result["next_objective"],
    )
    check(
        "visual_and_report_artifacts_present",
        (directory / "synthese_v11k_surface_exchange.png").stat().st_size > 10_000
        and (directory / "rapport_v11k_surface_exchange.md").stat().st_size > 5_000,
        {
            "png_bytes": (directory / "synthese_v11k_surface_exchange.png").stat().st_size,
            "report_bytes": (directory / "rapport_v11k_surface_exchange.md").stat().st_size,
        },
    )
    status = "PASS" if all(item["pass"] for item in checks) else "FAIL"
    return {
        "iteration": "V11K",
        "status": status,
        "audit_scope": "Independent serialized-artifact read-back; V11K kernel not imported",
        "audit_count": len(checks),
        "audits_passed": sum(item["pass"] for item in checks),
        "checks": checks,
        "audited_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    configuration = read(CONFIG)
    directory = (ROOT / args.output).resolve()
    allowed_roots = [(ROOT / configuration[key]).resolve() for key in ("output_directory", "scratch_directory")]
    if not any(directory == root or root in directory.parents for root in allowed_roots):
        raise ValueError("Outside V11K output roots")
    release_path = directory / "release_audit.json"
    if release_path.exists():
        raise FileExistsError("Preserve prior audit; choose an unaudited output directory")
    result = audit(directory)
    release_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "audits": result["audit_count"],
        "passed": result["audits_passed"],
        "failed": [item for item in result["checks"] if not item["pass"]],
    }, ensure_ascii=False), flush=True)
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
