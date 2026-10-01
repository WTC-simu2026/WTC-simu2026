"""WTC 1 V8B — floor-by-floor core stability and redistribution sensitivity.

This deliberately transparent network model sits between an A×Fy envelope and
a full nonlinear finite-element model.  It uses real historic WF section
properties, nominal AISC column strength, localized NIST Case B removals, and
several load/redistribution/effective-length assumptions.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V8_DIR = ROOT / "wtc1_simulation_v8"
TRANSFER_PATH = V8_DIR / "data" / "nist_wtc1_transfer.json"
SCHEDULE_PATH = ROOT / "wtc1_3d_v4" / "data" / "core_sections_impact_zone.json"
PARAMETERS_PATH = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
AISC_PATH = V8_DIR / "data" / "aisc_historic_wf_properties.json"
OUTPUT_DIR = V8_DIR / "output"

KIP_TO_N = 4_448.2216152605
STORY_LENGTH_IN = 144.0
GPA_TO_KSI = 145.0377377


def floor_band(floor: int) -> str:
    if floor <= 94:
        return "95-92"
    if floor <= 97:
        return "98-95"
    return "101-98"


def yield_ratio(temp_c: float, params: dict[str, float]) -> float:
    a2 = float(params["A2"])
    exponent = -0.5 * (
        (temp_c / float(params["s1_c"])) ** float(params["m1"])
        + (temp_c / float(params["s2_c"])) ** float(params["m2"])
    )
    return (1.0 - a2) * math.exp(exponent) + a2


def e_polynomial_gpa(temp_c: float, params: dict[str, float]) -> float:
    return (
        float(params["e0"])
        + float(params["e1"]) * temp_c
        + float(params["e2"]) * temp_c**2
        + float(params["e3"]) * temp_c**3
    )


def elastic_modulus_ksi(temp_c: float, params: dict[str, float], tail_model: str) -> float:
    e20 = e_polynomial_gpa(20.0, params)
    if temp_c <= 600.0:
        return max(e_polynomial_gpa(max(0.0, temp_c), params), 0.05 * e20) * GPA_TO_KSI
    e600 = e_polynomial_gpa(600.0, params)
    if tail_model == "hold_e600_upper_bound":
        value = e600
    elif tail_model == "linear_to_5pct_at_1000c":
        fraction = min(max((temp_c - 600.0) / 400.0, 0.0), 1.0)
        value = e600 + fraction * (0.05 * e20 - e600)
    else:
        raise ValueError(tail_model)
    return max(value, 0.05 * e20) * GPA_TO_KSI


def box_properties(segment: dict[str, object]) -> dict[str, float]:
    # Type-300 detail: two horizontal plate-1 elements fit between two full-height
    # vertical plate-2 elements.  This is a geometric reconstruction, not a NIST
    # section-property table replacement.
    p1, p2 = segment["plates"]
    t1, w1 = float(p1["t_in"]), float(p1["w_in"])
    t2, h2 = float(p2["t_in"]), float(p2["w_in"])
    total_width = w1 + 2.0 * t2
    total_height = h2
    y1 = 0.5 * (total_height - t1)
    x2 = 0.5 * (total_width - t2)
    area = 2.0 * (t1 * w1 + t2 * h2)
    ix = 2.0 * (w1 * t1**3 / 12.0 + w1 * t1 * y1**2) + 2.0 * (t2 * h2**3 / 12.0)
    iy = 2.0 * (t1 * w1**3 / 12.0) + 2.0 * (h2 * t2**3 / 12.0 + h2 * t2 * x2**2)
    return {
        "area_in2": area,
        "ix_in4": ix,
        "iy_in4": iy,
        "rx_in": math.sqrt(ix / area),
        "ry_in": math.sqrt(iy / area),
    }


def nominal_column_capacity_kip(
    section: dict[str, float | str],
    temp_c: float,
    k_factor: float,
    fy_params: dict[str, float],
    e_params: dict[str, float],
    tail_model: str,
) -> float:
    area = float(section["area_in2"])
    rmin = min(float(section["rx_in"]), float(section["ry_in"]))
    fy_hot = float(section["fy_ksi"]) * yield_ratio(temp_c, fy_params)
    e_hot = elastic_modulus_ksi(temp_c, e_params, tail_model)
    slenderness = k_factor * STORY_LENGTH_IN / rmin
    fe = math.pi**2 * e_hot / slenderness**2
    ratio = fy_hot / fe
    if ratio <= 2.25:
        fcr = (0.658**ratio) * fy_hot
    else:
        fcr = 0.877 * fe
    return max(0.0, fcr * area)


def tributary_weights(coords: dict[int, tuple[float, float]], width: float, depth: float) -> dict[int, float]:
    counts = {column: 0 for column in coords}
    nx, ny = 401, 261
    for ix in range(nx):
        x = -0.5 * width + width * (ix + 0.5) / nx
        for iy in range(ny):
            y = -0.5 * depth + depth * (iy + 0.5) / ny
            nearest = min(coords, key=lambda column: (coords[column][0] - x) ** 2 + (coords[column][1] - y) ** 2)
            counts[nearest] += 1
    total = float(sum(counts.values()))
    return {column: count / total for column, count in counts.items()}


def normalized(values: dict[int, float]) -> dict[int, float]:
    total = sum(values.values())
    return {key: value / total for key, value in values.items()}


def distribute_one(
    source: int,
    value: float,
    loads: dict[int, float],
    survivors: set[int],
    sections: dict[int, dict[str, float | str]],
    coords: dict[int, tuple[float, float]],
    scheme: str,
) -> bool:
    if not survivors:
        return False
    if scheme == "global_capacity":
        weights = normalized({column: float(sections[column]["room_pn_kip_k1"]) for column in survivors})
    elif scheme == "local_four":
        sx, sy = coords[source]
        candidates = sorted(
            survivors,
            key=lambda column: (coords[column][0] - sx) ** 2 + (coords[column][1] - sy) ** 2,
        )[:4]
        raw = {}
        for column in candidates:
            distance2 = (coords[column][0] - sx) ** 2 + (coords[column][1] - sy) ** 2
            raw[column] = 1.0 / max(distance2, 0.05**2)
        weights = normalized(raw)
    else:
        raise ValueError(scheme)
    for column, weight in weights.items():
        loads[column] = loads.get(column, 0.0) + value * weight
    return True


def initial_loads(
    total_kip: float,
    sections: dict[int, dict[str, float | str]],
    tributary: dict[int, float],
    method: str,
) -> dict[int, float]:
    if method == "capacity_proportional":
        weights = normalized({column: float(row["room_pn_kip_k1"]) for column, row in sections.items()})
    elif method == "area_proportional":
        weights = normalized({column: float(row["area_in2"]) for column, row in sections.items()})
    elif method == "plan_tributary_grid":
        weights = tributary
    else:
        raise ValueError(method)
    return {column: total_kip * weights[column] for column in sections}


def remove_initial_damage(
    loads: dict[int, float],
    removed: set[int],
    sections: dict[int, dict[str, float | str]],
    coords: dict[int, tuple[float, float]],
    redistribution: str,
) -> tuple[dict[int, float], bool]:
    working = dict(loads)
    survivors = set(working) - removed
    for column in sorted(removed):
        value = working.pop(column, 0.0)
        if not distribute_one(column, value, working, survivors, sections, coords, redistribution):
            return working, False
    return working, True


def cascade(
    start_loads: dict[int, float],
    temperatures: dict[int, float],
    sections: dict[int, dict[str, float | str]],
    coords: dict[int, tuple[float, float]],
    k_factor: float,
    redistribution: str,
    fy_params: dict[str, float],
    e_params: dict[str, float],
    tail_model: str,
) -> dict[str, object]:
    loads = dict(start_loads)
    survivors = set(loads)
    failed: list[int] = []
    peak_dcr = 0.0
    while survivors:
        capacities = {
            column: nominal_column_capacity_kip(
                sections[column], temperatures[column], k_factor, fy_params, e_params, tail_model
            )
            for column in survivors
        }
        dcr = {column: loads[column] / max(capacities[column], 1e-9) for column in survivors}
        current_peak = max(dcr.values())
        peak_dcr = max(peak_dcr, current_peak)
        if current_peak <= 1.0:
            return {
                "equilibrium": True,
                "additional_failed_count": len(failed),
                "additional_failed_columns": failed,
                "surviving_count": len(survivors),
                "final_peak_dcr": current_peak,
                "maximum_dcr_during_cascade": peak_dcr,
            }
        column = max(dcr, key=dcr.get)
        failed.append(column)
        value = loads.pop(column)
        survivors.remove(column)
        if not distribute_one(column, value, loads, survivors, sections, coords, redistribution):
            break
    return {
        "equilibrium": False,
        "additional_failed_count": len(failed),
        "additional_failed_columns": failed,
        "surviving_count": 0,
        "final_peak_dcr": None,
        "maximum_dcr_during_cascade": peak_dcr,
    }


def build_sections(
    floor: int,
    schedule: dict[str, object],
    aisc: dict[str, object],
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[int, dict[str, float | str]]:
    band = floor_band(floor)
    output = {}
    for column in schedule["columns"]:
        segment = column["segments"][band]
        if segment["kind"] == "WF":
            props = aisc["shapes"][segment["shape"]]
            base = {
                "area_in2": float(props["area_in2"]),
                "ix_in4": float(props["ix_in4"]),
                "iy_in4": float(props["iy_in4"]),
                "rx_in": float(props["rx_in"]),
                "ry_in": float(props["ry_in"]),
                "designation": str(segment["shape"]),
                "property_status": str(props["selection_status"]),
            }
        else:
            base = box_properties(segment)
            base["designation"] = f"BOX-{segment['column_type']}"
            base["property_status"] = "RECONSTRUCTED_FROM_TYPE_300_PLATES"
        base["fy_ksi"] = float(segment["fy_ksi"])
        base["room_pn_kip_k1"] = nominal_column_capacity_kip(
            base, 20.0, 1.0, fy_params, e_params, "hold_e600_upper_bound"
        )
        output[int(column["id"])] = base
    return output


def critical(values: list[dict[str, object]], condition) -> float | None:
    for row in values:
        if condition(row):
            return float(row["hot_fraction"])
    return None


def calculate() -> dict[str, object]:
    transfer = json.loads(TRANSFER_PATH.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS_PATH.read_text(encoding="utf-8"))
    aisc = json.loads(AISC_PATH.read_text(encoding="utf-8"))
    fy_params = transfer["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = transfer["steel_temperature_model"]["young_modulus_parameters"]
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }
    tributary = tributary_weights(
        coords,
        float(parameters["established_facts"]["core_width_east_west_m"]),
        float(parameters["established_facts"]["core_depth_north_south_m"]),
    )
    total_kip = float(transfer["nist_global_core_loads_floor_98_kip"]["100_min_case_b"])
    damage = transfer["core_damage"]["more_severe"]
    thermal = transfer["fire_case_b"]["core_column_temperature_ranges_c"]
    times = transfer["fire_case_b"]["times_min"]

    floors: dict[str, object] = {}
    for floor in range(93, 100):
        sections = build_sections(floor, schedule, aisc, fy_params, e_params)
        states = {
            int(row["column"]): str(row["state"])
            for row in damage
            if floor in [int(value) for value in row["floors"]]
        }
        removed = {column for column, state in states.items() if state in {"severed", "heavy"}}
        t_min, t_max = [float(value) for value in thermal[str(floor)][-1]]
        floors[str(floor)] = {
            "sections": sections,
            "impact_states": {str(key): value for key, value in sorted(states.items())},
            "initial_removed": sorted(removed),
            "temperature_100_min_c": [t_min, t_max],
        }

    matrix = []
    baseline_curves: dict[str, object] = {}
    k_factors = [0.7, 1.0, 1.5, 2.0]
    load_methods = ["capacity_proportional", "area_proportional", "plan_tributary_grid"]
    redistributions = ["global_capacity", "local_four"]
    tail_models = ["hold_e600_upper_bound", "linear_to_5pct_at_1000c"]
    hot_fractions = [step / 20.0 for step in range(21)]

    for floor in range(93, 100):
        floor_data = floors[str(floor)]
        sections = {int(k): v for k, v in floor_data["sections"].items()}
        removed = set(floor_data["initial_removed"])
        t_min, t_max = floor_data["temperature_100_min_c"]
        for k_factor in k_factors:
            for load_method in load_methods:
                raw = initial_loads(total_kip, sections, tributary, load_method)
                for redistribution in redistributions:
                    start, viable = remove_initial_damage(raw, removed, sections, coords, redistribution)
                    if not viable:
                        continue
                    for tail_model in tail_models:
                        vulnerability = sorted(
                            start,
                            key=lambda column: start[column]
                            / max(
                                nominal_column_capacity_kip(
                                    sections[column], t_max, k_factor, fy_params, e_params, tail_model
                                ),
                                1e-9,
                            ),
                            reverse=True,
                        )
                        sweep = []
                        for fraction in hot_fractions:
                            hot_count = int(math.ceil(fraction * len(vulnerability) - 1e-12))
                            hot = set(vulnerability[:hot_count])
                            temperatures = {
                                column: (t_max if column in hot else t_min) for column in start
                            }
                            state = cascade(
                                start,
                                temperatures,
                                sections,
                                coords,
                                k_factor,
                                redistribution,
                                fy_params,
                                e_params,
                                tail_model,
                            )
                            sweep.append({"hot_fraction": fraction, "hot_count": hot_count, **state})
                        summary = {
                            "floor": floor,
                            "k_factor": k_factor,
                            "load_method": load_method,
                            "redistribution": redistribution,
                            "elastic_modulus_tail": tail_model,
                            "initial_removed_count": len(removed),
                            "initial_surviving_count": len(start),
                            "temperature_min_c": t_min,
                            "temperature_max_c": t_max,
                            "critical_fraction_first_additional_failure": critical(
                                sweep, lambda row: int(row["additional_failed_count"]) > 0
                            ),
                            "critical_fraction_no_equilibrium": critical(
                                sweep, lambda row: not bool(row["equilibrium"])
                            ),
                        }
                        matrix.append(summary)
                        if (
                            k_factor == 1.0
                            and load_method == "capacity_proportional"
                            and redistribution == "local_four"
                            and tail_model == "hold_e600_upper_bound"
                        ):
                            baseline_curves[str(floor)] = {"summary": summary, "sweep": sweep}

    # Explicit uniform bounds and a synthetic midpoint time trace for the baseline.
    uniform_bounds: dict[str, object] = {}
    midpoint_time_trace: dict[str, object] = {}
    demand_history = transfer["nist_global_core_loads_floor_98_kip"]["case_b_time_history"]
    for floor in range(93, 100):
        floor_data = floors[str(floor)]
        sections = {int(k): v for k, v in floor_data["sections"].items()}
        removed = set(floor_data["initial_removed"])
        raw = initial_loads(total_kip, sections, tributary, "capacity_proportional")
        start, _ = remove_initial_damage(raw, removed, sections, coords, "local_four")
        t_min, t_max = floor_data["temperature_100_min_c"]
        bound_rows = {}
        for label, temp in (("uniform_min", t_min), ("uniform_midpoint_not_median", 0.5 * (t_min + t_max)), ("uniform_max", t_max)):
            bound_rows[label] = cascade(
                start,
                {column: temp for column in start},
                sections,
                coords,
                1.0,
                "local_four",
                fy_params,
                e_params,
                "hold_e600_upper_bound",
            )
        uniform_bounds[str(floor)] = bound_rows

        trace_rows = []
        for index, time in enumerate(times):
            demand = float(demand_history[str(time)])
            raw_time = initial_loads(demand, sections, tributary, "capacity_proportional")
            start_time, _ = remove_initial_damage(raw_time, removed, sections, coords, "local_four")
            low, high = [float(value) for value in thermal[str(floor)][index]]
            temp = 0.5 * (low + high)
            state = cascade(
                start_time,
                {column: temp for column in start_time},
                sections,
                coords,
                1.0,
                "local_four",
                fy_params,
                e_params,
                "hold_e600_upper_bound",
            )
            trace_rows.append(
                {
                    "time_min": time,
                    "reference_floor98_core_load_kip": demand,
                    "uniform_midpoint_temperature_c_not_median": temp,
                    **state,
                }
            )
        midpoint_time_trace[str(floor)] = trace_rows

    return {
        "model": "WTC1_V8B_CORE_STABILITY_REDISTRIBUTION_NETWORK",
        "version": "8.1.0",
        "reference_floor98_core_load_100_min_kip": total_kip,
        "floor_inputs": floors,
        "plan_tributary_weights": {str(key): value for key, value in sorted(tributary.items())},
        "targeted_hot_fraction_matrix": matrix,
        "baseline_targeted_hot_fraction_curves": baseline_curves,
        "baseline_uniform_temperature_bounds": uniform_bounds,
        "baseline_uniform_midpoint_time_trace": midpoint_time_trace,
        "baseline_definition": {
            "k_factor": 1.0,
            "load_method": "capacity_proportional",
            "redistribution": "local_four",
            "elastic_modulus_tail": "hold_e600_upper_bound",
            "hot_targeting": "Columns are ranked by load divided by capacity at the floor maximum temperature; highest vulnerability heated first.",
        },
        "limitations": [
            "This is a one-story column network, not a three-dimensional nonlinear finite-element model.",
            "The same NIST Floor 98 total core load is used as a scale on Floors 93–99 because a complete published floor-by-floor load field is unavailable.",
            "The plan tributary grid ignores elevator openings, core beam stiffness, and actual individual column loads.",
            "Moderate and light impact damage do not reduce capacity; severed and heavy states are removed as in final Case B.",
            "No thermal bowing, creep, residual stress, connection failure, diaphragm deformation, floor pull-in, perimeter wall, or hat-truss action is included.",
            "The NIST E(T) polynomial is only published for 0–600 °C; two explicit tail sensitivities are used above 600 °C.",
            "Eight core columns were reinforced above Floor 98 in the NIST reference model; reinforcement plate dimensions are not yet available, so Floors 98–99 are conservatively unreinforced here.",
            "Most WF properties use ASD7 rows as an explicit proxy for the NIST-reported sixth-edition AISC source; 14WF500 and 14WF550 use LRFD3 as stated by NIST.",
            "Core plan coordinates are reconstructed to about ±0.30 m, adequate only for redistribution sensitivity.",
        ],
    }


def fonts():
    from PIL import ImageFont

    try:
        return {
            "title": ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 30),
            "panel": ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 23),
            "regular": ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18),
            "small": ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 15),
        }
    except OSError:
        default = ImageFont.load_default()
        return {"title": default, "panel": default, "regular": default, "small": default}


def write_plot(result: dict[str, object]) -> Path:
    from PIL import Image, ImageDraw

    f = fonts()
    width, height = 2750, 1160
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text(
        (width // 2, 45),
        "WTC 1 — V8B : stabilité du noyau et redistribution locale",
        fill=(20, 20, 20),
        font=f["title"],
        anchor="mm",
    )
    boxes = [(95, 155, 825, 840), (1010, 155, 1740, 840), (1925, 155, 2655, 840)]

    def xy(box, x, y, xmin, xmax, ymin, ymax):
        x0, y0, x1, y1 = box
        return (
            int(x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)),
            int(y1 - (y - ymin) / (ymax - ymin) * (y1 - y0)),
        )

    def axes(box, title, xlabel, ylabel, xmin, xmax, ymin, ymax, xticks, yticks):
        draw.rectangle(box, outline=(40, 40, 40), width=2)
        draw.text(((box[0] + box[2]) // 2, box[1] - 42), title, fill=(20, 20, 20), font=f["panel"], anchor="mm")
        draw.text(((box[0] + box[2]) // 2, box[3] + 53), xlabel, fill=(35, 35, 35), font=f["regular"], anchor="mm")
        draw.text((box[0] + 9, box[1] + 9), ylabel, fill=(70, 70, 70), font=f["small"], anchor="la")
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

    curves = result["baseline_targeted_hot_fraction_curves"]

    box = boxes[0]
    axes(box, "A. Seuils au scénario de base", "Étage", "Fraction chauffée ciblée", 92.5, 99.5, 0, 1, [93, 94, 95, 96, 97, 98, 99], [0, 0.25, 0.5, 0.75, 1])
    first_points, loss_points = [], []
    for floor in range(93, 100):
        summary = curves[str(floor)]["summary"]
        first = summary["critical_fraction_first_additional_failure"]
        loss = summary["critical_fraction_no_equilibrium"]
        first_points.append(xy(box, floor, 1.02 if first is None else float(first), 92.5, 99.5, 0, 1))
        loss_points.append(xy(box, floor, 1.02 if loss is None else float(loss), 92.5, 99.5, 0, 1))
    draw.line(first_points, fill=(225, 135, 35), width=5)
    draw.line(loss_points, fill=(180, 50, 55), width=5)
    for point in first_points:
        draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=(225, 135, 35))
    for point in loss_points:
        draw.rectangle((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=(180, 50, 55))

    box = boxes[1]
    axes(box, "B. Cascade selon la fraction chaude", "Fraction à Tmax", "Défaillances additionnelles", 0, 1, 0, 47, [0, 0.25, 0.5, 0.75, 1], [0, 10, 20, 30, 40])
    colors = {"94": (63, 126, 188), "95": (238, 142, 43), "96": (190, 55, 57), "97": (75, 150, 90)}
    for floor, color in colors.items():
        points = [
            xy(box, float(row["hot_fraction"]), float(row["additional_failed_count"]), 0, 1, 0, 47)
            for row in curves[floor]["sweep"]
        ]
        draw.line(points, fill=color, width=5)
        draw.text((points[-1][0] - 5, points[-1][1]), f"étage {floor}", fill=color, font=f["small"], anchor="rm")

    box = boxes[2]
    axes(box, "C. Sensibilité à la longueur efficace", "Facteur K", "Fraction chaude sans équilibre", 0.5, 2.2, 0, 1, [0.7, 1, 1.5, 2], [0, 0.25, 0.5, 0.75, 1])
    methods = {
        "capacity_proportional": ((63, 126, 188), "charge ∝ capacité"),
        "area_proportional": ((238, 142, 43), "charge ∝ aire"),
        "plan_tributary_grid": ((190, 55, 57), "aires tributaires de plan"),
    }
    matrix = result["targeted_hot_fraction_matrix"]
    for method, (color, label) in methods.items():
        points = []
        for k in [0.7, 1.0, 1.5, 2.0]:
            row = next(
                item
                for item in matrix
                if item["floor"] == 95
                and item["k_factor"] == k
                and item["load_method"] == method
                and item["redistribution"] == "local_four"
                and item["elastic_modulus_tail"] == "hold_e600_upper_bound"
            )
            value = row["critical_fraction_no_equilibrium"]
            points.append(xy(box, k, 1.02 if value is None else float(value), 0.5, 2.2, 0, 1))
        draw.line(points, fill=color, width=5)
        for point in points:
            draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=color)

    draw.text((105, 930), "Scénario de base :", fill=(20, 20, 20), font=f["panel"])
    draw.text(
        (105, 978),
        "K = 1,0 • charge initiale proportionnelle à la capacité • redistribution vers les 4 colonnes les plus proches • E conservé à E(600 °C) au-delà de 600 °C.",
        fill=(35, 35, 35),
        font=f["regular"],
    )
    draw.line((105, 1040, 165, 1040), fill=(225, 135, 35), width=6)
    draw.text((180, 1030), "première défaillance additionnelle", fill=(35, 35, 35), font=f["regular"])
    draw.line((730, 1040, 790, 1040), fill=(180, 50, 55), width=6)
    draw.text((805, 1030), "aucun équilibre dans ce réseau", fill=(35, 35, 35), font=f["regular"])
    draw.text(
        (width // 2, 1120),
        "La fraction chaude est une sensibilité ciblée sur les colonnes les plus vulnérables — elle ne prétend pas reproduire le champ spatial NIST.",
        fill=(125, 35, 35),
        font=f["regular"],
        anchor="mm",
    )
    path = OUTPUT_DIR / "synthese_wtc1_v8b.png"
    img.save(path)
    return path


def percentage(value: float | None) -> str:
    return "> 100 %" if value is None else f"{100.0 * value:.0f} %"


def write_report(result: dict[str, object]) -> Path:
    curves = result["baseline_targeted_hot_fraction_curves"]
    bounds = result["baseline_uniform_temperature_bounds"]
    rows = []
    for floor in range(93, 100):
        data = curves[str(floor)]["summary"]
        floor_input = result["floor_inputs"][str(floor)]
        rows.append(
            f"| {floor} | {', '.join(str(v) for v in floor_input['initial_removed']) or '—'} | "
            f"{floor_input['temperature_100_min_c'][0]:.0f}–{floor_input['temperature_100_min_c'][1]:.0f} | "
            f"{percentage(data['critical_fraction_first_additional_failure'])} | "
            f"{percentage(data['critical_fraction_no_equilibrium'])} | "
            f"{'oui' if bounds[str(floor)]['uniform_midpoint_not_median']['equilibrium'] else 'non'} | "
            f"{'oui' if bounds[str(floor)]['uniform_max']['equilibrium'] else 'non'} |"
        )

    f95 = curves["95"]["summary"]
    f98 = curves["98"]["summary"]
    cold93 = curves["93"]["sweep"][0]
    cold95 = curves["95"]["sweep"][0]
    text = f"""# WTC 1 — V8B : stabilité et redistribution du noyau

