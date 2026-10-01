"""WTC 1 V8I-A - bounded cracked-slab catenary on the V8H core network.

V8I keeps the V8H column and beam laws, then adds a geometrically nonlinear,
reinforcement-only membrane spring in parallel with every connected proxy edge.
The membrane is deliberately capped by reinforcement yield and ultimate strain.
It is a reduced-order sensitivity envelope, not an as-built floor model.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8b_stability_network as v8b  # noqa: E402
import run_v8f_vertical_load_path as v8f  # noqa: E402
import run_v8h_mechanical_core_transfer as v8h  # noqa: E402


CONFIG = V8 / "data" / "v8i_core_slab_catenary.json"
TRANSFER = V8 / "data" / "nist_wtc1_transfer.json"
AISC = V8 / "data" / "aisc_historic_wf_properties.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8i_dalle_catenary.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8i_dalle_catenary.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8i_dalle_catenary.png"

FLOORS_DESC = list(range(99, 93, -1))
TIMES = [20, 40, 60]
TIME_INDEX = {20: 0, 40: 1, 60: 2}
GAMMAS = [1.0, 2.0]
SEEDS = list(range(100))
TAIL = "linear_to_5pct_at_1000c"
BEAM_PROFILE = "14WF136"
BEAM_CONNECTION_FACTOR = 1.0
BEAM_ACTIVE_PLANES = 2
BEAM_TEMPERATURE_POLICY = "mean_endpoint_column_temperature_proxy"
SLAB_THICKNESS_IN = 4.5
M_TO_IN = 39.37007874015748
LOAD_STEPS = 10
MAX_ACTIVE_SET_ITERATIONS = 160


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return a monotone-chain convex hull without a repeated end point."""
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(
        origin: tuple[float, float],
        first: tuple[float, float],
        second: tuple[float, float],
    ) -> float:
        return (first[0] - origin[0]) * (second[1] - origin[1]) - (
            first[1] - origin[1]
        ) * (second[0] - origin[0])

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    return 0.5 * abs(
        sum(
            points[index][0] * points[(index + 1) % len(points)][1]
            - points[(index + 1) % len(points)][0] * points[index][1]
            for index in range(len(points))
        )
    )


def area_normalized_width_m(
    coords: dict[int, tuple[float, float]],
    edges: list[tuple[int, int]],
    active_area_fraction: float,
) -> tuple[float, float, float]:
    """Return strip width, convex-hull area, and summed network edge length.

    The factor two represents two reinforcement directions.  This conserves a
    declared amount of slab/reinforcement volume over the isotropic proxy graph;
    it does not identify a physical strip belonging to an individual edge.
    """
    area_m2 = polygon_area(convex_hull(list(coords.values())))
    edge_length_sum_m = sum(math.dist(coords[i], coords[j]) for i, j in edges)
    width_m = (
        2.0 * area_m2 * active_area_fraction / edge_length_sum_m
        if active_area_fraction > 0.0 and edge_length_sum_m > 0.0
        else 0.0
    )
    return width_m, area_m2, edge_length_sum_m


def membrane_law(
    length_m: float,
    effective_width_m: float,
    reinforcement_ratio: float,
    wire_yield_ksi_rt: float,
    ultimate_strain: float,
    temperature_c: float,
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, float]:
    length_in = length_m * M_TO_IN
    width_in = effective_width_m * M_TO_IN
    steel_area_in2 = width_in * SLAB_THICKNESS_IN * reinforcement_ratio
    e_ksi = v8b.elastic_modulus_ksi(temperature_c, e_params, TAIL)
    fy_ksi = wire_yield_ksi_rt * v8b.yield_ratio(temperature_c, fy_params)
    axial_yield_kip = steel_area_in2 * fy_ksi
    yield_strain = fy_ksi / max(e_ksi, 1e-12) if steel_area_in2 > 0.0 else 0.0
    ultimate_delta_in = (
        length_in * math.sqrt(max(0.0, (1.0 + ultimate_strain) ** 2 - 1.0))
        if ultimate_strain > 0.0
        else 0.0
    )
    return {
        "length_in": length_in,
        "effective_width_in": width_in,
        "slab_thickness_in": SLAB_THICKNESS_IN,
        "reinforcement_ratio": reinforcement_ratio,
        "steel_area_in2": steel_area_in2,
        "temperature_c": temperature_c,
        "e_ksi": e_ksi,
        "fy_ksi": fy_ksi,
        "yield_strain": yield_strain,
        "axial_yield_kip": axial_yield_kip,
        "ultimate_strain": ultimate_strain,
        "ultimate_delta_in": ultimate_delta_in,
    }


def membrane_state_at_delta(
    delta_in: float,
    law: dict[str, float],
) -> dict[str, float | bool]:
    length_in = float(law["length_in"])
    steel_area_in2 = float(law["steel_area_in2"])
    if length_in <= 0.0 or steel_area_in2 <= 0.0:
        return {
            "fractured": True,
            "strain": 0.0,
            "axial_force_kip": 0.0,
            "vertical_force_kip": 0.0,
            "secant_kip_per_in": 0.0,
            "yielded": False,
        }
    stretched_in = math.hypot(length_in, delta_in)
    strain = stretched_in / length_in - 1.0
    fractured = strain > float(law["ultimate_strain"]) * (1.0 + 1e-9)
    if fractured:
        return {
            "fractured": True,
            "strain": strain,
            "axial_force_kip": 0.0,
            "vertical_force_kip": 0.0,
            "secant_kip_per_in": 0.0,
            "yielded": True,
        }
    elastic_axial_kip = float(law["e_ksi"]) * steel_area_in2 * strain
    axial_force_kip = min(elastic_axial_kip, float(law["axial_yield_kip"]))
    vertical_force_kip = axial_force_kip * delta_in / max(stretched_in, 1e-12)
    secant = axial_force_kip / max(stretched_in, 1e-12)
    return {
        "fractured": False,
        "strain": strain,
        "axial_force_kip": axial_force_kip,
        "vertical_force_kip": vertical_force_kip,
        "secant_kip_per_in": secant,
        "yielded": strain >= float(law["yield_strain"]),
    }


