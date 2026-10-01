"""WTC 1 V8P - bounded contour digitization and vertical state graph.

This script digitizes the discrete ANSYS contour images in NIST NCSTAR 1-6D
Figures 4-60 and 4-61.  It preserves the contour bins as intervals, constructs
an algebraically continuous vertical load-change state, and tests a graph
interpolator on three columns that are excluded from all parameter selection.

The resulting model is an emulator of selected official-model outputs.  It is
not a recovered ANSYS model, an event probability, or a collapse-mechanism test.
"""

from __future__ import annotations

import itertools
import json
import math
import platform
import statistics
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
CONFIG_PATH = V8 / "data" / "v8p_vertical_state_graph.json"
DIGITIZATION_PATH = V8 / "output" / "digitisation_wtc1_v8p_verticale.json"
RESULT_PATH = V8 / "output" / "resultats_wtc1_v8p_graphe_vertical.json"
REPORT_PATH = V8 / "output" / "rapport_wtc1_v8p_graphe_vertical.md"
PLOT_PATH = V8 / "output" / "synthese_wtc1_v8p_graphe_vertical.png"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs() -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    provenance = config["provenance"]
    return {
        "config": config,
        "pdf": ROOT / config["digitization"]["pdf"],
        "v8b": read_json(ROOT / provenance["v8b_results"]),
        "v8n": read_json(ROOT / provenance["v8n_configuration"]),
        "v8o_digitization": read_json(ROOT / provenance["v8o_digitization"]),
        "geometry": read_json(ROOT / provenance["core_geometry"]),
    }


def image_placements(page: Any) -> dict[str, list[float]]:
    placements: dict[str, list[float]] = {}

    def visit(operator: bytes, operands: list[Any], cm: list[float], tm: list[float]) -> None:
        del tm
        if operator == b"Do" and operands:
            name = str(operands[0]).lstrip("/")
            placements[name] = [float(value) for value in cm]

    page.extract_text(visitor_operand_before=visit)
    return placements


def horizontal_segments(page: Any) -> list[tuple[float, float, float, float]]:
    segments: list[tuple[float, float, float, float]] = []
    start: tuple[float, float] | None = None
    for operands, operator in page.get_contents().operations:
        if operator == b"m" and len(operands) >= 2:
            start = (float(operands[0]), float(operands[1]))
        elif operator == b"l" and start is not None and len(operands) >= 2:
            end = (float(operands[0]), float(operands[1]))
            segments.append((start[0], start[1], end[0], end[1]))
        elif operator in (b"S", b"s", b"f", b"F", b"B", b"b"):
            start = None
    return segments


def palette_index(pixel: tuple[int, int, int], palette: list[tuple[int, int, int]]) -> int | None:
    if pixel == (0, 0, 0):
        return None
    distances = [sum((int(pixel[i]) - color[i]) ** 2 for i in range(3)) for color in palette]
    index = int(np.argmin(distances))
    return index if distances[index] <= 9 else None


def x_clusters(image: Image.Image, palette: list[tuple[int, int, int]], gap: int, expected: int) -> list[dict[str, int]]:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    populated = sorted(
        {
            x
            for y in range(rgb.height)
            for x in range(rgb.width)
            if palette_index(pixels[x, y], palette) is not None
        }
    )
    for candidate_gap in dict.fromkeys([gap, 4, 6, 3, 7, 8, 9, 10]):
        groups: list[list[int]] = []
        for x in populated:
            if not groups or x - groups[-1][-1] > candidate_gap:
                groups.append([x])
            else:
                groups[-1].append(x)
        if len(groups) == expected:
            rows = []
            for group in groups:
                counts = Counter(
                    x
                    for x in group
                    for y in range(rgb.height)
                    if palette_index(pixels[x, y], palette) is not None
                )
                anchor = counts.most_common(1)[0][0]
                rows.append({"minimum": min(group), "maximum": max(group), "anchor": int(anchor)})
            return rows
    raise RuntimeError(f"Expected {expected} colored column paths, found incompatible x clusters")


def floor_page_positions(tick_y: list[float], floors: list[int], tick_floors: list[int]) -> dict[int, float]:
    if len(tick_y) != len(tick_floors):
        raise RuntimeError(f"Expected {len(tick_floors)} floor ticks, found {len(tick_y)}")
    pairs = sorted(zip(tick_floors, tick_y))
    output: dict[int, float] = {}
    for floor in floors:
        if floor in tick_floors:
            output[floor] = float(dict(pairs)[floor])
            continue
        lower = max(item for item in pairs if item[0] < floor)
        upper = min(item for item in pairs if item[0] > floor)
        fraction = (floor - lower[0]) / (upper[0] - lower[0])
        output[floor] = float(lower[1] + fraction * (upper[1] - lower[1]))
    return output


def sample_path(
    image: Image.Image,
    cluster: dict[str, int],
    row: float,
    palette: list[tuple[int, int, int]],
    x_padding: int,
    y_window: int,
) -> dict[str, Any]:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    x0 = max(0, cluster["minimum"] - x_padding)
    x1 = min(rgb.width - 1, cluster["maximum"] + x_padding)
    center = int(round(row))

    def collect(radius: int) -> list[int]:
        values: list[int] = []
        for y in range(max(0, center - radius), min(rgb.height - 1, center + radius) + 1):
            for x in range(x0, x1 + 1):
                index = palette_index(pixels[x, y], palette)
                if index is not None:
                    values.append(index)
        return values

    values = collect(y_window)
    expanded = False
    if not values:
        values = collect(max(5, 2 * y_window))
        expanded = True
    if not values:
        return {
            "status": "absent_displayed_segment",
            "palette_index": None,
            "palette_indices_observed": [],
            "sample_row_pixel": float(row),
            "expanded_search": expanded,
        }
    counts = Counter(values)
    mode = int(counts.most_common(1)[0][0])
    return {
        "status": "colored_segment",
        "palette_index": mode,
        "palette_indices_observed": sorted(set(int(value) for value in values)),
        "sample_row_pixel": float(row),
        "expanded_search": expanded,
    }


