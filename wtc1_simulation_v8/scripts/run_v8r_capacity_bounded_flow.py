"""WTC 1 V8R - exact capacity-bounded floor-flow feasibility audit.

This iteration converts the V8Q equilibrium bookkeeping graph into a bounded
circulation problem.  Core-edge capacities come from the existing V8L/V8H
proxy beam law.  Boundary-port capacities come only from V8M's geometry-based
vertical component, never directly from the published 44/94 kip seat limits.

The result is a reduced cold-path audit, not an as-built finite-element model.
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8h_mechanical_core_transfer as v8h  # noqa: E402


CONFIG_PATH = V8 / "data" / "v8r_capacity_bounded_flow.json"
RESULT_PATH = V8 / "output" / "resultats_wtc1_v8r_flux_bornes.json"
REPORT_PATH = V8 / "output" / "rapport_wtc1_v8r_flux_bornes.md"
PLOT_PATH = V8 / "output" / "synthese_wtc1_v8r_flux_bornes.png"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs() -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    provenance = config["provenance"]
    return {
        "config": config,
        "digitization": read_json(ROOT / provenance["v8p_digitization"]),
        "v8p_config": read_json(ROOT / provenance["v8p_configuration"]),
        "v8q": read_json(ROOT / provenance["v8q_results"]),
        "v8h_config": read_json(ROOT / provenance["v8h_configuration"]),
        "v8l_config": read_json(ROOT / provenance["v8l_configuration"]),
        "v8m_config": read_json(ROOT / provenance["v8m_configuration"]),
        "v8m_results": read_json(ROOT / provenance["v8m_results"]),
        "aisc": read_json(ROOT / provenance["aisc_properties"]),
        "transfer": read_json(ROOT / provenance["nist_transfer"]),
        "geometry": read_json(ROOT / provenance["core_geometry"]),
    }


def orthogonal_edges(columns: set[int]) -> list[tuple[int, int]]:
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
    ordered = [rows[key] for key in sorted(rows)]
    for upper, lower in zip(ordered, ordered[1:]):
        upper_by_digit = {column % 100: column for column in upper if column in columns}
        lower_by_digit = {column % 100: column for column in lower if column in columns}
        for digit in sorted(set(upper_by_digit) & set(lower_by_digit)):
            edges.add(tuple(sorted((upper_by_digit[digit], lower_by_digit[digit]))))
    return sorted(edges)


class Dinic:
    def __init__(self, node_count: int, tolerance: float) -> None:
        self.graph: list[list[dict[str, Any]]] = [[] for _ in range(node_count)]
        self.tolerance = tolerance

    def add_edge(self, source: int, target: int, capacity: float) -> tuple[int, int, float]:
        forward = {"to": target, "rev": len(self.graph[target]), "cap": float(capacity)}
        reverse = {"to": source, "rev": len(self.graph[source]), "cap": 0.0}
        self.graph[source].append(forward)
        self.graph[target].append(reverse)
        return source, len(self.graph[source]) - 1, float(capacity)

    def max_flow(self, source: int, sink: int, maximum_iterations: int) -> float:
        total = 0.0
        iterations = 0
        while iterations < maximum_iterations:
            level = [-1] * len(self.graph)
            level[source] = 0
            queue = deque([source])
            while queue:
                node = queue.popleft()
                for edge in self.graph[node]:
                    if edge["cap"] > self.tolerance and level[edge["to"]] < 0:
                        level[edge["to"]] = level[node] + 1
                        queue.append(edge["to"])
            if level[sink] < 0:
                break
            cursor = [0] * len(self.graph)

            def send(node: int, amount: float) -> float:
                if node == sink:
                    return amount
                while cursor[node] < len(self.graph[node]):
                    edge = self.graph[node][cursor[node]]
                    if edge["cap"] > self.tolerance and level[edge["to"]] == level[node] + 1:
                        pushed = send(edge["to"], min(amount, edge["cap"]))
                        if pushed > self.tolerance:
                            edge["cap"] -= pushed
                            self.graph[edge["to"]][edge["rev"]]["cap"] += pushed
                            return pushed
                    cursor[node] += 1
                return 0.0

            while iterations < maximum_iterations:
                pushed = send(source, float("inf"))
                iterations += 1
                if pushed <= self.tolerance:
                    break
                total += pushed
        if iterations >= maximum_iterations:
            raise RuntimeError("Maximum-flow iteration limit reached")
        return total

    def reachable(self, source: int) -> set[int]:
        seen = {source}
        stack = [source]
        while stack:
            node = stack.pop()
            for edge in self.graph[node]:
                if edge["cap"] > self.tolerance and edge["to"] not in seen:
                    seen.add(edge["to"])
                    stack.append(edge["to"])
        return seen


def bounded_transshipment(
    nodes: list[str],
    demands: dict[str, float],
    bounded_edges: list[dict[str, Any]],
    tolerance: float,
    maximum_iterations: int,
) -> dict[str, Any]:
    names = list(dict.fromkeys(nodes))
    index = {name: position for position, name in enumerate(names)}
    super_source = len(names)
    super_sink = len(names) + 1
    solver = Dinic(len(names) + 2, tolerance)
    lower_balance = {name: 0.0 for name in names}
    references: list[dict[str, Any]] = []
    for row in bounded_edges:
        source = str(row["source"])
        target = str(row["target"])
        lower = float(row["lower_kip"])
        upper = float(row["upper_kip"])
        if upper < lower - tolerance:
            raise RuntimeError(f"Invalid bounded edge {row['label']}: {lower}>{upper}")
        lower_balance[source] -= lower
        lower_balance[target] += lower
        reference = solver.add_edge(index[source], index[target], max(0.0, upper - lower))
        references.append({**row, "reference": reference})

    residual = {
        name: float(demands.get(name, 0.0)) - lower_balance[name]
        for name in names
    }
    if abs(sum(residual.values())) > max(tolerance, 1e-6):
        raise RuntimeError(f"Residual node demands do not sum to zero: {sum(residual.values())}")
    required = 0.0
    for name, value in residual.items():
        if value < -tolerance:
            solver.add_edge(super_source, index[name], -value)
            required += -value
        elif value > tolerance:
            solver.add_edge(index[name], super_sink, value)
    achieved = solver.max_flow(super_source, super_sink, maximum_iterations)
    feasible = achieved >= required - tolerance
    flows: list[dict[str, Any]] = []
    if feasible:
        for row in references:
            source, position, initial_capacity = row["reference"]
            remaining = float(solver.graph[source][position]["cap"])
            flow = float(row["lower_kip"]) + initial_capacity - remaining
            flows.append(
                {
                    "label": row["label"],
                    "kind": row["kind"],
                    "source": row["source"],
                    "target": row["target"],
                    "flow_kip": flow,
                    "lower_kip": float(row["lower_kip"]),
                    "upper_kip": float(row["upper_kip"]),
                }
            )
    reachable = solver.reachable(super_source)
    return {
        "feasible": feasible,
        "required_balancing_flow_kip": required,
        "achieved_balancing_flow_kip": achieved,
        "feasibility_deficit_kip": max(0.0, required - achieved),
        "super_source_reachable_node_count": len(reachable),
        "flows": flows,
    }


def build_problem(inputs: dict[str, Any]) -> dict[str, Any]:
    coordinates = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in inputs["geometry"]["core_layout_reconstruction"]["columns"]
    }
    columns = sorted(coordinates)
    rows = {
        (str(row["state"]), int(row["floor"]), int(row["column"])): row
        for row in inputs["digitization"]["rows"]
    }
    totals_source = inputs["v8p_config"]["official_core_totals_kip"]
    totals = {
        floor: {
            state: float(totals_source[str(floor)][state])
            for state in ("before_impact", "after_impact")
        }
        for floor in inputs["config"]["floors"]
    }
    xs = [value[0] for value in coordinates.values()]
    ys = [value[1] for value in coordinates.values()]
    face_columns = {
        "north": sorted(column for column, value in coordinates.items() if math.isclose(value[1], max(ys), abs_tol=1e-8)),
        "south": sorted(column for column, value in coordinates.items() if math.isclose(value[1], min(ys), abs_tol=1e-8)),
        "east": sorted(column for column, value in coordinates.items() if math.isclose(value[0], max(xs), abs_tol=1e-8)),
        "west": sorted(column for column, value in coordinates.items() if math.isclose(value[0], min(xs), abs_tol=1e-8)),
    }
    boundary = sorted(set().union(*face_columns.values()))
    moment_edges = sorted(
        tuple(sorted(int(value) for value in edge))
        for edge in inputs["v8h_config"]["moment_beam_topology"]["edges"]
    )
    orthogonal = orthogonal_edges(set(columns))
    damaged_floor96 = {
        tuple(sorted(int(value) for value in edge))
        for edge in inputs["v8l_config"]["beam_damage_definition"]["floor96_removed_edges"]
    }
    return {
        "columns": columns,
        "coordinates": coordinates,
        "rows": rows,
        "totals": totals,
        "face_columns": face_columns,
        "boundary": boundary,
        "topologies": {
            "nist_moment_only": moment_edges,
            "orthogonal_floor96_reconstruction": orthogonal,
        },
        "damaged_floor96": damaged_floor96,
    }


def interval(problem: dict[str, Any], state: str, floor: int, column: int) -> tuple[float, float]:
    row = problem["rows"][(state, floor, column)]
    return float(row["compression_low_kip"]), float(row["compression_high_kip"])


def beam_capacity_map(
    inputs: dict[str, Any],
    problem: dict[str, Any],
    edge_case: dict[str, Any],
    floor: int,
    multiplier: float = 1.0,
    force_active: bool = False,
) -> dict[tuple[int, int], float]:
    if edge_case.get("kind") == "unknown_unbounded":
        return {
            edge: multiplier * float(edge_case["capacity_kip_per_direction"])
            for edge in problem["topologies"][edge_case["topology"]]
        }
    if (
        floor not in set(int(value) for value in inputs["config"]["edge_mapping"]["active_floors"])
        and not force_active
    ):
        return {}
    shape = inputs["aisc"]["shapes"][edge_case["profile"]]
    fy_params = inputs["transfer"]["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = inputs["transfer"]["steel_temperature_model"]["young_modulus_parameters"]
    output: dict[tuple[int, int], float] = {}
    for edge in problem["topologies"][edge_case["topology"]]:
        if floor == 96 and edge in problem["damaged_floor96"]:
            output[edge] = 0.0
            continue
        first, second = edge
        length = math.dist(problem["coordinates"][first], problem["coordinates"][second])
        law = v8h.beam_law(
            shape,
            length,
            float(inputs["config"]["edge_mapping"]["temperature_c"]),
            float(edge_case["connection_factor"]),
            int(inputs["config"]["edge_mapping"]["active_planes_per_floor"]),
            fy_params,
            e_params,
        )
        if edge_case["capacity_point"] == "yield_force":
            capacity = float(law["yield_force_kip"])
        elif edge_case["capacity_point"] == "prefracture_force":
            capacity = float(law["yield_force_kip"]) + float(
                inputs["config"]["edge_mapping"]["post_yield_tangent_ratio"]
            ) * float(law["initial_stiffness_kip_per_in"]) * max(
                0.0,
                float(law["ultimate_displacement_in"]) - float(law["yield_displacement_in"]),
            )
        else:
            raise RuntimeError(f"Unknown capacity point {edge_case['capacity_point']}")
        output[edge] = multiplier * max(0.0, capacity)
    return output


def find_v8m_case(inputs: dict[str, Any], topology: str) -> dict[str, Any]:
    for row in inputs["v8m_results"]["case_rows"]:
        if (
            row["topology"] == topology
            and float(row["concrete_effectiveness_factor"])
            == float(inputs["config"]["port_mapping"]["concrete_effectiveness_factor"])
            and row["connection_regime"] == inputs["config"]["port_mapping"]["connection_regime"]
        ):
            return row
    raise RuntimeError(f"V8M case not found: {topology}")


def port_capacity_map(
    inputs: dict[str, Any],
    problem: dict[str, Any],
    port_case: dict[str, Any],
    floor: int,
    multiplier: float = 1.0,
    force_active: bool = False,
) -> tuple[dict[int, float], dict[str, Any]]:
    output = {column: 0.0 for column in problem["boundary"]}
    kind = port_case["kind"]
    if kind == "none":
        return output, {"mapped": True, "aggregate_capacity_kip": 0.0, "face_capacity_per_floor_kip": {}}
    if kind == "unknown_unbounded":
        capacity = float(inputs["config"]["port_mapping"]["unknown_unbounded_capacity_kip_per_port"])
        return (
            {column: capacity for column in problem["boundary"]},
            {
                "mapped": False,
                "aggregate_capacity_kip": capacity * len(problem["boundary"]),
                "face_capacity_per_floor_kip": {},
            },
        )
    if kind != "v8m":
        raise RuntimeError(f"Unknown port kind {kind}")
    active = floor in set(int(value) for value in port_case["active_floors"])
    if not active and not force_active:
        return output, {"mapped": True, "aggregate_capacity_kip": 0.0, "face_capacity_per_floor_kip": {}, "inactive_floor": True}
    source = find_v8m_case(inputs, str(port_case["topology"]))
    response = source["reference_responses"][str(float(port_case["drop_in"]))]
    face_capacities: dict[str, float] = {}
    for face_row in response["face_rows"]:
        face = str(face_row["face"])
        floor_count = int(face_row["floor_count"])
        per_floor = multiplier * float(face_row["face_transfer_kip"]) / floor_count
        face_capacities[face] = per_floor
        face_nodes = problem["face_columns"][face]
        share = per_floor / len(face_nodes)
        for column in face_nodes:
            output[column] += share
    return output, {
        "mapped": True,
        "aggregate_capacity_kip": float(sum(output.values())),
        "face_capacity_per_floor_kip": face_capacities,
        "source_total_transfer_all_active_floors_kip": float(response["total_vertical_transfer_kip"]),
        "active_or_sensitivity_extrapolated": active or force_active,
    }


def floor_feasibility(
    inputs: dict[str, Any],
    problem: dict[str, Any],
    edge_case: dict[str, Any],
    port_case: dict[str, Any],
    floor: int,
    port_multiplier: float = 1.0,
    force_port_active: bool = False,
    edge_multiplier: float = 1.0,
    force_edge_active: bool = False,
) -> dict[str, Any]:
    before_total = problem["totals"][floor]["before_impact"]
    after_total = problem["totals"][floor]["after_impact"]
    total_change = after_total - before_total
    edge_caps = beam_capacity_map(
        inputs,
        problem,
        edge_case,
        floor,
        multiplier=edge_multiplier,
        force_active=force_edge_active,
    )
    port_caps, port_meta = port_capacity_map(
        inputs,
        problem,
        port_case,
        floor,
        multiplier=port_multiplier,
        force_active=force_port_active,
    )
    nodes = ["BEFORE", "AFTER", "EXTERNAL"] + [f"C{column}" for column in problem["columns"]]
    demands = {name: 0.0 for name in nodes}
    demands["BEFORE"] = -before_total
    demands["AFTER"] = after_total
    demands["EXTERNAL"] = before_total - after_total
    edges: list[dict[str, Any]] = []
    for column in problem["columns"]:
        before_low, before_high = interval(problem, "before_impact", floor, column)
        after_low, after_high = interval(problem, "after_impact", floor, column)
        edges.append(
            {
                "source": "BEFORE",
                "target": f"C{column}",
                "lower_kip": before_low,
                "upper_kip": before_high,
                "label": f"before_{column}",
                "kind": "before_load_interval",
            }
        )
        edges.append(
            {
                "source": f"C{column}",
                "target": "AFTER",
                "lower_kip": after_low,
                "upper_kip": after_high,
                "label": f"after_{column}",
                "kind": "after_load_interval",
            }
        )
    for (first, second), capacity in edge_caps.items():
        for source, target in ((first, second), (second, first)):
            edges.append(
                {
                    "source": f"C{source}",
                    "target": f"C{target}",
                    "lower_kip": 0.0,
                    "upper_kip": capacity,
                    "label": f"core_{source}_{target}",
                    "kind": "core_edge_direction",
                }
            )
    for column, capacity in port_caps.items():
        for source, target, suffix in (
            ("EXTERNAL", f"C{column}", "into_core"),
            (f"C{column}", "EXTERNAL", "out_of_core"),
        ):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "lower_kip": 0.0,
                    "upper_kip": capacity,
                    "label": f"port_{column}_{suffix}",
                    "kind": "boundary_port_direction",
                }
            )
    solved = bounded_transshipment(
        nodes,
        demands,
        edges,
        float(inputs["config"]["numerics"]["capacity_tolerance_kip"]),
        int(inputs["config"]["numerics"]["maximum_flow_iterations"]),
    )
    chosen_before = 0.0
    chosen_after = 0.0
    port_net = 0.0
    maximum_edge_utilization = 0.0
    maximum_port_utilization = 0.0
    if solved["feasible"]:
        for row in solved["flows"]:
            if row["kind"] == "before_load_interval":
                chosen_before += float(row["flow_kip"])
            elif row["kind"] == "after_load_interval":
                chosen_after += float(row["flow_kip"])
            elif row["kind"] == "boundary_port_direction":
                sign = 1.0 if row["source"] == "EXTERNAL" else -1.0
                port_net += sign * float(row["flow_kip"])
                if row["upper_kip"] > 0:
                    maximum_port_utilization = max(maximum_port_utilization, row["flow_kip"] / row["upper_kip"])
            elif row["kind"] == "core_edge_direction" and row["upper_kip"] > 0:
                maximum_edge_utilization = max(maximum_edge_utilization, row["flow_kip"] / row["upper_kip"])
    aggregate_port_capacity = float(sum(port_caps.values()))
    return {
        "floor": floor,
        "feasible": bool(solved["feasible"]),
        "official_before_total_kip": before_total,
        "official_after_total_kip": after_total,
        "official_total_change_kip": total_change,
        "absolute_total_change_kip": abs(total_change),
        "mapped_edge_count": sum(value > 0.0 for value in edge_caps.values()),
        "aggregate_directed_core_edge_capacity_kip": float(sum(edge_caps.values())),
        "aggregate_symmetric_port_capacity_kip": aggregate_port_capacity,
        "net_port_capacity_necessary_condition_passed": abs(total_change) <= aggregate_port_capacity + 1e-7,
        "net_port_capacity_ratio_required": None if aggregate_port_capacity <= 0 else abs(total_change) / aggregate_port_capacity,
        "chosen_before_total_kip": chosen_before if solved["feasible"] else None,
        "chosen_after_total_kip": chosen_after if solved["feasible"] else None,
        "chosen_port_net_into_core_kip": port_net if solved["feasible"] else None,
        "maximum_core_edge_direction_utilization": maximum_edge_utilization if solved["feasible"] else None,
        "maximum_port_direction_utilization": maximum_port_utilization if solved["feasible"] else None,
        "feasibility_deficit_kip": float(solved["feasibility_deficit_kip"]),
        "port_mapping": port_meta,
    }


def run_cases(inputs: dict[str, Any], problem: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for edge_case in inputs["config"]["edge_cases"]:
        for port_case in inputs["config"]["port_cases"]:
            floor_rows = [
                floor_feasibility(inputs, problem, edge_case, port_case, int(floor))
                for floor in inputs["config"]["floors"]
            ]
            rows.append(
                {
                    "edge_case": edge_case,
                    "port_case": port_case,
                    "unknown_external_path": port_case["kind"] == "unknown_unbounded",
                    "unknown_internal_path": edge_case.get("kind") == "unknown_unbounded",
                    "feasible_floor_count": sum(row["feasible"] for row in floor_rows),
                    "all_seven_floors_feasible": all(row["feasible"] for row in floor_rows),
                    "aggregate_port_capacity_across_floors_kip": float(
                        sum(row["aggregate_symmetric_port_capacity_kip"] for row in floor_rows)
                    ),
                    "aggregate_core_edge_capacity_across_floors_kip": float(
                        sum(row["aggregate_directed_core_edge_capacity_kip"] for row in floor_rows)
                    ),
                    "floor_rows": floor_rows,
                }
            )
    return rows


def minimum_joint_multipliers(
    inputs: dict[str, Any], problem: dict[str, Any]
) -> list[dict[str, Any]]:
    edge_case = next(row for row in inputs["config"]["edge_cases"] if row["name"] == "orthogonal_upper_prefracture")
    port_case = next(row for row in inputs["config"]["port_cases"] if row["name"] == "intact_full_drop25")
    low_bound = float(inputs["config"]["sensitivity"]["minimum_joint_capacity_multiplier_low"])
    high_bound = float(inputs["config"]["sensitivity"]["minimum_joint_capacity_multiplier_high"])
    iterations = int(inputs["config"]["sensitivity"]["bisection_iterations"])
    rows: list[dict[str, Any]] = []
    for floor in inputs["config"]["floors"]:
        force_active = bool(
            floor == 93
            and inputs["config"]["sensitivity"]["extrapolate_intact_drop25_and_v8l_edges_to_floor93_for_multiplier_only"]
        )
        high_result = floor_feasibility(
            inputs,
            problem,
            edge_case,
            port_case,
            floor,
            port_multiplier=high_bound,
            force_port_active=force_active,
            edge_multiplier=high_bound,
            force_edge_active=force_active,
        )
        if not high_result["feasible"]:
            multiplier = None
            final_result = high_result
        else:
            low = low_bound
            high = high_bound
            for _ in range(iterations):
                middle = 0.5 * (low + high)
                result = floor_feasibility(
                    inputs,
                    problem,
                    edge_case,
                    port_case,
                    floor,
                    port_multiplier=middle,
                    force_port_active=force_active,
                    edge_multiplier=middle,
                    force_edge_active=force_active,
                )
                if result["feasible"]:
                    high = middle
                else:
                    low = middle
            multiplier = high
            final_result = floor_feasibility(
                inputs,
                problem,
                edge_case,
                port_case,
                floor,
                port_multiplier=high,
                force_port_active=force_active,
                edge_multiplier=high,
                force_edge_active=force_active,
            )
        rows.append(
            {
                "floor": floor,
                "minimum_joint_capacity_multiplier": multiplier,
                "floor93_edge_and_port_mapping_extrapolated": force_active,
                "official_absolute_total_change_kip": abs(
                    problem["totals"][floor]["after_impact"] - problem["totals"][floor]["before_impact"]
                ),
                "feasible_at_search_upper_bound": bool(high_result["feasible"]),
                "final_feasibility_deficit_kip": float(final_result["feasibility_deficit_kip"]),
            }
        )
    return rows


def summarize(inputs: dict[str, Any], problem: dict[str, Any], cases: list[dict[str, Any]], multipliers: list[dict[str, Any]]) -> dict[str, Any]:
    mapped = [
        row
        for row in cases
        if not row["unknown_external_path"] and not row["unknown_internal_path"]
    ]
    unknown = [
        row
        for row in cases
        if row["unknown_external_path"] or row["unknown_internal_path"]
    ]
    best_mapped = max(
        mapped,
        key=lambda row: (
            row["feasible_floor_count"],
            row["aggregate_port_capacity_across_floors_kip"],
            row["aggregate_core_edge_capacity_across_floors_kip"],
        ),
    )
    best_unknown = max(unknown, key=lambda row: row["feasible_floor_count"])
    per_floor_any = {
        str(floor): any(
            next(item for item in row["floor_rows"] if item["floor"] == floor)["feasible"]
            for row in mapped
        )
        for floor in inputs["config"]["floors"]
    }
    any_all = any(row["all_seven_floors_feasible"] for row in mapped)
    as_built_complete = False
    gates = {
        "mapped_bounded_case_all_seven_floors_feasible": any_all,
        "as_built_edge_and_connection_mapping_complete": as_built_complete,
        "unmapped_internal_or_external_path_required_for_all_floor_solution": (
            not any_all and any(row["all_seven_floors_feasible"] for row in unknown)
        ),
        "cold_capacity_gate_passed": bool(any_all and as_built_complete),
        "thermal_or_blender_authorized": False,
    }
    return {
        "case_count": len(cases),
        "mapped_bounded_case_count": len(mapped),
        "unknown_path_diagnostic_case_count": len(unknown),
        "best_mapped_case": best_mapped,
        "best_unknown_case": best_unknown,
        "any_mapped_case_feasible_by_floor": per_floor_any,
        "minimum_joint_multipliers": multipliers,
        "gates": gates,
    }


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
    image = Image.new("RGB", (1800, 1120), "white")
    draw = ImageDraw.Draw(image)
    navy = (24, 48, 78)
    blue = (48, 116, 156)
    orange = (226, 126, 34)
    red = (184, 55, 55)
    green = (55, 145, 95)
    grey = (105, 115, 125)
    pale = (237, 242, 246)
    draw.rectangle((0, 0, 1800, 112), fill=navy)
    draw.text((55, 25), "WTC 1 - V8R : circulation a capacites bornees", font=font(42, True), fill="white")
    draw.text((57, 78), "Les capacites V8L/V8M sont des enveloppes proxy, pas les Books 5/6 as-built", font=font(21), fill=(220, 230, 240))

    floors = result["configuration"]["floors"]
    best = result["summary"]["best_mapped_case"]
    floor_rows = best["floor_rows"]
    draw.text((80, 145), "Meilleur cas borne : changement total vs capacite externe", font=font(28, True), fill=navy)
    x0, y0, x1, y1 = 110, 220, 880, 790
    maximum = max(
        max(row["absolute_total_change_kip"], row["aggregate_symmetric_port_capacity_kip"])
        for row in floor_rows
    ) * 1.18
    for order, row in enumerate(floor_rows):
        y = y0 + 40 + order * 70
        width_change = row["absolute_total_change_kip"] / maximum * (x1 - x0 - 150)
        width_capacity = row["aggregate_symmetric_port_capacity_kip"] / maximum * (x1 - x0 - 150)
        draw.text((x0, y - 18), f"F{row['floor']}", font=font(21, True), fill=navy)
        draw.rectangle((x0 + 70, y - 18, x0 + 70 + width_change, y), fill=orange)
        draw.rectangle((x0 + 70, y + 7, x0 + 70 + width_capacity, y + 25), fill=blue)
        draw.text((x0 + 80 + max(width_change, width_capacity), y - 17), f"{row['absolute_total_change_kip']:.0f} / {row['aggregate_symmetric_port_capacity_kip']:.0f} kip", font=font(18), fill=navy)
        draw.ellipse((x1 - 35, y - 10, x1 - 13, y + 12), fill=green if row["feasible"] else red)
    draw.rectangle((x0 + 70, y1 + 5, x0 + 100, y1 + 22), fill=orange)
    draw.text((x0 + 110, y1), "changement officiel absolu", font=font(18), fill=grey)
    draw.rectangle((x0 + 365, y1 + 5, x0 + 395, y1 + 22), fill=blue)
    draw.text((x0 + 405, y1), "capacite externe", font=font(18), fill=grey)

    draw.text((980, 145), "Multiplicateur commun minimal : aretes + V8M a 25 in", font=font(28, True), fill=navy)
    mx0, my0, mx1, my1 = 1010, 225, 1690, 665
    draw.rectangle((mx0, my0, mx1, my1), outline=(195, 205, 215), width=2)
    max_multiplier = max(
        row["minimum_joint_capacity_multiplier"] or 0.0
        for row in result["summary"]["minimum_joint_multipliers"]
    ) * 1.15
    max_multiplier = max(max_multiplier, 1.0)
    for order, row in enumerate(result["summary"]["minimum_joint_multipliers"]):
        y = my0 + 35 + order * 53
        value = row["minimum_joint_capacity_multiplier"]
        draw.text((mx0 + 15, y - 10), f"F{row['floor']}", font=font(20, True), fill=navy)
        if value is not None:
            endpoint = mx0 + 75 + value / max_multiplier * (mx1 - mx0 - 140)
            draw.rectangle((mx0 + 75, y - 9, endpoint, y + 10), fill=blue if value <= 1.0 else red)
            draw.text((endpoint + 8, y - 11), f"x{value:.2f}", font=font(18), fill=navy)
        else:
            draw.text((mx0 + 85, y - 11), "non resolu", font=font(18), fill=red)
    draw.line((mx0 + 75 + (mx1 - mx0 - 140) / max_multiplier, my0, mx0 + 75 + (mx1 - mx0 - 140) / max_multiplier, my1), fill=grey, width=2)

    sx0, sy0, sx1, sy1 = 970, 720, 1710, 980
    draw.rounded_rectangle((sx0, sy0, sx1, sy1), radius=18, fill=pale, outline=(195, 205, 215), width=2)
    gates = result["summary"]["gates"]
    lines = [
        f"Cas testes : {result['summary']['case_count']}",
        f"Meilleur cas borne : {best['feasible_floor_count']} / 7 etages",
        f"Cas inconnu ouvert : {result['summary']['best_unknown_case']['feasible_floor_count']} / 7 etages",
        f"Un chemin interne/externe inconnu est requis : {'OUI' if gates['unmapped_internal_or_external_path_required_for_all_floor_solution'] else 'NON'}",
        f"Affectations as-built completes : {'OUI' if gates['as_built_edge_and_connection_mapping_complete'] else 'NON'}",
        f"Porte froide : {'PASS' if gates['cold_capacity_gate_passed'] else 'FAIL'}",
        "Thermique / Blender : NON AUTORISE",
    ]
    draw.text((sx0 + 30, sy0 + 24), "Diagnostic V8R", font=font(30, True), fill=navy)
    for position, line in enumerate(lines):
        color = red if "FAIL" in line or "NON AUTORISE" in line else navy
        draw.text((sx0 + 32, sy0 + 75 + position * 27), line, font=font(19, position >= 5), fill=color)

    draw.rectangle((0, 1020, 1800, 1120), fill=navy)
    draw.text((65, 1052), "Un echec borne signale un chemin modele insuffisant ; il ne demontre ni fraude des donnees ni demolition.", font=font(22), fill="white")
    image.save(PLOT_PATH)


def write_report(result: dict[str, Any]) -> None:
    summary = result["summary"]
    best = summary["best_mapped_case"]
    unknown = summary["best_unknown_case"]
    gates = summary["gates"]
    floor_table = "\n".join(
        f"| {row['floor']} | {row['official_total_change_kip']:+.0f} | {row['aggregate_symmetric_port_capacity_kip']:.1f} | {'oui' if row['net_port_capacity_necessary_condition_passed'] else 'non'} | {'PASS' if row['feasible'] else 'FAIL'} | {row['feasibility_deficit_kip']:.1f} |"
        for row in best["floor_rows"]
    )
    multiplier_table = "\n".join(
        f"| {row['floor']} | {('non résolu' if row['minimum_joint_capacity_multiplier'] is None else f'{row['minimum_joint_capacity_multiplier']:.3f}')} | {'oui, sensibilité seulement' if row['floor93_edge_and_port_mapping_extrapolated'] else 'non'} |"
        for row in summary["minimum_joint_multipliers"]
    )
    case_cards = sorted(
        [
            row
            for row in result["case_rows"]
            if not row["unknown_external_path"] and not row["unknown_internal_path"]
        ],
        key=lambda row: (row["feasible_floor_count"], row["aggregate_port_capacity_across_floors_kip"]),
        reverse=True,
    )[:10]
    case_table = "\n".join(
        f"| {row['edge_case']['name']} | {row['port_case']['name']} | {row['feasible_floor_count']}/7 |"
        for row in case_cards
    )
    report = f"""# WTC 1 - V8R : audit de circulation à capacités bornées

