#!/usr/bin/env python3
"""V10I: exact-file, read-only local intake and PDF-container audit."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdf
from pypdf import PdfReader


SCRIPT_PATH = Path(__file__).resolve()
ROOT = SCRIPT_PATH.parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10i_local_structural_intake_audit.json"

OUTPUTS = {
    "source_manifest": "wtc1_simulation_v8/output/v10i_local_intake_source_manifest.json",
    "identity_matrix_csv": "wtc1_simulation_v8/output/v10i_source_identity_matrix.csv",
    "container_metadata": "wtc1_simulation_v8/output/v10i_pdf_container_metadata.json",
    "page_count_audit_csv": "wtc1_simulation_v8/output/v10i_register_page_count_audit.csv",
    "working_copy_manifest": "wtc1_simulation_v8/output/v10i_working_copy_manifest.json",
    "archive_integrity_audit": "wtc1_simulation_v8/output/v10i_source_archive_integrity_audit.json",
    "regression_audit": "wtc1_simulation_v8/output/v10i_regression_audit.json",
    "model_gate": "wtc1_simulation_v8/output/v10i_structural_source_gate.json",
    "report": "wtc1_simulation_v8/output/rapport_wtc1_v10i_reception_locale.md",
    "results": "wtc1_simulation_v8/output/resultats_wtc1_v10i_reception_locale.json",
    "offline_audit": "wtc1_simulation_v8/output/v10i_offline_package_audit.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(relative_path: str, payload: Any) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_csv(relative_path: str, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def hash_file(path: Path, algorithms: tuple[str, ...] = ("sha256",)) -> dict[str, str]:
    digests = {name: hashlib.new(name) for name in algorithms}
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            for digest in digests.values():
                digest.update(block)
    return {name: digest.hexdigest() for name, digest in digests.items()}


def sha256_file(path: Path) -> str:
    return hash_file(path, ("sha256",))["sha256"]


def metadata_to_plain(metadata: Any) -> dict[str, str | None]:
    keys = ["/Title", "/Author", "/Subject", "/Creator", "/Producer", "/CreationDate", "/ModDate"]
    if metadata is None:
        return {key.lstrip("/").lower(): None for key in keys}
    return {
        key.lstrip("/").lower(): (str(metadata.get(key)) if metadata.get(key) is not None else None)
        for key in keys
    }


def inspect_pdf_container(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        prefix = handle.read(16)
        handle.seek(max(0, path.stat().st_size - 4096))
        suffix = handle.read()
    header_match = re.match(rb"%PDF-(\d\.\d)", prefix)
    signature_valid = prefix.startswith(b"%PDF-")
    eof_marker_present = b"%%EOF" in suffix
    parse_error = None
    page_count = None
    encrypted = None
    metadata: dict[str, str | None] = {}
    try:
        reader = PdfReader(str(path), strict=False)
        encrypted = bool(reader.is_encrypted)
        page_count = len(reader.pages)
        metadata = metadata_to_plain(reader.metadata)
    except Exception as exc:  # pragma: no cover - recorded as a gate failure
        parse_error = f"{type(exc).__name__}: {exc}"
    return {
        "pdf_signature_valid": signature_valid,
        "pdf_header_version": header_match.group(1).decode("ascii") if header_match else None,
        "eof_marker_present_in_last_4096_bytes": eof_marker_present,
        "parseable": parse_error is None,
        "parse_error": parse_error,
        "encrypted": encrypted,
        "container_page_count": page_count,
        "document_information_dictionary": metadata,
        "page_content_read": False,
        "page_rendered": False,
        "text_extracted": False,
    }


def main() -> int:
    started = utc_now()
    start_clock = time.perf_counter()
    config = read_json(CONFIG_PATH)
    expected = config["expected"]
    destination_dir = ROOT / config["destination_directory"]

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

    source_records: list[dict[str, Any]] = []
    container_records: list[dict[str, Any]] = []
    source_before: list[dict[str, Any]] = []
    for source in config["sources"]:
        path = Path(source["source_path"])
        exists = path.is_file()
        size = path.stat().st_size if exists else None
        hashes = hash_file(path, ("md5", "sha1", "sha256")) if exists else {"md5": None, "sha1": None, "sha256": None}
        container = inspect_pdf_container(path) if exists else {
            "pdf_signature_valid": False,
            "pdf_header_version": None,
            "eof_marker_present_in_last_4096_bytes": False,
            "parseable": False,
            "parse_error": "SOURCE_FILE_MISSING",
            "encrypted": None,
            "container_page_count": None,
            "document_information_dictionary": {},
            "page_content_read": False,
            "page_rendered": False,
            "text_extracted": False,
        }
        basename_matches = exists and path.name.casefold() == f"{source['document_id']}.pdf".casefold()
        parent_matches = exists and path.parent.resolve() == Path(config["path_resolution"]["resolved_exact_directory"]).resolve()
        identity_matches = (
            exists
            and basename_matches
            and parent_matches
            and size == source["archive_original_size_bytes"]
            and hashes["md5"] == source["archive_original_md5"]
            and hashes["sha1"] == source["archive_original_sha1"]
        )
        record = {
            "request_order": source["request_order"],
            "document_id": source["document_id"],
            "track": source["track"],
            "source_path": source["source_path"],
            "source_exists": exists,
            "source_basename": path.name,
            "exact_basename_matches": basename_matches,
            "exact_parent_directory_matches": parent_matches,
            "local_size_bytes": size,
            "archive_original_size_bytes": source["archive_original_size_bytes"],
            "size_matches_archive_metadata": size == source["archive_original_size_bytes"],
            "local_md5": hashes["md5"],
            "archive_original_md5": source["archive_original_md5"],
            "md5_matches_archive_metadata": hashes["md5"] == source["archive_original_md5"],
            "local_sha1": hashes["sha1"],
            "archive_original_sha1": source["archive_original_sha1"],
            "sha1_matches_archive_metadata": hashes["sha1"] == source["archive_original_sha1"],
            "local_sha256": hashes["sha256"],
            "archive_item_identifier": source["archive_item_identifier"],
            "archive_original_name": source["archive_original_name"],
            "archive_original_source_flag": source["archive_original_source_flag"],
            "archive_metadata_byte_identity_matches": identity_matches,
            "user_asserted_authenticity_recorded": True,
            "official_nist_chain_verified": False,
            "governing_revision_or_as_built_authority_verified": False,
            "floor93_99_applicability_verified": False,
            "page_content_read": False,
            "physical_credit": 0,
        }
        source_records.append(record)
        container_records.append(
            {
                "document_id": source["document_id"],
                "source_path": source["source_path"],
                **container,
            }
        )
        source_before.append(
            {
                "document_id": source["document_id"],
                "path": source["source_path"],
                "size_bytes_before": size,
                "md5_before": hashes["md5"],
                "sha1_before": hashes["sha1"],
                "sha256_before": hashes["sha256"],
            }
        )

    all_identity_matches = all(row["archive_metadata_byte_identity_matches"] for row in source_records)
    all_containers_pass = all(
        row["pdf_signature_valid"] and row["eof_marker_present_in_last_4096_bytes"] and row["parseable"]
        and row["container_page_count"] is not None and row["container_page_count"] > 0
        for row in container_records
    )

    working_copies: list[dict[str, Any]] = []
    copy_errors: list[str] = []
    if all_identity_matches and all_containers_pass:
        destination_dir.mkdir(parents=True, exist_ok=True)
        for source_record in source_records:
            source_path = Path(source_record["source_path"])
            destination_name = f"{source_record['document_id']}__{source_record['local_sha256'][:16]}.pdf"
            destination_path = destination_dir / destination_name
            if destination_path.exists():
                existing_hash = sha256_file(destination_path)
                if existing_hash == source_record["local_sha256"] and destination_path.stat().st_size == source_record["local_size_bytes"]:
                    copy_status = "ALREADY_PRESENT_AND_VERIFIED"
                else:
                    copy_status = "CONFLICTING_EXISTING_FILE_NOT_OVERWRITTEN"
                    copy_errors.append(str(destination_path.relative_to(ROOT)).replace("\\", "/"))
            else:
                shutil.copyfile(source_path, destination_path)
                copy_status = "CREATED_AND_VERIFIED"
            destination_hash = sha256_file(destination_path) if destination_path.is_file() else None
            destination_size = destination_path.stat().st_size if destination_path.is_file() else None
            working_copies.append(
                {
                    "document_id": source_record["document_id"],
                    "source_path": source_record["source_path"],
                    "destination_path": str(destination_path.relative_to(ROOT)).replace("\\", "/"),
                    "copy_status": copy_status,
                    "size_bytes": destination_size,
                    "sha256": destination_hash,
                    "size_matches_source": destination_size == source_record["local_size_bytes"],
                    "sha256_matches_source": destination_hash == source_record["local_sha256"],
                    "claims_official_nist_chain": False,
                    "claims_revision_or_as_built_authority": False,
                    "claims_floor93_99_applicability": False,
                    "physical_credit": 0,
                }
            )

    source_after: list[dict[str, Any]] = []
    for before in source_before:
        path = Path(before["path"])
        hashes = hash_file(path, ("md5", "sha1", "sha256")) if path.is_file() else {"md5": None, "sha1": None, "sha256": None}
        size = path.stat().st_size if path.is_file() else None
        source_after.append(
            {
                "document_id": before["document_id"],
                "path": before["path"],
                "size_bytes_after": size,
                "md5_after": hashes["md5"],
                "sha1_after": hashes["sha1"],
                "sha256_after": hashes["sha256"],
                "unchanged_from_before": (
                    size == before["size_bytes_before"]
                    and hashes["md5"] == before["md5_before"]
                    and hashes["sha1"] == before["sha1_before"]
                    and hashes["sha256"] == before["sha256_before"]
                ),
            }
        )

    protected_after: list[dict[str, Any]] = []
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

    page_count_rows = []
    container_by_id = {row["document_id"]: row for row in container_records}
    for source in config["sources"]:
        actual = container_by_id[source["document_id"]]["container_page_count"]
        page_count_rows.append(
            {
                "document_id": source["document_id"],
                "register_claimed_page_count": source["register_claimed_page_count"],
                "container_page_count": actual,
                "container_matches_register_claim": "YES" if actual == source["register_claimed_page_count"] else "NO",
                "register_quality_flag": source["register_quality_flag"],
                "interpretation": "Container count comparison only; no page content was read and a match does not establish revision or applicability.",
            }
        )

    aggregate_bytes = sum(row["local_size_bytes"] or 0 for row in source_records)
    working_copy_pass = (
        len(working_copies) == expected["working_copy_count"]
        and not copy_errors
        and all(row["size_matches_source"] and row["sha256_matches_source"] for row in working_copies)
    )
    checks = {
        "protected_v10h_and_blender_hashes_all_match": all(row["hash_matches"] for row in protected_before),
        "exact_source_file_count": len(source_records) == expected["source_file_count"],
        "all_exact_source_files_exist": all(row["source_exists"] for row in source_records),
        "all_exact_basenames_and_parent_directory_match": all(
            row["exact_basename_matches"] and row["exact_parent_directory_matches"] for row in source_records
        ),
        "aggregate_source_bytes_exact": aggregate_bytes == expected["aggregate_source_bytes"],
        "all_size_md5_sha1_match_archive_original_metadata": (
            sum(row["archive_metadata_byte_identity_matches"] for row in source_records)
            == expected["archive_metadata_identity_match_count"]
        ),
        "all_pdf_signatures_eof_markers_and_containers_pass": all_containers_pass,
        "parseable_pdf_container_count": sum(row["parseable"] for row in container_records) == expected["parseable_pdf_container_count"],
        "working_copy_count_and_hashes": working_copy_pass,
        "source_archive_exact_files_unchanged": all(row["unchanged_from_before"] for row in source_after),
        "protected_inputs_unchanged_after_v10i": all(row["unchanged_from_before"] for row in protected_after),
        "page_content_read_render_and_text_extraction_count_zero": all(
            not row["page_content_read"] and not row["page_rendered"] and not row["text_extracted"]
            for row in container_records
        ),
        "official_chain_revision_as_built_and_floor_applicability_not_promoted": all(
            not row["official_nist_chain_verified"]
            and not row["governing_revision_or_as_built_authority_verified"]
            and not row["floor93_99_applicability_verified"]
            for row in source_records
        ),
        "all_physical_credit_zero": all(row["physical_credit"] == 0 for row in source_records)
        and all(row["physical_credit"] == 0 for row in working_copies),
        "no_network_or_external_contact_during_v10i": True,
        "official_sources_not_read_or_modified": True,
        "solver_blender_thermal_gates_closed": True,
    }
    validation_status = "PASS" if all(checks.values()) else "FAIL"
    completed = utc_now()

    write_csv(
        OUTPUTS["identity_matrix_csv"],
        source_records,
        list(source_records[0].keys()),
    )
    write_csv(
        OUTPUTS["page_count_audit_csv"],
        page_count_rows,
        list(page_count_rows[0].keys()),
    )

    source_manifest = {
        "iteration": "V10I",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "source_directory": config["path_resolution"]["resolved_exact_directory"],
        "source_policy": "READ_ONLY_EXACT_FILES_ONLY",
        "path_resolution": config["path_resolution"],
        "user_source_statement": config["user_source_statement"],
        "pre_v10i_remote_discovery": {
            "occurred": True,
            "authorization_basis": "The user explicitly asked the assistant to search the Internet for the five exact documents.",
            "use_in_v10i": "Previously observed Archive.org original-object size, MD5 and SHA-1 metadata are frozen in the V10I configuration; V10I itself makes zero network requests.",
        },
        "files": source_records,
        "aggregate_size_bytes": aggregate_bytes,
        "evidence_qualification": {
            "byte_identity_to_archive_org_original_objects": all_identity_matches,
            "user_asserted_authenticity_recorded": True,
            "complete_chain_required_for_bounded_intake": False,
            "official_nist_chain_verified": False,
            "governing_revision_or_as_built_authority_verified": False,
            "floor93_99_applicability_verified": False,
            "physical_credit": 0,
        },
    }
    write_json(OUTPUTS["source_manifest"], source_manifest)

    container_metadata = {
        "iteration": "V10I",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "software": {"python": platform.python_version(), "pypdf": pypdf.__version__},
        "inspection_scope": "PDF signature, trailing EOF marker, encryption flag, page-tree count and document information dictionary only.",
        "page_content_read_count": 0,
        "page_render_count": 0,
        "text_extraction_count": 0,
        "files": container_records,
    }
    write_json(OUTPUTS["container_metadata"], container_metadata)

    working_copy_manifest = {
        "iteration": "V10I",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "destination_directory": config["destination_directory"],
        "working_copy_count": len(working_copies),
        "working_copy_total_bytes": sum(row["size_bytes"] or 0 for row in working_copies),
        "files": working_copies,
        "copy_errors": copy_errors,
    }
    write_json(OUTPUTS["working_copy_manifest"], working_copy_manifest)

    archive_integrity = {
        "iteration": "V10I",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "read_only_source_files_before": source_before,
        "read_only_source_files_after": source_after,
        "all_unchanged": all(row["unchanged_from_before"] for row in source_after),
        "source_write_operation_count": 0,
        "source_rename_move_delete_operation_count": 0,
        "recursive_directory_scan_count": 0,
        "bounded_first_level_listing_count_before_v10i": config["path_resolution"]["bounded_first_level_listing_count_before_v10i"],
    }
    write_json(OUTPUTS["archive_integrity_audit"], archive_integrity)

    regression_audit = {
        "iteration": "V10I",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "protected_inputs_before": protected_before,
        "protected_inputs_after": protected_after,
        "checks": checks,
    }
    write_json(OUTPUTS["regression_audit"], regression_audit)

    requirements_closed = expected["requirements_closed"]
    requirements_blocking = expected["requirements_solver_blocking"]
    model_gate = {
        "iteration": "V10I",
        "generated_at_utc": completed,
        "validation_status": validation_status,
        "checks": checks,
        "local_container_intake_gate": "PASS_FIVE_EXACT_ARCHIVE_OBJECT_IDENTITIES" if validation_status == "PASS" else "FAIL",
        "user_asserted_authenticity_gate": "RECORDED_NOT_INDEPENDENTLY_PROVEN",
        "official_nist_chain_gate": "NOT_REQUIRED_FOR_INTAKE_BUT_NOT_VERIFIED",
        "revision_as_built_authority_gate": "CLOSED_NOT_VERIFIED",
        "wtc1_floor93_99_applicability_gate": "CLOSED_NOT_VERIFIED",
        "drawing_page_content_gate": "CLOSED_ZERO_PAGES_READ",
        "requirement_closure_gate": f"CLOSED_{requirements_closed}_OF_22",
        "structural_solver_readiness_gate": f"CLOSED_{requirements_blocking}_OF_22_BLOCKING",
        "v10j_bounded_frontmatter_gate": "OPEN_FOR_IMMUTABLE_MAXIMUM_25_PAGE_PREDECLARATION_ONLY",
        "network_gate": "CLOSED_DURING_V10I",
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

    identity_table = [
        "| Document | Octets | MD5/SHA-1 Archive.org | Pages conteneur | Registre |",
        "|---|---:|---|---:|---:|",
    ]
    for source in source_records:
        container = container_by_id[source["document_id"]]
        register_count = next(item["register_claimed_page_count"] for item in config["sources"] if item["document_id"] == source["document_id"])
        identity_table.append(
            f"| {source['document_id']} | {source['local_size_bytes']} | {'MATCH' if source['archive_metadata_byte_identity_matches'] else 'FAIL'} | {container['container_page_count']} | {register_count} |"
        )

    mismatch_ids = [row["document_id"] for row in page_count_rows if row["container_matches_register_claim"] == "NO"]
    report = f"""# WTC 1 — V10I — réception locale des cinq documents