def compression_interval(levels_lb: list[float], indices: list[int]) -> tuple[float, float, float]:
    if not indices:
        return 0.0, 0.0, 0.0
    intervals = []
    for index in indices:
        first = -float(levels_lb[index]) / 1000.0
        second = -float(levels_lb[index + 1]) / 1000.0
        intervals.append((min(first, second), max(first, second)))
    low = min(row[0] for row in intervals)
    high = max(row[1] for row in intervals)
    mode = indices[0]
    mode_first = -float(levels_lb[mode]) / 1000.0
    mode_second = -float(levels_lb[mode + 1]) / 1000.0
    midpoint = 0.5 * (mode_first + mode_second)
    return float(low), float(high), float(midpoint)


def digitize_state(reader: PdfReader, inputs: dict[str, Any], state: str) -> dict[str, Any]:
    settings = inputs["config"]["digitization"]
    state_settings = settings["states"][state]
    page = reader.pages[int(state_settings["zero_based_page_index"])]
    placements = image_placements(page)
    image_files = {Path(item.name).stem: item.image.convert("RGB") for item in page.images}
    big = [
        (name, matrix)
        for name, matrix in placements.items()
        if abs(matrix[0]) > 75.0 and abs(matrix[3]) > 100.0 and name in image_files
    ]
    # Panels in the same visual row differ by a few tenths of a PDF point in
    # their y placement.  Bucket the y coordinate before sorting left-to-right
    # so those drafting offsets cannot swap the 700/800 or 900/1000 panels.
    big.sort(key=lambda item: (-round(item[1][5] / 20.0), item[1][4]))
    series_order = [int(value) for value in settings["series_by_panel_position"]]
    if len(big) != len(series_order):
        raise RuntimeError(f"Expected six structural panel images on {state}, found {len(big)}")
    palette = [tuple(int(value) for value in row) for row in settings["palette_low_to_high_force_rgb"]]
    segments = horizontal_segments(page)
    floors = [int(value) for value in settings["floors"]]
    tick_floors = [int(value) for value in settings["floor_tick_labels"]]
    rows: list[dict[str, Any]] = []
    panels: list[dict[str, Any]] = []

    for series, (name, matrix) in zip(series_order, big):
        image = image_files[name]
        columns = [int(value) for value in settings["columns_by_series_descending"][str(series)]]
        clusters = x_clusters(
            image,
            palette,
            int(settings["x_cluster_gap_pixels"]),
            len(columns),
        )
        x_end = matrix[4] + matrix[0]
        tick_y = sorted(
            {
                round(0.5 * (y0 + y1), 6)
                for x0, y0, x1, y1 in segments
                if x_end + 1.0 <= min(x0, x1) <= x_end + 12.0
                and 6.0 <= abs(x1 - x0) <= 9.0
                and abs(y1 - y0) <= 0.2
                and matrix[5] <= 0.5 * (y0 + y1) <= matrix[5] + matrix[3]
            }
        )
        page_y = floor_page_positions(tick_y, floors, tick_floors)
        levels = [float(value) for value in settings["contour_levels_lb"][state][str(series)]]
        if len(levels) != len(palette) + 1:
            raise RuntimeError(f"Contour-level count mismatch for {state} series {series}")

        for column, cluster in zip(columns, clusters):
            for floor in floors:
                pixel_row = (1.0 - (page_y[floor] - matrix[5]) / matrix[3]) * (image.height - 1)
                sampled = sample_path(
                    image,
                    cluster,
                    pixel_row,
                    palette,
                    int(settings["x_padding_pixels"]),
                    int(settings["y_window_pixels"]),
                )
                indices = sampled["palette_indices_observed"]
                if sampled["palette_index"] is not None:
                    mode = int(sampled["palette_index"])
                    indices_for_interval = sorted(set(indices + [mode]))
                    low, high, _ = compression_interval(levels, indices_for_interval)
                    _, _, midpoint = compression_interval(levels, [mode])
                else:
                    low, high, midpoint = 0.0, 0.0, 0.0
                rows.append(
                    {
                        "state": state,
                        "series": series,
                        "column": column,
                        "floor": floor,
                        "status": sampled["status"],
                        "palette_index": sampled["palette_index"],
                        "palette_indices_observed": indices,
                        "compression_low_kip": low,
                        "compression_high_kip": high,
                        "compression_midpoint_kip": midpoint,
                        "sample_row_pixel": sampled["sample_row_pixel"],
                        "path_x_anchor_pixel": cluster["anchor"],
                        "path_x_minimum_pixel": cluster["minimum"],
                        "path_x_maximum_pixel": cluster["maximum"],
                        "expanded_search": sampled["expanded_search"],
                    }
                )
        panels.append(
            {
                "series": series,
                "image_resource": name,
                "image_width_pixels": image.width,
                "image_height_pixels": image.height,
                "placement_matrix": matrix,
                "tick_page_y": tick_y,
                "floor_page_y": {str(key): value for key, value in page_y.items()},
                "x_clusters": clusters,
                "contour_levels_lb": levels,
            }
        )
    return {"state": state, "panels": panels, "rows": rows}