## Conclusion

V8R ferme la liberté mathématique illimitée de V8Q et teste **{summary['case_count']} combinaisons exactes** de circulation avec intervalles de charge, capacités d'arêtes et capacités externes. Le meilleur cas borné ne satisfait que **{best['feasible_floor_count']} étage(s) sur 7**. Un cas diagnostique laissant ouverts les chemins internes et externes inconnus en satisfait **{unknown['feasible_floor_count']} sur 7**.

La porte froide reste **FAIL** : aucune combinaison V8L/V8M bornée ne couvre simultanément les sept étages, les affectations as-built des poutres et assemblages restent absentes, et les chemins internes/externes non publiés demeurent déterminants. Ce résultat ne démontre ni que les données NIST sont truquées, ni qu'une démolition a eu lieu ; il montre précisément quelle capacité manque dans le modèle réduit.

## 1. Faits et résultats officiels utilisés

- Les intervalles avant/après impact et les sommes des Floors 93-99 viennent de la numérisation V8P des sorties NIST.
- Les 17 arêtes `nist_moment_only` sont une transcription du sous-réseau de poutres de moment du modèle officiel.
- Le graphe orthogonal de 79 arêtes est une reconstruction contrainte par figures, pas le Book 5 as-built.
- NIST indique que son noyau Case B isolé ne capturait pas les transferts via planchers, façades et hat truss.

