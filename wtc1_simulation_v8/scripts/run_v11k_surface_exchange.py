"""Run, document and package the bounded V11K surface-exchange coupon."""
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

import test_v11k_surface_exchange
import v11k_surface_exchange_model as physics


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11k_surface_exchange_predeclaration.json"


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
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def saved_v11j_control(directory: Path) -> dict[str, Any]:
    manifest = read(directory / "offline_manifest.json")
    results = read(directory / "results_v11j.json")
    release = read(directory / "release_audit.json")
    expected_hashes = dict(manifest["input_sha256"])
    for name, expected in manifest["output_sha256"].items():
        expected_hashes[(directory / name).relative_to(ROOT).as_posix()] = expected
    hash_checks = {
        name: (ROOT / name).is_file() and sha(ROOT / name) == expected
        for name, expected in expected_hashes.items()
    }
    identity_checks = {
        "iteration": results["iteration"] == "V11J",
        "results_status": results["status"] == "PASS",
        "manifest_status": manifest["implementation_status"] == "PASS",
        "release_status": release["status"] == "PASS",
        "tests": results["test_count"] == results["tests_passed"] == 31,
        "cases": results["case_count"] == 5,
        "digest": results["numerical_digest_sha256"] == "e5a62e868a1448268eb389512a5ca90015d662316636c11342924122775513a4",
    }
    return {
        "iteration": "V11J",
        "status": "PASS" if all(hash_checks.values()) and all(identity_checks.values()) else "FAIL",
        "hash_checks": hash_checks,
        "identity_checks": identity_checks,
        "results_sha256": sha(directory / "results_v11j.json"),
        "manifest_sha256": sha(directory / "offline_manifest.json"),
        "release_audit_sha256": sha(directory / "release_audit.json"),
        "tests": results["test_count"],
        "cases": results["case_count"],
        "numerical_digest_sha256": results["numerical_digest_sha256"],
    }


