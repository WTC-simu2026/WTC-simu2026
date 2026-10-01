#!/usr/bin/env python3
"""V9U - categorical stairwell stack for Floors 93-99.

Only the V9R floor-band continuity and transfer topology are used to decide
whether the hypothetical V9T Floor 95 placements may be repeated as labelled
categorical placeholders.  The output has no physical vertical scale, no
floor-specific as-built geometry and no mechanical or damage credit.  No
solver or Blender process is invoked.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9u_floor93_99_categorical_stairwell_stack.json"
V9T_LAYER_PATH = ROOT / "wtc1_simulation_v8/output/v9t_floor95_stairwell_layer.json"
V9R_TOPOLOGY_PATH = ROOT / "wtc1_simulation_v8/output/v9r_stairwell_topology.json"
V9R_FLOOR_MATRIX_PATH = ROOT / "wtc1_simulation_v8/output/v9r_stairwell_floor_matrix.csv"
WARNING = (
    "V9U - PILE CATEGORIELLE HYPOTHETIQUE - AUCUNE GEOMETRIE AS-BUILT - "
    "ZERO CREDIT MECANIQUE"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def resolve_map(mapping: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path, expected_hash in mapping.items():
        path = ROOT / relative_path
        exists = path.is_file()
        observed = sha256(path) if exists else None
        rows.append(
            {
                "path": relative_path,
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else None,
                "expected_sha256": expected_hash,
                "observed_sha256": observed,
                "pass": exists and observed == expected_hash,
            }
        )
    return rows


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"Expected boolean text, received {value!r}")


def read_floor_matrix(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for source in csv.DictReader(handle):
            rows.append(
                {
                    "floor": int(source["floor"]),
                    "stair_alias": source["stair_alias"],
                    "v9q_numeric_alias": int(source["v9q_numeric_alias"]),
                    "present_in_reported_vertical_extent": parse_bool(
                        source["present_in_reported_vertical_extent"]
                    ),
                    "service_status": source["service_status"],
                    "floor_band_layout": source["floor_band_layout"],
                    "table_2_2_panel_present": parse_bool(source["table_2_2_panel_present"]),
                    "transfer_event": source["transfer_event"],
                    "core_relation": source["core_relation"],
                    "clear_width_in": float(source["clear_width_in"]),
                    "landing_width_in": float(source["landing_width_in"]),
                    "landing_depth_in": float(source["landing_depth_in"]),
                    "floor_95_labelled_overlay": parse_bool(source["floor_95_labelled_overlay"]),
                    "qualitative_floor_95_position": source["qualitative_floor_95_position"],
                    "inherited_damage_evidence": source["inherited_damage_evidence"],
                    "exact_metric_plan_coordinates_qualified": parse_bool(
                        source["exact_metric_plan_coordinates_qualified"]
                    ),
                    "flight_and_stringer_geometry_qualified": parse_bool(
                        source["flight_and_stringer_geometry_qualified"]
                    ),
                    "connections_qualified": parse_bool(source["connections_qualified"]),
                    "discrete_mass_qualified": parse_bool(source["discrete_mass_qualified"]),
                    "stiffness_qualified": parse_bool(source["stiffness_qualified"]),
                    "strength_qualified": parse_bool(source["strength_qualified"]),
                    "load_path_credit_qualified": parse_bool(
                        source["load_path_credit_qualified"]
                    ),
                }
            )
    return rows


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_variant_stack(
    output: Path,
    variant: str,
    floors: list[int],
    floor_summaries: dict[int, dict[str, Any]],
    variant_instances: list[dict[str, Any]],
) -> None:
    image = Image.new("RGB", (1500, 1320), "white")
    draw = ImageDraw.Draw(image)
    warning_font = load_font(21, bold=True)
    title_font = load_font(30, bold=True)
    header_font = load_font(21, bold=True)
    body_font = load_font(18)
    small_font = load_font(15)
    colors = {"A": (205, 45, 45), "C": (143, 61, 184), "B": (31, 132, 72)}

    draw.rectangle((0, 0, image.width, 48), fill=(145, 0, 0))
    draw.text((14, 11), WARNING, fill="white", font=warning_font)
    draw.text(
        (48, 66),
        f"V9U - variante {variant.upper()} - niveaux 93 a 99",
        fill=(0, 0, 0),
        font=title_font,
    )
    draw.text(
        (48, 104),
        "Axe vertical ordinal seulement | espacement d'affichage sans echelle physique",
        fill=(145, 0, 0),
        font=header_font,
    )

    by_floor: dict[int, list[dict[str, Any]]] = {}
    for instance in variant_instances:
        by_floor.setdefault(instance["floor"], []).append(instance)

    row_top = 145
    row_height = 154
    panel_left = 105
    panel_size = 124
    coordinate_scale = panel_size / 1000.0
    previous_layout: str | None = None
    for display_index, floor in enumerate(sorted(floors, reverse=True)):
        y = row_top + display_index * row_height
        summary = floor_summaries[floor]
        layout = summary["floor_band_layout"]
        if previous_layout is not None and layout != previous_layout:
            draw.line((45, y - 8, 1455, y - 8), fill=(35, 85, 165), width=5)
            draw.text((1180, y - 33), "FRONTIERE DE BANDE", fill=(35, 85, 165), font=small_font)
        previous_layout = layout

        draw.rectangle((45, y, 1455, y + 136), fill=(248, 248, 248), outline=(95, 95, 95), width=2)
        draw.text((58, y + 48), f"F{floor}", fill=(0, 0, 0), font=header_font)
        draw.rectangle(
            (panel_left, y + 6, panel_left + panel_size, y + 130),
            fill="white",
            outline=(35, 35, 35),
            width=2,
        )
        for instance in sorted(by_floor[floor], key=lambda item: ("A", "C", "B").index(item["stair"])):
            bounds = instance["bounds_common_px"]
            box = (
                panel_left + bounds["min_x"] * coordinate_scale,
                y + 6 + bounds["min_y"] * coordinate_scale,
                panel_left + bounds["max_x"] * coordinate_scale,
                y + 6 + bounds["max_y"] * coordinate_scale,
            )
            draw.rectangle(box, fill=colors[instance["stair"]], outline=(20, 20, 20), width=1)

        source_label = (
            "F95: ajustement V9T hypothetique, figure officielle en amont"
            if floor == 95
            else "REPÉTITION CATEGORIELLE HYPOTHETIQUE DE F95"
        )
        draw.text((252, y + 12), source_label, fill=(145, 0, 0), font=header_font)
        draw.text((252, y + 47), layout, fill=(20, 20, 20), font=body_font)
        draw.text(
            (252, y + 77),
            "3 escaliers: CONTINUES | transfert: NONE | geometrie as-built observee: NON",
            fill=(35, 35, 35),
            font=body_font,
        )
        draw.text(
            (252, y + 105),
            "masse = rigidite = resistance = connexion = chemin de charge = credit dommage = 0",
            fill=(90, 0, 0),
            font=small_font,
        )

    draw.text(
        (48, 1245),
        "Les coordonnees 2D identiques facilitent la comparaison visuelle; elles n'affirment pas une identite geometrique reelle entre etages.",
        fill=(0, 0, 0),
        font=body_font,
    )
    draw.text(
        (48, 1276),
        "Aucun z physique, aucune hauteur d'etage, aucun solveur et aucun processus Blender.",
        fill=(145, 0, 0),
        font=header_font,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")


def make_contact_sheet(variant_paths: dict[str, Path], output: Path, variant_order: list[str]) -> None:
    image = Image.new("RGB", (1860, 760), (235, 235, 235))
    draw = ImageDraw.Draw(image)
    warning_font = load_font(19, bold=True)
    title_font = load_font(24, bold=True)
    draw.rectangle((0, 0, image.width, 44), fill=(145, 0, 0))
    draw.text((12, 10), WARNING, fill="white", font=warning_font)
    for index, variant in enumerate(variant_order):
        x = 15 + index * 615
        draw.rectangle((x, 55, x + 595, 742), fill="white", outline=(40, 40, 40), width=2)
        draw.text((x + 14, 66), variant.upper(), fill=(0, 0, 0), font=title_font)
        with Image.open(variant_paths[variant]) as source:
            tile = source.convert("RGB")
            tile.thumbnail((570, 635), Image.Resampling.LANCZOS)
        image.paste(tile, (x + 12 + (570 - tile.width) // 2, 98))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "variant",
        "floor",
        "categorical_level_index",
        "stair",
        "floor_band_layout",
        "table_2_2_panel_present",
        "service_status",
        "transfer_event",
        "floor_95_labelled_overlay_available",
        "placement_status",
        "hypothetical_placement",
        "copy_of_floor95_display_coordinates",
        "geometry_identity_across_floors_asserted",
        "observed_as_built_geometry",
        "physical_vertical_scale_assigned",
        "physical_z_m",
        "common_relative_scale_common_px_per_published_in",
        "min_x_common_px",
        "min_y_common_px",
        "max_x_common_px",
        "max_y_common_px",
        "mass_kg",
        "stiffness_n_per_m",
        "strength_n",
        "connection_credit",
        "load_path_credit",
        "component_damage_credit",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)


def main() -> int:
    config = read_json(CONFIG_PATH)
    generated_at = utc_now()
    outputs = {name: ROOT / value for name, value in config["outputs"].items()}
    floors = [int(value) for value in config["stack"]["floors"]]
    stair_order = list(config["stack"]["stair_order"])
    variant_order = list(config["stack"]["variant_order"])

    regression_checks = resolve_map(config["regression_files"])
    input_checks = resolve_map(config["input_artifacts"])
    protected_before = resolve_map(config["protected_files"])

    v9t_layer = read_json(V9T_LAYER_PATH)
    v9r_topology = read_json(V9R_TOPOLOGY_PATH)
    all_matrix_rows = read_floor_matrix(V9R_FLOOR_MATRIX_PATH)
    selected_rows = [
        row
        for row in all_matrix_rows
        if row["floor"] in floors and row["stair_alias"] in stair_order
    ]
    order_by_stair = {stair: index for index, stair in enumerate(stair_order)}
    selected_rows.sort(key=lambda row: (row["floor"], order_by_stair[row["stair_alias"]]))
    row_map = {(row["floor"], row["stair_alias"]): row for row in selected_rows}
    topology_by_stair = {row["letter_alias"]: row for row in v9r_topology["stairways"]}

    target_bands: list[dict[str, Any]] = []
    for band in v9r_topology["floor_bands"]:
        covered = [
            floor
            for floor in floors
            if int(band["floor_start"]) <= floor <= int(band["floor_end"])
        ]
        if covered:
            target_bands.append(
                {
                    "source_floor_start": int(band["floor_start"]),
                    "source_floor_end": int(band["floor_end"]),
                    "target_floor_start": min(covered),
                    "target_floor_end": max(covered),
                    "covered_floors": covered,
                    "layout": band["layout"],
                    "table_panel": bool(band["table_panel"]),
                }
            )

    band_by_floor: dict[int, dict[str, Any]] = {}
    for floor in floors:
        matches = [band for band in target_bands if floor in band["covered_floors"]]
        if len(matches) == 1:
            band_by_floor[floor] = matches[0]

    floor_summaries: dict[int, dict[str, Any]] = {}
    dimension_checks: list[bool] = []
    for floor in floors:
        rows = [row_map[(floor, stair)] for stair in stair_order if (floor, stair) in row_map]
        landing_dimensions_match = []
        for row in rows:
            topology_row = topology_by_stair[row["stair_alias"]]
            landing_dimensions_match.append(
                row["landing_width_in"] == float(topology_row["landing_by_exit_door_width_in"])
                and row["landing_depth_in"] == float(topology_row["landing_by_exit_door_depth_in"])
            )
        dimension_checks.extend(landing_dimensions_match)
        band = band_by_floor.get(floor)
        all_present = len(rows) == len(stair_order) and all(
            row["present_in_reported_vertical_extent"] for row in rows
        )
        all_continue = len(rows) == len(stair_order) and all(
            row["service_status"] == "CONTINUES" for row in rows
        )
        no_transfer = len(rows) == len(stair_order) and all(
            row["transfer_event"] == "NONE" for row in rows
        )
        floor_summaries[floor] = {
            "floor": floor,
            "categorical_level_index": floors.index(floor),
            "floor_band_layout": band["layout"] if band else None,
            "table_2_2_panel_present": band["table_panel"] if band else None,
            "all_three_stairs_present": all_present,
            "all_three_stairs_continue": all_continue,
            "no_listed_transfer_event": no_transfer,
            "landing_dimensions_match_v9r_topology": all(landing_dimensions_match),
            "floor_95_labelled_overlay_row_count": sum(
                int(row["floor_95_labelled_overlay"]) for row in rows
            ),
            "categorical_continuity_supported": bool(
                band and all_present and all_continue and no_transfer and all(landing_dimensions_match)
            ),
            "floor_specific_as_built_geometry_supported": False,
            "rows": rows,
        }

    transitions: list[dict[str, Any]] = []
    for lower, upper in zip(floors[:-1], floors[1:]):
        lower_summary = floor_summaries[lower]
        upper_summary = floor_summaries[upper]
        transfer_rows = [
            row_map[(floor, stair)]
            for floor in (lower, upper)
            for stair in stair_order
            if row_map[(floor, stair)]["transfer_event"] != "NONE"
        ]
        transitions.append(
            {
                "from_floor": lower,
                "to_floor": upper,
                "from_band_layout": lower_summary["floor_band_layout"],
                "to_band_layout": upper_summary["floor_band_layout"],
                "band_boundary": lower_summary["floor_band_layout"]
                != upper_summary["floor_band_layout"],
                "listed_transfer_events": [
                    {
                        "floor": row["floor"],
                        "stair": row["stair_alias"],
                        "event": row["transfer_event"],
                    }
                    for row in transfer_rows
                ],
                "categorical_continuity_supported": lower_summary[
                    "categorical_continuity_supported"
                ]
                and upper_summary["categorical_continuity_supported"]
                and not transfer_rows,
                "identical_floor_specific_geometry_established": False,
            }
        )

    variants: dict[str, Any] = {}
    metric_rows: list[dict[str, Any]] = []
    all_instances: list[dict[str, Any]] = []
    physical = config["stack"]["assigned_physical_properties"]
    for variant in variant_order:
        source_variant = v9t_layer["variants"][variant]
        instances: list[dict[str, Any]] = []
        for floor in floors:
            summary = floor_summaries[floor]
            for stair in stair_order:
                source = source_variant["stairs"][stair]
                row = row_map[(floor, stair)]
                status = (
                    config["stack"]["floor_95_status"]
                    if floor == config["stack"]["source_geometry_floor"]
                    else config["stack"]["other_floor_status"]
                )
                geometry_payload = {
                    "bounds_common_px": copy.deepcopy(source["bounds_common_px"]),
                    "polygon_common_px": copy.deepcopy(source["polygon_common_px"]),
                    "centroid_common_px": copy.deepcopy(source["centroid_common_px"]),
                    "rotation_deg_hypothesis": source["rotation_deg_hypothesis"],
                    "published_landing_dimensions_in": copy.deepcopy(
                        source["published_landing_dimensions_in"]
                    ),
                }
                instance = {
                    "instance_id": f"{variant}_F{floor}_{stair}",
                    "variant": variant,
                    "floor": floor,
                    "categorical_level_index": floors.index(floor),
                    "stair": stair,
                    "floor_band_layout": summary["floor_band_layout"],
                    "table_2_2_panel_present": row["table_2_2_panel_present"],
                    "service_status": row["service_status"],
                    "transfer_event": row["transfer_event"],
                    "core_relation": row["core_relation"],
                    "floor_95_labelled_overlay_available": row["floor_95_labelled_overlay"],
                    "source_geometry_floor": config["stack"]["source_geometry_floor"],
                    "placement_status": status,
                    "hypothetical_placement": True,
                    "copy_of_floor95_display_coordinates": True,
                    "geometry_identity_across_floors_asserted": False,
                    "floor_specific_geometry_observed": False,
                    "as_built_geometry_observed": False,
                    "categorical_continuity_supported": summary[
                        "categorical_continuity_supported"
                    ],
                    "coordinate_system": config["stack"]["coordinate_system"],
                    "vertical_axis_semantics": config["stack"]["vertical_axis_semantics"],
                    "physical_vertical_scale_assigned": False,
                    "floor_to_floor_height_m": None,
                    "physical_z_m": None,
                    "common_relative_scale_common_px_per_published_in": v9t_layer[
                        "common_relative_scale_common_px_per_published_in"
                    ],
                    "scale_is_physical_conversion": False,
                    **geometry_payload,
                    "floor95_geometry_copy_fingerprint_sha256": canonical_sha256(
                        geometry_payload
                    ),
                    "assigned_physical_properties": copy.deepcopy(physical),
                    "zero_value_interpretation": config["stack"]["zero_value_interpretation"],
                    "component_damage_inference_performed": False,
                    "solver_geometry_authorized": False,
                    "mechanical_credit": False,
                    "physical_validation": False,
                }
                instances.append(instance)
                all_instances.append(instance)
                bounds = instance["bounds_common_px"]
                metric_rows.append(
                    {
                        "variant": variant,
                        "floor": floor,
                        "categorical_level_index": floors.index(floor),
                        "stair": stair,
                        "floor_band_layout": summary["floor_band_layout"],
                        "table_2_2_panel_present": row["table_2_2_panel_present"],
                        "service_status": row["service_status"],
                        "transfer_event": row["transfer_event"],
                        "floor_95_labelled_overlay_available": row[
                            "floor_95_labelled_overlay"
                        ],
                        "placement_status": status,
                        "hypothetical_placement": True,
                        "copy_of_floor95_display_coordinates": True,
                        "geometry_identity_across_floors_asserted": False,
                        "observed_as_built_geometry": False,
                        "physical_vertical_scale_assigned": False,
                        "physical_z_m": "",
                        "common_relative_scale_common_px_per_published_in": instance[
                            "common_relative_scale_common_px_per_published_in"
                        ],
                        "min_x_common_px": bounds["min_x"],
                        "min_y_common_px": bounds["min_y"],
                        "max_x_common_px": bounds["max_x"],
                        "max_y_common_px": bounds["max_y"],
                        "mass_kg": physical["mass_kg"],
                        "stiffness_n_per_m": physical["stiffness_n_per_m"],
                        "strength_n": physical["strength_n"],
                        "connection_credit": physical["connection_credit"],
                        "load_path_credit": physical["load_path_credit"],
                        "component_damage_credit": physical["component_damage_credit"],
                    }
                )
        variants[variant] = {
            "placement_variant_status": "SEPARATE_HYPOTHETICAL_V9T_VARIANT_NOT_PROBABILITY_OR_CONFIDENCE_BOUND",
            "source_v9t_placement_specification": copy.deepcopy(
                source_variant["placement_specification"]
            ),
            "instance_count": len(instances),
            "instances": instances,
        }

    stack_fingerprint_payload = {
        "floors": floors,
        "bands": target_bands,
        "transitions": transitions,
        "instances": [
            {
                "instance_id": item["instance_id"],
                "placement_status": item["placement_status"],
                "bounds_common_px": item["bounds_common_px"],
                "polygon_common_px": item["polygon_common_px"],
                "physical_z_m": item["physical_z_m"],
            }
            for item in all_instances
        ],
    }
    stack_fingerprint = canonical_sha256(stack_fingerprint_payload)

    figure_dir = outputs["figure_directory"]
    variant_paths: dict[str, Path] = {}
    floor_summary_public = {
        floor: {key: value for key, value in summary.items() if key != "rows"}
        for floor, summary in floor_summaries.items()
    }
    for variant in variant_order:
        path = figure_dir / f"v9u_{variant}_categorical_stack.png"
        draw_variant_stack(
            path,
            variant,
            floors,
            floor_summary_public,
            variants[variant]["instances"],
        )
        variant_paths[variant] = path
    make_contact_sheet(variant_paths, outputs["contact_sheet"], variant_order)

    protected_after = resolve_map(config["protected_files"])
    transfer_event_count = sum(
        int(row["transfer_event"] != "NONE") for row in selected_rows
    )
    overlay_row_count = sum(int(row["floor_95_labelled_overlay"]) for row in selected_rows)
    band_boundary_count = sum(int(row["band_boundary"]) for row in transitions)
    qualification_fields = (
        "exact_metric_plan_coordinates_qualified",
        "flight_and_stringer_geometry_qualified",
        "connections_qualified",
        "discrete_mass_qualified",
        "stiffness_qualified",
        "strength_qualified",
        "load_path_credit_qualified",
    )
    all_qualifications_closed = all(
        row[field] is False for row in selected_rows for field in qualification_fields
    )
    all_zero = all(float(value) == 0.0 for value in physical.values())
    mechanics_closed = all(
        config["gates"][key] is False
        for key in (
            "metric_as_built_solver_geometry_authorized",
            "whole_stair_enclosure_geometry_authorized",
            "physical_vertical_scale_authorized",
            "discrete_mass_authorized",
            "stiffness_authorized",
            "strength_authorized",
            "connection_authorized",
            "load_path_credit_authorized",
            "component_damage_validation_authorized",
            "global_solver_authorized",
            "blender_authorized",
            "blender_physical_validation_authorized",
        )
    )
    source_policy_closed = all(
        config["source_policy"][key] is False
        for key in (
            "source_archive_read",
            "source_archive_rescanned",
            "network_access_used",
            "official_source_files_modified",
            "structural_solver_authorized",
            "blender_authorized",
            "blender_master_modification_authorized",
            "physical_interpretation_authorized",
            "metric_as_built_geometry_authorized",
            "physical_vertical_scale_authorized",
            "mass_assignment_authorized",
            "stiffness_assignment_authorized",
            "strength_assignment_authorized",
            "connection_assignment_authorized",
            "load_path_credit_authorized",
            "component_damage_validation_authorized",
        )
    )
    checks = {
        "v8u_through_v9t_chained_regression_hashes": len(regression_checks)
        == config["gates"]["regression_hash_count_expected"]
        and all(row["pass"] for row in regression_checks),
        "direct_input_artifact_hashes": len(input_checks)
        == config["gates"]["input_artifact_hash_count_expected"]
        and all(row["pass"] for row in input_checks),
        "protected_blender_master_before_after": len(protected_before)
        == config["gates"]["protected_file_hash_count_expected"]
        and all(row["pass"] for row in protected_before)
        and all(row["pass"] for row in protected_after),
        "v9t_geometry_layer_pass_and_fingerprint": v9t_layer["validation_status"] == "PASS"
        and v9t_layer["floor"] == config["stack"]["source_geometry_floor"]
        and v9t_layer["geometry_fingerprint_sha256"]
        == config["gates"]["v9t_geometry_fingerprint_sha256"]
        and v9t_layer["physical_scale_assigned"] is False,
        "floor_count": len(floors) == config["gates"]["floor_count_expected"]
        and floors == list(range(93, 100)),
        "stairway_count": len(stair_order) == config["gates"]["stairway_count_expected"]
        and set(stair_order) == {"A", "B", "C"},
        "variant_count_and_separation": len(variant_order)
        == config["gates"]["variant_count_expected"]
        and set(variant_order) == {"low", "base", "high"}
        and set(variants) == set(variant_order),
        "floor_stair_documentary_coverage": len(selected_rows)
        == config["gates"]["floor_stair_documentary_row_count_expected"]
        and len(row_map) == len(selected_rows)
        and all((floor, stair) in row_map for floor in floors for stair in stair_order),
        "two_documented_floor_bands_preserved": len(target_bands)
        == config["gates"]["documented_floor_band_count_expected"]
        and len(band_by_floor) == len(floors)
        and all(
            row_map[(floor, stair)]["floor_band_layout"]
            == band_by_floor[floor]["layout"]
            for floor in floors
            for stair in stair_order
        ),
        "all_three_stairs_documented_continuous": all(
            summary["categorical_continuity_supported"]
            for summary in floor_summaries.values()
        ),
        "no_transfer_event_93_99": transfer_event_count
        == config["gates"]["transfer_event_count_expected"],
        "adjacent_transition_coverage": len(transitions)
        == config["gates"]["adjacent_floor_transition_count_expected"]
        and all(row["categorical_continuity_supported"] for row in transitions),
        "band_boundary_preserved_without_geometry_inference": band_boundary_count
        == config["gates"]["band_boundary_transition_count_expected"]
        and all(row["identical_floor_specific_geometry_established"] is False for row in transitions),
        "floor95_overlay_not_extrapolated": overlay_row_count
        == config["gates"]["floor_95_overlay_row_count_expected"]
        and all(
            row["floor_95_labelled_overlay"] == (row["floor"] == 95)
            for row in selected_rows
        ),
        "published_landing_dimensions_consistent": all(dimension_checks),
        "upstream_metric_and_mechanical_qualifications_closed": all_qualifications_closed,
        "categorical_stack_instance_count": len(all_instances)
        == config["gates"]["stack_instance_count_expected"]
        and all(len(variants[variant]["instances"]) == 21 for variant in variant_order),
        "all_placements_explicitly_hypothetical": all(
            item["hypothetical_placement"] is True
            and item["as_built_geometry_observed"] is False
            and item["geometry_identity_across_floors_asserted"] is False
            for item in all_instances
        ),
        "no_physical_vertical_coordinate_or_scale": config["stack"][
            "physical_vertical_scale_assigned"
        ]
        is False
        and config["stack"]["floor_to_floor_height_assigned"] is False
        and config["stack"]["z_coordinate_assigned"] is False
        and all(
            item["physical_z_m"] is None
            and item["floor_to_floor_height_m"] is None
            and item["physical_vertical_scale_assigned"] is False
            for item in all_instances
        ),
        "relative_scale_not_physical_conversion": v9t_layer[
            "common_relative_scale_common_px_per_published_in"
        ]
        == 2.3245978260869564
        and all(item["scale_is_physical_conversion"] is False for item in all_instances),
        "zero_physical_properties_and_credit": all_zero
        and all(
            all(float(value) == 0.0 for value in item["assigned_physical_properties"].values())
            for item in all_instances
        ),
        "mechanical_solver_blender_gates_closed": mechanics_closed,
        "source_policy_closed": source_policy_closed,
        "figures_created": len(variant_paths) == 3
        and all(path.is_file() for path in variant_paths.values())
        and outputs["contact_sheet"].is_file(),
    }
    overall_status = "PASS" if all(checks.values()) else "FAIL"

    continuity_audit = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "documentary_basis": [
            "V9R categorical floor bands from NCSTAR 1-7 Table 2-2",
            "V9R transfer-event topology from NCSTAR 1-7 Table 2-2 and transfer-hallway text",
            "V9R floor-by-stair matrix",
        ],
        "target_floors": floors,
        "target_stairs": stair_order,
        "floor_bands": target_bands,
        "floor_summaries": list(floor_summary_public.values()),
        "adjacent_floor_transitions": transitions,
        "counts": {
            "floor_count": len(floors),
            "stair_count": len(stair_order),
            "floor_stair_row_count": len(selected_rows),
            "floor_band_count": len(target_bands),
            "adjacent_transition_count": len(transitions),
            "band_boundary_transition_count": band_boundary_count,
            "listed_transfer_event_count": transfer_event_count,
            "floor_95_overlay_row_count": overlay_row_count,
        },
        "decision": {
            "categorical_seven_floor_stack_supported": overall_status == "PASS",
            "identical_floor_specific_geometry_supported": False,
            "metric_as_built_geometry_supported": False,
            "mechanical_or_damage_credit_supported": False,
        },
        "limitation": (
            "The 95-to-96 floor-band boundary is retained. The absence of a listed transfer event "
            "supports only categorical continuity and does not prove unchanged plan geometry."
        ),
    }
    categorical_stack = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "stack_status": "CATEGORICAL_HYPOTHETICAL_REPETITION_ONLY",
        "target_floors": floors,
        "source_geometry_floor": config["stack"]["source_geometry_floor"],
        "coordinate_system": config["stack"]["coordinate_system"],
        "vertical_axis_semantics": config["stack"]["vertical_axis_semantics"],
        "physical_vertical_scale_assigned": False,
        "floor_to_floor_height_assigned": False,
        "z_coordinate_assigned": False,
        "common_relative_scale_common_px_per_published_in": v9t_layer[
            "common_relative_scale_common_px_per_published_in"
        ],
        "scale_interpretation": config["stack"]["scale_interpretation"],
        "source_v9t_geometry_fingerprint_sha256": v9t_layer[
            "geometry_fingerprint_sha256"
        ],
        "categorical_stack_fingerprint_sha256": stack_fingerprint,
        "floor_bands": target_bands,
        "adjacent_floor_transitions": transitions,
        "variants": variants,
        "global_assigned_physical_properties": physical,
        "zero_value_interpretation": config["stack"]["zero_value_interpretation"],
        "observed_as_built_geometry_instance_count": 0,
        "hypothetical_instance_count": len(all_instances),
        "metric_as_built_geometry": False,
        "whole_stair_enclosure_geometry": False,
        "solver_geometry_authorized": False,
        "mechanical_credit": False,
        "component_damage_validation": False,
        "physical_validation": False,
    }
    model_gate = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "checks": checks,
        "qualification": {
            "categorical_seven_floor_stack": overall_status == "PASS",
            "three_separate_hypothetical_variants": overall_status == "PASS",
            "documented_continuity_without_transfer_93_99": overall_status == "PASS",
            "floor_band_boundary_preserved": overall_status == "PASS",
            "identical_floor_specific_geometry": False,
            "metric_as_built_geometry": False,
            "whole_stair_enclosure_geometry": False,
            "physical_vertical_scale": False,
            "mechanical_properties": False,
            "load_path_credit": False,
            "component_damage_validation": False,
            "structural_solver": False,
            "blender": False,
            "physical_validation": False,
        },
        "decision": (
            "V9U permits only three separate categorical seven-floor stacks. Every placement, "
            "including Floor 95, is hypothetical; repetition outside Floor 95 is not observed geometry."
        ),
    }
    results = {
        "iteration": config["iteration"],
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "random_seed": config["dataset"]["random_seed"],
        "random_draw_used": config["dataset"]["random_draw_used"],
        "scope": config["dataset"]["scope"],
        "observed_or_transcribed_facts": {
            "target_floor_count": len(floors),
            "floor_stair_documentary_row_count": len(selected_rows),
            "all_rows_present_and_continue": all(
                summary["all_three_stairs_present"]
                and summary["all_three_stairs_continue"]
                for summary in floor_summaries.values()
            ),
            "listed_transfer_event_count": transfer_event_count,
            "floor_band_count": len(target_bands),
            "floor_band_ranges_in_target": [
                [band["target_floor_start"], band["target_floor_end"]]
                for band in target_bands
            ],
            "floor_95_labelled_overlay_row_count": overlay_row_count,
            "other_floor_labelled_overlay_row_count": sum(
                int(row["floor_95_labelled_overlay"])
                for row in selected_rows
                if row["floor"] != 95
            ),
        },
        "official_model_results": {
            "floor_bands_derive_from_nist_schematic_panels": True,
            "floor_95_overlay_derives_from_nist_model_figure": True,
            "independent_as_built_measurement": False,
            "floor_specific_geometry_for_93_94_96_99_published_in_v9r": False,
        },
        "archive_claims_used": [],
        "model_hypotheses": {
            "repeat_v9t_normalized_coordinates_for_categorical_display": True,
            "all_repeated_placements_hypothetical": True,
            "low_base_high_retained_separately": True,
            "equal_display_spacing_has_physical_meaning": False,
            "physical_scale": None,
            "physical_vertical_coordinate": None,
        },
        "derived_results": {
            "categorical_stack_authorized": overall_status == "PASS",
            "variant_count": len(variant_order),
            "instances_per_variant": len(floors) * len(stair_order),
            "total_hypothetical_instance_count": len(all_instances),
            "floor95_hypothetical_instance_count": sum(
                int(item["floor"] == 95) for item in all_instances
            ),
            "cross_floor_hypothetical_repetition_count": sum(
                int(item["floor"] != 95) for item in all_instances
            ),
            "band_boundary_transition_count": band_boundary_count,
            "categorical_stack_fingerprint_sha256": stack_fingerprint,
            "inherited_common_relative_scale_common_px_per_published_in": v9t_layer[
                "common_relative_scale_common_px_per_published_in"
            ],
        },
        "contradictions_and_missing_information": [
            "Only Floor 95 has the labelled official-model overlay used upstream; Floors 93, 94 and 96-99 have no floor-specific footprint in V9R.",
            "Floors 95 and 96 lie in different published categorical bands. No transfer is listed, but identical plan geometry is not thereby established.",
            "The inherited 2.324597826 normalized-pixel-per-published-inch scale is not a physical conversion.",
            "Exact offsets, orientations, walls, doors, flights, stringers, connections, floor-to-floor heights, as-built coordinates and component damage remain unresolved.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    write_json(outputs["categorical_stack"], categorical_stack)
    write_json(outputs["continuity_audit"], continuity_audit)
    write_metrics_csv(outputs["metrics_csv"], metric_rows)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)

    report_lines = [
        "# WTC 1 - V9U - pile catégorielle hypothétique des escaliers, niveaux 93 à 99",
        "",
        f"**Validation générale : {overall_status}**",
        "",
        "> PILE CATÉGORIELLE HYPOTHÉTIQUE — AUCUNE GÉOMÉTRIE AS-BUILT — ZÉRO CRÉDIT MÉCANIQUE — PAS DE VALIDATION PHYSIQUE",
        "",
        "## Conclusion",
        "",
        "La continuité documentaire V9R autorise une pile catégorielle de sept niveaux pour A, C et B : les 21 lignes étage/cage indiquent que les cages sont présentes, qu'elles continuent et qu'aucun transfert n'est listé entre 93 et 99. Cette décision ne qualifie pas une répétition géométrique réelle. Les variantes LOW, BASE et HIGH restent trois hypothèses séparées.",
        "",
        "## 1. Faits directement observés ou transcrits",
        "",
        "- V9R contient 21 lignes pertinentes : sept niveaux multipliés par trois cages.",
        "- Toutes portent `CONTINUES`, `present_in_reported_vertical_extent=true` et `transfer_event=NONE`.",
        "- Deux bandes documentaires couvrent la cible : 83-95 et 96-102; dans V9U elles apparaissent respectivement sur 93-95 et 96-99.",
        "- La seule superposition étiquetée par étage dans ce jeu est celle du niveau 95; aucune ligne des six autres niveaux n'en revendique une.",
        "",
        "## 2. Résultats d'un modèle officiel",
        "",
        "Les bandes proviennent de panneaux schématiques NIST et la superposition du niveau 95 d'une figure du modèle officiel. Ce ne sont ni des relevés indépendants ni des plans d'exécution cotés. Le changement de bande entre 95 et 96 est conservé explicitement.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune. L'archive source n'a été ni ouverte ni rescannée.",
        "",
        "## 4. Hypothèses propres au modèle",
        "",
        "- Pour chaque variante, les coordonnées normalisées V9T du niveau 95 sont répétées comme marqueurs catégoriels aux niveaux 93 à 99.",
        "- Même au niveau 95, LOW, BASE et HIGH restent des ajustements relatifs hypothétiques, pas une géométrie observée.",
        "- L'espacement vertical des planches est seulement graphique. Aucun z, aucune hauteur d'étage et aucune échelle verticale physique ne sont attribués.",
        "- L'absence de transfert listé permet la continuité catégorielle, mais ne prouve pas une identité de plan entre étages.",
        "",
        "## 5. Résultats dérivés",
        "",
        f"- Trois piles séparées de {len(floors) * len(stair_order)} instances chacune; {len(all_instances)} instances hypothétiques au total.",
        f"- Frontières de bandes dans la cible : {band_boundary_count}; événements de transfert listés : {transfer_event_count}.",
        f"- Répétitions hors niveau 95 : {sum(int(item['floor'] != 95) for item in all_instances)}.",
        f"- Empreinte déterministe de la pile : `{stack_fingerprint}`.",
        f"- Échelle relative héritée : {v9t_layer['common_relative_scale_common_px_per_published_in']:.9f} pixels normalisés par pouce publié; elle n'est pas une conversion physique.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- Aucun contour spécifique aux niveaux 93, 94, 96, 97, 98 ou 99 n'est publié dans les artefacts V9R utilisés.",
        "- La frontière 95-96 ne documente pas la transformation exacte entre les deux bandes.",
        "- Les positions, orientations, murs, portes, volées, limons, connexions et hauteurs d'étage as-built restent inconnus.",
        "- Les indications de dommage de la matrice V9R ne sont ni propagées ni converties en dommage de composant dans V9U.",
        "",
        "## Portes de validation",
        "",
    ]
    for name, passed in checks.items():
        report_lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "Masse, rigidité, résistance, connexion, chemin de charge et crédit de dommage valent explicitement zéro dans V9U. Ces zéros signifient qu'aucun crédit n'est attribué par le modèle; ils ne décrivent pas une absence physique dans la tour.",
            "",
            "Aucun solveur et aucun processus Blender n'ont été exécutés. Le fichier Blender maître conserve son empreinte protégée.",
            "",
            "## Livrables",
            "",
            f"- Pile catégorielle : `{rel(outputs['categorical_stack'])}`",
            f"- Audit de continuité : `{rel(outputs['continuity_audit'])}`",
            f"- Mesures : `{rel(outputs['metrics_csv'])}`",
            f"- Porte modèle : `{rel(outputs['model_gate'])}`",
            f"- Planche de contrôle : `{rel(outputs['contact_sheet'])}`",
            "",
            "## Étape suivante pré-déclarée - V9V",
            "",
            config["next_iteration"]["objective"],
            "",
        ]
    )
    outputs["report"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report"].write_text("\n".join(report_lines), encoding="utf-8", newline="\n")

    generated_files = [
        outputs["categorical_stack"],
        outputs["continuity_audit"],
        outputs["metrics_csv"],
        outputs["model_gate"],
        outputs["contact_sheet"],
        outputs["results"],
        outputs["report"],
        *variant_paths.values(),
    ]
    manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "status": overall_status,
        "source_archive_read": False,
        "source_archive_rescanned": False,
        "network_access_used": False,
        "solver_executed": False,
        "blender_executed": False,
        "regression_files": regression_checks,
        "input_artifacts": input_checks,
        "protected_files_before": protected_before,
        "protected_files_after": protected_after,
        "source_v9t_geometry_fingerprint_sha256": v9t_layer["geometry_fingerprint_sha256"],
        "categorical_stack_fingerprint_sha256": stack_fingerprint,
        "generated_files": [
            {
                "path": rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in generated_files
        ],
    }
    write_json(outputs["source_manifest"], manifest)

    print(
        json.dumps(
            {
                "iteration": config["iteration"],
                "status": overall_status,
                "floor_count": len(floors),
                "floor_stair_row_count": len(selected_rows),
                "floor_band_count": len(target_bands),
                "transfer_event_count": transfer_event_count,
                "band_boundary_count": band_boundary_count,
                "variant_count": len(variant_order),
                "hypothetical_instance_count": len(all_instances),
                "categorical_stack_fingerprint_sha256": stack_fingerprint,
                "checks": checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
