#!/usr/bin/env python3
"""Build and validate the solver-neutral WTC 1 V10A readiness schema."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10a_solver_neutral_readiness_schema.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_files(files: dict[str, str], label: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for relative_path, expected in files.items():
        path = ROOT / relative_path
        actual = digest(path) if path.is_file() else None
        rows.append(
            {
                "path": relative_path,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "matches": actual == expected,
            }
        )
    failures = [row["path"] for row in rows if not row["matches"]]
    if failures:
        raise RuntimeError(f"{label} hash failure: {failures}")
    return {"count": len(rows), "all_match": True, "files": rows}


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def normalized_edge(edge: list[int] | tuple[int, int]) -> tuple[int, int]:
    a, b = int(edge[0]), int(edge[1])
    return (a, b) if a < b else (b, a)


def yes_no(value: bool) -> str:
    return "YES" if value else "NO"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def build_node_rows(
    floors: list[int],
    columns: list[int],
    boundary_columns: set[int],
    faces_by_column: dict[int, list[str]],
    faces: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for floor in floors:
        for column in columns:
            membership = "|".join(faces_by_column.get(column, []))
            rows.append(
                {
                    "node_id": f"CORE_F{floor}_C{column}",
                    "floor": floor,
                    "subsystem": "core",
                    "role": "core_column_identifier_catalogue",
                    "source_identifier": column,
                    "face": membership,
                    "x": "",
                    "y": "",
                    "z": "",
                    "coordinate_unit": "",
                    "coordinate_status": "NULL_RECONSTRUCTED_V8Q_COORDINATES_EXCLUDED",
                    "evidence_class": "OFFICIAL_MODEL_OUTPUT_DEPENDENT_IDENTIFIER",
                    "source_path": "wtc1_simulation_v8/output/resultats_wtc1_v8q_flux_reseau.json",
                    "official_model_dependency": "YES",
                    "solver_node_authorized": "NO",
                    "missing_required_fields": "as_built_x|as_built_y|floor_elevation_z|coordinate_system|joint_eccentricity",
                }
            )
        rows.append(
            {
                "node_id": f"OFFICE_F{floor}_BOUNDARY",
                "floor": floor,
                "subsystem": "office_floor",
                "role": "office_boundary_requirement_placeholder",
                "source_identifier": "",
                "face": "",
                "x": "",
                "y": "",
                "z": "",
                "coordinate_unit": "",
                "coordinate_status": "NULL_REQUIREMENT_PLACEHOLDER",
                "evidence_class": "DERIVED_REQUIREMENT_RECORD",
                "source_path": "wtc1_simulation_v8/data/v10a_solver_neutral_readiness_schema.json",
                "official_model_dependency": "NO",
                "solver_node_authorized": "NO",
                "missing_required_fields": "physical_node_identity|as_built_xyz|diaphragm_topology|tributary_mapping",
            }
        )
        for face in faces:
            rows.append(
                {
                    "node_id": f"OFFICE_F{floor}_{face.upper()}",
                    "floor": floor,
                    "subsystem": "office_floor",
                    "role": "office_face_requirement_placeholder",
                    "source_identifier": "",
                    "face": face,
                    "x": "",
                    "y": "",
                    "z": "",
                    "coordinate_unit": "",
                    "coordinate_status": "NULL_REQUIREMENT_PLACEHOLDER",
                    "evidence_class": "MODEL_REQUIREMENT_NOT_AS_BUILT_GEOMETRY",
                    "source_path": "wtc1_simulation_v8/data/v8m_core_floor_perimeter_coupling.json",
                    "official_model_dependency": "PARTIAL_CONTEXT_ONLY",
                    "solver_node_authorized": "NO",
                    "missing_required_fields": "physical_node_identity|as_built_xyz|truss_and_slab_mapping|seat_location",
                }
            )
            rows.append(
                {
                    "node_id": f"PERIMETER_F{floor}_{face.upper()}",
                    "floor": floor,
                    "subsystem": "perimeter",
                    "role": "perimeter_face_requirement_placeholder",
                    "source_identifier": "",
                    "face": face,
                    "x": "",
                    "y": "",
                    "z": "",
                    "coordinate_unit": "",
                    "coordinate_status": "NULL_REQUIREMENT_PLACEHOLDER",
                    "evidence_class": "MODEL_REQUIREMENT_NOT_MEMBER_LEVEL_TOPOLOGY",
                    "source_path": "wtc1_simulation_v8/data/v8m_core_floor_perimeter_coupling.json",
                    "official_model_dependency": "PARTIAL_CONTEXT_ONLY",
                    "solver_node_authorized": "NO",
                    "missing_required_fields": "member_ids|as_built_xyz|spandrel_mapping|splice_mapping|damage_state",
                }
            )
    require(all(str(row["source_identifier"]) in {str(value) for value in columns} for row in rows if row["subsystem"] == "core"), "Unexpected core identifier")
    require(all(row["face"] == "" or row["source_identifier"] in boundary_columns or row["subsystem"] != "core" for row in rows), "Core face membership assigned to a non-boundary column")
    return rows


def empty_physical_fields() -> dict[str, str]:
    return {
        "member_section": "",
        "material_id": "",
        "mass": "",
        "length": "",
        "area": "",
        "inertia": "",
        "stiffness": "",
        "capacity": "",
        "damage_state": "",
        "connection_i": "",
        "connection_j": "",
    }


def element_row(
    element_id: str,
    family: str,
    floor_from: int,
    floor_to: int,
    node_i: str,
    node_j: str,
    membership: str,
    topology_status: str,
    official_model_reference: str,
    case_ai_reference: bool,
    evidence_class: str,
    source_path: str,
    missing: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "element_id": element_id,
        "element_family": family,
        "floor_from": floor_from,
        "floor_to": floor_to,
        "node_i": node_i,
        "node_j": node_j,
        "face_or_membership": membership,
        "topology_status": topology_status,
        "official_model_reference": official_model_reference,
        "case_ai_floor96_removed_edge_reference": yes_no(case_ai_reference),
        "evidence_class": evidence_class,
        "source_path": source_path,
        "as_built_assignment": "NO",
    }
    row.update(empty_physical_fields())
    row.update(
        {
            "solver_element_authorized": "NO",
            "missing_required_fields": missing,
        }
    )
    return row


def build_element_rows(
    floors: list[int],
    columns: list[int],
    orthogonal_edges: list[list[int]],
    moment_edges: set[tuple[int, int]],
    damage_edges: set[tuple[int, int]],
    boundary_columns: list[int],
    faces_by_column: dict[int, list[str]],
    faces: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for floor_from, floor_to in zip(floors[:-1], floors[1:]):
        for column in columns:
            rows.append(
                element_row(
                    f"COREVERT_F{floor_from}_F{floor_to}_C{column}",
                    "core_vertical_identifier_continuity",
                    floor_from,
                    floor_to,
                    f"CORE_F{floor_from}_C{column}",
                    f"CORE_F{floor_to}_C{column}",
                    "|".join(faces_by_column.get(column, [])),
                    "IDENTIFIER_CONTINUITY_ONLY",
                    "V8Q_V8P_OFFICIAL_MODEL_IDENTIFIER_CONTINUITY",
                    False,
                    "OFFICIAL_MODEL_OUTPUT_DEPENDENT_REFERENCE",
                    "wtc1_simulation_v8/output/resultats_wtc1_v8q_flux_reseau.json",
                    "as_built_segment|splice|section|material|length|eccentricity|constitutive_law|capacity|damage",
                )
            )
    for floor in floors:
        for edge in orthogonal_edges:
            a, b = normalized_edge(edge)
            is_moment = (a, b) in moment_edges
            is_case_ai = floor == 96 and (a, b) in damage_edges
            reference_parts: list[str] = []
            if is_moment:
                reference_parts.append("V8H_OFFICIAL_MODEL_MOMENT_SUBNETWORK_TRANSCRIPTION")
            if is_case_ai:
                reference_parts.append("V8L_FLOOR96_CASE_AI_REMOVED_EDGE_REFERENCE_ONLY")
            rows.append(
                element_row(
                    f"COREIN_F{floor}_C{a}_C{b}",
                    "core_inplane_official_model_moment_reference" if is_moment else "core_inplane_hypothetical_orthogonal_candidate",
                    floor,
                    floor,
                    f"CORE_F{floor}_C{a}",
                    f"CORE_F{floor}_C{b}",
                    "",
                    "OFFICIAL_MODEL_TOPOLOGY_REFERENCE_NOT_AS_BUILT" if is_moment else "V8Q_RECONSTRUCTION_HYPOTHESIS_ONLY",
                    "|".join(reference_parts),
                    is_case_ai,
                    "OFFICIAL_MODEL_TOPOLOGY_TRANSCRIPTION" if is_moment else "MODEL_HYPOTHESIS_ONLY",
                    "wtc1_simulation_v8/data/v8h_core_beam_network.json" if is_moment else "wtc1_simulation_v8/output/resultats_wtc1_v8q_flux_reseau.json",
                    "physical_member_identity|floor_applicability|section|material|length|connection_law|capacity|physical_damage_state",
                )
            )
        for column in boundary_columns:
            membership = "|".join(faces_by_column[column])
            rows.append(
                element_row(
                    f"COREOFF_F{floor}_C{column}",
                    "core_to_office_algebraic_port_requirement",
                    floor,
                    floor,
                    f"CORE_F{floor}_C{column}",
                    f"OFFICE_F{floor}_BOUNDARY",
                    membership,
                    "V8Q_ALGEBRAIC_PORT_NOT_PHYSICAL_CONNECTION",
                    "V8Q_BALANCE_VARIABLE_ONLY",
                    False,
                    "MODEL_REQUIREMENT_FROM_ALGEBRAIC_HYPOTHESIS",
                    "wtc1_simulation_v8/output/resultats_wtc1_v8q_flux_reseau.json",
                    "actual_truss_or_slab_path|tributary_mapping|compatibility|connection_law|capacity|damage",
                )
            )
        for face in faces:
            rows.append(
                element_row(
                    f"OFFDIST_F{floor}_{face.upper()}",
                    "office_boundary_to_face_distribution_requirement",
                    floor,
                    floor,
                    f"OFFICE_F{floor}_BOUNDARY",
                    f"OFFICE_F{floor}_{face.upper()}",
                    face,
                    "REQUIREMENT_PLACEHOLDER_NOT_DIAPHRAGM_ELEMENT",
                    "",
                    False,
                    "DERIVED_REQUIREMENT_RECORD",
                    "wtc1_simulation_v8/data/v10a_solver_neutral_readiness_schema.json",
                    "floor_specific_topology|diaphragm_stiffness|openings|connections|damage",
                )
            )
            rows.append(
                element_row(
                    f"OFFPER_F{floor}_{face.upper()}",
                    "office_to_perimeter_face_requirement",
                    floor,
                    floor,
                    f"OFFICE_F{floor}_{face.upper()}",
                    f"PERIMETER_F{floor}_{face.upper()}",
                    face,
                    "V8M_FACE_ENVELOPE_NOT_MEMBER_LEVEL_PATH",
                    "V8M_GENERIC_COMPONENT_CONTEXT_ONLY",
                    False,
                    "MODEL_ENVELOPE_REQUIREMENT_NOT_AS_BUILT",
                    "wtc1_simulation_v8/data/v8m_core_floor_perimeter_coupling.json",
                    "truss_ids|slab_strip|interior_seat|exterior_seat|compatibility|constitutive_law|capacity|damage",
                )
            )
    for floor_from, floor_to in zip(floors[:-1], floors[1:]):
        for face in faces:
            rows.append(
                element_row(
                    f"PERIVERT_F{floor_from}_F{floor_to}_{face.upper()}",
                    "perimeter_face_vertical_requirement_placeholder",
                    floor_from,
                    floor_to,
                    f"PERIMETER_F{floor_from}_{face.upper()}",
                    f"PERIMETER_F{floor_to}_{face.upper()}",
                    face,
                    "FACE_PLACEHOLDER_NOT_MEMBER_LEVEL_VERTICAL_TOPOLOGY",
                    "LIMITED_V8M_OFFICIAL_CONTEXT_ONLY",
                    False,
                    "DERIVED_REQUIREMENT_FROM_LIMITED_OFFICIAL_CONTEXT",
                    "wtc1_simulation_v8/data/v8m_core_floor_perimeter_coupling.json",
                    "panel_column_ids|sections|spandrels|splices|connections|material|capacity|damage",
                )
            )
    return rows


def main() -> int:
    started = time.perf_counter()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    config = load_json(CONFIG_PATH)
    require(config["iteration"] == "V10A", "Unexpected iteration in V10A configuration")

    regression_audit = verify_files(config["regression_files"], "V9Z immutable regression")
    cached_input_audit = verify_files(config["cached_input_files"], "V10A cached input")
    protected_before = verify_files(config["protected_files"], "Protected Blender master before V10A")
    require(regression_audit["count"] == config["gates"]["regression_hash_count_expected"], "Regression file count mismatch")
    require(cached_input_audit["count"] == config["gates"]["cached_input_hash_count_expected"], "Cached input count mismatch")

    h = load_json(ROOT / "wtc1_simulation_v8/data/v8h_core_beam_network.json")
    l = load_json(ROOT / "wtc1_simulation_v8/data/v8l_multistory_cold_frame.json")
    m_config = load_json(ROOT / "wtc1_simulation_v8/data/v8m_core_floor_perimeter_coupling.json")
    m_results = load_json(ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v8m_couplage_perimetre_froid.json")
    p = load_json(ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v8p_graphe_vertical.json")
    q_config = load_json(ROOT / "wtc1_simulation_v8/data/v8q_floor_network_flow.json")
    q = load_json(ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v8q_flux_reseau.json")
    r_config = load_json(ROOT / "wtc1_simulation_v8/data/v8r_capacity_bounded_flow.json")
    r = load_json(ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v8r_flux_bornes.json")
    u = load_json(ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v9u_pile_categorielle_escaliers.json")
    u_gate = load_json(ROOT / "wtc1_simulation_v8/output/v9u_stairwell_model_gate.json")

    floors = [int(value) for value in config["schema_definition"]["floors"]]
    faces = [str(value) for value in config["schema_definition"]["faces"]]
    columns = [int(value) for value in q["topology"]["columns"]]
    orthogonal_edges = [[int(value) for value in edge] for edge in q["topology"]["orthogonal_edges"]]
    boundary_columns = [int(value) for value in q["topology"]["boundary_port_columns"]]
    moment_edges = {normalized_edge(edge) for edge in h["moment_beam_topology"]["edges"]}
    damage_edges = {normalized_edge(edge) for edge in l["beam_damage_definition"]["floor96_removed_edges"]}
    face_columns = {face: [int(value) for value in r["topology"]["face_columns"][face]] for face in faces}
    faces_by_column: dict[int, list[str]] = {
        column: [face for face in faces if column in face_columns[face]] for column in boundary_columns
    }

    require(floors == list(range(93, 100)), "V10A floor range must be exactly Floors 93-99")
    require(r_config["floors"] == floors, "V8R floor range differs from V10A")
    require(len(columns) == 47 and len(set(columns)) == 47, "Expected 47 unique V8Q column identifiers")
    require(len(orthogonal_edges) == 79 and len({normalized_edge(edge) for edge in orthogonal_edges}) == 79, "Expected 79 unique V8Q orthogonal edges")
    require(len(boundary_columns) == 24 and len(set(boundary_columns)) == 24, "Expected 24 unique V8Q boundary ports")
    require(len(moment_edges) == 17 and moment_edges.issubset({normalized_edge(edge) for edge in orthogonal_edges}), "V8H moment edge subset mismatch")
    require(len(damage_edges) == 4 and damage_edges.issubset({normalized_edge(edge) for edge in orthogonal_edges}), "V8L Floor 96 Case Ai edge subset mismatch")
    require(r["topology"]["column_count"] == 47 and r["topology"]["orthogonal_edge_count"] == 79, "V8R topology count mismatch")
    require(r["topology"]["boundary_port_columns"] == boundary_columns, "V8R/V8Q boundary ports differ")
    require(q["null_space_audit"]["structural_nullity"] == 56, "V8Q structural nullity changed")
    require(q["null_space_audit"]["variables_with_null_space_support"] == 103, "V8Q null-space-supported flow count changed")
    require(not q["gates"]["mechanical_capacity_gate_passed"], "V8Q mechanical gate unexpectedly open")
    require(not r["summary"]["gates"]["cold_capacity_gate_passed"], "V8R cold capacity gate unexpectedly open")
    require(not any(r["summary"]["any_mapped_case_feasible_by_floor"].values()), "A mapped V8R floor unexpectedly became feasible")
    require(u["validation_status"] == "PASS" and u_gate["validation_status"] == "PASS", "V9U categorical stair regression failed")
    require(u["derived_results"]["instances_per_variant"] == 21 and u["derived_results"]["variant_count"] == 3, "V9U stair record count changed")
    require(not u["model_gate"]["mechanical_properties"] and not u["model_gate"]["load_path_credit"], "V9U stair mechanical gate unexpectedly open")
    require(m_results["summary"]["gate_passed"] is False, "V8M physical gate unexpectedly open")
    require(m_config["analysis"]["hat_truss_cold_credit_kip"] == 0.0, "V8M hat-truss cold credit changed")
    require(q_config["acceptance_gates"]["mechanical_capacity_calibration_required"], "V8Q mechanical calibration requirement missing")

    node_rows = build_node_rows(floors, columns, set(boundary_columns), faces_by_column, faces)
    element_rows = build_element_rows(
        floors,
        columns,
        orthogonal_edges,
        moment_edges,
        damage_edges,
        boundary_columns,
        faces_by_column,
        faces,
    )

    node_fields = [
        "node_id", "floor", "subsystem", "role", "source_identifier", "face", "x", "y", "z",
        "coordinate_unit", "coordinate_status", "evidence_class", "source_path", "official_model_dependency",
        "solver_node_authorized", "missing_required_fields",
    ]
    element_fields = [
        "element_id", "element_family", "floor_from", "floor_to", "node_i", "node_j", "face_or_membership",
        "topology_status", "official_model_reference", "case_ai_floor96_removed_edge_reference", "evidence_class",
        "source_path", "as_built_assignment", "member_section", "material_id", "mass", "length", "area", "inertia",
        "stiffness", "capacity", "damage_state", "connection_i", "connection_j", "solver_element_authorized",
        "missing_required_fields",
    ]
    physical_element_fields = [
        "member_section", "material_id", "mass", "length", "area", "inertia", "stiffness", "capacity",
        "damage_state", "connection_i", "connection_j",
    ]
    node_counts = Counter(row["role"] for row in node_rows)
    element_counts = Counter(row["element_family"] for row in element_rows)
    expected = config["expected_counts"]
    require(len(node_rows) == expected["total_node_catalogue_count"], "Total node catalogue count mismatch")
    require(node_counts["core_column_identifier_catalogue"] == expected["core_node_count"], "Core node count mismatch")
    require(node_counts["office_boundary_requirement_placeholder"] == expected["office_boundary_placeholder_node_count"], "Office boundary node count mismatch")
    require(node_counts["office_face_requirement_placeholder"] == expected["office_face_placeholder_node_count"], "Office face node count mismatch")
    require(node_counts["perimeter_face_requirement_placeholder"] == expected["perimeter_face_placeholder_node_count"], "Perimeter face node count mismatch")
    require(len(element_rows) == expected["total_element_catalogue_count"], "Total element catalogue count mismatch")
    require(element_counts["core_vertical_identifier_continuity"] == expected["core_vertical_element_count"], "Core vertical count mismatch")
    require(element_counts["core_inplane_official_model_moment_reference"] == expected["official_model_moment_inplane_element_count"], "Moment reference count mismatch")
    require(element_counts["core_inplane_hypothetical_orthogonal_candidate"] == expected["hypothetical_orthogonal_inplane_element_count"], "Hypothetical orthogonal count mismatch")
    require(element_counts["core_to_office_algebraic_port_requirement"] == expected["core_to_office_port_requirement_count"], "Core-office port count mismatch")
    require(element_counts["office_boundary_to_face_distribution_requirement"] == expected["office_face_distribution_requirement_count"], "Office distribution count mismatch")
    require(element_counts["office_to_perimeter_face_requirement"] == expected["office_to_perimeter_requirement_count"], "Office-perimeter count mismatch")
    require(element_counts["perimeter_face_vertical_requirement_placeholder"] == expected["perimeter_vertical_placeholder_count"], "Perimeter vertical count mismatch")
    require(all(row["solver_node_authorized"] == "NO" for row in node_rows), "A V10A node was solver-authorized")
    require(all(row["solver_element_authorized"] == "NO" for row in element_rows), "A V10A element was solver-authorized")
    require(all(row["x"] == row["y"] == row["z"] == "" for row in node_rows), "A V10A physical coordinate was assigned")
    require(all(row[field] == "" for row in element_rows for field in physical_element_fields), "A V10A physical property was assigned")
    require(sum(row["case_ai_floor96_removed_edge_reference"] == "YES" for row in element_rows) == 4, "Expected four Floor 96 Case Ai references")

    connection_rows = [
        {
            "connection_id": row["connection_id"],
            "family": row["family"],
            "expected_catalogue_occurrences": row["expected_catalogue_occurrences"],
            "source_status": row["source_status"],
            "required_fields": "|".join(row["required_fields"]),
            "solver_credit": row["solver_credit"],
        }
        for row in config["connection_requirements"]
    ]
    require(len(connection_rows) == expected["connection_requirement_family_count"], "Connection requirement family count mismatch")
    require(all(row["solver_credit"] == "NONE" for row in connection_rows), "A V10A connection family received solver credit")

    official_totals = p["configuration"]["official_core_totals_kip"]
    mapped_by_floor = r["summary"]["any_mapped_case_feasible_by_floor"]
    floor_rows: list[dict[str, Any]] = []
    for floor in floors:
        totals = official_totals[str(floor)]
        floor_rows.append(
            {
                "floor": floor,
                "core_identifier_records": len(columns),
                "official_model_moment_edge_references": len(moment_edges),
                "hypothetical_orthogonal_edge_candidates": len(orthogonal_edges) - len(moment_edges),
                "algebraic_boundary_port_requirements": len(boundary_columns),
                "official_model_before_core_total_kip": totals["before_impact"],
                "official_model_after_core_total_kip": totals["after_impact"],
                "official_totals_evidence_class": "OFFICIAL_MODEL_OUTPUT_DEPENDENT_NOT_APPLIED_LOAD",
                "load_input_authorized": "NO",
                "v8r_any_mapped_bounded_case_feasible": yes_no(bool(mapped_by_floor[str(floor)])),
                "v8r_multiplier_adopted_as_capacity": "NO",
                "floor93_primary_capacity_mapping_missing": yes_no(floor == 93),
                "floor96_case_ai_reference_edge_count": len(damage_edges) if floor == 96 else 0,
                "physical_damage_state_assigned": "NO",
                "categorical_stair_records": 3,
                "stair_variants_kept_separate": "LOW|BASE|HIGH",
                "stair_solver_nodes": 0,
                "stair_solver_elements": 0,
                "floor_solver_ready": "NO",
            }
        )

    source_gate_rows = config["source_gate_requirements"]
    source_gate_counts = Counter(row["status"] for row in source_gate_rows)
    blocking_count = sum(bool(row["blocking"]) for row in source_gate_rows)
    require(len(source_gate_rows) == expected["source_gate_requirement_count"], "Source gate requirement count mismatch")
    require(source_gate_counts == Counter({"MISSING": 10, "PARTIAL_NOT_SOLVER_READY": 9, "DOCUMENTED_REFERENCE_ONLY": 3}), "Unexpected V10A source-gate status counts")
    require(blocking_count == len(source_gate_rows), "Every V10A source gate must remain blocking")
    require(all(entry["assignment_in_v10a"] is None for entry in config["unit_dictionary"]), "A V10A solver unit was assigned")

    checks = {
        "v9z_regression_hashes": regression_audit["all_match"],
        "cached_input_hashes": cached_input_audit["all_match"],
        "protected_blender_master_before": protected_before["all_match"],
        "exact_floor_range_93_99": floors == list(range(93, 100)),
        "v8q_topology_counts_reproduced": len(columns) == 47 and len(orthogonal_edges) == 79 and len(boundary_columns) == 24,
        "v8h_moment_subset_separated": len(moment_edges) == 17,
        "v8l_case_ai_references_not_damage_assignments": sum(row["case_ai_floor96_removed_edge_reference"] == "YES" for row in element_rows) == 4 and all(row["damage_state"] == "" for row in element_rows),
        "v8q_null_space_warning_preserved": q["null_space_audit"]["structural_nullity"] == 56 and q["null_space_audit"]["variables_with_null_space_support"] == 103,
        "v8r_mapped_capacity_gate_preserved_closed": not any(mapped_by_floor.values()),
        "v8r_multipliers_not_adopted": all(row["v8r_multiplier_adopted_as_capacity"] == "NO" for row in floor_rows),
        "node_catalogue_count": len(node_rows) == expected["total_node_catalogue_count"],
        "element_catalogue_count": len(element_rows) == expected["total_element_catalogue_count"],
        "connection_family_count": len(connection_rows) == expected["connection_requirement_family_count"],
        "source_gate_requirement_count": len(source_gate_rows) == expected["source_gate_requirement_count"],
        "all_source_gates_blocking": blocking_count == len(source_gate_rows),
        "all_coordinates_null": all(row["x"] == row["y"] == row["z"] == "" for row in node_rows),
        "all_physical_element_properties_null": all(row[field] == "" for row in element_rows for field in physical_element_fields),
        "all_catalogue_rows_solver_authorized_false": all(row["solver_node_authorized"] == "NO" for row in node_rows) and all(row["solver_element_authorized"] == "NO" for row in element_rows),
        "all_connection_families_zero_credit": all(row["solver_credit"] == "NONE" for row in connection_rows),
        "official_model_outputs_not_applied_as_loads": all(row["load_input_authorized"] == "NO" for row in floor_rows),
        "v9u_stair_records_excluded_from_solver": expected["stairwell_solver_node_count"] == 0 and expected["stairwell_solver_element_count"] == 0 and u["model_gate"]["load_path_credit"] is False,
        "unit_dictionary_has_no_assignments": all(entry["assignment_in_v10a"] is None for entry in config["unit_dictionary"]),
        "source_archive_and_official_sources_not_read": not config["source_policy"]["source_archive_read"] and not config["source_policy"]["official_sources_directory_read"],
        "no_external_contact_or_network": not config["source_policy"]["external_contact_authorized"] and not config["source_policy"]["network_access_authorized"],
        "solver_blender_thermal_gates_closed": not config["source_policy"]["structural_solver_authorized"] and not config["source_policy"]["blender_authorized"] and not config["source_policy"]["thermal_continuation_authorized"],
    }
    require(all(checks.values()), f"V10A validation failure: {[name for name, passed in checks.items() if not passed]}")

    outputs = {name: ROOT / path for name, path in config["outputs"].items()}
    write_csv(outputs["node_catalogue_csv"], node_rows, node_fields)
    write_csv(outputs["element_catalogue_csv"], element_rows, element_fields)
    write_csv(
        outputs["connection_matrix_csv"],
        connection_rows,
        ["connection_id", "family", "expected_catalogue_occurrences", "source_status", "required_fields", "solver_credit"],
    )
    write_csv(
        outputs["floor_matrix_csv"],
        floor_rows,
        list(floor_rows[0]),
    )

    protected_after = verify_files(config["protected_files"], "Protected Blender master after V10A")
    checks["protected_blender_master_after"] = protected_after["all_match"]
    source_manifest = {
        "iteration": "V10A",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "scope": "Hashed cached artifacts only; no source archive, work/official_sources, network or external contact.",
        "regression_files": regression_audit,
        "cached_input_files": cached_input_audit,
        "protected_blender_master_before": protected_before,
        "protected_blender_master_after": protected_after,
        "source_policy": config["source_policy"],
    }
    schema = {
        "iteration": "V10A",
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "scope": config["dataset"]["scope"],
        "epistemic_classes": config["evidence_policy"],
        "schema_rules": config["schema_definition"],
        "catalogue_columns": {"nodes": node_fields, "elements": element_fields},
        "catalogue_counts": {
            "nodes": len(node_rows),
            "elements_or_requirement_relations": len(element_rows),
            "node_roles": dict(sorted(node_counts.items())),
            "element_families": dict(sorted(element_counts.items())),
            "connection_requirement_families": len(connection_rows),
            "source_gate_requirements": len(source_gate_rows),
        },
        "null_assignment_policy": {
            "node_coordinates_all_null": True,
            "element_physical_fields_all_null": physical_element_fields,
            "mass_assignment_count": 0,
            "stiffness_assignment_count": 0,
            "capacity_assignment_count": 0,
            "connection_law_assignment_count": 0,
            "damage_state_assignment_count": 0,
            "load_path_credit_count": 0,
        },
        "official_model_dependency": {
            "core_identifiers": True,
            "moment_subnetwork_references": True,
            "floor_totals_kip": True,
            "floor_totals_applied_as_loads": False,
            "floor96_case_ai_edges_are_reference_flags_only": True,
        },
        "solver_readiness": False,
    }
    unit_dictionary = {
        "iteration": "V10A",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "purpose": "Preserve original unit labels and exact conversion definitions for future use without assigning a solver unit system in V10A.",
        "no_assignments_in_v10a": True,
        "entries": config["unit_dictionary"],
    }
    source_gate_audit = {
        "iteration": "V10A",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "requirement_count": len(source_gate_rows),
        "status_counts": dict(sorted(source_gate_counts.items())),
        "blocking_requirement_count": blocking_count,
        "nonblocking_requirement_count": len(source_gate_rows) - blocking_count,
        "all_solver_readiness_requirements_satisfied": False,
        "requirements": source_gate_rows,
    }
    model_gate = {
        "iteration": "V10A",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "checks": checks,
        "qualification": {
            "documentary_schema_complete": True,
            "catalogue_internal_consistency": True,
            "official_model_dependence_explicit": True,
            "model_hypotheses_explicit": True,
            "as_built_geometry": False,
            "member_sections": False,
            "material_properties": False,
            "connection_laws": False,
            "boundary_conditions": False,
            "physical_damage_states": False,
            "structural_solver_ready": False,
            "structural_solver_executed": False,
            "blender_executed": False,
            "physical_validation": False,
        },
        "decision": "PASS for a solver-neutral documentary readiness schema only. The structural solver gate remains CLOSED because all 22 source requirements are blocking and all physical assignments remain null.",
    }
    results = {
        "iteration": "V10A",
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "run": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "elapsed_seconds_before_final_serialization": round(time.perf_counter() - started, 3),
            "deterministic": True,
            "structural_solver_executed": False,
            "blender_executed": False,
        },
        "random_seed": config["dataset"]["random_seed"],
        "random_draw_used": config["dataset"]["random_draw_used"],
        "scope": config["dataset"]["scope"],
        "input_manifest": relative(outputs["source_manifest"]),
        "output_files": {name: relative(path) for name, path in outputs.items()},
        "observed_or_transcribed_facts": [
            "The 11 selected cached inputs and 12 V9Z regression artifacts match their predeclared SHA-256 values.",
            "V8Q contains 47 core-column identifiers, 79 orthogonal candidate edges and 24 algebraic boundary ports for each of Floors 93-99.",
            "V8H contains 17 moment-subnetwork edge references; V8L contains four Floor 96 Case Ai removed-edge references.",
            "V9U contains 21 categorical floor-stair records per LOW, BASE and HIGH variant and assigns no mechanical properties or load-path credit.",
        ],
        "official_model_results": [
            {
                "source": "V8P transcription of NIST official-model outputs",
                "floor_totals_kip": official_totals,
                "use_in_v10a": "REFERENCE_ONLY_NOT_APPLIED_LOADS",
            },
            {
                "source": "V8H/V8L official-model topology and Case Ai references",
                "moment_edge_reference_count_per_floor": len(moment_edges),
                "floor96_case_ai_removed_edge_reference_count": len(damage_edges),
                "physical_damage_state_assigned": False,
            },
        ],
        "archive_claims_used": [],
        "model_hypotheses": [
            "The 62 V8Q non-moment orthogonal edges per floor remain reconstructed candidates, not as-built beams or slab strips.",
            "The 24 V8Q ports per floor remain algebraic balance variables, not identified physical connections.",
            "Office-boundary, office-face and perimeter-face records are requirement placeholders, not solver nodes or physical discretization.",
            "V8M face paths remain upper-envelope abstractions and do not establish individual trusses, seats, slab strips or perimeter attachments.",
            "LOW, BASE and HIGH stair placements remain separate categorical hypotheses and create zero V10A structural entities.",
        ],
        "derived_results": {
            "floor_count": len(floors),
            "node_catalogue_count": len(node_rows),
            "element_or_requirement_relation_count": len(element_rows),
            "connection_requirement_family_count": len(connection_rows),
            "source_gate_requirement_count": len(source_gate_rows),
            "source_gate_status_counts": dict(sorted(source_gate_counts.items())),
            "blocking_source_gate_count": blocking_count,
            "official_model_moment_edge_reference_count": element_counts["core_inplane_official_model_moment_reference"],
            "hypothetical_orthogonal_edge_candidate_count": element_counts["core_inplane_hypothetical_orthogonal_candidate"],
            "all_physical_assignment_counts": {
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
            "solver_readiness": False,
            "structural_solver_executed": False,
            "blender_executed": False,
        },
        "contradictions_and_missing_information": [
            "V8Q is algebraically balanced but has structural nullity 56; all 103 flow variables have null-space support, so its representative flows are not identified physical transfers.",
            "No mapped bounded V8R case is feasible on any of Floors 93-99. V8R capacity multipliers are sensitivity diagnostics and are not adopted.",
            "Source-qualified as-built coordinates, floor elevations, core and perimeter schedules, office-floor topology, connection laws, boundary conditions and physical damage states are absent from the selected inputs.",
            "The V9U stair repetition is categorical continuity only and is neither observed repeated geometry nor a mechanical path.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    check_lines = "\n".join(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in checks.items())
    report = f"""# WTC 1 - V10A - schema de preparation mecanique neutre au solveur

