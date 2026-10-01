"""Run, document and package the bounded V11J transient-conduction coupon."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

import test_v11j_transient_conduction
import v11j_transient_conduction_model as physics


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11j_transient_conduction_predeclaration.json"


def read(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path.name}")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def saved_control(
    directory: Path,
    iteration: str,
    expected_tests: int,
    expected_cases: int,
    expected_digest: str,
) -> dict[str, Any]:
    manifest = read(directory / "offline_manifest.json")
    results = read(directory / f"results_{iteration.lower()}.json")
    release = read(directory / "release_audit.json")
    expected_hashes = dict(manifest["input_sha256"])
    for name, expected in manifest["output_sha256"].items():
        expected_hashes[(directory / name).relative_to(ROOT).as_posix()] = expected
    hash_checks = {
        name: (ROOT / name).is_file() and sha(ROOT / name) == expected
        for name, expected in expected_hashes.items()
    }
    identity_checks = {
        "iteration": results["iteration"] == iteration,
        "results_status": results["status"] == "PASS",
        "manifest_status": manifest["implementation_status"] == "PASS",
        "release_status": release["status"] == "PASS",
        "test_count": results["test_count"] == results["tests_passed"] == expected_tests,
        "case_count": results["case_count"] == expected_cases,
        "numerical_digest": results["numerical_digest_sha256"] == expected_digest,
    }
    return {
        "iteration": iteration,
        "status": "PASS" if all(hash_checks.values()) and all(identity_checks.values()) else "FAIL",
        "hash_checks": hash_checks,
        "identity_checks": identity_checks,
        "results_sha256": sha(directory / f"results_{iteration.lower()}.json"),
        "manifest_sha256": sha(directory / "offline_manifest.json"),
        "release_audit_sha256": sha(directory / "release_audit.json"),
        "tests": results["test_count"],
        "cases": results["case_count"],
        "numerical_digest_sha256": results["numerical_digest_sha256"],
    }


def flatten_profiles(reference_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in reference_runs:
        for snapshot in run["profiles"]:
            exact = snapshot["analytical_temperature_c"]
            for index, (x_m, depth, temperature) in enumerate(zip(
                snapshot["x_m"], snapshot["depth_from_top_m"], snapshot["temperature_c"]
            )):
                analytical = None if exact is None else exact[index]
                rows.append({
                    "case_id": snapshot["case_id"],
                    "step": snapshot["step"],
                    "time_s": snapshot["time_s"],
                    "cell_index": index,
                    "x_from_bottom_m": x_m,
                    "depth_from_top_m": depth,
                    "temperature_c": temperature,
                    "analytical_temperature_c": analytical,
                    "error_k": None if analytical is None else temperature - analytical,
                })
    return rows


def flatten_histories(reference_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for run in reference_runs for row in run["history"]]


def flatten_convergence(space: dict[str, Any], temporal: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in space["rows"]:
        rows.append({"refinement_kind": "space_operator_exact_time", **row})
    for case_id, data in temporal.items():
        for row in data["rows"]:
            rows.append({
                "refinement_kind": "time_backward_euler",
                "case_id": case_id,
                **row,
            })
    return rows


def font(size: int, bold: bool = False):
    path = "C:/Windows/Fonts/segoeui" + ("b" if bold else "") + ".ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def make_figure(path: Path, result: dict[str, Any], reference_runs: list[dict[str, Any]], space: dict[str, Any], temporal: dict[str, Any]) -> None:
    image = Image.new("RGB", (1680, 1120), "#edf3f5")
    draw = ImageDraw.Draw(image)

    def label(x: float, y: float, value: str, size: int = 20, color: str = "#263e50", bold: bool = False) -> None:
        draw.text((x, y), value, font=font(size, bold), fill=color)

    def card(box: tuple[int, int, int, int]) -> None:
        draw.rounded_rectangle(box, radius=18, fill="white", outline="#cedbe1", width=2)

    label(42, 24, "WTC 1 / V11J — coupon de conduction 1D", 35, bold=True)
    label(43, 75, "Propriétés constantes, conditions synthétiques, aucun feu ni couplage mécanique.", 23)
    card((35, 122, 1645, 264))
    label(60, 145, f"{result['tests_passed']}/{result['test_count']} contrôles numériques réussis", 29, bold=True)
    label(60, 194, "Bilan conservatif : ΔH = ∫(qbas entrant + qhaut entrant) dt, par m².", 22)
    label(1050, 194, f"Résidu relatif max : {result['maxima']['energy_relative']:.2e}", 22, color="#267a55", bold=True)

    card((35, 300, 1085, 875))
    label(60, 322, "Échauffement par palier supérieur : profils dans l'épaisseur", 24, bold=True)
    plot = (95, 390, 1035, 815)
    draw.rectangle(plot, fill="#f8fbfc", outline="#aebfc8", width=2)
    step_run = next(run for run in reference_runs if run["summary"]["id"] == "TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC")
    selected = [step_run["profiles"][index] for index in (0, 10, 20, 40)]
    colours = ["#4e79a7", "#59a14f", "#f28e2b", "#e15759"]
    for snapshot, colour in zip(selected, colours):
        points = []
        for depth, temperature in zip(snapshot["depth_from_top_m"], snapshot["temperature_c"]):
            px = plot[0] + (float(temperature) - 15.0) / 110.0 * (plot[2] - plot[0])
            py = plot[1] + float(depth) / float(result["geometry"]["thickness_m"]) * (plot[3] - plot[1])
            points.append((px, py))
        draw.line(points, fill=colour, width=4)
        label(140 + selected.index(snapshot) * 210, 835, f"t={snapshot['time_s']:.0f} s", 18, colour, bold=True)
    for temperature in (20, 40, 60, 80, 100, 120):
        px = plot[0] + (temperature - 15.0) / 110.0 * (plot[2] - plot[0])
        draw.line((px, plot[3], px, plot[3] + 8), fill="#526b78", width=2)
        label(px - 14, plot[3] + 12, str(temperature), 16)
    label(475, 862, "Température (°C)", 18)
    label(48, 565, "profondeur", 17)
    label(48, 590, "depuis face", 17)
    label(48, 615, "chaude", 17)

    card((1120, 300, 1645, 875))
    label(1145, 323, "Convergence", 24, bold=True)
    space_orders = space["observed_orders"]
    sine_time = temporal["SINE_DIRICHLET_TRANSIENT"]["observed_orders"]
    step_time = temporal["TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC"]["observed_orders"]
    label(1145, 390, "Opérateur spatial", 21, bold=True)
    label(1145, 430, "ordres observés :", 19)
    label(1145, 465, " / ".join(f"{value:.3f}" for value in space_orders), 20, "#4e79a7", bold=True)
    label(1145, 535, "Euler implicite — sinus", 21, bold=True)
    label(1145, 575, " / ".join(f"{value:.3f}" for value in sine_time), 20, "#59a14f", bold=True)
    label(1145, 645, "Euler implicite — palier", 21, bold=True)
    label(1145, 685, " / ".join(f"{value:.3f}" for value in step_time), 20, "#f28e2b", bold=True)
    label(1145, 760, "Attendus : espace ≈ 2", 18)
    label(1145, 795, "et temps ≈ 1.", 18)

    card((35, 920, 1645, 1082))
    label(60, 942, "Limite d'interprétation", 24, bold=True)
    label(60, 985, "Le palier à 120 °C et le flux de 1 kW/m² sont des entrées de vérification, pas un incendie WTC.", 21)
    label(60, 1023, "Pas de rayonnement, convection, humidité, deck, SFRM, propriété variable, contrainte ou fissuration chaude.", 21)
    image.save(path)


def write_report(
    path: Path,
    configuration: dict[str, Any],
    result: dict[str, Any],
    reference_runs: list[dict[str, Any]],
    space: dict[str, Any],
    temporal: dict[str, Any],
    sensitivity: list[dict[str, Any]],
) -> None:
    summaries = [run["summary"] for run in reference_runs]
    lines = [
        "# V11J — coupon de conduction transitoire 1D",
        "",
        "## Résultat",
        "",
        f"V11J passe {result['tests_passed']}/{result['test_count']} contrôles numériques. Le coupon conservatif calcule la conduction transitoire dans 4,35 in ({configuration['geometry']['thickness_m']:.5f} m) d'épaisseur équivalente, sur 1 m², avec propriétés constantes. Les cinq cas incluent deux contrôles stationnaires, deux champs transitoires à solution analytique et un contrôle à flux imposé avec solution analytique de température moyenne.",
        "",
        "La température calculée reste séparée du panneau V11I. Ce coupon n'est pas un incendie WTC. Aucun résultat de cette itération n'est une température de gaz, une exposition d'incendie, une température historique du WTC1, une contrainte, une rupture ou une validation d'effondrement.",
        "",
        "## 1. Faits directement observés ou transcrits",
        "",
        "NIST NCSTAR 1-5G indique, dans son modèle officiel, une épaisseur équivalente de dalle de 4,35 in et décrit un maillage thermique d'environ 16 éléments dans l'épaisseur afin de résoudre l'onde thermique et les forts gradients de surface. Cette information borne la géométrie et motive le premier niveau de raffinement ; elle ne transforme pas le coupon V11J en reproduction du modèle NIST.",
        "",
        "NIST NCSTAR 1-5F emploie k=1,0 W/(m·K), rho=2 000 kg/m³ et cp=0,88 kJ/(kg·K) pour représenter la dalle comme condition de bord du calcul de gaz, tout en renvoyant le calcul détaillé de pénétration à une analyse séparée. NIST TN 1681 donne, pour des estimations constantes simples, 0,5 W/(m·K) pour un béton léger et 1,3 W/(m·K) pour un béton courant, avec des réserves sur densité, granulats, humidité et essais à petite échelle.",
        "",
        "## 2. Résultats d'un modèle officiel",
        "",
        "Les valeurs et choix NIST ci-dessus sont des entrées ou pratiques de modèles officiels, pas des mesures individualisées de la dalle modélisée ici. Aucun champ de température NIST n'est importé dans V11J.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune archive locale, photographie ou vidéo n'est analysée. Les trois références primaires ont été consultées par leurs publications NIST en ligne et sont enregistrées dans le manifeste de sources.",
        "",
        "## 4. Hypothèses propres au modèle",
        "",
        f"La masse volumique rho={configuration['constant_properties']['density_kg_m3']:.0f} kg/m³ et la chaleur massique cp={configuration['constant_properties']['specific_heat_j_kg_k']:.0f} J/(kg·K) sont reprises telles quelles des hypothèses génériques V11H. La conductivité de référence k={configuration['constant_properties']['reference_conductivity_w_m_k']:.1f} W/(m·K) est constante ; la sensibilité couvre 0,5, 1,0 et 1,3 W/(m·K). Cette combinaison n'est pas un matériau WTC calibré.",
        "",
        "Le domaine est homogène, unidimensionnel, sans tôle de deck, armature, humidité, chaleur latente, contact, convection, rayonnement ou SFRM. Euler implicite avance les volumes finis centrés. La convention est q entrant positif à chaque face. Par unité de surface, H=rho·cp·Σ(Ti−Tref)·dx et chaque pas vérifie ΔH=dt(qbas,entrant+qhaut,entrant).",
        "",
        "## 5. Résultats dérivés",
        "",
        "| Cas | Cellules × pas | Fo final | T moyenne finale (°C) | Min / max (°C) | Erreur L∞ analytique (K) | ΔH (MJ/m²) | ∫q dt (MJ/m²) | Résidu énergie relatif |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        linf = "—" if summary["terminal_field_linf_error_k"] is None else f"{summary['terminal_field_linf_error_k']:.6g}"
        lines.append(
            f"| {summary['id']} | {summary['cell_count']} × {summary['step_count']} | {summary['terminal_fourier_number']:.6f} | {summary['final_mean_temperature_c']:.6f} | {summary['final_minimum_temperature_c']:.4f} / {summary['final_maximum_temperature_c']:.4f} | {linf} | {summary['enthalpy_change_j_m2']/1e6:.6f} | {summary['cumulative_inward_heat_j_m2']/1e6:.6f} | {summary['maximum_total_energy_residual_relative']:.3e} |"
        )
    lines += [
        "",
        f"Le résidu incrémental absolu maximal est {result['maxima']['energy_increment_absolute_j_m2']:.3e} J/m². Le résidu total absolu maximal est {result['maxima']['energy_total_absolute_j_m2']:.3e} J/m² et le maximum relatif hors bilan nul {result['maxima']['energy_relative']:.3e}.",
        "",
        "Le contrôle uniforme adiabatique reste à 60 °C et échange exactement 0 J/m². Le profil linéaire 20–120 °C reste stationnaire ; ses flux de face, opposés, valent ±k·100/L. Le flux supérieur constant de 1 000 W/m² pendant 1 800 s apporte 1,800000 MJ/m² et élève la moyenne à la valeur analytique.",
        "",
        "### Raffinement",
        "",
        "| Diagnostic | Ordres observés successifs | Attendu |",
        "|---|---|---|",
        f"| Opérateur spatial, mode sinus, temps exact | {' / '.join(f'{value:.6f}' for value in space['observed_orders'])} | 2 |",
    ]
    for case_id, data in temporal.items():
        lines.append(
            f"| Euler implicite, {case_id} | {' / '.join(f'{value:.6f}' for value in data['observed_orders'])} | 1 |"
        )
    lines += [
        "",
        "Le contrôle spatial emploie la valeur propre exacte de l'opérateur volumes finis pour isoler l'erreur spatiale de l'erreur temporelle. Les contrôles temporels utilisent 256 cellules et 100, 200, 400 puis 800 pas.",
        "",
        "### Sensibilité à la conductivité — même palier synthétique de 1 800 s",
        "",
        "| k (W/m·K) | Diffusivité (m²/s) | T moyenne (°C) | Cellule basse (°C) | Profondeur du centroïde thermique depuis le haut (mm) | ΔH (MJ/m²) |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sensitivity:
        lines.append(
            f"| {row['conductivity_w_m_k']:.3f} | {row['thermal_diffusivity_m2_s']:.6e} | {row['final_mean_temperature_c']:.6f} | {row['final_bottom_cell_temperature_c']:.6f} | {1000*row['thermal_centroid_depth_from_top_m']:.4f} | {row['enthalpy_change_j_m2']/1e6:.6f} |"
        )
    lines += [
        "",
        "Ces trois réponses sont une sensibilité paramétrique conditionnelle, pas des probabilités ni trois scénarios d'incendie.",
        "",
        "## 6. Contradictions, limites et informations manquantes",
        "",
        "Une température prescrite de face ou un flux imposé ne calcule pas un incendie. Il manque les températures de gaz et flux nets sourcés, les coefficients convectifs, l'émissivité et les facteurs de vue, le rayonnement, l'état du SFRM, la tôle, l'humidité et les propriétés dépendantes de la température. Les valeurs constantes ne sont valides que comme vérification bornée.",
        "",
        "Aucune température V11J n'est appliquée au panneau V11I. Aucune propriété mécanique ou endommagée n'est changée ; aucune énergie mécanique, fissuration chaude, localisation complète, rupture, impact, initiation, arrêt ou propagation d'effondrement n'est calculée. Blender reste une visualisation inchangée.",
        "",
        "## Suite bornée",
        "",
        result["next_objective"],
        "",
        "## Sources primaires utilisées",
        "",
    ]
    for source in configuration["method_sources"]:
        lines.append(f"- [{source['id']}]({source['url']}) — {source['locator']}; {source['scope']}")
    lines += [
        "",
        f"Exécution : {result['runtime']['seconds']:.3f} s sur CPU ; Python {result['runtime']['python']}, NumPy {result['runtime']['numpy']}, Pillow {result['runtime']['Pillow']}. Graine {configuration['random_seed']}, sans tirage. Empreinte numérique : {result['numerical_digest_sha256']}. Aucun GPU, solveur externe, Blender ou rescannage d'archive.",
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    configuration = read(CONFIG)
    inherited = read(ROOT / configuration["inherited_thermomechanical_configuration"])
    directory = (ROOT / args.output).resolve()
    roots = [(ROOT / configuration[key]).resolve() for key in ("output_directory", "scratch_directory")]
    if not any(directory == root or root in directory.parents for root in roots):
        raise ValueError("Outside V11J output roots")
    if directory.exists():
        raise FileExistsError("Preserve previous output; choose a new directory")

    controls = {
        "V11H": saved_control(
            ROOT / configuration["inherited_thermomechanical_directory"],
            "V11H", 27, 11,
            "a7a39e9a1a4f00709e390da28766c66806b81e9696a25eae1a5b82effa616f8e",
        ),
        "V11I": saved_control(
            ROOT / configuration["previous_panel_directory"],
            "V11I", 32, 3,
            "f44bf662b31a9d9058125f6fdb7935a28fe8a1a6c30b4f014f0e6df3cbebfa53",
        ),
        "old_drivers_reexecuted": False,
    }
    if controls["V11H"]["status"] != "PASS" or controls["V11I"]["status"] != "PASS":
        raise ValueError("Inherited V11H/V11I saved control failed")

    code = [
        "wtc1_simulation_v8/scripts/v11j_transient_conduction_model.py",
        "wtc1_simulation_v8/scripts/test_v11j_transient_conduction.py",
        "wtc1_simulation_v8/scripts/run_v11j_transient_conduction.py",
        "wtc1_simulation_v8/scripts/audit_v11j_release.py",
    ]
    tracked = list(dict.fromkeys([
        CONFIG.relative_to(ROOT).as_posix(),
        configuration["inherited_thermomechanical_configuration"],
        configuration["previous_panel_configuration"],
        *configuration["protected_files"],
        *code,
    ]))
    missing = [name for name in tracked if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing declared input(s): {missing}")
    before = {name: sha(ROOT / name) for name in tracked}

    directory.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    cases = configuration["cases"]
    reference_runs = [physics.run_case(configuration, case) for case in cases]
    print("Five reference conduction cases computed", flush=True)
    replay_runs = [physics.run_case(configuration, case) for case in cases]
    reference_digest = digest(reference_runs)
    replay_digest = digest(replay_runs)
    space = physics.spatial_operator_refinement(configuration)
    temporal = physics.time_refinement(configuration)
    sensitivity = physics.conductivity_sensitivity(configuration)
    print("Replay, analytical refinements and conductivity sensitivity computed", flush=True)

    tests = test_v11j_transient_conduction.run(
        configuration, inherited, reference_runs, replay_runs, space, temporal,
        sensitivity, controls, reference_digest, replay_digest,
    )
    status = "PASS" if all(test["pass"] for test in tests) else "FAIL"
    summaries = [run["summary"] for run in reference_runs]
    energy_relative_candidates = [
        row["maximum_total_energy_residual_relative"]
        for row in summaries
        if abs(row["enthalpy_change_j_m2"]) > 1.0
    ]
    runtime = {
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "seconds": time.perf_counter() - clock,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "Pillow": pillow_version,
        "executable": sys.executable,
        "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        "scope": "Reference/replay, analytical space operator, two time refinements, conductivity sensitivity and tests before rendering",
    }
    next_objective = (
        "V11K : qualifier séparément des conditions de surface convectives et radiatives sur le coupon, d'abord avec cas synthétiques et références analytiques ou manufacturées, puis bilan de puissance et sensibilité. Conserver les propriétés constantes de V11J comme contrôle, ne rattacher aucune courbe à un incendie WTC sans flux net ou température de gaz primaire sourcé, et ne coupler au panneau qu'après qualification."
    )
    numerical_digest = digest({
        "reference_summaries": summaries,
        "space_refinement": space,
        "time_refinement": temporal,
        "conductivity_sensitivity": sensitivity,
    })
    result = {
        "iteration": "V11J",
        "status": status,
        "test_count": len(tests),
        "tests_passed": sum(test["pass"] for test in tests),
        "case_count": len(reference_runs),
        "reference_state_count": sum(len(run["history"]) for run in reference_runs),
        "case_summaries": summaries,
        "geometry": configuration["geometry"],
        "properties": configuration["constant_properties"],
        "maxima": {
            "analytic_field_linf_k": max(row["terminal_field_linf_error_k"] or 0.0 for row in summaries),
            "analytic_mean_absolute_k": max(abs(row["terminal_mean_error_k"]) for row in summaries),
            "energy_increment_absolute_j_m2": max(row["maximum_increment_energy_residual_absolute_j_m2"] for row in summaries),
            "energy_total_absolute_j_m2": max(row["maximum_total_energy_residual_absolute_j_m2"] for row in summaries),
            "energy_relative": max(energy_relative_candidates, default=0.0),
            "maximum_principle_violation_k": max(row["maximum_principle_violation_k"] for row in summaries),
            "space_order_minimum": min(space["observed_orders"]),
            "space_order_maximum": max(space["observed_orders"]),
            "time_order_minimum": min(value for data in temporal.values() for value in data["observed_orders"]),
            "time_order_maximum": max(value for data in temporal.values() for value in data["observed_orders"]),
        },
        "inherited_V11H_control_status": controls["V11H"]["status"],
        "inherited_V11I_control_status": controls["V11I"]["status"],
        "runtime": runtime,
        "numerical_digest_sha256": numerical_digest,
        "one_dimensional_constant_property_conduction_qualified": status == "PASS",
        "boundary_conditions_are_synthetic": True,
        "temperature_history_coupled_to_panel": False,
        "fire_solved": False,
        "surface_convection_solved": False,
        "surface_radiation_solved": False,
        "moisture_or_phase_change_solved": False,
        "temperature_dependent_properties_solved": False,
        "thermal_strain_or_mechanics_solved": False,
        "heated_fracture_solved": False,
        "material_properties_degraded": False,
        "aircraft_impact_computed": False,
        "collapse_validated": False,
        "blender_changed": False,
        "global_energy_credit_j": 0.0,
        "next_iteration": "V11K",
        "next_objective": next_objective,
    }

    write_json(directory / "results_v11j.json", result)
    write_json(directory / "conduction_cases.json", reference_runs)
    write_csv(directory / "temperature_profiles.csv", flatten_profiles(reference_runs))
    histories = flatten_histories(reference_runs)
    write_csv(directory / "boundary_flux_history.csv", histories)
    write_csv(directory / "energy_ledger.csv", [{
        key: row[key]
        for key in (
            "case_id", "step", "time_s", "bottom_inward_flux_w_m2",
            "top_inward_flux_w_m2", "net_inward_flux_w_m2", "enthalpy_j_m2",
            "enthalpy_change_j_m2", "cumulative_inward_heat_j_m2",
            "total_energy_residual_j_m2",
        )
    } for row in histories])
    write_json(directory / "space_time_convergence.json", {"space": space, "time": temporal})
    write_csv(directory / "space_time_convergence.csv", flatten_convergence(space, temporal))
    write_json(directory / "conductivity_sensitivity.json", sensitivity)
    write_csv(directory / "conductivity_sensitivity.csv", sensitivity)
    write_json(directory / "inherited_controls.json", controls)
    write_json(directory / "thermal_property_ledger.json", {
        "iteration": "V11J",
        "geometry": configuration["geometry"],
        "constant_properties": configuration["constant_properties"],
        "numerical_method": configuration["numerical_method"],
        "scope": configuration["scope"],
        "method_sources": configuration["method_sources"],
        "mechanical_energy_j_m2": 0.0,
        "global_energy_credit_j": 0.0,
        "temperature_history_coupled_to_panel": False,
        "no_damage_history_or_property_updated": True,
    })
    write_json(directory / "numerical_audit.json", {
        "iteration": "V11J",
        "status": status,
        "test_count": len(tests),
        "tests": tests,
        "reference_digest_sha256": reference_digest,
        "replay_digest_sha256": replay_digest,
    })
    write_json(directory / "source_manifest.json", {
        "iteration": "V11J",
        "input_and_protected_sha256": before,
        "V11H_control": controls["V11H"],
        "V11I_control": controls["V11I"],
        "primary_method_sources": configuration["method_sources"],
        "source_scope": "Saved V11H/V11I artifacts plus three primary NIST publication locators. No source archive rescan, video analysis or imported WTC temperature field.",
        "internet_source_used": True,
        "primary_sources_only": True,
        "remote_sources_downloaded": False,
        "new_archive_pdf_photo_or_video_analysis": False,
        "external_solver_or_multiagent_validation": False,
    })
    make_figure(directory / "synthese_v11j_conduction.png", result, reference_runs, space, temporal)
    write_report(
        directory / "rapport_v11j_conduction_transitoire.md",
        configuration, result, reference_runs, space, temporal, sensitivity,
    )

    after = {name: sha(ROOT / name) for name in tracked}
    write_json(directory / "offline_manifest.json", {
        "iteration": "V11J",
        "implementation_status": status,
        "input_sha256": after,
        "input_and_protected_unchanged": before == after,
        "V11H_control_status": controls["V11H"]["status"],
        "V11I_control_status": controls["V11I"]["status"],
        "output_sha256": {
            item.name: sha(item)
            for item in sorted(directory.iterdir())
            if item.is_file()
        },
        "manifest_excludes_itself": True,
    })
    summary = {
        "status": status,
        "tests": len(tests),
        "states": result["reference_state_count"],
        "runtime_seconds": runtime["seconds"],
        "maxima": result["maxima"],
        "V11H": controls["V11H"]["status"],
        "V11I": controls["V11I"]["status"],
        "inputs_unchanged": before == after,
        "failed_tests": [test for test in tests if not test["pass"]],
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if status != "PASS" or before != after:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