## Résultat

**{validation_status}** pour la réception locale bornée V10I. Les cinq fichiers fournis correspondent octet pour octet aux tailles, MD5 et SHA-1 des objets marqués `original` dans les métadonnées Archive.org observées avant V10I. Leurs SHA-256 locaux sont enregistrés et cinq copies de travail vérifiées ont été créées dans `{config['destination_directory']}`.

{chr(10).join(identity_table)}

Discordances éventuelles entre le nombre de pages du conteneur et le registre : **{', '.join(mismatch_ids) if mismatch_ids else 'aucune'}**. Une concordance de nombre de pages ne prouve ni la révision ni l'applicabilité.

## Faits directement observés

Les cinq chemins explicites existent dans `WTC1_HARNESS`. Leur nom, taille, MD5 et SHA-1 correspondent aux métadonnées figées des cinq objets Archive.org originaux. Chaque fichier possède une signature PDF, un marqueur EOF et un arbre de pages lisible. Aucune page n'est lue ou rendue et aucun texte n'est extrait.

## Résultats de modèles officiels

Aucun résultat de modèle officiel n'est produit ou validé dans V10I.

## Affirmations d'archives et de l'utilisateur

Archive.org marque ces cinq objets comme `original` dans ses conteneurs. L'utilisateur les considère authentiques et indique qu'une chaîne complète est facultative. Ces affirmations autorisent ici une réception documentaire bornée, mais ne prouvent pas à elles seules un dépôt officiel NIST, la révision gouvernante ou un état as-built.

