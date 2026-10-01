#!/usr/bin/env python3
"""V9T - deterministic geometry-only Floor 95 stairwell layer.

The script combines V9S qualitative normalized envelopes with the published
exit-door landing dimensions transcribed in V9R.  The resulting low, base and
high rectangles are explicitly hypothetical relative-fit placements.  They
are not as-built coordinates, enclosure footprints, solver geometry or a
source of mechanical credit.  No solver or Blender process is invoked.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9t_floor95_stairwell_geometry_layer.json"
WARNING = (
    "V9T - PLACEMENTS HYPOTHETIQUES - ZERO CREDIT MECANIQUE - "
    "PAS DE VALIDATION PHYSIQUE"
)
STAIR_ORDER = ("A", "C", "B")
VARIANT_ORDER = ("low", "base", "high")
PAIR_ORDER = (("A", "B"), ("A", "C"), ("B", "C"))


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


def dimensions(bounds: dict[str, float]) -> tuple[float, float]:
    return bounds["max_x"] - bounds["min_x"], bounds["max_y"] - bounds["min_y"]


def centroid(bounds: dict[str, float]) -> tuple[float, float]:
    return (
        (bounds["min_x"] + bounds["max_x"]) / 2.0,
        (bounds["min_y"] + bounds["max_y"]) / 2.0,
    )


def polygon_from_bounds(bounds: dict[str, float]) -> list[list[float]]:
    return [
        [bounds["min_x"], bounds["min_y"]],
        [bounds["max_x"], bounds["min_y"]],
        [bounds["max_x"], bounds["max_y"]],
        [bounds["min_x"], bounds["max_y"]],
    ]


def direct_transform(
    envelope: dict[str, float],
    oriented_dimensions_in: tuple[float, float],
    scale: float,
    fraction_x: float,
    fraction_y: float,
) -> dict[str, Any]:
    envelope_width, envelope_height = dimensions(envelope)
    width = oriented_dimensions_in[0] * scale
    height = oriented_dimensions_in[1] * scale
    residual_x = envelope_width - width
    residual_y = envelope_height - height
    tx = envelope["min_x"] + residual_x * fraction_x
    ty = envelope["min_y"] + residual_y * fraction_y
    bounds = {
        "min_x": tx,
        "min_y": ty,
        "max_x": tx + width,
        "max_y": ty + height,
    }
    return {
        "bounds_common_px": bounds,
        "polygon_common_px": polygon_from_bounds(bounds),
        "translation_common_px": [tx, ty],
        "residual_span_common_px": [residual_x, residual_y],
        "transform_matrix_3x3": [
            [scale, 0.0, tx],
            [0.0, scale, ty],
            [0.0, 0.0, 1.0],
        ],
    }


def matrix_transform(
    oriented_dimensions_in: tuple[float, float], matrix: list[list[float]]
) -> list[list[float]]:
    local = [
        [0.0, 0.0],
        [oriented_dimensions_in[0], 0.0],
        [oriented_dimensions_in[0], oriented_dimensions_in[1]],
        [0.0, oriented_dimensions_in[1]],
    ]
    output: list[list[float]] = []
    for x, y in local:
        output.append(
            [
                matrix[0][0] * x + matrix[0][1] * y + matrix[0][2],
                matrix[1][0] * x + matrix[1][1] * y + matrix[1][2],
            ]
        )
    return output


def max_polygon_difference(first: list[list[float]], second: list[list[float]]) -> float:
    return max(
        abs(value_a - value_b)
        for point_a, point_b in zip(first, second)
        for value_a, value_b in zip(point_a, point_b)
    )


def contained(
    inner: dict[str, float], outer: dict[str, float], tolerance: float
) -> tuple[bool, dict[str, float]]:
    margins = {
        "left": inner["min_x"] - outer["min_x"],
        "top": inner["min_y"] - outer["min_y"],
        "right": outer["max_x"] - inner["max_x"],
        "bottom": outer["max_y"] - inner["max_y"],
    }
    return all(value >= -tolerance for value in margins.values()), margins


def intersection_area(first: dict[str, float], second: dict[str, float]) -> float:
    overlap_x = max(0.0, min(first["max_x"], second["max_x"]) - max(first["min_x"], second["min_x"]))
    overlap_y = max(0.0, min(first["max_y"], second["max_y"]) - max(first["min_y"], second["min_y"]))
    return overlap_x * overlap_y


def clearance(first: dict[str, float], second: dict[str, float]) -> float:
    dx = max(first["min_x"] - second["max_x"], second["min_x"] - first["max_x"], 0.0)
    dy = max(first["min_y"] - second["max_y"], second["min_y"] - first["max_y"], 0.0)
    return math.hypot(dx, dy)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_variant(
    output: Path,
    variant_name: str,
    entries: dict[str, Any],
    scale: float,
) -> None:
    margin = 105
    canvas_extent = 1000
    image = Image.new("RGB", (1210, 1285), "white")
    draw = ImageDraw.Draw(image)
    warning_font = load_font(22, bold=True)
    title_font = load_font(30, bold=True)
    body_font = load_font(20)
    label_font = load_font(24, bold=True)
    draw.rectangle((0, 0, image.width, 48), fill=(145, 0, 0))
    draw.text((16, 11), WARNING, fill="white", font=warning_font)
    draw.text(
        (margin, 62),
        f"V9T - variante {variant_name.upper()} - Floor 95",
        fill=(0, 0, 0),
        font=title_font,
    )
    draw.text(
        (margin, 98),
        f"Canevas qualitatif 1000 x 1000 | echelle relative={scale:.9f}",
        fill=(35, 35, 35),
        font=body_font,
    )
    draw.rectangle(
        (margin, 140, margin + canvas_extent, 140 + canvas_extent),
        outline=(30, 30, 30),
        width=3,
    )
    for index in range(1, 10):
        x = margin + index * 100
        y = 140 + index * 100
        draw.line((x, 140, x, 1140), fill=(220, 220, 220), width=1)
        draw.line((margin, y, 1105, y), fill=(220, 220, 220), width=1)

    colors = {"A": (216, 49, 49), "B": (38, 139, 76), "C": (151, 64, 190)}
    for stair in STAIR_ORDER:
        entry = entries[stair]
        color = colors[stair]
        envelope = entry["source_envelope_common_px"]
        rectangle = entry["bounds_common_px"]
        env_box = (
            margin + envelope["min_x"],
            140 + envelope["min_y"],
            margin + envelope["max_x"],
            140 + envelope["max_y"],
        )
        rect_box = (
            margin + rectangle["min_x"],
            140 + rectangle["min_y"],
            margin + rectangle["max_x"],
            140 + rectangle["max_y"],
        )
        draw.rectangle(env_box, outline=(*color,), width=2)
        draw.rectangle(rect_box, fill=tuple(min(255, value + 75) for value in color), outline=color, width=4)
        center = centroid(rectangle)
        draw.text(
            (margin + center[0] - 9, 140 + center[1] - 13),
            stair,
            fill=(0, 0, 0),
            font=label_font,
        )
    draw.text(
        (margin, 1162),
        "Contour fin : enveloppe V9S | rectangle plein : palier relatif hypothetique",
        fill=(0, 0, 0),
        font=body_font,
    )
    draw.text(
        (margin, 1191),
        "ZERO masse, rigidite, resistance, connexion et chemin de charge assignes.",
        fill=(145, 0, 0),
        font=body_font,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")


def make_contact_sheet(variant_paths: dict[str, Path], output: Path) -> None:
    image = Image.new("RGB", (1830, 715), (235, 235, 235))
    draw = ImageDraw.Draw(image)
    warning_font = load_font(20, bold=True)
    title_font = load_font(25, bold=True)
    draw.rectangle((0, 0, image.width, 45), fill=(145, 0, 0))
    draw.text((14, 10), WARNING, fill="white", font=warning_font)
    for index, variant in enumerate(VARIANT_ORDER):
        x = 15 + index * 605
        y = 58
        draw.rectangle((x, y, x + 590, y + 640), fill="white", outline=(40, 40, 40), width=2)
        draw.text((x + 12, y + 8), variant.upper(), fill=(0, 0, 0), font=title_font)
        with Image.open(variant_paths[variant]) as source:
            tile = source.convert("RGB")
            tile.thumbnail((570, 590), Image.Resampling.LANCZOS)
        image.paste(tile, (x + 10 + (570 - tile.width) // 2, y + 42))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "variant",
        "stair",
        "rotation_deg",
        "published_width_in",
        "published_depth_in",
        "oriented_x_in",
        "oriented_y_in",
        "scale_common_px_per_published_in",
        "min_x_common_px",
        "min_y_common_px",
        "max_x_common_px",
        "max_y_common_px",
        "residual_x_common_px",
        "residual_y_common_px",
        "contained_in_v9s_envelope",
        "transform_max_abs_error_common_px",
        "dimension_max_abs_error_in",
        "variant_min_pairwise_clearance_common_px",
        "variant_topology_pass",
        "mass_kg",
        "stiffness_n_per_m",
        "strength_n",
        "connection_credit",
        "load_path_credit",
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

    regression_checks = resolve_map(config["regression_files"])
    input_checks = resolve_map(config["input_artifacts"])
    protected_before = resolve_map(config["protected_files"])

    envelopes = read_json(ROOT / "wtc1_simulation_v8/output/v9s_stairwell_qualitative_envelopes.json")
    topology = read_json(ROOT / "wtc1_simulation_v8/output/v9r_stairwell_topology.json")
    topology_by_stair = {row["letter_alias"]: row for row in topology["stairways"]}

    oriented: dict[str, dict[str, Any]] = {}
    scale_candidates: list[dict[str, Any]] = []
    for stair in STAIR_ORDER:
        source = topology_by_stair[stair]
        width_in = float(source["landing_by_exit_door_width_in"])
        depth_in = float(source["landing_by_exit_door_depth_in"])
        rotation = float(config["geometry"]["orientation_hypotheses"][stair]["rotation_deg"])
        if rotation == 0.0:
            x_in, y_in = width_in, depth_in
        elif rotation == 90.0:
            x_in, y_in = depth_in, width_in
        else:
            raise ValueError(f"Unsupported rotation for {stair}: {rotation}")
        envelope_bounds = envelopes["stairs"][stair]["bounds_common_px"]
        envelope_width, envelope_height = dimensions(envelope_bounds)
        x_capacity = envelope_width / x_in
        y_capacity = envelope_height / y_in
        oriented[stair] = {
            "published_width_in": width_in,
            "published_depth_in": depth_in,
            "rotation_deg": rotation,
            "oriented_x_in": x_in,
            "oriented_y_in": y_in,
            "source_envelope_common_px": envelope_bounds,
            "source_envelope_status": envelopes["stairs"][stair]["status"],
            "envelope_width_common_px": envelope_width,
            "envelope_height_common_px": envelope_height,
        }
        scale_candidates.extend(
            [
                {"stair": stair, "axis": "x", "capacity": x_capacity},
                {"stair": stair, "axis": "y", "capacity": y_capacity},
            ]
        )

    controlling_candidate = min(scale_candidates, key=lambda row: row["capacity"])
    common_scale = float(controlling_candidate["capacity"])
    variants: dict[str, Any] = {}
    topology_audits: dict[str, Any] = {}
    metric_rows: list[dict[str, Any]] = []
    maximum_transform_error = 0.0
    maximum_dimension_error = 0.0

    containment_tolerance = float(config["gates"]["containment_tolerance_common_px"])
    intersection_tolerance = float(config["gates"]["intersection_area_tolerance_common_px2"])
    for variant_name in VARIANT_ORDER:
        variant_spec = config["geometry"]["placement_variants"][variant_name]
        entries: dict[str, Any] = {}
        for stair in STAIR_ORDER:
            source = oriented[stair]
            transformed = direct_transform(
                source["source_envelope_common_px"],
                (source["oriented_x_in"], source["oriented_y_in"]),
                common_scale,
                float(variant_spec["residual_fraction_x"]),
                float(variant_spec["residual_fraction_y"]),
            )
            reproduced = matrix_transform(
                (source["oriented_x_in"], source["oriented_y_in"]),
                transformed["transform_matrix_3x3"],
            )
            transform_error = max_polygon_difference(transformed["polygon_common_px"], reproduced)
            bounds = transformed["bounds_common_px"]
            derived_width, derived_height = dimensions(bounds)
            dimension_error = max(
                abs(derived_width / common_scale - source["oriented_x_in"]),
                abs(derived_height / common_scale - source["oriented_y_in"]),
            )
            is_contained, margins = contained(
                bounds, source["source_envelope_common_px"], containment_tolerance
            )
            maximum_transform_error = max(maximum_transform_error, transform_error)
            maximum_dimension_error = max(maximum_dimension_error, dimension_error)
            entries[stair] = {
                "stair": stair,
                "source_envelope_common_px": source["source_envelope_common_px"],
                "source_envelope_status": source["source_envelope_status"],
                "published_landing_dimensions_in": {
                    "width": source["published_width_in"],
                    "depth": source["published_depth_in"],
                },
                "rotation_deg_hypothesis": source["rotation_deg"],
                "oriented_dimensions_in": {
                    "x": source["oriented_x_in"],
                    "y": source["oriented_y_in"],
                },
                "common_relative_scale_common_px_per_published_in": common_scale,
                **transformed,
                "centroid_common_px": list(centroid(bounds)),
                "containment_margins_common_px": margins,
                "contained_in_v9s_envelope": is_contained,
                "independent_matrix_polygon_common_px": reproduced,
                "transform_max_abs_error_common_px": transform_error,
                "dimension_max_abs_error_in": dimension_error,
                "assigned_physical_properties": config["geometry"]["assigned_physical_properties"],
                "metric_as_built_geometry": False,
                "solver_geometry_authorized": False,
                "mechanical_credit": False,
            }

        pair_rows: list[dict[str, Any]] = []
        for first_stair, second_stair in PAIR_ORDER:
            first = entries[first_stair]["bounds_common_px"]
            second = entries[second_stair]["bounds_common_px"]
            area = intersection_area(first, second)
            gap = clearance(first, second)
            pair_rows.append(
                {
                    "pair": f"{first_stair}-{second_stair}",
                    "intersection_area_common_px2": area,
                    "clearance_common_px": gap,
                    "non_overlap": area <= intersection_tolerance and gap > 0.0,
                }
            )
        a = entries["A"]["bounds_common_px"]
        b = entries["B"]["bounds_common_px"]
        c = entries["C"]["bounds_common_px"]
        a_center = centroid(a)
        b_center = centroid(b)
        c_center = centroid(c)
        relations = {
            "C_WEST_OF_A": c["max_x"] < a["min_x"],
            "A_NORTH_OF_B": a["max_y"] < b["min_y"],
            "C_NORTH_OF_B": c["max_y"] < b["min_y"],
            "B_CENTROID_X_BETWEEN_C_AND_A": c_center[0] < b_center[0] < a_center[0],
        }
        topology_pass = all(relations.values()) and all(row["non_overlap"] for row in pair_rows)
        minimum_clearance = min(row["clearance_common_px"] for row in pair_rows)
        topology_audits[variant_name] = {
            "relations": relations,
            "pairs": pair_rows,
            "minimum_pairwise_clearance_common_px": minimum_clearance,
            "pass": topology_pass,
        }
        for stair in STAIR_ORDER:
            entry = entries[stair]
            bounds = entry["bounds_common_px"]
            physical = entry["assigned_physical_properties"]
            metric_rows.append(
                {
                    "variant": variant_name,
                    "stair": stair,
                    "rotation_deg": entry["rotation_deg_hypothesis"],
                    "published_width_in": entry["published_landing_dimensions_in"]["width"],
                    "published_depth_in": entry["published_landing_dimensions_in"]["depth"],
                    "oriented_x_in": entry["oriented_dimensions_in"]["x"],
                    "oriented_y_in": entry["oriented_dimensions_in"]["y"],
                    "scale_common_px_per_published_in": common_scale,
                    "min_x_common_px": bounds["min_x"],
                    "min_y_common_px": bounds["min_y"],
                    "max_x_common_px": bounds["max_x"],
                    "max_y_common_px": bounds["max_y"],
                    "residual_x_common_px": entry["residual_span_common_px"][0],
                    "residual_y_common_px": entry["residual_span_common_px"][1],
                    "contained_in_v9s_envelope": entry["contained_in_v9s_envelope"],
                    "transform_max_abs_error_common_px": entry["transform_max_abs_error_common_px"],
                    "dimension_max_abs_error_in": entry["dimension_max_abs_error_in"],
                    "variant_min_pairwise_clearance_common_px": minimum_clearance,
                    "variant_topology_pass": topology_pass,
                    "mass_kg": physical["mass_kg"],
                    "stiffness_n_per_m": physical["stiffness_n_per_m"],
                    "strength_n": physical["strength_n"],
                    "connection_credit": physical["connection_credit"],
                    "load_path_credit": physical["load_path_credit"],
                }
            )
        variants[variant_name] = {
            "placement_specification": variant_spec,
            "stairs": entries,
            "topology_audit": topology_audits[variant_name],
        }

    fingerprint_payload = {
        "common_scale": common_scale,
        "controlling_candidate": controlling_candidate,
        "variants": {
            variant: {
                stair: variants[variant]["stairs"][stair]["polygon_common_px"]
                for stair in STAIR_ORDER
            }
            for variant in VARIANT_ORDER
        },
    }
    geometry_fingerprint = canonical_sha256(fingerprint_payload)

    figure_dir = outputs["figure_directory"]
    variant_paths: dict[str, Path] = {}
    for variant_name in VARIANT_ORDER:
        path = figure_dir / f"v9t_{variant_name}_placement.png"
        draw_variant(path, variant_name, variants[variant_name]["stairs"], common_scale)
        variant_paths[variant_name] = path
    make_contact_sheet(variant_paths, outputs["contact_sheet"])

    protected_after = resolve_map(config["protected_files"])
    all_zero = all(
        float(value) == 0.0
        for value in config["geometry"]["assigned_physical_properties"].values()
    )
    mechanics_closed = all(
        config["gates"][key] is False
        for key in (
            "metric_as_built_solver_geometry_authorized",
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
            "mass_assignment_authorized",
            "stiffness_assignment_authorized",
            "strength_assignment_authorized",
            "connection_assignment_authorized",
            "load_path_credit_authorized",
            "component_damage_validation_authorized",
        )
    )
    checks = {
        "regression_hashes": len(regression_checks) == config["gates"]["regression_hash_count_expected"]
        and all(row["pass"] for row in regression_checks),
        "input_artifact_hashes": len(input_checks) == config["gates"]["input_artifact_hash_count_expected"]
        and all(row["pass"] for row in input_checks),
        "protected_file_before_after": len(protected_before)
        == config["gates"]["protected_file_hash_count_expected"]
        and all(row["pass"] for row in protected_before)
        and all(row["pass"] for row in protected_after),
        "upstream_coordinate_boundary": envelopes["coordinate_system"]
        == config["geometry"]["coordinate_system"]
        and envelopes["physical_scale_assigned"] is False,
        "stairway_count": len(oriented) == config["gates"]["stairway_count_expected"],
        "variant_count": len(variants) == config["gates"]["variant_count_expected"],
        "common_scale_rule": common_scale == min(row["capacity"] for row in scale_candidates),
        "transform_reproducibility": maximum_transform_error
        <= config["gates"]["transform_reproduction_tolerance_common_px"],
        "published_dimension_reproduction": maximum_dimension_error
        <= config["gates"]["dimension_reproduction_tolerance_in"],
        "envelope_containment": all(
            variants[variant]["stairs"][stair]["contained_in_v9s_envelope"]
            for variant in VARIANT_ORDER
            for stair in STAIR_ORDER
        ),
        "topology_and_non_overlap": all(
            topology_audits[variant]["pass"] for variant in VARIANT_ORDER
        ),
        "positive_pairwise_clearance": all(
            topology_audits[variant]["minimum_pairwise_clearance_common_px"]
            > config["gates"]["minimum_pairwise_clearance_common_px_exclusive"]
            for variant in VARIANT_ORDER
        ),
        "zero_physical_properties": all_zero,
        "mechanical_and_blender_gates_closed": mechanics_closed,
        "source_policy_closed": source_policy_closed,
        "figures_created": len(variant_paths) == 3
        and all(path.is_file() for path in variant_paths.values())
        and outputs["contact_sheet"].is_file(),
    }
    overall_status = "PASS" if all(checks.values()) else "FAIL"

    geometry_layer = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "floor": config["geometry"]["floor"],
        "coordinate_system": config["geometry"]["coordinate_system"],
        "common_canvas_size_px": config["geometry"]["common_canvas_size_px"],
        "physical_scale_assigned": False,
        "metric_as_built_geometry": False,
        "common_relative_scale_common_px_per_published_in": common_scale,
        "scale_rule": config["geometry"]["common_relative_scale_rule"],
        "scale_interpretation": config["geometry"]["scale_interpretation"],
        "controlling_scale_candidate": controlling_candidate,
        "scale_candidates": scale_candidates,
        "geometry_fingerprint_sha256": geometry_fingerprint,
        "variants": variants,
        "global_assigned_physical_properties": config["geometry"]["assigned_physical_properties"],
        "solver_geometry_authorized": False,
        "mechanical_credit": False,
    }
    transform_audit = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "direct_method": "axis-aligned bounds from scaled oriented dimensions plus residual-envelope fraction",
        "independent_method": "homogeneous 3x3 matrix applied to four local landing corners",
        "geometry_fingerprint_sha256": geometry_fingerprint,
        "maximum_transform_abs_error_common_px": maximum_transform_error,
        "maximum_dimension_abs_error_in": maximum_dimension_error,
        "topology_audits": topology_audits,
        "checks": checks,
    }
    model_gate = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "checks": checks,
        "qualification": {
            "deterministic_geometry_only_layer": overall_status == "PASS",
            "three_hypothetical_placement_variants": overall_status == "PASS",
            "relative_landing_dimension_preservation": overall_status == "PASS",
            "topology_and_non_overlap": overall_status == "PASS",
            "metric_as_built_geometry": False,
            "whole_stair_enclosure_geometry": False,
            "mechanical_properties": False,
            "load_path_credit": False,
            "component_damage_validation": False,
            "structural_solver": False,
            "blender": False,
            "physical_validation": False,
        },
        "decision": (
            "V9T qualifies only deterministic relative-fit landing rectangles inside the V9S qualitative "
            "Floor 95 envelopes. Low/base/high are placement hypotheses, not confidence bounds or probabilities."
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
            "A_C_landing_by_exit_door_in": [92.0, 78.0],
            "B_landing_by_exit_door_in": [116.0, 78.0],
            "v9s_envelope_count": len(envelopes["stairs"]),
        },
        "official_model_results": {
            "v9s_envelopes_derive_from_nist_model_figures": True,
            "independent_as_built_measurement": False,
        },
        "archive_claims_used": [],
        "model_hypotheses": {
            "orientation_hypotheses": config["geometry"]["orientation_hypotheses"],
            "common_relative_scale_rule": config["geometry"]["common_relative_scale_rule"],
            "placement_variants": config["geometry"]["placement_variants"],
            "physical_scale": None,
        },
        "derived_results": {
            "common_relative_scale_common_px_per_published_in": common_scale,
            "controlling_scale_candidate": controlling_candidate,
            "geometry_fingerprint_sha256": geometry_fingerprint,
            "variant_count": len(variants),
            "stair_rectangle_count": len(variants) * len(oriented),
            "maximum_transform_abs_error_common_px": maximum_transform_error,
            "maximum_dimension_abs_error_in": maximum_dimension_error,
            "minimum_pairwise_clearance_by_variant_common_px": {
                variant: topology_audits[variant]["minimum_pairwise_clearance_common_px"]
                for variant in VARIANT_ORDER
            },
        },
        "contradictions_and_missing_information": [
            "The V9S envelopes are qualitative normalized unions of official-model graphics, not dimensioned as-built plans.",
            "The 92 by 78 in and 116 by 78 in values describe landings by exit doors, not whole stair enclosures.",
            "Orientation and low/base/high residual placements are explicit hypotheses.",
            "Walls, doors, flights, treads, risers, stringers, attachments, exact metric coordinates, mass and component damage remain unresolved.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    write_json(outputs["geometry_layer"], geometry_layer)
    write_json(outputs["transform_audit"], transform_audit)
    write_metrics_csv(outputs["metrics_csv"], metric_rows)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)

    report_lines = [
        "# WTC 1 - V9T - couche geometrique hypothetique des trois escaliers au niveau 95",
        "",
        f"**Validation generale : {overall_status}**",
        "",
        "> V9T - PLACEMENTS HYPOTHETIQUES - ZERO CREDIT MECANIQUE - PAS DE VALIDATION PHYSIQUE",
        "",
        "## Portee",
        "",
        "V9T conserve les regressions V8U a V9S et construit neuf rectangles de palier deterministes (trois escaliers x trois placements) dans le canevas qualitatif V9S. Le calcul verifie uniquement la reproduction des transformations, le maintien dans les enveloppes, la topologie et l'absence de chevauchement.",
        "",
        "## 1. Faits directement observes ou transcrits",
        "",
        "- V9R transcrit des paliers par porte de sortie de 92 x 78 pouces pour A et C, et de 116 x 78 pouces pour B.",
        "- V9S fournit trois enveloppes rectangulaires sur un canevas normalise de 1000 x 1000 pixels, sans echelle physique.",
        "- A et B reposent sur une union qualitative de deux figures; C ne possede qu'une enveloppe issue de la Figure 5-2.",
        "",
        "## 2. Resultats d'un modele officiel",
        "",
        "Les enveloppes V9S derivent de figures de modeles NIST. Elles ne sont pas des mesures as-built independantes. Les dimensions publiees concernent des paliers par porte de sortie et non l'enveloppe complete de chaque cage.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune. L'archive source n'a ete ni ouverte ni rescanee.",
        "",
        "## 4. Hypotheses propres au modele",
        "",
        "- A et C conservent le grand cote publie sur l'axe X; B est tourne de 90 degres pour suivre l'enveloppe V9S plus haute que large.",
        "- Une echelle relative commune est le minimum des six capacites enveloppe/dimension. Elle preserve les rapports publies mais n'est pas une conversion physique pixel-pouce.",
        "- LOW place chaque palier au bord inferieur-gauche de l'espace residuel, BASE au centre et HIGH au bord superieur-droit. Ces noms ne sont ni des probabilites, ni des intervalles de confiance, ni une meilleure estimation.",
        "",
        "## 5. Resultats derives",
        "",
        f"- Echelle relative commune : {common_scale:.9f} pixels normalises par pouce publie; controle par {controlling_candidate['stair']} axe {controlling_candidate['axis']}.",
        f"- Empreinte deterministe des coordonnees : `{geometry_fingerprint}`.",
        f"- Erreur maximale entre deux implementations de la transformation : {maximum_transform_error:.3e} pixel commun.",
        f"- Erreur maximale de restitution des dimensions publiees : {maximum_dimension_error:.3e} pouce.",
    ]
    for variant in VARIANT_ORDER:
        report_lines.append(
            f"- {variant.upper()} : ecart minimal entre rectangles = "
            f"{topology_audits[variant]['minimum_pairwise_clearance_common_px']:.3f} px; "
            f"topologie/non-chevauchement = {'PASS' if topology_audits[variant]['pass'] else 'FAIL'}."
        )
    report_lines.extend(
        [
            "",
            "Ces resultats qualifient la coherence interne d'une couche geometrique relative, pas la geometrie reelle des cages ni leur comportement lors de l'impact.",
            "",
            "## 6. Contradictions et informations manquantes",
            "",
            "- La position metrique exacte et l'orientation as-built ne sont pas disponibles.",
            "- Les rectangles representent uniquement les dimensions publiees de paliers, pas les murs, portes, volees, limons ou connexions.",
            "- La cage C reste fondee sur une seule figure pour son enveloppe qualitative au niveau 95.",
            "- Aucun dommage composant complet des trois cages n'est qualifie.",
            "",
            "## Portes de validation",
            "",
        ]
    )
    for name, passed in checks.items():
        report_lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "Masse, rigidite, resistance, connexion, chemin de charge et dommage recoivent explicitement une valeur de credit nulle. Cela signifie absence de credit dans ce modele, pas absence physique dans la tour.",
            "",
            "Aucun solveur et aucun processus Blender n'ont ete executes. Le fichier maitre Blender conserve son empreinte initiale.",
            "",
            "## Livrables",
            "",
            f"- Couche : `{rel(outputs['geometry_layer'])}`",
            f"- Audit des transformations : `{rel(outputs['transform_audit'])}`",
            f"- Mesures : `{rel(outputs['metrics_csv'])}`",
            f"- Porte modele : `{rel(outputs['model_gate'])}`",
            f"- Planche de controle : `{rel(outputs['contact_sheet'])}`",
            "",
            "## Etape suivante predeclaree - V9U",
            "",
            config["next_iteration"]["objective"],
            "",
        ]
    )
    outputs["report"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report"].write_text("\n".join(report_lines), encoding="utf-8", newline="\n")

    generated_files = [
        outputs["geometry_layer"],
        outputs["transform_audit"],
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
        "geometry_fingerprint_sha256": geometry_fingerprint,
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
                "common_relative_scale": common_scale,
                "controlling_candidate": controlling_candidate,
                "geometry_fingerprint_sha256": geometry_fingerprint,
                "maximum_transform_error_common_px": maximum_transform_error,
                "maximum_dimension_error_in": maximum_dimension_error,
                "minimum_clearances_common_px": {
                    variant: topology_audits[variant]["minimum_pairwise_clearance_common_px"]
                    for variant in VARIANT_ORDER
                },
                "checks": checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
