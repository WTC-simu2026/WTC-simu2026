"""Reopen and independently verify the IMPACT-I02A Blender transfer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "wtc1_simulation_v8/output/impact_i02a_structured_wing/CONTACT_M050_R1/computed_frames.npz"
)
OUTPUT = ROOT / "wtc1_3d_v4/output/impact_i02a"
BLEND_PATH = OUTPUT / "IMPACT_I02A_SOLVER_STATES.blend"
FRAME_DIR = ROOT / "wtc1_3d_v4/renders/impact_i02a/frames"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    data = np.load(SOURCE)
    expected = data["points_mm"][:, :, [0, 2, 1]] / 1000.0
    expected_quads = data["quads"].astype(np.int32)
    expected_parts = data["parts"].astype(np.int32)

    obj = bpy.data.objects.get("I02A_OPENRADIOSS_SHELL_STATES")
    if obj is None:
        raise RuntimeError("Solver-state mesh is absent from reopened .blend")
    mesh = obj.data
    keys = obj.data.shape_keys.key_blocks
    position_errors = []
    for state_index, key in enumerate(keys):
        coordinates = np.empty(len(key.data) * 3, dtype=np.float32)
        key.data.foreach_get("co", coordinates)
        error = float(
            np.max(np.abs(coordinates.reshape((-1, 3)) - expected[state_index]))
        )
        position_errors.append(error)

    actual_quads = np.empty((len(mesh.polygons), 4), dtype=np.int32)
    for index, polygon in enumerate(mesh.polygons):
        actual_quads[index] = polygon.vertices[:]
    topology_identical = bool(np.array_equal(actual_quads, expected_quads))

    part_attr = mesh.attributes.get("solver_part_id")
    actual_parts = np.empty(len(part_attr.data), dtype=np.int32)
    part_attr.data.foreach_get("value", actual_parts)
    parts_identical = bool(np.array_equal(actual_parts, expected_parts))

    constant_interpolation = True
    action = obj.data.shape_keys.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        for keyframe in curve.keyframe_points:
                            constant_interpolation &= keyframe.interpolation == "CONSTANT"

    rigid_objects = [item.name for item in bpy.data.objects if item.rigid_body]
    source_hash = sha256(SOURCE)
    state_frames = sorted(FRAME_DIR.glob("state_*.png"))
    checks = {
        "source_hash_matches_blend": obj.get("source_sha256") == source_hash,
        "shape_keys_match_25_states": len(keys) == expected.shape[0] == 25,
        "max_coordinate_error_below_1e_6_m": max(position_errors) < 1.0e-6,
        "shell_topology_identical": topology_identical,
        "part_ids_identical": parts_identical,
        "constant_interpolation_only": bool(constant_interpolation),
        "no_blender_rigid_bodies": len(rigid_objects) == 0,
        "no_blender_physics_flag": obj.get("blender_physics") is False,
        "fracture_and_erosion_disabled_flag": obj.get("erosion_or_fracture") is False,
        "twenty_five_lossless_state_frames": len(state_frames) == 25,
        "lossless_state_frames_nonempty": all(path.stat().st_size > 10000 for path in state_frames),
        "warning_metadata_present": "Rupture disabled" in bpy.context.scene.get(
            "permanent_warning", ""
        ),
    }
    audit = {
        "iteration": "IMPACT-I02A",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "blend_sha256": sha256(BLEND_PATH),
        "source_npz_sha256": source_hash,
        "solver_states": int(expected.shape[0]),
        "vertices_per_state": int(expected.shape[1]),
        "shell_faces": int(expected_quads.shape[0]),
        "max_coordinate_error_m": max(position_errors),
        "coordinate_error_m_by_state": position_errors,
        "lossless_state_frame_sha256": {path.name: sha256(path) for path in state_frames},
        "blender_physics": False,
        "scope": obj.get("scope"),
    }
    (OUTPUT / "blender_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))
    if audit["status"] != "PASS":
        raise RuntimeError("IMPACT-I02A Blender audit failed")


if __name__ == "__main__":
    main()
