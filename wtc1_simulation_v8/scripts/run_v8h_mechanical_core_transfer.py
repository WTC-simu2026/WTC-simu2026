"""WTC 1 V8H-A - mechanically capped core-floor transfer, Floors 94-99.

This reduced-order model replaces V8F's direct nearest-neighbour load split by
vertical column springs coupled through bilinear beam springs.  It deliberately
keeps the documented moment-beam topology separate from a connected nearest-
four proxy because the original beam and connection schedules are unavailable.
"""

from __future__ import annotations

import json
import math
import random
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


CONFIG = V8 / "data" / "v8h_core_beam_network.json"
TRANSFER = V8 / "data" / "nist_wtc1_transfer.json"
AISC = V8 / "data" / "aisc_historic_wf_properties.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
V8F_RESULT = V8 / "output" / "resultats_wtc1_v8f_transfert_vertical.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8h_transfert_mecanique.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8h_transfert_mecanique.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8h_transfert_mecanique.png"

FLOORS_DESC = list(range(99, 93, -1))
TIMES = [80, 100]
GAMMAS = [1.0, 2.0]
SEEDS = list(range(100))
PROFILES = ["12WF65", "14WF136", "14WF228"]
TOPOLOGIES = ["nist_moment_only", "nearest_four_proxy"]
CONNECTION_FACTORS = [0.5, 1.0]
ACTIVE_PLANES = [1, 2]
BEAM_TEMPERATURE_POLICIES = [
    "cold_20c_upper_transfer_bound",
    "mean_endpoint_column_temperature_proxy",
]
TAIL = "linear_to_5pct_at_1000c"
HARDENING_RATIO = 0.01
ULTIMATE_ROTATION_RAD = 0.02
FY_BEAM_RT_KSI = 37.0
STORY_LENGTH_IN = 144.0
M_TO_IN = 39.37007874015748


def wf_plastic_modulus_proxy_in3(shape: dict[str, float | str]) -> float:
    """Rectangular flange/web reconstruction; root fillets are omitted."""
    d = float(shape["depth_in"])
    tw = float(shape["web_thickness_in"])
    bf = float(shape["flange_width_in"])
    tf = float(shape["flange_thickness_in"])
    hw = max(0.0, d - 2.0 * tf)
    flange_q_top = bf * tf * (0.5 * d - 0.5 * tf)
    half_web_q = tw * (0.5 * hw) * (0.25 * hw)
    return 2.0 * (flange_q_top + half_web_q)


def nearest_four_edges(coords: dict[int, tuple[float, float]]) -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for column, (x, y) in coords.items():
        nearest = sorted(
            (other for other in coords if other != column),
            key=lambda other: (coords[other][0] - x) ** 2 + (coords[other][1] - y) ** 2,
        )[:4]
        for other in nearest:
            edges.add(tuple(sorted((column, other))))
    return sorted(edges)


def beam_law(
    shape: dict[str, float | str],
    length_m: float,
    temperature_c: float,
    connection_factor: float,
    active_planes: int,
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, float]:
    length_in = length_m * M_TO_IN
    e_ksi = v8b.elastic_modulus_ksi(temperature_c, e_params, TAIL)
    fy_ksi = FY_BEAM_RT_KSI * v8b.yield_ratio(temperature_c, fy_params)
    ix = float(shape["ix_in4"])
    zx = wf_plastic_modulus_proxy_in3(shape)
    stiffness = active_planes * 12.0 * e_ksi * ix / max(length_in**3, 1e-12)
    mp_kip_in = fy_ksi * zx
    yield_force = (
        active_planes
        * connection_factor
        * 2.0
        * mp_kip_in
        / max(length_in, 1e-12)
    )
    yield_displacement = yield_force / max(stiffness, 1e-12)
    ultimate_displacement = ULTIMATE_ROTATION_RAD * length_in
    return {
        "temperature_c": temperature_c,
        "length_m": length_m,
        "e_ksi": e_ksi,
        "fy_ksi": fy_ksi,
        "ix_in4": ix,
        "zx_proxy_in3": zx,
        "initial_stiffness_kip_per_in": stiffness,
        "yield_force_kip": yield_force,
        "yield_displacement_in": yield_displacement,
        "ultimate_displacement_in": ultimate_displacement,
    }


