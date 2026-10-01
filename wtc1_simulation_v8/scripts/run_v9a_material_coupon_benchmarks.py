#!/usr/bin/env python3
"""Run V9A source-backed scalar coupon rate-law benchmarks and completeness audit."""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from run_v8v_deformable_projectile import sha256
from run_v8w_pairwise_contact import verify_regressions


def fit_log_rate(rows: list[dict], rate_key: str, stress_key: str) -> dict:
    x = [math.log(float(row[rate_key])) for row in rows]
    y = [math.log(float(row[stress_key])) for row in rows]
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    sxx = sum((value - x_mean) ** 2 for value in x)
    slope = sum((left - x_mean) * (right - y_mean) for left, right in zip(x, y)) / sxx
    intercept = y_mean - slope * x_mean
    residuals = [right - (intercept + slope * left) for left, right in zip(x, y)]
    sse = sum(value * value for value in residuals)
    sst = sum((value - y_mean) ** 2 for value in y)
    standard_error = math.sqrt((sse / (len(x) - 2)) / sxx) if len(x) > 2 else None
    fitted_rows = []
    for row, log_rate, log_stress, residual in zip(rows, x, y, residuals):
        predicted = math.exp(intercept + slope * log_rate)
        observed = math.exp(log_stress)
        fitted_rows.append(
            {
                "sample": row["sample"],
                "rate_per_s": math.exp(log_rate),
                "observed_strength_ksi": observed,
                "predicted_strength_ksi": predicted,
                "relative_residual": (predicted - observed) / observed,
                "log_residual": residual,
            }
        )
    loo = []
    for held_out in range(len(rows)):
        training = [row for index, row in enumerate(rows) if index != held_out]
        fitted = fit_log_rate_no_loo(training, rate_key, stress_key)
        target = rows[held_out]
        predicted = math.exp(
            fitted["intercept"] + fitted["slope"] * math.log(float(target[rate_key]))
        )
        observed = float(target[stress_key])
        loo.append(
            {
                "sample": target["sample"],
                "observed_strength_ksi": observed,
                "predicted_strength_ksi": predicted,
                "relative_error": (predicted - observed) / observed,
            }
        )
    return {
        "slope_m": slope,
        "intercept_ln_ksi": intercept,
        "slope_standard_error_from_rounded_rows": standard_error,
        "r_squared_log_space": 1.0 - sse / sst if sst else 1.0,
        "maximum_absolute_fit_relative_residual": max(abs(item["relative_residual"]) for item in fitted_rows),
        "maximum_absolute_leave_one_out_relative_error": max(abs(item["relative_error"]) for item in loo),
        "fitted_rows": fitted_rows,
        "leave_one_out": loo,
    }


def fit_log_rate_no_loo(rows: list[dict], rate_key: str, stress_key: str) -> dict:
    x = [math.log(float(row[rate_key])) for row in rows]
    y = [math.log(float(row[stress_key])) for row in rows]
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    sxx = sum((value - x_mean) ** 2 for value in x)
    slope = sum((left - x_mean) * (right - y_mean) for left, right in zip(x, y)) / sxx
    return {"slope": slope, "intercept": y_mean - slope * x_mean}


def verify_sources(config: dict, project_root: Path) -> dict:
    files = []
    for source in config["sources"]:
        if "path" not in source:
            continue
        path = project_root / source["path"]
        actual = sha256(path) if path.exists() else None
        files.append(
            {
                "id": source["id"],
                "path": source["path"],
                "expected_sha256": source["sha256"],
                "actual_sha256": actual,
                "passed": actual == source["sha256"],
                "source_modified": False,
            }
        )
    return {"files": files, "passed": all(item["passed"] for item in files)}


def completeness(config: dict, key: str) -> dict:
    rows = []
    for requirement in config["minimum_identification_requirements"]:
        rows.append(
            {
                "id": requirement["id"],
                "description": requirement["description"],
                "available": bool(requirement[key]),
            }
        )
    return {
        "requirements": rows,
        "available_count": sum(item["available"] for item in rows),
        "required_count": len(rows),
        "passed": all(item["available"] for item in rows),
    }


