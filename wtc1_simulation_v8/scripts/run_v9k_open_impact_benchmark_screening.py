#!/usr/bin/env python3
"""Run the deterministic V9K primary-source benchmark screening without a solver."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9k_open_impact_benchmark_screening.json"
EVIDENCE_PATH = ROOT / "wtc1_simulation_v8/data/v9k_open_impact_screening_evidence.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
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


def verify_acquired_sources(evidence: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    records = []
    for source in evidence["acquired_sources"]:
        path = ROOT / source["path"]
        exists = path.exists()
        actual_size = path.stat().st_size if exists else None
        actual_hash = digest(path) if exists else None
        passed = exists and actual_size == source["size_bytes"] and actual_hash == source["sha256"]
        records.append({
            **source,
            "actual_size_bytes": actual_size,
            "actual_sha256": actual_hash,
            "passed": passed,
        })
    return records, bool(records) and all(item["passed"] for item in records)


def verify_source_content(evidence: dict[str, Any]) -> dict[str, Any]:
    metadata_71018 = load_json(ROOT / next(item["path"] for item in evidence["acquired_sources"] if item["id"] == "nasa_20050171018_metadata"))
    metadata_77899 = load_json(ROOT / next(item["path"] for item in evidence["acquired_sources"] if item["id"] == "nasa_20050177899_metadata"))
    altair_path = ROOT / next(item["path"] for item in evidence["acquired_sources"] if item["id"] == "altair_rd_e_2602_html")
    altair_text = altair_path.read_text(encoding="utf-8", errors="replace")
    checks = {
        "NASA_20050171018_id": str(metadata_71018.get("id")) == "20050171018",
        "NASA_20050171018_public": metadata_71018.get("distribution") == "PUBLIC",
        "NASA_20050171018_no_download": not metadata_71018.get("downloads"),
        "NASA_20050177899_id": str(metadata_77899.get("id")) == "20050177899",
        "NASA_20050177899_public": metadata_77899.get("distribution") == "PUBLIC",
        "NASA_20050177899_pdf_declared": "20050177899.pdf" in json.dumps(metadata_77899),
        "Altair_RD_E_2602_title": "RD-E: 2602 Ductile Failure Model" in altair_text,
        "Altair_input_zip_declared": "RD-E-2602_Ductile.zip" in altair_text,
        "Altair_failure_keywords_present": all(value in altair_text for value in ("/FAIL/JOHNSON", "/FAIL/TAB1", "/FAIL/BIQUAD")),
    }
    return {"checks": checks, "passed": all(checks.values())}


def build_report(result: dict[str, Any]) -> str:
    rows = []
    for candidate in result["candidate_matrix"]:
        rows.append(
            f"| {candidate['id']} | {candidate['passed_gate_count']}/7 | "
            f"{'RETENU' if candidate['selected'] else 'REJETE'} | {candidate['controlling_rejection_reasons'][0]} |"
        )
    table = "\n".join(rows)
    return f"""# WTC 1 - V9K, criblage d'un benchmark ouvert d'impact rapide

## Conclusion courte

V9K est valide comme criblage, mais **aucun des quatre candidats ne franchit les sept portes pre-declarees**. Aucun benchmark n'est selectionne et aucun solveur n'est lance. La recherche confirme qu'il existe des comparateurs utiles pour le contact, la perforation et la fragmentation, mais pas encore un cas ouvert qui combine deck reconstructible, mesure physique, rupture objective et convergence exploitable pour qualifier le projectile deformable de la facade.

## 1. Faits directement observes ou transcrits

- Les deux fiches NASA sont des sources gouvernementales publiques. Le cas de 1996 publie un regime d'essai jusqu'a 350 m/s et un graphe de vitesse de perforation, mais pas de deck ni de definition complete du projectile.
- L'article NASA de 1997 decrit un impact de racine de pale sur panneau metallique, DYNA3D, Cowper-Symonds et une rupture par deformation plastique effective. Les auteurs ont ajuste la deformation maximale pour obtenir un accord qualitatif et disent que les parametres predictifs restent a etablir.
- Le rapport FAA DOT/FAA/TC-14/43 documente des sensibilites de maillage et de rupture. La fragmentation change avec le maillage; le rapport indique aussi que les valeurs de rupture doivent etre ajustees selon l'evenement et le maillage. Les temps de calcul complets publies vont de 10 a 208 heures sur 8 a 24 processeurs.
- L'exemple officiel Altair RD-E 2602 fournit un petit fichier d'entree annonce et plusieurs lois de rupture, mais utilise une sphere rigide, omet les effets de vitesse et ne compare pas ses sorties a un essai mesure.

## 2. Resultats de modeles officiels

- NASA rapporte un accord qualitatif pour la vitesse de perforation et la fleche, sans serie mesuree ni incertitude publiee dans l'article.
- La FAA rapporte une sequence de fragmentation compatible avec des essais industriels decrits, mais sans paire ouverte complete mesure/calcul pour le modele de soufflante.
- Altair compare entre elles plusieurs formulations numeriques de rupture. Ce cas illustre le solveur; il ne valide pas physiquement la rupture.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive WTC en lecture seule n'a pas ete rescanee.

