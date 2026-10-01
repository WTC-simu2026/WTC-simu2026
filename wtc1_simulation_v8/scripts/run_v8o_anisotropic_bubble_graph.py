"""WTC 1 V8O - vector-digitized anisotropic cold redistribution graph.

The anisotropic kernel is identified only from the Floor 98 bubble-map change.
The separate maximum-DCR map is held back until cross-figure validation.  Both
sources are outputs of the NIST global model, so this remains an emulator audit.
"""

from __future__ import annotations

import itertools
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
CONFIG = V8 / "data" / "v8o_anisotropic_bubble_graph.json"
V8N_CONFIG = V8 / "data" / "v8n_inverse_core_redistribution.json"
V8N_RESULT = V8 / "output" / "resultats_wtc1_v8n_redistribution_inverse_froide.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
OUT_DIGITIZATION = V8 / "output" / "digitisation_wtc1_v8o_floor98.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8o_graphe_anisotrope.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8o_graphe_anisotrope.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8o_graphe_anisotrope.png"


def load_inputs() -> dict[str, object]:
    return {
        "config": json.loads(CONFIG.read_text(encoding="utf-8")),
        "v8n_config": json.loads(V8N_CONFIG.read_text(encoding="utf-8")),
        "v8n_result": json.loads(V8N_RESULT.read_text(encoding="utf-8")),
        "v8b": json.loads(V8B_RESULT.read_text(encoding="utf-8")),
        "parameters": json.loads(PARAMETERS.read_text(encoding="utf-8")),
    }


def vector_circles(pdf_path: Path, page_index: int) -> list[dict[str, float]]:
    operations = PdfReader(str(pdf_path)).pages[page_index].get_contents().operations
    circles: list[dict[str, float]] = []
    points: list[tuple[float, float]] = []
    for operands, operator in operations:
        name = operator.decode("latin1")
        if name == "m":
            points = [(float(operands[0]), float(operands[1]))]
        elif name == "c" and points:
            points.extend(
                (float(operands[index]), float(operands[index + 1]))
                for index in (0, 2, 4)
            )
        elif name == "b*" and points:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            radius_x = 0.5 * (max(xs) - min(xs))
            radius_y = 0.5 * (max(ys) - min(ys))
            circles.append(
                {
                    "center_x_pdf_points": 0.5 * (min(xs) + max(xs)),
                    "center_y_pdf_points": 0.5 * (min(ys) + max(ys)),
                    "radius_x_pdf_points": radius_x,
                    "radius_y_pdf_points": radius_y,
                    "radius_pdf_points": 0.5 * (radius_x + radius_y),
                }
            )
            points = []
    return circles


def select_core_circles(
    circles: list[dict[str, float]], x_range: list[float], row_bands: dict[str, list[float]]
) -> dict[int, dict[str, float]]:
    selected: dict[int, dict[str, float]] = {}
    for row_text, values in row_bands.items():
        row = int(row_text)
        lower, upper, expected_count = float(values[0]), float(values[1]), int(values[2])
        paths = sorted(
            [
                circle
                for circle in circles
                if float(x_range[0]) < circle["center_x_pdf_points"] < float(x_range[1])
                and lower < circle["center_y_pdf_points"] <= upper
            ],
            key=lambda circle: circle["center_x_pdf_points"],
        )
        if len(paths) != expected_count:
            raise RuntimeError(
                f"Vector digitization row {row}: expected {expected_count}, found {len(paths)}"
            )
        for digit, circle in enumerate(paths, start=1):
            selected[row * 100 + digit] = circle
    if len(selected) != 47:
        raise RuntimeError(f"Expected 47 core circles, found {len(selected)}")
    return selected


def normalized_loads(
    selected: dict[int, dict[str, float]], total_kip: float
) -> dict[int, float]:
    areas = {
        column: float(circle["radius_pdf_points"]) ** 2
        for column, circle in selected.items()
    }
    scale = total_kip / sum(areas.values())
    return {column: area * scale for column, area in areas.items()}


def load_uncertainty(
    selected: dict[int, dict[str, float]], total_kip: float, radius_uncertainty: float
) -> dict[int, dict[str, float]]:
    columns = sorted(selected)
    radii = np.array([selected[column]["radius_pdf_points"] for column in columns])
    rng = np.random.default_rng(814)
    perturbation = rng.uniform(-radius_uncertainty, radius_uncertainty, size=(10000, len(columns)))
    sampled_radii = np.maximum(radii[np.newaxis, :] + perturbation, 0.03)
    sampled_area = sampled_radii**2
    sampled_load = sampled_area / sampled_area.sum(axis=1, keepdims=True) * total_kip
    return {
        column: {
            "p02_5_kip": float(np.percentile(sampled_load[:, index], 2.5)),
            "p50_kip": float(np.percentile(sampled_load[:, index], 50.0)),
            "p97_5_kip": float(np.percentile(sampled_load[:, index], 97.5)),
        }
        for index, column in enumerate(columns)
    }