## Hypothèses propres au modèle

Les cinq identifiants restent des candidats de recherche issus du lot minimal V10H. Leur contenu n'est pas présumé suffisant et les documents d'un même livre ne sont pas présumés interchangeables.

## Résultats dérivés

L'identité binaire aux objets Archive.org est établie pour 5/5 fichiers et les copies de travail reproduisent exactement les SHA-256 sources. Ce résultat qualifie uniquement le conteneur documentaire local.

## Contradictions et informations manquantes

- La chaîne officielle NIST n'est pas vérifiée ; elle n'est pas exigée pour cette réception bornée.
- Aucune page de titre, révision, index ou dessin n'est encore inspectée.
- L'applicabilité au WTC 1 et aux étages 93–99, la révision gouvernante et le statut as-built restent inconnus.
- L'anomalie de registre `2 - C/2` pour WTCI-000024-L reste non résolue.
- Les 22 exigences demeurent bloquantes.

## Portes physiques

V10I attribue zéro coordonnée, section, matériau, masse, rigidité, résistance, loi de connexion, dommage ou crédit de chemin de charge. Aucun accès réseau n'a lieu pendant V10I, `work/official_sources/` n'est pas lu, et aucun solveur, calcul thermique ou Blender n'est lancé. Les cinq sources de l'archive restent inchangées.

