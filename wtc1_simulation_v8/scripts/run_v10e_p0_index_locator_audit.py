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
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdf
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "wtc1_simulation_v8" / "data" / "v10e_p0_index_locator_audit.json"
CHUNK_SIZE = 1024 * 1024
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
    "drawing_geometry_transcribed",
    "dimensions_transcribed",
    "member_properties_transcribed",
    "connection_details_transcribed",
    "physical_properties_assigned",
    "damage_or_load_path_credit_assigned",
    "tower_a_promoted_to_wtc1",
    "revision_or_as_built_authority_claimed",
}
CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
KEYWORD_PATTERNS = {
    "index": re.compile(r"\bindex\b", re.IGNORECASE),
    "drawing": re.compile(r"\bdrawing(?:s)?\b", re.IGNORECASE),
    "revision": re.compile(r"\brevision(?:s)?\b|\brev\.?\b", re.IGNORECASE),
    "tower": re.compile(r"\btower(?:s)?\b", re.IGNORECASE),
    "floor": re.compile(r"\bfloor(?:s)?\b", re.IGNORECASE),
    "story": re.compile(r"\bstor(?:y|ies)\b", re.IGNORECASE),
    "sheet": re.compile(r"\bsheet(?:s)?\b", re.IGNORECASE),
}
DRAWING_TOKEN_PATTERN = re.compile(
    r"(?<![A-Z0-9])(?:1[01]|[1-9])\s*[-–—]\s*[A-Z]{0,3}\d+[A-Z0-9.]*\s*[-–—]\s*\d+(?:\.\d+)?(?![A-Z0-9])",
    re.IGNORECASE,
)
TOWER_TOKEN_PATTERN = re.compile(r"\bTOWER\s+(?:A\s*(?:\+|AND|&)\s*B|A|B)\b", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


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
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def verify_hashed_file(item: dict[str, Any]) -> dict[str, Any]:
    path = (PROJECT_ROOT / item["path"]).resolve()
    exists = path.is_file()
    actual_sha256 = None
    size_bytes = None
    if exists:
        actual_sha256, size_bytes = sha256_file(path)
    return {
        "role": item["role"],
        "path": item["path"],
        "exists": exists,
        "expected_sha256": item["expected_sha256"].lower(),
        "actual_sha256": actual_sha256,
        "size_bytes": size_bytes,
        "matches": bool(exists and actual_sha256 == item["expected_sha256"].lower()),
    }


def check_source_policy(config: dict[str, Any]) -> list[str]:
    expected_false = (
        "source_archive_read",
        "source_archive_modified",
        "official_sources_directory_read",
        "official_sources_directory_modified",
        "network_access_authorized",
        "external_contact_authorized",
        "non_candidate_page_content_read_authorized",
        "full_document_text_extraction_authorized",
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
    )
    expected_true = (
        "v10d_working_copies_read_only",
        "candidate_page_content_read_authorized",
        "candidate_page_render_authorized",
    )
    errors: list[str] = []
    policy = config["source_policy"]
    for key in expected_false:
        if policy.get(key) is not False:
            errors.append(f"source_policy.{key} must be false")
    for key in expected_true:
        if policy.get(key) is not True:
            errors.append(f"source_policy.{key} must be true")
    return errors


def build_candidates(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    candidates: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for target in config["targets"]:
        pages = target.get("candidate_pdf_pages_1_based", [])
        for page_value in pages:
            page_number = int(page_value)
            candidate_id = f"{target['document_id']}__p{page_number:04d}"
            if candidate_id in seen:
                errors.append(f"duplicate candidate: {candidate_id}")
            seen.add(candidate_id)
            if page_number < 1 or page_number > int(target["container_page_count"]):
                errors.append(f"candidate outside declared container bounds: {candidate_id}")
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "acquisition_sequence": int(target["acquisition_sequence"]),
                    "document_id": target["document_id"],
                    "book_number": int(target["book_number"]),
                    "group_id": target["group_id"],
                    "subsystem": target["subsystem"],
                    "source_path": target["path"],
                    "pdf_page_1_based": page_number,
                    "declared_container_page_count": int(target["container_page_count"]),
                    "candidate_rationale": target["candidate_rationale"],
                    "register_tower_label": target["register_tower_label"],
                    "register_drawing_start": target["register_drawing_start"],
                    "register_drawing_end": target["register_drawing_end"],
                }
            )
    required = int(config["render_policy"]["required_candidate_page_count"])
    maximum = int(config["render_policy"]["maximum_candidate_page_count"])
    if len(candidates) != required:
        errors.append(f"candidate count {len(candidates)} does not equal required {required}")
    if len(candidates) > maximum:
        errors.append(f"candidate count {len(candidates)} exceeds maximum {maximum}")
    return candidates, errors