def assemble_and_solve(
    loads: np.ndarray,
    load_factor: float,
    nodes: list[int],
    survivors: set[int],
    column_stiffness: dict[int, float],
    edge_rows: list[dict[str, object]],
) -> tuple[np.ndarray | None, str | None]:
    size = len(nodes)
    index = {column: position for position, column in enumerate(nodes)}
    adjacency = {column: set() for column in nodes}
    for edge in edge_rows:
        if str(edge["state"]) == "fractured":
            continue
        i, j = int(edge["i"]), int(edge["j"])
        adjacency[i].add(j)
        adjacency[j].add(i)
    floating_zero_resultant_anchors: list[int] = []
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
                return None, "disconnected_loaded_component"
            # Fix only the arbitrary rigid translation of an unloaded or
            # self-equilibrated floating component.  This adds no meaningful
            # vertical reaction because its external resultant is zero.
            floating_zero_resultant_anchors.append(min(component))
    matrix = np.zeros((size, size), dtype=float)
    rhs = load_factor * loads.copy()
    for column in survivors:
        matrix[index[column], index[column]] += column_stiffness[column]
    for column in floating_zero_resultant_anchors:
        matrix[index[column], index[column]] += 1.0
    for edge in edge_rows:
        state = str(edge["state"])
        if state == "fractured":
            continue
        i = index[int(edge["i"])]
        j = index[int(edge["j"])]
        stiffness = float(edge["stiffness"])
        constant = 0.0
        if state == "plastic":
            tangent = HARDENING_RATIO * stiffness
            constant = float(edge["sign"]) * (
                float(edge["capacity"]) - tangent * float(edge["yield_displacement"])
            )
        else:
            tangent = stiffness
        matrix[i, i] += tangent
        matrix[j, j] += tangent
        matrix[i, j] -= tangent
        matrix[j, i] -= tangent
        rhs[i] -= constant
        rhs[j] += constant
    try:
        displacement = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        return None, "singular_transfer_network"
    if not np.all(np.isfinite(displacement)):
        return None, "non_finite_displacement"
    return displacement, None


