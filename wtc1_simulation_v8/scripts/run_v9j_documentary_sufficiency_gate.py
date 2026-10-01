#!/usr/bin/env python3
"""Evaluate the V9J documentary sufficiency gate without reconstructing signals."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9j_documentary_sufficiency_gate.json"
EVIDENCE_PATH = ROOT / "wtc1_simulation_v8/data/v9j_documentary_evidence.json"


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


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def nested_get(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def verify_regressions(config: dict[str, Any]) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for relative, expected in config["regressions"]["required_files"].items():
        path = ROOT / relative
        actual = digest(path) if path.exists() else None
        files[relative] = {
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": actual == expected,
        }
    metrics = []
    for declaration in config["regressions"]["required_metrics"]:
        source = load_json(ROOT / declaration["results"])
        actual = nested_get(source, declaration["path"])
        metrics.append({**declaration, "actual": actual, "passed": actual == declaration["expected"]})
    return {
        "files": files,
        "metrics": metrics,
        "passed": all(item["passed"] for item in files.values()) and all(item["passed"] for item in metrics),
    }


def verify_sources(evidence: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    records = []
    for source in evidence["acquired_sources"] + evidence["local_verified_sources"]:
        path = ROOT / source["path"]
        exists = path.exists()
        actual_size = path.stat().st_size if exists else None
        actual_hash = digest(path) if exists else None
        expected_size = source.get("size_bytes")
        passed = exists and actual_hash == source["sha256"] and (expected_size is None or actual_size == expected_size)
        records.append({
            "id": source["id"],
            "type": source.get("type", "verified_local_source"),
            "path": source["path"],
            "url": source.get("url"),
            "doi": source.get("doi"),
            "urn": source.get("urn"),
            "license": source.get("license"),
            "expected_size_bytes": expected_size,
            "actual_size_bytes": actual_size,
            "expected_sha256": source["sha256"],
            "actual_sha256": actual_hash,
            "passed": passed,
        })
    return records, bool(records) and all(item["passed"] for item in records)


def oai_identity_check(evidence: dict[str, Any]) -> dict[str, Any]:
    source = next(item for item in evidence["acquired_sources"] if item["id"] == "bam_oai_record")
    text = (ROOT / source["path"]).read_text(encoding="utf-8")
    checks = {
        "oai_identifier_present": "oai:kobv.de-opus4-bam:61333" in text,
        "doi_present": "10.1016/j.ijmecsci.2024.109749" in text,
        "urn_present": "urn:nbn:de:kobv:b43-613339" in text,
        "exact_pdf_url_present": "JentzschEtAl_2024_ShearBandFormationWithSHPBExperiments.pdf" in text,
        "open_access_present": "info:eu-repo/semantics/openAccess" in text,
        "cc_by_4_present": "creativecommons.org/licenses/by/4.0" in text,
    }
    return {"checks": checks, "passed": all(checks.values())}


def build_report(result: dict[str, Any]) -> str:
    findings = result["required_definition_findings"]
    statuses = result["finding_status_counts"]
    return f"""# WTC 1 - V9J, suffisance documentaire de l'analogue S355

## Conclusion courte

V9J récupère légalement le texte intégral primaire et documente deux éléments jusque-là manquants : l'équation 12 et le facteur correctif numérique `b = 1,02`. Le verdict global reste **INSUFFISANT** : {statuses['documented']} définition(s) sur {result['required_definition_count']} satisfont entièrement les critères pré-déclarés, {statuses['partial']} restent partielles et {statuses['unknown']} reste inconnue.

Aucune reconstruction contrainte-déformation, identification de matériau, loi de rupture ou simulation d'impact n'est donc autorisée.

## 1. Faits directement observés ou transcrits

- Le dépôt institutionnel BAM fournit le PDF primaire de 14 pages, lié au DOI `10.1016/j.ijmecsci.2024.109749`, sous licence CC BY 4.0. Son identité locale est vérifiée par SHA-256.
- À la page 4, l'équation 12 impose le déplacement longitudinal du bord extérieur de la barre incidente comme le produit de `b`, de la vitesse acoustique `c_B` et de l'intégrale temporelle de la déformation longitudinale mesurée `epsilon_zz`.
- La vitesse acoustique publiée est `c_B = 4 639 m/s`. La page 5 précise une intégration par différences centrales et un facteur sans dimension `b = 1,02`, conservé pour toutes les simulations rapportées.
- La publication exprime le déplacement longitudinal en `u_z`; l'image de coordonnées P4V035 affiche `+z` vers la droite, `+y` vers le haut et l'onde incidente vers la gauche.
- La figure 5 publie notamment les dimensions 17, 10, 12,2, 2 et 0,35 mm ainsi qu'un rayon d'entaille moyen de 0,1741 mm. Le texte de cette figure concerne toutefois la géométrie `x = 0`, alors que P4V035/P6V035 est classée `x = 0,35 mm` dans la description du jeu de données.