## 4. Hypotheses propres a V9K

- Les sept portes sont toutes obligatoires : provenance, licence, deck ou reconstruction complete, rupture regularisee, mesures, convergence et execution locale bornee.
- Une etude de sensibilite dont l'issue qualitative change avec le maillage n'est pas une preuve de convergence.
- Le seuil futur de 10 pour cent sur l'observable d'impulsion ou equivalent n'est pas applique ici, car aucune simulation V9K n'est autorisee.

## 5. Resultats derives

| Candidat | Portes franchies | Decision | Motif controlant |
| --- | ---: | --- | --- |
{table}

- Candidats evalues : **{result['candidate_count']}**.
- Candidats selectionnes : **{result['selected_candidate_count']}**.
- Le meilleur cas executable est RD-E 2602, mais il ne franchit que 3 portes sur 7 et echoue sur la licence explicite du deck, la regularisation, la mesure et la convergence.
- Le cas FAA est le plus instructif pour la fragmentation : il montre directement que la rupture depend du maillage et du choix de loi. Cette information justifie de ne pas passer a la facade globale.

## 6. Contradictions et informations manquantes

- Les pages Altair annoncent un ZIP public, mais la page inspectee est protegee par une mention All Rights Reserved et ne fournit pas de licence de reutilisation explicite pour le deck.
- La FAA explore trois configurations de maillage, mais elles ne forment pas une sequence de convergence avec un observable commun; le maillage fin change le verdict de fragmentation.
- Les sources NASA donnent des essais physiquement pertinents, mais pas les definitions et sorties quantitatives necessaires a une reproduction independante.
- Le telechargement local du PDF FAA a ete refuse par le serveur ROSA P (HTTP 403). Son texte primaire indexe, son DOI, sa taille et son empreinte SHA-512 de depot ont ete controles; l'absence de deck et les echecs de convergence/execution suffisent au rejet.

## Decision

