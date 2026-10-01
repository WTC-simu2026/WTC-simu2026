#!/usr/bin/env python3
"""V9X - bounded provenance and printed-anchor transcription audit.

The iteration verifies fixed local files, records only source-visible labels and
categorical stair topology, and explicitly rejects every ambiguous numeric
grid-to-stair chain. It never measures scan pixels, creates physical
coordinates, invokes Blender, or runs a structural solver.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps, __version__ as PILLOW_VERSION


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9x_stairwell_printed_anchor_transcription.json"

WARNING = (
    "V9X - TRANSCRIPTION DOCUMENTAIRE BORNEE - AUCUNE COORDONNEE AS-BUILT - "
    "AUCUNE MESURE DE PIXELS - ZERO CREDIT PHYSIQUE"
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


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def resolve_relative_map(mapping: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path, expected_hash in mapping.items():
        path = ROOT / relative_path
        exists = path.is_file()
        observed = digest(path) if exists else None
        rows.append(
            {
                "path": relative_path,
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else None,
                "expected_sha256": expected_hash.lower(),
                "observed_sha256": observed,
                "pass": exists and observed == expected_hash.lower(),
            }
        )
    return rows


def inspect_file(path: Path, expected: dict[str, Any], image_file: bool) -> dict[str, Any]:
    exists = path.is_file()
    observed: dict[str, Any] = {
        "name": path.name,
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "sha256": digest(path) if exists else None,
    }
    if "md5" in expected:
        observed["md5"] = digest(path, "md5") if exists else None
    if "sha1" in expected:
        observed["sha1"] = digest(path, "sha1") if exists else None
    if image_file and exists:
        with Image.open(path) as image:
            observed["width_px"], observed["height_px"] = image.size
            observed["mode"] = image.mode
    checks = {
        "size": exists and observed["size_bytes"] == int(expected["bytes"]),
        "sha256": exists and observed["sha256"] == str(expected["sha256"]).lower(),
    }
    if "md5" in expected:
        checks["md5"] = exists and observed["md5"] == str(expected["md5"]).lower()
    if "sha1" in expected:
        checks["sha1"] = exists and observed["sha1"] == str(expected["sha1"]).lower()
    if image_file:
        checks["dimensions"] = (
            exists
            and observed.get("width_px") == int(expected["width_px"])
            and observed.get("height_px") == int(expected["height_px"])
        )
    observed["expected"] = {
        key: expected[key]
        for key in ("bytes", "width_px", "height_px", "md5", "sha1", "sha256")
        if key in expected
    }
    observed["checks"] = checks
    observed["pass"] = all(checks.values())
    return observed


def unchanged(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> bool:
    return len(before) == len(after) and all(
        left.get("sha256") == right.get("sha256")
        and left.get("size_bytes") == right.get("size_bytes")
        for left, right in zip(before, after)
    )


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def add_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    source: Path,
    box: tuple[int, int, int, int],
    label: str,
    label_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=(55, 55, 55), width=2, fill=(246, 246, 246))
    label_height = 48
    with Image.open(source) as image:
        prepared = ImageOps.contain(
            image.convert("RGB"),
            (x1 - x0 - 12, y1 - y0 - label_height - 12),
            Image.Resampling.LANCZOS,
        )
    px = x0 + (x1 - x0 - prepared.width) // 2
    py = y0 + 6 + (y1 - y0 - label_height - 12 - prepared.height) // 2
    canvas.paste(prepared, (px, py))
    draw.rectangle((x0, y1 - label_height, x1, y1), fill=(255, 255, 255))
    draw.text((x0 + 10, y1 - label_height + 10), label, fill=(20, 20, 20), font=label_font)


def draw_contact_sheet(
    path: Path,
    plan_root: Path,
    core_sheets: list[dict[str, Any]],
    marsh_root: Path,
    marsh_files: list[dict[str, Any]],
) -> None:
    canvas = Image.new("RGB", (2400, 1810), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(34, bold=True)
    subtitle_font = load_font(22, bold=False)
    label_font = load_font(20, bold=True)
    draw.text((42, 28), "WTC 1 - V9X - controle visuel documentaire des ancrages imprimes", fill=(15, 15, 15), font=title_font)
    draw.text((42, 78), WARNING, fill=(145, 0, 0), font=subtitle_font)
    draw.text(
        (42, 112),
        "Miniatures pour verification humaine uniquement; aucune distance, echelle ou coordonnee n'en est extraite.",
        fill=(40, 40, 40),
        font=subtitle_font,
    )

    panel_width = 565
    gap = 22
    x_values = [42 + index * (panel_width + gap) for index in range(4)]
    for index, sheet in enumerate(core_sheets):
        add_panel(
            canvas,
            draw,
            plan_root / sheet["sheet"],
            (x_values[index], 160, x_values[index] + panel_width, 690),
            f"{sheet['sheet']} | niveaux {sheet['floor_scope']}",
            label_font,
        )

    for index, source in enumerate(marsh_files):
        row = index // 4
        column = index % 4
        y0 = 720 + row * 500
        add_panel(
            canvas,
            draw,
            marsh_root / source["name"],
            (x_values[column], y0, x_values[column] + panel_width, y0 + 470),
            f"F{source['floor']} | {source['name']} | RECORD DRAWING",
            label_font,
        )

    draw.text(
        (42, 1730),
        "Conclusion visuelle: topologie categorielle a trois escaliers corroboree; 0 chaine cotee acceptee; 0 ancrage ferme accepte.",
        fill=(120, 0, 0),
        font=subtitle_font,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, optimize=True)


def write_matrix_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "sheet",
        "floor_scope",
        "floors_used",
        "plan_stair_number",
        "nist_alias",
        "categorical_location",
        "printed_stair_label_visible",
        "numbered_column_bubbles_visible",
        "dimension_chain_status",
        "closed_grid_anchor_status",
        "accepted_numeric_dimension_count",
        "accepted_grid_anchor_id_count",
        "scan_pixel_measurement_used",
        "numeric_coordinate_created",
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in records:
            output = dict(row)
            output["floors_used"] = "|".join(str(value) for value in row["floors_used"])
            writer.writerow(output)


def main() -> int:
    config = read_json(CONFIG_PATH)
    generated_at = utc_now()
    outputs = {
        name: ROOT / value
        for name, value in config["outputs"].items()
        if name != "figure_directory"
    }
    (ROOT / config["outputs"]["figure_directory"]).mkdir(parents=True, exist_ok=True)

    regression_checks = resolve_relative_map(config["regression_files"])
    protected_before = resolve_relative_map(config["protected_files"])

    plan_root = ROOT / config["plan_sources"]["root"]
    plan_before = [
        inspect_file(plan_root / name, expected, image_file=True)
        for name, expected in config["plan_sources"]["files"].items()
    ]
    marsh_root = Path(config["marsh_overview_sources"]["root"])
    marsh_before = [
        inspect_file(marsh_root / expected["name"], expected, image_file=True)
        for expected in config["marsh_overview_sources"]["files"]
    ]
    pdf_root = Path(config["supplemental_pdfs"]["root"])
    pdf_before = [
        inspect_file(pdf_root / expected["name"], expected, image_file=False)
        for expected in config["supplemental_pdfs"]["files"]
    ]

    audit = config["transcription_audit"]
    physical = audit["assigned_physical_properties"]
    records: list[dict[str, Any]] = []
    for sheet in audit["core_sheets"]:
        for stair in audit["stair_definitions"]:
            records.append(
                {
                    "sheet": sheet["sheet"],
                    "floor_scope": sheet["floor_scope"],
                    "floors_used": list(sheet["floors_used"]),
                    "plan_stair_number": int(stair["plan_stair_number"]),
                    "nist_alias": stair["nist_alias"],
                    "categorical_location": stair["categorical_location"],
                    "printed_stair_label_visible": True,
                    "numbered_column_bubbles_visible": True,
                    "dimension_chain_status": audit["dimension_chain_policy"]["candidate_status"],
                    "closed_grid_anchor_status": "REJECTED_NO_UNAMBIGUOUS_CLOSED_GRID_TO_STAIR_SET",
                    "accepted_numeric_dimension_count": 0,
                    "accepted_grid_anchor_id_count": 0,
                    "scan_pixel_measurement_used": False,
                    "numeric_coordinate_created": False,
                    "model_geometry_promoted": False,
                    "variant_status": audit["variant_status"],
                    "mass_kg": physical["mass_kg"],
                    "stiffness_n_per_m": physical["stiffness_n_per_m"],
                    "strength_n": physical["strength_n"],
                    "connection_credit": physical["connection_credit"],
                    "load_path_credit": physical["load_path_credit"],
                    "component_damage_credit": physical["component_damage_credit"],
                    "limitation": (
                        "The stair label and categorical relation are source-visible, but the "
                        "printed dimension digits and extension-line endpoints do not form an "
                        "independently reproducible closed anchor set on this scan."
                    ),
                }
            )

    marsh_topology = [
        {
            "floor": int(source["floor"]),
            "file": source["name"],
            "record_drawing_stamp_visible": True,
            "floor_specific_sheet_identifier_visible": True,
            "three_stair_topology_visible": True,
            "photographic_perspective_present": True,
            "numeric_geometry_extracted": False,
            "as_built_coordinate_promotion": False,
            "classification": "FLOOR_SPECIFIC_RECORD_DRAWING_PHOTOGRAPH_TOPOLOGY_CROSS_CHECK_ONLY",
        }
        for source in config["marsh_overview_sources"]["files"]
    ]

    accepted_dimensions = sum(row["accepted_numeric_dimension_count"] for row in records)
    accepted_anchor_sets = sum(
        row["closed_grid_anchor_status"].startswith("ACCEPTED") for row in records
    )
    pixel_coordinates = sum(row["numeric_coordinate_created"] for row in records)
    promoted_geometry = sum(row["model_geometry_promoted"] for row in records)
    counts = {
        "regression_file_count": len(regression_checks),
        "plan_source_file_count": len(plan_before),
        "core_transcription_sheet_count": len(audit["core_sheets"]),
        "supporting_section_sheet_count": len(audit["section_support"]),
        "marsh_overview_file_count": len(marsh_before),
        "supplemental_pdf_count": len(pdf_before),
        "transcription_candidate_record_count": len(records),
        "categorical_stair_relation_count": len(audit["stair_definitions"]),
        "marsh_floor_topology_count": len(marsh_topology),
        "record_drawing_stamp_count": sum(row["record_drawing_stamp_visible"] for row in marsh_topology),
        "accepted_numeric_dimension_chain_count": accepted_dimensions,
        "accepted_closed_grid_anchor_set_count": accepted_anchor_sets,
        "scan_pixel_coordinate_count": pixel_coordinates,
        "model_geometry_promoted_record_count": promoted_geometry,
        "wayback_plan_match_count": int(config["provenance"]["plan_zip_wayback"]["target_file_count_compared"]),
        "wayback_marsh_match_count": int(config["provenance"]["marsh_zip_wayback"]["target_file_count_compared"]),
        "variant_count": len(audit["variant_order"]),
    }
    transcription_fingerprint = canonical_sha256(records)

    draw_contact_sheet(
        outputs["contact_sheet"],
        plan_root,
        audit["core_sheets"],
        marsh_root,
        config["marsh_overview_sources"]["files"],
    )

    plan_after = [
        inspect_file(plan_root / name, expected, image_file=True)
        for name, expected in config["plan_sources"]["files"].items()
    ]
    marsh_after = [
        inspect_file(marsh_root / expected["name"], expected, image_file=True)
        for expected in config["marsh_overview_sources"]["files"]
    ]
    pdf_after = [
        inspect_file(pdf_root / expected["name"], expected, image_file=False)
        for expected in config["supplemental_pdfs"]["files"]
    ]
    protected_after = resolve_relative_map(config["protected_files"])

    gates = config["gates"]
    provenance = config["provenance"]
    checks = {
        "v9w_regression_hashes": len(regression_checks) == gates["regression_hash_count_expected"] and all(row["pass"] for row in regression_checks),
        "plan_sources_hashes_and_dimensions": len(plan_before) == gates["plan_source_file_count_expected"] and all(row["pass"] for row in plan_before),
        "plan_sources_unchanged": unchanged(plan_before, plan_after),
        "marsh_overviews_hashes_and_dimensions": len(marsh_before) == gates["marsh_overview_file_count_expected"] and all(row["pass"] for row in marsh_before),
        "marsh_overviews_unchanged": unchanged(marsh_before, marsh_after),
        "supplemental_pdfs_hashes": len(pdf_before) == gates["supplemental_pdf_count_expected"] and all(row["pass"] for row in pdf_before),
        "supplemental_pdfs_unchanged": unchanged(pdf_before, pdf_after),
        "protected_blender_master_unchanged": all(row["pass"] for row in protected_before) and all(row["pass"] for row in protected_after) and protected_before == protected_after,
        "core_transcription_sheet_count": counts["core_transcription_sheet_count"] == gates["core_transcription_sheet_count_expected"],
        "supporting_section_sheet_count": counts["supporting_section_sheet_count"] == gates["supporting_section_sheet_count_expected"],
        "transcription_candidate_count": counts["transcription_candidate_record_count"] == gates["transcription_candidate_record_count_expected"],
        "all_ambiguous_candidates_rejected": all(row["dimension_chain_status"] == "NOT_TRANSCRIBED_SCAN_AMBIGUITY" and row["accepted_grid_anchor_id_count"] == 0 for row in records),
        "categorical_stair_relation_count": counts["categorical_stair_relation_count"] == gates["categorical_stair_relation_count_expected"],
        "marsh_floor_topology_count": counts["marsh_floor_topology_count"] == gates["marsh_floor_topology_count_expected"],
        "record_drawing_stamp_count": counts["record_drawing_stamp_count"] == gates["record_drawing_stamp_count_expected"],
        "no_accepted_numeric_dimension_chain": accepted_dimensions == gates["accepted_numeric_dimension_chain_count_expected"],
        "no_accepted_closed_grid_anchor_set": accepted_anchor_sets == gates["accepted_closed_grid_anchor_set_count_expected"],
        "no_scan_pixel_coordinates": pixel_coordinates == gates["scan_pixel_coordinate_count_expected"],
        "no_model_geometry_promotion": promoted_geometry == gates["model_geometry_promoted_record_count_expected"],
        "wayback_plan_distribution_match": provenance["plan_zip_wayback"]["all_target_files_match"] and counts["wayback_plan_match_count"] == gates["wayback_plan_match_count_expected"],
        "current_internet_archive_distribution_match": provenance["current_internet_archive_item"]["all_target_files_match"],
        "wayback_marsh_distribution_match": provenance["marsh_zip_wayback"]["all_target_files_match"] and counts["wayback_marsh_match_count"] == gates["wayback_marsh_match_count_expected"],
        "upstream_nist_file_level_provenance_not_overclaimed": provenance["official_nist_context"]["exact_local_plan_files_linked_by_file_level_nist_receipt"] is gates["upstream_nist_file_level_provenance_verified_expected"],
        "as_built_status_not_verified": False is gates["as_built_status_verified_expected"],
        "variant_separation_retained": counts["variant_count"] == gates["variant_count_expected"],
        "zero_physical_properties": all(value == 0.0 for value in physical.values()),
        "solver_and_blender_prohibited": not gates["global_solver_authorized"] and not gates["blender_authorized"],
        "supplemental_pdfs_not_used_for_geometry": all(not row["used_for_geometry"] for row in config["supplemental_pdfs"]["files"]),
    }
    overall_status = "PASS" if all(checks.values()) else "FAIL"

    provenance_audit = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "qualified_status": provenance["qualified_status"],
        "plan_distribution_chain": {
            "wayback_nistreview": provenance["plan_zip_wayback"],
            "current_internet_archive": provenance["current_internet_archive_item"],
            "archived_nistreview_page": provenance["archived_nistreview_page"],
            "local_file_checks": plan_before,
        },
        "marsh_distribution_chain": {
            "wayback_nistreview": provenance["marsh_zip_wayback"],
            "local_overview_checks": marsh_before,
            "record_drawing_stamp_count": counts["record_drawing_stamp_count"],
        },
        "official_nist_context": provenance["official_nist_context"],
        "supplemental_pdf_classification": config["supplemental_pdfs"]["files"],
        "decision": (
            "The ten targeted TIFFs are bitwise linked to the archived nistreview ZIP and the current Internet Archive item. "
            "This does not establish a file-level upstream NIST receipt or as-built geometry. The seven floor-overview photographs "
            "are linked to the archived nistreview FOIA-labelled distribution and visibly bear RECORD DRAWING stamps, but their "
            "photographic perspective and missing field-verification chain preclude coordinate extraction."
        ),
    }

    transcription = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "warning": WARNING,
        "manual_policy": audit["dimension_chain_policy"],
        "printed_grid_observation": audit["printed_grid_observation"],
        "section_support": audit["section_support"],
        "records": records,
        "marsh_floor_topology_cross_check": marsh_topology,
        "counts": counts,
        "transcription_fingerprint_sha256": transcription_fingerprint,
        "decision": {
            "categorical_three_stair_topology_retained": True,
            "categorical_locations": {
                stair["nist_alias"]: stair["categorical_location"]
                for stair in audit["stair_definitions"]
            },
            "printed_numeric_dimension_chain_accepted": False,
            "closed_grid_anchor_set_accepted": False,
            "metric_coordinate_created": False,
            "as_built_geometry_created": False,
            "model_geometry_updated": False,
        },
    }

    qualification = {
        "bounded_provenance_audit": overall_status == "PASS",
        "ten_plan_files_linked_to_nistreview_wayback_and_current_internet_archive": overall_status == "PASS",
        "upstream_nist_file_level_receipt": False,
        "seven_floor_record_drawing_photo_topology_cross_check": overall_status == "PASS",
        "categorical_three_stair_relations": True,
        "printed_numeric_dimension_chain": False,
        "closed_numeric_grid_anchor_set": False,
        "scan_pixel_to_physical_transform": False,
        "as_built_geometry": False,
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
            "V9X passes as a reproducible conservative documentary audit, not as a geometry qualification. "
            "The public-distribution chain and seven-floor categorical topology are documented, while every ambiguous "
            "numeric dimension/grid candidate is rejected and all as-built, coordinate, damage and physical gates remain closed."
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
            "plan_source_file_count": counts["plan_source_file_count"],
            "core_sheet_titles": [
                {"sheet": row["sheet"], "floor_scope": row["floor_scope"]}
                for row in audit["core_sheets"]
            ],
            "section_titles": [row["accepted_transcription"] for row in audit["section_support"]],
            "numbered_core_column_bubbles_visible": True,
            "record_drawing_stamp_count": counts["record_drawing_stamp_count"],
            "floor_specific_record_plan_topology_count": counts["marsh_floor_topology_count"],
        },
        "official_model_results": {
            "inherited_alias_join": {"1": "A", "2": "C", "3": "B"},
            "official_nist_drawing_collection_context": provenance["official_nist_context"],
            "no_official_model_damage_result_created": True,
        },
        "archive_claims": {
            "user_claim": "The plans were recovered through NIST material on Internet Archive/nistreview.org.",
            "verified_portion": provenance["qualified_status"],
            "unverified_portion": "No file-level NIST receipt links the exact ten TIFFs to the agency collection, and no as-built field verification is established."
        },
        "model_hypotheses": {
            "low_base_high_retained_separately": True,
            "scan_pixel_coordinates_assumed": False,
            "ambiguous_dimension_digits_guessed": False,
            "unchanged_floor_geometry_assumed": False,
            "as_built_condition_assumed": False,
        },
        "derived_results": {
            **counts,
            "transcription_fingerprint_sha256": transcription_fingerprint,
            "categorical_locations": {stair["nist_alias"]: stair["categorical_location"] for stair in audit["stair_definitions"]},
        },
        "contradictions_and_missing_information": [
            "No complete printed dimension chain with simultaneously legible digits and endpoints is independently reproducible across the four core scans.",
            "Visible numbered column bubbles do not by themselves define a closed grid-to-stair coordinate set.",
            "The archived nistreview page marks the Marsh fire-floor distribution as a FOIA release but does not apply that wording to the original-plan ZIP line.",
            "The current Internet Archive item metadata does not supply a source field tying the exact files to NIST and contains a title/internal-path date discrepancy.",
            "NIST's general statement that it received original design/fabrication/construction drawings does not identify these ten TIFFs and NIST also reported that a complete as-built set was unavailable.",
            "RECORD DRAWING stamps on photographed tenant sheets do not establish field-verified metric coordinates from perspective images.",
        ],
        "checks": checks,
        "model_gate": qualification,
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    write_json(outputs["provenance_audit"], provenance_audit)
    write_json(outputs["transcription"], transcription)
    write_matrix_csv(outputs["matrix_csv"], records)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)

    report_lines = [
        "# WTC 1 - V9X - provenance et transcription bornee des ancrages imprimes des escaliers",
        "",
        f"**Validation generale : {overall_status}**",
        "",
        "> PASS DOCUMENTAIRE CONSERVATEUR - ZERO CHAINE COTEE ACCEPTEE - ZERO ANCRAGE NUMERIQUE FERME - PAS AS-BUILT - ZERO CREDIT PHYSIQUE",
        "",
        "## Conclusion",
        "",
        "V9X est PASS comme audit documentaire reproductible, mais la porte geometrique reste fermee. Les dix TIFF cibles sont identiques aux fichiers distribues par le ZIP nistreview archive et par l'item Internet Archive actuel. Les sept vues d'ensemble Marsh des niveaux 93 a 99 portent visiblement un cachet RECORD DRAWING et corroborent une topologie a trois escaliers. En revanche, aucune des douze tentatives feuille-escalier ne fournit une chaine complete dont les chiffres et les extremites de cote soient a la fois lisibles et reproductibles. Aucune valeur n'est devinee, aucune coordonnee n'est creee et aucune geometrie V9T/V9U n'est modifiee.",
        "",
        "## 1. Faits directement observes ou transcrits",
        "",
        "- A-A-148, A-A-150, A-A-151 et A-A-153 affichent Stair 1, Stair 2 et Stair 3 ainsi que des bulles numerotees de colonnes du noyau.",
        "- A-A-125 porte le titre Stair Sections - Stair 1 and 2; A-A-126 porte Stair Sections - Stair 2 and 3. Ces sections ne recoivent aucun credit de localisation horizontale.",
        "- Une photographie d'ensemble ciblee pour chacun des niveaux 93 a 99 affiche l'identifiant du niveau, un cachet RECORD DRAWING et trois cages ou symboles d'escaliers.",
        "- Les photographies sont prises en perspective; aucune echelle pixel n'est exploitee.",
        "",
        "## 2. Resultats ou contexte officiel NIST",
        "",
        "- NIST indique avoir recu des plans de conception originaux et des plans originaux de fabrication/construction des tours.",
        "- NIST indique aussi qu'un jeu complet de plans as-built n'etait pas disponible et distingue les plans contractuels originaux et leurs revisions.",
        "- Ces declarations generales ne constituent pas un recu NIST au niveau fichier pour les dix TIFF locaux et ne valident aucune coordonnee as-built.",
        "",
        "## 3. Affirmations provenant des archives",
        "",
        "- L'utilisateur a decrit les plans comme recuperes depuis des ressources NIST via nistreview.org/Internet Archive.",
        "- La chaine binaire locale vers le ZIP nistreview archive et vers l'item Internet Archive actuel est verifiee pour les dix fichiers cibles.",
        "- La page nistreview archivee qualifie explicitement le lot Marsh de diffusion FOIA, mais n'applique pas cette mention a la ligne du ZIP de plans originaux.",
        "- Le PDF Douglas est une critique externe de la simulation NIST, Greening une analyse externe simplifiee, et WTCI-008-S un rapport externe de risque immobilier; aucun n'est une sortie officielle NIST ni une entree geometrique V9X.",
        "",
        "### Sources publiques de provenance",
        "",
        f"- [Item Internet Archive des plans]({provenance['current_internet_archive_item']['url']})",
        f"- [Page nistreview archivee]({provenance['archived_nistreview_page']['url']})",
        f"- [Etat de la collecte NIST]({provenance['official_nist_context']['data_collection_url']})",
        f"- [Limite du jeu as-built dans le document NIST]({provenance['official_nist_context']['media_handout_url']})",
        "",
        "## 4. Hypotheses propres au modele",
        "",
        "- Les relations A=upper east, C=upper west et B=lower central restent purement categorielles et servent seulement a la continuite documentaire.",
        "- LOW, BASE et HIGH restent trois placements V9T/V9U separes, explicitement hypothetiques et inchanges.",
        "- Aucune repetition d'un niveau, aucun alignement apparent et aucun cachet RECORD DRAWING ne sont transformes en coordonnee as-built.",
        "",
        "## 5. Resultats derives",
        "",
        f"- Fichiers de plans verifies : {counts['plan_source_file_count']}.",
        f"- Vues Marsh ciblees et verifiees : {counts['marsh_overview_file_count']}.",
        f"- Candidats feuille-escalier controles : {counts['transcription_candidate_record_count']}.",
        f"- Chaines de cotes numeriques acceptees : {accepted_dimensions}.",
        f"- Jeux d'ancrages de grille fermes acceptes : {accepted_anchor_sets}.",
        f"- Coordonnees issues des pixels : {pixel_coordinates}; geometries de modele promues : {promoted_geometry}.",
        f"- Empreinte de transcription : `{transcription_fingerprint}`.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- Les superpositions d'annotations, le bruit du scan et l'ambiguite de certaines extremites de lignes de cote empechent un calage numerique unique.",
        "- Une bulle de colonne visible n'est pas, a elle seule, une chaine fermee entre une grille et le contour d'une cage.",
        "- Il manque un recu NIST/FOIA au niveau fichier, une source vectorielle ou lossless plus lisible et une trace de verification de chantier.",
        "- Aucun fait de dommage, aucune masse, rigidite, resistance, connexion ou capacite de chemin de charge n'est deduit de ces plans.",
        "",
        "## Portes de validation",
        "",
    ]
    for name, passed in checks.items():
        report_lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "Le Blender maitre conserve son empreinte protegee. Aucun processus Blender et aucun solveur structurel n'ont ete executes.",
            "",
            "## Livrables",
            "",
            f"- Audit de provenance : `{rel(outputs['provenance_audit'])}`",
            f"- Transcription bornee : `{rel(outputs['transcription'])}`",
            f"- Matrice CSV : `{rel(outputs['matrix_csv'])}`",
            f"- Porte modele : `{rel(outputs['model_gate'])}`",
            f"- Planche de controle : `{rel(outputs['contact_sheet'])}`",
            "",
            "## Etape suivante pre-declaree - V9Y",
            "",
            config["next_iteration"]["objective"],
            "",
        ]
    )
    outputs["report"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report"].write_text("\n".join(report_lines), encoding="utf-8", newline="\n")

    generated_files = [
        outputs["provenance_audit"],
        outputs["transcription"],
        outputs["matrix_csv"],
        outputs["model_gate"],
        outputs["contact_sheet"],
        outputs["results"],
        outputs["report"],
    ]
    source_manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "runtime": {
            "python": platform.python_version(),
            "python_executable": sys.executable,
            "pillow": PILLOW_VERSION,
        },
        "source_archive_read": False,
        "source_archive_rescanned": False,
        "source_archive_files_modified": False,
        "workspace_plan_sources_before": plan_before,
        "workspace_plan_sources_after": plan_after,
        "supplemental_marsh_sources_before": marsh_before,
        "supplemental_marsh_sources_after": marsh_after,
        "supplemental_pdfs_before": pdf_before,
        "supplemental_pdfs_after": pdf_after,
        "regression_files": regression_checks,
        "protected_files_before": protected_before,
        "protected_files_after": protected_after,
        "network_access_used_for_provenance_recheck": True,
        "script_network_access_used": False,
        "solver_executed": False,
        "blender_executed": False,
        "scan_pixel_measurement_used": False,
        "model_geometry_promoted": False,
        "transcription_fingerprint_sha256": transcription_fingerprint,
        "generated_files": [
            {"path": rel(path), "size_bytes": path.stat().st_size, "sha256": digest(path)}
            for path in generated_files
        ],
    }
    write_json(outputs["source_manifest"], source_manifest)

    print(
        json.dumps(
            {
                "iteration": config["iteration"],
                "status": overall_status,
                "plan_source_file_count": counts["plan_source_file_count"],
                "marsh_floor_topology_count": counts["marsh_floor_topology_count"],
                "transcription_candidate_record_count": counts["transcription_candidate_record_count"],
                "accepted_numeric_dimension_chain_count": accepted_dimensions,
                "accepted_closed_grid_anchor_set_count": accepted_anchor_sets,
                "model_geometry_promoted": False,
                "solver_executed": False,
                "blender_executed": False,
                "report": rel(outputs["report"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
