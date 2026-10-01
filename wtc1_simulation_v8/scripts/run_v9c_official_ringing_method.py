#!/usr/bin/env python3
"""Run V9C official third-order ringing-aware yield revalidation."""

from __future__ import annotations

import csv
import json
import math
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from run_v8v_deformable_projectile import sha256
from run_v8w_pairwise_contact import verify_regressions


def interval_relative_error(value: float | None, bounds: list[float]) -> float | None:
    if value is None:
        return None
    low, high = sorted(float(item) for item in bounds)
    if low <= value <= high:
        return 0.0
    if value < low:
        return (low - value) / low
    return (value - high) / high


def read_engineering_curve(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            engineering_strain = float(row["engineering_strain"])
            engineering_stress = float(row["engineering_stress_ksi"])
            true_strain = math.log1p(engineering_strain)
            true_stress = engineering_stress * (1.0 + engineering_strain)
            rows.append(
                {
                    "engineering_strain": engineering_strain,
                    "engineering_stress_ksi": engineering_stress,
                    "true_strain": true_strain,
                    "true_stress_ksi": true_stress,
                }
            )
    return rows


def fit_cubic_and_yield(
    curve: list[dict],
    fit_window: list[float],
    modulus_values: list[float],
    central_modulus: float,
) -> dict:
    lower, upper = (float(value) for value in fit_window)
    midpoint = 0.5 * (lower + upper)
    half_width = 0.5 * (upper - lower)
    fit_rows = [row for row in curve if lower <= row["true_strain"] <= upper]
    x = np.array([row["true_strain"] for row in fit_rows], dtype=float)
    y = np.array([row["true_stress_ksi"] for row in fit_rows], dtype=float)
    z = (x - midpoint) / half_width if len(x) else np.array([], dtype=float)
    design = np.column_stack((z**3, z**2, z, np.ones_like(z))) if len(z) else np.empty((0, 4))
    rank = int(np.linalg.matrix_rank(design)) if len(z) else 0
    coefficients = None
    rmse = None
    rmse_fraction = None
    roots_by_modulus = []
    if len(z) >= 4 and rank == 4:
        coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        predicted = design @ coefficients
        rmse = float(np.sqrt(np.mean((predicted - y) ** 2)))
        mean_stress = float(np.mean(y))
        rmse_fraction = rmse / mean_stress if mean_stress else None
        derivative_coefficients = np.polyder(coefficients)
        for modulus in modulus_values:
            equation = coefficients.copy()
            equation[-2] -= modulus * half_width
            equation[-1] -= modulus * (midpoint - 0.01)
            candidate_roots = []
            for root in np.roots(equation):
                if abs(float(np.imag(root))) > 1e-8:
                    continue
                z_root = float(np.real(root))
                true_strain = midpoint + half_width * z_root
                if lower - 1e-10 <= true_strain <= upper + 1e-10:
                    true_stress = float(np.polyval(coefficients, z_root))
                    slope = float(np.polyval(derivative_coefficients, z_root) / half_width)
                    engineering_stress = true_stress / math.exp(true_strain)
                    candidate_roots.append(
                        {
                            "true_strain": true_strain,
                            "true_stress_ksi": true_stress,
                            "engineering_equivalent_stress_ksi": engineering_stress,
                            "cubic_slope_ksi": slope,
                            "slope_below_elastic_modulus": slope < modulus,
                        }
                    )
            qualified = sorted(
                (item for item in candidate_roots if item["slope_below_elastic_modulus"]),
                key=lambda item: item["true_strain"],
            )
            selected = qualified[0] if len(qualified) == 1 else None
            roots_by_modulus.append(
                {
                    "elastic_modulus_ksi": modulus,
                    "real_in_window_roots": candidate_roots,
                    "qualified_root_count": len(qualified),
                    "selected_root": selected,
                    "unique_selected_root": selected is not None,
                }
            )
    selected_by_modulus = {
        item["elastic_modulus_ksi"]: item["selected_root"] for item in roots_by_modulus
    }
    central = selected_by_modulus.get(central_modulus)
    selected_stresses = [
        item["selected_root"]["engineering_equivalent_stress_ksi"]
        for item in roots_by_modulus
        if item["selected_root"] is not None
    ]
    spread = None
    if central is not None and len(selected_stresses) == len(modulus_values):
        spread = (max(selected_stresses) - min(selected_stresses)) / central[
            "engineering_equivalent_stress_ksi"
        ]
    return {
        "fit_point_count": len(fit_rows),
        "polynomial_rank": rank,
        "scaled_cubic_coefficients": coefficients.tolist() if coefficients is not None else None,
        "fit_rmse_ksi": rmse,
        "fit_rmse_fraction_of_mean_true_stress": rmse_fraction,
        "roots_by_elastic_modulus": roots_by_modulus,
        "central_selected_root": central,
        "yield_spread_across_modulus_range_relative_to_central": spread,
    }


def verify_source(config: dict, project_root: Path) -> dict:
    source = next(item for item in config["sources"] if "path" in item)
    path = project_root / source["path"]
    actual = sha256(path) if path.exists() else None
    return {
        "id": source["id"],
        "path": source["path"],
        "expected_sha256": source["sha256"],
        "actual_sha256": actual,
        "passed": actual == source["sha256"],
        "source_modified": False,
    }


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100.0 * value:.2f} %"


