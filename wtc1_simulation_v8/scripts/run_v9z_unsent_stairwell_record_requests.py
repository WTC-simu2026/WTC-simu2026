#!/usr/bin/env python3
"""Generate and validate the local, unsent V9Z WTC 1 record-request drafts."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9z_unsent_stairwell_record_requests.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


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
    if not all(row["matches"] for row in rows):
        failed = [row["path"] for row in rows if not row["matches"]]
        raise RuntimeError(f"{label} hash failure: {failed}")
    return {"count": len(rows), "all_match": True, "files": rows}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def extract_html_text(path: Path) -> str:
    source = path.read_text(encoding="utf-8", errors="replace")
    source = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", source, flags=re.I | re.S)
    return normalize_text(re.sub(r"<[^>]+>", " ", source))


def extract_pdf_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(path)
    text = normalize_text(" ".join(page.extract_text() or "" for page in reader.pages))
    return text, len(reader.pages)


def verify_route_sources(config: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for source_id, spec in config["official_route_sources"].items():
        path = ROOT / spec["path"]
        size = path.stat().st_size if path.is_file() else None
        actual_hash = digest(path) if path.is_file() else None
        if spec["media_type"] == "text/html":
            extracted_text = extract_html_text(path)
            page_count = None
        elif spec["media_type"] == "application/pdf":
            extracted_text, page_count = extract_pdf_text(path)
        else:
            raise RuntimeError(f"Unsupported V9Z source type: {spec['media_type']}")
        term_rows = [
            {"term": term, "present": normalize_text(term).casefold() in extracted_text.casefold()}
            for term in spec["required_text"]
        ]
        row = {
            "source_id": source_id,
            "path": spec["path"],
            "url": spec["url"],
            "media_type": spec["media_type"],
            "expected_bytes": spec["bytes"],
            "actual_bytes": size,
            "expected_sha256": spec["sha256"],
            "actual_sha256": actual_hash,
            "hash_and_size_match": size == spec["bytes"] and actual_hash == spec["sha256"],
            "page_count": page_count,
            "page_count_matches": page_count == spec.get("expected_page_count") if "expected_page_count" in spec else True,
            "required_text": term_rows,
            "all_required_text_present": all(item["present"] for item in term_rows),
        }
        rows.append(row)
    if not all(row["hash_and_size_match"] and row["page_count_matches"] and row["all_required_text_present"] for row in rows):
        raise RuntimeError("Official V9Z route-source verification failed")
    return {"count": len(rows), "all_match": True, "sources": rows}


def format_record_list(records: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{index}. **{row['record_id']} - {row['category']}**: {row['description']} Preferred delivery: {row['preferred_format']}."
        for index, row in enumerate(records, start=1)
    )


def build_nist_draft(config: dict[str, Any]) -> str:
    policy = config["draft_policy"]
    scope = config["request_scope"]
    sheets = ", ".join(scope["target_sheets"])
    record_list = format_record_list(config["record_categories"])
    return f"""# Local unsent draft - NIST FOIA request for four WTC 1 stair-plan sheets

> **STATUS: LOCAL DRAFT - NOT SENT OR SUBMITTED.** No email, web form, postal request, fee commitment or external contact has been made. Re-check the official route immediately before any separately authorized submission.

**Route transcribed from the hashed NIST FOIA page snapshot dated 2026-08-31**

- Email: `foia@nist.gov`
- Postal: NIST FOIA Office, 100 Bureau Drive, STOP 1710, Gaithersburg, MD 20899-1710
- Official instructions: https://www.nist.gov/director/freedom-information-act

**From:** {policy['requester_name_placeholder']}  
**Postal address:** {policy['requester_address_placeholder']}  
**Email:** {policy['requester_email_placeholder']}  
**Date:** {policy['request_date_placeholder']}  
**Requester status/purpose for fee assessment:** [REQUESTER STATUS AND NONCOMMERCIAL OR COMMERCIAL PURPOSE]

**Subject: Narrow FOIA request - WTC 1 sheets {sheets} and directly associated identification/custody records**

Dear NIST FOIA Officer,

This is a request under the Freedom of Information Act, 5 U.S.C. Section 552. I request electronic copies of existing NIST records limited to the four World Trade Center 1 / North Tower / Tower A drawing sheets **{sheets}**, plus only the directly associated records needed to identify their version, source, custody and release history.

