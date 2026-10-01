"""Read-only internal audit of the saved V9O Blender derivative."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import bpy


WORKSPACE = Path(__file__).resolve().parents[2]
CONFIG_PATH = WORKSPACE / "wtc1_simulation_v8/data/v9o_blender_storyboard_preview.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def action_fcurves(action: bpy.types.Action) -> Iterable[bpy.types.FCurve]:
    if hasattr(action, "fcurves"):
        yield from action.fcurves
        return
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                yield from channelbag.fcurves


def location_keyframe_frames(obj: bpy.types.Object) -> list[int]:
    if obj.animation_data is None or obj.animation_data.action is None:
        return []
    frames: set[int] = set()
    for fcurve in action_fcurves(obj.animation_data.action):
        if fcurve.data_path != "location":
            continue
        for point in fcurve.keyframe_points:
            frames.add(int(round(point.co[0])))
    return sorted(frames)


def location_at(scene: bpy.types.Scene, obj: bpy.types.Object, frame: int) -> list[float]:
    scene.frame_set(frame)
    return [float(value) for value in obj.location]


def close_vector(left: list[float], right: list[float], tolerance: float = 1e-6) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(left, right))


def main() -> None:
    config = load_json(CONFIG_PATH)
    output_path = WORKSPACE / config["output"]["blender_internal_audit"]
    master_path = WORKSPACE / config["master_policy"]["master_blend"]
    derivative_path = WORKSPACE / config["master_policy"]["derivative_blend"]
    current_file = Path(bpy.data.filepath).resolve()
    if current_file != derivative_path.resolve():
        raise RuntimeError(f"Expected the V9O derivative, opened {current_file}")

    story_name = config["master_policy"]["new_storyboard_scene"]
    card_name = config["master_policy"]["new_card_scene"]
    proof_name = config["master_policy"]["new_proof_scene"]
    required_scenes = [story_name, card_name, proof_name]
    missing_scenes = [name for name in required_scenes if bpy.data.scenes.get(name) is None]
    if missing_scenes:
        raise RuntimeError(f"Missing V9O scenes: {missing_scenes}")
    scene = bpy.data.scenes[story_name]

    branch_records: dict[str, Any] = {}
    for branch_id, keyframes in config["animation_keyframes"].items():
        root_name = f"V9O_AA11_{branch_id.upper()}_ROOT"
        root = bpy.data.objects.get(root_name)
        if root is None:
            raise RuntimeError(f"Missing branch parent {root_name}")
        expected_frames = [
            int(round(float(item["presentation_time_s"]) * int(config["blender"]["frame_rate_fps"]))) + 1
            for item in keyframes
        ]
        actual_frames = location_keyframe_frames(root)
        contact_frame = next(
            expected_frames[index]
            for index, item in enumerate(keyframes)
            if float(item["event_time_s"]) == 0.0
        )
        sample_frames = sorted({contact_frame, (contact_frame + scene.frame_end) // 2, scene.frame_end})
        sampled_locations = {str(frame): location_at(scene, root, frame) for frame in sample_frames}
        contact_location = sampled_locations[str(contact_frame)]
        freeze_verified = all(close_vector(contact_location, location) for location in sampled_locations.values())
        branch_records[branch_id] = {
            "parent": root_name,
            "expected_location_keyframe_frames": expected_frames,
            "actual_location_keyframe_frames": actual_frames,
            "keyframe_frames_match": actual_frames == expected_frames,
            "contact_frame": contact_frame,
            "sampled_postcontact_locations_m": sampled_locations,
            "postcontact_freeze_verified": freeze_verified,
        }

    rigid_body_objects = [obj.name for obj in bpy.data.objects if obj.rigid_body is not None]
    particle_objects = [obj.name for obj in bpy.data.objects if len(obj.particle_systems) > 0]
    fluid_modifiers = [
        {"object": obj.name, "modifier": modifier.name, "type": modifier.type}
        for obj in bpy.data.objects
        for modifier in obj.modifiers
        if "FLUID" in modifier.type
    ]
    rigidbody_scenes = [scene_item.name for scene_item in bpy.data.scenes if scene_item.rigidbody_world is not None]
    cameras = sorted(
        obj.name for obj in scene.objects if obj.type == "CAMERA" and obj.name.startswith("CAM_V9O_")
    )
    markers = sorted(
        ({"name": marker.name, "frame": int(marker.frame)} for marker in scene.timeline_markers),
        key=lambda item: item["frame"],
    )
    silhouette_children = sorted(
        obj.name for obj in scene.objects if obj.name.startswith("V9O_") and obj.get("physics_enabled") is False
    )

    audit = {
        "iteration": "V9O",
        "status": "PASS" if all(record["postcontact_freeze_verified"] for record in branch_records.values()) else "FAIL",
        "read_only_audit": True,
        "opened_file": str(current_file.relative_to(WORKSPACE)).replace("\\", "/"),
        "opened_file_sha256": sha256(current_file),
        "master": {
            "path": str(master_path.relative_to(WORKSPACE)).replace("\\", "/"),
            "expected_sha256": config["master_policy"]["master_expected_sha256"],
            "actual_sha256": sha256(master_path),
            "unchanged": sha256(master_path) == config["master_policy"]["master_expected_sha256"],
        },
        "blender": {
            "version": bpy.app.version_string,
            "version_tuple": list(bpy.app.version),
        },
        "scenes": {
            "required": required_scenes,
            "present": [name for name in required_scenes if bpy.data.scenes.get(name) is not None],
            "storyboard_flags": {
                "iteration": scene.get("iteration"),
                "visualization_only": scene.get("visualization_only"),
                "physical_validation": scene.get("physical_validation"),
                "postcontact_motion_authorized": scene.get("postcontact_motion_authorized"),
                "permanent_banner": scene.get("permanent_banner"),
                "source_storyboard": scene.get("source_storyboard"),
            },
            "frame_start": int(scene.frame_start),
            "frame_end": int(scene.frame_end),
            "fps": int(scene.render.fps),
        },
        "timeline_markers": markers,
        "cameras": cameras,
        "branches": branch_records,
        "silhouette_object_count": len(silhouette_children),
        "physics": {
            "rigid_body_object_count": len(rigid_body_objects),
            "rigid_body_objects": rigid_body_objects,
            "particle_system_object_count": len(particle_objects),
            "particle_system_objects": particle_objects,
            "fluid_modifier_count": len(fluid_modifiers),
            "fluid_modifiers": fluid_modifiers,
            "rigidbody_world_scene_count": len(rigidbody_scenes),
            "rigidbody_world_scenes": rigidbody_scenes,
            "structural_solver_executed": False,
            "blender_physics_executed": False,
            "physical_validation": False,
        },
        "scope": {
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "network_access_used": False,
            "external_contact_made": False,
            "foia_request_sent": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(audit, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("V9O_INTERNAL_AUDIT=" + json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
