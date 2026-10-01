"""WTC 1 V8A — audited NIST impact/fire transfer and core axial envelope.

This is not a crash solver and not a collapse proof.  It transfers the three
published NIST impact cases onto the 47 transcribed WTC 1 core-column schedules,
then evaluates nominal axial-yield envelopes with the NIST steel reduction curve.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V8_DIR = ROOT / "wtc1_simulation_v8"
INPUT_PATH = V8_DIR / "data" / "nist_wtc1_transfer.json"
SCHEDULE_PATH = ROOT / "wtc1_3d_v4" / "data" / "core_sections_impact_zone.json"
OUTPUT_DIR = V8_DIR / "output"

KIP_TO_N = 4_448.2216152605
MPH_TO_M_S = 0.44704
STEEL_DENSITY_LB_IN3 = 490.0 / 1728.0

BAND_LABELS = {
    "95-92": "bande 95–92",
    "98-95": "bande 98–95",
    "101-98": "bande 101–98",
}


def floor_band(floor: int) -> str:
    if floor <= 94:
        return "95-92"
    if floor <= 97:
        return "98-95"
    return "101-98"


def wf_weight_lb_ft(shape: str) -> float:
    match = re.fullmatch(r"(?:12|14)WF([0-9.]+)", shape)
    if not match:
        raise ValueError(f"Désignation WF non reconnue: {shape}")
    return float(match.group(1))


def gross_area_in2(segment: dict[str, object]) -> float:
    if segment["kind"] == "WF":
        return wf_weight_lb_ft(str(segment["shape"])) / (STEEL_DENSITY_LB_IN3 * 12.0)
    if segment["kind"] == "BOX":
        return float(segment["gross_area_in2"])
    raise ValueError(f"Type de section inconnu: {segment['kind']}")


def yield_ratio(temp_c: float, params: dict[str, float]) -> float:
    a2 = float(params["A2"])
    exponent = -0.5 * (
        (temp_c / float(params["s1_c"])) ** float(params["m1"])
        + (temp_c / float(params["s2_c"])) ** float(params["m2"])
    )
    return (1.0 - a2) * math.exp(exponent) + a2


def young_modulus_gpa(temp_c: float, params: dict[str, float]) -> float:
    if not 0.0 <= temp_c <= 600.0:
        raise ValueError("La formule NIST E(T) transcrite n'est valide que de 0 à 600 °C.")
    return (
        float(params["e0"])
        + float(params["e1"]) * temp_c
        + float(params["e2"]) * temp_c**2
        + float(params["e3"]) * temp_c**3
    )


def damage_on_floor(case_rows: list[dict[str, object]], floor: int) -> dict[int, str]:
    return {
        int(row["column"]): str(row["state"])
        for row in case_rows
        if floor in [int(value) for value in row["floors"]]
    }


def threshold_temperature(nominal_capacity_kip: float, demand_kip: float, params: dict[str, float]) -> float | None:
    if nominal_capacity_kip <= demand_kip:
        return 20.0
    if nominal_capacity_kip * yield_ratio(1_200.0, params) > demand_kip:
        return None
    low, high = 20.0, 1_200.0
    for _ in range(100):
        mid = 0.5 * (low + high)
        if nominal_capacity_kip * yield_ratio(mid, params) > demand_kip:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def hot_fraction_to_demand(
    nominal_capacity_kip: float,
    demand_kip: float,
    t_min_c: float,
    t_max_c: float,
    params: dict[str, float],
) -> dict[str, object]:
    cap_cool = nominal_capacity_kip * yield_ratio(t_min_c, params)
    cap_hot = nominal_capacity_kip * yield_ratio(t_max_c, params)
    if cap_cool <= demand_kip:
        return {"status": "demand_reached_even_at_floor_minimum", "fraction": 0.0}
    if cap_hot > demand_kip:
        return {"status": "demand_not_reached_even_if_uniform_maximum", "fraction": None}
    fraction = (cap_cool - demand_kip) / (cap_cool - cap_hot)
    return {"status": "interpolated_two_temperature_envelope", "fraction": fraction}


def calculate() -> dict[str, object]:
    inputs = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    fy_params = inputs["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = inputs["steel_temperature_model"]["young_modulus_parameters"]
    demand = float(inputs["nist_global_core_loads_floor_98_kip"]["100_min_case_b"])

    section_rows: dict[str, dict[int, dict[str, float | str]]] = {}
    for band in BAND_LABELS:
        section_rows[band] = {}
        for column in schedule["columns"]:
            segment = column["segments"][band]
            area = gross_area_in2(segment)
            fy_ksi = float(segment["fy_ksi"])
            section_rows[band][int(column["id"])] = {
                "area_in2": area,
                "fy_ksi": fy_ksi,
                "py_kip": area * fy_ksi,
                "designation": str(segment.get("shape", f"BOX-{segment.get('column_type')}")),
            }

    aircraft_results: dict[str, object] = {}
    base_mass = float(inputs["aircraft"]["base_total_mass_kg"])
    for case_name, case in inputs["aircraft"]["cases"].items():
        mass = base_mass * float(case["mass_factor"])
        speed = float(case["speed_mph"]) * MPH_TO_M_S
        aircraft_results[case_name] = {
            "mass_kg": mass,
            "speed_m_s": speed,
            "kinetic_energy_gj": 0.5 * mass * speed**2 / 1e9,
            "momentum_MN_s": mass * speed / 1e6,
            "source_parameters": case,
        }

    cases: dict[str, object] = {}
    removal_states = {"severed", "heavy"}
    for case_name, damage_rows in inputs["core_damage"].items():
        if case_name == "final_case_b_rule":
            continue
        floor_results: dict[str, object] = {}
        for floor in range(93, 100):
            band = floor_band(floor)
            states = damage_on_floor(damage_rows, floor)
            removed = sorted(column for column, state in states.items() if state in removal_states)
            nominal_all = sum(float(row["py_kip"]) for row in section_rows[band].values())
            removed_py = sum(float(section_rows[band][column]["py_kip"]) for column in removed)
            floor_results[str(floor)] = {
                "schedule_band": band,
                "reported_damage_states": {str(k): v for k, v in sorted(states.items())},
                "removed_if_heavy_treated_as_severed": removed,
                "remaining_column_count": 47 - len(removed),
                "nominal_all_core_py_kip": nominal_all,
                "removed_nominal_py_kip": removed_py,
                "remaining_nominal_py_kip": nominal_all - removed_py,
                "remaining_nominal_py_MN": (nominal_all - removed_py) * KIP_TO_N / 1e6,
            }
        cases[case_name] = {"floor_results": floor_results}

    thermal_ranges = inputs["fire_case_b"]["core_column_temperature_ranges_c"]
    severe_floors = cases["more_severe"]["floor_results"]
    thermal_100: dict[str, object] = {}
    for floor_text, ranges in thermal_ranges.items():
        floor = int(floor_text)
        t_min, t_max = [float(value) for value in ranges[-1]]
        t_mid = 0.5 * (t_min + t_max)
        nominal = float(severe_floors[floor_text]["remaining_nominal_py_kip"])
        threshold = threshold_temperature(nominal, demand, fy_params)
        fraction = hot_fraction_to_demand(nominal, demand, t_min, t_max, fy_params)
        thermal_100[floor_text] = {
            "temperature_min_c": t_min,
            "temperature_max_c": t_max,
            "temperature_midpoint_c_not_median": t_mid,
            "capacity_uniform_min_kip": nominal * yield_ratio(t_min, fy_params),
            "capacity_uniform_midpoint_kip": nominal * yield_ratio(t_mid, fy_params),
            "capacity_uniform_max_kip": nominal * yield_ratio(t_max, fy_params),
            "capacity_uniform_min_MN": nominal * yield_ratio(t_min, fy_params) * KIP_TO_N / 1e6,
            "capacity_uniform_midpoint_MN": nominal * yield_ratio(t_mid, fy_params) * KIP_TO_N / 1e6,
            "capacity_uniform_max_MN": nominal * yield_ratio(t_max, fy_params) * KIP_TO_N / 1e6,
            "uniform_temperature_to_equal_floor98_core_demand_c": threshold,
            "two_temperature_hot_fraction_to_equal_floor98_core_demand": fraction,
        }

    material_curve = []
    for temp in range(20, 1_001, 20):
        row: dict[str, object] = {
            "temperature_c": temp,
            "yield_ratio": yield_ratio(float(temp), fy_params),
        }
        if temp <= 600:
            modulus = young_modulus_gpa(float(temp), e_params)
            row["young_modulus_gpa"] = modulus
            row["young_modulus_ratio_to_20c"] = modulus / young_modulus_gpa(20.0, e_params)
        material_curve.append(row)

    return {
        "model": "WTC1_V8A_NIST_TRANSFER_CORE_ENVELOPE",
        "version": "8.0.0",
        "inputs": {
            "nist_transfer": str(INPUT_PATH),
            "core_schedule": str(SCHEDULE_PATH),
        },
        "aircraft_cases": aircraft_results,
        "impact_damage_cases": cases,
        "case_b_thermal_envelopes_at_100_min": thermal_100,
        "material_curve": material_curve,
        "reference_demand": {
            "value_kip": demand,
            "value_MN": demand * KIP_TO_N / 1e6,
            "scope": "NIST global WTC 1 model, total core load at Floor 98, 100 min, Case B",
            "warning": "Used on other floors only as a scale reference; it is not a floor-by-floor load field.",
        },
        "limitations": [
            "A×Fy(T) is a nominal gross axial-yield envelope, not a buckling resistance.",
            "Heavy damage is treated as removed only to reproduce the conservative final Case B transfer rule.",
            "The reported NIST temperature extrema are not spatial averages or percentiles.",
            "The two-temperature hot-fraction calculation assumes damage is proportional to nominal column capacity and ignores load concentration.",
            "No perimeter wall, floor diaphragm, hat truss, connection failure, thermal bowing, creep, or geometric imperfection is solved in V8A.",
            "The 47-column schedule is a manual transcription and still needs an independent second reading.",
        ],
    }


def fonts():
    from PIL import ImageFont

    try:
        return {
            "title": ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 31),
            "panel": ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 24),
            "regular": ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 19),
            "small": ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16),
        }
    except OSError:
        default = ImageFont.load_default()
        return {"title": default, "panel": default, "regular": default, "small": default}


def write_plot(result: dict[str, object]) -> Path:
    from PIL import Image, ImageDraw

    f = fonts()
    width, height = 2750, 1170
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text(
        (width // 2, 48),
        "WTC 1 — V8A : transfert NIST impact → feu → enveloppe axiale du noyau",
        fill=(20, 20, 20),
        font=f["title"],
        anchor="mm",
    )
    boxes = [(90, 155, 820, 850), (1010, 155, 1740, 850), (1930, 155, 2660, 850)]

    def xy(box, x, y, xmin, xmax, ymin, ymax):
        x0, y0, x1, y1 = box
        return (
            int(x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)),
            int(y1 - (y - ymin) / (ymax - ymin) * (y1 - y0)),
        )

    def axes(box, title, xlabel, ylabel, xmin, xmax, ymin, ymax, xticks, yticks):
        draw.rectangle(box, outline=(40, 40, 40), width=2)
        draw.text(((box[0] + box[2]) // 2, box[1] - 43), title, fill=(20, 20, 20), font=f["panel"], anchor="mm")
        draw.text(((box[0] + box[2]) // 2, box[3] + 55), xlabel, fill=(35, 35, 35), font=f["regular"], anchor="mm")
        draw.text((box[0] + 10, box[1] + 10), ylabel, fill=(70, 70, 70), font=f["small"], anchor="la")
        for tick in xticks:
            p0 = xy(box, tick, ymin, xmin, xmax, ymin, ymax)
            p1 = xy(box, tick, ymax, xmin, xmax, ymin, ymax)
            draw.line((p0, p1), fill=(228, 228, 228), width=1)
            draw.text((p0[0], box[3] + 9), str(tick), fill=(45, 45, 45), font=f["small"], anchor="ma")
        for tick in yticks:
            p0 = xy(box, xmin, tick, xmin, xmax, ymin, ymax)
            p1 = xy(box, xmax, tick, xmin, xmax, ymin, ymax)
            draw.line((p0, p1), fill=(228, 228, 228), width=1)
            draw.text((box[0] - 9, p0[1]), str(tick), fill=(45, 45, 45), font=f["small"], anchor="rm")

    # Panel A: impact energy.
    box = boxes[0]
    axes(box, "A. Trois cas d’impact NIST", "Cas", "Énergie cinétique (GJ)", 0, 4, 0, 3.5, [], [0, 1, 2, 3])
    names = [("less_severe", "moins sévère"), ("base", "base"), ("more_severe", "plus sévère")]
    colors = [(63, 126, 188), (238, 142, 43), (190, 55, 57)]
    for i, ((key, label), color) in enumerate(zip(names, colors), start=1):
        energy = float(result["aircraft_cases"][key]["kinetic_energy_gj"])
        left = xy(box, i - 0.31, 0, 0, 4, 0, 3.5)[0]
        right = xy(box, i + 0.31, 0, 0, 4, 0, 3.5)[0]
        top = xy(box, i, energy, 0, 4, 0, 3.5)[1]
        draw.rectangle((left, top, right, box[3]), fill=color)
        draw.text(((left + right) // 2, top - 8), f"{energy:.2f}", fill=(20, 20, 20), font=f["regular"], anchor="ms")
        draw.text(((left + right) // 2, box[3] + 28), label, fill=(25, 25, 25), font=f["small"], anchor="ma")

    # Panel B: nominal capacity remaining by floor and impact case.
    box = boxes[1]
    axes(box, "B. Noyau après dommage d’impact", "Étage", "A·Fy restant (MN)", 92.5, 99.5, 0, 600, [93, 94, 95, 96, 97, 98, 99], [0, 150, 300, 450, 600])
    for (key, _), color in zip(names, colors):
        points = []
        for floor in range(93, 100):
            value = float(result["impact_damage_cases"][key]["floor_results"][str(floor)]["remaining_nominal_py_MN"])
            points.append(xy(box, floor, value, 92.5, 99.5, 0, 600))
        draw.line(points, fill=color, width=5)
        for point in points:
            draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=color)
    demand_mn = float(result["reference_demand"]["value_MN"])
    y_demand = xy(box, 93, demand_mn, 92.5, 99.5, 0, 600)[1]
    for x in range(box[0], box[2], 20):
        draw.line((x, y_demand, min(x + 11, box[2]), y_demand), fill=(90, 55, 120), width=4)
    draw.text((box[0] + 15, y_demand - 10), "127 MN : charge noyau NIST au niveau 98, 100 min", fill=(90, 55, 120), font=f["small"], anchor="ls")

    # Panel C: 100 min uniform-temperature bounds for final Case B.
    box = boxes[2]
    axes(box, "C. Feu Case B à 100 min", "Étage", "Capacité axiale (MN)", 92.5, 99.5, 0, 600, [93, 94, 95, 96, 97, 98, 99], [0, 150, 300, 450, 600])
    styles = [
        ("capacity_uniform_min_MN", (48, 142, 78), "T minimale uniforme"),
        ("capacity_uniform_midpoint_MN", (224, 139, 33), "milieu min–max uniforme"),
        ("capacity_uniform_max_MN", (174, 45, 50), "T maximale uniforme"),
    ]
    for field, color, _ in styles:
        points = [
            xy(box, floor, float(result["case_b_thermal_envelopes_at_100_min"][str(floor)][field]), 92.5, 99.5, 0, 600)
            for floor in range(93, 100)
        ]
        draw.line(points, fill=color, width=5)
        for point in points:
            draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=color)
    y_demand = xy(box, 93, demand_mn, 92.5, 99.5, 0, 600)[1]
    for x in range(box[0], box[2], 20):
        draw.line((x, y_demand, min(x + 11, box[2]), y_demand), fill=(90, 55, 120), width=4)

    legend_y = 930
    draw.text((130, legend_y), "Légende", fill=(20, 20, 20), font=f["panel"])
    legend_items = [
        ((63, 126, 188), "impact moins sévère"),
        ((238, 142, 43), "impact de base"),
        ((190, 55, 57), "impact plus sévère / Case B"),
        ((48, 142, 78), "température minimale appliquée uniformément"),
        ((224, 139, 33), "milieu min–max appliqué uniformément (ce n’est pas une médiane)"),
        ((174, 45, 50), "température maximale appliquée uniformément"),
    ]
    x, y = 130, legend_y + 52
    for index, (color, label) in enumerate(legend_items):
        if index == 3:
            x, y = 1375, legend_y + 52
        draw.line((x, y + 8, x + 55, y + 8), fill=color, width=7)
        draw.text((x + 70, y), label, fill=(35, 35, 35), font=f["regular"])
        y += 42
    draw.text(
        (width // 2, 1135),
        "Les courbes thermiques sont des bornes artificielles construites avec les extrema NIST — pas des températures moyennes mesurées.",
        fill=(125, 35, 35),
        font=f["regular"],
        anchor="mm",
    )
    path = OUTPUT_DIR / "synthese_wtc1_v8a.png"
    img.save(path)
    return path


def format_fraction(entry: dict[str, object]) -> str:
    if entry["fraction"] is None:
        return "impossible même à Tmax uniforme"
    return f"{100.0 * float(entry['fraction']):.0f} %"


def write_report(result: dict[str, object]) -> Path:
    floors = result["impact_damage_cases"]["more_severe"]["floor_results"]
    thermal = result["case_b_thermal_envelopes_at_100_min"]
    base_energy = float(result["aircraft_cases"]["base"]["kinetic_energy_gj"])
    severe_energy = float(result["aircraft_cases"]["more_severe"]["kinetic_energy_gj"])
    demand_mn = float(result["reference_demand"]["value_MN"])
    floor98_nominal = float(floors["98"]["remaining_nominal_py_MN"])
    floor98_hot = float(thermal["98"]["capacity_uniform_max_MN"])
    floor95_nominal = float(floors["95"]["remaining_nominal_py_MN"])
    floor95_mid = float(thermal["95"]["capacity_uniform_midpoint_MN"])
    floor95_hot = float(thermal["95"]["capacity_uniform_max_MN"])

    rows = []
    for floor in range(93, 100):
        impact = floors[str(floor)]
        heat = thermal[str(floor)]
        removed = impact["removed_if_heavy_treated_as_severed"]
        tcrit = heat["uniform_temperature_to_equal_floor98_core_demand_c"]
        rows.append(
            "| {floor} | {removed} | {nominal:.0f} | {tmin:.0f}–{tmax:.0f} | {cool:.0f} | {mid:.0f} | {hot:.0f} | {tcrit} | {fraction} |".format(
                floor=floor,
                removed=", ".join(str(value) for value in removed) if removed else "—",
                nominal=float(impact["remaining_nominal_py_MN"]),
                tmin=float(heat["temperature_min_c"]),
                tmax=float(heat["temperature_max_c"]),
                cool=float(heat["capacity_uniform_min_MN"]),
                mid=float(heat["capacity_uniform_midpoint_MN"]),
                hot=float(heat["capacity_uniform_max_MN"]),
                tcrit=(f"{float(tcrit):.0f} °C" if tcrit is not None else "> 1 200 °C"),
                fraction=format_fraction(heat["two_temperature_hot_fraction_to_equal_floor98_core_demand"]),
            )
        )

    text = f"""# WTC 1 — V8A : transfert impact–feu NIST sur les 47 colonnes du noyau