def interval_distance(value: float, low: float, high: float) -> float:
    if value < low:
        return low - value
    if value > high:
        return value - high
    return 0.0


def digitization_checks(inputs: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    config = inputs["config"]
    totals = config["official_core_totals_kip"]
    states = ("before_impact", "after_impact")
    floors = [int(value) for value in config["digitization"]["floors"]]
    aggregate: list[dict[str, Any]] = []
    for state in states:
        for floor in floors:
            selected = [row for row in rows if row["state"] == state and row["floor"] == floor]
            low = sum(float(row["compression_low_kip"]) for row in selected)
            high = sum(float(row["compression_high_kip"]) for row in selected)
            midpoint = sum(float(row["compression_midpoint_kip"]) for row in selected)
            official = float(totals[str(floor)][state])
            aggregate.append(
                {
                    "state": state,
                    "floor": floor,
                    "official_total_kip": official,
                    "digitized_low_sum_kip": low,
                    "digitized_high_sum_kip": high,
                    "digitized_midpoint_sum_kip": midpoint,
                    "official_inside_aggregate_interval": low <= official <= high,
                    "midpoint_error_kip": midpoint - official,
                }
            )

    v8o = {int(row["column"]): row for row in inputs["v8o_digitization"]["rows"]}
    floor98: list[dict[str, Any]] = []
    load_key = {"before_impact": "before_load_kip", "after_impact": "after_load_kip"}
    for state in states:
        for row in rows:
            if row["state"] != state or row["floor"] != 98:
                continue
            observed = float(v8o[int(row["column"])][load_key[state]])
            low = float(row["compression_low_kip"])
            high = float(row["compression_high_kip"])
            midpoint = float(row["compression_midpoint_kip"])
            floor98.append(
                {
                    "state": state,
                    "column": int(row["column"]),
                    "bubble_load_kip": observed,
                    "contour_low_kip": low,
                    "contour_high_kip": high,
                    "contour_midpoint_kip": midpoint,
                    "bubble_inside_contour_interval": low <= observed <= high,
                    "midpoint_error_kip": midpoint - observed,
                }
            )
    coverage = sum(row["bubble_inside_contour_interval"] for row in floor98) / len(floor98)
    midpoint_mae = statistics.mean(abs(float(row["midpoint_error_kip"])) for row in floor98)
    counts = {
        state: sum(1 for row in rows if row["state"] == state)
        for state in states
    }
    missing = {
        state: sum(1 for row in rows if row["state"] == state and row["status"] != "colored_segment")
        for state in states
    }
    return {
        "observation_counts": counts,
        "absent_displayed_segment_counts": missing,
        "aggregate_total_checks": aggregate,
        "all_official_totals_inside_aggregate_intervals": all(
            row["official_inside_aggregate_interval"] for row in aggregate
        ),
        "floor98_bubble_comparison": floor98,
        "floor98_bubble_interval_coverage": coverage,
        "floor98_bubble_midpoint_mae_kip": midpoint_mae,
    }


def write_digitization(inputs: dict[str, Any], states: list[dict[str, Any]], checks: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "method": "Direct extraction of PDF panel rasters and vector floor ticks; exact RGB palette classification; force retained as a contour interval.",
        "source": inputs["config"]["official_facts"],
        "assumption": inputs["config"]["digitization"]["missing_segment_interpretation"],
        "states": states,
        "rows": [row for state in states for row in state["rows"]],
        "checks": checks,
    }
    DIGITIZATION_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def prepare_graph(inputs: dict[str, Any], digitization: dict[str, Any]) -> dict[str, Any]:
    config = inputs["config"]
    floors = [int(value) for value in config["digitization"]["floors"]]
    coords = {
        int(row["id"]): np.array([float(row["x_m"]), float(row["y_m"])], dtype=float)
        for row in inputs["geometry"]["core_layout_reconstruction"]["columns"]
    }
    columns = sorted(coords)
    table = {
        (str(row["state"]), int(row["column"]), int(row["floor"])): row
        for row in digitization["rows"]
    }
    before = {
        (column, floor): float(table[("before_impact", column, floor)]["compression_midpoint_kip"])
        for column in columns
        for floor in floors
    }
    after = {
        (column, floor): float(table[("after_impact", column, floor)]["compression_midpoint_kip"])
        for column in columns
        for floor in floors
    }
    intervals = {
        (column, floor): (
            float(table[("after_impact", column, floor)]["compression_low_kip"]),
            float(table[("after_impact", column, floor)]["compression_high_kip"]),
        )
        for column in columns
        for floor in floors
    }
    delta = {(column, floor): after[(column, floor)] - before[(column, floor)] for column in columns for floor in floors}
    innovations: dict[tuple[int, int], float] = {}
    for column in columns:
        for floor in reversed(floors):
            innovations[(column, floor)] = (
                delta[(column, floor)]
                if floor == max(floors)
                else delta[(column, floor)] - delta[(column, floor + 1)]
            )
    totals = config["official_core_totals_kip"]
    total_delta = {
        floor: float(totals[str(floor)]["after_impact"]) - float(totals[str(floor)]["before_impact"])
        for floor in floors
    }
    mean_innovation = {
        floor: (
            total_delta[floor] if floor == max(floors) else total_delta[floor] - total_delta[floor + 1]
        ) / len(columns)
        for floor in floors
    }
    capacities: dict[tuple[int, int], float] = {}
    damaged_by_floor: dict[int, set[int]] = {}
    for floor in floors:
        source = inputs["v8b"]["floor_inputs"][str(floor)]
        capacities.update(
            {
                (int(column), floor): float(section["room_pn_kip_k1"])
                for column, section in source["sections"].items()
            }
        )
        damaged_by_floor[floor] = {int(value) for value in source["initial_removed"]}
    x_distances: list[float] = []
    rows_by_id: dict[int, list[int]] = {}
    for column in columns:
        rows_by_id.setdefault(column // 100, []).append(column)
    for row_columns in rows_by_id.values():
        ordered = sorted(row_columns, key=lambda value: coords[value][0])
        x_distances.extend(abs(float(coords[b][0] - coords[a][0])) for a, b in zip(ordered, ordered[1:]))
    y_values = sorted(set(round(float(value[1]), 6) for value in coords.values()))
    bay_y = statistics.median(b - a for a, b in zip(y_values, y_values[1:]))
    return {
        "floors": floors,
        "columns": columns,
        "coords": coords,
        "before": before,
        "after": after,
        "intervals": intervals,
        "delta": delta,
        "innovations": innovations,
        "mean_innovation": mean_innovation,
        "capacities": capacities,
        "damaged_by_floor": damaged_by_floor,
        "bay_x_m": float(statistics.median(x_distances)),
        "bay_y_m": float(bay_y),
    }


def parameter_cases(config: dict[str, Any]) -> list[dict[str, float]]:
    settings = config["vertical_state_graph"]
    keys = [
        "transfer_length_x_bays",
        "transfer_length_y_bays",
        "vertical_length_floors",
        "capacity_similarity_exponent",
    ]
    return [
        {key: float(value) for key, value in zip(keys, values)}
        for values in itertools.product(*(settings[key] for key in keys))
    ]


def predict_column(
    target: int,
    reference_columns: list[int],
    parameters: dict[str, float],
    graph: dict[str, Any],
) -> list[dict[str, Any]]:
    floors: list[int] = graph["floors"]
    lx = float(parameters["transfer_length_x_bays"]) * float(graph["bay_x_m"])
    ly = float(parameters["transfer_length_y_bays"]) * float(graph["bay_y_m"])
    lv = float(parameters["vertical_length_floors"])
    exponent = float(parameters["capacity_similarity_exponent"])
    predicted_u: dict[int, float] = {}
    for floor in floors:
        target_capacity = max(float(graph["capacities"][(target, floor)]), 1e-9)
        numerator = 0.0
        denominator = 0.0
        for reference in reference_columns:
            delta_xy = graph["coords"][reference] - graph["coords"][target]
            for reference_floor in floors:
                reference_capacity = max(float(graph["capacities"][(reference, reference_floor)]), 1e-9)
                capacity_distance = abs(math.log(reference_capacity / target_capacity))
                weight = math.exp(
                    -abs(float(delta_xy[0])) / lx
                    -abs(float(delta_xy[1])) / ly
                    -abs(reference_floor - floor) / lv
                    -exponent * capacity_distance
                )
                residual = float(graph["innovations"][(reference, reference_floor)]) - float(
                    graph["mean_innovation"][reference_floor]
                )
                numerator += weight * residual
                denominator += weight
        residual_prediction = numerator / denominator if denominator else 0.0
        predicted_u[floor] = float(graph["mean_innovation"][floor]) + residual_prediction

    running_delta = 0.0
    rows: list[dict[str, Any]] = []
    for floor in reversed(floors):
        running_delta += predicted_u[floor]
        predicted_after = float(graph["before"][(target, floor)]) + running_delta
        observed = float(graph["after"][(target, floor)])
        low, high = graph["intervals"][(target, floor)]
        rows.append(
            {
                "column": target,
                "floor": floor,
                "predicted_innovation_kip": predicted_u[floor],
                "predicted_delta_kip": running_delta,
                "predicted_after_kip": predicted_after,
                "observed_midpoint_kip": observed,
                "observed_low_kip": low,
                "observed_high_kip": high,
                "midpoint_error_kip": predicted_after - observed,
                "interval_distance_kip": interval_distance(predicted_after, low, high),
                "inside_observed_interval": low <= predicted_after <= high,
            }
        )
    rows.sort(key=lambda row: row["floor"])
    return rows


def prediction_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    midpoint_errors = [abs(float(row["midpoint_error_kip"])) for row in rows]
    interval_errors = [float(row["interval_distance_kip"]) for row in rows]
    return {
        "node_count": len(rows),
        "interval_coverage": sum(bool(row["inside_observed_interval"]) for row in rows) / len(rows),
        "interval_mae_kip": statistics.mean(interval_errors),
        "midpoint_mae_kip": statistics.mean(midpoint_errors),
        "midpoint_rmse_kip": math.sqrt(statistics.mean(value * value for value in midpoint_errors)),
        "midpoint_maximum_error_kip": max(midpoint_errors),
        "mean_bias_kip": statistics.mean(float(row["midpoint_error_kip"]) for row in rows),
    }


def fit_graph(inputs: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    config = inputs["config"]
    reserved = {int(value) for value in config["reserved_validation_columns"]}
    damaged = {int(value) for value in config["damaged_boundary_columns"]}
    training = sorted(set(graph["columns"]) - reserved - damaged)
    cases = parameter_cases(config)
    scored: list[dict[str, Any]] = []
    for parameters in cases:
        rows: list[dict[str, Any]] = []
        for target in training:
            references = sorted(damaged | (set(training) - {target}))
            rows.extend(predict_column(target, references, parameters, graph))
        metrics = prediction_metrics(rows)
        scored.append({"parameters": parameters, "metrics": metrics})
    scored.sort(
        key=lambda row: (
            float(row["metrics"]["interval_mae_kip"]),
            float(row["metrics"]["midpoint_mae_kip"]),
            float(row["metrics"]["midpoint_maximum_error_kip"]),
        )
    )
    best = scored[0]
    best_rows: list[dict[str, Any]] = []
    for target in training:
        references = sorted(damaged | (set(training) - {target}))
        best_rows.extend(predict_column(target, references, best["parameters"], graph))

    interval_limit = float(best["metrics"]["interval_mae_kip"]) + 5.0
    midpoint_limit = float(best["metrics"]["midpoint_mae_kip"]) * 1.05 + 5.0
    near = [
        row
        for row in scored
        if float(row["metrics"]["interval_mae_kip"]) <= interval_limit
        and float(row["metrics"]["midpoint_mae_kip"]) <= midpoint_limit
    ]
    return {
        "parameter_case_count": len(cases),
        "training_survivor_columns": training,
        "damaged_boundary_columns": sorted(damaged),
        "reserved_columns_excluded": sorted(reserved),
        "best_parameters": best["parameters"],
        "best_inner_metrics": best["metrics"],
        "best_inner_rows": best_rows,
        "near_optimal_count": len(near),
        "near_optimal": near,
        "top_parameter_cases": scored[:20],
    }


def validate_reserved(inputs: dict[str, Any], graph: dict[str, Any], fit: dict[str, Any]) -> dict[str, Any]:
    config = inputs["config"]
    reserved = [int(value) for value in config["reserved_validation_columns"]]
    damaged = {int(value) for value in config["damaged_boundary_columns"]}
    training = set(int(value) for value in fit["training_survivor_columns"])
    references = sorted(damaged | training)
    rows: list[dict[str, Any]] = []
    for target in reserved:
        rows.extend(predict_column(target, references, fit["best_parameters"], graph))
    metrics = prediction_metrics(rows)

    official_dcr = {
        int(key): float(value)
        for key, value in inputs["v8n"]["official_maximum_dcr_after_impact"].items()
    }
    dcr_rows: list[dict[str, Any]] = []
    for column in reserved:
        predicted_values = [
            float(row["predicted_after_kip"]) / float(graph["capacities"][(column, int(row["floor"]))])
            for row in rows
            if int(row["column"]) == column
        ]
        predicted = max(predicted_values)
        observed = official_dcr[column]
        dcr_rows.append(
            {
                "column": column,
                "official_maximum_dcr": observed,
                "predicted_maximum_dcr": predicted,
                "error": predicted - observed,
            }
        )
    dcr_max = max(abs(float(row["error"])) for row in dcr_rows)

    near_predictions: dict[tuple[int, int], list[float]] = {
        (column, floor): [] for column in reserved for floor in graph["floors"]
    }
    for candidate in fit["near_optimal"]:
        for column in reserved:
            for row in predict_column(column, references, candidate["parameters"], graph):
                near_predictions[(column, int(row["floor"]))].append(float(row["predicted_after_kip"]))
    spread_rows = [
        {
            "column": column,
            "floor": floor,
            "minimum_kip": min(values),
            "maximum_kip": max(values),
            "range_kip": max(values) - min(values),
        }
        for (column, floor), values in near_predictions.items()
        if values
    ]
    keys = list(fit["best_parameters"])
    parameter_ranges = {
        key: {
            "minimum": min(float(row["parameters"][key]) for row in fit["near_optimal"]),
            "maximum": max(float(row["parameters"][key]) for row in fit["near_optimal"]),
        }
        for key in keys
    }
    return {
        "rows": rows,
        "metrics": metrics,
        "dcr_rows": dcr_rows,
        "dcr_maximum_absolute_error": dcr_max,
        "near_optimal_holdout_spread": spread_rows,
        "maximum_near_optimal_holdout_range_kip": max(float(row["range_kip"]) for row in spread_rows),
        "near_optimal_parameter_ranges": parameter_ranges,
        "targets_used_for_parameter_selection": False,
    }


def vertical_reconstruction_error(graph: dict[str, Any]) -> float:
    maximum = 0.0
    for column in graph["columns"]:
        running = 0.0
        for floor in reversed(graph["floors"]):
            running += float(graph["innovations"][(column, floor)])
            maximum = max(maximum, abs(running - float(graph["delta"][(column, floor)])))
    return maximum


def boundary_flags(config: dict[str, Any], best: dict[str, float]) -> list[str]:
    settings = config["vertical_state_graph"]
    flags = []
    for key, value in best.items():
        grid = [float(item) for item in settings[key]]
        if math.isclose(value, min(grid), abs_tol=1e-12):
            flags.append(f"{key}=minimum")
        if math.isclose(value, max(grid), abs_tol=1e-12):
            flags.append(f"{key}=maximum")
    return flags


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def draw_scatter(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    rows: list[dict[str, Any]],
    title: str,
    x_label: str,
    y_label: str,
    maximum: float,
    colors: dict[int, tuple[int, int, int]],
) -> None:
    x, y, width, height = box
    navy = (32, 47, 67)
    grid = (207, 216, 226)
    draw.text((x + width // 2, y - 55), title, anchor="mm", font=font(24, True), fill=navy)
    for index in range(6):
        value = maximum * index / 5
        px = x + width * index / 5
        py = y + height - height * index / 5
        draw.line((px, y, px, y + height), fill=grid, width=1)
        draw.line((x, py, x + width, py), fill=grid, width=1)
        draw.text((px, y + height + 12), f"{value:.0f}", anchor="ma", font=font(14), fill=navy)
        draw.text((x - 12, py), f"{value:.0f}", anchor="rm", font=font(14), fill=navy)
    draw.rectangle((x, y, x + width, y + height), outline=navy, width=2)
    draw.line((x, y + height, x + width, y), fill=(42, 148, 89), width=3)
    for row in rows:
        observed = float(row["observed_midpoint_kip"])
        predicted = float(row["predicted_after_kip"])
        low = float(row["observed_low_kip"])
        high = float(row["observed_high_kip"])
        px = x + width * max(0.0, min(observed, maximum)) / maximum
        py = y + height - height * max(0.0, min(predicted, maximum)) / maximum
        lo = x + width * max(0.0, min(low, maximum)) / maximum
        hi = x + width * max(0.0, min(high, maximum)) / maximum
        color = colors.get(int(row["column"]), (48, 111, 184))
        draw.line((lo, py, hi, py), fill=color, width=2)
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=color, outline=(255, 255, 255), width=1)
    draw.text((x + width // 2, y + height + 50), x_label, anchor="mm", font=font(17, True), fill=navy)
    draw.text((x + 12, y + 12), y_label, anchor="la", font=font(15, True), fill=navy)


def render_plot(payload: dict[str, Any]) -> None:
    image = Image.new("RGB", (1900, 1180), "white")
    draw = ImageDraw.Draw(image)
    navy = (32, 47, 67)
    blue = (48, 111, 184)
    red = (198, 55, 55)
    draw.text((950, 48), "WTC 1 V8P - etats nodaux verticaux et controle reserve", anchor="mm", font=font(34, True), fill=navy)
    training_rows = payload["graph_identification"]["best_inner_rows"]
    reserved_rows = payload["reserved_validation"]["rows"]
    maximum = max(
        max(float(row["observed_high_kip"]) for row in training_rows + reserved_rows),
        max(float(row["predicted_after_kip"]) for row in training_rows + reserved_rows),
    )
    maximum = math.ceil(maximum / 250.0) * 250.0
    draw_scatter(
        draw,
        (130, 170, 720, 480),
        training_rows,
        "Validation interne par colonne entiere",
        "milieu de l'intervalle NIST (kip)",
        "prediction (kip)",
        maximum,
        {},
    )
    draw_scatter(
        draw,
        (1040, 170, 720, 480),
        reserved_rows,
        "Colonnes 705 / 804 / 605 jamais ajustees",
        "milieu de l'intervalle NIST (kip)",
        "prediction (kip)",
        maximum,
        {705: (39, 138, 95), 804: (222, 124, 35), 605: (156, 82, 183)},
    )
    digit = payload["digitization"]["checks"]
    fit = payload["graph_identification"]
    reserved = payload["reserved_validation"]
    cards = [
        ("Numerisation Floor 98", f"couverture {digit['floor98_bubble_interval_coverage']:.1%}", f"MAE milieux {digit['floor98_bubble_midpoint_mae_kip']:.0f} kip"),
        ("Validation reservee", f"couverture {reserved['metrics']['interval_coverage']:.1%}", f"MAE milieux {reserved['metrics']['midpoint_mae_kip']:.0f} kip"),
        ("DCR reserve", f"erreur max {reserved['dcr_maximum_absolute_error']:.3f}", "cibles non utilisees"),
        ("Identifiabilite", f"{fit['near_optimal_count']} cas quasi equivalents", f"dispersion max {reserved['maximum_near_optimal_holdout_range_kip']:.0f} kip"),
    ]
    for index, (title, main, sub) in enumerate(cards):
        x = 125 + index * 430
        draw.rounded_rectangle((x, 730, x + 380, 875), radius=16, fill=(244, 247, 250), outline=(210, 219, 229), width=2)
        draw.text((x + 18, 755), title, font=font(17, True), fill=navy)
        draw.text((x + 18, 800), main, font=font(25, True), fill=blue)
        draw.text((x + 18, 845), sub, font=font(14), fill=navy)
    summary = payload["summary"]
    fill = (230, 247, 237) if summary["gate_passed"] else (253, 232, 232)
    headline = (36, 130, 76) if summary["gate_passed"] else red
    draw.rounded_rectangle((125, 930, 1775, 1042), radius=18, fill=fill)
    draw.text((950, 968), summary["gate_label"], anchor="mm", font=font(29, True), fill=headline)
    draw.text((950, 1010), summary["gate_explanation"], anchor="mm", font=font(16), fill=navy)
    draw.text((950, 1125), "Interpolation de sorties NIST, pas validation independante de l'evenement reel.", anchor="mm", font=font(16, True), fill=red)
    image.save(PLOT_PATH)


def write_report(payload: dict[str, Any]) -> None:
    digit = payload["digitization"]["checks"]
    fit = payload["graph_identification"]
    reserved = payload["reserved_validation"]
    summary = payload["summary"]
    params = fit["best_parameters"]
    parameter_flags = ", ".join(summary["parameter_boundary_flags"]) or "aucune"
    per_column = []
    for column in (705, 804, 605):
        selected = [row for row in reserved["rows"] if int(row["column"]) == column]
        per_column.append(
            {
                "column": column,
                "coverage": sum(bool(row["inside_observed_interval"]) for row in selected) / len(selected),
                "mae": statistics.mean(abs(float(row["midpoint_error_kip"])) for row in selected),
                "bias": statistics.mean(float(row["midpoint_error_kip"]) for row in selected),
            }
        )
    lines = [
        "# WTC 1 - V8P : etats nodaux et graphe vertical",
        "",
        "## Resultat principal",
        "",
        summary["report_conclusion"],
        "",
        f"Les Figures 4-60 et 4-61 fournissent {digit['observation_counts']['before_impact']} etats avant impact et {digit['observation_counts']['after_impact']} etats apres impact. Chaque valeur reste un intervalle de contour; aucune fausse precision ponctuelle n'est introduite.",
        f"Le controle independant au niveau 98 avec la carte de bulles V8O place {digit['floor98_bubble_interval_coverage']:.1%} des charges dans l'intervalle de contour correspondant.",
        "",
        "## Faits officiels utilises",
        "",
        "- Figures 4-60 et 4-61 : contours de charge axiale le long des 47 lignes de poteaux du noyau avant et apres impact.",
        "- Table 4-20 : totaux de charge du noyau a chaque niveau 93-99.",
        "- Figure 4-69 : DCR axial maximal 93-99, utilise seulement apres le choix des parametres.",
        "",
        "## Controle de la numerisation",
        "",
        "| Etat | Segments absents affiches |",
        "|---|---:|",
        f"| Avant impact | {digit['absent_displayed_segment_counts']['before_impact']} |",
        f"| Apres impact | {digit['absent_displayed_segment_counts']['after_impact']} |",
        "",
        f"Les totaux officiels appartiennent a tous les intervalles agreges : **{'oui' if digit['all_official_totals_inside_aggregate_intervals'] else 'non'}**.",
        "",
        "## Graphe vertical",
        "",
        "La variation de charge de chaque poteau est decomposee en innovations entre niveaux consecutifs. La sommation descendante reconstruit exactement l'etat du poteau et impose la continuite verticale par construction.",
        "",
        f"- Longueur est-ouest : **{params['transfer_length_x_bays']:.2f} travee(s)**.",
        f"- Longueur nord-sud : **{params['transfer_length_y_bays']:.2f} travee(s)**.",
        f"- Longueur verticale : **{params['vertical_length_floors']:.2f} etage(s)**.",
        f"- Exposant de similarite de capacite : **{params['capacity_similarity_exponent']:.2f}**.",
        f"- Jeux de parametres testes : **{fit['parameter_case_count']}**.",
        f"- Cas quasi equivalents : **{fit['near_optimal_count']}**.",
        f"- Parametres en butee de grille : **{parameter_flags}**.",
        "",
        "## Validation reservee 705 / 804 / 605",
        "",
        f"- Couverture des 21 intervalles : **{reserved['metrics']['interval_coverage']:.1%}**.",
        f"- Distance moyenne hors intervalle : **{reserved['metrics']['interval_mae_kip']:.1f} kip**.",
        f"- MAE par rapport aux milieux de classe : **{reserved['metrics']['midpoint_mae_kip']:.1f} kip**.",
        f"- Erreur ponctuelle maximale : **{reserved['metrics']['midpoint_maximum_error_kip']:.1f} kip**.",
        f"- Dispersion maximale des predictions quasi equivalentes : **{reserved['maximum_near_optimal_holdout_range_kip']:.1f} kip**.",
        "",
        "| Poteau | Couverture des 7 intervalles | MAE milieu (kip) | Biais (kip) |",
        "|---:|---:|---:|---:|",
    ]
    for row in per_column:
        lines.append(f"| {row['column']} | {row['coverage']:.1%} | {row['mae']:.1f} | {row['bias']:+.1f} |")
    lines.extend(
        [
        "",
        "| Poteau | DCR officiel | DCR predit | Erreur |",
        "|---:|---:|---:|---:|",
        ]
    )
    for row in reserved["dcr_rows"]:
        lines.append(
            f"| {row['column']} | {row['official_maximum_dcr']:.2f} | {row['predicted_maximum_dcr']:.3f} | {row['error']:+.3f} |"
        )
    lines.extend(
        [
            "",
            "## Hypotheses propres a V8P",
            "",
            "- Un pixel couleur a un niveau donne represente seulement l'intervalle de sa classe ANSYS.",
            "- L'absence locale de segment colore est convertie en charge nulle et conservee comme drapeau distinct.",
            "- Le champ d'innovation est interpole; aucune rigidite de dalle, loi d'assemblage ou rotation nodale reelle n'est identifiee.",
            "- Les poteaux endommages restent des conditions de bord connues. Les trois poteaux reserves ne participent jamais au choix des parametres.",
            "",
            "## Limites et identifiabilite",
            "",
            f"- {fit['near_optimal_count']} combinaisons restent quasi equivalentes sur les seules donnees d'apprentissage.",
            "- Les contours sont larges et les panneaux de chaque serie utilisent une echelle differente; les milieux de classe ne sont pas des mesures exactes.",
            "- Toutes les cibles proviennent du meme modele global NIST. Une bonne prediction est une coherence entre sorties, pas une validation independante.",
            "- Aucun resultat ne constitue une probabilite de l'evenement ou un test distinctif d'explosifs.",
            "",
            "## Decision du gate",
            "",
            summary["gate_decision"],
            "",
            f"Temps d'execution : {payload['run']['elapsed_seconds']:.2f} s.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    reader = PdfReader(inputs["pdf"])
    states = [digitize_state(reader, inputs, state) for state in ("before_impact", "after_impact")]
    flat_rows = [row for state in states for row in state["rows"]]
    checks = digitization_checks(inputs, flat_rows)
    digitization = write_digitization(inputs, states, checks)
    graph = prepare_graph(inputs, digitization)
    fit = fit_graph(inputs, graph)
    reserved = validate_reserved(inputs, graph, fit)
    reconstruction_error = vertical_reconstruction_error(graph)
    config = inputs["config"]
    gates = config["acceptance_gates"]
    flags = boundary_flags(config, fit["best_parameters"])
    validation_checks = {
        "observation_count_before": checks["observation_counts"]["before_impact"] == int(gates["digitized_observation_count_per_state"]),
        "observation_count_after": checks["observation_counts"]["after_impact"] == int(gates["digitized_observation_count_per_state"]),
        "official_totals_inside_aggregate_intervals": checks["all_official_totals_inside_aggregate_intervals"],
        "floor98_bubble_coverage": checks["floor98_bubble_interval_coverage"] >= float(gates["floor98_bubble_interval_coverage_min"]),
        "reserved_targets_not_used_for_selection": not reserved["targets_used_for_parameter_selection"],
        "reserved_interval_coverage": reserved["metrics"]["interval_coverage"] >= float(gates["reserved_interval_coverage_min"]),
        "reserved_interval_mae": reserved["metrics"]["interval_mae_kip"] <= float(gates["reserved_interval_mae_kip_max"]),
        "reserved_midpoint_mae": reserved["metrics"]["midpoint_mae_kip"] <= float(gates["reserved_midpoint_mae_kip_max"]),
        "reserved_midpoint_maximum_error": reserved["metrics"]["midpoint_maximum_error_kip"] <= float(gates["reserved_midpoint_maximum_error_kip_max"]),
        "reserved_dcr_maximum_error": reserved["dcr_maximum_absolute_error"] <= float(gates["reserved_dcr_maximum_error_max"]),
        "vertical_reconstruction": reconstruction_error <= float(gates["vertical_reconstruction_error_kip_max"]),
    }
    gate_passed = all(validation_checks.values())
    if gate_passed:
        gate_label = "GATE D'INTERPOLATION FROIDE VALIDE"
        gate_explanation = "Les seuils reserves passent; cela valide seulement l'emulateur borne des sorties NIST."
        gate_decision = "**VALIDE COMME EMULATEUR BORNE.** Les controles reserves passent, mais aucune propriete physique manquante n'est identifiee."
        report_conclusion = "V8P exploite les contours verticaux et predit les trois colonnes reservees dans les seuils declares. Le resultat valide uniquement une interpolation coherente des sorties froides NIST."
    else:
        failed = [key for key, value in validation_checks.items() if not value]
        gate_label = "GATE VERTICAL FROID NON VALIDE"
        gate_explanation = "Au moins un controle reserve ou de numerisation echoue; aucune etape thermique ou Blender n'est autorisee."
        gate_decision = "**NON VALIDE.** Le graphe vertical ne satisfait pas tous les seuils reserves ou les controles de numerisation."
        report_conclusion = "V8P ajoute les donnees nodales verticales absentes des iterations precedentes, mais le chemin froid reste non valide sur les criteres declares."
    elapsed = time.perf_counter() - started
    payload = {
        "dataset": config["dataset"],
        "run": {
            "iteration": "V8P",
            "timestamp_local": datetime.now().astimezone().isoformat(),
            "elapsed_seconds": elapsed,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "deterministic": True,
        },
        "sources": config["official_facts"],
        "configuration": config,
        "digitization": {
            "path": str(DIGITIZATION_PATH.relative_to(ROOT)),
            "checks": checks,
        },
        "derived_graph": {
            "bay_x_m": graph["bay_x_m"],
            "bay_y_m": graph["bay_y_m"],
            "vertical_reconstruction_maximum_error_kip": reconstruction_error,
            "official_mean_innovation_kip": {str(key): value for key, value in graph["mean_innovation"].items()},
        },
        "graph_identification": fit,
        "reserved_validation": reserved,
        "validation_checks": validation_checks,
        "summary": {
            "parameter_boundary_flags": flags,
            "gate_passed": gate_passed,
            "gate_label": gate_label,
            "gate_explanation": gate_explanation,
            "gate_decision": gate_decision,
            "report_conclusion": report_conclusion,
            "failed_checks": [key for key, value in validation_checks.items() if not value],
            "interpretation": "Bounded cross-output NIST emulator only; not an independent structural solution, event probability, or demolition test.",
        },
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    render_plot(payload)
    write_report(payload)
    print(json.dumps({
        "gate_passed": gate_passed,
        "failed_checks": payload["summary"]["failed_checks"],
        "digitized_counts": checks["observation_counts"],
        "floor98_coverage": checks["floor98_bubble_interval_coverage"],
        "best_parameters": fit["best_parameters"],
        "near_optimal_count": fit["near_optimal_count"],
        "reserved_metrics": reserved["metrics"],
        "reserved_dcr_max_error": reserved["dcr_maximum_absolute_error"],
    }, indent=2))


if __name__ == "__main__":
    main()
