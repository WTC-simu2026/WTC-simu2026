"""Audit saved IMPACT-I02F R3 crack-band coupons without rerunning them."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json"
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_new(path: Path, value: object) -> None:
    if path.exists():
        raise RuntimeError("Existing audit preserved: " + str(path))
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1.0e-30)


def one_column(headers: list[str], title: str, variable: str) -> int:
    matches = [index for index, header in enumerate(headers) if title in header and re.search(r"\b" + variable + r"\b", header)]
    if len(matches) != 1:
        raise RuntimeError(f"Ambiguous history column {title}/{variable}: {matches}")
    return matches[0]


def audit_case(cfg: dict, configured_case: dict) -> dict:
    case_id = configured_case["id"].replace("_R0", "_R3")
    directory = OUT / case_id
    meta = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
    csv_path = directory / f"{meta['name']}T01.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        headers = next(csv.reader(stream))
    values = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    if values.ndim == 1:
        values = values[None, :]
    if values.shape[1] != len(headers):
        raise RuntimeError("History header/data mismatch for " + case_id)
    time_ms = values[:, 0]
    band_ie = values[:, one_column(headers, "PRESCRIBED_LOCALIZATION_BAND", "IE")] * 0.001
    band_mass = values[:, one_column(headers, "PRESCRIBED_LOCALIZATION_BAND", "MASS")]
    band_eroded = values[:, one_column(headers, "PRESCRIBED_LOCALIZATION_BAND", "ERODED")]
    boundary_columns = [index for index, header in enumerate(headers) if "BOUNDARY_X_HISTORY" in header]
    node_count = len(meta["left_nodes"]) + len(meta["right_nodes"])
    if len(boundary_columns) != 3 * node_count:
        raise RuntimeError("Unexpected boundary history layout for " + case_id)
    left_count = len(meta["left_nodes"])
    left_reaction_impulse_columns = boundary_columns[2 : 3 * left_count : 3]
    right_displacement_columns = boundary_columns[3 * left_count :: 3]
    support_impulse_N_ms = -np.sum(values[:, left_reaction_impulse_columns], axis=1)
    reaction_force_N = np.gradient(support_impulse_N_ms, time_ms)
    right_displacement_mm = np.mean(values[:, right_displacement_columns], axis=1)
    plastic_work_J = values[:, 16] * 0.001
    total_energy_J = (values[:, 1] + values[:, 2] + values[:, 8] + values[:, 11]) * 0.001
    external_work_J = values[:, 9] * 0.001
    energy_residual_J = total_energy_J - total_energy_J[0] - external_work_J
    eroded_indices = np.flatnonzero(band_eroded > 0)
    separation_index = int(eroded_indices[0]) if len(eroded_indices) else len(values) - 1
    expected_area = float(meta["crack_area_mm2"])
    expected_yield_force = float(meta["material"]["yield_strength_mpa"]) * expected_area
    if meta["target_plastic_work_J"] is not None:
        target_plastic_work = float(meta["target_plastic_work_J"])
        plastic_mask = (plastic_work_J >= 0.10 * target_plastic_work) & (plastic_work_J <= 0.90 * target_plastic_work)
    else:
        target_plastic_work = None
        plastic_mask = plastic_work_J >= 0.10 * float(np.max(plastic_work_J))
    plastic_mask &= np.arange(len(values)) < separation_index
    if not np.any(plastic_mask):
        raise RuntimeError("No plastic plateau samples for " + case_id)
    plateau_force = float(np.median(reaction_force_N[plastic_mask]))
    shell_columns = [index for index, header in enumerate(headers) if "LOCALIZATION_BAND_ELEMENT_HISTORY" in header]
    expected_shell_columns = 3 * len(meta["band_elements"])
    if len(shell_columns) != expected_shell_columns:
        raise RuntimeError("Unexpected shell history layout for " + case_id)
    shell_history = values[:, shell_columns].reshape(len(values), len(meta["band_elements"]), 3)
    active = shell_history[:, :, 0]
    epsp = shell_history[:, :, 1]
    failure = bool(configured_case["failure"])
    warning_text = (directory / "starter.log").read_text(encoding="utf-8", errors="replace")
    warning_ids = sorted(set(re.findall(r"WARNING ID\s*:\s*(\d+)", warning_text)))
    engine_text = (directory / "engine.log").read_text(encoding="utf-8", errors="replace")
    cycles = re.findall(r"TOTAL NUMBER OF CYCLES\s*:\s*(\d+)", engine_text)
    execution = json.loads((directory / "execution.json").read_text(encoding="utf-8"))
    energy_scale = max(float(np.max(np.abs(total_energy_J))), float(np.max(np.abs(external_work_J))), 1.0e-12)
    max_ke_J = float(np.max(values[: separation_index + 1, 2]) * 0.001)
    max_ie_J = float(np.max(values[: separation_index + 1, 1]) * 0.001)
    source_current = all(sha(ROOT / path) == digest for path, digest in meta["source_sha256"].items())
    common_checks = {
        "time_monotonic_and_reaches_end": bool(np.all(np.diff(time_ms) > 0) and time_ms[-1] >= 0.999 * cfg["execution"]["end_ms"]),
        "mass_initial": abs(band_mass[0] - meta["expected_mass_g"]) <= 1.0e-7 * max(meta["expected_mass_g"], 1.0),
        "target_displacement": abs(right_displacement_mm[-1] - meta["target_displacement_mm"]) <= 0.002 * meta["target_displacement_mm"],
        "quasi_static": max_ke_J / max(max_ie_J, 1.0e-12) <= cfg["gates"]["maximum_kinetic_to_internal_energy_fraction_before_failure"],
        "global_energy": float(np.max(np.abs(energy_residual_J))) / energy_scale <= cfg["gates"]["maximum_global_energy_residual_fraction"],
        "plastic_plateau_force": abs(plateau_force - expected_yield_force) / expected_yield_force <= 0.03,
        "source_hashes": source_current,
        "config_hash": meta["config_sha256"] == sha(CFG),
        "generator_hash": meta["generator_sha256"] == sha(ROOT / "wtc1_simulation_v8/scripts/run_impact_i02f.py"),
        "executables_and_exit_codes": len(execution) == 3 and all(item["returncode"] == 0 and Path(item["command"][0]).is_file() and sha(Path(item["command"][0])) == item["executable_sha256"] for item in execution),
        "normal_engine_termination": "NORMAL TERMINATION" in engine_text and len(cycles) == 1,
        "no_solver_error": "ERROR ID" not in warning_text and "ERROR TERMINATION" not in engine_text,
        "warnings_bounded": warning_ids == (["3145"] if failure else []),
    }
    expected_total_at_failure_J = None
    plastic_error = None
    total_error = None
    if failure:
        elastic_energy_J = (
            0.5
            * float(meta["material"]["yield_strength_mpa"]) ** 2
            / float(meta["material"]["young_modulus_mpa"])
            * float(meta["mesh"]["h_mm"])
            * expected_area
            * 0.001
        )
        expected_total_at_failure_J = target_plastic_work + elastic_energy_J
        plastic_error = abs(plastic_work_J[separation_index] - target_plastic_work) / target_plastic_work
        total_error = abs(external_work_J[separation_index] - expected_total_at_failure_J) / expected_total_at_failure_J
        specific_checks = {
            "all_band_elements_eroded": int(round(band_eroded[-1])) == len(meta["band_elements"]),
            "mass_zero_after_deletion": abs(band_mass[-1]) <= 1.0e-12,
            "no_reactivation": bool(np.all(np.diff(active, axis=0) <= 1.0e-12)),
            "failure_strain_reached": abs(float(np.max(epsp)) - float(meta["failure_plastic_strain"])) / float(meta["failure_plastic_strain"]) <= 0.03,
            "plastic_work_target": plastic_error <= cfg["gates"]["maximum_plastic_work_target_error_fraction"],
            "total_work_target_including_elastic": total_error <= cfg["gates"]["maximum_plastic_work_target_error_fraction"],
        }
    else:
        specific_checks = {
            "no_band_element_eroded": int(round(band_eroded[-1])) == cfg["gates"]["required_unbreakable_eroded_elements"],
            "mass_preserved_without_failure": abs(band_mass[-1] - band_mass[0]) <= 1.0e-7 * max(band_mass[0], 1.0),
            "all_elements_active": bool(np.all(active == 1)),
            "control_plastic_strain_reached": float(np.max(epsp)) >= 0.95 * cfg["execution"]["non_eroding_control_plastic_strain"],
        }
    checks = {key: bool(value) for key, value in {**common_checks, **specific_checks}.items()}
    result = {
        "case_id": case_id,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "metrics": {
            "samples": len(values),
            "cycles": int(cycles[0]) if cycles else None,
            "shell_elements": len(meta["band_elements"]),
            "failure_plastic_strain": meta["failure_plastic_strain"],
            "maximum_plastic_strain": float(np.max(epsp)),
            "expected_yield_force_N": expected_yield_force,
            "plastic_plateau_force_N": plateau_force,
            "target_plastic_work_J": target_plastic_work,
            "plastic_work_at_separation_J": float(plastic_work_J[separation_index]) if failure else None,
            "expected_total_work_at_failure_J": expected_total_at_failure_J,
            "external_work_at_separation_J": float(external_work_J[separation_index]) if failure else None,
            "plastic_work_target_error_fraction": plastic_error,
            "total_work_target_error_fraction": total_error,
            "separation_time_ms": float(time_ms[separation_index]) if failure else None,
            "separation_displacement_mm": float(right_displacement_mm[separation_index]) if failure else None,
            "eroded_elements_final": int(round(band_eroded[-1])),
            "maximum_energy_residual_fraction": float(np.max(np.abs(energy_residual_J))) / energy_scale,
            "maximum_kinetic_to_internal_ratio_before_separation": max_ke_J / max(max_ie_J, 1.0e-12),
            "execution_seconds": sum(float(item["seconds"]) for item in execution),
            "warning_ids": warning_ids,
        },
    }
    dump_new(directory / "case_audit_r3.json", result)
    return result


def main() -> None:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    results = {case["id"].replace("_R0", "_R3"): audit_case(cfg, case) for case in cfg["cases"]}
    pairs: dict[str, dict] = {}
    for material, energy_labels in {
        "AA2024": ["G15", "G30", "G60"],
        "AA7075": ["GMIN", "GMEAN", "GMAX"],
    }.items():
        for energy in energy_labels:
            key = f"{material}_{energy}"
            coarse = results[f"{key}_H4_R3"]["metrics"]
            fine = results[f"{key}_H2_R3"]["metrics"]
            pairs[key] = {
                "plastic_plateau_force_difference_fraction": relative_difference(coarse["plastic_plateau_force_N"], fine["plastic_plateau_force_N"]),
                "plastic_work_difference_fraction": relative_difference(coarse["plastic_work_at_separation_J"], fine["plastic_work_at_separation_J"]),
                "total_separation_work_difference_fraction": relative_difference(coarse["external_work_at_separation_J"], fine["external_work_at_separation_J"]),
            }
    nominal = results["AA2024_G30_H2_R3"]["metrics"]
    halfdt = results["AA2024_G30_H2_HALFDT_R3"]["metrics"]
    temporal = {
        "plastic_plateau_force_difference_fraction": relative_difference(nominal["plastic_plateau_force_N"], halfdt["plastic_plateau_force_N"]),
        "plastic_work_difference_fraction": relative_difference(nominal["plastic_work_at_separation_J"], halfdt["plastic_work_at_separation_J"]),
        "total_separation_work_difference_fraction": relative_difference(nominal["external_work_at_separation_J"], halfdt["external_work_at_separation_J"]),
    }
    mesh_checks = {
        key + "_force": value["plastic_plateau_force_difference_fraction"] <= cfg["gates"]["maximum_peak_force_mesh_difference_fraction"]
        for key, value in pairs.items()
    }
    mesh_checks.update({
        key + "_plastic_work": value["plastic_work_difference_fraction"] <= cfg["gates"]["maximum_separation_work_mesh_difference_fraction"]
        for key, value in pairs.items()
    })
    mesh_checks.update({
        key + "_total_work": value["total_separation_work_difference_fraction"] <= cfg["gates"]["maximum_separation_work_mesh_difference_fraction"]
        for key, value in pairs.items()
    })
    campaign_checks = {
        "all_case_checks": all(result["status"] == "PASS" for result in results.values()),
        **mesh_checks,
        "temporal_force": temporal["plastic_plateau_force_difference_fraction"] <= cfg["gates"]["maximum_temporal_peak_force_difference_fraction"],
        "temporal_plastic_work": temporal["plastic_work_difference_fraction"] <= cfg["gates"]["maximum_temporal_peak_force_difference_fraction"],
        "temporal_total_work": temporal["total_separation_work_difference_fraction"] <= cfg["gates"]["maximum_temporal_peak_force_difference_fraction"],
        "2024_work_monotonic": all(
            results[f"AA2024_{energy}_H2_R3"]["metrics"]["plastic_work_at_separation_J"] < results[f"AA2024_{next_energy}_H2_R3"]["metrics"]["plastic_work_at_separation_J"]
            for energy, next_energy in [("G15", "G30"), ("G30", "G60")]
        ),
        "7075_work_monotonic": all(
            results[f"AA7075_{energy}_H2_R3"]["metrics"]["plastic_work_at_separation_J"] < results[f"AA7075_{next_energy}_H2_R3"]["metrics"]["plastic_work_at_separation_J"]
            for energy, next_energy in [("GMIN", "GMEAN"), ("GMEAN", "GMAX")]
        ),
    }
    comparisons = {
        "mesh_pairs": pairs,
        "temporal_half_dt": temporal,
        "interpretation": "Crack-band unit-cell numerical objectivity only; not an M(T) tearing calibration and not a Boeing material card.",
    }
    campaign = {
        "iteration": "IMPACT-I02F",
        "accepted_revision": "R3",
        "status": "PASS" if all(campaign_checks.values()) else "FAIL",
        "checks": campaign_checks,
        "accepted_cases": list(results),
        "case_results": results,
        "case_check_count": sum(len(result["checks"]) for result in results.values()),
        "campaign_check_count": len(campaign_checks),
        "accepted_execution_seconds_total": sum(result["metrics"]["execution_seconds"] for result in results.values()),
        "rejected_development_runs_preserved": ["AA2024_G30_H4_R0", "AA2024_G30_H4_R1", "AA2024_G30_H4_R2", "AA2024_G30_H2_R2"],
        "metal_tearing_physically_calibrated": False,
        "boeing_767_material_card_qualified": False,
        "notched_coupon_validated": False,
        "wing_zone_integration_authorized": False,
        "full_aircraft_impact_qualified": False,
        "cold_V11F_preserved": True,
    }
    dump_new(OUT / "comparisons_r3.json", comparisons)
    dump_new(OUT / "campaign_audit_r3.json", campaign)
    print(json.dumps({"status": campaign["status"], "cases": len(results), "case_checks": campaign["case_check_count"], "campaign_checks": len(campaign_checks), "failed": [key for key, value in campaign_checks.items() if not value]}))


if __name__ == "__main__":
    main()
