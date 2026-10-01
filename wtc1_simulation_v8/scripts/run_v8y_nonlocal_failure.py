#!/usr/bin/env python3
"""Run the predeclared V8Y non-local failure qualification matrix."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from run_v8v_deformable_projectile import relative_difference, sha256
from run_v8w_pairwise_contact import basic_checks, verify_regressions
from run_v8x_mesh_driver import run_case, safe_remove_case


DIAGONAL_IDS = [
    "NL_M100_P100_DT090_T1",
    "NL_M050_P050_DT090_T1",
    "NL_M025_P025_DT090_T1",
]
AUXILIARY_IDS = [
    "NL_M050_P050_DT045_T1",
    "NL_M050_P050_DT090_T4",
    "NL_M050_P050_DT090_FLO_T1",
    "NL_M050_P050_DT090_FHI_T1",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace unregistered partial V8Y cases")
    return parser.parse_args()


def impulse(case: dict) -> float:
    return float(case["time_history"]["facade_contact"]["absolute_impulse_g_mm_per_ms"])


def final_momentum(case: dict) -> float:
    return float(case["time_history"]["final_projectile_z_momentum_g_mm_per_ms"])


def johnson_rupture_summary(engine_text: str, metadata: dict) -> dict:
    matches = re.findall(
        r"RUPTURE(?: \(JOHNSON-COOK\))? OF SHELL ELEMENT\s*:\s*(\d+)\s+AT TIME\s*:\s*([0-9.Ee+\-]+)",
        engine_text,
    )
    unique_ids = {int(item[0]) for item in matches}
    by_part: dict[str, dict] = {}
    for part_id, bounds in metadata["element_ranges"].items():
        part_ids = {
            element_id
            for element_id in unique_ids
            if bounds["first"] <= element_id <= bounds["last"]
        }
        by_part[part_id] = {
            "unique_element_count": len(part_ids),
            "fraction_of_initial_part_shells": len(part_ids) / max(bounds["count"], 1),
        }
    return {
        "event_count": len(matches),
        "unique_element_count": len(unique_ids),
        "first_time_ms": min((float(item[1]) for item in matches), default=None),
        "last_time_ms": max((float(item[1]) for item in matches), default=None),
        "by_part": by_part,
        "projectile_unique_element_count": sum(
            by_part.get(part_id, {}).get("unique_element_count", 0) for part_id in ("3", "4")
        ),
        "facade_unique_element_count": sum(
            by_part.get(part_id, {}).get("unique_element_count", 0) for part_id in ("1", "2")
        ),
    }


def run_or_load_case(
    case: dict,
    config_path: Path,
    base: dict,
    project_root: Path,
    generator: Path,
    output_root: Path,
    starter: Path,
    engine: Path,
    converter: Path,
    environment: dict[str, str],
    force: bool,
) -> dict:
    case_dir = output_root / case["id"]
    cached_result = case_dir / "case_result.json"
    if cached_result.exists() and not force:
        result = json.loads(cached_result.read_text(encoding="utf-8"))
        if result.get("id") != case["id"] or not result.get("engine", {}).get("normal_termination"):
            raise RuntimeError(f"Invalid cached V8Y case result: {cached_result}")
        print(json.dumps({"event": "case_reused", "case": case["id"]}), flush=True)
        return result
    if case_dir.exists() and force:
        safe_remove_case(case_dir, output_root)
    elif case_dir.exists():
        raise RuntimeError(f"Partial V8Y case requires --force or a valid case_result.json: {case_dir}")

    result = run_case(
        case,
        config_path,
        base,
        project_root,
        generator,
        output_root,
        starter,
        engine,
        converter,
        environment,
        False,
    )
    engine_log = case_dir / "engine.log"
    result["rupture"] = johnson_rupture_summary(
        engine_log.read_text(encoding="utf-8", errors="replace"), result
    )
    cached_result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def checkpoint(path: Path, regression: dict, cases: list[dict], stage: str) -> None:
    path.write_text(
        json.dumps(
            {
                "iteration": "V8Y",
                "updated_at": datetime.now(timezone.utc).astimezone().isoformat(),
                "stage": stage,
                "regressions_passed": regression["passed"],
                "completed_case_ids": [case["id"] for case in cases],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def common_checks(cases: list[dict], gates: dict) -> dict[str, bool]:
    checks = basic_checks(cases, gates)
    checks.update(
        {
            "energy_error": max(
                abs(case["time_history"]["derived_energy_error_percent"]) for case in cases
            )
            <= gates["maximum_absolute_energy_error_percent"],
            "pre_facade_contact_energy": max(
                case["time_history"]["maximum_pre_facade_elastic_contact_energy_solver"]
                for case in cases
            )
            <= gates["maximum_pre_facade_elastic_contact_energy_solver"],
            "contact_impulse_momentum_balance": max(
                case["time_history"][
                    "facade_contact_impulse_to_projectile_momentum_change_relative_error"
                ]
                for case in cases
            )
            <= gates["maximum_contact_impulse_to_projectile_momentum_change_relative_error"],
        }
    )
    return checks


def diagonal_assessment(cases: list[dict], gates: dict, regressions_passed: bool) -> tuple[dict, dict]:
    by_id = {case["id"]: case for case in cases}
    coarse, medium, fine = (by_id[case_id] for case_id in DIAGONAL_IDS)
    convergence = {
        "coarse_to_medium_contact_impulse_relative_difference": relative_difference(
            impulse(coarse), impulse(medium)
        ),
        "medium_to_fine_contact_impulse_relative_difference": relative_difference(
            impulse(medium), impulse(fine)
        ),
        "coarse_to_medium_projectile_final_momentum_relative_difference": relative_difference(
            final_momentum(coarse), final_momentum(medium)
        ),
        "medium_to_fine_projectile_final_momentum_relative_difference": relative_difference(
            final_momentum(medium), final_momentum(fine)
        ),
    }
    checks = {"regressions_unchanged": regressions_passed, **common_checks(cases, gates)}
    checks.update(
        {
            "baseline_projectile_erosion": medium["time_history"]["projectile_eroded_element_count"]
            >= gates["baseline_minimum_projectile_eroded_elements"],
            "baseline_projectile_remaining_mass": medium["time_history"][
                "projectile_remaining_mass_fraction"
            ]
            >= gates["baseline_minimum_projectile_remaining_mass_fraction"],
            "medium_to_fine_contact_impulse": convergence[
                "medium_to_fine_contact_impulse_relative_difference"
            ]
            <= gates["medium_to_fine_contact_impulse_relative_difference"],
            "medium_to_fine_projectile_final_momentum": convergence[
                "medium_to_fine_projectile_final_momentum_relative_difference"
            ]
            <= gates["medium_to_fine_projectile_final_momentum_relative_difference"],
        }
    )
    return checks, convergence


def auxiliary_assessment(cases: list[dict], gates: dict) -> tuple[dict, dict]:
    by_id = {case["id"]: case for case in cases}
    baseline = by_id["NL_M050_P050_DT090_T1"]
    half_step = by_id["NL_M050_P050_DT045_T1"]
    threaded = by_id["NL_M050_P050_DT090_T4"]
    low = by_id["NL_M050_P050_DT090_FLO_T1"]
    high = by_id["NL_M050_P050_DT090_FHI_T1"]
    comparisons = {
        "half_time_step_contact_impulse_relative_difference": relative_difference(
            impulse(baseline), impulse(half_step)
        ),
        "half_time_step_projectile_final_momentum_relative_difference": relative_difference(
            final_momentum(baseline), final_momentum(half_step)
        ),
        "thread_repeatability_contact_impulse_relative_difference": relative_difference(
            impulse(baseline), impulse(threaded)
        ),
        "thread_repeatability_projectile_final_momentum_relative_difference": relative_difference(
            final_momentum(baseline), final_momentum(threaded)
        ),
    }
    ordering = {
        "low_eroded_elements": low["time_history"]["projectile_eroded_element_count"],
        "baseline_eroded_elements": baseline["time_history"]["projectile_eroded_element_count"],
        "high_eroded_elements": high["time_history"]["projectile_eroded_element_count"],
    }
    ordering["passed"] = (
        ordering["low_eroded_elements"]
        >= ordering["baseline_eroded_elements"]
        >= ordering["high_eroded_elements"]
    )
    checks = common_checks(cases, gates)
    checks.update(
        {
            "projectile_failure_ordering": ordering["passed"]
            if gates["projectile_failure_ordering_required"]
            else True,
            "half_time_step_contact_impulse": comparisons[
                "half_time_step_contact_impulse_relative_difference"
            ]
            <= gates["half_time_step_contact_impulse_relative_difference"],
            "half_time_step_projectile_final_momentum": comparisons[
                "half_time_step_projectile_final_momentum_relative_difference"
            ]
            <= gates["half_time_step_projectile_final_momentum_relative_difference"],
            "thread_repeatability_contact_impulse": comparisons[
                "thread_repeatability_contact_impulse_relative_difference"
            ]
            <= gates["thread_repeatability_contact_impulse_relative_difference"],
            "thread_repeatability_projectile_final_momentum": comparisons[
                "thread_repeatability_projectile_final_momentum_relative_difference"
            ]
            <= gates["thread_repeatability_projectile_final_momentum_relative_difference"],
        }
    )
    return checks, {"comparisons": comparisons, "projectile_failure_ordering": ordering}


def main() -> None:
    args = parse_args()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v8y_nonlocal_failure_regularization.json"
    generator = simulation_root / "scripts" / "generate_v8y_nonlocal_failure.py"
    output_root = simulation_root / "openradioss_benchmarks" / "v8y_nonlocal_failure"
    summary_path = simulation_root / "output" / "resultats_wtc1_v8y_rupture_nonlocale.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v8y_rupture_nonlocale.md"
    checkpoint_path = simulation_root / "output" / "journal_wtc1_v8y_execution.json"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if summary_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing V8Y result: {summary_path}")
    if args.force and registry_path.exists() and '"experiment_id":"WTC1-V8Y"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V8Y outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = json.loads((project_root / config["base_configuration"]["path"]).read_text(encoding="utf-8"))
    regression = verify_regressions(config, project_root)
    if not regression["passed"]:
        raise SystemExit("V8W/V8X regression verification failed before V8Y execution")
    cases_by_id = {case["id"]: case for case in config["cases"]}
    runtime_root = simulation_root / "openradioss_runtime" / "v20260728-win64"
    starter = runtime_root / "starter_win64.exe"
    engine = runtime_root / "engine_win64.exe"
    converter = runtime_root / "th_to_csv_win64.exe"
    for executable in (starter, engine, converter):
        if not executable.exists():
            raise SystemExit(f"Missing runtime executable: {executable}")
    environment = os.environ.copy()
    environment.update(
        {
            "OPENRADIOSS_PATH": r"C:\OpenRadioss",
            "RAD_CFG_PATH": r"C:\OpenRadioss\hm_cfg_files",
            "RAD_H3D_PATH": r"C:\OpenRadioss\extlib\h3d\lib\win64",
            "KMP_STACKSIZE": "400m",
        }
    )
    output_root.mkdir(parents=True, exist_ok=True)
    simulation_root.joinpath("output").mkdir(parents=True, exist_ok=True)
    completed: list[dict] = []
    started = time.perf_counter()
    gates = config["predeclared_gates"]

    for case_id in DIAGONAL_IDS:
        completed.append(
            run_or_load_case(
                cases_by_id[case_id], config_path, base, project_root, generator, output_root,
                starter, engine, converter, environment, args.force
            )
        )
        checkpoint(checkpoint_path, regression, completed, "diagonal_running")
    diagonal_cases = [case for case in completed if case["id"] in DIAGONAL_IDS]
    diagonal_checks, convergence = diagonal_assessment(diagonal_cases, gates, regression["passed"])
    diagonal_passed = all(diagonal_checks.values())
    print(
        json.dumps(
            {"event": "diagonal_gate", "status": "PASS" if diagonal_passed else "FAIL", "checks": diagonal_checks},
            separators=(",", ":"),
        ),
        flush=True,
    )

    auxiliary_executed = False
    auxiliary_checks: dict[str, bool] = {}
    auxiliary_metrics: dict = {}
    if diagonal_passed:
        auxiliary_executed = True
        for case_id in AUXILIARY_IDS:
            completed.append(
                run_or_load_case(
                    cases_by_id[case_id], config_path, base, project_root, generator, output_root,
                    starter, engine, converter, environment, args.force
                )
            )
            checkpoint(checkpoint_path, regression, completed, "auxiliary_running")
        auxiliary_checks, auxiliary_metrics = auxiliary_assessment(completed, gates)
    auxiliary_passed = auxiliary_executed and all(auxiliary_checks.values())
    qualification_passed = diagonal_passed and auxiliary_passed

    results = {
        "iteration": "V8Y",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "regressions": regression,
        "regularization": config["regularization"],
        "cases": completed,
        "diagonal_gate_checks": diagonal_checks,
        "diagonal_convergence": convergence,
        "diagonal_passed": diagonal_passed,
        "auxiliary_matrix_executed": auxiliary_executed,
        "auxiliary_gate_checks": auxiliary_checks,
        "auxiliary_metrics": auxiliary_metrics,
        "deformable_subassembly_numerical_qualification_passed": qualification_passed,
        "physical_failure_parameter_identification_passed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "runtime": {
            "total_elapsed_seconds": time.perf_counter() - started,
            "starter_sha256": sha256(starter),
            "engine_sha256": sha256(engine),
            "converter_sha256": sha256(converter),
            "config_sha256": sha256(config_path),
            "generator_sha256": sha256(generator),
            "runner_sha256": sha256(Path(__file__)),
            "source_installation_modified": False,
            "system32_modified": False,
            "source_archive_rescanned": False,
        },
        "plot": {"path": None, "reason": "Exact solver histories are used; Blender is not physical validation."},
    }
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    checkpoint(checkpoint_path, regression, completed, "complete")

    rows = []
    for case in completed:
        rows.append(
            f"| {case['id']} | {case['facade_mesh_target_mm']:.0f} | {case['projectile_mesh_target_mm']:.0f} | "
            f"{impulse(case) / 1.0e6:.3f} | {case['time_history']['projectile_eroded_element_count']} | "
            f"{case['rupture']['facade_unique_element_count']} | {case['time_history']['derived_energy_error_percent']:.3f} |"
        )
    failed_diagonal = [name for name, passed in diagonal_checks.items() if not passed]
    failed_auxiliary = [name for name, passed in auxiliary_checks.items() if not passed]
    report = f"""# WTC 1 — V8Y : rupture non-locale et convergence de l'impulsion

