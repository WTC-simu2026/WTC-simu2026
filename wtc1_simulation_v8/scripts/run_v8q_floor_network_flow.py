"""WTC 1 V8Q - constrained floor network-flow and null-space audit.

The model imposes exact nodal equilibrium on the V8L orthogonal core graph by
using the bounded V8P axial-force digitization.  It also reserves six new
columns before model selection.  The selected weighted minimum-energy flow is
only a gauge for one representative of a non-unique inverse problem; it is not
a calibrated floor, connection, or collapse model.
"""

from __future__ import annotations

import json
import math
import platform
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
CONFIG_PATH = V8 / "data" / "v8q_floor_network_flow.json"
RESULT_PATH = V8 / "output" / "resultats_wtc1_v8q_flux_reseau.json"
REPORT_PATH = V8 / "output" / "rapport_wtc1_v8q_flux_reseau.md"
PLOT_PATH = V8 / "output" / "synthese_wtc1_v8q_flux_reseau.png"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs() -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    provenance = config["provenance"]
    return {
        "config": config,
        "digitization": read_json(ROOT / provenance["v8p_digitization"]),
        "v8p": read_json(ROOT / provenance["v8p_results"]),
        "geometry": read_json(ROOT / provenance["core_geometry"]),
    }


def orthogonal_edges(columns: set[int]) -> list[tuple[int, int]]:
    """Reproduce the explicit V8L orthogonal-envelope adjacency."""
    rows = {
        5: list(range(501, 509)),
        6: list(range(601, 609)),
        7: list(range(701, 709)),
        8: list(range(801, 808)),
        9: list(range(901, 909)),
        10: list(range(1001, 1009)),
    }
    edges: set[tuple[int, int]] = set()
    for row in rows.values():
        present = [column for column in row if column in columns]
        for first, second in zip(present, present[1:]):
            edges.add((first, second))
    ordered_rows = [rows[key] for key in sorted(rows)]
    for upper, lower in zip(ordered_rows, ordered_rows[1:]):
        by_digit_upper = {column % 100: column for column in upper if column in columns}
        by_digit_lower = {column % 100: column for column in lower if column in columns}
        for digit in sorted(set(by_digit_upper) & set(by_digit_lower)):
            edges.add(tuple(sorted((by_digit_upper[digit], by_digit_lower[digit]))))
    return sorted(edges)


def project_box_sum(
    values: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    target: float,
    tolerance: float,
) -> np.ndarray:
    """Euclidean projection on a box intersected with one exact sum."""
    low_sum = float(np.sum(lower))
    high_sum = float(np.sum(upper))
    if target < low_sum - tolerance or target > high_sum + tolerance:
        raise RuntimeError(
            f"Infeasible bounded sum: target={target:.6f}, range=[{low_sum:.6f},{high_sum:.6f}]"
        )
    tau_low = float(np.min(values - upper)) - 1.0
    tau_high = float(np.max(values - lower)) + 1.0
    for _ in range(160):
        tau = 0.5 * (tau_low + tau_high)
        candidate = np.clip(values - tau, lower, upper)
        if float(np.sum(candidate)) > target:
            tau_low = tau
        else:
            tau_high = tau
    output = np.clip(values - 0.5 * (tau_low + tau_high), lower, upper)
    residual = target - float(np.sum(output))
    if abs(residual) > tolerance:
        if residual > 0:
            available = upper - output
        else:
            available = output - lower
        index = int(np.argmax(available))
        output[index] += residual
    if abs(float(np.sum(output)) - target) > max(tolerance, 1e-8):
        raise RuntimeError("Bounded projection did not reach its exact total")
    return output


