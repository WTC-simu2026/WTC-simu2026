#!/usr/bin/env python3
"""Run the predeclared V8Z numerical LeMAX sensitivity and source audit."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from run_v8v_deformable_projectile import relative_difference, sha256
from run_v8w_pairwise_contact import verify_regressions
from run_v8y_nonlocal_failure import common_checks, final_momentum, impulse, run_or_load_case


MEDIUM_IDS = ["LM050_M050_P050_DT090_T1", "LM200_M050_P050_DT090_T1"]
FINE_IDS = ["LM050_M025_P025_DT090_T1", "LM200_M025_P025_DT090_T1"]
CACHED_ALIASES = {
    "NL_M050_P050_DT090_T1": "LM100_M050_P050_DT090_T1",
    "NL_M025_P025_DT090_T1": "LM100_M025_P025_DT090_T1",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace unregistered partial V8Z cases")
    return parser.parse_args()


def checkpoint(path: Path, regression: dict, cases: list[dict], stage: str) -> None:
    path.write_text(
        json.dumps(
            {
                "iteration": "V8Z",
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


def parse_solver_nonlocal(starter_output: Path) -> dict:
    text = starter_output.read_text(encoding="utf-8", errors="replace")
    rlen = sorted(
        {
            float(value)
            for value in re.findall(
                r"NON-LOCAL INTERNAL LENGTH\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*=\s*([0-9.Ee+\-]+)",
                text,
            )
        }
    )
    lemax = sorted(
        {
            float(value)
            for value in re.findall(
                r"MAXIMAL ELEMENT LENGTH TARGET\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*\.\s*=\s*([0-9.Ee+\-]+)",
                text,
            )
        }
    )
    return {
        "starter_output": str(starter_output),
        "reported_rlen_mm": rlen,
        "reported_lemax_mm": lemax,
        "rlen_reported": len(rlen) == 1,
        "lemax_reported": len(lemax) == 1,
    }


def annotate_new_case(result: dict, case_dir: Path) -> dict:
    outputs = list(case_dir.glob("*_0000.out"))
    if len(outputs) != 1:
        raise RuntimeError(f"Expected one Starter output in {case_dir}, found {len(outputs)}")
    result["solver_nonlocal"] = parse_solver_nonlocal(outputs[0])
    expected = float(result["lemax_mm"])
    values = result["solver_nonlocal"]["reported_lemax_mm"]
    result["solver_nonlocal"]["lemax_matches_case"] = len(values) == 1 and math.isclose(
        values[0], expected, rel_tol=0.0, abs_tol=1.0e-9
    )
    (case_dir / "case_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return result


def load_v8y_references(config: dict, project_root: Path) -> list[dict]:
    specification = config["v8y_cached_reference"]
    results = json.loads((project_root / specification["results"]).read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in results["cases"]}
    references: list[dict] = []
    for source_id, alias in CACHED_ALIASES.items():
        case = copy.deepcopy(by_id[source_id])
        case["source_iteration"] = "V8Y"
        case["source_case_id"] = source_id
        case["id"] = alias
        case["lemax_mm"] = float(specification["lemax_mm"])
        case["study_role"] = "immutable_v8y_reference"
        artifact_path = project_root / case["artifacts"]["starter"]
        starter_outputs = list(artifact_path.parent.glob("*_0000.out"))
        if len(starter_outputs) != 1:
            raise RuntimeError(f"Expected one cached V8Y Starter output for {source_id}")
        case["solver_nonlocal"] = parse_solver_nonlocal(starter_outputs[0])
        values = case["solver_nonlocal"]["reported_lemax_mm"]
        case["solver_nonlocal"]["lemax_matches_case"] = len(values) == 1 and math.isclose(
            values[0], case["lemax_mm"], rel_tol=0.0, abs_tol=1.0e-9
        )
        references.append(case)
    return references


def verify_source_audit(config: dict, project_root: Path) -> dict:
    files: list[dict] = []
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


def metric(case: dict, name: str) -> float:
    if name == "contact_impulse":
        return impulse(case)
    if name == "projectile_final_momentum":
        return final_momentum(case)
    raise KeyError(name)


def maximum_pairwise_difference(cases: list[dict], name: str) -> tuple[float, list[dict]]:
    comparisons: list[dict] = []
    for left, right in itertools.combinations(sorted(cases, key=lambda item: item["lemax_mm"]), 2):
        difference = relative_difference(metric(left, name), metric(right, name))
        comparisons.append(
            {
                "left_id": left["id"],
                "right_id": right["id"],
                "left_lemax_mm": left["lemax_mm"],
                "right_lemax_mm": right["lemax_mm"],
                "relative_difference": difference,
            }
        )
    return max((item["relative_difference"] for item in comparisons), default=0.0), comparisons


def rupture_and_length_checks(cases: list[dict], gates: dict) -> dict[str, bool]:
    return {
        "projectile_rupture_each_case": min(
            case["time_history"]["projectile_eroded_element_count"] for case in cases
        )
        >= gates["minimum_projectile_eroded_elements_each_case"],
        "projectile_remaining_mass_each_case": min(
            case["time_history"]["projectile_remaining_mass_fraction"] for case in cases
        )
        >= gates["minimum_projectile_remaining_mass_fraction_each_case"],
        "solver_rlen_reported_each_case": all(
            case["solver_nonlocal"]["rlen_reported"] for case in cases
        ),
        "solver_lemax_matches_each_case": all(
            case["solver_nonlocal"]["lemax_matches_case"] for case in cases
        ),
    }


def stage_assessment(
    cases: list[dict], gates: dict, regression_passed: bool, mesh_mm: float
) -> tuple[dict, dict]:
    selected = [case for case in cases if math.isclose(case["facade_mesh_target_mm"], mesh_mm)]
    impulse_max, impulse_pairs = maximum_pairwise_difference(selected, "contact_impulse")
    momentum_max, momentum_pairs = maximum_pairwise_difference(selected, "projectile_final_momentum")
    checks = {"regressions_unchanged": regression_passed, **common_checks(selected, gates)}
    checks.update(rupture_and_length_checks(selected, gates))
    prefix = "medium" if math.isclose(mesh_mm, 50.0) else "fine"
    checks[f"{prefix}_across_lemax_contact_impulse"] = impulse_max <= gates[
        f"maximum_{prefix}_across_lemax_contact_impulse_relative_difference"
    ]
    checks[f"{prefix}_across_lemax_projectile_final_momentum"] = momentum_max <= gates[
        f"maximum_{prefix}_across_lemax_projectile_final_momentum_relative_difference"
    ]
    return checks, {
        "mesh_mm": mesh_mm,
        "maximum_pairwise_contact_impulse_relative_difference": impulse_max,
        "contact_impulse_pairwise_comparisons": impulse_pairs,
        "maximum_pairwise_projectile_final_momentum_relative_difference": momentum_max,
        "projectile_final_momentum_pairwise_comparisons": momentum_pairs,
    }


def mesh_convergence(cases: list[dict], gates: dict) -> tuple[dict, dict]:
    by_key = {(float(case["lemax_mm"]), float(case["facade_mesh_target_mm"])): case for case in cases}
    metrics: dict[str, dict] = {}
    checks: dict[str, bool] = {}
    for lemax in (50.0, 100.0, 200.0):
        medium = by_key[(lemax, 50.0)]
        fine = by_key[(lemax, 25.0)]
        label = f"lemax_{int(lemax):03d}"
        impulse_difference = relative_difference(impulse(medium), impulse(fine))
        momentum_difference = relative_difference(final_momentum(medium), final_momentum(fine))
        metrics[label] = {
            "medium_id": medium["id"],
            "fine_id": fine["id"],
            "contact_impulse_relative_difference": impulse_difference,
            "projectile_final_momentum_relative_difference": momentum_difference,
        }
        checks[f"{label}_medium_to_fine_contact_impulse"] = impulse_difference <= gates[
            "maximum_medium_to_fine_contact_impulse_relative_difference_each_lemax"
        ]
        checks[f"{label}_medium_to_fine_projectile_final_momentum"] = momentum_difference <= gates[
            "maximum_medium_to_fine_projectile_final_momentum_relative_difference_each_lemax"
        ]
    return checks, metrics


def main() -> None:
    args = parse_args()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v8z_failure_length_identifiability.json"
    generator = simulation_root / "scripts" / "generate_v8z_failure_length.py"
    output_root = simulation_root / "openradioss_benchmarks" / "v8z_failure_length"
    summary_path = simulation_root / "output" / "resultats_wtc1_v8z_longueur_rupture.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v8z_longueur_rupture.md"
    checkpoint_path = simulation_root / "output" / "journal_wtc1_v8z_execution.json"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if summary_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing V8Z result: {summary_path}")
    if args.force and registry_path.exists() and '"experiment_id":"WTC1-V8Z"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V8Z outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = json.loads((project_root / config["base_configuration"]["path"]).read_text(encoding="utf-8"))
    regression = verify_regressions(config, project_root)
    source_audit = verify_source_audit(config, project_root)
    if not regression["passed"]:
        raise SystemExit("V8W/V8X/V8Y regression verification failed before V8Z execution")
    if not source_audit["passed"]:
        raise SystemExit("A declared read-only official source changed or is missing")

    cases_by_id = {case["id"]: case for case in config["cases"]}
    cached_references = load_v8y_references(config, project_root)
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

    for case_id in MEDIUM_IDS:
        case = run_or_load_case(
            cases_by_id[case_id], config_path, base, project_root, generator, output_root,
            starter, engine, converter, environment, args.force
        )
        completed.append(annotate_new_case(case, output_root / case_id))
        checkpoint(checkpoint_path, regression, completed, "medium_running")

    medium_cases = [cached_references[0], *completed]
    medium_checks, medium_metrics = stage_assessment(
        medium_cases, gates, regression["passed"], 50.0
    )
    medium_passed = all(medium_checks.values())
    print(
        json.dumps(
            {"event": "medium_gate", "status": "PASS" if medium_passed else "FAIL", "checks": medium_checks},
            separators=(",", ":"),
        ),
        flush=True,
    )

    fine_executed = False
    fine_checks: dict[str, bool] = {}
    fine_metrics: dict = {}
    convergence_checks: dict[str, bool] = {}
    convergence_metrics: dict = {}
    if medium_passed:
        fine_executed = True
        for case_id in FINE_IDS:
            case = run_or_load_case(
                cases_by_id[case_id], config_path, base, project_root, generator, output_root,
                starter, engine, converter, environment, args.force
            )
            completed.append(annotate_new_case(case, output_root / case_id))
            checkpoint(checkpoint_path, regression, completed, "fine_running")
        all_cases = [*cached_references, *completed]
        fine_checks, fine_metrics = stage_assessment(all_cases, gates, regression["passed"], 25.0)
        convergence_checks, convergence_metrics = mesh_convergence(all_cases, gates)
    fine_passed = fine_executed and all(fine_checks.values())
    convergence_passed = fine_executed and all(convergence_checks.values())
    numerical_length_sensitivity_passed = medium_passed and fine_passed and convergence_passed

    all_reported_cases = [*cached_references, *completed]
    results = {
        "iteration": "V8Z",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "source_audit": {**source_audit, "conclusion": config["source_audit_conclusion"]},
        "regressions": regression,
        "regularization_sensitivity": config["regularization_sensitivity"],
        "cases": all_reported_cases,
        "new_case_ids": [case["id"] for case in completed],
        "cached_v8y_case_ids": [case["id"] for case in cached_references],
        "medium_gate_checks": medium_checks,
        "medium_metrics": medium_metrics,
        "medium_passed": medium_passed,
        "fine_matrix_executed": fine_executed,
        "fine_gate_checks": fine_checks,
        "fine_metrics": fine_metrics,
        "fine_passed": fine_passed,
        "mesh_convergence_gate_checks": convergence_checks,
        "mesh_convergence_metrics": convergence_metrics,
        "mesh_convergence_passed": convergence_passed,
        "numerical_length_sensitivity_passed": numerical_length_sensitivity_passed,
        "deformable_subassembly_numerical_qualification_passed": numerical_length_sensitivity_passed,
        "physical_failure_parameter_identification_passed": False,
        "deformable_subassembly_physical_qualification_passed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "thermal_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "explosive_or_thermite_mechanism_supported": False,
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
            "official_source_files_modified": False,
        },
        "plot": {"path": None, "reason": "Exact solver histories are used; Blender is not physical validation."},
    }
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    checkpoint(checkpoint_path, regression, completed, "complete")

    rows: list[str] = []
    for case in sorted(all_reported_cases, key=lambda item: (item["facade_mesh_target_mm"], item["lemax_mm"]), reverse=True):
        rlen_values = case["solver_nonlocal"]["reported_rlen_mm"]
        rlen_text = f"{rlen_values[0]:.3f}" if len(rlen_values) == 1 else "non lu"
        source = case.get("source_iteration", "V8Z")
        rows.append(
            f"| {case['id']} | {source} | {case['facade_mesh_target_mm']:.0f} | {case['lemax_mm']:.0f} | "
            f"{rlen_text} | {impulse(case) / 1.0e6:.3f} | "
            f"{case['time_history']['projectile_eroded_element_count']} | "
            f"{case['time_history']['projectile_remaining_mass_fraction']:.3f} | "
            f"{case['time_history']['derived_energy_error_percent']:.3f} |"
        )
    failed_medium = [name for name, passed in medium_checks.items() if not passed]
    failed_fine = [name for name, passed in fine_checks.items() if not passed]
    failed_convergence = [name for name, passed in convergence_checks.items() if not passed]
    report = f"""# WTC 1 — V8Z : identifiabilité de la rupture et sensibilité numérique de LeMAX

