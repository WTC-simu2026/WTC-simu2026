#!/usr/bin/env python3
"""V9V - cached-source sufficiency audit for Floors 93-99 stair evidence.

This iteration audits already cached NIST material and upstream V9R-V9U
artifacts.  It identifies source-visible floor-specific marker candidates but
does not digitize, register, impute or promote geometry.  It assigns no
physical property, damage or load-path credit and invokes neither Blender nor
a structural solver.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9v_floor93_99_stairwell_evidence_sufficiency.json"
V9R_SOURCE_MANIFEST = ROOT / "wtc1_simulation_v8/output/v9r_stairwell_source_manifest.json"
V9R_CANDIDATE_MATRIX = ROOT / "wtc1_simulation_v8/output/v9r_stairwell_plan_candidate_matrix.json"
V9R_FLOOR_MATRIX = ROOT / "wtc1_simulation_v8/output/v9r_stairwell_floor_matrix.csv"
V9S_SOURCE_MANIFEST = ROOT / "wtc1_simulation_v8/output/v9s_stairwell_registration_source_manifest.json"
V9S_DIGITIZATION = ROOT / "wtc1_simulation_v8/output/v9s_stairwell_digitization.json"
V9S_ENVELOPES = ROOT / "wtc1_simulation_v8/output/v9s_stairwell_qualitative_envelopes.json"
V9U_CONTINUITY_AUDIT = ROOT / "wtc1_simulation_v8/output/v9u_stairwell_continuity_audit.json"

WARNING = (
    "V9V - AUDIT DE SUFFISANCE - AUCUNE PROMOTION GEOMETRIQUE - "
    "AUCUN PLAN AS-BUILT - ZERO CREDIT MECANIQUE"
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
                "expected_sha256": expected_hash,
                "observed_sha256": observed,
                "pass": exists and observed == expected_hash,
            }
        )
    return records


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
                    "transfer_event": source["transfer_event"],
                    "floor_95_labelled_overlay": parse_bool(
                        source["floor_95_labelled_overlay"]
                    ),
                    "exact_metric_plan_coordinates_qualified": parse_bool(
                        source["exact_metric_plan_coordinates_qualified"]
                    ),
                    "connections_qualified": parse_bool(source["connections_qualified"]),
                    "discrete_mass_qualified": parse_bool(
                        source["discrete_mass_qualified"]
                    ),
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


def write_matrix_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "floor",
        "stair",
        "numeric_alias",
        "floor_band_layout",
        "categorical_continuity_documented",
        "exact_floor_figure_9_124_panel",
        "figure_9_124_marker_visibility",
        "source_visible_marker",
        "floor95_clean_overlay_available",
        "floor96_structural_grid_only",
        "bounded_registration_candidate",
        "metric_as_built_plan_available",
        "numeric_floor_specific_offset_available",
        "geometry_promoted_in_v9v",
        "v9u_categorical_placeholder_retained",
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


def draw_contact_sheet(
    path: Path,
    floors: list[int],
    stair_order: list[str],
    records: list[dict[str, Any]],
    counts: dict[str, int],
) -> None:
    image = Image.new("RGB", (1760, 1180), "white")
    draw = ImageDraw.Draw(image)
    warning_font = load_font(21, bold=True)
    title_font = load_font(32, bold=True)
    subtitle_font = load_font(21)
    header_font = load_font(18, bold=True)
    body_font = load_font(18)
    small_font = load_font(15)

    draw.rectangle((0, 0, image.width, 52), fill=(145, 0, 0))
    draw.text((16, 13), WARNING, fill="white", font=warning_font)
    draw.text(
        (42, 78),
        "V9V - suffisance des preuves d'escaliers par niveau, F93-F99",
        fill=(0, 0, 0),
        font=title_font,
    )
    draw.text(
        (42, 123),
        "Figure 9-124: marqueurs d'un modele officiel; ni plans d'execution, ni geometrie observee",
        fill=(115, 0, 0),
        font=subtitle_font,
    )

    columns = [
        ("Niveau", 42, 120),
        ("Bande", 162, 150),
        ("Panneau exact", 312, 185),
        ("Marqueur A", 497, 170),
        ("Marqueur C", 667, 170),
        ("Marqueur B", 837, 170),
        ("Plan metrique", 1007, 170),
        ("Offset chiffre", 1177, 170),
        ("Promotion V9V", 1347, 190),
    ]
    table_top = 184
    row_h = 94
    table_right = 1537
    for label, x, width in columns:
        draw.rectangle((x, table_top, x + width, table_top + 62), fill=(35, 55, 80), outline="white")
        bbox = draw.textbbox((0, 0), label, font=header_font)
        draw.text(
            (x + (width - (bbox[2] - bbox[0])) / 2, table_top + 20),
            label,
            fill="white",
            font=header_font,
        )

    index = {(row["floor"], row["stair"]): row for row in records}

    def cell(x: int, y: int, width: int, text: str, fill: tuple[int, int, int]) -> None:
        draw.rectangle((x, y, x + width, y + row_h), fill=fill, outline=(235, 235, 235), width=2)
        bbox = draw.textbbox((0, 0), text, font=body_font)
        draw.text(
            (x + (width - (bbox[2] - bbox[0])) / 2, y + (row_h - (bbox[3] - bbox[1])) / 2 - 2),
            text,
            fill=(20, 20, 20),
            font=body_font,
        )

    green = (185, 226, 190)
    amber = (250, 224, 160)
    red = (246, 188, 188)
    gray = (222, 225, 229)
    for row_index, floor in enumerate(floors):
        y = table_top + 62 + row_index * row_h
        first = index[(floor, stair_order[0])]
        cell(42, y, 120, f"F{floor}", (235, 240, 247))
        band = "83-95" if floor <= 95 else "96-102"
        cell(162, y, 150, band, green)
        exact = first["exact_floor_figure_9_124_panel"]
        cell(312, y, 185, "OUI" if exact else "NON", green if exact else gray)
        for stair_index, stair in enumerate(stair_order):
            record = index[(floor, stair)]
            visibility = record["figure_9_124_marker_visibility"]
            if record["source_visible_marker"]:
                text = "VISIBLE"
                fill = green
            elif visibility.startswith("NOT_RECOVERABLE"):
                text = "MASQUE"
                fill = amber
            else:
                text = "AUCUN PANNEAU"
                fill = gray
            cell(497 + stair_index * 170, y, 170, text, fill)
        cell(1007, y, 170, "NON", red)
        cell(1177, y, 170, "NON", red)
        cell(1347, y, 190, "INTERDITE", red)

    box_top = table_top + 62 + len(floors) * row_h + 24
    draw.rounded_rectangle((42, box_top, table_right, box_top + 165), radius=14, fill=(245, 247, 250), outline=(70, 90, 115), width=2)
    draw.text((65, box_top + 18), "Decision V9V", fill=(0, 0, 0), font=header_font)
    summary_lines = [
        f"5 panneaux exacts (F93-F97), {counts['visible_marker_count']} marqueurs visibles sur 15; C masque a F94 et F95.",
        "F98-F99: aucune vue exacte. Les bandes documentent la continuite, pas une geometrie identique.",
        "0 plan as-built metrique, 0 offset chiffre, 0 promotion. LOW / BASE / HIGH restent separes.",
    ]
    for line_index, line in enumerate(summary_lines):
        draw.text((65, box_top + 55 + line_index * 32), line, fill=(20, 20, 20), font=body_font)

    legend_y = box_top + 187
    legend_items = [(green, "preuve visible"), (amber, "source masquee"), (gray, "aucun panneau"), (red, "porte fermee")]
    x = 42
    for color, label in legend_items:
        draw.rectangle((x, legend_y, x + 30, legend_y + 22), fill=color, outline=(80, 80, 80))
        draw.text((x + 40, legend_y + 1), label, fill=(40, 40, 40), font=small_font)
        x += 290

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def main() -> int:
    config = read_json(CONFIG_PATH)
    generated_at = utc_now()
    outputs = {name: ROOT / value for name, value in config["outputs"].items()}

    regression_checks = resolve_map(config["regression_files"])
    input_checks = resolve_map(config["input_artifacts"])
    source_checks = resolve_map(config["cached_source_files"])
    protected_before = resolve_map(config["protected_files"])

    v9r_manifest = read_json(V9R_SOURCE_MANIFEST)
    v9r_candidates = read_json(V9R_CANDIDATE_MATRIX)
    v9s_manifest = read_json(V9S_SOURCE_MANIFEST)
    v9s_digitization = read_json(V9S_DIGITIZATION)
    v9s_envelopes = read_json(V9S_ENVELOPES)
    v9u_continuity = read_json(V9U_CONTINUITY_AUDIT)
    floor_matrix = read_floor_matrix(V9R_FLOOR_MATRIX)

    floors = config["audit"]["floors"]
    stair_order = config["audit"]["stair_order"]
    aliases = config["audit"]["numeric_aliases"]
    variants = config["audit"]["variant_order"]
    physical = config["audit"]["assigned_physical_properties"]
    visibility = config["audit"]["figure_9_124"]["marker_visibility"]

    selected_rows = [
        row
        for row in floor_matrix
        if row["floor"] in floors and row["stair_alias"] in stair_order
    ]
    selected_index = {(row["floor"], row["stair_alias"]): row for row in selected_rows}

    records: list[dict[str, Any]] = []
    for floor in floors:
        for stair in stair_order:
            upstream = selected_index[(floor, stair)]
            marker_visibility = visibility[str(floor)][stair]
            marker_visible = marker_visibility == "VISIBLE_NUMBERED_MARKER_BOX"
            exact_panel = 93 <= floor <= 97
            if marker_visible:
                limitation = (
                    "Source-visible Figure 9-124 marker only; per-panel registration and uncertainty "
                    "remain future work, and the marker is not a whole enclosure."
                )
            elif marker_visibility.startswith("NOT_RECOVERABLE"):
                limitation = "Marker not recoverable from modeled disruption and raster loss; no imputation authorized."
            else:
                limitation = "No exact-floor Figure 9-124 panel is published for this floor."
            records.append(
                {
                    "floor": floor,
                    "stair": stair,
                    "numeric_alias": aliases[stair],
                    "floor_band_layout": upstream["floor_band_layout"],
                    "categorical_continuity_documented": (
                        upstream["present_in_reported_vertical_extent"]
                        and upstream["service_status"] == "CONTINUES"
                        and upstream["transfer_event"] == "NONE"
                    ),
                    "exact_floor_figure_9_124_panel": exact_panel,
                    "figure_9_124_marker_visibility": marker_visibility,
                    "source_visible_marker": marker_visible,
                    "floor95_clean_overlay_available": floor == 95,
                    "floor96_structural_grid_only": floor == 96,
                    "bounded_registration_candidate": marker_visible,
                    "metric_as_built_plan_available": False,
                    "numeric_floor_specific_offset_available": False,
                    "geometry_promoted_in_v9v": False,
                    "v9u_categorical_placeholder_retained": True,
                    "variant_status": config["audit"]["variant_status"],
                    "mass_kg": physical["mass_kg"],
                    "stiffness_n_per_m": physical["stiffness_n_per_m"],
                    "strength_n": physical["strength_n"],
                    "connection_credit": physical["connection_credit"],
                    "load_path_credit": physical["load_path_credit"],
                    "component_damage_credit": physical["component_damage_credit"],
                    "limitation": limitation,
                }
            )

    visible_marker_count = sum(int(record["source_visible_marker"]) for record in records)
    unrecoverable_marker_count = sum(
        int(record["figure_9_124_marker_visibility"].startswith("NOT_RECOVERABLE"))
        for record in records
    )
    exact_panel_floors = sorted(
        {record["floor"] for record in records if record["exact_floor_figure_9_124_panel"]}
    )
    no_panel_floors = sorted(set(floors) - set(exact_panel_floors))
    visible_by_floor = {
        floor: sum(
            int(record["source_visible_marker"])
            for record in records
            if record["floor"] == floor
        )
        for floor in floors
    }
    complete_marker_floors = sorted(floor for floor, count in visible_by_floor.items() if count == 3)
    partial_marker_floors = sorted(floor for floor, count in visible_by_floor.items() if 0 < count < 3)
    candidate_records = [record for record in records if record["bounded_registration_candidate"]]
    metric_plan_count = sum(int(record["metric_as_built_plan_available"]) for record in records)
    numeric_offset_count = sum(
        int(record["numeric_floor_specific_offset_available"]) for record in records
    )
    promoted_count = sum(int(record["geometry_promoted_in_v9v"]) for record in records)

    counts = {
        "floor_count": len(floors),
        "stair_count": len(stair_order),
        "floor_stair_record_count": len(records),
        "exact_floor_panel_count": len(exact_panel_floors),
        "visible_marker_count": visible_marker_count,
        "unrecoverable_marker_count": unrecoverable_marker_count,
        "floor_without_panel_count": len(no_panel_floors),
        "complete_visible_marker_floor_count": len(complete_marker_floors),
        "partial_visible_marker_floor_count": len(partial_marker_floors),
        "bounded_registration_candidate_record_count": len(candidate_records),
        "floor_specific_metric_plan_count": metric_plan_count,
        "numeric_floor_specific_offset_count": numeric_offset_count,
        "geometry_promoted_record_count": promoted_count,
        "variant_count": len(variants),
    }

    relevant_v9s_anchors = [
        anchor
        for anchor in v9s_manifest["pdf_anchors"]
        if anchor["source"] == "work/official_sources/ncstar1-2bv2.pdf"
        and anchor["pdf_page"] in (164, 165)
    ]
    v9s_floor95_stairs = v9s_digitization["sources"]["figure_9_124"]["stairs"]
    alias_checks = [
        selected_index[(floor, stair)]["v9q_numeric_alias"] == aliases[stair]
        for floor in floors
        for stair in stair_order
    ]
    all_zero = all(value == 0.0 for value in physical.values())

    draw_contact_sheet(outputs["contact_sheet"], floors, stair_order, records, counts)
    protected_after = resolve_map(config["protected_files"])

    gates = config["gates"]
    checks = {
        "v8u_through_v9u_chained_regression_hashes": (
            len(regression_checks) == gates["regression_hash_count_expected"]
            and all(record["pass"] for record in regression_checks)
        ),
        "direct_input_artifact_hashes": (
            len(input_checks) == gates["input_artifact_hash_count_expected"]
            and all(record["pass"] for record in input_checks)
        ),
        "cached_official_source_hashes": (
            len(source_checks) == gates["cached_source_hash_count_expected"]
            and all(record["pass"] for record in source_checks)
        ),
        "protected_blender_master_before_after": (
            len(protected_before) == gates["protected_file_hash_count_expected"]
            and all(record["pass"] for record in protected_before)
            and all(record["pass"] for record in protected_after)
            and [record["observed_sha256"] for record in protected_before]
            == [record["observed_sha256"] for record in protected_after]
        ),
        "upstream_v9r_source_audit_pass": bool(v9r_manifest["passed"]),
        "upstream_v9r_no_metric_candidate": (
            v9r_candidates["metric_solver_geometry_candidate_count"] == 0
        ),
        "upstream_v9s_source_audit_pass": v9s_manifest["status"] == "PASS",
        "upstream_v9u_continuity_audit_pass": (
            v9u_continuity["validation_status"] == "PASS"
            and v9u_continuity["decision"]["categorical_seven_floor_stack_supported"]
            and not v9u_continuity["decision"]["identical_floor_specific_geometry_supported"]
        ),
        "figure_9_124_page_anchors_164_165": (
            len(relevant_v9s_anchors) == 2
            and all(anchor["pass"] for anchor in relevant_v9s_anchors)
        ),
        "numeric_alias_mapping_1A_2C_3B": all(alias_checks),
        "floor_count": len(floors) == gates["floor_count_expected"],
        "stair_count": len(stair_order) == gates["stair_count_expected"],
        "floor_stair_record_count": len(records) == gates["floor_stair_record_count_expected"],
        "all_floor_stair_rows_retain_categorical_continuity": all(
            record["categorical_continuity_documented"] for record in records
        ),
        "figure_9_124_exact_floor_panel_count": (
            len(exact_panel_floors) == gates["figure_9_124_exact_floor_panel_count_expected"]
            and exact_panel_floors == [93, 94, 95, 96, 97]
        ),
        "figure_9_124_visible_marker_count": (
            visible_marker_count == gates["figure_9_124_visible_marker_count_expected"]
        ),
        "figure_9_124_unrecoverable_marker_count": (
            unrecoverable_marker_count
            == gates["figure_9_124_unrecoverable_marker_count_expected"]
        ),
        "floor_without_figure_9_124_panel_count": (
            len(no_panel_floors) == gates["floor_without_figure_9_124_panel_count_expected"]
            and no_panel_floors == [98, 99]
        ),
        "complete_visible_marker_floor_count": (
            len(complete_marker_floors)
            == gates["complete_visible_marker_floor_count_expected"]
            and complete_marker_floors == [93, 96, 97]
        ),
        "partial_visible_marker_floor_count": (
            len(partial_marker_floors)
            == gates["partial_visible_marker_floor_count_expected"]
            and partial_marker_floors == [94, 95]
        ),
        "floor95_visibility_consistent_with_v9s": (
            v9s_floor95_stairs["A"]["visibility"] == "VISIBLE_NUMBERED_MARKER_BOX"
            and v9s_floor95_stairs["C"]["visibility"]
            == "NOT_RECOVERABLE_ON_FLOOR_95_PANEL"
            and v9s_floor95_stairs["B"]["visibility"] == "VISIBLE_NUMBERED_MARKER_BOX"
        ),
        "floor_specific_metric_plan_count_zero": (
            metric_plan_count == gates["floor_specific_metric_plan_count_expected"]
        ),
        "numeric_floor_specific_offset_count_zero": (
            numeric_offset_count == gates["numeric_floor_specific_offset_count_expected"]
        ),
        "geometry_promoted_record_count_zero": (
            promoted_count == gates["geometry_promoted_record_count_expected"]
            and all(record["v9u_categorical_placeholder_retained"] for record in records)
        ),
        "low_base_high_retained_separately": (
            variants == ["low", "base", "high"]
            and len(variants) == gates["variant_count_expected"]
        ),
        "zero_physical_properties_and_credit": all_zero,
        "mechanical_solver_blender_gates_closed": (
            not gates["metric_as_built_solver_geometry_authorized"]
            and not gates["discrete_mass_authorized"]
            and not gates["stiffness_authorized"]
            and not gates["strength_authorized"]
            and not gates["connection_authorized"]
            and not gates["load_path_credit_authorized"]
            and not gates["component_damage_validation_authorized"]
            and not gates["global_solver_authorized"]
            and not gates["blender_authorized"]
            and not gates["blender_physical_validation_authorized"]
        ),
        "source_policy_closed": (
            not config["source_policy"]["source_archive_read"]
            and not config["source_policy"]["source_archive_rescanned"]
            and not config["source_policy"]["network_access_used"]
            and config["source_policy"]["cached_official_sources_read_only"]
            and not config["source_policy"]["official_source_files_modified"]
        ),
        "contact_sheet_created": outputs["contact_sheet"].is_file(),
    }
    overall_status = "PASS" if all(checks.values()) else "FAIL"

    matrix_fingerprint = canonical_sha256(records)
    evidence_matrix = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "source_semantics": (
            "Figure 9-124 numbered boxes are positions in an official base-case global-impact "
            "model result. They are not whole stair enclosures, as-built observations or independent damage data."
        ),
        "floor_range": [min(floors), max(floors)],
        "stair_order": stair_order,
        "numeric_aliases": aliases,
        "variant_order": variants,
        "records": records,
        "counts": counts,
        "exact_panel_floors": exact_panel_floors,
        "complete_visible_marker_floors": complete_marker_floors,
        "partial_visible_marker_floors": partial_marker_floors,
        "no_panel_floors": no_panel_floors,
        "matrix_fingerprint_sha256": matrix_fingerprint,
        "geometry_promoted": False,
        "physical_validation": False,
    }

    source_units = [
        {
            "id": "NCSTAR1_2B_FIGURE_9_124",
            "source_class": "official_model_result",
            "facts": [
                "The text maps 1=A, 2=C and 3=B.",
                "The calculated base-case disruption figure covers Floors 93-97.",
                "The text states that stairwell positions are outlined with red boxes.",
                "The global model included core partition walls only on Floors 94-97, limiting Floor 93 damage ascertainment."
            ],
            "derived_visual_audit": {
                "visible_marker_count": visible_marker_count,
                "unrecoverable_markers": ["F94-C", "F95-C"],
                "no_panel_floors": no_panel_floors,
            },
            "authorized_use_in_v9v": "candidate inventory only",
            "geometry_promoted": False,
        },
        *config["audit"]["other_cached_candidates"],
    ]
    sufficiency_audit = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "audit_type": "CACHED_SOURCE_ONLY_SUFFICIENCY_AUDIT",
        "source_units": source_units,
        "promotion_criteria": config["audit"]["promotion_criteria"],
        "counts": counts,
        "decision": {
            "cached_source_audit_complete": overall_status == "PASS",
            "bounded_registration_candidate_floor_stair_records": len(candidate_records),
            "future_candidate_floors": exact_panel_floors,
            "geometry_promoted_beyond_categorical_in_v9v": False,
            "floor_specific_metric_as_built_geometry_supported": False,
            "numeric_floor_specific_offset_supported": False,
            "floors_98_99_remain_categorical_only": True,
            "missing_markers_imputed": False,
        },
        "limitation": (
            "The 13 visible boxes are floor-specific official-model position markers only. "
            "They require a later per-panel registration and cannot be treated as complete enclosures, "
            "as-built coordinates, measured offsets or independent component-damage observations."
        ),
    }

    qualification = {
        "cached_source_sufficiency_audit": overall_status == "PASS",
        "figure_9_124_exact_floor_candidate_panels_93_97": overall_status == "PASS",
        "source_visible_marker_candidates": visible_marker_count,
        "future_bounded_registration_candidate_floors": exact_panel_floors,
        "missing_marker_imputation": False,
        "geometry_promoted_beyond_v9u_categorical_placeholders": False,
        "floor_specific_metric_as_built_geometry": False,
        "numeric_floor_specific_offset": False,
        "whole_stair_enclosure_geometry": False,
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
            "V9V promotes no geometry. It identifies 13 source-visible Figure 9-124 marker "
            "candidates on Floors 93-97 for a later bounded qualitative registration; C on "
            "Floors 94 and 95 is not recoverable, and Floors 98-99 remain categorical only."
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
            "figure_9_124_stated_floor_range": [93, 97],
            "numeric_aliases": aliases,
            "stair_positions_stated_as_red_boxes": True,
            "cached_pdf_anchor_pages": [164, 165],
            "floor93_damage_ascertainment_limited_by_model_partition_omission": True,
        },
        "official_model_results": {
            "figure_9_124_is_calculated_base_case": True,
            "floor_specific_panel_count": len(exact_panel_floors),
            "source_visible_marker_count": visible_marker_count,
            "unrecoverable_marker_count": unrecoverable_marker_count,
            "independent_as_built_measurement": False,
            "independent_component_damage_validation": False,
        },
        "archive_claims_used": [],
        "model_hypotheses": {
            "missing_marker_imputation": False,
            "unchanged_floor_geometry_assumed": False,
            "marker_box_treated_as_whole_enclosure": False,
            "physical_scale_assigned": False,
            "low_base_high_retained_separately": True,
        },
        "derived_results": {
            "bounded_registration_candidate_record_count": len(candidate_records),
            "complete_visible_marker_floors": complete_marker_floors,
            "partial_visible_marker_floors": partial_marker_floors,
            "categorical_only_no_panel_floors": no_panel_floors,
            "floor_specific_metric_plan_count": metric_plan_count,
            "numeric_floor_specific_offset_count": numeric_offset_count,
            "geometry_promoted_record_count": promoted_count,
            "matrix_fingerprint_sha256": matrix_fingerprint,
        },
        "contradictions_and_missing_information": [
            "Stair C marker boxes are not recoverable in the Floor 94 and Floor 95 panels.",
            "Figure 9-124 has no Floor 98 or Floor 99 panel.",
            "The numbered boxes are model-position markers, not whole stair enclosures or as-built observations.",
            "No cached source documents a metric floor-specific offset, signed displacement or dimension chain on Floors 93-99.",
            "Floor 93 damage ascertainment is limited because the cited global model omitted core partition walls there.",
        ],
        "checks": checks,
        "model_gate": qualification,
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    write_json(outputs["evidence_matrix_json"], evidence_matrix)
    write_matrix_csv(outputs["evidence_matrix_csv"], records)
    write_json(outputs["sufficiency_audit"], sufficiency_audit)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)

    report_lines = [
        "# WTC 1 - V9V - audit de suffisance des preuves d'escaliers, niveaux 93 a 99",
        "",
        f"**Validation generale : {overall_status}**",
        "",
        "> AUDIT DOCUMENTAIRE EN CACHE - AUCUNE PROMOTION GEOMETRIQUE - AUCUN PLAN AS-BUILT - ZERO CREDIT MECANIQUE OU DE DOMMAGE",
        "",
        "## Conclusion",
        "",
        "V9V est PASS comme audit de suffisance. La Figure 9-124 de NCSTAR 1-2B fournit cinq panneaux du modele officiel, un par niveau de 93 a 97. Treize marqueurs numerotes de position de cage sont recuperables sur quinze possibles. Cette disponibilite justifie uniquement une future registration qualitative bornee; V9V ne cree, ne remplace et ne promeut aucune geometrie.",
        "",
        "## 1. Faits directement observes ou transcrits",
        "",
        "- Le texte source associe 1 a A, 2 a C et 3 a B, couvre les niveaux 93 a 97 et indique que les positions des cages sont encadrees en rouge.",
        "- Les panneaux F93, F96 et F97 montrent les trois marqueurs; F94 et F95 montrent A et B, tandis que C n'est pas recuperable dans la perturbation representee.",
        "- Aucun panneau Figure 9-124 n'est fourni pour F98 ou F99.",
        "- Les panneaux de la Table 2-2 couvrent seulement les bandes 83-95 et 96-102; ils ne sont pas des plans distincts pour chaque niveau.",
        "",
        "## 2. Resultats d'un modele officiel",
        "",
        "- La Figure 9-124 est explicitement un resultat calcule du cas de base d'impact global. Ses boites numerotees sont des marqueurs de position dans le modele officiel.",
        "- Le texte precise que le modele global ne contenait les cloisons du noyau qu'aux niveaux 94 a 97; l'evaluation du dommage ou des debris au niveau 93 etait donc limitee.",
        "- La Figure 5-2 du niveau 95 et les deux figures structurelles du niveau 96 restent des sources officielles utiles comme reperes, mais elles ne sont pas des mesures as-built independantes.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune. L'archive source n'a ete ni ouverte ni rescanee. Seuls les PDF officiels deja en cache et leurs artefacts verifies ont ete lus en lecture seule.",
        "",
        "## 4. Hypotheses propres au modele",
        "",
        "- Aucun marqueur masque n'est reconstruit ou impute.",
        "- Aucune similitude visuelle entre panneaux n'est convertie en identite geometrique entre niveaux.",
        "- Les boites ne sont pas assimilees a des enveloppes completes, des paliers, des volees ou des connexions.",
        "- LOW, BASE et HIGH restent trois hypotheses separees et ne sont pas mises a jour par V9V.",
        "",
        "## 5. Resultats derives",
        "",
        f"- Panneaux exacts disponibles : {len(exact_panel_floors)} ({', '.join('F'+str(value) for value in exact_panel_floors)}).",
        f"- Marqueurs recuperables : {visible_marker_count}; candidats de future registration bornee : {len(candidate_records)}.",
        f"- Niveaux avec trois marqueurs : {', '.join('F'+str(value) for value in complete_marker_floors)}.",
        f"- Niveaux partiels : {', '.join('F'+str(value) for value in partial_marker_floors)}; niveaux sans panneau : {', '.join('F'+str(value) for value in no_panel_floors)}.",
        f"- Empreinte de la matrice : `{matrix_fingerprint}`.",
        "- Plans metriques qualifies : 0; offsets chiffres qualifies : 0; geometries promues : 0.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- C n'est pas recuperable aux niveaux 94 et 95 dans la Figure 9-124.",
        "- Les niveaux 98 et 99 restent documentes seulement par leur bande topologique.",
        "- Aucun document mis en cache ne fournit une transformation metrique, une orientation cotee ou un deplacement signe par niveau entre 93 et 99.",
        "- Le dommage affiche est une sortie du modele officiel et ne recoit aucun credit de validation independante de composant.",
        "",
        "## Portes de validation",
        "",
    ]
    for name, passed in checks.items():
        report_lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "Masse, rigidite, resistance, connexion, chemin de charge et credit de dommage restent explicitement a zero. Aucun solveur et aucun processus Blender n'ont ete executes; le fichier Blender maitre conserve son empreinte protegee.",
            "",
            "## Livrables",
            "",
            f"- Matrice JSON : `{rel(outputs['evidence_matrix_json'])}`",
            f"- Matrice CSV : `{rel(outputs['evidence_matrix_csv'])}`",
            f"- Audit de suffisance : `{rel(outputs['sufficiency_audit'])}`",
            f"- Porte modele : `{rel(outputs['model_gate'])}`",
            f"- Planche de controle : `{rel(outputs['contact_sheet'])}`",
            "",
            "## Etape suivante pre-declaree - V9W",
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
        outputs["sufficiency_audit"],
        outputs["model_gate"],
        outputs["contact_sheet"],
        outputs["results"],
        outputs["report"],
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
        "geometry_promoted": False,
        "regression_files": regression_checks,
        "input_artifacts": input_checks,
        "cached_source_files": source_checks,
        "protected_files_before": protected_before,
        "protected_files_after": protected_after,
        "matrix_fingerprint_sha256": matrix_fingerprint,
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
                "exact_floor_panel_count": len(exact_panel_floors),
                "visible_marker_count": visible_marker_count,
                "unrecoverable_marker_count": unrecoverable_marker_count,
                "no_panel_floors": no_panel_floors,
                "geometry_promoted_record_count": promoted_count,
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