## Résultat principal

La chaîne de données est maintenant explicite : les trois impacts NIST donnent **{float(result['aircraft_cases']['less_severe']['kinetic_energy_gj']):.2f} GJ**, **{base_energy:.2f} GJ** et **{severe_energy:.2f} GJ** d’énergie cinétique initiale. Le modèle final Case B ne reprend pas le cas de base : il reprend le cas d’impact **plus sévère**, puis traite comme absentes les colonnes qualifiées de sectionnées ou lourdement endommagées, étage par étage.

Cette opération ne suffit pas, à elle seule, à faire disparaître la capacité axiale brute du noyau. Au niveau 98, aucune des neuf colonnes Case B n’est supprimée et l’enveloppe nominale vaut encore **{floor98_nominal:.0f} MN**. Même si la température maximale NIST de cet étage à 100 min (**{float(thermal['98']['temperature_max_c']):.0f} °C**) était appliquée artificiellement aux 47 colonnes, l’enveloppe `A × Fy(T)` resterait **{floor98_hot:.0f} MN**, contre **{demand_mn:.0f} MN** de charge totale du noyau donnée par le modèle global NIST au niveau 98.

Au niveau 95, les neuf colonnes sélectionnées par Case B sont toutes retirées : l’enveloppe brute descend à **{floor95_nominal:.0f} MN**. L’application uniforme du milieu de la plage thermique NIST donnerait **{floor95_mid:.0f} MN**, tandis que l’application uniforme de son maximum donnerait seulement **{floor95_hot:.0f} MN**. Mais ces deux valeurs sont des constructions de sensibilité : NIST publie des extrema spatiaux, pas une température moyenne. On ne peut donc pas choisir la courbe rouge comme « résultat réel ».

