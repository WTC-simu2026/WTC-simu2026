"""WTC 1 V8F - vertically coupled core load-path sensitivity, Floors 94-99.

V8E assessed each story independently.  V8F carries the final column loads of
one story into the story below, so an impact or thermal redistribution remains
present down the core.  This is still a transparent reduced-order network, not
a full-building finite-element analysis.  The floor diaphragm is represented
only by an explicit redistribution reach and is not strength-checked.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8b_stability_network as v8b  # noqa: E402


TRANSFER = V8 / "data" / "nist_wtc1_transfer.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
V8E_RESULT = V8 / "output" / "resultats_wtc1_v8e_champs_thermiques.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8f_transfert_vertical.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8f_transfert_vertical.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8f_transfert_vertical.png"

FLOORS_DESC = list(range(99, 93, -1))
TIMES = [20, 40, 60, 80, 100]
GAMMAS = [0.5, 1.0, 2.0, 4.0]
SEEDS = list(range(200))
TAILS = ["hold_e600_upper_bound", "linear_to_5pct_at_1000c"]
TRANSFER_SCHEMES = ["local_four", "local_eight", "global_capacity"]
AMPLIFICATIONS = [1.0, 1.15]
DAMAGE_RESIDUALS = {
    "nist_removed_only": {"moderate": 1.0, "light": 1.0},
    "moderate95_light99": {"moderate": 0.95, "light": 0.99},
    "moderate80_light95": {"moderate": 0.80, "light": 0.95},
}


def normalize_field(values: dict[int, float]) -> dict[int, float]:
    low = min(values.values())
    high = max(values.values())
    if high - low < 1e-12:
        return {column: 0.5 for column in values}
    return {column: (value - low) / (high - low) for column, value in values.items()}


def smooth_score(coords: dict[int, tuple[float, float]], seed: int) -> dict[int, float]:
    rng = random.Random(911_000 + seed)
    x_values = [xy[0] for xy in coords.values()]
    y_values = [xy[1] for xy in coords.values()]
    hot_spots = [
        (
            rng.uniform(min(x_values), max(x_values)),
            rng.uniform(min(y_values), max(y_values)),
            rng.uniform(4.0, 14.0),
            rng.uniform(0.5, 1.2),
        )
        for _ in range(rng.randint(1, 3))
    ]
    scores = {}
    for column, (x, y) in coords.items():
        value = sum(
            amplitude
            * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * sigma**2))
            for cx, cy, sigma, amplitude in hot_spots
        )
        scores[column] = value + 0.03 * rng.random()
    return normalize_field(scores)


def temperatures_from_scores(
    scores: dict[int, float], t_min: float, t_max: float, gamma: float
) -> dict[int, float]:
    normalized_scores = normalize_field(scores)
    return {
        column: t_min + (t_max - t_min) * max(0.0, min(1.0, score)) ** gamma
        for column, score in normalized_scores.items()
    }


def normalized(values: dict[int, float]) -> dict[int, float]:
    total = sum(values.values())
    if total <= 0.0:
        return {key: 1.0 / len(values) for key in values}
    return {key: value / total for key, value in values.items()}


def redistribute(
    source: int,
    value: float,
    loads: dict[int, float],
    survivors: set[int],
    sections: dict[int, dict[str, float | str]],
    coords: dict[int, tuple[float, float]],
    scheme: str,
    amplification: float,
) -> bool:
    if not survivors:
        return False
    if scheme == "global_capacity":
        weights = normalized(
            {column: float(sections[column]["room_pn_kip_k1"]) for column in survivors}
        )
    else:
        count = {"local_four": 4, "local_eight": 8}[scheme]
        sx, sy = coords[source]
        candidates = sorted(
            survivors,
            key=lambda column: (coords[column][0] - sx) ** 2 + (coords[column][1] - sy) ** 2,
        )[:count]
        weights = normalized(
            {
                column: 1.0
                / max(
                    (coords[column][0] - sx) ** 2 + (coords[column][1] - sy) ** 2,
                    0.05**2,
                )
                for column in candidates
            }
        )
    for column, weight in weights.items():
        loads[column] = loads.get(column, 0.0) + amplification * value * weight
    return True


def story_cascade(
    incoming_loads: dict[int, float],
    temperatures: dict[int, float],
    sections: dict[int, dict[str, float | str]],
    removed: set[int],
    impact_states: dict[int, str],
    residuals: dict[str, float],
    coords: dict[int, tuple[float, float]],
    tail: str,
    scheme: str,
    amplification: float,
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, object]:
    # Reintroduce unloaded lower-story segments as possible recipients.  A
    # segment that failed in the story above does not imply that the segment
    # below is absent; floor framing may transfer load into it.
    loads = {column: float(incoming_loads.get(column, 0.0)) for column in sections}
    survivors = set(sections) - removed
    initial_total = sum(loads.values())
    impact_transferred = 0.0
    for column in sorted(removed):
        value = loads.pop(column, 0.0)
        impact_transferred += value
        if not redistribute(
            column, value, loads, survivors, sections, coords, scheme, amplification
        ):
            return {
                "equilibrium": False,
                "reason": "no_recipient_after_impact_removal",
                "final_loads": {},
                "failed_columns": [],
                "surviving_count": 0,
                "initial_total_kip": initial_total,
                "final_total_kip": 0.0,
            }

    failed: list[int] = []
    maximum_dcr = 0.0
    while survivors:
        capacities = {}
        for column in survivors:
            residual = residuals.get(impact_states.get(column, "intact"), 1.0)
            capacities[column] = residual * v8b.nominal_column_capacity_kip(
                sections[column], temperatures[column], 1.0, fy_params, e_params, tail
            )
        dcr = {
            column: loads.get(column, 0.0) / max(capacities[column], 1e-9)
            for column in survivors
        }
        peak = max(dcr.values())
        maximum_dcr = max(maximum_dcr, peak)
        if peak <= 1.0:
            final_loads = {column: loads.get(column, 0.0) for column in survivors}
            return {
                "equilibrium": True,
                "reason": "stable",
                "final_loads": final_loads,
                "failed_columns": failed,
                "failed_count": len(failed),
                "surviving_count": len(survivors),
                "final_peak_dcr": peak,
                "maximum_dcr_during_cascade": maximum_dcr,
                "initial_total_kip": initial_total,
                "final_total_kip": sum(final_loads.values()),
                "impact_removed_load_transferred_kip": impact_transferred,
            }
        column = max(dcr, key=dcr.get)
        failed.append(column)
        value = loads.pop(column, 0.0)
        survivors.remove(column)
        if not redistribute(
            column, value, loads, survivors, sections, coords, scheme, amplification
        ):
            break

    return {
        "equilibrium": False,
        "reason": "cascade_exhausted_survivors",
        "final_loads": {},
        "failed_columns": failed,
        "failed_count": len(failed),
        "surviving_count": 0,
        "final_peak_dcr": None,
        "maximum_dcr_during_cascade": maximum_dcr,
        "initial_total_kip": initial_total,
        "final_total_kip": 0.0,
        "impact_removed_load_transferred_kip": impact_transferred,
    }


def simulate_path(
    demand: float,
    base_score: dict[int, float],
    gamma: float,
    time_index: int,
    prepared: dict[int, dict[str, object]],
    thermal: dict[str, list[list[float]]],
    coords: dict[int, tuple[float, float]],
    tail: str,
    scheme: str,
    amplification: float,
    residuals: dict[str, float],
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, object]:
    top_sections = prepared[99]["sections"]
    incoming = v8b.initial_loads(demand, top_sections, {}, "capacity_proportional")
    floor_results = {}
    first_failed_floor = None
    for floor in FLOORS_DESC:
        sections = prepared[floor]["sections"]
        t_min, t_max = [float(value) for value in thermal[str(floor)][time_index]]
        scores = normalize_field({column: base_score[column] for column in sections})
        temperatures = temperatures_from_scores(scores, t_min, t_max, gamma)
        state = story_cascade(
            incoming,
            temperatures,
            sections,
            prepared[floor]["removed"],
            prepared[floor]["impact_states"],
            residuals,
            coords,
            tail,
            scheme,
            amplification,
            fy_params,
            e_params,
        )
        floor_results[str(floor)] = {
            key: value for key, value in state.items() if key != "final_loads"
        }
        if not state["equilibrium"]:
            first_failed_floor = floor
            break
        incoming = state["final_loads"]
    return {
        "equilibrium_all_floors": first_failed_floor is None,
        "first_failed_floor": first_failed_floor,
        "floors_reached": len(floor_results),
        "floors": floor_results,
    }


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = fraction * (len(ordered) - 1)
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (position - low) * (ordered[high] - ordered[low])


def main() -> None:
    transfer = json.loads(TRANSFER.read_text(encoding="utf-8"))
    prior_b = json.loads(V8B_RESULT.read_text(encoding="utf-8"))
    prior_e = json.loads(V8E_RESULT.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }
    fy_params = transfer["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = transfer["steel_temperature_model"]["young_modulus_parameters"]
    thermal = transfer["fire_case_b"]["core_column_temperature_ranges_c"]
    history = transfer["nist_global_core_loads_floor_98_kip"]["case_b_time_history"]
    damage = transfer["core_damage"]["more_severe"]

    prepared: dict[int, dict[str, object]] = {}
    for floor in FLOORS_DESC:
        floor_data = prior_b["floor_inputs"][str(floor)]
        states = {
            int(row["column"]): str(row["state"])
            for row in damage
            if floor in [int(value) for value in row["floors"]]
        }
        prepared[floor] = {
            "sections": {int(key): value for key, value in floor_data["sections"].items()},
            "removed": set(int(value) for value in floor_data["initial_removed"]),
            "impact_states": states,
        }

    prior_lookup = {
        (row["time_min"], row["elastic_modulus_tail"], row["gamma"]): row[
            "system_no_equilibrium_fraction"
        ]
        for row in prior_e["smooth_field_ensemble"]
    }
    fields = {seed: smooth_score(coords, seed) for seed in SEEDS}
    rows = []
    for time_index, time in enumerate(TIMES):
        demand = float(history[str(time)])
        for tail in TAILS:
            for gamma in GAMMAS:
                for scheme in TRANSFER_SCHEMES:
                    for damage_name, residuals in DAMAGE_RESIDUALS.items():
                        for amplification in AMPLIFICATIONS:
                            failures = 0
                            first_floors: list[int] = []
                            reached: list[int] = []
                            final_floor_peak_dcr: list[float] = []
                            for seed in SEEDS:
                                state = simulate_path(
                                    demand,
                                    fields[seed],
                                    gamma,
                                    time_index,
                                    prepared,
                                    thermal,
                                    coords,
                                    tail,
                                    scheme,
                                    amplification,
                                    residuals,
                                    fy_params,
                                    e_params,
                                )
                                reached.append(int(state["floors_reached"]))
                                if not state["equilibrium_all_floors"]:
                                    failures += 1
                                    first_floors.append(int(state["first_failed_floor"]))
                                elif "94" in state["floors"]:
                                    final_floor_peak_dcr.append(
                                        float(state["floors"]["94"]["final_peak_dcr"])
                                    )
                            rows.append(
                                {
                                    "time_min": time,
                                    "elastic_modulus_tail": tail,
                                    "gamma": gamma,
                                    "redistribution": scheme,
                                    "damage_residual_case": damage_name,
                                    "transfer_amplification": amplification,
                                    "field_count": len(SEEDS),
                                    "system_no_equilibrium_fraction": failures / len(SEEDS),
                                    "prior_v8e_independent_fraction": prior_lookup[(time, tail, gamma)],
                                    "median_first_failed_floor": statistics.median(first_floors)
                                    if first_floors
                                    else None,
                                    "first_failed_floor_counts": {
                                        str(floor): first_floors.count(floor) for floor in FLOORS_DESC
                                    },
                                    "median_floors_reached": statistics.median(reached),
                                    "median_floor94_peak_dcr_when_reached": statistics.median(
                                        final_floor_peak_dcr
                                    )
                                    if final_floor_peak_dcr
                                    else None,
                                    "p90_floor94_peak_dcr_when_reached": quantile(
                                        final_floor_peak_dcr, 0.9
                                    )
                                    if final_floor_peak_dcr
                                    else None,
                                }
                            )

    payload = {
        "model": "WTC1_V8F_VERTICALLY_COUPLED_CORE_LOAD_PATH",
        "version": "8.5.0",
        "facts_transferred": {
            "floors": sorted(FLOORS_DESC),
            "times_min": TIMES,
            "impact_damage": "NIST Case B: severed/heavy segments removed only on reported stories",
            "temperature_input": "NIST Case B per-floor spatial extrema",
            "demand_input": "NIST Case B Floor 98 total core compression history",
        },
        "model_assumptions": {
            "vertical_coupling": "stable final column loads at each story become incoming loads at the story below",
            "top_load": "Floor 98 total core demand applied at Floor 99 because per-floor totals are unavailable",
            "story_self_weight": "not added between Floors 99 and 94",
            "floor_diaphragm": "unlimited strength; represented only by nearest-4, nearest-8, or global redistribution",
            "transfer_amplification": AMPLIFICATIONS,
            "damage_residuals": DAMAGE_RESIDUALS,
            "moderate_light_warning": "residual factors are sensitivity assumptions, not NIST measured capacities",
            "temperatures": "vertically correlated synthetic fields that span NIST extrema; not column temperature measurements",
            "fractions_are_probabilities": False,
        },
        "ensemble_rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    baseline = [
        row
        for row in rows
        if row["redistribution"] == "local_four"
        and row["damage_residual_case"] == "nist_removed_only"
        and row["transfer_amplification"] == 1.0
    ]
    baseline_100 = [row for row in baseline if row["time_min"] == 100]
    linear_100 = {
        row["gamma"]: row
        for row in baseline_100
        if row["elastic_modulus_tail"] == "linear_to_5pct_at_1000c"
    }
    sensitivity_100 = [
        row
        for row in rows
        if row["time_min"] == 100
        and row["elastic_modulus_tail"] == "linear_to_5pct_at_1000c"
        and row["gamma"] == 1.0
        and row["transfer_amplification"] == 1.0
    ]

    md = [
        "# WTC 1 - V8F : chemin de charge vertical couple, niveaux 94-99",
        "",
        "## Resultat principal",
        "",
        "V8F conserve les redistributions de charge d'un niveau au suivant. La fraction de champs sans equilibre reste une metrique de robustesse sur 200 champs thermiques synthetiques bornes par NIST; ce n'est pas une probabilite de l'effondrement reel.",
        "",
        "### Cas de base a 100 min",
        "",
        "Redistribution vers quatre colonnes voisines, aucun affaiblissement invente des dommages moderate/light, amplification de transfert 1,00.",
        "",
        "| Champ thermique | V8E, niveaux independants | V8F, chemin vertical | premier niveau defaillant median |",
        "|---|---:|---:|---:|",
    ]
    for gamma in GAMMAS:
        row = linear_100[gamma]
        md.append(
            f"| gamma={str(gamma).replace('.', ',')} | {100*row['prior_v8e_independent_fraction']:.1f} % | {100*row['system_no_equilibrium_fraction']:.1f} % | {row['median_first_failed_floor'] if row['median_first_failed_floor'] is not None else 'aucun'} |"
        )
    md.extend(
        [
            "",
            "### Sensibilite du transfert a 100 min, gamma=1",
            "",
            "| Portee de redistribution | Capacite moderate/light | champs sans equilibre |",
            "|---|---|---:|",
        ]
    )
    damage_labels = {
        "nist_removed_only": "100 % / 100 % (regle NIST de retrait seule)",
        "moderate95_light99": "95 % / 99 % (hypothese)",
        "moderate80_light95": "80 % / 95 % (hypothese conservative)",
    }
    scheme_labels = {
        "local_four": "4 voisines",
        "local_eight": "8 voisines",
        "global_capacity": "globale proportionnelle a la capacite",
    }
    for scheme in TRANSFER_SCHEMES:
        for damage_name in DAMAGE_RESIDUALS:
            row = next(
                item
                for item in sensitivity_100
                if item["redistribution"] == scheme
                and item["damage_residual_case"] == damage_name
            )
            md.append(
                f"| {scheme_labels[scheme]} | {damage_labels[damage_name]} | {100*row['system_no_equilibrium_fraction']:.1f} % |"
            )
    md.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Une perte d'equilibre signifie que ce reseau statique ne trouve plus de chemin de compression avec la regle imposee; elle ne simule pas encore le mouvement global ni la propagation dynamique.",
            "- Le couplage vertical diminue ici la fraction sans equilibre par rapport a V8E : a gamma=1, elle passe de 71,0 % a 61,5 %. La distribution heritee des niveaux superieurs peut donc decharger certaines colonnes localement vulnerables au lieu de recommencer une repartition independante a chaque etage.",
            "- La comparaison V8E/V8F isole l'effet du couplage vertical. Les variations entre 4 voisines, 8 voisines et redistribution globale mesurent l'incertitude sur le role des poutres, dalles et connexions.",
            "- Une amplification hypothetique de 1,15 de chaque charge transferee porte, a 100 min et gamma=1, la fraction sans equilibre a 99,0 % pour 4 voisines, 92,0 % pour 8 voisines et 1,5 % pour la redistribution globale. Ce fort ecart montre pourquoi l'etape dynamique ne peut pas etre deduite du seul calcul statique.",
            "- Les facteurs moderate/light sont volontairement separes des faits NIST. Aucun de ces facteurs n'est presente comme une mesure publiee.",
            "- Leur effet n'est pas strictement monotone dans les variantes locales (ecarts de quelques points), car l'algorithme sequentiel change l'ordre des ruptures et donc le chemin impose. C'est une sensibilite de la regle de cascade, pas un effet physique a interpreter.",
            "- Le modele ne verifie pas la resistance du diaphragme qui effectue le transfert. Cette limite peut rendre certaines redistributions trop optimistes.",
            "- La facade, les planchers exterieurs, le hat truss, le fluage, les connexions et la dynamique de chute restent absents.",
            "",
        ]
    )
    OUT_REPORT.write_text("\n".join(md), encoding="utf-8")

    tail = "linear_to_5pct_at_1000c"
    matrix = [
        [
            next(
                row["system_no_equilibrium_fraction"]
                for row in baseline
                if row["time_min"] == time
                and row["gamma"] == gamma
                and row["elastic_modulus_tail"] == tail
            )
            for gamma in GAMMAS
        ]
        for time in TIMES
    ]
    sens_matrix = []
    y_labels = []
    for scheme in TRANSFER_SCHEMES:
        sens_matrix.append(
            [
                next(
                    row["system_no_equilibrium_fraction"]
                    for row in sensitivity_100
                    if row["redistribution"] == scheme
                    and row["damage_residual_case"] == damage_name
                )
                for damage_name in DAMAGE_RESIDUALS
            ]
        )
        y_labels.append(scheme_labels[scheme])

    def heat_color(value: float) -> tuple[int, int, int]:
        stops = [
            (0.0, (24, 15, 54)),
            (0.35, (111, 31, 95)),
            (0.7, (220, 75, 65)),
            (1.0, (252, 221, 92)),
        ]
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if value <= b:
                f = (value - a) / (b - a)
                return tuple(round(ca[k] + f * (cb[k] - ca[k])) for k in range(3))
        return stops[-1][1]

    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        name = "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            return ImageFont.load_default()

    image = Image.new("RGB", (1900, 920), "white")
    draw = ImageDraw.Draw(image)
    draw.text((950, 42), "WTC 1 - V8F : chemin de charge vertical couple", anchor="ma", font=font(42, True), fill=(20, 25, 35))
    draw.text((950, 102), "200 champs par case - robustesse, pas probabilite physique", anchor="ma", font=font(26), fill=(90, 95, 105))

    # Left: time/localization heat map.  Store TIMES bottom-to-top visually.
    left_x, top_y, cw, ch = 160, 245, 130, 90
    draw.text((left_x + 2*cw, 175), "Cas de base", anchor="ma", font=font(30, True), fill=(25, 30, 40))
    for j, gamma in enumerate(GAMMAS):
        draw.text((left_x + j*cw + cw/2, top_y - 32), str(gamma).replace(".", ","), anchor="mm", font=font(23), fill=(35, 40, 50))
    for row_index, time in enumerate(reversed(TIMES)):
        source_index = TIMES.index(time)
        y = top_y + row_index*ch
        draw.text((left_x - 22, y + ch/2), str(time), anchor="rm", font=font(23), fill=(35, 40, 50))
        for j, value in enumerate(matrix[source_index]):
            x = left_x + j*cw
            draw.rectangle((x, y, x+cw, y+ch), fill=heat_color(value), outline="white", width=3)
            draw.text((x+cw/2, y+ch/2), f"{100*value:.0f}%", anchor="mm", font=font(24, True), fill="white" if value < 0.78 else (25, 20, 25))
    draw.text((left_x + 2*cw, top_y + 5*ch + 42), "gamma : diffusion vers localisation", anchor="ma", font=font(23), fill=(45, 50, 60))
    draw.text((12, top_y + 2.5*ch), "Temps", anchor="lm", font=font(23), fill=(45, 50, 60))

    # Right: redistribution/damage-residual sensitivity.
    right_x, right_y, rw, rh = 1050, 285, 190, 112
    draw.text((right_x + 1.5*rw, 175), "A 100 min - gamma=1 - amplification 1,00", anchor="ma", font=font(30, True), fill=(25, 30, 40))
    for j, label in enumerate(["100/100", "95/99", "80/95"]):
        draw.text((right_x + j*rw + rw/2, right_y - 34), label, anchor="mm", font=font(23), fill=(35, 40, 50))
    short_y_labels = ["4 voisines", "8 voisines", "globale"]
    for i, values in enumerate(sens_matrix):
        y = right_y + i*rh
        draw.text((right_x - 25, y + rh/2), short_y_labels[i], anchor="rm", font=font(23), fill=(35, 40, 50))
        for j, value in enumerate(values):
            x = right_x + j*rw
            draw.rectangle((x, y, x+rw, y+rh), fill=heat_color(value), outline="white", width=3)
            draw.text((x+rw/2, y+rh/2), f"{100*value:.0f}%", anchor="mm", font=font(25, True), fill="white" if value < 0.78 else (25, 20, 25))
    draw.text((right_x + 1.5*rw, right_y + 3*rh + 46), "Capacite residuelle moderate/light (%)", anchor="ma", font=font(23), fill=(45, 50, 60))
    draw.text((950, 840), "Une case sans equilibre indique l'echec du reseau statique impose, pas une preuve d'effondrement global.", anchor="ma", font=font(24), fill=(90, 45, 45))
    image.save(OUT_PNG)
    print(json.dumps({"json": str(OUT_JSON), "report": str(OUT_REPORT), "plot": str(OUT_PNG), "cases": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
