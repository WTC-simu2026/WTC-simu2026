#!/usr/bin/env python3
"""V9W - targeted audit of Port Authority architectural drawing scans.

Only ten explicitly selected archive files are read. The iteration records
nominal drawing-sheet coverage and visible stair identifiers for Floors 93-99.
It does not calibrate scan pixels, extract coordinates, claim as-built status,
assign physical properties, run a structural solver, or invoke Blender.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9w_floor93_99_port_authority_plan_audit.json"
V9V_MATRIX_PATH = ROOT / "wtc1_simulation_v8/output/v9v_floor93_99_stairwell_evidence_matrix.json"

WARNING = (
    "V9W - PLANS NOMINAUX DE DESSIN - PAS AS-BUILT - "
    "AUCUNE CONVERSION PIXEL/PHYSIQUE - ZERO CREDIT MECANIQUE"
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


def resolve_relative_map(mapping: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative_path, expected_hash in mapping.items():
        path = ROOT / relative_path
        exists = path.is_file()
        observed = sha256(path) if exists else None
        records.append(
            {
                "path": relative_path,
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else None,
                "expected_sha256": expected_hash.lower(),
                "observed_sha256": observed,
                "pass": exists and observed == expected_hash.lower(),
            }
        )
    return records


def inspect_source_file(path: Path, expected: dict[str, Any], label: str) -> dict[str, Any]:
    exists = path.is_file()
    observed_hash = sha256(path) if exists else None
    width = None
    height = None
    mode = None
    if exists:
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
    expected_hash = str(expected["sha256"]).lower()
    dimensions_pass = (
        exists
        and width == int(expected["width_px"])
        and height == int(expected["height_px"])
    )
    return {
        "name": path.name,
        "path": str(path),
        "location_class": label,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "width_px": width,
        "height_px": height,
        "mode": mode,
        "expected_sha256": expected_hash,
        "observed_sha256": observed_hash,
        "hash_pass": exists and observed_hash == expected_hash,
        "dimensions_pass": dimensions_pass,
        "pass": exists and observed_hash == expected_hash and dimensions_pass,
    }


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def write_matrix_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "floor",
        "stair",
        "plan_stair_number",
        "floor_plan_sheet",
        "core_plan_sheet",
        "core_coverage_kind",
        "plan_identifier_visible",
        "nominal_drawing_location_documented",
        "v9v_figure_9_124_marker_visibility",
        "v9v_source_visible_marker",
        "v9w_documentary_effect",
        "official_model_damage_marker_gap_closed",
        "drawing_status",
        "drawing_scale_transcription",
        "scan_pixel_to_physical_conversion_used",
        "numeric_dimension_extracted",
        "model_geometry_promoted",
        "variant_status",
        "mass_kg",
        "stiffness_n_per_m",
        "strength_n",
        "connection_credit",
        "load_path_credit",
        "component_damage_credit",
        "limitation",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def make_core_thumbnail(path: Path, crop_box: tuple[int, int, int, int], size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        crop = source.convert("L").crop(crop_box)
    crop = ImageOps.autocontrast(crop, cutoff=1)
    thumb = ImageOps.contain(crop, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("L", size, 255)
    canvas.paste(thumb, ((size[0] - thumb.width) // 2, (size[1] - thumb.height) // 2))
    return canvas.convert("RGB")


def draw_contact_sheet(
    path: Path,
    mappings: list[dict[str, Any]],
    copy_root: Path,
    counts: dict[str, int],
) -> None:
    image = Image.new("RGB", (2400, 1700), "white")
    draw = ImageDraw.Draw(image)
    warning_font = load_font(25, bold=True)
    title_font = load_font(38, bold=True)
    subtitle_font = load_font(24)
    header_font = load_font(21, bold=True)
    body_font = load_font(20)
    small_font = load_font(17)

    draw.rectangle((0, 0, image.width, 62), fill=(142, 0, 0))
    draw.text((20, 16), WARNING, fill="white", font=warning_font)
    draw.text(
        (45, 92),
        "V9W - couverture des escaliers F93-F99 par plans architecturaux cibles",
        fill=(10, 25, 45),
        font=title_font,
    )
    draw.text(
        (45, 146),
        "Identifiants visibles 1/2/3; jointure documentaire NIST: 1=A, 2=C, 3=B",
        fill=(70, 70, 70),
        font=subtitle_font,
    )

    columns = [
        ("Niveau", 45, 130),
        ("Plan etage", 175, 235),
        ("Plan noyau", 410, 235),
        ("Portee du plan noyau", 645, 470),
        ("IDs visibles", 1115, 235),
        ("Effet documentaire", 1350, 690),
    ]
    table_top = 205
    header_h = 58
    row_h = 74
    for label, x, width in columns:
        draw.rectangle((x, table_top, x + width, table_top + header_h), fill=(35, 62, 91), outline="white")
        bbox = draw.textbbox((0, 0), label, font=header_font)
        draw.text(
            (x + (width - (bbox[2] - bbox[0])) / 2, table_top + 16),
            label,
            fill="white",
            font=header_font,
        )

    for index, mapping in enumerate(mappings):
        y = table_top + header_h + index * row_h
        exact = mapping["core_coverage_kind"] == "TITLED_SINGLE_FLOOR"
        background = (226, 243, 229) if exact else (242, 236, 211)
        effect = (
            "Plan individuel du noyau"
            if exact
            else "Couverture explicite par plage de niveaux"
        )
        if mapping["floor"] in (94, 95):
            effect += "; Stair 2 documente C sans recreer le marqueur de dommage NIST"
        elif mapping["floor"] in (98, 99):
            effect += "; comble l'absence de panneau NIST au niveau du plan nominal"
        values = [
            f"F{mapping['floor']}",
            mapping["floor_plan_sheet"].replace(".tif", ""),
            mapping["core_plan_sheet"].replace(".tif", ""),
            mapping["core_plan_title_scope"],
            "1 / 2 / 3",
            effect,
        ]
        for value, (_, x, width) in zip(values, columns):
            draw.rectangle((x, y, x + width, y + row_h), fill=background, outline=(215, 215, 215), width=2)
            font = small_font if width >= 470 else body_font
            lines = fit_text(draw, value, font, width - 18)[:3]
            total_h = len(lines) * 21
            for line_index, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                draw.text(
                    (x + (width - (bbox[2] - bbox[0])) / 2, y + (row_h - total_h) / 2 + line_index * 21),
                    line,
                    fill=(25, 25, 25),
                    font=font,
                )

    boundary_y = table_top + header_h + len(mappings) * row_h + 28
    cards = [
        (
            "ETABLI",
            "7 niveaux couverts; 21 identifiants de cage lies; cartouches WTC/Port Authority visibles.",
            (205, 234, 208),
        ),
        (
            "NON ETABLI",
            "Originalite materielle, chaine de possession, statut as-built, coordonnees et dimensions transcrites.",
            (250, 221, 193),
        ),
        (
            "INTERDIT EN V9W",
            "Conversion pixel/pouce, mise a jour LOW/BASE/HIGH, dommage, masse, rigidite, resistance ou chemin de charge.",
            (244, 201, 201),
        ),
    ]
    card_w = 725
    for card_index, (label, text, fill) in enumerate(cards):
        x = 45 + card_index * (card_w + 28)
        draw.rounded_rectangle((x, boundary_y, x + card_w, boundary_y + 180), radius=18, fill=fill, outline=(100, 100, 100), width=2)
        draw.text((x + 22, boundary_y + 18), label, fill=(35, 35, 35), font=header_font)
        lines = fit_text(draw, text, body_font, card_w - 44)
        for line_index, line in enumerate(lines[:5]):
            draw.text((x + 22, boundary_y + 58 + line_index * 25), line, fill=(35, 35, 35), font=body_font)

    thumb_y = boundary_y + 225
    draw.text(
        (45, thumb_y - 42),
        "Apercus de controle des quatre feuilles de noyau (miniatures seulement; aucune mesure de pixels)",
        fill=(60, 60, 60),
        font=header_font,
    )
    thumb_specs = [
        ("A-A-148", "F89-F93", (350, 480, 3200, 2980)),
        ("A-A-150", "F94", (300, 450, 3300, 2900)),
        ("A-A-151", "F95", (300, 400, 3300, 2900)),
        ("A-A-153", "F96-F100", (300, 450, 3500, 3000)),
    ]
    thumb_size = (535, 390)
    for thumb_index, (sheet, scope, crop_box) in enumerate(thumb_specs):
        x = 45 + thumb_index * 575
        thumb = make_core_thumbnail(copy_root / f"{sheet}.tif", crop_box, thumb_size)
        image.paste(thumb, (x, thumb_y))
        draw.rectangle((x, thumb_y, x + thumb_size[0], thumb_y + thumb_size[1]), outline=(90, 90, 90), width=2)
        draw.rectangle((x, thumb_y + thumb_size[1] - 42, x + thumb_size[0], thumb_y + thumb_size[1]), fill=(255, 255, 255))
        draw.text((x + 12, thumb_y + thumb_size[1] - 34), f"{sheet} - {scope}", fill=(25, 25, 25), font=small_font)

    footer = (
        f"PASS documentaire attendu: {counts['nominal_plan_coverage_floor_count']} niveaux, "
        f"{counts['visible_plan_identifier_record_count']} identifiants; "
        "0 coordonnee, 0 geometrie de modele, 0 credit physique."
    )
    draw.text((45, 1653), footer, fill=(90, 0, 0), font=small_font)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def main() -> int:
    config = read_json(CONFIG_PATH)
    generated_at = utc_now()
    outputs = {name: ROOT / value for name, value in config["outputs"].items() if name != "figure_directory"}
    figure_directory = ROOT / config["outputs"]["figure_directory"]
    figure_directory.mkdir(parents=True, exist_ok=True)

    regression_checks = resolve_relative_map(config["regression_files"])
    protected_before = resolve_relative_map(config["protected_files"])

    archive_root = Path(config["archive_source"]["root"])
    copy_root = ROOT / config["archive_source"]["workspace_copy_directory"]
    source_before: list[dict[str, Any]] = []
    copy_checks: list[dict[str, Any]] = []
    for name, expected in config["archive_files"].items():
        source_before.append(inspect_source_file(archive_root / name, expected, "read_only_archive_source"))
        copy_checks.append(inspect_source_file(copy_root / name, expected, "workspace_binary_copy"))

    v9v = read_json(V9V_MATRIX_PATH)
    v9v_index = {(int(row["floor"]), row["stair"]): row for row in v9v["records"]}
    aliases = {key: int(value) for key, value in config["audit"]["plan_numeric_aliases"].items()}
    mappings = list(config["audit"]["floor_sheet_mapping"])
    variants = list(config["audit"]["variant_order"])
    physical = config["audit"]["assigned_physical_properties"]

    records: list[dict[str, Any]] = []
    for mapping in mappings:
        floor = int(mapping["floor"])
        for stair in config["audit"]["stair_order"]:
            number = aliases[stair]
            prior = v9v_index[(floor, stair)]
            identifier_visible = number in mapping["visible_plan_stair_numbers"]
            if floor in (94, 95) and stair == "C":
                effect = "NOMINAL_PLAN_LOCATION_DOCUMENTED_V9V_DAMAGE_MARKER_REMAINS_UNRECOVERABLE"
            elif floor in (98, 99):
                effect = "NOMINAL_PLAN_RANGE_COVERAGE_DOCUMENTED_NO_FIGURE_9_124_PANEL"
            else:
                effect = "NOMINAL_PLAN_CROSS_CHECK_DOCUMENTED"
            records.append(
                {
                    "floor": floor,
                    "stair": stair,
                    "plan_stair_number": number,
                    "floor_plan_sheet": mapping["floor_plan_sheet"],
                    "core_plan_sheet": mapping["core_plan_sheet"],
                    "core_coverage_kind": mapping["core_coverage_kind"],
                    "plan_identifier_visible": identifier_visible,
                    "nominal_drawing_location_documented": identifier_visible,
                    "v9v_figure_9_124_marker_visibility": prior["figure_9_124_marker_visibility"],
                    "v9v_source_visible_marker": prior["source_visible_marker"],
                    "v9w_documentary_effect": effect,
                    "official_model_damage_marker_gap_closed": False,
                    "drawing_status": config["audit"]["drawing_status"],
                    "drawing_scale_transcription": config["audit"]["drawing_scale_transcription"],
                    "scan_pixel_to_physical_conversion_used": False,
                    "numeric_dimension_extracted": False,
                    "model_geometry_promoted": False,
                    "variant_status": config["audit"]["variant_status"],
                    "mass_kg": physical["mass_kg"],
                    "stiffness_n_per_m": physical["stiffness_n_per_m"],
                    "strength_n": physical["strength_n"],
                    "connection_credit": physical["connection_credit"],
                    "load_path_credit": physical["load_path_credit"],
                    "component_damage_credit": physical["component_damage_credit"],
                    "limitation": (
                        "Visible nominal drawing identifier only; no scan-derived coordinate, "
                        "as-built certification, physical property or damage validation."
                    ),
                }
            )

    visible_records = [row for row in records if row["plan_identifier_visible"]]
    nominal_coverage_floors = sorted(
        {row["floor"] for row in records if row["nominal_drawing_location_documented"]}
    )
    single_floor_floors = [
        int(row["floor"]) for row in mappings if row["core_coverage_kind"] == "TITLED_SINGLE_FLOOR"
    ]
    multi_floor_floors = [
        int(row["floor"]) for row in mappings if row["core_coverage_kind"] == "TITLED_MULTI_FLOOR_RANGE"
    ]
    missing_marker_records = [
        row
        for row in records
        if row["v9v_figure_9_124_marker_visibility"] == "NOT_RECOVERABLE_AMID_MODELED_DISRUPTION"
    ]
    no_panel_floors = sorted(
        {
            row["floor"]
            for row in records
            if row["v9v_figure_9_124_marker_visibility"] == "NO_FLOOR_SPECIFIC_PANEL"
        }
    )
    numeric_dimension_count = sum(bool(row["numeric_dimension_extracted"]) for row in records)
    pixel_coordinate_count = sum(bool(row["scan_pixel_to_physical_conversion_used"]) for row in records)
    promoted_count = sum(bool(row["model_geometry_promoted"]) for row in records)
    counts = {
        "archive_source_file_count": len(source_before),
        "workspace_source_copy_count": len(copy_checks),
        "relevant_floor_and_core_plan_sheet_count": sum(
            1 for entry in config["archive_files"].values() if entry["role"] in {"floor plan", "core plan"}
        ),
        "supporting_schedule_and_section_sheet_count": sum(
            1
            for entry in config["archive_files"].values()
            if entry["role"] in {"drawing schedule", "supporting stair sections"}
        ),
        "floor_count": len(mappings),
        "stair_count": len(config["audit"]["stair_order"]),
        "floor_stair_record_count": len(records),
        "visible_plan_identifier_record_count": len(visible_records),
        "nominal_plan_coverage_floor_count": len(nominal_coverage_floors),
        "single_floor_core_sheet_floor_count": len(single_floor_floors),
        "multi_floor_core_sheet_floor_count": len(multi_floor_floors),
        "v9v_missing_marker_gap_count": len(missing_marker_records),
        "plan_location_documented_for_v9v_missing_marker_gap_count": sum(
            bool(row["nominal_drawing_location_documented"]) for row in missing_marker_records
        ),
        "v9v_no_panel_floor_count": len(no_panel_floors),
        "plan_band_coverage_for_v9v_no_panel_floor_count": sum(
            1
            for floor in no_panel_floors
            if next(row for row in mappings if int(row["floor"]) == floor)["core_coverage_kind"]
            == "TITLED_MULTI_FLOOR_RANGE"
        ),
        "numeric_dimension_extraction_count": numeric_dimension_count,
        "scan_pixel_coordinate_count": pixel_coordinate_count,
        "model_geometry_promoted_record_count": promoted_count,
        "variant_count": len(variants),
    }
    matrix_fingerprint = canonical_sha256(records)

    draw_contact_sheet(outputs["contact_sheet"], mappings, copy_root, counts)

    source_after: list[dict[str, Any]] = []
    for name, expected in config["archive_files"].items():
        source_after.append(inspect_source_file(archive_root / name, expected, "read_only_archive_source_after"))
    protected_after = resolve_relative_map(config["protected_files"])

    source_unchanged = all(
        before["observed_sha256"] == after["observed_sha256"]
        for before, after in zip(source_before, source_after)
    )
    protected_unchanged = all(
        before["observed_sha256"] == after["observed_sha256"]
        for before, after in zip(protected_before, protected_after)
    )
    source_copy_match = all(
        source["observed_sha256"] == copy["observed_sha256"]
        for source, copy in zip(source_before, copy_checks)
    )

    gates = config["gates"]
    checks = {
        "regression_hashes": len(regression_checks) == gates["regression_hash_count_expected"] and all(row["pass"] for row in regression_checks),
        "archive_source_files": len(source_before) == gates["archive_source_file_count_expected"] and all(row["pass"] for row in source_before),
        "workspace_source_copies": len(copy_checks) == gates["workspace_source_copy_count_expected"] and all(row["pass"] for row in copy_checks),
        "source_copy_hash_identity": source_copy_match,
        "archive_sources_unchanged": source_unchanged,
        "protected_blender_master_unchanged": protected_unchanged and all(row["pass"] for row in protected_after),
        "relevant_plan_sheet_count": counts["relevant_floor_and_core_plan_sheet_count"] == gates["relevant_floor_and_core_plan_sheet_count_expected"],
        "supporting_sheet_count": counts["supporting_schedule_and_section_sheet_count"] == gates["supporting_schedule_and_section_sheet_count_expected"],
        "floor_count": counts["floor_count"] == gates["floor_count_expected"],
        "stair_count": counts["stair_count"] == gates["stair_count_expected"],
        "floor_stair_record_count": counts["floor_stair_record_count"] == gates["floor_stair_record_count_expected"],
        "visible_plan_identifiers": counts["visible_plan_identifier_record_count"] == gates["visible_plan_identifier_record_count_expected"],
        "nominal_plan_floor_coverage": counts["nominal_plan_coverage_floor_count"] == gates["nominal_plan_coverage_floor_count_expected"],
        "single_floor_core_sheet_coverage": counts["single_floor_core_sheet_floor_count"] == gates["single_floor_core_sheet_floor_count_expected"],
        "multi_floor_core_sheet_coverage": counts["multi_floor_core_sheet_floor_count"] == gates["multi_floor_core_sheet_floor_count_expected"],
        "v9v_missing_marker_gap_count": counts["v9v_missing_marker_gap_count"] == gates["v9v_missing_marker_gap_count_expected"],
        "plan_location_for_v9v_missing_markers": counts["plan_location_documented_for_v9v_missing_marker_gap_count"] == gates["plan_location_documented_for_v9v_missing_marker_gap_count_expected"],
        "v9v_no_panel_floor_count": counts["v9v_no_panel_floor_count"] == gates["v9v_no_panel_floor_count_expected"],
        "plan_band_for_v9v_no_panel_floors": counts["plan_band_coverage_for_v9v_no_panel_floor_count"] == gates["plan_band_coverage_for_v9v_no_panel_floor_count_expected"],
        "no_numeric_dimension_extraction": numeric_dimension_count == gates["numeric_dimension_extraction_count_expected"],
        "no_scan_pixel_coordinates": pixel_coordinate_count == gates["scan_pixel_coordinate_count_expected"],
        "no_model_geometry_promotion": promoted_count == gates["model_geometry_promoted_record_count_expected"],
        "variant_separation_retained": len(variants) == gates["variant_count_expected"],
        "as_built_status_not_verified": False is gates["as_built_status_verified_expected"],
        "official_model_damage_marker_gap_not_closed": False is gates["official_model_damage_marker_gap_closed_expected"],
        "zero_physical_properties": all(value == 0.0 for value in physical.values()),
        "solver_and_blender_prohibited": not gates["global_solver_authorized"] and not gates["blender_authorized"],
    }
    overall_status = "PASS" if all(checks.values()) else "FAIL"

    evidence_matrix = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "source_semantics": config["audit"]["drawing_status"],
        "floor_range": [93, 99],
        "stair_order": config["audit"]["stair_order"],
        "plan_numeric_aliases": aliases,
        "variant_order": variants,
        "records": records,
        "counts": counts,
        "nominal_plan_coverage_floors": nominal_coverage_floors,
        "single_floor_core_sheet_floors": single_floor_floors,
        "multi_floor_core_sheet_floors": multi_floor_floors,
        "matrix_fingerprint_sha256": matrix_fingerprint,
        "model_geometry_promoted": False,
        "physical_validation": False,
    }

    identifier_audit = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "audit_type": "TARGETED_HASHED_ARCHIVE_DRAWING_IDENTIFIER_AUDIT",
        "manual_transcription_policy": config["audit"]["manual_transcription_policy"],
        "sheet_mapping": mappings,
        "alias_join": {
            "plan_identifiers": [1, 2, 3],
            "nist_aliases": aliases,
            "source": config["audit"]["alias_join_source"],
            "classification": "derived_cross_source_identifier_join",
        },
        "v9v_gap_effect": {
            "F94_C": "Stair 2 is visible on A-A-150; nominal plan location documented, NIST damage marker still unrecoverable.",
            "F95_C": "Stair 2 is visible on A-A-151; nominal plan location documented, NIST damage marker still unrecoverable.",
            "F98_F99": "A-A-152 and A-A-153 explicitly cover Floors 96-100; nominal plan coverage documented, no separate Figure 9-124 panel created.",
        },
        "counts": counts,
        "decision": {
            "nominal_drawing_identifier_evidence_qualified": overall_status == "PASS",
            "all_seven_floors_documented": len(nominal_coverage_floors) == 7,
            "all_three_plan_stair_identifiers_documented": len(visible_records) == 21,
            "scan_pixels_used_as_dimensions": False,
            "as_built_status_verified": False,
            "model_geometry_updated": False,
            "official_model_damage_marker_gap_closed": False,
        },
    }

    qualification = {
        "targeted_archive_plan_audit": overall_status == "PASS",
        "wtc_port_authority_title_block_characteristics_observed": True,
        "nominal_plan_identifier_evidence_floors_93_99": overall_status == "PASS",
        "stair_1_2_3_to_A_C_B_join": overall_status == "PASS",
        "v9v_F94_F95_C_nominal_plan_location_documented": overall_status == "PASS",
        "v9v_F98_F99_nominal_plan_band_coverage_documented": overall_status == "PASS",
        "originality_or_chain_of_custody_verified": False,
        "as_built_geometry": False,
        "numeric_dimension_chain": False,
        "scan_pixel_to_physical_transform": False,
        "model_geometry_promotion": False,
        "three_separate_hypothetical_variants_retained": True,
        "mechanical_properties": False,
        "load_path_credit": False,
        "component_damage_validation": False,
        "structural_solver": False,
        "blender": False,
        "physical_validation": False,
    }
    model_gate = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "checks": checks,
        "qualification": qualification,
        "decision": (
            "V9W qualifies the selected scans only as nominal WTC/Port Authority drawing evidence. "
            "It documents Stair 1, 2 and 3 across Floors 93-99 and closes the V9V documentary "
            "location gaps at drawing level, while leaving as-built, coordinate, damage and physical gates closed."
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
            "resolved_archive_directory": config["archive_source"]["root"],
            "targeted_scan_count": len(source_before),
            "all_source_hashes_and_dimensions_match": all(row["pass"] for row in source_before),
            "visible_wtc_port_authority_title_blocks": True,
            "visible_drawing_scale_transcription": config["audit"]["drawing_scale_transcription"],
            "sheet_titles": {
                name: metadata["title_transcription"] for name, metadata in config["archive_files"].items()
            },
            "visible_plan_stair_numbers": [1, 2, 3],
        },
        "official_model_results": {
            "nist_alias_join": aliases,
            "v9v_missing_markers": config["audit"]["v9v_prior_gaps"]["official_model_markers_not_recoverable"],
            "v9v_floors_without_panel": config["audit"]["v9v_prior_gaps"]["floors_without_figure_9_124_panel"],
            "official_model_damage_marker_gap_closed_by_plan_scans": False,
        },
        "archive_claims": [
            config["archive_source"]["archive_claim"],
            "V9W does not independently verify the word original or an as-built status.",
        ],
        "model_hypotheses": {
            "plan_number_to_letter_join_applied": True,
            "scan_pixel_coordinates_assumed": False,
            "unchanged_as_built_condition_assumed": False,
            "printed_scale_used_for_coordinate_generation": False,
            "low_base_high_retained_separately": True,
        },
        "derived_results": {
            **counts,
            "nominal_plan_coverage_floors": nominal_coverage_floors,
            "single_floor_core_sheet_floors": single_floor_floors,
            "multi_floor_core_sheet_floors": multi_floor_floors,
            "matrix_fingerprint_sha256": matrix_fingerprint,
        },
        "contradictions_and_missing_information": [
            "The user-described originality is not supported by an independently documented chain of custody.",
            "No as-built or record-drawing certification was verified on the inspected scans.",
            "Revision blocks are visible but were not exhaustively transcribed or reconciled in V9W.",
            "No printed dimension chain, coordinate or orientation anchor is numerically transcribed in V9W.",
            "A design-plan stair location cannot recreate a missing official-model damage marker or validate real component damage.",
            "The 96-100 sheets provide a titled floor range, not a distinct scanned plan panel for each of Floors 96-99.",
        ],
        "checks": checks,
        "model_gate": qualification,
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    write_json(outputs["evidence_matrix_json"], evidence_matrix)
    write_matrix_csv(outputs["evidence_matrix_csv"], records)
    write_json(outputs["identifier_audit"], identifier_audit)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)

    report_lines = [
        "# WTC 1 - V9W - audit cible des plans architecturaux d'escaliers, niveaux 93 a 99",
        "",
        f"**Validation generale : {overall_status}**",
        "",
        "> PLANS NOMINAUX DE DESSIN - PAS DE STATUT AS-BUILT VERIFIE - AUCUNE CONVERSION PIXEL/PHYSIQUE - ZERO CREDIT MECANIQUE OU DE DOMMAGE",
        "",
        "## Conclusion",
        "",
        "V9W est PASS comme audit documentaire cible. Les sept niveaux 93 a 99 sont couverts par des feuilles dont les cartouches nomment le World Trade Center et la Port of New York Authority. Les plans de noyau montrent Stair 1, Stair 2 et Stair 3; la jointure deja documentee par NIST les associe respectivement a A, C et B. Cette nouvelle preuve comble les lacunes de localisation nominale de V9V, sans transformer les scans en geometrie as-built, en coordonnees de modele ou en validation du dommage.",
        "",
        "## 1. Faits directement observes ou transcrits",
        "",
        f"- Le chemin reel trouve dans le dossier parent est `{config['archive_source']['root']}`; le chemin imbrique fourni ne correspondait pas a un dossier existant.",
        "- Dix TIFF cibles ont ete lus en lecture seule, copies bit a bit dans l'entree V9W et verifies par SHA-256; aucune enumeration recursive de l'archive n'a ete effectuee.",
        "- A-A-147/148 couvrent 89-93, A-A-149/150/151 couvrent 94-95, et A-A-152/153 couvrent 96-100.",
        "- Les feuilles de noyau A-A-148, A-A-150, A-A-151 et A-A-153 montrent les identifiants Stair 1, Stair 2 et Stair 3.",
        "- Les cartouches visibles portent The World Trade Center, The Port of New York Authority, les numeros de plan, une echelle indiquee de 1/8 pouce pour 1 pied et des blocs de revision.",
        "- A-A-125 et A-A-126 contiennent des sections des escaliers 1, 2 et 3; V9W n'en extrait aucune cote numerique.",
        "",
        "## 2. Resultats d'un modele officiel",
        "",
        "- V9V avait transcrit la correspondance NIST 1=A, 2=C et 3=B et identifie deux marqueurs C non recuperables dans les panneaux de dommage F94 et F95.",
        "- Les plans montrent Stair 2 aux niveaux 94 et 95, ce qui documente une position nominale de dessin pour C; cela ne reconstruit pas les marqueurs de dommage NIST manquants.",
        "- Les plans 96-100 documentent les niveaux 98 et 99 absents de la Figure 9-124, mais ne creent pas de nouveau resultat de modele officiel.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "- L'utilisateur a presente le lot comme les plans originaux du WTC.",
        "- Les cartouches et numeros de feuilles sont compatibles avec des scans de plans architecturaux WTC/Port Authority. V9W ne verifie toutefois ni la chaine de possession, ni l'originalite materielle, ni un statut as-built.",
        "",
        "## 4. Hypotheses propres au modele",
        "",
        "- La jointure Stair 1/2/3 vers A/C/B est une jointure documentaire entre les identifiants des plans et la correspondance NIST deja verifiee.",
        "- Aucun pixel n'est converti en pouce, aucun contour n'est numerise et aucune cote non imprimee n'est inferee.",
        "- LOW, BASE et HIGH restent trois hypotheses separees; leurs placements V9T/V9U ne sont pas ajustes par V9W.",
        "- Aucune equivalence entre plan contractuel et etat reel du 11 septembre 2001 n'est supposee.",
        "",
        "## 5. Resultats derives",
        "",
        f"- Niveaux couverts par un plan nominal : {counts['nominal_plan_coverage_floor_count']} sur 7.",
        f"- Enregistrements niveau-cage avec identifiant visible : {counts['visible_plan_identifier_record_count']} sur 21.",
        "- F94-C et F95-C disposent maintenant d'une localisation nominale de plan, tout en conservant le statut de marqueur de dommage officiel non recuperable.",
        "- F98 et F99 disposent d'une couverture explicite par la plage 96-100, sans panneau distinct par niveau.",
        f"- Empreinte de la matrice : `{matrix_fingerprint}`.",
        "- Cotes numeriques extraites : 0; coordonnees issues des pixels : 0; geometries de modele promues : 0.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- Aucun cachet as-built ou record drawing et aucune chaine de provenance independante n'ont ete verifies.",
        "- Les blocs de revision visibles n'ont pas encore ete transcrits et reconcilies feuille par feuille.",
        "- La plage 96-100 est une feuille commune; elle n'etablit pas que toutes les modifications ulterieures ou conditions construites etaient identiques a chaque niveau.",
        "- Les dimensions imprimees et reperes de grille devront etre transcrits et contre-verifies avant toute geometrie nominale chiffre.",
        "- Une geometrie de plan ne valide ni masse, rigidite, resistance, connexion, dommage, chemin de charge ni mecanisme d'effondrement.",
        "",
        "## Portes de validation",
        "",
    ]
    for name, passed in checks.items():
        report_lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "Le fichier Blender maitre conserve son empreinte protegee. Aucun solveur, aucun processus Blender et aucun acces reseau n'ont ete executes.",
            "",
            "## Livrables",
            "",
            f"- Matrice JSON : `{rel(outputs['evidence_matrix_json'])}`",
            f"- Matrice CSV : `{rel(outputs['evidence_matrix_csv'])}`",
            f"- Audit des identifiants : `{rel(outputs['identifier_audit'])}`",
            f"- Porte modele : `{rel(outputs['model_gate'])}`",
            f"- Planche de controle : `{rel(outputs['contact_sheet'])}`",
            "",
            "## Etape suivante pre-declaree - V9X",
            "",
            config["next_iteration"]["objective"],
            "",
        ]
    )
    outputs["report"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report"].write_text("\n".join(report_lines), encoding="utf-8", newline="\n")

    generated_files = [
        outputs["evidence_matrix_json"],
        outputs["evidence_matrix_csv"],
        outputs["identifier_audit"],
        outputs["model_gate"],
        outputs["contact_sheet"],
        outputs["results"],
        outputs["report"],
    ]
    manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "status": overall_status,
        "source_archive_read": True,
        "source_archive_targeted_file_count": len(source_before),
        "source_archive_rescanned": False,
        "source_archive_files_modified": False,
        "targeted_binary_copies_created": True,
        "network_access_used": False,
        "solver_executed": False,
        "blender_executed": False,
        "model_geometry_promoted": False,
        "regression_files": regression_checks,
        "archive_sources_before": source_before,
        "archive_sources_after": source_after,
        "workspace_source_copies": copy_checks,
        "source_copy_hash_identity": source_copy_match,
        "protected_files_before": protected_before,
        "protected_files_after": protected_after,
        "manual_transcription_policy": config["audit"]["manual_transcription_policy"],
        "matrix_fingerprint_sha256": matrix_fingerprint,
        "generated_files": [
            {"path": rel(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in generated_files
        ],
    }
    write_json(outputs["source_manifest"], manifest)

    print(
        json.dumps(
            {
                "iteration": config["iteration"],
                "status": overall_status,
                "targeted_source_file_count": len(source_before),
                "floor_count": counts["floor_count"],
                "visible_plan_identifier_record_count": counts["visible_plan_identifier_record_count"],
                "nominal_plan_coverage_floors": nominal_coverage_floors,
                "numeric_dimension_extraction_count": numeric_dimension_count,
                "model_geometry_promoted_record_count": promoted_count,
                "matrix_fingerprint_sha256": matrix_fingerprint,
                "checks": checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
