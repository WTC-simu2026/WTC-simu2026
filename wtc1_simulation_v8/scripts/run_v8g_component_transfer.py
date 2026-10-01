"""WTC 1 V8G - component-bounded floor-seat and hat-truss checks.

V8G separates two mechanisms that V8F bundled under a generic transfer label:
1. vertical core-to-wall transfer through the hat truss; and
2. support of floor trusses by their interior and exterior seats.

The hat-truss check is necessarily NIST-calibrated because the only available
aggregate transfer demand is from the NIST global model.  It is therefore an
internal mechanical-consistency check, not an independent global FE solution.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8f_vertical_load_path as v8f  # noqa: E402


COMPONENTS = V8 / "data" / "nist_wtc1_component_capacities_v8g.json"
TRANSFER = V8 / "data" / "nist_wtc1_transfer.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8g_composants.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8g_composants.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8g_composants.png"

FLOORS = list(range(94, 100))
FLOORS_DESC = list(reversed(FLOORS))
TIMES = [20, 40, 60, 80, 100]
GAMMAS = [0.5, 1.0, 2.0, 4.0]
SEEDS = list(range(200))
LOAD_FACTORS = [1.0, 2.0, 4.0, 6.0]
SCHEMES = ["local_four", "local_eight", "global_capacity"]


def interpolate(x: float, xs: list[float], ys: list[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for index in range(1, len(xs)):
        if x <= xs[index]:
            fraction = (x - xs[index - 1]) / (xs[index] - xs[index - 1])
            return ys[index - 1] + fraction * (ys[index] - ys[index - 1])
    raise AssertionError("unreachable")


def seat_ensemble(
    component_data: dict[str, object],
    transfer_data: dict[str, object],
    coords: dict[int, tuple[float, float]],
) -> list[dict[str, object]]:
    seats = component_data["floor_truss_seats"]
    temperature_axis = [float(value) for value in seats["temperatures_c"]]
    thermal = transfer_data["fire_case_b"]["floor_truss_temperature_ranges_c"]
    rows: list[dict[str, object]] = []
    score_fields = {seed: v8f.smooth_score(coords, seed) for seed in SEEDS}
    for floor in FLOORS:
        for time_index, time in enumerate(TIMES):
            t_min, t_max = [float(value) for value in thermal[str(floor)][time_index]]
            for gamma in GAMMAS:
                temperature_fields = [
                    v8f.temperatures_from_scores(score_fields[seed], t_min, t_max, gamma)
                    for seed in SEEDS
                ]
                for side, capacity_key in [
                    ("interior", "interior_vertical_capacity_kip"),
                    ("exterior", "exterior_vertical_capacity_kip"),
                ]:
                    curves = seats[capacity_key]
                    for load_factor in LOAD_FACTORS:
                        demand = float(seats["normal_service_load_per_paired_trusses_kip"]) * load_factor
                        ratios: list[float] = []
                        below = 0
                        count = 0
                        field_fractions: list[float] = []
                        for temperature_field in temperature_fields:
                            field_below = 0
                            field_count = 0
                            for temperature in temperature_field.values():
                                for curve in curves.values():
                                    capacity = interpolate(
                                        float(temperature),
                                        temperature_axis,
                                        [float(value) for value in curve],
                                    )
                                    ratios.append(capacity / demand)
                                    field_below += int(capacity < demand)
                                    field_count += 1
                            below += field_below
                            count += field_count
                            field_fractions.append(field_below / field_count)
                        rows.append(
                            {
                                "floor": floor,
                                "time_min": time,
                                "gamma": gamma,
                                "seat_side": side,
                                "load_factor": load_factor,
                                "demand_kip": demand,
                                "temperature_min_c": t_min,
                                "temperature_max_c": t_max,
                                "sample_type_combinations": count,
                                "capacity_below_demand_fraction": below / count,
                                "median_field_fraction": statistics.median(field_fractions),
                                "median_capacity_to_demand": statistics.median(ratios),
                                "minimum_capacity_to_demand": min(ratios),
                            }
                        )
    return rows


def prepare_core_inputs(
    transfer: dict[str, object], prior_b: dict[str, object]
) -> dict[int, dict[str, object]]:
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
    return prepared


def hat_truss_checks(component_data: dict[str, object]) -> dict[str, object]:
    hat = component_data["hat_truss"]
    transfer_80 = float(hat["net_outward_transfer_history_kip"]["80"])
    max_outrigger_dcr_80 = max(float(value) for value in hat["outtrigger_dcr_at_80_min"].values())
    calibrated_capacity = transfer_80 / max_outrigger_dcr_80
    connections = hat["connections_at_80_min"]
    connection_rows = []
    for row in connections:
        ultimate_dcr = float(row["demand_kip"]) / float(row["ultimate_kip"])
        yield_dcr = float(row["demand_kip"]) / float(row["yield_kip"])
        connection_rows.append({**row, "ultimate_dcr": ultimate_dcr, "yield_dcr": yield_dcr})
    capacity_cases = {
        "nist_calibrated_capacity": calibrated_capacity,
        "demonstrated_80min_transfer": transfer_80,
        "75pct_calibrated_sensitivity": 0.75 * calibrated_capacity,
        "50pct_calibrated_sensitivity": 0.50 * calibrated_capacity,
        "no_hat_truss_sensitivity": 0.0,
    }
    history_rows = []
    for time in TIMES:
        required = float(hat["net_outward_transfer_history_kip"][str(time)])
        for name, capacity in capacity_cases.items():
            carried = min(required, capacity)
            history_rows.append(
                {
                    "time_min": time,
                    "capacity_case": name,
                    "capacity_kip": capacity,
                    "required_transfer_kip": required,
                    "carried_transfer_kip": carried,
                    "unmet_transfer_kip": required - carried,
                    "utilization": required / capacity if capacity > 0.0 else None,
                }
            )
    return {
        "demonstrated_transfer_at_80_min_kip": transfer_80,
        "controlling_outrigger_at_80_min": "E",
        "controlling_outrigger_dcr_at_80_min": max_outrigger_dcr_80,
        "nist_calibrated_aggregate_capacity_kip": calibrated_capacity,
        "reserve_above_80min_transfer_kip": calibrated_capacity - transfer_80,
        "reserve_above_80min_transfer_fraction": calibrated_capacity / transfer_80 - 1.0,
        "maximum_connection_ultimate_dcr_at_80_min": max(row["ultimate_dcr"] for row in connection_rows),
        "controlling_connection_ids": [
            row["id"]
            for row in connection_rows
            if math.isclose(
                row["ultimate_dcr"],
                max(item["ultimate_dcr"] for item in connection_rows),
                rel_tol=1e-9,
            )
        ],
        "connection_checks": connection_rows,
        "capacity_cases_kip": capacity_cases,
        "history": history_rows,
    }


def core_path_with_hat_limits(
    component_data: dict[str, object],
    transfer: dict[str, object],
    prior_b: dict[str, object],
    parameters: dict[str, object],
    hat_checks: dict[str, object],
) -> list[dict[str, object]]:
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }
    fields = {seed: v8f.smooth_score(coords, seed) for seed in SEEDS}
    prepared = prepare_core_inputs(transfer, prior_b)
    fy_params = transfer["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = transfer["steel_temperature_model"]["young_modulus_parameters"]
    thermal = transfer["fire_case_b"]["core_column_temperature_ranges_c"]
    official_history = transfer["nist_global_core_loads_floor_98_kip"]["case_b_time_history"]
    required_history = component_data["hat_truss"]["net_outward_transfer_history_kip"]
    rows: list[dict[str, object]] = []
    residuals = {"moderate": 1.0, "light": 1.0}
    for time_index, time in enumerate(TIMES):
        official_demand = float(official_history[str(time)])
        required_transfer = float(required_history[str(time)])
        for capacity_name, capacity in hat_checks["capacity_cases_kip"].items():
            unmet = max(0.0, required_transfer - float(capacity))
            adjusted_demand = official_demand + unmet
            for gamma in GAMMAS:
                for scheme in SCHEMES:
                    failed = 0
                    first_failed_floors: list[int] = []
                    for seed in SEEDS:
                        state = v8f.simulate_path(
                            adjusted_demand,
                            fields[seed],
                            gamma,
                            time_index,
                            prepared,
                            thermal,
                            coords,
                            "linear_to_5pct_at_1000c",
                            scheme,
                            1.0,
                            residuals,
                            fy_params,
                            e_params,
                        )
                        if not state["equilibrium_all_floors"]:
                            failed += 1
                            first_failed_floors.append(int(state["first_failed_floor"]))
                    rows.append(
                        {
                            "time_min": time,
                            "gamma": gamma,
                            "core_redistribution_rule": scheme,
                            "hat_capacity_case": capacity_name,
                            "hat_capacity_kip": capacity,
                            "required_hat_transfer_kip": required_transfer,
                            "unmet_hat_transfer_added_to_core_kip": unmet,
                            "adjusted_core_demand_kip": adjusted_demand,
                            "field_count": len(SEEDS),
                            "system_no_equilibrium_fraction": failed / len(SEEDS),
                            "median_first_failed_floor": statistics.median(first_failed_floors)
                            if first_failed_floors
                            else None,
                        }
                    )
    return rows


def pct(value: float) -> str:
    return f"{100.0 * value:.1f} %".replace(".", ",")


def render_summary(
    hat_checks: dict[str, object], seat_rows: list[dict[str, object]], core_rows: list[dict[str, object]]
) -> None:
    def font(size: int, bold: bool = False):
        path = "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            return ImageFont.load_default()

    image = Image.new("RGB", (1900, 1080), "white")
    draw = ImageDraw.Draw(image)
    navy = (24, 34, 56)
    blue = (47, 99, 160)
    amber = (220, 142, 46)
    red = (184, 58, 50)
    gray = (105, 112, 123)
    draw.text((950, 45), "WTC 1 - V8G : chemins de transfert bornes par les composants", anchor="ma", font=font(40, True), fill=navy)
    draw.text((950, 100), "Chapeau structurel et attaches de plancher analyses separement", anchor="ma", font=font(25), fill=gray)

    # Hat-truss load and calibrated capacity.
    x0, y0, w, h = 110, 225, 760, 430
    draw.text((x0 + w / 2, 170), "Transfert noyau -> facades", anchor="ma", font=font(30, True), fill=navy)
    capacity = float(hat_checks["nist_calibrated_aggregate_capacity_kip"])
    history = [
        row for row in hat_checks["history"] if row["capacity_case"] == "nist_calibrated_capacity"
    ]
    max_y = 7600.0
    points = []
    for index, row in enumerate(history):
        x = x0 + index * w / (len(history) - 1)
        y = y0 + h - float(row["required_transfer_kip"]) / max_y * h
        points.append((x, y))
        draw.line((x, y0, x, y0 + h), fill=(230, 233, 238), width=1)
        draw.text((x, y0 + h + 28), str(row["time_min"]), anchor="ma", font=font(21), fill=navy)
    cap_y = y0 + h - capacity / max_y * h
    draw.line((x0, cap_y, x0 + w, cap_y), fill=red, width=5)
    draw.text((x0 + 8, cap_y - 15), f"capacite calibree {capacity:.0f} kip", anchor="la", font=font(21, True), fill=red)
    draw.line(points, fill=blue, width=6)
    for (x, y), row in zip(points, history):
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=blue)
        draw.text((x, y - 28), f"{float(row['required_transfer_kip']):.0f}", anchor="ma", font=font(18, True), fill=blue)
    draw.text((x0 + w / 2, y0 + h + 67), "minutes apres impact", anchor="ma", font=font(21), fill=gray)
    draw.text((x0, y0 - 16), "kip", anchor="ls", font=font(20), fill=gray)

    # Seat-risk bars at 100 min, gamma=1, service load.
    x1, y1, bw = 1040, 235, 690
    draw.text((x1 + bw / 2, 170), "Attaches sous charge de service (16 kip)", anchor="ma", font=font(30, True), fill=navy)
    selected = {
        (row["floor"], row["seat_side"]): row
        for row in seat_rows
        if row["time_min"] == 100 and row["gamma"] == 1.0 and row["load_factor"] == 1.0
    }
    for index, floor in enumerate(FLOORS):
        y = y1 + index * 68
        draw.text((x1 - 20, y + 18), str(floor), anchor="rm", font=font(21, True), fill=navy)
        for side, color, offset in [("interior", blue, 0), ("exterior", amber, 25)]:
            value = float(selected[(floor, side)]["capacity_below_demand_fraction"])
            draw.rectangle((x1, y + offset, x1 + bw, y + offset + 16), fill=(235, 237, 241))
            draw.rectangle((x1, y + offset, x1 + bw * value, y + offset + 16), fill=color)
            draw.text((x1 + bw + 12, y + offset + 8), f"{100*value:.1f}%", anchor="lm", font=font(17), fill=navy)
    draw.rectangle((x1, y1 + 6 * 68 + 12, x1 + 22, y1 + 6 * 68 + 30), fill=blue)
    draw.text((x1 + 32, y1 + 6 * 68 + 21), "interieures", anchor="lm", font=font(19), fill=navy)
    draw.rectangle((x1 + 190, y1 + 6 * 68 + 12, x1 + 212, y1 + 6 * 68 + 30), fill=amber)
    draw.text((x1 + 222, y1 + 6 * 68 + 21), "exterieures", anchor="lm", font=font(19), fill=navy)

    # Core sensitivity summary.
    draw.line((90, 760, 1810, 760), fill=(220, 224, 231), width=2)
    draw.text((950, 815), "Effet conditionnel sur le reseau du noyau a 100 min (gamma=1)", anchor="ma", font=font(29, True), fill=navy)
    cases = [
        ("nist_calibrated_capacity", "capacite calibree"),
        ("75pct_calibrated_sensitivity", "75 %"),
        ("50pct_calibrated_sensitivity", "50 %"),
        ("no_hat_truss_sensitivity", "sans chapeau"),
    ]
    colors = [blue, (71, 137, 116), amber, red]
    for index, ((case, label), color) in enumerate(zip(cases, colors)):
        row = next(
            item
            for item in core_rows
            if item["time_min"] == 100
            and item["gamma"] == 1.0
            and item["core_redistribution_rule"] == "local_four"
            and item["hat_capacity_case"] == case
        )
        x = 170 + index * 420
        value = float(row["system_no_equilibrium_fraction"])
        draw.text((x + 150, 865), label, anchor="ma", font=font(21, True), fill=navy)
        draw.rectangle((x, 905, x + 300, 950), fill=(235, 237, 241))
        draw.rectangle((x, 905, x + 300 * value, 950), fill=color)
        draw.text((x + 150, 927), f"{100*value:.1f}%", anchor="mm", font=font(22, True), fill="white" if value > 0.35 else navy)
    draw.text((950, 1025), "Fractions de champs synthetiques sans equilibre : sensibilite du modele, pas probabilites reelles.", anchor="ma", font=font(22), fill=gray)
    image.save(OUT_PNG)


def main() -> None:
    components = json.loads(COMPONENTS.read_text(encoding="utf-8"))
    transfer = json.loads(TRANSFER.read_text(encoding="utf-8"))
    prior_b = json.loads(V8B_RESULT.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }

    hat_checks = hat_truss_checks(components)
    seats = seat_ensemble(components, transfer, coords)
    core = core_path_with_hat_limits(components, transfer, prior_b, parameters, hat_checks)
    payload = {
        "model": "WTC1_V8G_COMPONENT_BOUNDED_TRANSFER",
        "version": "8.6.0",
        "facts_transferred": {
            "seat_capacities": "NIST NCSTAR 1-6 Tables 4-2 and 4-3",
            "normal_seat_load": "approximately 16 kip for paired trusses at 80 psf service gravity load",
            "hat_transfer": "NIST NCSTAR 1-6D Tables 4-23, 4-24, and 5-3",
            "hat_member_checks": "NIST NCSTAR 1-6D Tables 4-27 and 4-29",
        },
        "model_assumptions": {
            "hat_capacity_calibration": "6748 kip transfer divided by controlling outrigger E DCR 0.97 at 80 min; assumes linear scaling of that response path",
            "degraded_hat_cases": "75%, 50%, and absent cases are sensitivities, not observations",
            "unmet_transfer": "any transfer above the imposed hat capacity is added back to total core compression",
            "seat_sampling": "each synthetic floor-temperature sample is crossed with every NIST seat type because the actual seat-type/temperature map is unavailable",
            "core_redistribution": "V8F local-four, local-eight, or global-capacity rule remains inside the core and is not yet component-bounded",
            "fractions_are_probabilities": False,
        },
        "hat_truss": hat_checks,
        "floor_seats": seats,
        "conditional_core_path": core,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    at_100 = [
        row for row in seats if row["time_min"] == 100 and row["gamma"] == 1.0 and row["load_factor"] == 1.0
    ]
    seat_lookup = {(row["floor"], row["seat_side"]): row for row in at_100}
    md = [
        "# WTC 1 - V8G : transferts bornes par les composants",
        "",
        "## Resultat principal",
        "",
        f"Le transfert maximal de noyau vers les facades publie par NIST est de **{hat_checks['demonstrated_transfer_at_80_min_kip']:.0f} kip** a 80 min. Le composant qui controle le chemin publie est l'outrigger E, avec un DCR de **{hat_checks['controlling_outrigger_dcr_at_80_min']:.2f}**. Une extrapolation lineaire donne une capacite globale d'environ **{hat_checks['nist_calibrated_aggregate_capacity_kip']:.0f} kip**, soit seulement **{100*hat_checks['reserve_above_80min_transfer_fraction']:.1f} %** de marge au-dessus de la demande a 80 min.",
        "",
        f"La connexion la plus sollicitee de la Table 4-29 atteint **{hat_checks['maximum_connection_ultimate_dcr_at_80_min']:.3f}** de sa capacite ultime. Dans les verifications publiees, ce sont donc les diagonales/outtriggers, et non les connexions listees, qui bornent le transfert.",
        "",
        "Cette coherence ne constitue pas une validation independante de la reponse globale NIST : la demande de 6 748 kip et le DCR de 0,97 proviennent du meme modele officiel. Elle montre toutefois que la charge transferee n'est pas superieure aux capacites de composants que NIST a publiees.",
        "",
        "## Attaches de plancher a 100 min",
        "",
        "Fraction des combinaisons *temperature synthetique x type d'attache NIST* dont la capacite verticale devient inferieure a la charge normale de 16 kip. Ce ne sont ni des comptes d'attaches reelles rompues, ni des probabilites.",
        "",
        "| Niveau | attaches interieures | attaches exterieures | plage thermique NIST |",
        "|---:|---:|---:|---:|",
    ]
    for floor in FLOORS:
        interior = seat_lookup[(floor, "interior")]
        exterior = seat_lookup[(floor, "exterior")]
        md.append(
            f"| {floor} | {pct(float(interior['capacity_below_demand_fraction']))} | {pct(float(exterior['capacity_below_demand_fraction']))} | {interior['temperature_min_c']:.0f}-{interior['temperature_max_c']:.0f} deg C |"
        )
    md.extend(
        [
            "",
            "Les attaches interieures restent generalement plus fortes verticalement. Aux temperatures voisines de 900 deg C, plusieurs types d'attaches exterieures tombent a 11-17 kip, donc autour ou sous la charge normale de 16 kip. Cela rend des deconnexions locales plausibles dans les zones les plus chaudes sans qu'une surcharge dynamique soit necessaire. La carte thermique exacte des attaches reste inconnue.",
            "",
            "## Sensibilite du chemin du noyau a 100 min",
            "",
            "Les valeurs ci-dessous reprennent le reseau V8F avec gamma=1, aucun affaiblissement invente des dommages moderate/light et aucune amplification de transfert. Seule la capacite du chapeau structurel change.",
            "",
            "| Capacite du chapeau | demande noyau ajustee | 4 voisines | 8 voisines | redistribution globale |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    case_labels = {
        "nist_calibrated_capacity": "capacite calibree NIST",
        "demonstrated_80min_transfer": "transfert demontre a 80 min",
        "75pct_calibrated_sensitivity": "75 % de la capacite calibree (hypothese)",
        "50pct_calibrated_sensitivity": "50 % (hypothese)",
        "no_hat_truss_sensitivity": "aucun transfert (borne)",
    }
    for case, label in case_labels.items():
        rows = [
            row for row in core if row["time_min"] == 100 and row["gamma"] == 1.0 and row["hat_capacity_case"] == case
        ]
        by_scheme = {row["core_redistribution_rule"]: row for row in rows}
        md.append(
            f"| {label} | {rows[0]['adjusted_core_demand_kip']:.0f} kip | {pct(by_scheme['local_four']['system_no_equilibrium_fraction'])} | {pct(by_scheme['local_eight']['system_no_equilibrium_fraction'])} | {pct(by_scheme['global_capacity']['system_no_equilibrium_fraction'])} |"
        )
    md.extend(
        [
            "",
            "## Faits, hypotheses et incertitudes",
            "",
            "### Faits directement transcrits",
            "",
            "- NIST donne les capacites verticales des attaches en fonction de la temperature et une charge normale d'environ 16 kip par paire de poutrelles.",
            "- Dans la reponse globale Case B, le noyau cede environ 6 748 kip aux facades a 80 min par le chapeau structurel; l'outrigger E atteint un DCR de 0,97.",
            "- Les charges totales aux niveaux 98 et 105 different de seulement 35 kip a 80 min, ce qui confirme que le transfert axial principal s'effectue au sommet plutot que directement par les planchers 94-99.",
            "",
            "### Hypotheses de V8G",
            "",
            "- La capacite agregee de 6 957 kip suppose une mise a l'echelle lineaire de la demande de l'outrigger E.",
            "- Les cas a 75 %, 50 % et sans chapeau ne sont pas des dommages observes; ils bornent la sensibilite.",
            "- Faute de carte attache-par-attache, les temperatures synthetiques sont croisees avec tous les types publies.",
            "- La redistribution entre colonnes du noyau reste celle de V8F. Les sections et connexions des poutres interieures ne sont pas encore suffisamment transcrites pour la remplacer proprement.",
            "",
            "### Contradictions ou zones non resolues",
            "",
            "- Aucune contradiction numerique interne n'apparait entre le transfert global publie et les capacites publiees du chapeau, mais la marge calculee sur l'outrigger E est faible et depend d'une verification NIST post-traitee.",
            "- Le modele global NIST ne representait pas explicitement toutes les ruptures de raccords du chapeau; celles-ci ont ete verifiees separement. Cette separation limite l'independance de la sequence calculee.",
            "- Les planchers du modele global etaient des plaques calibrees en rigidite membranaire, avec une rigidite de flexion non reproduite exactement. Les sous-modeles de plancher compensent partiellement cette limite, sans constituer un modele complet unique.",
            "- V8G ne teste aucune hypothese d'explosif. Elle montre seulement que le chemin de charge officiel publie est mecaniquement admissible au niveau des composants transcrits, avec une faible marge locale au composant critique.",
            "",
        ]
    )
    OUT_REPORT.write_text("\n".join(md), encoding="utf-8")
    render_summary(hat_checks, seats, core)
    print(
        json.dumps(
            {
                "json": str(OUT_JSON),
                "report": str(OUT_REPORT),
                "plot": str(OUT_PNG),
                "seat_rows": len(seats),
                "core_rows": len(core),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
