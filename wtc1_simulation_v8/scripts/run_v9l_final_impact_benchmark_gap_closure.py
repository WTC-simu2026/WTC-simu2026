#!/usr/bin/env python3
"""Close the V9L open-impact benchmark search without executing a solver."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9l_final_impact_benchmark_gap_closure.json"
EVIDENCE_PATH = ROOT / "wtc1_simulation_v8/data/v9l_final_gap_closure_evidence.json"


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


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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
    for source in evidence["acquired_sources"]:
        path = ROOT / source["path"]
        exists = path.exists()
        actual_size = path.stat().st_size if exists else None
        actual_hash = digest(path) if exists else None
        records.append({
            **source,
            "actual_size_bytes": actual_size,
            "actual_sha256": actual_hash,
            "passed": exists and actual_size == source["size_bytes"] and actual_hash == source["sha256"],
        })
    return records, bool(records) and all(item["passed"] for item in records)


def extract_card_block(text: str, card_prefix: str) -> str:
    lines = text.splitlines()
    collecting = False
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("/"):
            if collecting:
                break
            collecting = stripped == card_prefix or stripped.startswith(card_prefix + "/")
        if collecting and not stripped.startswith("#") and stripped:
            result.append(line.rstrip())
    return "\n".join(result)


def value_after_header(lines: list[str], marker: str, position: int) -> float | None:
    for index, line in enumerate(lines):
        if marker.lower() not in line.lower():
            continue
        for candidate in lines[index + 1:]:
            stripped = candidate.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("/"):
                return None
            fields = stripped.split()
            if len(fields) <= position:
                return None
            try:
                return float(fields[position])
            except ValueError:
                return None
    return None


def inspect_altair_archive(config: dict[str, Any]) -> dict[str, Any]:
    archive_path = ROOT / config["archive_handling"]["download_path"]
    extraction_path = ROOT / config["archive_handling"]["extraction_path"]
    members: list[dict[str, Any]] = []
    safe_names = True
    extracted_match = True
    with zipfile.ZipFile(archive_path, "r") as archive:
        for info in archive.infolist():
            pure = PurePosixPath(info.filename)
            member_safe = not pure.is_absolute() and ".." not in pure.parts
            safe_names = safe_names and member_safe
            if info.is_dir():
                continue
            data = archive.read(info.filename)
            extracted = extraction_path.joinpath(*pure.parts)
            extracted_exists = extracted.exists()
            extracted_hash = digest(extracted) if extracted_exists else None
            member_hash = digest_bytes(data)
            member_match = extracted_exists and extracted.stat().st_size == info.file_size and extracted_hash == member_hash
            extracted_match = extracted_match and member_match
            members.append({
                "archive_path": info.filename,
                "size_bytes": info.file_size,
                "compressed_size_bytes": info.compress_size,
                "sha256": member_hash,
                "safe_relative_path": member_safe,
                "extracted_path": str(extracted.relative_to(ROOT)).replace("\\", "/"),
                "extracted_sha256": extracted_hash,
                "extracted_matches_archive": member_match,
            })

    files = sorted(extraction_path.rglob("*.rad"))
    file_records: list[dict[str, Any]] = []
    failure_counts = {"/FAIL/JOHNSON": 0, "/FAIL/TAB1": 0, "/FAIL/BIQUAD": 0}
    rigid_sphere_files: list[str] = []
    imposed_velocity_files: list[str] = []
    nonlocal_files: list[str] = []
    interface_files: list[str] = []
    license_hits: list[dict[str, str]] = []
    biquad_reference_lengths: list[dict[str, Any]] = []
    tab1_element_length_functions: list[dict[str, Any]] = []
    plate_geometry_digests: set[str] = set()
    one_shell_geometry_digests: set[str] = set()
    card_pattern = re.compile(r"^\s*(/[A-Z0-9_./=-]+)", re.MULTILINE)
    for path in files:
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        text = path.read_text(encoding="utf-8", errors="replace")
        cards = card_pattern.findall(text.upper())
        for name in failure_counts:
            if any(card == name or card.startswith(name + "/") for card in cards):
                failure_counts[name] += 1
        if "/RWALL/SPHER/1" in cards:
            rigid_sphere_files.append(relative)
        if "/IMPVEL/1" in cards:
            imposed_velocity_files.append(relative)
        if any(card.startswith("/NONLOCAL") for card in cards):
            nonlocal_files.append(relative)
        if any(card.startswith("/INTER/") for card in cards):
            interface_files.append(relative)
        for term in ("copyright", "license", "all rights reserved", "permission", "redistribut", "proprietary", "confidential"):
            if term in text.lower():
                license_hits.append({"path": relative, "term": term})
        lines = text.splitlines()
        if "/FAIL/BIQUAD" in text.upper():
            biquad_reference_lengths.append({"path": relative, "value": value_after_header(lines, "Ref.El_Length", 5)})
        if "/FAIL/TAB1" in text.upper():
            tab1_element_length_functions.append({"path": relative, "value": value_after_header(lines, "Fct_ID_EL", 0)})
        geometry = extract_card_block(text, "/NODE") + "\n" + extract_card_block(text, "/SHELL")
        geometry_hash = digest_bytes(geometry.encode("utf-8")) if geometry.strip() else None
        if path.name.endswith("_0000.rad"):
            if "/plate_model/" in "/" + str(path.relative_to(extraction_path)).replace("\\", "/"):
                plate_geometry_digests.add(geometry_hash or "")
            if "/one_shell/" in "/" + str(path.relative_to(extraction_path)).replace("\\", "/"):
                one_shell_geometry_digests.add(geometry_hash or "")
        file_records.append({
            "path": relative,
            "size_bytes": path.stat().st_size,
            "sha256": digest(path),
            "role": "starter" if path.name.endswith("_0000.rad") else "engine" if path.name.endswith("_0001.rad") else "unknown",
            "cards": cards,
            "geometry_sha256": geometry_hash,
        })

    starters = [item for item in file_records if item["role"] == "starter"]
    engines = [item for item in file_records if item["role"] == "engine"]
    objective_regularization_active = bool(nonlocal_files) or any(
        item["value"] not in (None, 0.0) for item in biquad_reference_lengths + tab1_element_length_functions
    )
    checks = {
        "archive_size_matches_predeclaration": archive_path.stat().st_size == 77961,
        "archive_member_paths_safe": safe_names,
        "archive_file_count_is_20": len(members) == 20,
        "extracted_file_count_is_20": len(files) == 20,
        "every_extracted_file_matches_archive_member": extracted_match,
        "starter_engine_pair_count_is_10": len(starters) == 10 and len(engines) == 10,
        "seven_plate_rigid_sphere_decks_found": len(rigid_sphere_files) == 7,
        "seven_plate_imposed_velocity_decks_found": len(imposed_velocity_files) == 7,
        "all_three_failure_formulations_found": failure_counts == {"/FAIL/JOHNSON": 6, "/FAIL/TAB1": 2, "/FAIL/BIQUAD": 2},
        "no_nonlocal_card_found": not nonlocal_files,
        "no_deformable_contact_interface_card_found": not interface_files,
        "no_embedded_license_notice_found": not license_hits,
        "objective_regularization_not_active": not objective_regularization_active,
        "one_unique_plate_geometry_across_variants": len(plate_geometry_digests) == 1,
        "one_unique_one_shell_geometry_across_variants": len(one_shell_geometry_digests) == 1,
    }
    return {
        "archive_path": str(archive_path.relative_to(ROOT)).replace("\\", "/"),
        "archive_size_bytes": archive_path.stat().st_size,
        "archive_sha256": digest(archive_path),
        "extraction_path": str(extraction_path.relative_to(ROOT)).replace("\\", "/"),
        "archive_members": members,
        "rad_files": file_records,
        "summary": {
            "rad_file_count": len(file_records),
            "starter_file_count": len(starters),
            "engine_file_count": len(engines),
            "plate_starter_count": sum("/plate_model/" in "/" + item["path"] for item in starters),
            "one_shell_starter_count": sum("/one_shell/" in "/" + item["path"] for item in starters),
            "failure_card_file_counts": failure_counts,
            "rigid_sphere_file_count": len(rigid_sphere_files),
            "imposed_velocity_file_count": len(imposed_velocity_files),
            "nonlocal_card_file_count": len(nonlocal_files),
            "deformable_contact_interface_file_count": len(interface_files),
            "embedded_license_hit_count": len(license_hits),
            "biquad_reference_element_lengths": biquad_reference_lengths,
            "tab1_element_length_function_ids": tab1_element_length_functions,
            "objective_regularization_active": objective_regularization_active,
            "unique_plate_geometry_count": len(plate_geometry_digests),
            "unique_one_shell_geometry_count": len(one_shell_geometry_digests),
            "declared_three_level_mesh_sequence_present": False,
            "measured_validation_payload_present": False,
            "projectile_model": "rigid_spherical_wall",
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def build_report(result: dict[str, Any]) -> str:
    rows = []
    for candidate in result["candidate_matrix"]:
        rows.append(
            f"| {candidate['id']} | {candidate['passed_gate_count']}/7 | "
            f"{'RETENU' if candidate['selected'] else 'REJETE'} | {candidate['controlling_rejection_reasons'][0]} |"
        )
    table = "\n".join(rows)
    return f"""# WTC 1 - V9L, clôture du benchmark ouvert d'impact rapide

