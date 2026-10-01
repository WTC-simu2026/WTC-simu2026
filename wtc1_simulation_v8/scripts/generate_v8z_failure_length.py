#!/usr/bin/env python3
"""Generate V8Z decks for a predeclared numerical LeMAX sensitivity."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from generate_v8w_pairwise_contact import write_engine as write_v8w_engine
from generate_v8w_pairwise_contact import write_starter as write_v8w_starter
from generate_v8y_nonlocal_failure import insert_regularized_failure


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def replace_iteration(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("V8W_", "V8Z_").replace("# V8W ", "# V8Z "),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    args = parse_args()
    study = json.loads(args.config.read_text(encoding="utf-8"))
    project_root = args.config.resolve().parents[2]
    base_path = project_root / study["base_configuration"]["path"]
    base = json.loads(base_path.read_text(encoding="utf-8"))
    case = next((item for item in study["cases"] if item["id"] == args.case_id), None)
    if case is None:
        raise SystemExit(f"Unknown case: {args.case_id}")
    if case["erosion_mode"] != "johnson_nonlocal":
        raise SystemExit(f"Unknown erosion mode: {case['erosion_mode']}")

    effective_config = copy.deepcopy(base)
    effective_case = copy.deepcopy(case)
    effective_config["execution"]["facade_impact_termination_time_ms"] = study[
        "execution_policy"
    ]["facade_impact_termination_time_ms"]
    effective_config["facade_material"]["failure_plastic_strain"] = 0.0
    effective_case["core_failure_strain"] = 0.0
    effective_case["cowling_failure_strain"] = 0.0

    rlen_mm = float(study["regularization_sensitivity"]["rlen_input_mm"])
    lemax_mm = float(case["lemax_mm"])
    args.output.mkdir(parents=True, exist_ok=True)
    run_name = f"V8Z_{case['id']}"
    starter_path = args.output / f"{run_name}_0000.rad"
    engine_path = args.output / f"{run_name}_0001.rad"
    metadata = write_v8w_starter(effective_config, effective_case, starter_path)
    write_v8w_engine(effective_config, effective_case, engine_path)
    replace_iteration(starter_path)
    replace_iteration(engine_path)
    insert_regularized_failure(starter_path, case, rlen_mm, lemax_mm)

    metadata["run_name"] = run_name
    metadata["erosion_mode"] = case["erosion_mode"]
    metadata["study_role"] = case["role"]
    metadata["law2_builtin_epsmax"] = {"facade": 0.0, "core": 0.0, "cowling": 0.0}
    metadata["johnson_constant_failure_strains"] = {
        "facade": float(case["facade_failure_strain"]),
        "core": float(case["core_failure_strain"]),
        "cowling": float(case["cowling_failure_strain"]),
    }
    metadata["nonlocal_regularization"] = {
        "rlen_input_mm": rlen_mm,
        "lemax_mm": lemax_mm,
        "status": "predeclared numerical sensitivity; not a measured material length",
    }
    metadata["base_configuration"] = study["base_configuration"]
    (args.output / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(metadata, separators=(",", ":")))


if __name__ == "__main__":
    main()
