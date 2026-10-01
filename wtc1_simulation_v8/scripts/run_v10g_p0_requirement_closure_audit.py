#!/usr/bin/env python3
"""V10G: close the bounded page branch and audit unresolved source requirements.

This iteration reads only previously validated manifests, matrices and gates. It
does not open drawing pages, access the source archive or official_sources, use
the network, assign physical properties, or launch a solver, thermal model or
Blender.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ROOT = SCRIPT_PATH.parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10g_p0_requirement_closure_audit.json"
OUTPUT_DIR = ROOT / "wtc1_simulation_v8/output"

OUTPUTS = {
    "source_manifest": "wtc1_simulation_v8/output/v10g_requirement_source_manifest.json",
    "regression_audit": "wtc1_simulation_v8/output/v10g_regression_audit.json",
    "p0_document_status_csv": "wtc1_simulation_v8/output/v10g_p0_document_status_matrix.csv",
    "requirement_status_csv": "wtc1_simulation_v8/output/v10g_unresolved_requirement_matrix.csv",
    "requirement_summary": "wtc1_simulation_v8/output/v10g_requirement_summary.json",
    "model_gate": "wtc1_simulation_v8/output/v10g_structural_source_gate.json",
    "report": "wtc1_simulation_v8/output/rapport_wtc1_v10g_cloture_exigences_p0.md",
    "results": "wtc1_simulation_v8/output/resultats_wtc1_v10g_cloture_exigences_p0.json",
    "offline_audit": "wtc1_simulation_v8/output/v10g_offline_package_audit.json",
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


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "1"}


def pipe_list(value: str) -> list[str]:
    return [item for item in value.split("|") if item]


def requirement_missing_evidence(requirement_id: str, field_group: str, has_p0: bool) -> str:
    fixed = {
        "D01": "Physical 2001 event-damage evidence joined to identified members; design drawings cannot close this field.",
        "T02": "Exact Book 9 upper-transfer drawings, floor applicability, revision context, joined topology and separate mechanical properties.",
        "B01": "A defensible truncated-model boundary formulation above Floor 99 and below Floor 93, including loads, displacements or support stiffness.",
        "S01": "Distinctive quantitative stairwell geometry, connections and mechanical properties; V9U remains categorical and zero-credit.",
    }
    if requirement_id in fixed:
        return fixed[requirement_id]
    prefix = "The P0 payload identity is available, but " if has_p0 else "No P0 payload candidate exists, and "
    return (
        prefix
        + "an exact WTC 1/Floors 93-99 drawing locator, applicable revision authority, requirement-specific content transcription "
        + f"and independent solver-ready evidence for {field_group} remain absent."
    )


def main() -> int:
    started = utc_now()
    start_clock = time.perf_counter()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = read_json(CONFIG_PATH)
    expected = config["expected_counts"]
    p0_ids = config["p0_document_ids"]
    p0_set = set(p0_ids)

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

    paths_by_role = {item["role"]: ROOT / item["path"] for item in config["protected_inputs"]}
    requirement_rows = read_csv(paths_by_role["v10b_requirement_matrix"])
    priority_rows = read_csv(paths_by_role["v10b_priority_matrix"])
    v10d_manifest = read_json(paths_by_role["v10d_working_copy_manifest"])
    v10e_rows = read_csv(paths_by_role["v10e_index_locator_matrix"])
    v10f_floor_rows = read_csv(paths_by_role["v10f_floor_locator_matrix"])
    v10f_results = read_json(paths_by_role["v10f_results"])
    v10f_gate = read_json(paths_by_role["v10f_gate"])

    priority_counts = Counter(row["priority"] for row in priority_rows)
    p0_priority_rows = [row for row in priority_rows if row["priority"] == "P0_LOCALIZE_FIRST"]
    p0_priority_by_id = {row["document_id"]: row for row in p0_priority_rows}
    manifest_by_id = {row["document_id"]: row for row in v10d_manifest["files"]}
    v10e_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in v10e_rows:
        v10e_by_id[row["document_id"]].append(row)
    v10f_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in v10f_floor_rows:
        v10f_by_id[row["document_id"]].append(row)

    requirement_links: dict[str, list[str]] = defaultdict(list)
    for row in requirement_rows:
        for document_id in pipe_list(row["candidate_document_ids"]):
            requirement_links[document_id].append(row["requirement_id"])

    p0_status_rows: list[dict[str, Any]] = []
    for document_id in p0_ids:
        priority = p0_priority_by_id[document_id]
        manifest = manifest_by_id[document_id]
        local_path = ROOT / manifest["destination_path"]
        index_rows = v10e_by_id.get(document_id, [])
        followup_rows = v10f_by_id.get(document_id, [])
        p0_status_rows.append(
            {
                "acquisition_sequence": priority["acquisition_sequence"],
                "document_id": document_id,
                "book_number": priority["book_number"],
                "group_id": priority["group_id"],
                "subsystem": priority["subsystem"],
                "v10d_working_copy_status": manifest["copy_status"],
                "v10d_manifest_sha256": manifest["sha256"],
                "v10d_manifest_size_bytes": manifest["size_bytes"],
                "local_file_exists": "YES" if local_path.is_file() else "NO",
                "local_file_size_matches_manifest": "YES" if local_path.is_file() and local_path.stat().st_size == manifest["size_bytes"] else "NO",
                "payload_hash_reverified_in_v10g": "NO_MANIFEST_CHAIN_ONLY",
                "v10e_bounded_index_rows": len(index_rows),
                "v10e_explicit_floor93_99_locator": "YES" if any(truthy(row["exact_floor_locator_on_same_candidate_page"]) for row in index_rows) else "NO",
                "v10f_floor_audit_rows": len(followup_rows),
                "v10f_followup_status": (
                    "BOUNDED_CROSS_REFERENCE_FOLLOWUP_COMPLETE_NO_TARGET_FLOOR_LOCATOR"
                    if followup_rows
                    else "NO_SECOND_WINDOW_TRIGGER_FROM_V10E"
                ),
                "v10f_explicit_floor93_99_locator": "YES" if any(truthy(row["exact_floor_locator_documented_in_v10f_window"]) for row in followup_rows) else "NO",
                "floor93_99_applicability": "NOT_ESTABLISHED",
                "revision_or_as_built_authority": "NOT_ESTABLISHED",
                "drawing_geometry_or_property_content_transcribed": "NO",
                "linked_requirement_count": len(requirement_links[document_id]),
                "linked_requirement_ids": "|".join(requirement_links[document_id]),
                "v10g_documentary_status": "LOCAL_HASH_VERIFIED_CONTAINER_PLUS_BOUNDED_LOCATOR_ONLY",
                "requirement_closure_credit": 0,
                "physical_credit": 0,
            }
        )

    p0_document_fields = [
        "acquisition_sequence",
        "document_id",
        "book_number",
        "group_id",
        "subsystem",
        "v10d_working_copy_status",
        "v10d_manifest_sha256",
        "v10d_manifest_size_bytes",
        "local_file_exists",
        "local_file_size_matches_manifest",
        "payload_hash_reverified_in_v10g",
        "v10e_bounded_index_rows",
        "v10e_explicit_floor93_99_locator",
        "v10f_floor_audit_rows",
        "v10f_followup_status",
        "v10f_explicit_floor93_99_locator",
        "floor93_99_applicability",
        "revision_or_as_built_authority",
        "drawing_geometry_or_property_content_transcribed",
        "linked_requirement_count",
        "linked_requirement_ids",
        "v10g_documentary_status",
        "requirement_closure_credit",
        "physical_credit",
    ]
    write_csv(OUTPUTS["p0_document_status_csv"], p0_status_rows, p0_document_fields)

    special = config["non_p0_requirement_dispositions"]
    requirement_status_rows: list[dict[str, Any]] = []
    for row in requirement_rows:
        requirement_id = row["requirement_id"]
        candidate_ids = pipe_list(row["candidate_document_ids"])
        linked_p0 = [item for item in p0_ids if item in candidate_ids]
        if requirement_id in special:
            status = special[requirement_id]
        elif linked_p0:
            status = "UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY"
        else:
            status = "UNRESOLVED_NO_P0_CANDIDATE"
        requirement_status_rows.append(
            {
                "requirement_id": requirement_id,
                "subsystem": row["v10a_subsystem"],
                "field_group": row["v10a_field_group"],
                "v10a_status": row["v10a_status"],
                "v10a_evidence_class": row["v10a_evidence_class"],
                "candidate_groups": row["candidate_groups"],
                "candidate_document_count": row["candidate_document_count"],
                "p0_candidate_document_count": len(linked_p0),
                "p0_candidate_document_ids": "|".join(linked_p0),
                "p0_payload_identity_available": "YES" if linked_p0 else "NO_NOT_APPLICABLE",
                "p0_bounded_locator_review_complete": "YES" if linked_p0 and all(v10e_by_id.get(item) for item in linked_p0) else "NO_NOT_APPLICABLE",
                "exact_wtc1_floor93_99_applicability": "NOT_ESTABLISHED",
                "revision_or_as_built_authority": "NOT_ESTABLISHED",
                "requirement_specific_drawing_content_transcribed": "NO",
                "v10g_status": status,
                "missing_closure_evidence": requirement_missing_evidence(
                    requirement_id, row["v10a_field_group"], bool(linked_p0)
                ),
                "requirement_closed_after_v10g": "NO",
                "remains_solver_blocking": "YES",
                "coordinates_assigned": 0,
                "member_sections_assigned": 0,
                "materials_assigned": 0,
                "mass_assigned": 0,
                "stiffness_assigned": 0,
                "capacity_assigned": 0,
                "connection_laws_assigned": 0,
                "damage_states_assigned": 0,
                "load_path_credit": 0,
            }
        )

    requirement_fields = [
        "requirement_id",
        "subsystem",
        "field_group",
        "v10a_status",
        "v10a_evidence_class",
        "candidate_groups",
        "candidate_document_count",
        "p0_candidate_document_count",
        "p0_candidate_document_ids",
        "p0_payload_identity_available",
        "p0_bounded_locator_review_complete",
        "exact_wtc1_floor93_99_applicability",
        "revision_or_as_built_authority",
        "requirement_specific_drawing_content_transcribed",
        "v10g_status",
        "missing_closure_evidence",
        "requirement_closed_after_v10g",
        "remains_solver_blocking",
        "coordinates_assigned",
        "member_sections_assigned",
        "materials_assigned",
        "mass_assigned",
        "stiffness_assigned",
        "capacity_assigned",
        "connection_laws_assigned",
        "damage_states_assigned",
        "load_path_credit",
    ]
    write_csv(OUTPUTS["requirement_status_csv"], requirement_status_rows, requirement_fields)

    p0_linked = [row for row in requirement_status_rows if int(row["p0_candidate_document_count"]) > 0]
    no_p0 = [row for row in requirement_status_rows if int(row["p0_candidate_document_count"]) == 0]
    closed = [row for row in requirement_status_rows if row["requirement_closed_after_v10g"] == "YES"]
    blocking = [row for row in requirement_status_rows if row["remains_solver_blocking"] == "YES"]
    status_counts = Counter(row["v10g_status"] for row in requirement_status_rows)

    checks = {
        "protected_input_hashes_all_match": all(row["hash_matches"] for row in protected_before),
        "v10f_validation_pass": v10f_results.get("validation_status") == "PASS" and v10f_gate.get("validation_status") == "PASS",
        "v10f_page_content_expansion_branch_closed": v10f_results["locator_summary"]["page_content_expansion_branch_closed"] is True,
        "v10f_return_gate_exact": v10f_gate.get("v10g_content_expansion_gate") == "CLOSED_RETURN_TO_PRIORITIZED_ACQUISITION_MATRIX",
        "v10b_requirement_row_count": len(requirement_rows) == expected["v10b_requirement_rows"],
        "v10b_candidate_document_count": len(priority_rows) == expected["v10b_candidate_documents"],
        "v10b_priority_counts": (
            priority_counts["P0_LOCALIZE_FIRST"] == expected["p0_documents"]
            and priority_counts["P1_PRIMARY_DETAIL"] == expected["p1_documents"]
            and priority_counts["P2_SUPPLEMENTAL"] == expected["p2_documents"]
        ),
        "p0_document_ids_exact_and_ordered": [row["document_id"] for row in p0_priority_rows] == p0_ids,
        "v10d_manifest_validation_pass": v10d_manifest.get("validation_status") == "PASS",
        "v10d_working_copy_count": v10d_manifest.get("accepted_working_copy_count") == expected["v10d_local_working_copies"],
        "v10d_manifest_p0_ids_exact": set(manifest_by_id) == p0_set,
        "v10d_working_copy_files_exist_and_sizes_match": all(
            row["local_file_exists"] == "YES" and row["local_file_size_matches_manifest"] == "YES" for row in p0_status_rows
        ),
        "v10e_index_transcription_row_count": len(v10e_rows) == expected["v10e_index_transcription_rows"],
        "all_p0_documents_have_v10e_bounded_review": set(v10e_by_id) == p0_set,
        "v10e_no_exact_target_floor_locator": not any(truthy(row["exact_floor_locator_on_same_candidate_page"]) for row in v10e_rows),
        "v10f_exact_target_floor_locator_count_zero": (
            v10f_results["locator_summary"]["exact_floor93_99_locator_candidate_count"]
            == expected["v10f_exact_floor93_99_locator_candidates"]
            and not any(truthy(row["exact_floor_locator_documented_in_v10f_window"]) for row in v10f_floor_rows)
        ),
        "all_v10a_requirement_ids_retained_once": len({row["requirement_id"] for row in requirement_status_rows}) == len(requirement_status_rows) == expected["v10b_requirement_rows"],
        "p0_linked_requirement_count": len(p0_linked) == expected["p0_linked_requirements"],
        "requirements_without_p0_candidate_count": len(no_p0) == expected["requirements_without_p0_candidate"],
        "requirements_closed_count_zero": len(closed) == expected["requirements_closed"],
        "all_requirements_remain_solver_blocking": len(blocking) == expected["requirements_solver_blocking"],
        "all_document_and_requirement_credit_zero": all(
            int(row["physical_credit"]) == 0 and int(row["requirement_closure_credit"]) == 0 for row in p0_status_rows
        ) and all(
            all(int(row[field]) == 0 for field in [
                "coordinates_assigned", "member_sections_assigned", "materials_assigned", "mass_assigned",
                "stiffness_assigned", "capacity_assigned", "connection_laws_assigned", "damage_states_assigned", "load_path_credit"
            ]) for row in requirement_status_rows
        ),
        "no_new_page_content_read_or_transcribed": True,
        "source_archive_and_official_sources_not_read_or_modified": True,
        "no_network_or_external_contact": True,
        "solver_blender_thermal_gates_closed": True,
    }

    validation_status = "PASS" if all(checks.values()) else "FAIL"
    completed = utc_now()

    source_manifest = {
        "iteration": "V10G",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "scope": "Previously validated derived manifests, matrices and gates only; no drawing page, source archive, official_sources file or network resource was opened.",
        "inputs": protected_before,
        "source_archive_read_count": 0,
        "official_sources_read_count": 0,
        "drawing_page_content_read_count": 0,
        "network_request_count": 0,
        "external_contact_count": 0,
        "qualification": "A chained hash confirms artifact identity, not the truth, authority, revision or as-built applicability of the underlying archive claim.",
    }
    write_json(OUTPUTS["source_manifest"], source_manifest)

    protected_after = []
    for item in config["protected_inputs"]:
        path = ROOT / item["path"]
        actual = sha256_file(path) if path.is_file() else None
        protected_after.append(
            {
                "role": item["role"],
                "path": item["path"],
                "sha256_after": actual,
                "unchanged_from_before": actual == next(row["actual_sha256"] for row in protected_before if row["role"] == item["role"]),
            }
        )
    checks["protected_inputs_unchanged_after_v10g"] = all(row["unchanged_from_before"] for row in protected_after)
    validation_status = "PASS" if all(checks.values()) else "FAIL"

    regression_audit = {
        "iteration": "V10G",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "protected_inputs_before": protected_before,
        "protected_inputs_after": protected_after,
        "checks": checks,
    }
    write_json(OUTPUTS["regression_audit"], regression_audit)

    summary = {
        "iteration": "V10G",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "candidate_document_count": len(priority_rows),
        "priority_counts": dict(sorted(priority_counts.items())),
        "p0_document_count": len(p0_status_rows),
        "p0_local_identity_available_count": sum(row["local_file_exists"] == "YES" for row in p0_status_rows),
        "p0_exact_floor93_99_applicability_count": 0,
        "p0_revision_or_as_built_authority_count": 0,
        "requirement_count": len(requirement_status_rows),
        "p0_linked_requirement_count": len(p0_linked),
        "requirements_without_p0_candidate_count": len(no_p0),
        "requirements_without_p0_candidate_ids": [row["requirement_id"] for row in no_p0],
        "requirement_status_counts": dict(sorted(status_counts.items())),
        "requirements_closed_count": len(closed),
        "requirements_solver_blocking_count": len(blocking),
        "physical_assignment_count": 0,
        "page_content_expansion_branch": "CLOSED",
        "next_permitted_action": "OFFLINE_P1_P2_MINIMUM_BUNDLE_PREDECLARATION_ONLY",
    }
    write_json(OUTPUTS["requirement_summary"], summary)

    physical_assignments = {
        "coordinates": 0,
        "member_sections": 0,
        "materials": 0,
        "mass": 0,
        "stiffness": 0,
        "capacity": 0,
        "connection_laws": 0,
        "damage_states": 0,
        "load_path_credit": 0,
    }
    model_gate = {
        "iteration": "V10G",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "checks": checks,
        "branch_decision": "V10F_PAGE_CONTENT_EXPANSION_CLOSED_RETURNED_TO_V10B_MATRIX",
        "p0_payload_identity_gate": "OPEN_FOR_NINE_LOCAL_MANIFEST_CHAINED_COPIES_ONLY",
        "wtc1_floor93_99_applicability_gate": "CLOSED_NOT_ESTABLISHED",
        "revision_as_built_authority_gate": "CLOSED_NOT_ESTABLISHED",
        "requirement_closure_gate": "CLOSED_ZERO_OF_TWENTY_TWO",
        "structural_solver_readiness_gate": "CLOSED_TWENTY_TWO_OF_TWENTY_TWO_BLOCKING",
        "p1_p2_predeclaration_gate": "OPEN_FOR_OFFLINE_SELECTION_ONLY",
        "drawing_page_content_gate": "CLOSED",
        "network_gate": "CLOSED",
        "source_archive_gate": "CLOSED",
        "official_sources_gate": "CLOSED",
        "thermal_continuation_gate": "CLOSED",
        "blender_gate": "CLOSED",
        "physical_assignments": physical_assignments,
        "physical_validation": False,
    }
    write_json(OUTPUTS["model_gate"], model_gate)

    table_lines = [
        "| Exigence | Sous-système | Champ | Statut V10G | P0 liés | Blocage |",
        "|---|---|---|---|---:|---|",
    ]
    for row in requirement_status_rows:
        table_lines.append(
            f"| {row['requirement_id']} | {row['subsystem']} | {row['field_group']} | {row['v10g_status']} | {row['p0_candidate_document_count']} | OUI |"
        )

    report = f"""# WTC 1 — V10G — clôture de la branche P0 et état des exigences

