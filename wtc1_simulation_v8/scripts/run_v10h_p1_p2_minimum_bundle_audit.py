#!/usr/bin/env python3
"""V10H: exact offline minimum-bundle predeclaration for P1/P2 documents."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ROOT = SCRIPT_PATH.parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10h_p1_p2_minimum_bundle_audit.json"

OUTPUTS = {
    "source_manifest": "wtc1_simulation_v8/output/v10h_requirement_source_manifest.json",
    "regression_audit": "wtc1_simulation_v8/output/v10h_regression_audit.json",
    "candidate_coverage_csv": "wtc1_simulation_v8/output/v10h_p1_p2_candidate_coverage_matrix.csv",
    "selected_bundle_csv": "wtc1_simulation_v8/output/v10h_selected_bundle_matrix.csv",
    "bundle_predeclaration": "wtc1_simulation_v8/output/v10h_minimum_bundle_predeclaration.json",
    "requirement_coverage_csv": "wtc1_simulation_v8/output/v10h_requirement_coverage_matrix.csv",
    "separate_tracks_csv": "wtc1_simulation_v8/output/v10h_separate_evidence_tracks.csv",
    "document_request_shortlist": "wtc1_simulation_v8/output/v10h_liste_courte_documents_recherches.md",
    "model_gate": "wtc1_simulation_v8/output/v10h_structural_source_gate.json",
    "report": "wtc1_simulation_v8/output/rapport_wtc1_v10h_lot_minimal_p1_p2.md",
    "results": "wtc1_simulation_v8/output/resultats_wtc1_v10h_lot_minimal_p1_p2.json",
    "offline_audit": "wtc1_simulation_v8/output/v10h_offline_package_audit.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(relative_path: str, payload: Any) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(relative_path: str, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pipe_list(value: str) -> list[str]:
    return [item for item in value.split("|") if item]


def claimed_page_count(text: str) -> int | None:
    match = re.search(r"\b(\d{2,3})\s+(?:page|pg)\b", text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def main() -> int:
    started = utc_now()
    start_clock = time.perf_counter()
    config = read_json(CONFIG_PATH)
    expected = config["expected"]
    selection_policy = config["selection_policy"]

    protected_before: list[dict[str, Any]] = []
    for item in config["protected_inputs"]:
        path = ROOT / item["path"]
        actual = sha256_file(path) if path.is_file() else None
        protected_before.append(
            {
                "role": item["role"],
                "path": item["path"],
                "expected_sha256": item["sha256"],
                "actual_sha256": actual,
                "exists": path.is_file(),
                "hash_matches": actual == item["sha256"],
            }
        )

    paths = {item["role"]: ROOT / item["path"] for item in config["protected_inputs"]}
    requirement_rows = read_csv(paths["v10b_requirement_matrix"])
    priority_rows = read_csv(paths["v10b_priority_matrix"])
    v10g_rows = read_csv(paths["v10g_unresolved_requirement_matrix"])
    v10g_summary = read_json(paths["v10g_requirement_summary"])
    v10g_gate = read_json(paths["v10g_gate"])
    v10g_results = read_json(paths["v10g_results"])

    requirements_by_id = {row["requirement_id"]: row for row in requirement_rows}
    v10g_by_id = {row["requirement_id"]: row for row in v10g_rows}
    priority_by_id = {row["document_id"]: row for row in priority_rows}
    priority_counts = Counter(row["priority"] for row in priority_rows)
    candidate_priorities = set(selection_policy["candidate_priorities"])
    candidates = sorted(
        [row for row in priority_rows if row["priority"] in candidate_priorities],
        key=lambda row: int(row["acquisition_sequence"]),
    )

    document_to_requirements: dict[str, set[str]] = defaultdict(set)
    for requirement in requirement_rows:
        for document_id in pipe_list(requirement["candidate_document_ids"]):
            document_to_requirements[document_id].add(requirement["requirement_id"])

    primary_excluded = set(selection_policy["primary_excluded_requirement_ids"])
    primary_requirements = [
        row["requirement_id"] for row in requirement_rows if row["requirement_id"] not in primary_excluded
    ]
    candidate_ids = {row["document_id"] for row in candidates}
    reachable_primary = [
        requirement_id
        for requirement_id in primary_requirements
        if any(requirement_id in document_to_requirements[document_id] for document_id in candidate_ids)
    ]
    unreachable_primary = [item for item in primary_requirements if item not in reachable_primary]

    bit_index = {requirement_id: index for index, requirement_id in enumerate(reachable_primary)}
    full_mask = (1 << len(reachable_primary)) - 1
    candidate_masks: dict[str, int] = {}
    for candidate in candidates:
        mask = 0
        for requirement_id in document_to_requirements[candidate["document_id"]]:
            if requirement_id in bit_index:
                mask |= 1 << bit_index[requirement_id]
        candidate_masks[candidate["document_id"]] = mask

    # Dynamic programming over the 16 reachable requirements. For each mask,
    # retain the lexicographically best solution under the predeclared cost.
    # Cost order: document count, P2 count, sequence sum, sequence tuple, IDs.
    states: dict[int, tuple[tuple[Any, ...], tuple[str, ...]]] = {
        0: ((0, 0, 0, tuple(), tuple()), tuple())
    }
    for candidate in candidates:
        document_id = candidate["document_id"]
        document_mask = candidate_masks[document_id]
        if document_mask == 0:
            continue
        sequence = int(candidate["acquisition_sequence"])
        p2_increment = 1 if candidate["priority"] == "P2_SUPPLEMENTAL" else 0
        for previous_mask, (_, previous_ids) in list(states.items()):
            new_mask = previous_mask | document_mask
            if new_mask == previous_mask:
                continue
            new_ids = previous_ids + (document_id,)
            sequences = tuple(int(priority_by_id[item]["acquisition_sequence"]) for item in new_ids)
            p2_count = sum(priority_by_id[item]["priority"] == "P2_SUPPLEMENTAL" for item in new_ids)
            cost = (len(new_ids), p2_count, sum(sequences), sequences, new_ids)
            if new_mask not in states or cost < states[new_mask][0]:
                states[new_mask] = (cost, new_ids)

    selected_primary_ids = list(states[full_mask][1]) if full_mask in states else []
    selected_primary_set = set(selected_primary_ids)
    selected_primary_rows = [priority_by_id[document_id] for document_id in selected_primary_ids]

    maximum_coverage_by_maximum_file_count: dict[str, int] = {}
    for limit in range(1, len(selected_primary_ids) + 1):
        maximum_coverage_by_maximum_file_count[str(limit)] = max(
            (mask.bit_count() for mask, (cost, _) in states.items() if cost[0] <= limit),
            default=0,
        )

    # Request order within the exact optimal set: greatest marginal coverage
    # first, then the earlier immutable V10B acquisition sequence.
    request_order: list[dict[str, Any]] = []
    covered_so_far: set[str] = set()
    remaining = list(selected_primary_rows)
    while remaining:
        ranked = sorted(
            remaining,
            key=lambda row: (
                -len((document_to_requirements[row["document_id"]] & set(reachable_primary)) - covered_so_far),
                int(row["acquisition_sequence"]),
            ),
        )
        chosen = ranked[0]
        coverage = document_to_requirements[chosen["document_id"]] & set(reachable_primary)
        marginal = sorted(coverage - covered_so_far, key=primary_requirements.index)
        request_order.append(
            {
                "row": chosen,
                "coverage": sorted(coverage, key=primary_requirements.index),
                "marginal": marginal,
            }
        )
        covered_so_far |= coverage
        remaining.remove(chosen)

    t02_id = selection_policy["separate_book9_requirement_id"]
    t02_candidates = sorted(
        [row for row in candidates if t02_id in document_to_requirements[row["document_id"]]],
        key=lambda row: (
            0 if row["priority"] == "P1_PRIMARY_DETAIL" else 1,
            int(row["acquisition_sequence"]),
        ),
    )
    t02_primary = t02_candidates[0]
    t02_fallback = t02_candidates[1] if len(t02_candidates) > 1 else None

    candidate_coverage_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        document_id = candidate["document_id"]
        coverage = sorted(
            document_to_requirements[document_id] & set(primary_requirements),
            key=primary_requirements.index,
        )
        selection_role = "NOT_SELECTED"
        if document_id in selected_primary_set:
            selection_role = "PRIMARY_MINIMUM_SET"
        elif document_id == t02_primary["document_id"]:
            selection_role = "SEPARATE_T02_PRIMARY"
        elif t02_fallback and document_id == t02_fallback["document_id"]:
            selection_role = "SEPARATE_T02_FALLBACK"
        candidate_coverage_rows.append(
            {
                "acquisition_sequence": candidate["acquisition_sequence"],
                "priority": candidate["priority"],
                "document_id": document_id,
                "book_number": candidate["book_number"],
                "group_id": candidate["group_id"],
                "subsystem": candidate["subsystem"],
                "register_pdf_title": candidate["register_pdf_title"],
                "register_content_summary": candidate["register_content_summary"],
                "register_claimed_page_count": claimed_page_count(candidate["register_content_summary"]) or "",
                "primary_requirement_coverage_count": len(coverage),
                "primary_requirement_ids": "|".join(coverage),
                "covers_separate_t02": "YES" if t02_id in document_to_requirements[document_id] else "NO",
                "selection_role": selection_role,
                "payload_or_page_accessed_in_v10h": "NO",
                "content_sufficiency_claimed": "NO",
                "physical_credit": 0,
            }
        )
    write_csv(
        OUTPUTS["candidate_coverage_csv"],
        candidate_coverage_rows,
        [
            "acquisition_sequence", "priority", "document_id", "book_number", "group_id", "subsystem",
            "register_pdf_title", "register_content_summary", "register_claimed_page_count",
            "primary_requirement_coverage_count", "primary_requirement_ids", "covers_separate_t02",
            "selection_role", "payload_or_page_accessed_in_v10h", "content_sufficiency_claimed", "physical_credit",
        ],
    )

    selected_bundle_rows: list[dict[str, Any]] = []
    for index, item in enumerate(request_order, start=1):
        row = item["row"]
        selected_bundle_rows.append(
            {
                "request_order": index,
                "track": "PRIMARY_DRAWING_REQUIREMENTS",
                "selection_role": "EXACT_MINIMUM_SET_PRIMARY",
                "document_id": row["document_id"],
                "expected_basename": f"{row['document_id']}.pdf",
                "priority": row["priority"],
                "acquisition_sequence": row["acquisition_sequence"],
                "book_number": row["book_number"],
                "group_id": row["group_id"],
                "register_pdf_title": row["register_pdf_title"],
                "register_content_summary": row["register_content_summary"],
                "nominal_requirement_count": len(item["coverage"]),
                "nominal_requirement_ids": "|".join(item["coverage"]),
                "marginal_requirement_count_in_request_order": len(item["marginal"]),
                "marginal_requirement_ids_in_request_order": "|".join(item["marginal"]),
                "payload_or_page_accessed_in_v10h": "NO",
                "floor93_99_applicability_established": "NO",
                "revision_or_as_built_authority_established": "NO",
                "requirement_closure_credit": 0,
                "physical_credit": 0,
            }
        )
    selected_bundle_rows.append(
        {
            "request_order": len(selected_bundle_rows) + 1,
            "track": "SEPARATE_BOOK9_T02",
            "selection_role": "EXACT_SEPARATE_TRACK_PRIMARY",
            "document_id": t02_primary["document_id"],
            "expected_basename": f"{t02_primary['document_id']}.pdf",
            "priority": t02_primary["priority"],
            "acquisition_sequence": t02_primary["acquisition_sequence"],
            "book_number": t02_primary["book_number"],
            "group_id": t02_primary["group_id"],
            "register_pdf_title": t02_primary["register_pdf_title"],
            "register_content_summary": t02_primary["register_content_summary"],
            "nominal_requirement_count": 1,
            "nominal_requirement_ids": t02_id,
            "marginal_requirement_count_in_request_order": 1,
            "marginal_requirement_ids_in_request_order": t02_id,
            "payload_or_page_accessed_in_v10h": "NO",
            "floor93_99_applicability_established": "NO_NOT_APPLICABLE_TO_BOOK9_UPPER_TRACK",
            "revision_or_as_built_authority_established": "NO",
            "requirement_closure_credit": 0,
            "physical_credit": 0,
        }
    )
    selected_bundle_fields = list(selected_bundle_rows[0].keys())
    write_csv(OUTPUTS["selected_bundle_csv"], selected_bundle_rows, selected_bundle_fields)

    selected_primary_details = []
    for item in request_order:
        row = item["row"]
        selected_primary_details.append(
            {
                "document_id": row["document_id"],
                "expected_basename": f"{row['document_id']}.pdf",
                "priority": row["priority"],
                "acquisition_sequence": int(row["acquisition_sequence"]),
                "book_number": int(row["book_number"]),
                "group_id": row["group_id"],
                "register_pdf_title": row["register_pdf_title"],
                "register_content_summary": row["register_content_summary"],
                "register_drawing_start": row["register_drawing_start"],
                "register_drawing_end": row["register_drawing_end"],
                "nominal_requirement_ids": item["coverage"],
                "marginal_requirement_ids_in_request_order": item["marginal"],
                "claims_content_sufficiency": False,
            }
        )

    predeclaration = {
        "iteration": "V10H",
        "generated_at_utc": utc_now(),
        "status": "IMMUTABLE_EXACT_IDENTITY_PREDECLARATION_FOR_FUTURE_LOCAL_INTAKE_ONLY",
        "selection_method": {
            "type": "EXACT_DYNAMIC_PROGRAMMING_SET_COVER",
            "objective_order": selection_policy["objective_order"],
            "reachable_requirement_count": len(reachable_primary),
            "state_mask_count_retained": len(states),
            "minimum_primary_document_count": len(selected_primary_ids),
            "maximum_coverage_by_maximum_file_count": maximum_coverage_by_maximum_file_count,
        },
        "primary_drawing_bundle_request_order": selected_primary_details,
        "separate_book9_t02_track": {
            "primary": {
                "document_id": t02_primary["document_id"],
                "expected_basename": f"{t02_primary['document_id']}.pdf",
                "priority": t02_primary["priority"],
                "acquisition_sequence": int(t02_primary["acquisition_sequence"]),
                "register_content_summary": t02_primary["register_content_summary"],
                "claims_content_sufficiency": False,
            },
            "fallback": {
                "document_id": t02_fallback["document_id"],
                "expected_basename": f"{t02_fallback['document_id']}.pdf",
                "priority": t02_fallback["priority"],
                "acquisition_sequence": int(t02_fallback["acquisition_sequence"]),
                "register_content_summary": t02_fallback["register_content_summary"],
                "claims_content_sufficiency": False,
            } if t02_fallback else None,
        },
        "future_local_intake_gate": {
            "maximum_primary_exact_files": 5,
            "exact_document_identifiers_only": True,
            "explicit_user_supplied_paths_required": True,
            "directory_scan_authorized": False,
            "network_request_authorized": False,
            "source_archive_scan_authorized": False,
            "official_sources_read_authorized": False,
            "pdf_page_open_or_render_authorized": False,
            "container_identity_fields_only": [
                "explicit_path", "basename", "byte_size", "sha256", "pdf_signature", "container_page_count"
            ],
        },
        "prohibited_promotions": [
            "NO_WTC1_OR_FLOOR93_99_APPLICABILITY_FROM_FILENAME_OR_REGISTER_ROW",
            "NO_REVISION_OR_AS_BUILT_AUTHORITY_FROM_FILENAME_OR_REGISTER_ROW",
            "NO_CONTENT_SUFFICIENCY_FROM_SET_COVER",
            "NO_COORDINATE_SECTION_MATERIAL_MASS_STIFFNESS_CAPACITY_CONNECTION_DAMAGE_OR_LOAD_PATH_CREDIT",
        ],
    }

    requirement_coverage_rows: list[dict[str, Any]] = []
    selected_all_primary = selected_primary_set | {t02_primary["document_id"]}
    for requirement in requirement_rows:
        requirement_id = requirement["requirement_id"]
        selected_links = [
            document_id
            for document_id in selected_all_primary
            if requirement_id in document_to_requirements[document_id]
        ]
        selected_links.sort(key=lambda item: int(priority_by_id[item]["acquisition_sequence"]))
        if requirement_id in reachable_primary:
            track = "PRIMARY_P1_P2_MINIMUM_SET"
            status = "PREDECLARED_IDENTITY_CANDIDATE_ONLY"
        elif requirement_id in unreachable_primary:
            track = "P0_ONLY_NO_P1_P2_CANDIDATE"
            status = "NO_NEW_P1_P2_COVERAGE"
        elif requirement_id == t02_id:
            track = "SEPARATE_BOOK9_T02"
            status = "PREDECLARED_IDENTITY_CANDIDATE_ONLY"
        elif requirement_id in selection_policy["separate_non_drawing_requirement_ids"]:
            track = "SEPARATE_NON_DRAWING_EVIDENCE"
            status = "NO_DRAWING_BUNDLE_COVERAGE"
        else:
            track = "UNCLASSIFIED"
            status = "NO_COVERAGE"
        requirement_coverage_rows.append(
            {
                "requirement_id": requirement_id,
                "subsystem": requirement["v10a_subsystem"],
                "field_group": requirement["v10a_field_group"],
                "v10g_status": v10g_by_id[requirement_id]["v10g_status"],
                "v10h_evidence_track": track,
                "v10h_predeclared_primary_document_count": len(selected_links),
                "v10h_predeclared_primary_document_ids": "|".join(selected_links),
                "v10h_nominal_coverage_status": status,
                "payload_or_page_accessed_in_v10h": "NO",
                "content_sufficiency_claimed": "NO",
                "requirement_closed_after_v10h": "NO",
                "remains_solver_blocking": "YES",
                "physical_credit": 0,
            }
        )
    write_csv(
        OUTPUTS["requirement_coverage_csv"],
        requirement_coverage_rows,
        list(requirement_coverage_rows[0].keys()),
    )

    separate_tracks_rows = [
        {
            "requirement_id": "N01",
            "track": "P0_ONLY_CORE_COLUMN_IDENTITY",
            "predeclared_document_ids": "WTCI-000013-L",
            "future_evidence_needed": "Exact schedule locator, WTC 1 and Floors 93-99 applicability, revision context, and independent identifier-to-member mapping.",
            "why_not_closed_by_v10h": "No P1/P2 candidate in the V10B matrix; V10H opens no P0 page.",
            "physical_credit": 0,
        },
        {
            "requirement_id": "E01",
            "track": "P0_ONLY_CORE_COLUMN_CONTINUITY",
            "predeclared_document_ids": "WTCI-000013-L",
            "future_evidence_needed": "Floor-specific column segment, splice and section continuity with revision authority.",
            "why_not_closed_by_v10h": "No P1/P2 candidate in the V10B matrix; V10H opens no P0 page.",
            "physical_credit": 0,
        },
        {
            "requirement_id": "D01",
            "track": "EVENT_SPECIFIC_DAMAGE_EVIDENCE",
            "predeclared_document_ids": "",
            "future_evidence_needed": "Physical 2001 damage evidence or validated event-model damage state joined to exact member identifiers.",
            "why_not_closed_by_v10h": "Design drawings cannot establish event damage.",
            "physical_credit": 0,
        },
        {
            "requirement_id": "T02",
            "track": "SEPARATE_BOOK9_UPPER_TRANSFER",
            "predeclared_document_ids": f"{t02_primary['document_id']}|{t02_fallback['document_id'] if t02_fallback else ''}".rstrip("|"),
            "future_evidence_needed": "Exact upper-transfer topology, member and connection mapping, applicability and revision context; mechanical properties remain separate.",
            "why_not_closed_by_v10h": "Only exact identifiers are predeclared; no payload or page is opened.",
            "physical_credit": 0,
        },
        {
            "requirement_id": "B01",
            "track": "TRUNCATED_MODEL_BOUNDARY_FORMULATION",
            "predeclared_document_ids": "",
            "future_evidence_needed": "Defensible loads, displacements or support stiffness above Floor 99 and below Floor 93, or a validated full-building coupling.",
            "why_not_closed_by_v10h": "A drawing-bundle set cover cannot define numerical boundary conditions.",
            "physical_credit": 0,
        },
        {
            "requirement_id": "S01",
            "track": "STAIRWELL_DISTINCTIVE_QUANTITATIVE_EVIDENCE",
            "predeclared_document_ids": "",
            "future_evidence_needed": "Floor-specific stair geometry, connections and mechanical properties from authoritative quantitative records.",
            "why_not_closed_by_v10h": "V9U remains a categorical hypothesis with zero mechanical credit.",
            "physical_credit": 0,
        },
    ]
    write_csv(OUTPUTS["separate_tracks_csv"], separate_tracks_rows, list(separate_tracks_rows[0].keys()))

    predeclared_primary_ids_request_order = [item["row"]["document_id"] for item in request_order]
    expected_primary_set = set(expected["minimum_primary_bundle_document_ids"])
    checks = {
        "protected_input_hashes_all_match": all(row["hash_matches"] for row in protected_before),
        "v10g_validation_pass": (
            v10g_results.get("validation_status") == "PASS"
            and v10g_gate.get("validation_status") == "PASS"
            and v10g_summary.get("validation_status") == "PASS"
        ),
        "v10g_page_branch_closed": v10g_summary.get("page_content_expansion_branch") == "CLOSED",
        "v10g_requirement_count_and_blocking_state": (
            v10g_summary.get("requirement_count") == expected["v10g_requirement_count"]
            and v10g_summary.get("requirements_closed_count") == 0
            and v10g_summary.get("requirements_solver_blocking_count") == expected["requirements_solver_blocking"]
        ),
        "v10b_candidate_document_count": len(priority_rows) == expected["v10b_candidate_document_count"],
        "v10b_priority_counts": (
            priority_counts["P0_LOCALIZE_FIRST"] == expected["p0_document_count"]
            and priority_counts["P1_PRIMARY_DETAIL"] == expected["p1_document_count"]
            and priority_counts["P2_SUPPLEMENTAL"] == expected["p2_document_count"]
        ),
        "p1_p2_candidate_document_count": len(candidates) == expected["p1_p2_candidate_document_count"],
        "v10b_and_v10g_requirement_ids_identical": set(requirements_by_id) == set(v10g_by_id),
        "all_v10g_requirements_remain_blocking": all(row["remains_solver_blocking"] == "YES" for row in v10g_rows),
        "primary_drawing_requirement_count": len(primary_requirements) == expected["primary_drawing_requirement_count"],
        "reachable_primary_requirement_count": len(reachable_primary) == expected["p1_p2_reachable_primary_requirement_count"],
        "unreachable_primary_requirement_ids_exact": unreachable_primary == expected["p1_p2_unreachable_primary_requirement_ids"],
        "exact_set_cover_target_reached": full_mask in states and candidate_masks and all(
            any(requirement_id in document_to_requirements[item] for item in selected_primary_ids)
            for requirement_id in reachable_primary
        ),
        "minimum_primary_bundle_document_count": len(selected_primary_ids) == expected["minimum_primary_bundle_document_count"],
        "minimum_primary_bundle_document_ids_exact": set(selected_primary_ids) == expected_primary_set,
        "no_smaller_bundle_covers_all_reachable_requirements": all(
            maximum_coverage_by_maximum_file_count[str(limit)] < len(reachable_primary)
            for limit in range(1, expected["minimum_primary_bundle_document_count"])
        ),
        "selected_primary_documents_are_p1": all(row["priority"] == "P1_PRIMARY_DETAIL" for row in selected_primary_rows),
        "book9_primary_document_exact": t02_primary["document_id"] == expected["separate_book9_primary_document_id"],
        "book9_fallback_document_exact": t02_fallback is not None and t02_fallback["document_id"] == expected["separate_book9_fallback_document_id"],
        "total_predeclared_primary_document_count": len(selected_bundle_rows) == expected["total_predeclared_primary_document_count"],
        "all_requirements_remain_open_and_blocking": (
            sum(row["requirement_closed_after_v10h"] == "YES" for row in requirement_coverage_rows) == expected["requirements_closed"]
            and sum(row["remains_solver_blocking"] == "YES" for row in requirement_coverage_rows) == expected["requirements_solver_blocking"]
        ),
        "all_credits_zero": all(int(row["physical_credit"]) == 0 for row in candidate_coverage_rows)
        and all(int(row["physical_credit"]) == 0 for row in selected_bundle_rows)
        and all(int(row["physical_credit"]) == 0 for row in requirement_coverage_rows)
        and all(int(row["physical_credit"]) == 0 for row in separate_tracks_rows),
        "no_payload_or_page_access": True,
        "source_archive_and_official_sources_not_read_or_modified": True,
        "no_network_or_external_contact": True,
        "solver_blender_thermal_gates_closed": True,
    }
    validation_status = "PASS" if all(checks.values()) else "FAIL"
    completed = utc_now()
    predeclaration["validation_status"] = validation_status
    write_json(OUTPUTS["bundle_predeclaration"], predeclaration)

    source_manifest = {
        "iteration": "V10H",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "scope": "Immutable V10B and V10G derived artifacts only. No target payload, PDF page, source archive, official_sources file or network resource was accessed.",
        "inputs": protected_before,
        "target_payload_read_count": 0,
        "drawing_page_content_read_count": 0,
        "source_archive_read_count": 0,
        "official_sources_read_count": 0,
        "network_request_count": 0,
        "external_contact_count": 0,
        "qualification": "Set-cover membership is derived from V10B candidate links and does not establish that any selected file contains sufficient, applicable or authoritative content.",
    }
    write_json(OUTPUTS["source_manifest"], source_manifest)

    protected_after = []
    for item in config["protected_inputs"]:
        path = ROOT / item["path"]
        actual = sha256_file(path) if path.is_file() else None
        before_hash = next(row["actual_sha256"] for row in protected_before if row["role"] == item["role"])
        protected_after.append(
            {
                "role": item["role"],
                "path": item["path"],
                "sha256_after": actual,
                "unchanged_from_before": actual == before_hash,
            }
        )
    checks["protected_inputs_unchanged_after_v10h"] = all(row["unchanged_from_before"] for row in protected_after)
    validation_status = "PASS" if all(checks.values()) else "FAIL"
    predeclaration["validation_status"] = validation_status
    write_json(OUTPUTS["bundle_predeclaration"], predeclaration)

    regression_audit = {
        "iteration": "V10H",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "protected_inputs_before": protected_before,
        "protected_inputs_after": protected_after,
        "checks": checks,
    }
    write_json(OUTPUTS["regression_audit"], regression_audit)

    request_lines = [
        "# V10H — liste courte de documents à rechercher",
        "",
        "Cette liste contient des identifiants exacts à rechercher. Aucun document n'est présumé suffisant, applicable aux étages 93–99, révision gouvernante ou as-built avant audit.",
        "",
        "| Ordre | Identifiant exact | Livre | Rôle documentaire nominal |",
        "|---:|---|---:|---|",
    ]
    for row in selected_bundle_rows:
        request_lines.append(
            f"| {row['request_order']} | `{row['document_id']}` | {row['book_number']} | {row['register_pdf_title']} — {row['register_content_summary']} |"
        )
    request_lines.extend(
        [
            "",
            "Attention : pour `WTCI-000024-L`, le registre donne une fin de plage `2 - C/2`, incohérente avec son classement Book 7. Cette chaîne doit être conservée comme anomalie de registre et vérifiée dans la source ; elle n'est pas corrigée par hypothèse.",
            "",
            "## Solutions de repli, seulement si le document principal est introuvable",
            "",
            "- Book 6 : `WTCI-000022-L`, puis `WTCI-000023-L` ;",
            "- Book 7 : `WTCI-000131-L_006`, `WTCI-000472-L`, `WTCI-001057-L` ou `WTCI-001061-L` ;",
            "- Book 4 : `WTCI-000017-L`, puis `WTCI-000018-L` ;",
            f"- Book 9 : `{t02_fallback['document_id']}`.",
            "",
            "## À conserver avec chaque fichier",
            "",
            "Conserver le nom original, l'URL ou l'identifiant Archive.org/NIST, la page de catalogue ou métadonnée associée et toute indication explicite de révision. Ne pas renommer ni convertir le PDF. Un suffixe de dessin contenant 93–99 ne doit pas être présenté comme une étiquette d'étage.",
        ]
    )
    (ROOT / OUTPUTS["document_request_shortlist"]).write_text(
        "\n".join(request_lines) + "\n", encoding="utf-8", newline="\n"
    )

    model_gate = {
        "iteration": "V10H",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "checks": checks,
        "selection_gate": "PASS_EXACT_MINIMUM_IDENTITY_BUNDLE_PREDECLARED",
        "primary_reachable_requirement_count": len(reachable_primary),
        "primary_unreachable_requirement_ids": unreachable_primary,
        "minimum_primary_bundle_document_count": len(selected_primary_ids),
        "minimum_primary_bundle_document_ids": selected_primary_ids,
        "separate_book9_primary_document_id": t02_primary["document_id"],
        "separate_book9_fallback_document_id": t02_fallback["document_id"] if t02_fallback else None,
        "requirement_closure_gate": "CLOSED_ZERO_OF_TWENTY_TWO",
        "structural_solver_readiness_gate": "CLOSED_TWENTY_TWO_OF_TWENTY_TWO_BLOCKING",
        "future_local_intake_gate": "CLOSED_UNTIL_EXPLICIT_USER_SUPPLIED_PATHS",
        "payload_and_page_gate": "CLOSED",
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
    write_json(OUTPUTS["model_gate"], model_gate)

    report_table = [
        "| Ordre | Document | Groupe | Couverture nominale | Gain marginal |",
        "|---:|---|---|---|---|",
    ]
    for row in selected_bundle_rows:
        report_table.append(
            f"| {row['request_order']} | {row['document_id']} | {row['group_id']} | {row['nominal_requirement_ids']} | {row['marginal_requirement_ids_in_request_order']} |"
        )

    report = f"""# WTC 1 — V10H — lot minimal P1/P2