{scope['explicit_exclusion']} In particular, this request does not concern the 65-sheet WTC 7 release identified in prior correspondence as FOIA 12-178 / WTCI-120.

For each target sheet, please provide the following existing records, if held:

{record_list}

For this request, "native file" means the source CAD or original digital image file NIST actually holds. I am not asking NIST to create a new record, recreate a drawing, perform a forensic analysis, calculate new metadata, or convert a record into a format it does not hold. If no native file is held, please provide the highest-resolution scan or image version NIST actually holds.

To keep the search narrow, a register, index, transmittal or database export may be limited to rows or portions that identify one or more of the four target sheets, together with the smallest existing legend needed to interpret their identifiers.

Please provide records electronically in their existing formats when practicable, preserving original filenames. If portions are exempt, please release any reasonably segregable non-exempt portions and identify the basis for any withholding. If NIST does not hold a target record but an existing disposition or referral record identifies another custodian, please provide that releasable record or identify the appropriate agency.

Please notify me in writing of any estimated fees before incurring a charge. This request contains no advance authorization for any fee amount and makes no fee-waiver claim.

Thank you for your consideration.

Sincerely,

{policy['requester_name_placeholder']}

---

## Internal V9Z control note - not part of a submission

- The document remains an unsent local draft.
- No record listed above is presumed to exist, be releasable, be as-built or contain recoverable dimensions.
- Receipt of a file would trigger a separate provenance, revision and dimension audit; it would not automatically create solver geometry.
- LOW, BASE and HIGH remain separate hypothetical placements with zero mass, stiffness, strength, connection, damage or load-path credit.
"""


def build_panynj_draft(config: dict[str, Any]) -> str:
    policy = config["draft_policy"]
    scope = config["request_scope"]
    sheets = ", ".join(scope["target_sheets"])
    record_list = format_record_list(config["record_categories"])
    return f"""# Local unsent draft - PANYNJ request for four WTC 1 stair-plan sheets

> **STATUS: LOCAL DRAFT - NOT SENT OR SUBMITTED.** No email, web form, fax, postal request, fee commitment or external contact has been made. Re-check the official route immediately before any separately authorized submission.

**Route transcribed from the visually reviewed, hashed PANYNJ records-request form snapshot dated 2026-08-31**

- Email: `pafoi@panynj.gov`
- Postal: General Counsel, The Port Authority of New York and New Jersey, 4 World Trade Center, 150 Greenwich Street, New York, NY 10007, Attention: FOI Administrator
- Official form: https://www.panynj.gov/content/dam/port-authority/forms/How_to_Request_a_Record.pdf

**From:** {policy['requester_name_placeholder']}  
**Postal address:** {policy['requester_address_placeholder']}  
**Email:** {policy['requester_email_placeholder']}  
**Date:** {policy['request_date_placeholder']}

**Subject: Narrow records request - WTC 1 sheets {sheets} and directly associated identification/custody records**

To the General Counsel / FOI Administrator:

Under the Port Authority Public Records Access Policy, I request electronic copies of existing Port Authority records limited to the four World Trade Center 1 / North Tower / Tower A drawing sheets **{sheets}**, plus only the directly associated records needed to identify their version, source, custody and release history.

{scope['explicit_exclusion']} It does not seek all architectural or engineering records for the World Trade Center complex.

For each target sheet, please provide the following existing records, if held:

{record_list}

For this request, "native file" means the source CAD or original digital image file the Port Authority actually holds. I am not asking the Port Authority to create a new record, recreate a drawing, perform a forensic analysis, calculate new metadata, or convert a record into a format it does not hold. If no native file is held, please provide the highest-resolution scan or image version the Port Authority actually holds.

To keep the request detailed and not overly broad, a register, index, transmittal or database export may be limited to rows or portions that identify one or more of the four target sheets, together with the smallest existing legend needed to interpret their identifiers. If a target record was transferred to NIST or another custodian, please provide any existing releasable transmittal, accession, disposition or referral record that specifically identifies the target sheet or file.

Please provide records electronically in their existing formats when practicable, preserving original filenames. If only part of a responsive record is available, please provide the releasable portion. If a target record is not held, please state that status and, if recorded, identify any transfer, retention disposition or responsible custodian.

Please advise me of any estimated fee before a charge is incurred. This request contains no advance authorization for any fee amount and makes no legal claim beyond requesting records under the Port Authority's published access process.