def solve_beam_network(
    loads_by_column: dict[int, float],
    survivors: set[int],
    column_stiffness: dict[int, float],
    edge_definitions: list[dict[str, float | int]],
    prefractured: set[tuple[int, int]],
) -> dict[str, object]:
    nodes = sorted(loads_by_column)
    index = {column: position for position, column in enumerate(nodes)}
    loads = np.array([float(loads_by_column[column]) for column in nodes], dtype=float)
    edges: list[dict[str, object]] = []
    for row in edge_definitions:
        key = tuple(sorted((int(row["i"]), int(row["j"]))))
        edges.append(
            {
                **row,
                "state": "fractured" if key in prefractured else "elastic",
                "sign": 0.0,
            }
        )

    # Proportional load increments retain the sign and fracture history of the
    # bilinear springs.  Ten steps are enough for this reduced-order envelope;
    # this is not a transient integration.
    displacement: np.ndarray | None = None
    for load_factor in np.linspace(0.1, 1.0, 10):
        for _iteration in range(100):
            displacement, reason = assemble_and_solve(
                loads, float(load_factor), nodes, survivors, column_stiffness, edges
            )
            if displacement is None:
                return {
                    "equilibrium": False,
                    "reason": reason,
                    "fractured_edges": sorted(prefractured),
                }
            changed = False
            for edge in edges:
                if edge["state"] == "fractured":
                    continue
                delta = displacement[index[int(edge["i"])]] - displacement[index[int(edge["j"])]]
                if edge["state"] == "elastic" and abs(delta) > float(edge["yield_displacement"]) * (1.0 + 1e-8):
                    edge["state"] = "plastic"
                    edge["sign"] = 1.0 if delta >= 0.0 else -1.0
                    changed = True
                if edge["state"] == "plastic" and abs(delta) > float(edge["ultimate_displacement"]):
                    edge["state"] = "fractured"
                    prefractured.add(tuple(sorted((int(edge["i"]), int(edge["j"])))))
                    changed = True
            if not changed:
                break
        else:
            return {
                "equilibrium": False,
                "reason": "beam_active_set_not_converged",
                "fractured_edges": sorted(prefractured),
            }

    assert displacement is not None
    # Preserve the sign for exact vertical equilibrium.  A locally negative
    # spring reaction is carried as tension into the next story, but only the
    # positive (compressive) part is checked against column buckling strength.
    reactions = {
        column: column_stiffness[column] * displacement[index[column]]
        for column in survivors
    }
    edge_forces = []
    for edge in edges:
        i, j = int(edge["i"]), int(edge["j"])
        delta = displacement[index[i]] - displacement[index[j]]
        if edge["state"] == "fractured":
            force = 0.0
        elif edge["state"] == "elastic":
            force = float(edge["stiffness"]) * delta
        else:
            tangent = HARDENING_RATIO * float(edge["stiffness"])
            force = tangent * delta + float(edge["sign"]) * (
                float(edge["capacity"]) - tangent * float(edge["yield_displacement"])
            )
        edge_forces.append(
            {
                "i": i,
                "j": j,
                "state": edge["state"],
                "force_kip": force,
                "capacity_kip": float(edge["capacity"]),
                "relative_displacement_in": delta,
            }
        )
    reaction_total = sum(reactions.values())
    load_total = float(loads.sum())
    relative_residual = abs(reaction_total - load_total) / max(load_total, 1e-9)
    return {
        "equilibrium": relative_residual < 1e-6,
        "reason": "stable" if relative_residual < 1e-6 else "force_residual",
        "reactions": reactions,
        "edge_forces": edge_forces,
        "fractured_edges": sorted(prefractured),
        "plastic_edge_count": sum(row["state"] == "plastic" for row in edges),
        "fractured_edge_count": sum(row["state"] == "fractured" for row in edges),
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
    connection_factor: float,
    active_planes: int,
    beam_temperature_policy: str,
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, object]:
    # A segment unloaded or absent in the story above remains a node and can
    # become a support in the story below.  Preserve all 47 nodal positions,
    # assigning zero incoming force where the upper-story reaction is absent.
    nodal_loads = {
        column: float(incoming_loads.get(column, 0.0)) for column in sections
    }
    survivors = set(sections) - set(removed)
    prefractured: set[tuple[int, int]] = set()
    failed_columns: list[int] = []
    maximum_dcr = 0.0
    for _cascade in range(len(sections) + 1):
        column_stiffness = {
            column: v8b.elastic_modulus_ksi(temperatures[column], e_params, TAIL)
            * float(sections[column]["area_in2"])
            / STORY_LENGTH_IN
            for column in survivors
        }
        capacities = {
            column: v8b.nominal_column_capacity_kip(
                sections[column], temperatures[column], 1.0, fy_params, e_params, TAIL
            )
            for column in survivors
        }
        edge_definitions: list[dict[str, float | int]] = []
        for i, j in edges:
            length_m = math.dist(coords[i], coords[j])
            if beam_temperature_policy == "cold_20c_upper_transfer_bound":
                beam_temperature = 20.0
            else:
                beam_temperature = 0.5 * (temperatures[i] + temperatures[j])
            law = beam_law(
                beam_shape,
                length_m,
                beam_temperature,
                connection_factor,
                active_planes,
                fy_params,
                e_params,
            )
            edge_definitions.append(
                {
                    "i": i,
                    "j": j,
                    "stiffness": law["initial_stiffness_kip_per_in"],
                    "capacity": law["yield_force_kip"],
                    "yield_displacement": law["yield_displacement_in"],
                    "ultimate_displacement": law["ultimate_displacement_in"],
                }
            )
        state = solve_beam_network(
            nodal_loads, survivors, column_stiffness, edge_definitions, prefractured
        )
        if not state["equilibrium"]:
            return {
                "equilibrium": False,
                "reason": state["reason"],
                "failed_columns": failed_columns,
                "failed_count": len(failed_columns),
                "surviving_count": len(survivors),
                "fractured_edge_count": len(state.get("fractured_edges", [])),
                "maximum_dcr_during_cascade": maximum_dcr,
                "relative_force_residual": state.get("relative_force_residual"),
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
                "plastic_edge_count": state["plastic_edge_count"],
                "fractured_edge_count": state["fractured_edge_count"],
                "maximum_abs_displacement_in": state["maximum_abs_displacement_in"],
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
        "fractured_edge_count": len(prefractured),
        "maximum_dcr_during_cascade": maximum_dcr,
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
    connection_factor: float,
    active_planes: int,
    beam_temperature_policy: str,
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, object]:
    top_sections = prepared[99]["sections"]
    incoming = v8b.initial_loads(demand_kip, top_sections, {}, "capacity_proportional")
    floor_results: dict[str, dict[str, object]] = {}
    first_failed_floor = None
    for floor in FLOORS_DESC:
        sections = prepared[floor]["sections"]
        t_min, t_max = [float(value) for value in thermal[str(floor)][time_index]]
        scores = v8f.normalize_field({column: field_score[column] for column in sections})
        temperatures = v8f.temperatures_from_scores(scores, t_min, t_max, gamma)
        state = story_response(
            incoming,
            temperatures,
            sections,
            prepared[floor]["removed"],
            coords,
            edges,
            beam_shape,
            connection_factor,
            active_planes,
            beam_temperature_policy,
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
    return float(np.quantile(np.asarray(values, dtype=float), fraction))


def component_envelopes(
    shapes: dict[str, dict[str, float | str]],
    coords: dict[int, tuple[float, float]],
    topologies: dict[str, list[tuple[int, int]]],
    fy_params: dict[str, float],
    e_params: dict[str, float],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for topology, edges in topologies.items():
        spans = sorted(math.dist(coords[i], coords[j]) for i, j in edges)
        median_span = statistics.median(spans)
        result[topology] = {
            "edge_count": len(edges),
            "connected_column_count": len({column for edge in edges for column in edge}),
            "span_min_m": min(spans),
            "span_median_m": median_span,
            "span_max_m": max(spans),
            "profiles_at_median_span": {
                profile: {
                    "20c": beam_law(
                        shapes[profile], median_span, 20.0, 1.0, 1, fy_params, e_params
                    ),
                    "600c": beam_law(
                        shapes[profile], median_span, 600.0, 1.0, 1, fy_params, e_params
                    ),
                }
                for profile in PROFILES
            },
        }
    return result


def render_plot(
    rows: list[dict[str, object]],
    envelopes: dict[str, object],
) -> None:
    def font(size: int, bold: bool = False):
        name = "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            return ImageFont.load_default()

    canvas = Image.new("RGB", (1900, 1050), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((950, 42), "WTC 1 - V8H-A : transfert mecanique borne", anchor="ma", font=font(42, True), fill=(20, 25, 35))
    draw.text((950, 100), "Poutres bilineaires + ressorts axiaux de colonnes, niveaux 94-99", anchor="ma", font=font(25), fill=(80, 85, 95))

    # Component force-displacement curves at the median moment-beam span.
    x0, y0, width, height = 120, 220, 720, 610
    draw.text((x0 + width / 2, 165), "Loi composant a 20 C", anchor="ma", font=font(29, True), fill=(25, 30, 40))
    draw.line((x0, y0, x0, y0 + height), fill=(60, 65, 75), width=3)
    draw.line((x0, y0 + height, x0 + width, y0 + height), fill=(60, 65, 75), width=3)
    env = envelopes["nist_moment_only"]
    laws = env["profiles_at_median_span"]
    max_force = max(float(laws[p]["20c"]["yield_force_kip"]) for p in PROFILES) * 1.15
    max_delta = max(float(laws[p]["20c"]["yield_displacement_in"]) for p in PROFILES) * 4.0
    colors = [(40, 103, 178), (221, 113, 38), (46, 139, 87)]
    for profile, color in zip(PROFILES, colors):
        law = laws[profile]["20c"]
        k = float(law["initial_stiffness_kip_per_in"])
        fy = float(law["yield_force_kip"])
        dy = float(law["yield_displacement_in"])
        points = []
        for step in range(121):
            delta = max_delta * step / 120.0
            force = k * delta if delta <= dy else fy + HARDENING_RATIO * k * (delta - dy)
            force = min(force, max_force)
            px = x0 + width * delta / max_delta
            py = y0 + height - height * force / max_force
            points.append((px, py))
        draw.line(points, fill=color, width=5)
    for idx, (profile, color) in enumerate(zip(PROFILES, colors)):
        draw.line((x0 + 32, y0 + 34 + idx * 42, x0 + 90, y0 + 34 + idx * 42), fill=color, width=6)
        draw.text((x0 + 105, y0 + 34 + idx * 42), profile, anchor="lm", font=font(22), fill=(35, 40, 50))
    draw.text((x0 + width / 2, y0 + height + 48), "Deplacement vertical relatif (in)", anchor="ma", font=font(22), fill=(45, 50, 60))
    draw.text((x0, y0 - 18), "Force (kip)", anchor="ls", font=font(22), fill=(45, 50, 60))
    draw.text((x0, y0 + height + 92), f"Portee mediane: {env['span_median_m']:.2f} m; 1 plan; assemblage=1,0", font=font(20), fill=(70, 75, 85))

    # Failure-fraction comparison at 100 min, gamma=1, strongest connection,
    # two active planes, endpoint temperature proxy.
    hx, hy, cw, ch = 1050, 280, 230, 150
    draw.text((hx + 1.5 * cw, 165), "Champs sans equilibre", anchor="ma", font=font(29, True), fill=(25, 30, 40))
    draw.text((hx + 1.5 * cw, 205), "100 min, gamma=1, assemblage=1,0, 2 plans", anchor="ma", font=font(20), fill=(75, 80, 90))
    for j, profile in enumerate(PROFILES):
        draw.text((hx + j * cw + cw / 2, hy - 38), profile, anchor="mm", font=font(22, True), fill=(35, 40, 50))
    labels = {"nist_moment_only": "NIST moment", "nearest_four_proxy": "Proxy 4 voisins"}
    for i, topology in enumerate(TOPOLOGIES):
        y = hy + i * ch
        draw.text((hx - 25, y + ch / 2), labels[topology], anchor="rm", font=font(22), fill=(35, 40, 50))
        for j, profile in enumerate(PROFILES):
            row = next(
                item
                for item in rows
                if item["time_min"] == 100
                and item["gamma"] == 1.0
                and item["topology"] == topology
                and item["beam_profile_proxy"] == profile
                and item["connection_factor"] == 1.0
                and item["active_floor_planes"] == 2
                and item["beam_temperature_policy"] == "mean_endpoint_column_temperature_proxy"
            )
            value = float(row["system_no_equilibrium_fraction"])
            color = (
                round(241 - 135 * value),
                round(247 - 170 * value),
                round(250 - 95 * value),
            )
            x = hx + j * cw
            draw.rectangle((x, y, x + cw, y + ch), fill=color, outline="white", width=4)
            draw.text((x + cw / 2, y + ch / 2), f"{100*value:.0f}%", anchor="mm", font=font(32, True), fill=(25, 30, 40))
    draw.text((hx + 1.5 * cw, hy + 2 * ch + 60), "Fraction de 100 champs synthetiques; pas une probabilite reelle", anchor="ma", font=font(20), fill=(85, 55, 55))
    draw.text((950, 995), "Le proxy connecte borne les chemins manquants; il ne reconstitue pas le plan de poutres d'origine.", anchor="ma", font=font(22, True), fill=(60, 65, 75))
    canvas.save(OUT_PNG)


def main() -> None:
    started = time.perf_counter()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    transfer = json.loads(TRANSFER.read_text(encoding="utf-8"))
    aisc = json.loads(AISC.read_text(encoding="utf-8"))
    prior_b = json.loads(V8B_RESULT.read_text(encoding="utf-8"))
    prior_f = json.loads(V8F_RESULT.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }
    shapes = {profile: aisc["shapes"][profile] for profile in PROFILES}
    fy_params = transfer["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = transfer["steel_temperature_model"]["young_modulus_parameters"]
    thermal = transfer["fire_case_b"]["core_column_temperature_ranges_c"]
    history = transfer["nist_global_core_loads_floor_98_kip"]["case_b_time_history"]
    damage = transfer["core_damage"]["more_severe"]

    prepared: dict[int, dict[str, object]] = {}
    for floor in FLOORS_DESC:
        floor_data = prior_b["floor_inputs"][str(floor)]
        prepared[floor] = {
            "sections": {int(key): value for key, value in floor_data["sections"].items()},
            "removed": set(int(value) for value in floor_data["initial_removed"]),
        }
    topologies = {
        "nist_moment_only": [
            tuple(int(value) for value in edge)
            for edge in config["moment_beam_topology"]["edges"]
        ],
        "nearest_four_proxy": nearest_four_edges(coords),
    }
    envelopes = component_envelopes(shapes, coords, topologies, fy_params, e_params)
    fields = {seed: v8f.smooth_score(coords, seed) for seed in SEEDS}

    rows: list[dict[str, object]] = []
    for time_index, time_min in [(3, 80), (4, 100)]:
        demand = float(history[str(time_min)])
        for gamma in GAMMAS:
            for topology_name in TOPOLOGIES:
                edges = topologies[topology_name]
                for profile in PROFILES:
                    for connection_factor in CONNECTION_FACTORS:
                        for active_planes in ACTIVE_PLANES:
                            for beam_temperature_policy in BEAM_TEMPERATURE_POLICIES:
                                failures = 0
                                first_floors: list[int] = []
                                floors_reached: list[int] = []
                                reasons: Counter[str] = Counter()
                                final_peak: list[float] = []
                                fractures: list[int] = []
                                maximum_displacements: list[float] = []
                                for seed in SEEDS:
                                    state = simulate_path(
                                        demand,
                                        fields[seed],
                                        gamma,
                                        time_index,
                                        prepared,
                                        thermal,
                                        coords,
                                        edges,
                                        shapes[profile],
                                        connection_factor,
                                        active_planes,
                                        beam_temperature_policy,
                                        fy_params,
                                        e_params,
                                    )
                                    floors_reached.append(int(state["floors_reached"]))
                                    if not state["equilibrium_all_floors"]:
                                        failures += 1
                                        first_floor = int(state["first_failed_floor"])
                                        first_floors.append(first_floor)
                                        reasons[str(state["floors"][str(first_floor)]["reason"])] += 1
                                    else:
                                        final_peak.append(float(state["floors"]["94"]["final_peak_dcr"]))
                                    for floor_state in state["floors"].values():
                                        fractures.append(int(floor_state.get("fractured_edge_count", 0)))
                                        if "maximum_abs_displacement_in" in floor_state:
                                            maximum_displacements.append(float(floor_state["maximum_abs_displacement_in"]))
                                rows.append(
                                    {
                                        "time_min": time_min,
                                        "gamma": gamma,
                                        "topology": topology_name,
                                        "beam_profile_proxy": profile,
                                        "connection_factor": connection_factor,
                                        "active_floor_planes": active_planes,
                                        "beam_temperature_policy": beam_temperature_policy,
                                        "field_count": len(SEEDS),
                                        "system_no_equilibrium_fraction": failures / len(SEEDS),
                                        "median_first_failed_floor": statistics.median(first_floors) if first_floors else None,
                                        "first_failed_floor_counts": {str(floor): first_floors.count(floor) for floor in FLOORS_DESC},
                                        "failure_reason_counts": dict(reasons),
                                        "median_floors_reached": statistics.median(floors_reached),
                                        "median_floor94_peak_dcr_when_reached": statistics.median(final_peak) if final_peak else None,
                                        "p90_floor94_peak_dcr_when_reached": quantile(final_peak, 0.90),
                                        "maximum_fractured_edges_in_any_reached_floor": max(fractures) if fractures else 0,
                                        "p90_maximum_story_displacement_in": quantile(maximum_displacements, 0.90),
                                    }
                                )

    v8f_reference = next(
        row
        for row in prior_f["ensemble_rows"]
        if row["time_min"] == 100
        and row["elastic_modulus_tail"] == TAIL
        and row["gamma"] == 1.0
        and row["redistribution"] == "local_four"
        and row["damage_residual_case"] == "nist_removed_only"
        and row["transfer_amplification"] == 1.0
    )
    runtime_seconds = time.perf_counter() - started
    payload = {
        "model": "WTC1_V8H_A_MECHANICALLY_CAPPED_CORE_TRANSFER",
        "version": "8.7.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": runtime_seconds,
        "configuration_file": str(CONFIG.relative_to(ROOT)).replace("\\", "/"),
        "facts_transferred": config["official_facts"],
        "model_assumptions": {
            "beam_schedule": config["beam_section_proxies"],
            "moment_topology": config["moment_beam_topology"],
            "proxy_topology": config["proxy_topology"],
            "mechanical_law": config["mechanical_law"],
            "vertical_coupling": "stable column-spring reactions at one story become nodal loads at the story below",
            "column_support": "elastic axial spring EA/L capped by the V8B nominal temperature-reduced column capacity",
            "column_failure_history": "fractured beam links persist within a story cascade; plastic offsets are recalculated after each column removal",
            "beam_temperature_proxy": "endpoint mean uses synthetic column temperatures because beam temperature histories are unavailable",
            "omitted": ["story self weight", "geometric P-delta compatibility between stories", "slab cracking and membrane failure", "connection-specific fracture", "transient dynamics"],
            "fractions_are_event_probabilities": False,
        },
        "topology_summary": {
            name: {
                "edge_count": len(edges),
                "connected_column_count": len({column for edge in edges for column in edge}),
            }
            for name, edges in topologies.items()
        },
        "component_envelopes": envelopes,
        "v8f_uncapped_reference": {
            "case": "100 min, gamma 1, local four, NIST removals only, amplification 1.0",
            "system_no_equilibrium_fraction": v8f_reference["system_no_equilibrium_fraction"],
        },
        "ensemble_rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Report a controlled comparison rather than selecting the most favorable
    # member envelope after seeing the result.
    selected = [
        row
        for row in rows
        if row["time_min"] == 100
        and row["gamma"] == 1.0
        and row["connection_factor"] == 1.0
        and row["active_floor_planes"] == 2
        and row["beam_temperature_policy"] == "mean_endpoint_column_temperature_proxy"
    ]
    moment_coverage = payload["topology_summary"]["nist_moment_only"]
    proxy_coverage = payload["topology_summary"]["nearest_four_proxy"]
    md = [
        "# WTC 1 - V8H-A : transfert mecanique borne dans le noyau",
        "",
        "## Resultat principal",
        "",
        "V8H-A remplace la redistribution directe de V8F par des ressorts axiaux de colonnes et des poutres bilineaires limitees en force et en deformation. Le resultat le plus net n'est pas une validation finale, mais l'identification d'une donneee indispensable : le sous-reseau NIST des seules poutres a assemblages rigides ne relie que "
        f"{moment_coverage['connected_column_count']} des 47 colonnes par {moment_coverage['edge_count']} liaisons. Il ne peut donc pas, a lui seul, redistribuer les charges des colonnes endommagees des rangees 500 et 1000.",
        "",
        "Le reseau proxy a quatre voisins relie les 47 colonnes par "
        f"{proxy_coverage['edge_count']} liaisons. Il teste mecanquement une enveloppe de chemins supplementaires (poutres secondaires + dalle), mais ne constitue pas le plan d'origine.",
        "",
        "Dans les 19 200 chemins tardifs testes (80 et 100 min), toutes les variantes finissent par creer une composante chargee sans appui apres plastification/rupture des liaisons : 18 633 s'arretent d'abord au niveau 97 et 567 au niveau 96. Ce resultat vaut uniquement pour ces reseaux locaux bornes. Chaque champ synthetique force en outre au moins une colonne a l'extremum chaud NIST du niveau; il s'agit d'un test de robustesse enveloppe, pas d'une distribution mesuree.",
        "",
        "### Comparaison a 100 min, gamma=1",
        "",
        "Assemblage a 100 % de la resistance plastique proxy, deux plans de poutres actifs, temperature de poutre prise comme moyenne des temperatures synthetiques aux extremites.",
        "",
        "| Topologie | Section WF proxy | champs sans equilibre | premier niveau defaillant median |",
        "|---|---:|---:|---:|",
    ]
    for topology in TOPOLOGIES:
        for profile in PROFILES:
            row = next(item for item in selected if item["topology"] == topology and item["beam_profile_proxy"] == profile)
            label = "NIST, poutres moment seulement" if topology == "nist_moment_only" else "Proxy connecte a 4 voisins"
            first = row["median_first_failed_floor"] if row["median_first_failed_floor"] is not None else "aucun"
            md.append(f"| {label} | {profile} | {100*float(row['system_no_equilibrium_fraction']):.1f} % | {first} |")
    md.extend(
        [
            "",
            f"Reference V8F non bornee correspondante (4 voisins) : {100*float(v8f_reference['system_no_equilibrium_fraction']):.1f} % de champs sans equilibre. La difference avec V8H-A mesure l'effet combine de la rigidite, de la capacite et de la rupture des chemins; elle n'est pas une probabilite physique.",
            "",
            "## Faits directement documentes",
            "",
            "- NIST n'a modele individuellement dans le modele global que les poutres de noyau a assemblages rigides; la rigidite axiale des autres poutres etait integree a celle de la dalle.",
            "- NIST attribue aux profiles WF de noyau de nuance 36 ksi un comportement de materiau avec Fy=37,0 ksi a temperature ambiante.",
            "- Le modele detaille du plancher 96 comporte les poutres du noyau et la dalle; NIST traite ce plancher comme typique des niveaux superieurs.",
            "- NCSTAR 1-2A nomme les fichiers originaux de nomenclature des poutres et assemblages, mais ces fichiers ne figurent pas dans l'archive locale inspectee.",
            "",
            "## Hypotheses du modele",
            "",
            "- Les profils 12WF65, 14WF136 et 14WF228 sont des bornes de sensibilite issues de la table historique AISC deja tracee; aucune de ces sections n'est attribuee a une poutre reelle des niveaux 94-99.",
            "- La resistance d'assemblage vaut 50 % ou 100 % de la force de plastification de la poutre proxy; aucune valeur Book 6 n'est disponible pour la remplacer.",
            "- Un ou deux plans de plancher peuvent participer au transfert. La rotation relative ultime de 0,02 rad et le tangent post-plastique de 1 % sont des hypotheses explicites.",
            "- La temperature de poutre est soit maintenue a 20 C (borne optimiste de transfert), soit prise comme moyenne des temperatures synthetiques des deux colonnes terminales (proxy, pas une mesure).",
            "",
            "## Resultats derives et limites",
            "",
            "- Une perte d'equilibre indique qu'aucune solution statique n'est trouvee avec les liaisons et limites imposees. Elle ne calcule ni la chute du bloc superieur ni la propagation dynamique globale.",
            "- Le motif final des 19 200 calculs est `disconnected_loaded_component` : apres ruptures successives, un groupe de noeuds conserve une charge verticale mais n'est plus relie a aucune colonne porteuse dans le reseau impose.",
            "- Le reseau moment-only est structurellement incomplet par conception; son echec ne contredit pas NIST, puisque NIST attribue aussi un role local a la dalle composite.",
            "- Le proxy connecte peut tester l'ordre de grandeur des sections, mais il ne peut pas valider l'as-built tant que les Books 5 et 6, la ferraille de dalle et les modifications locales ne sont pas recuperes.",
            "- Les fractions portent sur 100 champs synthetiques bornes par les extrema NIST. Elles ne sont jamais interpretees comme probabilite de l'evenement reel.",
            "",
            "## Contradictions ou informations manquantes",
            "",
            "Aucune contradiction numerique nouvelle avec les sorties NIST n'est etablie a ce stade. En revanche, il existe une lacune documentaire bloquante pour une verification independante : les fichiers WTCAB-Bk5-BeamSched.xls / WTCAB_DBk5.mdb et les donnees Book 6 d'assemblages ne sont pas publies dans le corpus local utilise. Une simulation qui leur substituerait une section unique sans intervalle donnerait une precision artificielle.",
            "",
            f"Temps d'execution : {runtime_seconds:.1f} s. Configuration, graines et resultats complets sont conserves dans le JSON V8H-A.",
            "",
        ]
    )
    OUT_REPORT.write_text("\n".join(md), encoding="utf-8")
    render_plot(rows, envelopes)
    print(json.dumps({"status": "PASS", "rows": len(rows), "runtime_seconds": runtime_seconds, "report": str(OUT_REPORT), "results": str(OUT_JSON), "plot": str(OUT_PNG)}, indent=2))


if __name__ == "__main__":
    main()
