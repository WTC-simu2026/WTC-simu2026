#!/usr/bin/env python3
"""Run and audit the V8U OpenRadioss impact-surrogate matrix."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace an unregistered V8U output matrix")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_process(executable: Path, arguments: list[str], cwd: Path, environment: dict[str, str], log: Path) -> dict:
    started = time.perf_counter()
    completed = subprocess.run(
        [str(executable), *arguments],
        cwd=str(cwd),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    elapsed = time.perf_counter() - started
    log.write_text(completed.stdout, encoding="utf-8", newline="\n")
    return {"exit_code": completed.returncode, "elapsed_seconds": elapsed, "stdout": completed.stdout}


def relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1.0e-30)


def parse_cycle_record(output_text: str) -> dict | None:
    records: list[dict] = []
    for line in output_text.splitlines():
        tokens = line.strip().split()
        if len(tokens) < 13 or not tokens[0].isdigit() or not tokens[5].endswith("%"):
            continue
        try:
            records.append(
                {
                    "line": line.rstrip(),
                    "cycle": int(tokens[0]),
                    "time_ms": float(tokens[1]),
                    "time_step_ms": float(tokens[2]),
                    "element_type": tokens[3],
                    "element_id": int(tokens[4]),
                    "energy_error_percent": float(tokens[5][:-1]),
                    "internal_energy_solver": float(tokens[6]),
                    "translational_kinetic_energy_solver": float(tokens[7]),
                    "rotational_kinetic_energy_solver": float(tokens[8]),
                    "external_work_solver": float(tokens[9]),
                    "mass_error": float(tokens[10]),
                    "total_mass_g": float(tokens[11]),
                    "added_mass_g": float(tokens[12]),
                }
            )
        except ValueError:
            continue
    return records[-1] if records else None


def read_time_history(csv_path: Path, projectile: dict) -> dict:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 2:
        raise RuntimeError(f"Time history too short: {csv_path}")
    rw_columns = [name for name in rows[0] if name.startswith("TH_RWALL_ENGINE_SURROGATE")]
    if len(rw_columns) != 1:
        raise RuntimeError(f"Expected one rigid-wall time-history channel, got {rw_columns}")
    rw_column = rw_columns[0]
    first, last = rows[0], rows[-1]
    initial_impulse = float(first[rw_column])
    final_impulse = float(last[rw_column])
    delta_impulse = final_impulse - initial_impulse
    mass_g = float(projectile["mass_g"])
    initial_velocity = float(projectile["initial_velocity_z_mm_per_ms"])
    final_velocity = initial_velocity + delta_impulse / mass_g
    initial_total = (
        float(first["INTERNAL ENERGY"])
        + float(first["KINETIC ENERGY"])
        + float(first["ROTATION ENERGY"])
    )
    final_total = (
        float(last["INTERNAL ENERGY"])
        + float(last["KINETIC ENERGY"])
        + float(last["ROTATION ENERGY"])
    )
    external_work = float(last["EXTERNAL WORK"])
    derived_energy_error = 100.0 * (final_total - initial_total - external_work) / max(abs(initial_total), 1.0e-30)
    return {
        "row_count": len(rows),
        "time_final_ms": float(last["time"]),
        "rigid_wall_channel": rw_column,
        "initial_normal_impulse_g_mm_per_ms": initial_impulse,
        "final_normal_impulse_g_mm_per_ms": final_impulse,
        "delta_normal_impulse_g_mm_per_ms": delta_impulse,
        "initial_velocity_z_mm_per_ms": initial_velocity,
        "residual_velocity_z_mm_per_ms": final_velocity,
        "residual_speed_m_per_s": abs(final_velocity),
        "speed_loss_m_per_s": abs(initial_velocity) - abs(final_velocity),
        "speed_loss_mph": (abs(initial_velocity) - abs(final_velocity)) / 0.44704,
        "initial_total_energy_solver": initial_total,
        "final_internal_energy_solver": float(last["INTERNAL ENERGY"]),
        "final_kinetic_energy_solver": float(last["KINETIC ENERGY"]),
        "final_rotational_energy_solver": float(last["ROTATION ENERGY"]),
        "final_total_energy_solver": final_total,
        "external_work_solver": external_work,
        "derived_energy_error_percent": derived_energy_error,
        "hourglass_energy_solver": float(last["HOURGLASS ENERGY"]),
        "hourglass_to_initial_energy_fraction": abs(float(last["HOURGLASS ENERGY"])) / max(abs(initial_total), 1.0e-30),
        "added_mass_g": float(last["ADDED MASS"]),
        "percentage_added_mass": float(last["PERCENTAGE ADDED MASS"]),
        "added_mass_fraction": float(last["PERCENTAGE ADDED MASS"]) / 100.0,
    }


def make_plot(results: dict, destination: Path) -> str | None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - optional presentation layer
        return f"matplotlib unavailable: {exc}"
    cases = results["cases"]
    mesh_cases = sorted(
        (case for case in cases if case["role"].startswith("mesh_")),
        key=lambda item: item["mesh_target_mm"],
        reverse=True,
    )
    failure_cases = sorted(
        (case for case in cases if case["threads"] == 1 and case["mesh_target_mm"] == 50.0),
        key=lambda item: item["failure_strain"],
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), constrained_layout=True)
    axes[0].plot(
        [case["mesh_target_mm"] for case in mesh_cases],
        [case["time_history"]["speed_loss_mph"] for case in mesh_cases],
        "o-",
        color="#1769aa",
        label="V8U rigid-sphere surrogate",
    )
    axes[0].axhspan(56.0, 74.0, color="#d9892b", alpha=0.18, label="NIST engine-component model range")
    axes[0].invert_xaxis()
    axes[0].set_xlabel("Target shell mesh size (mm)")
    axes[0].set_ylabel("Projectile speed loss (mph)")
    axes[0].set_title("Mesh sensitivity at failure strain 0.20")
    axes[0].grid(alpha=0.25)
    axes[0].legend(fontsize=8)
    axes[1].plot(
        [case["failure_strain"] for case in failure_cases],
        [case["time_history"]["speed_loss_mph"] for case in failure_cases],
        "o-",
        color="#7b2cbf",
    )
    axes[1].set_xlabel("Element deletion plastic strain")
    axes[1].set_ylabel("Projectile speed loss (mph)")
    axes[1].set_title("Failure sensitivity at 50 mm")
    axes[1].grid(alpha=0.25)
    fig.suptitle("WTC 1 V8U — numerical qualification surrogate, not an aircraft reconstruction", fontsize=11)
    fig.savefig(destination, dpi=180)
    plt.close(fig)
    return None


def main() -> None:
    args = parse_args()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v8u_openradioss_impact_submodel.json"
    generator_path = simulation_root / "scripts" / "generate_v8u_impact_panel.py"
    output_root = simulation_root / "openradioss_benchmarks" / "v8u_impact_panel"
    summary_path = simulation_root / "output" / "resultats_wtc1_v8u_impact_openradioss.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v8u_impact_openradioss.md"
    plot_path = simulation_root / "output" / "figure_wtc1_v8u_impact_openradioss.png"
    if summary_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing V8U result: {summary_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    runtime_root = simulation_root / "openradioss_runtime" / "v20260728-win64"
    starter = runtime_root / "starter_win64.exe"
    engine = runtime_root / "engine_win64.exe"
    converter = runtime_root / "th_to_csv_win64.exe"
    if not converter.exists():
        shutil.copy2(Path(r"C:\OpenRadioss\exec\th_to_csv_win64.exe"), converter)
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
    case_results: list[dict] = []
    overall_started = time.perf_counter()
    for case in config["cases"]:
        case_dir = output_root / case["id"]
        if case_dir.exists() and args.force:
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        generation = run_process(
            Path(os.sys.executable),
            [
                str(generator_path),
                "--config",
                str(config_path),
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
        rupture_matches = re.findall(r"RUPTURE OF SHELL ELEMENT\s*:\s*(\d+)\s+AT TIME\s*:\s*([0-9.Ee+\-]+)", engine_run["stdout"])
        time_history = read_time_history(case_dir / f"{run_name}T01.csv", config["projectile"])
        case_results.append(
            {
                **case,
                **metadata,
                "starter": {
                    "exit_code": starter_run["exit_code"],
                    "elapsed_seconds": starter_run["elapsed_seconds"],
                    "warning_count": starter_run["stdout"].count("WARNING ID"),
                },
                "engine": {
                    "exit_code": engine_run["exit_code"],
                    "elapsed_seconds": engine_run["elapsed_seconds"],
                    "normal_termination": "NORMAL TERMINATION" in engine_output_text,
                    "last_printed_cycle": parse_cycle_record(engine_output_text),
                },
                "time_history": time_history,
                "rupture": {
                    "event_count": len(rupture_matches),
                    "unique_element_count": len({int(item[0]) for item in rupture_matches}),
                    "fraction_of_initial_shells": len({int(item[0]) for item in rupture_matches}) / metadata["shell_count_total"],
                    "first_time_ms": min((float(item[1]) for item in rupture_matches), default=None),
                    "last_time_ms": max((float(item[1]) for item in rupture_matches), default=None),
                },
                "artifacts": {
                    "starter": str((case_dir / f"{run_name}_0000.rad").relative_to(project_root)).replace("\\", "/"),
                    "engine": str((case_dir / f"{run_name}_0001.rad").relative_to(project_root)).replace("\\", "/"),
                    "time_history_csv": str((case_dir / f"{run_name}T01.csv").relative_to(project_root)).replace("\\", "/"),
                    "engine_output": str(engine_output.relative_to(project_root)).replace("\\", "/"),
                },
            }
        )

    by_id = {case["id"]: case for case in case_results}
    medium = by_id["M050_E020_T1"]
    fine = by_id["M025_E020_T1"]
    threaded = by_id["M050_E020_T4"]
    convergence = {
        "medium_to_fine_impulse_relative_difference": relative_difference(
            medium["time_history"]["delta_normal_impulse_g_mm_per_ms"],
            fine["time_history"]["delta_normal_impulse_g_mm_per_ms"],
        ),
        "medium_to_fine_residual_speed_relative_difference": relative_difference(
            medium["time_history"]["residual_speed_m_per_s"],
            fine["time_history"]["residual_speed_m_per_s"],
        ),
        "thread_repeatability_impulse_relative_difference": relative_difference(
            medium["time_history"]["delta_normal_impulse_g_mm_per_ms"],
            threaded["time_history"]["delta_normal_impulse_g_mm_per_ms"],
        ),
        "thread_repeatability_residual_speed_relative_difference": relative_difference(
            medium["time_history"]["residual_speed_m_per_s"],
            threaded["time_history"]["residual_speed_m_per_s"],
        ),
    }
    gates_config = config["predeclared_gates"]
    gate_checks = {
        "all_starter_exit_code_zero": all(case["starter"]["exit_code"] == 0 for case in case_results),
        "all_engine_exit_code_zero": all(case["engine"]["exit_code"] == 0 for case in case_results),
        "all_normal_termination": all(case["engine"]["normal_termination"] for case in case_results),
        "energy_error": max(abs(case["time_history"]["derived_energy_error_percent"]) for case in case_results)
        <= gates_config["maximum_absolute_energy_error_percent"],
        "added_mass": max(case["time_history"]["added_mass_fraction"] for case in case_results)
        <= gates_config["maximum_added_mass_fraction"],
        "hourglass_energy": max(case["time_history"]["hourglass_to_initial_energy_fraction"] for case in case_results)
        <= gates_config["maximum_hourglass_to_initial_energy_fraction"],
        "medium_to_fine_impulse": convergence["medium_to_fine_impulse_relative_difference"]
        <= gates_config["medium_to_fine_impulse_relative_difference"],
        "medium_to_fine_residual_speed": convergence["medium_to_fine_residual_speed_relative_difference"]
        <= gates_config["medium_to_fine_residual_speed_relative_difference"],
        "thread_repeatability_impulse": convergence["thread_repeatability_impulse_relative_difference"]
        <= gates_config["thread_repeatability_impulse_relative_difference"],
        "thread_repeatability_residual_speed": convergence["thread_repeatability_residual_speed_relative_difference"]
        <= gates_config["thread_repeatability_residual_speed_relative_difference"],
    }
    qualification_passed = all(gate_checks.values())
    results = {
        "iteration": "V8U",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "cases": case_results,
        "convergence": convergence,
        "gate_checks": gate_checks,
        "surrogate_numerical_qualification_passed": qualification_passed,
        "global_wtc_impact_physics_qualification_passed": False,
        "comparison_to_official_model": {
            "nist_engine_component_speed_loss_range_mph": [56.0, 74.0],
            "classification": "official_model_result",
            "comparability": "diagnostic context only; V8U uses a rigid sphere, truncated facade surrogate, different initial speed, and no detailed engine breakup",
        },
        "runtime": {
            "total_elapsed_seconds": time.perf_counter() - overall_started,
            "starter_sha256": sha256(starter),
            "engine_sha256": sha256(engine),
            "converter_sha256": sha256(converter),
            "config_sha256": sha256(config_path),
            "generator_sha256": sha256(generator_path),
            "source_installation_modified": False,
            "system32_modified": False,
        },
    }
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    plot_error = make_plot(results, plot_path)
    results["plot"] = {
        "path": str(plot_path.relative_to(project_root)).replace("\\", "/") if plot_path.exists() else None,
        "error": plot_error,
    }
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    table_rows = []
    for case in case_results:
        th = case["time_history"]
        table_rows.append(
            f"| {case['id']} | {case['mesh_target_mm']:.0f} | {case['failure_strain']:.2f} | {case['threads']} | "
            f"{case['shell_count_total']} | {case['rupture']['unique_element_count']} | "
            f"{th['residual_speed_m_per_s']:.3f} | {th['speed_loss_mph']:.3f} | {th['derived_energy_error_percent']:.3f} |"
        )
    failed = [name for name, passed in gate_checks.items() if not passed]
    gate_text = "PASS" if qualification_passed else "FAIL: " + ", ".join(failed)
    report = f"""# WTC 1 — V8U : sous-modèle d’impact OpenRadioss