## Conclusion courte

V9L est validée comme **résultat négatif de clôture**. Le ZIP Altair a bien été récupéré et inspecté, et le rapport FAA DOT/FAA/AR-08/36 a été contrôlé sur ses pages techniques utiles. Aucun des deux cas ne réunit simultanément mesures physiques, rupture objectivement régularisée, convergence à trois niveaux, modèle réutilisable et exécution locale bornée. Aucun solveur n'a donc été lancé et la recherche externe de benchmark est close sans assouplir les critères.

## 1. Faits directement observés ou transcrits

- Le ZIP Altair mesure exactement 77 961 octets et contient 20 fichiers RAD : 10 Starter et 10 Engine. Les sept cas de plaque utilisent une sphère rigide `/RWALL/SPHER`; il n'existe ni projectile déformable, ni carte `/NONLOCAL`, ni données d'essai mesurées, ni licence embarquée.
- Les cartes BIQUAD ont une longueur élémentaire de référence nulle et les cartes TAB1 n'activent aucune fonction de longueur d'élément. Les variantes partagent une géométrie de plaque unique : ce ne sont pas trois maillages de convergence.
- Le rapport FAA est un rapport final public de 48 pages. Le lien FAA historique ne répond plus; la copie inspectée provient de la capture 2014 de cette URL, avec identité vérifiée sur la couverture et la fiche documentaire du rapport.
- Les essais FAA/UCB concernent des plaques d'aluminium 2024-T3/T351 de 1/16, 1/8 et 1/4 pouce, frappées par une sphère d'acier de 1/2 pouce. Les graphes donnent les vitesses initiales et résiduelles mesurées, avec des limites balistiques d'environ 400, 700 et 1350 ft/s.
- Le projectile FAA est maillé et peut se déformer élastiquement, mais le modèle interdit sa plasticité et les essais n'ont montré aucun écoulement du projectile. Ce cas ne qualifie donc pas la rupture du projectile.

