"""R4 audit-policy correction over immutable IMPACT-I02F R3 solver histories."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json"
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"


def dump_new(path: Path, value: object) -> None:
    if path.exists():
        raise RuntimeError("Existing R4 audit preserved: " + str(path))
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    previous = json.loads((OUT / "campaign_audit_r3.json").read_text(encoding="utf-8"))
    comparisons = json.loads((OUT / "comparisons_r3.json").read_text(encoding="utf-8"))
    revised_results = {}
    for configured in cfg["cases"]:
        case_id = configured["id"].replace("_R0", "_R3")
        directory = OUT / case_id
        result = json.loads(json.dumps(previous["case_results"][case_id]))
        meta = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
        csv_path = directory / f"{meta['name']}T01.csv"
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            headers = next(csv.reader(stream))
        values = np.loadtxt(csv_path, delimiter=",", skiprows=1)
        time_ms = values[:, 0]
        old_time = result["checks"].pop("time_monotonic_and_reaches_end")
        if configured["failure"]:
            terminal_condition = (
                np.all(np.diff(time_ms) > 0)
                and time_ms[-1] <= cfg["execution"]["end_ms"]
                and result["metrics"]["eroded_elements_final"] == result["metrics"]["shell_elements"]
                and result["metrics"]["separation_time_ms"] == float(time_ms[-1])
            )
            result["checks"]["history_terminal_condition"] = bool(terminal_condition)
            result["metrics"]["audit_r3_time_gate"] = old_time
            result["metrics"]["history_end_reason"] = "all_model_elements_deleted_before_requested_engine_end"
        else:
            result["checks"]["history_terminal_condition"] = bool(
                np.all(np.diff(time_ms) > 0) and time_ms[-1] >= 0.999 * cfg["execution"]["end_ms"]
            )
            old_control = result["checks"].pop("control_plastic_strain_reached")
            material = meta["material"]
            elastic_yield = material["yield_strength_mpa"] / material["young_modulus_mpa"]
            imposed_engineering_total = elastic_yield + cfg["execution"]["non_eroding_control_plastic_strain"]
            expected_log_plastic = math.log1p(imposed_engineering_total) - elastic_yield
            measured = result["metrics"]["maximum_plastic_strain"]
            result["checks"]["control_logarithmic_plastic_strain"] = abs(measured - expected_log_plastic) / expected_log_plastic <= 0.01
            result["metrics"]["audit_r3_control_gate"] = old_control
            result["metrics"]["expected_logarithmic_plastic_strain"] = expected_log_plastic
            result["metrics"]["strain_measure_interpretation"] = "logarithmic shell plastic strain compared with the finite-strain transform of the prescribed engineering strain"
        result["status"] = "PASS" if all(result["checks"].values()) else "FAIL"
        result["audit_policy_revision"] = "R4"
        dump_new(directory / "case_audit_r4.json", result)
        revised_results[case_id] = result
    campaign = json.loads(json.dumps(previous))
    campaign["accepted_solver_revision"] = "R3"
    campaign["accepted_audit_policy_revision"] = "R4"
    campaign.pop("accepted_revision", None)
    campaign["case_results"] = revised_results
    campaign["case_check_count"] = sum(len(result["checks"]) for result in revised_results.values())
    campaign["checks"]["all_case_checks"] = all(result["status"] == "PASS" for result in revised_results.values())
    campaign["status"] = "PASS" if all(campaign["checks"].values()) else "FAIL"
    campaign["rejected_audits_preserved"] = ["campaign_audit_r3.json"]
    campaign["audit_policy_change"] = {
        "solver_inputs_changed": False,
        "solver_rerun": False,
        "history_terminal_rule": "requested end time OR complete deletion of every modeled element",
        "control_strain_rule": "compare saved logarithmic plastic strain with finite-strain transform of prescribed engineering strain",
    }
    comparisons["audit_policy_revision"] = "R4"
    comparisons["solver_results_changed"] = False
    dump_new(OUT / "comparisons_r4.json", comparisons)
    dump_new(OUT / "campaign_audit_r4.json", campaign)
    print(json.dumps({"status": campaign["status"], "cases": len(revised_results), "case_checks": campaign["case_check_count"], "campaign_checks": len(campaign["checks"]), "failed": [key for key, value in campaign["checks"].items() if not value]}))


if __name__ == "__main__":
    main()
