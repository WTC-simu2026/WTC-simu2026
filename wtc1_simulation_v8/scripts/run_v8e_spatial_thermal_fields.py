"""WTC 1 V8E — spatially correlated thermal-field sensitivity, Floors 94-99.

NIST publishes per-floor spatial minima and maxima rather than a temperature
for each core column.  V8E therefore does not invent a single 'best' map.  It
tests explicit deterministic envelopes and ensembles of smooth spatial fields
that exactly span each published range.  Fractions of synthetic fields are
robustness metrics, not physical probabilities.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8b_stability_network as v8b  # noqa: E402


TRANSFER = V8 / "data" / "nist_wtc1_transfer.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8e_champs_thermiques.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8e_champs_thermiques.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8e_champs_thermiques.png"

FLOORS = list(range(94, 100))
TIMES = [20, 40, 60, 80, 100]
GAMMAS = [0.5, 1.0, 2.0, 4.0]
SEEDS = list(range(200))
TAILS = ["hold_e600_upper_bound", "linear_to_5pct_at_1000c"]


def normalize(values: dict[int, float]) -> dict[int, float]:
    low = min(values.values())
    high = max(values.values())
    if high - low < 1e-12:
        return {column: 0.5 for column in values}
    return {column: (value - low) / (high - low) for column, value in values.items()}


def smooth_score(coords: dict[int, tuple[float, float]], seed: int) -> dict[int, float]:
    rng = random.Random(911_000 + seed)
    x_values = [xy[0] for xy in coords.values()]
    y_values = [xy[1] for xy in coords.values()]
    hot_spots = []
    for _ in range(rng.randint(1, 3)):
        hot_spots.append(
            (
                rng.uniform(min(x_values), max(x_values)),
                rng.uniform(min(y_values), max(y_values)),
                rng.uniform(4.0, 14.0),
                rng.uniform(0.5, 1.2),
            )
        )
    scores = {}
    for column, (x, y) in coords.items():
        value = 0.0
        for cx, cy, sigma, amplitude in hot_spots:
            value += amplitude * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * sigma**2))
        value += 0.03 * rng.random()
        scores[column] = value
    return normalize(scores)


def deterministic_scores(
    name: str,
    columns: set[int],
    coords: dict[int, tuple[float, float]],
    start_loads: dict[int, float],
    sections: dict[int, dict[str, float | str]],
    t_max: float,
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[int, float]:
    if name in {"uniform_min", "uniform_midpoint", "uniform_max"}:
        value = {"uniform_min": 0.0, "uniform_midpoint": 0.5, "uniform_max": 1.0}[name]
        return {column: value for column in columns}
    if name == "capacity_targeted":
        raw = {
            column: start_loads[column]
            / max(
                v8b.nominal_column_capacity_kip(
                    sections[column],
                    t_max,
                    1.0,
                    fy_params,
                    e_params,
                    "linear_to_5pct_at_1000c",
                ),
                1e-9,
            )
            for column in columns
        }
        return normalize(raw)
    if name == "damage_centered":
        # Center of the NIST Case-B severed/heavy cluster in the surviving plan.
        cx, cy, sigma = 0.0, 5.0, 8.0
    elif name == "north_hotspot":
        cx, cy, sigma = 0.0, 11.0, 8.0
    elif name == "south_hotspot":
        cx, cy, sigma = 0.0, -10.0, 8.0
    else:
        raise ValueError(name)
    raw = {
        column: math.exp(-((coords[column][0] - cx) ** 2 + (coords[column][1] - cy) ** 2) / (2.0 * sigma**2))
        for column in columns
    }
    return normalize(raw)


def temperatures_from_scores(
    scores: dict[int, float], t_min: float, t_max: float, gamma: float
) -> dict[int, float]:
    if all(abs(value - next(iter(scores.values()))) < 1e-12 for value in scores.values()):
        return {column: t_min + (t_max - t_min) * value for column, value in scores.items()}
    normalized = normalize(scores)
    return {
        column: t_min + (t_max - t_min) * max(0.0, min(1.0, score)) ** gamma
        for column, score in normalized.items()
    }


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    position = fraction * (len(ordered) - 1)
    low = int(math.floor(position))
    high = int(math.ceil(position))
    if low == high:
        return ordered[low]
    return ordered[low] + (position - low) * (ordered[high] - ordered[low])


def main() -> None:
    transfer = json.loads(TRANSFER.read_text(encoding="utf-8"))
    prior = json.loads(V8B_RESULT.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }
    fy_params = transfer["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = transfer["steel_temperature_model"]["young_modulus_parameters"]
    thermal = transfer["fire_case_b"]["core_column_temperature_ranges_c"]
    demand_history = transfer["nist_global_core_loads_floor_98_kip"]["case_b_time_history"]

    prepared: dict[int, dict[str, object]] = {}
    for floor in FLOORS:
        floor_data = prior["floor_inputs"][str(floor)]
        sections = {int(key): value for key, value in floor_data["sections"].items()}
        removed = set(int(value) for value in floor_data["initial_removed"])
        prepared[floor] = {"sections": sections, "removed": removed}

    deterministic_names = [
        "uniform_min",
        "uniform_midpoint",
        "uniform_max",
        "damage_centered",
        "north_hotspot",
        "south_hotspot",
        "capacity_targeted",
    ]
    deterministic_rows = []
    ensemble_rows = []
    field_cache = {seed: smooth_score(coords, seed) for seed in SEEDS}

    for time_index, time in enumerate(TIMES):
        demand = float(demand_history[str(time)])
        floor_starts: dict[int, dict[str, object]] = {}
        for floor in FLOORS:
            sections = prepared[floor]["sections"]
            removed = prepared[floor]["removed"]
            raw = v8b.initial_loads(demand, sections, {}, "capacity_proportional")
            start, viable = v8b.remove_initial_damage(
                raw, removed, sections, coords, "local_four"
            )
            if not viable:
                raise RuntimeError(f"Initial damage redistribution failed at Floor {floor}")
            floor_starts[floor] = {"start": start, "sections": sections}

        for tail in TAILS:
            for name in deterministic_names:
                system_equilibrium = True
                floor_results = {}
                for floor in FLOORS:
                    start = floor_starts[floor]["start"]
                    sections = floor_starts[floor]["sections"]
                    t_min, t_max = [float(value) for value in thermal[str(floor)][time_index]]
                    scores = deterministic_scores(
                        name,
                        set(start),
                        coords,
                        start,
                        sections,
                        t_max,
                        fy_params,
                        e_params,
                    )
                    temps = temperatures_from_scores(scores, t_min, t_max, 1.0)
                    state = v8b.cascade(
                        start,
                        temps,
                        sections,
                        coords,
                        1.0,
                        "local_four",
                        fy_params,
                        e_params,
                        tail,
                    )
                    system_equilibrium = system_equilibrium and bool(state["equilibrium"])
                    floor_results[str(floor)] = {
                        "temperature_min_assigned_c": min(temps.values()),
                        "temperature_max_assigned_c": max(temps.values()),
                        **state,
                    }
                deterministic_rows.append(
                    {
                        "time_min": time,
                        "elastic_modulus_tail": tail,
                        "field": name,
                        "system_equilibrium_all_floors": system_equilibrium,
                        "floors": floor_results,
                    }
                )

            for gamma in GAMMAS:
                system_failures = 0
                floor_failures = {floor: 0 for floor in FLOORS}
                additional_counts = {floor: [] for floor in FLOORS}
                system_failed_floor_counts = []
                for seed in SEEDS:
                    base_score = field_cache[seed]
                    failed_floor_count = 0
                    for floor in FLOORS:
                        start = floor_starts[floor]["start"]
                        sections = floor_starts[floor]["sections"]
                        t_min, t_max = [float(value) for value in thermal[str(floor)][time_index]]
                        floor_scores = normalize({column: base_score[column] for column in start})
                        temps = temperatures_from_scores(floor_scores, t_min, t_max, gamma)
                        state = v8b.cascade(
                            start,
                            temps,
                            sections,
                            coords,
                            1.0,
                            "local_four",
                            fy_params,
                            e_params,
                            tail,
                        )
                        additional_counts[floor].append(int(state["additional_failed_count"]))
                        if not bool(state["equilibrium"]):
                            floor_failures[floor] += 1
                            failed_floor_count += 1
                    if failed_floor_count:
                        system_failures += 1
                    system_failed_floor_counts.append(failed_floor_count)
                ensemble_rows.append(
                    {
                        "time_min": time,
                        "elastic_modulus_tail": tail,
                        "gamma": gamma,
                        "field_count": len(SEEDS),
                        "interpretation": "fraction of bounded synthetic fields; not a physical probability",
                        "system_no_equilibrium_fraction": system_failures / len(SEEDS),
                        "median_failed_floor_count": statistics.median(system_failed_floor_counts),
                        "p90_failed_floor_count": quantile(system_failed_floor_counts, 0.9),
                        "floors": {
                            str(floor): {
                                "no_equilibrium_fraction": floor_failures[floor] / len(SEEDS),
                                "median_additional_failed_columns": statistics.median(additional_counts[floor]),
                                "p90_additional_failed_columns": quantile(additional_counts[floor], 0.9),
                            }
                            for floor in FLOORS
                        },
                    }
                )

    payload = {
        "model": "WTC1_V8E_SPATIALLY_CORRELATED_THERMAL_FIELD_SENSITIVITY",
        "version": "8.4.0",
        "facts_transferred": {
            "floors": FLOORS,
            "times_min": TIMES,
            "temperature_input": "NIST Case B per-floor spatial minimum and maximum",
            "demand_input": "NIST Case B Floor 98 total core compression history",
            "impact_damage": "NIST more-severe Case B severed/heavy columns removed floor by floor",
        },
        "model_assumptions": {
            "effective_length_factor": 1.0,
            "initial_load_allocation": "capacity proportional",
            "redistribution": "four nearest surviving columns",
            "system_criterion": "all six independently assessed stories must retain equilibrium",
            "vertical_coupling_limit": "spatial fields are vertically correlated, but failed-member load transfer between stories is not yet represented",
            "floor_demand_limit": "Floor 98 total core compression is used at Floors 94-99 because floor-specific totals are unavailable",
            "temperature_limit": "synthetic fields reproduce extrema but are not NIST column-by-column temperatures",
        },
        "ensemble": {
            "seeds": len(SEEDS),
            "gamma_values": GAMMAS,
            "gamma_meaning": "0.5 diffuse hot field; 4.0 localized hot field",
            "fields_are_probabilities": False,
        },
        "deterministic_cases": deterministic_rows,
        "smooth_field_ensemble": ensemble_rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Focused 100-minute summary.
    final_rows = [row for row in ensemble_rows if row["time_min"] == 100]
    md = [
        "# WTC 1 — V8E : champs thermiques spatiaux corrélés, niveaux 94–99",
        "",
        "## Résultat",
        "",
        "V8E remplace la température uniforme par 200 champs spatiaux lisses pour chaque combinaison. Chaque champ atteint exactement les extrema publiés par NIST au niveau considéré. Les fractions ci-dessous décrivent uniquement la robustesse de cet ensemble synthétique; elles ne sont pas des probabilités de l’événement réel.",
        "",
        "### À 100 minutes — perte d’équilibre d’au moins un niveau",
        "",
        "| Extrapolation E au-dessus de 600 °C | Répartition thermique | Fraction des 200 champs | Niveaux défaillants médians |",
        "|---|---:|---:|---:|",
    ]
    for row in final_rows:
        tail_label = "E maintenu à E600 (borne haute)" if row["elastic_modulus_tail"] == "hold_e600_upper_bound" else "E décroît vers 5 % à 1000 °C"
        field_label = {0.5: "diffuse, γ=0,5", 1.0: "linéaire, γ=1", 2.0: "localisée, γ=2", 4.0: "très localisée, γ=4"}[row["gamma"]]
        md.append(f"| {tail_label} | {field_label} | {100*row['system_no_equilibrium_fraction']:.1f} % | {row['median_failed_floor_count']:.1f} |")

    final_linear = {
        row["gamma"]: row
        for row in final_rows
        if row["elastic_modulus_tail"] == "linear_to_5pct_at_1000c"
    }
    md.extend(
        [
            "",
            "### Localisation par niveau à 100 minutes",
            "",
            "| Niveau | Champs γ=1 sans équilibre | Champs très localisés γ=4 sans équilibre |",
            "|---:|---:|---:|",
        ]
    )
    for floor in FLOORS:
        md.append(
            f"| {floor} | {100*final_linear[1.0]['floors'][str(floor)]['no_equilibrium_fraction']:.1f} % | {100*final_linear[4.0]['floors'][str(floor)]['no_equilibrium_fraction']:.1f} % |"
        )

    det100 = [row for row in deterministic_rows if row["time_min"] == 100 and row["elastic_modulus_tail"] == "linear_to_5pct_at_1000c"]
    md.extend(
        [
            "",
            "### Enveloppes déterministes à 100 minutes",
            "",
            "| Champ | Équilibre conservé aux six niveaux | Niveaux sans équilibre |",
            "|---|---:|---|",
        ]
    )
    labels = {
        "uniform_min": "minimum uniforme (borne froide)",
        "uniform_midpoint": "milieu uniforme, non médian NIST",
        "uniform_max": "maximum uniforme (borne chaude irréaliste)",
        "damage_centered": "foyer centré sur la zone endommagée",
        "north_hotspot": "foyer nord",
        "south_hotspot": "foyer sud",
        "capacity_targeted": "foyer ciblant les colonnes les plus sollicitées",
    }
    for row in det100:
        failed = [floor for floor, state in row["floors"].items() if not state["equilibrium"]]
        md.append(f"| {labels[row['field']]} | {'oui' if row['system_equilibrium_all_floors'] else 'non'} | {', '.join(failed) if failed else 'aucun'} |")
    md.extend(
        [
            "",
            "## Ce que V8E établit — et n’établit pas",
            "",
            "- Il mesure la sensibilité à l’information thermique manquante sans présenter un champ inventé comme le champ réel.",
            "- Une perte d’équilibre dans ce réseau signifie que la règle locale de redistribution ne trouve plus de portance; ce n’est pas encore une simulation dynamique de la tour.",
            "- Les planchers, poutres du noyau, façades, connexions, hat truss, fluage et transfert vertical post-rupture restent absents.",
            "- Le résultat le plus important est la séparation entre cas robustes et cas dépendant fortement de l’emplacement du foyer.",
            "",
        ]
    )
    OUT_REPORT.write_text("\n".join(md), encoding="utf-8")

    # Heatmap: ensemble no-equilibrium fraction versus time and localization.
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), dpi=180, sharey=True, layout="constrained")
    for ax, tail in zip(axes, TAILS):
        subset = [row for row in ensemble_rows if row["elastic_modulus_tail"] == tail]
        matrix = [
            [
                next(row["system_no_equilibrium_fraction"] for row in subset if row["time_min"] == time and row["gamma"] == gamma)
                for gamma in GAMMAS
            ]
            for time in TIMES
        ]
        image = ax.imshow(matrix, origin="lower", aspect="auto", vmin=0.0, vmax=1.0, cmap="magma")
        ax.set_xticks(range(len(GAMMAS)), [str(value).replace(".", ",") for value in GAMMAS])
        ax.set_yticks(range(len(TIMES)), TIMES)
        ax.set_xlabel("γ : diffusion → localisation")
        ax.set_title("E maintenu à E600" if tail.startswith("hold") else "E extrapolé vers 5 % à 1000 °C", pad=10)
        for i, row_values in enumerate(matrix):
            for j, value in enumerate(row_values):
                ax.text(j, i, f"{100*value:.0f}%", ha="center", va="center", color="white" if value > 0.45 else "black", fontsize=9)
    axes[0].set_ylabel("Temps après impact (min)")
    fig.suptitle("WTC 1 — V8E : champs synthétiques sans équilibre à au moins un niveau\n200 champs par case — métrique de robustesse, pas probabilité physique", fontsize=15)
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.82, label="fraction de champs")
    fig.savefig(OUT_PNG, bbox_inches="tight")
    print(json.dumps({"json": str(OUT_JSON), "report": str(OUT_REPORT), "plot": str(OUT_PNG), "ensemble_cases": len(ensemble_rows)}, indent=2))


if __name__ == "__main__":
    main()
