"""Audit the single I02F local I02E-zone metal-tearing sensitivity."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_impact_i02e import audit, load_config


ROOT = Path(__file__).resolve().parents[2]
BASE_CFG = ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r9.json"
COUPON_CFG = ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json"
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"
CASE_ID = "ZONE_AA2024_G30_H0635_R0"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes_match(mapping: dict[str, str]) -> bool:
    return bool(mapping) and all((ROOT / path).is_file() and sha(ROOT / path) == digest for path, digest in mapping.items())


def main() -> None:
    target = OUT / CASE_ID / "zone_audit_r0.json"
    if target.exists():
        raise RuntimeError("Existing zone audit preserved: " + str(target))
    cfg = load_config(BASE_CFG)
    cfg["output_root"] = "wtc1_simulation_v8/output/impact_i02f_tear_coupon"
    result = audit(CASE_ID, cfg)
    directory = OUT / CASE_ID
    meta = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
    coupon = json.loads(COUPON_CFG.read_text(encoding="utf-8"))
    base_campaign = json.loads((ROOT / "wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/campaign_audit_r10.json").read_text(encoding="utf-8"))
    base = base_campaign["case_results"]["CONTACT_RUPTURABLE_H0635_R9"]
    base_release_path = ROOT / "wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/release_audit.json"
    base_release = json.loads(base_release_path.read_text(encoding="utf-8"))
    csv_path = directory / f"{meta['name']}T01.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        headers = next(csv.reader(stream))
    values = np.loadtxt(csv_path, delimiter=",", skiprows=1)
    skin_eroded_column = next(index for index, header in enumerate(headers) if "WING_SKINS" in header and "ERODED" in header)
    skin_mass_column = next(index for index, header in enumerate(headers) if "WING_SKINS" in header and "MASS" in header)
    first_eroded = int(np.flatnonzero(values[:, skin_eroded_column] > 0)[0])
    skin_shells = meta["element_ranges"]["2"][1] - meta["element_ranges"]["2"][0] + 1
    skin_mass_loss_g = float(values[0, skin_mass_column] - values[-1, skin_mass_column])
    skin_mass_loss_fraction = skin_mass_loss_g / float(values[0, skin_mass_column])
    impulse_change = (result["final_contact_impulse_abs_Ns"] - base["final_contact_impulse_abs_Ns"]) / base["final_contact_impulse_abs_Ns"]
    joint_work_change = (result["final_joint_work_J"] - base["final_joint_work_J"]) / base["final_joint_work_J"]
    wing_ie_change = (result["max_wing_shell_internal_energy_J"] - base["max_wing_shell_internal_energy_J"]) / base["max_wing_shell_internal_energy_J"]
    execution = json.loads((directory / "execution.json").read_text(encoding="utf-8"))
    source_current = all(sha(ROOT / path) == digest for path, digest in meta["source_sha256"].items())
    checks = dict(result["checks"])
    checks.pop("starter_warnings")
    checks.pop("wing_shells_not_eroded")
    checks.update(
        warnings_expected_for_disjoint_type7_and_obsolete_tab1=(result["warning_ids"] == ["3145", "477"] and result["contact_main_secondary_node_sets_disjoint"]),
        skin_erosion_occurs=0 < result["max_wing_eroded_shells"] < skin_shells,
        skin_eroded_count_matches_mass_loss=abs(skin_mass_loss_fraction - result["max_wing_eroded_shells"] / skin_shells) <= 1.0e-6,
        inherited_material_history_preserved=abs(meta["i02f_metal_tearing"]["inherited_yield_strength_mpa"] - 310.264) <= 1.0e-12,
        crack_band_equation=abs(meta["i02f_metal_tearing"]["failure_plastic_strain"] - 30.0 / (310.264 * 6.35)) <= 1.0e-14,
        source_hashes=source_current,
        coupon_config_hash=meta["coupon_config_sha256"] == sha(COUPON_CFG),
        zone_runner_hash=meta["generator_sha256"] == sha(ROOT / "wtc1_simulation_v8/scripts/run_impact_i02f_zone.py"),
        starter_and_engine_hashes=(
            meta["starter_sha256"] == sha(directory / f"{meta['name']}_0000.rad")
            and meta["engine_sha256"] == sha(directory / f"{meta['name']}_0001.rad")
        ),
        executable_hashes=all(Path(item["command"][0]).is_file() and sha(Path(item["command"][0])) == item["executable_sha256"] for item in execution),
        i02e_baseline_release_current=base_release["delivery_status"] == "PASS" and hashes_match(base_release["artifact_sha256"]),
        same_initial_energy_as_baseline=abs(result["initial_ke_J"] - base["initial_ke_J"]) <= 1.0e-6,
        same_initial_mass_as_baseline=abs(result["initial_global_mass_g"] - base["initial_global_mass_g"]) <= 1.0e-6,
        cohesive_zone_remains_active=not result["any_cohesive_deletion"] and result["minimum_active_area_fraction"] >= 0.999999,
    )
    result.update(
        status="PASS" if all(checks.values()) else "FAIL",
        checks=checks,
        first_skin_erosion_time_ms=float(values[first_eroded, 0]),
        skin_shell_count=skin_shells,
        skin_eroded_fraction=result["max_wing_eroded_shells"] / skin_shells,
        skin_mass_loss_g=skin_mass_loss_g,
        skin_mass_loss_fraction=skin_mass_loss_fraction,
        baseline_case="CONTACT_RUPTURABLE_H0635_R9",
        comparison_to_no_metal_tearing_baseline={
            "contact_impulse_change_fraction": impulse_change,
            "joint_work_change_fraction": joint_work_change,
            "maximum_wing_internal_energy_change_fraction": wing_ie_change,
        },
        qualification={
            "unit_cell_energy_gate_passed": json.loads((OUT / "campaign_audit_r5.json").read_text(encoding="utf-8"))["status"] == "PASS",
            "physical_2024_tearing_calibrated": False,
            "notched_coupon_validated": False,
            "irregular_shell_characteristic_length_regularized": False,
            "boeing_767_wing_qualified": False,
            "full_facade_qualified": False,
            "historical_penetration_conclusion_authorized": False,
        },
        interpretation=(
            "This single-zone run proves numerical sensitivity to the declared Gf=30 N/mm constant-strain deletion hypothesis. "
            "It does not establish that 2024-T3 has that dynamic fracture energy, that the local I02E bay represents an as-built Boeing wing, "
            "or that the real aircraft did or did not penetrate the WTC1 facade."
        ),
        source_count=len(coupon["sources"]),
    )
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), "failed": [key for key, value in checks.items() if not value], "skin_eroded": result["max_wing_eroded_shells"], "skin_eroded_fraction": result["skin_eroded_fraction"], "impulse_change_fraction": impulse_change}))


if __name__ == "__main__":
    main()