## Résultat

La matrice V8U s’est exécutée sans modifier `C:\\OpenRadioss` ni `System32`. Le verdict du portail numérique pré-déclaré est **{gate_text}**.

Ce verdict concerne uniquement un projectile sphérique rigide et un petit panneau de coques. Il ne constitue ni une reproduction de l’impact du vol AA11, ni une validation de l’état d’endommagement global NIST, ni un test de la chaîne incendie-initiation-propagation, ni un test d’une hypothèse de démolition.

## 1. Faits directement documentés

- NIST décrit 59 colonnes caisson par façade, nominalement carrées de 14 pouces, espacées de 40 pouces, avec des allèges de 52 pouces.
- Un élément récupéré voisin de la zone d’impact, N8, provient du WTC 1 vers les étages 97–100 ; une plaque de semelle de 5/16 pouce est documentée, ainsi qu’un acier spécifié à 60 ksi.
- Pour ce groupe d’acier, NIST rapporte un coefficient longitudinal de sensibilité au taux d’environ 0,016 pour la limite d’élasticité.
- Dans ses sous-modèles de moteur, NIST rapporte des pertes de vitesse de 56 à 74 mph selon la position et le traitement des assemblages. Ce sont des résultats de modèle officiel, pas des mesures directes de l’événement.