La conclusion V8A est nette mais limitée : **les dommages d’impact NIST et leurs extrema thermiques peuvent produire localement des capacités axiales très faibles, mais les tableaux publiés ne suffisent pas à établir combien de colonnes se trouvent simultanément près de ces maxima ni quelle charge chacune porte**. L’initiation doit donc être testée par stabilité géométrique et redistribution noyau–planchers–façades, pas seulement par `A × Fy(T)`.

## Tableau de sensibilité Case B à 100 min

La ligne de comparaison de **{demand_mn:.0f} MN** est la charge NIST du noyau au niveau 98. Sur les autres étages, elle sert uniquement d’échelle : ce n’est pas un champ de charges étage par étage.

| Étage | Colonnes retirées sur cet étage | A·Fy restant (MN) | plage T noyau (°C) | capacité à Tmin uniforme (MN) | capacité au milieu uniforme (MN) | capacité à Tmax uniforme (MN) | T uniforme pour atteindre 127 MN | fraction « chaude » min/max pour atteindre 127 MN |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## Faits établis intégrés

- Conditions d’impact WTC 1 de base : 443 mph, 283 600 lb, 66 100 lb de carburant, trajectoire descendante de 10,6° et roulis de 25° aile gauche basse.
- Cas supplémentaires NIST : 414 mph / 95 % de la masse pour le cas moins sévère et 472 mph / 105 % de la masse pour le cas plus sévère, avec variations simultanées des déformations à rupture de l’avion et de la tour.
- Le cas structurel final B provient du dommage d’impact plus sévère et retire neuf identifiants de colonnes lorsqu’ils sont sectionnés ou lourdement endommagés.
- Les plages thermiques à 100 min proviennent des minima et maxima spatiaux des tableaux NIST pour les colonnes du noyau, les colonnes périphériques et les poutrelles de plancher.
- La réduction de limite d’élasticité suit l’équation 6-1 de NCSTAR 1-3D. Le module de Young transcrit suit l’équation 2-2 uniquement jusqu’à 600 °C.

