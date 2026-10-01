"""Aggregate accepted IMPACT-I02E-R9 results under the R10 audit policy."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

from audit_impact_i02e import load_config
from run_impact_i02c import ROOT, dump, sha


DEFAULT_CFG = ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r10.json"


def relative(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1.0e-30)


def first_contact_ms(history: dict) -> float | None:
    impulse = np.abs(np.asarray(history["contact_impulse_Ns"]))
    hits = np.flatnonzero(impulse > 1.0e-6)
    return float(history["time_ms"][hits[0]]) if len(hits) else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CFG)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    cfg = load_config(config_path)
    output = ROOT / cfg["output_root"]
    cases = {case["id"]: case for case in cfg["cases"]}
    results = {case_id: json.loads((output / case_id / "results.json").read_text(encoding="utf-8")) for case_id in cases}
    histories = {case_id: json.loads((output / case_id / "history.json").read_text(encoding="utf-8")) for case_id in cases}

    merged = results["CONTACT_MERGED_H127_R9"]
    unbreakable = results["CONTACT_UNBREAKABLE_H127_R9"]
    rupturable = results["CONTACT_RUPTURABLE_H127_R9"]
    half_dt = results["CONTACT_RUPTURABLE_HALFDT_H127_R9"]
    low_mass = results["CONTACT_RUPTURABLE_LOWMASS_H127_R9"]
    refined = results["CONTACT_RUPTURABLE_H0635_R9"]
    gate = cfg["gates"]

    comparisons = {
        "configured_geometric_first_contact_ms": cfg["wing_bay"]["front_z_mm"] / cfg["speed"]["m_per_s"],
        "sampled_first_contact_ms_by_case": {
            case_id: first_contact_ms(histories[case_id])
            for case_id, case in cases.items()
            if case["contact"]
        },
        "h127_variant_comparison": {
            "merged": {
                "impulse_Ns": merged["final_contact_impulse_abs_Ns"],
                "max_global_nodal_relative_displacement_mm": merged["max_pair_relative_displacement_mm"],
                "joint_work_J": merged["max_joint_work_J"],
            },
            "unbreakable": {
                "impulse_Ns": unbreakable["final_contact_impulse_abs_Ns"],
                "max_global_nodal_relative_displacement_mm": unbreakable["max_pair_relative_displacement_mm"],
                "joint_work_J": unbreakable["max_joint_work_J"],
                "minimum_active_area_fraction": unbreakable["minimum_active_area_fraction"],
            },
            "rupturable": {
                "impulse_Ns": rupturable["final_contact_impulse_abs_Ns"],
                "max_global_nodal_relative_displacement_mm": rupturable["max_pair_relative_displacement_mm"],
                "joint_work_J": rupturable["max_joint_work_J"],
                "minimum_active_area_fraction": rupturable["minimum_active_area_fraction"],
            },
            "merged_unbreakable_impulse_ratio": merged["final_contact_impulse_abs_Ns"] / unbreakable["final_contact_impulse_abs_Ns"],
            "rupturable_relative_to_merged_impulse_change": (rupturable["final_contact_impulse_abs_Ns"] - merged["final_contact_impulse_abs_Ns"]) / merged["final_contact_impulse_abs_Ns"],
            "rupturable_relative_to_unbreakable_impulse_change": (rupturable["final_contact_impulse_abs_Ns"] - unbreakable["final_contact_impulse_abs_Ns"]) / unbreakable["final_contact_impulse_abs_Ns"],
        },
        "time_step_sensitivity": {
            "impulse_difference_fraction": relative(rupturable["final_contact_impulse_abs_Ns"], half_dt["final_contact_impulse_abs_Ns"]),
            "joint_work_difference_fraction": relative(rupturable["max_joint_work_J"], half_dt["max_joint_work_J"]),
            "maximum_relative_displacement_difference_fraction": relative(rupturable["max_pair_relative_displacement_mm"], half_dt["max_pair_relative_displacement_mm"]),
        },
        "numerical_mass_sensitivity": {
            "baseline_areal_mass_g_per_mm2": 0.0001,
            "lower_areal_mass_g_per_mm2": 0.00001,
            "baseline_declared_mass_g": rupturable["declared_numerical_connection_mass_g"],
            "lower_declared_mass_g": low_mass["declared_numerical_connection_mass_g"],
            "impulse_difference_fraction": relative(rupturable["final_contact_impulse_abs_Ns"], low_mass["final_contact_impulse_abs_Ns"]),
            "joint_work_difference_fraction": relative(rupturable["max_joint_work_J"], low_mass["max_joint_work_J"]),
            "maximum_relative_displacement_difference_fraction": relative(rupturable["max_pair_relative_displacement_mm"], low_mass["max_pair_relative_displacement_mm"]),
        },
        "spatial_refinement": {
            "h127_impulse_Ns": rupturable["final_contact_impulse_abs_Ns"],
            "h0635_impulse_Ns": refined["final_contact_impulse_abs_Ns"],
            "impulse_difference_fraction": relative(rupturable["final_contact_impulse_abs_Ns"], refined["final_contact_impulse_abs_Ns"]),
            "h127_joint_work_J": rupturable["max_joint_work_J"],
            "h0635_joint_work_J": refined["max_joint_work_J"],
            "joint_work_difference_fraction": relative(rupturable["max_joint_work_J"], refined["max_joint_work_J"]),
            "maximum_relative_displacement_difference_fraction": relative(rupturable["max_pair_relative_displacement_mm"], refined["max_pair_relative_displacement_mm"]),
            "qualification": "One additional refinement passes the declared differences but does not establish asymptotic convergence.",
        },
        "outcome_within_0_35_ms": {
            "rupturable_any_deleted_h127": rupturable["any_cohesive_deletion"],
            "rupturable_any_deleted_h0635": refined["any_cohesive_deletion"],
            "rupturable_minimum_active_area_fraction_h127": rupturable["minimum_active_area_fraction"],
            "rupturable_minimum_active_area_fraction_h0635": refined["minimum_active_area_fraction"],
            "interpretation": "No cohesive cell deletion is sampled in the bounded window. This does not mean an aircraft wing remains intact; shell metal failure is disabled and later contact is not computed.",
        },
    }
    dump(output / "comparisons_r10.json", comparisons)

    high_mass_cases = [result for case_id, result in results.items() if "LOWMASS" not in case_id]
    shell_masses = [result["expected_wing_shell_mass_g"] for result in high_mass_cases]
    checks = {
        "all_case_audits": all(result["status"] == "PASS" for result in results.values()),
        "all_free_controls_zero_internal_energy": all(
            result["max_free_flight_internal_energy_over_initial_ke"] == 0
            for result in results.values()
            if not result["contact"]
        ),
        "shell_mass_identical_between_variants": relative(min(shell_masses), max(shell_masses)) <= gate["max_shell_mass_difference_between_variants_fraction"],
        "merged_unbreakable_impulse_ratio": gate["minimum_merged_to_unbreakable_impulse_ratio"] <= comparisons["h127_variant_comparison"]["merged_unbreakable_impulse_ratio"] <= gate["maximum_merged_to_unbreakable_impulse_ratio"],
        "unbreakable_zone_remains_active": unbreakable["minimum_active_area_fraction"] >= gate["minimum_unbreakable_active_area_fraction"],
        "half_dt_impulse": comparisons["time_step_sensitivity"]["impulse_difference_fraction"] <= gate["max_half_dt_contact_impulse_difference_fraction"],
        "half_dt_joint_work": comparisons["time_step_sensitivity"]["joint_work_difference_fraction"] <= gate["max_half_dt_joint_work_difference_fraction"],
        "numerical_mass_impulse": comparisons["numerical_mass_sensitivity"]["impulse_difference_fraction"] <= gate["max_numerical_mass_sensitivity_contact_impulse_difference_fraction"],
        "numerical_mass_joint_work": comparisons["numerical_mass_sensitivity"]["joint_work_difference_fraction"] <= gate["max_numerical_mass_sensitivity_joint_work_difference_fraction"],
        "h127_h0635_impulse": comparisons["spatial_refinement"]["impulse_difference_fraction"] <= gate["max_h127_h0635_contact_impulse_difference_fraction"],
        "h127_h0635_joint_work": comparisons["spatial_refinement"]["joint_work_difference_fraction"] <= gate["max_h127_h0635_joint_work_difference_fraction"],
        "no_shell_erosion": all(result["max_wing_eroded_shells"] == 0 for result in results.values()),
        "cohesive_history_irreversible": all(result["cohesive_no_healing"] for result in results.values()),
    }
    execution_seconds = {
        case_id: result["execution_seconds"]
        for case_id, result in results.items()
    }
    preflights = {
        "FREE_RUPTURABLE_H127_R0": "Interrupted full-story zero-height preflight; no causal attribution.",
        "FREE_RUPTURABLE_H127_R1": "Interrupted full-story finite-height preflight; full-story model was too costly.",
        "FREE_RUPTURABLE_H254_R2": "Interrupted before cycle-output diagnosis.",
        "FREE_RUPTURABLE_SHORT_H254_R3": "Interrupted one-step diagnosis.",
        "FREE_RUPTURABLE_ZERO_SPEED_H254_R4": "Zero speed did not remove the tiny time step.",
        "FREE_RUPTURABLE_PRINT_H254_R5": "Measured constant 3.3674e-9 ms step from the former numerical connection mass.",
        "FREE_RUPTURABLE_H254_R6": "Rejected: part 8 absent from initial velocity, creating pre-contact joint vibration.",
        "FREE_MERGED_H254_R7": "Rejected with R7 topology: an intermediate connection row was absent from skin shells.",
        "FREE_RUPTURABLE_H254_R7": "Rejected with R7 topology despite a clean rigid translation.",
        "CONTACT_RUPTURABLE_H254_R8": "Normal termination but failed the 5 percent energy gate at 25.4 mm.",
        "CONTACT_RUPTURABLE_HALFDT_H254_R8": "Confirmed the coarse energy loss was not time-step driven.",
        "CONTACT_RUPTURABLE_H127_R8": "Passed and justified the R9 12.7 mm baseline; superseded for final provenance.",
    }
    campaign = {
        "id": cfg["id"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": {key: bool(value) for key, value in checks.items()},
        "case_check_count": sum(len(result["checks"]) for result in results.values()),
        "accepted_cases": list(results),
        "case_results": results,
        "comparisons": comparisons,
        "accepted_execution_seconds": execution_seconds,
        "accepted_execution_seconds_total": sum(execution_seconds.values()),
        "retained_preflights": preflights,
        "python": sys.version,
        "platform": platform.platform(),
        "physical_aircraft_impact_qualified": False,
        "metal_tearing_qualified": False,
        "full_facade_qualified": False,
        "later_time_behavior_qualified": False,
        "asymptotic_mesh_convergence_qualified": False,
        "qualification": "Bounded local first-contact comparison of one idealized skin-stringer zone. It cannot decide whether real Boeing wings should break or whether the observed WTC1 penetration is physically reproduced.",
        "source_hashes": {
            "config_r10": sha(config_path),
            "summarizer": sha(Path(__file__)),
            "auditor": sha(ROOT / "wtc1_simulation_v8/scripts/audit_impact_i02e.py"),
            "generator_current": sha(ROOT / "wtc1_simulation_v8/scripts/run_impact_i02e.py"),
        },
    }
    dump(output / "campaign_audit_r10.json", campaign)
    print(
        json.dumps(
            {
                "status": campaign["status"],
                "cases": len(results),
                "case_checks": campaign["case_check_count"],
                "campaign_checks": len(checks),
                "seconds": campaign["accepted_execution_seconds_total"],
                "comparisons": comparisons,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    sys.exit(0 if campaign["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