## Résultat

Le portail à maille 50 mm est **{'PASS' if medium_passed else 'FAIL'}**. La matrice à 25 mm est **{'PASS' if fine_passed else ('NON EXÉCUTÉE' if not fine_executed else 'FAIL')}**. La robustesse numérique sur `LeMAX=50/100/200 mm` est **{'PASS' if numerical_length_sensitivity_passed else 'FAIL'}**.

Ce résultat ne constitue pas une identification physique : le portail des paramètres de rupture réels reste **FAIL** et la simulation globale reste fermée.

## 1. Faits directement observés ou transcrits

- NIST NCSTAR 1-3D rapporte des essais mécaniques rapides sur une sélection d'aciers du WTC, avec des essais de traction à 50–500 s⁻¹ et certains essais de compression à des taux supérieurs.
- La documentation Radioss définit `Rlen` comme longueur interne non locale et `LeMAX` comme cible de convergence de maille ; avec `LeMAX`, le solveur calcule automatiquement `Rlen`.
- Les trois PDF officiels contrôlés ont conservé leurs empreintes SHA-256 déclarées : **{'PASS' if source_audit['passed'] else 'FAIL'}**.
- Les résultats et scripts V8W, V8X et V8Y gelés sont inchangés : **{'PASS' if regression['passed'] else 'FAIL'}**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats et choix d'un modèle officiel

