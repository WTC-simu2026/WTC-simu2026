"""Add immutable I02H controls. Existing solver results and source files are read-only."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path

import run_impact_i02h as base
import audit_impact_i02h as audit

ROOT = base.ROOT
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02h_completion_r1.json"
OUT = base.OUTPUT


def snapshot():
    target = OUT / "preservation_before_finalization.json"
    if target.exists():
        raise RuntimeError("Snapshot exists; preserve it")
    files = [p for p in OUT.rglob("*") if p.is_file()]
    # Targeted prior artifacts, no archive scan and no historical rerun.
    state = json.loads((ROOT / "harness/state.json").read_text(encoding="utf-8-sig"))
    for value in state["validated_artifacts"].values():
        if isinstance(value, str) and any(s in value for s in ("impact_i02g", "v11f_panel_coupling", "v11r_integrated_panel", "WTC1_V11F_HANDOFF", "WTC1_V11R_HANDOFF")):
            path = ROOT / value
            if path.is_file():
                files.append(path)
    files += [base.CFG, Path(base.__file__), Path(audit.__file__), ROOT / "wtc1_simulation_v8/scripts/run_impact_i02g.py", ROOT / "wtc1_simulation_v8/scripts/audit_impact_i02g.py"]
    base.dump(target, {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "scope": "All existing I02H files; targeted prior I02G, V11F and V11R validated-artifact references; original generators and auditors.", "files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": base.sha(p)} for p in sorted(set(files))]})
    print(json.dumps({"preservation_snapshot": str(target), "files": len(set(files))}), flush=True)


def run(case_id):
    settings = json.loads(CFG.read_text(encoding="utf-8"))
    original = ROOT / settings["base_configuration"]
    if base.sha(original) != settings["base_configuration_sha256"] or base.sha(Path(base.__file__)) != settings["base_generator_sha256"]:
        raise RuntimeError("Original I02H input changed")
    cfg = copy.deepcopy(json.loads(original.read_text(encoding="utf-8")))
    case = next(c for c in settings["cases"] if c["id"] == case_id)
    cfg["execution"].update(threads=settings["threads"], maximum_case_wall_seconds=settings["maximum_case_wall_seconds"])
    cfg["cases"] = [case]
    cfg["completion_provenance"] = {"configuration": CFG.relative_to(ROOT).as_posix(), "sha256": base.sha(CFG), "driver_sha256": base.sha(Path(__file__)), "random_seed": None}
    directory = OUT / case_id
    if directory.exists():
        raise RuntimeError("Existing case preserved: " + str(directory))
    directory.mkdir()
    base.CFG = directory / "effective_configuration.json"
    base.dump(base.CFG, cfg)
    metadata = base.generate(cfg, case, directory)
    environment = os.environ.copy()
    environment.update(RAD_CFG_PATH="C:/OpenRadioss/hm_cfg_files", RAD_H3D_PATH="C:/OpenRadioss/extlib/h3d/lib/win64", OPENRADIOSS_PATH="C:/OpenRadioss", OMP_NUM_THREADS="1", KMP_STACKSIZE="400m")
    records = []
    try:
        for executable, arguments, log in [
            ("starter_win64.exe", ["-i", metadata["name"] + "_0000.rad", "-np", "1"], "starter.log"),
            ("engine_win64.exe", ["-i", metadata["name"] + "_0001.rad"], "engine.log"),
            ("th_to_csv_win64.exe", [metadata["name"] + "T01"], "converter.log"),
        ]:
            records.append(base.execute(base.RUNTIME / executable, arguments, directory, environment, log, settings["maximum_case_wall_seconds"]))
            base.dump(directory / "execution.json", records)
    except Exception as error:
        base.dump(directory / "failure.json", {"exception": repr(error), "completed_jobs": records, "qualification": "diagnostic only"})
        raise
    result = audit.audit_case(directory, cfg)
    print(json.dumps({"case": case_id, "checks": result["gates"], "seconds": result["execution_seconds_recorded"], "peak_MPa": result["peak_remote_stress_mpa"], "final_extension_mm": result["final_state"]["mean_extension_mm"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--case")
    args = parser.parse_args()
    if args.snapshot:
        snapshot()
    if args.case:
        run(args.case)
