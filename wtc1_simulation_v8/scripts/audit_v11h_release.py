"""Read-back audit for saved V11H files; does not import the mechanics kernel."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative(a, b, floor=1e-30):
    return abs(float(a) - float(b)) / max(floor, abs(float(a)), abs(float(b)))


def count_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def audit(directory):
    checks = []

    def check(name, condition, evidence):
        checks.append({"test": name, "pass": bool(condition), "evidence": evidence})

    manifest = read(directory / "offline_manifest.json")
    result = read(directory / "results_v11h.json")
    numerical = read(directory / "numerical_audit.json")
    paths = read(directory / "section_paths.json")
    mesh = read(directory / "mesh_convergence.json")
    material = read(directory / "thermal_material_ledger.json")
    cold = read(directory / "cold_v11f_control.json")
    bar = read(directory / "v10w_bar_replay.json")
    source = read(directory / "source_manifest.json")

    outputs = {name: sha(directory / name) == expected for name, expected in manifest["output_sha256"].items()}
    inputs = {name: sha(ROOT / name) == expected for name, expected in manifest["input_sha256"].items()}
    check("saved_output_hashes", all(outputs.values()), outputs)
    check("frozen_input_and_protected_hashes", all(inputs.values()), inputs)
    check("manifest_status_and_input_integrity", manifest["implementation_status"] == "PASS" and manifest["input_and_protected_unchanged"], {
        "status": manifest["implementation_status"], "unchanged": manifest["input_and_protected_unchanged"]
    })

    ids = [run["summary"]["id"] for run in paths]
    check("saved_case_and_state_counts", len(paths) == len(set(ids)) == result["case_count"] == 11 and
          sum(len(run["history"]) for run in paths) == result["state_count"], {
              "cases": len(paths), "unique": len(set(ids)), "states": sum(len(run["history"]) for run in paths)
          })
    check("saved_implementation_tests_pass", numerical["status"] == result["status"] == "PASS" and
          numerical["test_count"] == result["test_count"] == result["tests_passed"] and
          all(test["pass"] for test in numerical["tests"]), result["test_count"])

    worst_energy = 0.0
    worst_free = 0.0
    worst_support_work = 0.0
    exact_zero_dissipation = True
    exact_zero_global = True
    for run in paths:
        mode = run["summary"]["mode"]
        for state in run["history"]:
            u = state["stored_mechanical_J_per_m"]
            wt = state["cumulative_thermoelastic_work_J_per_m"]
            wm = state["cumulative_external_mechanical_work_J_per_m"]
            worst_energy = max(worst_energy, abs(u - wt - wm) / max(1.0, abs(u), abs(wt), abs(wm)))
            worst_support_work = max(worst_support_work, abs(wm))
            if mode in ("FREE", "CURVATURE_RESTRAINED_AXIAL_FREE"):
                worst_free = max(worst_free, state["free_axial_residual_relative"])
            if mode in ("FREE", "AXIAL_RESTRAINED_ROTATION_FREE"):
                worst_free = max(worst_free, state["free_moment_residual_relative"])
            exact_zero_dissipation &= state["dissipated_J_per_m"] == 0.0
            exact_zero_global &= state["global_energy_credit_J"] == 0.0
    check("saved_mechanical_energy_identity", worst_energy <= 1e-10, worst_energy)
    check("saved_free_resultants", worst_free <= 1e-10, worst_free)
    check("saved_support_mechanical_work_zero", worst_support_work < 1e-7, worst_support_work)
    check("saved_no_dissipation_or_global_energy_credit", exact_zero_dissipation and exact_zero_global, {
        "dissipation_exact_zero": exact_zero_dissipation, "global_exact_zero": exact_zero_global
    })

    by_id = {run["summary"]["id"]: run for run in paths}
    alpha = material["thermal_properties"]["concrete"]["thermal_expansion_per_k"]
    length = by_id["PLAIN_UNIFORM_FREE"]["inventory"]["span_m"]
    h = by_id["PLAIN_GRADIENT_FREE"]["inventory"]["equivalent_thickness_m"]
    uniform_free = by_id["PLAIN_UNIFORM_FREE"]["summary"]["peak"]
    expected_eps = alpha * 100.0
    free_errors = {
        "eps0": relative(uniform_free["eps0"], expected_eps, 1e-15),
        "extension": relative(uniform_free["centroid_extension_m"], expected_eps * length, 1e-15),
        "kappa": abs(uniform_free["kappa_per_m"]),
        "stress_scaled": uniform_free["maximum_absolute_stress_Pa"] / max(1.0, by_id["PLAIN_UNIFORM_FREE"]["inventory"]["E_concrete_Pa"] * expected_eps),
    }
    check("saved_uniform_free_closed_form", max(free_errors.values()) <= 1e-10, free_errors)

    restrained = by_id["PLAIN_UNIFORM_FULLY_RESTRAINED"]
    restrained_peak = restrained["summary"]["peak"]
    ea = restrained["inventory"]["section_stiffness"]["K_N"]
    expected_n = -ea * expected_eps
    expected_u = 0.5 * ea * expected_eps**2
    restraint_errors = {
        "force": relative(restrained_peak["N_N"], expected_n, 1e-12),
        "reaction": relative(restrained_peak["support_reaction_N"], -expected_n, 1e-12),
        "energy": relative(restrained_peak["stored_mechanical_J_per_m"], expected_u, 1e-12),
        "thermal_work": relative(restrained_peak["cumulative_thermoelastic_work_J_per_m"], expected_u, 1e-12),
    }
    check("saved_uniform_restrained_closed_form", max(restraint_errors.values()) <= 1e-10, restraint_errors)

    gradient = by_id["PLAIN_GRADIENT_FREE"]["summary"]["peak"]
    expected_kappa = -alpha * 100.0 / h
    gradient_errors = {
        "eps0": relative(gradient["eps0"], alpha * 50.0, 1e-15),
        "kappa": relative(gradient["kappa_per_m"], expected_kappa, 1e-15),
        "bow": relative(gradient["simply_supported_free_bow_midspan_m"], abs(expected_kappa) * length**2 / 8, 1e-15),
    }
    check("saved_through_depth_gradient_closed_form", max(gradient_errors.values()) <= 1e-10, gradient_errors)

    common = by_id["R02_COMMON_ALPHA_GRADIENT_FREE"]["summary"]["peak"]
    differential = by_id["R02_GRADIENT_FREE"]["summary"]["peak"]
    check("saved_common_and_differential_alpha_controls", common["maximum_absolute_stress_Pa"] < 1e-4 and
          differential["maximum_absolute_stress_Pa"] > 1.0, {
              "common_stress_Pa": common["maximum_absolute_stress_Pa"],
              "differential_stress_Pa": differential["maximum_absolute_stress_Pa"],
          })

    cycle_ids = ("R02_UNIFORM_RESTRAINED_CYCLE", "R02_GRADIENT_FREE_CYCLE")
    cycle_values = {}
    cycle_ok = True
    for case_id in cycle_ids:
        final = by_id[case_id]["summary"]["final"]
        values = {key: abs(final[key]) for key in (
            "eps0", "kappa_per_m", "maximum_absolute_stress_Pa", "stored_mechanical_J_per_m",
            "cumulative_thermoelastic_work_J_per_m", "sensible_enthalpy_change_J_per_m"
        )}
        cycle_values[case_id] = values
        cycle_ok &= values["eps0"] <= 1e-12 and values["kappa_per_m"] <= 1e-12
        cycle_ok &= values["maximum_absolute_stress_Pa"] < 1e-4
        cycle_ok &= max(values["stored_mechanical_J_per_m"], values["cumulative_thermoelastic_work_J_per_m"],
                        values["sensible_enthalpy_change_J_per_m"]) <= 1e-8
    check("saved_cycles_return_to_reference", cycle_ok, cycle_values)

    cached = read(ROOT / "wtc1_simulation_v8/output/v10w_analytical_reference.json")
    declared = cached["declared_inputs"]
    dt = declared["temperature"]["maximum_temperature_change_c"]
    length_mm = declared["geometry"]["length_mm"]
    area_mm2 = declared["geometry"]["area_mm2"]
    modulus = declared["material"]["young_modulus_mpa"]
    alpha_bar = declared["material"]["thermal_expansion_per_c"]
    expected_bar = {
        "uniform_free_tip_displacement_mm": alpha_bar * dt * length_mm,
        "uniform_restrained_force_magnitude_N": modulus * area_mm2 * alpha_bar * dt,
        "uniform_restrained_stress_MPa": modulus * alpha_bar * dt,
        "axial_linear_gradient_free_tip_displacement_mm": 0.5 * alpha_bar * dt * length_mm,
    }
    bar_errors = {key: relative(bar[key], value, 1e-30) for key, value in expected_bar.items()}
    check("saved_v10w_bar_replay", max(bar_errors.values()) <= 1e-10, bar_errors)

    mesh_counts = {key: len(value) for key, value in mesh.items()}
    check("saved_three_mesh_families", set(mesh) == {"40", "80", "320"} and all(count == 11 for count in mesh_counts.values()), mesh_counts)
    csv_counts = {
        "section_paths": count_csv(directory / "section_paths.csv"),
        "fiber_states": count_csv(directory / "section_fiber_states.csv"),
        "energy_ledger": count_csv(directory / "energy_ledger.csv"),
        "mesh_comparison": count_csv(directory / "section_mesh_comparison.csv"),
    }
    expected_fibers = sum(len(run["peak_fibers"]) for run in paths)
    check("saved_csv_row_counts", csv_counts == {
        "section_paths": result["state_count"], "fiber_states": expected_fibers,
        "energy_ledger": 2 * result["case_count"], "mesh_comparison": 3 * result["case_count"],
    }, csv_counts)

    checks_from_source = source["inherited_manifest_checks"]
    check("saved_inherited_v11f_v11g_hash_checks", all(checks_from_source.values()), {
        "count": len(checks_from_source), "failed": [key for key, value in checks_from_source.items() if not value]
    })
    check("saved_v11f_cold_control", cold["status"] == result["cold_v11f_control_status"] == "PASS" and
          all(cold["hash_checks"].values()) and all(cold["identity_checks"].values()), {
              "status": cold["status"], "tests": cold["test_count"], "cases": cold["case_count"]
          })
    check("bounded_scope_flags", result["prescribed_temperature_only"] and result["global_energy_credit_J"] == 0.0 and
          not any(result[key] for key in (
              "cold_panel_mechanics_changed", "heated_fracture_solved", "full_panel_thermomechanical_coupling_solved",
              "heat_transfer_solved", "fire_solved", "aircraft_impact_computed", "collapse_validated", "blender_changed"
          )) and material["temperature_field_is_fire_calculation"] is False, "Elastic prescribed-temperature section only")
    check("no_undeclared_heat_transfer_properties", all(value is None for value in
          material["thermal_properties"]["unused_heat_transfer_fields"].values()),
          material["thermal_properties"]["unused_heat_transfer_fields"])
    check("report_and_figure_saved", (directory / "rapport_v11h_thermomecanique.md").is_file() and
          (directory / "synthese_v11h_thermomecanique.png").is_file(), {
              "report_bytes": (directory / "rapport_v11h_thermomecanique.md").stat().st_size,
              "figure_bytes": (directory / "synthese_v11h_thermomecanique.png").stat().st_size,
          })

    script = Path(__file__).resolve()
    return {
        "iteration": "V11H", "status": "PASS" if all(item["pass"] for item in checks) else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "check_count": len(checks), "checks": checks,
        "output_hash_count": len(outputs), "input_hash_count": len(inputs),
        "audit_script": script.relative_to(ROOT).as_posix(), "audit_script_sha256": sha(script),
        "scope": "Independent saved-file arithmetic and hash checks; no mechanics-kernel import or external validation.",
        "maximum_reconstructed_energy_residual_relative": worst_energy,
        "maximum_reconstructed_free_resultant_residual_relative": worst_free,
        "global_energy_credit_J": 0.0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    directory = (ROOT / args.directory).resolve()
    roots = [
        (ROOT / "tmp/v11h_thermomechanical").resolve(),
        (ROOT / "wtc1_simulation_v8/output/v11h_thermomechanical").resolve(),
    ]
    if not any(directory == root or root in directory.parents for root in roots):
        raise ValueError("Outside V11H output roots")
    result = audit(directory)
    if args.write:
        output = directory / "release_audit.json"
        if output.exists():
            raise FileExistsError("Existing release audit preserved")
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "checks"}, indent=2, ensure_ascii=False))
    if result["status"] != "PASS":
        print(json.dumps([item for item in result["checks"] if not item["pass"]], indent=2, ensure_ascii=False))
        raise SystemExit(1)