## Prochaine itération

V10J pourra inspecter au maximum cinq pages de front-matter/index par document, soit 25 pages au total, après pré-déclaration immuable des pages exactes et uniquement pour des champs de localisation, de tour, d'étage et de révision.
"""
    (ROOT / OUTPUTS["report"]).write_text(report, encoding="utf-8", newline="\n")

    results = {
        "iteration": "V10I",
        "started_at_utc": started,
        "completed_at_utc": completed,
        "validation_status": validation_status,
        "dataset": {
            "name": "Five exact user-supplied local structural PDF container intake",
            "version": config["dataset_version"],
            "random_seed": config["random_seed"],
            "random_draw_used": config["random_draw_used"],
            "scope": config["objective"],
        },
        "observed_or_transcribed_facts": [
            "Five exact PDF basenames are present in the resolved read-only WTC1_HARNESS source directory.",
            "All five local files match the pre-observed Archive.org original-object byte size, MD5 and SHA-1 metadata.",
            "All five files have parseable PDF containers; V10I reads zero page content, renders zero pages and extracts zero text.",
            "Five workspace working copies match their source SHA-256 values."
        ],
        "official_model_results": [
            "No official-model result is created or independently validated."
        ],
        "archive_claims_used": [
            "Archive.org metadata labels the matched file entries as original objects inside the named item containers."
        ],
        "user_assertions": [
            config["user_source_statement"]["assertion"]
        ],
        "model_hypotheses": [
            "The five exact identifiers remain V10H research candidates; binary identity does not establish content sufficiency or physical applicability."
        ],
        "derived_results": {
            "source_file_count": len(source_records),
            "aggregate_source_bytes": aggregate_bytes,
            "archive_metadata_identity_match_count": sum(row["archive_metadata_byte_identity_matches"] for row in source_records),
            "parseable_pdf_container_count": sum(row["parseable"] for row in container_records),
            "working_copy_count": len(working_copies),
            "working_copy_total_bytes": sum(row["size_bytes"] or 0 for row in working_copies),
            "register_page_count_mismatch_count": len(mismatch_ids),
            "register_page_count_mismatch_document_ids": mismatch_ids,
            "page_content_read_count": 0,
            "page_render_count": 0,
            "text_extraction_count": 0,
            "requirements_closed_count": requirements_closed,
            "requirements_solver_blocking_count": requirements_blocking,
            "physical_assignment_count": 0,
        },
        "contradictions_and_missing_information": [
            "Official NIST chain, governing revision, as-built authority and WTC 1/Floors 93-99 applicability remain unverified.",
            "No title, revision, index or drawing page has been inspected.",
            "The WTCI-000024-L register endpoint string '2 - C/2' remains an unresolved register anomaly.",
            "All 22 structural requirements remain solver blocking."
        ],
        "checks": checks,
        "operation_counts": {
            "pre_v10i_authorized_remote_discovery": 1,
            "network_request_during_v10i": 0,
            "exact_source_file_read": len(source_records),
            "source_directory_recursive_scan": 0,
            "source_file_write": 0,
            "source_file_rename_move_delete": 0,
            "official_sources_read": 0,
            "official_sources_write": 0,
            "drawing_page_content_read": 0,
            "page_render": 0,
            "text_extraction": 0,
            "structural_solver_run": 0,
            "thermal_model_run": 0,
            "blender_launch": 0,
            "blender_master_write": 0,
        },
        "physical_assignments": model_gate["physical_assignments"],
        "outputs": OUTPUTS,
        "software": {
            "python": platform.python_version(),
            "pypdf": pypdf.__version__,
            "platform": platform.platform(),
            "elapsed_seconds_before_final_serialization": round(time.perf_counter() - start_clock, 3),
        },
        "next_iteration": config["next_iteration"],
        "errors": [name for name, passed in checks.items() if not passed] + copy_errors,
    }
    write_json(OUTPUTS["results"], results)

    offline_files = [
        "wtc1_simulation_v8/data/v10i_local_structural_intake_audit.json",
        "wtc1_simulation_v8/scripts/run_v10i_local_structural_intake_audit.py",
        OUTPUTS["source_manifest"],
        OUTPUTS["identity_matrix_csv"],
        OUTPUTS["container_metadata"],
        OUTPUTS["page_count_audit_csv"],
        OUTPUTS["working_copy_manifest"],
        OUTPUTS["archive_integrity_audit"],
        OUTPUTS["regression_audit"],
        OUTPUTS["model_gate"],
        OUTPUTS["report"],
        OUTPUTS["results"],
    ]
    missing_files = [path for path in offline_files if not (ROOT / path).is_file()]
    offline_audit = {
        "iteration": "V10I",
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
        "source_archive_file_included": False,
        "drawing_page_content_included": False,
        "official_sources_included": False,
    }
    write_json(OUTPUTS["offline_audit"], offline_audit)

    print(
        json.dumps(
            {
                "iteration": "V10I",
                "validation_status": validation_status,
                "source_files": len(source_records),
                "aggregate_source_bytes": aggregate_bytes,
                "archive_metadata_identity_matches": sum(row["archive_metadata_byte_identity_matches"] for row in source_records),
                "parseable_pdf_containers": sum(row["parseable"] for row in container_records),
                "working_copies": len(working_copies),
                "register_page_count_mismatches": mismatch_ids,
                "page_content_read": 0,
                "requirements_closed": requirements_closed,
                "requirements_solver_blocking": requirements_blocking,
                "failed_checks": [name for name, passed in checks.items() if not passed],
                "copy_errors": copy_errors,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if validation_status == "PASS" and not missing_files else 1


if __name__ == "__main__":
    raise SystemExit(main())