## 2. Affirmations des archives locales

Aucune nouvelle affirmation provenant des vidéos, affiches ou archives militantes n'est utilisée dans les équations V8R. Les archives originales sont restées en lecture seule.

## 3. Hypothèses de capacité

1. Les profils 12WF65, 14WF136 et 14WF228 encadrent les poutres, mais leur affectation réelle aux arêtes n'est pas connue.
2. Les forces d'arête sont plafonnées soit à l'écoulement, soit juste avant la rotation de rupture de 0,02 rad de la loi V8L.
3. Les arêtes retirées par la figure de dommage V8L au Floor 96 ont une capacité nulle.
4. Les ports externes emploient uniquement la composante verticale calculée par V8M pour 2, 5, 12 ou 25 in. Les limites 44/94 kip ne sont jamais posées directement comme ressorts verticaux.
5. Le signe symétrique des ports est une borne optimiste ; la compatibilité directionnelle réelle n'est pas reconstruite.
6. Le Floor 93 ne reçoit aucune capacité V8L/V8M extrapolée dans l'audit principal.

## 4. Meilleur cas borné

- Arêtes : `{best['edge_case']['name']}`.
- Ports : `{best['port_case']['name']}`.
- Étages faisables : **{best['feasible_floor_count']}/7**.

| Étage | Variation totale officielle (kip) | Capacité externe symétrique (kip) | Condition nette | Circulation | Déficit (kip) |
|---:|---:|---:|---:|---:|---:|
{floor_table}