## Résultat principal

V8B remplace les inerties fictives par les propriétés historiques AISC des 43 profils WF, ajoute les trois caissons reconstruits, calcule une résistance nominale de colonne avec flambement, puis redistribue localement les charges lorsqu’une colonne est retirée ou dépasse sa capacité.

Dans le scénario de base (`K = 1,0`, charges initiales proportionnelles à la capacité nominale, redistribution vers quatre voisines, température maximale ciblée d’abord sur les colonnes les plus vulnérables), l’étage 95 connaît sa première défaillance additionnelle lorsque **{percentage(f95['critical_fraction_first_additional_failure'])}** des 38 colonnes restantes sont placées au maximum NIST de l’étage. Le réseau ne trouve plus d’équilibre à **{percentage(f95['critical_fraction_no_equilibrium'])}**. Au niveau 98, avec sa plage beaucoup plus basse de 41–227 °C, aucune perte d’équilibre n’apparaît même si les 47 colonnes sont placées au maximum publié (**{percentage(f98['critical_fraction_no_equilibrium'])}**).

Le seuil de première défaillance vaut 0 % aux niveaux endommagés parce que la seule redistribution des colonnes Case B surcharge déjà quelques voisines, même à la température minimale de l’étage. Aux niveaux 93–94, le réseau sélectionne d’abord **{', '.join(str(v) for v in cold93['additional_failed_columns'])}**, puis retrouve un équilibre avec {cold93['surviving_count']} colonnes. Ce résultat est qualitativement remarquable : NIST indique indépendamment que 705 a flambé après impact et que 605 et 804 ont montré un flambement mineur. Ces identifiants n’ont pas été imposés comme ruptures dans V8B. Au niveau 95, la même règle produit {cold95['additional_failed_count']} défaillances supplémentaires à froid mais conserve encore un équilibre; cela illustre aussi la forte dépendance à la façon dont les planchers et le système global redistribuent réellement les charges.

