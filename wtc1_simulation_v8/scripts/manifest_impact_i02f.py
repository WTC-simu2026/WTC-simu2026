"""Hash the preserved IMPACT-I02F inputs, scripts and outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"
TARGET = OUT / "artifact_manifest_r1.json"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    if TARGET.exists():
        raise RuntimeError("Existing I02F manifest preserved: " + str(TARGET))
    files = [
        ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json",
        ROOT / "harness/handoffs/WTC1_IMPACT_I02F_HANDOFF.md",
        *[ROOT / "wtc1_simulation_v8/input/impact_i02f_sources" / name for name in [
            "NASA_CR_191523_2024T3_CTOA.pdf",
            "NASA_19990028733_wide_stiffened_panels.pdf",
            "NASA_19730023698_7075T6_fracture.pdf",
            "NASA_19740003601_2024T3_1p02mm_fracture.pdf",
        ]],
        *[ROOT / "wtc1_simulation_v8/scripts" / name for name in [
            "run_impact_i02f.py",
            "audit_impact_i02f.py",
            "audit_impact_i02f_r4.py",
            "audit_impact_i02f_r5.py",
            "run_impact_i02f_zone.py",
            "audit_impact_i02f_zone.py",
            "summarize_impact_i02f.py",
            "manifest_impact_i02f.py",
            "release_impact_i02f.py",
        ]],
    ]
    files.extend(
        path for path in OUT.rglob("*")
        if path.is_file()
        and path.name not in {"artifact_manifest_r1.json", "release_audit_pre_state.json", "release_audit.json"}
        and not path.name.startswith("harness_")
    )
    unique = sorted(set(files), key=rel)
    if not all(path.is_file() for path in unique):
        missing = [rel(path) for path in unique if not path.is_file()]
        raise RuntimeError("Missing manifest inputs: " + ", ".join(missing))
    manifest = {
        "iteration": "IMPACT-I02F",
        "file_count": len(unique),
        "files": {rel(path): sha(path) for path in unique},
        "accepted_solver_revision": "R3",
        "accepted_audit_policy_revision": "R5",
        "sources_read_only": True,
        "rejected_development_outputs_preserved": True,
    }
    TARGET.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "files": len(unique), "manifest": rel(TARGET)}))


if __name__ == "__main__":
    main()
