#!/usr/bin/env python3
"""Run the predeclared V8X mesh-driver and no-erosion diagnostic."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from run_v8v_deformable_projectile import parse_cycle_record, relative_difference, run_process, sha256
from run_v8w_pairwise_contact import read_time_history, rupture_summary, verify_regressions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace unregistered V8X outputs only")
    return parser.parse_args()


def safe_remove_case(case_dir: Path, output_root: Path) -> None:
    resolved_case = case_dir.resolve()
    resolved_root = output_root.resolve()
    if resolved_case == resolved_root or resolved_root not in resolved_case.parents:
        raise RuntimeError(f"Refusing unsafe recursive removal: {resolved_case}")
    shutil.rmtree(resolved_case)


def run_case(
    case: dict,
    study_path: Path,
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
    if case_dir.exists():
        if not force:
            raise RuntimeError(f"Existing unregistered V8X case requires --force: {case_dir}")
        safe_remove_case(case_dir, output_root)
    case_dir.mkdir(parents=True)
    generation = run_process(
        Path(os.sys.executable),
        [
            str(generator),
            "--config",
            str(study_path),
            "--case-id",
            case["id"],
            "--output",
            str(case_dir),
        ],
        project_root,
        environment,
        case_dir / "generation.log",
    )
    if generation["exit_code"] != 0:
        raise RuntimeError(f"Generator failed for {case['id']}")
    metadata = json.loads((case_dir / "generation_metadata.json").read_text(encoding="utf-8"))
    run_name = metadata["run_name"]
    case_environment = environment.copy()
    case_environment["OMP_NUM_THREADS"] = str(case["threads"])
    starter_run = run_process(
        starter,
        ["-i", f"{run_name}_0000.rad", "-np", "1"],
        case_dir,
        case_environment,
        case_dir / "starter.log",
    )
    if starter_run["exit_code"] != 0:
        raise RuntimeError(f"Starter failed for {case['id']}")
    engine_run = run_process(
        engine,
        ["-i", f"{run_name}_0001.rad"],
        case_dir,
        case_environment,
        case_dir / "engine.log",
    )
    if engine_run["exit_code"] != 0:
        raise RuntimeError(f"Engine failed for {case['id']}")
    converter_run = run_process(
        converter,
        [f"{run_name}T01"],
        case_dir,
        case_environment,
        case_dir / "converter.log",
    )
    if converter_run["exit_code"] != 0:
        raise RuntimeError(f"Time-history conversion failed for {case['id']}")

    engine_output = case_dir / f"{run_name}_0001.out"
    engine_output_text = engine_output.read_text(encoding="utf-8", errors="replace")
    initial_penetrations = [
        int(value)
        for value in re.findall(
            r"THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS", starter_run["stdout"]
        )
    ]
    result = {
        **case,
        **metadata,
        "starter": {
            "exit_code": starter_run["exit_code"],
            "elapsed_seconds": starter_run["elapsed_seconds"],
            "warning_count": starter_run["stdout"].count("WARNING ID"),
            "initial_penetration_warning_count": len(initial_penetrations),
            "initial_penetrating_node_count": sum(initial_penetrations),
        },
        "engine": {
            "exit_code": engine_run["exit_code"],
            "elapsed_seconds": engine_run["elapsed_seconds"],
            "normal_termination": "NORMAL TERMINATION" in engine_output_text,
            "last_printed_cycle": parse_cycle_record(engine_output_text),
        },
        "time_history": read_time_history(
            case_dir / f"{run_name}T01.csv", base["projectile"], "facade_impact"
        ),
        "rupture": rupture_summary(engine_run["stdout"], metadata),
        "artifacts": {
            "starter": str((case_dir / f"{run_name}_0000.rad").relative_to(project_root)).replace("\\", "/"),
            "engine": str((case_dir / f"{run_name}_0001.rad").relative_to(project_root)).replace("\\", "/"),
            "time_history_csv": str((case_dir / f"{run_name}T01.csv").relative_to(project_root)).replace("\\", "/"),
            "engine_output": str(engine_output.relative_to(project_root)).replace("\\", "/"),
        },
    }
    print(
        json.dumps(
            {
                "event": "case_completed",
                "case": case["id"],
                "erosion_mode": case["erosion_mode"],
                "normal_termination": result["engine"]["normal_termination"],
                "elapsed_seconds": result["engine"]["elapsed_seconds"],
            }
        ),
        flush=True,
    )
    return result


def impulse(case: dict) -> float:
    return float(case["time_history"]["facade_contact"]["absolute_impulse_g_mm_per_ms"])


def fixed_other_sensitivity(coarse: dict, medium: dict, fine: dict) -> dict:
    return {
        "coarse_impulse_g_mm_per_ms": impulse(coarse),
        "medium_impulse_g_mm_per_ms": impulse(medium),
        "fine_impulse_g_mm_per_ms": impulse(fine),
        "coarse_to_medium_relative_difference": relative_difference(impulse(coarse), impulse(medium)),
        "medium_to_fine_relative_difference": relative_difference(impulse(medium), impulse(fine)),
    }


def cross_sensitivity(
    facade_coarse: dict,
    baseline: dict,
    facade_fine: dict,
    projectile_coarse: dict,
    projectile_fine: dict,
) -> dict:
    facade = fixed_other_sensitivity(facade_coarse, baseline, facade_fine)
    projectile = fixed_other_sensitivity(projectile_coarse, baseline, projectile_fine)
    facade_driver = facade["medium_to_fine_relative_difference"]
    projectile_driver = projectile["medium_to_fine_relative_difference"]
    if facade_driver > 1.2 * projectile_driver:
        classification = "facade_mesh_dominant_in_tested_50_to_25_step"
    elif projectile_driver > 1.2 * facade_driver:
        classification = "projectile_mesh_dominant_in_tested_50_to_25_step"
    else:
        classification = "coupled_or_similar_mesh_sensitivity_in_tested_50_to_25_step"
    return {
        "facade_mesh_at_fixed_50mm_projectile": facade,
        "projectile_mesh_at_fixed_50mm_facade": projectile,
        "classification_rule_ratio": 1.2,
        "classification": classification,
    }


def executed_basic_checks(cases: list[dict], gates: dict) -> dict:
    return {
        "all_executed_starter_exit_code_zero": all(case["starter"]["exit_code"] == 0 for case in cases),
        "all_executed_engine_exit_code_zero": all(case["engine"]["exit_code"] == 0 for case in cases),
        "all_executed_normal_termination": all(case["engine"]["normal_termination"] for case in cases),
        "initial_penetrations": max(case["starter"]["initial_penetrating_node_count"] for case in cases)
        <= gates["maximum_initial_penetrating_node_count"],
        "energy_error": max(abs(case["time_history"]["derived_energy_error_percent"]) for case in cases)
        <= gates["maximum_absolute_energy_error_percent"],
        "added_mass": max(case["time_history"]["added_mass_fraction"] for case in cases)
        <= gates["maximum_added_mass_fraction"],
        "hourglass_energy": max(
            case["time_history"]["hourglass_to_initial_energy_fraction"] for case in cases
        )
        <= gates["maximum_hourglass_to_initial_energy_fraction"],
        "pre_facade_contact_energy": max(
            case["time_history"]["maximum_pre_facade_elastic_contact_energy_solver"] for case in cases
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


def checkpoint(path: Path, regression: dict, cases: list[dict], stage: str) -> None:
    path.write_text(
        json.dumps(
            {
                "iteration": "V8X",
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


def main() -> None:
    args = parse_args()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    study_path = simulation_root / "data" / "v8x_mesh_driver_diagnostic.json"
    generator = simulation_root / "scripts" / "generate_v8x_mesh_driver.py"
    output_root = simulation_root / "openradioss_benchmarks" / "v8x_mesh_driver"
    summary_path = simulation_root / "output" / "resultats_wtc1_v8x_mailles_erosion.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v8x_mailles_erosion.md"
    checkpoint_path = simulation_root / "output" / "journal_wtc1_v8x_execution.json"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if summary_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing V8X result: {summary_path}")
    if args.force and registry_path.exists() and '"experiment_id":"WTC1-V8X"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V8X outputs")

    study = json.loads(study_path.read_text(encoding="utf-8"))
    base_path = project_root / study["base_configuration"]["path"]
    if sha256(base_path) != study["base_configuration"]["sha256"]:
        raise SystemExit("V8W base configuration hash mismatch")
    base = json.loads(base_path.read_text(encoding="utf-8"))
    regression = verify_regressions(study, project_root)
    if not regression["passed"]:
        raise SystemExit("V8W regression failed before V8X execution")

    v8w_results_path = simulation_root / "output" / "resultats_wtc1_v8w_contact_pairwise.json"
    v8w_results = json.loads(v8w_results_path.read_text(encoding="utf-8"))
    v8w_by_id = {case["id"]: case for case in v8w_results["cases"]}
    cached = {
        key: v8w_by_id[case_id] for key, case_id in study["cached_v8w_cases"].items()
    }

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
    by_case_id = {case["id"]: case for case in study["cases"]}
    executed: list[dict] = []
    overall_started = time.perf_counter()

    stage1_ids = ["E_F100_P050", "E_F025_P050", "E_F050_P100", "E_F050_P025"]
    for case_id in stage1_ids:
        executed.append(
            run_case(
                by_case_id[case_id], study_path, base, project_root, generator, output_root,
                starter, engine, converter, environment, args.force
            )
        )
        checkpoint(checkpoint_path, regression, executed, "erosion_cross_running")
    executed_by_id = {case["id"]: case for case in executed}
    erosion_cross = cross_sensitivity(
        executed_by_id["E_F100_P050"],
        cached["F050_P050"],
        executed_by_id["E_F025_P050"],
        executed_by_id["E_F050_P100"],
        executed_by_id["E_F050_P025"],
    )
    print(json.dumps({"event": "erosion_cross_complete", "result": erosion_cross}), flush=True)

    stage2_ids = ["N_F100_P100", "N_F050_P050", "N_F025_P025"]
    for case_id in stage2_ids:
        executed.append(
            run_case(
                by_case_id[case_id], study_path, base, project_root, generator, output_root,
                starter, engine, converter, environment, args.force
            )
        )
        checkpoint(checkpoint_path, regression, executed, "non_eroding_diagonal_running")
    executed_by_id = {case["id"]: case for case in executed}
    non_eroding_diagonal = fixed_other_sensitivity(
        executed_by_id["N_F100_P100"],
        executed_by_id["N_F050_P050"],
        executed_by_id["N_F025_P025"],
    )
    gates = study["predeclared_gates"]
    non_eroding_diagonal_passed = (
        non_eroding_diagonal["medium_to_fine_relative_difference"]
        <= gates["non_eroding_medium_to_fine_contact_impulse_relative_difference"]
    )
    print(
        json.dumps(
            {
                "event": "non_eroding_diagonal_gate",
                "status": "PASS" if non_eroding_diagonal_passed else "FAIL",
                "result": non_eroding_diagonal,
            }
        ),
        flush=True,
    )

    conditional_executed = False
    non_eroding_cross = None
    if not non_eroding_diagonal_passed:
        conditional_executed = True
        stage3_ids = ["NC_F100_P050", "NC_F025_P050", "NC_F050_P100", "NC_F050_P025"]
        for case_id in stage3_ids:
            executed.append(
                run_case(
                    by_case_id[case_id], study_path, base, project_root, generator, output_root,
                    starter, engine, converter, environment, args.force
                )
            )
            checkpoint(checkpoint_path, regression, executed, "non_eroding_cross_running")
        executed_by_id = {case["id"]: case for case in executed}
        non_eroding_cross = cross_sensitivity(
            executed_by_id["NC_F100_P050"],
            executed_by_id["N_F050_P050"],
            executed_by_id["NC_F025_P050"],
            executed_by_id["NC_F050_P100"],
            executed_by_id["NC_F050_P025"],
        )

    non_eroding_cases = [
        case for case in executed if case["erosion_mode"] == "law2_default_non_eroding"
    ]
    basic_checks = executed_basic_checks(executed, gates)
    gate_checks = {
        "v8w_regressions_unchanged": regression["passed"],
        **basic_checks,
        "non_eroding_zero_erosion": max(
            case["time_history"]["projectile_eroded_element_count"]
            + case["rupture"]["facade_unique_element_count"]
            for case in non_eroding_cases
        )
        <= gates["non_eroding_maximum_eroded_elements"],
        "non_eroding_medium_to_fine_contact_impulse": non_eroding_diagonal_passed,
        "immutable_eroding_medium_to_fine_contact_impulse": v8w_results["convergence"][
            "medium_to_fine_contact_impulse_relative_difference"
        ]
        <= gates["unchanged_eroding_medium_to_fine_contact_impulse_relative_difference"],
    }
    diagnostic_completed = all(
        value for name, value in gate_checks.items() if name != "immutable_eroding_medium_to_fine_contact_impulse"
    )
    if non_eroding_diagonal_passed:
        driver_classification = {
            "principal_tested_driver": "unregularized_strain_to_failure_erosion",
            "basis": "The immutable eroding diagonal fails 10 percent while the non-eroding diagonal passes it.",
            "classification": "derived_diagnostic_inference_not_real_event_fact",
        }
    else:
        driver_classification = {
            "principal_tested_driver": non_eroding_cross["classification"] if non_eroding_cross else "unresolved",
            "basis": "The non-eroding diagonal also fails; the conditional fixed-other-mesh cross matrix controls the classification.",
            "classification": "derived_diagnostic_inference_not_real_event_fact",
        }

    results = {
        "iteration": "V8X",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(study_path.relative_to(project_root)).replace("\\", "/"),
        "scope": study["dataset"]["scope"],
        "regressions": regression,
        "cached_v8w_diagonal_case_ids": study["cached_v8w_cases"],
        "executed_cases": executed,
        "conditional_non_eroding_cross_executed": conditional_executed,
        "erosion_enabled_cross_sensitivity": erosion_cross,
        "non_eroding_diagonal": non_eroding_diagonal,
        "non_eroding_cross_sensitivity": non_eroding_cross,
        "driver_classification": driver_classification,
        "gate_checks": gate_checks,
        "mesh_sensitivity_diagnostic_completed": diagnostic_completed,
        "deformable_subassembly_qualification_passed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "runtime": {
            "total_elapsed_seconds": time.perf_counter() - overall_started,
            "starter_sha256": sha256(starter),
            "engine_sha256": sha256(engine),
            "converter_sha256": sha256(converter),
            "config_sha256": sha256(study_path),
            "generator_sha256": sha256(generator),
            "runner_sha256": sha256(Path(__file__)),
            "source_installation_modified": False,
            "system32_modified": False,
            "source_archive_rescanned": False,
        },
        "plot": {
            "path": None,
            "reason": "The diagnostic is expressed by exact mesh-to-impulse mappings; Blender and visual similarity are not used."
        },
    }
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    checkpoint(checkpoint_path, regression, executed, "complete")

    executed_rows = []
    for case in executed:
        th = case["time_history"]
        executed_rows.append(
            f"| {case['id']} | {case['facade_mesh_target_mm']:.0f} | {case['projectile_mesh_target_mm']:.0f} | "
            f"{case['erosion_mode']} | {impulse(case) / 1.0e6:.3f} | "
            f"{th['projectile_eroded_element_count'] + case['rupture']['facade_unique_element_count']} | "
            f"{th['derived_energy_error_percent']:.3f} |"
        )
    report = f"""# WTC 1 — V8X : origine de la sensibilité de maille de l'impulsion

