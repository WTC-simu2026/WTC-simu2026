#!/usr/bin/env python3
"""Digitize the V9B NIST M26/C80 vector curves with predeclared gates."""

from __future__ import annotations

import csv
import json
import math
import platform
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

from run_v8v_deformable_projectile import sha256
from run_v8w_pairwise_contact import verify_regressions


def fit_coordinate_from_values(coordinates: list[float], values: list[float]) -> dict:
    """Fit coordinate = intercept + slope * printed_value."""
    value_mean = statistics.fmean(values)
    coordinate_mean = statistics.fmean(coordinates)
    denominator = sum((value - value_mean) ** 2 for value in values)
    slope = sum(
        (value - value_mean) * (coordinate - coordinate_mean)
        for value, coordinate in zip(values, coordinates)
    ) / denominator
    intercept = coordinate_mean - slope * value_mean
    residuals = [
        coordinate - (intercept + slope * value)
        for coordinate, value in zip(coordinates, values)
    ]
    return {
        "intercept_pdf_points": intercept,
        "slope_pdf_points_per_unit": slope,
        "residuals_pdf_points": residuals,
        "maximum_absolute_residual_pdf_points": max(abs(value) for value in residuals),
    }


def colour_matches(actual: object, expected: list[float], tolerance: float) -> bool:
    if actual is None:
        return False
    values = tuple(float(value) for value in actual)
    return len(values) == len(expected) and all(
        abs(left - right) <= tolerance for left, right in zip(values, expected)
    )


def path_points(curve: dict) -> list[tuple[float, float]]:
    points = curve.get("pts") or curve.get("points") or []
    return [(float(x), float(y)) for x, y in points]


def select_segments(
    page: object,
    expected_rgb: list[float],
    axis: dict,
    x_calibration: dict,
    y_calibration: dict,
    colour_tolerance: float,
) -> list[dict]:
    x_left = x_calibration["intercept_pdf_points"] + x_calibration[
        "slope_pdf_points_per_unit"
    ] * float(axis["x_min"])
    x_right = x_calibration["intercept_pdf_points"] + x_calibration[
        "slope_pdf_points_per_unit"
    ] * float(axis["x_max"])
    y_bottom = y_calibration["intercept_pdf_points"] + y_calibration[
        "slope_pdf_points_per_unit"
    ] * float(axis["y_min_ksi"])
    y_top = y_calibration["intercept_pdf_points"] + y_calibration[
        "slope_pdf_points_per_unit"
    ] * float(axis["y_max_ksi"])
    selected = []
    for curve in page.curves:
        if not colour_matches(curve.get("stroking_color"), expected_rgb, colour_tolerance):
            continue
        if float(curve["x1"]) < x_left - 1.0 or float(curve["x0"]) > x_right + 1.0:
            continue
        if float(curve["bottom"]) > y_bottom + 1.0 or float(curve["top"]) < y_top - 1.0:
            continue
        if len(path_points(curve)) <= 2:
            continue
        selected.append(curve)
    return sorted(selected, key=lambda item: (float(item["x0"]), float(item["top"])))