def legend_diagnostic(
    selected: dict[int, dict[str, float]], total_kip: float, references: list[list[float]]
) -> dict[str, object]:
    radius = np.array([float(row[0]) for row in references])
    load = np.array([float(row[1]) for row in references])
    area = radius**2
    coefficient = float(np.dot(area, load) / np.dot(area, area))
    predicted = coefficient * area
    raw_sum = coefficient * sum(
        float(circle["radius_pdf_points"]) ** 2 for circle in selected.values()
    )
    return {
        "legend_kip_per_radius_squared": coefficient,
        "legend_rows": [
            {
                "radius_pdf_points": float(r),
                "label_kip": float(target),
                "regression_kip": float(value),
                "relative_residual": float((value - target) / target),
            }
            for r, target, value in zip(radius, load, predicted)
        ],
        "raw_core_sum_from_legend_kip": float(raw_sum),
        "published_core_total_kip": total_kip,
        "published_to_legend_raw_scale_factor": float(total_kip / raw_sum),
        "warning": "The legend-calibrated raw bubble sum is inconsistent with the published total; normalized relative areas are used instead.",
    }


def digitize(inputs: dict[str, object]) -> dict[str, object]:
    settings = inputs["config"]["vector_digitization"]
    pdf = ROOT / settings["pdf"]
    circles = vector_circles(pdf, int(settings["zero_based_page_index"]))
    before_selected = select_core_circles(
        circles,
        settings["core_x_range_pdf_points"],
        settings["before_impact_row_bands_pdf_points"],
    )
    after_selected = select_core_circles(
        circles,
        settings["core_x_range_pdf_points"],
        settings["after_impact_row_bands_pdf_points"],
    )
    before_total = float(settings["official_core_totals_floor98_kip"]["before_impact"])
    after_total = float(settings["official_core_totals_floor98_kip"]["after_impact"])
    before_loads = normalized_loads(before_selected, before_total)
    after_loads = normalized_loads(after_selected, after_total)
    uncertainty = float(settings["radius_uncertainty_pdf_points"])
    rows = []
    for column in sorted(before_loads):
        rows.append(
            {
                "column": column,
                "before_radius_pdf_points": float(before_selected[column]["radius_pdf_points"]),
                "after_radius_pdf_points": float(after_selected[column]["radius_pdf_points"]),
                "before_load_kip": float(before_loads[column]),
                "after_load_kip": float(after_loads[column]),
                "change_kip": float(after_loads[column] - before_loads[column]),
            }
        )
    payload = {
        "method": "direct PDF vector-path extraction; load proportional to radius squared; normalized to Table 4-20 totals",
        "pdf": str(pdf),
        "pdf_page": 287,
        "vector_circle_count_all_page": len(circles),
        "core_circle_count_before": len(before_selected),
        "core_circle_count_after": len(after_selected),
        "radius_uncertainty_pdf_points": uncertainty,
        "before_impact": {
            "total_kip": before_total,
            "uncertainty": load_uncertainty(before_selected, before_total, uncertainty),
            "legend_diagnostic": legend_diagnostic(
                before_selected, before_total, settings["legend_reference_radius_and_load"]
            ),
        },
        "after_impact": {
            "total_kip": after_total,
            "uncertainty": load_uncertainty(after_selected, after_total, uncertainty),
            "legend_diagnostic": legend_diagnostic(
                after_selected, after_total, settings["legend_reference_radius_and_load"]
            ),
        },
        "rows": rows,
    }
    OUT_DIGITIZATION.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return payload


