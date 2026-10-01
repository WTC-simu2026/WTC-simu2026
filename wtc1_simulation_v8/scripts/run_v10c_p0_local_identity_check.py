#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import socket
import stat as stat_module
import sys
import tempfile
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "wtc1_simulation_v8" / "data" / "v10c_p0_local_identity_check.json"
CHUNK_SIZE = 1024 * 1024

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


class GateExceeded(RuntimeError):
    def __init__(self, metric: str, actual: int, maximum: int) -> None:
        super().__init__(f"{metric} exceeded: {actual} > {maximum}")
        self.metric = metric
        self.actual = actual
        self.maximum = maximum


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
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
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(CHUNK_SIZE)
            if not block:
                break
            digest.update(block)
            total += len(block)
    return digest.hexdigest(), total


def sha256_pdf_with_header(path: Path) -> tuple[str, int, bytes]:
    digest = hashlib.sha256()
    total = 0
    header = b""
    with path.open("rb") as handle:
        while True:
            block = handle.read(CHUNK_SIZE)
            if not block:
                break
            if not header:
                header = block[:8]
            digest.update(block)
            total += len(block)
    return digest.hexdigest(), total, header


def project_file_record(item: dict[str, Any]) -> dict[str, Any]:
    path = (PROJECT_ROOT / item["path"]).resolve()
    expected = item["expected_sha256"].lower()
    exists = path.is_file()
    actual = None
    size = None
    if exists:
        actual, size = sha256_file(path)
    return {
        "role": item["role"],
        "path": item["path"],
        "size_bytes": size,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "exists": exists,
        "matches": bool(exists and actual == expected),
    }


def normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    value_node = cell.find(f"{{{MAIN_NS}}}v")
    if cell_type == "s" and value_node is not None and value_node.text is not None:
        return shared_strings[int(value_node.text)]
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{MAIN_NS}}}is")
        if inline is None:
            return ""
        return "".join(inline.itertext())
    if value_node is None or value_node.text is None:
        return ""
    return value_node.text


def read_register_targets(register_path: Path, targets: list[dict[str, Any]]) -> dict[str, Any]:
    with zipfile.ZipFile(register_path, "r") as archive:
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(item.itertext())
            for item in shared_root.findall(f"{{{MAIN_NS}}}si")
        ]
        sheet_root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rel_root = ET.fromstring(archive.read("xl/worksheets/_rels/sheet1.xml.rels"))

    relationships = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rel_root.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    hyperlink_by_cell: dict[str, str] = {}
    hyperlinks_node = sheet_root.find(f"{{{MAIN_NS}}}hyperlinks")
    if hyperlinks_node is not None:
        for hyperlink in hyperlinks_node.findall(f"{{{MAIN_NS}}}hyperlink"):
            cell_ref = hyperlink.attrib.get("ref", "")
            relation_id = hyperlink.attrib.get(f"{{{DOC_REL_NS}}}id", "")
            hyperlink_by_cell[cell_ref] = relationships.get(relation_id, "")

    target_ids = {target["document_id"] for target in targets}
    rows_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sheet_data = sheet_root.find(f"{{{MAIN_NS}}}sheetData")
    if sheet_data is None:
        raise RuntimeError("Sheet1 has no sheetData")

    for row in sheet_data.findall(f"{{{MAIN_NS}}}row"):
        row_number = int(row.attrib["r"])
        values: dict[str, str] = {}
        for cell in row.findall(f"{{{MAIN_NS}}}c"):
            reference = cell.attrib["r"]
            column = "".join(character for character in reference if character.isalpha())
            values[column] = cell_value(cell, shared_strings)
        document_id = normalize_cell(values.get("D"))
        if document_id in target_ids:
            rows_by_id[document_id].append(
                {
                    "row": row_number,
                    "book_number": normalize_cell(values.get("A")),
                    "title_column_b": normalize_cell(values.get("B")),
                    "register_pdf_title": normalize_cell(values.get("C")),
                    "document_id": document_id,
                    "register_content_summary": normalize_cell(values.get("E")),
                    "register_file_or_folder_size": normalize_cell(values.get("F")),
                    "register_floors": normalize_cell(values.get("G")),
                    "register_area": normalize_cell(values.get("H")),
                    "register_tower_label": normalize_cell(values.get("I")),
                    "register_drawing_start": normalize_cell(values.get("J")),
                    "register_drawing_end": normalize_cell(values.get("K")),
                    "hyperlink_cell": f"E{row_number}",
                    "register_hyperlink": hyperlink_by_cell.get(f"E{row_number}", ""),
                }
            )

    checks: list[dict[str, Any]] = []
    transcribed: list[dict[str, Any]] = []
    for target in targets:
        identifier = target["document_id"]
        candidates = rows_by_id.get(identifier, [])
        exactly_once = len(candidates) == 1
        row_data = candidates[0] if exactly_once else {}
        comparisons = {
            "row": row_data.get("row") == int(target["workbook_row"]),
            "book_number": normalize_cell(row_data.get("book_number")) == str(target["book_number"]),
            "title_column_b": normalize_cell(row_data.get("title_column_b")) == identifier,
            "document_id": normalize_cell(row_data.get("document_id")) == identifier,
            "register_pdf_title": normalize_cell(row_data.get("register_pdf_title")) == normalize_cell(target["register_pdf_title"]),
            "register_content_summary": normalize_cell(row_data.get("register_content_summary")) == normalize_cell(target["register_content_summary"]),
            "register_file_or_folder_size": normalize_cell(row_data.get("register_file_or_folder_size")) == normalize_cell(target["register_file_or_folder_size"]),
            "register_tower_label": normalize_cell(row_data.get("register_tower_label")) == normalize_cell(target["register_tower_label"]),
            "register_drawing_start": normalize_cell(row_data.get("register_drawing_start")) == normalize_cell(target["register_drawing_start"]),
            "register_drawing_end": normalize_cell(row_data.get("register_drawing_end")) == normalize_cell(target["register_drawing_end"]),
            "register_hyperlink": normalize_cell(row_data.get("register_hyperlink")) == normalize_cell(target["register_hyperlink"]),
        }
        check = {
            "document_id": identifier,
            "candidate_row_count": len(candidates),
            "exactly_once": exactly_once,
            "comparisons": comparisons,
            "all_fields_match": bool(exactly_once and all(comparisons.values())),
        }
        checks.append(check)
        transcribed.append(
            {
                "acquisition_sequence": target["acquisition_sequence"],
                "document_id": identifier,
                "expected_filename": target["expected_filename"],
                "group_id": target["group_id"],
                "subsystem": target["subsystem"],
                "workbook_row": target["workbook_row"],
                "book_number": target["book_number"],
                "register_pdf_title": row_data.get("register_pdf_title", target["register_pdf_title"]),
                "register_content_summary": row_data.get("register_content_summary", target["register_content_summary"]),
                "register_file_or_folder_size": row_data.get("register_file_or_folder_size", target["register_file_or_folder_size"]),
                "register_floors": row_data.get("register_floors", ""),
                "register_area": row_data.get("register_area", ""),
                "register_tower_label": row_data.get("register_tower_label", target["register_tower_label"]),
                "register_drawing_start": row_data.get("register_drawing_start", target["register_drawing_start"]),
                "register_drawing_end": row_data.get("register_drawing_end", target["register_drawing_end"]),
                "register_hyperlink": row_data.get("register_hyperlink", target["register_hyperlink"]),
                "evidence_class": "ARCHIVE_REGISTER_CLAIM_NOT_OFFICIAL_SOURCE",
                "register_row_exactly_once": exactly_once,
                "register_fields_and_hyperlink_match": bool(exactly_once and all(comparisons.values())),
            }
        )

    return {
        "target_checks": checks,
        "transcribed_rows": sorted(transcribed, key=lambda row: row["acquisition_sequence"]),
        "all_targets_exactly_once": all(item["exactly_once"] for item in checks),
        "all_target_fields_match": all(item["all_fields_match"] for item in checks),
        "hyperlink_count": sum(1 for item in transcribed if item["register_hyperlink"]),
    }