def flatten_profiles(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in runs:
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


def flatten_histories(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for run in runs for row in run["history"]]


def flatten_convergence(space: dict[str, Any], temporal: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [{"refinement_kind": "space_operator_exact_time", **row} for row in space["rows"]]
    rows.extend({"refinement_kind": "time_backward_euler", **row} for row in temporal["rows"])
    return rows


def font(size: int, bold: bool = False):
    path = "C:/Windows/Fonts/segoeui" + ("b" if bold else "") + ".ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def make_figure(
    path: Path,
    result: dict[str, Any],
    runs: list[dict[str, Any]],
    space: dict[str, Any],
    temporal: dict[str, Any],
) -> None:
    image = Image.new("RGB", (1700, 1160), "#eef3f5")
    draw = ImageDraw.Draw(image)

    def label(x: float, y: float, value: str, size: int = 20, color: str = "#243d4c", bold: bool = False) -> None:
        draw.text((x, y), value, font=font(size, bold), fill=color)

    def card(box: tuple[int, int, int, int]) -> None:
        draw.rounded_rectangle(box, radius=18, fill="white", outline="#cbd9df", width=2)

    label(42, 24, "WTC 1 / V11K — échanges de surface bornés", 35, bold=True)
    label(43, 74, "Convection + rayonnement synthétiques, conduction 1D constante, aucun incendie calculé.", 22)
    card((35, 120, 1665, 265))
    label(60, 144, f"{result['tests_passed']}/{result['test_count']} contrôles numériques réussis", 29, bold=True)
    label(60, 196, "q entrant = q convection + q rayonnement = conduction dans la demi-maille", 22)
    label(1185, 196, f"Résidu énergie relatif : {result['maxima']['energy_relative']:.2e}", 19, "#267a55", True)

    card((35, 300, 1110, 900))
    label(60, 325, "Palier combiné : profils dans l'épaisseur", 24, bold=True)
    plot = (100, 400, 1060, 830)
    draw.rectangle(plot, fill="#f9fbfc", outline="#aebfc8", width=2)
    step_run = next(item for item in runs if item["summary"]["id"] == "COMBINED_STEP_TRANSIENT")
    selected = [step_run["profiles"][index] for index in (0, 10, 20, 40)]
    colours = ["#4e79a7", "#59a14f", "#f28e2b", "#e15759"]
    minimum_t, maximum_t = 15.0, 255.0
    length = float(result["geometry"]["thickness_m"])
    for snapshot, colour in zip(selected, colours):
        points = []
        for depth, temperature in zip(snapshot["depth_from_top_m"], snapshot["temperature_c"]):
            px = plot[0] + (float(temperature) - minimum_t) / (maximum_t - minimum_t) * (plot[2] - plot[0])
            py = plot[1] + float(depth) / length * (plot[3] - plot[1])
            points.append((px, py))
        draw.line(points, fill=colour, width=4)
        label(145 + selected.index(snapshot) * 220, 850, f"t={snapshot['time_s']:.0f} s", 18, colour, True)
    for temperature in (20, 60, 100, 140, 180, 220):
        px = plot[0] + (temperature - minimum_t) / (maximum_t - minimum_t) * (plot[2] - plot[0])
        draw.line((px, plot[3], px, plot[3] + 8), fill="#526b78", width=2)
        label(px - 15, plot[3] + 12, str(temperature), 16)
    label(500, 882, "Température (°C)", 18)
    label(48, 585, "profondeur", 17)
    label(48, 610, "depuis face", 17)
    label(48, 635, "chaude", 17)

    card((1145, 300, 1665, 900))
    label(1170, 325, "Contrôles", 24, bold=True)
    label(1170, 390, "Ordres espace", 20, bold=True)
    label(1170, 430, " / ".join(f"{value:.3f}" for value in space["observed_orders"]), 19, "#4e79a7", True)
    label(1170, 500, "Ordres temps", 20, bold=True)
    label(1170, 540, " / ".join(f"{value:.3f}" for value in temporal["observed_orders"]), 19, "#59a14f", True)
    label(1170, 615, "Surface max", 20, bold=True)
    label(1170, 652, f"{result['maxima']['surface_balance_w_m2']:.2e} W/m²", 19, "#f28e2b", True)
    label(1170, 725, "Newton max", 20, bold=True)
    label(1170, 762, f"{result['maxima']['newton_iterations']} itérations", 19, "#e15759", True)
    label(1170, 820, "Références : équilibre,", 17)
    label(1170, 846, "stationnaires et mode Robin.", 17)

    card((35, 940, 1665, 1120))
    label(60, 965, "Limite d'interprétation", 24, bold=True)
    label(60, 1010, "Les températures 20–250 °C, h=10–50 W/m²K et émissivités 0–0,9 sont des entrées synthétiques.", 21)
    label(60, 1048, "Aucun feu WTC, deck, SFRM, humidité, propriété variable, contrainte, fissuration ou effondrement n'est calculé.", 21)
    image.save(path)


def write_report(
    path: Path,
    configuration: dict[str, Any],
    result: dict[str, Any],
    runs: list[dict[str, Any]],
    space: dict[str, Any],
    temporal: dict[str, Any],
    sensitivity: list[dict[str, Any]],
) -> None:
    summaries = [item["summary"] for item in runs]
    space_errors_text = " / ".join(f"{row['linf_error_k']:.6g}" for row in space["rows"])
    space_orders_text = " / ".join(f"{value:.6f}" for value in space["observed_orders"])
    time_errors_text = " / ".join(f"{row['linf_error_k']:.6g}" for row in temporal["rows"])
    time_orders_text = " / ".join(f"{value:.6f}" for value in temporal["observed_orders"])
    lines = [
        "# V11K — convection et rayonnement de surface sur coupon 1D",
        "",
        "## Résultat",
        "",
        f"V11K passe {result['tests_passed']}/{result['test_count']} contrôles numériques. Six cas synthétiques couplent une surface sans masse au coupon constant V11J : q entrant = h(Tgaz−Ts) + εσ(Trad,K⁴−Ts,K⁴), puis conduction dans la demi-maille. Les contributions convective et radiative sont conservées séparément en W/m² et J/m².",
        "",
        "Cette qualification ne calcule pas un incendie. Les températures ambiantes, coefficients d'échange et émissivités ne sont pas attribués au WTC1. Aucun champ V11K n'est appliqué au panneau mécanique V11I.",
        "",
        "## 1. Faits directement observés ou transcrits",
        "",
        "NIST TN 1681 donne la relation convective simple Qc=h·As·(Ts−Tf), indique une plage typique d'environ 10 à 30 W/(m²·K) dans un compartiment en feu, et additionne convection et rayonnement comme condition de bord de la conduction. V11K inverse seulement le signe pour déclarer positif ce qui entre dans le coupon.",
        "",
        "Le rapport technique FDS NISTIR 6902 formule également le flux net reçu par un solide comme somme des termes convectif et radiatif, couplée à une conduction unidimensionnelle. La table NIST/CODATA 2022 donne σ=5,670374419×10⁻⁸ W/(m²·K⁴), valeur exacte dans le SI de 2019.",
        "",
        "## 2. Résultats d'un modèle officiel",
        "",
        "Ces documents décrivent des équations et conventions de modèles officiels. V11K ne relance ni FDS ni le modèle thermique NIST du WTC ; aucun champ de gaz, facteur de vue, flux de flamme ou résultat officiel n'est importé.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune archive locale, photographie, vidéo ou nouvelle page de PDF archivée n'est analysée. Les références méthodologiques proviennent directement des publications NIST en ligne consignées dans le manifeste.",
        "",
        "## 4. Hypothèses propres au modèle",
        "",
        f"Le coupon homogène a L={configuration['geometry']['thickness_m']:.5f} m et A=1 m². Les constantes V11J sont inchangées : k={configuration['constant_properties']['conductivity_w_m_k']:.1f} W/(m·K), ρ={configuration['constant_properties']['density_kg_m3']:.0f} kg/m³ et cp={configuration['constant_properties']['specific_heat_j_kg_k']:.0f} J/(kg·K). Il n'y a ni deck, armature, humidité, chaleur latente, SFRM, contact ni dépendance en température.",
        "",
        "Chaque surface a une capacité nulle. Le rayonnement emploie Ts+273,15 et Trad+273,15 en kelvins absolus. Euler implicite et Newton résolvent simultanément la conduction et les deux équilibres de surface. Le bilan stocké est ΔH=∫(qconv,bas+qrad,bas+qconv,haut+qrad,haut)dt, par mètre carré.",
        "",
        "Les valeurs h=10 à 50 W/(m²·K), ε=0 à 0,9 et les environnements de 20 à 250 °C sont des essais de vérification et de sensibilité. Ce ne sont ni des mesures, ni des probabilités, ni des scénarios d'incendie WTC.",
        "",
        "## 5. Résultats dérivés",
        "",
        "| Cas | T moyenne finale (°C) | Ts bas / haut (°C) | qconv haut (W/m²) | qrad haut (W/m²) | ΔH (MJ/m²) | ∫q dt (MJ/m²) | Erreur L∞ (K) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        error = "—" if summary["terminal_field_linf_error_k"] is None else f"{summary['terminal_field_linf_error_k']:.6g}"
        lines.append(
            f"| {summary['id']} | {summary['final_mean_temperature_c']:.6f} | {summary['final_bottom_surface_temperature_c']:.4f} / {summary['final_top_surface_temperature_c']:.4f} | {summary['final_top_convective_inward_flux_w_m2']:.4f} | {summary['final_top_radiative_inward_flux_w_m2']:.4f} | {summary['enthalpy_change_j_m2']/1e6:.6f} | {summary['cumulative_total_inward_heat_j_m2']/1e6:.6f} | {error} |"
        )
    lines += [
        "",
        f"Le résidu maximal d'équilibre d'une surface vaut {result['maxima']['surface_balance_w_m2']:.3e} W/m² ; le résidu non linéaire global {result['maxima']['nonlinear_residual_w_m2']:.3e} W/m². Newton demande au plus {result['maxima']['newton_iterations']} itérations par pas. Le résidu énergétique total maximal est {result['maxima']['energy_total_absolute_j_m2']:.3e} J/m², soit {result['maxima']['energy_relative']:.3e} relativement pour les cas à bilan non nul.",
        "",
        "Les contrôles d'équilibre et les trois profils stationnaires restent invariants. Pour la convection seule, le débit stationnaire est aussi recalculé par la résistance fermée 1/hbas+L/k+1/hhaut. Le mode propre de Robin fournit la référence transitoire continue.",
        "",
        "### Raffinement indépendant",
        "",
        "| Diagnostic | Erreurs L∞ successives (K) | Ordres observés |",
        "|---|---|---|",
        f"| Opérateur spatial, temps exact | {space_errors_text} | {space_orders_text} |",
        f"| Euler implicite, 256 cellules | {time_errors_text} | {time_orders_text} |",
        "",
        "### Sensibilités du palier combiné à 1 800 s",
        "",
        "| Paramètre | Valeur | h haut (W/m²K) | ε haut | T moyenne (°C) | ΔH (MJ/m²) | Convection cumulée (MJ/m²) | Rayonnement cumulé (MJ/m²) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sensitivity:
        lines.append(
            f"| {row['parameter']} | {row['value']:.3f} | {row['top_h_w_m2_k']:.3f} | {row['top_emissivity']:.3f} | {row['final_mean_temperature_c']:.6f} | {row['enthalpy_change_j_m2']/1e6:.6f} | {row['cumulative_convective_j_m2']/1e6:.6f} | {row['cumulative_radiative_j_m2']/1e6:.6f} |"
        )
    lines += [
        "",
        "L'énergie reçue augmente monotoniquement avec h haut lorsque ε est fixé, et avec ε haut lorsque h est fixé. Cette réponse est conditionnelle au coupon et aux autres paramètres inchangés.",
        "",
        "## 6. Contradictions, limites et informations manquantes",
        "",
        "Une température de gaz ou radiative imposée n'est pas un incendie calculé. Il manque un historique primaire de flux net ou de températures environnantes, les facteurs de vue, la composition des gaz, l'état local du SFRM, le deck, l'humidité, les propriétés thermiques variables et leurs incertitudes. La plage de h n'est qu'un encadrement méthodologique général.",
        "",
        "Le coupon reste unidimensionnel et sans mécanique. Il ne modifie aucune propriété d'un matériau endommagé, n'accorde aucune énergie à une rupture et ne traite ni fissuration chaude, ni localisation après fracture, ni impact, ni initiation, arrêt ou propagation d'effondrement. Des tests numériques réussis qualifient ce sous-modèle, pas le comportement réel de la tour. Blender reste inchangé et purement visuel.",
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
    inherited_configuration = read(ROOT / configuration["inherited_conduction_configuration"])
    directory = (ROOT / args.output).resolve()
    allowed_roots = [(ROOT / configuration[key]).resolve() for key in ("output_directory", "scratch_directory")]
    if not any(directory == root or root in directory.parents for root in allowed_roots):
        raise ValueError("Outside V11K output roots")
    if directory.exists():
        raise FileExistsError("Preserve previous output; choose a new directory")

    controls = {
        "V11J": saved_v11j_control(ROOT / configuration["inherited_conduction_directory"]),
        "old_driver_reexecuted": False,
    }
    if controls["V11J"]["status"] != "PASS":
        raise ValueError("Saved V11J control failed")

    code = [
        "wtc1_simulation_v8/scripts/v11k_surface_exchange_model.py",
        "wtc1_simulation_v8/scripts/test_v11k_surface_exchange.py",
        "wtc1_simulation_v8/scripts/run_v11k_surface_exchange.py",
        "wtc1_simulation_v8/scripts/audit_v11k_release.py",
    ]
    tracked = list(dict.fromkeys([
        CONFIG.relative_to(ROOT).as_posix(),
        configuration["inherited_conduction_configuration"],
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
    print("Six reference surface-exchange cases computed", flush=True)
    replay_runs = [physics.run_case(configuration, case) for case in cases]
    reference_digest = digest(reference_runs)
    replay_digest = digest(replay_runs)
    space = physics.spatial_operator_refinement(configuration)
    temporal = physics.time_refinement(configuration)
    sensitivity = physics.surface_exchange_sensitivity(configuration)
    print("Replay, Robin refinements and h/emissivity sensitivities computed", flush=True)

    tests = test_v11k_surface_exchange.run(
        configuration, inherited_configuration, reference_runs, replay_runs,
        space, temporal, sensitivity, controls, reference_digest, replay_digest,
    )
    status = "PASS" if all(item["pass"] for item in tests) else "FAIL"
    summaries = [item["summary"] for item in reference_runs]
    energy_relative_candidates = [
        item["maximum_total_energy_residual_relative"]
        for item in summaries
        if abs(item["enthalpy_change_j_m2"]) > 1.0
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
        "scope": "Six reference/replay cases, exact-time Robin space refinement, backward-Euler time refinement, two bounded surface sensitivities and tests before rendering",
    }
    next_objective = (
        "V11L : effectuer un premier couplage unidirectionnel, limité et réversible, d'un profil transitoire V11K sauvegardé vers le panneau thermoélastique non endommagé V11I. Vérifier interpolation, dilatation libre/empêchée, réactions, travail thermique et bilan énergétique contre les contrôles V11H/V11I ; conserver le palier synthétique explicitement non-WTC et ne traiter ni fissuration chaude ni propriété dégradée avant une formulation d'histoire et d'énergie dédiée."
    )
    numerical_payload = {
        "reference_summaries": summaries,
        "space_refinement": space,
        "time_refinement": temporal,
        "surface_exchange_sensitivity": sensitivity,
    }
    numerical_digest = digest(numerical_payload)
    result = {
        "iteration": "V11K",
        "status": status,
        "test_count": len(tests),
        "tests_passed": sum(item["pass"] for item in tests),
        "case_count": len(reference_runs),
        "reference_state_count": sum(len(item["history"]) for item in reference_runs),
        "case_summaries": summaries,
        "geometry": configuration["geometry"],
        "constant_properties": configuration["constant_properties"],
        "surface_exchange": configuration["surface_exchange"],
        "maxima": {
            "analytic_field_linf_k": max(item["terminal_field_linf_error_k"] or 0.0 for item in summaries),
            "analytic_mean_absolute_k": max(abs(item["terminal_mean_error_k"] or 0.0) for item in summaries),
            "surface_balance_w_m2": max(item["maximum_surface_balance_residual_w_m2"] for item in summaries),
            "nonlinear_residual_w_m2": max(item["maximum_nonlinear_residual_w_m2"] for item in summaries),
            "newton_iterations": max(item["maximum_newton_iterations"] for item in summaries),
            "energy_increment_absolute_j_m2": max(item["maximum_increment_energy_residual_absolute_j_m2"] for item in summaries),
            "energy_total_absolute_j_m2": max(item["maximum_total_energy_residual_absolute_j_m2"] for item in summaries),
            "energy_relative": max(energy_relative_candidates, default=0.0),
            "maximum_principle_violation_k": max(item["maximum_principle_violation_k"] for item in summaries),
            "space_order_minimum": min(space["observed_orders"]),
            "space_order_maximum": max(space["observed_orders"]),
            "time_order_minimum": min(temporal["observed_orders"]),
            "time_order_maximum": max(temporal["observed_orders"]),
        },
        "inherited_V11J_control_status": controls["V11J"]["status"],
        "runtime": runtime,
        "numerical_digest_sha256": numerical_digest,
        "constant_property_conduction_control_preserved": controls["V11J"]["status"] == "PASS",
        "surface_convection_and_radiation_qualified": status == "PASS",
        "surface_conditions_are_synthetic": True,
        "temperature_history_coupled_to_panel": False,
        "fire_solved": False,
        "temperature_dependent_properties_solved": False,
        "thermal_strain_or_mechanics_solved": False,
        "heated_fracture_solved": False,
        "material_properties_degraded": False,
        "aircraft_impact_computed": False,
        "collapse_validated": False,
        "blender_changed": False,
        "global_energy_credit_j": 0.0,
        "next_iteration": "V11L",
        "next_objective": next_objective,
    }

    write_json(directory / "results_v11k.json", result)
    write_json(directory / "surface_exchange_cases.json", reference_runs)
    write_csv(directory / "temperature_profiles.csv", flatten_profiles(reference_runs))
    histories = flatten_histories(reference_runs)
    write_csv(directory / "surface_exchange_history.csv", histories)
    energy_fields = [
        "case_id", "step", "time_s", "bottom_convective_inward_flux_w_m2",
        "bottom_radiative_inward_flux_w_m2", "top_convective_inward_flux_w_m2",
        "top_radiative_inward_flux_w_m2", "net_inward_flux_w_m2", "enthalpy_j_m2",
        "enthalpy_change_j_m2", "cumulative_bottom_convective_j_m2",
        "cumulative_bottom_radiative_j_m2", "cumulative_top_convective_j_m2",
        "cumulative_top_radiative_j_m2", "cumulative_total_inward_heat_j_m2",
        "total_energy_residual_j_m2",
    ]
    write_csv(directory / "energy_ledger.csv", [{name: row[name] for name in energy_fields} for row in histories])
    write_json(directory / "space_time_convergence.json", {"space": space, "time": temporal})
    write_csv(directory / "space_time_convergence.csv", flatten_convergence(space, temporal))
    write_json(directory / "surface_exchange_sensitivity.json", sensitivity)
    write_csv(directory / "surface_exchange_sensitivity.csv", sensitivity)
    write_json(directory / "inherited_control.json", controls)
    write_json(directory / "thermal_property_ledger.json", {
        "iteration": "V11K",
        "geometry": configuration["geometry"],
        "constant_properties": configuration["constant_properties"],
        "surface_exchange": configuration["surface_exchange"],
        "numerical_method": configuration["numerical_method"],
        "scope": configuration["scope"],
        "method_sources": configuration["method_sources"],
        "surface_storage_j_m2": 0.0,
        "mechanical_energy_j_m2": 0.0,
        "global_energy_credit_j": 0.0,
        "temperature_history_coupled_to_panel": False,
        "no_damage_history_or_property_updated": True,
    })
    write_json(directory / "numerical_audit.json", {
        "iteration": "V11K",
        "status": status,
        "test_count": len(tests),
        "tests": tests,
        "reference_digest_sha256": reference_digest,
        "replay_digest_sha256": replay_digest,
        "numerical_payload_digest_sha256": numerical_digest,
    })
    write_json(directory / "source_manifest.json", {
        "iteration": "V11K",
        "input_and_protected_sha256": before,
        "V11J_control": controls["V11J"],
        "primary_method_sources": configuration["method_sources"],
        "source_scope": "Saved V11J artifacts plus primary NIST equations/constants. No archive rescan, video analysis, downloaded source file or imported WTC fire field.",
        "internet_source_used": True,
        "primary_sources_only": True,
        "remote_sources_downloaded": False,
        "new_archive_pdf_photo_or_video_analysis": False,
        "external_solver_or_multiagent_validation": False,
    })
    make_figure(directory / "synthese_v11k_surface_exchange.png", result, reference_runs, space, temporal)
    write_report(
        directory / "rapport_v11k_surface_exchange.md",
        configuration, result, reference_runs, space, temporal, sensitivity,
    )

    after = {name: sha(ROOT / name) for name in tracked}
    write_json(directory / "offline_manifest.json", {
        "iteration": "V11K",
        "implementation_status": status,
        "input_sha256": after,
        "input_and_protected_unchanged": before == after,
        "V11J_control_status": controls["V11J"]["status"],
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
        "V11J": controls["V11J"]["status"],
        "inputs_unchanged": before == after,
        "failed_tests": [item for item in tests if not item["pass"]],
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if status != "PASS" or before != after:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
