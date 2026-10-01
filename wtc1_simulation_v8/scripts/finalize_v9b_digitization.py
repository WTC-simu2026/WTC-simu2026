#!/usr/bin/env python3
"""Finalize V9B as a validated negative digitization result."""

from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

from run_v8v_deformable_projectile import sha256
from run_v8w_pairwise_contact import verify_regressions


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{100.0 * value:.2f} %"


def main() -> None:
    started = time.perf_counter()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v9b_stress_strain_digitization.json"
    digitizer_path = simulation_root / "scripts" / "run_v9b_digitization.py"
    preliminary_path = simulation_root / "output" / "resultats_wtc1_v9b_numerisation_preliminaire.json"
    audit_path = simulation_root / "output" / "v9b_cf6_public_source_audit.json"
    results_path = simulation_root / "output" / "resultats_wtc1_v9b_numerisation_courbes.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v9b_numerisation_courbes.md"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if registry_path.exists() and '"experiment_id":"WTC1-V9B"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V9B outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    preliminary = json.loads(preliminary_path.read_text(encoding="utf-8"))
    engine_audit = json.loads(audit_path.read_text(encoding="utf-8"))
    regressions = verify_regressions(config, project_root)
    if not regressions["passed"]:
        raise SystemExit("V9A regression verification failed while finalizing V9B")
    if preliminary["runtime"]["config_sha256"] != sha256(config_path):
        raise SystemExit("V9B preliminary output does not match the current predeclared config")
    if preliminary["runtime"]["runner_sha256"] != sha256(digitizer_path):
        raise SystemExit("V9B preliminary output does not match the current digitizer")
    if preliminary["digitization_gate_summary"]["digitization_passed"]:
        raise SystemExit(
            "Digitization passed; this negative-result finalizer cannot replace the required conditional coupon"
        )
    if preliminary["conditional_openradioss_coupon_authorized"]:
        raise SystemExit("Inconsistent preliminary result: failed digitization authorized a coupon")
    if preliminary["openradioss_coupon_executed"]:
        raise SystemExit("Inconsistent preliminary result: a solver coupon was executed")

    curve_results = preliminary["curve_results"]
    failed_curves = [item for item in curve_results if not item["passed"]]
    passed_curves = [item for item in curve_results if item["passed"]]
    axis_maximum = max(
        max(
            item["x"]["maximum_absolute_residual_pdf_points"],
            item["y"]["maximum_absolute_residual_pdf_points"],
        )
        for item in preliminary["axis_calibrations"]
    )
    output_hashes = {
        item["csv"]: sha256(project_root / item["csv"]) for item in curve_results
    }
    final_results = {
        "iteration": "V9B",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "status": "validated_negative_digitization_gates_not_passed_coupon_not_authorized",
        "iteration_execution_validated": True,
        "scientific_digitization_gate_passed": False,
        "configuration": preliminary["configuration"],
        "scope": preliminary["scope"],
        "evidence_policy": preliminary["evidence_policy"],
        "source_verification": preliminary["source_verification"],
        "regressions": regressions,
        "digitization_method": preliminary["digitization_method"],
        "axis_calibrations": preliminary["axis_calibrations"],
        "curve_results": curve_results,
        "digitization_gate_summary": preliminary["digitization_gate_summary"],
        "failed_curve_ids": [item["curve_id"] for item in failed_curves],
        "passed_curve_count": len(passed_curves),
        "failed_curve_count": len(failed_curves),
        "maximum_axis_calibration_residual_pdf_points": axis_maximum,
        "cf6_public_source_audit": engine_audit,
        "cf6_80a2_or_cowling_material_card_identification_passed": engine_audit[
            "cf6_80a2_or_cowling_material_card_identification_passed"
        ],
        "generic_aircraft_or_engine_alloy_substituted": False,
        "conditional_openradioss_coupon_authorized": False,
        "openradioss_coupon_executed": False,
        "openradioss_coupon_not_executed_reason": "Three predeclared curve gates failed: C80_QS did not meet the minimum vector-point count, C80_299 exceeded the individual yield and tensile-strength error limits, and C80_401 exceeded the individual yield error limit. Running the coupon would violate the predeclared sequence.",
        "failure_deletion_executed": False,
        "fracture_calibration_executed": False,
        "physical_internal_length_inferred": False,
        "facade_impact_executed": False,
        "facade_impact_interpretation_authorized": False,
        "whole_aircraft_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "thermal_qualification_passed": False,
        "blender_executed": False,
        "blender_physics_validation_passed": False,
        "explosive_or_thermite_mechanism_tested": False,
        "scope_gates": preliminary["scope_gates"],
        "interpretation": "V9B reproducibly extracts all nine declared M26 and C80 vector traces and passes both axis-calibration gates and both median property-error gates. It does not pass the full digitization gate because three C80 traces fail individual completeness or property concordance criteria. The mismatch is consistent with visible high-rate ringing and sparse quasi-static vector sampling, but this is a bounded interpretation rather than proof of cause. No filtering was introduced after seeing the result, and the conditional OpenRadioss coupon was not run. V9B is therefore a valid negative evidence result, not a solver failure and not physical validation of rupture or facade impact.",
        "runtime": {
            "elapsed_seconds_finalizer": time.perf_counter() - started,
            "python": platform.python_version(),
            "config_sha256": sha256(config_path),
            "digitizer_sha256": sha256(digitizer_path),
            "preliminary_results_sha256": sha256(preliminary_path),
            "engine_audit_sha256": sha256(audit_path),
            "finalizer_sha256": sha256(Path(__file__)),
            "digitized_csv_sha256": output_hashes,
            "source_archive_rescanned": False,
            "official_source_files_modified": False,
            "solver_executed": False,
            "blender_executed": False
        }
    }
    results_path.write_text(
        json.dumps(final_results, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    curve_rows = []
    for item in curve_results:
        failed_reasons = []
        if not item["point_count_passed"]:
            failed_reasons.append("points")
        if not item["yield_validation_passed"]:
            failed_reasons.append("Fy")
        if not item["tensile_validation_passed"]:
            failed_reasons.append("TS")
        status = "PASS" if item["passed"] else "FAIL (" + ", ".join(failed_reasons) + ")"
        curve_rows.append(
            f"| {item['curve_id']} | {item['rate_per_s']:.6g} | {item['unique_centerline_point_count']} | "
            f"{item['digitized_yield_1_percent_offset_ksi']:.2f} | "
            f"{item['yield_reference_interval_ksi'][0]:.1f}-{item['yield_reference_interval_ksi'][1]:.1f} | "
            f"{percent(item['yield_relative_error_to_interval'])} | "
            f"{item['digitized_tensile_strength_ksi']:.2f} | "
            f"{item['tensile_reference_interval_ksi'][0]:.1f}-{item['tensile_reference_interval_ksi'][1]:.1f} | "
            f"{percent(item['tensile_relative_error_to_interval'])} | {status} |"
        )
    gate_summary = preliminary["digitization_gate_summary"]
    report = f"""# WTC 1 - V9B : numérisation des courbes M26 et C80

## Résultat

L'exécution de V9B est **validée comme résultat négatif**. La numérisation complète est **FAIL** selon les portes déclarées avant calcul. Les neuf tracés sont extraits et les axes sont calibrés, mais trois courbes C80 échouent au moins un critère individuel. L'éprouvette OpenRadioss conditionnelle est donc **non autorisée et non exécutée**.

Ce résultat ne dit pas que l'impact de l'avion sur la façade échoue physiquement. Il dit seulement que les figures publiques utilisées ici ne suffisent pas, sans filtrage ou hypothèse ajoutée après coup, à construire et valider la réponse plastique/rate demandée pour l'étape suivante.

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D Figure A-28 publie cinq courbes longitudinales M26 à 6.06E-5, 65, 100, 260 et 417 /s.
- NCSTAR 1-3D Figure A-48 publie quatre courbes longitudinales C80 à 8.75E-5, 84, 299 et 401 /s.
- Les Tables A-12 et A-14 donnent les limites à 1 % et résistances maximales employées comme références.
- Le rapport avertit que des oscillations de charge subsistent dans les essais rapides et qu'aucun filtrage mathématique n'a été appliqué.
- Les pages source ont été rendues à 300 dpi et contrôlées visuellement. Les données numériques proviennent néanmoins des chemins vectoriels du PDF, non des pixels rendus.

## 2. Résultats d'un modèle officiel

Aucun résultat global NIST n'est recalculé dans V9B. Les figures et tables NIST servent seulement de mesures publiées à numériser et comparer.

## 3. Affirmations provenant des archives locales

Aucune affirmation nouvelle n'est tirée des archives locales. L'archive source n'a pas été rescannée et les PDF officiels n'ont pas été modifiés.

## 4. Hypothèses propres au modèle

- Une droite d'offset à 1 % avec `E = 29 000 ksi` est utilisée uniquement pour relire la limite d'élasticité sur les courbes.
- Aucun lissage ni filtrage n'est appliqué après observation des résultats.
- Le court segment orange terminal de C80-401/s est rattaché au tracé vert uniquement parce que son écart vectoriel de {next(item['terminal_alias_gap_pdf_points'] for item in curve_results if item['curve_id'] == 'C80_401'):.3f} point reste sous la limite pré-déclarée de 1.5 point.
- Aucune partie après striction n'est convertie en loi de rupture.

## 5. Résultats dérivés

- Résidu maximal de calibration des axes : **{axis_maximum:.3f} point PDF**, sous la limite de 0.25.
- Erreur médiane Fy : **{percent(gate_summary['median_yield_relative_error'])}**, sous la limite de 5 %.
- Erreur médiane TS : **{percent(gate_summary['median_tensile_relative_error'])}**, sous la limite de 5 %.
- Erreur individuelle maximale Fy : **{percent(gate_summary['maximum_yield_relative_error'])}**.
- Erreur individuelle maximale TS : **{percent(gate_summary['maximum_tensile_relative_error'])}**.
- Six courbes passent tous leurs critères et trois échouent : **{', '.join(item['curve_id'] for item in failed_curves)}**.

| Courbe | Vitesse (/s) | Points | Fy num. (ksi) | Fy table (ksi) | Erreur Fy | TS num. (ksi) | TS table (ksi) | Erreur TS | Porte |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(curve_rows)}

## 6. Contradictions, limites et informations manquantes

- **C80_QS** contient 25 points centraux uniques, sous le minimum de 30. Ses résistances sont proches de la table, mais la complétude vectorielle échoue.
- **C80_299** dépasse les limites individuelles pour Fy ({percent(next(item['yield_relative_error_to_interval'] for item in curve_results if item['curve_id'] == 'C80_299'))}) et TS ({percent(next(item['tensile_relative_error_to_interval'] for item in curve_results if item['curve_id'] == 'C80_299'))}).
- **C80_401** dépasse la limite individuelle Fy ({percent(next(item['yield_relative_error_to_interval'] for item in curve_results if item['curve_id'] == 'C80_401'))}).
- Les oscillations visibles sont cohérentes avec l'avertissement NIST, mais les données brutes et la procédure exacte de réduction utilisées pour les valeurs tabulées ne sont pas publiques ici. On ne peut donc pas attribuer toute la différence au seul ringing.
- La recherche publique ciblée GE/FAA/NASA fournit des dimensions, des actions de navigabilité et des concepts adjacents de nacelle ou de confinement. Elle ne fournit toujours **aucune des 9 exigences** d'une carte matériau/rupture assignable au CF6-80A2 ou à son capotage de production.
- Aucune nuance générique, aucun concept composite expérimental et aucun modèle de moteur voisin n'est substitué au CF6-80A2.

## Décision de porte

La porte de numérisation V9B reste fermée. Conformément au protocole pré-déclaré :

- pas d'éprouvette OpenRadioss ;
- pas de suppression d'éléments ni calibration de rupture ;
- pas d'impact façade ;
- pas de simulation avion complet, tour globale, thermique ou Blender ;
- aucune conclusion sur explosif ou thermite.

## Suite recommandée

Conserver V9B comme cas de régression négatif. Pour V9C, rechercher d'abord soit les données numériques brutes des essais NIST M26/C80, soit une méthode officielle documentée reliant les tracés oscillants aux valeurs Fy/TS tabulées. À défaut, ne pas construire de carte plastique haute vitesse à partir de ces figures. La recherche CF6-80A2 doit rester limitée à des composants et matériaux explicitement identifiés, sans substitution générique.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "iteration_execution_validated": True,
                "scientific_digitization_gate_passed": False,
                "failed_curve_ids": final_results["failed_curve_ids"],
                "openradioss_coupon_executed": False,
                "results": str(results_path),
                "report": str(report_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