## Résultat

Le diagnostic V8X est **{'PASS' if diagnostic_completed else 'FAIL'}** comme expérience de localisation. Le projectile/façade déformable reste **NON QUALIFIÉ**, car le cas érodant V8W conserve un écart d'impulsion 50–25 mm de **{v8w_results['convergence']['medium_to_fine_contact_impulse_relative_difference']:.3%}**, supérieur au seuil inchangé de 10 %.

Le contrôle sans érosion donne un écart 50–25 mm de **{non_eroding_diagonal['medium_to_fine_relative_difference']:.3%}** et son portail est **{'PASS' if non_eroding_diagonal_passed else 'FAIL'}**. La classification dérivée est : **{driver_classification['principal_tested_driver']}**. C'est une inférence limitée à ces sous-modèles, pas un fait sur l'impact réel.

## 1. Faits directement documentés

- La documentation officielle Radioss indique que LAW2 possède un critère intégré de déformation plastique maximale et que sa valeur par défaut est `1e20`. Les cas `N_`/`NC_` utilisent `EPSmax=0`, qui appelle ce défaut et désactive donc pratiquement l'érosion sur la durée testée.
- V8W et ses résultats sont inchangés selon les empreintes et métriques gelées : **{'PASS' if regression['passed'] else 'FAIL'}**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats d'un modèle officiel

