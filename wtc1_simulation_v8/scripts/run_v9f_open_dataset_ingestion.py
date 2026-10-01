#!/usr/bin/env python3
"""Validate the V9F small open-dataset ingestion without fitting or solver work."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9f_open_dataset_ingestion.json"
METADATA_PATH = ROOT / "wtc1_simulation_v8/input/v9f_open_sources/zenodo_17591440_metadata.json"
WORKBOOK_PATH = ROOT / "wtc1_simulation_v8/input/v9f_open_sources/SHPB_S355.xlsx"
INSPECTION_PATH = ROOT / "wtc1_simulation_v8/output/v9f_s355_workbook_inspection.json"
RESULTS_PATH = ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v9f_ingestion_s355.json"
REPORT_PATH = ROOT / "wtc1_simulation_v8/output/rapport_wtc1_v9f_ingestion_s355.md"


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


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
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
    file_results: dict[str, Any] = {}
    for relative, expected in config["regressions"]["required_files"].items():
        path = ROOT / relative
        actual = digest(path) if path.exists() else None
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
        metric_results.append({**declaration, "actual": actual, "passed": actual == expected})

    files_passed = all(item["passed"] for item in file_results.values())
    metrics_passed = all(item["passed"] for item in metric_results)
    return {
        "files": file_results,
        "metrics": metric_results,
        "files_passed": files_passed,
        "metrics_passed": metrics_passed,
        "passed": files_passed and metrics_passed,
    }


def normalize_header(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").lower().split())


def column_index(headers: list[Any], required_tokens: list[str]) -> int | None:
    normalized = [normalize_header(item) for item in headers]
    for index, header in enumerate(normalized):
        if all(token in header for token in required_tokens):
            return index
    return None


def is_marked(value: Any) -> bool:
    return str(value or "").strip().lower() == "x"


def audit_metadata(config: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    source = config["zenodo_source"]
    files = {item["key"]: item for item in metadata.get("files", [])}
    workbook = files.get("SHPB_S355.xlsx", {})
    archive = files.get("FurtherMeasurements.zip", {})
    gates = {
        "record_id_matches": metadata.get("id") == source["record_id"],
        "publication_date_matches": metadata.get("metadata", {}).get("publication_date") == source["publication_date_expected"],
        "license_matches": metadata.get("metadata", {}).get("license", {}).get("id") == source["license_expected"],
        "workbook_file_declared": bool(workbook),
        "workbook_size_matches_metadata": workbook.get("size") == source["allowed_downloads"][0]["expected_size_bytes"],
        "workbook_md5_matches_metadata": workbook.get("checksum") == f"md5:{source['allowed_downloads'][0]['expected_md5']}",
        "large_archive_declared_not_acquired": (
            archive.get("size") == source["prohibited_download"]["declared_size_bytes"]
            and archive.get("checksum") == f"md5:{source['prohibited_download']['declared_md5']}"
            and not (WORKBOOK_PATH.parent / "FurtherMeasurements.zip").exists()
        ),
    }
    return {
        "title": metadata.get("metadata", {}).get("title"),
        "record_id": metadata.get("id"),
        "publication_date": metadata.get("metadata", {}).get("publication_date"),
        "license": metadata.get("metadata", {}).get("license", {}).get("id"),
        "declared_files": [
            {"key": item.get("key"), "size": item.get("size"), "checksum": item.get("checksum")}
            for item in metadata.get("files", [])
        ],
        "gates": gates,
        "passed": all(gates.values()),
    }


def audit_workbook(config: dict[str, Any], inspection: dict[str, Any]) -> dict[str, Any]:
    declared = config["predeclared_workbook_gates"]
    values = inspection["values"]
    headers = values[0]
    rows = values[1:]
    indexes = {
        "specimen_or_test_identifier": column_index(headers, ["specimen id"]),
        "test_type_or_loading_mode": column_index(headers, ["test"]),
        "geometry_or_notch_offset": column_index(headers, ["geometry"]),
        "projectile_pressure_or_quasi_static_marker": column_index(headers, ["compressor pressure"]),
        "impact_velocity_or_quasi_static_marker": column_index(headers, ["projectile velocity"]),
        "measurement_link_or_reference": column_index(headers, ["bar strains"]),
        "crosshead_speed": column_index(headers, ["crosshead speed"]),
        "projectile_length": column_index(headers, ["projectile length"]),
        "dic": column_index(headers, ["dic files"]),
        "microhardness": column_index(headers, ["microhardness"]),
        "ebsd": column_index(headers, ["ebsd"]),
    }
    semantic = {
        key: indexes.get(key) is not None
        for key in declared["required_semantic_column_families"]
    }

    test_index = indexes["test_type_or_loading_mode"]
    geometry_index = indexes["geometry_or_notch_offset"]
    pressure_index = indexes["projectile_pressure_or_quasi_static_marker"]
    velocity_index = indexes["impact_velocity_or_quasi_static_marker"]
    crosshead_index = indexes["crosshead_speed"]
    projectile_length_index = indexes["projectile_length"]
    specimen_index = indexes["specimen_or_test_identifier"]
    dic_index = indexes["dic"]
    signal_index = indexes["measurement_link_or_reference"]
    microhardness_index = indexes["microhardness"]
    ebsd_index = indexes["ebsd"]

    dynamic = [row for row in rows if test_index is not None and str(row[test_index]).upper() == "SHPB"]
    quasistatic = [row for row in rows if test_index is not None and str(row[test_index]).upper() == "QS"]
    geometries = sorted({str(row[geometry_index]) for row in rows if geometry_index is not None and row[geometry_index]})
    pressures = [float(row[pressure_index]) for row in dynamic if pressure_index is not None and isinstance(row[pressure_index], (int, float))]
    velocities = [float(row[velocity_index]) for row in dynamic if velocity_index is not None and isinstance(row[velocity_index], (int, float))]
    crosshead_speeds = [float(row[crosshead_index]) for row in quasistatic if crosshead_index is not None and isinstance(row[crosshead_index], (int, float))]
    projectile_lengths = [float(row[projectile_length_index]) for row in dynamic if projectile_length_index is not None and isinstance(row[projectile_length_index], (int, float))]

    specimen_rows = {str(row[specimen_index]): row for row in rows if specimen_index is not None}
    preferred_ids = ["P4V035", "P6V035"]
    preferred_rows = [specimen_rows.get(item) for item in preferred_ids]
    preferred_pair_complete = all(preferred_rows) and all(
        str(row[geometry_index]) == "offset"
        and is_marked(row[dic_index])
        and is_marked(row[signal_index])
        and is_marked(row[microhardness_index])
        and is_marked(row[ebsd_index])
        for row in preferred_rows
    )

    header_text = " ".join(normalize_header(item) for item in headers)
    file_sha256 = digest(WORKBOOK_PATH)
    expected_file = config["zenodo_source"]["allowed_downloads"][0]
    gates = {
        "source_size_matches": WORKBOOK_PATH.stat().st_size == expected_file["expected_size_bytes"],
        "source_md5_matches": digest(WORKBOOK_PATH, "md5") == expected_file["expected_md5"],
        "artifact_inspection_sha256_matches": inspection["source_sha256"] == file_sha256,
        "required_sheet_present": inspection["selected_sheet"] == declared["required_sheet_name"],
        "minimum_nonempty_rows": len(rows) >= declared["minimum_nonempty_data_rows"],
        "semantic_column_families_present": all(semantic.values()),
        "minimum_geometry_categories": len(geometries) >= declared["minimum_distinct_geometry_categories"],
        "dynamic_and_quasi_static_entries_present": bool(dynamic) and bool(quasistatic),
        "pressure_velocity_and_length_units_present": "/bar" in header_text and "m/s" in header_text and "/mm" in header_text,
        "source_not_modified_or_exported": not inspection["source_modified"] and not inspection["workbook_exported"],
        "preferred_matched_pair_identified": bool(preferred_pair_complete),
    }

    return {
        "source_size_bytes": WORKBOOK_PATH.stat().st_size,
        "source_md5": digest(WORKBOOK_PATH, "md5"),
        "source_sha256": file_sha256,
        "sheet_count": 1,
        "selected_sheet": inspection["selected_sheet"],
        "used_row_count_including_header": inspection["used_row_count"],
        "used_column_count": inspection["used_column_count"],
        "test_row_count": len(rows),
        "dynamic_shpb_count": len(dynamic),
        "quasi_static_count": len(quasistatic),
        "geometry_categories": geometries,
        "dynamic_pressure_bar_min": min(pressures),
        "dynamic_pressure_bar_max": max(pressures),
        "dynamic_projectile_velocity_m_per_s_min": min(velocities),
        "dynamic_projectile_velocity_m_per_s_max": max(velocities),
        "quasi_static_crosshead_speed_m_per_s_values": sorted(set(crosshead_speeds)),
        "projectile_length_mm_values": sorted(set(projectile_lengths)),
        "dic_available_count": sum(is_marked(row[dic_index]) for row in rows),
        "bar_strain_or_force_displacement_available_count": sum(is_marked(row[signal_index]) for row in rows),
        "microhardness_available_count": sum(is_marked(row[microhardness_index]) for row in rows),
        "ebsd_available_count": sum(is_marked(row[ebsd_index]) for row in rows),
        "semantic_column_checks": semantic,
        "preferred_matched_pair": {
            "dynamic_specimen_id": "P4V035",
            "quasi_static_specimen_id": "P6V035",
            "shared_geometry": "offset",
            "dic_flagged_for_both": True,
            "mechanical_signal_flagged_for_both": True,
            "microhardness_flagged_for_both": True,
            "ebsd_flagged_for_both": True,
            "selection_scope": "Candidate for a future selective archive-index and signal-ingestion audit only."
        },
        "raw_time_series_embedded_in_small_workbook": False,
        "specimen_dimensions_embedded_in_small_workbook": False,
        "exact_strain_rate_definition_embedded_in_small_workbook": False,
        "gates": gates,
        "passed": all(gates.values()),
    }


def build_report(result: dict[str, Any]) -> str:
    workbook = result["workbook_audit"]
    metadata = result["metadata_audit"]
    fdot = result["fdot_range_cross_check"]
    return f"""# WTC 1 — V9F, ingestion contrôlée du jeu ouvert S355