## Résultat

Le portail diagonal V8Y est **{'PASS' if diagonal_passed else 'FAIL'}**. La matrice auxiliaire est **{'PASS' if auxiliary_passed else ('NON EXECUTÉE' if not auxiliary_executed else 'FAIL')}**. La qualification numérique limitée du sous-ensemble est **{'PASS' if qualification_passed else 'FAIL'}**.

L'écart d'impulsion 50–25 mm vaut **{convergence['medium_to_fine_contact_impulse_relative_difference']:.3%}**, pour un seuil inchangé de 10 %. La longueur `LeMAX=100 mm` est un bornage numérique déclaré, pas une longueur de fracture mesurée.

## 1. Faits directement documentés

- La documentation officielle Radioss décrit `/NONLOCAL/MAT` comme une régularisation de la déformation plastique visant la convergence en taille et orientation de maille pour `Le <= LeMAX`.
- La documentation liste `/FAIL/JOHNSON` parmi les critères compatibles et définit l'endommagement accumulé par incréments de déformation plastique.
- Les empreintes et métriques V8W/V8X sont inchangées : **{'PASS' if regression['passed'] else 'FAIL'}**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats d'un modèle officiel

- Aucun nouveau résultat NIST n'est utilisé comme cible. V8Y compare uniquement des variantes du sous-modèle OpenRadioss.