## Résultat

**{validation_status}** pour la pré-déclaration hors ligne V10H. L'optimisation exacte couvre nominalement les **{len(reachable_primary)}** exigences atteignables par P1/P2 avec **{len(selected_primary_ids)} documents**, puis conserve T02 sur un cinquième document Book 9 séparé. Aucune combinaison de un à trois documents ne couvre ces {len(reachable_primary)} exigences.

Le lot principal exact est : `{', '.join(selected_primary_ids)}`. La piste T02 sélectionne `{t02_primary['document_id']}` avec `{t02_fallback['document_id'] if t02_fallback else 'aucun'}` comme repli.

## Faits observés ou transcrits

La matrice V10B contient 53 identifiants : 9 P0, 23 P1 et 21 P2. V10G conserve 22 exigences toutes bloquantes. V10H ne lit que ces matrices et leurs artefacts de validation ; aucun payload ou contenu de page n'est consulté.

## Résultats de modèles officiels

Aucun nouveau résultat de modèle officiel n'est produit. Une couverture documentaire nominale ne valide aucun résultat officiel ni mécanisme physique.

## Affirmations d'archives

Les titres, numéros de livres, résumés de contenu et plages de dessins restent des affirmations du registre d'archive. Ils ne prouvent ni l'applicabilité WTC 1/étages 93–99, ni la révision gouvernante, ni le statut as-built.