def main() -> None:
    started = time.perf_counter()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v9c_official_ringing_method.json"
    v9b_results_path = simulation_root / "output" / "resultats_wtc1_v9b_numerisation_courbes.json"
    results_path = simulation_root / "output" / "resultats_wtc1_v9c_methode_ringing.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v9c_methode_ringing.md"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if registry_path.exists() and '"experiment_id":"WTC1-V9C"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V9C outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    v9b = json.loads(v9b_results_path.read_text(encoding="utf-8"))
    regressions = verify_regressions(config, project_root)
    source_verification = verify_source(config, project_root)
    if not regressions["passed"]:
        raise SystemExit("V9B regression verification failed before V9C")
    if not source_verification["passed"]:
        raise SystemExit("The declared read-only NIST source changed or is missing")

    method = config["ringing_aware_method"]
    gates = config["predeclared_revalidation_gates"]
    modulus_values = [float(value) for value in method["elastic_modulus_ksi_values"]]
    central_modulus = float(method["central_elastic_modulus_ksi"])
    curve_results = []
    for old in v9b["curve_results"]:
        curve = read_engineering_curve(project_root / old["csv"])
        fitted = fit_cubic_and_yield(
            curve,
            method["fit_window_true_strain"],
            modulus_values,
            central_modulus,
        )
        central_root = fitted["central_selected_root"]
        yield_strength = (
            central_root["engineering_equivalent_stress_ksi"]
            if central_root is not None
            else None
        )
        yield_error = interval_relative_error(yield_strength, old["yield_reference_interval_ksi"])
        tensile_strength = float(old["digitized_tensile_strength_ksi"])
        tensile_error = interval_relative_error(
            tensile_strength, old["tensile_reference_interval_ksi"]
        )
        fit_points_passed = fitted["fit_point_count"] >= int(
            gates["minimum_fit_points_per_curve"]
        )
        rank_passed = fitted["polynomial_rank"] == int(gates["required_polynomial_rank"])
        rmse_passed = (
            fitted["fit_rmse_fraction_of_mean_true_stress"] is not None
            and fitted["fit_rmse_fraction_of_mean_true_stress"]
            <= float(gates["maximum_fit_rmse_fraction_of_mean_true_stress"])
        )
        root_passed = central_root is not None and all(
            item["unique_selected_root"] for item in fitted["roots_by_elastic_modulus"]
        )
        modulus_sensitivity_passed = (
            fitted["yield_spread_across_modulus_range_relative_to_central"] is not None
            and fitted["yield_spread_across_modulus_range_relative_to_central"]
            <= float(gates["maximum_yield_spread_across_modulus_range_relative_to_central"])
        )
        yield_passed = yield_error is not None and yield_error <= float(
            gates["maximum_individual_yield_relative_error"]
        )
        tensile_passed = tensile_error is not None and tensile_error <= float(
            gates["maximum_individual_tensile_relative_error"]
        )
        passed = all(
            (
                fit_points_passed,
                rank_passed,
                rmse_passed,
                root_passed,
                modulus_sensitivity_passed,
                yield_passed,
                tensile_passed,
            )
        )
        curve_results.append(
            {
                "curve_id": old["curve_id"],
                "coupon_series_id": old["coupon_series_id"],
                "rate_per_s": old["rate_per_s"],
                "orientation": old["orientation"],
                "specimen_geometry": old["specimen_geometry"],
                "source_csv": old["csv"],
                "cubic_fit": fitted,
                "ringing_aware_yield_engineering_equivalent_ksi": yield_strength,
                "yield_reference_interval_ksi": old["yield_reference_interval_ksi"],
                "yield_relative_error_to_interval": yield_error,
                "unchanged_v9b_tensile_strength_ksi": tensile_strength,
                "tensile_reference_interval_ksi": old["tensile_reference_interval_ksi"],
                "tensile_relative_error_to_interval": tensile_error,
                "fit_points_passed": fit_points_passed,
                "polynomial_rank_passed": rank_passed,
                "fit_rmse_passed": rmse_passed,
                "unique_root_passed": root_passed,
                "modulus_sensitivity_passed": modulus_sensitivity_passed,
                "yield_validation_passed": yield_passed,
                "tensile_validation_passed": tensile_passed,
                "passed": passed,
            }
        )

    yield_errors = [
        item["yield_relative_error_to_interval"]
        for item in curve_results
        if item["yield_relative_error_to_interval"] is not None
    ]
    tensile_errors = [item["tensile_relative_error_to_interval"] for item in curve_results]
    median_yield = statistics.median(yield_errors) if yield_errors else None
    median_tensile = statistics.median(tensile_errors) if tensile_errors else None
    expected_count = 9
    count_passed = len(curve_results) == expected_count if gates["all_nine_curves_required"] else True
    median_yield_passed = median_yield is not None and median_yield <= float(
        gates["maximum_median_yield_relative_error"]
    )
    median_tensile_passed = median_tensile is not None and median_tensile <= float(
        gates["maximum_median_tensile_relative_error"]
    )
    revalidation_passed = all(
        (
            regressions["passed"],
            source_verification["passed"],
            count_passed,
            all(item["passed"] for item in curve_results),
            median_yield_passed,
            median_tensile_passed,
        )
    )
    failed = [item for item in curve_results if not item["passed"]]
    status = (
        "method_revalidation_passed_conditional_coupon_pending"
        if revalidation_passed
        else "validated_negative_official_method_revalidation_not_passed_coupon_not_authorized"
    )
    results = {
        "iteration": "V9C",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "status": status,
        "iteration_execution_validated": True,
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "source_verification": source_verification,
        "regressions": regressions,
        "public_raw_data_audit": config["public_raw_data_audit"],
        "ringing_aware_method": method,
        "curve_results": curve_results,
        "revalidation_gate_summary": {
            "expected_curve_count": expected_count,
            "actual_curve_count": len(curve_results),
            "curve_count_passed": count_passed,
            "passed_curve_count": sum(item["passed"] for item in curve_results),
            "failed_curve_ids": [item["curve_id"] for item in failed],
            "maximum_yield_relative_error": max(yield_errors) if yield_errors else None,
            "median_yield_relative_error": median_yield,
            "median_yield_passed": median_yield_passed,
            "maximum_tensile_relative_error": max(tensile_errors),
            "median_tensile_relative_error": median_tensile,
            "median_tensile_passed": median_tensile_passed,
            "all_individual_curves_passed": all(item["passed"] for item in curve_results),
            "revalidation_passed": revalidation_passed,
        },
        "conditional_openradioss_coupon_authorized": bool(
            revalidation_passed and config["conditional_coupon"]["authorized_only_if_revalidation_passed"]
        ),
        "openradioss_coupon_executed": False,
        "failure_deletion_executed": False,
        "fracture_calibration_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scope_gates"],
        "interpretation": "V9C identifies and implements the official NIST third-order ringing-aware yield procedure on the immutable V9B vector traces. The calculation is a method-reproduction attempt, not a reconstruction of the missing corrected raw load channels. Tensile strength remains the unchanged unfiltered V9B maximum. The conditional coupon is authorized only if every declared fit, root, modulus-sensitivity, yield and tensile gate passes.",
        "runtime": {
            "elapsed_seconds": time.perf_counter() - started,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "config_sha256": sha256(config_path),
            "runner_sha256": sha256(Path(__file__)),
            "source_archive_rescanned": False,
            "official_source_files_modified": False,
            "solver_executed": False,
            "blender_executed": False,
        },
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    table_rows = []
    for item in curve_results:
        reasons = []
        for key, label in (
            ("fit_points_passed", "points"),
            ("polynomial_rank_passed", "rang"),
            ("fit_rmse_passed", "RMSE"),
            ("unique_root_passed", "racine"),
            ("modulus_sensitivity_passed", "E"),
            ("yield_validation_passed", "Fy"),
            ("tensile_validation_passed", "TS"),
        ):
            if not item[key]:
                reasons.append(label)
        label = "PASS" if item["passed"] else "FAIL (" + ", ".join(reasons) + ")"
        table_rows.append(
            f"| {item['curve_id']} | {item['rate_per_s']:.6g} | {item['cubic_fit']['fit_point_count']} | "
            f"{item['ringing_aware_yield_engineering_equivalent_ksi'] if item['ringing_aware_yield_engineering_equivalent_ksi'] is not None else float('nan'):.2f} | "
            f"{item['yield_reference_interval_ksi'][0]:.1f}-{item['yield_reference_interval_ksi'][1]:.1f} | "
            f"{pct(item['yield_relative_error_to_interval'])} | {item['unchanged_v9b_tensile_strength_ksi']:.2f} | "
            f"{pct(item['tensile_relative_error_to_interval'])} | {label} |"
        )
    summary = results["revalidation_gate_summary"]
    report = f"""# WTC 1 - V9C : méthode officielle de traitement du ringing

## Résultat

L'exécution de V9C est **validée**. La revalidation scientifique est **{'PASS' if revalidation_passed else 'FAIL'}**. {'Toutes les portes sont franchies, mais l éprouvette OpenRadioss reste une étape suivante distincte.' if revalidation_passed else 'Au moins une porte pré-déclarée reste en échec ; aucune éprouvette OpenRadioss n est autorisée ou exécutée.'}

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D décrit environ 5 000 points acquis par essai : charge, déplacement, déformation de la zone utile, déformation côté mors et temps.
- Le signal de charge corrigé est obtenu en comparant le signal côté mors à la moyenne du capteur piézoélectrique.
- Quand le ringing empêche une lecture visuelle fiable de `Fy`, NIST ajuste un polynôme d'ordre 3 entre 1 % et 5 % de déformation et l'intersecte avec une droite élastique décalée de 1 %.
- NIST définit `TS` comme la charge maximale divisée par l'aire initiale. V9C conserve donc sans filtrage les maxima V9B.
- Les recherches exactes sur M26-C1B1-RF, C80-A-2-2 et C80-A-2-3 n'ont pas localisé les canaux bruts publics. Le dépôt NIST trouvé pour les aciers WTC concerne les courbes à haute température et vitesses quasi statiques, pas ces essais rapides à température ambiante.

## 2. Résultats d'un modèle officiel

La procédure polynomiale est une méthode officielle NIST de réduction de mesure. Son application ici ne recrée pas les signaux corrigés originaux absents.

## 3. Affirmations provenant des archives locales

Aucune affirmation nouvelle n'est tirée des archives. L'archive source n'a pas été rescannée et les sources officielles sont restées en lecture seule.

## 4. Hypothèses propres au modèle

- Les courbes d'ingénieur V9B sont converties en contrainte et déformation vraies avant l'ajustement.
- Le polynôme est ajusté par moindres carrés non pondérés, avec la coordonnée ramenée à `[-1,1]` pour la stabilité numérique.
- Faute de pente élastique individuelle lisible et de canaux bruts, `E` est testé à 28 000, 29 000 et 30 000 ksi. La valeur centrale est 29 000 ksi et la dispersion doit rester sous 5 %.
- Aucun filtre n'est ajouté à `TS` après observation des résultats.

## 5. Résultats dérivés

- Courbes passant toutes les portes : **{summary['passed_curve_count']} / 9**.
- Erreur médiane `Fy` : **{pct(summary['median_yield_relative_error'])}** ; maximum : **{pct(summary['maximum_yield_relative_error'])}**.
- Erreur médiane `TS` : **{pct(summary['median_tensile_relative_error'])}** ; maximum : **{pct(summary['maximum_tensile_relative_error'])}**.
- Courbes en échec : **{', '.join(summary['failed_curve_ids']) if summary['failed_curve_ids'] else 'aucune'}**.

| Courbe | Vitesse (/s) | Points fit | Fy V9C (ksi) | Fy table | Erreur Fy | TS inchangée (ksi) | Erreur TS | Porte |
|---|---:|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(table_rows)}

## 6. Contradictions, limites et informations manquantes

- Le rapport publie la séquence de réduction mais pas les canaux bruts, les fenêtres temporelles `t1/t2`, le module ajusté de chaque essai ni un budget d'incertitude par éprouvette.
- Une concordance avec `Fy` ne suffirait pas à qualifier la courbe plastique complète ; `TS` et la forme pré-striction doivent également franchir leurs portes.
- Une discordance persistante de `TS` ne peut pas être corrigée par le polynôme de `Fy`, car la procédure officielle définit `TS` séparément à partir du maximum de charge.

## Décision de porte

- Éprouvette OpenRadioss autorisée : **{'oui' if results['conditional_openradioss_coupon_authorized'] else 'non'}**.
- Éprouvette exécutée : **non**.
- Rupture, suppression d'éléments et impact façade : **non exécutés**.
- Avion complet, tour globale, thermique et Blender : **portes fermées**.
- Aucun mécanisme explosif ou thermite n'est testé.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2))
    print(f"RESULTS={results_path}")
    print(f"REPORT={report_path}")


if __name__ == "__main__":
    main()