## Hypothèses de V8A

- Les sections WF sont converties en aire brute à partir de leur poids nominal et d’une masse volumique de 490 lb/ft³; les trois caissons utilisent les dimensions de plaques déjà transcrites.
- Une colonne « heavy » est supprimée uniquement pour reproduire la règle conservatrice de transfert Case B; ce n’est pas une loi mécanique générale.
- Une suppression ne vaut que sur les étages indiqués par la carte NIST. Elle n’efface pas l’identifiant sur toute la hauteur de la tour.
- Les calculs « Tmin uniforme », « milieu uniforme » et « Tmax uniforme » sont des bornes de sensibilité. Le milieu min–max n’est ni une moyenne ni une médiane.
- La colonne « fraction chaude » mélange seulement deux températures et répartit la chaleur proportionnellement à la capacité nominale. Elle ne représente pas la carte spatiale NIST et ignore la concentration des charges.

## Archives locales : statut séparé

L’archive `Disaster and Failure Studies Repository` a été inspectée en lecture seule. Elle contient surtout des photographies et vidéos d’essais de feu, plus les visualisations officielles NIST des impacts, feux et réponses structurales. Aucun fichier tabulaire nouveau n’y a encore fourni de champ de température ou de charge directement exploitable. Les valeurs numériques V8A proviennent donc des rapports NIST primaires et des plans du WTC déjà transcrits; aucune affirmation éditoriale locale n’entre dans le calcul.

