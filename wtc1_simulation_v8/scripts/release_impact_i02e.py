"""Final release gate before and after registering IMPACT-I02E."""

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
SIM = ROOT / "wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone"
VIEW = ROOT / "wtc1_3d_v4/output/impact_i02e"
MEDIA = ROOT / "wtc1_3d_v4/renders/impact_i02e"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def hashes_match(mapping: dict[str, str]) -> bool:
    return bool(mapping) and all((ROOT / path).is_file() and sha256(ROOT / path) == digest for path, digest in mapping.items())


parser = argparse.ArgumentParser()
parser.add_argument("--phase", choices=["pre_state", "post_state"], required=True)
args = parser.parse_args()

campaign = read_json(SIM / "campaign_audit_r10.json")
comparisons = read_json(SIM / "comparisons_r10.json")
manifest = read_json(SIM / "source_manifest_r10.json")
accepted = campaign["accepted_cases"]
rows = campaign["case_results"]
checks: dict[str, bool] = {}
records: dict[str, object] = {}

checks["campaign_pass"] = campaign["status"] == "PASS" and len(accepted) == 8 and all(campaign["checks"].values())
checks["129_case_checks_pass"] = campaign["case_check_count"] == 129 and sum(len(row["checks"]) for row in rows.values()) == 129 and all(
    all(row["checks"].values()) for row in rows.values()
)
checks["qualification_limits_retained"] = not any(
    campaign[key]
    for key in [
        "physical_aircraft_impact_qualified",
        "metal_tearing_qualified",
        "full_facade_qualified",
        "later_time_behavior_qualified",
        "asymptotic_mesh_convergence_qualified",
    ]
)
checks["accepted_cases_are_r9"] = set(rows) == set(accepted) and all(name.endswith("_R9") for name in accepted)
checks["accepted_manifest_current"] = manifest["file_count"] == len(manifest["files"]) and hashes_match(manifest["files"])

generator = ROOT / "wtc1_simulation_v8/scripts/run_impact_i02e.py"
provenance_ok = True
execution_ok = True
for case in accepted:
    generated = read_json(SIM / case / "generation.json")
    provenance_ok &= generated["generator_sha256"] == sha256(generator)
    provenance_ok &= all(sha256(ROOT / item["path"]) == item["sha256"] for item in generated["config_chain"])
    provenance_ok &= all(sha256(ROOT / path) == digest for path, digest in generated["source_sha256"].items())
    for execution in read_json(SIM / case / "execution.json"):
        executable = Path(execution["command"][0])
        execution_ok &= execution["returncode"] == 0 and executable.is_file() and sha256(executable) == execution["executable_sha256"]
checks["case_generation_provenance"] = provenance_ok
checks["executables_and_exit_codes"] = execution_ok
checks["mass_energy_momentum_all_cases"] = all(
    row["checks"]["initial_mass"]
    and row["checks"]["mass_preserved"]
    and row["checks"]["no_dynamic_mass_scaling"]
    and row["checks"]["global_energy"]
    and row["checks"]["initial_ke"]
    for row in rows.values()
)
checks["contact_momentum_all_contact_cases"] = all(
    row["checks"].get("contact_wing_momentum", True) and row["checks"].get("support_total_momentum", True)
    for row in rows.values()
)
checks["cold_free_flight_controls"] = all(campaign["checks"][key] for key in ["all_free_controls_zero_internal_energy", "shell_mass_identical_between_variants"])
checks["time_mass_mesh_sensitivities"] = all(
    campaign["checks"][key]
    for key in [
        "half_dt_impulse",
        "half_dt_joint_work",
        "numerical_mass_impulse",
        "numerical_mass_joint_work",
        "h127_h0635_impulse",
        "h127_h0635_joint_work",
    ]
)
checks["no_cohesive_or_shell_deletion"] = (
    not comparisons["outcome_within_0_35_ms"]["rupturable_any_deleted_h127"]
    and not comparisons["outcome_within_0_35_ms"]["rupturable_any_deleted_h0635"]
    and all(row["max_wing_eroded_shells"] == 0 for row in rows.values())
)

for label, path in [
    ("I02D", "wtc1_simulation_v8/output/impact_i02d_lap_joint/release_audit.json"),
    ("I02C", "wtc1_simulation_v8/output/impact_i02c_deformable_joint/release_audit.json"),
    ("I02B", "wtc1_simulation_v8/output/impact_i02b_joint_coupon/release_audit.json"),
    ("I02A", "wtc1_simulation_v8/output/impact_i02a_structured_wing/release_audit.json"),
    ("I01", "wtc1_simulation_v8/output/impact_i01_first_contact/release_audit.json"),
]:
    previous = read_json(ROOT / path)
    checks[f"{label}_preserved"] = previous["delivery_status"] == "PASS" and hashes_match(previous["artifact_sha256"])

for name in ["v11f_panel_coupling", "v11r_integrated_panel"]:
    old = read_json(ROOT / "wtc1_simulation_v8/output" / name / "offline_manifest.json")
    retained: list[bool] = []
    for key, value in old.items():
        if "sha256" not in key or not isinstance(value, dict):
            continue
        for path, digest in value.items():
            target = ROOT / "wtc1_simulation_v8/output" / name / path if key == "output_sha256" else ROOT / path
            if name in str(target) or ("v11f_" in str(target) if name.startswith("v11f") else "v11r_" in str(target)):
                retained.append(target.is_file() and sha256(target) == digest)
    checks[f"{name}_preserved"] = bool(retained) and all(retained)
    records[f"{name}_hashes"] = len(retained)

