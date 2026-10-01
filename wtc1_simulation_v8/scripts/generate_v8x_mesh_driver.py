#!/usr/bin/env python3
"""Generate V8X cross-mesh and non-eroding diagnostic decks."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from generate_v8w_pairwise_contact import write_engine as write_v8w_engine
from generate_v8w_pairwise_contact import write_starter as write_v8w_starter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def replace_iteration(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("V8W_", "V8X_").replace("# V8W ", "# V8X "),
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

    effective_config = copy.deepcopy(base)
    effective_case = copy.deepcopy(case)
    effective_config["execution"]["facade_impact_termination_time_ms"] = study[
        "execution_policy"
    ]["facade_impact_termination_time_ms"]
    if case["erosion_mode"] == "law2_default_non_eroding":
        effective_config["facade_material"]["failure_plastic_strain"] = 0.0
        effective_case["core_failure_strain"] = 0.0
        effective_case["cowling_failure_strain"] = 0.0
    elif case["erosion_mode"] != "v8w_enabled":
        raise SystemExit(f"Unknown erosion mode: {case['erosion_mode']}")

    args.output.mkdir(parents=True, exist_ok=True)
    v8w_run_name = f"V8W_{case['id']}"
    v8x_run_name = f"V8X_{case['id']}"
    starter_path = args.output / f"{v8x_run_name}_0000.rad"
    engine_path = args.output / f"{v8x_run_name}_0001.rad"
    metadata = write_v8w_starter(effective_config, effective_case, starter_path)
    write_v8w_engine(effective_config, effective_case, engine_path)
    replace_iteration(starter_path)
    replace_iteration(engine_path)
    metadata["run_name"] = v8x_run_name
    metadata["erosion_mode"] = case["erosion_mode"]
    metadata["study_role"] = case["role"]
    metadata["effective_failure_plastic_strains"] = {
        "facade": float(effective_config["facade_material"]["failure_plastic_strain"]),
        "core": float(effective_case["core_failure_strain"]),
        "cowling": float(effective_case["cowling_failure_strain"]),
    }
    metadata["non_eroding_default_interpretation"] = (
        "LAW2 EPSmax=0 invokes the documented default 1e20 failure plastic strain"
        if case["erosion_mode"] == "law2_default_non_eroding"
        else None
    )
    metadata["base_configuration"] = study["base_configuration"]
    (args.output / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(metadata, separators=(",", ":")))


if __name__ == "__main__":
    main()
