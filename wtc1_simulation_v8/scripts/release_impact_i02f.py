"""Final pre/post-state release gate for IMPACT-I02F."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def hashes_match(mapping: dict[str, str]) -> bool:
    return bool(mapping) and all((ROOT / path).is_file() and sha(ROOT / path) == digest for path, digest in mapping.items())


parser = argparse.ArgumentParser()
parser.add_argument("--phase", choices=["pre_state", "post_state"], required=True)
args = parser.parse_args()

campaign = read(OUT / "campaign_audit_r5.json")
comparisons = read(OUT / "comparisons_r5.json")
zone = read(OUT / "ZONE_AA2024_G30_H0635_R0/zone_audit_r0.json")
summary = read(OUT / "summary_i02f_r1.json")
manifest = read(OUT / "artifact_manifest_r1.json")
checks: dict[str, bool] = {}
records: dict[str, object] = {}

checks["unit_cell_campaign"] = (
    campaign["status"] == "PASS"
    and len(campaign["accepted_cases"]) == 15
    and campaign["case_check_count"] == 281
    and campaign["campaign_check_count"] == 24
    and all(campaign["checks"].values())
    and all(result["status"] == "PASS" and all(result["checks"].values()) for result in campaign["case_results"].values())
)
checks["mesh_and_time_comparisons"] = all(
    value["plastic_plateau_force_difference_fraction"] <= 0.05
    and value["plastic_work_difference_fraction"] <= 0.10
    and value["total_separation_work_difference_fraction"] <= 0.10
    for value in comparisons["mesh_pairs"].values()
) and max(comparisons["temporal_half_dt"].values()) <= 0.03
checks["zone_audit"] = zone["status"] == "PASS" and len(zone["checks"]) == 28 and all(zone["checks"].values())
checks["qualification_limits"] = (
    not summary["physical_2024_tearing_calibrated"]
    and not summary["boeing_767_wing_qualified"]
    and not summary["full_facade_qualified"]
    and not summary["historical_penetration_conclusion_authorized"]
    and not zone["qualification"]["irregular_shell_characteristic_length_regularized"]
)
checks["summary_and_report"] = (
    summary["status"] == "PASS"
    and sha(OUT / "rapport_impact_i02f_r1.md") == summary["report_sha256"]
    and sha(OUT / "synthese_impact_i02f_r1.png") == summary["figure_sha256"]
)
with Image.open(OUT / "synthese_impact_i02f_r1.png") as image:
    image.verify()
    checks["figure_readable"] = image.size == (1800, 920)
checks["manifest_current"] = manifest["file_count"] == len(manifest["files"]) and hashes_match(manifest["files"])

i02e_release = read(ROOT / "wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/release_audit.json")
checks["I02E_preserved"] = i02e_release["delivery_status"] == "PASS" and hashes_match(i02e_release["artifact_sha256"])
for name in ["v11f_panel_coupling", "v11r_integrated_panel"]:
    old = read(ROOT / "wtc1_simulation_v8/output" / name / "offline_manifest.json")
    retained = []
    for key, value in old.items():
        if "sha256" not in key or not isinstance(value, dict):
            continue
        for path, digest in value.items():
            target = ROOT / "wtc1_simulation_v8/output" / name / path if key == "output_sha256" else ROOT / path
            if name in str(target) or ("v11f_" in str(target) if name.startswith("v11f") else "v11r_" in str(target)):
                retained.append(target.is_file() and sha(target) == digest)
    checks[name + "_preserved"] = bool(retained) and all(retained)
    records[name + "_hashes"] = len(retained)

artifacts = [
    ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json",
    *[ROOT / "wtc1_simulation_v8/scripts" / name for name in [
        "run_impact_i02f.py", "audit_impact_i02f.py", "audit_impact_i02f_r4.py", "audit_impact_i02f_r5.py",
        "run_impact_i02f_zone.py", "audit_impact_i02f_zone.py", "summarize_impact_i02f.py",
        "manifest_impact_i02f.py", "release_impact_i02f.py",
    ]],
    OUT / "campaign_audit_r5.json",
    OUT / "comparisons_r5.json",
    OUT / "ZONE_AA2024_G30_H0635_R0/zone_audit_r0.json",
    OUT / "summary_i02f_r1.json",
    OUT / "rapport_impact_i02f_r1.md",
    OUT / "synthese_impact_i02f_r1.png",
    OUT / "artifact_manifest_r1.json",
    ROOT / "harness/handoffs/WTC1_IMPACT_I02F_HANDOFF.md",
]
checks["release_artifacts_exist"] = all(path.is_file() for path in artifacts)

process = subprocess.run(
    [r"C:\Program Files\PowerShell\7\pwsh.exe", "-NoProfile", "-Command", "& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6 -Compress"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=60,
)
(OUT / f"harness_{args.phase}.log").write_text(process.stdout + process.stderr, encoding="utf-8", newline="\n")
harness = json.loads(process.stdout)
checks["harness_pass"] = process.returncode == 0 and harness["Status"] == "PASS"

state = read(ROOT / "harness/state.json")
lines = (ROOT / "harness/experiments/registry.jsonl").read_text(encoding="utf-8-sig").splitlines()
registry = [json.loads(line) for line in lines if line.strip()]
count = sum(row.get("experiment_id") == "WTC1-IMPACT-I02F" for row in registry)
prefix = hashlib.sha256("\n".join(lines[:104]).encode()).hexdigest()
if args.phase == "pre_state":
    checks["route_before"] = state["current_iteration"] == "IMPACT-I02E" and state["next_iteration"] == "IMPACT-I02F"
    checks["registry_before"] = len(registry) == 104 and count == 0
else:
    pre = read(OUT / "release_audit_pre_state.json")
    checks["pre_audit"] = pre["delivery_status"] == "PASS" and hashes_match(pre["artifact_sha256"])
    checks["registry_prefix"] = prefix == pre["registry_prefix_sha256"]
    checks["route_after"] = state["current_iteration"] == "IMPACT-I02F" and state["next_iteration"] == "IMPACT-I02G"
    checks["registry_after"] = len(registry) == 105 and count == 1
    key = state["impact_i02f_key_results"]
    checks["state_key_results"] = (
        key["unit_cell_cases"] == 15
        and key["zone_skin_eroded_shells"] == 336
        and not key["physical_2024_tearing_calibrated"]
        and not key["boeing_767_wing_qualified"]
    )

records.update(
    manifest_files=manifest["file_count"],
    unit_cell_cases=len(campaign["accepted_cases"]),
    unit_cell_case_checks=campaign["case_check_count"],
    unit_cell_campaign_checks=campaign["campaign_check_count"],
    zone_checks=len(zone["checks"]),
    zone_skin_eroded_shells=zone["max_wing_eroded_shells"],
    zone_contact_impulse_Ns=zone["final_contact_impulse_abs_Ns"],
)
result = {
    "phase": args.phase,
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "delivery_status": "PASS" if all(checks.values()) else "FAIL",
    "checks": checks,
    "records": records,
    "harness": harness,
    "registry_prefix_sha256": prefix,
    "meaning": "Numerically regularized prescribed crack-band unit cells and one local I02E sensitivity only; no physical Boeing material card, notched-coupon validation, full facade or historical penetration conclusion.",
    "artifact_sha256": {rel(path): sha(path) for path in artifacts},
}
target = OUT / ("release_audit.json" if args.phase == "post_state" else "release_audit_pre_state.json")
target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": result["delivery_status"], "checks": len(checks), "failed": [key for key, value in checks.items() if not value], "records": records}))
if result["delivery_status"] != "PASS":
    raise SystemExit(1)
