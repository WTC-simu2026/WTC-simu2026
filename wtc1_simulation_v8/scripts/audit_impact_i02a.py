"""Aggregate, gate and document the accepted IMPACT-I02A calculations."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CFG_PATH = ROOT / "wtc1_simulation_v8/data/impact_i02a_structured_wing.json"
RUN_SCRIPT = ROOT / "wtc1_simulation_v8/scripts/run_impact_i02a.py"
EXPORT_SCRIPT = ROOT / "wtc1_simulation_v8/scripts/export_impact_i02a.py"
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02a_structured_wing"
I01 = ROOT / "wtc1_simulation_v8/output/impact_i01_first_contact"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_json(CFG_PATH)
    results = {case["id"]: load_json(OUTPUT / case["id"] / "results.json") for case in cfg["cases"]}
    free = results["FREE_M050_R1"]
    nominal = results["CONTACT_M050_R1"]
    half_dt = results["CONTACT_DT045_R1"]
    animation = load_json(OUTPUT / "animation_export_audit.json")

    common_time = min(nominal["end_ms"], half_dt["end_ms"])
    nominal_history = load_json(OUTPUT / "CONTACT_M050_R1/history_si.json")
    half_history = load_json(OUTPUT / "CONTACT_DT045_R1/history_si.json")
    nominal_impulse_common = float(np.interp(common_time, [row["t_ms"] for row in nominal_history], [abs(row["contact_impulse_Ns"]) for row in nominal_history]))
    half_impulse_common = float(np.interp(common_time, [row["t_ms"] for row in half_history], [abs(row["contact_impulse_Ns"]) for row in half_history]))
    dt_difference = abs(nominal_impulse_common - half_impulse_common) / max(nominal_impulse_common, half_impulse_common)

    i01_result = load_json(I01 / "M050/results.json")
    i01_history = load_json(I01 / "M050/history_si.json")
    i01_impulse_common = float(np.interp(common_time, [row["t_ms"] for row in i01_history], [row["contact_impulse_abs_Ns"] for row in i01_history]))
    topology_impulse_change = (nominal_impulse_common - i01_impulse_common) / i01_impulse_common
    mass_change = (nominal["initial_wing_mass_kg"] - i01_result["box_mass_kg"]) / i01_result["box_mass_kg"]

    final_epsp = animation["cases"]["CONTACT_M050_R1"]["states"][-1]["max_epsp_by_part"]
    final_epsp_dt = animation["cases"]["CONTACT_DT045_R1"]["states"][-1]["max_epsp_by_part"]
    max_epsp_relative_difference = max(
        abs(final_epsp[str(part)] - final_epsp_dt[str(part)]) / max(abs(final_epsp[str(part)]), abs(final_epsp_dt[str(part)]), 1.0e-30)
        for part in range(1, 8)
    )

    checks = {
        "normal_termination_all": all(result["normal_termination"] for result in results.values()),
        "starter_warnings_zero_all": all(result["starter_warnings"] <= cfg["predeclared_checks"]["max_starter_warnings"] for result in results.values()),
        "initial_penetrations_zero_all": all(max(result["initial_penetration_counts"] or [0]) <= cfg["predeclared_checks"]["max_initial_penetrations"] for result in results.values()),
        "energy_error_nominal": nominal["max_abs_energy_error_fraction"] <= cfg["predeclared_checks"]["max_abs_energy_error_fraction"],
        "energy_error_half_dt": half_dt["max_abs_energy_error_fraction"] <= cfg["predeclared_checks"]["max_abs_energy_error_fraction"],
        "contact_momentum_nominal": nominal["contact_wing_momentum_error_fraction"] <= cfg["predeclared_checks"]["max_momentum_impulse_relative_error"],
        "contact_momentum_half_dt": half_dt["contact_wing_momentum_error_fraction"] <= cfg["predeclared_checks"]["max_momentum_impulse_relative_error"],
        "support_momentum_nominal": nominal["support_total_momentum_error_fraction"] <= cfg["predeclared_checks"]["max_support_impulse_total_momentum_relative_error"],
        "support_momentum_half_dt": half_dt["support_total_momentum_error_fraction"] <= cfg["predeclared_checks"]["max_support_impulse_total_momentum_relative_error"],
        "added_mass_all": all(result["max_added_mass_fraction"] <= cfg["predeclared_checks"]["max_added_mass_fraction"] for result in results.values()),
        "hourglass_nominal": nominal["max_hourglass_over_initial_ke"] <= cfg["predeclared_checks"]["max_hourglass_over_initial_ke"],
        "hourglass_half_dt": half_dt["max_hourglass_over_initial_ke"] <= cfg["predeclared_checks"]["max_hourglass_over_initial_ke"],
        "half_dt_impulse": dt_difference <= cfg["predeclared_checks"]["max_half_dt_impulse_difference"],
        "free_flight_speed": free["free_flight_speed_error_fraction"] <= cfg["predeclared_checks"]["max_free_flight_speed_error_fraction"],
        "eroded_elements_zero_all": all(result["max_wing_eroded_elements"] == cfg["predeclared_checks"]["eroded_elements"] for result in results.values()),
        "animation_identity_all": all(
            state["displacement_identity_error_mm"] < animation["position_quantization_tolerance_mm"]
            for case in animation["cases"].values()
            for state in case["states"]
        ),
        "animation_all_elements_active": all(
            state["min_erosion_status"] == 1.0 and state["max_erosion_status"] == 1.0
            for case in animation["cases"].values()
            for state in case["states"]
        ),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    comparison = {
        "common_time_ms": common_time,
        "structured_impulse_Ns": nominal_impulse_common,
        "structured_half_dt_impulse_Ns": half_impulse_common,
        "half_dt_impulse_difference_fraction": dt_difference,
        "i01_closed_box_impulse_Ns": i01_impulse_common,
        "structured_relative_to_i01_impulse_change_fraction": topology_impulse_change,
        "structured_mass_kg": nominal["initial_wing_mass_kg"],
        "i01_closed_box_mass_kg": i01_result["box_mass_kg"],
        "mass_change_fraction": mass_change,
        "interpretation": "The 27 percent impulse shift at nearly unchanged mass proves that internal topology and thickness assignment matter in this reduced numerical model. It is not an observed aircraft-impact measurement and cannot identify real fracture.",
    }
    write_json(OUTPUT / "comparisons.json", comparison)

    execution_seconds = {}
    for case in cfg["cases"]:
        execution_seconds[case["id"]] = sum(item["seconds"] for item in load_json(OUTPUT / case["id"] / "execution.json"))
    campaign = {
        "id": cfg["id"],
        "status": status,
        "checks": checks,
        "case_results": results,
        "comparison": comparison,
        "max_effective_plastic_strain_by_part_nominal": final_epsp,
        "max_effective_plastic_strain_by_part_half_dt": final_epsp_dt,
        "max_epsp_relative_difference_half_dt": max_epsp_relative_difference,
        "accepted_case_execution_seconds": execution_seconds,
        "rejected_preflight": {
            "path": "wtc1_simulation_v8/output/impact_i02a_structured_wing/FREE_M050",
            "reason": "Seven /PROP/SHELL unsupported-field warnings from an explicit obsolete Istrain field. Preserved and superseded by FREE_M050_R1 with zero warnings.",
        },
        "physical_qualification": False,
        "fracture_qualification": False,
        "graphics_geometry_mechanical_credit": 0,
    }
    write_json(OUTPUT / "campaign_audit.json", campaign)

    manifest_paths = [
        CFG_PATH,
        RUN_SCRIPT,
        EXPORT_SCRIPT,
        Path(__file__).resolve(),
        ROOT / "wtc1_simulation_v8/scripts/plot_impact_i02a.py",
        ROOT / "work/official_sources/ncstar1-2bv1.pdf",
        ROOT / "wtc1_simulation_v8/data/impact_i01_first_contact.json",
        ROOT / "wtc1_simulation_v8/data/impact_i02_geom.json",
    ]
    manifest = {
        "generated_by": "wtc1_simulation_v8/scripts/audit_impact_i02a.py",
        "python": sys.version,
        "platform": platform.platform(),
        "files": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in manifest_paths
        ],
        "remote_sources": [source for source in cfg["sources"] if "url" in source],
    }
    write_json(OUTPUT / "source_manifest.json", manifest)
    print(json.dumps({"status": status, "checks": len(checks), "comparison": comparison, "max_epsp": final_epsp}, ensure_ascii=False))


if __name__ == "__main__":
    main()