native = read_json(VIEW / "native_export_audit_r10.json")
checks["native_export_pass"] = native["status"] == "PASS" and len(native["cases"]) == 3
native_current = True
native_check_count = 0
for case, case_data in native["cases"].items():
    native_current &= len(case_data["states"]) == 30
    native_current &= sha256(ROOT / case_data["npz"]) == case_data["npz_sha256"]
    native_current &= sha256(ROOT / case_data["pvd"]) == case_data["pvd_sha256"]
    for state in case_data["states"]:
        native_check_count += len(state["checks"])
        native_current &= all(state["checks"].values())
        native_current &= sha256(ROOT / state["source"]) == state["source_sha256"]
        native_current &= sha256(ROOT / state["vtk"]) == state["vtk_sha256"]
checks["native_sources_and_exports_current"] = native_current

presentation = read_json(MEDIA / "presentation_audit_r10.json")
checks["movie_pass"] = presentation["status"] == "PASS" and all(presentation["checks"].values())
checks["movie_and_overview_current"] = (
    sha256(ROOT / presentation["video"]) == presentation["video_sha256"]
    and sha256(ROOT / presentation["overview"]) == presentation["overview_sha256"]
)
checks["movie_frames_current"] = len(presentation["frames"]) == 30 and all(
    sha256(MEDIA / "frames_r10" / f"state_{frame['state']:03d}.png") == frame["sha256"] for frame in presentation["frames"]
)
checks["movie_sources_current"] = all(
    sha256(SIM / case / "native_frames_r10.npz") == digest for case, digest in presentation["source_npz_sha256"].items()
)
for state in [0, 19, 29]:
    with Image.open(MEDIA / "frames_r10" / f"state_{state:03d}.png") as image:
        image.verify()
        checks[f"frame_{state:03d}_readable"] = image.size == (1800, 1000)

artifacts = [
    ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone.json",
    ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r9.json",
    ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r10.json",
    *[
        ROOT / "wtc1_simulation_v8/scripts" / f"{name}_impact_i02e.py"
        for name in ["run", "audit", "summarize", "export", "present", "manifest", "release"]
    ],
    SIM / "comparisons_r10.json",
    SIM / "campaign_audit_r10.json",
    SIM / "source_manifest_r10.json",
    SIM / "rapport_impact_i02e.md",
    ROOT / "harness/handoffs/WTC1_IMPACT_I02E_HANDOFF.md",
    VIEW / "native_export_audit_r10.json",
    MEDIA / "presentation_audit_r10.json",
    MEDIA / "I02E_apercu_comparatif.png",
    MEDIA / "I02E_premier_contact_comparatif.mp4",
]
checks["report_handoff_and_artifacts_exist"] = all(path.is_file() for path in artifacts)

process = subprocess.run(
    [
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        "-NoProfile",
        "-Command",
        "& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6 -Compress",
    ],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=60,
)
(SIM / f"harness_{args.phase}.log").write_text(process.stdout + process.stderr, encoding="utf-8")
harness = json.loads(process.stdout)
checks["harness_pass"] = process.returncode == 0 and harness["Status"] == "PASS"

state = read_json(ROOT / "harness/state.json")
lines = (ROOT / "harness/experiments/registry.jsonl").read_text(encoding="utf-8-sig").splitlines()
registry = [json.loads(line) for line in lines if line.strip()]
count = sum(row.get("experiment_id") == "WTC1-IMPACT-I02E" for row in registry)
prefix = hashlib.sha256("\n".join(lines[:103]).encode()).hexdigest()
if args.phase == "pre_state":
    checks["route_before"] = state["current_iteration"] == "IMPACT-I02D" and state["next_iteration"] == "IMPACT-I02E"
    checks["registry_before"] = len(registry) == 103 and count == 0
else:
    pre = read_json(SIM / "release_audit_pre_state.json")
    checks["pre_audit_pass"] = pre["delivery_status"] == "PASS" and hashes_match(pre["artifact_sha256"])
    checks["registry_old_lines_unchanged"] = prefix == pre["registry_prefix_sha256"]
    checks["route_after"] = state["current_iteration"] == "IMPACT-I02E" and state["next_iteration"] == "IMPACT-I02F"
    checks["registry_after"] = len(registry) == 104 and count == 1
    key = state["impact_i02e_key_results"]
    checks["state_qualification"] = (
        key["accepted_cases"] == 8
        and key["case_boolean_checks"] == 129
        and not key["physical_aircraft_impact_qualified"]
        and not key["metal_tearing_qualified"]
        and not key["full_facade_qualified"]
    )

records.update(
    accepted_cases=len(accepted),
    case_checks=campaign["case_check_count"],
    campaign_checks=len(campaign["checks"]),
    accepted_execution_seconds=campaign["accepted_execution_seconds_total"],
    manifest_files=manifest["file_count"],
    native_state_checks=native_check_count,
)
result = {
    "phase": args.phase,
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "delivery_status": "PASS" if all(checks.values()) else "FAIL",
    "checks": checks,
    "records": records,
    "harness": harness,
    "registry_prefix_sha256": prefix,
    "meaning": (
        "Bounded local first-contact skin-stringer/facade-column comparison only. Shell metal failure is disabled, "
        "local plastic strain is outside a qualified tearing model, and no full aircraft, full facade or historical "
        "penetration conclusion is validated."
    ),
    "artifact_sha256": {relative(path): sha256(path) for path in artifacts},
}
target = SIM / ("release_audit.json" if args.phase == "post_state" else "release_audit_pre_state.json")
target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(
    json.dumps(
        {
            "status": result["delivery_status"],
            "checks": len(checks),
            "failed": [key for key, value in checks.items() if not value],
            "records": records,
            "harness": harness,
        },
        indent=2,
    )
)
sys.exit(0 if all(checks.values()) else 1)