- Aucun nouveau résultat NIST n'est utilisé comme cible. V8X compare seulement des variantes du même sous-modèle OpenRadioss.

## 3. Hypothèses propres au modèle

- La façade trois colonnes par trois étages, le noyau/capotage carrés, les matériaux et les deux contacts pairwise restent ceux de V8W.
- Le contrôle sans érosion n'est pas une loi de rupture réelle ; c'est un cas limite numérique destiné à séparer l'effet de suppression d'éléments de celui de la discrétisation du contact.
- Les seuils ne sont pas recalés sur les résultats : le portail d'impulsion reste fixé à 10 %.

## 4. Résultats dérivés

| Cas exécuté | Maille façade (mm) | Maille projectile (mm) | Mode | Impulsion façade (kN·s) | Éléments érodés | Erreur énergie (%) |
|---|---:|---:|---|---:|---:|---:|
{chr(10).join(executed_rows)}

### Matrice érodante, variable isolée

- Façade 100/50/25 mm avec projectile 50 mm : **{erosion_cross['facade_mesh_at_fixed_50mm_projectile']['coarse_impulse_g_mm_per_ms']/1e6:.3f} / {erosion_cross['facade_mesh_at_fixed_50mm_projectile']['medium_impulse_g_mm_per_ms']/1e6:.3f} / {erosion_cross['facade_mesh_at_fixed_50mm_projectile']['fine_impulse_g_mm_per_ms']/1e6:.3f} kN·s** ; écart 50–25 mm **{erosion_cross['facade_mesh_at_fixed_50mm_projectile']['medium_to_fine_relative_difference']:.3%}**.
- Projectile 100/50/25 mm avec façade 50 mm : **{erosion_cross['projectile_mesh_at_fixed_50mm_facade']['coarse_impulse_g_mm_per_ms']/1e6:.3f} / {erosion_cross['projectile_mesh_at_fixed_50mm_facade']['medium_impulse_g_mm_per_ms']/1e6:.3f} / {erosion_cross['projectile_mesh_at_fixed_50mm_facade']['fine_impulse_g_mm_per_ms']/1e6:.3f} kN·s** ; écart 50–25 mm **{erosion_cross['projectile_mesh_at_fixed_50mm_facade']['medium_to_fine_relative_difference']:.3%}**.