**Validation generale : PASS**

> PASS DOCUMENTAIRE ET DE SCHEMA UNIQUEMENT - PORTE SOLVEUR FERMEE - ZERO COORDONNEE AS-BUILT - ZERO PROPRIETE MECANIQUE - ZERO ETAT DE DOMMAGE - ZERO CREDIT DE CHEMIN DE CHARGE

## Conclusion

V10A construit un inventaire reproductible de ce qu'exigerait un futur modele sept niveaux du noyau, des planchers de bureaux, du perimetre et de leurs transferts entre les niveaux 93 et 99. Le catalogue contient **{len(node_rows)} enregistrements de noeuds ou emplacements requis** et **{len(element_rows)} relations topologiques ou exigences de liaison**. Aucun de ces enregistrements n'est autorise comme entite solveur.

La validation du schema est PASS, mais la preparation physique est explicitement insuffisante : les **{len(source_gate_rows)} exigences de source** restent toutes bloquantes. Aucun solveur structurel, Blender ou calcul thermique n'a ete lance.

## 1. Faits directement observes ou transcrits

- Les {regression_audit['count']} artefacts de regression V9Z et les {cached_input_audit['count']} entrees cachees V8H, V8L, V8M, V8P, V8Q, V8R et V9U correspondent aux empreintes predeclarees.
- V8Q fournit 47 identifiants de colonnes du noyau, 79 aretes orthogonales candidates et 24 ports algebriques par niveau.
- V8H fournit 17 aretes du sous-reseau de moment. V8L fournit quatre references d'aretes retirees au niveau 96 pour le Case Ai.
- Le Blender maitre conserve exactement son empreinte protegee avant et apres V10A.