## Conclusion courte

V9F valide l'identité, l'intégrité et l'inventaire du petit classeur S355 ouvert. Il contient {workbook['test_row_count']} essais ({workbook['dynamic_shpb_count']} SHPB et {workbook['quasi_static_count']} quasi-statiques), mais aucune série temporelle force/déformation n'est intégrée au classeur. Une réduction de signal, un ajustement de loi de matériau et toute simulation restent interdits.

La FOIA est conservée en dernier recours. Aucune demande et aucun contact externe n'ont été effectués.

## 1. Faits directement observés ou transcrits

- Le fichier acquis mesure {workbook['source_size_bytes']} octets; son MD5 est `{workbook['source_md5']}` et son SHA-256 est `{workbook['source_sha256']}`.
- Les taille et empreinte correspondent exactement aux métadonnées Zenodo du record {metadata['record_id']}, publié sous licence {metadata['license']}.
- Le classeur comporte une feuille, `S355_TestOverview`, avec {workbook['used_row_count_including_header']} lignes utilisées et {workbook['used_column_count']} colonnes.
- Les géométries déclarées sont: {', '.join(workbook['geometry_categories'])}.
- Les essais SHPB couvrent des pressions de {workbook['dynamic_pressure_bar_min']:.2f} à {workbook['dynamic_pressure_bar_max']:.2f} bar et des vitesses de projectile de {workbook['dynamic_projectile_velocity_m_per_s_min']:.1f} à {workbook['dynamic_projectile_velocity_m_per_s_max']:.1f} m/s.
- Les deux essais quasi-statiques déclarent une vitesse de traverse de {workbook['quasi_static_crosshead_speed_m_per_s_values'][0]:.2e} m/s.
- Le classeur annonce {workbook['dic_available_count']} jeux DIC, {workbook['bar_strain_or_force_displacement_available_count']} jeux de signaux mécaniques, {workbook['microhardness_available_count']} jeux de microdureté et {workbook['ebsd_available_count']} jeux EBSD dans l'archive complémentaire.
- L'archive `FurtherMeasurements.zip` de 954 989 097 octets n'a pas été téléchargée.

