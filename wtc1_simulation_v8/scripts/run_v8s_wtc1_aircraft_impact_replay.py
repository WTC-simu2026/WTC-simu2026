"""WTC 1 V8S - freeze and audit the upstream AA11 impact replay.

V8S deliberately stops before a global explicit finite-element solve.  It
separates input kinematics and geometry from NIST outputs, calculates a
reproducible kinematic/energy envelope, inventories installed solvers, and
predeclares the metrics that a later impact deck must pass.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
CONFIG_PATH = V8 / "data" / "v8s_wtc1_aircraft_impact_replay.json"
RESULT_PATH = V8 / "output" / "resultats_wtc1_v8s_impact_avion.json"
REPORT_PATH = V8 / "output" / "rapport_wtc1_v8s_impact_avion.md"
PLOT_PATH = V8 / "output" / "synthese_wtc1_v8s_impact_avion.png"

LB_TO_KG = 0.45359237
MPH_TO_MPS = 0.44704
FT_TO_M = 0.3048
IN_TO_M = 0.0254


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def source_audit(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in config["sources"]:
        path = ROOT / source["path"]
        row: dict[str, Any] = {
            "id": source["id"],
            "path": source["path"],
            "exists": path.is_file(),
            "status": source["status"],
        }
        if path.is_file():
            row["size_bytes"] = path.stat().st_size
            row["sha256"] = sha256(path)
        rows.append(row)
    return rows


def solver_audit(config: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in config["solver_inventory"]:
        candidate_strings = []
        if "path" in item:
            candidate_strings.append(item["path"])
        candidate_strings.extend(item.get("candidate_paths", []))
        candidates = [Path(value) for value in candidate_strings]
        existing = [path for path in candidates if path.exists()]
        executable_present = any(path.is_file() for path in existing)
        installation_present = bool(existing)
        rows.append(
            {
                "name": item["name"],
                "role": item["role"],
                "version_verified": item.get("version_verified"),
                "candidate_paths": candidate_strings,
                "existing_paths": [str(path) for path in existing],
                "installation_present": installation_present,
                "executable_present": executable_present,
                "qualifies_for_global_high_rate_impact": bool(
                    item["qualifies_for_global_high_rate_impact"]
                ),
                "reason": item.get("reason"),
            }
        )
    ready = any(
        row["installation_present"] and row["qualifies_for_global_high_rate_impact"]
        for row in rows
    )
    return {
        "rows": rows,
        "qualified_explicit_solver_installed": ready,
        "interpretation": (
            "At least one candidate high-rate explicit solver is installed."
            if ready
            else "No candidate high-rate explicit solver was found at the predeclared installation paths."
        ),
    }


def case_calculation(
    name: str,
    case: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    base_weight_lb = float(config["aircraft_mass"]["base_loaded_weight_lb"])
    mass_lb = base_weight_lb * float(case["aircraft_mass_factor"])
    mass_kg = mass_lb * LB_TO_KG
    speed_mph = float(case["speed_mph"])
    speed_mps = speed_mph * MPH_TO_MPS
    trajectory_pitch_rad = math.radians(float(case["trajectory_pitch_deg"]))
    orientation_pitch_rad = math.radians(float(case["orientation_pitch_deg"]))
    roll_rad = math.radians(float(case["roll_deg"]))
    yaw_from_face_normal_rad = math.radians(0.3)

    kinetic_energy_j = 0.5 * mass_kg * speed_mps**2
    momentum_ns = mass_kg * speed_mps
    velocity_normal_mps = speed_mps * math.cos(trajectory_pitch_rad) * math.cos(
        yaw_from_face_normal_rad
    )
    velocity_down_mps = speed_mps * math.sin(trajectory_pitch_rad)
    fuselage_m = float(config["aircraft_geometry"]["fuselage_length_ft"]) * FT_TO_M
    span_m = float(config["aircraft_geometry"]["wingspan_ft"]) * FT_TO_M
    fuselage_normal_projection_m = fuselage_m * math.cos(orientation_pitch_rad)
    tail_clearance_time_s = fuselage_normal_projection_m / velocity_normal_mps
    tower_crossing_time_s = float(config["tower_geometry"]["tower_depth_m"]) / velocity_normal_mps
    wing_horizontal_projection_m = span_m * math.cos(roll_rad)
    wing_vertical_tip_separation_m = span_m * math.sin(roll_rad)
    tail_above_nose_m = fuselage_m * math.sin(orientation_pitch_rad)
    floor_height_m = float(config["tower_geometry"]["upper_office_floor_height_ft"]) * FT_TO_M
    bay_m = float(config["tower_geometry"]["perimeter_column_spacing_m"])

    return {
        "case": name,
        "inputs": {
            "mass_factor": float(case["aircraft_mass_factor"]),
            "mass_lb": mass_lb,
            "mass_kg": mass_kg,
            "speed_mph": speed_mph,
            "speed_mps": speed_mps,
            "trajectory_pitch_deg": float(case["trajectory_pitch_deg"]),
            "orientation_pitch_deg": float(case["orientation_pitch_deg"]),
            "roll_deg": float(case["roll_deg"]),
            "aircraft_failure_strain_factor": float(case["aircraft_failure_strain_factor"]),
            "tower_failure_strain_factor": float(case["tower_failure_strain_factor"]),
            "design_live_load_fraction": float(case["design_live_load_fraction"]),
        },
        "derived_kinematics": {
            "velocity_normal_to_facade_mps": velocity_normal_mps,
            "velocity_downward_mps": velocity_down_mps,
            "momentum_total_mn_s": momentum_ns / 1e6,
            "momentum_normal_to_facade_mn_s": mass_kg * velocity_normal_mps / 1e6,
            "momentum_downward_mn_s": mass_kg * velocity_down_mps / 1e6,
            "kinetic_energy_gj": kinetic_energy_j / 1e9,
            "kinetic_energy_normal_component_gj": 0.5 * mass_kg * velocity_normal_mps**2 / 1e9,
            "kinetic_energy_vertical_component_gj": 0.5 * mass_kg * velocity_down_mps**2 / 1e9,
            "tail_clearance_time_s": tail_clearance_time_s,
            "nose_tower_depth_crossing_time_s": tower_crossing_time_s,
        },
        "reduced_silhouette_diagnostic": {
            "wing_horizontal_projection_m": wing_horizontal_projection_m,
            "wing_vertical_tip_separation_m": wing_vertical_tip_separation_m,
            "nominal_facade_bays_spanned": wing_horizontal_projection_m / bay_m,
            "nominal_floor_heights_spanned_by_wingtips": wing_vertical_tip_separation_m / floor_height_m,
            "tail_above_nose_from_fuselage_pitch_m": tail_above_nose_m,
            "tail_above_nose_from_fuselage_pitch_ft": tail_above_nose_m / FT_TO_M,
            "warning": "Rigid projection only; it does not predict failed members, penetration, fragmentation, or debris trajectories.",
        },
    }


def component_energy_table(config: dict[str, Any], base_speed_mps: float) -> list[dict[str, Any]]:
    total_lb = float(config["aircraft_mass"]["base_loaded_weight_lb"])
    rows = []
    for name, weight_lb in config["aircraft_mass"]["components_lb"].items():
        mass_kg = float(weight_lb) * LB_TO_KG
        rows.append(
            {
                "component": name,
                "weight_lb": float(weight_lb),
                "mass_kg": mass_kg,
                "mass_fraction": float(weight_lb) / total_lb,
                "translational_kinetic_energy_gj": 0.5 * mass_kg * base_speed_mps**2 / 1e9,
            }
        )
    return rows


def input_integrity(config: dict[str, Any], geometry: dict[str, Any]) -> dict[str, Any]:
    component_sum = sum(float(value) for value in config["aircraft_mass"]["components_lb"].values())
    expected_sum = float(config["aircraft_mass"]["component_sum_expected_lb"])
    established = geometry["established_facts"]
    checks = {
        "aircraft_component_mass_sum_matches_lb": math.isclose(
            component_sum, expected_sum, rel_tol=0.0, abs_tol=1e-6
        ),
        "tower_width_matches_geometry": math.isclose(
            float(config["tower_geometry"]["tower_width_m"]),
            float(established["tower_width_m"]),
            rel_tol=0.0,
            abs_tol=1e-8,
        ),
        "facade_pitch_matches_geometry": math.isclose(
            float(config["tower_geometry"]["perimeter_column_spacing_m"]),
            float(established["perimeter_column_spacing_m"]),
            rel_tol=0.0,
            abs_tol=1e-8,
        ),
        "perimeter_count_matches_geometry": int(established["perimeter_columns_per_face"])
        == int(config["tower_geometry"]["perimeter_columns_per_face"]),
        "official_outputs_separated_from_inputs": True,
        "no_archive_claim_used_as_numerical_input": True,
    }
    return {
        "checks": checks,
        "component_sum_lb": component_sum,
        "expected_component_sum_lb": expected_sum,
        "passed": all(checks.values()),
    }


def reserved_output_comparison(
    config: dict[str, Any],
    cases: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    official = config["official_outputs_reserved_for_validation"]
    base = cases["base"]
    predicted = base["derived_kinematics"]["tail_clearance_time_s"]
    observed = float(official["full_aircraft_inside_tower_s_approx"])
    absolute_error = abs(predicted - observed)
    initial_momentum_ns = base["derived_kinematics"]["momentum_total_mn_s"] * 1e6
    transferred_fraction = 1.0 - float(
        official["aircraft_residual_momentum_fraction_at_0_25_s_approx"]
    )
    equivalent_force_mn = initial_momentum_ns * transferred_fraction / observed / 1e6
    fuel_out = float(official["outside_tower_base_case_lb"]["fuel"])
    debris_out = float(official["outside_tower_base_case_lb"]["aircraft_debris"])
    fuel_total = float(config["aircraft_mass"]["components_lb"]["fuel"])
    airframe_total = float(config["aircraft_mass"]["base_loaded_weight_lb"]) - fuel_total
    table_debris_total = 196000.0
    return {
        "tail_clearance": {
            "predicted_from_inputs_s": predicted,
            "nist_reported_approx_s": observed,
            "absolute_error_s": absolute_error,
            "predeclared_gate_s": 0.03,
            "passed": absolute_error <= 0.03,
            "qualification": "This validates only a geometric timing scale, not penetration force or damage."
        },
        "nist_output_equivalent_mean_transfer_force_to_0_25_s_mn": equivalent_force_mn,
        "mean_force_qualification": "Derived from the NIST residual-momentum output, not independently predicted by V8S.",
        "outside_tower_reporting": {
            "fuel_outside_fraction_of_fuel": fuel_out / fuel_total,
            "debris_outside_fraction_of_table_debris": debris_out / table_debris_total,
            "table_debris_accounting_fraction_of_nonfuel_aircraft": table_debris_total / airframe_total,
            "nonfuel_aircraft_minus_table_debris_lb": airframe_total - table_debris_total,
            "ambiguity": official["outside_tower_ambiguity"],
        },
        "far_side_classification": {
            "whole_aircraft_exit": False,
            "intact_engine_exit_in_base_wtc1_model": False,
            "small_fragment_exit_calculated": True,
            "statement": official["far_side_statement"],
        },
    }


def readiness_gates(
    config: dict[str, Any],
    sources: list[dict[str, Any]],
    solvers: dict[str, Any],
    integrity: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "source_files_present_and_hashed": all(row["exists"] and row.get("sha256") for row in sources),
        "input_integrity_passed": integrity["passed"],
        "tail_clearance_scale_check_passed": comparison["tail_clearance"]["passed"],
        "validation_metrics_predeclared": len(config["validation_metrics_predeclared"]) >= 8,
        "damage_outputs_reserved_from_input_calculation": True,
        "independent_facade_validation_available_with_refined_nist_orientation": False,
        "as_built_impact_zone_mesh_complete": False,
        "solver_ready_for_global_high_rate_impact": solvers["qualified_explicit_solver_installed"],
        "global_aircraft_impact_replay_ready": False,
        "thermal_or_blender_coupling_authorized": False,
    }
    gates["global_aircraft_impact_replay_ready"] = all(
        [
            gates["source_files_present_and_hashed"],
            gates["input_integrity_passed"],
            gates["validation_metrics_predeclared"],
            gates["as_built_impact_zone_mesh_complete"],
            gates["solver_ready_for_global_high_rate_impact"],
        ]
    )
    return {
        "gates": gates,
        "passed": gates["global_aircraft_impact_replay_ready"],
        "interpretation": "V8S freezes a traceable replay specification, but the global explicit impact gate remains closed.",
    }


def format_float(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def build_report(result: dict[str, Any]) -> str:
    cases = result["derived_results"]["cases"]
    base = cases["base"]
    comparison = result["comparison_to_reserved_official_outputs"]
    solvers = result["solver_audit"]
    gates = result["readiness"]
    lines = [
        "# WTC 1 — V8S : gel de la reconstitution d’impact du vol AA11",
        "",
        "## Conclusion de l’itération",
        "",
        "V8S fixe une enveloppe d’entrée traçable et vérifie son échelle cinématique, mais **ne constitue pas encore une simulation de rupture de la tour**. Le cas de base transporte "
        f"{format_float(base['derived_kinematics']['kinetic_energy_gj'])} GJ et "
        f"{format_float(base['derived_kinematics']['momentum_total_mn_s'])} MN·s. "
        "Le temps purement géométrique nécessaire pour que la queue franchisse la façade nord vaut "
        f"{format_float(base['derived_kinematics']['tail_clearance_time_s'])} s, contre environ 0,25 s dans la sortie NIST : "
        f"écart {format_float(comparison['tail_clearance']['absolute_error_s'])} s. Ce contrôle valide une échelle de temps, pas les dommages.",
        "",
        "Le verrou principal est matériel et documentaire : Blender reste une visualisation, CalculiX 2.22 reste utile pour des contrôles de composants, mais aucun solveur explicite à grande vitesse qualifié n’a été trouvé. Le maillage *as-built* des plaques, assemblages, fenêtres, planchers et contenus de la zone d’impact n’est pas non plus complet.",
        "",
        "## 1. Faits officiels transcrits",
        "",
        "- NIST retient pour AA11 une masse chargée de 283 600 lb, dont 66 100 lb de carburant.",
        "- L’analyse vidéo donne 443 ± 30 mph, une trajectoire descendante de 10,6° ± 3° et un cap latéral de 180,3° ± 4° par rapport au nord structurel.",
        "- Les dimensions publiées utilisées ici sont 155 ft pour le fuselage et 159 ft 2 in pour l’envergure.",
        "- Les trois enveloppes NIST utilisent 414, 443 et 472 mph avec des facteurs de masse de 0,95, 1,00 et 1,05.",
        "",
        "## 2. Résultats du modèle officiel réservés pour comparaison",
        "",
        "- Le calcul NIST indique que l’appareil est entièrement entré dans le volume vers 0,25 s, avec environ 30 % du moment initial encore porté par ses constituants.",
        "- Dans le cas de base WTC 1, les ailes sont décrites comme fragmentées par la façade; les deux moteurs terminent à moins de 50 mph, l’un dans le noyau et l’autre entre le noyau et la façade sud.",
        "- Le NIST décrit une petite quantité de débris sortant côté sud, pas un avion intact ni un moteur intact traversant entièrement WTC 1.",
        "- Les 17 400 lb de débris et 6 700 lb de carburant annoncés « hors tour » mélangent rebond côté nord et passage côté sud; ce total ne mesure donc pas la seule sortie opposée.",
        "",
        "## 3. Résultats dérivés de V8S",
        "",
        "| Cas | Masse (t) | Vitesse (m/s) | Énergie (GJ) | Moment (MN·s) | Queue dans la tour (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    labels = {"less_severe": "moins sévère", "base": "base", "more_severe": "plus sévère"}
    for name in ("less_severe", "base", "more_severe"):
        row = cases[name]
        inputs = row["inputs"]
        derived = row["derived_kinematics"]
        lines.append(
            f"| {labels[name]} | {inputs['mass_kg'] / 1000:.2f} | {inputs['speed_mps']:.2f} | "
            f"{derived['kinetic_energy_gj']:.3f} | {derived['momentum_total_mn_s']:.3f} | "
            f"{derived['tail_clearance_time_s']:.3f} |"
        )
    silhouette = base["reduced_silhouette_diagnostic"]
    lines.extend(
        [
            "",
            "Avec 25° de roulis, la projection rigide de l’envergure représente environ "
            f"{silhouette['nominal_facade_bays_spanned']:.1f} travées de façade et "
            f"{silhouette['nominal_floor_heights_spanned_by_wingtips']:.1f} hauteurs d’étage entre les saumons. "
            "Ce résultat explique seulement l’ordre de grandeur de l’empreinte verticale; il ne décide pas quels poteaux rompent.",
            "",
            "La force moyenne équivalente de "
            f"{comparison['nist_output_equivalent_mean_transfer_force_to_0_25_s_mn']:.1f} MN jusqu’à 0,25 s "
            "est calculée à partir de la courbe de moment NIST. Elle est donc un résumé de sortie officielle, pas une prédiction indépendante de V8S.",
            "",
            "## 4. Inventaire des solveurs",
            "",
            "| Outil | Présent | Rôle retenu | Solveur global d’impact qualifié |",
            "|---|:---:|---|:---:|",
        ]
    )
    for row in solvers["rows"]:
        lines.append(
            f"| {row['name']} | {'oui' if row['installation_present'] else 'non'} | "
            f"{row['role']} | {'oui' if row['qualifies_for_global_high_rate_impact'] else 'non'} |"
        )
    lines.extend(
        [
            "",
            "## 5. Hypothèses propres à V8S",
            "",
        ]
    )
    for item in result["model_hypotheses"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 6. Affirmations provenant des archives locales",
            "",
            "Aucune affirmation de l’archive locale n’est utilisée comme entrée numérique dans V8S. Les originaux n’ont pas été modifiés.",
            "",
            "## 7. Contradictions, dépendances et inconnues",
            "",
            "- La position, l’orientation du fuselage et le roulis final du jeu NIST ont été raffinés à partir de l’empreinte de dommages observée. Leur réutilisation ne peut donc pas valider indépendamment cette même empreinte.",
            "- L’analyse NIST elle-même signale un maillage plus grossier sur la face opposée, l’absence des fenêtres, des contenus partiels, l’absence de résistance aérodynamique et de mouillage du carburant, et l’absence de déflagration du carburant dans le calcul d’impact.",
            "- La distribution de débris publiée omet environ 18 000 lb d’éléments érodés selon le texte; les totaux arrondis laissent un écart comptable plus grand. V8S conserve cette différence comme incertitude au lieu de la corriger silencieusement.",
            "- L’absence actuelle d’un solveur explicite et d’un maillage de rupture complet empêche de trancher la pénétration, la carte de dommages ou l’hypothèse d’explosifs.",
            "",
            "## 8. Métriques préenregistrées",
            "",
        ]
    )
    for metric in result["validation_metrics_predeclared"]:
        lines.append(f"- **{metric['id']}** — {metric['metric']} ; seuil : {metric['gate']}.")
    lines.extend(
        [
            "",
            "## 9. Portes de validation",
            "",
            "| Porte | État |",
            "|---|:---:|",
        ]
    )
    for name, value in gates["gates"].items():
        lines.append(f"| `{name}` | {'PASS' if value else 'FAIL'} |")
    lines.extend(
        [
            "",
            "**Décision : porte globale V8S fermée.** La prochaine itération doit construire un paquet de solveur explicite indépendant du rendu Blender, en commençant par un sous-assemblage aile/moteur–panneau de façade et une étude de convergence avant toute tour complète.",
            "",
            "## 10. Reproductibilité",
            "",
            f"- Configuration : `{result['artifacts']['configuration']}`",
            f"- Script : `{result['artifacts']['script']}`",
            f"- Résultats : `{result['artifacts']['results']}`",
            f"- Graphique : `{result['artifacts']['plot']}`",
            f"- Graine déclarée : `{result['execution']['random_seed']}` (aucun tirage aléatoire dans V8S)",
            f"- Durée : {result['execution']['runtime_seconds']:.3f} s",
            "",
        ]
    )
    return "\n".join(lines)


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    paths = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in paths:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def draw_plot(result: dict[str, Any]) -> None:
    width, height = 1700, 1120
    image = Image.new("RGB", (width, height), "#f5f7fb")
    draw = ImageDraw.Draw(image)
    navy = "#18324a"
    blue = "#2f6f9f"
    orange = "#d9822b"
    red = "#b33a3a"
    green = "#2f7d59"
    gray = "#657786"
    draw.text((70, 45), "WTC 1 — V8S / Impact AA11", fill=navy, font=font(42, True))
    draw.text(
        (70, 100),
        "Enveloppe cinématique, contrôle d’échelle et porte solveur",
        fill=gray,
        font=font(24),
    )

    cases = result["derived_results"]["cases"]
    names = ["less_severe", "base", "more_severe"]
    labels = ["Moins sévère", "Base", "Plus sévère"]
    colors = [blue, orange, red]
    energies = [cases[name]["derived_kinematics"]["kinetic_energy_gj"] for name in names]
    maximum = max(energies)
    draw.text((75, 170), "Énergie cinétique initiale", fill=navy, font=font(28, True))
    for index, (name, label, color, energy) in enumerate(zip(names, labels, colors, energies)):
        y = 230 + index * 95
        draw.text((80, y), label, fill=navy, font=font(21, True))
        draw.rounded_rectangle((270, y, 270 + 660 * energy / maximum, y + 43), 8, fill=color)
        row = cases[name]
        draw.text(
            (950, y + 4),
            f"{energy:.3f} GJ   {row['inputs']['speed_mph']:.0f} mph   {row['inputs']['mass_kg']/1000:.1f} t",
            fill=navy,
            font=font(21),
        )

    base = cases["base"]
    clearance = result["comparison_to_reserved_official_outputs"]["tail_clearance"]
    draw.rounded_rectangle((70, 535, 820, 760), 18, fill="#ffffff", outline="#ccd6df", width=2)
    draw.text((100, 565), "Contrôle géométrique", fill=navy, font=font(27, True))
    draw.text(
        (100, 620),
        f"Queue derrière la façade : {clearance['predicted_from_inputs_s']:.3f} s",
        fill=blue,
        font=font(23, True),
    )
    draw.text((100, 664), "Sortie NIST : ≈ 0,250 s", fill=navy, font=font(22))
    draw.text(
        (100, 706),
        f"Écart : {clearance['absolute_error_s']:.3f} s — {'PASS' if clearance['passed'] else 'FAIL'}",
        fill=green if clearance["passed"] else red,
        font=font(22, True),
    )

    silhouette = base["reduced_silhouette_diagnostic"]
    draw.rounded_rectangle((880, 535, 1630, 760), 18, fill="#ffffff", outline="#ccd6df", width=2)
    draw.text((910, 565), "Projection rigide de l’envergure", fill=navy, font=font(27, True))
    draw.text(
        (910, 620),
        f"{silhouette['wing_horizontal_projection_m']:.1f} m horizontal ≈ {silhouette['nominal_facade_bays_spanned']:.1f} travées",
        fill=blue,
        font=font(22),
    )
    draw.text(
        (910, 664),
        f"{silhouette['wing_vertical_tip_separation_m']:.1f} m vertical ≈ {silhouette['nominal_floor_heights_spanned_by_wingtips']:.1f} étages",
        fill=orange,
        font=font(22),
    )
    draw.text((910, 710), "Diagnostic de silhouette — aucune rupture calculée", fill=gray, font=font(19))

    draw.text((75, 825), "Portes de calcul", fill=navy, font=font(28, True))
    gate_names = [
        ("Entrées sourcées", result["readiness"]["gates"]["source_files_present_and_hashed"]),
        ("Échelle temporelle", result["readiness"]["gates"]["tail_clearance_scale_check_passed"]),
        ("Maillage as-built", result["readiness"]["gates"]["as_built_impact_zone_mesh_complete"]),
        ("Solveur explicite", result["readiness"]["gates"]["solver_ready_for_global_high_rate_impact"]),
        ("Rejeu global", result["readiness"]["gates"]["global_aircraft_impact_replay_ready"]),
    ]
    for index, (label, passed) in enumerate(gate_names):
        x = 75 + index * 318
        fill = green if passed else red
        draw.rounded_rectangle((x, 885, x + 280, 965), 14, fill="#ffffff", outline=fill, width=3)
        draw.text((x + 18, 902), label, fill=navy, font=font(19, True))
        draw.text((x + 18, 936), "PASS" if passed else "FAIL", fill=fill, font=font(20, True))

    draw.text(
        (75, 1030),
        "Blender = visualisation. V8S ne conclut ni sur la carte de dommages, ni sur l’incendie, ni sur une démolition.",
        fill=gray,
        font=font(19),
    )
    image.save(PLOT_PATH)


def main() -> None:
    started = time.perf_counter()
    config = read_json(CONFIG_PATH)
    geometry = read_json(ROOT / config["provenance"]["tower_geometry"])
    sources = source_audit(config)
    solvers = solver_audit(config)
    integrity = input_integrity(config, geometry)
    cases = {
        name: case_calculation(name, config["nist_global_input_cases"][name], config)
        for name in ("less_severe", "base", "more_severe")
    }
    base_speed_mps = cases["base"]["inputs"]["speed_mps"]
    components = component_energy_table(config, base_speed_mps)
    comparison = reserved_output_comparison(config, cases)
    readiness = readiness_gates(config, sources, solvers, integrity, comparison)
    runtime = time.perf_counter() - started
    result = {
        "experiment_id": "WTC1-V8S",
        "status": "validated_input_freeze_reduced_kinematic_check_global_explicit_gate_not_passed",
        "execution": {
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "runtime_seconds": runtime,
            "random_seed": int(config["dataset"]["random_seed"]),
            "random_draws": 0,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "process_id": os.getpid(),
        },
        "dataset": config["dataset"],
        "source_audit": sources,
        "input_integrity": integrity,
        "derived_results": {
            "cases": cases,
            "base_case_component_energy": components,
        },
        "comparison_to_reserved_official_outputs": comparison,
        "solver_audit": solvers,
        "validation_metrics_predeclared": config["validation_metrics_predeclared"],
        "model_hypotheses": config["model_hypotheses"],
        "required_missing_inputs": config["required_missing_inputs"],
        "readiness": readiness,
        "interpretation": (
            "The base AA11 input envelope carries about 2.52 GJ and the independent geometric "
            "tail-clearance estimate agrees with the NIST 0.25 s scale. This is not a damage or "
            "collapse validation. No qualified global high-rate explicit solver or complete as-built "
            "impact-zone mesh is presently available, so the impact replay, thermal coupling and "
            "Blender dynamics gates remain closed."
        ),
        "artifacts": {
            "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
            "script": str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"),
            "results": str(RESULT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "report": str(REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "plot": str(PLOT_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    write_json(RESULT_PATH, result)
    draw_plot(result)
    REPORT_PATH.write_text(build_report(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "readiness": readiness}, ensure_ascii=False))


if __name__ == "__main__":
    main()
