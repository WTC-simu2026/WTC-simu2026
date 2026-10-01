"""WTC 1 V8N - inverse-calibrated cold core redistribution surrogate.

The iteration calibrates only against published NIST global-model outputs.
It deliberately reserves floors and columns from fitting so that interpolation
and spatial generalization errors are visible.  It is not an ANSYS recreation
and it does not authorize thermal, collapse, or Blender dynamics.
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
CONFIG = V8 / "data" / "v8n_inverse_core_redistribution.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8n_redistribution_inverse_froide.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8n_redistribution_inverse_froide.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8n_redistribution_inverse_froide.png"


def load_inputs() -> dict[str, object]:
    return {
        "config": json.loads(CONFIG.read_text(encoding="utf-8")),
        "v8b": json.loads(V8B_RESULT.read_text(encoding="utf-8")),
        "parameters": json.loads(PARAMETERS.read_text(encoding="utf-8")),
    }


def logistic(x: np.ndarray, lower: float, upper: float, midpoint: float, scale: float) -> np.ndarray:
    shape = 1.0 / (1.0 + np.exp(-(x - midpoint) / scale))
    return lower + (upper - lower) * shape


def fit_logistic(
    x: np.ndarray, y: np.ndarray, settings: dict[str, object]
) -> dict[str, float]:
    best: dict[str, float] | None = None
    midpoint_values = np.arange(
        float(settings["midpoint_min_floor"]),
        float(settings["midpoint_max_floor"]) + 0.5 * float(settings["midpoint_step"]),
        float(settings["midpoint_step"]),
    )
    scale_values = np.arange(
        float(settings["scale_min_floors"]),
        float(settings["scale_max_floors"]) + 0.5 * float(settings["scale_step"]),
        float(settings["scale_step"]),
    )
    for midpoint in midpoint_values:
        for scale in scale_values:
            shape = 1.0 / (1.0 + np.exp(-(x - midpoint) / scale))
            design = np.column_stack((np.ones_like(shape), shape))
            lower, span = np.linalg.lstsq(design, y, rcond=None)[0]
            upper = lower + span
            if upper <= lower:
                continue
            predicted = lower + span * shape
            rmse = float(np.sqrt(np.mean((predicted - y) ** 2)))
            candidate = {
                "lower_kip": float(lower),
                "upper_kip": float(upper),
                "midpoint_floor": float(midpoint),
                "scale_floors": float(scale),
                "training_rmse_kip": rmse,
            }
            if best is None or (
                rmse,
                abs(float(scale)),
                abs(float(midpoint) - 96.0),
            ) < (
                best["training_rmse_kip"],
                abs(best["scale_floors"]),
                abs(best["midpoint_floor"] - 96.0),
            ):
                best = candidate
    if best is None:
        raise RuntimeError("No monotonic logistic fit found")
    return best


def floor_generalization(config: dict[str, object]) -> dict[str, object]:
    totals = config["official_core_totals_kip"]
    floors = np.array([int(value) for value in config["calibration"]["floor_generalization"]["floors"]], dtype=float)
    deltas = np.array(
        [
            float(totals[str(int(floor))]["after_impact"])
            - float(totals[str(int(floor))]["before_impact"])
            for floor in floors
        ],
        dtype=float,
    )
    settings = config["calibration"]["floor_generalization"]
    heldout_rows: list[dict[str, float]] = []
    for index, heldout_floor in enumerate(floors):
        mask = np.ones(len(floors), dtype=bool)
        mask[index] = False
        fit = fit_logistic(floors[mask], deltas[mask], settings)
        prediction = float(
            logistic(
                np.array([heldout_floor]),
                fit["lower_kip"],
                fit["upper_kip"],
                fit["midpoint_floor"],
                fit["scale_floors"],
            )[0]
        )
        heldout_rows.append(
            {
                "floor": int(heldout_floor),
                "observed_delta_kip": float(deltas[index]),
                "predicted_delta_kip": prediction,
                "error_kip": prediction - float(deltas[index]),
                "absolute_error_kip": abs(prediction - float(deltas[index])),
            }
        )
    full_fit = fit_logistic(floors, deltas, settings)
    fitted = logistic(
        floors,
        full_fit["lower_kip"],
        full_fit["upper_kip"],
        full_fit["midpoint_floor"],
        full_fit["scale_floors"],
    )
    errors = [row["absolute_error_kip"] for row in heldout_rows]
    return {
        "method": settings["method"],
        "official_rows": [
            {
                "floor": int(floor),
                "before_impact_kip": float(totals[str(int(floor))]["before_impact"]),
                "after_impact_kip": float(totals[str(int(floor))]["after_impact"]),
                "delta_kip": float(delta),
                "full_fit_delta_kip": float(fit_value),
            }
            for floor, delta, fit_value in zip(floors, deltas, fitted)
        ],
        "leave_one_floor_out": heldout_rows,
        "lofo_mae_kip": float(np.mean(errors)),
        "lofo_rmse_kip": float(np.sqrt(np.mean(np.square(errors)))),
        "lofo_maximum_absolute_error_kip": float(max(errors)),
        "full_fit": full_fit,
    }


def prepared(inputs: dict[str, object]) -> dict[str, object]:
    config = inputs["config"]
    coords = {
        int(row["id"]): np.array([float(row["x_m"]), float(row["y_m"])], dtype=float)
        for row in inputs["parameters"]["core_layout_reconstruction"]["columns"]
    }
    floors = sorted(int(value) for value in config["official_core_totals_kip"])
    capacities: dict[int, dict[int, float]] = {}
    removed: dict[int, set[int]] = {}
    for floor in floors:
        source = inputs["v8b"]["floor_inputs"][str(floor)]
        capacities[floor] = {
            int(column): float(section["room_pn_kip_k1"])
            for column, section in source["sections"].items()
        }
        removed[floor] = {int(value) for value in source["initial_removed"]}
    columns = sorted(coords)
    nearest = []
    for column in columns:
        distances = [
            float(np.linalg.norm(coords[column] - coords[other]))
            for other in columns
            if other != column
        ]
        nearest.append(min(distances))
    bay_m = float(np.median(nearest))
    max_abs_y = max(abs(float(coord[1])) for coord in coords.values())
    return {
        "floors": floors,
        "columns": columns,
        "coords": coords,
        "capacities": capacities,
        "removed": removed,
        "reference_bay_m": bay_m,
        "max_abs_y_m": max_abs_y,
    }


def metric_rows(rows: list[dict[str, float]]) -> dict[str, float]:
    errors = np.array([row["error"] for row in rows], dtype=float)
    return {
        "count": int(len(rows)),
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "maximum_absolute_error": float(np.max(np.abs(errors))),
        "mean_bias": float(np.mean(errors)),
    }


def redistribute_floor(
    config: dict[str, object],
    prep: dict[str, object],
    floor: int,
    after_total_kip: float,
    transfer_length_bays: float,
    capacity_exponent: float,
    global_mixing: float,
    north_bias: float,
) -> dict[str, object]:
    columns = prep["columns"]
    capacities = prep["capacities"][floor]
    removed = prep["removed"][floor]
    survivors = [column for column in columns if column not in removed]
    before_total = float(config["official_core_totals_kip"][str(floor)]["before_impact"])
    pre_dcr = {int(key): float(value) for key, value in config["official_maximum_dcr_before_impact"].items()}
    raw = {column: pre_dcr[column] * capacities[column] for column in columns}
    raw_sum = sum(raw.values())
    baseline = {column: before_total * raw[column] / raw_sum for column in columns}
    loads = {column: baseline[column] for column in survivors}
    bay_m = float(prep["reference_bay_m"])
    max_abs_y = float(prep["max_abs_y_m"])

    def capacity_tilt_weight(column: int) -> float:
        y_norm = float(prep["coords"][column][1]) / max_abs_y
        return capacities[column] ** capacity_exponent * math.exp(north_bias * y_norm)

    for source in sorted(removed):
        weights = {}
        for target in survivors:
            distance_bays = float(np.linalg.norm(prep["coords"][source] - prep["coords"][target])) / bay_m
            weights[target] = capacity_tilt_weight(target) * math.exp(
                -distance_bays / transfer_length_bays
            )
        denominator = sum(weights.values())
        for target in survivors:
            loads[target] += baseline[source] * weights[target] / denominator

    total_adjustment = after_total_kip - before_total
    global_weights = {column: capacity_tilt_weight(column) for column in survivors}
    global_weight_sum = sum(global_weights.values())
    for column in survivors:
        loads[column] += total_adjustment * global_weights[column] / global_weight_sum

    fully_mixed = {
        column: after_total_kip * global_weights[column] / global_weight_sum
        for column in survivors
    }
    loads = {
        column: (1.0 - global_mixing) * loads[column]
        + global_mixing * fully_mixed[column]
        for column in survivors
    }
    return {
        "floor": floor,
        "removed_columns": sorted(removed),
        "before_total_kip": before_total,
        "prescribed_after_total_kip": after_total_kip,
        "calculated_after_total_kip": float(sum(loads.values())),
        "column_loads_kip": {str(column): float(loads[column]) for column in survivors},
        "column_dcr": {
            str(column): float(loads[column] / capacities[column]) for column in survivors
        },
    }


def spatial_prediction(
    config: dict[str, object],
    prep: dict[str, object],
    floor_fit: dict[str, float],
    transfer_length_bays: float,
    capacity_exponent: float,
    global_mixing: float,
    north_bias: float,
) -> dict[str, object]:
    floor_rows = []
    maxima: dict[int, float] = {column: -math.inf for column in prep["columns"]}
    governing_floor: dict[int, int | None] = {column: None for column in prep["columns"]}
    for floor in prep["floors"]:
        predicted_delta = float(
            logistic(
                np.array([float(floor)]),
                floor_fit["lower_kip"],
                floor_fit["upper_kip"],
                floor_fit["midpoint_floor"],
                floor_fit["scale_floors"],
            )[0]
        )
        before_total = float(config["official_core_totals_kip"][str(floor)]["before_impact"])
        row = redistribute_floor(
            config,
            prep,
            floor,
            before_total + predicted_delta,
            transfer_length_bays,
            capacity_exponent,
            global_mixing,
            north_bias,
        )
        floor_rows.append(row)
        for column_text, dcr in row["column_dcr"].items():
            column = int(column_text)
            if float(dcr) > maxima[column]:
                maxima[column] = float(dcr)
                governing_floor[column] = floor
    return {
        "floor_rows": floor_rows,
        "maximum_dcr": {
            str(column): float(value)
            for column, value in maxima.items()
            if math.isfinite(value)
        },
        "governing_floor": {
            str(column): floor
            for column, floor in governing_floor.items()
            if floor is not None
        },
    }


def spatial_calibration(
    config: dict[str, object], prep: dict[str, object], floor_result: dict[str, object]
) -> dict[str, object]:
    settings = config["calibration"]["spatial_generalization"]
    targets = {int(key): float(value) for key, value in config["official_maximum_dcr_after_impact"].items()}
    holdout = {int(value) for value in settings["holdout_columns"]}
    training = sorted(set(targets) - holdout)
    best: dict[str, object] | None = None
    case_count = 0
    for length in settings["transfer_length_bays"]:
        for exponent in settings["capacity_bias_exponent"]:
            for mixing in settings["global_mixing_fraction"]:
                for bias in settings["north_bias"]:
                    case_count += 1
                    prediction = spatial_prediction(
                        config,
                        prep,
                        floor_result["full_fit"],
                        float(length),
                        float(exponent),
                        float(mixing),
                        float(bias),
                    )
                    rows = [
                        {
                            "column": column,
                            "observed": targets[column],
                            "predicted": float(prediction["maximum_dcr"][str(column)]),
                            "error": float(prediction["maximum_dcr"][str(column)]) - targets[column],
                        }
                        for column in training
                    ]
                    metrics = metric_rows(rows)
                    score = (
                        metrics["rmse"],
                        metrics["mae"],
                        float(mixing),
                        float(length),
                    )
                    if best is None or score < best["score"]:
                        best = {
                            "score": score,
                            "parameters": {
                                "transfer_length_bays": float(length),
                                "capacity_bias_exponent": float(exponent),
                                "global_mixing_fraction": float(mixing),
                                "north_bias": float(bias),
                            },
                            "prediction": prediction,
                            "training_rows": rows,
                            "training_metrics": metrics,
                        }
    if best is None:
        raise RuntimeError("Spatial calibration produced no case")
    prediction = best["prediction"]
    holdout_rows = [
        {
            "column": column,
            "observed": targets[column],
            "predicted": float(prediction["maximum_dcr"][str(column)]),
            "error": float(prediction["maximum_dcr"][str(column)]) - targets[column],
            "governing_floor": int(prediction["governing_floor"][str(column)]),
        }
        for column in sorted(holdout)
    ]
    training_rows = []
    for row in best["training_rows"]:
        training_rows.append(
            {
                **row,
                "governing_floor": int(prediction["governing_floor"][str(row["column"])]),
            }
        )
    return {
        "method": settings["method"],
        "parameter_case_count": case_count,
        "best_parameters": best["parameters"],
        "training_columns": training,
        "holdout_columns": sorted(holdout),
        "training_rows": training_rows,
        "holdout_rows": holdout_rows,
        "training_metrics": best["training_metrics"],
        "holdout_metrics": metric_rows(holdout_rows),
        "prediction": prediction,
    }


def preimpact_construction_check(
    config: dict[str, object], prep: dict[str, object]
) -> dict[str, object]:
    official = {int(key): float(value) for key, value in config["official_maximum_dcr_before_impact"].items()}
    predicted = {column: -math.inf for column in prep["columns"]}
    governing = {column: None for column in prep["columns"]}
    for floor in prep["floors"]:
        capacities = prep["capacities"][floor]
        total = float(config["official_core_totals_kip"][str(floor)]["before_impact"])
        raw = {column: official[column] * capacities[column] for column in prep["columns"]}
        scale = total / sum(raw.values())
        for column in prep["columns"]:
            dcr = scale * raw[column] / capacities[column]
            if dcr > predicted[column]:
                predicted[column] = dcr
                governing[column] = floor
    rows = [
        {
            "column": column,
            "observed": official[column],
            "predicted": float(predicted[column]),
            "error": float(predicted[column] - official[column]),
            "governing_floor": int(governing[column]),
        }
        for column in prep["columns"]
    ]
    return {
        "status": "IN_SAMPLE_PRIOR_CONSTRUCTION_CHECK_NOT_VALIDATION",
        "rows": rows,
        "metrics": metric_rows(rows),
    }


def validate(
    config: dict[str, object], prep: dict[str, object], floor_result: dict[str, object], spatial: dict[str, object]
) -> dict[str, bool]:
    targets = {int(key) for key in config["official_maximum_dcr_after_impact"]}
    damaged = {int(value) for value in config["official_severed_or_heavily_damaged_columns"]}
    holdout = set(spatial["holdout_columns"])
    checks = {
        "core_column_count_is_47": len(prep["columns"]) == 47,
        "official_postimpact_dcr_count_is_38": len(targets) == 38,
        "damaged_plus_target_count_is_47": len(targets | damaged) == 47 and not (targets & damaged),
        "holdout_declared_and_not_damaged": bool(holdout) and holdout <= targets,
        "seven_floor_lofo_predictions_exist": len(floor_result["leave_one_floor_out"]) == 7,
        "spatial_parameter_count_matches_grid": spatial["parameter_case_count"] == math.prod(
            len(config["calibration"]["spatial_generalization"][key])
            for key in (
                "transfer_length_bays",
                "capacity_bias_exponent",
                "global_mixing_fraction",
                "north_bias",
            )
        ),
        "all_floor_totals_conserved": all(
            math.isclose(
                float(row["prescribed_after_total_kip"]),
                float(row["calculated_after_total_kip"]),
                rel_tol=0.0,
                abs_tol=1e-6,
            )
            for row in spatial["prediction"]["floor_rows"]
        ),
        "all_predictions_finite": all(
            math.isfinite(float(row["predicted"]))
            for row in spatial["training_rows"] + spatial["holdout_rows"]
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"V8N validation failed: {checks}")
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
    blue = (54, 112, 183)
    orange = (223, 132, 35)
    green = (44, 145, 90)
    red = (190, 57, 57)
    grey = (220, 224, 230)
    draw.text((950, 52), "WTC 1 V8N - redistribution froide calibree avec tests reserves", anchor="mm", font=font(34, True), fill=navy)

    # Floor delta and leave-one-out predictions.
    x0, y0, w, h = 125, 185, 760, 500
    draw.text((x0 + w / 2, y0 - 62), "Changement de charge totale du noyau", anchor="mm", font=font(24, True), fill=navy)
    ymin, ymax = -800.0, 650.0
    for tick in [-600, -300, 0, 300, 600]:
        y = y0 + h - (tick - ymin) / (ymax - ymin) * h
        draw.line((x0, y, x0 + w, y), fill=grey, width=1)
        draw.text((x0 - 12, y), str(tick), anchor="rm", font=font(15), fill=navy)
    draw.rectangle((x0, y0, x0 + w, y0 + h), outline=navy, width=2)
    official = payload["floor_generalization"]["official_rows"]
    lofo = {row["floor"]: row for row in payload["floor_generalization"]["leave_one_floor_out"]}
    official_points = []
    fit_points = []
    for row in official:
        x = x0 + (row["floor"] - 93) / 6 * w
        official_y = y0 + h - (row["delta_kip"] - ymin) / (ymax - ymin) * h
        fit_y = y0 + h - (row["full_fit_delta_kip"] - ymin) / (ymax - ymin) * h
        official_points.append((x, official_y))
        fit_points.append((x, fit_y))
        draw.ellipse((x - 7, official_y - 7, x + 7, official_y + 7), fill=navy)
        held = lofo[row["floor"]]
        held_y = y0 + h - (held["predicted_delta_kip"] - ymin) / (ymax - ymin) * h
        draw.rectangle((x - 6, held_y - 6, x + 6, held_y + 6), outline=orange, width=3)
        draw.text((x, y0 + h + 14), str(row["floor"]), anchor="ma", font=font(15), fill=navy)
    draw.line(official_points, fill=navy, width=3)
    draw.line(fit_points, fill=blue, width=4)
    draw.text((x0 + w / 2, y0 + h + 52), "etage", anchor="mm", font=font(17, True), fill=navy)
    draw.text((x0 + 10, y0 + 10), "delta (kip)", anchor="la", font=font(15, True), fill=navy)
    draw.line((x0 + 25, y0 - 27, x0 + 65, y0 - 27), fill=blue, width=4)
    draw.text((x0 + 75, y0 - 27), "ajustement complet", anchor="lm", font=font(14), fill=navy)
    draw.rectangle((x0 + 260, y0 - 34, x0 + 272, y0 - 22), outline=orange, width=3)
    draw.text((x0 + 282, y0 - 27), "prediction etage exclu", anchor="lm", font=font(14), fill=navy)

    # DCR scatter.
    sx, sy, sw, sh = 1050, 185, 660, 500
    draw.text((sx + sw / 2, sy - 62), "DCR poteaux : officiel vs surrogate", anchor="mm", font=font(24, True), fill=navy)
    vmin, vmax = 0.25, 1.45
    for tick in [0.4, 0.6, 0.8, 1.0, 1.2, 1.4]:
        px = sx + (tick - vmin) / (vmax - vmin) * sw
        py = sy + sh - (tick - vmin) / (vmax - vmin) * sh
        draw.line((px, sy, px, sy + sh), fill=grey, width=1)
        draw.line((sx, py, sx + sw, py), fill=grey, width=1)
        draw.text((px, sy + sh + 12), f"{tick:.1f}", anchor="ma", font=font(14), fill=navy)
        draw.text((sx - 12, py), f"{tick:.1f}", anchor="rm", font=font(14), fill=navy)
    draw.rectangle((sx, sy, sx + sw, sy + sh), outline=navy, width=2)
    draw.line((sx, sy + sh, sx + sw, sy), fill=green, width=3)
    for row in payload["spatial_calibration"]["training_rows"]:
        px = sx + (row["observed"] - vmin) / (vmax - vmin) * sw
        py = sy + sh - (row["predicted"] - vmin) / (vmax - vmin) * sh
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=blue)
    for row in payload["spatial_calibration"]["holdout_rows"]:
        px = sx + (row["observed"] - vmin) / (vmax - vmin) * sw
        py = sy + sh - (row["predicted"] - vmin) / (vmax - vmin) * sh
        draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=orange, outline=navy, width=2)
        if row["column"] in (605, 804):
            draw.text((px + 10, py - 8), str(row["column"]), font=font(13, True), fill=red)
    draw.text((sx + sw / 2, sy + sh + 52), "DCR officiel", anchor="mm", font=font(17, True), fill=navy)
    draw.text((sx + 10, sy + 10), "DCR predit", anchor="la", font=font(15, True), fill=navy)
    draw.ellipse((sx + 25, sy - 33, sx + 35, sy - 23), fill=blue)
    draw.text((sx + 45, sy - 28), "calibration", anchor="lm", font=font(14), fill=navy)
    draw.ellipse((sx + 170, sy - 36, sx + 186, sy - 20), fill=orange, outline=navy, width=2)
    draw.text((sx + 198, sy - 28), "poteaux reserves", anchor="lm", font=font(14), fill=navy)

    floor_metrics = payload["floor_generalization"]
    spatial = payload["spatial_calibration"]
    parameters = spatial["best_parameters"]
    cards = [
        ("Etages exclus un par un", f"MAE {floor_metrics['lofo_mae_kip']:.0f} kip", f"erreur max {floor_metrics['lofo_maximum_absolute_error_kip']:.0f} kip"),
        ("Poteaux reserves", f"MAE DCR {spatial['holdout_metrics']['mae']:.3f}", f"erreur max {spatial['holdout_metrics']['maximum_absolute_error']:.3f}"),
        ("Transfert equivalent", f"{parameters['transfer_length_bays']:.2f} travees", f"melange global {parameters['global_mixing_fraction']:.2f}"),
        ("Biais de redistribution", f"capacite^{parameters['capacity_bias_exponent']:.2f}", f"biais nord {parameters['north_bias']:+.2f}"),
    ]
    for index, (title, value, note) in enumerate(cards):
        cx = 125 + index * 430
        cy = 790
        draw.rounded_rectangle((cx, cy, cx + 380, cy + 145), radius=14, fill=(244, 247, 250), outline=grey, width=2)
        draw.text((cx + 18, cy + 20), title, font=font(17, True), fill=navy)
        draw.text((cx + 18, cy + 59), value, font=font(25, True), fill=blue)
        draw.text((cx + 18, cy + 106), note, font=font(15), fill=navy)

    gate = payload["summary"]
    color = green if gate["gate_passed"] else red
    draw.rounded_rectangle((125, 995, 1775, 1090), radius=18, fill=(232, 247, 239) if gate["gate_passed"] else (249, 230, 230))
    draw.text((950, 1025), gate["gate_label"], anchor="mm", font=font(28, True), fill=color)
    draw.text((950, 1064), gate["gate_explanation"], anchor="mm", font=font(17), fill=navy)
    draw.text((950, 1142), "Calibration sur sorties NIST : ce passage ne valide ni les entrees officielles ni l'evenement reel.", anchor="mm", font=font(17, True), fill=red)
    canvas.save(OUT_PNG)


def write_report(payload: dict[str, object]) -> None:
    floor = payload["floor_generalization"]
    spatial = payload["spatial_calibration"]
    params = spatial["best_parameters"]
    summary = payload["summary"]
    lines = [
        "# WTC 1 - V8N : redistribution froide inverse du noyau",
        "",
        "## Resultat principal",
        "",
        summary["report_conclusion"],
        "",
        (
            f"Le test leave-one-floor-out donne une erreur absolue moyenne de {floor['lofo_mae_kip']:.0f} kip "
            f"et une erreur maximale de {floor['lofo_maximum_absolute_error_kip']:.0f} kip sur le changement de charge totale du noyau. "
            f"Sur les {spatial['holdout_metrics']['count']} poteaux reserves avant la recherche parametrique, l'erreur DCR moyenne est "
            f"{spatial['holdout_metrics']['mae']:.3f} et l'erreur maximale {spatial['holdout_metrics']['maximum_absolute_error']:.3f}."
        ),
        "",
        "## Faits et resultats officiels",
        "",
        "- La Table 4-20 publie les charges totales du noyau avant et juste apres impact, etage par etage.",
        "- Les Figures 4-68 et 4-69 publient les DCR axiaux maximaux des poteaux du noyau entre les niveaux 93 et 99.",
        "- Les capacites NIST utilisent AISC LRFD E2-1 avec K=1 et un facteur de resistance egal a 1; NIST signale une incertitude importante sur demandes et capacites.",
        "",
        "## Parametres inverses retenus",
        "",
        f"- Longueur de transfert equivalente : **{params['transfer_length_bays']:.2f} travees de noyau**.",
        f"- Exposant de biais vers la capacite : **{params['capacity_bias_exponent']:.2f}**.",
        f"- Fraction de melange global : **{params['global_mixing_fraction']:.2f}**.",
        f"- Biais nord-sud : **{params['north_bias']:+.2f}**.",
        "",
        "Ces valeurs ne sont ni un module de dalle ANSYS retrouve, ni des proprietes mesurees. Elles forment le jeu de parametres du surrogate qui minimise l'erreur sur les seuls poteaux de calibration.",
        f"Parametres places sur une borne de recherche : **{', '.join(summary['parameter_boundary_flags']) if summary['parameter_boundary_flags'] else 'aucun'}**. Une borne active signale une identification incomplete meme si les seuils predictifs sont franchis.",
        "",
        "## Test hors echantillon par etage",
        "",
        "| Etage exclu | Delta officiel (kip) | Prediction (kip) | Erreur (kip) |",
        "|---:|---:|---:|---:|",
    ]
    for row in floor["leave_one_floor_out"]:
        lines.append(
            f"| {row['floor']} | {row['observed_delta_kip']:.0f} | {row['predicted_delta_kip']:.0f} | {row['error_kip']:+.0f} |"
        )
    lines.extend(
        [
            "",
            "## Test hors echantillon par poteau",
            "",
            "| Poteau reserve | DCR officiel | DCR predit | Erreur | Etage gouvernant du surrogate |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in spatial["holdout_rows"]:
        lines.append(
            f"| {row['column']} | {row['observed']:.2f} | {row['predicted']:.3f} | {row['error']:+.3f} | {row['governing_floor']} |"
        )
    lines.extend(
        [
            "",
            "## Hypotheses propres a V8N",
            "",
            "- Le profil pre-impact utilise les DCR pre-impact comme prior spatial, multiplie par les capacites froides V8B puis renormalise a la charge officielle de chaque etage.",
            "- La charge des segments retires est repartie par un noyau exponentiel de distance; la fraction de melange global approxime l'action membranaire longue portee omise.",
            "- Les charges totales post-impact suivent une transition logistique a quatre parametres. Sa qualite est testee en excluant successivement chacun des sept etages.",
            "- Les douze poteaux reserves, dont 605 et 804 a DCR officiel eleve, ne participent pas au choix des quatre parametres spatiaux.",
            "",
            "## Limites et contradictions",
            "",
            "- Le jeu de calibration provient du modele NIST lui-meme; un bon accord demontre seulement que ce surrogate peut emuler certains de ses champs froids.",
            "- La carte DCR donne un maximum sur 93-99 et non une charge numerique par poteau et par niveau. L'etage gouvernant predit reste donc non verifie directement.",
            "- Les rigidites de membrane, sections exactes et fichiers d'entree globaux ne sont pas publies dans les pages exploitees. La V8N ne les reconstitue pas de maniere unique.",
            "- Un echec sur un poteau reserve indique un manque de structure dans le surrogate; il ne constitue ni une contradiction du modele global NIST ni un indice d'explosif.",
            "",
            "## Decision du gate",
            "",
            summary["gate_decision"],
            "",
            f"Temps d'execution : {payload['run']['elapsed_seconds']:.2f} s. Cas spatiaux testes : {spatial['parameter_case_count']}.",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    config = inputs["config"]
    prep = prepared(inputs)
    floor_result = floor_generalization(config)
    spatial = spatial_calibration(config, prep, floor_result)
    precheck = preimpact_construction_check(config, prep)
    gates = config["acceptance_gates"]
    floor_pass = floor_result["lofo_mae_kip"] <= float(gates["floor_lofo_mae_kip_max"])
    spatial_mae_pass = spatial["holdout_metrics"]["mae"] <= float(gates["heldout_column_dcr_mae_max"])
    spatial_max_pass = spatial["holdout_metrics"]["maximum_absolute_error"] <= float(gates["heldout_column_dcr_max_error_max"])
    gate_passed = bool(floor_pass and spatial_mae_pass and spatial_max_pass)
    settings = config["calibration"]["spatial_generalization"]
    best_parameters = spatial["best_parameters"]
    boundary_flags = []
    for parameter, grid_key in (
        ("transfer_length_bays", "transfer_length_bays"),
        ("capacity_bias_exponent", "capacity_bias_exponent"),
        ("global_mixing_fraction", "global_mixing_fraction"),
        ("north_bias", "north_bias"),
    ):
        grid = [float(value) for value in settings[grid_key]]
        value = float(best_parameters[parameter])
        if math.isclose(value, min(grid), abs_tol=1e-12):
            boundary_flags.append(f"{parameter}=minimum")
        elif math.isclose(value, max(grid), abs_tol=1e-12):
            boundary_flags.append(f"{parameter}=maximum")
    validation = validate(config, prep, floor_result, spatial)
    elapsed = time.perf_counter() - started
    if gate_passed:
        gate_label = "GATE SURROGATE FROID VALIDE AVEC RESERVES"
        gate_explanation = "Les seuils reserves sont franchis; les bornes actives interdisent toutefois d'interpreter les parametres comme uniques."
        gate_decision = "**VALIDE AVEC RESERVES.** Le surrogate peut etre utilise comme etat froid de reference pour une prochaine sensibilite thermique, mais pas comme preuve du mecanisme reel ni comme solveur global."
        report_conclusion = "La V8N reproduit les tendances froides NIST avec une erreur contenue sur les etages et poteaux deliberement exclus de l'ajustement. Le chemin manquant des V8L/V8M peut donc etre remplace numeriquement par un surrogate calibre, mais sa rigidite equivalente n'est pas identifiee de facon unique et reste dependante du modele officiel."
    else:
        gate_label = "GATE SURROGATE FROID NON VALIDE"
        gate_explanation = "Au moins un seuil hors echantillon echoue; le surrogate ne doit pas etre propage vers la thermique."
        gate_decision = "**NON VALIDE.** La redistribution interne inverse reste insuffisamment predictive. La prochaine iteration doit enrichir sa topologie ou retrouver des entrees mecaniques supplementaires avant toute thermique."
        report_conclusion = "La V8N ne generalise pas suffisamment les sorties froides NIST laissees hors calibration. Une concordance sur les points ajustes ne peut donc pas reparer le chemin de charge manquant des V8L/V8M."
    payload = {
        "dataset": config["dataset"],
        "run": {
            "iteration": "V8N",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": elapsed,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "random_seed": None,
            "deterministic": True,
        },
        "sources": config["official_facts"],
        "configuration": config,
        "derived_geometry": {"reference_core_bay_m": prep["reference_bay_m"]},
        "preimpact_prior_construction_check": precheck,
        "floor_generalization": floor_result,
        "spatial_calibration": spatial,
        "validation_checks": validation,
        "summary": {
            "floor_gate_pass": floor_pass,
            "spatial_mae_gate_pass": spatial_mae_pass,
            "spatial_maximum_error_gate_pass": spatial_max_pass,
            "parameter_identification_interior": not boundary_flags,
            "parameter_boundary_flags": boundary_flags,
            "gate_passed": gate_passed,
            "gate_label": gate_label,
            "gate_explanation": gate_explanation,
            "gate_decision": gate_decision,
            "report_conclusion": report_conclusion,
            "interpretation": "The fitted parameters emulate selected NIST cold outputs and are not event probabilities, recovered ANSYS material properties, independent validation, or demolition evidence.",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(payload)
    render_plot(payload)
    print(json.dumps({
        "gate_passed": gate_passed,
        "floor_lofo_mae_kip": floor_result["lofo_mae_kip"],
        "floor_lofo_max_error_kip": floor_result["lofo_maximum_absolute_error_kip"],
        "training_dcr_mae": spatial["training_metrics"]["mae"],
        "holdout_dcr_mae": spatial["holdout_metrics"]["mae"],
        "holdout_dcr_max_error": spatial["holdout_metrics"]["maximum_absolute_error"],
        "best_parameters": spatial["best_parameters"],
        "outputs": [str(OUT_JSON), str(OUT_REPORT), str(OUT_PNG)],
    }, indent=2))


if __name__ == "__main__":
    main()