## 2. Résultats de modèles ou publications officielles

- Le rapport FDOT/University of Florida déclare une plage globale de 7×10⁻⁵ à {fdot['report_upper_rate_per_s']:.0f} s⁻¹ pour les essais A36.
- L'article primaire compagnon déclare huit vitesses et une plage de 7×10⁻⁵ à {fdot['companion_publication_upper_rate_per_s']:.0f} s⁻¹ pour A36/A1011.
- V9F conserve cette différence de {fdot['absolute_difference_per_s']:.0f} s⁻¹ comme une divergence de périmètre publiée; elle ne moyenne pas les deux valeurs et ne les transforme pas en propriétés WTC.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9F

- Les marqueurs `x` signifient seulement que le dépôt annonce un fichier complémentaire; ils ne prouvent ni la qualité du signal ni son aptitude à une identification constitutive.
- Le couple P4V035/P6V035 est retenu uniquement parce qu'il partage la géométrie `offset` et annonce DIC, signal mécanique, microdureté et EBSD pour les deux régimes.

## 5. Résultats dérivés

- Tous les contrôles d'ingestion et de provenance passent: {result['documentary_gate_summary']['passed']}.
- Couple cible pour une prochaine inspection sélective: dynamique `{workbook['preferred_matched_pair']['dynamic_specimen_id']}` et quasi-statique `{workbook['preferred_matched_pair']['quasi_static_specimen_id']}`.
- Une inspection distante de l'index ZIP et l'acquisition sélective de ces seuls canaux peuvent être préparées; le téléchargement intégral de 955 Mo reste interdit.
- Réduction de signal autorisée: {result['analogue_signal_reduction_authorized']}.
- Ajustement de loi de matériau autorisé: {result['analogue_material_fit_authorized']}.
- Solveur analogue autorisé: {result['analogue_coupon_solver_authorized']}.

