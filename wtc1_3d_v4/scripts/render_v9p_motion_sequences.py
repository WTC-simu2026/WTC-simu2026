"""Render the bounded V9P pre-contact motion sequences from the V9O derivative.

The opened V9O blend file is never saved. Blender physics and structural solvers
remain disabled. Four sequences stop before first contact; the contact interval is
represented later by a validated frozen still.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from pathlib import Path
from typing import Any

import bpy


WORKSPACE = Path(__file__).resolve().parents[2]
CONFIG_PATH = WORKSPACE / "wtc1_simulation_v8/data/v9p_low_resolution_animatic.json"
V9O_CONFIG_PATH = WORKSPACE / "wtc1_simulation_v8/data/v9o_blender_storyboard_preview.json"
V9O_BUILDER_PATH = WORKSPACE / "wtc1_3d_v4/scripts/build_v9o_storyboard_preview.py"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_v9o_builder() -> Any:
    spec = importlib.util.spec_from_file_location("v9o_builder_helpers", V9O_BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load V9O builder helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def aggregate_frame_identity(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        relative = str(path.relative_to(WORKSPACE)).replace("\\", "/")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> None:
    started = time.perf_counter()
    config = load_json(CONFIG_PATH)
    v9o_config = load_json(V9O_CONFIG_PATH)
    helpers = load_v9o_builder()
    derivative_path = WORKSPACE / config["blender"]["source_derivative"]
    master_path = WORKSPACE / config["blender"]["source_master"]
    manifest_path = WORKSPACE / config["output"]["motion_render_manifest"]
    closing_card_path = WORKSPACE / config["output"]["closing_card"]
    opened_path = Path(bpy.data.filepath).resolve()
    if opened_path != derivative_path.resolve():
        raise RuntimeError(f"Expected V9O derivative, opened {opened_path}")
    derivative_hash_before = sha256(derivative_path)
    master_hash_before = sha256(master_path)
    if derivative_hash_before != config["blender"]["source_derivative_expected_sha256"]:
        raise RuntimeError("V9O derivative hash does not match the predeclared V9P input")
    if master_hash_before != config["blender"]["source_master_expected_sha256"]:
        raise RuntimeError("V4.2 master hash does not match the predeclared V9P input")

    scene = bpy.data.scenes.get(config["blender"]["storyboard_scene"])
    card_scene = bpy.data.scenes.get(config["blender"]["card_scene"])
    if scene is None or card_scene is None:
        raise RuntimeError("Validated V9O storyboard/card scene is missing")
    overlay_collection = bpy.data.collections.get("V9O_ACTIVE_OVERLAY")
    card_collection = bpy.data.collections.get("V9O_CARD_CONTENT")
    if overlay_collection is None or card_collection is None:
        raise RuntimeError("Validated V9O overlay/card collection is missing")

    panel_material = bpy.data.materials.get("V9O_OVERLAY_PANEL")
    if panel_material is None:
        panel_material = helpers.make_material(
            "V9P_OVERLAY_PANEL",
            (0.015, 0.024, 0.04, 1.0),
            emission_strength=0.75,
        )
    materials = {
        "panel": panel_material,
        "warning": bpy.data.materials["V9O_WARNING_ORANGE"],
        "white": bpy.data.materials["V9O_TEXT_WHITE"],
        "muted": bpy.data.materials["V9O_TEXT_MUTED"],
        "cyan": bpy.data.materials["V9O_TEXT_CYAN"],
        "dark": bpy.data.materials["V9O_TEXT_DARK"],
        "card_bg": bpy.data.materials["V9O_CARD_BACKGROUND_MAT"],
    }
    branches: dict[str, list[bpy.types.Object]] = {}
    branch_roots: dict[str, bpy.types.Object] = {}
    for branch_id in ("less_severe", "base", "more_severe"):
        root = bpy.data.objects.get(f"V9O_AA11_{branch_id.upper()}_ROOT")
        if root is None:
            raise RuntimeError(f"Missing V9O branch root {branch_id}")
        branch_roots[branch_id] = root
        branches[branch_id] = [root, *list(root.children_recursive)]
    cameras = {
        name: bpy.data.objects[name]
        for name in ("CAM_V9O_NORTH", "CAM_V9O_OBLIQUE", "CAM_V9O_SIDE")
    }
    v9o_shots = {shot["shot_id"]: shot for shot in v9o_config["shot_renders"]}
    source_fps = int(config["blender"]["source_timeline_fps"])
    frame_step = int(config["blender"]["motion_frame_step"])
    resolution = config["blender"]["resolution_px"]
    scene.render.resolution_x = int(resolution[0])
    scene.render.resolution_y = int(resolution[1])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    render_records: list[dict[str, Any]] = []
    comparison_offsets = {"less_severe": -29.0, "base": 0.0, "more_severe": 29.0}
    for shot in config["shots"]:
        if shot["source_type"] != "motion_sequence":
            continue
        source_shot = v9o_shots[shot["id"]]
        if source_shot["branch_mode"] == "all_comparison_offset":
            visible = ["less_severe", "base", "more_severe"]
            for branch_id, root in branch_roots.items():
                root.delta_location.x = comparison_offsets[branch_id]
        elif source_shot["branch_mode"] == "single":
            visible = [source_shot["branch_id"]]
            for root in branch_roots.values():
                root.delta_location.x = 0.0
        else:
            raise RuntimeError(f"Unexpected V9P motion branch mode: {source_shot['branch_mode']}")
        helpers.set_branch_visibility(branches, visible)
        camera = cameras[source_shot["camera_id"]]
        helpers.create_camera_overlay(
            scene,
            overlay_collection,
            camera,
            shot["motion_title"],
            shot["motion_subtitle"],
            shot["motion_epistemic_label"],
            config["permanent_text"],
            materials,
            contact_stop=False,
        )
        banner = bpy.data.objects.get("V9O_OVERLAY_BANNER")
        banner_text = banner.data.body if banner is not None else None
        if banner_text != config["permanent_text"]["banner"]:
            raise RuntimeError(f"Permanent banner mismatch for {shot['id']}")
        pattern_path = WORKSPACE / shot["source"]
        output_dir = pattern_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered_paths: list[Path] = []
        frames = list(range(int(shot["source_frame_start"]), int(shot["source_frame_end_exclusive"]), frame_step))
        expected_count = round(float(shot["duration_s"]) * int(config["blender"]["motion_render_fps"]))
        if len(frames) != expected_count:
            raise RuntimeError(f"Unexpected frame count for {shot['id']}: {len(frames)} != {expected_count}")
        for output_index, source_frame in enumerate(frames, start=1):
            scene.frame_set(source_frame)
            scene.camera = camera
            output_path = output_dir / f"frame_{output_index:04d}.png"
            scene.render.filepath = str(output_path)
            if bpy.context.window is not None:
                bpy.context.window.scene = scene
            bpy.ops.render.render(write_still=True, scene=scene.name)
            rendered_paths.append(output_path)
        render_records.append({
            "shot_id": shot["id"],
            "camera": camera.name,
            "visible_branches": visible,
            "source_frame_start": frames[0],
            "source_frame_end": frames[-1],
            "source_frame_step": frame_step,
            "render_fps": config["blender"]["motion_render_fps"],
            "rendered_frame_count": len(rendered_paths),
            "first_frame": str(rendered_paths[0].relative_to(WORKSPACE)).replace("\\", "/"),
            "first_frame_sha256": sha256(rendered_paths[0]),
            "last_frame": str(rendered_paths[-1].relative_to(WORKSPACE)).replace("\\", "/"),
            "last_frame_sha256": sha256(rendered_paths[-1]),
            "total_size_bytes": sum(path.stat().st_size for path in rendered_paths),
            "aggregate_path_and_sha256": aggregate_frame_identity(rendered_paths),
            "permanent_banner_text": banner_text,
            "maximum_event_time_status": "negative_event_time_only_contact_frame_excluded",
        })

    for root in branch_roots.values():
        root.delta_location.x = 0.0
    last_v9o_card = v9o_shots["S11_TWO_TRACKS_AND_CLOSE"]
    closing_body = last_v9o_card["body"] + "\n\n" + config["stairwell_requirement"]["closing_card_text"]
    helpers.create_card_content(
        card_collection,
        last_v9o_card["title"],
        closing_body,
        "EXIGENCE UTILISATEUR / PROPRIÉTÉS STRUCTURELLES INCONNUES",
        config["permanent_text"],
        materials,
    )
    card_camera = bpy.data.objects.get("CAM_V9O_CARD")
    if card_camera is None:
        raise RuntimeError("V9O card camera is missing")
    closing_card_path.parent.mkdir(parents=True, exist_ok=True)
    card_scene.render.resolution_x = int(resolution[0])
    card_scene.render.resolution_y = int(resolution[1])
    card_scene.render.resolution_percentage = 100
    helpers.render_scene(card_scene, card_camera, closing_card_path)
    body_object = bpy.data.objects.get("V9O_CARD_BODY")
    if body_object is None or config["stairwell_requirement"]["closing_card_text"] not in body_object.data.body:
        raise RuntimeError("Three-stairwell requirement is missing from the V9P closing card")

    rigid_body_objects = [obj.name for obj in bpy.data.objects if obj.rigid_body is not None]
    particle_objects = [obj.name for obj in bpy.data.objects if len(obj.particle_systems) > 0]
    fluid_modifiers = [
        {"object": obj.name, "modifier": modifier.name}
        for obj in bpy.data.objects
        for modifier in obj.modifiers
        if "FLUID" in modifier.type
    ]
    rigidbody_world_scenes = [item.name for item in bpy.data.scenes if item.rigidbody_world is not None]
    derivative_hash_after = sha256(derivative_path)
    master_hash_after = sha256(master_path)
    manifest = {
        "iteration": "V9P",
        "status": "PASS" if derivative_hash_after == derivative_hash_before and master_hash_after == master_hash_before else "FAIL",
        "blender_version": bpy.app.version_string,
        "configuration": str(CONFIG_PATH.relative_to(WORKSPACE)).replace("\\", "/"),
        "source_derivative": {
            "path": config["blender"]["source_derivative"],
            "sha256_before": derivative_hash_before,
            "sha256_after": derivative_hash_after,
            "unchanged": derivative_hash_before == derivative_hash_after,
            "saved": False,
        },
        "source_master": {
            "path": config["blender"]["source_master"],
            "sha256_before": master_hash_before,
            "sha256_after": master_hash_after,
            "unchanged": master_hash_before == master_hash_after,
        },
        "motion_sequences": render_records,
        "motion_sequence_count": len(render_records),
        "motion_frame_count": sum(record["rendered_frame_count"] for record in render_records),
        "closing_card": {
            "path": str(closing_card_path.relative_to(WORKSPACE)).replace("\\", "/"),
            "size_bytes": closing_card_path.stat().st_size,
            "sha256": sha256(closing_card_path),
            "dimensions_px": resolution,
            "three_stairwell_requirement_present": True,
            "three_stairwell_count": config["stairwell_requirement"]["requested_count"],
            "mass_stiffness_strength_or_load_path_credit_assigned": False,
        },
        "physics_audit": {
            "rigid_body_object_count": len(rigid_body_objects),
            "rigid_body_objects": rigid_body_objects,
            "particle_system_object_count": len(particle_objects),
            "particle_system_objects": particle_objects,
            "fluid_modifier_count": len(fluid_modifiers),
            "fluid_modifiers": fluid_modifiers,
            "rigidbody_world_scene_count": len(rigidbody_world_scenes),
            "rigidbody_world_scenes": rigidbody_world_scenes,
            "structural_solver_executed": False,
            "blender_physics_executed": False,
            "physical_validation": False,
        },
        "scope": {
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "network_access_used": False,
            "new_source_acquisition": False,
            "external_contact_made": False,
            "foia_request_sent": False,
        },
        "runtime": {
            "elapsed_s": time.perf_counter() - started,
            "render_engine": scene.render.engine,
            "resolution_px": resolution,
            "source_timeline_fps": source_fps,
            "motion_render_fps": config["blender"]["motion_render_fps"],
        },
        "interpretation": "Rendered frames are a low-resolution illustrative animatic source. They contain only pre-contact rigid-silhouette geometry; contact and later intervals use frozen or explanatory cards. No impact physics is calculated.",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("V9P_MOTION_MANIFEST=" + json.dumps(manifest, ensure_ascii=False))
    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