## Ce que V8A ne démontre pas

- `A × Fy(T)` ne décrit ni le flambement, ni la flexion thermique, ni le fluage, ni les imperfections initiales.
- Les façades, les planchers, leurs connexions et le hat truss ne sont pas encore couplés.
- L’impact n’est pas recalculé indépendamment : les trois cartes NIST sont les états initiaux testés.
- Aucune conclusion sur la propagation globale après l’amorce ne peut être tirée de cette seule enveloppe.

## Prochaine itération V8B

Construire le sous-modèle thermo-mécanique des niveaux 93–99 avec les 47 colonnes, des diaphragmes de plancher simplifiés et les retraits Case B localisés. Les cas thermiques seront au minimum : champ froid, champ médian explicitement synthétique, concentration chaude sur les colonnes de la trajectoire d’impact, et variantes d’isolant intact/retiré. Le critère sera une perte de stabilité sous charge imposée, pas seulement l’atteinte de la limite d’élasticité.

![Synthèse V8A](synthese_wtc1_v8a.png)
"""
    path = OUTPUT_DIR / "rapport_wtc1_v8a.md"
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = calculate()
    json_path = OUTPUT_DIR / "resultats_wtc1_v8a.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    plot_path = write_plot(result)
    report_path = write_report(result)
    print(json_path)
    print(plot_path)
    print(report_path)


if __name__ == "__main__":
    main()