## Résultat

**{validation_status}** pour l'audit de synthèse V10G. La branche de lecture de pages ouverte en V10E/V10F est fermée : V10F n'a documenté aucun couple exact « étage 93–99 + page ou dessin ». Les neuf documents P0 disposent d'une identité locale chaînée par manifeste et d'un audit borné de localisateurs, mais cela ne ferme aucune exigence mécanique.

- documents candidats V10B : **{len(priority_rows)}** (P0 : {priority_counts['P0_LOCALIZE_FIRST']}, P1 : {priority_counts['P1_PRIMARY_DETAIL']}, P2 : {priority_counts['P2_SUPPLEMENTAL']}) ;
- documents P0 locaux enregistrés : **{len(p0_status_rows)}** ;
- exigences liées à au moins un P0 : **{len(p0_linked)}** ;
- exigences sans candidat P0 : **{len(no_p0)}** ({', '.join(row['requirement_id'] for row in no_p0)}) ;
- exigences fermées : **{len(closed)}/22** ;
- exigences encore bloquantes pour un solveur : **{len(blocking)}/22**.

## Faits observés ou transcrits antérieurement

V10D enregistre neuf copies de travail avec taille et SHA-256. V10E enregistre 29 transcriptions bornées de pages d'index. V10F enregistre zéro localisateur exact pour les étages 93 à 99 et ferme explicitement l'expansion de contenu. V10G ne relit aucune page de dessin : il ne lit que les matrices, manifestes et portes déjà validés.