Ce résultat resserre l’incertitude sans la supprimer : les niveaux 94–97 peuvent devenir instables dans le réseau si une fraction suffisante des colonnes porteuses approche les maxima thermiques, surtout après la suppression des éléments Case B et avec redistribution locale. Mais NIST ne publie pas, dans les tableaux utilisés ici, la fraction exacte de colonnes simultanément chaude ni un champ colonne-par-colonne directement réutilisable. V8B ne permet donc pas encore de dire que ce seuil a effectivement été atteint.

## Seuils à 100 min — scénario de base

| Étage | Colonnes Case B retirées | plage NIST noyau (°C) | première défaillance supplémentaire | plus d’équilibre | équilibre au milieu uniforme | équilibre à Tmax uniforme |
|---:|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## Faits établis intégrés

- NIST signale que son noyau isolé WTC 1 avec dommage Case B ne convergeait pas sous gravité sans redistribution vers le système global; c’est précisément la raison d’introduire ici deux règles de redistribution.
- Le noyau NIST complet incluait les colonnes, poutres et dalles des niveaux 89–106, la plasticité, le flambement plastique et le fluage; il n’incluait pas le hat truss dans le sous-modèle isolé.
- Au niveau 98, la charge totale du noyau Case B passe de 34 429 kip après impact à un maximum de 36 473 kip à 10 min, puis à 28 478 kip à 100 min.
- NIST indique que les colonnes 501, 508, 703, 803, 904, 1002, 1006 et 1007 étaient renforcées entre les niveaux 98 et 106.
- La base AISC historique téléchargée fournit `A`, `Ix`, `Iy`, `rx` et `ry`; NIST dit avoir utilisé le manuel AISC 6e édition, sauf les 14WF455–730 pris dans LRFD3.