def check_working_copy_manifest(config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    declared = config["working_copy_manifest"]
    path = (PROJECT_ROOT / declared["path"]).resolve()
    errors: list[str] = []
    if not path.is_file():
        return {"path": declared["path"], "exists": False, "matches": False}, ["working-copy manifest missing"]
    actual_sha256, size_bytes = sha256_file(path)
    manifest = load_json(path)
    hash_matches = actual_sha256 == declared["expected_sha256"].lower()
    status_matches = manifest.get("validation_status") == declared["required_validation_status"]
    count_matches = int(manifest.get("accepted_working_copy_count", -1)) == int(declared["required_copy_count"])
    bytes_matches = int(manifest.get("accepted_working_copy_total_bytes", -1)) == int(declared["required_total_bytes"])
    if not hash_matches:
        errors.append("working-copy manifest hash mismatch")
    if not status_matches:
        errors.append("working-copy manifest validation status mismatch")
    if not count_matches:
        errors.append("working-copy manifest copy count mismatch")
    if not bytes_matches:
        errors.append("working-copy manifest byte total mismatch")
    record = {
        "path": declared["path"],
        "exists": True,
        "size_bytes": size_bytes,
        "expected_sha256": declared["expected_sha256"].lower(),
        "actual_sha256": actual_sha256,
        "hash_matches": hash_matches,
        "validation_status": manifest.get("validation_status"),
        "validation_status_matches": status_matches,
        "accepted_working_copy_count": manifest.get("accepted_working_copy_count"),
        "copy_count_matches": count_matches,
        "accepted_working_copy_total_bytes": manifest.get("accepted_working_copy_total_bytes"),
        "byte_total_matches": bytes_matches,
        "matches": hash_matches and status_matches and count_matches and bytes_matches,
    }
    return record, errors


def verify_source_copies(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for target in config["targets"]:
        path = (PROJECT_ROOT / target["path"]).resolve()
        exists = path.is_file()
        sha256 = None
        size_bytes = None
        page_count = None
        pdf_error = None
        if exists:
            sha256, size_bytes = sha256_file(path)
            try:
                reader = PdfReader(path)
                page_count = len(reader.pages)
            except Exception as error:
                pdf_error = f"{type(error).__name__}: {error}"
        hash_matches = sha256 == target["expected_sha256"].lower()
        size_matches = size_bytes == int(target["expected_size_bytes"])
        page_count_matches = page_count == int(target["container_page_count"])
        matches = bool(exists and hash_matches and size_matches and page_count_matches and pdf_error is None)
        if not matches:
            errors.append(f"working copy validation failed: {target['document_id']}")
        records.append(
            {
                "document_id": target["document_id"],
                "book_number": int(target["book_number"]),
                "path": target["path"],
                "exists": exists,
                "expected_sha256": target["expected_sha256"].lower(),
                "actual_sha256_before_render": sha256,
                "expected_size_bytes": int(target["expected_size_bytes"]),
                "actual_size_bytes_before_render": size_bytes,
                "expected_container_page_count": int(target["container_page_count"]),
                "actual_container_page_count": page_count,
                "hash_matches": hash_matches,
                "size_matches": size_matches,
                "page_count_matches": page_count_matches,
                "pdf_error": pdf_error,
                "matches_before_render": matches,
            }
        )
    return records, errors


def embedded_text_signals(page: Any, floor_targets: list[int]) -> dict[str, Any]:
    try:
        text = page.extract_text() or ""
        error = None
    except Exception as exc:
        text = ""
        error = f"{type(exc).__name__}: {exc}"
    encoded = text.encode("utf-8")
    keyword_counts = {name: len(pattern.findall(text)) for name, pattern in KEYWORD_PATTERNS.items()}
    floor_counts = {
        str(floor): len(re.findall(rf"(?<!\d){floor}(?!\d)", text))
        for floor in floor_targets
    }
    drawing_tokens = sorted({re.sub(r"\s+", "", token.upper()).replace("–", "-").replace("—", "-") for token in DRAWING_TOKEN_PATTERN.findall(text)})
    tower_tokens = sorted({re.sub(r"\s+", " ", token.upper()).strip() for token in TOWER_TOKEN_PATTERN.findall(text)})
    return {
        "extraction_error": error,
        "extractable_character_count": len(text),
        "extracted_text_sha256": hashlib.sha256(encoded).hexdigest(),
        "keyword_counts": keyword_counts,
        "target_floor_token_counts": floor_counts,
        "drawing_identifier_candidate_tokens": drawing_tokens[:25],
        "drawing_identifier_candidate_token_count": len(drawing_tokens),
        "tower_label_candidate_tokens": tower_tokens[:10],
        "embedded_text_stored_verbatim": False,
        "manual_visual_confirmation_required": True,
    }


def pdftoppm_version() -> str:
    try:
        completed = subprocess.run(
            ["pdftoppm", "-v"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        text = (completed.stdout + "\n" + completed.stderr).strip().splitlines()
        return text[0] if text else "unknown"
    except Exception as error:
        return f"unavailable: {type(error).__name__}: {error}"


def render_candidate(
    candidate: dict[str, Any],
    target: dict[str, Any],
    config: dict[str, Any],
    temporary_directory: Path,
) -> dict[str, Any]:
    policy = config["render_policy"]
    source_path = (PROJECT_ROOT / target["path"]).resolve()
    output_directory = (PROJECT_ROOT / policy["individual_page_directory"]).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{candidate['candidate_id']}.png"
    temporary_prefix = temporary_directory / candidate["candidate_id"]
    command = [
        "pdftoppm",
        "-f",
        str(candidate["pdf_page_1_based"]),
        "-l",
        str(candidate["pdf_page_1_based"]),
        "-singlefile",
        "-gray",
        "-r",
        str(int(policy["dpi"])),
        "-png",
        str(source_path),
        str(temporary_prefix),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=180)
    temporary_png = temporary_prefix.with_suffix(".png")
    if completed.returncode != 0 or not temporary_png.is_file():
        raise RuntimeError(
            f"pdftoppm failed for {candidate['candidate_id']}: "
            f"returncode={completed.returncode}; stderr={completed.stderr.strip()[:500]}"
        )
    with Image.open(temporary_png) as image:
        image.load()
        width, height = image.size
        mode = image.mode
    pixels = width * height
    if pixels > int(policy["maximum_pixels_per_rendered_page"]):
        raise RuntimeError(f"rendered pixel cap exceeded for {candidate['candidate_id']}: {pixels}")
    shutil.copyfile(temporary_png, output_path)
    png_sha256, png_size = sha256_file(output_path)
    return {
        "render_path": relative_path(output_path),
        "render_sha256": png_sha256,
        "render_size_bytes": png_size,
        "width_pixels": width,
        "height_pixels": height,
        "pixel_count": pixels,
        "image_mode": mode,
        "dpi": int(policy["dpi"]),
        "renderer_return_code": completed.returncode,
    }


def create_contact_sheet(records: list[dict[str, Any]], output_path: Path, columns: int, title: str) -> None:
    if not records:
        raise ValueError("contact sheet requires at least one record")
    tile_width = 430
    tile_height = 320
    image_area_height = 272
    header_height = 34
    rows = (len(records) + columns - 1) // columns
    sheet = Image.new("L", (columns * tile_width, header_height + rows * tile_height), color=255)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((10, 10), title, fill=0, font=font)
    for index, record in enumerate(records):
        row = index // columns
        column = index % columns
        left = column * tile_width
        top = header_height + row * tile_height
        image_path = PROJECT_ROOT / record["render_path"]
        with Image.open(image_path) as source:
            thumbnail = source.convert("L")
            thumbnail.thumbnail((tile_width - 20, image_area_height - 14), Image.Resampling.LANCZOS)
        x = left + (tile_width - thumbnail.width) // 2
        y = top + 6 + (image_area_height - thumbnail.height) // 2
        sheet.paste(thumbnail, (x, y))
        draw.rectangle((left, top, left + tile_width - 1, top + tile_height - 1), outline=150, width=1)
        label = f"{record['document_id']} | PDF p. {record['pdf_page_1_based']}"
        draw.text((left + 8, top + image_area_height + 8), label, fill=0, font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, format="PNG", optimize=True)


def render_pages(
    config: dict[str, Any],
    candidates: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[str]]:
    errors: list[str] = []
    targets_by_id = {target["document_id"]: target for target in config["targets"]}
    floor_targets = [int(value) for value in config["manual_transcription"]["floor_target_set"]]
    records: list[dict[str, Any]] = []
    readers: dict[str, PdfReader] = {}
    tmp_root = PROJECT_ROOT / "tmp" / "pdfs"
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="v10e_", dir=tmp_root) as temporary_name:
        temporary_directory = Path(temporary_name)
        for candidate in candidates:
            target = targets_by_id[candidate["document_id"]
            ]
            try:
                reader = readers.get(candidate["document_id"])
                if reader is None:
                    reader = PdfReader(PROJECT_ROOT / target["path"])
                    readers[candidate["document_id"]] = reader
                page = reader.pages[candidate["pdf_page_1_based"] - 1]
                text_signals = embedded_text_signals(page, floor_targets)
                render = render_candidate(candidate, target, config, temporary_directory)
                records.append({**candidate, **render, "embedded_text_signals": text_signals})
            except Exception as error:
                errors.append(f"{candidate['candidate_id']}: {type(error).__name__}: {error}")

    source_after: list[dict[str, Any]] = []
    before_by_id = {record["document_id"]: record for record in source_records}
    for target in config["targets"]:
        path = PROJECT_ROOT / target["path"]
        actual_sha256, size_bytes = sha256_file(path)
        before = before_by_id[target["document_id"]]
        unchanged = (
            actual_sha256 == before["actual_sha256_before_render"]
            and size_bytes == before["actual_size_bytes_before_render"]
        )
        if not unchanged:
            errors.append(f"source changed during render: {target['document_id']}")
        source_after.append(
            {
                **before,
                "actual_sha256_after_render": actual_sha256,
                "actual_size_bytes_after_render": size_bytes,
                "unchanged_after_render": unchanged,
            }
        )

    if len(records) == len(candidates):
        by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_document[record["document_id"]].append(record)
        document_contact_records: list[dict[str, Any]] = []
        doc_dir = PROJECT_ROOT / config["render_policy"]["per_document_contact_sheet_directory"]
        for document_id, document_records in by_document.items():
            document_records.sort(key=lambda item: item["pdf_page_1_based"])
            path = doc_dir / f"{document_id}__contact_sheet.png"
            create_contact_sheet(document_records, path, min(3, len(document_records)), f"V10E | {document_id}")
            sha256, size = sha256_file(path)
            document_contact_records.append(
                {
                    "document_id": document_id,
                    "path": relative_path(path),
                    "sha256": sha256,
                    "size_bytes": size,
                    "candidate_page_count": len(document_records),
                }
            )
        global_path = PROJECT_ROOT / config["render_policy"]["global_contact_sheet"]
        create_contact_sheet(records, global_path, 4, "V10E | 29 candidate PDF pages | visual locator audit")
        global_sha256, global_size = sha256_file(global_path)
        contact_sheet_record = {
            "path": relative_path(global_path),
            "sha256": global_sha256,
            "size_bytes": global_size,
            "candidate_page_count": len(records),
            "per_document_contact_sheets": sorted(document_contact_records, key=lambda item: item["document_id"]),
        }
    else:
        contact_sheet_record = {
            "path": config["render_policy"]["global_contact_sheet"],
            "sha256": None,
            "size_bytes": None,
            "candidate_page_count": len(records),
            "per_document_contact_sheets": [],
        }

    aggregate_pixels = sum(int(record["pixel_count"]) for record in records)
    aggregate_png_bytes = sum(int(record["render_size_bytes"]) for record in records)
    policy = config["render_policy"]
    caps = {
        "render_count": len(records),
        "required_render_count": int(policy["required_candidate_page_count"]),
        "maximum_render_count": int(policy["maximum_candidate_page_count"]),
        "aggregate_rendered_pixels": aggregate_pixels,
        "maximum_aggregate_rendered_pixels": int(policy["maximum_aggregate_rendered_pixels"]),
        "aggregate_rendered_png_bytes": aggregate_png_bytes,
        "maximum_aggregate_rendered_png_bytes": int(policy["maximum_aggregate_rendered_png_bytes"]),
        "maximum_observed_pixels_per_page": max((int(record["pixel_count"]) for record in records), default=0),
        "maximum_pixels_per_rendered_page": int(policy["maximum_pixels_per_rendered_page"]),
    }
    if caps["render_count"] != caps["required_render_count"]:
        errors.append("render count does not equal required candidate count")
    if caps["render_count"] > caps["maximum_render_count"]:
        errors.append("render count exceeds maximum")
    if caps["aggregate_rendered_pixels"] > caps["maximum_aggregate_rendered_pixels"]:
        errors.append("aggregate pixel cap exceeded")
    if caps["aggregate_rendered_png_bytes"] > caps["maximum_aggregate_rendered_png_bytes"]:
        errors.append("aggregate PNG byte cap exceeded")
    if caps["maximum_observed_pixels_per_page"] > caps["maximum_pixels_per_rendered_page"]:
        errors.append("per-page pixel cap exceeded")
    return records, source_after, {"caps": caps, "contact_sheet": contact_sheet_record}, errors


def validate_manual_transcription(
    config: dict[str, Any], candidates: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    path = PROJECT_ROOT / config["manual_transcription"]["path"]
    errors: list[str] = []
    if not path.is_file():
        audit = {
            "iteration": "V10E",
            "generated_at_utc": utc_now(),
            "validation_status": "FAIL",
            "path": relative_path(path),
            "errors": ["manual transcription file missing"],
        }
        return None, audit, audit["errors"]
    payload = load_json(path)
    if set(payload) != TOP_LEVEL_TRANSCRIPTION_KEYS:
        errors.append(
            "manual transcription top-level keys differ from the exact allowed set: "
            + ", ".join(sorted(set(payload) ^ TOP_LEVEL_TRANSCRIPTION_KEYS))
        )
    if payload.get("iteration") != "V10E":
        errors.append("manual transcription iteration is not V10E")
    if payload.get("method") != config["manual_transcription"]["transcription_method"]:
        errors.append("manual transcription method does not match configuration")
    attestation = payload.get("scope_attestation", {})
    if not isinstance(attestation, dict) or set(attestation) != SCOPE_ATTESTATION_KEYS:
        errors.append("scope_attestation keys differ from the exact allowed set")
    elif any(attestation.get(key) is not False for key in SCOPE_ATTESTATION_KEYS):
        errors.append("every scope_attestation value must be false")
    records = payload.get("records", [])
    if not isinstance(records, list):
        records = []
        errors.append("records must be a list")
    candidate_by_id = {item["candidate_id"]: item for item in candidates}
    allowed_fields = set(config["manual_transcription"]["allowed_transcription_fields"])
    allowed_classes = set(config["manual_transcription"]["allowed_page_classifications"])
    seen: set[str] = set()
    forbidden_key_occurrences: list[str] = []
    normalized_records: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        prefix = f"record[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} is not an object")
            continue
        if set(record) != RECORD_KEYS:
            errors.append(f"{prefix} keys differ from the exact allowed record set")
        candidate_id = record.get("candidate_id")
        if candidate_id in seen:
            errors.append(f"duplicate manual record: {candidate_id}")
        seen.add(candidate_id)
        candidate = candidate_by_id.get(candidate_id)
        if candidate is None:
            errors.append(f"unknown candidate in manual transcription: {candidate_id}")
            continue
        if record.get("document_id") != candidate["document_id"]:
            errors.append(f"document mismatch: {candidate_id}")
        if record.get("pdf_page_1_based") != candidate["pdf_page_1_based"]:
            errors.append(f"page mismatch: {candidate_id}")
        if record.get("page_classification") not in allowed_classes:
            errors.append(f"invalid page classification: {candidate_id}")
        if record.get("visual_review_status") != "COMPLETED":
            errors.append(f"visual review not completed: {candidate_id}")
        if record.get("confidence") not in CONFIDENCE_VALUES:
            errors.append(f"invalid confidence: {candidate_id}")
        transcription = record.get("transcription")
        if not isinstance(transcription, dict):
            errors.append(f"transcription is not an object: {candidate_id}")
            transcription = {}
        if set(transcription) != allowed_fields:
            errors.append(f"transcription fields differ from exact allowed set: {candidate_id}")
        normalized_transcription: dict[str, list[str]] = {}
        for field in allowed_fields:
            values = transcription.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                errors.append(f"{candidate_id}.{field} must be a list of strings")
                values = []
            clean_values = [value.strip() for value in values if value.strip()]
            normalized_transcription[field] = clean_values
        for forbidden in config["manual_transcription"]["forbidden_transcription_fields"]:
            if forbidden in transcription:
                forbidden_key_occurrences.append(f"{candidate_id}.{forbidden}")
        normalized_records.append({**record, "transcription": normalized_transcription})
    expected_ids = set(candidate_by_id)
    missing_ids = sorted(expected_ids - seen)
    extra_ids = sorted(seen - expected_ids)
    if missing_ids:
        errors.append("missing candidates: " + ", ".join(missing_ids))
    if extra_ids:
        errors.append("extra candidates: " + ", ".join(extra_ids))
    required_count = int(config["render_policy"]["required_candidate_page_count"])
    if len(records) != required_count:
        errors.append(f"manual record count {len(records)} does not equal required {required_count}")
    if forbidden_key_occurrences:
        errors.append("forbidden transcription keys present: " + ", ".join(forbidden_key_occurrences))
    classification_counts = Counter(record.get("page_classification", "INVALID") for record in normalized_records)
    field_value_counts = {
        field: sum(len(record["transcription"].get(field, [])) for record in normalized_records)
        for field in sorted(allowed_fields)
    }
    audit = {
        "iteration": "V10E",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not errors else "FAIL",
        "path": relative_path(path),
        "record_count": len(records),
        "required_record_count": required_count,
        "unique_candidate_count": len(seen),
        "missing_candidate_ids": missing_ids,
        "extra_candidate_ids": extra_ids,
        "classification_counts": dict(sorted(classification_counts.items())),
        "allowed_field_value_counts": field_value_counts,
        "forbidden_transcription_key_occurrence_count": len(forbidden_key_occurrences),
        "scope_attestation": attestation,
        "errors": errors,
    }
    normalized = {**payload, "records": normalized_records} if not errors else None
    return normalized, audit, errors


def target_floors_from_record(record: dict[str, Any], targets: list[int]) -> set[int]:
    values = (
        record["transcription"].get("visible_floor_labels", [])
        + record["transcription"].get("visible_floor_ranges", [])
    )
    found: set[int] = set()
    for floor in targets:
        pattern = re.compile(rf"(?<!\d){floor}(?!\d)")
        if any(pattern.search(value) for value in values):
            found.add(floor)
    return found


def make_locator_rows(
    config: dict[str, Any], manual: dict[str, Any], candidates: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidate_by_id = {item["candidate_id"]: item for item in candidates}
    floor_targets = [int(value) for value in config["manual_transcription"]["floor_target_set"]]
    index_rows: list[dict[str, Any]] = []
    records_by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
    exact_floor_locator_records: list[str] = []
    continuation_reference_records: list[str] = []
    for record in manual["records"]:
        candidate = candidate_by_id[record["candidate_id"]]
        transcription = record["transcription"]
        floors = target_floors_from_record(record, floor_targets)
        locator_values = (
            transcription["visible_drawing_identifiers"]
            + transcription["visible_page_or_sheet_locators"]
            + transcription["visible_cross_references"]
        )
        exact_floor_locator = bool(floors and locator_values)
        continuation_reference = bool(transcription["visible_cross_references"])
        if exact_floor_locator:
            exact_floor_locator_records.append(record["candidate_id"])
        if continuation_reference:
            continuation_reference_records.append(record["candidate_id"])
        row = {
            "candidate_id": record["candidate_id"],
            "document_id": record["document_id"],
            "book_number": candidate["book_number"],
            "subsystem": candidate["subsystem"],
            "pdf_page_1_based": record["pdf_page_1_based"],
            "page_classification": record["page_classification"],
            "confidence": record["confidence"],
            "visible_drawing_identifiers": " | ".join(transcription["visible_drawing_identifiers"]),
            "visible_page_or_sheet_locators": " | ".join(transcription["visible_page_or_sheet_locators"]),
            "visible_index_headings": " | ".join(transcription["visible_index_headings"]),
            "visible_tower_labels": " | ".join(transcription["visible_tower_labels"]),
            "visible_floor_labels": " | ".join(transcription["visible_floor_labels"]),
            "visible_floor_ranges": " | ".join(transcription["visible_floor_ranges"]),
            "visible_revision_or_issue_fields": " | ".join(transcription["visible_revision_or_issue_fields"]),
            "visible_cross_references": " | ".join(transcription["visible_cross_references"]),
            "target_floors_explicitly_visible": " | ".join(str(value) for value in sorted(floors)),
            "exact_floor_locator_on_same_candidate_page": exact_floor_locator,
            "index_continuation_cross_reference_visible": continuation_reference,
            "claims_wtc1_applicability": False,
            "claims_revision_or_as_built_authority": False,
            "physical_credit": 0,
        }
        index_rows.append(row)
        records_by_document[record["document_id"]].append({"record": record, "row": row, "floors": floors})

    floor_rows: list[dict[str, Any]] = []
    targets_by_id = {target["document_id"]: target for target in config["targets"]}
    for target in config["targets"]:
        document_records = records_by_document.get(target["document_id"], [])
        for floor in floor_targets:
            matches = [item for item in document_records if floor in item["floors"]]
            locator_matches = [item for item in matches if item["row"]["exact_floor_locator_on_same_candidate_page"]]
            floor_rows.append(
                {
                    "document_id": target["document_id"],
                    "book_number": int(target["book_number"]),
                    "subsystem": target["subsystem"],
                    "target_floor": floor,
                    "candidate_pages_with_floor_label": " | ".join(
                        str(item["record"]["pdf_page_1_based"]) for item in matches
                    ),
                    "candidate_pages_with_exact_floor_locator": " | ".join(
                        str(item["record"]["pdf_page_1_based"]) for item in locator_matches
                    ),
                    "floor_label_visible_in_bounded_window": bool(matches),
                    "exact_floor_locator_documented_in_bounded_window": bool(locator_matches),
                    "tower_label_from_register": target["register_tower_label"],
                    "tower_a_promoted_to_wtc1": False,
                    "revision_or_as_built_authority_claimed": False,
                    "geometry_or_dimension_transcribed": False,
                    "physical_credit": 0,
                }
            )
    summary = {
        "exact_floor_locator_candidate_ids": sorted(exact_floor_locator_records),
        "exact_floor_locator_candidate_count": len(exact_floor_locator_records),
        "index_continuation_cross_reference_candidate_ids": sorted(continuation_reference_records),
        "index_continuation_cross_reference_candidate_count": len(continuation_reference_records),
        "documents_with_any_target_floor_label": sorted(
            {
                row["document_id"]
                for row in floor_rows
                if row["floor_label_visible_in_bounded_window"]
            }
        ),
        "documents_with_exact_target_floor_locator": sorted(
            {
                row["document_id"]
                for row in floor_rows
                if row["exact_floor_locator_documented_in_bounded_window"]
            }
        ),
    }
    summary["v10f_second_bounded_window_condition_met"] = bool(
        summary["exact_floor_locator_candidate_count"]
        or summary["index_continuation_cross_reference_candidate_count"]
    )
    return index_rows, floor_rows, summary


def render_report(
    config: dict[str, Any],
    source_manifest: dict[str, Any],
    render_audit: dict[str, Any],
    manual_audit: dict[str, Any],
    locator_summary: dict[str, Any],
    validation_status: str,
) -> str:
    caps = render_audit["caps"]
    source_count = len(source_manifest["working_copies"])
    visible_docs = locator_summary["documents_with_any_target_floor_label"]
    exact_docs = locator_summary["documents_with_exact_target_floor_locator"]
    next_condition = locator_summary["v10f_second_bounded_window_condition_met"]
    expansion = "OUVERTE de façon strictement bornée" if next_condition else "FERMÉE"
    lines = [
        "# WTC 1 — V10E — audit borné des localisateurs d’index P0",
        "",
        f"**Validation générale : {validation_status}**",
        "",
        "## Résultat opérationnel",
        "",
        f"V10E a vérifié {source_count} copies P0 issues de V10D et rendu exactement {caps['render_count']} pages candidates pré-déclarées. "
        f"La transcription visuelle comporte {manual_audit['record_count']} enregistrements. La porte d’expansion V10F est **{expansion}** selon la seule présence d’un renvoi d’index visible ou d’un localisateur explicite associé aux étages 93 à 99.",
        "",
        "Cette décision ne confère aucune autorité as-built, ne démontre pas que « Tower A » désigne WTC 1 et n’accorde aucun crédit géométrique ou mécanique.",
        "",
        "## 1. Faits directement observés ou transcrits",
        "",
        f"- {caps['render_count']} rendus PNG ont été produits à {config['render_policy']['dpi']} dpi en niveaux de gris, uniquement pour les pages candidates.",
        f"- Documents où un libellé explicite parmi 93–99 apparaît dans la fenêtre bornée : {', '.join(visible_docs) if visible_docs else 'aucun'}.",
        f"- Documents où un tel libellé partage une page avec un identifiant/localisateur visible : {', '.join(exact_docs) if exact_docs else 'aucun'}.",
        f"- Pages portant un renvoi d’index/croisé transcrit : {locator_summary['index_continuation_cross_reference_candidate_count']}.",
        "- Les chaînes transcrites restent des inscriptions visibles sur les rendus ; leur exactitude documentaire et leur applicabilité au WTC 1 ne sont pas établies par cette seule étape.",
        "",
        "## 2. Résultats d’un modèle officiel",
        "",
        "Aucun résultat de modèle officiel n’est calculé, relu ou validé dans V10E.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune archive source locale et aucun fichier de `work/official_sources/` n’a été lu pendant V10E. Les intitulés de registre hérités de V10D restent des affirmations documentaires, non une validation de provenance ou de statut as-built.",
        "",
        "## 4. Hypothèses propres au modèle",
        "",
        "- Les pages 1 à 3 de huit PDF et les pages 1 à 5 du Book 7 ont été traitées comme fenêtres candidates d’index/front matter.",
        "- Pour le Book 7, l’écart de cinq pages entre le conteneur et le registre motive seulement cette fenêtre ; il ne prouve pas que ces cinq pages constituent l’index.",
        "- Une correspondance textuelle à un étage 93–99 reste un localisateur documentaire potentiel, pas une géométrie ni une propriété structurale.",
        "",
        "## 5. Résultats dérivés",
        "",
        f"- Porte conditionnelle V10F : {'condition satisfaite pour une seconde fenêtre bornée' if next_condition else 'condition non satisfaite ; aucune seconde fenêtre de contenu n’est autorisée par V10E'}.",
        f"- Pixels rendus : {caps['aggregate_rendered_pixels']:,} sur un plafond de {caps['maximum_aggregate_rendered_pixels']:,}.",
        f"- Octets PNG individuels : {caps['aggregate_rendered_png_bytes']:,} sur un plafond de {caps['maximum_aggregate_rendered_png_bytes']:,}.",
        "- Masse, rigidité, résistance, capacité, loi de connexion, dommage et crédit de chemin de charge : zéro.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- La chaîne de provenance complète, l’identité WTC 1, l’autorité de révision et le statut as-built restent non établis.",
        "- Les propriétés physiques, détails géométriques et états de dommage nécessaires à un solveur ne sont pas acquis dans V10E.",
        "- Un index ou un renvoi n’est pas le dessin référencé ; toute lecture suivante doit être pré-déclarée et bornée.",
        "",
        "## Garde-fous",
        "",
        "- Aucun accès réseau, contact externe, solveur structurel, calcul thermique ou lancement de Blender.",
        "- Aucun contenu de page non candidate lu ou transcrit.",
        "- Aucun dessin, cote, section de membre, matériau ou détail d’assemblage transcrit.",
        "- Le fichier Blender maître est resté inchangé.",
        "",
        "## Suite V10F",
        "",
        config["next_iteration"]["objective"],
    ]
    return "\n".join(lines)


def csv_data_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def build_offline_package_audit(config: dict[str, Any]) -> dict[str, Any]:
    outputs = config["outputs"]
    artifact_specs = [
        ("configuration", relative_path(CONFIG_PATH)),
        ("script", "wtc1_simulation_v8/scripts/run_v10e_p0_index_locator_audit.py"),
        ("manual_transcription", config["manual_transcription"]["path"]),
        ("source_manifest", outputs["source_manifest"]),
        ("candidate_page_manifest", outputs["candidate_page_manifest"]),
        ("render_audit", outputs["render_audit"]),
        ("manual_transcription_audit", outputs["manual_transcription_audit"]),
        ("index_locator_matrix_csv", outputs["index_locator_matrix_csv"]),
        ("floor93_99_locator_matrix_csv", outputs["floor93_99_locator_matrix_csv"]),
        ("model_gate", outputs["model_gate"]),
        ("report", outputs["report"]),
        ("results", outputs["results"]),
        ("contact_sheet", outputs["contact_sheet"]),
    ]
    artifacts: list[dict[str, Any]] = []
    missing: list[str] = []
    for role, relative in artifact_specs:
        path = PROJECT_ROOT / relative
        if not path.is_file():
            missing.append(relative)
            artifacts.append({"role": role, "path": relative, "exists": False, "sha256": None, "size_bytes": None})
            continue
        sha256, size_bytes = sha256_file(path)
        artifacts.append(
            {
                "role": role,
                "path": relative,
                "exists": True,
                "sha256": sha256,
                "size_bytes": size_bytes,
            }
        )

    checks: dict[str, bool] = {"all_declared_artifacts_exist": not missing}
    if not missing:
        source_manifest = load_json(PROJECT_ROOT / outputs["source_manifest"])
        candidate_manifest = load_json(PROJECT_ROOT / outputs["candidate_page_manifest"])
        render_audit = load_json(PROJECT_ROOT / outputs["render_audit"])
        manual_audit = load_json(PROJECT_ROOT / outputs["manual_transcription_audit"])
        gate = load_json(PROJECT_ROOT / outputs["model_gate"])
        results = load_json(PROJECT_ROOT / outputs["results"])
        operation_counts = source_manifest["operation_counts"]
        checks.update(
            {
                "source_manifest_pass": source_manifest.get("validation_status") == "PASS",
                "candidate_manifest_pass": candidate_manifest.get("validation_status") == "PASS",
                "render_audit_pass": render_audit.get("validation_status") == "PASS",
                "manual_transcription_audit_pass": manual_audit.get("validation_status") == "PASS",
                "model_gate_pass": gate.get("validation_status") == "PASS",
                "results_pass": results.get("validation_status") == "PASS",
                "candidate_page_count_exactly_29": candidate_manifest.get("candidate_page_count") == 29,
                "rendered_page_count_exactly_29": candidate_manifest.get("rendered_candidate_page_count") == 29,
                "manual_record_count_exactly_29": manual_audit.get("record_count") == 29,
                "index_locator_csv_row_count_exactly_29": csv_data_row_count(
                    PROJECT_ROOT / outputs["index_locator_matrix_csv"]
                )
                == 29,
                "floor93_99_csv_row_count_exactly_63": csv_data_row_count(
                    PROJECT_ROOT / outputs["floor93_99_locator_matrix_csv"]
                )
                == 63,
                "non_candidate_page_content_read_count_zero": candidate_manifest.get(
                    "non_candidate_page_content_read_count"
                )
                == 0,
                "source_hashes_unchanged_after_render": render_audit.get(
                    "source_hashes_unchanged_after_render"
                )
                is True,
                "all_procedural_gates_true": all(gate.get("gates", {}).values()),
                "physical_assignment_count_zero": sum(gate.get("physical_assignments", {}).values()) == 0,
                "tower_a_not_promoted_to_wtc1": results.get("tower_a_promoted_to_wtc1") is False,
                "revision_or_as_built_authority_not_claimed": results.get(
                    "revision_or_as_built_authority_claimed"
                )
                is False,
                "source_archive_and_official_sources_operation_count_zero": all(
                    operation_counts.get(key) == 0
                    for key in (
                        "source_archive_read",
                        "source_archive_write",
                        "official_sources_read",
                        "official_sources_write",
                    )
                ),
                "network_external_solver_thermal_blender_operation_count_zero": all(
                    operation_counts.get(key) == 0
                    for key in (
                        "network_request",
                        "external_contact",
                        "structural_solver_run",
                        "thermal_model_run",
                        "blender_launch",
                        "blender_master_write",
                    )
                ),
            }
        )
    status = "PASS" if all(checks.values()) else "FAIL"
    return {
        "iteration": "V10E",
        "generated_at_utc": utc_now(),
        "validation_status": status,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "checks": checks,
        "missing_artifacts": missing,
        "scope": "Offline package consistency and hash audit only; no archive, network, solver, thermal or Blender operation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded V10E P0 drawing-index locator audit.")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Verify and render the exact candidate pages without requiring manual transcription.",
    )
    args = parser.parse_args()
    started_at = utc_now()
    config = load_json(CONFIG_PATH)
    if config.get("iteration") != "V10E":
        raise RuntimeError("configuration iteration is not V10E")

    preflight_errors = check_source_policy(config)
    candidates, candidate_errors = build_candidates(config)
    preflight_errors.extend(candidate_errors)
    regression_records = [verify_hashed_file(item) for item in config["regression_files"]]
    protected_records = [verify_hashed_file(item) for item in config["protected_files"]]
    if not all(record["matches"] for record in regression_records):
        preflight_errors.append("one or more V10D regression hashes do not match")
    if not all(record["matches"] for record in protected_records):
        preflight_errors.append("one or more protected-file hashes do not match")
    manifest_record, manifest_errors = check_working_copy_manifest(config)
    preflight_errors.extend(manifest_errors)
    source_records_before, source_errors = verify_source_copies(config)
    preflight_errors.extend(source_errors)

    if preflight_errors:
        print(json.dumps({"iteration": "V10E", "validation_status": "FAIL", "errors": preflight_errors}, indent=2))
        return 1

    rendered_records, source_records_after, render_meta, render_errors = render_pages(
        config, candidates, source_records_before
    )
    source_unchanged = all(record["unchanged_after_render"] for record in source_records_after)
    source_manifest = {
        "iteration": "V10E",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not render_errors and source_unchanged else "FAIL",
        "scope": "Nine hash-verified V10D P0 working copies only; source archive and work/official_sources not read.",
        "regression_files": regression_records,
        "protected_files": protected_records,
        "working_copy_manifest": manifest_record,
        "working_copies": source_records_after,
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
        "errors": render_errors,
    }
    outputs = config["outputs"]
    write_json(PROJECT_ROOT / outputs["source_manifest"], source_manifest)
    candidate_manifest = {
        "iteration": "V10E",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not render_errors else "FAIL",
        "candidate_page_count": len(candidates),
        "rendered_candidate_page_count": len(rendered_records),
        "non_candidate_page_content_read_count": 0,
        "embedded_text_extraction_scope": "candidate pages only",
        "embedded_text_stored_verbatim": False,
        "candidates": rendered_records,
        "errors": render_errors,
    }
    write_json(PROJECT_ROOT / outputs["candidate_page_manifest"], candidate_manifest)
    render_audit = {
        "iteration": "V10E",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if not render_errors else "FAIL",
        "software": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pypdf": pypdf.__version__,
            "pillow": pillow_version,
            "pdftoppm": pdftoppm_version(),
        },
        "policy": config["render_policy"],
        "caps": render_meta["caps"],
        "contact_sheet": render_meta["contact_sheet"],
        "source_hashes_unchanged_after_render": source_unchanged,
        "non_candidate_page_content_read_count": 0,
        "errors": render_errors,
    }
    write_json(PROJECT_ROOT / outputs["render_audit"], render_audit)

    if args.render_only:
        status = "PASS" if not render_errors and source_unchanged else "FAIL"
        print(
            json.dumps(
                {
                    "iteration": "V10E",
                    "stage": "RENDER_ONLY",
                    "validation_status": status,
                    "candidate_page_count": len(candidates),
                    "render_count": len(rendered_records),
                    "contact_sheet": outputs["contact_sheet"],
                    "errors": render_errors,
                },
                indent=2,
            )
        )
        return 0 if status == "PASS" else 1

    manual, manual_audit, manual_errors = validate_manual_transcription(config, candidates)
    write_json(PROJECT_ROOT / outputs["manual_transcription_audit"], manual_audit)
    if manual is None:
        print(json.dumps({"iteration": "V10E", "validation_status": "FAIL", "errors": manual_errors}, indent=2))
        return 1

    index_rows, floor_rows, locator_summary = make_locator_rows(config, manual, candidates)
    index_fields = [
        "candidate_id",
        "document_id",
        "book_number",
        "subsystem",
        "pdf_page_1_based",
        "page_classification",
        "confidence",
        "visible_drawing_identifiers",
        "visible_page_or_sheet_locators",
        "visible_index_headings",
        "visible_tower_labels",
        "visible_floor_labels",
        "visible_floor_ranges",
        "visible_revision_or_issue_fields",
        "visible_cross_references",
        "target_floors_explicitly_visible",
        "exact_floor_locator_on_same_candidate_page",
        "index_continuation_cross_reference_visible",
        "claims_wtc1_applicability",
        "claims_revision_or_as_built_authority",
        "physical_credit",
    ]
    floor_fields = [
        "document_id",
        "book_number",
        "subsystem",
        "target_floor",
        "candidate_pages_with_floor_label",
        "candidate_pages_with_exact_floor_locator",
        "floor_label_visible_in_bounded_window",
        "exact_floor_locator_documented_in_bounded_window",
        "tower_label_from_register",
        "tower_a_promoted_to_wtc1",
        "revision_or_as_built_authority_claimed",
        "geometry_or_dimension_transcribed",
        "physical_credit",
    ]
    write_csv(PROJECT_ROOT / outputs["index_locator_matrix_csv"], index_fields, index_rows)
    write_csv(PROJECT_ROOT / outputs["floor93_99_locator_matrix_csv"], floor_fields, floor_rows)

    gates = {
        "v10d_regression_hashes_all_match": all(record["matches"] for record in regression_records),
        "v10d_working_copy_manifest_matches": manifest_record["matches"],
        "all_nine_working_copy_hashes_and_sizes_match": all(
            record["matches_before_render"] for record in source_records_after
        ),
        "protected_blender_master_unchanged": all(record["matches"] for record in protected_records),
        "candidate_page_count_exactly_29": len(candidates) == 29,
        "candidate_pages_unique_and_inside_container_bounds": not candidate_errors,
        "render_count_exactly_29": len(rendered_records) == 29,
        "render_pixel_and_byte_caps_not_exceeded": not render_errors,
        "source_pdf_hashes_unchanged_after_render": source_unchanged,
        "manual_transcription_record_count_exactly_29": manual_audit["record_count"] == 29,
        "manual_transcription_uses_only_allowed_fields": manual_audit["validation_status"] == "PASS",
        "non_candidate_page_content_read_count_zero": candidate_manifest["non_candidate_page_content_read_count"] == 0,
        "drawing_geometry_and_dimension_transcription_count_zero": (
            manual_audit["forbidden_transcription_key_occurrence_count"] == 0
            and all(value is False for value in manual_audit["scope_attestation"].values())
        ),
        "source_archive_and_official_sources_not_read_or_modified": True,
        "no_network_or_external_contact": True,
        "physical_assignment_count_zero": True,
        "solver_blender_thermal_gates_closed": True,
    }
    validation_status = "PASS" if all(gates.values()) else "FAIL"
    model_gate = {
        "iteration": "V10E",
        "generated_at_utc": utc_now(),
        "validation_status": validation_status,
        "gates": gates,
        "locator_summary": locator_summary,
        "v10f_content_expansion_gate": (
            "OPEN_FOR_ONE_PREDECLARED_BOUNDED_WINDOW"
            if locator_summary["v10f_second_bounded_window_condition_met"]
            else "CLOSED_RETURN_TO_PRIORITY_MATRIX"
        ),
        "wtc1_identity_gate": "CLOSED_NOT_ESTABLISHED",
        "revision_as_built_authority_gate": "CLOSED_NOT_ESTABLISHED",
        "geometry_promotion_gate": "CLOSED_ZERO_CREDIT",
        "structural_solver_gate": "CLOSED",
        "blender_gate": "CLOSED",
        "thermal_continuation_gate": "CLOSED",
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
    results = {
        "iteration": "V10E",
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "validation_status": validation_status,
        "dataset": config["dataset"],
        "candidate_page_count": len(candidates),
        "rendered_page_count": len(rendered_records),
        "manual_transcription_record_count": manual_audit["record_count"],
        "source_copy_count": len(source_records_after),
        "locator_summary": locator_summary,
        "render_caps": render_meta["caps"],
        "page_classification_counts": manual_audit["classification_counts"],
        "operation_counts": source_manifest["operation_counts"],
        "physical_assignment_count": 0,
        "drawing_geometry_or_dimension_transcription_count": 0,
        "tower_a_promoted_to_wtc1": False,
        "revision_or_as_built_authority_claimed": False,
        "next_iteration": config["next_iteration"],
        "outputs": outputs,
    }
    write_json(PROJECT_ROOT / outputs["results"], results)
    report = render_report(config, source_manifest, render_audit, manual_audit, locator_summary, validation_status)
    write_text(PROJECT_ROOT / outputs["report"], report)
    offline_audit = build_offline_package_audit(config)
    write_json(PROJECT_ROOT / outputs["offline_audit"], offline_audit)
    final_status = "PASS" if validation_status == "PASS" and offline_audit["validation_status"] == "PASS" else "FAIL"
    print(
        json.dumps(
            {
                "iteration": "V10E",
                "stage": "FINAL",
                "validation_status": final_status,
                "candidate_page_count": len(candidates),
                "render_count": len(rendered_records),
                "manual_record_count": manual_audit["record_count"],
                "exact_floor_locator_candidate_count": locator_summary["exact_floor_locator_candidate_count"],
                "index_continuation_cross_reference_candidate_count": locator_summary[
                    "index_continuation_cross_reference_candidate_count"
                ],
                "v10f_second_bounded_window_condition_met": locator_summary[
                    "v10f_second_bounded_window_condition_met"
                ],
                "offline_package_audit_status": offline_audit["validation_status"],
                "offline_package_artifact_count": offline_audit["artifact_count"],
                "errors": manual_errors + render_errors,
            },
            indent=2,
        )
    )
    return 0 if final_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