Thank you for your consideration.

Sincerely,

{policy['requester_name_placeholder']}

---

## Internal V9Z control note - not part of a submission

- The document remains an unsent local draft.
- The PANYNJ form states that it facilitates requests under the Port Authority Public Records Access Policy and does not constitute legal advice; V9Z does not convert that form into a legal conclusion.
- No target record is presumed to exist, be releasable, be as-built or contain recoverable dimensions.
- Receipt of a file would trigger a separate provenance, revision and dimension audit; it would not automatically create solver geometry.
- LOW, BASE and HIGH remain separate hypothetical placements with zero mass, stiffness, strength, connection, damage or load-path credit.
"""


def main() -> int:
    started = datetime.now(timezone.utc)
    generated_at = started.isoformat(timespec="seconds").replace("+00:00", "Z")
    config = load_json(CONFIG_PATH)
    if config["iteration"] != "V9Z":
        raise RuntimeError("Unexpected iteration in V9Z configuration")

    regressions = verify_files(config["regression_files"], "V9Y regression")
    protected_before = verify_files(config["protected_files"], "Protected Blender master")
    route_sources = verify_route_sources(config)
    outputs = {key: ROOT / value for key, value in config["outputs"].items()}
    targets = config["request_scope"]["target_sheets"]
    records = config["record_categories"]
    policy = config["draft_policy"]

    if len(targets) != len(set(targets)):
        raise RuntimeError("Duplicate target sheet in V9Z request scope")
    if len(records) != len({row["record_id"] for row in records}):
        raise RuntimeError("Duplicate V9Z record category ID")

    nist_draft = build_nist_draft(config)
    panynj_draft = build_panynj_draft(config)
    write_text(outputs["nist_draft"], nist_draft)
    write_text(outputs["panynj_draft"], panynj_draft)

    matrix_rows: list[dict[str, Any]] = []
    for row in records:
        matrix_rows.append(
            {
                "record_id": row["record_id"],
                "category": row["category"],
                "sheet_scope": "|".join(targets),
                "description": row["description"],
                "preferred_format": row["preferred_format"],
                "purpose": row["purpose"],
                "requested_from_nist": "YES",
                "requested_from_panynj": "YES",
                "request_status": "LOCAL_DRAFT_UNSENT",
                "geometry_effect_if_received": row["geometry_effect_if_received"],
            }
        )
    outputs["record_matrix_csv"].parent.mkdir(parents=True, exist_ok=True)
    with outputs["record_matrix_csv"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(matrix_rows[0].keys()))
        writer.writeheader()
        writer.writerows(matrix_rows)
    matrix_fingerprint = hashlib.sha256(
        json.dumps(matrix_rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    draft_texts = {"NIST_FOIA": nist_draft, "PANYNJ_RECORDS": panynj_draft}
    placeholders = [
        policy["requester_name_placeholder"],
        policy["requester_address_placeholder"],
        policy["requester_email_placeholder"],
        policy["request_date_placeholder"],
    ]
    gates = config["gates"]
    checks = {
        "v9y_regression_hashes": regressions["all_match"] and regressions["count"] == gates["regression_hash_count_expected"],
        "official_route_source_hashes_and_content": route_sources["all_match"] and route_sources["count"] == gates["official_route_source_count_expected"],
        "protected_blender_master_unchanged_before_generation": protected_before["all_match"],
        "exact_four_target_sheets": len(targets) == gates["target_sheet_count_expected"] == 4,
        "exact_record_category_count": len(records) == gates["record_category_count_expected"],
        "two_local_drafts_created": len(draft_texts) == gates["draft_count_expected"],
        "every_target_named_in_each_draft": all(all(sheet in text for sheet in targets) for text in draft_texts.values()),
        "requester_identity_remains_placeholder_only": policy["no_personal_identity_inserted"] and all(all(token in text for token in placeholders) for text in draft_texts.values()),
        "narrow_scope_explicit_in_each_draft": all("not a request" in text.casefold() for text in draft_texts.values()),
        "existing_records_only": all("not asking" in text.casefold() and "create a new record" in text.casefold() for text in draft_texts.values()),
        "advance_fee_estimate_without_commitment": policy["advance_fee_estimate_requested"] and not policy["fee_amount_committed"] and all("no advance authorization" in text.casefold() for text in draft_texts.values()),
        "request_unsent_and_no_external_contact": policy["submission_status"] == "LOCAL_DRAFT_UNSENT" and gates["request_sent_count_expected"] == 0 and gates["external_contact_count_expected"] == 0,
        "no_source_archive_read_or_rescan": not config["source_policy"]["source_archive_read"] and not config["source_policy"]["source_archive_rescanned"],
        "no_official_sources_directory_modification": not config["source_policy"]["official_sources_directory_modified"],
        "no_additional_plan_dataset_acquisition": not config["source_policy"]["additional_plan_dataset_acquisition_authorized"],
        "no_geometry_promotion": gates["model_geometry_promoted_record_count_expected"] == 0 and not gates["metric_as_built_solver_geometry_authorized"],
        "variant_separation_retained": gates["variant_count_expected"] == 3,
        "every_record_category_has_zero_immediate_geometry_effect": all(row["geometry_effect_if_received"].startswith("NONE") for row in records),
        "zero_physical_damage_and_load_path_credit": all(
            not gates[key]
            for key in (
                "discrete_mass_authorized",
                "stiffness_authorized",
                "strength_authorized",
                "connection_authorized",
                "damage_credit_authorized",
                "load_path_credit_authorized",
            )
        ),
        "solver_and_blender_prohibited": not gates["global_solver_authorized"] and not gates["blender_authorized"] and not gates["blender_physical_validation_authorized"],
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"V9Z checks failed before output freeze: {failed}")

    route_audit = {
        "iteration": "V9Z",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "source_verification": route_sources,
        "observed_or_transcribed_routes": {
            "NIST_FOIA": {
                "official_url": config["official_route_sources"]["NIST_FOIA"]["url"],
                "email": "foia@nist.gov",
                "postal": "NIST FOIA Office, 100 Bureau Drive, STOP 1710, Gaithersburg, MD 20899-1710",
                "form_required": False,
                "request_detail_required": True,
                "advance_cost_estimate_available": True,
                "segregable_portions_policy_transcribed": True,
            },
            "PANYNJ_RECORDS": {
                "official_url": config["official_route_sources"]["PANYNJ_RECORDS"]["url"],
                "email": "pafoi@panynj.gov",
                "postal": "General Counsel, The Port Authority of New York and New Jersey, 4 World Trade Center, 150 Greenwich Street, New York, NY 10007, Attention: FOI Administrator",
                "fax": "(212) 435-8649",
                "detailed_not_overly_broad_requirement": True,
                "advance_fee_estimate_language_present": True,
                "form_disclaims_legal_advice": True,
                "visual_page_review_completed": True,
            },
        },
        "qualification": "These are current route facts transcribed from hashed official snapshots. They do not prove that the requested records exist, are releasable, are authoritative revisions or are as-built.",
        "submission_status": "LOCAL_DRAFT_UNSENT",
        "external_contact_count": 0,
    }

    unsent_manifest = {
        "iteration": "V9Z",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "configuration": {"path": relative(CONFIG_PATH), "sha256": digest(CONFIG_PATH)},
        "script": {"path": relative(Path(__file__)), "sha256": digest(Path(__file__))},
        "regressions": regressions,
        "protected_files_before": protected_before,
        "official_route_sources": route_sources,
        "drafts": [
            {"agency": "NIST", "path": relative(outputs["nist_draft"]), "sha256": digest(outputs["nist_draft"]), "status": "LOCAL_DRAFT_UNSENT"},
            {"agency": "PANYNJ", "path": relative(outputs["panynj_draft"]), "sha256": digest(outputs["panynj_draft"]), "status": "LOCAL_DRAFT_UNSENT"},
        ],
        "record_matrix": {"path": relative(outputs["record_matrix_csv"]), "sha256": digest(outputs["record_matrix_csv"]), "fingerprint_sha256": matrix_fingerprint},
        "target_sheets": targets,
        "record_category_count": len(records),
        "request_sent_count": 0,
        "external_contact_count": 0,
        "fee_commitment": False,
        "source_archive_read": False,
        "source_archive_rescanned": False,
    }

    model_gate = {
        "iteration": "V9Z",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "checks": checks,
        "qualification": {
            "official_request_routes_verified_from_hashed_snapshots": True,
            "two_precise_unsent_drafts": True,
            "request_submitted": False,
            "external_contact": False,
            "responsive_records_received": False,
            "native_or_higher_resolution_target_source_received": False,
            "file_level_custody_or_release_record_received": False,
            "revision_authority_verified": False,
            "field_or_as_built_status_verified": False,
            "categorical_three_stair_topology_retained": True,
            "printed_numeric_dimension_chain": False,
            "closed_numeric_grid_anchor_set": False,
            "scan_pixel_to_physical_transform": False,
            "as_built_geometry": False,
            "model_geometry_promotion": False,
            "three_separate_hypothetical_variants_retained": True,
            "mechanical_properties": False,
            "damage_credit": False,
            "load_path_credit": False,
            "structural_solver": False,
            "blender": False,
            "physical_validation": False,
        },
        "decision": "V9Z passes only as a reproducible preparation of two narrow, unsent record-request drafts. It creates no agency response, provenance proof, as-built geometry, mechanical property, damage result, solver result or Blender validation.",
    }

    derived = {
        "v9y_regression_file_count": regressions["count"],
        "official_route_source_count": route_sources["count"],
        "official_route_pdf_page_count": next(row["page_count"] for row in route_sources["sources"] if row["source_id"] == "PANYNJ_RECORDS"),
        "target_sheet_count": len(targets),
        "record_category_count": len(records),
        "draft_count": 2,
        "request_sent_count": 0,
        "external_contact_count": 0,
        "fee_commitment_count": 0,
        "responsive_record_count": 0,
        "model_geometry_promoted_record_count": 0,
        "variant_count": 3,
        "matrix_fingerprint_sha256": matrix_fingerprint,
    }

    results = {
        "iteration": "V9Z",
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "random_seed": config["dataset"]["random_seed"],
        "random_draw_used": config["dataset"]["random_draw_used"],
        "scope": config["dataset"]["scope"],
        "observed_or_transcribed_facts": route_audit["observed_or_transcribed_routes"],
        "official_model_results": {
            "official_model_result_created": False,
            "context_only": "V9Y disambiguated NIST FOIA 12-178 / WTCI-120 as a WTC 7 drawing release; V9Z uses that only to prevent a request mismatch.",
        },
        "archive_claims": {
            "new_archive_claim_accepted": False,
            "qualification": "Earlier public dataset titles remain distribution labels, not agency receipts or as-built certifications.",
        },
        "model_hypotheses": {
            "low_base_high_retained_separately": True,
            "native_file_exists_assumed": False,
            "higher_resolution_scan_exists_assumed": False,
            "as_built_condition_assumed": False,
        },
        "derived_results": derived,
        "contradictions_and_missing_information": [
            "A verified submission route does not establish that either agency holds any target record.",
            "The drafts request existing records only and cannot compel creation of native files, metadata, reconstructions or analyses that are not held.",
            "No agency response, revision register, exact file-level receipt, field-verification record or superior target source exists in V9Z.",
            "Any future response must be separately hashed and audited before it can affect provenance or geometry gates.",
            "Official contact routes can change after the hashed 2026-08-31 snapshots and must be rechecked before any authorized submission.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    check_lines = "\n".join(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in checks.items())
    report = f"""# WTC 1 - V9Z - demandes ciblees de plans, preparees mais non envoyees