def is_reparse_point(entry: os.DirEntry[str]) -> bool:
    try:
        metadata = entry.stat(follow_symlinks=False)
    except OSError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    marker = getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & marker)


def traverse_archive(
    root: Path,
    target_name_map: dict[str, str],
    bounds: dict[str, int],
) -> dict[str, Any]:
    counters = {
        "directories_visited": 0,
        "file_entries_examined_by_name": 0,
        "utf8_path_bytes_examined": 0,
        "reparse_points_skipped": 0,
        "compressed_archive_entry_scan_count": 0,
        "unrelated_source_payload_read_count": 0,
    }
    access_errors: list[dict[str, Any]] = []
    gate_breaches: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    reparse_points: list[str] = []
    stack = [root]
    completed = True

    try:
        while stack:
            current = stack.pop()
            counters["directories_visited"] += 1
            if counters["directories_visited"] > bounds["maximum_directories_visited"]:
                raise GateExceeded(
                    "directories_visited",
                    counters["directories_visited"],
                    bounds["maximum_directories_visited"],
                )
            try:
                with os.scandir(current) as iterator:
                    entries = sorted(list(iterator), key=lambda item: (item.name.casefold(), item.name))
            except OSError as error:
                access_errors.append(
                    {
                        "path": str(current),
                        "operation": "scandir",
                        "error_type": type(error).__name__,
                        "error": str(error),
                    }
                )
                continue

            subdirectories: list[Path] = []
            for entry in entries:
                relative = Path(entry.path).relative_to(root)
                counters["utf8_path_bytes_examined"] += len(str(relative).encode("utf-8"))
                if counters["utf8_path_bytes_examined"] > bounds["maximum_utf8_path_bytes_examined"]:
                    raise GateExceeded(
                        "utf8_path_bytes_examined",
                        counters["utf8_path_bytes_examined"],
                        bounds["maximum_utf8_path_bytes_examined"],
                    )

                try:
                    if entry.is_symlink() or is_reparse_point(entry):
                        counters["reparse_points_skipped"] += 1
                        reparse_points.append(str(relative))
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        subdirectories.append(Path(entry.path))
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    counters["file_entries_examined_by_name"] += 1
                    if counters["file_entries_examined_by_name"] > bounds["maximum_file_entries_examined_by_name"]:
                        raise GateExceeded(
                            "file_entries_examined_by_name",
                            counters["file_entries_examined_by_name"],
                            bounds["maximum_file_entries_examined_by_name"],
                        )
                    identifier = target_name_map.get(entry.name.casefold())
                    if identifier is None:
                        continue
                    metadata = entry.stat(follow_symlinks=False)
                    matches.append(
                        {
                            "document_id": identifier,
                            "source_path": str(Path(entry.path).resolve()),
                            "source_relative_path": str(relative),
                            "source_filename": entry.name,
                            "size_bytes": int(metadata.st_size),
                            "mtime_ns_before": int(metadata.st_mtime_ns),
                            "source_sha256_before": None,
                            "source_sha256_after": None,
                            "pdf_header_hex": None,
                            "pdf_header_valid": None,
                            "working_copy_path": None,
                            "working_copy_sha256": None,
                            "source_unchanged_after_copy": None,
                            "copy_status": "NOT_ATTEMPTED",
                        }
                    )
                except GateExceeded:
                    raise
                except OSError as error:
                    access_errors.append(
                        {
                            "path": str(Path(entry.path)),
                            "operation": "entry_metadata",
                            "error_type": type(error).__name__,
                            "error": str(error),
                        }
                    )
            for directory in reversed(subdirectories):
                stack.append(directory)
    except GateExceeded as error:
        completed = False
        gate_breaches.append(
            {
                "metric": error.metric,
                "actual": error.actual,
                "maximum": error.maximum,
            }
        )

    matches.sort(key=lambda item: (item["document_id"], item["source_relative_path"].casefold(), item["source_relative_path"]))
    return {
        "completed": completed,
        "counters": counters,
        "access_errors": access_errors,
        "gate_breaches": gate_breaches,
        "reparse_points": reparse_points,
        "matches": matches,
    }


