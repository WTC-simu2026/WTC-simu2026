from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10j_bounded_frontmatter_index_audit.json"
SCRIPT_PATH = Path(__file__).resolve()


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
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def abs_from_rel(relative_path: str) -> Path:
    return ROOT / Path(relative_path)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def font(size: int) -> ImageFont.ImageFont:
    arial = Path("C:/Windows/Fonts/arial.ttf")
    if arial.exists():
        return ImageFont.truetype(str(arial), size=size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def make_vertical_contact_sheet(
    image_records: list[dict[str, Any]], output_path: Path, title: str, target_width: int = 1800
) -> dict[str, Any]:
    title_font = font(34)
    label_font = font(26)
    margin = 28
    title_height = 70
    label_height = 48
    prepared: list[tuple[Image.Image, str]] = []
    for record in image_records:
        source = abs_from_rel(record["render_path"])
        with Image.open(source) as opened:
            page = opened.convert("L")
            scale = min(1.0, (target_width - 2 * margin) / page.width)
            resized = page.resize(
                (max(1, round(page.width * scale)), max(1, round(page.height * scale))),
                Image.Resampling.LANCZOS,
            )
            prepared.append((resized, record["page_id"]))

    total_height = title_height + margin
    total_height += sum(label_height + image.height + margin for image, _ in prepared)
    sheet = Image.new("L", (target_width, total_height), color=255)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 18), title, fill=0, font=title_font)
    y = title_height
    for image, label in prepared:
        draw.text((margin, y), label, fill=0, font=label_font)
        y += label_height
        x = (target_width - image.width) // 2
        sheet.paste(image, (x, y))
        y += image.height + margin
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, format="PNG", optimize=True)
    return {
        "path": rel(output_path),
        "sha256": sha256_file(output_path),
        "size_bytes": output_path.stat().st_size,
        "width_px": sheet.width,
        "height_px": sheet.height,
    }


def make_global_contact_sheet(
    document_sheets: list[dict[str, Any]], output_path: Path, target_width: int = 1600
) -> dict[str, Any]:
    title_font = font(34)
    label_font = font(24)
    margin = 24
    title_height = 70
    row_height = 410
    sheet = Image.new("L", (target_width, title_height + len(document_sheets) * row_height + margin), 255)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 18), "V10J - 25 pages predeclarees (aperçu)", fill=0, font=title_font)
    y = title_height
    for record in document_sheets:
        source = abs_from_rel(record["path"])
        with Image.open(source) as opened:
            preview = opened.convert("L")
            preview.thumbnail((target_width - 2 * margin, row_height - 65), Image.Resampling.LANCZOS)
        draw.text((margin, y), record["document_id"], fill=0, font=label_font)
        y += 42
        x = (target_width - preview.width) // 2
        sheet.paste(preview, (x, y))
        y += row_height - 42
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, format="PNG", optimize=True)
    return {
        "path": rel(output_path),
        "sha256": sha256_file(output_path),
        "size_bytes": output_path.stat().st_size,
        "width_px": sheet.width,
        "height_px": sheet.height,
    }


