"""Release audit for cached IMPACT-I02A outputs; never reruns the solver."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "wtc1_simulation_v8/output/impact_i02a_structured_wing"
VIEW = ROOT / "wtc1_3d_v4/output/impact_i02a"
RENDER = ROOT / "wtc1_3d_v4/renders/impact_i02a"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def preserved_release(path: Path) -> bool:
    release = json.loads(path.read_text(encoding="utf-8-sig"))
    if release.get("delivery_status") != "PASS":
        return False
    return all((ROOT / item).is_file() and sha256(ROOT / item) == digest for item, digest in release["artifact_sha256"].items())


parser = argparse.ArgumentParser()
parser.add_argument("--phase", choices=("pre_state", "post_state"), required=True)
args = parser.parse_args()

checks: dict[str, bool] = {}
records: dict[str, object] = {}

campaign = json.loads((SIM / "campaign_audit.json").read_text())
comparisons = json.loads((SIM / "comparisons.json").read_text())
animation_export = json.loads((SIM / "animation_export_audit.json").read_text())
blender = json.loads((VIEW / "blender_audit.json").read_text())
animation = json.loads((VIEW / "animation_audit.json").read_text())

checks["campaign_pass_17_checks"] = campaign["status"] == "PASS" and len(campaign["checks"]) == 17 and all(campaign["checks"].values())
checks["three_accepted_normal_terminations"] = len(campaign["case_results"]) == 3 and all(row["normal_termination"] for row in campaign["case_results"].values())
checks["no_warnings_erosion_or_added_mass"] = all(
    row["starter_warnings"] == 0
    and row["max_wing_eroded_elements"] == 0
    and row["max_added_mass_fraction"] < 1.0e-6
    for row in campaign["case_results"].values()
)
checks["nominal_energy_momentum_reaction_gates"] = (
    campaign["case_results"]["CONTACT_M050_R1"]["max_abs_energy_error_fraction"] < 0.05
    and campaign["case_results"]["CONTACT_M050_R1"]["contact_wing_momentum_error_fraction"] < 0.02
    and campaign["case_results"]["CONTACT_M050_R1"]["support_total_momentum_error_fraction"] < 0.05
)
checks["half_dt_impulse_exact_record"] = abs(comparisons["half_dt_impulse_difference_fraction"] - 0.00025835717287846395) < 1.0e-12
checks["i01_comparison_exact_record"] = abs(comparisons["structured_relative_to_i01_impulse_change_fraction"] + 0.27223561863587165) < 1.0e-12
checks["physical_and_fracture_qualification_false"] = not campaign["physical_qualification"] and not campaign["fracture_qualification"]
checks["twenty_five_nominal_exported_states"] = animation_export["cases"]["CONTACT_M050_R1"]["converted_frames"] == 25
checks["export_identity_within_declared_tolerance"] = max(
    row["displacement_identity_error_mm"]
    for case in animation_export["cases"].values()
    for row in case["states"]
) < animation_export["position_quantization_tolerance_mm"]
checks["all_exported_elements_active"] = all(
    row["min_erosion_status"] == row["max_erosion_status"] == 1.0
    for case in animation_export["cases"].values()
    for row in case["states"]
)
checks["blender_audit_pass"] = blender["status"] == "PASS" and all(blender["checks"].values())
checks["blender_current_hash"] = sha256(VIEW / "IMPACT_I02A_SOLVER_STATES.blend") == blender["blend_sha256"]
checks["blender_exact_coordinate_transfer"] = blender["max_coordinate_error_m"] == 0.0 and blender["solver_states"] == 25
checks["gif_audit_pass"] = animation["status"] == "PASS" and all(animation["checks"].values())
checks["gif_current_hash"] = sha256(RENDER / "IMPACT_I02A_solver_states.gif") == animation["animation_sha256"]
with Image.open(RENDER / "IMPACT_I02A_solver_states.gif") as gif:
    checks["gif_reopens_25_frames"] = gif.size == (960, 620) and gif.n_frames == 25
for filename in ("I02A_initial.png", "I02A_contact_0p25ms.png", "I02A_final_1p20ms.png"):
    with Image.open(RENDER / filename) as image:
        image.verify()
    checks[f"image_{filename}"] = Image.open(RENDER / filename).size == (960, 620)

source_manifest = json.loads((SIM / "source_manifest.json").read_text())
checks["source_manifest_files_unchanged"] = all(
    (ROOT / item["path"]).is_file() and sha256(ROOT / item["path"]) == item["sha256"]
    for item in source_manifest["files"]
)
checks["report_and_handoff_exist"] = (SIM / "rapport_impact_i02a.md").is_file() and (ROOT / "harness/handoffs/WTC1_IMPACT_I02A_HANDOFF.md").is_file()
checks["impact_i01_preserved"] = preserved_release(ROOT / "wtc1_simulation_v8/output/impact_i01_first_contact/release_audit.json")
checks["impact_i02_geom_preserved"] = preserved_release(ROOT / "wtc1_3d_v4/output/impact_i02_geom/final/release_audit.json")

for name in ("v11f_panel_coupling", "v11r_integrated_panel"):
    manifest = json.loads((ROOT / "wtc1_simulation_v8/output" / name / "offline_manifest.json").read_text())
    preserved = []
    for key, value in manifest.items():
        if "sha256" not in key or not isinstance(value, dict):
            continue
        for path, digest in value.items():
            target = ROOT / "wtc1_simulation_v8/output" / name / path if key == "output_sha256" else ROOT / path
            if name in str(target) or ("v11f_" in str(target) if name.startswith("v11f") else "v11r_" in str(target)):
                preserved.append(target.is_file() and sha256(target) == digest)
    checks[f"{name}_preserved"] = bool(preserved) and all(preserved)
    records[f"{name}_hash_count"] = len(preserved)

power_shell = r"C:\Program Files\PowerShell\7\pwsh.exe"
command = "& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6 -Compress"
process = subprocess.run(
    [power_shell, "-NoProfile", "-Command", command],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=60,
)
(SIM / f"harness_{args.phase}.log").write_text(process.stdout + process.stderr, encoding="utf-8")
try:
    harness = json.loads(process.stdout)
except json.JSONDecodeError:
    harness = {"Status": "FAIL", "raw": process.stdout}
checks["harness_pass"] = process.returncode == 0 and harness.get("Status") == "PASS"

state = json.loads((ROOT / "harness/state.json").read_text())
registry = [
    json.loads(line)
    for line in (ROOT / "harness/experiments/registry.jsonl").read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
]
registered = sum(item.get("experiment_id") == "WTC1-IMPACT-I02A" for item in registry)
if args.phase == "pre_state":
    checks["pre_state_route"] = state["current_iteration"] == "IMPACT-I02-GEOM" and state["next_iteration"] == "IMPACT-I02"
    checks["pre_registry_absent"] = registered == 0
else:
    checks["post_state_route"] = state["current_iteration"] == "IMPACT-I02A" and state["next_iteration"] == "IMPACT-I02B"
    checks["post_registry_once"] = registered == 1

artifacts = [
    ROOT / "wtc1_simulation_v8/data/impact_i02a_structured_wing.json",
    ROOT / "wtc1_simulation_v8/scripts/run_impact_i02a.py",
    ROOT / "wtc1_simulation_v8/scripts/export_impact_i02a.py",
    ROOT / "wtc1_simulation_v8/scripts/audit_impact_i02a.py",
    ROOT / "wtc1_simulation_v8/scripts/plot_impact_i02a.py",
    SIM / "rapport_impact_i02a.md",
    SIM / "campaign_audit.json",
    SIM / "comparisons.json",
    SIM / "source_manifest.json",
    SIM / "synthese_impact_i02a.png",
    ROOT / "wtc1_3d_v4/scripts/build_impact_i02a.py",
    ROOT / "wtc1_3d_v4/scripts/verify_impact_i02a_blend.py",
    ROOT / "wtc1_3d_v4/scripts/encode_impact_i02a_gif.py",
    VIEW / "IMPACT_I02A_SOLVER_STATES.blend",
    VIEW / "build_manifest.json",
    VIEW / "blender_audit.json",
    VIEW / "animation_audit.json",
    RENDER / "IMPACT_I02A_solver_states.gif",
    RENDER / "I02A_initial.png",
    RENDER / "I02A_contact_0p25ms.png",
    RENDER / "I02A_final_1p20ms.png",
    ROOT / "harness/handoffs/WTC1_IMPACT_I02A_HANDOFF.md",
]
checks["all_release_artifacts_exist"] = all(path.is_file() for path in artifacts)
result = {
    "phase": args.phase,
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "delivery_status": "PASS" if all(checks.values()) else "FAIL",
    "meaning": "Numerical and visualization consistency for a reduced non-eroding structured wing section; not physical WTC1 validation.",
    "checks": checks,
    "records": records,
    "harness": harness,
    "artifact_sha256": {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in artifacts
    },
}
target = SIM / ("release_audit.json" if args.phase == "post_state" else "release_audit_pre_state.json")
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["delivery_status"],
    "checks": len(checks),
    "failed": [name for name, passed in checks.items() if not passed],
    "records": records,
    "harness": harness,
}, indent=2))
sys.exit(0 if all(checks.values()) else 1)