def main() -> None:
    started = time.perf_counter()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v9a_material_coupon_evidence.json"
    results_path = simulation_root / "output" / "resultats_wtc1_v9a_eprouvettes_materiaux.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v9a_eprouvettes_materiaux.md"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if registry_path.exists() and '"experiment_id":"WTC1-V9A"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V9A outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    regressions = verify_regressions(config, project_root)
    source_verification = verify_sources(config, project_root)
    if not regressions["passed"]:
        raise SystemExit("V8Z regression verification failed before V9A")
    if not source_verification["passed"]:
        raise SystemExit("A declared read-only official source changed or is missing")

    benchmark_results = []
    tolerance = float(
        config["predeclared_benchmarks"]["maximum_absolute_slope_difference_from_published"]
    )
    for series in config["coupon_series"]:
        published = series["published_rate_slopes"]
        for observable, rate_key, stress_key, published_key, uncertainty_key in (
            (
                "yield_1_percent_offset",
                "yield_rate_per_s",
                "yield_ksi",
                "yield_1_percent_offset_m",
                "yield_standard_uncertainty",
            ),
            (
                "tensile_strength",
                "tensile_rate_per_s",
                "tensile_ksi",
                "tensile_strength_m",
                "tensile_strength_standard_uncertainty",
            ),
        ):
            fitted = fit_log_rate(series["observations"], rate_key, stress_key)
            published_m = float(published[published_key])
            difference = abs(fitted["slope_m"] - published_m)
            benchmark_results.append(
                {
                    "coupon_series_id": series["id"],
                    "component": series["component"],
                    "location": series["location"],
                    "observable": observable,
                    "source_observation_count": len(series["observations"]),
                    "published_slope_m": published_m,
                    "published_standard_uncertainty": float(published[uncertainty_key]),
                    "reproduced_slope_m": fitted["slope_m"],
                    "absolute_slope_difference": difference,
                    "rounding_tolerance": tolerance,
                    "passed": difference <= tolerance,
                    "fit": fitted,
                }
            )

    rate_strength_passed = all(item["passed"] for item in benchmark_results)
    controlling_loo = max(
        benchmark_results,
        key=lambda item: item["fit"]["maximum_absolute_leave_one_out_relative_error"],
    )
    wtc_completeness = completeness(config, "wtc_selected_series_available")
    engine_completeness = completeness(config, "cf6_80a2_or_cowling_available")
    physical_fracture_card_identification_passed = wtc_completeness["passed"]
    cf6_80a2_or_cowling_material_card_identification_passed = engine_completeness["passed"]
    openradioss_coupon_executed = False

    results = {
        "iteration": "V9A",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "source_verification": source_verification,
        "regressions": regressions,
        "engine_identity_audit": config["engine_identity_audit"],
        "benchmark_results": benchmark_results,
        "wtc_rate_strength_benchmark_passed": rate_strength_passed,
        "diagnostic_generalization": {
            "gate_predeclared": False,
            "interpretation": "Diagnostic only; the small, unevenly replicated dataset is not treated as a predictive validation set.",
            "maximum_absolute_leave_one_out_relative_error": controlling_loo["fit"]["maximum_absolute_leave_one_out_relative_error"],
            "controlling_coupon_series_id": controlling_loo["coupon_series_id"],
            "controlling_observable": controlling_loo["observable"],
        },
        "wtc_fracture_card_completeness": wtc_completeness,
        "cf6_80a2_or_cowling_card_completeness": engine_completeness,
        "physical_fracture_card_identification_passed": physical_fracture_card_identification_passed,
        "cf6_80a2_or_cowling_material_card_identification_passed": cf6_80a2_or_cowling_material_card_identification_passed,
        "openradioss_coupon_execution_authorized": config["predeclared_benchmarks"]["openradioss_coupon_execution_authorized"],
        "openradioss_coupon_executed": openradioss_coupon_executed,
        "openradioss_coupon_not_executed_reason": config["predeclared_benchmarks"]["reason_openradioss_not_authorized"],
        "facade_impact_interpretation_authorized": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "thermal_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "explosive_or_thermite_mechanism_supported": False,
        "runtime": {
            "elapsed_seconds": time.perf_counter() - started,
            "python": "stdlib deterministic log-linear regression",
            "config_sha256": sha256(config_path),
            "runner_sha256": sha256(Path(__file__)),
            "source_archive_rescanned": False,
            "official_source_files_modified": False,
            "solver_executed": False,
            "blender_executed": False,
        },
    }
    simulation_root.joinpath("output").mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    rows = []
    for item in benchmark_results:
        rows.append(
            f"| {item['coupon_series_id']} | {item['observable']} | {item['source_observation_count']} | "
            f"{item['published_slope_m']:.6f} | {item['reproduced_slope_m']:.6f} | "
            f"{item['absolute_slope_difference']:.6f} | {'PASS' if item['passed'] else 'FAIL'} |"
        )
    missing_wtc = [
        item["id"] for item in wtc_completeness["requirements"] if not item["available"]
    ]
    missing_engine = [
        item["id"] for item in engine_completeness["requirements"] if not item["available"]
    ]
    report = f"""# WTC 1 - V9A : éprouvettes et identification des matériaux

## Résultat

La reproduction limitée des lois de vitesse sur la résistance est **{'PASS' if rate_strength_passed else 'FAIL'}**. Les quatre pentes publiées pour les éprouvettes M26 et C80 sont retrouvées à partir des valeurs tabulées.

L'identification d'une carte de rupture physique WTC est **{'PASS' if physical_fracture_card_identification_passed else 'FAIL'}**. L'identification d'une carte moteur/capotage CF6-80A2 est **{'PASS' if cf6_80a2_or_cowling_material_card_identification_passed else 'FAIL'}**. Aucun calcul OpenRadioss de rupture n'est autorisé ou exécuté dans V9A.

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D publie des valeurs individuelles de vitesse de déformation, limite à 1 %, résistance maximale, allongement total et réduction de section pour des éprouvettes WTC identifiées.
- La série périphérique M26 provient de la colonne 130/131, niveaux 90-93 ; la série de noyau C80 provient de la colonne 603, niveaux 92-95.
- Les essais couvrent plusieurs vitesses, mais les géométries et rapports `sqrt(A)/L` changent. NIST précise que l'allongement à rupture n'est comparable que pour des éprouvettes géométriquement similaires.
- AA11, qui a frappé le WTC 1, utilisait des moteurs **General Electric CF6-80A2**. Le JT9D-7R4D concernait UA175 et le WTC 2.
- Les empreintes des PDF officiels et des fichiers V8Z gelés sont inchangées.

## 2. Résultats et choix d'un modèle officiel

- NIST a utilisé un modèle détaillé de PW4000 comme substitut des moteurs des deux avions, à partir de manuels propriétaires Pratt & Whitney.
- NIST n'a pas testé les matériaux structuraux de l'avion. Les courbes 2024/7075 provenaient de la littérature et aucun effet de vitesse n'a été inclus faute de données suffisantes.
- Le modèle de moteur NIST a augmenté les densités de 20 % pour répartir la masse de composants non représentés. Ce choix n'est pas une mesure de matériau.

## 3. Affirmations des archives locales

- Aucune nouvelle affirmation de l'archive locale n'est utilisée. L'archive source n'a pas été rescannée.

## 4. Hypothèses propres au modèle

- La seule opération de V9A est une régression de `ln(résistance)` sur `ln(vitesse de déformation)`, conforme à l'équation 4-9 de NCSTAR 1-3D.
- La tolérance de 0,0001 sur la pente couvre uniquement l'arrondi des tableaux. Elle ne mesure pas une fidélité physique.
- Les résidus d'ajustement et de validation croisée sont rapportés sans portail prédictif, car le jeu est petit et les essais ne sont pas uniformément répliqués.

## 5. Résultats dérivés

| Série | Observable | Points | Pente publiée | Pente reproduite | Écart absolu | Portail |
|---|---|---:|---:|---:|---:|---|
{chr(10).join(rows)}

- L'erreur relative maximale en retrait d'un point est **{controlling_loo['fit']['maximum_absolute_leave_one_out_relative_error']:.3%}**, contrôlée par `{controlling_loo['coupon_series_id']} / {controlling_loo['observable']}`. C'est un diagnostic sans portail, qui interdit d'interpréter le simple `PASS` des pentes comme une validation prédictive.
- Complétude WTC pour une carte de rupture : **{wtc_completeness['available_count']}/{wtc_completeness['required_count']}** exigences disponibles.
- Éléments WTC manquants : `{', '.join(missing_wtc)}`.
- Complétude CF6-80A2/capotage : **{engine_completeness['available_count']}/{engine_completeness['required_count']}** exigences disponibles.
- Éléments moteur/capotage manquants : `{', '.join(missing_engine)}`.

## 6. Contradictions et informations manquantes

- Les itérations précédentes ont parfois nommé le JT9D comme cible WTC 1 ; NCSTAR 1-2B l'attribue au vol UA175/WTC 2. La cible correcte pour AA11/WTC 1 est CF6-80A2.
- Les tableaux NIST identifient la sensibilité de résistance de certains aciers WTC, mais pas une surface de rupture dépendant de la triaxialité et de l'angle de Lode.
- Ils ne donnent pas l'énergie de fracture, la largeur de localisation ou une longueur interne physique permettant d'identifier `/NONLOCAL/MAT`.
- L'index public GE confirme l'existence des manuels CF6-80A/A2, mais ne fournit pas les cartes matériau/rupture des composants et les qualifie de propriétaires.
- Faute de ces données, aucun alliage générique n'est substitué au CF6-80A2. L'impact façade, l'avion complet, le modèle global, le thermique et Blender restent fermés. Blender demeure une visualisation seulement.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "iteration": "V9A",
                "rate_strength_benchmark": "PASS" if rate_strength_passed else "FAIL",
                "wtc_fracture_card": "PASS" if physical_fracture_card_identification_passed else "FAIL",
                "cf6_80a2_or_cowling_card": "PASS" if cf6_80a2_or_cowling_material_card_identification_passed else "FAIL",
                "openradioss_coupon": "NOT_AUTHORIZED",
                "results": str(results_path),
                "report": str(report_path),
                "runtime_seconds": results["runtime"]["elapsed_seconds"],
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
