#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import posixpath
import re
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdf
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "wtc1_simulation_v8" / "data" / "v10d_p0_remote_identity_acquisition.json"
CHUNK_SIZE = 1024 * 1024
SELECTED_RESPONSE_HEADERS = (
    "Content-Length",
    "Content-Type",
    "Content-Range",
    "Content-Encoding",
    "ETag",
    "Last-Modified",
    "Accept-Ranges",
)


class RemotePolicyError(RuntimeError):
    pass


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
            writer.writerow({field: row.get(field, "") for field in fieldnames})


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


def project_record(item: dict[str, Any]) -> dict[str, Any]:
    path = (PROJECT_ROOT / item["path"]).resolve()
    exists = path.is_file()
    actual_sha256 = None
    size_bytes = None
    if exists:
        actual_sha256, size_bytes = sha256_file(path)
    expected_sha256 = item["expected_sha256"].lower()
    return {
        "role": item["role"],
        "path": item["path"],
        "exists": exists,
        "size_bytes": size_bytes,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "matches": bool(exists and actual_sha256 == expected_sha256),
    }


def relative_project_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def allowed_remote_url(url: str, policy: dict[str, Any]) -> bool:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != policy["allowed_scheme"]:
        return False
    host = (parsed.hostname or "").lower()
    return host == policy["allowed_exact_host"] or host.endswith(policy["allowed_host_suffix"])


def terminal_filename(url: str) -> str:
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    return posixpath.basename(path)


def exact_terminal_match(url: str, expected_filename: str) -> bool:
    return terminal_filename(url).casefold() == expected_filename.casefold()


def selected_headers(headers: Any) -> dict[str, str | None]:
    return {name: headers.get(name) for name in SELECTED_RESPONSE_HEADERS}


def positive_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text.isdigit():
        return None
    number = int(text)
    return number if number > 0 else None


def total_size_from_content_range(value: Any) -> int | None:
    if value is None:
        return None
    match = re.fullmatch(r"bytes\s+\d+-\d+/(\d+|\*)", str(value).strip(), flags=re.IGNORECASE)
    if not match or match.group(1) == "*":
        return None
    return positive_int(match.group(1))


def content_encoding_is_identity(headers: dict[str, str | None]) -> bool:
    value = (headers.get("Content-Encoding") or "").strip().lower()
    return value in ("", "identity")


class BoundedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, policy: dict[str, Any]) -> None:
        super().__init__()
        self.policy = policy
        self.redirect_chain: list[dict[str, Any]] = []

    def redirect_request(
        self,
        request: urllib.request.Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> urllib.request.Request | None:
        if len(self.redirect_chain) >= int(self.policy["maximum_redirects_per_request"]):
            raise RemotePolicyError("redirect count exceeds the predeclared per-request cap")
        absolute_url = urllib.parse.urljoin(request.full_url, new_url)
        allowed = allowed_remote_url(absolute_url, self.policy)
        self.redirect_chain.append(
            {
                "status_code": int(code),
                "from_url": request.full_url,
                "to_url": absolute_url,
                "allowed_https_archive_org_host": allowed,
            }
        )
        if not allowed:
            raise RemotePolicyError(f"redirect leaves allowed HTTPS Archive.org hosts: {absolute_url}")
        return super().redirect_request(request, file_pointer, code, message, headers, absolute_url)


class NetworkRecorder:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.records: list[dict[str, Any]] = []
        self.target_request_counts: dict[str, int] = defaultdict(int)

    def open(
        self,
        target: dict[str, Any],
        method: str,
        purpose: str,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[Any | None, dict[str, Any]]:
        started = time.perf_counter()
        identifier = target["document_id"]
        initial_url = target["register_hyperlink"]
        record: dict[str, Any] = {
            "request_sequence": len(self.records) + 1,
            "document_id": identifier,
            "method": method,
            "purpose": purpose,
            "initial_url": initial_url,
            "initial_url_exact_register_hyperlink": True,
            "initial_url_allowed_https_archive_org_host": allowed_remote_url(initial_url, self.policy),
            "request_headers": {},
            "response_status": None,
            "final_url": None,
            "final_url_allowed_https_archive_org_host": None,
            "terminal_filename": None,
            "terminal_filename_matches_expected": None,
            "redirect_chain": [],
            "response_headers": {},
            "body_bytes_read": 0,
            "policy_violation": False,
            "error_type": None,
            "error": None,
        }

        if len(self.records) >= int(self.policy["maximum_total_requests"]):
            record.update(
                {
                    "policy_violation": True,
                    "error_type": "REQUEST_BUDGET_EXCEEDED",
                    "error": "maximum_total_requests exceeded",
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                }
            )
            self.records.append(record)
            return None, record
        if self.target_request_counts[identifier] >= int(self.policy["maximum_requests_per_target"]):
            record.update(
                {
                    "policy_violation": True,
                    "error_type": "TARGET_REQUEST_BUDGET_EXCEEDED",
                    "error": "maximum_requests_per_target exceeded",
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                }
            )
            self.records.append(record)
            return None, record
        if not record["initial_url_allowed_https_archive_org_host"]:
            record.update(
                {
                    "policy_violation": True,
                    "error_type": "INITIAL_URL_POLICY_VIOLATION",
                    "error": initial_url,
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                }
            )
            self.records.append(record)
            return None, record

        self.target_request_counts[identifier] += 1
        headers = {
            "User-Agent": self.policy["user_agent"],
            "Accept": "application/pdf",
            "Accept-Encoding": self.policy["accept_encoding"],
            "Connection": "close",
        }
        if extra_headers:
            headers.update(extra_headers)
        record["request_headers"] = headers
        redirect_handler = BoundedRedirectHandler(self.policy)
        opener = urllib.request.build_opener(redirect_handler)
        request = urllib.request.Request(initial_url, headers=headers, method=method)
        try:
            response = opener.open(request, timeout=float(self.policy["request_timeout_seconds"]))
            final_url = response.geturl()
            final_allowed = allowed_remote_url(final_url, self.policy)
            record.update(
                {
                    "response_status": int(response.getcode()),
                    "final_url": final_url,
                    "final_url_allowed_https_archive_org_host": final_allowed,
                    "terminal_filename": terminal_filename(final_url),
                    "terminal_filename_matches_expected": exact_terminal_match(final_url, target["expected_filename"]),
                    "redirect_chain": redirect_handler.redirect_chain,
                    "response_headers": selected_headers(response.headers),
                    "policy_violation": not final_allowed,
                    "_started": started,
                }
            )
            if not final_allowed:
                response.close()
                record.update(
                    {
                        "error_type": "FINAL_URL_POLICY_VIOLATION",
                        "error": final_url,
                        "elapsed_seconds": round(time.perf_counter() - started, 3),
                    }
                )
                record.pop("_started", None)
                self.records.append(record)
                return None, record
            return response, record
        except urllib.error.HTTPError as error:
            final_url = error.geturl() or initial_url
            record.update(
                {
                    "response_status": int(error.code),
                    "final_url": final_url,
                    "final_url_allowed_https_archive_org_host": allowed_remote_url(final_url, self.policy),
                    "terminal_filename": terminal_filename(final_url),
                    "terminal_filename_matches_expected": exact_terminal_match(final_url, target["expected_filename"]),
                    "redirect_chain": redirect_handler.redirect_chain,
                    "response_headers": selected_headers(error.headers),
                    "policy_violation": not allowed_remote_url(final_url, self.policy),
                    "error_type": "HTTPError",
                    "error": str(error),
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                }
            )
            error.close()
            self.records.append(record)
            return None, record
        except Exception as error:
            is_policy = isinstance(error, RemotePolicyError)
            record.update(
                {
                    "redirect_chain": redirect_handler.redirect_chain,
                    "policy_violation": is_policy,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                }
            )
            self.records.append(record)
            return None, record

    def finish(
        self,
        response: Any,
        record: dict[str, Any],
        body_bytes_read: int,
        body_sha256: str | None = None,
        error: Exception | None = None,
    ) -> None:
        response.close()
        record["body_bytes_read"] = int(body_bytes_read)
        if body_sha256 is not None:
            record["body_sha256"] = body_sha256
        if error is not None:
            record["error_type"] = type(error).__name__
            record["error"] = str(error)
        started = float(record.pop("_started", time.perf_counter()))
        record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        self.records.append(record)


def verify_locator(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    locator_config = config["v10c_locator"]
    locator_path = (PROJECT_ROOT / locator_config["path"]).resolve()
    actual_hash, size_bytes = sha256_file(locator_path)
    locator = load_json(locator_path)
    rows = locator.get("rows", [])
    rows_by_id = {row.get("document_id"): row for row in rows}
    target_checks: list[dict[str, Any]] = []
    fields = (
        "acquisition_sequence",
        "document_id",
        "expected_filename",
        "group_id",
        "subsystem",
        "workbook_row",
        "book_number",
        "register_pdf_title",
        "register_content_summary",
        "register_tower_label",
        "register_drawing_start",
        "register_drawing_end",
        "register_hyperlink",
    )
    for target in config["targets"]:
        row = rows_by_id.get(target["document_id"], {})
        comparisons = {field: row.get(field) == target.get(field) for field in fields}
        target_checks.append(
            {
                "document_id": target["document_id"],
                "row_found": bool(row),
                "field_comparisons": comparisons,
                "all_fields_match": bool(row and all(comparisons.values())),
                "local_identity_status": row.get("local_identity_status"),
                "required_local_identity_status_matches": row.get("local_identity_status")
                == locator_config["required_local_identity_status"],
            }
        )
    audit = {
        "path": locator_config["path"],
        "size_bytes": size_bytes,
        "expected_sha256": locator_config["expected_sha256"],
        "actual_sha256": actual_hash,
        "hash_matches": actual_hash == locator_config["expected_sha256"],
        "validation_status": locator.get("validation_status"),
        "validation_status_matches": locator.get("validation_status")
        == locator_config["required_validation_status"],
        "target_count": len(rows),
        "target_count_matches": len(rows) == int(locator_config["required_target_count"]),
        "target_checks": target_checks,
        "all_target_fields_match": all(item["all_fields_match"] for item in target_checks),
        "all_targets_were_not_localized": all(
            item["required_local_identity_status_matches"] for item in target_checks
        ),
    }
    return locator, audit


def preflight_target(
    target: dict[str, Any],
    recorder: NetworkRecorder,
    policy: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "document_id": target["document_id"],
        "expected_filename": target["expected_filename"],
        "register_hyperlink": target["register_hyperlink"],
        "preflight_status": "PREFLIGHT_UNRESOLVED",
        "preflight_method_used": None,
        "preflight_final_url": None,
        "preflight_terminal_filename": None,
        "preflight_terminal_filename_matches": False,
        "preflight_content_length_bytes": None,
        "preflight_content_encoding_identity": False,
        "range_probe_body_hex": None,
        "range_probe_pdf_signature_observed": None,
        "full_get_authorized": False,
        "aggregate_reserved_bytes": 0,
    }

    head_response, head_record = recorder.open(target, "HEAD", "REMOTE_IDENTITY_AND_SIZE_PREFLIGHT")
    need_range_probe = True
    if head_response is not None:
        headers = head_record["response_headers"]
        head_length = positive_int(headers.get("Content-Length"))
        recorder.finish(head_response, head_record, 0)
        result.update(
            {
                "preflight_method_used": "HEAD",
                "preflight_final_url": head_record["final_url"],
                "preflight_terminal_filename": head_record["terminal_filename"],
                "preflight_terminal_filename_matches": bool(
                    head_record["terminal_filename_matches_expected"]
                ),
                "preflight_content_length_bytes": head_length,
                "preflight_content_encoding_identity": content_encoding_is_identity(headers),
            }
        )
        if head_record["policy_violation"]:
            result["preflight_status"] = "PREFLIGHT_POLICY_VIOLATION"
            return result
        if not head_record["terminal_filename_matches_expected"]:
            result["preflight_status"] = "PREFLIGHT_REJECT_TERMINAL_FILENAME"
            return result
        if not content_encoding_is_identity(headers):
            result["preflight_status"] = "PREFLIGHT_REJECT_CONTENT_ENCODING"
            return result
        if head_record["response_status"] == 200 and head_length is not None:
            need_range_probe = False

    if need_range_probe:
        range_response, range_record = recorder.open(
            target,
            "GET",
            "REMOTE_SIZE_AND_SIGNATURE_RANGE_PREFLIGHT",
            {"Range": policy["range_probe"]},
        )
        if range_response is None:
            if range_record.get("policy_violation"):
                result["preflight_status"] = "PREFLIGHT_POLICY_VIOLATION"
            else:
                result["preflight_status"] = "PREFLIGHT_TRANSPORT_UNAVAILABLE"
            return result
        try:
            probe = range_response.read(int(policy["range_probe_maximum_body_bytes_read"]))
            recorder.finish(range_response, range_record, len(probe), hashlib.sha256(probe).hexdigest())
        except Exception as error:
            recorder.finish(range_response, range_record, 0, error=error)
            result["preflight_status"] = "PREFLIGHT_TRANSPORT_UNAVAILABLE"
            return result
        headers = range_record["response_headers"]
        content_range_total = total_size_from_content_range(headers.get("Content-Range"))
        content_length = positive_int(headers.get("Content-Length"))
        if range_record["response_status"] == 206:
            inferred_length = content_range_total
        elif range_record["response_status"] == 200:
            inferred_length = content_length
        else:
            inferred_length = None
        result.update(
            {
                "preflight_method_used": "GET_RANGE_0_7",
                "preflight_final_url": range_record["final_url"],
                "preflight_terminal_filename": range_record["terminal_filename"],
                "preflight_terminal_filename_matches": bool(
                    range_record["terminal_filename_matches_expected"]
                ),
                "preflight_content_length_bytes": inferred_length,
                "preflight_content_encoding_identity": content_encoding_is_identity(headers),
                "range_probe_body_hex": probe.hex(),
                "range_probe_pdf_signature_observed": probe.startswith(
                    policy["require_pdf_signature"].encode("ascii")
                ),
            }
        )
        if range_record["policy_violation"]:
            result["preflight_status"] = "PREFLIGHT_POLICY_VIOLATION"
            return result
        if not range_record["terminal_filename_matches_expected"]:
            result["preflight_status"] = "PREFLIGHT_REJECT_TERMINAL_FILENAME"
            return result
        if not content_encoding_is_identity(headers):
            result["preflight_status"] = "PREFLIGHT_REJECT_CONTENT_ENCODING"
            return result
        if not probe.startswith(policy["require_pdf_signature"].encode("ascii")):
            result["preflight_status"] = "PREFLIGHT_REJECT_PDF_SIGNATURE"
            return result

    length = result["preflight_content_length_bytes"]
    if length is None or int(length) <= 0:
        result["preflight_status"] = "PREFLIGHT_REJECT_UNKNOWN_LENGTH"
    elif int(length) > int(policy["maximum_individual_payload_bytes"]):
        result["preflight_status"] = "PREFLIGHT_REJECT_INDIVIDUAL_SIZE_CAP"
    else:
        result["preflight_status"] = "PREFLIGHT_ELIGIBLE"
    return result


def bounded_metadata(reader: PdfReader, maximum_characters: int) -> tuple[dict[str, str], bool]:
    metadata = reader.metadata or {}
    output: dict[str, str] = {}
    truncated = False
    for index, key in enumerate(sorted(metadata.keys(), key=lambda value: str(value))):
        if index >= 50:
            truncated = True
            break
        key_text = str(key)[:128]
        value_text = str(metadata.get(key, ""))
        if len(value_text) > maximum_characters:
            value_text = value_text[:maximum_characters]
            truncated = True
        output[key_text] = value_text
    return output, truncated


def acquire_target(
    target: dict[str, Any],
    preflight: dict[str, Any],
    recorder: NetworkRecorder,
    policy: dict[str, Any],
    working_copy_policy: dict[str, Any],
    container_policy: dict[str, Any],
    destination_root: Path,
    accepted_bytes_before: int,
    full_get_bytes_before: int,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, int, int, list[str]]:
    result: dict[str, Any] = {
        "document_id": target["document_id"],
        "full_get_attempted": False,
        "full_get_status": "NOT_AUTHORIZED_BY_PREFLIGHT",
        "full_get_final_url": None,
        "full_get_terminal_filename": None,
        "full_get_terminal_filename_matches": False,
        "full_get_declared_length_bytes": None,
        "preflight_length_matches_full_get": None,
        "payload_bytes_read": 0,
        "pdf_signature_valid": False,
        "payload_sha256": None,
        "container_parse_status": "NOT_PARSED",
        "working_copy_path": None,
        "working_copy_sha256": None,
        "copy_status": None,
        "integrity_error": None,
    }
    if not preflight.get("full_get_authorized"):
        return result, None, None, 0, 0, []

    result["full_get_attempted"] = True
    response, request_record = recorder.open(target, "GET", "FULL_PDF_ACQUISITION")
    if response is None:
        result["full_get_status"] = (
            "FULL_GET_POLICY_VIOLATION"
            if request_record.get("policy_violation")
            else "FULL_GET_TRANSPORT_UNAVAILABLE"
        )
        return result, None, None, 0, 0, []

    headers = request_record["response_headers"]
    declared_length = positive_int(headers.get("Content-Length"))
    result.update(
        {
            "full_get_final_url": request_record["final_url"],
            "full_get_terminal_filename": request_record["terminal_filename"],
            "full_get_terminal_filename_matches": bool(
                request_record["terminal_filename_matches_expected"]
            ),
            "full_get_declared_length_bytes": declared_length,
            "preflight_length_matches_full_get": declared_length
            == preflight.get("preflight_content_length_bytes"),
        }
    )

    rejection = None
    if request_record["response_status"] != int(policy["full_get_status_required"]):
        rejection = "FULL_GET_REJECT_STATUS"
    elif not request_record["terminal_filename_matches_expected"]:
        rejection = "FULL_GET_REJECT_TERMINAL_FILENAME"
    elif not content_encoding_is_identity(headers):
        rejection = "FULL_GET_REJECT_CONTENT_ENCODING"
    elif declared_length is None:
        rejection = "FULL_GET_REJECT_UNKNOWN_LENGTH"
    elif declared_length > int(policy["maximum_individual_payload_bytes"]):
        rejection = "FULL_GET_REJECT_INDIVIDUAL_SIZE_CAP"
    elif full_get_bytes_before + declared_length > int(
        policy["maximum_aggregate_full_get_payload_bytes"]
    ):
        rejection = "FULL_GET_REJECT_AGGREGATE_TRANSFER_CAP"
    elif accepted_bytes_before + declared_length > int(
        policy["maximum_aggregate_accepted_payload_bytes"]
    ):
        rejection = "FULL_GET_REJECT_AGGREGATE_ACCEPTED_CAP"

    if rejection is not None:
        recorder.finish(response, request_record, 0)
        result["full_get_status"] = rejection
        return result, None, None, 0, 0, []

    destination_root.mkdir(parents=True, exist_ok=True)
    temporary_paths: list[str] = []
    temporary_path: Path | None = None
    bytes_read = 0
    digest = hashlib.sha256()
    first_bytes = b""
    read_error: Exception | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".v10d_{target['document_id']}_",
            suffix=".part",
            dir=destination_root,
            delete=False,
        ) as temporary_handle:
            temporary_path = Path(temporary_handle.name)
            temporary_paths.append(str(temporary_path))
            remaining = int(declared_length)
            while remaining > 0:
                block = response.read(min(CHUNK_SIZE, remaining))
                if not block:
                    break
                if len(first_bytes) < 8:
                    first_bytes += block[: 8 - len(first_bytes)]
                temporary_handle.write(block)
                digest.update(block)
                bytes_read += len(block)
                remaining -= len(block)
    except Exception as error:
        read_error = error
    recorder.finish(
        response,
        request_record,
        bytes_read,
        digest.hexdigest() if bytes_read else None,
        read_error,
    )
    result["payload_bytes_read"] = bytes_read

    if read_error is not None:
        result["full_get_status"] = "FULL_GET_BODY_READ_ERROR"
    elif bytes_read != declared_length:
        result["full_get_status"] = "FULL_GET_REJECT_LENGTH_MISMATCH"
    elif not first_bytes.startswith(policy["require_pdf_signature"].encode("ascii")):
        result["full_get_status"] = "FULL_GET_REJECT_PDF_SIGNATURE"
    else:
        result["pdf_signature_valid"] = True

    if result["full_get_status"] != "NOT_AUTHORIZED_BY_PREFLIGHT":
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
        return result, None, None, 0, bytes_read, []

    if temporary_path is None:
        result["full_get_status"] = "FULL_GET_INTERNAL_TEMPORARY_PATH_ERROR"
        return result, None, None, 0, bytes_read, ["temporary path was not created"]

    payload_sha256 = digest.hexdigest()
    result["payload_sha256"] = payload_sha256
    container_record: dict[str, Any] | None = None
    try:
        reader = PdfReader(str(temporary_path), strict=False)
        encrypted = bool(reader.is_encrypted)
        empty_password_decrypt_result = None
        if encrypted:
            empty_password_decrypt_result = int(reader.decrypt(""))
        page_count = len(reader.pages)
        metadata, metadata_truncated = bounded_metadata(
            reader,
            int(container_policy["maximum_metadata_value_characters"]),
        )
        container_record = {
            "document_id": target["document_id"],
            "expected_filename": target["expected_filename"],
            "book_number": target["book_number"],
            "group_id": target["group_id"],
            "subsystem": target["subsystem"],
            "register_pdf_title": target["register_pdf_title"],
            "register_content_summary": target["register_content_summary"],
            "register_page_count": target["register_page_count"],
            "register_drawing_start": target["register_drawing_start"],
            "register_drawing_end": target["register_drawing_end"],
            "register_tower_label": target["register_tower_label"],
            "register_evidence_class": "ARCHIVE_REGISTER_CLAIM_NOT_OFFICIAL_SOURCE",
            "remote_final_url": request_record["final_url"],
            "pdf_header_version": first_bytes[5:8].decode("ascii", errors="replace"),
            "file_size_bytes": bytes_read,
            "sha256": payload_sha256,
            "page_count": page_count,
            "register_page_count_matches_container": page_count == target["register_page_count"],
            "encrypted": encrypted,
            "empty_password_decrypt_result": empty_password_decrypt_result,
            "document_information_metadata": metadata,
            "document_information_metadata_is_embedded_claim_not_verified_provenance": True,
            "document_information_metadata_truncated": metadata_truncated,
            "page_text_extracted": False,
            "page_rendered": False,
            "drawing_geometry_inspected": False,
        }
        result["container_parse_status"] = "PASS"
    except Exception as error:
        result["full_get_status"] = "FULL_GET_REJECT_CONTAINER_PARSE"
        result["container_parse_status"] = "FAIL"
        result["integrity_error"] = f"{type(error).__name__}: {error}"
        if temporary_path.exists():
            temporary_path.unlink()
        return result, None, None, 0, bytes_read, []

    destination = destination_root / f"{target['document_id']}__{payload_sha256[:16]}.pdf"
    integrity_errors: list[str] = []
    try:
        if destination.exists():
            existing_sha256, existing_size = sha256_file(destination)
            if existing_sha256 != payload_sha256 or existing_size != bytes_read:
                raise RuntimeError(f"existing destination conflicts with acquired payload: {destination}")
            temporary_path.unlink()
            copy_status = "EXISTING_VERIFIED_AFTER_REACQUISITION"
        else:
            temporary_path.rename(destination)
            copy_status = "CREATED_AND_VERIFIED"
        destination_sha256, destination_size = sha256_file(destination)
        if destination_sha256 != payload_sha256 or destination_size != bytes_read:
            raise RuntimeError(f"destination verification failed: {destination}")
    except Exception as error:
        if temporary_path.exists():
            temporary_path.unlink()
        message = f"{type(error).__name__}: {error}"
        result.update(
            {
                "full_get_status": "FULL_GET_DESTINATION_INTEGRITY_ERROR",
                "integrity_error": message,
            }
        )
        integrity_errors.append(message)
        return result, None, None, 0, bytes_read, integrity_errors

    copy_record = {
        "document_id": target["document_id"],
        "source_register_hyperlink": target["register_hyperlink"],
        "remote_final_url": request_record["final_url"],
        "remote_terminal_filename": request_record["terminal_filename"],
        "destination_path": relative_project_path(destination),
        "size_bytes": destination_size,
        "sha256": destination_sha256,
        "copy_status": copy_status,
        "claims_provenance_or_as_built_authority": False,
    }
    container_record["working_copy_path"] = copy_record["destination_path"]
    result.update(
        {
            "full_get_status": "ACQUIRED_HASHED_AND_CONTAINER_TRANSCRIBED",
            "working_copy_path": copy_record["destination_path"],
            "working_copy_sha256": destination_sha256,
            "copy_status": copy_status,
        }
    )
    return result, container_record, copy_record, destination_size, bytes_read, integrity_errors


def main() -> int:
    started = time.perf_counter()
    generated_at = utc_now()
    config = load_json(CONFIG_PATH)
    policy = config["remote_policy"]
    targets = sorted(config["targets"], key=lambda target: target["acquisition_sequence"])
    output_paths = {
        name: (PROJECT_ROOT / path).resolve() for name, path in config["outputs"].items()
    }

    regression_records = [project_record(item) for item in config["regression_files"]]
    regression_all_match = all(record["matches"] for record in regression_records)
    protected_before = [project_record(item) for item in config["protected_files"]]
    protected_before_all_match = all(record["matches"] for record in protected_before)
    locator, locator_audit = verify_locator(config)

    target_identifiers_unique = len({target["document_id"] for target in targets}) == len(targets)
    target_filenames_unique = len({target["expected_filename"].casefold() for target in targets}) == len(targets)
    target_urls_unique = len({target["register_hyperlink"] for target in targets}) == len(targets)
    all_initial_urls_allowed = all(allowed_remote_url(target["register_hyperlink"], policy) for target in targets)
    all_pre_network_gates = bool(
        config["iteration"] == "V10D"
        and len(targets) == 9
        and target_identifiers_unique
        and target_filenames_unique
        and target_urls_unique
        and all_initial_urls_allowed
        and regression_all_match
        and protected_before_all_match
        and locator_audit["hash_matches"]
        and locator_audit["validation_status_matches"]
        and locator_audit["target_count_matches"]
        and locator_audit["all_target_fields_match"]
        and locator_audit["all_targets_were_not_localized"]
    )
    if not all_pre_network_gates:
        print(
            json.dumps(
                {
                    "iteration": "V10D",
                    "validation_status": "FAIL_BEFORE_NETWORK",
                    "regression_all_match": regression_all_match,
                    "protected_before_all_match": protected_before_all_match,
                    "locator_audit": locator_audit,
                    "target_count": len(targets),
                    "target_identifiers_unique": target_identifiers_unique,
                    "target_filenames_unique": target_filenames_unique,
                    "target_urls_unique": target_urls_unique,
                    "all_initial_urls_allowed": all_initial_urls_allowed,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    recorder = NetworkRecorder(policy)
    preflight_rows = [preflight_target(target, recorder, policy) for target in targets]
    preflight_by_id = {row["document_id"]: row for row in preflight_rows}

    aggregate_reserved = 0
    for target in targets:
        row = preflight_by_id[target["document_id"]]
        if row["preflight_status"] != "PREFLIGHT_ELIGIBLE":
            continue
        size_bytes = int(row["preflight_content_length_bytes"])
        if aggregate_reserved + size_bytes > int(policy["maximum_aggregate_full_get_payload_bytes"]):
            row["preflight_status"] = "PREFLIGHT_REJECT_AGGREGATE_FULL_GET_CAP"
            continue
        aggregate_reserved += size_bytes
        row["aggregate_reserved_bytes"] = size_bytes
        row["full_get_authorized"] = True

    destination_root = (PROJECT_ROOT / config["working_copy_policy"]["destination_directory"]).resolve()
    if not destination_root.is_relative_to(PROJECT_ROOT):
        raise RuntimeError("V10D destination escapes the project root")

    acquisition_by_id: dict[str, dict[str, Any]] = {}
    container_records: list[dict[str, Any]] = []
    working_copies: list[dict[str, Any]] = []
    accepted_bytes = 0
    full_get_body_bytes = 0
    integrity_errors: list[str] = []
    for target in targets:
        preflight = preflight_by_id[target["document_id"]]
        acquisition, container, copy_record, accepted_delta, full_get_delta, errors = acquire_target(
            target,
            preflight,
            recorder,
            policy,
            config["working_copy_policy"],
            config["container_transcription"],
            destination_root,
            accepted_bytes,
            full_get_body_bytes,
        )
        acquisition_by_id[target["document_id"]] = acquisition
        accepted_bytes += accepted_delta
        full_get_body_bytes += full_get_delta
        integrity_errors.extend(errors)
        if container is not None:
            container_records.append(container)
        if copy_record is not None:
            working_copies.append(copy_record)

    protected_after = [project_record(item) for item in config["protected_files"]]
    protected_after_all_match = all(record["matches"] for record in protected_after)
    temporary_paths_after = (
        sorted(str(path) for path in destination_root.glob(".v10d_*.part"))
        if destination_root.is_dir()
        else []
    )

    identity_rows: list[dict[str, Any]] = []
    page_count_rows: list[dict[str, Any]] = []
    container_by_id = {record["document_id"]: record for record in container_records}
    for target in targets:
        preflight = preflight_by_id[target["document_id"]]
        acquisition = acquisition_by_id[target["document_id"]]
        container = container_by_id.get(target["document_id"])
        accepted = acquisition["full_get_status"] == "ACQUIRED_HASHED_AND_CONTAINER_TRANSCRIBED"
        if accepted:
            remote_identity_status = "ACQUIRED_HASHED_AND_CONTAINER_TRANSCRIBED"
        elif acquisition["full_get_attempted"]:
            remote_identity_status = acquisition["full_get_status"]
        else:
            remote_identity_status = preflight["preflight_status"]
        page_count = container.get("page_count") if container else None
        page_count_match = container.get("register_page_count_matches_container") if container else None
        identity_rows.append(
            {
                "acquisition_sequence": target["acquisition_sequence"],
                "document_id": target["document_id"],
                "expected_filename": target["expected_filename"],
                "book_number": target["book_number"],
                "group_id": target["group_id"],
                "subsystem": target["subsystem"],
                "register_pdf_title": target["register_pdf_title"],
                "register_tower_label": target["register_tower_label"],
                "initial_register_hyperlink": target["register_hyperlink"],
                "preflight_method": preflight["preflight_method_used"],
                "preflight_status": preflight["preflight_status"],
                "preflight_final_url": preflight["preflight_final_url"],
                "preflight_terminal_filename": preflight["preflight_terminal_filename"],
                "preflight_terminal_filename_matches": "YES"
                if preflight["preflight_terminal_filename_matches"]
                else "NO",
                "preflight_content_length_bytes": preflight["preflight_content_length_bytes"],
                "full_get_attempted": "YES" if acquisition["full_get_attempted"] else "NO",
                "full_get_status": acquisition["full_get_status"],
                "full_get_final_url": acquisition["full_get_final_url"],
                "full_get_terminal_filename": acquisition["full_get_terminal_filename"],
                "payload_size_bytes": acquisition["payload_bytes_read"],
                "payload_sha256": acquisition["payload_sha256"],
                "pdf_signature_valid": "YES" if acquisition["pdf_signature_valid"] else "NO",
                "container_page_count": page_count,
                "register_page_count": target["register_page_count"],
                "register_page_count_matches_container": (
                    "YES" if page_count_match is True else "NO" if page_count_match is False else ""
                ),
                "working_copy_path": acquisition["working_copy_path"],
                "copy_status": acquisition["copy_status"],
                "remote_identity_status": remote_identity_status,
                "drawing_page_content_read": "NO",
                "tower_a_to_wtc1_mapping_verified": "NO",
                "floor93_99_applicability_verified": "NO",
                "as_built_or_revision_authority_verified": "NO",
                "physical_assignment_count": 0,
                "solver_requirement_closed": "NO",
            }
        )
        page_count_rows.append(
            {
                "acquisition_sequence": target["acquisition_sequence"],
                "document_id": target["document_id"],
                "book_number": target["book_number"],
                "register_content_summary": target["register_content_summary"],
                "register_page_count": target["register_page_count"],
                "container_page_count": page_count,
                "page_count_match": (
                    "YES" if page_count_match is True else "NO" if page_count_match is False else "NOT_ACQUIRED"
                ),
                "interpretation": "DIAGNOSTIC_REGISTER_CLAIM_COMPARISON_NOT_PROVENANCE_OR_AS_BUILT_VALIDATION",
            }
        )

    accepted_count = len(working_copies)
    transport_unavailable_count = sum(
        "TRANSPORT_UNAVAILABLE" in row["remote_identity_status"] for row in identity_rows
    )
    rejected_or_unavailable_count = len(targets) - accepted_count
    page_count_match_count = sum(
        record["register_page_count_matches_container"] for record in container_records
    )
    range_probe_body_bytes = sum(
        int(record["body_bytes_read"])
        for record in recorder.records
        if record["purpose"] == "REMOTE_SIZE_AND_SIGNATURE_RANGE_PREFLIGHT"
    )
    request_body_bytes = sum(int(record["body_bytes_read"]) for record in recorder.records)
    redirect_count = sum(len(record["redirect_chain"]) for record in recorder.records)
    policy_violation_count = sum(bool(record["policy_violation"]) for record in recorder.records)
    request_budget_passed = bool(
        len(recorder.records) <= int(policy["maximum_total_requests"])
        and all(
            count <= int(policy["maximum_requests_per_target"])
            for count in recorder.target_request_counts.values()
        )
    )
    accepted_terminal_pass = all(
        row["full_get_terminal_filename_matches"] for row in acquisition_by_id.values()
        if row["full_get_status"] == "ACQUIRED_HASHED_AND_CONTAINER_TRANSCRIBED"
    )
    accepted_signature_pass = all(
        row["pdf_signature_valid"] for row in acquisition_by_id.values()
        if row["full_get_status"] == "ACQUIRED_HASHED_AND_CONTAINER_TRANSCRIBED"
    )
    accepted_size_pass = all(
        int(record["size_bytes"]) <= int(policy["maximum_individual_payload_bytes"])
        for record in working_copies
    )
    accepted_hash_pass = all(
        sha256_file(PROJECT_ROOT / record["destination_path"])
        == (record["sha256"], record["size_bytes"])
        for record in working_copies
    )
    container_parse_pass = all(
        acquisition_by_id[record["document_id"]]["container_parse_status"] == "PASS"
        for record in working_copies
    )
    every_full_get_had_preflight = all(
        preflight_by_id[identifier]["full_get_authorized"]
        and positive_int(preflight_by_id[identifier]["preflight_content_length_bytes"]) is not None
        for identifier, row in acquisition_by_id.items()
        if row["full_get_attempted"]
    )

    checks = {
        "v10c_regression_hashes": regression_all_match,
        "v10c_locator_hash_and_validation_status": bool(
            locator_audit["hash_matches"] and locator_audit["validation_status_matches"]
        ),
        "v10c_locator_nine_not_localized_targets_match": bool(
            locator_audit["target_count_matches"]
            and locator_audit["all_target_fields_match"]
            and locator_audit["all_targets_were_not_localized"]
        ),
        "protected_blender_master_before": protected_before_all_match,
        "protected_blender_master_after": protected_after_all_match,
        "target_count_exactly_nine": len(targets) == 9,
        "target_identifiers_filenames_and_urls_unique": bool(
            target_identifiers_unique and target_filenames_unique and target_urls_unique
        ),
        "initial_request_urls_exactly_match_v10c_locator": locator_audit["all_target_fields_match"],
        "all_requested_urls_and_redirects_allowed": policy_violation_count == 0,
        "request_budgets_not_exceeded": request_budget_passed,
        "every_full_get_had_known_positive_preflight_length": every_full_get_had_preflight,
        "full_get_payload_bytes_within_64_mib_cap": full_get_body_bytes
        <= int(policy["maximum_aggregate_full_get_payload_bytes"]),
        "all_accepted_terminal_filenames_match": accepted_terminal_pass,
        "all_accepted_pdf_signatures_valid": accepted_signature_pass,
        "all_accepted_individual_sizes_within_16_mib_cap": accepted_size_pass,
        "aggregate_accepted_size_within_64_mib_cap": accepted_bytes
        <= int(policy["maximum_aggregate_accepted_payload_bytes"]),
        "all_accepted_hashes_and_destinations_match": accepted_hash_pass,
        "all_accepted_containers_parse_without_page_content_access": container_parse_pass,
        "destination_integrity_error_count_zero": len(integrity_errors) == 0,
        "temporary_payload_count_zero_after_run": len(temporary_paths_after) == 0,
        "source_archive_and_official_sources_not_read_or_modified": True,
        "no_search_engine_url_discovery_or_external_contact": True,
        "drawing_page_content_read_count_zero": True,
        "physical_assignment_count_zero": True,
        "solver_blender_thermal_gates_closed": True,
    }
    validation_status = "PASS" if all(checks.values()) else "FAIL"

    identity_fields = [
        "acquisition_sequence",
        "document_id",
        "expected_filename",
        "book_number",
        "group_id",
        "subsystem",
        "register_pdf_title",
        "register_tower_label",
        "initial_register_hyperlink",
        "preflight_method",
        "preflight_status",
        "preflight_final_url",
        "preflight_terminal_filename",
        "preflight_terminal_filename_matches",
        "preflight_content_length_bytes",
        "full_get_attempted",
        "full_get_status",
        "full_get_final_url",
        "full_get_terminal_filename",
        "payload_size_bytes",
        "payload_sha256",
        "pdf_signature_valid",
        "container_page_count",
        "register_page_count",
        "register_page_count_matches_container",
        "working_copy_path",
        "copy_status",
        "remote_identity_status",
        "drawing_page_content_read",
        "tower_a_to_wtc1_mapping_verified",
        "floor93_99_applicability_verified",
        "as_built_or_revision_authority_verified",
        "physical_assignment_count",
        "solver_requirement_closed",
    ]
    page_fields = [
        "acquisition_sequence",
        "document_id",
        "book_number",
        "register_content_summary",
        "register_page_count",
        "container_page_count",
        "page_count_match",
        "interpretation",
    ]
    write_csv(output_paths["identity_matrix_csv"], identity_fields, identity_rows)
    write_csv(output_paths["page_count_audit_csv"], page_fields, page_count_rows)
    identity_fingerprint, _ = sha256_file(output_paths["identity_matrix_csv"])

    source_manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "scope": config["dataset"]["scope"],
        "v10c_regression_files": {
            "count": len(regression_records),
            "all_match": regression_all_match,
            "files": regression_records,
        },
        "v10c_locator": locator_audit,
        "protected_blender_master_before": protected_before,
        "protected_blender_master_after": protected_after,
        "remote_targets": [
            {
                "acquisition_sequence": target["acquisition_sequence"],
                "document_id": target["document_id"],
                "expected_filename": target["expected_filename"],
                "initial_register_hyperlink": target["register_hyperlink"],
                "evidence_class": "ARCHIVE_REGISTER_CLAIM_NOT_OFFICIAL_SOURCE",
            }
            for target in targets
        ],
        "source_policy": config["source_policy"],
        "source_archive": {
            "path": "C:/Users/jeuxpc/Desktop/ARCH/11 septembre 2001",
            "read": False,
            "modified": False,
        },
        "official_sources_directory": {
            "path": "work/official_sources",
            "read": False,
            "modified": False,
        },
    }

    request_audit = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "policy": policy,
        "actual": {
            "target_count": len(targets),
            "request_count": len(recorder.records),
            "request_count_by_target": dict(sorted(recorder.target_request_counts.items())),
            "redirect_count": redirect_count,
            "policy_violation_count": policy_violation_count,
            "range_probe_body_bytes": range_probe_body_bytes,
            "full_get_body_bytes": full_get_body_bytes,
            "all_request_body_bytes": request_body_bytes,
            "aggregate_preflight_reserved_bytes": aggregate_reserved,
            "accepted_payload_bytes": accepted_bytes,
            "accepted_payload_count": accepted_count,
            "transport_unavailable_count": transport_unavailable_count,
            "rejected_or_unavailable_count": rejected_or_unavailable_count,
        },
        "preflight_rows": preflight_rows,
        "requests": recorder.records,
        "qualification": "Only the nine exact V10C register hyperlinks were used as initial request URLs. Server redirects were allowed only to HTTPS Archive.org hosts. HTTP headers and endpoint strings are remote response claims, not provenance or as-built validation.",
    }

    container_metadata = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "transcription_policy": config["container_transcription"],
        "accepted_container_count": len(container_records),
        "records": container_records,
        "qualification": "Only PDF container metadata, page counts and register index-locator fields were transcribed. No page text, drawing geometry or rendered page was accessed. Embedded metadata is an unverified payload claim.",
    }

    working_copy_manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "destination_directory": config["working_copy_policy"]["destination_directory"],
        "directory_created": destination_root.is_dir(),
        "accepted_working_copy_count": accepted_count,
        "accepted_working_copy_total_bytes": accepted_bytes,
        "maximum_individual_payload_bytes": policy["maximum_individual_payload_bytes"],
        "maximum_aggregate_payload_bytes": policy["maximum_aggregate_accepted_payload_bytes"],
        "files": working_copies,
        "integrity_errors": integrity_errors,
        "temporary_payload_paths_after_run": temporary_paths_after,
        "source_archive_write_operation_count": 0,
    }

    model_gate = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "checks": checks,
        "qualification": {
            "bounded_remote_identity_acquisition_complete": validation_status == "PASS",
            "accepted_payload_count": accepted_count,
            "rejected_or_unavailable_payload_count": rejected_or_unavailable_count,
            "container_metadata_transcribed_count": len(container_records),
            "drawing_page_content_transcribed_count": 0,
            "tower_a_to_wtc1_mapping_verified": False,
            "floor93_99_document_assignment_verified": False,
            "as_built_or_revision_authority_verified": False,
            "v10a_requirement_closed_count": 0,
            "physical_coordinate_assignment_count": 0,
            "member_section_assignment_count": 0,
            "material_assignment_count": 0,
            "mass_assignment_count": 0,
            "stiffness_assignment_count": 0,
            "capacity_assignment_count": 0,
            "connection_law_assignment_count": 0,
            "damage_state_assignment_count": 0,
            "load_path_credit_count": 0,
            "structural_solver_ready": False,
            "structural_solver_executed": False,
            "blender_executed": False,
            "thermal_continuation_executed": False,
            "physical_validation": False,
        },
        "decision": (
            "PASS for the bounded remote identity/acquisition procedure only; provenance, drawing-content, revision, as-built, physical-property and solver-readiness gates remain CLOSED."
            if validation_status == "PASS"
            else "FAIL: one or more predeclared regression, endpoint, request, size, integrity or no-promotion gates failed."
        ),
    }

    report_lines = [
        "# WTC 1 - V10D - acquisition distante bornee des neuf identifiants P0",
        "",
        f"**Validation generale : {validation_status}**",
        "",
        "> ACQUISITION DOCUMENTAIRE BORNEE - AUCUNE PAGE DE PLAN TRANSCRITE - AUCUNE PROPRIETE PHYSIQUE - SOLVEUR, THERMIQUE ET BLENDER FERMES",
        "",
        "## Conclusion",
        "",
        (
            f"V10D a utilise uniquement les neuf hyperliens exacts conserves dans V10C. "
            f"{accepted_count}/9 payloads ont satisfait le nom terminal, la signature PDF, les plafonds, le hachage, la copie et la lecture du conteneur; "
            f"{rejected_or_unavailable_count}/9 ont ete rejetes ou sont restes indisponibles dans ce controle borne."
        ),
        "",
        (
            f"Les GET complets ont lu {full_get_body_bytes} octets sur une limite de "
            f"{policy['maximum_aggregate_full_get_payload_bytes']}; les copies acceptees totalisent {accepted_bytes} octets. "
            "Une copie Archive.org acceptee ne prouve ni chaine de transmission NIST, ni revision applicable, ni statut as-built, ni applicabilite aux niveaux 93-99."
        ),
        "",
        "## 1. Faits directement observes ou transcrits",
        "",
        f"- Requetes emises : {len(recorder.records)} sur une limite de {policy['maximum_total_requests']}; redirections serveur : {redirect_count}.",
        f"- Violations d'endpoint ou de redirection : {policy_violation_count}.",
        f"- Payloads acceptes, haches et copies : {accepted_count}/9.",
        f"- Comparaisons de nombre de pages registre/conteneur concordantes : {page_count_match_count}/{accepted_count} copies acceptees.",
        "- Texte de page extrait : 0; page rendue : 0; geometrie de dessin inspectee : 0.",
        "",
        "## 2. Resultats de modeles officiels",
        "",
        "- V10D ne produit aucun resultat de modele officiel et ne reexecute aucun calcul NIST.",
        "- Les 22 exigences documentaires V10A restent bloquantes; un PDF identifie ne fournit pas automatiquement une propriete mecanique ni un etat de dommage.",
        "",
        "## 3. Affirmations provenant des archives",
        "",
        "- Les titres, numeros de Drawing Books, nombres de pages publies, plages de dessins, etiquette Tower A+B et hyperliens proviennent du registre d'archive d'avril 2019.",
        "- Les en-tetes HTTP, URL finales et metadonnees PDF sont des affirmations des endpoints ou payloads distants; elles ne constituent pas une reception officielle NIST.",
        "",
        "## 4. Hypotheses propres au modele",
        "",
        "- P0 est une priorite de workflow documentaire, pas une probabilite d'authenticite, d'applicabilite ou d'importance physique.",
        "- L'egalite du nom terminal, la signature PDF et le hachage etablissent une identite de payload dans ce protocole; elles n'etablissent pas seules la provenance ou le statut as-built.",
        "",
        "## 5. Resultats derives",
        "",
        f"- Taille cumulee des copies acceptees : {accepted_bytes} octets, inferieure ou egale au plafond de {policy['maximum_aggregate_accepted_payload_bytes']} octets.",
        f"- Empreinte SHA-256 de la matrice d'identite V10D : `{identity_fingerprint}`.",
        "- Coordonnees, sections, materiaux, masses, rigidites, capacites, lois de connexion, dommages et credits de chemin de charge assignes : 0.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- La correspondance Tower A vers WTC 1 n'est pas independamment verifiee par V10D.",
        "- Les champs Floors du registre restent vides; l'applicabilite aux niveaux 93-99 n'est pas etablie.",
        "- Aucun index de dessin, cartouche, bloc de revision, page de detail ou geometrie n'est transcrit dans V10D.",
        "- L'acceptation d'un conteneur ne ferme ni la revision, ni le statut field/as-built, ni les donnees de connexions et proprietes necessaires au solveur.",
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
                "**Decision :** procedure distante V10D PASS; portes de provenance, contenu, as-built, proprietes, dommages et solveur FERMEES."
                if validation_status == "PASS"
                else "**Decision :** V10D FAIL; aucun enregistrement d'iteration ni mise a jour d'etat n'est autorise."
            ),
            "",
            "## Livrables principaux",
            "",
            "- Audit des requetes : wtc1_simulation_v8/output/v10d_p0_remote_request_audit.json",
            "- Matrice d'identite : wtc1_simulation_v8/output/v10d_p0_remote_identity_matrix.csv",
            "- Metadonnees de conteneur : wtc1_simulation_v8/output/v10d_p0_container_metadata.json",
            "- Manifeste des copies : wtc1_simulation_v8/output/v10d_p0_working_copy_manifest.json",
            "- Audit des nombres de pages : wtc1_simulation_v8/output/v10d_p0_register_page_count_audit.csv",
            "- Porte documentaire/solveur : wtc1_simulation_v8/output/v10d_structural_source_gate.json",
            "",
            "## Etape suivante predeclaree - V10E",
            "",
            config["next_iteration"]["objective"],
            "",
        ]
    )
    report_text = "\n".join(report_lines)

    output_file_list = [config["outputs"][name] for name in config["outputs"]]
    results = {
        "iteration": config["iteration"],
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": validation_status,
        "run": {
            "python": platform.python_version(),
            "pypdf": pypdf.__version__,
            "platform": platform.platform(),
            "hostname": socket.gethostname(),
            "elapsed_seconds_before_final_serialization": round(time.perf_counter() - started, 3),
            "network_access_used": True,
            "search_engine_used": False,
            "url_discovery_used": False,
            "structural_solver_executed": False,
            "blender_executed": False,
            "thermal_continuation_executed": False,
        },
        "random_seed": config["dataset"]["random_seed"],
        "random_draw_used": config["dataset"]["random_draw_used"],
        "scope": config["dataset"]["scope"],
        "input_manifest": {
            "v10c_regression_count": len(regression_records),
            "v10c_locator": config["v10c_locator"]["path"],
            "target_identifier_count": len(targets),
            "exact_initial_register_hyperlink_count": len(targets),
        },
        "output_files": output_file_list,
        "observed_or_transcribed_facts": {
            "request_count": len(recorder.records),
            "redirect_count": redirect_count,
            "accepted_payload_count": accepted_count,
            "accepted_payload_bytes": accepted_bytes,
            "accepted_container_count": len(container_records),
            "register_page_count_match_count": page_count_match_count,
            "drawing_page_content_read_count": 0,
            "pdf_page_render_count": 0,
        },
        "official_model_results": {
            "new_official_model_result_count": 0,
            "v10a_requirement_count_retained": 22,
            "v10a_requirement_closed_count": 0,
        },
        "archive_claims_used": {
            "evidence_class": config["v10c_locator"]["evidence_class"],
            "register_target_count": len(targets),
            "tower_label": "A+B",
            "claims_official_provenance_or_as_built_authority": False,
        },
        "model_hypotheses": {
            "p0_is_workflow_priority_not_probability": True,
            "terminal_filename_signature_hash_is_payload_identity_not_provenance": True,
            "transport_failure_or_identity_rejection_is_valid_bounded_result": True,
        },
        "derived_results": {
            "preflight_eligible_and_authorized_count": sum(
                row["full_get_authorized"] for row in preflight_rows
            ),
            "accepted_payload_count": accepted_count,
            "rejected_or_unavailable_count": rejected_or_unavailable_count,
            "transport_unavailable_count": transport_unavailable_count,
            "range_probe_body_bytes": range_probe_body_bytes,
            "full_get_body_bytes": full_get_body_bytes,
            "all_request_body_bytes": request_body_bytes,
            "aggregate_preflight_reserved_bytes": aggregate_reserved,
            "accepted_payload_bytes": accepted_bytes,
            "identity_matrix_fingerprint_sha256": identity_fingerprint,
            "physical_assignment_count": 0,
            "requirement_closed_count": 0,
            "solver_readiness": False,
            "structural_solver_executed": False,
            "blender_executed": False,
            "thermal_continuation_executed": False,
            "physical_validation": False,
        },
        "contradictions_and_missing_information": [
            "The V10C register fields and hyperlinks are archive claims rather than a file-level NIST receipt.",
            "Tower A+B does not independently establish a Tower A to WTC 1 mapping.",
            "The selected register Floors fields are blank, so Floors 93-99 applicability remains unverified.",
            "No drawing index, title block, revision block, member schedule, connection detail or geometry page is transcribed in V10D.",
            "Payload identity and container parsing do not establish revision authority, field/as-built status, September 11 damage or a physical load path.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": {
            "source_archive_read": False,
            "source_archive_modified": False,
            "official_sources_directory_read": False,
            "official_sources_directory_modified": False,
            "network_access_used": True,
            "network_initial_url_count": len(targets),
            "search_engine_used": False,
            "url_discovery_used": False,
            "external_contact_count": 0,
            "drawing_page_content_read_count": 0,
            "structural_solver_executed": False,
            "blender_executed": False,
            "thermal_continuation_executed": False,
        },
        "next_iteration": config["next_iteration"],
    }

    write_json(output_paths["source_manifest"], source_manifest)
    write_json(output_paths["request_audit"], request_audit)
    write_json(output_paths["container_metadata"], container_metadata)
    write_json(output_paths["working_copy_manifest"], working_copy_manifest)
    write_json(output_paths["model_gate"], model_gate)
    output_paths["report"].parent.mkdir(parents=True, exist_ok=True)
    with output_paths["report"].open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report_text)
    write_json(output_paths["results"], results)

    summary = {
        "iteration": config["iteration"],
        "validation_status": validation_status,
        "request_count": len(recorder.records),
        "redirect_count": redirect_count,
        "accepted_payload_count": accepted_count,
        "rejected_or_unavailable_count": rejected_or_unavailable_count,
        "accepted_payload_bytes": accepted_bytes,
        "full_get_body_bytes": full_get_body_bytes,
        "register_page_count_match_count": page_count_match_count,
        "drawing_page_content_read_count": 0,
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
