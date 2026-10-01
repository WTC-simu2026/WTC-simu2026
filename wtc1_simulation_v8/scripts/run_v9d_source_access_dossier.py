#!/usr/bin/env python3
"""Build the V9D local source-access dossier without sending any request."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9d_source_access_dossier.json"
RESULTS_PATH = ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v9d_dossier_acces_sources.json"
REPORT_PATH = ROOT / "wtc1_simulation_v8/output/rapport_wtc1_v9d_dossier_acces_sources.md"
REQUEST_PATH = ROOT / "wtc1_simulation_v8/output/v9d_brouillon_demande_donnees_nist.md"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip() + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_get(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def verify_regressions(config: dict[str, Any]) -> dict[str, Any]:
    file_results: dict[str, Any] = {}
    for relative, expected in config["regressions"]["required_files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else None
        file_results[relative] = {
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": actual == expected,
        }

    metric_results = []
    for declaration in config["regressions"]["required_metrics"]:
        source = load_json(ROOT / declaration["results"])
        actual = nested_get(source, declaration["path"])
        expected = declaration["expected"]
        metric_results.append(
            {
                **declaration,
                "actual": actual,
                "passed": actual == expected,
            }
        )

    files_passed = all(item["passed"] for item in file_results.values())
    metrics_passed = all(item["passed"] for item in metric_results)
    return {
        "files": file_results,
        "metrics": metric_results,
        "files_passed": files_passed,
        "metrics_passed": metrics_passed,
        "passed": files_passed and metrics_passed,
    }


def build_request(config: dict[str, Any]) -> str:
    nist = config["nist_source_access"]
    report = nist["report"]
    route = nist["official_access_route"]
    specimen_lines = []
    for item in nist["specimens_requested"]:
        rate = item.get("rate_per_s", item.get("rate_class", "not stated"))
        specimen_lines.append(f"- {item['id']} — {item['series']} — rate: {rate}")
    record_lines = [f"{index}. {item}" for index, item in enumerate(nist["records_requested"], 1)]
    address = "\n".join(route["postal_address_lines"])
    return f"""# UNSENT DRAFT — NIST records request for NCSTAR 1-3D tensile-test data

Status: **local draft only; not sent or published**

To: NIST FOIA Office ({route['email']})

Postal route if required:

{address}

Subject: Request for machine-readable tensile-test records underlying NIST NCSTAR 1-3D

Dear NIST FOIA Officer,

I request electronic copies of the machine-readable measurement and reduction records underlying the room-temperature tensile and high-strain-rate results reported in **{report['series']}**, “{report['title']},” final NIST publication ID {report['final_publication_id']} and draft publication ID {report['draft_publication_id']}.

The relevant report locations are Section 4.2.1, Section 4.2.2 and Figure 4-3, together with Figures A-28 and A-48 and Tables A-12 and A-14.

## Specimens

{chr(10).join(specimen_lines)}

## Records requested

{chr(10).join(record_lines)}

## Delivery and record status

- Preferred format: {nist['preferred_delivery']['format']}
- Preferred delivery: {nist['preferred_delivery']['delivery']}
- Partial release: {nist['preferred_delivery']['partial_release']}
- Fees: {nist['preferred_delivery']['fee_commitment']}

If any requested record is not held by NIST, please identify whether it was never retained, destroyed under a retention schedule, transferred to another custodian, or withheld, and provide any available file names, accession numbers, contract numbers, laboratory notebook identifiers, authorship/custodian metadata, or other catalog identifiers that would allow the record to be located.

This request seeks measurement and processing records, not a new technical analysis or an interpretation of the World Trade Center event.

Sincerely,