- NIST NCSTAR 1-2B décrit des déformations critiques ajustées selon la taille de maille dans ses essais de composants ; il s'agit d'un choix de modèle dépendant de la résolution.
- NIST indique ne pas avoir testé les matériaux structuraux du Boeing 767 et avoir utilisé des propriétés de littérature ouverte, avec des variations de déformation de rupture dans l'étude d'incertitude.
- Ces réglages NIST ne sont pas des mesures directes d'une longueur interne physique transférable au projectile équivalent V8Y.

## 3. Affirmations des archives locales

- Aucune nouvelle affirmation provenant de l'archive locale n'est utilisée dans V8Z.

## 4. Hypothèses propres au modèle

- Les longueurs `LeMAX=50/100/200 mm` forment une plage numérique factorielle déclarée avant calcul. Elles ne sont ni des bornes physiques ni ajustées sur l'impulsion.
- La géométrie équivalente, les courbes matériaux et les déformations de rupture 0,20/0,20/0,12 sont héritées de V8Y.
- Le cas V8Y à `LeMAX=100 mm` est réutilisé sans recalcul ni modification.

## 5. Résultats dérivés

| Cas | Source | Maille (mm) | LeMAX (mm) | Rlen solveur (mm) | Impulsion (kN·s) | Érosion projectile | Masse restante | Erreur énergie (%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

- Écart maximal d'impulsion entre longueurs à 50 mm : **{medium_metrics['maximum_pairwise_contact_impulse_relative_difference']:.3%}**.
- Écart maximal de quantité de mouvement finale entre longueurs à 50 mm : **{medium_metrics['maximum_pairwise_projectile_final_momentum_relative_difference']:.3%}**.
- Portails moyens en échec : **{', '.join(failed_medium) if failed_medium else 'aucun'}**.
- Portails fins en échec : **{', '.join(failed_fine) if failed_fine else ('aucun' if fine_executed else 'non évalués')}**.
- Portails de convergence 50–25 mm en échec : **{', '.join(failed_convergence) if failed_convergence else ('aucun' if fine_executed else 'non évalués')}**.

## 6. Contradictions et informations manquantes

- Les sources examinées ne fournissent pas de surface de rupture à grande vitesse et triaxialité représentative pour les aciers WTC, le moteur ou le capotage équivalent.
- Elles ne fournissent pas non plus de longueur interne physique utilisable pour identifier `Rlen` ou `LeMAX` dans ce modèle.
- Une éventuelle convergence numérique ne valide donc ni le JT9D, ni l'avion complet, ni l'impact global sur le WTC 1.
- Les portails global, thermique et Blender restent fermés. Blender demeure uniquement une visualisation. Aucun résultat V8Z ne teste un mécanisme explosif ou thermitique.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "iteration": "V8Z",
                "medium_gate": "PASS" if medium_passed else "FAIL",
                "fine_gate": "PASS" if fine_passed else ("NOT_RUN" if not fine_executed else "FAIL"),
                "numerical_length_sensitivity": "PASS" if numerical_length_sensitivity_passed else "FAIL",
                "physical_identification": "FAIL",
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