def solve_box_equality_qp(
    hessian: np.ndarray,
    linear: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    target_sum: float,
    tolerance: float,
    maximum_iterations: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Active-set solution of a positive-definite box/equality quadratic program.

    Minimize 0.5*x'Hx-linear'x with bounds and sum(x)=target_sum.
    """
    n = len(linear)
    if target_sum < float(np.sum(lower)) - tolerance or target_sum > float(np.sum(upper)) + tolerance:
        raise RuntimeError("QP bounds are incompatible with the requested total")

    def projected_fallback(initial: np.ndarray, reason: str) -> tuple[np.ndarray, dict[str, Any]]:
        eigen_maximum = float(np.max(np.linalg.eigvalsh(hessian)))
        step = 0.98 / eigen_maximum
        x = project_box_sum(initial, lower, upper, target_sum, tolerance)
        y = x.copy()
        acceleration = 1.0
        objective = float(0.5 * x @ hessian @ x - linear @ x)
        for fallback_iteration in range(1, maximum_iterations + 1):
            candidate = project_box_sum(
                y - step * (hessian @ y - linear),
                lower,
                upper,
                target_sum,
                tolerance,
            )
            candidate_objective = float(0.5 * candidate @ hessian @ candidate - linear @ candidate)
            if candidate_objective > objective + 1e-9 * max(abs(objective), 1.0):
                y = x.copy()
                acceleration = 1.0
                candidate = project_box_sum(
                    x - step * (hessian @ x - linear),
                    lower,
                    upper,
                    target_sum,
                    tolerance,
                )
                candidate_objective = float(0.5 * candidate @ hessian @ candidate - linear @ candidate)
            fixed_point = project_box_sum(
                candidate - step * (hessian @ candidate - linear),
                lower,
                upper,
                target_sum,
                tolerance,
            )
            residual = float(np.max(np.abs(fixed_point - candidate)))
            if residual <= max(tolerance, 1e-7):
                return candidate, {
                    "iterations": fallback_iteration,
                    "status": "optimal_projected_fallback",
                    "fallback_reason": reason,
                    "projected_fixed_point_residual_kip": residual,
                }
            next_acceleration = 0.5 * (1.0 + math.sqrt(1.0 + 4.0 * acceleration * acceleration))
            y = candidate + ((acceleration - 1.0) / next_acceleration) * (candidate - x)
            x = candidate
            objective = candidate_objective
            acceleration = next_acceleration
        raise RuntimeError(f"Projected QP fallback exceeded its iteration limit after {reason}")

    fixed: dict[int, float] = {}
    solution = project_box_sum(0.5 * (lower + upper), lower, upper, target_sum, tolerance)
    nu = 0.0
    seen: dict[tuple[tuple[int, int], ...], int] = {}

    for iteration in range(1, maximum_iterations + 1):
        free = [index for index in range(n) if index not in fixed]
        fixed_indices = sorted(fixed)
        if not free:
            if abs(float(np.sum(solution)) - target_sum) <= tolerance:
                return solution, {"iterations": iteration, "status": "all_fixed", "kkt_violation": None}
            raise RuntimeError("Active-set QP exhausted all free variables")

        h_ff = hessian[np.ix_(free, free)]
        rhs = linear[free].copy()
        remaining = target_sum
        if fixed_indices:
            fixed_values = np.array([fixed[index] for index in fixed_indices], dtype=float)
            rhs -= hessian[np.ix_(free, fixed_indices)] @ fixed_values
            remaining -= float(np.sum(fixed_values))
        kkt = np.block(
            [
                [h_ff, np.ones((len(free), 1), dtype=float)],
                [np.ones((1, len(free)), dtype=float), np.zeros((1, 1), dtype=float)],
            ]
        )
        solved = np.linalg.solve(kkt, np.concatenate([rhs, [remaining]]))
        free_values = solved[:-1]
        nu = float(solved[-1])
        for index, value in fixed.items():
            solution[index] = value
        for index, value in zip(free, free_values):
            solution[index] = float(value)

        violations: list[tuple[float, int, float]] = []
        for index in free:
            scale = max(float(upper[index] - lower[index]), 1.0)
            if solution[index] < lower[index] - tolerance:
                violations.append(((lower[index] - solution[index]) / scale, index, float(lower[index])))
            elif solution[index] > upper[index] + tolerance:
                violations.append(((solution[index] - upper[index]) / scale, index, float(upper[index])))
        if violations:
            _, index, bound = max(violations)
            fixed[index] = bound
            continue

        gradient = hessian @ solution - linear
        release: list[tuple[float, int]] = []
        for index, bound in fixed.items():
            reduced = float(gradient[index] + nu)
            if abs(bound - lower[index]) <= tolerance and reduced < -tolerance:
                release.append((-reduced, index))
            elif abs(bound - upper[index]) <= tolerance and reduced > tolerance:
                release.append((reduced, index))
        if not release:
            bound_error = max(
                float(np.max(lower - solution)),
                float(np.max(solution - upper)),
                abs(float(np.sum(solution)) - target_sum),
            )
            return solution, {
                "iterations": iteration,
                "status": "optimal_active_set",
                "fixed_variable_count": len(fixed),
                "kkt_violation": max(0.0, bound_error),
            }

        _, index = max(release)
        del fixed[index]
        signature = tuple(sorted((key, -1 if abs(value - lower[key]) <= tolerance else 1) for key, value in fixed.items()))
        seen[signature] = seen.get(signature, 0) + 1
        if seen[signature] > 5:
            return projected_fallback(solution, "active_set_cycle")

    return projected_fallback(solution, "active_set_iteration_limit")


def interval_distance(value: float, low: float, high: float) -> float:
    return max(low - value, 0.0, value - high)


def percentile(values: list[float], level: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=float), level))


def build_problem(inputs: dict[str, Any]) -> dict[str, Any]:
    config = inputs["config"]
    coordinates = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in inputs["geometry"]["core_layout_reconstruction"]["columns"]
    }
    columns = sorted(coordinates)
    index = {column: position for position, column in enumerate(columns)}
    edges = orthogonal_edges(set(columns))

    xs = [coordinates[column][0] for column in columns]
    ys = [coordinates[column][1] for column in columns]
    x_low, x_high = min(xs), max(xs)
    y_low, y_high = min(ys), max(ys)
    boundary = [
        column
        for column in columns
        if math.isclose(coordinates[column][0], x_low, abs_tol=1e-8)
        or math.isclose(coordinates[column][0], x_high, abs_tol=1e-8)
        or math.isclose(coordinates[column][1], y_low, abs_tol=1e-8)
        or math.isclose(coordinates[column][1], y_high, abs_tol=1e-8)
    ]

    incidence = np.zeros((len(columns), len(edges)), dtype=float)
    lengths: list[float] = []
    for edge_index, (first, second) in enumerate(edges):
        incidence[index[first], edge_index] = -1.0
        incidence[index[second], edge_index] = 1.0
        delta = np.asarray(coordinates[second]) - np.asarray(coordinates[first])
        lengths.append(float(np.linalg.norm(delta)))
    ports = np.zeros((len(columns), len(boundary)), dtype=float)
    for port_index, column in enumerate(boundary):
        ports[index[column], port_index] = 1.0
    matrix = np.concatenate([incidence, ports], axis=1)

    rows = {
        (str(row["state"]), int(row["floor"]), int(row["column"])): row
        for row in inputs["digitization"]["rows"]
    }
    floors = sorted(int(value) for value in inputs["v8p"]["configuration"]["digitization"]["floors"])
    totals = {
        floor: {
            state: float(inputs["v8p"]["configuration"]["official_core_totals_kip"][str(floor)][state])
            for state in ("before_impact", "after_impact")
        }
        for floor in floors
    }
    return {
        "columns": columns,
        "index": index,
        "coordinates": coordinates,
        "edges": edges,
        "edge_lengths": np.asarray(lengths, dtype=float),
        "boundary": boundary,
        "incidence": incidence,
        "ports": ports,
        "matrix": matrix,
        "rows": rows,
        "floors": floors,
        "totals": totals,
    }


def interval_arrays(problem: dict[str, Any], state: str, floor: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    selected = [problem["rows"][(state, floor, column)] for column in problem["columns"]]
    low = np.asarray([float(row["compression_low_kip"]) for row in selected], dtype=float)
    high = np.asarray([float(row["compression_high_kip"]) for row in selected], dtype=float)
    midpoint = np.asarray([float(row["compression_midpoint_kip"]) for row in selected], dtype=float)
    return low, high, midpoint


def gauge(problem: dict[str, Any], boundary_penalty: float) -> dict[str, Any]:
    edge_reference = float(np.median(problem["edge_lengths"]))
    edge_weights = np.maximum(problem["edge_lengths"] / edge_reference, 1e-9)
    weights = np.concatenate(
        [edge_weights, np.full(len(problem["boundary"]), float(boundary_penalty), dtype=float)]
    )
    inverse_weights = 1.0 / weights
    matrix = problem["matrix"]
    gram = (matrix * inverse_weights[np.newaxis, :]) @ matrix.T
    q_matrix = np.linalg.inv(gram)
    return {"weights": weights, "inverse_weights": inverse_weights, "q": q_matrix}


def minimum_gauge_flow(problem: dict[str, Any], gauge_data: dict[str, Any], demand: np.ndarray) -> np.ndarray:
    matrix = problem["matrix"]
    return gauge_data["inverse_weights"] * (matrix.T @ (gauge_data["q"] @ demand))


def solve_after_state(
    inputs: dict[str, Any],
    problem: dict[str, Any],
    gauge_data: dict[str, Any],
    floor: int,
    before: np.ndarray,
    target_after: np.ndarray,
    hidden_columns: set[int],
    observed_penalty: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    config = inputs["config"]
    low, high, _ = interval_arrays(problem, "after_impact", floor)
    total = problem["totals"][floor]["after_impact"]
    observed = np.asarray([column not in hidden_columns for column in problem["columns"]], dtype=float)
    lower = low.copy()
    upper = high.copy()
    for position, column in enumerate(problem["columns"]):
        if column in hidden_columns:
            lower[position] = 0.0
            upper[position] = total
    hessian = gauge_data["q"] + observed_penalty * np.diag(observed)
    linear = gauge_data["q"] @ before + observed_penalty * observed * target_after
    solution, diagnostics = solve_box_equality_qp(
        hessian,
        linear,
        lower,
        upper,
        total,
        float(config["numerics"]["projected_gradient_tolerance_kip"]),
        int(config["numerics"]["maximum_iterations"]),
    )
    diagnostics["official_total_residual_kip"] = float(np.sum(solution) - total)
    diagnostics["observed_bounds_maximum_violation_kip"] = max(
        0.0,
        float(np.max(lower - solution)),
        float(np.max(solution - upper)),
    )
    return solution, diagnostics


def center_before(inputs: dict[str, Any], problem: dict[str, Any], floor: int) -> np.ndarray:
    low, high, midpoint = interval_arrays(problem, "before_impact", floor)
    total = problem["totals"][floor]["before_impact"]
    return project_box_sum(
        midpoint,
        low,
        high,
        total,
        float(inputs["config"]["numerics"]["projection_tolerance_kip"]),
    )


def select_parameters(inputs: dict[str, Any], problem: dict[str, Any]) -> dict[str, Any]:
    config = inputs["config"]
    final_reserved = set(int(value) for value in config["reserved_validation"]["columns"])
    cases: list[dict[str, Any]] = []
    for boundary_penalty in config["inner_validation"]["boundary_port_penalties"]:
        gauge_data = gauge(problem, float(boundary_penalty))
        for observed_penalty in config["inner_validation"]["observed_target_penalties"]:
            errors: list[float] = []
            outside: list[float] = []
            rows: list[dict[str, Any]] = []
            for held_column in config["inner_validation"]["columns"]:
                hidden = final_reserved | {int(held_column)}
                held_position = problem["index"][int(held_column)]
                for floor in problem["floors"]:
                    before = center_before(inputs, problem, floor)
                    _, _, after_midpoint = interval_arrays(problem, "after_impact", floor)
                    after, diagnostics = solve_after_state(
                        inputs,
                        problem,
                        gauge_data,
                        floor,
                        before,
                        after_midpoint,
                        hidden,
                        float(observed_penalty),
                    )
                    observation = problem["rows"][("after_impact", floor, int(held_column))]
                    prediction = float(after[held_position])
                    low = float(observation["compression_low_kip"])
                    high = float(observation["compression_high_kip"])
                    midpoint = float(observation["compression_midpoint_kip"])
                    error = prediction - midpoint
                    distance = interval_distance(prediction, low, high)
                    errors.append(error)
                    outside.append(distance)
                    rows.append(
                        {
                            "column": int(held_column),
                            "floor": floor,
                            "prediction_kip": prediction,
                            "observed_low_kip": low,
                            "observed_high_kip": high,
                            "observed_midpoint_kip": midpoint,
                            "midpoint_error_kip": error,
                            "distance_outside_interval_kip": distance,
                            "solver": diagnostics,
                        }
                    )
            case = {
                "boundary_port_penalty": float(boundary_penalty),
                "observed_target_penalty": float(observed_penalty),
                "node_count": len(rows),
                "interval_coverage": float(sum(value <= 1e-9 for value in outside) / len(outside)),
                "interval_mae_kip": float(statistics.fmean(outside)),
                "midpoint_mae_kip": float(statistics.fmean(abs(value) for value in errors)),
                "midpoint_maximum_error_kip": float(max(abs(value) for value in errors)),
                "mean_bias_kip": float(statistics.fmean(errors)),
                "rows": rows,
            }
            cases.append(case)
    best = min(
        cases,
        key=lambda row: (
            row["interval_mae_kip"],
            row["midpoint_mae_kip"],
            row["midpoint_maximum_error_kip"],
            row["boundary_port_penalty"],
            row["observed_target_penalty"],
        ),
    )
    return {"case_count": len(cases), "best": best, "cases": cases}


def final_reserved_solution(
    inputs: dict[str, Any],
    problem: dict[str, Any],
    selected: dict[str, Any],
) -> dict[str, Any]:
    config = inputs["config"]
    hidden = set(int(value) for value in config["reserved_validation"]["columns"])
    gauge_data = gauge(problem, float(selected["boundary_port_penalty"]))
    rows: list[dict[str, Any]] = []
    floors: list[dict[str, Any]] = []
    central_flows: dict[int, np.ndarray] = {}
    central_after: dict[int, np.ndarray] = {}
    central_before: dict[int, np.ndarray] = {}
    for floor in problem["floors"]:
        before = center_before(inputs, problem, floor)
        _, _, after_midpoint = interval_arrays(problem, "after_impact", floor)
        after, solver = solve_after_state(
            inputs,
            problem,
            gauge_data,
            floor,
            before,
            after_midpoint,
            hidden,
            float(selected["observed_target_penalty"]),
        )
        demand = after - before
        flow = minimum_gauge_flow(problem, gauge_data, demand)
        residual = problem["matrix"] @ flow - demand
        edge_count = len(problem["edges"])
        port_sum = float(np.sum(flow[edge_count:]))
        expected_delta = (
            problem["totals"][floor]["after_impact"]
            - problem["totals"][floor]["before_impact"]
        )
        floors.append(
            {
                "floor": floor,
                "official_before_total_kip": problem["totals"][floor]["before_impact"],
                "official_after_total_kip": problem["totals"][floor]["after_impact"],
                "official_total_change_kip": expected_delta,
                "solved_before_total_kip": float(np.sum(before)),
                "solved_after_total_kip": float(np.sum(after)),
                "boundary_port_sum_kip": port_sum,
                "boundary_port_sum_error_kip": port_sum - expected_delta,
                "maximum_nodal_equilibrium_residual_kip": float(np.max(np.abs(residual))),
                "edge_flow_l2_kip": float(np.linalg.norm(flow[:edge_count])),
                "port_flow_l2_kip": float(np.linalg.norm(flow[edge_count:])),
                "maximum_absolute_edge_flow_kip": float(np.max(np.abs(flow[:edge_count]))),
                "maximum_absolute_port_flow_kip": float(np.max(np.abs(flow[edge_count:]))),
                "solver": solver,
            }
        )
        central_flows[floor] = flow
        central_after[floor] = after
        central_before[floor] = before
        for column in sorted(hidden):
            position = problem["index"][column]
            observation = problem["rows"][("after_impact", floor, column)]
            prediction = float(after[position])
            low = float(observation["compression_low_kip"])
            high = float(observation["compression_high_kip"])
            midpoint = float(observation["compression_midpoint_kip"])
            rows.append(
                {
                    "column": column,
                    "floor": floor,
                    "prediction_kip": prediction,
                    "observed_low_kip": low,
                    "observed_high_kip": high,
                    "observed_midpoint_kip": midpoint,
                    "inside_observed_interval": low - 1e-9 <= prediction <= high + 1e-9,
                    "distance_outside_interval_kip": interval_distance(prediction, low, high),
                    "midpoint_error_kip": prediction - midpoint,
                }
            )
    return {
        "gauge": gauge_data,
        "rows": rows,
        "floors": floors,
        "central_flows": central_flows,
        "central_after": central_after,
        "central_before": central_before,
    }


def sample_uncertainty(
    inputs: dict[str, Any],
    problem: dict[str, Any],
    selected: dict[str, Any],
    final: dict[str, Any],
) -> dict[str, Any]:
    config = inputs["config"]
    hidden = set(int(value) for value in config["reserved_validation"]["columns"])
    sample_count = int(config["uncertainty_sampling"]["sample_count"])
    rng = np.random.default_rng(int(config["uncertainty_sampling"]["seed"]))
    prediction_samples = {(floor, column): [] for floor in problem["floors"] for column in hidden}
    flow_samples = {
        (floor, variable): []
        for floor in problem["floors"]
        for variable in range(problem["matrix"].shape[1])
    }
    tolerance = float(config["numerics"]["projection_tolerance_kip"])
    gauge_data = final["gauge"]

    for _ in range(sample_count):
        for floor in problem["floors"]:
            before_low, before_high, _ = interval_arrays(problem, "before_impact", floor)
            raw_before = before_low + rng.random(len(before_low)) * (before_high - before_low)
            before = project_box_sum(
                raw_before,
                before_low,
                before_high,
                problem["totals"][floor]["before_impact"],
                tolerance,
            )
            after_low, after_high, _ = interval_arrays(problem, "after_impact", floor)
            target_after = after_low + rng.random(len(after_low)) * (after_high - after_low)
            after, _ = solve_after_state(
                inputs,
                problem,
                gauge_data,
                floor,
                before,
                target_after,
                hidden,
                float(selected["observed_target_penalty"]),
            )
            demand = after - before
            flow = minimum_gauge_flow(problem, gauge_data, demand)
            for column in hidden:
                prediction_samples[(floor, column)].append(float(after[problem["index"][column]]))
            for variable, value in enumerate(flow):
                flow_samples[(floor, variable)].append(float(value))

    reserved_bands: list[dict[str, Any]] = []
    central_by_key = {(row["floor"], row["column"]): row for row in final["rows"]}
    for floor in problem["floors"]:
        for column in sorted(hidden):
            values = prediction_samples[(floor, column)]
            central = central_by_key[(floor, column)]
            p05 = percentile(values, 5.0)
            p95 = percentile(values, 95.0)
            observed_low = float(central["observed_low_kip"])
            observed_high = float(central["observed_high_kip"])
            observed_midpoint = float(central["observed_midpoint_kip"])
            reserved_bands.append(
                {
                    "column": column,
                    "floor": floor,
                    "central_prediction_kip": float(central["prediction_kip"]),
                    "sample_minimum_kip": min(values),
                    "sample_p05_kip": p05,
                    "sample_median_kip": percentile(values, 50.0),
                    "sample_p95_kip": p95,
                    "sample_maximum_kip": max(values),
                    "p90_width_kip": p95 - p05,
                    "observed_low_kip": observed_low,
                    "observed_high_kip": observed_high,
                    "observed_midpoint_kip": observed_midpoint,
                    "observed_midpoint_inside_p90": p05 <= observed_midpoint <= p95,
                    "observed_interval_overlaps_p90": not (observed_high < p05 or observed_low > p95),
                }
            )

    edge_count = len(problem["edges"])
    flow_bands: list[dict[str, Any]] = []
    for floor in problem["floors"]:
        central_flow = final["central_flows"][floor]
        for variable in range(problem["matrix"].shape[1]):
            values = flow_samples[(floor, variable)]
            if variable < edge_count:
                first, second = problem["edges"][variable]
                name = f"edge_{first}_{second}"
                kind = "orthogonal_core_edge"
            else:
                column = problem["boundary"][variable - edge_count]
                name = f"boundary_port_{column}"
                kind = "external_floor_perimeter_port"
            p05 = percentile(values, 5.0)
            p95 = percentile(values, 95.0)
            flow_bands.append(
                {
                    "floor": floor,
                    "variable_index": variable,
                    "name": name,
                    "kind": kind,
                    "central_minimum_gauge_flow_kip": float(central_flow[variable]),
                    "sample_minimum_kip": min(values),
                    "sample_p05_kip": p05,
                    "sample_median_kip": percentile(values, 50.0),
                    "sample_p95_kip": p95,
                    "sample_maximum_kip": max(values),
                    "p90_width_kip": p95 - p05,
                }
            )
    return {"reserved_bands": reserved_bands, "flow_bands": flow_bands}


def null_space_audit(problem: dict[str, Any], rank_tolerance: float) -> dict[str, Any]:
    matrix = problem["matrix"]
    _, singular_values, vh = np.linalg.svd(matrix, full_matrices=True)
    threshold = rank_tolerance * float(singular_values[0])
    rank = int(np.sum(singular_values > threshold))
    null_basis = vh[rank:, :].T
    support_norm = np.linalg.norm(null_basis, axis=1) if null_basis.size else np.zeros(matrix.shape[1])
    unbounded = [int(index) for index, value in enumerate(support_norm) if value > 1e-10]
    edge_rank = int(np.linalg.matrix_rank(problem["incidence"], tol=threshold))
    edge_cycle_nullity = len(problem["edges"]) - edge_rank
    return {
        "node_count": int(matrix.shape[0]),
        "orthogonal_edge_count": len(problem["edges"]),
        "boundary_port_count": len(problem["boundary"]),
        "unknown_flow_count": int(matrix.shape[1]),
        "matrix_rank": rank,
        "matrix_full_row_rank": rank == matrix.shape[0],
        "structural_nullity": int(matrix.shape[1] - rank),
        "edge_incidence_rank": edge_rank,
        "edge_cycle_nullity": edge_cycle_nullity,
        "variables_with_null_space_support": len(unbounded),
        "all_supported_flow_components_have_unbounded_raw_ranges": len(unbounded) == matrix.shape[1],
        "smallest_nonzero_singular_value": float(singular_values[rank - 1]) if rank else None,
        "largest_singular_value": float(singular_values[0]),
        "condition_number_nonzero_spectrum": float(singular_values[0] / singular_values[rank - 1]),
        "interpretation": "Any flow component with nonzero null-space support has an unbounded mathematical range when no constitutive law or capacity bound is imposed. Reported finite flow bands apply only to the selected weighted minimum-energy gauge.",
    }


def metrics_and_gates(
    inputs: dict[str, Any],
    problem: dict[str, Any],
    parameter_selection: dict[str, Any],
    final: dict[str, Any],
    uncertainty: dict[str, Any],
    null_audit: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = final["rows"]
    errors = [float(row["midpoint_error_kip"]) for row in rows]
    outside = [float(row["distance_outside_interval_kip"]) for row in rows]
    bands = uncertainty["reserved_bands"]
    metrics = {
        "reserved_node_count": len(rows),
        "reserved_interval_coverage": float(sum(row["inside_observed_interval"] for row in rows) / len(rows)),
        "reserved_interval_mae_kip": float(statistics.fmean(outside)),
        "reserved_midpoint_mae_kip": float(statistics.fmean(abs(value) for value in errors)),
        "reserved_midpoint_maximum_error_kip": float(max(abs(value) for value in errors)),
        "reserved_mean_bias_kip": float(statistics.fmean(errors)),
        "reserved_p90_band_midpoint_coverage": float(
            sum(row["observed_midpoint_inside_p90"] for row in bands) / len(bands)
        ),
        "reserved_p90_band_interval_overlap": float(
            sum(row["observed_interval_overlaps_p90"] for row in bands) / len(bands)
        ),
        "reserved_median_p90_width_kip": float(statistics.median(row["p90_width_kip"] for row in bands)),
        "reserved_maximum_p90_width_kip": float(max(row["p90_width_kip"] for row in bands)),
        "maximum_nodal_equilibrium_residual_kip": float(
            max(row["maximum_nodal_equilibrium_residual_kip"] for row in final["floors"])
        ),
        "maximum_boundary_port_sum_error_kip": float(
            max(abs(row["boundary_port_sum_error_kip"]) for row in final["floors"])
        ),
        "inner_interval_coverage": float(parameter_selection["best"]["interval_coverage"]),
        "inner_midpoint_mae_kip": float(parameter_selection["best"]["midpoint_mae_kip"]),
        "inner_midpoint_maximum_error_kip": float(
            parameter_selection["best"]["midpoint_maximum_error_kip"]
        ),
    }
    acceptance = inputs["config"]["acceptance_gates"]
    algebraic = (
        null_audit["matrix_full_row_rank"]
        and metrics["maximum_nodal_equilibrium_residual_kip"]
        <= float(acceptance["maximum_equilibrium_residual_kip"])
    )
    predictive = (
        metrics["reserved_interval_coverage"] >= float(acceptance["reserved_interval_coverage_min"])
        and metrics["reserved_midpoint_mae_kip"] <= float(acceptance["reserved_midpoint_mae_kip_max"])
        and metrics["reserved_midpoint_maximum_error_kip"]
        <= float(acceptance["reserved_midpoint_maximum_error_kip_max"])
        and metrics["reserved_p90_band_midpoint_coverage"]
        >= float(acceptance["reserved_p90_band_midpoint_coverage_min"])
    )
    identified = null_audit["structural_nullity"] <= int(acceptance["identified_transfer_nullity_max"])
    capacity_calibrated = False
    gates = {
        "algebraic_feasibility_passed": bool(algebraic),
        "reserved_predictive_gate_passed": bool(predictive),
        "transfer_identification_gate_passed": bool(identified),
        "mechanical_capacity_calibration_present": capacity_calibrated,
        "mechanical_capacity_gate_passed": capacity_calibrated,
        "overall_cold_gate_passed": bool(algebraic and predictive and identified and capacity_calibrated),
        "thermal_or_blender_authorized": False,
    }
    return metrics, gates


def round_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: round_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [round_tree(item) for item in value]
    if isinstance(value, np.ndarray):
        return round_tree(value.tolist())
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return round(number, 9) if math.isfinite(number) else str(number)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def draw_plot(result: dict[str, Any]) -> None:
    width, height = 1800, 1120
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    navy = (23, 47, 78)
    blue = (42, 111, 151)
    orange = (230, 126, 34)
    red = (179, 54, 54)
    grey = (110, 120, 130)
    pale = (235, 241, 246)
    draw.rectangle((0, 0, width, 110), fill=navy)
    draw.text((55, 25), "WTC 1 - V8Q : flux de reseau et identifiabilite", font=font(42, True), fill="white")
    draw.text((57, 78), "Equilibre exact ne signifie pas chemin mecanique identifie", font=font(21), fill=(220, 230, 240))

    rows = result["reserved_validation"]["rows"]
    x0, y0, x1, y1 = 90, 190, 860, 825
    draw.rectangle((x0, y0, x1, y1), outline=(190, 200, 210), width=2)
    draw.text((x0, 140), "Colonnes reservees : predit vs milieu observe", font=font(27, True), fill=navy)
    maximum = max(max(row["prediction_kip"], row["observed_midpoint_kip"]) for row in rows) * 1.08
    minimum = 0.0
    for fraction in np.linspace(0.0, 1.0, 6):
        value = minimum + fraction * (maximum - minimum)
        px = x0 + fraction * (x1 - x0)
        py = y1 - fraction * (y1 - y0)
        draw.line((px, y0, px, y1), fill=pale, width=1)
        draw.line((x0, py, x1, py), fill=pale, width=1)
        draw.text((px - 28, y1 + 10), f"{value:.0f}", font=font(16), fill=grey)
        draw.text((x0 - 62, py - 10), f"{value:.0f}", font=font(16), fill=grey)
    draw.line((x0, y1, x1, y0), fill=grey, width=3)
    palette = {93: (49, 130, 189), 94: (69, 158, 172), 95: (90, 180, 120), 96: (170, 180, 70), 97: (230, 160, 50), 98: (220, 100, 55), 99: (170, 55, 65)}
    for row in rows:
        x = x0 + (row["observed_midpoint_kip"] - minimum) / (maximum - minimum) * (x1 - x0)
        y = y1 - (row["prediction_kip"] - minimum) / (maximum - minimum) * (y1 - y0)
        color = palette[int(row["floor"])]
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color, outline="white", width=1)
    draw.text(((x0 + x1) // 2 - 90, y1 + 48), "Milieu observe (kip)", font=font(21), fill=navy)
    draw.text((x0 + 8, y0 + 8), "Prediction (kip)", font=font(19), fill=navy)

    rx0, ry0, rx1, ry1 = 950, 190, 1720, 515
    draw.text((rx0, 140), "Conservation du total par etage", font=font(27, True), fill=navy)
    floor_rows = result["floor_solutions"]
    max_delta = max(abs(row["official_total_change_kip"]) for row in floor_rows) * 1.18
    zero_x = (rx0 + rx1) / 2
    draw.line((zero_x, ry0, zero_x, ry1), fill=grey, width=2)
    for order, row in enumerate(floor_rows):
        y = ry0 + 30 + order * 40
        value = row["official_total_change_kip"]
        endpoint = zero_x + value / max_delta * (rx1 - rx0) * 0.45
        draw.rectangle((min(zero_x, endpoint), y - 10, max(zero_x, endpoint), y + 10), fill=blue if value >= 0 else orange)
        draw.text((rx0, y - 12), f"F{row['floor']}", font=font(19, True), fill=navy)
        label_x = endpoint + 8
        if value < 0 and abs(endpoint - zero_x) < 80:
            label_x = endpoint - 48
        draw.text((label_x, y - 11), f"{value:+.0f}", font=font(18), fill=navy)

    audit = result["null_space_audit"]
    metrics = result["metrics"]
    gates = result["gates"]
    box = (950, 570, 1720, 960)
    draw.rounded_rectangle(box, radius=18, fill=(246, 248, 250), outline=(195, 205, 215), width=2)
    draw.text((985, 600), "Diagnostic V8Q", font=font(31, True), fill=navy)
    lines = [
        f"Noeuds / aretes / ports : {audit['node_count']} / {audit['orthogonal_edge_count']} / {audit['boundary_port_count']}",
        f"Inconnues / rang / nullite : {audit['unknown_flow_count']} / {audit['matrix_rank']} / {audit['structural_nullity']}",
        f"Couverture reservee : {100*metrics['reserved_interval_coverage']:.1f} %",
        f"MAE reservee : {metrics['reserved_midpoint_mae_kip']:.1f} kip",
        f"Erreur max : {metrics['reserved_midpoint_maximum_error_kip']:.1f} kip",
        f"Bande P90, milieux couverts : {100*metrics['reserved_p90_band_midpoint_coverage']:.1f} %",
        f"Residuel d'equilibre max : {metrics['maximum_nodal_equilibrium_residual_kip']:.2e} kip",
        f"Faisabilite algebrique : {'OUI' if gates['algebraic_feasibility_passed'] else 'NON'}",
        f"Flux mecaniquement identifies : {'OUI' if gates['transfer_identification_gate_passed'] else 'NON'}",
    ]
    for index, line in enumerate(lines):
        color = red if index == len(lines) - 1 and not gates["transfer_identification_gate_passed"] else navy
        draw.text((985, 660 + index * 31), line, font=font(20, index >= 7), fill=color)

    draw.rectangle((0, 1020, width, height), fill=navy)
    footer = "Les bandes finies sont conditionnelles a la jauge d'energie minimale ; sans loi constitutive, les flux bruts restent non uniques."
    draw.text((65, 1053), footer, font=font(22), fill="white")
    image.save(PLOT_PATH)


def write_report(result: dict[str, Any]) -> None:
    audit = result["null_space_audit"]
    metrics = result["metrics"]
    gates = result["gates"]
    best = result["parameter_selection"]["best"]
    floor_lines = "\n".join(
        f"| {row['floor']} | {row['official_total_change_kip']:+.0f} | {row['boundary_port_sum_kip']:+.3f} | {row['maximum_nodal_equilibrium_residual_kip']:.2e} | {row['maximum_absolute_edge_flow_kip']:.1f} |"
        for row in result["floor_solutions"]
    )
    reserved_by_column: list[str] = []
    for column in result["configuration"]["reserved_validation"]["columns"]:
        selected_rows = [row for row in result["reserved_validation"]["rows"] if row["column"] == column]
        coverage = sum(row["inside_observed_interval"] for row in selected_rows) / len(selected_rows)
        mae = statistics.fmean(abs(row["midpoint_error_kip"]) for row in selected_rows)
        maximum = max(abs(row["midpoint_error_kip"]) for row in selected_rows)
        reserved_by_column.append(f"| {column} | {100*coverage:.1f} % | {mae:.1f} | {maximum:.1f} |")

    if gates["reserved_predictive_gate_passed"]:
        prediction_text = "Le seuil prédictif réservé est franchi selon les critères préenregistrés."
    else:
        prediction_text = "Le seuil prédictif réservé n'est pas franchi selon les critères préenregistrés."
    report = f"""# WTC 1 - V8Q : flux de réseau contraint et audit du noyau nul

## Conclusion

V8Q trouve un équilibre algébrique exact à chacun des sept étages, mais **n'identifie pas un chemin mécanique unique**. La matrice possède {audit['unknown_flow_count']} flux inconnus pour {audit['node_count']} équilibres, un rang de {audit['matrix_rank']} et une nullité structurelle de **{audit['structural_nullity']}**. Sans lois force-déplacement et capacités, les flux bruts compatibles ont donc des directions non bornées dans le noyau nul.

{prediction_text} Sur les {metrics['reserved_node_count']} valeurs cachées, la couverture des intervalles est de **{100*metrics['reserved_interval_coverage']:.1f} %**, la MAE au milieu des intervalles de **{metrics['reserved_midpoint_mae_kip']:.1f} kip** et l'erreur maximale de **{metrics['reserved_midpoint_maximum_error_kip']:.1f} kip**. L'équilibre seul ne suffit donc pas à autoriser une étape thermique ou Blender.

## 1. Faits et résultats officiels utilisés

- **Résultat du modèle officiel :** les intervalles axiaux proviennent de la numérisation V8P des Figures 4-60 et 4-61 de NIST NCSTAR 1-6D, pages PDF 283-284.
- **Résultat du modèle officiel :** les sommes de charges du noyau par étage proviennent du Tableau 4-20, page PDF 294.
- **Fait de traitement :** les six colonnes 502, 607, 703, 806, 906 et 1003 ont été réservées avant tout réglage V8Q ; leurs 42 intervalles après impact ne participent ni à la sélection interne ni à la résolution finale.

Ce sont des sorties du même modèle global NIST. V8Q teste leur cohérence interne et leur prédictibilité conditionnelle ; il ne constitue pas une validation indépendante du scénario réel.

## 2. Affirmations des archives locales

Aucune nouvelle affirmation d'archive locale n'est introduite dans V8Q. Aucun PDF source, plan, photo ou vidéo de l'archive n'a été modifié.

## 3. Hypothèses propres au modèle

1. Les différences de charge axiale sont équilibrées par un flux signé sur le graphe orthogonal V8L et par des ports externes situés sur le pourtour reconstruit du noyau.
2. Les {audit['orthogonal_edge_count']} arêtes sont topologiques ; elles ne correspondent pas à un inventaire as-built complet des poutres, dalles et assemblages.
3. Les {audit['boundary_port_count']} ports représentent globalement le chemin noyau-plancher-périmètre manquant, sans lui attribuer de rigidité ou de résistance publiée.
4. Une jauge quadratique choisit un représentant fini : poids de port {best['boundary_port_penalty']:.1f}, pénalité des cibles observées {best['observed_target_penalty']:.1f}. Ce choix vient uniquement des colonnes de validation interne préenregistrées.
5. Les bandes d'incertitude viennent de 256 tirages dans les intervalles de numérisation. Elles sont conditionnelles à cette jauge et ne sont pas les bornes physiques exhaustives.

## 4. Résultats dérivés : équilibre par étage

| Étage | Changement total officiel (kip) | Somme des ports (kip) | Résiduel nodal max (kip) | Flux d'arête max dans la jauge (kip) |
|---:|---:|---:|---:|---:|
{floor_lines}

Le résiduel maximal est **{metrics['maximum_nodal_equilibrium_residual_kip']:.3e} kip**. La faisabilité algébrique passe, mais cette réussite est attendue puisque les ports de bord rendent la matrice de bilan de rang plein.

## 5. Test réellement réservé

| Colonne | Couverture des 7 intervalles | MAE milieu (kip) | Erreur max (kip) |
|---:|---:|---:|---:|
{chr(10).join(reserved_by_column)}

- Couverture globale des intervalles : **{100*metrics['reserved_interval_coverage']:.1f} %**.
- Distance moyenne hors intervalle : **{metrics['reserved_interval_mae_kip']:.1f} kip**.
- Couverture des milieux observés par les bandes P5-P95 : **{100*metrics['reserved_p90_band_midpoint_coverage']:.1f} %**.
- Largeur médiane de ces bandes : **{metrics['reserved_median_p90_width_kip']:.1f} kip**.
- Validation interne : couverture **{100*metrics['inner_interval_coverage']:.1f} %**, MAE milieu **{metrics['inner_midpoint_mae_kip']:.1f} kip**.

## 6. Audit d'identifiabilité

| Quantité | Valeur |
|---|---:|
| Nœuds | {audit['node_count']} |
| Arêtes orthogonales | {audit['orthogonal_edge_count']} |
| Ports externes | {audit['boundary_port_count']} |
| Flux inconnus | {audit['unknown_flow_count']} |
| Rang | {audit['matrix_rank']} |
| Nullité structurelle | **{audit['structural_nullity']}** |
| Nullité cyclique des seules arêtes | {audit['edge_cycle_nullity']} |
| Composantes ayant un support dans le noyau nul | {audit['variables_with_null_space_support']} |

Pour tout flux particulier `x`, tout vecteur `z` du noyau vérifie aussi `M(x+z)=d`. Si une composante de `z` y est non nulle, sa plage mathématique brute est non bornée sans capacité ou loi constitutive. Les valeurs finies du JSON et du graphique sont uniquement celles de la jauge d'énergie minimale.

## 7. Portes de décision

- Faisabilité algébrique : **{'PASS' if gates['algebraic_feasibility_passed'] else 'FAIL'}**.
- Prédiction des colonnes réservées : **{'PASS' if gates['reserved_predictive_gate_passed'] else 'FAIL'}**.
- Identification des transferts : **{'PASS' if gates['transfer_identification_gate_passed'] else 'FAIL'}**.
- Calibration mécanique des capacités : **ABSENTE / FAIL**.
- Porte froide globale : **{'PASS' if gates['overall_cold_gate_passed'] else 'FAIL'}**.
- Couplage thermique ou Blender : **NON AUTORISÉ**.

## 8. Contradictions, incertitudes et portée

- **Pas de contradiction numérique nouvelle avec les totaux NIST :** un réseau suffisamment libre peut reproduire exactement les bilans publiés.
- **Zone d'incertitude majeure :** cette reproduction n'indique pas quelles dalles, poutres, attaches, façades ou mécanismes tridimensionnels ont réellement porté les transferts.
- **Limite falsifiante :** une topologie avec {audit['structural_nullity']} directions nulles ne peut pas transformer l'accord d'équilibre en preuve d'un chemin physique.
- **Aucune inférence sur des explosifs ou la thermite :** V8Q ne contient aucune prédiction distinctive de ces hypothèses et ne peut donc ni les confirmer ni les exclure.
- **Étape suivante justifiée :** borner les ports et arêtes par des lois force-déplacement traçables, ou reconnaître explicitement que l'information as-built nécessaire manque. Une animation Blender resterait une visualisation tant que cette porte mécanique n'est pas franchie.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    problem = build_problem(inputs)
    config = inputs["config"]
    reserved = set(int(value) for value in config["reserved_validation"]["columns"])
    inner = set(int(value) for value in config["inner_validation"]["columns"])
    v8p_reserved = set(int(value) for value in config["reserved_validation"]["v8p_reserved_columns_not_reused"])
    if reserved & inner or reserved & v8p_reserved:
        raise RuntimeError("Reserved, inner-validation, and V8P holdout sets must remain distinct")

    parameter_selection = select_parameters(inputs, problem)
    selected = parameter_selection["best"]
    final = final_reserved_solution(inputs, problem, selected)
    uncertainty = sample_uncertainty(inputs, problem, selected, final)
    null_audit = null_space_audit(problem, float(config["numerics"]["rank_relative_tolerance"]))
    metrics, gates = metrics_and_gates(inputs, problem, parameter_selection, final, uncertainty, null_audit)

    edge_count = len(problem["edges"])
    all_top_flows: list[dict[str, Any]] = []
    for floor in problem["floors"]:
        flow = final["central_flows"][floor]
        for variable, value in enumerate(flow):
            if variable < edge_count:
                first, second = problem["edges"][variable]
                name = f"edge_{first}_{second}"
                kind = "orthogonal_core_edge"
            else:
                column = problem["boundary"][variable - edge_count]
                name = f"boundary_port_{column}"
                kind = "external_floor_perimeter_port"
            all_top_flows.append(
                {"floor": floor, "name": name, "kind": kind, "flow_kip": float(value), "absolute_flow_kip": abs(float(value))}
            )
    top_flows = sorted(all_top_flows, key=lambda row: row["absolute_flow_kip"], reverse=True)[:30]

    result = {
        "dataset": config["dataset"],
        "run": {
            "iteration": "V8Q",
            "timestamp_local": datetime.now().astimezone().isoformat(),
            "elapsed_seconds": time.perf_counter() - started,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "deterministic": True,
            "seed": int(config["uncertainty_sampling"]["seed"]),
        },
        "sources": config["official_facts"],
        "configuration": config,
        "topology": {
            "columns": problem["columns"],
            "coordinates_m": {str(key): list(value) for key, value in problem["coordinates"].items()},
            "orthogonal_edges": [list(edge) for edge in problem["edges"]],
            "boundary_port_columns": problem["boundary"],
            "orientation": "Each edge is oriented from the lower identifier to the higher identifier; positive port flow enters the core node.",
        },
        "null_space_audit": null_audit,
        "parameter_selection": parameter_selection,
        "floor_solutions": final["floors"],
        "reserved_validation": {"columns": sorted(reserved), "rows": final["rows"], "uncertainty_bands": uncertainty["reserved_bands"]},
        "minimum_gauge_flow_bands": uncertainty["flow_bands"],
        "largest_minimum_gauge_flows": top_flows,
        "metrics": metrics,
        "gates": gates,
        "summary": {
            "interpretation": "V8Q obtains exact algebraic balance but the explicit network has a large structural null space and no calibrated capacity law. The finite reported transfers are gauge-conditioned and cannot identify the real cold path, authorize thermal/Blender coupling, or support an explosive/thermite inference.",
            "next_step": "Add traceable force-displacement and capacity bounds to the external ports and surviving floor/core edges, preferably from as-built schedules; otherwise preserve the non-identifiability conclusion.",
        },
    }
    result = round_tree(result)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(result)
    draw_plot(result)
    print(json.dumps({"result": str(RESULT_PATH), "report": str(REPORT_PATH), "plot": str(PLOT_PATH), "metrics": result["metrics"], "gates": result["gates"], "nullity": result["null_space_audit"]["structural_nullity"], "elapsed_seconds": result["run"]["elapsed_seconds"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
