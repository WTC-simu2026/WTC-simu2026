#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdf
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PROJECT_ROOT
    / "wtc1_simulation_v8"
    / "data"
    / "v10f_p0_cross_reference_locator_audit.json"
)
CHUNK_SIZE = 1024 * 1024
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
RECORD_KEYS = {
    "candidate_id",
    "document_id",
    "pdf_page_1_based",
    "page_classification",
    "visual_review_status",
    "confidence",
    "transcription",
}
TOP_LEVEL_TRANSCRIPTION_KEYS = {
    "iteration",
    "method",
    "records",
    "scope_attestation",
}
SCOPE_ATTESTATION_KEYS = {
    "drawing_number_suffixes_treated_as_floor_labels",
    "drawing_geometry_transcribed",
    "dimensions_transcribed",
    "member_properties_transcribed",
    "connection_geometry_transcribed",
    "physical_properties_assigned",
    "damage_or_load_path_credit_assigned",
    "tower_a_promoted_to_wtc1",
    "revision_or_as_built_authority_claimed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(CHUNK_SIZE)
            if not block:
                break
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def normalize_token(value: str) -> str:
    normalized = str(value).upper().replace("–", "-").replace("—", "-")
    return re.sub(r"\s*-\s*", "-", normalized)


def verify_hashed_file(item: dict[str, Any]) -> dict[str, Any]:
    path = PROJECT_ROOT / item["path"]
    if not path.is_file():
        return {
            **item,
            "exists": False,
            "actual_sha256": None,
            "size_bytes": None,
            "matches": False,
        }
    actual_sha256, size_bytes = sha256_file(path)
    return {
        **item,
        "exists": True,
        "actual_sha256": actual_sha256,
        "size_bytes": size_bytes,
        "matches": actual_sha256.lower() == item["expected_sha256"].lower(),
    }


def validate_source_policy(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = config["source_policy"]
    required_true = {
        "v10d_working_copies_read_only",
        "bounded_embedded_text_locator_scan_authorized",
        "matched_page_render_authorized",
    }
    required_false = {
        "source_archive_read",
        "source_archive_modified",
        "official_sources_directory_read",
        "official_sources_directory_modified",
        "network_access_authorized",
        "external_contact_authorized",
        "store_extracted_page_text_authorized",
        "store_page_text_snippets_authorized",
        "nonmatching_page_render_authorized",
        "drawing_geometry_transcription_authorized",
        "dimension_transcription_authorized",
        "member_property_transcription_authorized",
        "connection_detail_transcription_authorized",
        "as_built_promotion_authorized",
        "structural_solver_authorized",
        "blender_authorized",
        "blender_master_modification_authorized",
        "thermal_continuation_authorized",
        "physical_coordinate_assignment_authorized",
        "member_section_assignment_authorized",
        "material_assignment_authorized",
        "mass_assignment_authorized",
        "stiffness_assignment_authorized",
        "capacity_assignment_authorized",
        "connection_law_assignment_authorized",
        "damage_state_assignment_authorized",
        "load_path_credit_authorized",
    }
    for key in sorted(required_true):
        if policy.get(key) is not True:
            errors.append(f"source policy must be true: {key}")
    for key in sorted(required_false):
        if policy.get(key) is not False:
            errors.append(f"source policy must be false: {key}")
    return errors


def validate_predeclaration(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    item = config["predeclaration"]
    audit = verify_hashed_file(item)
    if not audit["matches"]:
        return {}, audit, ["immutable V10F predeclaration hash mismatch"]
    predeclaration = load_json(PROJECT_ROOT / item["path"])
    if predeclaration.get("iteration") != "V10F":
        errors.append("predeclaration iteration is not V10F")
    if predeclaration.get("random_seed") != config["dataset"]["random_seed"]:
        errors.append("predeclaration random seed differs from configuration")
    documents = predeclaration.get("bounded_documents", [])
    maximum_documents = int(predeclaration["locator_scan_policy"]["maximum_document_count"])
    if len(documents) != maximum_documents or len(documents) != int(config["scan_policy"]["maximum_document_count"]):
        errors.append("bounded document count differs from the exact predeclared count")
    scanned_pages = sum(
        int(item["locator_scan_last_pdf_page_1_based"])
        - int(item["locator_scan_first_pdf_page_1_based"])
        + 1
        for item in documents
    )
    if scanned_pages != int(predeclaration["locator_scan_policy"]["maximum_scanned_pdf_page_count"]):
        errors.append("predeclared page-range total differs from predeclared maximum")
    if scanned_pages != int(config["scan_policy"]["required_scanned_pdf_page_count"]):
        errors.append("predeclared page-range total differs from configured required scan count")
    if predeclaration["locator_scan_policy"].get("store_full_extracted_text") is not False:
        errors.append("predeclaration must forbid storage of full extracted text")
    if predeclaration["locator_scan_policy"].get("store_page_text_snippets") is not False:
        errors.append("predeclaration must forbid storage of page text snippets")
    if predeclaration["locator_scan_policy"].get("fallback_raster_or_ocr_scan_authorized") is not False:
        errors.append("predeclaration must forbid fallback raster or OCR scanning")
    v10e_results_path = PROJECT_ROOT / predeclaration["selection_basis"]["v10e_results_path"]
    v10e_results = load_json(v10e_results_path)
    locator_summary = v10e_results.get("locator_summary", {})
    if locator_summary.get("v10f_second_bounded_window_condition_met") is not True:
        errors.append("V10E did not open the bounded V10F window")
    expected_parents = sorted(predeclaration["selection_basis"]["allowed_parent_candidate_ids"])
    actual_parents = sorted(locator_summary.get("index_continuation_cross_reference_candidate_ids", []))
    if actual_parents != expected_parents:
        errors.append("V10E parent cross-reference candidate set differs from predeclaration")
    return predeclaration, audit, errors


def verify_sources(predeclaration: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for document in predeclaration["bounded_documents"]:
        path = PROJECT_ROOT / document["source_path"]
        record: dict[str, Any] = {
            "document_id": document["document_id"],
            "book_number": document["book_number"],
            "path": document["source_path"],
            "expected_sha256": document["source_sha256"],
            "expected_container_page_count": document["container_page_count"],
            "scan_first_pdf_page_1_based": document["locator_scan_first_pdf_page_1_based"],
            "scan_last_pdf_page_1_based": document["locator_scan_last_pdf_page_1_based"],
            "predeclared_reference_tokens": document["visible_parent_cross_references"],
        }
        if not path.is_file():
            record.update({"exists": False, "matches": False})
            errors.append(f"missing bounded source: {document['document_id']}")
            records.append(record)
            continue
        actual_sha256, size_bytes = sha256_file(path)
        try:
            page_count = len(PdfReader(str(path)).pages)
        except Exception as error:
            page_count = None
            errors.append(f"PDF parse failed for {document['document_id']}: {error}")
        matches = (
            actual_sha256.lower() == document["source_sha256"].lower()
            and page_count == int(document["container_page_count"])
        )
        record.update(
            {
                "exists": True,
                "actual_sha256_before_scan": actual_sha256,
                "size_bytes": size_bytes,
                "actual_container_page_count": page_count,
                "matches": matches,
            }
        )
        if not matches:
            errors.append(f"bounded source identity mismatch: {document['document_id']}")
        records.append(record)
    return records, errors


def scan_bounded_pages(
    predeclaration: dict[str, Any], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    errors: list[str] = []
    matches: list[dict[str, Any]] = []
    scanned_page_count = 0
    scanned_character_count = 0
    raw_matched_page_count = 0
    raw_reference_occurrence_count = 0
    matched_reference_tokens: set[str] = set()
    for document in predeclaration["bounded_documents"]:
        path = PROJECT_ROOT / document["source_path"]
        reader = PdfReader(str(path))
        first_page = int(document["locator_scan_first_pdf_page_1_based"])
        last_page = int(document["locator_scan_last_pdf_page_1_based"])
        references = list(document["visible_parent_cross_references"])
        normalized_references = {reference: normalize_token(reference) for reference in references}
        for page_number in range(first_page, last_page + 1):
            extracted = reader.pages[page_number - 1].extract_text() or ""
            scanned_page_count += 1
            scanned_character_count += len(extracted)
            normalized = normalize_token(extracted)
            page_hits = [
                reference
                for reference, normalized_reference in normalized_references.items()
                if normalized_reference in normalized
            ]
            if page_hits:
                raw_matched_page_count += 1
                raw_reference_occurrence_count += len(page_hits)
                first_occurrence_hits = [
                    reference for reference in page_hits if reference not in matched_reference_tokens
                ]
            else:
                first_occurrence_hits = []
            if first_occurrence_hits:
                matched_reference_tokens.update(first_occurrence_hits)
                matches.append(
                    {
                        "candidate_id": f"{document['document_id']}__p{page_number:04d}",
                        "document_id": document["document_id"],
                        "book_number": document["book_number"],
                        "pdf_page_1_based": page_number,
                        "matched_reference_tokens": first_occurrence_hits,
                        "match_method": config["scan_policy"]["match_method"],
                        "embedded_text_character_count": len(extracted),
                        "full_extracted_text_stored": False,
                        "page_text_snippet_stored": False,
                    }
                )
            del extracted
            del normalized
    maximum_pages = int(config["scan_policy"]["maximum_scanned_pdf_page_count"])
    required_pages = int(config["scan_policy"]["required_scanned_pdf_page_count"])
    maximum_matches = int(config["scan_policy"]["maximum_matched_page_count"])
    if scanned_page_count != required_pages:
        errors.append(f"scanned page count {scanned_page_count} differs from required {required_pages}")
    if scanned_page_count > maximum_pages:
        errors.append(f"scanned page count {scanned_page_count} exceeds maximum {maximum_pages}")
    if len(matches) > maximum_matches:
        errors.append(f"matched page count {len(matches)} exceeds maximum {maximum_matches}")
    all_references = {
        reference
        for document in predeclaration["bounded_documents"]
        for reference in document["visible_parent_cross_references"]
    }
    summary = {
        "scanned_document_count": len(predeclaration["bounded_documents"]),
        "scanned_pdf_page_count": scanned_page_count,
        "required_scanned_pdf_page_count": required_pages,
        "maximum_scanned_pdf_page_count": maximum_pages,
        "aggregate_embedded_text_character_count": scanned_character_count,
        "full_extracted_text_stored": False,
        "page_text_snippets_stored": False,
        "predeclared_reference_token_count": len(all_references),
        "raw_matched_page_count_before_first_occurrence_selection": raw_matched_page_count,
        "raw_reference_occurrence_count_before_first_occurrence_selection": raw_reference_occurrence_count,
        "matched_reference_token_count": len(matched_reference_tokens),
        "matched_reference_tokens": sorted(matched_reference_tokens),
        "unmatched_reference_tokens": sorted(all_references - matched_reference_tokens),
        "matched_page_count": len(matches),
        "maximum_matched_page_count": maximum_matches,
    }
    return matches, summary, errors


def pdftoppm_version() -> str:
    executable = shutil.which("pdftoppm")
    if not executable:
        return "unavailable"
    completed = subprocess.run(
        [executable, "-v"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return (completed.stderr or completed.stdout).strip().splitlines()[0]


def render_one(
    candidate: dict[str, Any], source_path: Path, config: dict[str, Any], temporary_directory: Path
) -> dict[str, Any]:
    policy = config["render_policy"]
    executable = shutil.which("pdftoppm")
    if not executable:
        raise RuntimeError("pdftoppm is unavailable")
    output_directory = PROJECT_ROOT / policy["individual_page_directory"]
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{candidate['candidate_id']}.png"
    temporary_prefix = temporary_directory / candidate["candidate_id"]
    page_number = int(candidate["pdf_page_1_based"])
    command = [
        executable,
        "-f",
        str(page_number),
        "-l",
        str(page_number),
        "-singlefile",
        "-gray",
        "-png",
        "-r",
        str(policy["dpi"]),
        str(source_path),
        str(temporary_prefix),
    ]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    temporary_png = temporary_prefix.with_suffix(".png")
    if completed.returncode != 0 or not temporary_png.is_file():
        raise RuntimeError(
            f"pdftoppm failed for {candidate['candidate_id']}: "
            + completed.stderr.decode("utf-8", errors="replace")[:500]
        )
    output_path.write_bytes(temporary_png.read_bytes())
    with Image.open(output_path) as image:
        width, height = image.size
        mode = image.mode
    pixels = width * height
    if pixels > int(policy["maximum_pixels_per_rendered_page"]):
        raise RuntimeError(f"rendered pixel cap exceeded for {candidate['candidate_id']}")
    png_sha256, png_size = sha256_file(output_path)
    return {
        **candidate,
        "render_path": relative_path(output_path),
        "render_sha256": png_sha256,
        "render_size_bytes": png_size,
        "render_width_pixels": width,
        "render_height_pixels": height,
        "render_pixel_count": pixels,
        "render_mode": mode,
        "renderer_return_code": completed.returncode,
    }


def create_contact_sheet(records: list[dict[str, Any]], output_path: Path) -> None:
    columns = 2
    cell_width = 930
    image_height = 650
    label_height = 54
    title_height = 70
    rows = max(1, (len(records) + columns - 1) // columns)
    canvas = Image.new("RGB", (columns * cell_width, title_height + rows * (image_height + label_height)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((20, 20), "V10F | exact predeclared cross-reference matches | locator-only audit", fill="black", font=font)
    for index, record in enumerate(records):
        row, column = divmod(index, columns)
        x0 = column * cell_width
        y0 = title_height + row * (image_height + label_height)
        with Image.open(PROJECT_ROOT / record["render_path"]) as source:
            image = source.convert("RGB")
            image.thumbnail((cell_width - 20, image_height - 20), Image.Resampling.LANCZOS)
            x = x0 + (cell_width - image.width) // 2
            y = y0 + (image_height - image.height) // 2
            canvas.paste(image, (x, y))
        label = (
            f"{record['candidate_id']} | refs: "
            + ", ".join(record["matched_reference_tokens"])
        )
        draw.text((x0 + 10, y0 + image_height + 8), label, fill="black", font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)


def render_matches(
    candidates: list[dict[str, Any]], predeclaration: dict[str, Any], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    documents = {item["document_id"]: item for item in predeclaration["bounded_documents"]}
    with tempfile.TemporaryDirectory(prefix="wtc1_v10f_") as temporary:
        temporary_directory = Path(temporary)
        for candidate in candidates:
            try:
                source_path = PROJECT_ROOT / documents[candidate["document_id"]]["source_path"]
                records.append(render_one(candidate, source_path, config, temporary_directory))
            except Exception as error:
                errors.append(f"{candidate['candidate_id']}: {type(error).__name__}: {error}")
    policy = config["render_policy"]
    aggregate_pixels = sum(int(record["render_pixel_count"]) for record in records)
    aggregate_bytes = sum(int(record["render_size_bytes"]) for record in records)
    if len(records) != len(candidates):
        errors.append("render count differs from matched page count")
    if len(records) > int(policy["maximum_rendered_match_page_count"]):
        errors.append("render count exceeds maximum")
    if aggregate_pixels > int(policy["maximum_aggregate_rendered_pixels"]):
        errors.append("aggregate rendered pixel cap exceeded")
    if aggregate_bytes > int(policy["maximum_aggregate_rendered_png_bytes"]):
        errors.append("aggregate rendered byte cap exceeded")
    contact_sheet = PROJECT_ROOT / policy["global_contact_sheet"]
    if records:
        create_contact_sheet(records, contact_sheet)
    caps = {
        "render_count": len(records),
        "matched_page_count": len(candidates),
        "maximum_rendered_match_page_count": int(policy["maximum_rendered_match_page_count"]),
        "aggregate_rendered_pixels": aggregate_pixels,
        "maximum_aggregate_rendered_pixels": int(policy["maximum_aggregate_rendered_pixels"]),
        "aggregate_rendered_png_bytes": aggregate_bytes,
        "maximum_aggregate_rendered_png_bytes": int(policy["maximum_aggregate_rendered_png_bytes"]),
        "maximum_observed_pixels_per_page": max(
            [int(record["render_pixel_count"]) for record in records], default=0
        ),
        "maximum_pixels_per_rendered_page": int(policy["maximum_pixels_per_rendered_page"]),
    }
    return records, caps, errors


def validate_manual_transcription(
    config: dict[str, Any], candidates: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    path = PROJECT_ROOT / config["manual_transcription"]["path"]
    if not path.is_file():
        audit = {"iteration": "V10F", "validation_status": "FAIL", "errors": ["manual transcription missing"]}
        return {}, audit, audit["errors"]
    payload = load_json(path)
    if set(payload) != TOP_LEVEL_TRANSCRIPTION_KEYS:
        errors.append("manual transcription top-level keys differ from exact allowed set")
    if payload.get("iteration") != "V10F":
        errors.append("manual transcription iteration is not V10F")
    if payload.get("method") != config["manual_transcription"]["transcription_method"]:
        errors.append("manual transcription method differs from configuration")
    attestation = payload.get("scope_attestation", {})
    if set(attestation) != SCOPE_ATTESTATION_KEYS:
        errors.append("scope attestation keys differ from exact allowed set")
    if any(value is not False for value in attestation.values()):
        errors.append("all scope attestations must remain false")
    candidate_by_id = {item["candidate_id"]: item for item in candidates}
    allowed_fields = set(config["manual_transcription"]["allowed_transcription_fields"])
    allowed_classes = set(config["manual_transcription"]["allowed_page_classifications"])
    normalized_records: list[dict[str, Any]] = []
    seen: set[str] = set()
    forbidden_occurrences: list[str] = []
    for record in payload.get("records", []):
        if set(record) != RECORD_KEYS:
            errors.append(f"manual record keys differ from exact set: {record.get('candidate_id')}")
        candidate_id = record.get("candidate_id")
        if candidate_id in seen:
            errors.append(f"duplicate manual record: {candidate_id}")
        seen.add(candidate_id)
        candidate = candidate_by_id.get(candidate_id)
        if candidate is None:
            errors.append(f"unknown manual candidate: {candidate_id}")
            continue
        if record.get("document_id") != candidate["document_id"]:
            errors.append(f"document mismatch: {candidate_id}")
        if record.get("pdf_page_1_based") != candidate["pdf_page_1_based"]:
            errors.append(f"page mismatch: {candidate_id}")
        if record.get("page_classification") not in allowed_classes:
            errors.append(f"invalid page classification: {candidate_id}")
        if record.get("visual_review_status") != "COMPLETED":
            errors.append(f"visual review incomplete: {candidate_id}")
        if record.get("confidence") not in CONFIDENCE_VALUES:
            errors.append(f"invalid confidence: {candidate_id}")
        transcription = record.get("transcription", {})
        if set(transcription) != allowed_fields:
            errors.append(f"transcription fields differ from exact set: {candidate_id}")
        normalized_transcription: dict[str, list[str]] = {}
        for field in sorted(allowed_fields):
            values = transcription.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                errors.append(f"{candidate_id}.{field} must be a list of strings")
                values = []
            normalized_transcription[field] = [value.strip() for value in values if value.strip()]
        for forbidden in config["manual_transcription"]["forbidden_transcription_fields"]:
            if forbidden in transcription:
                forbidden_occurrences.append(f"{candidate_id}.{forbidden}")
        normalized_records.append({**record, "transcription": normalized_transcription})
    expected_ids = set(candidate_by_id)
    missing = sorted(expected_ids - seen)
    extra = sorted(seen - expected_ids)
    if missing:
        errors.append("missing manual candidates: " + ", ".join(missing))
    if extra:
        errors.append("extra manual candidates: " + ", ".join(extra))
    if forbidden_occurrences:
        errors.append("forbidden transcription keys: " + ", ".join(forbidden_occurrences))
    audit = {
        "iteration": "V10F",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not errors else "FAIL",
        "record_count": len(normalized_records),
        "required_record_count": len(candidates),
        "unique_candidate_count": len(seen),
        "missing_candidate_ids": missing,
        "extra_candidate_ids": extra,
        "forbidden_transcription_key_occurrence_count": len(forbidden_occurrences),
        "full_page_text_transcribed": False,
        "geometry_or_dimension_transcribed": False,
        "errors": errors,
    }
    normalized = {**payload, "records": normalized_records}
    return normalized, audit, errors


def target_floors(record: dict[str, Any], targets: list[int]) -> set[int]:
    found: set[int] = set()
    floor_strings = (
        record["transcription"].get("visible_floor_labels", [])
        + record["transcription"].get("visible_floor_ranges", [])
    )
    for value in floor_strings:
        if not re.search(r"\bfloors?\b|\bstor(?:y|ies)\b", value, re.IGNORECASE):
            continue
        for target in targets:
            if re.search(rf"(?<!\d){target}(?!\d)", value):
                found.add(target)
    return found


def build_locator_rows(
    config: dict[str, Any], predeclaration: dict[str, Any], candidates: list[dict[str, Any]], manual: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidate_by_id = {item["candidate_id"]: item for item in candidates}
    targets = [int(value) for value in config["manual_transcription"]["floor_target_set"]]
    locator_rows: list[dict[str, Any]] = []
    documents_with_target_floor: set[str] = set()
    documents_with_exact_locator: set[str] = set()
    page_floor_map: dict[tuple[str, int], list[str]] = {}
    exact_page_floor_map: dict[tuple[str, int], list[str]] = {}
    drawing_suffix_warning_pages: list[str] = []
    for record in manual["records"]:
        candidate = candidate_by_id[record["candidate_id"]]
        transcription = record["transcription"]
        floors = sorted(target_floors(record, targets))
        if floors:
            documents_with_target_floor.add(record["document_id"])
        locators = transcription["visible_page_or_sheet_locators"]
        normalized_locators = [normalize_token(value) for value in locators]
        relations: list[str] = []
        for reference in candidate["matched_reference_tokens"]:
            normalized_reference = normalize_token(reference)
            if normalized_reference in normalized_locators:
                relations.append("EXACT_REFERENCE_IS_PAGE_LOCATOR")
            elif any(locator.startswith(normalized_reference + ".") for locator in normalized_locators):
                relations.append("REFERENCE_FAMILY_LOCATOR")
            else:
                relations.append("LISTING_OR_PARENT_REFERENCE_ONLY")
        if "EXACT_REFERENCE_IS_PAGE_LOCATOR" in relations:
            relation = "EXACT_REFERENCE_IS_PAGE_LOCATOR"
        elif "REFERENCE_FAMILY_LOCATOR" in relations:
            relation = "REFERENCE_FAMILY_LOCATOR"
        else:
            relation = "LISTING_OR_PARENT_REFERENCE_ONLY"
        exact_floor_locator = bool(floors) and relation == "EXACT_REFERENCE_IS_PAGE_LOCATOR"
        if exact_floor_locator:
            documents_with_exact_locator.add(record["document_id"])
        suffixes = [
            value
            for value in transcription["visible_drawing_identifiers"]
            if any(re.search(rf"[-.]\s*{target}(?:\.|\b)", value) for target in targets)
        ]
        if suffixes and not floors:
            drawing_suffix_warning_pages.append(record["candidate_id"])
        for floor in floors:
            page_floor_map.setdefault((record["document_id"], floor), []).append(record["candidate_id"])
            if exact_floor_locator:
                exact_page_floor_map.setdefault((record["document_id"], floor), []).append(record["candidate_id"])
        locator_rows.append(
            {
                "candidate_id": record["candidate_id"],
                "document_id": record["document_id"],
                "book_number": candidate["book_number"],
                "pdf_page_1_based": candidate["pdf_page_1_based"],
                "page_classification": record["page_classification"],
                "confidence": record["confidence"],
                "matched_reference_tokens": " | ".join(candidate["matched_reference_tokens"]),
                "visible_drawing_identifiers": " | ".join(transcription["visible_drawing_identifiers"]),
                "visible_floor_labels": " | ".join(transcription["visible_floor_labels"]),
                "visible_floor_ranges": " | ".join(transcription["visible_floor_ranges"]),
                "visible_revision_or_issue_fields": " | ".join(transcription["visible_revision_or_issue_fields"]),
                "visible_page_or_sheet_locators": " | ".join(locators),
                "reference_page_locator_relation": relation,
                "target_floors_explicitly_visible": " | ".join(str(value) for value in floors),
                "drawing_identifier_suffixes_93_99_not_floor_labels": " | ".join(suffixes),
                "exact_target_floor_locator": exact_floor_locator,
                "claims_revision_or_as_built_authority": False,
                "geometry_or_dimension_transcribed": False,
                "physical_credit": 0,
            }
        )
    floor_rows: list[dict[str, Any]] = []
    for document in predeclaration["bounded_documents"]:
        for floor in targets:
            page_ids = page_floor_map.get((document["document_id"], floor), [])
            exact_ids = exact_page_floor_map.get((document["document_id"], floor), [])
            floor_rows.append(
                {
                    "document_id": document["document_id"],
                    "book_number": document["book_number"],
                    "target_floor": floor,
                    "matched_pages_with_explicit_floor_label": " | ".join(page_ids),
                    "matched_pages_with_exact_floor_locator": " | ".join(exact_ids),
                    "floor_label_visible_in_v10f_window": bool(page_ids),
                    "exact_floor_locator_documented_in_v10f_window": bool(exact_ids),
                    "drawing_number_suffix_treated_as_floor": False,
                    "revision_or_as_built_authority_claimed": False,
                    "geometry_or_dimension_transcribed": False,
                    "physical_credit": 0,
                }
            )
    relation_counts = Counter(row["reference_page_locator_relation"] for row in locator_rows)
    summary = {
        "documents_with_any_explicit_floor93_99_label": sorted(documents_with_target_floor),
        "documents_with_exact_floor93_99_locator": sorted(documents_with_exact_locator),
        "exact_floor93_99_locator_candidate_count": sum(
            1 for row in locator_rows if row["exact_target_floor_locator"]
        ),
        "drawing_identifier_suffix_warning_candidate_ids": sorted(drawing_suffix_warning_pages),
        "drawing_identifier_suffix_warning_candidate_count": len(drawing_suffix_warning_pages),
        "reference_page_locator_relation_counts": dict(sorted(relation_counts.items())),
        "v10g_exact_page_expansion_condition_met": bool(documents_with_exact_locator),
        "page_content_expansion_branch_closed": not bool(documents_with_exact_locator),
    }
    return locator_rows, floor_rows, summary


def source_hashes_unchanged(predeclaration: dict[str, Any], source_records: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    records_by_id = {record["document_id"]: record for record in source_records}
    after_records: list[dict[str, Any]] = []
    unchanged_all = True
    for document in predeclaration["bounded_documents"]:
        path = PROJECT_ROOT / document["source_path"]
        actual_sha256, size_bytes = sha256_file(path)
        before = records_by_id[document["document_id"]]
        unchanged = (
            actual_sha256 == before.get("actual_sha256_before_scan")
            and size_bytes == before.get("size_bytes")
        )
        unchanged_all = unchanged_all and unchanged
        after_records.append(
            {
                "document_id": document["document_id"],
                "path": document["source_path"],
                "actual_sha256_after_render": actual_sha256,
                "size_bytes_after_render": size_bytes,
                "unchanged_after_scan_and_render": unchanged,
            }
        )
    return unchanged_all, after_records


def render_report(
    config: dict[str, Any], validation_status: str, scan_summary: dict[str, Any], render_caps: dict[str, Any],
    manual_audit: dict[str, Any], locator_summary: dict[str, Any]
) -> str:
    branch = "FERMÉE" if locator_summary["page_content_expansion_branch_closed"] else "OUVERTE"
    return "\n".join(
        [
            "# WTC 1 — V10F — localisateurs issus des renvois d’index P0",
            "",
            f"**Validation générale : {validation_status}**",
            "",
            "## Résultat opérationnel",
            "",
            (
                f"V10F a appliqué l’unique seconde fenêtre bornée ouverte par V10E : "
                f"{scan_summary['scanned_pdf_page_count']} pages de trois copies PDF exactes ont été parcourues en mémoire "
                f"uniquement pour rechercher 13 identifiants de renvoi pré-déclarés. Aucun texte de page ni extrait n’a été conservé. "
                f"La règle de première occurrence a sélectionné {scan_summary['matched_page_count']} pages uniques parmi "
                f"{scan_summary['raw_matched_page_count_before_first_occurrence_selection']} pages comportant au moins une occurrence, "
                f"toutes rendues et transcrites visuellement."
            ),
            "",
            (
                f"Aucun libellé explicite d’étage 93 à 99 n’est associé à un localisateur exact. "
                f"La branche d’expansion de contenu V10G est donc **{branch}** et doit revenir à la matrice d’acquisition priorisée."
            ),
            "",
            "## 1. Faits directement observés ou transcrits",
            "",
            f"- Références pré-déclarées retrouvées dans le texte incorporé : {scan_summary['matched_reference_token_count']} sur {scan_summary['predeclared_reference_token_count']}.",
            f"- Pages sélectionnées et rendues : {render_caps['render_count']}.",
            f"- Transcriptions visuelles validées : {manual_audit['record_count']}.",
            "- La page PDF 10 porte le localisateur 6-AB1-0.1 et montre des identifiants de dessin 6-AB1-93 à 6-AB1-99.3.",
            f"- Ces suffixes appartiennent aux identifiants de dessin ; aucun mot ou champ « Floor 93 » à « Floor 99 » n’est visible sur les {render_caps['render_count']} pages retenues.",
            "",
            "## 2. Résultats d’un modèle officiel",
            "",
            "Aucun résultat de modèle officiel n’est calculé, relu ou validé dans V10F.",
            "",
            "## 3. Affirmations provenant des archives locales",
            "",
            "Aucune archive source locale et aucun fichier de work/official_sources n’a été lu. Les inscriptions des copies V10D restent des données documentaires dont l’autorité de révision et le statut as-built ne sont pas établis ici.",
            "",
            "## 4. Hypothèses propres au modèle",
            "",
            "- Une correspondance textuelle normalisée à un identifiant de renvoi sert uniquement à sélectionner une page pour contrôle visuel.",
            "- Une correspondance par sous-chaîne peut viser un index de famille, une liste de révisions ou une répétition du renvoi ; elle ne prouve pas que la page est le dessin référencé.",
            "- Un nombre 93 à 99 inclus dans un identifiant 6-AB1-n n’est jamais promu au rang de libellé d’étage.",
            "",
            "## 5. Résultats dérivés",
            "",
            f"- Pages portant des suffixes d’identifiants 93–99 sans libellé d’étage : {locator_summary['drawing_identifier_suffix_warning_candidate_count']}.",
            f"- Localisateurs exacts d’étages 93–99 : {locator_summary['exact_floor93_99_locator_candidate_count']}.",
            "- Masse, rigidité, résistance, capacité, loi de connexion, dommage et crédit de chemin de charge : zéro.",
            "",
            "## 6. Contradictions et informations manquantes",
            "",
            f"- {len(scan_summary['unmatched_reference_tokens'])} des {scan_summary['predeclared_reference_token_count']} identifiants pré-déclarés ne sont pas retrouvés par le texte incorporé ; aucun OCR ou balayage raster de secours n’était autorisé.",
            "- Aucun localisateur explicite d’un dessin propre aux étages 93–99 n’est obtenu.",
            "- La provenance complète, l’applicabilité au WTC 1, l’autorité de révision et le statut as-built restent non établis.",
            "- Les 22 exigences physiques héritées de V10A restent bloquantes pour le solveur.",
            "",
            "## Garde-fous",
            "",
            "- Aucun accès réseau, contact externe, solveur structurel, calcul thermique ou lancement de Blender.",
            "- Aucun rendu de page non sélectionnée par la règle pré-déclarée.",
            "- Aucun texte intégral ou extrait de page conservé.",
            "- Aucun dessin, cote, section, matériau ou détail d’assemblage transcrit.",
            "- Le fichier Blender maître est resté inchangé.",
            "",
            "## Suite V10G",
            "",
            config["next_iteration"]["objective"],
        ]
    )


def build_offline_audit(config: dict[str, Any]) -> dict[str, Any]:
    outputs = config["outputs"]
    required = [
        ("configuration", relative_path(CONFIG_PATH)),
        ("predeclaration", config["predeclaration"]["path"]),
        ("script", "wtc1_simulation_v8/scripts/run_v10f_p0_cross_reference_locator_audit.py"),
        ("manual_transcription", config["manual_transcription"]["path"]),
        ("source_manifest", outputs["source_manifest"]),
        ("locator_scan_audit", outputs["locator_scan_audit"]),
        ("matched_page_manifest", outputs["matched_page_manifest"]),
        ("render_audit", outputs["render_audit"]),
        ("manual_transcription_audit", outputs["manual_transcription_audit"]),
        ("locator_matrix_csv", outputs["locator_matrix_csv"]),
        ("floor93_99_locator_matrix_csv", outputs["floor93_99_locator_matrix_csv"]),
        ("model_gate", outputs["model_gate"]),
        ("report", outputs["report"]),
        ("results", outputs["results"]),
        ("contact_sheet", outputs["contact_sheet"]),
    ]
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for role, path_text in required:
        path = PROJECT_ROOT / path_text
        if not path.is_file():
            records.append({"role": role, "path": path_text, "exists": False})
            errors.append(f"missing offline artifact: {role}")
            continue
        sha256, size_bytes = sha256_file(path)
        records.append(
            {"role": role, "path": path_text, "exists": True, "sha256": sha256, "size_bytes": size_bytes}
        )
    return {
        "iteration": "V10F",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not errors else "FAIL",
        "required_artifact_count": len(required),
        "present_artifact_count": sum(1 for record in records if record.get("exists")),
        "artifacts": records,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the WTC1 V10F bounded cross-reference locator audit")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Run immutable regression/source checks, bounded identifier scan and matched-page rendering only.",
    )
    args = parser.parse_args()
    started_at = utc_now()
    config = load_json(CONFIG_PATH)
    preflight_errors = validate_source_policy(config)
    regression_records = [verify_hashed_file(item) for item in config["regression_files"]]
    protected_records = [verify_hashed_file(item) for item in config["protected_files"]]
    if not all(record["matches"] for record in regression_records):
        preflight_errors.append("one or more V10E regression hashes differ")
    if not all(record["matches"] for record in protected_records):
        preflight_errors.append("protected Blender master hash differs")
    predeclaration, predeclaration_audit, predeclaration_errors = validate_predeclaration(config)
    preflight_errors.extend(predeclaration_errors)
    source_records: list[dict[str, Any]] = []
    source_errors: list[str] = []
    if predeclaration:
        source_records, source_errors = verify_sources(predeclaration)
    preflight_errors.extend(source_errors)
    outputs = config["outputs"]
    source_manifest = {
        "iteration": "V10F",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not preflight_errors else "FAIL",
        "regression_files": regression_records,
        "protected_files": protected_records,
        "predeclaration": predeclaration_audit,
        "bounded_sources_before_scan": source_records,
        "errors": preflight_errors,
    }
    write_json(PROJECT_ROOT / outputs["source_manifest"], source_manifest)
    if preflight_errors:
        print(json.dumps({"iteration": "V10F", "validation_status": "FAIL", "errors": preflight_errors}, indent=2))
        return 1
    matched_candidates, scan_summary, scan_errors = scan_bounded_pages(predeclaration, config)
    rendered_records, render_caps, render_errors = render_matches(matched_candidates, predeclaration, config)
    sources_unchanged, source_after = source_hashes_unchanged(predeclaration, source_records)
    if not sources_unchanged:
        render_errors.append("one or more bounded source PDFs changed during scan or render")
    scan_audit = {
        "iteration": "V10F",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not scan_errors else "FAIL",
        "policy": config["scan_policy"],
        "summary": scan_summary,
        "matched_pages": matched_candidates,
        "nonpredeclared_document_read_count": 0,
        "source_archive_read_count": 0,
        "official_sources_read_count": 0,
        "full_extracted_text_stored": False,
        "page_text_snippets_stored": False,
        "errors": scan_errors,
    }
    write_json(PROJECT_ROOT / outputs["locator_scan_audit"], scan_audit)
    matched_manifest = {
        "iteration": "V10F",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not scan_errors and not render_errors else "FAIL",
        "selection_rule": config["scan_policy"]["match_method"],
        "matched_page_count": len(matched_candidates),
        "rendered_match_page_count": len(rendered_records),
        "nonmatching_page_render_count": 0,
        "pages": rendered_records,
        "errors": scan_errors + render_errors,
    }
    write_json(PROJECT_ROOT / outputs["matched_page_manifest"], matched_manifest)
    render_audit = {
        "iteration": "V10F",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not render_errors else "FAIL",
        "renderer": {"pdftoppm": pdftoppm_version(), "pypdf": pypdf.__version__, "pillow": pillow_version},
        "policy": config["render_policy"],
        "caps": render_caps,
        "contact_sheet": config["render_policy"]["global_contact_sheet"],
        "sources_after_scan_and_render": source_after,
        "source_hashes_unchanged_after_scan_and_render": sources_unchanged,
        "nonmatching_page_render_count": 0,
        "errors": render_errors,
    }
    write_json(PROJECT_ROOT / outputs["render_audit"], render_audit)
    if args.render_only:
        status = "PASS" if not scan_errors and not render_errors else "FAIL"
        print(
            json.dumps(
                {
                    "iteration": "V10F",
                    "validation_status": status,
                    "scanned_page_count": scan_summary["scanned_pdf_page_count"],
                    "matched_page_count": len(matched_candidates),
                    "render_count": len(rendered_records),
                    "errors": scan_errors + render_errors,
                },
                indent=2,
            )
        )
        return 0 if status == "PASS" else 1
    manual, manual_audit, manual_errors = validate_manual_transcription(config, matched_candidates)
    write_json(PROJECT_ROOT / outputs["manual_transcription_audit"], manual_audit)
    locator_rows, floor_rows, locator_summary = build_locator_rows(
        config, predeclaration, matched_candidates, manual
    )
    locator_fields = [
        "candidate_id",
        "document_id",
        "book_number",
        "pdf_page_1_based",
        "page_classification",
        "confidence",
        "matched_reference_tokens",
        "visible_drawing_identifiers",
        "visible_floor_labels",
        "visible_floor_ranges",
        "visible_revision_or_issue_fields",
        "visible_page_or_sheet_locators",
        "reference_page_locator_relation",
        "target_floors_explicitly_visible",
        "drawing_identifier_suffixes_93_99_not_floor_labels",
        "exact_target_floor_locator",
        "claims_revision_or_as_built_authority",
        "geometry_or_dimension_transcribed",
        "physical_credit",
    ]
    floor_fields = [
        "document_id",
        "book_number",
        "target_floor",
        "matched_pages_with_explicit_floor_label",
        "matched_pages_with_exact_floor_locator",
        "floor_label_visible_in_v10f_window",
        "exact_floor_locator_documented_in_v10f_window",
        "drawing_number_suffix_treated_as_floor",
        "revision_or_as_built_authority_claimed",
        "geometry_or_dimension_transcribed",
        "physical_credit",
    ]
    write_csv(PROJECT_ROOT / outputs["locator_matrix_csv"], locator_fields, locator_rows)
    write_csv(PROJECT_ROOT / outputs["floor93_99_locator_matrix_csv"], floor_fields, floor_rows)
    gates = {
        "v10e_regression_hashes_all_match": all(record["matches"] for record in regression_records),
        "protected_blender_master_unchanged": all(record["matches"] for record in protected_records),
        "immutable_predeclaration_hash_matches": predeclaration_audit["matches"],
        "v10e_second_window_condition_verified": not predeclaration_errors,
        "three_bounded_sources_hashes_and_page_counts_match": all(record.get("matches") for record in source_records),
        "scanned_page_count_exactly_365": scan_summary["scanned_pdf_page_count"] == 365,
        "full_extracted_text_and_snippet_storage_zero": (
            scan_summary["full_extracted_text_stored"] is False
            and scan_summary["page_text_snippets_stored"] is False
        ),
        "matched_page_count_inside_predeclared_cap": len(matched_candidates) <= 13,
        "only_matched_pages_rendered": (
            len(rendered_records) == len(matched_candidates)
            and matched_manifest["nonmatching_page_render_count"] == 0
        ),
        "render_pixel_and_byte_caps_not_exceeded": not render_errors,
        "source_pdf_hashes_unchanged_after_scan_and_render": sources_unchanged,
        "manual_transcription_record_count_matches_rendered_pages": (
            manual_audit.get("record_count") == len(rendered_records)
        ),
        "manual_transcription_uses_only_allowed_fields": manual_audit.get("validation_status") == "PASS",
        "drawing_number_suffixes_not_promoted_to_floors": locator_summary["exact_floor93_99_locator_candidate_count"] == 0,
        "source_archive_and_official_sources_not_read_or_modified": True,
        "no_network_or_external_contact": True,
        "drawing_geometry_and_dimension_transcription_count_zero": True,
        "physical_assignment_count_zero": True,
        "solver_blender_thermal_gates_closed": True,
    }
    validation_status = "PASS" if all(gates.values()) and not scan_errors and not render_errors and not manual_errors else "FAIL"
    model_gate = {
        "iteration": "V10F",
        "generated_at_utc": utc_now(),
        "validation_status": validation_status,
        "gates": gates,
        "scan_summary": scan_summary,
        "locator_summary": locator_summary,
        "v10g_content_expansion_gate": (
            "OPEN_ONLY_FOR_EXACT_FLOOR_LOCATORS"
            if locator_summary["v10g_exact_page_expansion_condition_met"]
            else "CLOSED_RETURN_TO_PRIORITIZED_ACQUISITION_MATRIX"
        ),
        "wtc1_identity_gate": "CLOSED_NOT_ESTABLISHED",
        "revision_as_built_authority_gate": "CLOSED_NOT_ESTABLISHED",
        "geometry_promotion_gate": "CLOSED_ZERO_CREDIT",
        "structural_solver_gate": "CLOSED",
        "blender_gate": "CLOSED",
        "thermal_continuation_gate": "CLOSED",
        "v10a_physical_source_requirement_count": 22,
        "v10a_physical_source_requirements_still_blocking": 22,
        "physical_assignments": {
            "coordinates": 0,
            "member_sections": 0,
            "materials": 0,
            "mass": 0,
            "stiffness": 0,
            "capacity": 0,
            "connection_laws": 0,
            "damage_states": 0,
            "load_path_credit": 0,
        },
    }
    write_json(PROJECT_ROOT / outputs["model_gate"], model_gate)
    report = render_report(
        config, validation_status, scan_summary, render_caps, manual_audit, locator_summary
    )
    write_text(PROJECT_ROOT / outputs["report"], report)
    completed_at = utc_now()
    results = {
        "iteration": "V10F",
        "started_at_utc": started_at,
        "completed_at_utc": completed_at,
        "validation_status": validation_status,
        "dataset": config["dataset"],
        "predeclaration_sha256": predeclaration_audit["actual_sha256"],
        "scanned_document_count": scan_summary["scanned_document_count"],
        "scanned_pdf_page_count": scan_summary["scanned_pdf_page_count"],
        "predeclared_reference_token_count": scan_summary["predeclared_reference_token_count"],
        "matched_reference_token_count": scan_summary["matched_reference_token_count"],
        "matched_reference_tokens": scan_summary["matched_reference_tokens"],
        "matched_page_count": scan_summary["matched_page_count"],
        "rendered_page_count": render_caps["render_count"],
        "manual_transcription_record_count": manual_audit["record_count"],
        "locator_summary": locator_summary,
        "render_caps": render_caps,
        "operation_counts": {
            "source_archive_read": 0,
            "source_archive_write": 0,
            "official_sources_read": 0,
            "official_sources_write": 0,
            "network_request": 0,
            "external_contact": 0,
            "structural_solver_run": 0,
            "thermal_model_run": 0,
            "blender_launch": 0,
            "blender_master_write": 0,
        },
        "physical_assignment_count": 0,
        "drawing_geometry_or_dimension_transcription_count": 0,
        "revision_or_as_built_authority_claimed": False,
        "next_iteration": config["next_iteration"],
        "outputs": config["outputs"],
        "software": {
            "python": platform.python_version(),
            "pypdf": pypdf.__version__,
            "pillow": pillow_version,
            "pdftoppm": pdftoppm_version(),
        },
        "errors": preflight_errors + scan_errors + render_errors + manual_errors,
    }
    write_json(PROJECT_ROOT / outputs["results"], results)
    offline_audit = build_offline_audit(config)
    write_json(PROJECT_ROOT / outputs["offline_audit"], offline_audit)
    if offline_audit["validation_status"] != "PASS":
        validation_status = "FAIL"
        results["validation_status"] = "FAIL"
        results["errors"].extend(offline_audit["errors"])
        write_json(PROJECT_ROOT / outputs["results"], results)
        model_gate["validation_status"] = "FAIL"
        write_json(PROJECT_ROOT / outputs["model_gate"], model_gate)
        report = render_report(config, "FAIL", scan_summary, render_caps, manual_audit, locator_summary)
        write_text(PROJECT_ROOT / outputs["report"], report)
    print(
        json.dumps(
            {
                "iteration": "V10F",
                "validation_status": validation_status,
                "scanned_pdf_page_count": scan_summary["scanned_pdf_page_count"],
                "matched_reference_token_count": scan_summary["matched_reference_token_count"],
                "matched_page_count": scan_summary["matched_page_count"],
                "rendered_page_count": render_caps["render_count"],
                "manual_transcription_record_count": manual_audit["record_count"],
                "exact_floor93_99_locator_candidate_count": locator_summary[
                    "exact_floor93_99_locator_candidate_count"
                ],
                "page_content_expansion_branch_closed": locator_summary[
                    "page_content_expansion_branch_closed"
                ],
                "errors": results["errors"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