**Validation generale : PASS**

> PASS DOCUMENTAIRE UNIQUEMENT - DEUX BROUILLONS LOCAUX NON ENVOYES - ZERO REPONSE D'AGENCE - ZERO GEOMETRIE PROMUE - ZERO CREDIT PHYSIQUE

## Conclusion

V9Z produit deux demandes etroitement bornees, l'une pour NIST et l'autre pour PANYNJ, sans les envoyer. Elles visent exactement **{len(targets)} feuilles** ({', '.join(targets)}) et **{len(records)} categories de documents existants**. Elles demandent le fichier natif s'il est reellement detenu, sinon le raster de plus haute resolution detenu, ainsi que le minimum de contexte de revision, registre, transmission, garde et diffusion permettant d'identifier les fichiers.

Cette iteration ne fournit aucune reponse d'agence et ne change donc aucune porte geometrique ou physique.

## 1. Faits directement observes ou transcrits

- La page FOIA NIST conservee et hachee indique une demande ecrite a `foia@nist.gov` ou au NIST FOIA Office, 100 Bureau Drive, STOP 1710, Gaithersburg, MD 20899-1710. Elle indique qu'aucun formulaire special n'est requis et qu'une estimation des frais peut etre demandee.
- Le formulaire officiel PANYNJ conserve et hache comporte deux pages. Il donne `pafoi@panynj.gov`, l'adresse 4 World Trade Center, 150 Greenwich Street, New York, NY 10007, et demande une description suffisamment detaillee et non trop large.
- Le formulaire PANYNJ prevoit l'information du demandeur sur l'estimation avant facturation et precise qu'il ne constitue pas un avis juridique.
- Les deux instantanes officiels ont ete verifies par taille, SHA-256 et texte attendu avant generation des brouillons.

