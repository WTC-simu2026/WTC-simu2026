"""Freeze the accepted I02E solver, export, presentation and source artifacts."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


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


campaign = read_json(SIM / "campaign_audit_r10.json")
if campaign["status"] != "PASS":
    raise RuntimeError("The R10 campaign audit is not PASS")

accepted_cases = campaign["accepted_cases"]
paths: list[Path] = [
    ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone.json",
    ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r9.json",
    ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r10.json",
    ROOT / "wtc1_simulation_v8/scripts/run_impact_i02e.py",
    ROOT / "wtc1_simulation_v8/scripts/audit_impact_i02e.py",
    ROOT / "wtc1_simulation_v8/scripts/summarize_impact_i02e.py",
    ROOT / "wtc1_simulation_v8/scripts/export_impact_i02e.py",
    ROOT / "wtc1_simulation_v8/scripts/present_impact_i02e.py",
    ROOT / "wtc1_simulation_v8/scripts/manifest_impact_i02e.py",
    ROOT / "wtc1_simulation_v8/scripts/release_impact_i02e.py",
    ROOT / "harness/handoffs/WTC1_IMPACT_I02E_HANDOFF.md",
    SIM / "comparisons_r10.json",
    SIM / "campaign_audit_r10.json",
    SIM / "rapport_impact_i02e.md",
    VIEW / "native_export_audit_r10.json",
    MEDIA / "presentation_audit_r10.json",
    MEDIA / "I02E_apercu_comparatif.png",
    MEDIA / "I02E_premier_contact_comparatif.mp4",
    MEDIA / "encoding_r10.log",
]

for case in accepted_cases:
    paths.extend(path for path in (SIM / case).rglob("*") if path.is_file())

for case in ["CONTACT_MERGED_H127_R9", "CONTACT_UNBREAKABLE_H127_R9", "CONTACT_RUPTURABLE_H127_R9"]:
    paths.extend(path for path in (VIEW / case).rglob("*") if path.is_file())

paths.extend(path for path in (MEDIA / "frames_r10").glob("*.png") if path.is_file())

reference_paths = [
    ROOT / "wtc1_simulation_v8/data/impact_i02a_structured_wing.json",
    ROOT / "wtc1_simulation_v8/output/impact_i02a_structured_wing/release_audit.json",
    ROOT / "wtc1_simulation_v8/data/impact_i02d_lap_joint.json",
    ROOT / "wtc1_simulation_v8/output/impact_i02d_lap_joint/release_audit.json",
    ROOT / "work/official_sources/ncstar1-2bv1.pdf",
]
paths.extend(reference_paths)

unique_paths = sorted(set(paths), key=lambda path: relative(path))
missing = [str(path) for path in unique_paths if not path.is_file()]
if missing:
    raise RuntimeError(f"Missing accepted artifacts: {missing}")

files = {relative(path): sha256(path) for path in unique_paths}
case_file_counts = {
    case: sum(1 for path in (SIM / case).rglob("*") if path.is_file())
    for case in accepted_cases
}
result = {
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "iteration": "IMPACT-I02E",
    "accepted_solver_revision": "R9",
    "audit_policy_revision": "R10",
    "accepted_cases": accepted_cases,
    "accepted_case_file_counts": case_file_counts,
    "file_count": len(files),
    "files": files,
    "remote_primary_documentation": [
        "https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm",
        "https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm",
        "https://help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r_2.htm",
        "https://2023.help.altair.com/2023/hwsolvers/rad/topics/solvers/rad/admas_starter_r.htm",
    ],
    "retained_but_not_promoted_preflights": campaign["retained_preflights"],
    "scope": (
        "Accepted R9 decks, execution logs, histories, native states, audits, direct VTK exports, "
        "the no-amplification comparison movie, configurations, scripts and pinned local references. "
        "Rejected preflight folders are retained on disk and listed by the campaign audit, but excluded "
        "from the accepted artifact hash set."
    ),
}

target = SIM / "source_manifest_r10.json"
target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "files": len(files), "cases": len(accepted_cases), "manifest": relative(target)}))