Les transferts internes peuvent redistribuer la charge entre colonnes, mais ils ne peuvent pas changer la somme du noyau. La différence totale avant/après doit nécessairement passer par un port externe. Cette condition de coupe explique une grande partie des échecs avant même les détails locaux.

## 5. Sensibilité : multiplicateur commun minimal des arêtes et de V8M à 25 in

La table suivante multiplie simultanément les arêtes orthogonales supérieures juste avant rupture et les ports V8M à 25 in. Pour le Floor 93 seulement, les deux enveloppes sont extrapolées comme sensibilité et ne deviennent pas des données as-built.

| Étage | Multiplicateur minimal | Extrapolation Floor 93 |
|---:|---:|---:|
{multiplier_table}

Un multiplicateur supérieur à 1 signifie que l'ensemble arêtes plus ports, à leurs enveloppes préenregistrées, reste insuffisant pour trouver un état dans tous les intervalles.

## 6. Dix meilleures combinaisons bornées

| Arêtes | Ports | Étages faisables |
|---|---|---:|
{case_table}

## 7. Portes de décision

- Un cas borné cartographié couvre les sept étages : **{'PASS' if gates['mapped_bounded_case_all_seven_floors_feasible'] else 'FAIL'}**.
- Affectations as-built complètes : **{'PASS' if gates['as_built_edge_and_connection_mapping_complete'] else 'FAIL'}**.
- Le cas complet exige un chemin interne ou externe inconnu : **{'OUI' if gates['unmapped_internal_or_external_path_required_for_all_floor_solution'] else 'NON'}**.
- Porte froide globale : **{'PASS' if gates['cold_capacity_gate_passed'] else 'FAIL'}**.
- Thermique et Blender : **NON AUTORISÉS**.

