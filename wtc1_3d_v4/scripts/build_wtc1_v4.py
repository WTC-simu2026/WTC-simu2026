"""Build the WTC 1 V4 geometric reference model in Blender.

This script deliberately creates no collapse or impact physics.  Geometry tagged
as provisional or representative must not be interpreted as drawing-level truth.
Run with Blender 5.x in background mode.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Sequence

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parents[1]
PARAMS_PATH = PROJECT_DIR / "data" / "wtc1_parameters.json"
CORE_SCHEDULE_PATH = PROJECT_DIR / "data" / "core_sections_impact_zone.json"
OUTPUT_DIR = PROJECT_DIR / "output"
RENDER_DIR = PROJECT_DIR / "renders"
BLEND_PATH = OUTPUT_DIR / "WTC1_V4_2_MASTER.blend"
MANIFEST_PATH = OUTPUT_DIR / "model_manifest.json"
FT_TO_M = 0.3048


def load_parameters() -> dict:
    with PARAMS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_core_schedule() -> dict:
    with CORE_SCHEDULE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def scheduled_gross_area_in2(segment: dict) -> float:
    """Recover gross area while preserving the schedule as the authority."""
    if segment["kind"] == "BOX":
        return float(segment["gross_area_in2"])
    if segment["kind"] == "WF":
        nominal_weight_lb_ft = float(str(segment["shape"]).split("WF", 1)[1])
        steel_density_lb_in3 = 490.0 / 1728.0
        return nominal_weight_lb_ft / (steel_density_lb_in3 * 12.0)
    raise ValueError(f"Unsupported scheduled core section: {segment['kind']}")


P = load_parameters()
F = P["established_facts"]
H = P["model_hypotheses"]


def reset_blender() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def create_collection(name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(collection)
    return collection


def make_material(
    name: str,
    color: tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.45,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    node = material.node_tree.nodes.get("Principled BSDF")
    if node:
        node.inputs["Base Color"].default_value = color
        node.inputs["Metallic"].default_value = metallic
        node.inputs["Roughness"].default_value = roughness
        node.inputs["Alpha"].default_value = color[3]
        if emission_strength:
            emission_input = node.inputs.get("Emission Color") or node.inputs.get("Emission")
            if emission_input:
                emission_input.default_value = color
            strength_input = node.inputs.get("Emission Strength")
            if strength_input:
                strength_input.default_value = emission_strength
    return material


def box_geometry(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int, int]],
    center: Sequence[float],
    size: Sequence[float],
) -> None:
    cx, cy, cz = center
    sx, sy, sz = (value / 2.0 for value in size)
    start = len(vertices)
    vertices.extend(
        [
            (cx - sx, cy - sy, cz - sz),
            (cx + sx, cy - sy, cz - sz),
            (cx + sx, cy + sy, cz - sz),
            (cx - sx, cy + sy, cz - sz),
            (cx - sx, cy - sy, cz + sz),
            (cx + sx, cy - sy, cz + sz),
            (cx + sx, cy + sy, cz + sz),
            (cx - sx, cy + sy, cz + sz),
        ]
    )
    faces.extend(
        [
            (start + 0, start + 3, start + 2, start + 1),
            (start + 4, start + 5, start + 6, start + 7),
            (start + 0, start + 1, start + 5, start + 4),
            (start + 1, start + 2, start + 6, start + 5),
            (start + 2, start + 3, start + 7, start + 6),
            (start + 3, start + 0, start + 4, start + 7),
        ]
    )


def mesh_from_boxes(
    name: str,
    boxes: Iterable[tuple[Sequence[float], Sequence[float]]],
    collection: bpy.types.Collection,
    material: bpy.types.Material,
    properties: dict | None = None,
) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    count = 0
    for center, size in boxes:
        box_geometry(vertices, faces, center, size)
        count += 1
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj["primitive_box_count"] = count
    if properties:
        for key, value in properties.items():
            obj[key] = value
    return obj


def add_cube(
    name: str,
    center: Sequence[float],
    size: Sequence[float],
    collection: bpy.types.Collection,
    material: bpy.types.Material,
    properties: dict | None = None,
) -> bpy.types.Object:
    return mesh_from_boxes(name, [(center, size)], collection, material, properties)


def add_beam_between(
    name: str,
    start: Sequence[float],
    end: Sequence[float],
    width: float,
    collection: bpy.types.Collection,
    material: bpy.types.Material,
) -> bpy.types.Object:
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    midpoint = (start_v + end_v) / 2.0
    bpy.ops.mesh.primitive_cube_add(location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (width, width, direction.length)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def floor_schedule() -> tuple[dict[int, float], dict[int, float], float, float]:
    heights_ft: dict[int, float] = {}
    for entry in P["floor_height_schedule_ft"]:
        for floor in range(entry["from"], entry["to"] + 1):
            heights_ft[floor] = float(entry["height"])
    if set(heights_ft) != set(range(1, 111)):
        raise ValueError("The floor schedule must define floors 1 through 110 exactly once.")
    schedule_total_m = sum(heights_ft.values()) * FT_TO_M
    datum_offset_m = F["roof_height_target_m"] - schedule_total_m
    elevation_m: dict[int, float] = {1: datum_offset_m}
    for floor in range(2, 111):
        elevation_m[floor] = elevation_m[floor - 1] + heights_ft[floor - 1] * FT_TO_M
    roof_m = elevation_m[110] + heights_ft[110] * FT_TO_M
    return heights_ft, elevation_m, datum_offset_m, roof_m


def create_text(
    name: str,
    text: str,
    location: Sequence[float],
    rotation: Sequence[float],
    size: float,
    collection: bpy.types.Collection,
    material: bpy.types.Material,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_CURVE", "FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.size = size
    curve.extrude = size * 0.015
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    obj.rotation_euler = rotation
    curve.materials.append(material)
    collection.objects.link(obj)
    return obj


def add_camera(
    name: str,
    location: Sequence[float],
    target: Sequence[float],
    lens: float,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(f"{name}_DATA")
    camera_data.lens = lens
    camera_data.sensor_width = 36.0
    camera = bpy.data.objects.new(name, camera_data)
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(camera)
    return camera


def add_area_light(
    name: str,
    location: Sequence[float],
    energy: float,
    size: float,
    collection: bpy.types.Collection,
    target: Sequence[float],
) -> bpy.types.Object:
    light_data = bpy.data.lights.new(f"{name}_DATA", "AREA")
    light_data.energy = energy
    light_data.shape = "DISK"
    light_data.size = size
    light = bpy.data.objects.new(name, light_data)
    light.location = location
    light.rotation_euler = (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()
    collection.objects.link(light)
    return light


def add_sun_light(
    name: str,
    rotation_degrees: Sequence[float],
    energy: float,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    light_data = bpy.data.lights.new(f"{name}_DATA", "SUN")
    light_data.energy = energy
    light_data.angle = math.radians(8.0)
    light = bpy.data.objects.new(name, light_data)
    light.rotation_euler = tuple(math.radians(value) for value in rotation_degrees)
    collection.objects.link(light)
    return light


def configure_scene(scene: bpy.types.Scene) -> None:
    # Blender 5.2 exposes Eevee under BLENDER_EEVEE (the 4.x
    # BLENDER_EEVEE_NEXT identifier is no longer present).
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.fps = 30
    scene.render.fps_base = 1.0
    scene.view_settings.look = "AgX - Medium High Contrast"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("WTC1_WORLD")
    scene.world.color = (0.08, 0.11, 0.16)
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.075, 0.105, 0.15, 1.0)
        background.inputs["Strength"].default_value = 0.32
    scene["model_scope"] = P["model"]["scope"]
    scene["north_axis"] = P["model"]["north_axis"]
    scene["impact_physics"] = "NOT_IMPLEMENTED"
    scene["collapse_physics"] = "NOT_IMPLEMENTED"


def create_linked_production_scene(
    name: str,
    root_collection: bpy.types.Collection,
    source_scene: bpy.types.Scene,
    camera: bpy.types.Object,
    frame_end: int,
    timeline_scope: str,
) -> bpy.types.Scene:
    """Create a saved scene that shares the master model collection."""
    scene = bpy.data.scenes.new(name)
    scene.collection.children.link(root_collection)
    scene.render.engine = source_scene.render.engine
    scene.render.resolution_x = source_scene.render.resolution_x
    scene.render.resolution_y = source_scene.render.resolution_y
    scene.render.resolution_percentage = source_scene.render.resolution_percentage
    scene.render.image_settings.file_format = source_scene.render.image_settings.file_format
    scene.render.image_settings.color_mode = source_scene.render.image_settings.color_mode
    scene.render.film_transparent = source_scene.render.film_transparent
    scene.render.fps = source_scene.render.fps
    scene.render.fps_base = source_scene.render.fps_base
    scene.view_settings.look = source_scene.view_settings.look
    scene.world = source_scene.world
    scene.camera = camera
    scene.frame_start = 1
    scene.frame_end = frame_end
    scene["timeline_scope"] = timeline_scope
    scene["physics_status"] = "NOT_IMPLEMENTED"
    scene["shared_geometry_source"] = "WTC1_MASTER / WTC1_V4_2_MODEL"
    return scene


def set_render_visibility(objects: Iterable[bpy.types.Object], hidden: bool) -> None:
    for obj in objects:
        obj.hide_render = hidden


def render_preview(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    filename: str,
    hide: Iterable[bpy.types.Object] = (),
    resolution: tuple[int, int] | None = None,
) -> None:
    hidden = list(hide)
    old_resolution = (scene.render.resolution_x, scene.render.resolution_y)
    try:
        set_render_visibility(hidden, True)
        if resolution:
            scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.camera = camera
        scene.render.filepath = str(RENDER_DIR / filename)
        bpy.context.window.scene = scene
        bpy.ops.render.render(write_still=True)
    finally:
        set_render_visibility(hidden, False)
        scene.render.resolution_x, scene.render.resolution_y = old_resolution


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    reset_blender()
    scene = bpy.context.scene
    scene.name = "WTC1_MASTER"
    configure_scene(scene)
    core_schedule = load_core_schedule()

    heights_ft, elevations, datum_offset, roof_z = floor_schedule()
    tower_w = float(F["tower_width_m"])
    tower_d = float(F["tower_depth_m"])
    half_w = tower_w / 2.0
    half_d = tower_d / 2.0
    core_w = float(F["core_width_east_west_m"])
    core_d = float(F["core_depth_north_south_m"])
    core_half_w = core_w / 2.0
    core_half_d = core_d / 2.0
    base_z = 0.0
    full_height = roof_z - base_z
    column_width = float(F["perimeter_column_nominal_width_m"])
    column_depth = 0.36
    spacing = float(F["perimeter_column_spacing_m"])

    root = create_collection("WTC1_V4_2_MODEL")
    c_ref = create_collection("00_REFERENCE", root)
    c_global = create_collection("10_GLOBAL", root)
    c_perimeter = create_collection("20_PERIMETER", root)
    c_core = create_collection("30_CORE", root)
    c_core_schedule = create_collection("32_CORE_SECTIONS_92_101_SCHEDULED", c_core)
    c_floors = create_collection("40_FLOORS", root)
    c_zone = create_collection("50_ZONE_89_103", root)
    c_hat = create_collection("60_HAT_TRUSS", root)
    c_annotations = create_collection("70_ANNOTATIONS", root)
    c_core_plan = create_collection("75_CORE_LAYOUT_VALIDATION", root)
    c_paths = create_collection("80_PATHS", root)
    c_cameras = create_collection("90_CAMERAS_LIGHTS", root)

    mat_ground = make_material("MAT_GROUND", (0.055, 0.075, 0.085, 1.0), metallic=0.05, roughness=0.82)
    mat_glass = make_material("MAT_GLASS_REFERENCE", (0.055, 0.16, 0.22, 0.62), metallic=0.45, roughness=0.24)
    mat_perimeter = make_material("MAT_PERIMETER_STEEL", (0.72, 0.77, 0.81, 1.0), metallic=0.82, roughness=0.26)
    mat_spandrel = make_material("MAT_SPANDREL", (0.34, 0.40, 0.45, 1.0), metallic=0.74, roughness=0.31)
    mat_concrete = make_material("MAT_FLOOR_SLAB", (0.37, 0.41, 0.43, 1.0), metallic=0.0, roughness=0.72)
    core_row_colors = {
        500: (0.98, 0.38, 0.12, 1.0),
        600: (0.98, 0.68, 0.10, 1.0),
        700: (0.55, 0.82, 0.16, 1.0),
        800: (0.10, 0.72, 0.78, 1.0),
        900: (0.23, 0.48, 0.96, 1.0),
        1000: (0.67, 0.31, 0.94, 1.0),
    }
    mat_core_rows = {
        row: make_material(f"MAT_CORE_ROW_{row}", color, metallic=0.48, roughness=0.30, emission_strength=0.18)
        for row, color in core_row_colors.items()
    }
    core_grade_colors = {
        36: (0.18, 0.48, 0.96, 1.0),
        42: (0.10, 0.78, 0.62, 1.0),
        45: (0.96, 0.68, 0.08, 1.0),
        50: (0.96, 0.20, 0.12, 1.0),
    }
    mat_core_grades = {
        fy: make_material(f"MAT_CORE_FY_{fy}_KSI", color, metallic=0.62, roughness=0.25, emission_strength=0.28)
        for fy, color in core_grade_colors.items()
    }
    mat_core_plate = make_material("MAT_CORE_PLAN_PLATE", (0.025, 0.040, 0.060, 1.0), metallic=0.08, roughness=0.70)
    mat_zone = make_material("MAT_ZONE_89_103", (0.15, 0.62, 0.90, 1.0), metallic=0.56, roughness=0.28)
    mat_impact = make_material("MAT_IMPACT_REFERENCE", (0.96, 0.055, 0.025, 0.72), metallic=0.05, roughness=0.30, emission_strength=1.25)
    mat_annotation = make_material("MAT_ANNOTATION", (0.96, 0.83, 0.18, 1.0), metallic=0.0, roughness=0.45, emission_strength=0.7)
    mat_hat = make_material("MAT_HAT_TRUSS_REFERENCE", (0.63, 0.28, 0.91, 1.0), metallic=0.55, roughness=0.30)

    ground = add_cube("GROUND_REFERENCE", (0, 0, -0.35), (360, 360, 0.7), c_ref, mat_ground)
    ground["status"] = "REFERENCE_ONLY"
    glass = add_cube(
        "FACADE_GLASS_REFERENCE",
        (0, 0, full_height / 2.0),
        (tower_w - 0.72, tower_d - 0.72, full_height),
        c_global,
        mat_glass,
        {"status": "VISUAL_ENVELOPE_ONLY"},
    )

    # Exactly 59 column centerlines on each face.  Corners belong to only one
    # face family geometrically, preserving a validation count of 236 members.
    centers = [(index - 29) * spacing for index in range(59)]
    perimeter_faces: dict[str, bpy.types.Object] = {}
    for face_name, boxes in {
        "NORTH": [((x, half_d - column_depth / 2.0, full_height / 2.0), (column_width, column_depth, full_height)) for x in centers],
        "SOUTH": [((x, -half_d + column_depth / 2.0, full_height / 2.0), (column_width, column_depth, full_height)) for x in centers],
        "EAST": [((half_w - column_depth / 2.0, y, full_height / 2.0), (column_depth, column_width, full_height)) for y in centers],
        "WEST": [((-half_w + column_depth / 2.0, y, full_height / 2.0), (column_depth, column_width, full_height)) for y in centers],
    }.items():
        perimeter_faces[face_name] = mesh_from_boxes(
            f"PERIMETER_COLUMNS_{face_name}",
            boxes,
            c_perimeter,
            mat_perimeter,
            {"status": "COUNT_AND_SPACING_REFERENCE", "column_count": 59, "face": face_name},
        )

    spandrel_h = float(F["spandrel_nominal_height_m"])
    spandrel_t = 0.22
    spandrel_faces: dict[str, bpy.types.Object] = {}
    face_box_sets: dict[str, list[tuple[Sequence[float], Sequence[float]]]] = {key: [] for key in perimeter_faces}
    for floor in range(2, 111):
        z = elevations[floor]
        face_box_sets["NORTH"].append(((0, half_d - spandrel_t / 2.0, z), (tower_w, spandrel_t, spandrel_h)))
        face_box_sets["SOUTH"].append(((0, -half_d + spandrel_t / 2.0, z), (tower_w, spandrel_t, spandrel_h)))
        face_box_sets["EAST"].append(((half_w - spandrel_t / 2.0, 0, z), (spandrel_t, tower_d, spandrel_h)))
        face_box_sets["WEST"].append(((-half_w + spandrel_t / 2.0, 0, z), (spandrel_t, tower_d, spandrel_h)))
    for face_name, boxes in face_box_sets.items():
        spandrel_faces[face_name] = mesh_from_boxes(
            f"SPANDRELS_{face_name}", boxes, c_perimeter, mat_spandrel, {"status": "REPRESENTATIVE_BANDS", "face": face_name}
        )

    slab_t = float(F["floor_slab_visual_thickness_m"])
    slab_boxes: list[tuple[Sequence[float], Sequence[float]]] = []
    clear_x = (tower_w - core_w) / 2.0
    clear_y = (tower_d - core_d) / 2.0
    for floor in range(1, 111):
        z = elevations[floor]
        slab_boxes.extend(
            [
                ((0, core_half_d + clear_y / 2.0, z), (tower_w - 0.8, clear_y, slab_t)),
                ((0, -core_half_d - clear_y / 2.0, z), (tower_w - 0.8, clear_y, slab_t)),
                ((core_half_w + clear_x / 2.0, 0, z), (clear_x, core_d, slab_t)),
                ((-core_half_w - clear_x / 2.0, 0, z), (clear_x, core_d, slab_t)),
            ]
        )
    floors_obj = mesh_from_boxes(
        "FLOOR_SLABS_WITH_CORE_OPENING",
        slab_boxes,
        c_floors,
        mat_concrete,
        {"status": "GEOMETRIC_REFERENCE", "floor_count": 110, "core_opening": True},
    )

    # The 47 identifiers and their relative topology are official NIST data.
    # Metric centres are digitized from the un-dimensioned NIST Figure 2-2 and
    # scaled to the published 135 ft x 87 ft core envelope.  They are therefore
    # explicitly tagged as reconstructed coordinates, not drawing-level truth.
    layout = P["core_layout_reconstruction"]
    core_columns = layout["columns"]
    if len(core_columns) != int(H["core_column_count"]):
        raise ValueError("The reconstructed core layout must contain exactly 47 columns.")
    core_section = H["core_column_visual_section_m"]
    core_row_objects: list[bpy.types.Object] = []
    scheduled_bottom_z = elevations[92]
    scheduled_top_z = elevations[101]
    for row in sorted(core_row_colors):
        row_columns = [column for column in core_columns if int(column["row"]) == row]
        # Full-height placeholders are retained only outside the zone for which
        # actual schedules have been transcribed.  This avoids hiding the
        # section-derived proxies inside a much larger generic prism.
        row_boxes = []
        for column in row_columns:
            x = float(column["x_m"])
            y = float(column["y_m"])
            row_boxes.extend(
                [
                    ((x, y, scheduled_bottom_z / 2.0), (core_section[0], core_section[1], scheduled_bottom_z)),
                    (
                        (x, y, (scheduled_top_z + roof_z) / 2.0),
                        (core_section[0], core_section[1], roof_z - scheduled_top_z),
                    ),
                ]
            )
        row_obj = mesh_from_boxes(
            f"CORE_COLUMNS_ROW_{row}_OUTSIDE_SCHEDULED_ZONE",
            row_boxes,
            c_core,
            mat_core_rows[row],
            {
                "topology_status": layout["topology_status"],
                "metric_coordinate_status": layout["metric_coordinate_status"],
                "coordinate_tolerance_m": float(layout["estimated_plan_tolerance_m"]),
                "section_status": "VISUAL_PLACEHOLDER_OUTSIDE_FLOORS_92_101",
                "column_count": len(row_columns),
                "column_ids": ",".join(str(column["id"]) for column in row_columns),
                "source": layout["source"],
            },
        )
        core_row_objects.append(row_obj)

    schedule_by_id = {int(column["id"]): column for column in core_schedule["columns"]}
    if set(schedule_by_id) != {int(column["id"]) for column in core_columns}:
        raise ValueError("The core schedule and reconstructed layout must contain the same 47 identifiers.")
    scheduled_core_objects: list[bpy.types.Object] = []
    scheduled_bands = (("95-92", 92, 95), ("98-95", 95, 98), ("101-98", 98, 101))
    for column in core_columns:
        column_id = int(column["id"])
        schedule_column = schedule_by_id[column_id]
        for band, floor_low, floor_high in scheduled_bands:
            segment = schedule_column["segments"][band]
            area_in2 = scheduled_gross_area_in2(segment)
            # A square of identical gross area makes the inventory visible
            # without pretending that the full historic WF outline is known.
            equivalent_side_m = math.sqrt(area_in2) * 0.0254
            z_low = elevations[floor_low]
            z_high = elevations[floor_high]
            fy = int(segment["fy_ksi"])
            designation = segment.get("shape", f"BOX-{segment.get('column_type')}")
            obj = add_cube(
                f"CORE_{column_id}_{band.replace('-', '_')}_{designation}_AREA_PROXY",
                (float(column["x_m"]), float(column["y_m"]), (z_low + z_high) / 2.0),
                (equivalent_side_m, equivalent_side_m, z_high - z_low),
                c_core_schedule,
                mat_core_grades[fy],
                {
                    "status": "SCHEDULED_GROSS_AREA_EQUIVALENT_SQUARE_NOT_EXACT_PROFILE",
                    "column_id": column_id,
                    "splice_band": band,
                    "floor_low": floor_low,
                    "floor_high": floor_high,
                    "designation": designation,
                    "section_kind": segment["kind"],
                    "fy_ksi": fy,
                    "gross_area_in2": area_in2,
                    "source_sheet": schedule_column["sheet"],
                    "source_pdf_page": int(schedule_column["pdf_page"]),
                    "source_dataset": core_schedule["dataset"]["source"],
                    "transcription_status": core_schedule["dataset"]["transcription_status"],
                },
            )
            scheduled_core_objects.append(obj)

    # Simplified load-path lines in the detailed zone.  They represent nominal
    # truss spacing and direction only, not member section or connection detail.
    truss_boxes: list[tuple[Sequence[float], Sequence[float]]] = []
    truss_spacing = float(F["floor_truss_spacing_m"])
    chord_width = 0.09
    north_south_span = half_d - core_half_d - 0.58
    east_west_span = half_w - core_half_w - 0.58
    x_line_count = int(math.floor((tower_w - 1.2) / truss_spacing)) + 1
    y_line_count = int(math.floor((tower_d - 1.2) / truss_spacing)) + 1
    x_lines = [(i - (x_line_count - 1) / 2.0) * truss_spacing for i in range(x_line_count)]
    y_lines = [(i - (y_line_count - 1) / 2.0) * truss_spacing for i in range(y_line_count)]
    for floor in range(F["detailed_floor_range"][0], F["detailed_floor_range"][1] + 1):
        z = elevations[floor] - 0.32
        for x in x_lines:
            truss_boxes.append(((x, core_half_d + north_south_span / 2.0, z), (chord_width, north_south_span, chord_width)))
            truss_boxes.append(((x, -core_half_d - north_south_span / 2.0, z), (chord_width, north_south_span, chord_width)))
        for y in y_lines:
            truss_boxes.append(((core_half_w + east_west_span / 2.0, y, z), (east_west_span, chord_width, chord_width)))
            truss_boxes.append(((-core_half_w - east_west_span / 2.0, y, z), (east_west_span, chord_width, chord_width)))
    zone_obj = mesh_from_boxes(
        "FLOOR_LOAD_PATHS_89_103_REPRESENTATIVE",
        truss_boxes,
        c_zone,
        mat_zone,
        {
            "status": "REPRESENTATIVE_NOT_SOLVER_READY",
            "warning": H["floor_trusses_status"],
            "floor_from": F["detailed_floor_range"][0],
            "floor_to": F["detailed_floor_range"][1],
            "nominal_spacing_m": truss_spacing,
        },
    )

    # Impact reference volume on the north facade (visual marker only).
    impact_low = elevations[F["impact_floor_range"][0]] - 0.65
    impact_high = elevations[F["impact_floor_range"][1] + 1] + 0.65
    impact_width = 37.0
    impact_height = impact_high - impact_low
    impact_border = 0.72
    impact_y = half_d + 0.55
    impact_obj = mesh_from_boxes(
        "IMPACT_ZONE_NORTH_FLOORS_93_99_REFERENCE",
        [
            ((0, impact_y, impact_low), (impact_width, 0.42, impact_border)),
            ((0, impact_y, impact_high), (impact_width, 0.42, impact_border)),
            ((-impact_width / 2.0, impact_y, (impact_low + impact_high) / 2.0), (impact_border, 0.42, impact_height)),
            ((impact_width / 2.0, impact_y, (impact_low + impact_high) / 2.0), (impact_border, 0.42, impact_height)),
        ],
        c_zone,
        mat_impact,
        {
            "status": "VISUAL_REFERENCE_ONLY",
            "warning": H["impact_volume_status"],
            "face": "NORTH",
            "floor_from": 93,
            "floor_to": 99,
        },
    )

    # Reference flight path: direction only, deliberately not animated.
    path_z = (elevations[95] + elevations[96]) / 2.0
    path_curve = bpy.data.curves.new("AA11_PATH_REFERENCE_CURVE", "CURVE")
    path_curve.dimensions = "3D"
    path_curve.bevel_depth = 0.32
    path_curve.bevel_resolution = 2
    spline = path_curve.splines.new("POLY")
    spline.points.add(2)
    for point, coordinate in zip(
        spline.points,
        [(-55.0, 230.0, path_z + 8.0, 1.0), (-22.0, 110.0, path_z + 3.0, 1.0), (0.0, half_d, path_z, 1.0)],
    ):
        point.co = coordinate
    path_curve.materials.append(mat_impact)
    path_obj = bpy.data.objects.new("AA11_APPROACH_PATH_REFERENCE", path_curve)
    path_obj["status"] = "DIRECTION_REFERENCE_ONLY"
    path_obj["velocity"] = "NOT_ASSIGNED"
    c_paths.objects.link(path_obj)

    # Hat-truss placeholder: only the overall load-path volume is shown.
    hat_bottom = elevations[107]
    hat_top = roof_z - 1.0
    hat_members = [
        ((-core_half_w + 1.0, -core_half_d + 1.0, hat_bottom), (core_half_w - 1.0, core_half_d - 1.0, hat_top)),
        ((core_half_w - 1.0, -core_half_d + 1.0, hat_bottom), (-core_half_w + 1.0, core_half_d - 1.0, hat_top)),
        ((-core_half_w + 1.0, core_half_d - 1.0, hat_bottom), (core_half_w - 1.0, -core_half_d + 1.0, hat_top)),
        ((core_half_w - 1.0, core_half_d - 1.0, hat_bottom), (-core_half_w + 1.0, -core_half_d + 1.0, hat_top)),
    ]
    for index, (start, end) in enumerate(hat_members, 1):
        member = add_beam_between(f"HAT_TRUSS_PLACEHOLDER_{index:02d}", start, end, 0.38, c_hat, mat_hat)
        member["status"] = "PLACEHOLDER_OVERALL_VOLUME_ONLY"

    # Low-poly antenna and mast reference.
    mast_base = roof_z
    mast_top = float(F["antenna_top_m"])
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.15, depth=mast_top - mast_base, location=(0, 0, (mast_top + mast_base) / 2.0))
    mast = bpy.context.object
    mast.name = "ANTENNA_MAST_REFERENCE"
    for old_collection in list(mast.users_collection):
        old_collection.objects.unlink(mast)
    c_global.objects.link(mast)
    mast.data.materials.append(mat_perimeter)
    mast["status"] = "LOW_POLY_REFERENCE"

    # Dedicated top-down validation board.  It is hidden from the exterior and
    # structural previews and exists only to make all 47 identifiers auditable.
    plan_z = roof_z + 1.0
    plan_validation_objects: list[bpy.types.Object] = []
    plate = add_cube(
        "CORE_LAYOUT_VALIDATION_PLATE",
        (0, 0, plan_z),
        (53.0, 40.0, 0.16),
        c_core_plan,
        mat_core_plate,
        {
            "status": "VALIDATION_VIEW_ONLY",
            "source": layout["source"],
            "coordinate_tolerance_m": float(layout["estimated_plan_tolerance_m"]),
        },
    )
    plan_validation_objects.append(plate)
    outline_t = 0.16
    outline_z = plan_z + 0.10
    for name, center, size in [
        ("CORE_PLAN_BORDER_NORTH", (0, core_half_d, outline_z), (core_w, outline_t, 0.10)),
        ("CORE_PLAN_BORDER_SOUTH", (0, -core_half_d, outline_z), (core_w, outline_t, 0.10)),
        ("CORE_PLAN_BORDER_EAST", (core_half_w, 0, outline_z), (outline_t, core_d, 0.10)),
        ("CORE_PLAN_BORDER_WEST", (-core_half_w, 0, outline_z), (outline_t, core_d, 0.10)),
    ]:
        plan_validation_objects.append(add_cube(name, center, size, c_core_plan, mat_annotation))

    marker_z = plan_z + 0.22
    for row in sorted(core_row_colors):
        row_columns = [column for column in core_columns if int(column["row"]) == row]
        markers = mesh_from_boxes(
            f"CORE_PLAN_MARKERS_ROW_{row}",
            [
                ((float(column["x_m"]), float(column["y_m"]), marker_z), (0.64, 0.64, 0.18))
                for column in row_columns
            ],
            c_core_plan,
            mat_core_rows[row],
            {"status": "VALIDATION_MARKERS_ONLY", "row": row, "column_count": len(row_columns)},
        )
        plan_validation_objects.append(markers)
        for column in row_columns:
            label = create_text(
                f"CORE_PLAN_LABEL_{column['id']}",
                str(column["id"]),
                (float(column["x_m"]), float(column["y_m"]) - 0.76, marker_z + 0.13),
                (0, 0, 0),
                0.50,
                c_core_plan,
                mat_core_rows[row],
            )
            label["status"] = "OFFICIAL_IDENTIFIER_ON_RECONSTRUCTED_POSITION"
            plan_validation_objects.append(label)

    plan_validation_objects.append(
        create_text(
            "CORE_PLAN_NORTH_LABEL",
            "NORTH  +Y",
            (0, 17.55, marker_z + 0.13),
            (0, 0, 0),
            0.86,
            c_core_plan,
            mat_annotation,
        )
    )
    plan_validation_objects.append(
        create_text(
            "CORE_PLAN_STATUS_LABEL",
            "WTC 1 CORE  |  OFFICIAL IDS  |  RECONSTRUCTED COORDINATES +/- 0.30 m",
            (0, -18.15, marker_z + 0.13),
            (0, 0, 0),
            0.72,
            c_core_plan,
            mat_annotation,
        )
    )

    # Scale / orientation annotations.
    label_north = create_text("LABEL_NORTH", "NORTH  +Y", (0, 67, 0.15), (0, 0, 0), 4.2, c_annotations, mat_annotation)
    label_model_status = create_text(
        "LABEL_MODEL_STATUS",
        "WTC 1 V4.2  |  SCHEDULED CORE AREA PROXIES 92-101  |  NO COLLAPSE PHYSICS",
        (0, -72, 0.16),
        (0, 0, 0),
        2.5,
        c_annotations,
        mat_annotation,
    )

    zone_mid_z = (elevations[89] + elevations[103]) / 2.0
    cam_exterior = add_camera("CAM_EXTERIOR", (540, -650, 345), (0, 0, 224), 56, c_cameras)
    cam_cutaway = add_camera("CAM_STRUCTURE_89_103", (145, -165, zone_mid_z + 25), (0, 0, zone_mid_z), 58, c_cameras)
    cam_impact = add_camera("CAM_IMPACT_NORTH", (0, 195, zone_mid_z + 4), (0, half_d, zone_mid_z), 67, c_cameras)
    scheduled_mid_z = (scheduled_bottom_z + scheduled_top_z) / 2.0
    cam_core_sections = add_camera(
        "CAM_CORE_SECTIONS_92_101",
        (82, -108, scheduled_mid_z + 17),
        (0, 0, scheduled_mid_z),
        58,
        c_cameras,
    )
    cam_core_plan = add_camera("CAM_CORE_LAYOUT_TOP", (0, 0, roof_z + 85), (0, 0, plan_z), 50, c_cameras)
    cam_core_plan.data.type = "ORTHO"
    # Blender's orthographic scale follows the horizontal extent for this
    # landscape render; 60 m leaves room for edge labels and the status legend.
    cam_core_plan.data.ortho_scale = 60.0
    add_sun_light("SUN_KEY", (24, -28, -32), 2.4, c_cameras)
    add_area_light("KEY_LIGHT", (260, -300, 510), 150000, 210, c_cameras, (0, 0, 230))
    add_area_light("FILL_LIGHT", (-260, 180, 360), 90000, 180, c_cameras, (0, 0, 270))
    add_area_light("ZONE_LIGHT", (0, 120, zone_mid_z + 80), 65000, 105, c_cameras, (0, 0, zone_mid_z))

    scene.camera = cam_exterior
    scene["schedule_total_m"] = sum(heights_ft.values()) * FT_TO_M
    scene["datum_offset_m"] = datum_offset
    scene["roof_height_m"] = roof_z
    scene["perimeter_column_count"] = sum(obj["column_count"] for obj in perimeter_faces.values())
    scene["core_column_count"] = sum(obj["column_count"] for obj in core_row_objects)
    scene["core_layout_topology_status"] = layout["topology_status"]
    scene["core_metric_coordinate_status"] = layout["metric_coordinate_status"]
    scene["core_coordinate_tolerance_m"] = float(layout["estimated_plan_tolerance_m"])
    scene["core_scheduled_section_proxy_count"] = len(scheduled_core_objects)
    scene["core_scheduled_floor_from"] = 92
    scene["core_scheduled_floor_to"] = 101
    scene["core_scheduled_section_status"] = H["core_section_zone_status"]
    scene["detailed_floor_from"] = 89
    scene["detailed_floor_to"] = 103

    # Preview 1: full exterior.  Impact marker is hidden to keep this a clean
    # dimensional reference view.
    render_preview(
        scene,
        cam_exterior,
        "wtc1_v4_2_exterior.png",
        hide=[impact_obj, path_obj, *plan_validation_objects],
    )

    # Preview 2: south-east cutaway around the detailed zone.
    render_preview(
        scene,
        cam_cutaway,
        "wtc1_v4_2_structure_89_103.png",
        hide=[
            glass,
            perimeter_faces["SOUTH"],
            perimeter_faces["EAST"],
            spandrel_faces["SOUTH"],
            spandrel_faces["EAST"],
            impact_obj,
            path_obj,
            *plan_validation_objects,
        ],
    )

    # Preview 3: explicit north-face impact reference.
    render_preview(
        scene,
        cam_impact,
        "wtc1_v4_2_impact_north_reference.png",
        hide=plan_validation_objects,
    )

    # Preview 4: the 141 schedule-derived gross-area proxies, isolated so that
    # their section and grade changes remain legible through the floor plates.
    core_sections_hide = [
        obj
        for obj in bpy.data.objects
        if obj not in scheduled_core_objects and obj.type not in {"CAMERA", "LIGHT"}
    ]
    render_preview(
        scene,
        cam_core_sections,
        "wtc1_v4_2_core_sections_92_101.png",
        hide=core_sections_hide,
        resolution=(1200, 900),
    )

    # Preview 5: isolated plan of the reconstructed NIST core layout.
    top_view_hide = [
        obj
        for obj in bpy.data.objects
        if obj not in plan_validation_objects and obj.type not in {"CAMERA", "LIGHT"}
    ]
    render_preview(
        scene,
        cam_core_plan,
        "wtc1_v4_2_core_layout_validation.png",
        hide=top_view_hide,
        resolution=(1400, 1000),
    )
    scene.camera = cam_exterior
    scene.render.filepath = ""

    # Separate production scenes share the same geometry but have independent
    # timelines.  Nothing is animated or simulated at this milestone.
    impact_scene = create_linked_production_scene(
        "IMPACT_SEGMENT", root, scene, cam_impact, 360, "12 seconds at 30 fps; animation not implemented"
    )
    collapse_scene = create_linked_production_scene(
        "COLLAPSE_SEGMENT", root, scene, cam_cutaway, 1800, "60 seconds at 30 fps; animation not implemented"
    )

    bpy.context.window.scene = scene
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    total_vertices = sum(len(obj.data.vertices) for obj in mesh_objects)
    total_polygons = sum(len(obj.data.polygons) for obj in mesh_objects)
    manifest = {
        "model": P["model"],
        "validation": {
            "perimeter_columns_expected": 236,
            "perimeter_columns_created": scene["perimeter_column_count"],
            "core_columns_created": scene["core_column_count"],
            "core_rows_created": {str(row): sum(1 for column in core_columns if int(column["row"]) == row) for row in sorted(core_row_colors)},
            "core_topology_status": layout["topology_status"],
            "core_identifier_status": layout["identifier_status"],
            "core_metric_coordinate_status": layout["metric_coordinate_status"],
            "core_coordinate_tolerance_m": float(layout["estimated_plan_tolerance_m"]),
            "core_scheduled_section_proxy_count": len(scheduled_core_objects),
            "core_scheduled_column_ids": len(schedule_by_id),
            "core_scheduled_splice_band_count": len(scheduled_bands),
            "core_schedule_transcription_status": core_schedule["dataset"]["transcription_status"],
            "floors_created": floors_obj["floor_count"],
            "roof_height_target_m": F["roof_height_target_m"],
            "roof_height_created_m": roof_z,
            "floor_schedule_total_m": scene["schedule_total_m"],
            "datum_offset_m": datum_offset,
            "mesh_object_count": len(mesh_objects),
            "total_vertices": total_vertices,
            "total_polygons": total_polygons,
            "detailed_zone_primitive_count": zone_obj["primitive_box_count"],
        },
        "scenes": {
            "WTC1_MASTER": "Geometric master and exterior camera",
            "IMPACT_SEGMENT": "12 s / 30 fps placeholder; no physics",
            "COLLAPSE_SEGMENT": "60 s / 30 fps placeholder; no physics",
        },
        "outputs": {
            "blend": str(BLEND_PATH),
            "renders": [
                str(RENDER_DIR / "wtc1_v4_2_exterior.png"),
                str(RENDER_DIR / "wtc1_v4_2_structure_89_103.png"),
                str(RENDER_DIR / "wtc1_v4_2_impact_north_reference.png"),
                str(RENDER_DIR / "wtc1_v4_2_core_sections_92_101.png"),
                str(RENDER_DIR / "wtc1_v4_2_core_layout_validation.png"),
            ],
        },
        "warnings": [
            H["core_layout_status"],
            H["core_section_zone_status"],
            H["floor_trusses_status"],
            H["facade_status"],
            H["impact_volume_status"],
        ],
    }
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    print("WTC1 V4.2 build complete")
    print(json.dumps(manifest["validation"], indent=2))


if __name__ == "__main__":
    main()