def disconnected_reason(
    loads: np.ndarray,
    load_factor: float,
    nodes: list[int],
    survivors: set[int],
    edges: list[dict[str, object]],
) -> str | None:
    index = {column: position for position, column in enumerate(nodes)}
    adjacency = {column: set() for column in nodes}
    for edge in edges:
        if edge["beam_state"] == "fractured" and edge["membrane_state"] == "fractured":
            continue
        i, j = int(edge["i"]), int(edge["j"])
        adjacency[i].add(j)
        adjacency[j].add(i)
    unseen = set(nodes)
    load_scale = max(float(np.sum(np.abs(loads))) * load_factor, 1.0)
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        if component.isdisjoint(survivors):
            resultant = load_factor * sum(float(loads[index[column]]) for column in component)
            if abs(resultant) > 1e-9 * load_scale:
                return "disconnected_loaded_component"
    return None


def assemble_composite(
    loads: np.ndarray,
    load_factor: float,
    nodes: list[int],
    survivors: set[int],
    column_stiffness: dict[int, float],
    edges: list[dict[str, object]],
    trial_displacement: np.ndarray,
) -> tuple[np.ndarray | None, str | None]:
    reason = disconnected_reason(loads, load_factor, nodes, survivors, edges)
    if reason is not None:
        return None, reason
    size = len(nodes)
    index = {column: position for position, column in enumerate(nodes)}
    matrix = np.zeros((size, size), dtype=float)
    rhs = load_factor * loads.copy()
    for column in survivors:
        matrix[index[column], index[column]] += column_stiffness[column]
    for edge in edges:
        i_column, j_column = int(edge["i"]), int(edge["j"])
        i, j = index[i_column], index[j_column]
        if edge["beam_state"] != "fractured":
            beam_stiffness = float(edge["beam_stiffness"])
            constant = 0.0
            if edge["beam_state"] == "plastic":
                tangent = v8h.HARDENING_RATIO * beam_stiffness
                constant = float(edge["beam_sign"]) * (
                    float(edge["beam_capacity"])
                    - tangent * float(edge["beam_yield_displacement"])
                )
            else:
                tangent = beam_stiffness
            matrix[i, i] += tangent
            matrix[j, j] += tangent
            matrix[i, j] -= tangent
            matrix[j, i] -= tangent
            rhs[i] -= constant
            rhs[j] += constant
        if edge["membrane_state"] != "fractured":
            delta = float(trial_displacement[i] - trial_displacement[j])
            membrane = membrane_state_at_delta(delta, edge["membrane_law"])
            tangent = float(membrane["secant_kip_per_in"])
            matrix[i, i] += tangent
            matrix[j, j] += tangent
            matrix[i, j] -= tangent
            matrix[j, i] -= tangent
    try:
        displacement = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        return None, "singular_composite_network"
    if not np.all(np.isfinite(displacement)):
        return None, "non_finite_displacement"
    return displacement, None