## Résultats de modèles officiels

Aucun nouveau résultat de modèle officiel n'est produit. Les références V10A restent des dépendances documentaires et ne sont pas converties en validation indépendante.

## Affirmations d'archives

Les intitulés, numéros de livres, étiquettes de tour et plages de dessins viennent du registre d'archive déjà audité. V10G ne confirme ni leur autorité de révision, ni leur statut as-built, ni leur applicabilité exacte au WTC 1 et aux étages 93–99.

## Hypothèses propres au modèle

Le lien entre une famille documentaire et une exigence est une priorité de recherche, pas une preuve que le document contient la donnée requise. Les priorités P0/P1/P2 ne sont ni des probabilités ni des niveaux d'authenticité.

## Résultats dérivés

Les neuf P0 couvrent au moins nominalement 18 exigences, mais seulement au niveau identité de contenant et localisateurs bornés. D01 exige des données de dommage liées à l'événement, T02 suit une piste séparée Book 9, B01 exige un modèle de frontières et S01 conserve zéro crédit mécanique. Ainsi, **0/22** exigence est fermée et le solveur reste interdit.

## Matrice des 22 exigences

{chr(10).join(table_lines)}

## Contradictions et informations manquantes

- Une copie locale hachée ne prouve pas l'identité WTC 1, l'applicabilité aux étages 93–99, la révision gouvernante ou le statut as-built.
- Les localisateurs bornés ne fournissent ni coordonnées, ni sections, ni propriétés de matériau, ni lois de connexion.
- Les plans de conception ne peuvent pas établir seuls le dommage physique du 11 septembre 2001.
- Les conditions aux limites du modèle tronqué 93–99 restent indéfinies.
- La couche d'escaliers V9U reste catégorielle, hypothétique et sans crédit mécanique.