## 8. Contradictions et informations manquantes

- V8R ne trouve pas de contradiction algébrique avec les intervalles NIST : l'ouverture conjointe des chemins internes et externes inconnus peut restaurer une solution.
- En revanche, les seules enveloppes bornées V8L/V8M documentées dans le harnais ne reproduisent pas les sept états simultanément.
- Le profil exact de chaque poutre, les connexions Book 6, la dalle composite, le diaphragme complet, les liaisons aux façades et leur réponse transitoire restent manquants.
- Le choix optimal n'est pas une preuve de capacité réelle : même le cas supérieur utilise des profils proxy et une distribution uniforme des capacités de face.
- Aucune conclusion sur des explosifs ou la thermite n'est permise par ce test de capacité.

## 9. Impact de l'avion : jalon conservé

La reconstitution d'impact reste obligatoire dans la feuille de route. Elle devra utiliser la masse, la vitesse, l'assiette, l'angle, les étages d'impact et la géométrie officielle, puis comparer les dommages de façade et de noyau. Les images de sortie de la façade opposée devront distinguer le fuselage des moteurs, du train, du carburant et des fragments. Blender ne sera utilisé que pour visualiser une dynamique calculée ailleurs.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def round_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: round_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [round_tree(item) for item in value]
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return round(number, 9) if math.isfinite(number) else str(number)
    if isinstance(value, np.integer):
        return int(value)
    return value