def prepare(inputs: dict[str, object]) -> dict[str, object]:
    coords = {
        int(row["id"]): np.array([float(row["x_m"]), float(row["y_m"])], dtype=float)
        for row in inputs["parameters"]["core_layout_reconstruction"]["columns"]
    }
    floors = sorted(int(value) for value in inputs["v8n_config"]["official_core_totals_kip"])
    capacities: dict[int, dict[int, float]] = {}
    removed: dict[int, set[int]] = {}
    for floor in floors:
        source = inputs["v8b"]["floor_inputs"][str(floor)]
        capacities[floor] = {
            int(column): float(section["room_pn_kip_k1"])
            for column, section in source["sections"].items()
        }
        removed[floor] = {int(value) for value in source["initial_removed"]}
    x_distances = []
    y_distances = []
    rows: dict[int, list[int]] = {}
    for column in sorted(coords):
        rows.setdefault(column // 100, []).append(column)
    for columns in rows.values():
        ordered = sorted(columns, key=lambda column: coords[column][0])
        x_distances.extend(
            abs(float(coords[second][0] - coords[first][0]))
            for first, second in zip(ordered, ordered[1:])
        )
    row_y = sorted(set(round(float(point[1]), 6) for point in coords.values()))
    y_distances.extend(second - first for first, second in zip(row_y, row_y[1:]))
    return {
        "coords": coords,
        "columns": sorted(coords),
        "floors": floors,
        "capacities": capacities,
        "removed": removed,
        "bay_x_m": float(np.median(x_distances)),
        "bay_y_m": float(np.median(y_distances)),
        "max_abs_y_m": max(abs(float(point[1])) for point in coords.values()),
    }


def kernel_weights(
    source: int,
    targets: list[int],
    prep: dict[str, object],
    capacities: dict[int, float],
    parameters: dict[str, float],
) -> dict[int, float]:
    lx = parameters["transfer_length_x_bays"] * float(prep["bay_x_m"])
    ly = parameters["transfer_length_y_bays"] * float(prep["bay_y_m"])
    weights = {}
    for target in targets:
        delta = prep["coords"][target] - prep["coords"][source]
        exponent = (
            -abs(float(delta[0])) / lx
            - abs(float(delta[1])) / ly
            + parameters["signed_x_bias"] * float(delta[0]) / lx
        )
        weights[target] = capacities[target] ** parameters["capacity_bias_exponent"] * math.exp(exponent)
    denominator = sum(weights.values())
    return {target: value / denominator for target, value in weights.items()}


def global_weights(
    targets: list[int], prep: dict[str, object], capacities: dict[int, float], parameters: dict[str, float]
) -> dict[int, float]:
    weights = {}
    for target in targets:
        y_norm = float(prep["coords"][target][1]) / float(prep["max_abs_y_m"])
        weights[target] = capacities[target] ** parameters["capacity_bias_exponent"] * math.exp(
            parameters["north_bias"] * y_norm
        )
    denominator = sum(weights.values())
    return {target: value / denominator for target, value in weights.items()}


def bubble_prediction(
    inputs: dict[str, object], digitization: dict[str, object], prep: dict[str, object], parameters: dict[str, float]
) -> dict[int, float]:
    before = {int(row["column"]): float(row["before_load_kip"]) for row in digitization["rows"]}
    observed_after = {int(row["column"]): float(row["after_load_kip"]) for row in digitization["rows"]}
    damaged = {int(value) for value in inputs["config"]["source_boundary_conditions"]["damaged_column_ids"]}
    survivors = sorted(set(before) - damaged)
    capacities = prep["capacities"][98]
    predicted = {column: before[column] for column in survivors}
    for source in sorted(damaged):
        release = max(before[source] - observed_after[source], 0.0)
        weights = kernel_weights(source, survivors, prep, capacities, parameters)
        for target in survivors:
            predicted[target] += release * weights[target]
    net_gain = float(inputs["config"]["source_boundary_conditions"]["net_core_gain_floor98_kip"])
    gain_weights = global_weights(survivors, prep, capacities, parameters)
    for target in survivors:
        predicted[target] += net_gain * gain_weights[target]
    for source in damaged:
        predicted[source] = observed_after[source]
    correction = float(digitization["after_impact"]["total_kip"]) - sum(predicted.values())
    for target in survivors:
        predicted[target] += correction * gain_weights[target]
    return predicted


def candidate_parameters(config: dict[str, object]) -> list[dict[str, float]]:
    settings = config["anisotropic_kernel"]
    keys = [
        "transfer_length_x_bays",
        "transfer_length_y_bays",
        "capacity_bias_exponent",
        "signed_x_bias",
        "north_bias",
    ]
    return [
        {key: float(value) for key, value in zip(keys, values)}
        for values in itertools.product(*(settings[key] for key in keys))
    ]


def errors_for_columns(
    predicted: dict[int, float], observed: dict[int, float], columns: list[int]
) -> list[dict[str, float]]:
    return [
        {
            "column": column,
            "observed": observed[column],
            "predicted": predicted[column],
            "error": predicted[column] - observed[column],
        }
        for column in columns
    ]


def metrics(rows: list[dict[str, float]]) -> dict[str, float]:
    values = np.array([float(row["error"]) for row in rows])
    return {
        "count": int(len(rows)),
        "mae": float(np.mean(np.abs(values))),
        "rmse": float(np.sqrt(np.mean(values**2))),
        "maximum_absolute_error": float(np.max(np.abs(values))),
        "mean_bias": float(np.mean(values)),
    }


def identify_kernel(
    inputs: dict[str, object], digitization: dict[str, object], prep: dict[str, object]
) -> dict[str, object]:
    observed = {int(row["column"]): float(row["after_load_kip"]) for row in digitization["rows"]}
    damaged = {int(value) for value in inputs["config"]["source_boundary_conditions"]["damaged_column_ids"]}
    survivors = sorted(set(observed) - damaged)
    folds = {
        name: sorted(column for column in survivors if column // 100 in set(rows))
        for name, rows in inputs["config"]["nested_spatial_validation"]["outer_folds"].items()
    }
    candidates = candidate_parameters(inputs["config"])
    predictions = [bubble_prediction(inputs, digitization, prep, parameters) for parameters in candidates]
    outer_rows: list[dict[str, float | str]] = []
    fold_results = []
    for fold_name, test_columns in folds.items():
        training_columns = sorted(set(survivors) - set(test_columns))
        best_index = min(
            range(len(candidates)),
            key=lambda index: (
                metrics(errors_for_columns(predictions[index], observed, training_columns))["rmse"],
                metrics(errors_for_columns(predictions[index], observed, training_columns))["mae"],
                candidates[index]["transfer_length_x_bays"] + candidates[index]["transfer_length_y_bays"],
            ),
        )
        test_rows = errors_for_columns(predictions[best_index], observed, test_columns)
        for row in test_rows:
            outer_rows.append({**row, "outer_fold": fold_name})
        fold_results.append(
            {
                "outer_fold": fold_name,
                "training_column_count": len(training_columns),
                "test_columns": test_columns,
                "selected_parameters": candidates[best_index],
                "training_metrics": metrics(
                    errors_for_columns(predictions[best_index], observed, training_columns)
                ),
                "test_metrics": metrics(test_rows),
            }
        )
    final_index = min(
        range(len(candidates)),
        key=lambda index: (
            metrics(errors_for_columns(predictions[index], observed, survivors))["rmse"],
            metrics(errors_for_columns(predictions[index], observed, survivors))["mae"],
            candidates[index]["transfer_length_x_bays"] + candidates[index]["transfer_length_y_bays"],
        ),
    )
    final_rows = errors_for_columns(predictions[final_index], observed, survivors)
    return {
        "parameter_case_count": len(candidates),
        "surviving_target_count": len(survivors),
        "outer_fold_results": fold_results,
        "outer_fold_rows": outer_rows,
        "outer_fold_metrics": metrics(outer_rows),
        "final_parameters": candidates[final_index],
        "final_fit_rows": final_rows,
        "final_fit_metrics": metrics(final_rows),
        "final_prediction": {str(column): float(value) for column, value in predictions[final_index].items()},
        "dcr_target_used_for_selection": False,
    }


def logistic(x: float, fit: dict[str, float]) -> float:
    shape = 1.0 / (1.0 + math.exp(-(x - float(fit["midpoint_floor"])) / float(fit["scale_floors"])))
    return float(fit["lower_kip"]) + (float(fit["upper_kip"]) - float(fit["lower_kip"])) * shape


def floor_prediction(
    inputs: dict[str, object], prep: dict[str, object], floor: int, parameters: dict[str, float]
) -> dict[str, object]:
    config = inputs["v8n_config"]
    capacities = prep["capacities"][floor]
    columns = prep["columns"]
    removed = prep["removed"][floor]
    survivors = sorted(set(columns) - removed)
    pre_dcr = {int(key): float(value) for key, value in config["official_maximum_dcr_before_impact"].items()}
    before_total = float(config["official_core_totals_kip"][str(floor)]["before_impact"])
    raw = {column: pre_dcr[column] * capacities[column] for column in columns}
    baseline = {column: before_total * raw[column] / sum(raw.values()) for column in columns}
    loads = {column: baseline[column] for column in survivors}
    for source in sorted(removed):
        weights = kernel_weights(source, survivors, prep, capacities, parameters)
        for target in survivors:
            loads[target] += baseline[source] * weights[target]
    full_fit = inputs["v8n_result"]["floor_generalization"]["full_fit"]
    after_total = before_total + logistic(float(floor), full_fit)
    adjustment = after_total - before_total
    gain_weights = global_weights(survivors, prep, capacities, parameters)
    for target in survivors:
        loads[target] += adjustment * gain_weights[target]
    correction = after_total - sum(loads.values())
    for target in survivors:
        loads[target] += correction * gain_weights[target]
    return {
        "floor": floor,
        "removed_columns": sorted(removed),
        "before_total_kip": before_total,
        "predicted_after_total_kip": after_total,
        "calculated_total_kip": float(sum(loads.values())),
        "column_loads_kip": {str(column): float(loads[column]) for column in survivors},
        "column_dcr": {str(column): float(loads[column] / capacities[column]) for column in survivors},
    }


def cross_figure_dcr(
    inputs: dict[str, object], prep: dict[str, object], parameters: dict[str, float]
) -> dict[str, object]:
    targets = {
        int(key): float(value)
        for key, value in inputs["v8n_config"]["official_maximum_dcr_after_impact"].items()
    }
    maxima = {column: -math.inf for column in targets}
    governing = {column: None for column in targets}
    floor_rows = []
    for floor in prep["floors"]:
        row = floor_prediction(inputs, prep, floor, parameters)
        floor_rows.append(row)
        for column in targets:
            if str(column) not in row["column_dcr"]:
                continue
            value = float(row["column_dcr"][str(column)])
            if value > maxima[column]:
                maxima[column] = value
                governing[column] = floor
    rows = [
        {
            "column": column,
            "observed": targets[column],
            "predicted": float(maxima[column]),
            "error": float(maxima[column] - targets[column]),
            "governing_floor": int(governing[column]),
        }
        for column in sorted(targets)
    ]
    return {
        "target_count": len(targets),
        "rows": rows,
        "metrics": metrics(rows),
        "column804": next(row for row in rows if row["column"] == 804),
        "floor_rows": floor_rows,
        "target_used_for_kernel_selection": False,
    }


def boundary_flags(config: dict[str, object], parameters: dict[str, float]) -> list[str]:
    flags = []
    for key, value in parameters.items():
        grid = [float(item) for item in config["anisotropic_kernel"][key]]
        if math.isclose(value, min(grid), abs_tol=1e-12):
            flags.append(f"{key}=minimum")
        elif math.isclose(value, max(grid), abs_tol=1e-12):
            flags.append(f"{key}=maximum")
    return flags


def validate(
    inputs: dict[str, object], digitization: dict[str, object], prep: dict[str, object], kernel: dict[str, object], dcr: dict[str, object]
) -> dict[str, bool]:
    checks = {
        "before_core_circle_count_47": digitization["core_circle_count_before"] == 47,
        "after_core_circle_count_47": digitization["core_circle_count_after"] == 47,
        "before_total_conserved": math.isclose(sum(row["before_load_kip"] for row in digitization["rows"]), 34029.0, abs_tol=1e-6),
        "after_total_conserved": math.isclose(sum(row["after_load_kip"] for row in digitization["rows"]), 34429.0, abs_tol=1e-6),
        "three_outer_folds": len(kernel["outer_fold_results"]) == 3,
        "all_38_survivors_scored_once_outer": len(kernel["outer_fold_rows"]) == 38 and len({row["column"] for row in kernel["outer_fold_rows"]}) == 38,
        "dcr_not_used_for_kernel_selection": not kernel["dcr_target_used_for_selection"] and not dcr["target_used_for_kernel_selection"],
        "dcr_target_count_38": dcr["target_count"] == 38,
        "all_floor_totals_conserved": all(math.isclose(row["predicted_after_total_kip"], row["calculated_total_kip"], abs_tol=1e-6) for row in dcr["floor_rows"]),
        "parameter_grid_count_3600": kernel["parameter_case_count"] == 3600,
    }
    if not all(checks.values()):
        raise RuntimeError(f"V8O validation failed: {checks}")
    return checks


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_plot(payload: dict[str, object]) -> None:
    canvas = Image.new("RGB", (1900, 1180), "white")
    draw = ImageDraw.Draw(canvas)
    navy = (30, 43, 61)
    blue = (52, 112, 183)
    orange = (223, 132, 35)
    green = (43, 145, 90)
    red = (192, 57, 57)
    grey = (220, 224, 230)
    draw.text((950, 50), "WTC 1 V8O - carte vectorielle et redistribution anisotrope", anchor="mm", font=font(34, True), fill=navy)

    panels = [
        (125, 185, 760, 500, "Carte Floor 98 : validation par blocs", payload["kernel_identification"]["outer_fold_rows"], "charge officielle normalisee (kip)", "charge predite (kip)", 0.0, 1900.0),
        (1050, 185, 660, 500, "DCR 93-99 : validation croisee entre figures", payload["cross_figure_dcr"]["rows"], "DCR officiel", "DCR predit", 0.25, 1.45),
    ]
    fold_colors = {"A_rows_5_8": blue, "B_rows_6_10": orange, "C_rows_7_9": green}
    for panel_index, (x0, y0, width, height, title, rows, xlabel, ylabel, minimum, maximum) in enumerate(panels):
        draw.text((x0 + width / 2, y0 - 60), title, anchor="mm", font=font(23, True), fill=navy)
        ticks = np.linspace(minimum, maximum, 6)
        for tick in ticks:
            x = x0 + (float(tick) - minimum) / (maximum - minimum) * width
            y = y0 + height - (float(tick) - minimum) / (maximum - minimum) * height
            draw.line((x, y0, x, y0 + height), fill=grey, width=1)
            draw.line((x0, y, x0 + width, y), fill=grey, width=1)
            label = f"{tick:.1f}" if maximum < 2 else f"{tick:.0f}"
            draw.text((x, y0 + height + 12), label, anchor="ma", font=font(13), fill=navy)
            draw.text((x0 - 10, y), label, anchor="rm", font=font(13), fill=navy)
        draw.rectangle((x0, y0, x0 + width, y0 + height), outline=navy, width=2)
        draw.line((x0, y0 + height, x0 + width, y0), fill=green, width=3)
        for row in rows:
            x = x0 + (float(row["observed"]) - minimum) / (maximum - minimum) * width
            y = y0 + height - (float(row["predicted"]) - minimum) / (maximum - minimum) * height
            color = fold_colors.get(str(row.get("outer_fold", "")), blue)
            radius = 6 if panel_index == 0 else 5
            if int(row["column"]) == 804 and panel_index == 1:
                color = orange
                radius = 9
                draw.text((x + 11, y - 7), "804", font=font(14, True), fill=red)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline=navy if radius > 6 else None)
        draw.text((x0 + width / 2, y0 + height + 50), xlabel, anchor="mm", font=font(16, True), fill=navy)
        draw.text((x0 + 10, y0 + 10), ylabel, anchor="la", font=font(14, True), fill=navy)

    kernel = payload["kernel_identification"]
    dcr = payload["cross_figure_dcr"]
    params = kernel["final_parameters"]
    digit = payload["digitization"]
    after_scale = digit["after_impact"]["legend_diagnostic"]["published_to_legend_raw_scale_factor"]
    cards = [
        ("Carte vectorielle reservee", f"MAE {kernel['outer_fold_metrics']['mae']:.0f} kip", f"erreur max {kernel['outer_fold_metrics']['maximum_absolute_error']:.0f} kip"),
        ("DCR autre figure", f"MAE {dcr['metrics']['mae']:.3f}", f"erreur max {dcr['metrics']['maximum_absolute_error']:.3f}"),
        ("Anisotropie retenue", f"Lx {params['transfer_length_x_bays']:.2f} / Ly {params['transfer_length_y_bays']:.2f}", f"biais x {params['signed_x_bias']:+.2f}"),
        ("Controle de l'echelle", f"facteur {after_scale:.3f}", "normalisation au total officiel"),
    ]
    for index, (title, value, note) in enumerate(cards):
        x = 125 + 430 * index
        y = 790
        draw.rounded_rectangle((x, y, x + 380, y + 145), radius=14, fill=(244, 247, 250), outline=grey, width=2)
        draw.text((x + 18, y + 20), title, font=font(17, True), fill=navy)
        draw.text((x + 18, y + 59), value, font=font(24, True), fill=blue)
        draw.text((x + 18, y + 106), note, font=font(14), fill=navy)

    summary = payload["summary"]
    gate_color = green if summary["gate_passed"] else red
    gate_fill = (232, 247, 239) if summary["gate_passed"] else (249, 230, 230)
    draw.rounded_rectangle((125, 995, 1775, 1090), radius=18, fill=gate_fill)
    draw.text((950, 1025), summary["gate_label"], anchor="mm", font=font(28, True), fill=gate_color)
    draw.text((950, 1064), summary["gate_explanation"], anchor="mm", font=font(17), fill=navy)
    draw.text((950, 1142), "Deux figures NIST distinctes, mais un meme modele officiel : aucune validation independante de l'evenement reel.", anchor="mm", font=font(16, True), fill=red)
    canvas.save(OUT_PNG)


def write_report(payload: dict[str, object]) -> None:
    digit = payload["digitization"]
    kernel = payload["kernel_identification"]
    dcr = payload["cross_figure_dcr"]
    params = kernel["final_parameters"]
    summary = payload["summary"]
    after_diag = digit["after_impact"]["legend_diagnostic"]
    lines = [
        "# WTC 1 - V8O : carte vectorielle et redistribution anisotrope",
        "",
        "## Resultat principal",
        "",
        summary["report_conclusion"],
        "",
        f"La mesure vectorielle retrouve 47 cercles avant impact et 47 apres impact. Sur les blocs de lignes exclus successivement, le noyau anisotrope predit les charges individuelles avec une MAE de {kernel['outer_fold_metrics']['mae']:.0f} kip et une erreur maximale de {kernel['outer_fold_metrics']['maximum_absolute_error']:.0f} kip.",
        f"Sans reutiliser les DCR pour choisir les parametres, la prediction croisee des 38 DCR donne une MAE de {dcr['metrics']['mae']:.3f} et une erreur maximale de {dcr['metrics']['maximum_absolute_error']:.3f}. Pour le poteau 804 : officiel {dcr['column804']['observed']:.2f}, predit {dcr['column804']['predicted']:.3f}.",
        "",
        "## Faits et resultats officiels",
        "",
        "- Les Figures 4-64 et 4-65 representent les charges axiales des poteaux au niveau 98 avant et apres impact.",
        "- La Table 4-20 fixe les totaux du noyau a 34 029 kip avant impact et 34 429 kip apres impact.",
        "- La Figure 4-69, conservee hors identification du noyau, fournit les DCR maximaux entre les niveaux 93 et 99.",
        "",
        "## Controle de la numerisation",
        "",
        f"La calibration directe par la legende produirait {after_diag['raw_core_sum_from_legend_kip']:.0f} kip apres impact, contre 34 429 kip dans la table, soit un facteur correctif {after_diag['published_to_legend_raw_scale_factor']:.3f}. Les diametres relatifs sont coherents, mais l'echelle absolue de la figure et le total publie ne le sont pas. V8O normalise donc les aires relatives au total tabule et ne pretend pas extraire des charges absolues independantes de la table.",
        "",
        "## Parametres anisotropes retenus",
        "",
        f"- Longueur est-ouest Lx : **{params['transfer_length_x_bays']:.2f} travee(s)**.",
        f"- Longueur nord-sud Ly : **{params['transfer_length_y_bays']:.2f} travee(s)**.",
        f"- Exposant de capacite : **{params['capacity_bias_exponent']:.2f}**.",
        f"- Biais directionnel est-ouest : **{params['signed_x_bias']:+.2f}**.",
        f"- Biais nord-sud du gain net : **{params['north_bias']:+.2f}**.",
        f"- Bornes actives : **{', '.join(summary['parameter_boundary_flags']) if summary['parameter_boundary_flags'] else 'aucune'}**.",
        "",
        "## Validation spatiale de la carte Floor 98",
        "",
        "| Bloc exclu | Poteaux testes | MAE (kip) | Erreur max (kip) |",
        "|---|---:|---:|---:|",
    ]
    for row in kernel["outer_fold_results"]:
        lines.append(
            f"| {row['outer_fold']} | {len(row['test_columns'])} | {row['test_metrics']['mae']:.0f} | {row['test_metrics']['maximum_absolute_error']:.0f} |"
        )
    lines.extend(
        [
            "",
            "## Plus grandes erreurs DCR entre figures",
            "",
            "| Poteau | DCR officiel | DCR predit | Erreur | Etage gouvernant |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(dcr["rows"], key=lambda item: abs(item["error"]), reverse=True)[:10]:
        lines.append(
            f"| {row['column']} | {row['observed']:.2f} | {row['predicted']:.3f} | {row['error']:+.3f} | {row['governing_floor']} |"
        )
    lines.extend(
        [
            "",
            "## Hypotheses propres a V8O",
            "",
            "- Les differences de charge des neuf poteaux marques endommages servent de conditions sources pour identifier la direction de redistribution au niveau 98.",
            "- La charge liberee suit un noyau exponentiel anisotrope; les capacites froides V8B biaisent les destinations.",
            "- Les parametres identifies au niveau 98 sont transferes sans recalibration aux retraits de segments par etage et au calcul des DCR 93-99.",
            "- La courbe de charge totale et le prior pre-impact proviennent de V8N; V8O ne constitue donc pas une reconstruction autonome.",
            "",
            "## Limites et contradictions",
            "",
            "- L'incoherence entre la legende graphique et le total tabule interdit de traiter les rayons comme une mesure absolue sans normalisation.",
            "- Les cartes de bulles et de DCR proviennent du meme modele NIST. Une prediction croisee reussie serait plus exigeante qu'un ajustement direct, mais resterait dependante des memes entrees officielles.",
            "- Le noyau anisotrope reste scalaire : rotations, flexion biaxiale, P-delta, dalle fissuree et assemblages reels ne sont pas resolus.",
            "- Aucun resultat V8O ne constitue une probabilite de l'evenement ou un test distinctif d'explosifs.",
            "",
            "## Decision du gate",
            "",
            summary["gate_decision"],
            "",
            f"Temps d'execution : {payload['run']['elapsed_seconds']:.2f} s. Jeux de parametres testes : {kernel['parameter_case_count']}.",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    digitization = digitize(inputs)
    prep = prepare(inputs)
    kernel = identify_kernel(inputs, digitization, prep)
    dcr = cross_figure_dcr(inputs, prep, kernel["final_parameters"])
    validation = validate(inputs, digitization, prep, kernel, dcr)
    gates = inputs["config"]["acceptance_gates"]
    bubble_mae_pass = kernel["outer_fold_metrics"]["mae"] <= float(gates["bubble_outer_fold_mae_kip_max"])
    bubble_max_pass = kernel["outer_fold_metrics"]["maximum_absolute_error"] <= float(gates["bubble_outer_fold_maximum_error_kip_max"])
    dcr_mae_pass = dcr["metrics"]["mae"] <= float(gates["cross_figure_dcr_mae_max"])
    dcr_max_pass = dcr["metrics"]["maximum_absolute_error"] <= float(gates["cross_figure_dcr_maximum_error_max"])
    column804_pass = abs(float(dcr["column804"]["error"])) <= float(gates["column804_dcr_absolute_error_max"])
    gate_passed = bool(bubble_mae_pass and bubble_max_pass and dcr_mae_pass and dcr_max_pass and column804_pass)
    flags = boundary_flags(inputs["config"], kernel["final_parameters"])
    if gate_passed:
        gate_label = "GATE ANISOTROPE FROID VALIDE AVEC RESERVES"
        gate_explanation = "La carte reservee et la figure DCR distincte franchissent les seuils; le surrogate reste dependant du modele NIST."
        gate_decision = "**VALIDE AVEC RESERVES.** Le surrogate anisotrope peut servir d'etat froid de reference pour une sensibilite thermique separee, sans etre confondu avec un solveur global ou une validation de l'evenement reel."
        report_conclusion = "La V8O transfere avec succes une anisotropie identifiee sur la carte de charges du niveau 98 vers la carte DCR distincte. Elle corrige donc le manque local de V8N au niveau des sorties officielles selectionnees, mais pas l'absence d'entrees structurelles independantes."
    else:
        gate_label = "GATE ANISOTROPE FROID NON VALIDE"
        gate_explanation = "Au moins un seuil reserve ou croise echoue; aucune propagation thermique ou Blender n'est autorisee."
        gate_decision = "**NON VALIDE.** La topologie anisotrope issue de la carte Floor 98 ne generalise pas suffisamment la carte DCR 93-99. Il faut davantage de donnees nodales ou un modele de plancher/assemblage explicite."
        report_conclusion = "La V8O mesure proprement la carte vectorielle et identifie une redistribution directionnelle, mais celle-ci ne generalise pas suffisamment toutes les sorties DCR laissees hors identification. Le chemin froid reste donc non valide."
    elapsed = time.perf_counter() - started
    payload = {
        "dataset": inputs["config"]["dataset"],
        "run": {
            "iteration": "V8O",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": elapsed,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "random_seed": 814,
            "deterministic_except_seeded_uncertainty": True,
        },
        "sources": inputs["config"]["official_facts"],
        "configuration": inputs["config"],
        "derived_geometry": {
            "bay_x_m": prep["bay_x_m"],
            "bay_y_m": prep["bay_y_m"],
        },
        "digitization": digitization,
        "kernel_identification": kernel,
        "cross_figure_dcr": dcr,
        "validation_checks": validation,
        "summary": {
            "bubble_outer_mae_gate_pass": bubble_mae_pass,
            "bubble_outer_maximum_gate_pass": bubble_max_pass,
            "cross_figure_dcr_mae_gate_pass": dcr_mae_pass,
            "cross_figure_dcr_maximum_gate_pass": dcr_max_pass,
            "column804_gate_pass": column804_pass,
            "parameter_boundary_flags": flags,
            "gate_passed": gate_passed,
            "gate_label": gate_label,
            "gate_explanation": gate_explanation,
            "gate_decision": gate_decision,
            "report_conclusion": report_conclusion,
            "interpretation": "V8O is a cross-figure emulator of selected NIST global-model outputs, not independent validation, an event probability, recovered ANSYS properties, or demolition evidence.",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(payload)
    render_plot(payload)
    print(
        json.dumps(
            {
                "gate_passed": gate_passed,
                "bubble_outer_mae_kip": kernel["outer_fold_metrics"]["mae"],
                "bubble_outer_max_error_kip": kernel["outer_fold_metrics"]["maximum_absolute_error"],
                "dcr_mae": dcr["metrics"]["mae"],
                "dcr_max_error": dcr["metrics"]["maximum_absolute_error"],
                "column804": dcr["column804"],
                "final_parameters": kernel["final_parameters"],
                "parameter_boundary_flags": flags,
                "legend_scale_factor_after": digitization["after_impact"]["legend_diagnostic"]["published_to_legend_raw_scale_factor"],
                "outputs": [str(OUT_DIGITIZATION), str(OUT_JSON), str(OUT_REPORT), str(OUT_PNG)],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