## Interdictions maintenues

V10G attribue zéro coordonnée as-built, section, matériau, masse, rigidité, résistance, loi de connexion, dommage ou crédit de chemin de charge. Aucun accès réseau, contact externe, lecture de l'archive source ou de `work/official_sources/`, solveur, continuation thermique ou lancement Blender n'a eu lieu. Le fichier Blender maître reste inchangé.

## Prochaine itération

V10H pourra seulement pré-déclarer hors ligne le plus petit lot exact P1/P2 maximisant la couverture marginale des exigences dépendantes de dessins, tout en maintenant D01, B01 et S01 sur des pistes de preuve séparées et T02 sur la piste Book 9. Aucun payload ou page ne devra être ouvert pendant cette pré-déclaration.
"""
    report_path = ROOT / OUTPUTS["report"]
    report_path.write_text(report, encoding="utf-8", newline="\n")

    results = {
        "iteration": "V10G",
        "started_at_utc": started,
        "completed_at_utc": completed,
        "validation_status": validation_status,
        "dataset": {
            "name": "P0 requirement closure audit after bounded locator branch closure",
            "version": config["dataset_version"],
            "random_seed": config["random_seed"],
            "random_draw_used": config["random_draw_used"],
            "scope": config["objective"],
        },
        "observed_or_transcribed_facts": [
            "The immutable V10B matrix contains 53 candidate documents and 22 source requirements.",
            "The chained V10D manifest records nine accepted P0 working copies; V10G verifies file presence and byte size but does not reopen or rehash their drawing content.",
            "The V10E locator matrix contains 29 bounded index-page transcription rows across all nine P0 documents.",
            "V10F records zero exact Floor 93-99 locator and explicitly closes further page-content expansion.",
        ],
        "official_model_results": [
            "No new official-model result is created; inherited official-model-dependent fields remain documentary dependencies rather than independent validation."
        ],
        "archive_claims_used": [
            "Previously audited archive-register titles, book numbers, tower labels and drawing ranges are retained as archive claims only."
        ],
        "model_hypotheses": [
            "Requirement-to-document-family links and P0/P1/P2 priorities are research-workflow hypotheses, not proof of content, authority or physical applicability."
        ],
        "derived_results": summary,
        "contradictions_and_missing_information": [
            "Local payload identity does not establish exact WTC 1/Floors 93-99 applicability, governing revision or as-built authority.",
            "No requirement-specific drawing content is transcribed, so coordinates, topology, sections and connections remain unavailable for solver assignment.",
            "Event damage, truncated-model boundaries and stairwell mechanical data require separate evidence classes.",
            "All 22 structural source requirements remain solver blocking."
        ],
        "checks": checks,
        "operation_counts": {
            "source_archive_read": 0,
            "source_archive_write": 0,
            "official_sources_read": 0,
            "official_sources_write": 0,
            "drawing_page_content_read": 0,
            "network_request": 0,
            "external_contact": 0,
            "structural_solver_run": 0,
            "thermal_model_run": 0,
            "blender_launch": 0,
            "blender_master_write": 0,
        },
        "physical_assignments": physical_assignments,
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
        "wtc1_simulation_v8/data/v10g_p0_requirement_closure_audit.json",
        "wtc1_simulation_v8/scripts/run_v10g_p0_requirement_closure_audit.py",
        OUTPUTS["source_manifest"],
        OUTPUTS["regression_audit"],
        OUTPUTS["p0_document_status_csv"],
        OUTPUTS["requirement_status_csv"],
        OUTPUTS["requirement_summary"],
        OUTPUTS["model_gate"],
        OUTPUTS["report"],
        OUTPUTS["results"],
    ]
    offline_audit = {
        "iteration": "V10G",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "files": [
            {
                "path": path,
                "size_bytes": (ROOT / path).stat().st_size,
                "sha256": sha256_file(ROOT / path),
            }
            for path in offline_files
        ],
        "file_count": len(offline_files),
        "missing_files": [path for path in offline_files if not (ROOT / path).is_file()],
        "source_archive_included": False,
        "official_sources_included": False,
        "drawing_payload_included": False,
    }
    write_json(OUTPUTS["offline_audit"], offline_audit)

    print(json.dumps({
        "iteration": "V10G",
        "validation_status": validation_status,
        "p0_documents": len(p0_status_rows),
        "p0_linked_requirements": len(p0_linked),
        "requirements_closed": len(closed),
        "requirements_solver_blocking": len(blocking),
        "page_content_expansion_branch": "CLOSED",
        "outputs": OUTPUTS,
        "failed_checks": [name for name, passed in checks.items() if not passed],
    }, ensure_ascii=False, indent=2))
    return 0 if validation_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