## 2. Resultats et contexte officiels

- V9Z ne cree aucun resultat de modele officiel.
- Le constat V9Y selon lequel FOIA 12-178 / WTCI-120 concerne 65 plans du WTC 7 est conserve uniquement pour eviter de confondre ce dossier avec les quatre feuilles WTC 1 ciblees.

## 3. Affirmations provenant des archives

- Aucune nouvelle affirmation d'archive n'est acceptee en V9Z.
- Les titres de distributions publiques vus auparavant ne deviennent ni recus d'agence, ni certifications as-built.

## 4. Hypotheses propres au modele

- L'existence d'un fichier natif, d'un meilleur scan, d'un registre de revision ou d'une certification as-built n'est pas supposee.
- LOW, BASE et HIGH restent trois placements distincts, explicitement hypothetiques et inchanges.
- Aucun fichier eventuellement recu ne deviendrait automatiquement une geometrie solveur : provenance, revision, cotes et extremites devraient etre valides separement.

## 5. Resultats derives

- Routes officielles verifiees : {derived['official_route_source_count']}.
- Feuilles ciblees : {derived['target_sheet_count']}.
- Categories documentaires : {derived['record_category_count']}.
- Brouillons crees : {derived['draft_count']}.
- Demandes envoyees : {derived['request_sent_count']}.
- Contacts externes : {derived['external_contact_count']}.
- Reponses recues : {derived['responsive_record_count']}.
- Geometries promues : {derived['model_geometry_promoted_record_count']}.
- Empreinte de matrice : `{matrix_fingerprint}`.