Le resultat negatif est conserve sans assouplir les criteres. V9K ne qualifie ni la rupture du projectile, ni le contact deformable-deformable, ni l'impulsion de facade. Il n'autorise aucune substitution de ces analogues aux aciers WTC M26/C80 ou aux materiaux d'un CF6-80A2 de production. Blender reste uniquement un outil de visualisation.
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    evidence = load_json(EVIDENCE_PATH)
    regressions = verify_regressions(config)
    source_records, source_hashes_passed = verify_acquired_sources(evidence)
    source_content = verify_source_content(evidence)
    required_gates = list(config["predeclared_required_selection_gates"])
    configured_candidate_ids = {item["id"] for item in config["candidate_scope"]}
    evidence_candidate_ids = {item["id"] for item in evidence["candidates"]}
    candidate_ids_match = configured_candidate_ids == evidence_candidate_ids
    candidate_matrix = []
    selected_ids = []
    gate_keys_match = True
    for candidate in evidence["candidates"]:
        gates = candidate["derived_gate_results"]
        keys_match = set(gates) == set(required_gates)
        gate_keys_match = gate_keys_match and keys_match
        passed_gate_count = sum(bool(gates[name]["passed"]) for name in required_gates if name in gates)
        all_passed = keys_match and passed_gate_count == len(required_gates)
        if all_passed:
            selected_ids.append(candidate["id"])
        candidate_matrix.append({
            "id": candidate["id"],
            "title": candidate["title"],
            "required_gate_count": len(required_gates),
            "passed_gate_count": passed_gate_count,
            "all_required_gates_passed": all_passed,
            "selected": all_passed,
            "gates": gates,
            "controlling_rejection_reasons": [gates[name]["reason"] for name in required_gates if not gates[name]["passed"]],
        })
    limits = evidence["scientific_limits"]
    acquired_bytes = sum(item["actual_size_bytes"] or 0 for item in source_records)
    single_file_limit_passed = all((item["actual_size_bytes"] or 0) <= config["acquisition_limits"]["maximum_single_file_bytes"] for item in source_records)
    total_limit_passed = acquired_bytes <= config["acquisition_limits"]["maximum_total_V9K_source_bytes"]
    selection_count_valid = len(selected_ids) <= config["selection_rule"]["maximum_selected_candidate_count"]
    expected_negative_result_matches = len(selected_ids) == limits["selected_candidate_count_expected"]
    safety_gates = {
        "V9J_regressions_unchanged": regressions["passed"],
        "all_acquired_source_hashes_and_sizes_verified": source_hashes_passed,
        "source_content_identity_checks_passed": source_content["passed"],
        "candidate_ids_match_predeclaration": candidate_ids_match,
        "gate_keys_match_predeclaration": gate_keys_match,
        "maximum_one_candidate_selected": selection_count_valid,
        "expected_negative_selection_matches_evidence": expected_negative_result_matches,
        "single_file_acquisition_limit_respected": single_file_limit_passed,
        "total_acquisition_limit_respected": total_limit_passed,
        "no_solver_deck_payload_acquired": limits["solver_deck_payload_acquired"] is False,
        "no_large_archive_acquired": limits["large_archive_acquired"] is False,
        "no_solver_executed": limits["solver_executed"] is False,
        "no_material_or_failure_fit": limits["material_or_failure_fit_performed"] is False,
        "no_WTC_or_CF6_substitution": limits["WTC_or_CF6_substitution_performed"] is False,
        "no_projectile_or_facade_or_global_run": all(limits[name] is False for name in ("projectile_rupture_executed", "facade_impact_executed", "global_impact_executed")),
        "source_archive_not_rescanned": limits["source_archive_rescanned"] is False,
        "FOIA_request_unsent": limits["FOIA_request_sent"] is False,
        "external_contact_not_made": limits["external_contact_made"] is False,
        "Blender_not_used_as_physical_validation": limits["blender_executed"] is False and limits["blender_used_as_physical_validation"] is False,
        "selection_gates_not_relaxed": limits["selection_gates_relaxed"] is False,
    }
    execution_validated = all(safety_gates.values())
    manifest = {
        "iteration": "V9K",
        "generated_at": started.isoformat(),
        "acquired_source_records": source_records,
        "remote_primary_sources_reviewed_without_payload_acquisition": evidence["remote_primary_sources_reviewed_without_payload_acquisition"],
        "source_content_identity": source_content,
        "acquired_source_bytes": acquired_bytes,
        "maximum_single_file_bytes": max((item["actual_size_bytes"] or 0) for item in source_records),
        "all_source_identities_verified": source_hashes_passed and source_content["passed"],
        "solver_deck_payload_acquired": False,
        "source_archive_rescanned": False,
    }
    matrix_output = {
        "iteration": "V9K",
        "generated_at": started.isoformat(),
        "predeclared_required_gates": config["predeclared_required_selection_gates"],
        "candidate_matrix": candidate_matrix,
        "selected_candidate_ids": selected_ids,
        "selection_rule": config["selection_rule"],
    }
    result = {
        "iteration": "V9K",
        "generated_at": started.isoformat(),
        "status": "validated_negative_primary_source_screening_no_candidate_selected_no_solver" if execution_validated and not selected_ids else "invalid_screening_or_safety_gate_failed",
        "iteration_execution_validated": execution_validated,
        "screening_gate_passed": execution_validated,
        "benchmark_selection_gate_passed": bool(selected_ids),
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "screening_evidence": str(EVIDENCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest": config["output"]["source_manifest"],
        "candidate_matrix_path": config["output"]["candidate_matrix"],
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "source_identity_gate": {
            "hashes_and_sizes_passed": source_hashes_passed,
            "content_checks_passed": source_content["passed"],
            "passed": source_hashes_passed and source_content["passed"],
        },
        "candidate_count": len(candidate_matrix),
        "required_gate_count": len(required_gates),
        "candidate_matrix": candidate_matrix,
        "selected_candidate_ids": selected_ids,
        "selected_candidate_count": len(selected_ids),
        "no_candidate_selected_without_relaxing_gates": not selected_ids and not limits["selection_gates_relaxed"],
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "acquired_source_bytes": acquired_bytes,
        "solver_deck_payload_acquired": False,
        "benchmark_solver_executed": False,
        "material_or_failure_fit_performed": False,
        "WTC_or_CF6_substitution_performed": False,
        "projectile_rupture_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scope_gates"],
        "interpretation": (
            "V9K validates a negative primary-source screening result. NASA provides relevant physical impact regimes but not reconstructible models or converged quantitative validation; "
            "FAA DOT/FAA/TC-14/43 documents material and mesh sensitivity severe enough to change fragmentation and requires long proprietary LS-DYNA runs; "
            "Altair RD-E 2602 is executable but is a rigid-projectile numerical feature example without measured validation, objective fracture regularization or a convergence study. "
            "No candidate satisfies all seven gates, so no benchmark, material substitution, rupture run, facade run or global WTC inference is authorized."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library deterministic source-screening gate",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "network_access_used_for_source_acquisition": True,
            "network_access_used_for_calculation": False,
            "source_acquisition_bytes": acquired_bytes,
            "source_archive_rescanned": False,
            "external_contact_made": False,
            "FOIA_request_sent": False,
            "solver_executed": False,
        },
    }
    write_json(ROOT / config["output"]["source_manifest"], manifest)
    write_json(ROOT / config["output"]["candidate_matrix"], matrix_output)
    write_json(ROOT / config["output"]["results"], result)
    write_text(ROOT / config["output"]["report"], build_report(result))
    print(json.dumps({
        "iteration": "V9K",
        "execution_validated": execution_validated,
        "candidate_count": len(candidate_matrix),
        "selected_candidate_count": len(selected_ids),
        "passed_gates_by_candidate": {item["id"]: item["passed_gate_count"] for item in candidate_matrix},
        "acquired_source_bytes": acquired_bytes,
        "solver_executed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated else 1


if __name__ == "__main__":
    sys.exit(main())