## 2. Resultats de modeles officiels

- Les totaux axiaux du noyau avant et apres impact, transcrits par V8P pour chaque niveau 93-99, sont conserves dans la matrice par niveau comme **sorties dependantes du modele officiel**.
- Ces totaux ne sont pas convertis en charges appliquees V10A.
- Les 17 aretes de moment par niveau et les quatre references Case Ai du niveau 96 ne constituent ni une verification as-built, ni des etats de dommage physiques assignes.

## 3. Affirmations provenant des archives

- Aucune archive source n'a ete lue ou rescanee en V10A.
- `work/official_sources/` n'a pas ete lu ni modifie.
- Aucune affirmation d'archive n'est promue en donnee solveur.

## 4. Hypotheses propres au modele

- Les 62 aretes orthogonales non rattachees au sous-reseau de moment, soit {element_counts['core_inplane_hypothetical_orthogonal_candidate']} occurrences sur sept niveaux, restent des reconstructions hypothetiques.
- Les 24 ports V8Q par niveau restent des variables de bilan algebrique, pas des connexions physiques identifiees.
- Les emplacements de face des planchers et du perimetre sont des exigences documentaires, pas une discretisation physique.
- LOW, BASE et HIGH restent trois variantes d'escalier separees, categorielle et hypothetiques. Elles generent zero noeud, zero element et zero credit structurel.

