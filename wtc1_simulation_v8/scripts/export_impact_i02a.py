"""Export saved IMPACT-I02A Radioss animation states to verified NPZ arrays."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02a_structured_wing.json"
CONVERTER = ROOT / "wtc1_simulation_v8/openradioss_runtime/v20260728-win64/anim_to_vtk_win64.exe"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_vtk(text: str) -> dict:
    arrays = {}
    lines = text.splitlines()
    index = 0
    data_count = 0
    while index < len(lines):
        words = lines[index].split()
        index += 1
        if not words:
            continue
        if words[0] == "TIME":
            while not lines[index].strip():
                index += 1
            arrays["time"] = float(lines[index])
            index += 1
        elif words[0] in ("POINT_DATA", "CELL_DATA"):
            data_count = int(words[1])
        elif words[0] in ("POINTS", "CELLS", "SCALARS", "VECTORS", "CELL_TYPES"):
            kind = words[0]
            if kind == "POINTS":
                key, count = "points", int(words[1]) * 3
            elif kind == "CELLS":
                key, count = "cells", int(words[2])
            elif kind == "CELL_TYPES":
                key, count = "types", int(words[1])
            elif kind == "SCALARS":
                key = words[1]
                count = data_count * (int(words[3]) if len(words) > 3 else 1)
                while not lines[index].strip():
                    index += 1
                if not lines[index].startswith("LOOKUP_TABLE"):
                    raise RuntimeError("Missing VTK lookup table")
                index += 1
            else:
                key, count = words[1], data_count * 3
            first = index
            value_count = 0
            while value_count < count:
                value_count += len(lines[index].split())
                index += 1
            values = np.fromstring(" ".join(lines[first:index]), sep=" ")
            if len(values) != count:
                raise RuntimeError(f"VTK count mismatch for {key}: {len(values)} != {count}")
            arrays[key] = values
    return arrays


def main() -> None:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    output_root = ROOT / cfg["output_root"]
    audit = {}
    start = time.perf_counter()
    for case in cfg["cases"]:
        directory = output_root / case["id"]
        animations = sorted(path for path in directory.glob("I02A_*A*") if re.fullmatch(r".*A\d{3}", path.name))
        if not case["id"].startswith("CONTACT_M050"):
            animations = [animations[0], animations[-1]]
        original = json.loads((directory / "mesh.json").read_text(encoding="utf-8"))
        points_by_state = []
        epsp_by_state = []
        times = []
        references = []
        states = []
        node_ids_reference = None
        quads_reference = None
        parts_reference = None
        for animation in animations:
            result = subprocess.run([str(CONVERTER), str(animation)], capture_output=True, text=True, encoding="utf-8", errors="strict")
            if result.returncode:
                raise RuntimeError(f"Animation conversion failed for {animation.name}")
            arrays = parse_vtk(result.stdout)
            node_ids = arrays["NODE_ID"].astype(int)
            points = arrays["points"].reshape(-1, 3)
            cells = arrays["cells"].astype(int).reshape(-1, 5)
            if not np.all(cells[:, 0] == 4):
                raise RuntimeError("Unexpected non-quad animation cell")
            quads = cells[:, 1:]
            parts = arrays["PART_ID"].astype(int)
            element_ids = arrays["ELEMENT_ID"].astype(int)
            if node_ids_reference is None:
                node_ids_reference, quads_reference, parts_reference = node_ids, quads, parts
            if not np.array_equal(node_ids, node_ids_reference) or not np.array_equal(quads, quads_reference) or not np.array_equal(parts, parts_reference):
                raise RuntimeError("Animation topology changed between states")
            initial = np.asarray(original["nodes_mm"])[node_ids - 1]
            displacement = arrays["Displacement"].reshape(-1, 3)
            identity_error = float(np.max(np.abs(points - initial - displacement)))
            if identity_error >= 0.05:
                raise RuntimeError(f"Coordinate/displacement identity failed: {identity_error}")
            for element_index, element_id in enumerate(element_ids):
                if set(node_ids[quads[element_index]]) != set(np.asarray(original["quads"][element_id - 1]) + 1):
                    raise RuntimeError("Element connectivity mismatch")
                if parts[element_index] != original["parts"][element_id - 1]:
                    raise RuntimeError("Part mapping mismatch")
            plastic_layers = [values for key, values in arrays.items() if "Plast" in key]
            epsp = np.maximum.reduce(plastic_layers)
            points_by_state.append(points.astype("float32"))
            epsp_by_state.append(epsp.astype("float32"))
            times.append(arrays["time"])
            references.append({"file": str(animation.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(animation)})
            states.append(
                {
                    "time_ms": arrays["time"],
                    "max_epsp_by_part": {str(part_id): float(epsp[parts == part_id].max()) for part_id in range(1, 8)},
                    "displacement_identity_error_mm": identity_error,
                    "min_erosion_status": float(arrays["EROSION_STATUS"].min()),
                    "max_erosion_status": float(arrays["EROSION_STATUS"].max()),
                }
            )
        npz = directory / "computed_frames.npz"
        np.savez_compressed(
            npz,
            points_mm=np.asarray(points_by_state),
            epsp=np.asarray(epsp_by_state),
            times_ms=np.asarray(times),
            quads=quads_reference,
            parts=parts_reference,
            node_ids=node_ids_reference,
        )
        audit[case["id"]] = {
            "converted_frames": len(animations),
            "states": states,
            "animation_sources": references,
            "output": str(npz.relative_to(ROOT)).replace("\\", "/"),
            "output_sha256": sha256(npz),
        }
    result = {
        "seconds": time.perf_counter() - start,
        "converter": str(CONVERTER.relative_to(ROOT)).replace("\\", "/"),
        "converter_sha256": sha256(CONVERTER),
        "position_quantization_tolerance_mm": 0.05,
        "cases": audit,
        "physical_validation": False,
    }
    write_json(output_root / "animation_export_audit.json", result)
    print(json.dumps({key: [value["converted_frames"], value["states"][-1]["max_epsp_by_part"]] for key, value in audit.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