def validation_checks(
    inputs: dict[str, Any],
    cases: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    fully_open = next(
        row
        for row in cases
        if row["unknown_internal_path"] and row["unknown_external_path"]
    )
    exact_total_residuals: list[float] = []
    exact_port_residuals: list[float] = []
    for row in fully_open["floor_rows"]:
        if row["feasible"]:
            exact_total_residuals.extend(
                [
                    abs(float(row["chosen_before_total_kip"]) - float(row["official_before_total_kip"])),
                    abs(float(row["chosen_after_total_kip"]) - float(row["official_after_total_kip"])),
                ]
            )
            exact_port_residuals.append(
                abs(float(row["chosen_port_net_into_core_kip"]) - float(row["official_total_change_kip"]))
            )
    checks = {
        "expected_case_count": len(inputs["config"]["edge_cases"]) * len(inputs["config"]["port_cases"]),
        "actual_case_count": len(cases),
        "case_count_matches_configuration": len(cases)
        == len(inputs["config"]["edge_cases"]) * len(inputs["config"]["port_cases"]),
        "fully_open_diagnostic_all_floors_feasible": fully_open["all_seven_floors_feasible"],
        "fully_open_maximum_official_total_residual_kip": max(exact_total_residuals, default=0.0),
        "fully_open_maximum_port_sum_residual_kip": max(exact_port_residuals, default=0.0),
        "all_joint_multiplier_searches_bracketed": all(
            row["feasible_at_search_upper_bound"]
            and row["minimum_joint_capacity_multiplier"] is not None
            for row in summary["minimum_joint_multipliers"]
        ),
        "mapped_cases_do_not_use_unknown_paths": all(
            not row["unknown_internal_path"] and not row["unknown_external_path"]
            for row in cases
            if not row["unknown_internal_path"] and not row["unknown_external_path"]
        ),
    }
    critical = [
        checks["case_count_matches_configuration"],
        checks["fully_open_diagnostic_all_floors_feasible"],
        checks["fully_open_maximum_official_total_residual_kip"] <= 1e-7,
        checks["fully_open_maximum_port_sum_residual_kip"] <= 1e-7,
        checks["all_joint_multiplier_searches_bracketed"],
    ]
    checks["all_critical_checks_passed"] = all(critical)
    if not checks["all_critical_checks_passed"]:
        raise RuntimeError(f"V8R validation failed: {checks}")
    return checks


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    problem = build_problem(inputs)
    cases = run_cases(inputs, problem)
    multipliers = minimum_joint_multipliers(inputs, problem)
    summary = summarize(inputs, problem, cases, multipliers)
    checks = validation_checks(inputs, cases, summary)
    result = {
        "dataset": inputs["config"]["dataset"],
        "run": {
            "iteration": "V8R",
            "timestamp_local": datetime.now().astimezone().isoformat(),
            "elapsed_seconds": time.perf_counter() - started,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "deterministic": True,
        },
        "sources": inputs["config"]["official_facts"],
        "configuration": inputs["config"],
        "topology": {
            "column_count": len(problem["columns"]),
            "moment_edge_count": len(problem["topologies"]["nist_moment_only"]),
            "orthogonal_edge_count": len(problem["topologies"]["orthogonal_floor96_reconstruction"]),
            "boundary_port_column_count": len(problem["boundary"]),
            "boundary_port_columns": problem["boundary"],
            "face_columns": problem["face_columns"],
            "floor96_removed_edges": [list(edge) for edge in sorted(problem["damaged_floor96"])],
        },
        "case_rows": cases,
        "summary": summary,
        "validation_checks": checks,
        "interpretation": {
            "result": "No mapped bounded V8L/V8M proxy case covers all seven V8P floors. Opening both unknown internal and external paths diagnoses whether omitted coupling restores algebraic feasibility, but it is not a mechanical validation.",
            "scope_limit": "This is a static necessary-capacity circulation audit. It does not enforce a common displacement field, dynamic impact equilibrium, thermal history, or as-built connection schedule.",
            "demolition_inference": "None. A missing bounded path in a reduced official-output emulator is not evidence of demolition or data fabrication.",
            "impact_replay": inputs["config"]["future_impact_replay"],
        },
    }
    result = round_tree(result)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(result)
    draw_plot(result)
    print(
        json.dumps(
            {
                "result": str(RESULT_PATH),
                "report": str(REPORT_PATH),
                "plot": str(PLOT_PATH),
                "case_count": result["summary"]["case_count"],
                "best_mapped_feasible_floors": result["summary"]["best_mapped_case"]["feasible_floor_count"],
                "best_unknown_feasible_floors": result["summary"]["best_unknown_case"]["feasible_floor_count"],
                "gates": result["summary"]["gates"],
                "multipliers": result["summary"]["minimum_joint_multipliers"],
                "elapsed_seconds": result["run"]["elapsed_seconds"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