[Requester name and contact details to be added only if sending is explicitly authorized]
"""


def check_documentary_gates(config: dict[str, Any], regressions: dict[str, Any], request_text: str) -> dict[str, Any]:
    nist = config["nist_source_access"]
    cf6 = config["cf6_80a2_public_update"]
    declared = config["predeclared_documentary_gates"]
    specimens = nist["specimens_requested"]
    specimen_ids = [item["id"] for item in specimens]
    records_text = " ".join(nist["records_requested"]).lower()

    channel_checks = {
        channel: channel.lower() in records_text
        for channel in declared["required_raw_channel_categories"]
    }
    external_cf6_contacts = [
        source.get("external_contact_made", False) for source in cf6["sources"]
    ]

    gates = {
        "v9c_regressions_unchanged": regressions["passed"],
        "official_nist_access_route_present": bool(
            nist["official_access_route"]["url"]
            and nist["official_access_route"]["email"]
        ),
        "minimum_exact_specimen_identifiers_passed": (
            len(specimens) >= declared["minimum_exact_specimen_identifiers"]
            and len(specimen_ids) == len(set(specimen_ids))
        ),
        "minimum_record_categories_passed": (
            len(nist["records_requested"]) >= declared["minimum_record_categories"]
        ),
        "required_raw_channels_all_named": all(channel_checks.values()),
        "no_fee_commitment_passed": "No fee commitment" in request_text,
        "partial_release_and_record_status_passed": (
            "Partial release" in request_text
            and "never retained" in request_text
            and "destroyed" in request_text
            and "transferred" in request_text
            and "withheld" in request_text
        ),
        "nist_request_remains_unsent": not nist["official_access_route"]["request_sent"],
        "nist_request_remains_unpublished": not nist["official_access_route"]["request_publicly_posted"],
        "cf6_requirement_count_is_nine": len(cf6["minimum_card_requirements"]) == 9,
        "cf6_available_requirement_count_is_zero": len(cf6["requirements_available"]) == 0,
        "generic_material_substitution_prohibited": not cf6["generic_alloy_substitution_authorized"],
        "ge_or_boeing_request_remains_unsent": not cf6["ge_or_boeing_request_sent"],
        "no_cf6_source_contact_made": not any(external_cf6_contacts),
    }
    return {
        "channel_checks": channel_checks,
        "gates": gates,
        "passed": all(gates.values()),
    }


def build_report(results: dict[str, Any]) -> str:
    dossier = results["nist_source_access_dossier"]
    cf6 = results["cf6_80a2_public_update"]
    gates = results["documentary_gate_summary"]
    gate_rows = "\n".join(
        f"| {name} | {'PASS' if passed else 'FAIL'} |"
        for name, passed in gates["gates"].items()
    )
    source_rows = "\n".join(
        f"| {source['id']} | {source['classification']} | {'oui' if source['material_or_fracture_card_found'] else 'non'} |"
        for source in cf6["sources"]
    )
    return f"""# WTC 1 — V9D : dossier d'accès aux sources manquantes

## Résultat

L'exécution documentaire de V9D est **{'PASS' if results['iteration_execution_validated'] else 'FAIL'}**. Le dossier de demande est complet selon les portes pré-déclarées, mais les données ne sont pas acquises. La qualification physique des matériaux reste **FAIL** et aucun calcul OpenRadioss ou impact façade n'est autorisé.

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D identifie les canaux de temps, charge, déplacement d'actionneur, déformation de la zone utile et déformation côté mors utilisés lors des essais rapides.
- Les identifiants de 12 éprouvettes M26/C80 sont publiés dans les tableaux A-12 et A-14 et sont maintenant explicitement inclus dans le dossier.
- La page FOIA officielle du NIST accepte une demande écrite détaillée par courrier électronique ou postal.
- L'index technique GE identifie `GEK 50460` comme manuel d'installation CF6-80A/A2, mais l'index public ne contient pas de loi matériau ni de données de rupture.

## 2. Résultats d'un modèle officiel

V9D ne recalcule aucun résultat NIST. Les écarts V9C de C80_299 et C80_401 restent inchangés et servent uniquement à expliquer pourquoi les canaux bruts sont nécessaires.

## 3. Affirmations provenant des archives locales

Aucune affirmation nouvelle n'est tirée des archives. L'archive source n'a pas été rescannée et `work/official_sources/` est resté en lecture seule.

## 4. Hypothèses propres au modèle

- La complétude du dossier est définie par 12 identifiants uniques, 10 catégories de dossiers, cinq familles de canaux bruts et une demande explicite du statut des enregistrements absents.
- Ces critères qualifient seulement le dossier administratif ; ils ne préjugent ni de l'existence, ni de la communicabilité, ni de la qualité scientifique des fichiers demandés.

## 5. Résultats dérivés

- Identifiants d'éprouvettes inclus : **{dossier['specimen_identifier_count']}**.
- Catégories de dossiers demandées : **{dossier['record_category_count']}**.
- Familles de canaux demandées : **{dossier['raw_channel_category_count']} / 5**.
- Voie officielle documentée : **NIST FOIA Office**.
- Demande envoyée ou publiée : **non**.
- Porte documentaire : **{'PASS' if gates['passed'] else 'FAIL'}**.

| Porte | Résultat |
|---|---|
{gate_rows}

### Actualisation CF6-80A2/nacelle

| Source | Classe | Carte matériau/rupture trouvée |
|---|---|---|
{source_rows}

- Exigences disponibles : **{cf6['requirements_available_count']} / {cf6['requirements_required_count']}**.
- Substitution par un matériau générique : **non**.

## 6. Contradictions, limites et informations manquantes