## 2. Hypothèses propres à V8U

- Trois colonnes caisson carrées fermées sont reliées par une allège d’un étage. Les soudures sont remplacées par des nœuds partagés ; planchers, boulons, sièges de fermes et plaques d’assemblage sont absents.
- L’épaisseur de 5/16 pouce est appliquée à toutes les faces des colonnes et 3/8 pouce à l’allège. Ces valeurs sont représentatives de pièces voisines ; elles ne constituent pas le bordereau exact du panneau 124 au niveau 96.
- Le projectile est une sphère rigide de 1,0 m et 4 558,6 kg à 443 mph. Sa masse dérive d’une moitié de la masse des deux moteurs avec capotages, mais son diamètre, sa rigidité et sa forme sont des choix de qualification.
- La déformation plastique de rupture 0,20 est entourée par 0,10 et 0,30. Cette suppression d’éléments est dépendante du maillage.

## 3. Résultats dérivés

| Cas | Maille (mm) | Rupture | Fils | Coques | Coques rompues | Vitesse résiduelle (m/s) | Perte (mph) | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table_rows)}

- Écart moyen-fin sur l’impulsion : **{convergence['medium_to_fine_impulse_relative_difference']:.3%}**.
- Écart moyen-fin sur la vitesse résiduelle : **{convergence['medium_to_fine_residual_speed_relative_difference']:.3%}**.
- Répétabilité 1/4 fils sur l’impulsion : **{convergence['thread_repeatability_impulse_relative_difference']:.3%}**.
- Répétabilité 1/4 fils sur la vitesse : **{convergence['thread_repeatability_residual_speed_relative_difference']:.3%}**.