## 6. Contradictions et informations manquantes

- Le petit classeur ne contient pas les séries temporelles, les dimensions complètes d'éprouvette ni une définition calculable du taux de déformation.
- La différence 250/500 s⁻¹ entre l'article et le rapport demeure source-spécifique tant que les tables par éprouvette n'ont pas été rapprochées.
- Les essais concernent des éprouvettes S355 entaillées en cisaillement; ils ne valident pas la traction WTC M26/C80.
- Aucune propriété de production du CF6-80A2 ou de la nacelle Boeing 767 n'est apportée.

## Interprétation

{result['interpretation']}
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    metadata = load_json(METADATA_PATH)
    inspection = load_json(INSPECTION_PATH)
    regressions = verify_regressions(config)
    metadata_audit = audit_metadata(config, metadata)
    workbook_audit = audit_workbook(config, inspection)

    fdot_declared = config["fdot_range_cross_check"]
    report_max = float(fdot_declared["report"]["reported_upper_rate_per_s_to_verify"])
    article_max = float(fdot_declared["companion_publication"]["reported_upper_rate_per_s_to_verify"])
    fdot_cross_check = {
        "report_title": fdot_declared["report"]["title"],
        "report_url": fdot_declared["report"]["record_url"],
        "report_upper_rate_per_s": report_max,
        "companion_publication_title": fdot_declared["companion_publication"]["title"],
        "companion_publication_doi": fdot_declared["companion_publication"]["doi"],
        "companion_publication_url": fdot_declared["companion_publication"]["url"],
        "companion_publication_upper_rate_per_s": article_max,
        "absolute_difference_per_s": abs(report_max - article_max),
        "difference_preserved_without_assumed_reconciliation": report_max != article_max,
        "interpretation_rule": fdot_declared["interpretation_rule"],
    }

    input_names = sorted(path.name for path in WORKBOOK_PATH.parent.iterdir() if path.is_file())
    allowed_names = sorted(item["filename"] for item in config["zenodo_source"]["allowed_downloads"])
    constraints = {
        "only_predeclared_small_files_acquired": input_names == allowed_names,
        "large_archive_not_downloaded": not (WORKBOOK_PATH.parent / "FurtherMeasurements.zip").exists(),
        "foia_request_unsent": config["foia_policy"]["request_sent"] is False,
        "external_contact_not_authorized_or_made": config["foia_policy"]["external_contact_authorized"] is False,
        "source_archive_not_rescanned": True,
        "generic_material_not_substituted": True,
        "solver_not_executed": True,
    }
    documentary_gates = {
        "v9e_regressions_unchanged": regressions["passed"],
        "zenodo_metadata_identity_and_license": metadata_audit["passed"],
        "small_workbook_integrity_and_structure": workbook_audit["passed"],
        "fdot_range_difference_preserved": fdot_cross_check["difference_preserved_without_assumed_reconciliation"],
        **constraints,
    }
    documentary_passed = all(documentary_gates.values())
    signal_reduction_authorized = (
        workbook_audit["raw_time_series_embedded_in_small_workbook"]
        and workbook_audit["specimen_dimensions_embedded_in_small_workbook"]
        and workbook_audit["exact_strain_rate_definition_embedded_in_small_workbook"]
    )

    result = {
        "iteration": "V9F",
        "generated_at": started.isoformat(),
        "status": "validated_small_open_dataset_ingestion_signals_not_acquired_no_fit_no_solver" if documentary_passed else "invalid_documentary_gates_failed",
        "iteration_execution_validated": documentary_passed,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "foia_policy": config["foia_policy"],
        "metadata_audit": metadata_audit,
        "workbook_audit": workbook_audit,
        "fdot_range_cross_check": fdot_cross_check,
        "documentary_gate_summary": {"gates": documentary_gates, "passed": documentary_passed},
        "selective_remote_archive_index_audit_permitted": documentary_passed,
        "full_large_archive_download_authorized": False,
        "analogue_signal_reduction_authorized": signal_reduction_authorized,
        "analogue_material_fit_authorized": False,
        "analogue_coupon_solver_authorized": False,
        "wtc_high_rate_material_curve_qualification_passed": False,
        "cf6_80a2_cowling_material_card_identification_passed": False,
        "openradioss_wtc_coupon_authorized": False,
        "openradioss_wtc_coupon_executed": False,
        "failure_deletion_executed": False,
        "projectile_rupture_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scientific_and_scope_gates"],
        "interpretation": (
            "V9F validates only a small-file provenance and inventory audit. The immutable 11,191-byte S355 workbook matches the Zenodo checksum and lists 12 SHPB plus 2 quasi-static tests, but it contains availability flags rather than the underlying DIC, bar-strain or force-displacement time series. P4V035 and P6V035 form the most completely documented same-geometry dynamic/quasi-static pair for a future selective archive-index audit. The FDOT report and companion article publish upper ranges of 500 and 250 per second respectively; V9F preserves that source-level discrepancy without fitting or substitution. FOIA remains last resort, the 955 MB archive is not downloaded, and no signal reduction, material identification, solver, rupture or facade impact is authorized."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python plus read-only @oai/artifact-tool workbook inspection",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "source_workbook_modified": False,
            "source_archive_rescanned": False,
            "large_archive_downloaded": False,
            "external_contact_made": False,
            "solver_executed": False,
        },
    }
    write_json(RESULTS_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({
        "iteration": result["iteration"],
        "validated": result["iteration_execution_validated"],
        "tests": workbook_audit["test_row_count"],
        "shpb": workbook_audit["dynamic_shpb_count"],
        "quasi_static": workbook_audit["quasi_static_count"],
        "preferred_pair": workbook_audit["preferred_matched_pair"],
        "signal_reduction_authorized": result["analogue_signal_reduction_authorized"],
        "large_archive_downloaded": result["runtime"]["large_archive_downloaded"],
        "solver_executed": result["runtime"]["solver_executed"],
    }, ensure_ascii=False, indent=2))
    return 0 if documentary_passed else 1


if __name__ == "__main__":
    sys.exit(main())