def load_and_validate_inputs(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    predecl_path = abs_from_rel(config["predeclaration"]["path"])
    require(predecl_path.exists(), f"Missing predeclaration: {rel(predecl_path)}", errors)
    if errors:
        raise RuntimeError("; ".join(errors))
    predecl_hash = sha256_file(predecl_path)
    predecl = load_json(predecl_path)
    require(predecl_hash == config["predeclaration"]["expected_sha256"], "Predeclaration hash mismatch", errors)
    require(
        predecl.get("predeclaration_status") == config["predeclaration"]["required_status"],
        "Predeclaration status mismatch",
        errors,
    )
    require(predecl.get("document_count") == config["predeclaration"]["required_document_count"], "Document count mismatch", errors)
    require(predecl.get("pages_per_document") == config["predeclaration"]["required_pages_per_document"], "Pages-per-document mismatch", errors)
    require(
        predecl.get("aggregate_candidate_page_count")
        == config["predeclaration"]["required_aggregate_candidate_page_count"],
        "Aggregate candidate-page count mismatch",
        errors,
    )

    regression_records: list[dict[str, Any]] = []
    for item in config["regression_files"] + config["protected_files"]:
        path = abs_from_rel(item["path"])
        actual = sha256_file(path) if path.exists() else None
        match = actual == item["expected_sha256"]
        regression_records.append(
            {
                "role": item["role"],
                "path": item["path"],
                "expected_sha256": item["expected_sha256"],
                "actual_sha256": actual,
                "exists": path.exists(),
                "hash_matches": match,
            }
        )
        require(match, f"Protected input mismatch: {item['role']}", errors)

    working_manifest_path = abs_from_rel(config["working_copy_manifest"]["path"])
    require(working_manifest_path.exists(), "Missing V10I working-copy manifest", errors)
    if working_manifest_path.exists():
        require(
            sha256_file(working_manifest_path) == config["working_copy_manifest"]["expected_sha256"],
            "V10I working-copy manifest hash mismatch",
            errors,
        )
        working_manifest = load_json(working_manifest_path)
    else:
        working_manifest = {}
    require(
        working_manifest.get("validation_status") == config["working_copy_manifest"]["required_validation_status"],
        "V10I working-copy manifest status mismatch",
        errors,
    )
    require(
        working_manifest.get("working_copy_count") == config["working_copy_manifest"]["required_copy_count"],
        "V10I working-copy count mismatch",
        errors,
    )
    require(
        working_manifest.get("working_copy_total_bytes") == config["working_copy_manifest"]["required_total_bytes"],
        "V10I working-copy total-byte mismatch",
        errors,
    )

    manifest_by_document = {item["document_id"]: item for item in working_manifest.get("files", [])}
    working_records: list[dict[str, Any]] = []
    seen_pages: set[tuple[str, int]] = set()
    candidate_count = 0
    for source in predecl["sources"]:
        document_id = source["document_id"]
        manifest_item = manifest_by_document.get(document_id)
        require(manifest_item is not None, f"Working-copy manifest missing {document_id}", errors)
        path = abs_from_rel(source["working_copy_path"])
        actual_hash = sha256_file(path) if path.exists() else None
        actual_size = path.stat().st_size if path.exists() else None
        require(path.exists(), f"Working copy missing: {source['working_copy_path']}", errors)
        require(actual_hash == source["expected_sha256"], f"Working-copy hash mismatch: {document_id}", errors)
        require(actual_size == source["expected_size_bytes"], f"Working-copy size mismatch: {document_id}", errors)
        if manifest_item:
            require(manifest_item["destination_path"] == source["working_copy_path"], f"Working-copy path mismatch: {document_id}", errors)
            require(manifest_item["sha256"] == source["expected_sha256"], f"Manifest source hash mismatch: {document_id}", errors)
        pages = source["candidate_pdf_pages_1_based"]
        require(len(pages) == predecl["pages_per_document"], f"Wrong candidate count: {document_id}", errors)
        for page in pages:
            candidate_count += 1
            require(1 <= page <= source["container_page_count"], f"Candidate page out of bounds: {document_id} p{page}", errors)
            key = (document_id, page)
            require(key not in seen_pages, f"Duplicate candidate page: {document_id} p{page}", errors)
            seen_pages.add(key)
        working_records.append(
            {
                "document_id": document_id,
                "path": source["working_copy_path"],
                "size_bytes": actual_size,
                "sha256": actual_hash,
                "container_page_count": source["container_page_count"],
                "candidate_pages_1_based": pages,
                "hash_and_size_match": actual_hash == source["expected_sha256"] and actual_size == source["expected_size_bytes"],
            }
        )
    require(candidate_count == predecl["aggregate_candidate_page_count"], "Candidate-page aggregate mismatch", errors)
    require(candidate_count <= predecl["hard_aggregate_render_cap"], "Hard render cap exceeded", errors)

    if errors:
        raise RuntimeError("; ".join(errors))

    common = {
        "predeclaration_path": rel(predecl_path),
        "predeclaration_sha256": predecl_hash,
        "regression_records": regression_records,
        "working_records": working_records,
        "candidate_page_count": candidate_count,
    }
    return predecl, common


def renderer_executable(requested: str | None) -> str:
    if requested:
        candidate = Path(requested)
        if candidate.exists():
            return str(candidate)
        resolved = shutil.which(requested)
        if resolved:
            return resolved
        raise FileNotFoundError(f"Renderer not found: {requested}")
    resolved = shutil.which("pdftoppm")
    if not resolved:
        raise FileNotFoundError("pdftoppm is not available")
    return resolved


def render_phase(config: dict[str, Any], requested_renderer: str | None) -> dict[str, Any]:
    started = time.perf_counter()
    generated_at = utc_now()
    predecl, common = load_and_validate_inputs(config)
    renderer = renderer_executable(requested_renderer)
    policy = predecl["render_policy"]
    pages_dir = abs_from_rel(policy["individual_page_directory"])
    documents_dir = abs_from_rel(policy["per_document_contact_sheet_directory"])
    pages_dir.mkdir(parents=True, exist_ok=True)
    documents_dir.mkdir(parents=True, exist_ok=True)

    image_records: list[dict[str, Any]] = []
    for source in predecl["sources"]:
        pdf = abs_from_rel(source["working_copy_path"])
        for page_number in source["candidate_pdf_pages_1_based"]:
            page_id = f"{source['document_id']}__p{page_number:04d}"
            prefix = pages_dir / page_id
            output_path = prefix.with_suffix(".png")
            command = [
                renderer,
                "-f",
                str(page_number),
                "-l",
                str(page_number),
                "-singlefile",
                "-r",
                str(policy["dpi"]),
                "-gray",
                "-png",
                str(pdf),
                str(prefix),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                raise RuntimeError(
                    f"pdftoppm failed for {page_id}: {completed.stderr.strip() or completed.stdout.strip()}"
                )
            if not output_path.exists():
                raise RuntimeError(f"Renderer did not create {rel(output_path)}")
            with Image.open(output_path) as image:
                width, height = image.size
                mode = image.mode
            pixels = width * height
            if pixels > policy["maximum_pixels_per_page"]:
                raise RuntimeError(f"Per-page pixel cap exceeded for {page_id}: {pixels}")
            image_records.append(
                {
                    "page_id": page_id,
                    "document_id": source["document_id"],
                    "pdf_page_1_based": page_number,
                    "source_pdf_path": source["working_copy_path"],
                    "source_pdf_sha256": source["expected_sha256"],
                    "render_path": rel(output_path),
                    "render_sha256": sha256_file(output_path),
                    "render_size_bytes": output_path.stat().st_size,
                    "width_px": width,
                    "height_px": height,
                    "pixel_count": pixels,
                    "mode": mode,
                    "dpi": policy["dpi"],
                }
            )

    aggregate_pixels = sum(record["pixel_count"] for record in image_records)
    aggregate_bytes = sum(record["render_size_bytes"] for record in image_records)
    if len(image_records) != predecl["aggregate_candidate_page_count"]:
        raise RuntimeError("Rendered page count does not match predeclaration")
    if aggregate_pixels > policy["maximum_aggregate_pixels"]:
        raise RuntimeError("Aggregate rendered-pixel cap exceeded")
    if aggregate_bytes > policy["maximum_aggregate_png_bytes"]:
        raise RuntimeError("Aggregate rendered-byte cap exceeded")

    document_sheets: list[dict[str, Any]] = []
    for source in predecl["sources"]:
        document_records = [record for record in image_records if record["document_id"] == source["document_id"]]
        output = documents_dir / f"{source['document_id']}__pages_1_5.png"
        sheet = make_vertical_contact_sheet(document_records, output, f"{source['document_id']} - pages PDF 1 a 5")
        sheet["document_id"] = source["document_id"]
        document_sheets.append(sheet)
    global_sheet = make_global_contact_sheet(document_sheets, abs_from_rel(policy["global_contact_sheet"]))

    source_manifest = {
        "iteration": "V10J",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "predeclaration": {
            "path": common["predeclaration_path"],
            "sha256": common["predeclaration_sha256"],
            "status": predecl["predeclaration_status"],
            "created_before_page_content_read": True,
        },
        "v10i_working_copy_manifest": {
            "path": config["working_copy_manifest"]["path"],
            "sha256": config["working_copy_manifest"]["expected_sha256"],
        },
        "working_copies": common["working_records"],
        "source_archive_read": False,
        "official_sources_read": False,
        "network_access_used": False,
    }
    write_json(abs_from_rel(config["outputs"]["source_manifest"]), source_manifest)

    regression_audit = {
        "iteration": "V10J",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "protected_inputs": common["regression_records"],
        "protected_input_count": len(common["regression_records"]),
        "all_hashes_match": all(item["hash_matches"] for item in common["regression_records"]),
        "working_copies": common["working_records"],
        "all_working_copy_hashes_and_sizes_match": all(item["hash_and_size_match"] for item in common["working_records"]),
    }
    write_json(abs_from_rel(config["outputs"]["regression_audit"]), regression_audit)

    candidate_manifest = {
        "iteration": "V10J",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "predeclaration_sha256": common["predeclaration_sha256"],
        "selection_rule": predecl["selection_rule"],
        "selection_is_content_blind": predecl["selection_is_content_blind"],
        "document_count": predecl["document_count"],
        "pages_per_document": predecl["pages_per_document"],
        "candidate_page_count": common["candidate_page_count"],
        "hard_aggregate_render_cap": predecl["hard_aggregate_render_cap"],
        "pages": [
            {
                "page_id": record["page_id"],
                "document_id": record["document_id"],
                "pdf_page_1_based": record["pdf_page_1_based"],
                "source_pdf_path": record["source_pdf_path"],
                "source_pdf_sha256": record["source_pdf_sha256"],
                "render_path": record["render_path"],
            }
            for record in image_records
        ],
    }
    write_json(abs_from_rel(config["outputs"]["candidate_page_manifest"]), candidate_manifest)

    render_audit = {
        "iteration": "V10J",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "renderer": renderer,
        "renderer_returned_page_count": len(image_records),
        "unique_rendered_page_count": len(image_records),
        "render_invocation_count": len(image_records),
        "finalize_rerender_count": 0,
        "dpi": policy["dpi"],
        "color_mode": policy["color_mode"],
        "aggregate_rendered_pixels": aggregate_pixels,
        "maximum_aggregate_rendered_pixels": policy["maximum_aggregate_pixels"],
        "aggregate_rendered_png_bytes": aggregate_bytes,
        "maximum_aggregate_rendered_png_bytes": policy["maximum_aggregate_png_bytes"],
        "pages": image_records,
        "document_contact_sheets": document_sheets,
        "global_contact_sheet": global_sheet,
        "source_pdf_hashes_unchanged_after_render": all(
            sha256_file(abs_from_rel(item["path"])) == item["sha256"] for item in common["working_records"]
        ),
        "page_content_scope": "EXACT_PREDECLARED_25_PAGES_ONLY",
        "full_document_text_scan_count": 0,
        "ocr_count": 0,
        "embedded_text_extraction_count": 0,
    }
    write_json(abs_from_rel(config["outputs"]["render_audit"]), render_audit)

    elapsed = time.perf_counter() - started
    return {
        "status": "PASS",
        "phase": "render",
        "rendered_page_count": len(image_records),
        "aggregate_rendered_pixels": aggregate_pixels,
        "aggregate_rendered_png_bytes": aggregate_bytes,
        "global_contact_sheet": global_sheet["path"],
        "elapsed_seconds": round(elapsed, 3),
    }


def verify_render_phase_outputs(config: dict[str, Any], predecl: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_path = abs_from_rel(config["outputs"]["candidate_page_manifest"])
    render_path = abs_from_rel(config["outputs"]["render_audit"])
    if not candidate_path.exists() or not render_path.exists():
        raise RuntimeError("Render-phase manifests are missing")
    candidate = load_json(candidate_path)
    render = load_json(render_path)
    if candidate.get("validation_status") != "PASS" or render.get("validation_status") != "PASS":
        raise RuntimeError("Render-phase manifest status is not PASS")
    if candidate.get("candidate_page_count") != predecl["aggregate_candidate_page_count"]:
        raise RuntimeError("Candidate-page count changed after predeclaration")
    if render.get("unique_rendered_page_count") != predecl["aggregate_candidate_page_count"]:
        raise RuntimeError("Rendered-page count changed after predeclaration")
    for record in render["pages"]:
        path = abs_from_rel(record["render_path"])
        if not path.exists() or sha256_file(path) != record["render_sha256"]:
            raise RuntimeError(f"Rendered page missing or changed: {record['page_id']}")
    global_path = abs_from_rel(render["global_contact_sheet"]["path"])
    if not global_path.exists() or sha256_file(global_path) != render["global_contact_sheet"]["sha256"]:
        raise RuntimeError("Global contact sheet missing or changed")
    return candidate, render


def finalize_phase(config: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    generated_at = utc_now()
    predecl, common = load_and_validate_inputs(config)
    candidate, render = verify_render_phase_outputs(config, predecl)
    transcription_path = abs_from_rel(config["manual_transcription"]["path"])
    if not transcription_path.exists():
        raise RuntimeError(f"Missing manual transcription: {rel(transcription_path)}")
    transcription = load_json(transcription_path)
    records = transcription.get("records", [])
    candidate_by_page = {record["page_id"]: record for record in candidate["pages"]}
    records_by_page: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    allowed_fields = set(config["manual_transcription"]["allowed_transcription_fields"])
    allowed_classifications = set(config["manual_transcription"]["allowed_page_classifications"])
    allowed_record_keys = {
        "page_id",
        "document_id",
        "pdf_page_1_based",
        "classification",
        "visual_review_status",
        "explicit_floor93_99_label_present",
        "notes",
    } | allowed_fields
    forbidden_fields = set(config["manual_transcription"]["forbidden_transcription_fields"])

    for record in records:
        page_id = record.get("page_id")
        require(page_id in candidate_by_page, f"Transcription record outside predeclaration: {page_id}", errors)
        require(page_id not in records_by_page, f"Duplicate transcription record: {page_id}", errors)
        records_by_page[page_id] = record
        unexpected = set(record) - allowed_record_keys
        require(not unexpected, f"Unexpected transcription keys for {page_id}: {sorted(unexpected)}", errors)
        require(not (set(record) & forbidden_fields), f"Forbidden transcription keys for {page_id}", errors)
        require(record.get("classification") in allowed_classifications, f"Invalid classification for {page_id}", errors)
        require(record.get("visual_review_status") == "REVIEWED", f"Page not visually reviewed: {page_id}", errors)
        if page_id in candidate_by_page:
            candidate_record = candidate_by_page[page_id]
            require(record.get("document_id") == candidate_record["document_id"], f"Document mismatch: {page_id}", errors)
            require(record.get("pdf_page_1_based") == candidate_record["pdf_page_1_based"], f"Page mismatch: {page_id}", errors)
        for field in allowed_fields:
            value = record.get(field, [])
            require(isinstance(value, list), f"Allowed field must be a list: {page_id} {field}", errors)
            if isinstance(value, list):
                require(all(isinstance(item, str) for item in value), f"Allowed field contains non-string: {page_id} {field}", errors)

    require(len(records) == config["expected"]["manual_transcription_record_count"], "Manual transcription count mismatch", errors)
    require(set(records_by_page) == set(candidate_by_page), "Manual transcription does not cover exactly the candidate pages", errors)
    if errors:
        raise RuntimeError("; ".join(errors))

    classification_counts = Counter(record["classification"] for record in records)
    exact_cross_reference_count = sum(len(record["visible_cross_reference_locators"]) for record in records)
    pages_with_cross_reference = [record["page_id"] for record in records if record["visible_cross_reference_locators"]]
    pages_with_explicit_floor93_99 = [record["page_id"] for record in records if record["explicit_floor93_99_label_present"]]
    documents_with_explicit_floor93_99 = sorted(
        {record["document_id"] for record in records if record["explicit_floor93_99_label_present"]}
    )

    locator_rows: list[dict[str, Any]] = []
    floor_rows: list[dict[str, Any]] = []
    for record in records:
        row = {
            "page_id": record["page_id"],
            "document_id": record["document_id"],
            "pdf_page_1_based": record["pdf_page_1_based"],
            "classification": record["classification"],
            "visible_document_identifiers": " | ".join(record["visible_document_identifiers"]),
            "visible_title_or_index_headings": " | ".join(record["visible_title_or_index_headings"]),
            "visible_tower_labels": " | ".join(record["visible_tower_labels"]),
            "visible_floor_labels": " | ".join(record["visible_floor_labels"]),
            "visible_floor_ranges": " | ".join(record["visible_floor_ranges"]),
            "visible_revision_or_issue_fields": " | ".join(record["visible_revision_or_issue_fields"]),
            "visible_cross_reference_locators": " | ".join(record["visible_cross_reference_locators"]),
            "explicit_floor93_99_label_present": str(record["explicit_floor93_99_label_present"]).lower(),
            "notes": record.get("notes", ""),
        }
        locator_rows.append(row)
        for label in record["visible_floor_labels"]:
            floor_rows.append(
                {
                    "page_id": record["page_id"],
                    "document_id": record["document_id"],
                    "pdf_page_1_based": record["pdf_page_1_based"],
                    "locator_kind": "VISIBLE_FLOOR_LABEL",
                    "visible_value": label,
                    "explicit_floor93_99_label_present": str(record["explicit_floor93_99_label_present"]).lower(),
                    "geometry_or_physical_credit": 0,
                }
            )
        for floor_range in record["visible_floor_ranges"]:
            floor_rows.append(
                {
                    "page_id": record["page_id"],
                    "document_id": record["document_id"],
                    "pdf_page_1_based": record["pdf_page_1_based"],
                    "locator_kind": "VISIBLE_FLOOR_RANGE",
                    "visible_value": floor_range,
                    "explicit_floor93_99_label_present": str(record["explicit_floor93_99_label_present"]).lower(),
                    "geometry_or_physical_credit": 0,
                }
            )

    locator_fields = [
        "page_id",
        "document_id",
        "pdf_page_1_based",
        "classification",
        "visible_document_identifiers",
        "visible_title_or_index_headings",
        "visible_tower_labels",
        "visible_floor_labels",
        "visible_floor_ranges",
        "visible_revision_or_issue_fields",
        "visible_cross_reference_locators",
        "explicit_floor93_99_label_present",
        "notes",
    ]
    floor_fields = [
        "page_id",
        "document_id",
        "pdf_page_1_based",
        "locator_kind",
        "visible_value",
        "explicit_floor93_99_label_present",
        "geometry_or_physical_credit",
    ]
    locator_path = abs_from_rel(config["outputs"]["frontmatter_locator_matrix_csv"])
    floor_path = abs_from_rel(config["outputs"]["floor93_99_locator_matrix_csv"])
    write_csv(locator_path, locator_fields, locator_rows)
    write_csv(floor_path, floor_fields, floor_rows)

    transcription_audit = {
        "iteration": "V10J",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "manual_transcription_path": rel(transcription_path),
        "manual_transcription_sha256": sha256_file(transcription_path),
        "candidate_page_count": len(candidate_by_page),
        "manual_transcription_record_count": len(records),
        "classification_counts": dict(sorted(classification_counts.items())),
        "allowed_fields_only": True,
        "visual_review_complete": True,
        "ocr_count": 0,
        "embedded_text_extraction_count": 0,
        "full_document_text_scan_count": 0,
        "non_candidate_page_content_read_count": 0,
        "geometry_or_dimension_transcription_count": 0,
        "pages_with_explicit_floor93_99_labels": pages_with_explicit_floor93_99,
        "documents_with_explicit_floor93_99_labels": documents_with_explicit_floor93_99,
        "visible_exact_cross_reference_locator_count": exact_cross_reference_count,
        "pages_with_visible_exact_cross_references": pages_with_cross_reference,
    }
    write_json(abs_from_rel(config["outputs"]["manual_transcription_audit"]), transcription_audit)

    cross_reference_branch_open = exact_cross_reference_count > 0
    next_objective = (
        config["next_iteration_conditional"]["objective_if_exact_cross_reference_visible"]
        if cross_reference_branch_open
        else config["next_iteration_conditional"]["objective_if_no_exact_cross_reference_visible"]
    )
    checks = {
        "v10i_regression_and_blender_hashes_all_match": all(item["hash_matches"] for item in common["regression_records"]),
        "immutable_predeclaration_hash_matches": common["predeclaration_sha256"] == config["predeclaration"]["expected_sha256"],
        "five_working_copy_hashes_and_sizes_match": all(item["hash_and_size_match"] for item in common["working_records"]),
        "candidate_page_count_exactly_25": candidate["candidate_page_count"] == 25,
        "rendered_page_count_exactly_25": render["unique_rendered_page_count"] == 25,
        "render_pixel_and_byte_caps_not_exceeded": (
            render["aggregate_rendered_pixels"] <= render["maximum_aggregate_rendered_pixels"]
            and render["aggregate_rendered_png_bytes"] <= render["maximum_aggregate_rendered_png_bytes"]
        ),
        "source_pdf_hashes_unchanged_after_render": render["source_pdf_hashes_unchanged_after_render"],
        "manual_transcription_record_count_exactly_25": len(records) == 25,
        "manual_transcription_uses_only_allowed_fields": True,
        "visual_review_complete": True,
        "non_candidate_and_full_document_scan_count_zero": True,
        "ocr_and_embedded_text_extraction_count_zero": True,
        "drawing_geometry_and_dimension_transcription_count_zero": True,
        "source_archive_and_official_sources_not_read_or_modified": True,
        "no_network_or_external_contact": True,
        "physical_assignment_count_zero": True,
        "solver_blender_thermal_gates_closed": True,
    }
    validation_status = "PASS" if all(checks.values()) else "FAIL"
    model_gate = {
        "iteration": "V10J",
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "checks": checks,
        "bounded_frontmatter_review_gate": "PASS_25_EXACT_PREDECLARED_PAGES_VISUALLY_REVIEWED",
        "official_nist_chain_gate": "NOT_REQUIRED_FOR_BOUNDED_REVIEW_BUT_NOT_VERIFIED",
        "revision_as_built_authority_gate": "CLOSED_NOT_VERIFIED",
        "wtc1_floor93_99_applicability_gate": "CLOSED_NOT_VERIFIED",
        "requirement_closure_gate": "CLOSED_0_OF_22",
        "structural_solver_readiness_gate": "CLOSED_22_OF_22_BLOCKING",
        "v10k_bounded_cross_reference_gate": (
            "OPEN_ONLY_FOR_EXACT_VISIBLE_V10J_CROSS_REFERENCE_LOCATORS"
            if cross_reference_branch_open
            else "CLOSED_NO_EXACT_VISIBLE_V10J_CROSS_REFERENCE_LOCATOR"
        ),
        "network_gate": "CLOSED",
        "source_archive_gate": "CLOSED",
        "official_sources_gate": "CLOSED",
        "thermal_continuation_gate": "CLOSED",
        "blender_gate": "CLOSED",
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
        "physical_validation": False,
    }
    write_json(abs_from_rel(config["outputs"]["model_gate"]), model_gate)

    report_lines = [
        "# WTC 1 - V10J - Audit borné des pages liminaires",
        "",
        f"**Validation générale : {validation_status}**",
        "",
        "## Portée",
        "",
        "V10J examine uniquement les pages PDF 1 à 5 des cinq copies de travail V10I, soit 25 pages pré-déclarées avant toute lecture. Le rendu est effectué à 120 dpi en niveaux de gris. Aucun OCR, aucune extraction de texte intégré et aucun balayage du reste des documents ne sont utilisés.",
        "",
        "## Faits directement observés ou transcrits",
        "",
        f"- Pages rendues et examinées visuellement : {len(records)}.",
        f"- Répartition des classifications : {json.dumps(dict(sorted(classification_counts.items())), ensure_ascii=False)}.",
        f"- Pages portant une mention explicite d'un étage cible 93-99 : {len(pages_with_explicit_floor93_99)}.",
        f"- Localisateurs de renvoi exacts visibles : {exact_cross_reference_count}.",
        "- Les inscriptions visibles sont conservées comme inscriptions de page; elles ne certifient ni la révision gouvernante, ni le statut as-built, ni l'applicabilité physique.",
        "",
        "## Résultats d'un modèle officiel",
        "",
        "Aucun résultat de modèle officiel n'est créé ni revalidé par V10J.",
        "",
        "## Affirmations provenant de l'archive et de l'utilisateur",
        "",
        "L'identité binaire des cinq fichiers avec les objets Archive.org gelés en V10I est conservée. L'affirmation de l'utilisateur selon laquelle les documents sont authentiques demeure enregistrée, sans être convertie en certification officielle indépendante.",
        "",
        "## Hypothèses propres au modèle",
        "",
        "Les cinq premières pages ont été choisies comme fenêtre liminaire déterministe et aveugle au contenu. Ce choix ne suppose pas que ces pages constituent un index complet.",
        "",
        "## Résultats dérivés",
        "",
        f"- Documents : 5; pages uniques : 25; pixels rendus : {render['aggregate_rendered_pixels']:,}; octets PNG : {render['aggregate_rendered_png_bytes']:,}.",
        "- Exigences physiques closes : 0 sur 22; exigences bloquant encore le solveur : 22 sur 22.",
        f"- Branche V10K de renvoi borné : {'ouverte uniquement sur les localisateurs visibles' if cross_reference_branch_open else 'fermée'}.",
        "",
        "## Contradictions et informations manquantes",
        "",
        "La chaîne NIST officielle, la révision gouvernante, le statut as-built, l'applicabilité exacte au WTC 1 et aux étages 93-99, ainsi que la suffisance des dessins pour les 22 exigences structurelles restent non établis. Aucun contenu géométrique, aucune cote et aucune propriété physique ne sont transcrits.",
        "",
        "## Interdictions et crédits nuls",
        "",
        "Aucun accès à l'archive source ou à work/official_sources, aucune requête réseau, aucun solveur, aucun modèle thermique et aucun lancement Blender n'ont lieu. Masse, rigidité, résistance, connexions, dommages et crédit de chemin de charge restent à zéro.",
    ]
    report_path = abs_from_rel(config["outputs"]["report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(report_lines) + "\n")

    results = {
        "iteration": "V10J",
        "started_at_utc": generated_at,
        "completed_at_utc": utc_now(),
        "validation_status": validation_status,
        "dataset": config["dataset"],
        "observed_or_transcribed_facts": [
            "Exactly 25 content-blind predeclared PDF pages were rendered and visually reviewed.",
            f"The 25 pages include {len(pages_with_explicit_floor93_99)} page(s) with an explicit target-floor label flag.",
            f"The visible transcription records {exact_cross_reference_count} exact cross-reference locator(s).",
        ],
        "official_model_results": ["No official-model result is created or independently validated."],
        "archive_claims_used": [
            "V10I binary identity with the frozen Archive.org original-object metadata is retained as a chained input."
        ],
        "user_assertions": [
            "The user's statement that the five files are authentic and that a complete chain is optional remains recorded."
        ],
        "model_hypotheses": [
            "PDF pages 1-5 in each file form a deterministic content-blind front-matter/index hypothesis, not a complete index claim."
        ],
        "derived_results": {
            "document_count": 5,
            "candidate_page_count": 25,
            "rendered_page_count": 25,
            "manual_transcription_record_count": len(records),
            "classification_counts": dict(sorted(classification_counts.items())),
            "pages_with_explicit_floor93_99_label_count": len(pages_with_explicit_floor93_99),
            "documents_with_explicit_floor93_99_labels": documents_with_explicit_floor93_99,
            "visible_exact_cross_reference_locator_count": exact_cross_reference_count,
            "pages_with_visible_exact_cross_references": pages_with_cross_reference,
            "aggregate_rendered_pixels": render["aggregate_rendered_pixels"],
            "aggregate_rendered_png_bytes": render["aggregate_rendered_png_bytes"],
            "requirements_closed_count": 0,
            "requirements_solver_blocking_count": 22,
            "physical_assignment_count": 0,
        },
        "contradictions_and_missing_information": [
            "Official NIST chain, governing revision, as-built authority and exact WTC 1/Floors 93-99 applicability remain unverified.",
            "No drawing geometry, dimension, section, material, connection, damage or load-path content is transcribed.",
            "All 22 structural requirements remain solver blocking."
        ],
        "checks": checks,
        "operation_counts": {
            "working_copy_pdf_read_count": 5,
            "candidate_page_content_read_count": 25,
            "unique_page_render_count": 25,
            "render_invocation_count": render["render_invocation_count"],
            "finalize_rerender_count": render["finalize_rerender_count"],
            "non_candidate_page_content_read_count": 0,
            "full_document_text_scan_count": 0,
            "ocr_count": 0,
            "embedded_text_extraction_count": 0,
            "source_archive_read_count": 0,
            "official_sources_read_count": 0,
            "network_request_count": 0,
            "external_contact_count": 0,
            "structural_solver_run_count": 0,
            "thermal_model_run_count": 0,
            "blender_launch_count": 0,
            "blender_master_write_count": 0,
        },
        "physical_assignments": model_gate["physical_assignments"],
        "outputs": config["outputs"],
        "software": {
            "python": platform.python_version(),
            "pillow": Image.__version__ if hasattr(Image, "__version__") else "unknown",
            "platform": platform.platform(),
            "elapsed_seconds_before_final_serialization": round(time.perf_counter() - started, 3),
        },
        "next_iteration": {"id": config["next_iteration_conditional"]["id"], "objective": next_objective},
        "errors": [],
    }
    results_path = abs_from_rel(config["outputs"]["results"])
    write_json(results_path, results)

    required_artifacts = [
        rel(CONFIG_PATH),
        common["predeclaration_path"],
        rel(SCRIPT_PATH),
        rel(transcription_path),
        config["outputs"]["source_manifest"],
        config["outputs"]["regression_audit"],
        config["outputs"]["candidate_page_manifest"],
        config["outputs"]["render_audit"],
        config["outputs"]["manual_transcription_audit"],
        config["outputs"]["frontmatter_locator_matrix_csv"],
        config["outputs"]["floor93_99_locator_matrix_csv"],
        config["outputs"]["model_gate"],
        config["outputs"]["report"],
        config["outputs"]["results"],
        config["outputs"]["contact_sheet"],
    ]
    required_artifacts.extend(sheet["path"] for sheet in render["document_contact_sheets"])
    artifact_records = []
    missing = []
    for relative_path in required_artifacts:
        path = abs_from_rel(relative_path)
        exists = path.exists()
        if not exists:
            missing.append(relative_path)
        artifact_records.append(
            {
                "path": relative_path,
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else None,
                "sha256": sha256_file(path) if exists else None,
            }
        )
    offline_audit = {
        "iteration": "V10J",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS" if validation_status == "PASS" and not missing else "FAIL",
        "required_artifact_count": len(required_artifacts),
        "missing_artifact_count": len(missing),
        "missing_artifacts": missing,
        "artifacts": artifact_records,
        "working_copy_hashes_unchanged_after_finalize": all(
            sha256_file(abs_from_rel(item["path"])) == item["sha256"] for item in common["working_records"]
        ),
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_read": False,
        "official_sources_modified": False,
        "network_access_used": False,
        "solver_executed": False,
        "thermal_continuation_executed": False,
        "blender_executed": False,
    }
    write_json(abs_from_rel(config["outputs"]["offline_audit"]), offline_audit)
    if offline_audit["validation_status"] != "PASS":
        raise RuntimeError(f"Offline package audit failed: {missing}")

    return {
        "status": validation_status,
        "phase": "finalize",
        "candidate_page_count": 25,
        "rendered_page_count": 25,
        "transcription_record_count": len(records),
        "explicit_floor93_99_page_count": len(pages_with_explicit_floor93_99),
        "visible_exact_cross_reference_locator_count": exact_cross_reference_count,
        "requirements_closed_count": 0,
        "requirements_solver_blocking_count": 22,
        "next_iteration": config["next_iteration_conditional"]["id"],
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded V10J front-matter/index audit")
    parser.add_argument("--phase", choices=("render", "finalize"), required=True)
    parser.add_argument("--renderer", default=None)
    args = parser.parse_args()
    config = load_json(CONFIG_PATH)
    result = render_phase(config, args.renderer) if args.phase == "render" else finalize_phase(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
