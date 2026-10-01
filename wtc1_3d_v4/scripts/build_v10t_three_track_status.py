"""Build the V10T static, three-track Blender status package.

The V4.2 master is opened as an immutable input and is never saved.  Every
created scene is static and labelled as visualization-only.  No Blender
physics, structural response, post-impact motion, fire, temperature field,
member failure, collapse, propagation or arrest is generated.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import bpy
from mathutils import Vector


WORKSPACE = Path(__file__).resolve().parents[2]
CONFIG_PATH = WORKSPACE / "wtc1_simulation_v8/data/v10t_three_track_3d_status_package.json"
PARAMS_PATH = WORKSPACE / "wtc1_3d_v4/data/wtc1_parameters.json"
SCRIPT_PATH = Path(__file__).resolve()
FT_TO_M = 0.3048


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(WORKSPACE.resolve()).as_posix()


def make_material(
    name: str,
    color: tuple[float, float, float, float],
    *,
    emission_strength: float = 0.0,
    metallic: float = 0.0,
    roughness: float = 0.5,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
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
    data.clip_end = 2500.0
    if ortho_scale is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
    camera = bpy.data.objects.new(name, data)
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(camera)
    camera["iteration"] = "V10T"
    camera["visualization_only"] = True
    return camera


def add_plane(
    name: str,
    width: float,
    height: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    half_w = width / 2.0
    half_h = height / 2.0
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    mesh.from_pydata(
        [(-half_w, -half_h, 0.0), (half_w, -half_h, 0.0), (half_w, half_h, 0.0), (-half_w, half_h, 0.0)],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj["iteration"] = "V10T"
    obj["visualization_only"] = True
    obj["physics_enabled"] = False
    return obj


def add_box(
    name: str,
    dimensions: Sequence[float],
    location: Sequence[float],
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    dx, dy, dz = (float(value) / 2.0 for value in dimensions)
    vertices = [
        (-dx, -dy, -dz), (dx, -dy, -dz), (dx, dy, -dz), (-dx, dy, -dz),
        (-dx, -dy, dz), (dx, -dy, dz), (dx, dy, dz), (-dx, dy, dz),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    collection.objects.link(obj)
    obj["iteration"] = "V10T"
    obj["visualization_only"] = True
    obj["physics_enabled"] = False
    obj["representation_status"] = "REFERENCE_FRAME_ONLY_NOT_PHYSICAL_FIELD"
    return obj


def add_text(
    name: str,
    body: str,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    *,
    size: float,
    align_x: str = "LEFT",
    align_y: str = "TOP_BASELINE",
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_CURVE", "FONT")
    curve.body = body
    curve.align_x = align_x
    curve.align_y = align_y
    curve.size = size
    curve.space_line = 1.15
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj["iteration"] = "V10T"
    obj["visualization_only"] = True
    obj["physics_enabled"] = False
    return obj


def configure_render(scene: bpy.types.Scene, config: dict[str, Any], resolution: Sequence[int]) -> None:
    visual = config["visual_contract"]
    scene.render.engine = visual["render_engine"]
    scene.render.resolution_x = int(resolution[0])
    scene.render.resolution_y = int(resolution[1])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.fps = 24
    scene.render.fps_base = 1.0
    scene.frame_start = int(visual["frame_start"])
    scene.frame_end = int(visual["frame_end"])
    if scene.world is None:
        scene.world = bpy.data.worlds.new(f"{scene.name}_WORLD")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.010, 0.018, 0.032, 1.0)
        background.inputs["Strength"].default_value = 0.32


def floor_elevations(params: dict[str, Any]) -> dict[int, float]:
    heights_ft: dict[int, float] = {}
    for entry in params["floor_height_schedule_ft"]:
        for floor in range(int(entry["from"]), int(entry["to"]) + 1):
            heights_ft[floor] = float(entry["height"])
    target = float(params["established_facts"]["roof_height_target_m"])
    datum = target - sum(heights_ft.values()) * FT_TO_M
    elevations = {1: datum}
    for floor in range(2, 112):
        elevations[floor] = elevations[floor - 1] + heights_ft.get(floor - 1, heights_ft[110]) * FT_TO_M
    return elevations


def camera_frame(camera: bpy.types.Object, scene: bpy.types.Scene, distance: float = 3.0) -> tuple[float, float, float]:
    aspect = scene.render.resolution_x / scene.render.resolution_y
    if camera.data.type == "ORTHO":
        width = float(camera.data.ortho_scale)
        height = width / aspect
        return width, height, 2.0
    width = distance * float(camera.data.sensor_width) / float(camera.data.lens)
    height = width / aspect
    return width, height, distance


def add_camera_overlay(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    shot: dict[str, Any],
    config: dict[str, Any],
    materials: dict[str, bpy.types.Material],
) -> None:
    collection = create_collection(f"V10T_OVERLAY_{shot['id']}", scene)
    width, height, distance = camera_frame(camera, scene)
    plane_z = -distance
    text_z = -distance + max(0.012, distance * 0.004)

    top = add_plane(f"V10T_{shot['id']}_TOP", width * 0.98, height * 0.205, materials["panel"], collection)
    top.parent = camera
    top.location = (0.0, height * 0.397, plane_z)
    middle = add_plane(f"V10T_{shot['id']}_MIDDLE", width * 0.63, height * 0.145, materials["panel"], collection)
    middle.parent = camera
    middle.location = (-width * 0.17, -height * 0.265, plane_z)
    bottom = add_plane(f"V10T_{shot['id']}_BOTTOM", width * 0.98, height * 0.095, materials["warning"], collection)
    bottom.parent = camera
    bottom.location = (0.0, -height * 0.445, plane_z)

    title = add_text(f"V10T_{shot['id']}_TITLE", shot["title"], materials["white"], collection, size=height * 0.044)
    title.parent = camera
    title.location = (-width * 0.465, height * 0.455, text_z)
    subtitle = add_text(f"V10T_{shot['id']}_SUBTITLE", shot["subtitle"], materials["muted"], collection, size=height * 0.026)
    subtitle.parent = camera
    subtitle.location = (-width * 0.465, height * 0.390, text_z)
    epistemic = add_text(f"V10T_{shot['id']}_EPISTEMIC", shot["epistemic_label"], materials["cyan"], collection, size=height * 0.021)
    epistemic.parent = camera
    epistemic.location = (-width * 0.465, height * 0.345, text_z)
    body = add_text(f"V10T_{shot['id']}_BODY", shot["body"], materials["white"], collection, size=height * 0.022)
    body.parent = camera
    body.location = (-width * 0.465, -height * 0.215, text_z)
    banner = add_text(
        f"V10T_{shot['id']}_BANNER",
        config["visual_contract"]["permanent_banner"],
        materials["dark"],
        collection,
        size=height * 0.029,
        align_x="CENTER",
        align_y="CENTER",
    )
    banner.parent = camera
    banner.location = (0.0, -height * 0.445, text_z)


def add_lights(scene: bpy.types.Scene, shot_id: str) -> None:
    collection = create_collection(f"V10T_LIGHTS_{shot_id}", scene)
    sun_data = bpy.data.lights.new(f"V10T_SUN_{shot_id}_DATA", "SUN")
    sun_data.energy = 2.2
    sun_data.angle = math.radians(8.0)
    sun = bpy.data.objects.new(f"V10T_SUN_{shot_id}", sun_data)
    sun.rotation_euler = (math.radians(28), math.radians(-20), math.radians(28))
    collection.objects.link(sun)
    sun["iteration"] = "V10T"
    sun["visualization_only"] = True
    area_data = bpy.data.lights.new(f"V10T_AREA_{shot_id}_DATA", "AREA")
    area_data.energy = 900.0
    area_data.shape = "DISK"
    area_data.size = 160.0
    area = bpy.data.objects.new(f"V10T_AREA_{shot_id}", area_data)
    area.location = (110.0, 130.0, 455.0)
    area.rotation_euler = (Vector((0.0, 0.0, 220.0)) - area.location).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(area)
    area["iteration"] = "V10T"
    area["visualization_only"] = True


def add_reference_zone(
    scene: bpy.types.Scene,
    shot_id: str,
    params: dict[str, Any],
    config: dict[str, Any],
    material: bpy.types.Material,
) -> dict[str, float]:
    collection = create_collection(f"V10T_REFERENCE_ZONE_{shot_id}", scene)
    elevations = floor_elevations(params)
    lower_floor, upper_floor = config["visual_contract"]["impact_zone_floors"]
    lower_z = elevations[int(lower_floor)]
    upper_z = elevations[int(upper_floor) + 1]
    centre_z = (lower_z + upper_z) / 2.0
    height = upper_z - lower_z
    facts = params["established_facts"]
    width = float(facts["tower_width_m"]) + 3.2
    depth = float(facts["tower_depth_m"]) + 3.2
    edge = 0.65
    index = 0
    for z in (lower_z, upper_z):
        for y in (-depth / 2.0, depth / 2.0):
            index += 1
            add_box(f"V10T_{shot_id}_ZONE_EDGE_{index:02d}", (width, edge, edge), (0.0, y, z), material, collection)
        for x in (-width / 2.0, width / 2.0):
            index += 1
            add_box(f"V10T_{shot_id}_ZONE_EDGE_{index:02d}", (edge, depth, edge), (x, 0.0, z), material, collection)
    for x in (-width / 2.0, width / 2.0):
        for y in (-depth / 2.0, depth / 2.0):
            index += 1
            add_box(f"V10T_{shot_id}_ZONE_EDGE_{index:02d}", (edge, edge, height), (x, y, centre_z), material, collection)
    collection["representation_status"] = config["visual_contract"]["impact_zone_marker_meaning"]
    collection["physical_field"] = False
    return {"lower_z_m": lower_z, "upper_z_m": upper_z, "height_m": height}


def create_tower_scene(
    source_scene: bpy.types.Scene,
    shot: dict[str, Any],
    config: dict[str, Any],
    params: dict[str, Any],
    materials: dict[str, bpy.types.Material],
) -> tuple[bpy.types.Scene, dict[str, float] | None]:
    scene = bpy.data.scenes.new(f"V10T_{shot['id']}")
    for source_collection in source_scene.collection.children:
        scene.collection.children.link(source_collection)
    scene.world = source_scene.world
    configure_render(scene, config, config["visual_contract"]["render_resolution_px"])
    scene["iteration"] = "V10T"
    scene["shot_id"] = shot["id"]
    scene["visualization_only"] = True
    scene["physical_validation"] = False
    scene["physical_state_release_count"] = 0
    scene["postcontact_motion_authorized"] = False
    scene["predicted_collapse_motion_authorized"] = False
    scene["permanent_banner"] = config["visual_contract"]["permanent_banner"]
    scene["secondary_warning"] = config["visual_contract"]["secondary_warning"]
    camera_collection = create_collection(f"V10T_CAMERA_{shot['id']}", scene)
    elevations = floor_elevations(params)
    impact_centre = (elevations[93] + elevations[100]) / 2.0
    if shot["camera"] == "impact_north":
        camera = add_camera(
            f"CAM_V10T_{shot['id']}",
            (0.0, 290.0, impact_centre + 1.0),
            (0.0, 0.0, impact_centre),
            camera_collection,
            ortho_scale=82.0,
        )
    elif shot["camera"] == "impact_oblique":
        camera = add_camera(
            f"CAM_V10T_{shot['id']}",
            (155.0, 235.0, impact_centre + 78.0),
            (0.0, 10.0, impact_centre),
            camera_collection,
            lens=55.0,
        )
    elif shot["camera"] == "full_oblique":
        camera = add_camera(
            f"CAM_V10T_{shot['id']}",
            (500.0, 500.0, 330.0),
            (0.0, 0.0, 210.0),
            camera_collection,
            lens=52.0,
        )
    else:
        raise ValueError(f"Unknown V10T camera {shot['camera']}")
    scene.camera = camera
    add_lights(scene, shot["id"])
    zone = None
    if bool(shot.get("zone_marker")):
        zone = add_reference_zone(scene, shot["id"], params, config, materials["warning"])
    add_camera_overlay(scene, camera, shot, config, materials)
    return scene, zone


def create_overview_scene(
    shot: dict[str, Any],
    config: dict[str, Any],
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Scene:
    scene = bpy.data.scenes.new(f"V10T_{shot['id']}")
    configure_render(scene, config, config["visual_contract"]["render_resolution_px"])
    scene["iteration"] = "V10T"
    scene["shot_id"] = shot["id"]
    scene["visualization_only"] = True
    scene["physical_validation"] = False
    scene["physical_state_release_count"] = 0
    scene["postcontact_motion_authorized"] = False
    scene["predicted_collapse_motion_authorized"] = False
    scene["permanent_banner"] = config["visual_contract"]["permanent_banner"]
    collection = create_collection("V10T_CHAIN_OVERVIEW_CONTENT", scene)
    camera_collection = create_collection("V10T_CHAIN_OVERVIEW_CAMERA", scene)
    camera = add_camera("CAM_V10T_CHAIN_OVERVIEW", (0.0, 0.0, 10.0), (0.0, 0.0, 0.0), camera_collection, ortho_scale=36.0)
    scene.camera = camera
    background = add_plane("V10T_OVERVIEW_BACKGROUND", 36.0, 20.25, materials["card_bg"], collection)
    background.location = (0.0, 0.0, 0.0)
    title = add_text("V10T_OVERVIEW_TITLE", shot["title"], materials["white"], collection, size=0.92)
    title.location = (-16.7, 8.5, 0.10)
    subtitle = add_text("V10T_OVERVIEW_SUBTITLE", shot["subtitle"], materials["cyan"], collection, size=0.55)
    subtitle.location = (-16.7, 6.9, 0.10)

    stage_labels = ["IMPACT /\nDOMMAGES", "FEU /\nTHERMIQUE", "INITIATION", "PROPAGATION /\nARRÊT"]
    stage_x = [-12.5, -4.2, 4.2, 12.5]
    for index, (label, x) in enumerate(zip(stage_labels, stage_x), start=1):
        panel = add_plane(f"V10T_STAGE_PANEL_{index}", 7.1, 2.5, materials["stage"], collection)
        panel.location = (x, 4.1, 0.04)
        text = add_text(f"V10T_STAGE_TEXT_{index}", label, materials["white"], collection, size=0.48, align_x="CENTER", align_y="CENTER")
        text.location = (x, 4.1, 0.10)
        if index < len(stage_labels):
            arrow = add_text(f"V10T_STAGE_ARROW_{index}", "→", materials["muted"], collection, size=0.72, align_x="CENTER", align_y="CENTER")
            arrow.location = ((x + stage_x[index]) / 2.0, 4.1, 0.10)

    rows = [
        ("CONTRÔLE ZÉRO", "logiciel uniquement — aucun état historique", materials["control"]),
        ("RÉFÉRENCE OFFICIELLE", "dépendante — plages et statuts bornés", materials["official"]),
        ("ÉVÉNEMENT PHYSIQUE", "indéterminé — 0 état physique transmis", materials["unknown"]),
    ]
    row_y = [0.9, -1.6, -4.1]
    for index, ((label, detail, material), y) in enumerate(zip(rows, row_y), start=1):
        swatch = add_plane(f"V10T_TRACK_SWATCH_{index}", 0.75, 1.25, material, collection)
        swatch.location = (-15.9, y, 0.05)
        label_obj = add_text(f"V10T_TRACK_LABEL_{index}", label, materials["white"], collection, size=0.58, align_y="CENTER")
        label_obj.location = (-15.0, y + 0.25, 0.10)
        detail_obj = add_text(f"V10T_TRACK_DETAIL_{index}", detail, materials["muted"], collection, size=0.48, align_y="CENTER")
        detail_obj.location = (-4.0, y + 0.25, 0.10)

    epistemic = add_text("V10T_OVERVIEW_EPISTEMIC", shot["epistemic_label"], materials["cyan"], collection, size=0.52, align_x="CENTER", align_y="CENTER")
    epistemic.location = (0.0, -6.2, 0.10)
    banner_panel = add_plane("V10T_OVERVIEW_BANNER_PANEL", 35.0, 1.45, materials["warning"], collection)
    banner_panel.location = (0.0, -8.75, 0.05)
    banner = add_text(
        "V10T_OVERVIEW_BANNER",
        config["visual_contract"]["permanent_banner"],
        materials["dark"],
        collection,
        size=0.62,
        align_x="CENTER",
        align_y="CENTER",
    )
    banner.location = (0.0, -8.75, 0.10)
    return scene


def render_scene(scene: bpy.types.Scene, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    scene.frame_set(1)
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    bpy.ops.render.render(write_still=True, scene=scene.name)


def create_proof_sheet(
    config: dict[str, Any],
    image_paths: list[Path],
    materials: dict[str, bpy.types.Material],
    proof_path: Path,
) -> bpy.types.Scene:
    scene = bpy.data.scenes.new("V10T_PROOF_SHEET")
    configure_render(scene, config, config["visual_contract"]["proof_sheet_resolution_px"])
    scene["iteration"] = "V10T"
    scene["visualization_only"] = True
    scene["physical_validation"] = False
    scene["physical_state_release_count"] = 0
    scene["postcontact_motion_authorized"] = False
    scene["predicted_collapse_motion_authorized"] = False
    scene["permanent_banner"] = config["visual_contract"]["permanent_banner"]
    collection = create_collection("V10T_PROOF_BACKGROUND", scene)
    camera = add_camera("CAM_V10T_PROOF", (0.0, 0.0, 10.0), (0.0, 0.0, 0.0), collection, ortho_scale=2.0)
    scene.camera = camera
    background = add_plane("V10T_PROOF_BACKGROUND_PLANE", 3.6, 2.0, materials["card_bg"], collection)
    background.location = (0.0, 0.0, 0.0)

    modern_compositor = not hasattr(scene, "node_tree")
    if not modern_compositor:
        scene.use_nodes = True
        node_tree = scene.node_tree
    else:
        node_tree = bpy.data.node_groups.new("V10T_PROOF_COMPOSITOR", "CompositorNodeTree")
        scene.compositing_node_group = node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    nodes.clear()
    render_layers = nodes.new("CompositorNodeRLayers")
    render_layers.layer = scene.view_layers[0].name
    previous = render_layers.outputs["Image"]
    columns = int(config["visual_contract"]["proof_sheet_columns"])
    cell_w, cell_h = config["visual_contract"]["proof_sheet_cell_resolution_px"]
    proof_w, proof_h = config["visual_contract"]["proof_sheet_resolution_px"]
    source_w, source_h = config["visual_contract"]["render_resolution_px"]
    scale = min(cell_w / source_w, cell_h / source_h)
    for index, path in enumerate(image_paths):
        row = index // columns
        col = index % columns
        image = bpy.data.images.load(str(path), check_existing=False)
        image_node = nodes.new("CompositorNodeImage")
        image_node.image = image
        transform = nodes.new("CompositorNodeTransform")
        centre_x = col * cell_w + cell_w / 2.0
        centre_y = proof_h - (row * cell_h + cell_h / 2.0)
        transform.inputs["X"].default_value = centre_x - proof_w / 2.0
        transform.inputs["Y"].default_value = centre_y - proof_h / 2.0
        transform.inputs["Scale"].default_value = scale
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
    render_scene(scene, proof_path)
    return scene


def image_record(path: Path) -> dict[str, Any]:
    image = bpy.data.images.load(str(path), check_existing=False)
    dimensions = [int(image.size[0]), int(image.size[1])]
    bpy.data.images.remove(image)
    return {
        "path": rel(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "dimensions_px": dimensions,
    }


def main() -> None:
    started = time.perf_counter()
    config = load_json(CONFIG_PATH)
    params = load_json(PARAMS_PATH)
    if config.get("iteration") != "V10T":
        raise RuntimeError("Unexpected V10T configuration iteration")
    visual = config["visual_contract"]
    outputs = config["outputs"]
    master_item = config["protected_files"][0]
    master_path = WORKSPACE / master_item["path"]
    derivative_path = WORKSPACE / visual["derivative_blend"]
    manifest_path = WORKSPACE / outputs["blender_internal_manifest"]
    render_dir = WORKSPACE / outputs["render_directory"]
    proof_path = WORKSPACE / outputs["proof_sheet"]
    master_hash_before = sha256(master_path)
    if master_hash_before != master_item["expected_sha256"]:
        raise RuntimeError("Immutable V4.2 master hash does not match V10T predeclaration")
    if Path(bpy.data.filepath).resolve() != master_path.resolve():
        raise RuntimeError(f"Blender opened unexpected file: {bpy.data.filepath}")
    if derivative_path.resolve() == master_path.resolve():
        raise RuntimeError("Derivative path must differ from immutable master")
    if derivative_path.exists():
        raise RuntimeError(f"V10T derivative already exists and will not be overwritten: {derivative_path}")
    derivative_path.parent.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    source_scene = bpy.data.scenes.get(visual["master_scene"])
    if source_scene is None:
        raise RuntimeError(f"Missing master scene {visual['master_scene']}")

    for name in ("AA11_APPROACH_PATH_REFERENCE", "IMPACT_ZONE_NORTH_FLOORS_93_99_REFERENCE", "LABEL_MODEL_STATUS", "LABEL_NORTH"):
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True
            obj.hide_viewport = True
    for obj in bpy.data.objects:
        if obj.name.startswith("CORE_PLAN_") or obj.name == "CORE_LAYOUT_VALIDATION_PLATE":
            obj.hide_render = True
            obj.hide_viewport = True

    materials = {
        "panel": make_material("V10T_PANEL", (0.012, 0.022, 0.040, 1.0), emission_strength=0.72),
        "warning": make_material("V10T_WARNING", (1.0, 0.46, 0.035, 1.0), emission_strength=1.0),
        "white": make_material("V10T_WHITE", (0.94, 0.97, 1.0, 1.0), emission_strength=1.0),
        "muted": make_material("V10T_MUTED", (0.66, 0.75, 0.86, 1.0), emission_strength=0.9),
        "cyan": make_material("V10T_CYAN", (0.20, 0.84, 0.96, 1.0), emission_strength=1.0),
        "dark": make_material("V10T_DARK", (0.018, 0.028, 0.045, 1.0), emission_strength=0.8),
        "card_bg": make_material("V10T_CARD_BG", (0.012, 0.024, 0.043, 1.0), emission_strength=0.55),
        "stage": make_material("V10T_STAGE", (0.075, 0.13, 0.20, 1.0), emission_strength=0.55),
        "control": make_material("V10T_CONTROL", (0.18, 0.62, 0.96, 1.0), emission_strength=1.0),
        "official": make_material("V10T_OFFICIAL", (1.0, 0.55, 0.08, 1.0), emission_strength=1.0),
        "unknown": make_material("V10T_UNKNOWN", (0.78, 0.28, 0.78, 1.0), emission_strength=1.0),
    }

    created_scenes: list[bpy.types.Scene] = []
    rendered: list[dict[str, Any]] = []
    zone_records: list[dict[str, Any]] = []
    render_paths: list[Path] = []
    for shot in visual["renders"]:
        if shot["kind"] == "card":
            scene = create_overview_scene(shot, config, materials)
            zone = None
        elif shot["kind"] == "tower":
            scene, zone = create_tower_scene(source_scene, shot, config, params, materials)
        else:
            raise RuntimeError(f"Unsupported V10T shot kind {shot['kind']}")
        created_scenes.append(scene)
        path = render_dir / shot["filename"]
        render_scene(scene, path)
        render_paths.append(path)
        rendered.append({
            "shot_id": shot["id"],
            "kind": shot["kind"],
            "epistemic_label": shot["epistemic_label"],
            "zone_marker": bool(shot.get("zone_marker", False)),
            **image_record(path),
        })
        if zone is not None:
            zone_records.append({"shot_id": shot["id"], **zone})

    proof_scene = create_proof_sheet(config, render_paths, materials, proof_path)
    created_scenes.append(proof_scene)

    for scene in created_scenes:
        if scene.frame_start != 1 or scene.frame_end != 1:
            raise RuntimeError(f"V10T scene is not static: {scene.name}")
        if scene.rigidbody_world is not None:
            raise RuntimeError(f"V10T scene has a rigid-body world: {scene.name}")

    v10t_objects = [obj for obj in bpy.data.objects if obj.get("iteration") == "V10T"]
    keyframe_count = 0
    for obj in v10t_objects:
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            if hasattr(action, "fcurves"):
                keyframe_count += sum(len(curve.keyframe_points) for curve in action.fcurves)
            else:
                keyframe_count += sum(
                    len(curve.keyframe_points)
                    for layer in action.layers
                    for strip in layer.strips
                    for channelbag in strip.channelbags
                    for curve in channelbag.fcurves
                )
    rigid_body_count = sum(1 for obj in v10t_objects if obj.rigid_body is not None)
    particle_system_count = sum(len(obj.particle_systems) for obj in v10t_objects)
    fluid_modifier_count = sum(1 for obj in v10t_objects for modifier in obj.modifiers if modifier.type == "FLUID")
    if any((keyframe_count, rigid_body_count, particle_system_count, fluid_modifier_count)):
        raise RuntimeError("V10T static/no-physics invariant failed")

    bpy.context.preferences.filepaths.save_version = 0
    if bpy.context.window is not None:
        bpy.context.window.scene = created_scenes[0]
    bpy.context.scene["v10t_visualization_only"] = True
    bpy.context.scene["v10t_physical_state_release_count"] = 0
    bpy.context.scene["v10t_historical_outcome_assignment_count"] = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(derivative_path), check_existing=False)

    master_hash_after = sha256(master_path)
    if master_hash_after != master_hash_before:
        raise RuntimeError("Immutable V4.2 master changed during V10T")

    proof_record = image_record(proof_path)
    manifest = {
        "iteration": "V10T",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_STATIC_LABELLED_BLENDER_VISUALIZATION_ONLY",
        "blender_version": bpy.app.version_string,
        "blender_version_tuple": list(bpy.app.version),
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256(SCRIPT_PATH)},
        "master": {
            "path": rel(master_path),
            "sha256_before": master_hash_before,
            "sha256_after": master_hash_after,
            "unchanged": master_hash_before == master_hash_after == master_item["expected_sha256"],
            "overwritten": False,
        },
        "derivative": {
            "path": rel(derivative_path),
            "sha256": sha256(derivative_path),
            "size_bytes": derivative_path.stat().st_size,
            "new_path": derivative_path.resolve() != master_path.resolve(),
        },
        "created_scene_names": [scene.name for scene in created_scenes],
        "created_scene_count": len(created_scenes),
        "render_count": len(rendered),
        "renders": rendered,
        "proof_sheet": proof_record,
        "reference_zone_records": zone_records,
        "permanent_banner": visual["permanent_banner"],
        "secondary_warning": visual["secondary_warning"],
        "track_release_summary": {
            "visualization_status_release_count": 3,
            "physical_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
        },
        "static_and_physics_audit": {
            "v10t_object_count": len(v10t_objects),
            "v10t_keyframe_count": keyframe_count,
            "v10t_rigid_body_count": rigid_body_count,
            "v10t_particle_system_count": particle_system_count,
            "v10t_fluid_modifier_count": fluid_modifier_count,
            "created_scene_rigidbody_world_count": sum(1 for scene in created_scenes if scene.rigidbody_world is not None),
            "all_created_scenes_frame_1_only": all(scene.frame_start == 1 and scene.frame_end == 1 for scene in created_scenes),
            "structural_solver_executed": False,
            "thermal_solver_executed": False,
            "fire_solver_executed": False,
            "propagation_solver_executed": False,
            "collision_or_fracture_executed": False,
            "blender_physics_executed": False,
            "blender_used_as_physical_validation": False,
        },
        "runtime": {
            "elapsed_s": time.perf_counter() - started,
            "render_engine": visual["render_engine"],
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "network_access_used": False,
            "external_contact_made": False,
            "structural_solver_run_count": 0,
            "thermal_solver_run_count": 0,
            "fire_solver_run_count": 0,
            "propagation_solver_run_count": 0,
            "other_solver_run_count": 0,
            "gpu_compute_run_count": 0,
            "blender_run_count": 1,
        },
        "interpretation": "V10T renders only released software/reference/unknown statuses. The intact master geometry and Floors 93-99 frame are visual references, not a computed physical state. No collapse or non-collapse outcome is assigned.",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("V10T_BLENDER_MANIFEST=" + json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