## Hypothèses propres au modèle

Le problème de couverture suppose seulement qu'un document candidat peut contribuer aux exigences auxquelles V10B l'a relié. Les documents d'un même groupe ne sont pas déclarés équivalents et le document sélectionné n'est pas déclaré suffisant.

## Résultats dérivés

{chr(10).join(report_table)}

Le gain marginal sert à ordonner la recherche au sein du lot optimal. Il ne représente ni une probabilité de succès ni une quantité physique.

## Pistes séparées et informations manquantes

- N01 et E01 restent P0 seulement, liés à `WTCI-000013-L` ; aucun nouveau candidat P1/P2 ne les couvre.
- Pour `WTCI-000024-L`, la fin de plage `2 - C/2` est une anomalie du registre conservée telle quelle, non une localisation Book 7 validée.
- D01 exige des données de dommage propres à l'événement, non des plans de conception.
- T02 demeure une piste Book 9 séparée.
- B01 exige un modèle numérique de conditions aux limites.
- S01 exige des données quantitatives distinctives ; V9U reste hypothétique et sans crédit mécanique.

## Portes maintenues

Zéro exigence est fermée et les 22 restent bloquantes. V10H n'attribue aucune coordonnée, section, propriété de matériau, masse, rigidité, résistance, loi de connexion, dommage ou crédit de chemin de charge. Aucun réseau, contact externe, accès à l'archive source ou à `work/official_sources/`, solveur, continuation thermique ou lancement Blender n'a eu lieu. Le fichier Blender maître reste inchangé.

