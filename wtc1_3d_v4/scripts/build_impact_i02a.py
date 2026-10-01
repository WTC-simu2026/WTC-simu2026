"""Build and render the IMPACT-I02A solver-state visualization.

Blender is used only as a viewer.  Every displayed shell vertex comes from a
saved OpenRadioss state.  States are held with constant interpolation and no
Blender physics, smoothing, fracture, or in-between deformation is enabled.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "wtc1_simulation_v8/output/impact_i02a_structured_wing/CONTACT_M050_R1/computed_frames.npz"
)
OUTPUT = ROOT / "wtc1_3d_v4/output/impact_i02a"
RENDERS = ROOT / "wtc1_3d_v4/renders/impact_i02a"
BLEND_PATH = OUTPUT / "IMPACT_I02A_SOLVER_STATES.blend"
FRAME_DIR = RENDERS / "frames"
ANIMATION_PATH = RENDERS / "IMPACT_I02A_solver_states.gif"
FRAMES_PER_STATE = 6
FPS = 30
STRAIN_DISPLAY_THRESHOLD = 0.20


PART_NAMES = {
    1: "facade_columns",
    2: "facade_spandrel",
    3: "wing_skins",
    4: "wing_spars",
    5: "wing_ribs",
    6: "stringer_webs",
    7: "stringer_flanges",
}

PART_COLORS = {
    1: (0.12, 0.32, 0.58, 1.0),
    2: (0.20, 0.48, 0.76, 1.0),
    3: (0.88, 0.68, 0.16, 1.0),
    4: (0.96, 0.40, 0.08, 1.0),
    5: (0.12, 0.67, 0.62, 1.0),
    6: (0.30, 0.72, 0.30, 1.0),
    7: (0.72, 0.82, 0.28, 1.0),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def material(name: str, color: tuple[float, float, float, float]):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.metallic = 0.15
    mat.roughness = 0.55
    return mat


def camera_text(camera, name: str, body: str, xy: tuple[float, float], size: float, color):
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = body
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.003
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = camera
    # Keep labels just beyond the camera near plane so they remain a true
    # screen-facing overlay instead of being depth-occluded by the model.
    obj.location = (xy[0], xy[1], -0.20)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.data.materials.append(material(f"{name}_material", color))
    return obj


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    data = np.load(SOURCE)
    points_mm = data["points_mm"]
    # Solver x=span, y=vertical, z=impact. Blender x=span, z=vertical,
    # y=impact. The swap is display-only and is audited on reopening.
    points_m = points_mm[:, :, [0, 2, 1]] / 1000.0
    quads = data["quads"].astype(np.int32)
    parts = data["parts"].astype(np.int32)
    epsp = data["epsp"]
    times_ms = data["times_ms"]

    if points_m.shape[0] != 25:
        raise RuntimeError(f"Expected 25 solver states, received {points_m.shape[0]}")
    if quads.shape[0] != parts.shape[0] or epsp.shape[1] != quads.shape[0]:
        raise RuntimeError("Element topology, part IDs, and strain arrays disagree")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 620
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = len(times_ms) * FRAMES_PER_STATE
    scene.world = bpy.data.worlds.new("World")
    scene.world.color = (0.025, 0.03, 0.04)
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studiolight_rotate_z = 0.35
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.background_type = "WORLD"
    shading.show_specular_highlight = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"

    mesh = bpy.data.meshes.new("I02A_solver_shell_mesh")
    mesh.from_pydata(points_m[0].tolist(), [], quads.tolist())
    mesh.update()
    obj = bpy.data.objects.new("I02A_OPENRADIOSS_SHELL_STATES", mesh)
    scene.collection.objects.link(obj)

    for part_id in sorted(PART_NAMES):
        mesh.materials.append(material(PART_NAMES[part_id], PART_COLORS[part_id]))
    mesh.materials.append(material("diagnostic_epsp_over_0p20", (0.92, 0.035, 0.025, 1.0)))
    base_indices = parts - 1
    mesh.polygons.foreach_set("material_index", base_indices.tolist())

    part_attr = mesh.attributes.new(name="solver_part_id", type="INT", domain="FACE")
    part_attr.data.foreach_set("value", parts.tolist())

    obj.shape_key_add(name="Basis_state_000_0ms")
    for state_index in range(1, len(times_ms)):
        key = obj.shape_key_add(name=f"State_{state_index:03d}_{times_ms[state_index]:.6f}ms")
        key.data.foreach_set("co", points_m[state_index].reshape(-1))
        first = state_index * FRAMES_PER_STATE + 1
        last = (state_index + 1) * FRAMES_PER_STATE
        for frame, value in ((first - 1, 0.0), (first, 1.0), (last, 1.0), (last + 1, 0.0)):
            key.value = value
            key.keyframe_insert(data_path="value", frame=frame)
        key.value = 0.0

    action = obj.data.shape_keys.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        for keyframe in curve.keyframe_points:
                            keyframe.interpolation = "CONSTANT"

    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (5.4, -6.7, 4.2)
    target = Vector((0.0, 0.55, 0.45))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 7.0
    scene.camera = camera

    warning = bpy.data.objects.new(
        "WARNING_RUPTURE_DESACTIVEE_PAS_VALIDATION_WTC1", None
    )
    scene.collection.objects.link(warning)
    warning["warning"] = (
        "Rupture disabled; final large strains exceed constitutive validity; "
        "Blender replays solver states only."
    )

    state_cache = {"index": None}

    def set_visual_state(scene_arg) -> None:
        state_index = min((scene_arg.frame_current - 1) // FRAMES_PER_STATE, len(times_ms) - 1)
        if state_cache["index"] == state_index:
            return
        indices = base_indices.copy()
        indices[epsp[state_index] > STRAIN_DISPLAY_THRESHOLD] = len(PART_NAMES)
        mesh.polygons.foreach_set("material_index", indices.tolist())
        mesh.update()
        state_cache["index"] = state_index

    bpy.app.handlers.frame_change_pre.append(set_visual_state)

    source_hash = sha256(SOURCE)
    obj["iteration"] = "IMPACT-I02A"
    obj["source_npz"] = str(SOURCE)
    obj["source_sha256"] = source_hash
    obj["solver"] = "OpenRadioss 20260728"
    obj["solver_states"] = int(len(times_ms))
    obj["coordinate_transform"] = "solver mm x,y,z -> Blender m x,z,y"
    obj["interpolation"] = "CONSTANT"
    obj["blender_physics"] = False
    obj["erosion_or_fracture"] = False
    obj["strain_display_threshold"] = STRAIN_DISPLAY_THRESHOLD
    obj["scope"] = (
        "Reduced structured wing section versus three representative facade columns; "
        "not whole-aircraft geometry and not physical WTC1 validation."
    )
    scene["permanent_warning"] = (
        "Rupture disabled; final large strains exceed constitutive validity; "
        "Blender replays solver states only."
    )
    scene["physical_duration_ms"] = float(times_ms[-1])
    scene["display_duration_s"] = scene.frame_end / FPS

    # Render three auditable stills before encoding the full state-hold movie.
    for state_index, label in ((0, "initial"), (5, "contact_0p25ms"), (24, "final_1p20ms")):
        scene.frame_set(state_index * FRAMES_PER_STATE + 1)
        set_visual_state(scene)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(RENDERS / f"I02A_{label}.png")
        bpy.ops.render.render(write_still=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

    # One lossless PNG per exact solver state.  A separate Pillow script merely
    # repeats each image for 0.2 s when it packages the GIF; it never invents
    # intermediate geometry.
    for state_index in range(len(times_ms)):
        scene.frame_set(state_index * FRAMES_PER_STATE + 1)
        set_visual_state(scene)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(FRAME_DIR / f"state_{state_index:03d}.png")
        bpy.ops.render.render(write_still=True)

    manifest = {
        "iteration": "IMPACT-I02A",
        "blender": bpy.app.version_string,
        "source_npz": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": source_hash,
        "blend": str(BLEND_PATH.relative_to(ROOT)).replace("\\", "/"),
        "animation_target": str(ANIMATION_PATH.relative_to(ROOT)).replace("\\", "/"),
        "lossless_state_frames": str(FRAME_DIR.relative_to(ROOT)).replace("\\", "/"),
        "solver_states": int(len(times_ms)),
        "vertices": int(points_m.shape[1]),
        "shell_faces": int(quads.shape[0]),
        "physical_times_ms": [float(value) for value in times_ms],
        "display_frames": int(scene.frame_end),
        "rendered_exact_state_frames": int(len(times_ms)),
        "fps": FPS,
        "display_duration_s": scene.frame_end / FPS,
        "frames_per_solver_state": FRAMES_PER_STATE,
        "interpolation": "CONSTANT",
        "coordinate_transform": "solver mm x,y,z -> Blender m x,z,y",
        "physics_engine": False,
        "fracture_or_erosion": False,
        "strain_display_threshold": STRAIN_DISPLAY_THRESHOLD,
        "render_seconds": time.perf_counter() - started,
        "scope": obj["scope"],
        "permanent_warning": scene["permanent_warning"],
    }
    (OUTPUT / "build_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
