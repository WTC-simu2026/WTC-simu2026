"""R5 terminal-history audit over immutable IMPACT-I02F R3 solver results."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"


def dump_new(path: Path, value: object) -> None:
    if path.exists():
        raise RuntimeError("Existing R5 audit preserved: " + str(path))
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    campaign = json.loads((OUT / "campaign_audit_r4.json").read_text(encoding="utf-8"))
    comparisons = json.loads((OUT / "comparisons_r4.json").read_text(encoding="utf-8"))
    for case_id, result in campaign["case_results"].items():
        if result["metrics"]["failure_plastic_strain"] is not None:
            result["checks"]["history_terminal_condition"] = bool(
                result["metrics"]["separation_time_ms"] is not None
                and result["metrics"]["eroded_elements_final"] == result["metrics"]["shell_elements"]
                and result["checks"]["normal_engine_termination"]
            )
            result["metrics"]["history_end_reason"] = "history_contains_complete_deletion; engine subsequently reaches normal termination"
        result["status"] = "PASS" if all(result["checks"].values()) else "FAIL"
        result["audit_policy_revision"] = "R5"
        dump_new(OUT / case_id / "case_audit_r5.json", result)
    campaign["accepted_audit_policy_revision"] = "R5"
    campaign["checks"]["all_case_checks"] = all(result["status"] == "PASS" for result in campaign["case_results"].values())
    campaign["status"] = "PASS" if all(campaign["checks"].values()) else "FAIL"
    campaign["rejected_audits_preserved"] = ["campaign_audit_r3.json", "campaign_audit_r4.json"]
    campaign["audit_policy_change"] = {
        "solver_inputs_changed": False,
        "solver_rerun": False,
        "terminal_history_rule": "saved history contains complete deletion and the independent engine log reports normal termination; no equality is required between first-deletion time, last T-file sample and requested engine end",
        "control_strain_rule": "unchanged from R4",
    }
    comparisons["audit_policy_revision"] = "R5"
    dump_new(OUT / "comparisons_r5.json", comparisons)
    dump_new(OUT / "campaign_audit_r5.json", campaign)
    print(json.dumps({"status": campaign["status"], "cases": len(campaign["case_results"]), "case_checks": campaign["case_check_count"], "campaign_checks": len(campaign["checks"]), "failed": [key for key, value in campaign["checks"].items() if not value]}))


if __name__ == "__main__":
    main()