## 5. Resultats derives

- Enregistrements de noeuds/exigences d'emplacement : {len(node_rows)}.
- Relations topologiques/exigences de liaison : {len(element_rows)}.
- Relations verticales du noyau par continuite d'identifiant : {element_counts['core_vertical_identifier_continuity']}.
- References d'aretes de moment : {element_counts['core_inplane_official_model_moment_reference']}.
- Aretes orthogonales hypothetiques : {element_counts['core_inplane_hypothetical_orthogonal_candidate']}.
- Exigences noyau-vers-plancher issues des ports algebriques : {element_counts['core_to_office_algebraic_port_requirement']}.
- Familles d'exigences de connexion : {len(connection_rows)}; credit solveur : aucun.
- Champs de coordonnees, section, materiau, masse, longueur, aire, inertie, rigidite, capacite, loi de connexion et dommage assignes : zero.

## 6. Contradictions et informations manquantes

- V8Q reproduit les bilans algebriques mais conserve une nullite structurelle de 56; les 103 variables de flux sont soutenues par l'espace nul. Ses flux ne sont donc pas des transferts physiques identifies.
- Aucun cas V8R borne et mappe n'est faisable sur un seul des niveaux 93-99. Les multiplicateurs V8R restent des diagnostics de sensibilite et ne sont recopies dans aucune capacite.
- Les coordonnees et elevations as-built, les sections et orientations par niveau, les plans complets de plancher, les assemblages, les conditions aux limites, les lois constitutives et les dommages physiques restent manquants.
- Les resultats generiques V8M ne suffisent pas pour identifier les chemins truss-siege-dalle-perimetre, ni leur compatibilite.