## 2. Résultats de modèles officiels

- La FAA compare trois configurations de maillage et plusieurs jeux Johnson-Cook. Elle conclut elle-même que les paramètres accordés à une taille d'élément sont plus précis et qu'augmenter la densité du maillage n'améliore pas nécessairement la prédiction.
- L'option non locale testée par la FAA n'a ni amélioré l'exactitude ni diminué la dépendance au maillage dans cette étude.
- Les contacts SOFT=1 et SOFT=2 ont donné des résultats proches avec des maillages de densités similaires; SOFT=2 coûtait davantage en calcul.
- Altair compare des formulations numériques de rupture. L'exemple n'est pas accompagné d'une validation expérimentale.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive WTC en lecture seule n'a pas été rescannée.

## 4. Hypothèses propres à V9L

- Les sept portes V9K restent obligatoires et ne sont pas pondérées.
- Trois maillages différents ne constituent une convergence que si un observable commun tend vers une valeur stable ou si une incertitude numérique est explicitement bornée.
- Une comparaison mesure/calcul de plaque ne peut pas être substituée aux aciers de façade WTC ni à un projectile moteur/capotage sans qualification distincte.

## 5. Résultats dérivés

| Candidat | Portes franchies | Décision | Premier motif de rejet |
| --- | ---: | --- | --- |
{table}

- Candidats retenus : **{result['selected_candidate_count']}**.
- ZIP Altair : complet et exécutable en principe, mais sphère rigide, aucune mesure, aucune convergence et aucune régularisation objective active.
- Rapport FAA : excellent comparateur descriptif de perforation de plaque, avec mesures et contact déformable, mais projectile sans plasticité, rupture dépendante du maillage, absence de convergence établie et absence de deck public.
- Le critère de clôture est satisfait : aucun cas ne combine les éléments requis. La recherche externe de benchmark est désormais gelée.

## 6. Contradictions et informations manquantes

