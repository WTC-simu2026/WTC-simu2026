"""Build and render the V9O visualization-only storyboard preview.

The V4.2 master is opened read-only by workflow convention and is never saved.
All additions are written to a new derivative blend file. No Blender physics,
structural solver, post-contact motion, source acquisition or archive access is
performed.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

import bpy
from mathutils import Vector


WORKSPACE = Path(__file__).resolve().parents[2]
CONFIG_PATH = WORKSPACE / "wtc1_simulation_v8/data/v9o_blender_storyboard_preview.json"
V9N_SPEC_PATH = WORKSPACE / "wtc1_simulation_v8/output/v9n_storyboard_specification.json"
PARAMS_PATH = WORKSPACE / "wtc1_3d_v4/data/wtc1_parameters.json"
FT_TO_M = 0.3048


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def make_material(
    name: str,
    color: tuple[float, float, float, float],
    *,
    emission_strength: float = 0.0,
    metallic: float = 0.0,
    roughness: float = 0.45,
) -> bpy.types.Material:
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    node = material.node_tree.nodes.get("Principled BSDF")
    if node is not None:
        node.inputs["Base Color"].default_value = color
        node.inputs["Metallic"].default_value = metallic
        node.inputs["Roughness"].default_value = roughness
        node.inputs["Alpha"].default_value = color[3]
        emission_color = node.inputs.get("Emission Color") or node.inputs.get("Emission")
        if emission_color is not None:
            emission_color.default_value = color
        emission = node.inputs.get("Emission Strength")
        if emission is not None:
            emission.default_value = emission_strength
    return material


def hex_to_rgba(value: str) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) / 255.0 for index in (0, 2, 4)) + (1.0,)


def floor_elevations(params: dict[str, Any]) -> dict[int, float]:
    heights_ft: dict[int, float] = {}
    for entry in params["floor_height_schedule_ft"]:
        for floor in range(int(entry["from"]), int(entry["to"]) + 1):
            heights_ft[floor] = float(entry["height"])
    target = float(params["established_facts"]["roof_height_target_m"])
    datum = target - sum(heights_ft.values()) * FT_TO_M
    elevations = {1: datum}
    for floor in range(2, 111):
        elevations[floor] = elevations[floor - 1] + heights_ft[floor - 1] * FT_TO_M
    return elevations


def create_collection(name: str, scene: bpy.types.Scene) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection


def add_camera(
    name: str,
    location: Sequence[float],
    target: Sequence[float],
    collection: bpy.types.Collection,
    *,
    lens: float = 50.0,
    ortho_scale: float | None = None,
) -> bpy.types.Object:
    data = bpy.data.cameras.new(f"{name}_DATA")
    data.lens = lens
    data.sensor_width = 36.0
    data.clip_start = 0.1
    data.clip_end = 2000.0
    if ortho_scale is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
    camera = bpy.data.objects.new(name, data)
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(camera)
    return camera


def create_extruded_polygon(
    name: str,
    points_xy: list[tuple[float, float]],
    thickness: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    half = thickness / 2.0
    count = len(points_xy)
    vertices = [(x, y, -half) for x, y in points_xy] + [(x, y, half) for x, y in points_xy]
    faces: list[tuple[int, ...]] = []
    faces.append(tuple(range(count - 1, -1, -1)))
    faces.append(tuple(range(count, 2 * count)))
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.location = (0.0, 0.0, 0.0)
    obj["representation_status"] = "RIGID_SCHEMATIC_SILHOUETTE_NOT_A_SOLVER_MESH"
    return obj


def create_aircraft_silhouette(
    branch_id: str,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    root = bpy.data.objects.new(f"V9O_AA11_{branch_id.upper()}_ROOT", None)
    collection.objects.link(root)
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 4.0
    root["branch_id"] = branch_id
    root["representation_status"] = "RIGID_SCHEMATIC_SILHOUETTE_PRECONTACT_ONLY"
    objects: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0, 0, 0))
    fuselage = bpy.context.object
    fuselage.name = f"V9O_{branch_id.upper()}_FUSELAGE"
    move_to_collection(fuselage, collection)
    fuselage.parent = root
    fuselage.location = (0.0, 23.62, 0.0)
    fuselage.scale = (2.55, 23.62, 2.70)
    fuselage.data.materials.append(material)
    fuselage["representation_status"] = "SCHEMATIC_ELLIPSOID_NOT_EXACT_767_SURFACE"
    objects.append(fuselage)

    wings = create_extruded_polygon(
        f"V9O_{branch_id.upper()}_WINGS",
        [(-24.26, 24.0), (-3.2, 15.5), (3.2, 15.5), (24.26, 24.0), (3.7, 30.0), (-3.7, 30.0)],
        0.62,
        material,
        collection,
        root,
    )
    objects.append(wings)
    tail = create_extruded_polygon(
        f"V9O_{branch_id.upper()}_TAILPLANE",
        [(-8.2, 40.2), (-1.8, 37.8), (1.8, 37.8), (8.2, 40.2), (1.8, 43.5), (-1.8, 43.5)],
        0.50,
        material,
        collection,
        root,
    )
    objects.append(tail)

    fin_points = [(-0.35, 37.8), (0.35, 37.8), (0.35, 44.8), (-0.35, 47.0)]
    fin_mesh = create_extruded_polygon(
        f"V9O_{branch_id.upper()}_VERTICAL_FIN_RAW",
        fin_points,
        0.8,
        material,
        collection,
        root,
    )
    fin_mesh.name = f"V9O_{branch_id.upper()}_VERTICAL_FIN"
    fin_mesh.rotation_euler = (0.0, math.radians(90.0), 0.0)
    fin_mesh.location = (0.0, 0.0, 3.0)
    objects.append(fin_mesh)

    for side, x in (("L", -8.8), ("R", 8.8)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.35, depth=5.8, location=(0, 0, 0))
        engine = bpy.context.object
        engine.name = f"V9O_{branch_id.upper()}_ENGINE_{side}"
        move_to_collection(engine, collection)
        engine.parent = root
        engine.location = (x, 20.8, -2.2)
        engine.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        engine.data.materials.append(material)
        engine["representation_status"] = "SCHEMATIC_ENGINE_POD_NOT_CF6_MODEL"
        objects.append(engine)

    for obj in objects:
        obj["physics_enabled"] = False
    return root, objects


def configure_render(scene: bpy.types.Scene, config: dict[str, Any], resolution: tuple[int, int]) -> None:
    scene.render.engine = config["blender"]["render_engine"]
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.fps = int(config["blender"]["frame_rate_fps"])
    scene.render.fps_base = 1.0
    if scene.world is None:
        scene.world = bpy.data.worlds.new(f"{scene.name}_WORLD")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.018, 0.028, 0.045, 1.0)
        background.inputs["Strength"].default_value = 0.38


def add_plane_object(
    name: str,
    width: float,
    height: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    hw, hh = width / 2.0, height / 2.0
    mesh.from_pydata([(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)], [], [(0, 1, 2, 3)])
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def add_text_object(
    name: str,
    body: str,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    *,
    size: float,
    align_x: str = "LEFT",
    align_y: str = "TOP_BASELINE",
    extrude: float = 0.0,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_CURVE", "FONT")
    curve.body = body
    curve.align_x = align_x
    curve.align_y = align_y
    curve.size = size
    curve.extrude = extrude
    curve.space_line = 1.15
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    return obj


def clear_collection_objects(collection: bpy.types.Collection) -> None:
    for obj in list(collection.objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
            elif isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)


def camera_frame_size(camera: bpy.types.Object, scene: bpy.types.Scene) -> tuple[float, float, float]:
    aspect = scene.render.resolution_x / scene.render.resolution_y
    if camera.data.type == "ORTHO":
        width = float(camera.data.ortho_scale)
        return width, width / aspect, 2.0
    distance = 3.0
    width = distance * float(camera.data.sensor_width) / float(camera.data.lens)
    return width, width / aspect, distance


def create_camera_overlay(
    scene: bpy.types.Scene,
    collection: bpy.types.Collection,
    camera: bpy.types.Object,
    title: str,
    subtitle: str,
    epistemic: str,
    permanent: dict[str, str],
    materials: dict[str, bpy.types.Material],
    *,
    contact_stop: bool,
) -> None:
    clear_collection_objects(collection)
    width, height, distance = camera_frame_size(camera, scene)
    z_plane = -distance
    z_text = -distance + max(0.01, distance * 0.002)

    top_panel = add_plane_object("V9O_OVERLAY_TOP_PANEL", width * 0.98, height * 0.19, materials["panel"], collection)
    top_panel.parent = camera
    top_panel.location = (0.0, height * 0.40, z_plane)
    bottom_panel = add_plane_object("V9O_OVERLAY_BOTTOM_PANEL", width * 0.98, height * 0.14, materials["warning"], collection)
    bottom_panel.parent = camera
    bottom_panel.location = (0.0, -height * 0.43, z_plane)

    title_obj = add_text_object("V9O_OVERLAY_TITLE", title, materials["white"], collection, size=height * 0.052)
    title_obj.parent = camera
    title_obj.location = (-width * 0.46, height * 0.455, z_text)
    subtitle_obj = add_text_object("V9O_OVERLAY_SUBTITLE", subtitle, materials["muted"], collection, size=height * 0.030)
    subtitle_obj.parent = camera
    subtitle_obj.location = (-width * 0.46, height * 0.385, z_text)
    epistemic_obj = add_text_object("V9O_OVERLAY_EPISTEMIC", epistemic, materials["cyan"], collection, size=height * 0.024)
    epistemic_obj.parent = camera
    epistemic_obj.location = (-width * 0.46, height * 0.335, z_text)
    banner = add_text_object(
        "V9O_OVERLAY_BANNER",
        permanent["banner"],
        materials["dark"],
        collection,
        size=height * 0.035,
        align_x="CENTER",
        align_y="CENTER",
    )
    banner.parent = camera
    banner.location = (0.0, -height * 0.43, z_text)
    if contact_stop:
        contact_panel = add_plane_object("V9O_CONTACT_STOP_PANEL", width * 0.86, height * 0.12, materials["warning"], collection)
        contact_panel.parent = camera
        contact_panel.location = (0.0, 0.0, z_plane)
        contact = add_text_object(
            "V9O_CONTACT_STOP_TEXT",
            permanent["contact_stop"],
            materials["dark"],
            collection,
            size=height * 0.036,
            align_x="CENTER",
            align_y="CENTER",
        )
        contact.parent = camera
        contact.location = (0.0, 0.0, z_text)


def create_card_content(
    collection: bpy.types.Collection,
    title: str,
    body: str,
    epistemic: str,
    permanent: dict[str, str],
    materials: dict[str, bpy.types.Material],
) -> None:
    clear_collection_objects(collection)
    background = add_plane_object("V9O_CARD_BACKGROUND", 36.0, 20.25, materials["card_bg"], collection)
    background.location = (0.0, 0.0, 0.0)
    accent = add_plane_object("V9O_CARD_ACCENT", 1.0, 15.0, materials["warning"], collection)
    accent.location = (-16.0, 0.8, 0.05)
    title_obj = add_text_object("V9O_CARD_TITLE", title, materials["white"], collection, size=1.15)
    title_obj.location = (-14.7, 7.4, 0.10)
    body_obj = add_text_object("V9O_CARD_BODY", body, materials["muted"], collection, size=0.83)
    body_obj.location = (-14.7, 4.2, 0.10)
    epistemic_obj = add_text_object("V9O_CARD_EPISTEMIC", epistemic, materials["cyan"], collection, size=0.58)
    epistemic_obj.location = (-14.7, -5.3, 0.10)
    banner_panel = add_plane_object("V9O_CARD_BANNER_PANEL", 34.0, 1.65, materials["warning"], collection)
    banner_panel.location = (0.0, -8.55, 0.05)
    banner = add_text_object(
        "V9O_CARD_BANNER",
        permanent["banner"],
        materials["dark"],
        collection,
        size=0.68,
        align_x="CENTER",
        align_y="CENTER",
    )
    banner.location = (0.0, -8.55, 0.10)


def event_position(branch: dict[str, Any], event_time_s: float) -> tuple[float, float, float]:
    for position in branch["precontact_positions"]:
        if math.isclose(float(position["event_time_s"]), event_time_s, abs_tol=1e-12):
            return (
                float(position["distance_before_facade_m"]),
                float(position["height_above_contact_reference_m"]),
                float(position["distance_along_velocity_vector_to_contact_m"]),
            )
    inputs = branch["inputs"]
    kin = branch["derived_precontact_kinematics"]
    lead = -event_time_s
    return (
        float(kin["velocity_normal_to_facade_mps"]) * lead,
        float(kin["velocity_downward_mps"]) * lead,
        float(inputs["speed_mps"]) * lead,
    )


def set_branch_position(
    root: bpy.types.Object,
    branch: dict[str, Any],
    event_time_s: float,
    contact_x: float,
    north_face_y: float,
    contact_z: float,
    *,
    comparison_x_offset: float = 0.0,
) -> None:
    distance_normal, height_above, _ = event_position(branch, event_time_s)
    root.location = (
        contact_x + comparison_x_offset,
        north_face_y + distance_normal,
        contact_z + height_above,
    )


def set_branch_visibility(branch_objects: dict[str, list[bpy.types.Object]], visible: Iterable[str]) -> None:
    visible_ids = set(visible)
    for branch_id, objects in branch_objects.items():
        hidden = branch_id not in visible_ids
        for obj in objects:
            obj.hide_render = hidden
            obj.hide_viewport = hidden


def render_scene(scene: bpy.types.Scene, camera: bpy.types.Object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.camera = camera
    scene.render.filepath = str(path)
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    bpy.ops.render.render(write_still=True, scene=scene.name)


def create_proof_sheet(
    config: dict[str, Any],
    frame_paths: list[Path],
    materials: dict[str, bpy.types.Material],
    proof_path: Path,
) -> bpy.types.Scene:
    proof_name = config["master_policy"]["new_proof_scene"]
    existing = bpy.data.scenes.get(proof_name)
    if existing is not None:
        bpy.data.scenes.remove(existing, do_unlink=True)
    scene = bpy.data.scenes.new(proof_name)
    proof_resolution = tuple(config["blender"]["proof_sheet_resolution_px"])
    configure_render(scene, config, proof_resolution)
    collection = create_collection("V9O_PROOF_BACKGROUND", scene)
    camera = add_camera("CAM_V9O_PROOF", (0, 0, 10), (0, 0, 0), collection, ortho_scale=2.0)
    scene.camera = camera
    modern_compositor = not hasattr(scene, "node_tree")
    if not modern_compositor:
        scene.use_nodes = True
        node_tree = scene.node_tree
    else:
        node_tree = bpy.data.node_groups.new(f"{proof_name}_COMPOSITOR", "CompositorNodeTree")
        scene.compositing_node_group = node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    nodes.clear()
    render_layers = nodes.new("CompositorNodeRLayers")
    render_layers.layer = scene.view_layers[0].name
    previous = render_layers.outputs["Image"]
    columns = int(config["blender"]["proof_sheet_columns"])
    rows = int(config["blender"]["proof_sheet_rows"])
    cell_w, cell_h = config["blender"]["proof_sheet_cell_resolution_px"]
    proof_w, proof_h = proof_resolution
    for index, path in enumerate(frame_paths):
        row = index // columns
        col = index % columns
        image = bpy.data.images.load(str(path), check_existing=False)
        image_node = nodes.new("CompositorNodeImage")
        image_node.image = image
        transform = nodes.new("CompositorNodeTransform")
        center_x = col * cell_w + cell_w / 2.0
        center_y = proof_h - (row * cell_h + cell_h / 2.0)
        transform.inputs["X"].default_value = center_x - proof_w / 2.0
        transform.inputs["Y"].default_value = center_y - proof_h / 2.0
        transform.inputs["Scale"].default_value = 0.5
        links.new(image_node.outputs["Image"], transform.inputs["Image"])
        alpha = nodes.new("CompositorNodeAlphaOver")
        alpha.inputs["Factor"].default_value = 1.0
        links.new(previous, alpha.inputs["Background"])
        links.new(transform.outputs["Image"], alpha.inputs["Foreground"])
        previous = alpha.outputs["Image"]
    if modern_compositor:
        node_tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        composite = nodes.new("NodeGroupOutput")
    else:
        composite = nodes.new("CompositorNodeComposite")
    links.new(previous, composite.inputs["Image"])
    render_scene(scene, camera, proof_path)
    return scene


def image_record(path: Path) -> dict[str, Any]:
    image = bpy.data.images.load(str(path), check_existing=False)
    size = [int(image.size[0]), int(image.size[1])]
    bpy.data.images.remove(image)
    return {
        "path": str(path.relative_to(WORKSPACE)).replace("\\", "/"),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "dimensions_px": size,
    }


def main() -> None:
    started_wall = time.perf_counter()
    config = load_json(CONFIG_PATH)
    storyboard = load_json(V9N_SPEC_PATH)
    params = load_json(PARAMS_PATH)
    master_path = WORKSPACE / config["master_policy"]["master_blend"]
    derivative_path = WORKSPACE / config["master_policy"]["derivative_blend"]
    manifest_path = WORKSPACE / config["output"]["visualization_manifest"]
    render_dir = WORKSPACE / config["output"]["render_directory"]
    proof_path = WORKSPACE / config["output"]["proof_sheet"]
    render_dir.mkdir(parents=True, exist_ok=True)
    derivative_path.parent.mkdir(parents=True, exist_ok=True)

    master_hash_before = sha256(master_path)
    expected_master_hash = config["master_policy"]["master_expected_sha256"]
    if master_hash_before != expected_master_hash:
        raise RuntimeError("V4.2 master hash does not match the predeclared V9O input")
    if master_path.resolve() == derivative_path.resolve():
        raise RuntimeError("Derivative path must differ from the immutable master path")
    current_file = Path(bpy.data.filepath).resolve()
    if current_file != master_path.resolve():
        raise RuntimeError(f"Blender opened unexpected file: {current_file}")

    source_scene = bpy.data.scenes.get(config["master_policy"]["existing_master_scene"])
    if source_scene is None:
        raise RuntimeError("WTC1_MASTER scene is missing from the V4.2 master")
    existing_story = bpy.data.scenes.get(config["master_policy"]["new_storyboard_scene"])
    if existing_story is not None:
        bpy.data.scenes.remove(existing_story, do_unlink=True)
    scene = bpy.data.scenes.new(config["master_policy"]["new_storyboard_scene"])
    for source_collection in source_scene.collection.children:
        scene.collection.children.link(source_collection)
    scene.world = source_scene.world
    scene.frame_start = int(config["blender"]["timeline_frame_start"])
    scene.frame_end = int(config["blender"]["timeline_frame_end"])
    configure_render(scene, config, tuple(config["blender"]["individual_frame_resolution_px"]))
    scene["iteration"] = "V9O"
    scene["visualization_only"] = True
    scene["physical_validation"] = False
    scene["postcontact_motion_authorized"] = False
    scene["permanent_banner"] = config["permanent_text"]["banner"]
    scene["source_storyboard"] = str(V9N_SPEC_PATH.relative_to(WORKSPACE)).replace("\\", "/")

    for name in (
        "AA11_APPROACH_PATH_REFERENCE",
        "IMPACT_ZONE_NORTH_FLOORS_93_99_REFERENCE",
        "LABEL_MODEL_STATUS",
        "LABEL_NORTH",
    ):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True
            obj.hide_viewport = True
    for obj in bpy.data.objects:
        if obj.name.startswith("CORE_PLAN_") or obj.name == "CORE_LAYOUT_VALIDATION_PLATE":
            obj.hide_render = True
            obj.hide_viewport = True

    aircraft_collection = create_collection("V9O_AIRCRAFT_SILHOUETTES", scene)
    camera_collection = create_collection("V9O_CAMERAS", scene)
    overlay_collection = create_collection("V9O_ACTIVE_OVERLAY", scene)

    branch_materials = {
        branch_id: make_material(
            f"V9O_BRANCH_{branch_id.upper()}",
            hex_to_rgba(style["color_hex"]),
            metallic=0.18,
            roughness=0.32,
        )
        for branch_id, style in storyboard["branch_style"].items()
    }
    materials = {
        "panel": make_material("V9O_OVERLAY_PANEL", (0.015, 0.024, 0.04, 1.0), emission_strength=0.75),
        "warning": make_material("V9O_WARNING_ORANGE", (1.0, 0.46, 0.04, 1.0), emission_strength=0.9),
        "white": make_material("V9O_TEXT_WHITE", (0.94, 0.97, 1.0, 1.0), emission_strength=1.0),
        "muted": make_material("V9O_TEXT_MUTED", (0.73, 0.80, 0.90, 1.0), emission_strength=0.9),
        "cyan": make_material("V9O_TEXT_CYAN", (0.18, 0.82, 0.95, 1.0), emission_strength=1.0),
        "dark": make_material("V9O_TEXT_DARK", (0.025, 0.035, 0.055, 1.0), emission_strength=0.8),
        "card_bg": make_material("V9O_CARD_BACKGROUND_MAT", (0.018, 0.030, 0.052, 1.0), emission_strength=0.55),
    }

    facts = params["established_facts"]
    elevations = floor_elevations(params)
    north_face_y = float(facts["tower_depth_m"]) / 2.0
    contact_x = -2.0 * FT_TO_M
    contact_z = elevations[96] + 1.6 * FT_TO_M
    branch_by_id = {branch["id"]: branch for branch in storyboard["branches"]}
    branch_roots: dict[str, bpy.types.Object] = {}
    branch_objects: dict[str, list[bpy.types.Object]] = {}
    for branch_id in ("less_severe", "base", "more_severe"):
        root, objects = create_aircraft_silhouette(branch_id, branch_materials[branch_id], aircraft_collection)
        branch = branch_by_id[branch_id]
        root.rotation_mode = "XYZ"
        root.rotation_euler = (
            math.radians(float(branch["inputs"]["orientation_pitch_deg"])),
            math.radians(float(branch["inputs"]["roll_deg"])),
            0.0,
        )
        set_branch_position(root, branch, -0.5, contact_x, north_face_y, contact_z)
        branch_roots[branch_id] = root
        branch_objects[branch_id] = [root, *objects]

    frame_rate = int(config["blender"]["frame_rate_fps"])
    animation_records: dict[str, list[dict[str, Any]]] = {}
    for branch_id, keyframes in config["animation_keyframes"].items():
        root = branch_roots[branch_id]
        branch = branch_by_id[branch_id]
        records = []
        for keyframe in keyframes:
            presentation_time = float(keyframe["presentation_time_s"])
            event_time = float(keyframe["event_time_s"])
            frame = int(round(presentation_time * frame_rate)) + 1
            set_branch_position(root, branch, event_time, contact_x, north_face_y, contact_z)
            root.keyframe_insert(data_path="location", frame=frame)
            records.append({"presentation_time_s": presentation_time, "event_time_s": event_time, "frame": frame, "location_m": list(root.location)})
        if root.animation_data and root.animation_data.action:
            action = root.animation_data.action
            if hasattr(action, "fcurves"):
                fcurves = action.fcurves
            else:
                fcurves = [
                    fcurve
                    for layer in action.layers
                    for strip in layer.strips
                    for channelbag in strip.channelbags
                    for fcurve in channelbag.fcurves
                ]
            for fcurve in fcurves:
                for point in fcurve.keyframe_points:
                    point.interpolation = "LINEAR"
        animation_records[branch_id] = records

    for shot in config["shot_renders"]:
        presentation_start = next(
            source["presentation_start_s"]
            for source in load_json(V9N_SPEC_PATH)["shots"]
            if source["id"] == shot["shot_id"]
        )
        scene.timeline_markers.new(shot["shot_id"], frame=int(round(float(presentation_start) * frame_rate)) + 1)

    cam_north = add_camera(
        "CAM_V9O_NORTH",
        (0.0, 260.0, contact_z + 7.0),
        (0.0, north_face_y, contact_z + 3.0),
        camera_collection,
        ortho_scale=92.0,
    )
    cam_oblique = add_camera(
        "CAM_V9O_OBLIQUE",
        (125.0, 205.0, contact_z + 62.0),
        (0.0, north_face_y + 14.0, contact_z + 2.0),
        camera_collection,
        lens=56.0,
    )
    cam_side = add_camera(
        "CAM_V9O_SIDE",
        (185.0, north_face_y + 42.0, contact_z + 20.0),
        (0.0, north_face_y + 28.0, contact_z + 3.0),
        camera_collection,
        ortho_scale=112.0,
    )
    cameras = {camera.name: camera for camera in (cam_north, cam_oblique, cam_side)}

    card_name = config["master_policy"]["new_card_scene"]
    existing_card = bpy.data.scenes.get(card_name)
    if existing_card is not None:
        bpy.data.scenes.remove(existing_card, do_unlink=True)
    card_scene = bpy.data.scenes.new(card_name)
    configure_render(card_scene, config, tuple(config["blender"]["individual_frame_resolution_px"]))
    card_collection = create_collection("V9O_CARD_CONTENT", card_scene)
    card_camera_collection = create_collection("V9O_CARD_CAMERA", card_scene)
    card_camera = add_camera("CAM_V9O_CARD", (0, 0, 10), (0, 0, 0), card_camera_collection, ortho_scale=36.0)
    card_scene.camera = card_camera
    card_scene["visualization_only"] = True
    card_scene["physical_validation"] = False

    frame_paths: list[Path] = []
    rendered_shots: list[dict[str, Any]] = []
    comparison_offsets = {"less_severe": -29.0, "base": 0.0, "more_severe": 29.0}
    contact_offsets = {"less_severe": -22.0, "base": 0.0, "more_severe": 22.0}
    for shot in config["shot_renders"]:
        output_path = render_dir / shot["filename"]
        if shot["kind"] == "card":
            create_card_content(
                card_collection,
                shot["title"],
                shot["body"],
                shot["epistemic_label"],
                config["permanent_text"],
                materials,
            )
            render_scene(card_scene, card_camera, output_path)
        else:
            camera = cameras[shot["camera_id"]]
            branch_mode = shot["branch_mode"]
            event_time = shot.get("event_time_s")
            if branch_mode == "none":
                visible: list[str] = []
            elif branch_mode == "single":
                visible = [shot["branch_id"]]
                branch_id = shot["branch_id"]
                set_branch_position(branch_roots[branch_id], branch_by_id[branch_id], float(event_time), contact_x, north_face_y, contact_z)
            elif branch_mode in {"all_comparison_offset", "all_contact_offset"}:
                visible = ["less_severe", "base", "more_severe"]
                offsets = comparison_offsets if branch_mode == "all_comparison_offset" else contact_offsets
                for branch_id in visible:
                    set_branch_position(
                        branch_roots[branch_id],
                        branch_by_id[branch_id],
                        float(event_time),
                        contact_x,
                        north_face_y,
                        contact_z,
                        comparison_x_offset=offsets[branch_id],
                    )
            else:
                raise ValueError(f"Unsupported branch mode {branch_mode}")
            set_branch_visibility(branch_objects, visible)
            create_camera_overlay(
                scene,
                overlay_collection,
                camera,
                shot["title"],
                shot["subtitle"],
                shot["epistemic_label"],
                config["permanent_text"],
                materials,
                contact_stop=bool(shot.get("contact_stop_overlay_required", False)),
            )
            render_scene(scene, camera, output_path)
        frame_paths.append(output_path)
        rendered_shots.append({
            "shot_id": shot["shot_id"],
            "kind": shot["kind"],
            "event_time_s": shot.get("event_time_s"),
            "branch_mode": shot.get("branch_mode"),
            "file": str(output_path.relative_to(WORKSPACE)).replace("\\", "/"),
        })

    set_branch_visibility(branch_objects, ["less_severe", "base", "more_severe"])
    scene.frame_set(1)
    clear_collection_objects(overlay_collection)
    proof_scene = create_proof_sheet(config, frame_paths, materials, proof_path)

    bpy.context.preferences.filepaths.save_version = 0
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    bpy.ops.wm.save_as_mainfile(filepath=str(derivative_path), check_existing=False)

    master_hash_after = sha256(master_path)
    if master_hash_after != master_hash_before:
        raise RuntimeError("Immutable V4.2 master changed during V9O")

    rigid_body_count = sum(1 for obj in bpy.data.objects if obj.rigid_body is not None)
    particle_system_count = sum(len(obj.particle_systems) for obj in bpy.data.objects)
    fluid_modifier_count = sum(
        1 for obj in bpy.data.objects for modifier in obj.modifiers if modifier.type == "FLUID"
    )
    postcontact_motion_keyframe_count = sum(
        1
        for records in animation_records.values()
        for record in records
        if float(record["event_time_s"]) > 0.0
    )
    manifest = {
        "iteration": "V9O",
        "status": "BLENDER_VISUALIZATION_ONLY_PREVIEW_RENDERED_NO_PHYSICS",
        "blender_version": bpy.app.version_string,
        "blender_version_tuple": list(bpy.app.version),
        "configuration": str(CONFIG_PATH.relative_to(WORKSPACE)).replace("\\", "/"),
        "source_storyboard": str(V9N_SPEC_PATH.relative_to(WORKSPACE)).replace("\\", "/"),
        "master": {
            "path": str(master_path.relative_to(WORKSPACE)).replace("\\", "/"),
            "sha256_before": master_hash_before,
            "sha256_after": master_hash_after,
            "unchanged": master_hash_before == master_hash_after == expected_master_hash,
            "overwritten": False,
        },
        "derivative": {
            "path": str(derivative_path.relative_to(WORKSPACE)).replace("\\", "/"),
            "size_bytes": derivative_path.stat().st_size,
            "sha256": sha256(derivative_path),
            "new_path": derivative_path.resolve() != master_path.resolve(),
        },
        "scenes": [scene.name, card_scene.name, proof_scene.name],
        "storyboard_scene": {
            "name": scene.name,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "fps": scene.render.fps,
            "timeline_marker_count": len(scene.timeline_markers),
            "timeline_markers": [{"name": marker.name, "frame": marker.frame} for marker in scene.timeline_markers],
            "contact_reference_m": {"x": contact_x, "north_face_y": north_face_y, "z": contact_z},
            "camera_names": sorted(cameras),
            "branch_parent_names": {key: value.name for key, value in branch_roots.items()},
            "branch_animation_keyframes": animation_records,
            "maximum_animated_event_time_s": max(
                float(record["event_time_s"])
                for records in animation_records.values()
                for record in records
            ),
            "postcontact_motion_keyframe_count": postcontact_motion_keyframe_count,
        },
        "renders": [image_record(path) for path in frame_paths],
        "proof_sheet": image_record(proof_path),
        "physics_audit": {
            "rigid_body_object_count": rigid_body_count,
            "particle_system_count": particle_system_count,
            "fluid_modifier_count": fluid_modifier_count,
            "storyboard_rigidbody_world_present": scene.rigidbody_world is not None,
            "card_rigidbody_world_present": card_scene.rigidbody_world is not None,
            "proof_rigidbody_world_present": proof_scene.rigidbody_world is not None,
            "structural_solver_executed": False,
            "collision_or_fracture_executed": False,
            "fuel_fire_or_smoke_executed": False,
            "blender_used_as_physical_validation": False,
        },
        "runtime": {
            "elapsed_s": time.perf_counter() - started_wall,
            "render_engine": config["blender"]["render_engine"],
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "network_access_used": False,
            "external_contact_made": False,
            "FOIA_request_sent": False,
            "structural_solver_executed": False,
            "blender_visualization_executed": True,
            "blender_physics_executed": False,
        },
        "interpretation": "The V9O images and blend file are labelled visualization artifacts. Rigid silhouettes move only at non-positive event times and stop at first contact. They are not physical impact, damage, rupture, debris, fuel, fire or tower-response results.",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("V9O_MANIFEST=" + json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