## 2. Résultats de modèles officiels

- Aucun modèle officiel WTC ni solveur physique n'est exécuté dans V9J.
- Les résultats Abaqus de l'article sont des résultats du modèle publié par ses auteurs pour l'éprouvette S355; V9J ne les reproduit pas et ne les transpose pas au WTC ou au CF6.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9J

- Le portail documentaire n'est déclaré franchi que si les cinq familles d'informations pré-déclarées sont toutes explicites dans une source primaire localisée par page, équation, figure ou métadonnée.
- Une convention SHPB générique ne peut pas remplacer une définition absente du jeu P4V035/P6V035.

## 5. Résultats dérivés

- Forme mathématique complète de l'équation 12 : **documentée**.
- Valeur et application du facteur correctif : **documentées**, `b = 1,02`.
- Repères et signes barre/spécimen : **partiels**; `u_z`, le sens physique de l'onde et le repère affiché sont documentés, mais la correspondance CSV `x/displacement_x` vers le `z/u_z` physique et le signe séparé de `BC_Trans` ne le sont pas.
- Dimensions nécessaires à une réduction nominale de P4V035 : **partielles**; plusieurs dimensions sont publiées, mais la figure de l'article traite `x = 0` et aucune réduction nominale complète de la variante décalée n'est définie.
- Alignement temporel absolu barre/DIC : **inconnu**; les deux caméras sont synchronisées entre elles et un déclencheur DIC virtuel est décrit, sans relation explicite avec les colonnes temporelles `BC_Inc`/`BC_Trans`.

## 6. Contradictions et informations manquantes

- La publication emploie le repère physique `y-z`, tandis que les CSV exposent `x-y-z` et `displacement_x/displacement_y`; l'équivalence numérique apparente entre CSV `x` et le `z` affiché reste une inférence interdite.
- L'équation 12 est explicitée pour le bord de la barre incidente. La documentation acquise ne donne pas séparément le signe et la convention appliqués au fichier `BC_Trans`.
- La variante publiée dans la figure 5 et la paire de données sélectionnée ne partagent pas la même valeur déclarée de l'offset `x`.
- Le décalage temporel stable mesuré en V9I n'établit toujours pas une synchronisation physique absolue.

## Décision