## 6. Contradictions et informations manquantes

- Une route de demande valide ne prouve ni l'existence, ni la communicabilite, ni l'autorite de revision d'un document cible.
- Aucun recu fichier par fichier, registre de dessin, fichier natif, meilleur raster ou document de verification sur site n'est obtenu par V9Z.
- Les routes de contact doivent etre recontrolees juste avant tout envoi futur explicitement autorise.
- Masse, rigidite, resistance, connexion, dommage, chemin de charge et validation physique restent a zero.

## Portes de validation

{check_lines}

Le Blender maitre conserve son empreinte protegee. Aucun processus Blender et aucun solveur structurel n'ont ete executes.

## Livrables

- Brouillon NIST : `{relative(outputs['nist_draft'])}`
- Brouillon PANYNJ : `{relative(outputs['panynj_draft'])}`
- Audit des routes : `{relative(outputs['route_audit'])}`
- Matrice des documents demandes : `{relative(outputs['record_matrix_csv'])}`
- Manifeste non envoye : `{relative(outputs['unsent_manifest'])}`
- Porte geometrique : `{relative(outputs['model_gate'])}`

## Etape suivante pre-declaree - V10A

{config['next_iteration']['objective']}
"""

    write_json(outputs["route_audit"], route_audit)
    write_json(outputs["unsent_manifest"], unsent_manifest)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)
    write_text(outputs["report"], report)

    missing_or_empty = [relative(path) for path in outputs.values() if not path.is_file() or path.stat().st_size == 0]
    if missing_or_empty:
        raise RuntimeError(f"V9Z output missing or empty: {missing_or_empty}")
    protected_after = verify_files(config["protected_files"], "Protected Blender master after V9Z")
    if not protected_after["all_match"]:
        raise RuntimeError("Protected Blender master changed during V9Z")

    elapsed = round((datetime.now(timezone.utc) - started).total_seconds(), 3)
    print(
        json.dumps(
            {
                "iteration": "V9Z",
                "status": "PASS",
                "target_sheet_count": len(targets),
                "record_category_count": len(records),
                "draft_count": 2,
                "request_sent_count": 0,
                "external_contact_count": 0,
                "model_geometry_promoted": False,
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