- La FAA publie trois maillages, mais le troisième modifie aussi la topologie dans le plan; les résultats montrent une sensibilité, pas une suite convergée.
- Les graphes FAA fournissent des mesures quantitatives, mais aucune barre d'incertitude ni table brute.
- Le rapport décrit une option non locale, sans publier la valeur numérique de longueur utilisée; sa conclusion ne montre aucun gain de convergence.
- Le ZIP Altair est publiquement téléchargeable, mais aucune licence de réutilisation explicite n'y est embarquée.

## Décision

V9L n'autorise ni ajustement de loi de rupture, ni conversion LS-DYNA, ni simulation du projectile, de la façade ou de l'impact global. Le verrou physique reste la rupture objectivée et convergée d'un projectile déformable. Blender demeure un outil de visualisation, jamais une validation physique.
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    evidence = load_json(EVIDENCE_PATH)
    regressions = verify_regressions(config)
    source_records, source_hashes_passed = verify_sources(evidence)
    archive_inventory = inspect_altair_archive(config)

    required_gates = list(config["unchanged_all_or_nothing_benchmark_gates"])
    configured_ids = {item["id"] for item in config["targets"]}
    evidence_ids = {item["id"] for item in evidence["targets"]}
    candidate_ids_match = configured_ids == evidence_ids
    candidate_matrix = []
    selected_ids = []
    gate_keys_match = True
    for target in evidence["targets"]:
        gates = target["derived_gate_results"]
        keys_match = set(gates) == set(required_gates)
        gate_keys_match = gate_keys_match and keys_match
        passed_count = sum(bool(gates[name]["passed"]) for name in required_gates if name in gates)
        all_passed = keys_match and passed_count == len(required_gates)
        if all_passed:
            selected_ids.append(target["id"])
        candidate_matrix.append({
            "id": target["id"],
            "title": target["title"],
            "required_gate_count": len(required_gates),
            "passed_gate_count": passed_count,
            "all_required_gates_passed": all_passed,
            "selected": all_passed,
            "gates": gates,
            "controlling_rejection_reasons": [gates[name]["reason"] for name in required_gates if not gates[name]["passed"]],
        })

    limits = evidence["scientific_limits"]
    acquired_bytes = sum(item["actual_size_bytes"] or 0 for item in source_records)
    critical_combo_absent = all(
        not (
            target["derived_gate_results"]["measured_validation_outputs"]["passed"]
            and target["derived_gate_results"]["failure_and_regularization_complete"]["passed"]
            and target["derived_gate_results"]["mesh_and_convergence_definition"]["passed"]
            and target["derived_gate_results"]["bounded_downloadable_deck_or_reconstructible_definition"]["passed"]
        )
        for target in evidence["targets"]
    )
    external_search_closed = not selected_ids and critical_combo_absent and not limits["selection_gates_relaxed"]
    safety_gates = {
        "V9K_regressions_unchanged": regressions["passed"],
        "source_hashes_and_sizes_verified": source_hashes_passed,
        "altair_archive_integrity_and_inventory_passed": archive_inventory["passed"],
        "candidate_ids_match_predeclaration": candidate_ids_match,
        "gate_keys_match_predeclaration": gate_keys_match,
        "maximum_one_candidate_selected": len(selected_ids) <= 1,
        "expected_negative_selection_matches": len(selected_ids) == limits["selected_candidate_count_expected"],
        "critical_gap_combo_absent": critical_combo_absent,
        "external_benchmark_search_closed_as_predeclared": external_search_closed == limits["external_benchmark_search_closed_expected"],
        "single_file_source_limit_respected": all((item["actual_size_bytes"] or 0) <= config["source_limits"]["maximum_single_file_bytes"] for item in source_records),
        "total_source_limit_respected": acquired_bytes <= config["source_limits"]["maximum_total_new_source_bytes"],
        "one_archive_and_one_report_only": len(source_records) == 2,
        "FAA_transport_fallback_disclosed": evidence["retrieval_provenance"]["transport_domain_exception_disclosed"],
        "no_solver_or_model_conversion": limits["solver_executed"] is False and limits["model_conversion_performed"] is False,
        "no_material_or_failure_fit": limits["material_or_failure_fit_performed"] is False,
        "no_WTC_or_CF6_substitution": limits["WTC_or_CF6_substitution_performed"] is False,
        "no_projectile_facade_or_global_run": all(limits[name] is False for name in ("projectile_rupture_executed", "facade_impact_executed", "global_impact_executed")),
        "source_archive_not_rescanned": limits["source_archive_rescanned"] is False,
        "FOIA_and_external_contact_unsent": limits["FOIA_request_sent"] is False and limits["external_contact_made"] is False,
        "Blender_not_used_as_physical_validation": limits["blender_executed"] is False and limits["blender_used_as_physical_validation"] is False,
        "selection_gates_not_relaxed": limits["selection_gates_relaxed"] is False,
    }
    execution_validated = all(safety_gates.values())

    manifest = {
        "iteration": "V9L",
        "generated_at": started.isoformat(),
        "acquired_source_records": source_records,
        "retrieval_provenance": evidence["retrieval_provenance"],
        "FAA_relevant_pdf_pages_inspected": [1, 2, 3, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 43, 47],
        "acquired_source_bytes": acquired_bytes,
        "maximum_single_file_bytes": max(item["actual_size_bytes"] or 0 for item in source_records),
        "all_source_identities_verified": source_hashes_passed,
        "source_archive_rescanned": False,
    }
    matrix_output = {
        "iteration": "V9L",
        "generated_at": started.isoformat(),
        "predeclared_required_gates": config["unchanged_all_or_nothing_benchmark_gates"],
        "candidate_matrix": candidate_matrix,
        "selected_candidate_ids": selected_ids,
        "critical_gap_combo_absent": critical_combo_absent,
        "external_benchmark_search_closed": external_search_closed,
        "stop_rule": config["stop_rules"],
    }
    result = {
        "iteration": "V9L",
        "generated_at": started.isoformat(),
        "status": "validated_negative_gap_closure_external_benchmark_search_closed_no_solver" if execution_validated and external_search_closed else "invalid_gap_closure_or_safety_gate_failed",
        "iteration_execution_validated": execution_validated,
        "gap_closure_audit_passed": execution_validated,
        "benchmark_selection_gate_passed": bool(selected_ids),
        "external_benchmark_search_closed": external_search_closed,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "evidence": str(EVIDENCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest": config["output"]["source_manifest"],
        "deck_inventory": config["output"]["deck_inventory"],
        "gap_closure_matrix_path": config["output"]["gap_closure_matrix"],
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "source_identity_gate": {"hashes_and_sizes_passed": source_hashes_passed, "passed": source_hashes_passed},
        "candidate_count": len(candidate_matrix),
        "required_gate_count": len(required_gates),
        "candidate_matrix": candidate_matrix,
        "selected_candidate_ids": selected_ids,
        "selected_candidate_count": len(selected_ids),
        "critical_gap_combo_absent": critical_combo_absent,
        "no_candidate_selected_without_relaxing_gates": not selected_ids and not limits["selection_gates_relaxed"],
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "acquired_source_bytes": acquired_bytes,
        "benchmark_solver_executed": False,
        "model_conversion_performed": False,
        "material_or_failure_fit_performed": False,
        "WTC_or_CF6_substitution_performed": False,
        "projectile_rupture_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scope_gates"],
        "interpretation": (
            "V9L closes the bounded external benchmark search. The official Altair archive is complete and locally runnable but uses a rigid sphere and supplies neither measured validation, active objective regularization nor a convergence sequence. "
            "FAA DOT/FAA/AR-08/36 supplies measured plate-impact residual velocities and three mesh configurations, but its projectile cannot yield, its damage parameters are explicitly tuned to element size and thickness, the nonlocal option does not remove mesh dependence, and no public deck or bounded local conversion route is supplied. "
            "Neither source qualifies deformable-projectile rupture or authorizes a facade/global WTC simulation."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library deterministic source and deck audit",
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
    write_json(ROOT / config["output"]["deck_inventory"], archive_inventory)
    write_json(ROOT / config["output"]["gap_closure_matrix"], matrix_output)
    write_json(ROOT / config["output"]["results"], result)
    write_text(ROOT / config["output"]["report"], build_report(result))
    print(json.dumps({
        "iteration": "V9L",
        "execution_validated": execution_validated,
        "candidate_count": len(candidate_matrix),
        "selected_candidate_count": len(selected_ids),
        "passed_gates_by_candidate": {item["id"]: item["passed_gate_count"] for item in candidate_matrix},
        "external_benchmark_search_closed": external_search_closed,
        "archive_checks_passed": archive_inventory["passed"],
        "solver_executed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated else 1


if __name__ == "__main__":
    sys.exit(main())