Le portail de suffisance documentaire V9J échoue de manière informative. L'équation et son facteur sont récupérés, mais la reconstruction contrainte-déformation demeure interdite. Cette conclusion ne porte ni sur les matériaux WTC M26/C80, ni sur le CF6-80A2, ni sur la rupture du projectile, ni sur l'impact de façade réel.
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    evidence = load_json(EVIDENCE_PATH)
    regressions = verify_regressions(config)
    source_records, sources_passed = verify_sources(evidence)
    oai = oai_identity_check(evidence)
    findings = evidence["required_definition_findings"]
    required = config["predeclared_required_definitions"]
    required_keys_match = set(findings) == set(required)
    status_counts = {
        "documented": sum(item["status"] == "documented" for item in findings.values()),
        "partial": sum(item["status"] == "partial" for item in findings.values()),
        "unknown": sum(item["status"] == "unknown" for item in findings.values()),
    }
    criterion_results = {name: bool(findings[name]["criterion_passed"]) for name in required}
    documentary_gate = required_keys_match and all(criterion_results.values())
    limits = evidence["scientific_limits"]
    safety_gates = {
        "v9i_regressions_unchanged": regressions["passed"],
        "all_documentary_sources_hash_verified": sources_passed,
        "institutional_OAI_identity_and_license_verified": oai["passed"],
        "required_definition_keys_match_predeclaration": required_keys_match,
        "no_generic_SHPB_convention_imported": limits["generic_SHPB_convention_imported"] is False,
        "no_stress_strain_reconstruction": limits["stress_strain_reconstruction_performed"] is False,
        "no_material_or_failure_fit": limits["material_or_failure_fit_performed"] is False,
        "no_solver": limits["solver_executed"] is False,
        "no_WTC_or_CF6_substitution": limits["WTC_or_CF6_substitution_performed"] is False,
        "source_archive_not_rescanned": limits["source_archive_rescanned"] is False,
        "P6V035_DIC_not_acquired": limits["P6V035_DIC_acquired"] is False,
        "full_Zenodo_ZIP_not_acquired": limits["full_Zenodo_ZIP_acquired"] is False,
        "FOIA_request_unsent": limits["FOIA_request_sent"] is False,
        "external_contact_not_made": limits["external_contact_made"] is False,
    }
    execution_validated = all(safety_gates.values())
    manifest = {
        "iteration": "V9J",
        "generated_at": started.isoformat(),
        "institutional_repository": "BAM OPUS4",
        "source_records": source_records,
        "oai_identity": oai,
        "acquired_source_bytes": sum(item.get("actual_size_bytes") or 0 for item in source_records if item["id"] in {"bam_primary_pdf", "bam_oai_record"}),
        "all_source_identities_verified": sources_passed and oai["passed"],
        "source_archive_rescanned": False,
    }
    result = {
        "iteration": "V9J",
        "generated_at": started.isoformat(),
        "status": (
            "validated_documentary_sufficiency_gate_passed_no_reconstruction"
            if execution_validated and documentary_gate
            else "validated_partial_documentary_recovery_gate_failed_no_reconstruction_no_solver"
            if execution_validated
            else "invalid_safety_regression_or_source_identity_gate_failed"
        ),
        "iteration_execution_validated": execution_validated,
        "documentary_sufficiency_gate_passed": documentary_gate,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "documentary_evidence": str(EVIDENCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest": config["output"]["source_manifest"],
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "source_identity_gate": {"source_files_passed": sources_passed, "oai_passed": oai["passed"], "passed": sources_passed and oai["passed"]},
        "required_definition_count": len(required),
        "finding_status_counts": status_counts,
        "criterion_results": criterion_results,
        "required_definition_findings": findings,
        "outcome_gate_summary": {
            "gates": criterion_results,
            "passed": documentary_gate,
            "expected_negative_result_is_valid_iteration": True,
        },
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "equation_12_recovered": criterion_results["equation_12_full_mathematical_form"],
        "correction_factor_recovered": criterion_results["correction_factor_numeric_value_and_application"],
        "correction_factor_b": 1.02,
        "acoustic_velocity_m_per_s": 4639.0,
        "absolute_bar_DIC_time_alignment_resolved": criterion_results["absolute_bar_DIC_time_alignment"],
        "CSV_to_physical_coordinate_mapping_resolved": criterion_results["bar_and_specimen_coordinate_sign_conventions"],
        "selected_offset_geometry_sufficient_for_nominal_reduction": criterion_results["complete_specimen_dimensions_for_reduction"],
        "analogue_stress_strain_reduction_authorized": documentary_gate and config["scope_gates"]["stress_strain_reconstruction_authorized"],
        "analogue_material_fit_authorized": False,
        "analogue_failure_law_fit_authorized": False,
        "analogue_coupon_solver_authorized": False,
        "WTC_or_CF6_solver_authorized": False,
        "failure_deletion_executed": False,
        "projectile_rupture_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scope_gates"],
        "interpretation": (
            "V9J recovers the full published equation 12 and its dimensionless correction factor b=1.02 from the verified CC BY 4.0 primary paper. "
            "The documentary gate nevertheless fails because CSV-to-physical coordinate mapping and the separate BC_Trans sign remain incomplete, the selected x=0.35 mm geometry is not uniquely specified for a nominal reduction by the paper's x=0 figure, and absolute bar/DIC alignment is absent. "
            "No stress-strain reconstruction, fit, solver, WTC or CF6 substitution, rupture or facade-impact claim is authorized."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library deterministic documentary gate",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "network_access_used_for_source_acquisition": True,
            "network_access_used_for_calculation": False,
            "source_acquisition_bytes": manifest["acquired_source_bytes"],
            "source_archive_rescanned": False,
            "additional_measurement_payload_downloaded": False,
            "full_Zenodo_ZIP_downloaded": False,
            "external_contact_made": False,
            "FOIA_request_sent": False,
            "stress_strain_reconstruction_performed": False,
            "solver_executed": False,
        },
    }
    manifest_path = ROOT / config["output"]["source_manifest"]
    results_path = ROOT / config["output"]["results"]
    report_path = ROOT / config["output"]["report"]
    write_json(manifest_path, manifest)
    write_json(results_path, result)
    write_text(report_path, build_report(result))
    print(json.dumps({
        "iteration": "V9J",
        "execution_validated": execution_validated,
        "documentary_sufficiency_gate_passed": documentary_gate,
        "finding_status_counts": status_counts,
        "equation_12_recovered": result["equation_12_recovered"],
        "correction_factor_b": result["correction_factor_b"],
        "source_acquisition_bytes": manifest["acquired_source_bytes"],
        "stress_strain_reconstruction_performed": False,
        "solver_executed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated else 1


if __name__ == "__main__":
    sys.exit(main())
