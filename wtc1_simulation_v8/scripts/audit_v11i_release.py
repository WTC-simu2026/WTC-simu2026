"""Independent read-back audit for saved V11I artifacts.

This script deliberately does not import the V11I mechanics kernel.  It checks
hashes, saved arithmetic, controls, guards and row counts from serialized files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11i_thermoelastic_panel_predeclaration.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def relative(a, b, floor=1e-30):
    return abs(float(a) - float(b)) / max(float(floor), abs(float(a)), abs(float(b)))


def count_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def audit(directory):
    cfg = read(CONFIG)
    manifest = read(directory / "offline_manifest.json")
    result = read(directory / "results_v11i.json")
    numerical = read(directory / "numerical_audit.json")
    paths = read(directory / "panel_paths.json")
    half_step = read(directory / "half_step_paths.json")
    mesh_runs = read(directory / "mesh_runs.json")
    comparisons = read(directory / "discretization_comparison.json")
    controls = read(directory / "cold_and_thermoelastic_controls.json")
    material = read(directory / "material_and_scope_ledger.json")
    source = read(directory / "source_manifest.json")
    checks = []

    def check(name, condition, evidence):
        checks.append({"test": name, "pass": bool(condition), "evidence": evidence})

    output_hashes = {
        name: (directory / name).is_file() and sha(directory / name) == expected
        for name, expected in manifest["output_sha256"].items()
    }
    input_hashes = {
        name: (ROOT / name).is_file() and sha(ROOT / name) == expected
        for name, expected in manifest["input_sha256"].items()
    }
    check("saved_output_hashes", all(output_hashes.values()), {
        "count": len(output_hashes),
        "failed": [name for name, passed in output_hashes.items() if not passed],
    })
    check("frozen_input_and_protected_hashes", all(input_hashes.values()), {
        "count": len(input_hashes),
        "failed": [name for name, passed in input_hashes.items() if not passed],
    })
    check(
        "manifest_status_and_input_integrity",
        manifest["iteration"] == "V11I"
        and manifest["implementation_status"] == "PASS"
        and manifest["input_and_protected_unchanged"]
        and manifest["manifest_excludes_itself"],
        {
            "iteration": manifest["iteration"],
            "status": manifest["implementation_status"],
            "unchanged": manifest["input_and_protected_unchanged"],
        },
    )

    ids = [data["summary"]["id"] for data in paths]
    declared_ids = [case["id"] for case in cfg["thermal_cases"]]
    reference_state_count = sum(len(data["history"]) for data in paths)
    check(
        "saved_case_and_state_counts",
        ids == declared_ids
        and len(ids) == len(set(ids)) == result["case_count"] == 3
        and reference_state_count == result["reference_state_count"],
        {"ids": ids, "states": reference_state_count},
    )
    check(
        "saved_implementation_tests_pass",
        result["iteration"] == numerical["iteration"] == "V11I"
        and result["status"] == numerical["status"] == "PASS"
        and result["test_count"] == result["tests_passed"] == numerical["test_count"]
        and len(numerical["tests"]) == numerical["test_count"]
        and all(test["pass"] for test in numerical["tests"]),
        {
            "tests": result["test_count"],
            "passed": result["tests_passed"],
            "status": result["status"],
        },
    )

    reconstructed_digest = digest({
        "reference": paths,
        "half_step": half_step,
        "mesh_summaries": {
            key: [row["summary"] for row in values]
            for key, values in mesh_runs.items()
        },
        "comparisons": comparisons,
    })
    check(
        "saved_numerical_digest_reconstructed",
        reconstructed_digest == result["numerical_digest_sha256"],
        {"saved": result["numerical_digest_sha256"], "reconstructed": reconstructed_digest},
    )

    histories = [state for data in paths for state in data["history"]]
    all_histories = histories + [state for data in half_step for state in data["history"]]
    worst_energy = 0.0
    worst_saved_energy_difference = 0.0
    worst_equilibrium = 0.0
    worst_vertical = 0.0
    worst_horizontal = 0.0
    decomposition = 0.0
    exact_zero_support = True
    exact_zero_dissipation = True
    exact_zero_global = True
    all_finite = True
    for state in all_histories:
        reconstructed = abs(
            float(state["stored_J"])
            - float(state["mechanical_external_work_J"])
            - float(state["thermoelastic_work_J"])
        ) / max(
            1.0,
            abs(float(state["stored_J"])),
            abs(float(state["mechanical_external_work_J"])),
            abs(float(state["thermoelastic_work_J"])),
        )
        worst_energy = max(worst_energy, reconstructed)
        worst_saved_energy_difference = max(
            worst_saved_energy_difference,
            abs(reconstructed - float(state["total_mechanical_energy_residual_relative"])),
        )
        decomposition = max(
            decomposition,
            abs(float(state["stored_J"]) - float(state["spring_stored_J"]) - float(state["slab_stored_J"]))
            / max(1.0, abs(float(state["stored_J"]))),
        )
        worst_equilibrium = max(worst_equilibrium, float(state["equilibrium_residual"]))
        worst_vertical = max(worst_vertical, float(state["vertical_balance_relative"]))
        worst_horizontal = max(worst_horizontal, float(state["horizontal_balance_absolute_N"]))
        exact_zero_support &= state["support_work_J"] == 0.0
        exact_zero_dissipation &= state["dissipated_J"] == 0.0
        exact_zero_global &= state["global_energy_credit_J"] == 0.0
        all_finite &= all(
            math.isfinite(float(state[key]))
            for key in (
                "gravity_factor", "thermal_scale", "stored_J", "spring_stored_J",
                "slab_stored_J", "sensible_enthalpy_J", "max_DCR",
                "equilibrium_residual", "total_mechanical_energy_residual_relative",
            )
        )
    check("saved_states_are_finite", all_finite, len(all_histories))
    check(
        "saved_mechanical_energy_identity",
        worst_energy <= cfg["acceptance"]["relative_total_energy"]
        and worst_saved_energy_difference <= 1e-15,
        {"maximum_reconstructed": worst_energy, "maximum_saved_difference": worst_saved_energy_difference},
    )
    check("saved_stored_energy_decomposition", decomposition <= 1e-12, decomposition)
    check(
        "saved_equilibrium_and_support_reactions",
        worst_equilibrium <= cfg["acceptance"]["relative_equilibrium"]
        and worst_vertical < 1e-8
        and worst_horizontal < 1e-5,
        {
            "equilibrium_relative": worst_equilibrium,
            "vertical_relative": worst_vertical,
            "horizontal_absolute_N": worst_horizontal,
        },
    )
    check(
        "saved_support_work_dissipation_and_global_credit_zero",
        exact_zero_support and exact_zero_dissipation and exact_zero_global,
        {
            "support_work_exact_zero": exact_zero_support,
            "dissipation_exact_zero": exact_zero_dissipation,
            "global_credit_exact_zero": exact_zero_global,
        },
    )

    by_id = {data["summary"]["id"]: data for data in paths}
    cold = by_id["COLD_DELTA_T_ZERO"]
    cold_final = cold["summary"]["final"]
    cold_preload = cold["summary"]["preload"]
    exact_fields = (
        "stored_J", "spring_stored_J", "slab_stored_J", "max_slab_down_m",
        "max_slab_up_m", "max_truss_down_m", "max_opening_m", "max_overlap_m",
        "seat_vertical_reaction_N", "seat_horizontal_reaction_N", "gravity_load_N", "max_DCR",
    )
    exact_cold = {key: abs(float(cold_final[key]) - float(cold_preload[key])) for key in exact_fields}
    check(
        "saved_zero_temperature_exact_preload_replay",
        max(exact_cold.values()) == 0.0
        and cold_final["sensible_enthalpy_J"] == 0.0
        and cold_final["thermoelastic_work_J"] == 0.0,
        exact_cold,
    )

    cached = controls["cached_V11F_quarter_gravity_row"]
    mapping = {
        "stored_J": "stored_J",
        "spring_stored_J": "spring_stored_J",
        "slab_stored_J": "slab_stored_J",
        "max_slab_down_m": "max_slab_down_m",
        "max_truss_down_m": "max_truss_down_m",
        "max_opening_m": "max_opening_m",
        "max_overlap_m": "max_overlap_m",
        "seat_vertical_reaction_N": "seat_reaction_N",
        "gravity_load_N": "gravity_load_N",
        "component_max_DCR": "max_DCR",
    }
    floors = cfg["comparison_absolute_floors_si"]
    cold_errors = {}
    for actual, saved in mapping.items():
        if actual.startswith("max_") and actual.endswith("_m"):
            floor = floors["displacement_m"]
        elif "stored" in actual:
            floor = floors["energy_J"]
        elif actual.endswith("_N"):
            floor = floors["force_N"]
        else:
            floor = 1e-9
        cold_errors[actual] = relative(cold_preload[actual], float(cached[saved]), floor)
    cold_discrete = {
        "contact_count": cold_preload["contact_count"] == int(cached["contact_count"]),
        "vertical_tension_count": cold_preload["vertical_tension_count"] == int(cached["vertical_tension_count"]),
        "governing_id": cold_preload["governing_id"] == cached["governing_id"],
        "governing_kind": cold_preload["governing_kind"] == cached["governing_kind"],
    }
    check(
        "saved_v11f_quarter_gravity_regression",
        max(cold_errors.values()) <= cfg["acceptance"]["cold_v11f_cached_response_relative"]
        and all(cold_discrete.values()),
        {"maximum_relative": max(cold_errors.values()), "discrete": cold_discrete},
    )

    inventories = [data["inventory"] for data in paths]
    tangent_maximum = max(inv["cold_zero_tangent_relative_difference"] for inv in inventories)
    topology_ok = all(
        inv["subdivisions"] == cfg["discretization"]["reference_subdivisions_per_steel_panel"]
        and inv["steel_nodes"] == 33
        and inv["steel_members"] == 63
        and inv["slab_nodes"] == 65
        and inv["slab_elements"] == 64
        and inv["gauss_sections"] == 128
        and inv["contact_stations"] == 17
        for inv in inventories
    )
    check(
        "saved_cold_tangent_and_topology",
        tangent_maximum <= cfg["acceptance"]["cold_nodal_zero_temperature_exact_replay_relative"]
        and topology_ok,
        {"maximum_tangent_relative": tangent_maximum, "topology": inventories[0]},
    )

    guard = cfg["loading"]["accepted_DCR_guard"]
    guard_tol = cfg["acceptance"]["guard_DCR_absolute_tolerance"]
    max_accepted = max(float(state["max_DCR"]) for state in all_histories)
    guarded = [data for data in paths if data["summary"]["guard_bracket"] is not None]
    brackets = [data["summary"]["guard_bracket"] for data in guarded]
    bracket_ok = all(
        bracket["accepted_DCR"] <= guard
        and bracket["rejected_DCR"] >= guard
        and bracket["accepted_scale"] < bracket["rejected_scale"]
        and not bracket["rejected_state_committed"]
        for bracket in brackets
    )
    terminal_ok = all(
        data["summary"]["terminal"] == "SAFE_DCR_GUARD_REACHED_BEFORE_NOMINAL_LIMIT"
        for data in guarded
    )
    check(
        "saved_dcr_guard_and_uncommitted_brackets",
        max_accepted <= guard + guard_tol
        and len(guarded) >= 1
        and bracket_ok
        and terminal_ok
        and all(state["max_DCR"] < cfg["loading"]["nominal_material_or_component_limit_DCR"] for state in all_histories),
        {"maximum_accepted_DCR": max_accepted, "guarded_cases": len(guarded), "brackets": brackets},
    )

    thermal_response = {}
    for case_id in ("SLAB_UNIFORM_100K", "SLAB_GRADIENT_TOP_100K"):
        final = by_id[case_id]["summary"]["final"]
        thermal_response[case_id] = {
            "scale": final["thermal_scale"],
            "thermoelastic_work_J": final["thermoelastic_work_J"],
            "reaction_change_N": final["seat_vertical_reaction_N"] - cold_preload["seat_vertical_reaction_N"],
            "spring_energy_change_J": final["spring_stored_J"] - cold_preload["spring_stored_J"],
        }
    check(
        "saved_nonzero_uniform_and_gradient_response",
        all(
            values["scale"] > 0.0
            and abs(values["thermoelastic_work_J"]) > 1e-8
            and (abs(values["reaction_change_N"]) > 1e-5 or abs(values["spring_energy_change_J"]) > 1e-7)
            for values in thermal_response.values()
        ),
        thermal_response,
    )

    reference_temperature = cfg["loading"]["reference_temperature_c"]
    face_errors = {}
    sensible_errors = {}
    for data in paths:
        summary = data["summary"]
        final = summary["final"]
        scale = float(final["thermal_scale"])
        expected_bottom = reference_temperature + scale * float(summary["delta_t_bottom_c"])
        expected_top = reference_temperature + scale * float(summary["delta_t_top_c"])
        face_errors[summary["id"]] = max(
            abs(float(final["slab_bottom_temperature_c"]) - expected_bottom),
            abs(float(final["slab_top_temperature_c"]) - expected_top),
        )
        average_delta = 0.5 * (
            float(summary["delta_t_bottom_c"]) + float(summary["delta_t_top_c"])
        ) * scale
        expected_sensible = (
            float(data["inventory"]["section"]["heat_capacity_J_per_m_K"])
            * float(data["inventory"]["span_m"])
            * average_delta
        )
        sensible_errors[summary["id"]] = relative(final["sensible_enthalpy_J"], expected_sensible, 1.0)
    check("saved_temperature_faces", max(face_errors.values()) <= 1e-12, face_errors)
    check("saved_sensible_enthalpy_closed_form", max(sensible_errors.values()) <= 1e-12, sensible_errors)

    unilateral_ok = all(
        (term["force_N"] <= 1e-7 if term["kind"] == "contact" else
         term["force_N"] >= -1e-7 if term["kind"] == "vertical_tie" else True)
        for data in paths for term in data["terms"]
    )
    check("saved_unilateral_force_signs", unilateral_ok, "contact <= 0 N; vertical tie >= 0 N")

    half_rows = comparisons["half_step"]
    fine_rows = comparisons["mesh"]["8"]
    coarse_rows = comparisons["mesh"]["2"]
    half_limit = cfg["acceptance"]["half_step_common_response_relative"]
    half_ok = all(
        row["reference_terminal"] == row["other_terminal"]
        and row["terminal_scale_absolute_difference"] <= cfg["acceptance"]["half_step_terminal_scale_absolute"]
        and row["displacement_relative_difference"] <= half_limit
        and row["reaction_relative_difference"] <= half_limit
        and row["energy_relative_difference"] <= half_limit
        and row["pass"] and all(row["gates"].values())
        for row in half_rows
    )
    fine_ok = all(
        row["reference_terminal"] == row["other_terminal"]
        and row["terminal_scale_relative_difference"] <= cfg["acceptance"]["mesh_terminal_scale_relative"]
        and row["displacement_relative_difference"] <= cfg["acceptance"]["mesh_common_displacement_relative"]
        and row["reaction_relative_difference"] <= cfg["acceptance"]["mesh_common_reaction_relative"]
        and row["energy_relative_difference"] <= cfg["acceptance"]["mesh_common_energy_relative"]
        and row["pass"] and all(row["gates"].values())
        for row in fine_rows
    )
    check(
        "saved_half_step_and_fine_mesh_gates",
        len(half_rows) == len(fine_rows) == len(coarse_rows) == 3 and half_ok and fine_ok,
        {
            "half_passed": sum(row["pass"] for row in half_rows),
            "fine_passed": sum(row["pass"] for row in fine_rows),
            "coarse_diagnostic_passed": sum(row["pass"] for row in coarse_rows),
        },
    )
    check(
        "saved_declared_mesh_families",
        set(mesh_runs) == {"2", "8"}
        and all(len(values) == 3 for values in mesh_runs.values())
        and len(half_step) == 3,
        {"half": len(half_step), "meshes": {key: len(value) for key, value in mesh_runs.items()}},
    )

    csv_counts = {
        "path_history": count_csv(directory / "path_history.csv"),
        "panel_section_states": count_csv(directory / "panel_section_states.csv"),
        "critical_fiber_states": count_csv(directory / "critical_fiber_states.csv"),
        "connection_forces": count_csv(directory / "connection_forces.csv"),
        "slab_nodes": count_csv(directory / "slab_nodes.csv"),
        "energy_ledger": count_csv(directory / "energy_ledger.csv"),
        "discretization_comparison": count_csv(directory / "discretization_comparison.csv"),
    }
    expected_counts = {
        "path_history": reference_state_count,
        "panel_section_states": sum(len(data["sections"]) for data in paths),
        "critical_fiber_states": sum(len(data["critical_fibers"]) for data in paths),
        "connection_forces": sum(len(data["terms"]) for data in paths),
        "slab_nodes": sum(len(data["slab_nodes"]) for data in paths),
        "energy_ledger": reference_state_count,
        "discretization_comparison": len(half_rows) + len(fine_rows) + len(coarse_rows),
    }
    check("saved_csv_row_counts", csv_counts == expected_counts, {"actual": csv_counts, "expected": expected_counts})

    inherited = (controls["V11F"], controls["V11H"])
    inherited_ok = all(
        control["status"] == "PASS"
        and all(control["hash_checks"].values())
        and all(control["identity_checks"].values())
        for control in inherited
    )
    source_controls_ok = source["V11F_control"] == controls["V11F"] and source["V11H_control"] == controls["V11H"]
    check(
        "saved_v11f_and_v11h_controls",
        inherited_ok and source_controls_ok and controls["old_drivers_reexecuted"] is False,
        {
            "V11F": controls["V11F"]["status"],
            "V11H": controls["V11H"]["status"],
            "old_drivers_reexecuted": controls["old_drivers_reexecuted"],
        },
    )

    thermal_properties = material["thermal_properties"]
    scope_flags_ok = (
        result["bounded_elastic_panel_thermomechanical_coupling_validated"]
        and result["temperature_is_prescribed_not_calculated"]
        and result["accepted_heated_crack_state_count"] == 0
        and result["material_properties_degraded"] is False
        and result["heat_transfer_solved"] is False
        and result["fire_solved"] is False
        and result["geometric_nonlinearity_solved"] is False
        and result["aircraft_impact_computed"] is False
        and result["collapse_validated"] is False
        and result["blender_changed"] is False
        and result["global_energy_credit_J"] == 0.0
        and material["no_damage_history_or_property_updated"]
        and material["global_energy_credit_J"] == 0.0
        and source["new_archive_pdf_photo_or_video_analysis"] is False
        and source["internet_source_used"] is False
        and source["external_solver_or_multiagent_validation"] is False
    )
    check("saved_bounded_scope_flags", scope_flags_ok, "Prescribed-temperature reversible local panel only")
    check(
        "saved_unused_heat_transfer_fields_null",
        all(value is None for value in thermal_properties["unused_heat_transfer_fields"].values()),
        thermal_properties["unused_heat_transfer_fields"],
    )
    check(
        "report_and_figure_saved",
        (directory / "rapport_v11i_panneau_thermoelastique.md").is_file()
        and (directory / "synthese_v11i_panneau_thermoelastique.png").is_file(),
        {
            "report_bytes": (directory / "rapport_v11i_panneau_thermoelastique.md").stat().st_size,
            "figure_bytes": (directory / "synthese_v11i_panneau_thermoelastique.png").stat().st_size,
        },
    )

    script = Path(__file__).resolve()
    return {
        "iteration": "V11I",
        "status": "PASS" if all(item["pass"] for item in checks) else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "check_count": len(checks),
        "checks": checks,
        "output_hash_count": len(output_hashes),
        "input_hash_count": len(input_hashes),
        "audit_script": script.relative_to(ROOT).as_posix(),
        "audit_script_sha256": sha(script),
        "scope": "Independent saved-file hashes and arithmetic; no import of the mechanics kernel or external validation.",
        "maximum_reconstructed_total_energy_residual_relative": worst_energy,
        "maximum_saved_equilibrium_residual_relative": worst_equilibrium,
        "maximum_accepted_DCR": max_accepted,
        "global_energy_credit_J": 0.0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    directory = (ROOT / args.directory).resolve()
    roots = [
        (ROOT / "tmp/v11i_thermoelastic_panel").resolve(),
        (ROOT / "wtc1_simulation_v8/output/v11i_thermoelastic_panel").resolve(),
    ]
    if not any(directory == root or root in directory.parents for root in roots):
        raise ValueError("Outside V11I output roots")
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