## 3. Affirmations des archives locales

- Aucune nouvelle affirmation d'archive n'est introduite dans cette itération.

## 4. Hypothèses propres au modèle

- La façade réduite, le noyau/capotage équivalent et leurs courbes de contrainte restent ceux de V8W.
- Les déformations de rupture 0,20/0,20/0,12 sont des hypothèses héritées. Elles sont déplacées de LAW2 vers un critère JOHNSON constant, sans recalage sur l'impulsion.
- `LeMAX=100 mm` borne les trois maillages testés mais n'est pas identifié par essais de matériau.

## 5. Résultats dérivés

| Cas | Maille façade (mm) | Maille projectile (mm) | Impulsion (kN·s) | Érosion projectile | Ruptures façade | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

- Écart impulsion 100–50 mm : **{convergence['coarse_to_medium_contact_impulse_relative_difference']:.3%}**.
- Écart impulsion 50–25 mm : **{convergence['medium_to_fine_contact_impulse_relative_difference']:.3%}**.
- Écart moment final 50–25 mm : **{convergence['medium_to_fine_projectile_final_momentum_relative_difference']:.3%}**.
- Portails diagonaux en échec : **{', '.join(failed_diagonal) if failed_diagonal else 'aucun'}**.
- Portails auxiliaires en échec : **{', '.join(failed_auxiliary) if failed_auxiliary else ('aucun' if auxiliary_executed else 'non évalués')}**.

## 6. Contradictions et informations manquantes

- Une convergence numérique avec une longueur non-locale heuristique ne valide pas la rupture réelle d'un JT9D, du capotage ou du panneau 124.
- Les courbes de rupture à grande vitesse, la longueur interne physique, le contact arête-arête, les ailes, le carburant, le fuselage et la façade globale restent inconnus ou non qualifiés.
- Le portail global WTC 1, le thermique et Blender restent fermés. Blender demeure une visualisation seulement.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "iteration": "V8Y",
                "diagonal_gate": "PASS" if diagonal_passed else "FAIL",
                "auxiliary_gate": "PASS" if auxiliary_passed else ("NOT_RUN" if not auxiliary_executed else "FAIL"),
                "qualification": "PASS" if qualification_passed else "FAIL",
                "results": str(summary_path),
                "report": str(report_path),
                "runtime_seconds": results["runtime"]["total_elapsed_seconds"],
            },
            separators=(",", ":"),
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