## 4. Comparaison au modèle officiel

La bande NIST de 56–74 mph est affichée comme repère diagnostique uniquement. Une différence avec V8U n’est pas une contradiction physique : NIST utilisait une représentation détaillée et déformable du moteur et plusieurs panneaux, alors que V8U emploie une sphère rigide et un panneau tronqué. L’intérêt de V8U est de révéler la sensibilité au maillage, à la rupture et au parallélisme avant d’engager un modèle plus coûteux.

## 5. Contradictions, inconnues et décision

- Bordereau exact des plaques du panneau 124 au niveau 96 : **inconnu dans le jeu local gelé**.
- Courbe matériau complète à grande vitesse et loi de rupture multiaxiale de cette plaque précise : **inconnues**.
- Géométrie et propriétés détaillées du moteur JT9D, capotage et assemblages : **non modélisées**.
- Contact déformable-déformable `/INTER/TYPE7`, rupture du projectile, aile et carburant : **non qualifiés par V8U**.
- Le portail global WTC-impact demeure **bloqué** même si le portail numérique du substitut passe.

La prochaine itération doit conserver ce cas comme test de régression, puis remplacer la sphère par un projectile déformable minimal et qualifier `/INTER/TYPE7` sur une géométrie de panneau plus étendue. Aucun transfert vers Blender ou vers un calcul global n’est justifié par V8U seul.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps({"status": gate_text, "results": str(summary_path), "report": str(report_path), "plot": str(plot_path) if plot_path.exists() else None}))


if __name__ == "__main__":
    main()