def reduce_to_centerline(
    segments: list[dict],
    x_calibration: dict,
    y_calibration: dict,
    axis: dict,
) -> tuple[list[dict], list[tuple[float, float]]]:
    raw_points: list[tuple[float, float]] = []
    for segment in segments:
        raw_points.extend(path_points(segment))
    x_left = min(float(value) for value in axis["x_tick_pdf_points"])
    x_right = max(float(value) for value in axis["x_tick_pdf_points"])
    y_bottom = max(float(value) for value in axis["y_tick_pdf_top_points"])
    y_top = y_calibration["intercept_pdf_points"] + y_calibration[
        "slope_pdf_points_per_unit"
    ] * float(axis["y_max_ksi"])
    grouped: dict[float, list[float]] = defaultdict(list)
    retained_raw = []
    for x_value, y_value in raw_points:
        if x_left - 0.1 <= x_value <= x_right + 0.1 and y_top - 0.5 <= y_value <= y_bottom + 0.5:
            grouped[round(x_value, 2)].append(y_value)
            retained_raw.append((x_value, y_value))
    centreline = []
    for x_value in sorted(grouped):
        y_value = statistics.median(grouped[x_value])
        strain = (x_value - x_calibration["intercept_pdf_points"]) / x_calibration[
            "slope_pdf_points_per_unit"
        ]
        stress = (y_value - y_calibration["intercept_pdf_points"]) / y_calibration[
            "slope_pdf_points_per_unit"
        ]
        if float(axis["x_min"]) - 1e-6 <= strain <= float(axis["x_max"]) + 1e-6:
            centreline.append(
                {
                    "x_pdf_points": x_value,
                    "y_pdf_top_points": y_value,
                    "engineering_strain": max(0.0, strain),
                    "engineering_stress_ksi": max(0.0, stress),
                }
            )
    return centreline, retained_raw


def endpoint_gap(left: list[dict], right: list[dict]) -> float | None:
    if not left or not right:
        return None
    left_point = max(left, key=lambda item: item["x_pdf_points"])
    right_point = min(right, key=lambda item: item["x_pdf_points"])
    return math.hypot(
        right_point["x_pdf_points"] - left_point["x_pdf_points"],
        right_point["y_pdf_top_points"] - left_point["y_pdf_top_points"],
    )


def merge_centrelines(*curves: list[dict]) -> list[dict]:
    grouped: dict[float, list[dict]] = defaultdict(list)
    for curve in curves:
        for point in curve:
            grouped[round(point["x_pdf_points"], 2)].append(point)
    merged = []
    for x_value in sorted(grouped):
        rows = grouped[x_value]
        merged.append(
            {
                "x_pdf_points": x_value,
                "y_pdf_top_points": statistics.median(
                    row["y_pdf_top_points"] for row in rows
                ),
                "engineering_strain": statistics.median(
                    row["engineering_strain"] for row in rows
                ),
                "engineering_stress_ksi": statistics.median(
                    row["engineering_stress_ksi"] for row in rows
                ),
            }
        )
    return merged


def offset_yield(curve: list[dict], elastic_modulus_ksi: float) -> dict:
    previous = None
    for point in curve:
        strain = point["engineering_strain"]
        stress = point["engineering_stress_ksi"]
        difference = stress - elastic_modulus_ksi * (strain - 0.01)
        current = (strain, stress, difference)
        if (
            previous is not None
            and current[0] >= 0.01
            and previous[2] >= 0.0
            and current[2] <= 0.0
            and current[0] > previous[0]
        ):
            fraction = previous[2] / (previous[2] - current[2])
            crossing_strain = previous[0] + fraction * (current[0] - previous[0])
            crossing_stress = previous[1] + fraction * (current[1] - previous[1])
            return {
                "engineering_strain": crossing_strain,
                "engineering_stress_ksi": crossing_stress,
                "found": True,
            }
        previous = current
    return {"engineering_strain": None, "engineering_stress_ksi": None, "found": False}


def interval_relative_error(value: float | None, bounds: list[float]) -> float | None:
    if value is None:
        return None
    low, high = sorted(float(item) for item in bounds)
    if low <= value <= high:
        return 0.0
    if value < low:
        return (low - value) / low
    return (value - high) / high


def verify_source(config: dict, project_root: Path) -> dict:
    source = config["sources"][0]
    path = project_root / source["path"]
    actual = sha256(path) if path.exists() else None
    return {
        "id": source["id"],
        "path": source["path"],
        "expected_sha256": source["sha256"],
        "actual_sha256": actual,
        "passed": actual == source["sha256"],
        "source_modified": False,
    }