- Une voie de demande identifiée ne prouve pas que les fichiers existent encore ou qu'ils seront communicables.
- Les index publics NIST examinés ne fournissent toujours pas les canaux bruts demandés.
- `GEK 50460`, les directives FAA et les études NASA voisines ne fournissent pas une carte production CF6-80A2/Boeing 767 traçable avec courbes dynamiques, rupture et assemblages.
- Une donnée CF6-générique ou une nacelle de recherche ne peut pas remplacer le composant de production ciblé.

## Décision de porte

- Dossier local et brouillon de demande : **validés**.
- Demande extérieure : **non envoyée**.
- Données NIST brutes acquises : **non**.
- Carte matériau/rupture CF6-80A2/nacelle qualifiée : **non**.
- Éprouvette OpenRadioss, rupture et impact façade : **non autorisés et non exécutés**.
- Avion complet, tour globale, thermique et Blender : **portes fermées**.
- Aucun mécanisme explosif ou thermite n'est testé.
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    regressions = verify_regressions(config)
    request_text = build_request(config)
    documentary = check_documentary_gates(config, regressions, request_text)

    nist = config["nist_source_access"]
    cf6 = config["cf6_80a2_public_update"]
    execution_validated = regressions["passed"] and documentary["passed"]

    results: dict[str, Any] = {
        "iteration": "V9D",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": (
            "validated_source_access_dossier_complete_data_not_acquired_coupon_not_authorized"
            if execution_validated
            else "execution_or_documentary_gate_failed"
        ),
        "iteration_execution_validated": execution_validated,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "nist_source_access_dossier": {
            "report_series": nist["report"]["series"],
            "final_publication_id": nist["report"]["final_publication_id"],
            "draft_publication_id": nist["report"]["draft_publication_id"],
            "official_route": nist["official_access_route"]["route_id"],
            "specimen_identifier_count": len(nist["specimens_requested"]),
            "specimen_identifiers": [item["id"] for item in nist["specimens_requested"]],
            "record_category_count": len(nist["records_requested"]),
            "raw_channel_category_count": sum(documentary["channel_checks"].values()),
            "raw_channel_checks": documentary["channel_checks"],
            "public_raw_channels_found": False,
            "request_sent": nist["official_access_route"]["request_sent"],
            "request_publicly_posted": nist["official_access_route"]["request_publicly_posted"],
            "draft_path": str(REQUEST_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "cf6_80a2_public_update": {
            "source_count": len(cf6["sources"]),
            "sources": cf6["sources"],
            "requirements_available_count": len(cf6["requirements_available"]),
            "requirements_required_count": len(cf6["minimum_card_requirements"]),
            "material_card_identification_passed": False,
            "generic_alloy_substitution_authorized": cf6["generic_alloy_substitution_authorized"],
            "external_request_sent": cf6["ge_or_boeing_request_sent"],
        },
        "documentary_gate_summary": documentary,
        "raw_nist_channels_acquired": False,
        "scientific_material_qualification_passed": False,
        "openradioss_coupon_authorized": False,
        "openradioss_coupon_executed": False,
        "failure_deletion_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scientific_and_scope_gates"],
        "interpretation": (
            "V9D validates only the completeness and provenance of a local unsent source-access dossier. "
            "It does not acquire the missing NIST channels, identify a CF6-80A2/cowling material card, "
            "authorize a coupon or validate an impact simulation."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "finished_at": datetime.now().astimezone().isoformat(),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "external_network_writes": 0,
            "solver_runs": 0,
        },
    }

    write_text(REQUEST_PATH, request_text)
    write_json(RESULTS_PATH, results)
    write_text(REPORT_PATH, build_report(results))

    print(json.dumps({
        "iteration": results["iteration"],
        "iteration_execution_validated": results["iteration_execution_validated"],
        "documentation_gate_passed": documentary["passed"],
        "specimen_identifier_count": results["nist_source_access_dossier"]["specimen_identifier_count"],
        "record_category_count": results["nist_source_access_dossier"]["record_category_count"],
        "raw_channel_category_count": results["nist_source_access_dossier"]["raw_channel_category_count"],
        "raw_nist_channels_acquired": results["raw_nist_channels_acquired"],
        "cf6_requirements_available": results["cf6_80a2_public_update"]["requirements_available_count"],
        "cf6_requirements_required": results["cf6_80a2_public_update"]["requirements_required_count"],
        "openradioss_coupon_authorized": results["openradioss_coupon_authorized"],
        "facade_impact_executed": results["facade_impact_executed"],
        "request_sent": results["nist_source_access_dossier"]["request_sent"],
    }, indent=2))
    return 0 if execution_validated else 2


if __name__ == "__main__":
    raise SystemExit(main())