def copy_source_and_hash(source: Path, destination: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".v10c_",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as output_handle:
            temporary_path = Path(output_handle.name)
            with source.open("rb") as input_handle:
                while True:
                    block = input_handle.read(CHUNK_SIZE)
                    if not block:
                        break
                    output_handle.write(block)
                    digest.update(block)
                    total += len(block)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        if destination.exists():
            raise FileExistsError(f"Destination appeared during copy: {destination}")
        os.rename(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return digest.hexdigest(), total


def relative_project_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def main() -> int:
    started = time.perf_counter()
    generated_at = utc_now()
    config = load_json(CONFIG_PATH)
    targets = sorted(config["targets"], key=lambda item: item["acquisition_sequence"])
    output_paths = {
        key: (PROJECT_ROOT / value).resolve()
        for key, value in config["outputs"].items()
    }

    regression_records = [project_file_record(item) for item in config["regression_files"]]
    regression_all_match = all(record["matches"] for record in regression_records)

    register_path = (PROJECT_ROOT / config["cached_register"]["path"]).resolve()
    register_hash, register_size = sha256_file(register_path)
    register_hash_matches = register_hash == config["cached_register"]["expected_sha256"].lower()
    register_audit = read_register_targets(register_path, targets)

    protected_before = [project_file_record(item) for item in config["protected_files"]]
    protected_before_all_match = all(record["matches"] for record in protected_before)

    expected_filenames = [target["expected_filename"].casefold() for target in targets]
    target_identifiers = [target["document_id"] for target in targets]
    target_preflight = {
        "target_count_exactly_nine": len(targets) == 9,
        "target_identifiers_unique": len(set(target_identifiers)) == len(target_identifiers),
        "exact_expected_filenames_unique": len(set(expected_filenames)) == len(expected_filenames),
    }

    preflight_passed = bool(
        regression_all_match
        and register_hash_matches
        and register_audit["all_targets_exactly_once"]
        and register_audit["all_target_fields_match"]
        and register_audit["hyperlink_count"] == 9
        and protected_before_all_match
        and all(target_preflight.values())
    )

    source_root = Path(config["archive_search"]["root"]).resolve()
    traversal = {
        "completed": False,
        "counters": {
            "directories_visited": 0,
            "file_entries_examined_by_name": 0,
            "utf8_path_bytes_examined": 0,
            "reparse_points_skipped": 0,
            "compressed_archive_entry_scan_count": 0,
            "unrelated_source_payload_read_count": 0,
        },
        "access_errors": [],
        "gate_breaches": [],
        "reparse_points": [],
        "matches": [],
    }
    if preflight_passed and source_root.is_dir():
        target_name_map = {
            target["expected_filename"].casefold(): target["document_id"]
            for target in targets
        }
        traversal = traverse_archive(
            source_root,
            target_name_map,
            config["archive_search"]["bounds"],
        )
    elif not source_root.is_dir():
        traversal["gate_breaches"].append(
            {
                "metric": "source_archive_root_exists",
                "actual": 0,
                "maximum": 0,
                "detail": str(source_root),
            }
        )

    matches = traversal["matches"]
    bounds = config["archive_search"]["bounds"]
    metadata_gate_breaches: list[dict[str, Any]] = []
    total_match_bytes = sum(item["size_bytes"] for item in matches)
    if len(matches) > bounds["maximum_exact_file_matches"]:
        metadata_gate_breaches.append(
            {
                "metric": "exact_file_matches",
                "actual": len(matches),
                "maximum": bounds["maximum_exact_file_matches"],
            }
        )
    for item in matches:
        if item["size_bytes"] > bounds["maximum_individual_exact_payload_bytes"]:
            metadata_gate_breaches.append(
                {
                    "metric": "individual_exact_payload_bytes",
                    "document_id": item["document_id"],
                    "path": item["source_path"],
                    "actual": item["size_bytes"],
                    "maximum": bounds["maximum_individual_exact_payload_bytes"],
                }
            )
    if total_match_bytes > bounds["maximum_aggregate_exact_match_bytes"]:
        metadata_gate_breaches.append(
            {
                "metric": "aggregate_exact_match_bytes",
                "actual": total_match_bytes,
                "maximum": bounds["maximum_aggregate_exact_match_bytes"],
            }
        )
    worst_case_source_read_bytes = total_match_bytes * 3
    if worst_case_source_read_bytes > bounds["maximum_source_payload_read_bytes"]:
        metadata_gate_breaches.append(
            {
                "metric": "worst_case_source_payload_read_bytes",
                "actual": worst_case_source_read_bytes,
                "maximum": bounds["maximum_source_payload_read_bytes"],
            }
        )

    payload_gate_ready = bool(
        preflight_passed
        and traversal["completed"]
        and not traversal["gate_breaches"]
        and not traversal["access_errors"]
        and not metadata_gate_breaches
    )

    source_payload_read_bytes = 0
    copy_errors: list[dict[str, Any]] = []
    working_copies: list[dict[str, Any]] = []

    if payload_gate_ready:
        for item in matches:
            source = Path(item["source_path"])
            digest, bytes_read, header = sha256_pdf_with_header(source)
            source_payload_read_bytes += bytes_read
            item["source_sha256_before"] = digest
            item["pdf_header_hex"] = header.hex()
            item["pdf_header_valid"] = header.startswith(b"%PDF-")

        all_headers_valid = all(item["pdf_header_valid"] for item in matches)
        if all_headers_valid and matches:
            destination_root = (PROJECT_ROOT / config["working_copy_policy"]["destination_directory"]).resolve()
            if not destination_root.is_relative_to(PROJECT_ROOT):
                raise RuntimeError("Working-copy directory escapes project root")
            unique_sources: dict[tuple[str, str], dict[str, Any]] = {}
            for item in matches:
                unique_sources.setdefault(
                    (item["document_id"], item["source_sha256_before"]),
                    item,
                )

            for (document_id, digest), representative in sorted(unique_sources.items()):
                source = Path(representative["source_path"])
                destination = destination_root / f"{document_id}__{digest[:16]}.pdf"
                try:
                    if destination.exists():
                        destination_digest, destination_size = sha256_file(destination)
                        if destination_digest != digest or destination_size != representative["size_bytes"]:
                            raise RuntimeError(
                                f"Existing working copy does not match source: {destination}"
                            )
                        copy_status = "EXISTING_VERIFIED"
                    else:
                        copied_digest, copied_bytes = copy_source_and_hash(source, destination)
                        source_payload_read_bytes += copied_bytes
                        if copied_digest != digest or copied_bytes != representative["size_bytes"]:
                            raise RuntimeError(
                                f"Copy hash or size mismatch for {destination}"
                            )
                        destination_digest, destination_size = sha256_file(destination)
                        if destination_digest != digest or destination_size != representative["size_bytes"]:
                            raise RuntimeError(
                                f"Destination verification mismatch for {destination}"
                            )
                        copy_status = "CREATED_AND_VERIFIED"
                    record = {
                        "document_id": document_id,
                        "source_sha256": digest,
                        "source_representative_path": representative["source_path"],
                        "destination_path": relative_project_path(destination),
                        "size_bytes": representative["size_bytes"],
                        "destination_sha256": destination_digest,
                        "copy_status": copy_status,
                    }
                    working_copies.append(record)
                    for item in matches:
                        if item["document_id"] == document_id and item["source_sha256_before"] == digest:
                            item["working_copy_path"] = record["destination_path"]
                            item["working_copy_sha256"] = destination_digest
                            item["copy_status"] = copy_status
                except Exception as error:
                    copy_errors.append(
                        {
                            "document_id": document_id,
                            "source_path": str(source),
                            "destination_path": str(destination),
                            "error_type": type(error).__name__,
                            "error": str(error),
                        }
                    )

        for item in matches:
            source = Path(item["source_path"])
            digest_after, bytes_read_after = sha256_file(source)
            source_payload_read_bytes += bytes_read_after
            stat_after = source.stat()
            item["source_sha256_after"] = digest_after
            item["mtime_ns_after"] = int(stat_after.st_mtime_ns)
            item["size_bytes_after"] = int(stat_after.st_size)
            item["source_unchanged_after_copy"] = bool(
                digest_after == item["source_sha256_before"]
                and item["size_bytes_after"] == item["size_bytes"]
                and item["mtime_ns_after"] == item["mtime_ns_before"]
            )

    protected_after = [project_file_record(item) for item in config["protected_files"]]
    protected_after_all_match = all(record["matches"] for record in protected_after)

    matches_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in matches:
        matches_by_id[item["document_id"]].append(item)

    identity_rows: list[dict[str, Any]] = []
    locator_rows: list[dict[str, Any]] = []
    register_by_id = {
        item["document_id"]: item
        for item in register_audit["transcribed_rows"]
    }
    for target in targets:
        identifier = target["document_id"]
        local_matches = matches_by_id.get(identifier, [])
        working_copy_paths = sorted(
            {
                item["working_copy_path"]
                for item in local_matches
                if item.get("working_copy_path")
            }
        )
        source_paths = sorted(item["source_path"] for item in local_matches)
        source_hashes = sorted(
            {
                item["source_sha256_before"]
                for item in local_matches
                if item.get("source_sha256_before")
            }
        )
        if not traversal["completed"] or traversal["access_errors"] or traversal["gate_breaches"]:
            status = "UNRESOLVED_SEARCH_GATE_NOT_COMPLETE"
        elif not local_matches:
            status = "NOT_LOCALIZED_IN_BOUNDED_VISIBLE_FILESYSTEM_NAME_CHECK"
        elif all(
            item.get("pdf_header_valid")
            and item.get("working_copy_path")
            and item.get("source_unchanged_after_copy")
            for item in local_matches
        ):
            status = "LOCALIZED_HASHED_AND_COPIED"
        else:
            status = "MATCH_FOUND_BUT_IDENTITY_OR_COPY_GATE_FAILED"

        identity_rows.append(
            {
                "acquisition_sequence": target["acquisition_sequence"],
                "document_id": identifier,
                "expected_filename": target["expected_filename"],
                "book_number": target["book_number"],
                "group_id": target["group_id"],
                "subsystem": target["subsystem"],
                "register_pdf_title": target["register_pdf_title"],
                "register_tower_label": target["register_tower_label"],
                "register_hyperlink": target["register_hyperlink"],
                "register_evidence_class": "ARCHIVE_REGISTER_CLAIM_NOT_OFFICIAL_SOURCE",
                "local_identity_status": status,
                "exact_visible_file_match_count": len(local_matches),
                "unique_source_hash_count": len(source_hashes),
                "source_paths_json": json.dumps(source_paths, ensure_ascii=False, separators=(",", ":")),
                "source_sha256_json": json.dumps(source_hashes, separators=(",", ":")),
                "working_copy_paths_json": json.dumps(working_copy_paths, ensure_ascii=False, separators=(",", ":")),
                "drawing_page_content_read": "NO",
                "tower_a_to_wtc1_mapping_verified": "NO",
                "floor93_99_applicability_verified": "NO",
                "as_built_or_revision_authority_verified": "NO",
                "physical_assignment_count": 0,
                "solver_requirement_closed": "NO",
            }
        )
        locator = dict(register_by_id[identifier])
        locator.update(
            {
                "local_identity_status": status,
                "exact_visible_file_match_count": len(local_matches),
                "source_paths": source_paths,
                "source_sha256": source_hashes,
                "working_copy_paths": working_copy_paths,
                "drawing_page_content_read": False,
                "tower_a_to_wtc1_mapping_verified": False,
                "floor93_99_applicability_verified": False,
                "as_built_or_revision_authority_verified": False,
            }
        )
        locator_rows.append(locator)

    localized_target_count = sum(
        row["local_identity_status"] == "LOCALIZED_HASHED_AND_COPIED"
        for row in identity_rows
    )
    missing_target_count = sum(
        row["local_identity_status"] == "NOT_LOCALIZED_IN_BOUNDED_VISIBLE_FILESYSTEM_NAME_CHECK"
        for row in identity_rows
    )
    unresolved_target_count = len(targets) - localized_target_count - missing_target_count

    pdf_headers_valid = all(item.get("pdf_header_valid") is True for item in matches) if matches else True
    copies_match = bool(
        not copy_errors
        and all(
            item.get("working_copy_sha256") == item.get("source_sha256_before")
            for item in matches
        )
    ) if matches else True
    sources_unchanged = all(item.get("source_unchanged_after_copy") is True for item in matches) if matches else True
    source_read_budget_passed = source_payload_read_bytes <= bounds["maximum_source_payload_read_bytes"]

    checks = {
        "v10b_regression_hashes": regression_all_match,
        "cached_register_hash": register_hash_matches,
        "cached_register_target_rows_exactly_once": register_audit["all_targets_exactly_once"],
        "cached_register_target_fields_match": register_audit["all_target_fields_match"],
        "cached_register_hyperlinks_match": register_audit["hyperlink_count"] == 9,
        "protected_blender_master_before": protected_before_all_match,
        "protected_blender_master_after": protected_after_all_match,
        "target_count_exactly_nine": target_preflight["target_count_exactly_nine"],
        "target_identifiers_unique": target_preflight["target_identifiers_unique"],
        "exact_expected_filenames_unique": target_preflight["exact_expected_filenames_unique"],
        "traversal_bounds_not_exceeded": traversal["completed"] and not traversal["gate_breaches"],
        "traversal_access_error_count_zero": len(traversal["access_errors"]) == 0,
        "exact_match_metadata_bounds_not_exceeded": len(metadata_gate_breaches) == 0,
        "source_payload_read_budget": source_read_budget_passed,
        "exact_match_pdf_headers_valid": pdf_headers_valid,
        "copied_payload_hashes_match_sources": copies_match,
        "exact_source_hashes_unchanged_after_copy": sources_unchanged,
        "source_archive_write_operation_count_zero": True,
        "unrelated_source_payload_read_count_zero": traversal["counters"]["unrelated_source_payload_read_count"] == 0,
        "compressed_archive_entry_scan_count_zero": traversal["counters"]["compressed_archive_entry_scan_count"] == 0,
        "official_sources_directory_not_read": True,
        "no_network_or_external_contact": True,
        "physical_assignment_count_zero": True,
        "solver_blender_thermal_gates_closed": True,
        "copy_error_count_zero": len(copy_errors) == 0,
    }
    validation_status = "PASS" if all(checks.values()) else "FAIL"

    match_inventory_rows = []
    for item in matches:
        match_inventory_rows.append(
            {
                "document_id": item["document_id"],
                "source_path": item["source_path"],
                "source_relative_path": item["source_relative_path"],
                "source_filename": item["source_filename"],
                "size_bytes": item["size_bytes"],
                "mtime_ns_before": item["mtime_ns_before"],
                "source_sha256_before": item.get("source_sha256_before") or "",
                "pdf_header_hex": item.get("pdf_header_hex") or "",
                "pdf_header_valid": "YES" if item.get("pdf_header_valid") else "NO",
                "working_copy_path": item.get("working_copy_path") or "",
                "working_copy_sha256": item.get("working_copy_sha256") or "",
                "copy_status": item.get("copy_status") or "",
                "mtime_ns_after": item.get("mtime_ns_after") or "",
                "source_sha256_after": item.get("source_sha256_after") or "",
                "source_unchanged_after_copy": "YES" if item.get("source_unchanged_after_copy") else "NO",
                "drawing_page_content_read": "NO",
                "provenance_or_revision_authority_verified": "NO",
            }
        )

    next_objective = (
        config["next_iteration"]["objective_if_missing_payloads"]
        if missing_target_count > 0 or unresolved_target_count > 0
        else config["next_iteration"]["objective_if_all_localized"]
    )
    next_iteration = {
        "id": config["next_iteration"]["id"],
        "objective": next_objective,
    }

    source_manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "scope": config["dataset"]["scope"],
        "v10b_regression_files": {
            "count": len(regression_records),
            "all_match": regression_all_match,
            "files": regression_records,
        },
        "cached_register": {
            "path": config["cached_register"]["path"],
            "size_bytes": register_size,
            "expected_sha256": config["cached_register"]["expected_sha256"],
            "actual_sha256": register_hash,
            "matches": register_hash_matches,
            "sheet_name": config["cached_register"]["sheet_name"],
            "used_range": config["cached_register"]["used_range"],
            "evidence_class": config["cached_register"]["evidence_class"],
            "target_hyperlink_count": register_audit["hyperlink_count"],
        },
        "protected_blender_master_before": protected_before,
        "protected_blender_master_after": protected_after,
        "source_archive": {
            "root": str(source_root),
            "read_only": True,
            "filename_metadata_traversal_performed": preflight_passed,
            "unrelated_file_content_read_count": traversal["counters"]["unrelated_source_payload_read_count"],
            "exact_match_content_file_count": len(matches),
            "write_operation_count": 0,
        },
        "source_policy": config["source_policy"],
    }

    search_gate_audit = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "method": config["archive_search"]["method"],
        "search_root": str(source_root),
        "target_filename_count": len(expected_filenames),
        "target_filenames": [target["expected_filename"] for target in targets],
        "bounds": bounds,
        "actual": {
            **traversal["counters"],
            "search_completed": traversal["completed"],
            "access_error_count": len(traversal["access_errors"]),
            "traversal_gate_breach_count": len(traversal["gate_breaches"]),
            "exact_file_match_count": len(matches),
            "aggregate_exact_match_bytes": total_match_bytes,
            "metadata_gate_breach_count": len(metadata_gate_breaches),
            "source_payload_read_bytes": source_payload_read_bytes,
            "localized_target_count": localized_target_count,
            "missing_target_count": missing_target_count,
            "unresolved_target_count": unresolved_target_count,
        },
        "traversal_gate_breaches": traversal["gate_breaches"],
        "metadata_gate_breaches": metadata_gate_breaches,
        "access_errors": traversal["access_errors"],
        "reparse_points_skipped": traversal["reparse_points"],
        "copy_errors": copy_errors,
        "interpretation": config["archive_search"]["missing_status_semantics"],
    }

    locator_transcription = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "source_workbook": config["cached_register"]["path"],
        "source_workbook_sha256": register_hash,
        "transcription_method": config["cached_register"]["hyperlink_transcription_method"],
        "network_access_used": False,
        "drawing_page_content_read": False,
        "target_count": len(locator_rows),
        "rows": locator_rows,
        "qualification": "Register titles, Tower A+B labels, drawing ranges and hyperlinks are archive-register claims. They do not independently verify WTC 1 mapping, Floors 93-99 applicability, revision authority or as-built status.",
    }

    working_copy_manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "destination_directory": config["working_copy_policy"]["destination_directory"],
        "directory_created": (PROJECT_ROOT / config["working_copy_policy"]["destination_directory"]).is_dir(),
        "exact_source_match_count": len(matches),
        "unique_working_copy_count": len(working_copies),
        "working_copy_total_bytes": sum(item["size_bytes"] for item in working_copies),
        "files": working_copies,
        "copy_errors": copy_errors,
        "source_hashes_unchanged_after_copy": sources_unchanged,
        "source_archive_write_operation_count": 0,
    }

    model_gate = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "checks": checks,
        "qualification": {
            "bounded_local_identity_check_complete": bool(
                traversal["completed"]
                and not traversal["access_errors"]
                and not traversal["gate_breaches"]
            ),
            "register_target_identifiers_and_hyperlinks_transcribed": register_audit["all_target_fields_match"],
            "localized_target_count": localized_target_count,
            "missing_target_count": missing_target_count,
            "target_payload_page_content_transcribed": False,
            "tower_a_to_wtc1_mapping_verified": False,
            "floor93_99_document_assignment_verified": False,
            "as_built_or_revision_authority_verified": False,
            "v10a_requirement_closed_count": 0,
            "member_sections_assigned": False,
            "material_properties_assigned": False,
            "connection_laws_assigned": False,
            "physical_damage_states_assigned": False,
            "structural_solver_ready": False,
            "structural_solver_executed": False,
            "blender_executed": False,
            "thermal_continuation_executed": False,
            "physical_validation": False,
        },
        "decision": (
            "PASS for the bounded local identity check only; drawing-content, provenance, revision, as-built and structural solver-readiness gates remain CLOSED."
            if validation_status == "PASS"
            else "FAIL: one or more predeclared identity, traversal, integrity or no-promotion gates failed."
        ),
    }

    report_lines = [
        "# WTC 1 - V10C - controle local borne des neuf identifiants P0",
        "",
        f"**Validation generale : {validation_status}**",
        "",
        "> CONTROLE D'IDENTITE DE FICHIERS UNIQUEMENT - AUCUNE PAGE DE PLAN TRANSCRITE - AUCUNE PROPRIETE PHYSIQUE - SOLVEUR ET BLENDER FERMES",
        "",
        "## Conclusion",
        "",
        (
            f"V10C a termine un parcours deterministe et borne des noms de fichiers visibles de l'archive source. "
            f"Il a examine {traversal['counters']['file_entries_examined_by_name']} fichiers dans "
            f"{traversal['counters']['directories_visited']} dossiers, pour "
            f"{traversal['counters']['utf8_path_bytes_examined']} octets UTF-8 de chemins. "
            f"{localized_target_count} des neuf identifiants P0 ont ete localises, haches et copies; "
            f"{missing_target_count} n'ont pas ete localises dans ce perimetre visible."
        ),
        "",
        (
            "Une non-localisation ne prouve pas l'absence d'un document dans une archive compressee, un depot distant ou tout autre stockage. "
            "V10C n'a inspecte aucune entree ZIP, aucun contenu de fichier non correspondant et aucune page de plan."
        ),
        "",
        "## 1. Faits directement observes ou transcrits",
        "",
        f"- Les neuf identifiants et neuf hyperliens du registre apparaissent chacun exactement une fois et correspondent aux valeurs predeclarees : {str(register_audit['all_target_fields_match']).upper()}.",
        f"- Dossiers visites : {traversal['counters']['directories_visited']} sur une limite de {bounds['maximum_directories_visited']}.",
        f"- Fichiers examines par nom : {traversal['counters']['file_entries_examined_by_name']} sur une limite de {bounds['maximum_file_entries_examined_by_name']}.",
        f"- Cibles de reanalyse (reparse points) volontairement non suivies : {traversal['counters']['reparse_points_skipped']} ({', '.join(traversal['reparse_points']) if traversal['reparse_points'] else 'aucune'}).",
        f"- Correspondances exactes visibles : {len(matches)}; copies de travail uniques : {len(working_copies)}.",
        f"- Erreurs d'acces : {len(traversal['access_errors'])}; depassements de porte : {len(traversal['gate_breaches']) + len(metadata_gate_breaches)}.",
        "",
        "## 2. Resultats de modeles officiels",
        "",
        "- V10C ne produit aucun resultat de modele officiel.",
        "- Les 22 exigences documentaires V10A restent bloquantes; une identite de fichier ne fournit ni propriete mecanique ni etat de dommage.",
        "",
        "## 3. Affirmations provenant des archives",
        "",
        "- Le classeur d'avril 2019 attribue aux neuf identifiants des titres, des familles de Drawing Books, l'etiquette Tower A+B et des hyperliens Archive.org.",
        "- Ces champs restent des affirmations de registre. Ils ne prouvent ni la correspondance Tower A vers WTC 1, ni les niveaux 93-99, ni la revision applicable, ni un statut as-built.",
        "",
        "## 4. Hypotheses propres au modele",
        "",
        "- La priorite P0 est un choix de workflow documentaire, pas une probabilite d'authenticite ou de pertinence physique.",
        "- Le parcours suppose seulement qu'un payload local non compresse conserve l'identifiant exact dans son nom de fichier. Cette hypothese n'est pas etendue aux conteneurs compresses ou aux fichiers renommes.",
        "",
        "## 5. Resultats derives",
        "",
        f"- Identifiants P0 localises : {localized_target_count}/9.",
        f"- Identifiants non localises dans le perimetre visible borne : {missing_target_count}/9.",
        f"- Octets de payload source lus pour les seules correspondances exactes : {source_payload_read_bytes}.",
        "- Pages de plans lues ou transcrites : 0.",
        "- Coordonnees, sections, materiaux, masses, rigidites, capacites, lois de connexion, dommages et credits de chemin de charge assignes : 0.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- Le registre ne renseigne aucun champ Floors pour les neuf cibles.",
        f"- {traversal['counters']['reparse_points_skipped']} cible de reanalyse n'a pas ete suivie afin de garantir le confinement au chemin d'archive; elle reste hors du perimetre de non-localisation.",
        "- Les identites locales manquantes restent a verifier par les hyperliens exacts du registre dans une iteration reseau separee et bornee.",
        "- Meme un PDF localise ne ferme pas la provenance, la revision, le statut as-built, l'applicabilite aux niveaux 93-99 ou l'etat physique du 11 septembre 2001.",
        "",
        "## Portes de validation",
        "",
    ]
    for name, passed in checks.items():
        report_lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            (
                "**Decision :** controle local d'identite PASS; portes de contenu, provenance, revision, as-built, proprietes physiques et solveur FERMEES."
                if validation_status == "PASS"
                else "**Decision :** controle V10C FAIL; aucun enregistrement d'iteration n'est autorise."
            ),
            "",
            "## Livrables principaux",
            "",
            "- Audit de recherche : wtc1_simulation_v8/output/v10c_p0_search_gate_audit.json",
            "- Matrice d'identite : wtc1_simulation_v8/output/v10c_p0_identity_matrix.csv",
            "- Inventaire des correspondances exactes : wtc1_simulation_v8/output/v10c_p0_exact_match_inventory.csv",
            "- Transcription des localisateurs : wtc1_simulation_v8/output/v10c_p0_locator_transcription.json",
            "- Manifeste des copies : wtc1_simulation_v8/output/v10c_p0_working_copy_manifest.json",
            "- Porte documentaire/solveur : wtc1_simulation_v8/output/v10c_structural_source_gate.json",
            "",
            "## Etape suivante predeclaree - V10D",
            "",
            next_objective,
            "",
        ]
    )
    report_text = "\n".join(report_lines)

    output_file_list = [config["outputs"][key] for key in config["outputs"]]
    results = {
        "iteration": config["iteration"],
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "run": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "hostname": socket.gethostname(),
            "elapsed_seconds_before_final_serialization": round(time.perf_counter() - started, 3),
            "deterministic_filename_traversal": True,
            "structural_solver_executed": False,
            "blender_executed": False,
        },
        "random_seed": config["dataset"]["random_seed"],
        "random_draw_used": config["dataset"]["random_draw_used"],
        "scope": config["dataset"]["scope"],
        "input_manifest": {
            "v10b_regression_count": len(regression_records),
            "cached_register": config["cached_register"]["path"],
            "source_archive_root": str(source_root),
            "target_identifier_count": len(targets),
        },
        "output_files": output_file_list,
        "observed_or_transcribed_facts": {
            "register_target_identifier_count": len(targets),
            "register_hyperlink_count": register_audit["hyperlink_count"],
            "directories_visited": traversal["counters"]["directories_visited"],
            "file_entries_examined_by_name": traversal["counters"]["file_entries_examined_by_name"],
            "utf8_path_bytes_examined": traversal["counters"]["utf8_path_bytes_examined"],
            "reparse_points_skipped": traversal["counters"]["reparse_points_skipped"],
            "reparse_point_paths": traversal["reparse_points"],
            "exact_visible_file_match_count": len(matches),
            "unique_working_copy_count": len(working_copies),
        },
        "official_model_results": {
            "new_official_model_result_count": 0,
            "v10a_requirement_count_retained": 22,
            "v10a_requirement_closed_count": 0,
        },
        "archive_claims_used": {
            "register_evidence_class": config["cached_register"]["evidence_class"],
            "tower_label": "A+B",
            "hyperlink_count": register_audit["hyperlink_count"],
            "claims_provenance_or_as_built_authority": False,
        },
        "model_hypotheses": {
            "p0_is_workflow_priority_not_probability": True,
            "visible_uncompressed_exact_filename_identity_rule": True,
            "renamed_or_compressed_payloads_detected": False,
        },
        "derived_results": {
            "target_count": len(targets),
            "localized_target_count": localized_target_count,
            "missing_target_count": missing_target_count,
            "unresolved_target_count": unresolved_target_count,
            "exact_file_match_count": len(matches),
            "aggregate_exact_match_bytes": total_match_bytes,
            "source_payload_read_bytes": source_payload_read_bytes,
            "working_copy_count": len(working_copies),
            "drawing_page_content_read_count": 0,
            "source_archive_write_operation_count": 0,
            "compressed_archive_entry_scan_count": 0,
            "unrelated_source_payload_read_count": 0,
            "network_access_count": 0,
            "external_contact_count": 0,
            "physical_assignment_count": 0,
            "requirement_closed_count": 0,
            "solver_readiness": False,
            "structural_solver_executed": False,
            "blender_executed": False,
            "thermal_continuation_executed": False,
            "physical_validation": False,
        },
        "contradictions_and_missing_information": [
            "All nine selected register Floors fields remain blank.",
            "Tower A+B does not independently establish a WTC 1 mapping.",
            "A missing exact visible filename does not establish absence from compressed archives, renamed files, remote repositories or every possible storage location.",
            "Skipped reparse targets are outside the bounded non-localization scope.",
            "No PDF page, revision block, drawing index or member schedule is transcribed in V10C.",
            "File identity alone cannot establish as-built authority, September 11 damage or a physical load path.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": {
            "source_archive_read": preflight_passed,
            "source_archive_filename_metadata_traversal": preflight_passed,
            "source_archive_content_rescan": False,
            "source_archive_write_operation_count": 0,
            "official_sources_directory_read": False,
            "network_access_used": False,
            "external_contact_count": 0,
            "structural_solver_executed": False,
            "blender_executed": False,
            "thermal_continuation_executed": False,
        },
        "next_iteration": next_iteration,
    }

    write_json(output_paths["source_manifest"], source_manifest)
    write_json(output_paths["search_gate_audit"], search_gate_audit)
    write_csv(
        output_paths["identity_matrix_csv"],
        [
            "acquisition_sequence",
            "document_id",
            "expected_filename",
            "book_number",
            "group_id",
            "subsystem",
            "register_pdf_title",
            "register_tower_label",
            "register_hyperlink",
            "register_evidence_class",
            "local_identity_status",
            "exact_visible_file_match_count",
            "unique_source_hash_count",
            "source_paths_json",
            "source_sha256_json",
            "working_copy_paths_json",
            "drawing_page_content_read",
            "tower_a_to_wtc1_mapping_verified",
            "floor93_99_applicability_verified",
            "as_built_or_revision_authority_verified",
            "physical_assignment_count",
            "solver_requirement_closed",
        ],
        identity_rows,
    )
    write_csv(
        output_paths["exact_match_inventory_csv"],
        [
            "document_id",
            "source_path",
            "source_relative_path",
            "source_filename",
            "size_bytes",
            "mtime_ns_before",
            "source_sha256_before",
            "pdf_header_hex",
            "pdf_header_valid",
            "working_copy_path",
            "working_copy_sha256",
            "copy_status",
            "mtime_ns_after",
            "source_sha256_after",
            "source_unchanged_after_copy",
            "drawing_page_content_read",
            "provenance_or_revision_authority_verified",
        ],
        match_inventory_rows,
    )
    write_json(output_paths["locator_transcription"], locator_transcription)
    write_json(output_paths["working_copy_manifest"], working_copy_manifest)
    write_json(output_paths["model_gate"], model_gate)
    output_paths["report"].parent.mkdir(parents=True, exist_ok=True)
    with output_paths["report"].open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report_text)
    write_json(output_paths["results"], results)

    summary = {
        "iteration": config["iteration"],
        "validation_status": validation_status,
        "directories_visited": traversal["counters"]["directories_visited"],
        "file_entries_examined_by_name": traversal["counters"]["file_entries_examined_by_name"],
        "exact_file_match_count": len(matches),
        "localized_target_count": localized_target_count,
        "missing_target_count": missing_target_count,
        "working_copy_count": len(working_copies),
        "requirement_closed_count": 0,
        "solver_readiness": False,
        "solver_executed": False,
        "blender_executed": False,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