## Portes de validation

{check_lines}

**Decision :** schema documentaire PASS; porte de preparation au solveur **FERMEE**.

## Livrables principaux

- Schema : `{relative(outputs['schema'])}`
- Catalogue de noeuds : `{relative(outputs['node_catalogue_csv'])}`
- Catalogue de relations : `{relative(outputs['element_catalogue_csv'])}`
- Matrice des connexions : `{relative(outputs['connection_matrix_csv'])}`
- Matrice par niveau : `{relative(outputs['floor_matrix_csv'])}`
- Audit des exigences de source : `{relative(outputs['source_gate_audit'])}`
- Porte de preparation solveur : `{relative(outputs['model_gate'])}`

## Etape suivante predeclaree - V10B

{config['next_iteration']['objective']}
"""

    write_json(outputs["source_manifest"], source_manifest)
    write_json(outputs["schema"], schema)
    write_json(outputs["unit_dictionary"], unit_dictionary)
    write_json(outputs["source_gate_audit"], source_gate_audit)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)
    write_text(outputs["report"], report)

    missing_or_empty = [relative(path) for path in outputs.values() if not path.is_file() or path.stat().st_size == 0]
    require(not missing_or_empty, f"V10A output missing or empty: {missing_or_empty}")
    require(verify_files(config["protected_files"], "Protected Blender master final V10A")["all_match"], "Protected Blender master changed")

    elapsed = round(time.perf_counter() - started, 3)
    print(
        json.dumps(
            {
                "iteration": "V10A",
                "status": "PASS",
                "node_catalogue_count": len(node_rows),
                "element_or_requirement_relation_count": len(element_rows),
                "source_gate_requirement_count": len(source_gate_rows),
                "blocking_source_gate_count": blocking_count,
                "solver_readiness": False,
                "physical_assignment_count": 0,
                "solver_executed": False,
                "blender_executed": False,
                "elapsed_seconds": elapsed,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