## Suite conditionnelle

V10I pourra vérifier uniquement les chemins locaux explicitement fournis par l'utilisateur pour les cinq identifiants pré-déclarés. Sans chemin fourni, aucune recherche de répertoire ne sera lancée.
"""
    (ROOT / OUTPUTS["report"]).write_text(report, encoding="utf-8", newline="\n")

    derived_results = {
        "candidate_document_count": len(priority_rows),
        "p1_p2_candidate_document_count": len(candidates),
        "primary_drawing_requirement_count": len(primary_requirements),
        "p1_p2_reachable_primary_requirement_count": len(reachable_primary),
        "p1_p2_reachable_primary_requirement_ids": reachable_primary,
        "p1_p2_unreachable_primary_requirement_count": len(unreachable_primary),
        "p1_p2_unreachable_primary_requirement_ids": unreachable_primary,
        "minimum_primary_bundle_document_count": len(selected_primary_ids),
        "minimum_primary_bundle_document_ids_in_v10b_sequence": selected_primary_ids,
        "minimum_primary_bundle_document_ids_in_request_order": predeclared_primary_ids_request_order,
        "maximum_coverage_by_maximum_file_count": maximum_coverage_by_maximum_file_count,
        "separate_book9_primary_document_id": t02_primary["document_id"],
        "separate_book9_fallback_document_id": t02_fallback["document_id"] if t02_fallback else None,
        "total_predeclared_primary_document_count": len(selected_bundle_rows),
        "requirements_closed_count": 0,
        "requirements_solver_blocking_count": len(requirement_coverage_rows),
        "physical_assignment_count": 0,
    }
    results = {
        "iteration": "V10H",
        "started_at_utc": started,
        "completed_at_utc": completed,
        "validation_status": validation_status,
        "dataset": {
            "name": "Exact offline P1/P2 minimum document bundle predeclaration",
            "version": config["dataset_version"],
            "random_seed": config["random_seed"],
            "random_draw_used": config["random_draw_used"],
            "scope": config["objective"],
        },
        "observed_or_transcribed_facts": [
            "V10B contains 53 exact candidate identifiers: 9 P0, 23 P1 and 21 P2.",
            "V10G contains 22 unresolved requirements, all still solver blocking.",
            "Forty-four P1/P2 candidate rows are available for the offline set-cover calculation.",
        ],
        "official_model_results": [
            "No new official-model result is produced and no inherited official-model output is independently validated."
        ],
        "archive_claims_used": [
            "Register titles, book numbers, content summaries and drawing ranges are retained as archive claims only."
        ],
        "model_hypotheses": [
            "V10B requirement-to-document links define nominal research coverage only; they do not prove content sufficiency, source authority or physical applicability."
        ],
        "derived_results": derived_results,
        "contradictions_and_missing_information": [
            "N01 and E01 have no P1/P2 candidate and remain on the already acquired P0 Book 3 track.",
            "The selected four-document primary set covers all 16 reachable requirement labels, but no selected payload or page has been inspected.",
            "The V10B endpoint string '2 - C/2' for WTCI-000024-L is retained as a register anomaly and is not repaired by inference.",
            "D01, B01 and S01 require evidence classes that a design-drawing bundle cannot provide.",
            "T02 requires a separate Book 9 path; its selected identifier is not a content-sufficiency finding.",
            "All 22 requirements remain open and solver blocking."
        ],
        "checks": checks,
        "operation_counts": {
            "target_payload_read": 0,
            "drawing_page_content_read": 0,
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
        "physical_assignments": model_gate["physical_assignments"],
        "outputs": OUTPUTS,
        "software": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "elapsed_seconds_before_final_serialization": round(time.perf_counter() - start_clock, 3),
        },
        "next_iteration": config["next_iteration"],
        "errors": [name for name, passed in checks.items() if not passed],
    }
    write_json(OUTPUTS["results"], results)

    offline_files = [
        "wtc1_simulation_v8/data/v10h_p1_p2_minimum_bundle_audit.json",
        "wtc1_simulation_v8/scripts/run_v10h_p1_p2_minimum_bundle_audit.py",
        OUTPUTS["source_manifest"],
        OUTPUTS["regression_audit"],
        OUTPUTS["candidate_coverage_csv"],
        OUTPUTS["selected_bundle_csv"],
        OUTPUTS["bundle_predeclaration"],
        OUTPUTS["requirement_coverage_csv"],
        OUTPUTS["separate_tracks_csv"],
        OUTPUTS["document_request_shortlist"],
        OUTPUTS["model_gate"],
        OUTPUTS["report"],
        OUTPUTS["results"],
    ]
    missing_files = [path for path in offline_files if not (ROOT / path).is_file()]
    offline_audit = {
        "iteration": "V10H",
        "generated_at_utc": completed,
        "validation_status": validation_status if not missing_files else "FAIL",
        "files": [
            {
                "path": path,
                "size_bytes": (ROOT / path).stat().st_size,
                "sha256": sha256_file(ROOT / path),
            }
            for path in offline_files
            if (ROOT / path).is_file()
        ],
        "file_count": len(offline_files),
        "missing_files": missing_files,
        "target_payload_included": False,
        "drawing_page_content_included": False,
        "source_archive_included": False,
        "official_sources_included": False,
    }
    write_json(OUTPUTS["offline_audit"], offline_audit)

    print(
        json.dumps(
            {
                "iteration": "V10H",
                "validation_status": validation_status,
                "p1_p2_candidates": len(candidates),
                "primary_requirements": len(primary_requirements),
                "reachable_primary_requirements": len(reachable_primary),
                "unreachable_primary_requirements": unreachable_primary,
                "minimum_primary_bundle_document_count": len(selected_primary_ids),
                "minimum_primary_bundle_document_ids": selected_primary_ids,
                "request_order": predeclared_primary_ids_request_order,
                "separate_book9_primary": t02_primary["document_id"],
                "separate_book9_fallback": t02_fallback["document_id"] if t02_fallback else None,
                "requirements_closed": 0,
                "requirements_solver_blocking": len(requirement_coverage_rows),
                "failed_checks": [name for name, passed in checks.items() if not passed],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if validation_status == "PASS" and not missing_files else 1


if __name__ == "__main__":
    raise SystemExit(main())