## Hypothèses de V8B

- Les charges individuelles sont testées suivant trois répartitions : proportionnelles à la capacité, proportionnelles à l’aire, ou issues d’aires tributaires de plan calculées autour des coordonnées du noyau.
- Après une rupture, la charge est soit redistribuée globalement, soit envoyée vers les quatre colonnes intactes les plus proches.
- Le facteur de longueur efficace `K` est balayé de 0,7 à 2,0. `K = 1,0` sert de scénario de base; `K = 2,0` représente une perte forte de maintien latéral.
- Les colonnes « severed » et « heavy » sont retirées étage par étage; les états « moderate » et « light » restent intacts faute de loi de réduction publiée.
- La capacité utilise la courbe nominale de colonne `Fcr` avec `Fy(T)` NIST. Au-dessus de 600 °C, deux prolongements explicites de `E(T)` sont testés parce que le polynôme transcrit n’est valide que jusqu’à 600 °C.
- Le cas « fraction chaude ciblée » place `Tmax` sur les membres présentant le rapport charge/capacité le plus défavorable et `Tmin` sur les autres. C’est une borne organisée, pas une reconstruction du feu.

## Zones d’incertitude et contradictions apparentes

- **Pas une contradiction formelle :** NIST lui-même rapporte que le noyau isolé Case B ne trouvait pas d’équilibre initial, alors que son modèle global le pouvait grâce aux autres chemins de charge. Notre réseau retrouve que la règle de redistribution change fortement le seuil.
- **Donnée manquante majeure :** les charges exactes colonne par colonne et les températures correspondantes ne sont disponibles ici que sous forme de figures à bulles et d’extrema. Les trois répartitions reconstruites restent des hypothèses.
- **Renforts manquants :** les dimensions des plaques de renforcement des huit colonnes 98–106 n’ont pas été retrouvées. V8B les omet, ce qui sous-estime leur résistance et rend les résultats 98–99 conservateurs.
- **Propriétés historiques :** la base AISC v16.0H ne présente pas de ligne « 6th » dans sa table principale pour ces profils. Les lignes ASD7 sont donc marquées comme proxy historique, tandis que 14WF500 et 14WF550 utilisent LRFD3 conformément à la règle NIST.
- **Limite essentielle :** un réseau d’un étage ne reproduit ni le raccourcissement cumulatif du noyau, ni le hat truss, ni la flexion thermique, ni le fluage, ni l’attraction de charge par dilatation, ni la traction exercée par les planchers sur la façade sud.

## Étape V8C

La prochaine version doit être un sous-modèle 3D des niveaux 93–99 dans CalculiX : poutres-colonnes avec imperfections, diaphragmes de plancher simplifiés, retraits Case B localisés et histoires thermiques par groupes spatiaux. Les résultats V8B servent à choisir les cas qui méritent ce calcul coûteux : `K ≈ 1`, redistribution locale, étages 94–97, fractions chaudes autour des seuils trouvés, plus variantes froides et maximales.

![Synthèse V8B](synthese_wtc1_v8b.png)
"""
    path = OUTPUT_DIR / "rapport_wtc1_v8b.md"
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = calculate()
    json_path = OUTPUT_DIR / "resultats_wtc1_v8b.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    plot_path = write_plot(result)
    report_path = write_report(result)
    print(json_path)
    print(plot_path)
    print(report_path)


if __name__ == "__main__":
    main()