### Contrôle sans érosion

- Diagonale 100/50/25 mm : **{non_eroding_diagonal['coarse_impulse_g_mm_per_ms']/1e6:.3f} / {non_eroding_diagonal['medium_impulse_g_mm_per_ms']/1e6:.3f} / {non_eroding_diagonal['fine_impulse_g_mm_per_ms']/1e6:.3f} kN·s** ; écart 50–25 mm **{non_eroding_diagonal['medium_to_fine_relative_difference']:.3%}**.
- Matrice croisée conditionnelle : **{'exécutée' if conditional_executed else 'non requise, car la diagonale sans érosion passe le portail de 10 %'}**.

## 5. Contradictions, inconnues et décision

- La géométrie et la rupture réelles du JT9D, le bordereau exact du panneau 124, le contact arête-arête, les ailes, le carburant et le fuselage restent inconnus ou non qualifiés.
- Supprimer l'érosion peut améliorer la convergence tout en supprimant une physique importante ; un résultat convergé sans rupture n'est donc pas une validation physique de l'impact.
- Une formulation de rupture régularisée par taille d'élément exige des données ou bornes de fracture explicites. Elle ne doit pas être inventée ni ajustée pour reproduire une impulsion souhaitée.
- Le portail global WTC 1, le thermique et Blender restent fermés. Blender demeure une visualisation seulement.

La prochaine itération doit conserver ces diagnostics et tester uniquement une rupture régularisée sourcée ou explicitement bornée, puis répéter le seuil de convergence de 10 % et l'ordre de rupture avant toute extension globale.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": "PASS" if diagnostic_completed else "FAIL",
                "non_eroding_impulse_gate": "PASS" if non_eroding_diagonal_passed else "FAIL",
                "driver": driver_classification["principal_tested_driver"],
                "results": str(summary_path),
                "report": str(report_path),
                "runtime_seconds": results["runtime"]["total_elapsed_seconds"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