def write_curve_csv(path: Path, curve: list[dict], ksi_to_mpa: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "engineering_strain",
                "engineering_stress_ksi",
                "engineering_stress_mpa",
                "x_pdf_points",
                "y_pdf_top_points",
            ],
        )
        writer.writeheader()
        for point in curve:
            writer.writerow(
                {
                    "engineering_strain": f"{point['engineering_strain']:.12g}",
                    "engineering_stress_ksi": f"{point['engineering_stress_ksi']:.12g}",
                    "engineering_stress_mpa": f"{point['engineering_stress_ksi'] * ksi_to_mpa:.12g}",
                    "x_pdf_points": f"{point['x_pdf_points']:.8g}",
                    "y_pdf_top_points": f"{point['y_pdf_top_points']:.8g}",
                }
            )


def main() -> None:
    started = time.perf_counter()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v9b_stress_strain_digitization.json"
    preliminary_path = simulation_root / "output" / "resultats_wtc1_v9b_numerisation_preliminaire.json"
    curve_root = simulation_root / "output" / "v9b_digitized_curves"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if registry_path.exists() and '"experiment_id":"WTC1-V9B"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V9B outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    regressions = verify_regressions(config, project_root)
    source_verification = verify_source(config, project_root)
    if not regressions["passed"]:
        raise SystemExit("V9A regression verification failed before V9B")
    if not source_verification["passed"]:
        raise SystemExit("The declared read-only NIST source changed or is missing")

    pdf_path = project_root / config["sources"][0]["path"]
    colour_tolerance = float(
        config["predeclared_digitization_gates"]["maximum_colour_component_difference"]
    )
    axis_limit = float(
        config["predeclared_digitization_gates"][
            "maximum_axis_calibration_residual_pdf_points"
        ]
    )
    elastic_modulus = float(config["digitization_method"]["elastic_modulus_ksi_hypothesis"])
    axis_results = []
    curve_results = []
    pdf = pdfplumber.open(pdf_path)
    try:
        for figure in config["figures"]:
            page = pdf.pages[int(figure["pdf_page_number"]) - 1]
            axis = figure["axis"]
            x_calibration = fit_coordinate_from_values(
                [float(value) for value in axis["x_tick_pdf_points"]],
                [float(value) for value in axis["x_tick_values"]],
            )
            y_calibration = fit_coordinate_from_values(
                [float(value) for value in axis["y_tick_pdf_top_points"]],
                [float(value) for value in axis["y_tick_values_ksi"]],
            )
            axis_passed = (
                x_calibration["maximum_absolute_residual_pdf_points"] <= axis_limit
                and y_calibration["maximum_absolute_residual_pdf_points"] <= axis_limit
            )
            line_width = float(axis["expected_line_width_pdf_points"])
            strain_uncertainty = (
                line_width / 2.0 + axis_limit
            ) / abs(x_calibration["slope_pdf_points_per_unit"])
            stress_uncertainty = (
                line_width / 2.0 + axis_limit
            ) / abs(y_calibration["slope_pdf_points_per_unit"])
            axis_results.append(
                {
                    "figure_id": figure["id"],
                    "pdf_page_number": figure["pdf_page_number"],
                    "x": x_calibration,
                    "y": y_calibration,
                    "maximum_allowed_residual_pdf_points": axis_limit,
                    "line_width_pdf_points": line_width,
                    "conservative_half_width_plus_calibration_strain_uncertainty": strain_uncertainty,
                    "conservative_half_width_plus_calibration_stress_uncertainty_ksi": stress_uncertainty,
                    "passed": axis_passed,
                }
            )

            for declared_curve in figure["curves"]:
                segments = select_segments(
                    page,
                    declared_curve["rgb"],
                    axis,
                    x_calibration,
                    y_calibration,
                    colour_tolerance,
                )
                centreline, retained_raw = reduce_to_centerline(
                    segments, x_calibration, y_calibration, axis
                )
                alias_gap = None
                alias_segment_count = 0
                alias_passed = True
                if "rgb_terminal_alias" in declared_curve:
                    alias_segments = select_segments(
                        page,
                        declared_curve["rgb_terminal_alias"],
                        axis,
                        x_calibration,
                        y_calibration,
                        colour_tolerance,
                    )
                    alias_centreline, alias_raw = reduce_to_centerline(
                        alias_segments, x_calibration, y_calibration, axis
                    )
                    alias_segment_count = len(alias_segments)
                    alias_gap = endpoint_gap(centreline, alias_centreline)
                    alias_limit = float(
                        config["predeclared_digitization_gates"][
                            "maximum_terminal_alias_gap_pdf_points"
                        ]
                    )
                    alias_passed = (
                        alias_segment_count == 1
                        and alias_gap is not None
                        and alias_gap <= alias_limit
                    )
                    if alias_passed:
                        centreline = merge_centrelines(centreline, alias_centreline)
                        retained_raw.extend(alias_raw)

                yield_result = offset_yield(centreline, elastic_modulus)
                tensile_strength = max(
                    (point["engineering_stress_ksi"] for point in centreline),
                    default=None,
                )
                yield_error = interval_relative_error(
                    yield_result["engineering_stress_ksi"],
                    declared_curve["yield_reference_ksi"],
                )
                tensile_error = interval_relative_error(
                    tensile_strength, declared_curve["tensile_reference_ksi"]
                )
                point_count = len(centreline)
                strain_coverage = (
                    max(point["engineering_strain"] for point in centreline)
                    - min(point["engineering_strain"] for point in centreline)
                    if centreline
                    else 0.0
                )
                identity_passed = bool(segments) and alias_passed
                point_gate = point_count >= int(
                    config["predeclared_digitization_gates"][
                        "minimum_unique_centerline_points_per_curve"
                    ]
                )
                coverage_gate = strain_coverage >= float(
                    config["predeclared_digitization_gates"][
                        "minimum_engineering_strain_coverage"
                    ]
                )
                yield_gate = yield_error is not None and yield_error <= float(
                    config["predeclared_digitization_gates"][
                        "maximum_individual_yield_relative_error"
                    ]
                )
                tensile_gate = tensile_error is not None and tensile_error <= float(
                    config["predeclared_digitization_gates"][
                        "maximum_individual_tensile_relative_error"
                    ]
                )
                curve_passed = all(
                    (
                        axis_passed,
                        identity_passed,
                        point_gate,
                        coverage_gate,
                        yield_gate,
                        tensile_gate,
                    )
                )
                csv_relative = Path("wtc1_simulation_v8/output/v9b_digitized_curves") / (
                    declared_curve["id"].lower() + ".csv"
                )
                write_curve_csv(
                    project_root / csv_relative,
                    centreline,
                    float(config["units"]["ksi_to_mpa"]),
                )
                curve_results.append(
                    {
                        "figure_id": figure["id"],
                        "figure": figure["figure"],
                        "pdf_page_number": figure["pdf_page_number"],
                        "coupon_series_id": figure["coupon_series_id"],
                        "curve_id": declared_curve["id"],
                        "rate_per_s": declared_curve["rate_per_s"],
                        "orientation": figure["orientation"],
                        "specimen_geometry": declared_curve["specimen_geometry"],
                        "source_segment_count": len(segments),
                        "source_raw_vector_point_count": len(retained_raw),
                        "unique_centerline_point_count": point_count,
                        "engineering_strain_coverage": strain_coverage,
                        "terminal_alias_segment_count": alias_segment_count,
                        "terminal_alias_gap_pdf_points": alias_gap,
                        "terminal_alias_passed": alias_passed,
                        "digitized_yield_1_percent_offset_ksi": yield_result[
                            "engineering_stress_ksi"
                        ],
                        "digitized_yield_strain": yield_result["engineering_strain"],
                        "yield_reference_interval_ksi": declared_curve[
                            "yield_reference_ksi"
                        ],
                        "yield_relative_error_to_interval": yield_error,
                        "digitized_tensile_strength_ksi": tensile_strength,
                        "tensile_reference_interval_ksi": declared_curve[
                            "tensile_reference_ksi"
                        ],
                        "tensile_relative_error_to_interval": tensile_error,
                        "stress_coordinate_uncertainty_ksi": stress_uncertainty,
                        "strain_coordinate_uncertainty": strain_uncertainty,
                        "csv": str(csv_relative).replace("\\", "/"),
                        "identity_passed": identity_passed,
                        "point_count_passed": point_gate,
                        "strain_coverage_passed": coverage_gate,
                        "yield_validation_passed": yield_gate,
                        "tensile_validation_passed": tensile_gate,
                        "passed": curve_passed,
                    }
                )
    finally:
        pdf.close()

    yield_errors = [
        item["yield_relative_error_to_interval"]
        for item in curve_results
        if item["yield_relative_error_to_interval"] is not None
    ]
    tensile_errors = [
        item["tensile_relative_error_to_interval"]
        for item in curve_results
        if item["tensile_relative_error_to_interval"] is not None
    ]
    gates = config["predeclared_digitization_gates"]
    expected_curve_count = sum(len(figure["curves"]) for figure in config["figures"])
    median_yield_error = statistics.median(yield_errors) if yield_errors else None
    median_tensile_error = statistics.median(tensile_errors) if tensile_errors else None
    curve_count_passed = (
        len(curve_results) == expected_curve_count
        if gates["all_nine_plotted_curves_required"]
        else True
    )
    median_yield_passed = (
        median_yield_error is not None
        and median_yield_error <= float(gates["maximum_median_yield_relative_error"])
    )
    median_tensile_passed = (
        median_tensile_error is not None
        and median_tensile_error <= float(gates["maximum_median_tensile_relative_error"])
    )
    digitization_passed = all(
        (
            regressions["passed"],
            source_verification["passed"],
            curve_count_passed,
            all(item["passed"] for item in axis_results),
            all(item["passed"] for item in curve_results),
            median_yield_passed,
            median_tensile_passed,
        )
    )
    results = {
        "iteration": "V9B",
        "stage": "digitization_preliminary",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "source_verification": source_verification,
        "regressions": regressions,
        "digitization_method": config["digitization_method"],
        "axis_calibrations": axis_results,
        "curve_results": curve_results,
        "digitization_gate_summary": {
            "expected_curve_count": expected_curve_count,
            "actual_curve_count": len(curve_results),
            "curve_count_passed": curve_count_passed,
            "maximum_yield_relative_error": max(yield_errors) if yield_errors else None,
            "median_yield_relative_error": median_yield_error,
            "median_yield_passed": median_yield_passed,
            "maximum_tensile_relative_error": max(tensile_errors)
            if tensile_errors
            else None,
            "median_tensile_relative_error": median_tensile_error,
            "median_tensile_passed": median_tensile_passed,
            "all_axis_calibrations_passed": all(item["passed"] for item in axis_results),
            "all_individual_curves_passed": all(item["passed"] for item in curve_results),
            "digitization_passed": digitization_passed,
        },
        "conditional_openradioss_coupon_authorized": bool(
            digitization_passed
            and config["predeclared_conditional_coupon"][
                "authorized_only_if_digitization_passed"
            ]
        ),
        "openradioss_coupon_executed": False,
        "rupture_or_failure_deletion_executed": False,
        "facade_impact_executed": False,
        "scope_gates": config["scope_gates"],
        "runtime": {
            "elapsed_seconds": time.perf_counter() - started,
            "python": platform.python_version(),
            "pdfplumber": getattr(pdfplumber, "__version__", "unknown"),
            "config_sha256": sha256(config_path),
            "runner_sha256": sha256(Path(__file__)),
            "source_archive_rescanned": False,
            "official_source_files_modified": False,
            "solver_executed": False,
            "blender_executed": False,
        },
    }
    preliminary_path.parent.mkdir(parents=True, exist_ok=True)
    preliminary_path.write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(results["digitization_gate_summary"], indent=2))
    print(f"PRELIMINARY_RESULTS={preliminary_path}")


if __name__ == "__main__":
    main()