def residual_and_tangent(
    loads: np.ndarray,
    load_factor: float,
    nodes: list[int],
    survivors: set[int],
    column_stiffness: dict[int, float],
    edges: list[dict[str, object]],
    displacement: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return nonlinear residual and exact tangent for the current active set."""
    size = len(nodes)
    index = {column: position for position, column in enumerate(nodes)}
    residual = -load_factor * loads.copy()
    tangent_matrix = np.zeros((size, size), dtype=float)
    for column in survivors:
        position = index[column]
        stiffness = column_stiffness[column]
        residual[position] += stiffness * displacement[position]
        tangent_matrix[position, position] += stiffness
    for edge in edges:
        i = index[int(edge["i"])]
        j = index[int(edge["j"])]
        delta = float(displacement[i] - displacement[j])
        force = 0.0
        tangent = 0.0
        if edge["beam_state"] != "fractured":
            beam_stiffness = float(edge["beam_stiffness"])
            if edge["beam_state"] == "plastic":
                beam_tangent = v8h.HARDENING_RATIO * beam_stiffness
                beam_force = beam_tangent * delta + float(edge["beam_sign"]) * (
                    float(edge["beam_capacity"])
                    - beam_tangent * float(edge["beam_yield_displacement"])
                )
            else:
                beam_tangent = beam_stiffness
                beam_force = beam_stiffness * delta
            force += beam_force
            tangent += beam_tangent
        if edge["membrane_state"] != "fractured":
            law = edge["membrane_law"]
            length_in = float(law["length_in"])
            stretched_in = math.hypot(length_in, delta)
            strain = stretched_in / length_in - 1.0
            elastic_axial = float(law["e_ksi"]) * float(law["steel_area_in2"]) * strain
            axial_yield = float(law["axial_yield_kip"])
            axial_force = min(elastic_axial, axial_yield)
            membrane_force = axial_force * delta / max(stretched_in, 1e-12)
            if elastic_axial < axial_yield:
                axial_tangent = (
                    float(law["e_ksi"])
                    * float(law["steel_area_in2"])
                    * delta
                    / max(length_in * stretched_in, 1e-12)
                )
            else:
                axial_tangent = 0.0
            membrane_tangent = (
                axial_tangent * delta / max(stretched_in, 1e-12)
                + axial_force * length_in**2 / max(stretched_in**3, 1e-12)
            )
            force += membrane_force
            tangent += membrane_tangent
        residual[i] += force
        residual[j] -= force
        tangent_matrix[i, i] += tangent
        tangent_matrix[j, j] += tangent
        tangent_matrix[i, j] -= tangent
        tangent_matrix[j, i] -= tangent
    return residual, tangent_matrix


def update_edge_states(
    edges: list[dict[str, object]],
    nodes: list[int],
    displacement: np.ndarray,
    prefractured_beams: set[tuple[int, int]],
    prefractured_membranes: set[tuple[int, int]],
) -> bool:
    index = {column: position for position, column in enumerate(nodes)}
    changed = False
    for edge in edges:
        i, j = index[int(edge["i"])], index[int(edge["j"])]
        delta = float(displacement[i] - displacement[j])
        key = tuple(sorted((int(edge["i"]), int(edge["j"]))))
        if edge["beam_state"] == "elastic" and abs(delta) > float(
            edge["beam_yield_displacement"]
        ) * (1.0 + 1e-8):
            edge["beam_state"] = "plastic"
            edge["beam_sign"] = 1.0 if delta >= 0.0 else -1.0
            changed = True
        if edge["beam_state"] == "plastic" and abs(delta) > float(
            edge["beam_ultimate_displacement"]
        ):
            edge["beam_state"] = "fractured"
            prefractured_beams.add(key)
            changed = True
        if edge["membrane_state"] != "fractured":
            membrane = membrane_state_at_delta(delta, edge["membrane_law"])
            if bool(membrane["fractured"]):
                edge["membrane_state"] = "fractured"
                prefractured_membranes.add(key)
                changed = True
    return changed


def solve_composite_network(
    loads_by_column: dict[int, float],
    survivors: set[int],
    column_stiffness: dict[int, float],
    edge_definitions: list[dict[str, object]],
    prefractured_beams: set[tuple[int, int]],
    prefractured_membranes: set[tuple[int, int]],
    initial_displacements: dict[int, float] | None = None,
) -> dict[str, object]:
    nodes = sorted(loads_by_column)
    index = {column: position for position, column in enumerate(nodes)}
    loads = np.array([float(loads_by_column[column]) for column in nodes], dtype=float)
    edges: list[dict[str, object]] = []
    for row in edge_definitions:
        key = tuple(sorted((int(row["i"]), int(row["j"]))))
        no_membrane = float(row["membrane_law"]["steel_area_in2"]) <= 0.0
        edges.append(
            {
                **row,
                "beam_state": "fractured" if key in prefractured_beams else "elastic",
                "beam_sign": 0.0,
                "membrane_state": (
                    "fractured" if key in prefractured_membranes or no_membrane else "active"
                ),
            }
        )

    initial_displacements = initial_displacements or {}
    initial_vector = np.array(
        [float(initial_displacements.get(column, 0.0)) for column in nodes], dtype=float
    )
    displacement = np.zeros(len(nodes), dtype=float)
    for load_factor in np.linspace(1.0 / LOAD_STEPS, 1.0, LOAD_STEPS):
        if float(load_factor) <= 1.0 / LOAD_STEPS + 1e-12:
            displacement = float(load_factor) * initial_vector
        for _iteration in range(MAX_ACTIVE_SET_ITERATIONS):
            update_edge_states(
                edges,
                nodes,
                displacement,
                prefractured_beams,
                prefractured_membranes,
            )
            reason = disconnected_reason(loads, float(load_factor), nodes, survivors, edges)
            if reason is not None:
                return {
                    "equilibrium": False,
                    "reason": reason,
                    "fractured_beams": sorted(prefractured_beams),
                    "fractured_membranes": sorted(prefractured_membranes),
                }
            residual, tangent_matrix = residual_and_tangent(
                loads,
                float(load_factor),
                nodes,
                survivors,
                column_stiffness,
                edges,
                displacement,
            )
            load_scale = max(float(np.linalg.norm(loads, ord=np.inf)) * load_factor, 1.0)
            residual_norm = float(np.linalg.norm(residual, ord=np.inf)) / load_scale
            if residual_norm < 1e-8:
                break
            try:
                correction = np.linalg.solve(tangent_matrix, -residual)
            except np.linalg.LinAlgError:
                return {
                    "equilibrium": False,
                    "reason": "singular_composite_tangent",
                    "fractured_beams": sorted(prefractured_beams),
                    "fractured_membranes": sorted(prefractured_membranes),
                }
            # Avoid stepping across several fracture surfaces at once.  The
            # limit is geometric (5 percent of the shortest active edge) and
            # only controls Newton continuation, not member capacity.
            shortest_edge_in = min(
                float(edge["membrane_law"]["length_in"]) for edge in edges
            )
            maximum_step = 0.05 * shortest_edge_in
            correction_peak = float(np.max(np.abs(correction)))
            if correction_peak > maximum_step:
                correction *= maximum_step / correction_peak
            accepted = False
            for line_search in range(9):
                alpha = 0.5**line_search
                candidate = displacement + alpha * correction
                candidate_residual, _ = residual_and_tangent(
                    loads,
                    float(load_factor),
                    nodes,
                    survivors,
                    column_stiffness,
                    edges,
                    candidate,
                )
                candidate_norm = float(
                    np.linalg.norm(candidate_residual, ord=np.inf)
                ) / load_scale
                if candidate_norm < residual_norm or line_search == 8:
                    displacement = candidate
                    accepted = True
                    break
            if not accepted:
                return {
                    "equilibrium": False,
                    "reason": "composite_newton_line_search_failed",
                    "fractured_beams": sorted(prefractured_beams),
                    "fractured_membranes": sorted(prefractured_membranes),
                }
        else:
            return {
                "equilibrium": False,
                "reason": "composite_newton_not_converged",
                "fractured_beams": sorted(prefractured_beams),
                "fractured_membranes": sorted(prefractured_membranes),
            }

    reactions = {
        column: column_stiffness[column] * displacement[index[column]]
        for column in survivors
    }
    edge_states: list[dict[str, object]] = []
    for edge in edges:
        i_column, j_column = int(edge["i"]), int(edge["j"])
        delta = float(displacement[index[i_column]] - displacement[index[j_column]])
        membrane = membrane_state_at_delta(delta, edge["membrane_law"])
        if edge["membrane_state"] == "fractured":
            membrane_force = 0.0
            membrane_yielded = (
                float(edge["membrane_law"]["steel_area_in2"]) > 0.0
            )
        else:
            membrane_force = float(membrane["vertical_force_kip"])
            membrane_yielded = bool(membrane["yielded"])
        edge_states.append(
            {
                "i": i_column,
                "j": j_column,
                "beam_state": edge["beam_state"],
                "membrane_state": edge["membrane_state"],
                "membrane_yielded": membrane_yielded,
                "membrane_vertical_force_kip": membrane_force,
                "membrane_strain": float(membrane["strain"]),
                "relative_displacement_in": delta,
            }
        )
    reaction_total = sum(reactions.values())
    load_total = float(loads.sum())
    relative_residual = abs(reaction_total - load_total) / max(abs(load_total), 1e-9)
    return {
        "equilibrium": relative_residual < 1e-6,
        "reason": "stable" if relative_residual < 1e-6 else "force_residual",
        "reactions": reactions,
        "displacements": {
            column: float(displacement[index[column]]) for column in nodes
        },
        "edge_states": edge_states,
        "fractured_beams": sorted(prefractured_beams),
        "fractured_membranes": sorted(prefractured_membranes),
        "plastic_beam_count": sum(row["beam_state"] == "plastic" for row in edge_states),
        "fractured_beam_count": sum(row["beam_state"] == "fractured" for row in edge_states),
        "yielded_membrane_count": sum(bool(row["membrane_yielded"]) for row in edge_states),
        "fractured_membrane_count": sum(row["membrane_state"] == "fractured" for row in edge_states),
        "maximum_membrane_strain": max(
            (float(row["membrane_strain"]) for row in edge_states), default=0.0
        ),
        "maximum_abs_displacement_in": float(np.max(np.abs(displacement))),
        "relative_force_residual": relative_residual,
    }


def story_response(
    incoming_loads: dict[int, float],
    temperatures: dict[int, float],
    sections: dict[int, dict[str, float | str]],
    removed: set[int],
    coords: dict[int, tuple[float, float]],
    edges: list[tuple[int, int]],
    beam_shape: dict[str, float | str],
    slab_case: dict[str, object],
    slab_width_m: float,
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, object]:
    nodal_loads = {
        column: float(incoming_loads.get(column, 0.0)) for column in sections
    }
    survivors = set(sections) - set(removed)
    prefractured_beams: set[tuple[int, int]] = set()
    prefractured_membranes: set[tuple[int, int]] = set()
    failed_columns: list[int] = []
    maximum_dcr = 0.0
    maximum_displacement = 0.0
    maximum_membrane_strain = 0.0
    maximum_yielded_membranes = 0
    maximum_fractured_membranes = 0
    maximum_fractured_beams = 0
    displacement_guess: dict[int, float] = {}
    for _cascade in range(len(sections) + 1):
        column_stiffness = {
            column: v8b.elastic_modulus_ksi(temperatures[column], e_params, TAIL)
            * float(sections[column]["area_in2"])
            / v8h.STORY_LENGTH_IN
            for column in survivors
        }
        capacities = {
            column: v8b.nominal_column_capacity_kip(
                sections[column], temperatures[column], 1.0, fy_params, e_params, TAIL
            )
            for column in survivors
        }
        edge_definitions: list[dict[str, object]] = []
        for i, j in edges:
            length_m = math.dist(coords[i], coords[j])
            beam_temperature = 0.5 * (temperatures[i] + temperatures[j])
            beam = v8h.beam_law(
                beam_shape,
                length_m,
                beam_temperature,
                BEAM_CONNECTION_FACTOR,
                BEAM_ACTIVE_PLANES,
                fy_params,
                e_params,
            )
            if slab_case["temperature_policy"] == "cold_20c_upper_bound":
                slab_temperature = 20.0
            else:
                slab_temperature = 0.5 * (temperatures[i] + temperatures[j])
            membrane = membrane_law(
                length_m,
                slab_width_m,
                float(slab_case["reinforcement_ratio"]),
                float(slab_case["wire_yield_ksi_rt"]),
                float(slab_case["ultimate_strain"]),
                slab_temperature,
                fy_params,
                e_params,
            )
            edge_definitions.append(
                {
                    "i": i,
                    "j": j,
                    "beam_stiffness": beam["initial_stiffness_kip_per_in"],
                    "beam_capacity": beam["yield_force_kip"],
                    "beam_yield_displacement": beam["yield_displacement_in"],
                    "beam_ultimate_displacement": beam["ultimate_displacement_in"],
                    "membrane_law": membrane,
                }
            )
        state = solve_composite_network(
            nodal_loads,
            survivors,
            column_stiffness,
            edge_definitions,
            prefractured_beams,
            prefractured_membranes,
            displacement_guess,
        )
        maximum_displacement = max(
            maximum_displacement, float(state.get("maximum_abs_displacement_in", 0.0))
        )
        maximum_membrane_strain = max(
            maximum_membrane_strain, float(state.get("maximum_membrane_strain", 0.0))
        )
        maximum_yielded_membranes = max(
            maximum_yielded_membranes, int(state.get("yielded_membrane_count", 0))
        )
        maximum_fractured_membranes = max(
            maximum_fractured_membranes, len(state.get("fractured_membranes", []))
        )
        maximum_fractured_beams = max(
            maximum_fractured_beams, len(state.get("fractured_beams", []))
        )
        if not state["equilibrium"]:
            return {
                "equilibrium": False,
                "reason": state["reason"],
                "failed_columns": failed_columns,
                "failed_count": len(failed_columns),
                "surviving_count": len(survivors),
                "maximum_dcr_during_cascade": maximum_dcr,
                "maximum_abs_displacement_in": maximum_displacement,
                "maximum_membrane_strain": maximum_membrane_strain,
                "maximum_yielded_membrane_count": maximum_yielded_membranes,
                "maximum_fractured_membrane_count": maximum_fractured_membranes,
                "maximum_fractured_beam_count": maximum_fractured_beams,
            }
        displacement_guess = {
            int(key): float(value) for key, value in state["displacements"].items()
        }
        reactions = {int(key): float(value) for key, value in state["reactions"].items()}
        dcr = {
            column: max(0.0, reactions.get(column, 0.0)) / max(capacities[column], 1e-12)
            for column in survivors
        }
        peak = max(dcr.values()) if dcr else float("inf")
        maximum_dcr = max(maximum_dcr, peak)
        if peak <= 1.0:
            return {
                "equilibrium": True,
                "reason": "stable",
                "final_loads": reactions,
                "failed_columns": failed_columns,
                "failed_count": len(failed_columns),
                "surviving_count": len(survivors),
                "final_peak_dcr": peak,
                "maximum_dcr_during_cascade": maximum_dcr,
                "maximum_abs_displacement_in": maximum_displacement,
                "maximum_membrane_strain": maximum_membrane_strain,
                "maximum_yielded_membrane_count": maximum_yielded_membranes,
                "maximum_fractured_membrane_count": maximum_fractured_membranes,
                "maximum_fractured_beam_count": maximum_fractured_beams,
            }
        failed = max(dcr, key=dcr.get)
        survivors.remove(failed)
        failed_columns.append(failed)
        if not survivors:
            break
    return {
        "equilibrium": False,
        "reason": "cascade_exhausted_survivors",
        "failed_columns": failed_columns,
        "failed_count": len(failed_columns),
        "surviving_count": 0,
        "maximum_dcr_during_cascade": maximum_dcr,
        "maximum_abs_displacement_in": maximum_displacement,
        "maximum_membrane_strain": maximum_membrane_strain,
        "maximum_yielded_membrane_count": maximum_yielded_membranes,
        "maximum_fractured_membrane_count": maximum_fractured_membranes,
        "maximum_fractured_beam_count": maximum_fractured_beams,
    }


def simulate_path(
    demand_kip: float,
    field_score: dict[int, float],
    gamma: float,
    time_index: int,
    prepared: dict[int, dict[str, object]],
    thermal: dict[str, list[list[float]]],
    coords: dict[int, tuple[float, float]],
    edges: list[tuple[int, int]],
    beam_shape: dict[str, float | str],
    slab_case: dict[str, object],
    slab_width_m: float,
    fy_params: dict[str, float],
    e_params: dict[str, float],
    fixed_temperature_fraction: float | None = None,
) -> dict[str, object]:
    top_sections = prepared[99]["sections"]
    incoming = v8b.initial_loads(demand_kip, top_sections, {}, "capacity_proportional")
    floor_results: dict[str, dict[str, object]] = {}
    first_failed_floor = None
    for floor in FLOORS_DESC:
        sections = prepared[floor]["sections"]
        t_min, t_max = [float(value) for value in thermal[str(floor)][time_index]]
        if fixed_temperature_fraction is None:
            scores = v8f.normalize_field(
                {column: field_score[column] for column in sections}
            )
            temperatures = v8f.temperatures_from_scores(scores, t_min, t_max, gamma)
        else:
            temperatures = {
                column: t_min + fixed_temperature_fraction * (t_max - t_min)
                for column in sections
            }
        state = story_response(
            incoming,
            temperatures,
            sections,
            prepared[floor]["removed"],
            coords,
            edges,
            beam_shape,
            slab_case,
            slab_width_m,
            fy_params,
            e_params,
        )
        floor_results[str(floor)] = {
            key: value for key, value in state.items() if key != "final_loads"
        }
        if not state["equilibrium"]:
            first_failed_floor = floor
            break
        incoming = state["final_loads"]
    return {
        "equilibrium_all_floors": first_failed_floor is None,
        "first_failed_floor": first_failed_floor,
        "floors_reached": len(floor_results),
        "floors": floor_results,
    }


def quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    return float(np.quantile(np.array(values, dtype=float), fraction))


def summarize_paths(paths: list[dict[str, object]]) -> dict[str, object]:
    failures = [path for path in paths if not path["equilibrium_all_floors"]]
    first_floors = [int(path["first_failed_floor"]) for path in failures]
    reasons: Counter[str] = Counter()
    floors_reached = [int(path["floors_reached"]) for path in paths]
    final_peaks: list[float] = []
    displacements: list[float] = []
    membrane_strains: list[float] = []
    fractured_membranes: list[int] = []
    fractured_beams: list[int] = []
    for path in paths:
        if path["equilibrium_all_floors"]:
            final_peaks.append(float(path["floors"]["94"]["final_peak_dcr"]))
        else:
            first = str(path["first_failed_floor"])
            reasons[str(path["floors"][first]["reason"])] += 1
        for floor_state in path["floors"].values():
            displacements.append(float(floor_state.get("maximum_abs_displacement_in", 0.0)))
            membrane_strains.append(float(floor_state.get("maximum_membrane_strain", 0.0)))
            fractured_membranes.append(
                int(floor_state.get("maximum_fractured_membrane_count", 0))
            )
            fractured_beams.append(int(floor_state.get("maximum_fractured_beam_count", 0)))
    return {
        "field_count": len(paths),
        "system_no_equilibrium_fraction": len(failures) / max(len(paths), 1),
        "median_first_failed_floor": statistics.median(first_floors) if first_floors else None,
        "first_failed_floor_counts": {
            str(floor): first_floors.count(floor) for floor in FLOORS_DESC
        },
        "failure_reason_counts": dict(reasons),
        "median_floors_reached": statistics.median(floors_reached),
        "median_floor94_peak_dcr_when_reached": (
            statistics.median(final_peaks) if final_peaks else None
        ),
        "p90_floor94_peak_dcr_when_reached": quantile(final_peaks, 0.90),
        "p90_maximum_story_displacement_in": quantile(displacements, 0.90),
        "p90_maximum_membrane_strain": quantile(membrane_strains, 0.90),
        "maximum_fractured_membranes_in_any_reached_floor": (
            max(fractured_membranes) if fractured_membranes else 0
        ),
        "maximum_fractured_beams_in_any_reached_floor": (
            max(fractured_beams) if fractured_beams else 0
        ),
    }


def component_envelopes(
    slab_cases: list[dict[str, object]],
    coords: dict[int, tuple[float, float]],
    edges: list[tuple[int, int]],
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> tuple[dict[str, object], dict[str, float]]:
    lengths = [math.dist(coords[i], coords[j]) for i, j in edges]
    geometry = {
        "convex_hull_area_m2": area_normalized_width_m(coords, edges, 1.0)[1],
        "edge_length_sum_m": sum(lengths),
        "edge_count": len(edges),
        "edge_length_min_m": min(lengths),
        "edge_length_median_m": statistics.median(lengths),
        "edge_length_max_m": max(lengths),
    }
    rows: dict[str, object] = {}
    representative_length = float(geometry["edge_length_median_m"])
    for slab_case in slab_cases:
        width_m, _, _ = area_normalized_width_m(
            coords, edges, float(slab_case["active_area_fraction"])
        )
        law = membrane_law(
            representative_length,
            width_m,
            float(slab_case["reinforcement_ratio"]),
            float(slab_case["wire_yield_ksi_rt"]),
            float(slab_case["ultimate_strain"]),
            20.0,
            fy_params,
            e_params,
        )
        at_ultimate = membrane_state_at_delta(
            0.999 * float(law["ultimate_delta_in"]), law
        )
        rows[str(slab_case["id"])] = {
            "effective_strip_width_m": width_m,
            "representative_edge_length_m": representative_length,
            "steel_area_per_representative_edge_in2": law["steel_area_in2"],
            "room_temperature_axial_yield_kip": law["axial_yield_kip"],
            "room_temperature_ultimate_relative_displacement_in": law[
                "ultimate_delta_in"
            ],
            "room_temperature_vertical_force_near_ultimate_kip": abs(
                float(at_ultimate["vertical_force_kip"])
            ),
        }
    return rows, geometry


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_plot(
    rows: list[dict[str, object]],
    slab_cases: list[dict[str, object]],
    components: dict[str, object],
    deterministic: list[dict[str, object]],
) -> None:
    canvas = Image.new("RGB", (1900, 1100), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (950, 48),
        "WTC 1 V8I-A - effet d'une dalle armee bornee, 20 a 60 min",
        anchor="mm",
        font=font(34, True),
        fill=(25, 35, 50),
    )
    colors = [
        (80, 80, 80),
        (196, 70, 65),
        (224, 150, 45),
        (75, 145, 205),
        (55, 155, 95),
        (105, 80, 180),
    ]
    color_by_case = {
        str(case["id"]): colors[index % len(colors)]
        for index, case in enumerate(slab_cases)
    }
    # Left panel: the mechanical capacity that distinguishes the slab cases.
    x0, y0, panel_width, panel_height = 95, 180, 790, 690
    draw.text(
        (x0 + panel_width / 2, y0 - 45),
        "Force verticale pres de l'allongement ultime",
        anchor="mm",
        font=font(26, True),
        fill=(35, 45, 60),
    )
    draw.text(
        (x0 + panel_width / 2, y0 - 12),
        "bande representative, acier a 20 C",
        anchor="mm",
        font=font(19),
        fill=(80, 85, 95),
    )
    plotted_cases = [case for case in slab_cases if float(case["active_area_fraction"]) > 0.0]
    maximum_capacity = max(
        float(components[str(case["id"])]["room_temperature_vertical_force_near_ultimate_kip"])
        for case in plotted_cases
    )
    axis_max = max(10.0, math.ceil(maximum_capacity / 10.0) * 10.0)
    label_width = 305
    bar_x = x0 + label_width
    bar_width = panel_width - label_width - 40
    row_height = panel_height / len(plotted_cases)
    for tick in range(0, int(axis_max) + 1, 10):
        x = bar_x + bar_width * tick / axis_max
        draw.line((x, y0, x, y0 + panel_height), fill=(228, 231, 236), width=2)
        draw.text((x, y0 + panel_height + 25), f"{tick} kip", anchor="ma", font=font(18), fill=(70, 75, 85))
    for index, slab_case in enumerate(plotted_cases):
        case_id = str(slab_case["id"])
        value = float(components[case_id]["room_temperature_vertical_force_near_ultimate_kip"])
        y = y0 + (index + 0.5) * row_height
        draw.text((bar_x - 15, y), case_id, anchor="rm", font=font(18), fill=(45, 50, 60))
        end_x = bar_x + bar_width * value / axis_max
        draw.rounded_rectangle(
            (bar_x, y - 21, end_x, y + 21),
            radius=8,
            fill=color_by_case[case_id],
        )
        draw.text((min(end_x + 10, x0 + panel_width), y), f"{value:.1f}", anchor="lm", font=font(18, True), fill=(35, 40, 50))

    # Right panel: deterministic controls expose the floor transition hidden
    # by the fully overlapping 100-percent ensemble curves.
    rx, ry = 1010, 180
    case_ids = ["no_slab_v8h_reference", "high_ratio_full_area", "cold_upper_envelope"]
    field_names = ["uniform_min", "uniform_midpoint", "uniform_max"]
    field_labels = ["minimum NIST", "milieu", "maximum NIST"]
    cell_width, cell_height = 205, 67
    label_width = 255
    draw.text(
        (rx + label_width + 1.5 * cell_width, ry - 45),
        "Premier niveau sans equilibre - controles uniformes",
        anchor="mm",
        font=font(26, True),
        fill=(35, 45, 60),
    )
    for column, label in enumerate(field_labels):
        draw.text(
            (rx + label_width + (column + 0.5) * cell_width, ry + 25),
            label,
            anchor="mm",
            font=font(18, True),
            fill=(55, 60, 70),
        )
    table_y = ry + 65
    row_index = 0
    for case_id in case_ids:
        draw.text(
            (rx, table_y + (row_index + 1.5) * cell_height),
            case_id,
            anchor="lm",
            font=font(17, True),
            fill=(45, 50, 60),
        )
        for time_min in TIMES:
            y = table_y + row_index * cell_height
            draw.text((rx + label_width - 12, y + cell_height / 2), f"{time_min} min", anchor="rm", font=font(18), fill=(65, 70, 80))
            for column, field_name in enumerate(field_names):
                item = next(
                    row
                    for row in deterministic
                    if row["slab_case"] == case_id
                    and row["time_min"] == time_min
                    and row["temperature_field"] == field_name
                )
                first_floor = item["first_failed_floor"]
                label = "stable" if first_floor is None else f"F{first_floor}"
                fill = (211, 231, 214) if first_floor is None else ((239, 211, 166) if int(first_floor) == 96 else (229, 181, 178))
                x = rx + label_width + column * cell_width
                draw.rectangle((x, y, x + cell_width, y + cell_height), fill=fill, outline="white", width=4)
                draw.text((x + cell_width / 2, y + cell_height / 2), label, anchor="mm", font=font(22, True), fill=(45, 45, 50))
            row_index += 1
        if case_id != case_ids[-1]:
            separator_y = table_y + row_index * cell_height
            draw.line((rx, separator_y, rx + label_width + 3 * cell_width, separator_y), fill=(100, 105, 115), width=3)
    draw.text(
        (950, 1040),
        "Les 3 600 champs spatiaux perdent l'equilibre dans ce reseau reduit; ce resultat n'est ni une probabilite reelle ni une preuve de demolition.",
        anchor="ma",
        font=font(21, True),
        fill=(95, 55, 55),
    )
    canvas.save(OUT_PNG)


def fmt_fraction(value: object) -> str:
    return f"{100.0 * float(value):.1f} %"


def main() -> None:
    started = time.perf_counter()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    transfer = json.loads(TRANSFER.read_text(encoding="utf-8"))
    aisc = json.loads(AISC.read_text(encoding="utf-8"))
    prior_b = json.loads(V8B_RESULT.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }
    edges = v8h.nearest_four_edges(coords)
    beam_shape = aisc["shapes"][BEAM_PROFILE]
    fy_params = transfer["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = transfer["steel_temperature_model"]["young_modulus_parameters"]
    thermal = transfer["fire_case_b"]["core_column_temperature_ranges_c"]
    history = transfer["nist_global_core_loads_floor_98_kip"]["case_b_time_history"]
    slab_cases = config["slab_cases"]

    prepared: dict[int, dict[str, object]] = {}
    for floor in FLOORS_DESC:
        floor_data = prior_b["floor_inputs"][str(floor)]
        prepared[floor] = {
            "sections": {int(key): value for key, value in floor_data["sections"].items()},
            "removed": set(int(value) for value in floor_data["initial_removed"]),
        }
    fields = {seed: v8f.smooth_score(coords, seed) for seed in SEEDS}
    widths = {
        str(case["id"]): area_normalized_width_m(
            coords, edges, float(case["active_area_fraction"])
        )[0]
        for case in slab_cases
    }
    components, geometry = component_envelopes(
        slab_cases, coords, edges, fy_params, e_params
    )

    rows: list[dict[str, object]] = []
    for time_min in TIMES:
        demand = float(history[str(time_min)])
        for gamma in GAMMAS:
            for slab_case in slab_cases:
                paths = [
                    simulate_path(
                        demand,
                        fields[seed],
                        gamma,
                        TIME_INDEX[time_min],
                        prepared,
                        thermal,
                        coords,
                        edges,
                        beam_shape,
                        slab_case,
                        widths[str(slab_case["id"])],
                        fy_params,
                        e_params,
                    )
                    for seed in SEEDS
                ]
                rows.append(
                    {
                        "time_min": time_min,
                        "gamma": gamma,
                        "slab_case": slab_case["id"],
                        **summarize_paths(paths),
                    }
                )

    deterministic: list[dict[str, object]] = []
    deterministic_cases = {
        "uniform_min": 0.0,
        "uniform_midpoint": 0.5,
        "uniform_max": 1.0,
    }
    reference_field = {column: 0.5 for column in coords}
    for time_min in TIMES:
        demand = float(history[str(time_min)])
        for slab_case in slab_cases:
            for name, fraction in deterministic_cases.items():
                state = simulate_path(
                    demand,
                    reference_field,
                    1.0,
                    TIME_INDEX[time_min],
                    prepared,
                    thermal,
                    coords,
                    edges,
                    beam_shape,
                    slab_case,
                    widths[str(slab_case["id"])],
                    fy_params,
                    e_params,
                    fixed_temperature_fraction=fraction,
                )
                deterministic.append(
                    {
                        "time_min": time_min,
                        "slab_case": slab_case["id"],
                        "temperature_field": name,
                        "equilibrium_all_floors": state["equilibrium_all_floors"],
                        "first_failed_floor": state["first_failed_floor"],
                        "floors_reached": state["floors_reached"],
                    }
                )

    cold_thermal = {
        str(floor): [[20.0, 20.0]] for floor in FLOORS_DESC
    }
    post_impact_cold: list[dict[str, object]] = []
    for slab_case in slab_cases:
        state = simulate_path(
            float(history["after_impact"]),
            reference_field,
            1.0,
            0,
            prepared,
            cold_thermal,
            coords,
            edges,
            beam_shape,
            slab_case,
            widths[str(slab_case["id"])],
            fy_params,
            e_params,
            fixed_temperature_fraction=0.0,
        )
        post_impact_cold.append(
            {
                "slab_case": slab_case["id"],
                "demand_kip": float(history["after_impact"]),
                "temperature_c": 20.0,
                "equilibrium_all_floors": state["equilibrium_all_floors"],
                "first_failed_floor": state["first_failed_floor"],
                "floors_reached": state["floors_reached"],
            }
        )

    runtime_seconds = time.perf_counter() - started
    payload = {
        "model": "WTC1_V8I_A_BOUNDED_CRACKED_SLAB_CATENARY",
        "version": "8.8.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": runtime_seconds,
        "configuration_file": str(CONFIG.relative_to(ROOT)).replace("\\", "/"),
        "facts_transferred": config["official_facts"],
        "documented_contradictions": config["documented_contradictions"],
        "model_assumptions": {
            **config["model_hypotheses"],
            "slab_cases": slab_cases,
            "omitted": [
                "as-built slab reinforcement and opening geometry",
                "localized slab impact damage mask",
                "concrete compression, cracking and aggregate interlock",
                "composite shear-stud failure",
                "office-floor transfer to the perimeter",
                "story self weight",
                "geometric P-delta compatibility between stories",
                "connection-specific fracture",
                "creep and transient dynamics",
            ],
        },
        "geometry_proxy": geometry,
        "component_envelopes": components,
        "ensemble_definition": config["ensemble"],
        "ensemble_rows": rows,
        "deterministic_cases": deterministic,
        "post_impact_cold_validation": post_impact_cold,
    }
    OUT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    selected_gamma = 1.0
    selected_rows = [row for row in rows if row["gamma"] == selected_gamma]
    md = [
        "# WTC 1 - V8I-A : dalle armee bornee et transition 20-60 min",
        "",
        "## Resultat principal",
        "",
        "V8I-A ajoute au reseau mecanique V8H une action de catenaire de dalle fissuree, portee uniquement par les armatures et bornee par leur limite elastique et leur allongement ultime. Il ne s'agit ni de la dalle NIST lineaire-elastique sans rupture, ni d'une transcription as-built : la topologie, la ferraille locale, les ouvertures et les degats de dalle restent incomplets.",
        "",
        f"Le proxy geometrique relie 47 colonnes par {geometry['edge_count']} aretes. L'enveloppe convexe des axes de colonnes mesure {geometry['convex_hull_area_m2']:.1f} m2; cette surface n'est pas la surface as-built nette de dalle.",
        "",
        "Resultat de validation decisif : les 3 600 champs spatiaux perdent l'equilibre, mais les controles uniformes minimaux et meme le cas post-impact entierement froid a 20 C echouent aussi. Or WTC 1 est reste debout 102 min apres l'impact. V8I-A est donc invalide comme representation autonome du chemin de charge reel; ses 100 % d'echec ne peuvent pas etre interpretes comme une probabilite ni comme une preuve en faveur d'un mecanisme de demolition.",
        "",
        "### Champs synthetiques, gamma=1",
        "",
        "| Cas de dalle | 20 min | 40 min | 60 min |",
        "|---|---:|---:|---:|",
    ]
    for slab_case in slab_cases:
        case_id = str(slab_case["id"])
        values = [
            next(
                row
                for row in selected_rows
                if row["slab_case"] == case_id and row["time_min"] == time_min
            )["system_no_equilibrium_fraction"]
            for time_min in TIMES
        ]
        md.append(
            f"| {case_id} | {fmt_fraction(values[0])} | {fmt_fraction(values[1])} | {fmt_fraction(values[2])} |"
        )
    md.extend(
        [
            "",
            "Chaque champ synthetique impose au moins un point a l'extremum chaud NIST du niveau. Les pourcentages ci-dessus mesurent donc la robustesse aux champs construits, jamais une probabilite de l'effondrement reel.",
            "",
            "### Cas uniformes de controle",
            "",
            "| Cas de dalle | Temps | minimum NIST | milieu de plage | maximum NIST |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    report_case_ids = [
        "no_slab_v8h_reference",
        "high_ratio_full_area",
        "cold_upper_envelope",
    ]
    for case_id in report_case_ids:
        for time_min in TIMES:
            statuses = []
            for field_name in deterministic_cases:
                row = next(
                    item
                    for item in deterministic
                    if item["slab_case"] == case_id
                    and item["time_min"] == time_min
                    and item["temperature_field"] == field_name
                )
                statuses.append(
                    "equilibre"
                    if row["equilibrium_all_floors"]
                    else f"echec F{row['first_failed_floor']}"
                )
            md.append(
                f"| {case_id} | {time_min} | {statuses[0]} | {statuses[1]} | {statuses[2]} |"
            )
    md.extend(
        [
            "",
            "### Validation statique post-impact, structure froide a 20 C",
            "",
            "| Cas de dalle | Demande noyau | Resultat |",
            "|---|---:|---:|",
        ]
    )
    for case_id in report_case_ids:
        row = next(item for item in post_impact_cold if item["slab_case"] == case_id)
        status = (
            "equilibre"
            if row["equilibrium_all_floors"]
            else f"echec F{row['first_failed_floor']}"
        )
        md.append(f"| {case_id} | {row['demand_kip']:.0f} kip | {status} |")
    md.extend(
        [
            "",
            "## Faits et sorties officielles transferees",
            "",
            "- NCSTAR 1-6C decrit au plancher 96 une dalle de noyau de 4,5 pouces sur poutres et poutres maitresses WF boulonnees aux colonnes.",
            "- NCSTAR 1-6C fournit 0,21 % et 0,74 % comme taux d'armatures de la dalle-type selon les deux directions, mais ne publie pas ici la ferraille as-built du noyau 94-99.",
            "- NCSTAR 1-6D indique que le module de la dalle de noyau du modele global a ete ajuste pour reproduire la rigidite composite acier-dalle; la valeur ajustee n'est pas fournie dans le passage inspecte.",
            "- NIST attribue aux planchers globaux une action de diaphragme et de membrane, tout en precisant que leur representation ne capture pas leurs modes de rupture thermiques.",
            "- La chronologie d'observation NIST place l'impact a 8:46:26 et le debut de l'effondrement a 10:28:20, soit 102 min plus tard; le batiment devait donc conserver un equilibre global apres impact et avant l'initiation.",
            "",
            "## Hypotheses propres a V8I",
            "",
            "- La dalle fissuree ne conserve aucune traction du beton : seule l'armature agit en catenaire. Cette option borne le mecanisme plus strictement que la coque lineaire-elastique globale de NIST.",
            "- Les taux 0,21 % et 0,74 % sont appliques isotropiquement, separement, comme bornes basse et haute; ils ne sont pas affectes a des directions reelles du noyau.",
            "- La largeur efficace est normalisee sur l'aire convexe des axes des colonnes, puis reduite par une fraction active. Les ouvertures, bords reels et degats localises ne sont pas mailles.",
            "- La limite d'elasticite de 70 ksi provient d'une representation NIST de treillis soude; le cas faible utilise 50 ksi et une ductilite inferieure pour tester la sensibilite.",
            "- Les poutres restent le proxy moyen 14WF136 de V8H avec deux plans actifs et assemblages a 100 % de la plastification proxy. Ce choix est favorable au transfert mais n'est pas une nomenclature as-built.",
            "",
            "## Resultats derives et limites",
            "",
            "- Une perte d'equilibre signifie qu'aucune solution statique n'est trouvee apres les ruptures imposees dans ce reseau reduit. Elle ne calcule ni l'initiation complete, ni la chute du bloc, ni la propagation dynamique.",
            "- Un maintien d'equilibre dans une borne favorable ne valide pas la chaine officielle complete; il montre seulement que ce sous-mecanisme peut porter la demande imposee avec ces hypotheses.",
            "- Un echec de toutes les bornes ne prouverait pas un explosif : il pourrait aussi signaler une topologie proxy incorrecte, des chemins manquants vers le perimetre ou le hat truss, ou une mauvaise reconstruction des champs thermiques.",
            "- Ici, l'echec du cas post-impact froid contredit directement la survie observee de la tour. La conclusion valide porte donc sur le sous-modele : il manque au moins un chemin stabilisant majeur avant toute etude d'initiation.",
            "",
            "## Contradictions et informations manquantes",
            "",
            "- Contradiction documentaire officielle : NCSTAR 1-6C qualifie la dalle de noyau de legere, tandis que NCSTAR 1-6 la qualifie de beton normal. V8I n'utilise pas la traction du beton, ce qui neutralise cette contradiction dans la loi de catenaire mais pas dans un futur modele de masse/compression.",
            "- Les fichiers WTCAB-Bk5-BeamSched.xls, WTCAB_DBk5.mdb et les donnees Drawing Book 6 ne figurent toujours pas dans le corpus local indexe.",
            "- Le module equivalent ajuste de la dalle globale NIST, la ferraille locale, les ouvertures et la carte de degats de dalle restent inconnus ou non transcrits.",
            "- La prochaine iteration doit d'abord reproduire l'equilibre post-impact froid en ajoutant explicitement les chemins noyau-planchers-perimetre et le hat truss; aucune animation d'effondrement ne doit etre couplee avant ce test.",
            "",
            f"Temps d'execution : {runtime_seconds:.1f} s. Configuration, graines, cas deterministes et lignes d'ensemble sont conserves dans le JSON V8I-A.",
            "",
        ]
    )
    OUT_REPORT.write_text("\n".join(md), encoding="utf-8")
    render_plot(rows, slab_cases, components, deterministic)
    print(
        json.dumps(
            {
                "status": "PASS",
                "rows": len(rows),
                "deterministic_cases": len(deterministic),
                "runtime_seconds": runtime_seconds,
                "report": str(OUT_REPORT),
                "results": str(OUT_JSON),
                "plot": str(OUT_PNG),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
